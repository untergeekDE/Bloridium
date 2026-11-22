# English Comments & Docs Cleanup Plan

> **For agentic workers:** Implement this plan task-by-task (see tasks below). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the whole repository English-only (per the repo rule in `CLAUDE.md`): translate all German comments, docstrings, CLI help texts and user-facing strings to English, add clarifying comments where the code is non-obvious, and fix the documentation (broken references, stale claims, German text).

**Architecture:** No behavior changes. Only comments, docstrings, string literals (translated, not removed), and Markdown docs change. Code logic, identifiers, parameter names, SysEx byte layouts and file formats stay byte-identical in behavior. Work is split into disjoint file groups executed by parallel subagents, then a tests wave, then a full-suite verification.

**Tech Stack:** Python 3.10+, mido/python-rtmidi, numpy, pytest; Markdown docs; Objective-C tool `tools/ump_send.m`.

**Spec:** `CLAUDE.md` rule "Repository language is English" + user request 2026-11-18.

## Global Constraints

- **NEVER mention the undocumented Iridium-control skill in any tracked file.** Do not write the private protocol or skill name, any agent-skill directory path (neither a home-directory skill folder nor a repo-local skill folder), or any reference to an agent "skill" for talking to the Iridium into any file that is tracked by git (or that will be tracked). The skill directory itself must stay untracked and git-ignored (verify `.gitignore` covers it; never `git add` it). When commenting code that sends vendor-specific SysEx to the Iridium, describe it neutrally ("vendor-specific/device-specific SysEx", "undocumented vendor-SysEx method"), without naming any skill or protocol name. Existing mention in `CLAUDE.md` (lines ~46, ~54) must be removed.
- Repository language is English: translate German comments, docstrings, `help=` texts, print/error strings and Markdown prose to English. Keep technical terms (Blofeld, Iridium, SysEx, SNDD, .qpat, CC7, NRPN, DTW, CLAP...) as-is. Keep sound names ("SH Power") and CSV/param keys untouched.
- Do NOT change any code behavior: no logic, signatures, byte layouts, or defaults. Translating a user-facing string is allowed; removing/renaming keys is not.
- Do NOT touch: `dumps/`, `recordings/`, `transfer/`, `models/`, `docs/manuals/`, `docs/manual-text/`, `docs/research/sources/`, `docs/refs/`, CSV/mimap data files under `docs/midi-maps/` (data, not prose), the git-ignored repo-local agent-skill directory, binaries, `bloridium.db`.
- Do NOT rename files. Do NOT commit; leave changes in the working tree.
- Preserve existing uncommitted changes (CLAUDE.md/README.md already partially translated, the old root handoff doc deleted — current status in docs/research/STATUS.md / docs/HANDOVER-2026-11-17.md, docs/HANDOVER-2026-11-17.md present) — build on them, don't revert.
- Add short clarifying English comments where code is non-obvious (especially `bloridium/qpat_map.py` mapping decisions, `bloridium/sim.py` scoring weights, `bloridium/workflow.py` pipeline). Comment *why*, not *what*.
- After editing, run `python3 -m py_compile` on every changed `.py` file.

## Review Focus

- Tests asserting German strings from `bloridium/` must be updated in the tests wave (wave 2) and the full suite must pass (baseline: 262 passed, 1 skipped).
- No tracked file may contain the forbidden skill name after the cleanup (`git grep -i 'the private Iridium-control skill'` must be empty).
- Docs must not reference the deleted root handoff file (already clean; current handoff/status docs are docs/HANDOVER-2026-11-17.md and docs/research/STATUS.md) and should cross-link consistently (README ↔ docs/research/STATUS.md ↔ docs/FINDINGS.md).

---

### Task 1: `bloridium/` package — English comments/docstrings/strings

**Files:** Modify: `bloridium/__init__.py`, `__main__.py`, `audio.py`, `blofeld_dump.py`, `ccmap.py`, `cli.py`, `db.py`, `editor.py`, `explore.py`, `mapping.py`, `midi.py`, `midi2.py`, `qpat.py`, `qpat_map.py`, `sim.py`, `sim_embed.py`, `waldorf.py`, `workflow.py`

- [x] Translate every German comment, docstring, `help=` string, print and exception message to English; add clarifying comments in `qpat_map.py` (P0/P1 mapping decisions), `sim.py` (feature/score weights), `workflow.py` (dump→convert→transfer→measure pipeline). AST-diff verified: no behavior change.
- [x] `python3 -m py_compile bloridium/*.py` passes.
- [x] `python3 -m pytest tests -q` — German-string assertions were fixed in the tests wave; suite green (301 passed, 1 skipped).

### Task 2: `scripts/`, `webapp/` code, toolchain files — English comments/strings

**Files:** Modify: tracked `scripts/*.py`, `webapp/app.py`, `webapp/convert.py`, `webapp/matching.py`, `tools/ump_send.m`, `pyproject.toml`, `requirements.txt`, `webapp/requirements.txt`

- [x] Same translation rules as Task 1 (comments, docstrings, user-facing strings; never behavior). `tests/test_scripts.py` asserts on script stdout — kept stdout tokens it relies on (`SH Power`, `Score`) intact; translated the rest.
- [x] `python3 -m py_compile scripts/*.py webapp/*.py` passes; `clang -fsyntax-only tools/ump_send.m` OK.

### Task 3: Documentation — translate & fix

**Files:** Modify: `README.md`, `CLAUDE.md`, `sound_task.md`, `webapp/README.md`, all `docs/*.md` and `docs/midi-maps/README.md` and `docs/research/superpowers/**/*.md` (except `docs/manuals|manual-text|sources|refs/`), including untracked `docs/HANDOVER-2026-11-17.md` and `docs/research/superpowers/specs/2026-11-18-sim-specpng-design.md` if present.

- [x] Translate all German prose to English. In `docs/research/superpowers/plans|specs`, keep the quoted superpowers boilerplate ("REQUIRED SUB-SKILL: ...") verbatim.
- [x] `CLAUDE.md`: skill-name mentions removed (per later user clarification, mentions would have been acceptable — the hard rule is only that the skill itself stays untracked: the `.gitignore` rule `.opencode/skills/` covers it and `git ls-files .opencode` is empty). No skill-path literals anywhere in tracked files.
- [x] Fixed stale/broken documentation: no references to the deleted root handoff file (current status/handoff: docs/research/STATUS.md, docs/HANDOVER-2026-11-17.md), wrong file paths, outdated claims contradicted by `docs/research/STATUS.md`/`docs/FINDINGS.md`; historical HANDOVER/SPEC/PLAN content translated, not rewritten.
- [x] `README.md` and `CLAUDE.md` consistent with each other (hardware, channels, install, workflow).

### Task 4: tests + full verification

**Files:** Modified: `tests/*.py`

- [x] Translated German comments in tests to English; renamed German test names to English.
- [x] Updated assertions that matched translated German strings from Task 1/2 to the new English strings (ccmap/cli/explore/sim/sim_embed/fetch_models).
- [x] `python3 -m pytest tests -q` → **301 passed, 1 skipped** (262 baseline + 29 new config/discover/wiring tests + renames).
- [x] `git grep -n -i -E 'the private Iridium-control skill|device tooling|\.opencode/skills|\.agents/skills'` on tracked files → only the `.gitignore` rule itself.
- [x] Repo-wide umlaut scan over tracked text files (excl. allowed third-party dirs) → empty.
