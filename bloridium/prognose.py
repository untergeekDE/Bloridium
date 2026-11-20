"""prognose.py – random forest (numpy-only, CPU): Blofeld SNDD parameters -> expected
conversion quality (0-100).

Why no sklearn: scipy was broken in the author's env (libgfortran missing) and the
repo core is numpy-only – hence a compact own RandomForestRegressor
(CART regression, bootstrap, mtry=p//3, SSE gain metric).
Persistence via stdlib pickle (no joblib needed). Only load model files you trust.

Caveat (2026-11-20): the shipped model (n=99) has R² < 0 on held-out data, and its
label (sim.compare "score") saturates – see FIXES_TODO.md before relying on it.

Features: SDATA bytes of the SNDD (indices 0..382 without name bytes 363..378) / 127.
Label: sim_log.jsonl – per location (meta.blofeld) the mean over result[target]
(default "combined", fallback "score"). Dumps: dumps/blofeld_sndd_<LOC>_<ts>.bin
(the location is also in the SysEx header bb/nn).
"""

from __future__ import annotations

import json
import pickle
from datetime import datetime
from pathlib import Path

import numpy as np

from . import blofeld_dump

REPO = Path(__file__).resolve().parent.parent
DEFAULT_DUMPS = REPO / "dumps"
DEFAULT_MODEL = REPO / "models" / "prognose_rf.pkl"

SDATA_SIZE = blofeld_dump.SDATA_SIZE          # 383
NAME_IDX = set(range(363, 379))               # Soundname im Dump
FEATURE_IDX = [i for i in range(SDATA_SIZE) if i not in NAME_IDX]   # 367 Features


# --------------------------------------------------------------------------
# Mini-Random-Forest (numpy-only)
# --------------------------------------------------------------------------

class _Tree:
    """CART regression tree: best SSE split over mtry random features."""

    def __init__(self, mtry: int, max_depth: int, min_samples_leaf: int, rng):
        self.mtry = mtry
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.rng = rng
        self.importance_ = None
        self.root = None

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.importance_ = np.zeros(X.shape[1])
        self.root = self._build(X, y, 0)
        return self

    def _build(self, X, y, depth):
        n = y.size
        if depth >= self.max_depth or n < 2 * self.min_samples_leaf:
            return {"leaf": True, "value": float(y.mean())}
        gain, feat, thr = self._best_split(X, y)
        if gain <= 1e-12 or feat is None:
            return {"leaf": True, "value": float(y.mean())}
        self.importance_[feat] += gain
        mask = X[:, feat] <= thr
        return {"leaf": False, "feat": feat, "thr": thr,
                "left": self._build(X[mask], y[mask], depth + 1),
                "right": self._build(X[~mask], y[~mask], depth + 1)}

    def _best_split(self, X, y):
        n, p = X.shape
        # subsample split search to max. 64 rows (speed; the partition itself uses all rows)
        if n > 64:
            sub = self.rng.choice(n, size=64, replace=False)
            X, y = X[sub], y[sub]
            n = y.size
        m = min(self.mtry, p)
        feats = self.rng.choice(p, size=m, replace=False)
        sse_parent = float(np.sum(y * y) - np.sum(y) ** 2 / n)
        best_gain, best_feat, best_thr = 0.0, None, None
        max_thr = 32
        for f in feats:
            col = X[:, f]
            order = np.argsort(col, kind="stable")
            cs = col[order]
            ys = y[order]
            c1 = np.cumsum(ys)
            c2 = np.cumsum(ys * ys)
            # thresholds at unique midpoints, capped at max_thr
            uniq = np.unique(cs)
            if uniq.size < 2:
                continue
            thr_cand = (uniq[:-1] + uniq[1:]) / 2.0
            if thr_cand.size > max_thr:
                thr_cand = thr_cand[np.linspace(0, thr_cand.size - 1, max_thr).astype(int)]
            # Indizes der Schwellen in der sortierten Folge
            pos = np.searchsorted(cs, thr_cand, side="right")
            pos = np.clip(pos, self.min_samples_leaf, n - self.min_samples_leaf)
            nl = pos.astype(float)
            sl = c1[pos - 1]
            sl2 = c2[pos - 1]
            sr = c1[-1] - sl
            sr2 = c2[-1] - sl2
            sse_l = sl2 - sl * sl / nl
            sse_r = sr2 - sr * sr / (n - nl)
            gains = sse_parent - sse_l - sse_r
            k = int(np.argmax(gains))
            if gains[k] > best_gain:
                best_gain, best_feat, best_thr = float(gains[k]), int(f), float(thr_cand[k])
        return best_gain, best_feat, best_thr

    def predict(self, X: np.ndarray) -> np.ndarray:
        X = np.atleast_2d(np.asarray(X, dtype=np.float64))
        return np.array([self._pred_row(self.root, row) for row in X])

    def _pred_row(self, node, row):
        while not node["leaf"]:
            node = node["left"] if row[node["feat"]] <= node["thr"] else node["right"]
        return node["value"]


class RandomForestRegressor:
    """Minimaler RF-Regressor im sklearn-Stil (fit/predict/estimators_/feature_importances_)."""

    def __init__(self, n_estimators: int = 200, max_depth: int = 10,
                 min_samples_leaf: int = 2, max_features: str = "third",
                 random_state: int = 42):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.max_features = max_features
        self.random_state = random_state
        self.estimators_: list[_Tree] = []
        self.feature_importances_: np.ndarray | None = None
        self.n_features_: int = 0

    def fit(self, X, y):
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64).ravel()
        n, p = X.shape
        self.n_features_ = p
        # regression: p//3 like the sklearn regression default – with few
        # informative features among 367, sqrt(p) would miss the signal
        mtry = max(1, p // 3) if self.max_features == "third" else p
        rng = np.random.default_rng(self.random_state)
        self.estimators_ = []
        imp = np.zeros(p)
        for _ in range(self.n_estimators):
            idx = rng.integers(0, n, n)          # Bootstrap
            t = _Tree(mtry, self.max_depth, self.min_samples_leaf, rng)
            t.fit(X[idx], y[idx])
            self.estimators_.append(t)
            imp += t.importance_
        self.feature_importances_ = imp / max(imp.sum(), 1e-12)
        return self

    def predict(self, X) -> np.ndarray:
        X = np.atleast_2d(np.asarray(X, dtype=np.float64))
        return np.mean([t.predict(X) for t in self.estimators_], axis=0)


# --------------------------------------------------------------------------
# Features / IO
# --------------------------------------------------------------------------

def param_names() -> list[str]:
    """Blofeld parameter names parallel to FEATURE_IDX (from blofeld_dump.SDATA)."""
    out = []
    for i in FEATURE_IDX:
        entry = blofeld_dump.SDATA.get(i)
        out.append(entry[0] if entry else f"param{i}")
    return out


def feature_vector(parsed: dict) -> np.ndarray:
    """SNDD parameter vector (367,) in [0,1] from a parse_sndd result."""
    sd = parsed["sdata"]
    return np.array([sd[i] for i in FEATURE_IDX], dtype=np.float64) / 127.0


def loc_from_header(data: bytes) -> str:
    """Location ('A043') from the SysEx header bytes (bb/nn), with/without F0/F7."""
    d = list(data)
    if d and d[0] == 0xF0:
        d = d[1:]
    if d and d[-1] == 0xF7:
        d = d[:-1]
    bb, nn = d[4], d[5]
    return f"{chr(65 + bb)}{nn + 1:03d}"


def find_dump(dumps_dir, loc: str) -> Path:
    """Newest SNDD dump (*.bin) with a matching location in the header."""
    dumps_dir = Path(dumps_dir)
    best = None
    for p in sorted(dumps_dir.glob("*.bin")):
        try:
            if loc_from_header(p.read_bytes()) == loc:
                if best is None or p.name > best.name:
                    best = p
        except Exception:
            continue
    if best is None:
        raise FileNotFoundError(f"no SNDD dump for {loc} in {dumps_dir}")
    return best


def load_training_rows(log_path, dumps_dir, target: str = "combined",
                       min_score_version: int | None = None):
    """JSONL log + dumps -> (X, y, locs, skipped).

    Aggregated per location (mean over all target values of that loc).
    error/silent entries and locs without a valid dump end up in `skipped`.

    min_score_version: skip rows whose result.score_version is lower (rows
    without the field count as version 1, i.e. the saturating pre-2026-11-20
    score). None = no filter (library default, keeps old behaviour).
    """
    log_path = Path(log_path)
    per_loc: dict[str, list[float]] = {}
    skipped: list[str] = []
    if log_path.exists():
        for line in log_path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                skipped.append("invalid JSON line in the log")
                continue
            meta, res = e.get("meta") or {}, e.get("result") or {}
            loc = meta.get("blofeld")
            if not loc:
                skipped.append("entry without meta.blofeld")
                continue
            if res.get("verdict") in ("error", "fehler") or res.get("score") is None:
                skipped.append(f"{loc}: error/silent ({res.get('error')})")
                continue
            if min_score_version is not None and \
                    int(res.get("score_version") or 1) < min_score_version:
                skipped.append(f"{loc}: score_version {res.get('score_version') or 1} "
                               f"< {min_score_version}")
                continue
            v = res.get(target)
            if v is None:
                v = res.get("score")
            if v is None:
                skipped.append(f"{loc}: neither '{target}' nor 'score' present")
                continue
            per_loc.setdefault(loc, []).append(float(v))
    X, y, locs = [], [], []
    for loc in sorted(per_loc):
        try:
            dump = find_dump(dumps_dir, loc)
        except FileNotFoundError:
            skipped.append(f"{loc}: no dump in {dumps_dir}")
            continue
        parsed = blofeld_dump.parse_sndd(dump.read_bytes())
        if not parsed["chk_ok"]:
            skipped.append(f"{loc}: Checksumme falsch ({dump.name})")
            continue
        X.append(feature_vector(parsed))
        y.append(float(np.mean(per_loc[loc])))
        locs.append(loc)
    X = np.array(X, dtype=np.float64).reshape(len(locs), len(FEATURE_IDX))
    return X, np.asarray(y, dtype=np.float64), locs, skipped


# --------------------------------------------------------------------------
# Train / Persist / Predict
# --------------------------------------------------------------------------

def _r2(y, p):
    ss_res = float(np.sum((y - p) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 1e-12 else 0.0


def train_model(X, y, seed: int = 42, n_estimators: int = 200, test_size: float = 0.25,
                target: str = "combined") -> dict:
    """RF trainieren -> Bundle {model, metrics, importances, …}.

    Holdout-Metriken (MAE/RMSE/R²) wenn n gross genug, sonst Train-Metriken;
    5-fold CV R² only for n >= 10. Deterministic via seed.
    """
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64).ravel()
    n = int(y.size)
    metrics = {"n": n, "mae": None, "rmse": None, "r2": None, "r2_cv": None, "holdout": False}
    n_test = int(n * test_size)
    if n >= 5 and n_test >= 2:
        rng = np.random.default_rng(seed)
        perm = rng.permutation(n)
        te = perm[:n_test]
        tr = perm[n_test:]
        rf = RandomForestRegressor(n_estimators=n_estimators, random_state=seed).fit(X[tr], y[tr])
        p = rf.predict(X[te])
        metrics.update(mae=float(np.mean(np.abs(y[te] - p))),
                       rmse=float(np.sqrt(np.mean((y[te] - p) ** 2))),
                       r2=_r2(y[te], p), holdout=True)
    else:
        rf = RandomForestRegressor(n_estimators=n_estimators, random_state=seed).fit(X, y)
        p = rf.predict(X)
        metrics.update(mae=float(np.mean(np.abs(y - p))),
                       rmse=float(np.sqrt(np.mean((y - p) ** 2))),
                       r2=_r2(y, p), holdout=False)
    if n >= 10:
        rng = np.random.default_rng(seed + 1)
        perm = rng.permutation(n)
        folds = np.array_split(perm, 5)
        scores = []
        for k in range(5):
            te = folds[k]
            tr = np.concatenate([folds[j] for j in range(5) if j != k])
            m = RandomForestRegressor(n_estimators=max(50, n_estimators // 2),
                                      random_state=seed).fit(X[tr], y[tr])
            scores.append(_r2(y[te], m.predict(X[te])))
        metrics["r2_cv"] = float(np.mean(scores))
    imps = sorted(zip(param_names(), rf.feature_importances_),
                  key=lambda t: -t[1])[:20]
    return {"model": rf, "metrics": metrics,
            "importances": [(nm, float(v)) for nm, v in imps],
            "feature_names": param_names(), "target": target, "n": n, "seed": seed,
            "trained_at": datetime.now().isoformat(timespec="seconds")}


def save_model(bundle: dict, path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(bundle, f)
    return path


def load_model(path) -> dict:
    with open(path, "rb") as f:
        return pickle.load(f)


def predict_loc(loc: str, dumps_dir, model_path) -> dict:
    """Predict one Blofeld location with a saved model.

    std = standard deviation over the individual trees (prediction uncertainty).
    """
    bundle = load_model(model_path)
    dump = find_dump(dumps_dir, loc)
    parsed = blofeld_dump.parse_sndd(dump.read_bytes())
    x = feature_vector(parsed).reshape(1, -1)
    rf = bundle["model"]
    tree_preds = np.array([t.predict(x)[0] for t in rf.estimators_])
    return {"loc": loc, "predicted": float(rf.predict(x)[0]),
            "std": float(tree_preds.std()), "model": Path(model_path).name,
            "target": bundle.get("target", "combined"),
            "dump": dump.name, "trained_at": bundle.get("trained_at")}
