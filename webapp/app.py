"""Bloridium web app – upload Blofeld dump, convert, ZIP + match score.

Layout like webpage.pdf: title "Bloridium Tool v<conversion>", upload form
(Select File / Convert), NOTE box, footer with untergeek.de / GitHub.
Background: webapp/static/bloridium-scaled.jpg (photo Iridium + Blofeld).

Local:   python3 webapp/app.py            ( then http://localhost:8000 )
Podman:  gunicorn -b 0.0.0.0:8000 app:app  (see webapp/Containerfile)

Env: DATA_DIR (default ./data), DATA_TTL_HOURS (default 24), PORT (default 8000),
     BLORIDIUM_CORE_DIR / BLORIDIUM_TEMPLATE (see convert.py)
"""

from __future__ import annotations

import os
import re
import shutil
import threading
import time
import uuid
from html import escape
from pathlib import Path

from flask import Flask, abort, after_this_request, request, send_file

import convert
import matching

TOKEN_RE = re.compile(r"[0-9a-f]{32}")

def footer(sim_ver: str) -> str:
    return ('<footer><strong>Read the blog post on <a href="https://www.untergeek.de/2026/11/bloridium-porting-blofeld-sounds-to-the-iridium/#more-6616">untergeek.de</a> &middot;</strong> '
            'Repository of conversion tools: '
            '<a href="https://github.com/untergeekDE/Bloridium">github.com/untergeekDE/Bloridium</a>'
            ' &middot; <a href="/privacy">Privacy</a>'
            ' &middot; <a href="https://www.untergeek.de/cc/">Imprint</a>'
            f' &middot; Bloridium v{convert.CONVERSION_VERSION} &middot; GPL-3.0</footer>')

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bloridium Tool v{conv}</title>
<style>
 body{{margin:0;min-height:100vh;font-family:system-ui,-apple-system,sans-serif;color:#1a1a1a;
   background:url('/static/bloridium-scaled.jpg') no-repeat center center fixed;
   background-size:cover}}
 .card{{max-width:780px;margin:3rem auto;background:rgba(255,255,255,.93);padding:1.4rem 1.8rem;
   border-radius:10px;box-shadow:0 3px 16px rgba(0,0,0,.45)}}
 h1{{margin:.1rem 0 .2rem;font-size:1.7rem}}
 h2{{font-size:1.15rem;margin:1.2rem 0 .3rem}}
 .sub{{margin:.1rem 0 1rem;color:#333;font-size:1.05rem}}
 form{{margin:1rem 0;padding:1rem;border:1px solid #bbb;border-radius:8px;background:#fafafa}}
 button{{font-size:1rem;padding:.45rem 1.2rem;border:1px solid #888;border-radius:6px;
   background:#eee;cursor:pointer}}
 button:hover{{background:#ddd}}
 .note{{background:#fff6d8;border:1px solid #d8b93c;border-radius:6px;padding:.55rem .8rem;
   font-size:.9rem;margin:.8rem 0}}
 footer{{font-size:.82rem;color:#555;margin-top:1.2rem}}
 table{{border-collapse:collapse;width:100%;margin:1rem 0;font-size:.88rem}}
 th,td{{border:1px solid #ccc;padding:.28rem .5rem;text-align:left}}
 th{{background:#f0f0f0}} .score{{font-weight:bold}}
 .bar{{background:#e4e4e4;border-radius:3px;min-width:90px}}
 .bar>div{{background:#4a7ebb;height:.65rem;border-radius:3px}}
 .err{{color:#a00}} code{{background:#f2f2f2;padding:0 .3rem}}
</style></head><body><div class="card">
{body}
</div></body></html>"""

def index_body(score_note: str) -> str:
    return f"""
<h1>Bloridium Tool v{convert.CONVERSION_VERSION}</h1>
<p class="sub"><b>Convert Blofeld Sound Banks for the Iridium</b></p>
<p>Upload a Blofeld Midi Dump File (.SYX bank, e.g. from Sysex Librarian,
   single sound as .bin/.hex, or a .mid MIDI file containing SysEx sound dumps)</p>
<p>Download as a ZIP with Iridium *.qpat file(s) to import from SD or USB</p>
<form method="post" action="/upload" enctype="multipart/form-data">
  <input type="file" name="file" accept=".syx,.bin,.hex,.mid,.midi" required>
  <button type="submit">Convert</button>
</form>
<p class="note">Your file is processed in memory. The generated ZIP is deleted
  after your one-time download (at the latest after one hour). Uploads are not
  used for training. See <a href="/privacy">Privacy</a>.</p>
<p class="note"><b>NOTE:</b> Due to a host of technical issues, the converted sound is a very
  crude approximation on what you get on the Blofeld. Use it as a starting point,
  not as a 1:1 representation.</p>
<p class="note">The predicted match score shown after conversion is {score_note}.</p>
{footer(_active_sim_version())}
"""


PRIVACY_BODY = """
<h1>Privacy</h1>
<p class="sub">Bloridium converter &ndash; bloridium.frankruft.de</p>

<p>This page explains what happens to the file you upload and to the data
produced while you use the converter.</p>

<h2>Controller</h2>
<p>J. Eggers, Herbartstr. 17, D-60316 Frankfurt/M, Germany.<br>
Contact: <a href="https://www.untergeek.de/cc/">Imprint and Contact</a>.</p>

<h2>What we process</h2>
<ul>
<li><b>Your upload.</b> The MIDI/SysEx file you select is processed in memory
to convert it. It is not written to disk and is discarded when the
conversion finishes.</li>
<li><b>Generated files.</b> The ZIP (including <code>report.json</code> with
sound names, parameters and scores) is stored under a random link only so
that you can download it. It is deleted as soon as the ZIP has been sent to
your browser. If you never download it, it is deleted automatically after
one hour. The download link works once.</li>
<li><b>Server logs.</b> The web server records a truncated IP address (the
last IPv4 octet or IPv6 group is replaced by <code>xxx</code>), date and
time, the requested URL (including the random download token), HTTP status,
transferred bytes, referrer and user agent. This is used only to operate the
service and to detect abuse. Server logs are rotated and deleted according
to the server configuration.</li>
</ul>

<h2>No training on your data</h2>
<p>Uploaded sounds are <b>not used for training</b> the similarity model and
are not used for any purpose other than producing your download. The random
forest model was trained on the operator's own A/B measurements, not on
user uploads.</p>

<h2>Cookies and tracking</h2>
<p>This service sets no cookies and uses no analytics, advertising, tracking
pixels, third-party fonts or CDNs. The page loads its background image from
this server. Links to external sites (for example the blog or GitHub) are
contacted only when you click them.</p>

<h2>Legal basis</h2>
<p>Providing the conversion you request is based on Art. 6(1)(b) GDPR
(pre-contractual/contractual request) or, where no contract applies, on
Art. 6(1)(f) GDPR (legitimate interest in operating the free tool). Server
logs are processed on the basis of Art. 6(1)(f) GDPR for security and abuse
prevention.</p>

<h2>Retention</h2>
<p>Uploads exist only in memory during the request. Generated ZIP/report
files are deleted after the one-time download, or after one hour if they are
never downloaded. Server logs are kept only for the period configured for
the web server and system logs and are then rotated out.</p>

<h2>Your rights</h2>
<p>You have the right to access, rectification, erasure, restriction of
processing, data portability and objection, and the right to complain to a
supervisory authority. The authority responsible for the controller is the
<a href="https://datenschutz.hessen.de/">Hessian Commissioner for Data
Protection and Freedom of Information</a>. Because the service has no user
accounts, we may need the download token from your link to identify the
temporary files.</p>

<h2>Score</h2>
<p>The predicted match score is a rough estimate. It is not an automated
decision with legal effect.</p>

<h2>Changes</h2>
<p>This page may be updated when the service changes. Last updated:
22 November 2026.</p>
"""


def _active_sim_version() -> str:
    mpath = matching.resolve_model_path(os.environ.get("BLORIDIUM_MODEL"))
    return matching.SIMILARITY_VERSION if mpath else matching.PLACEHOLDER_VERSION


def _score_note() -> str:
    mpath = matching.resolve_model_path(os.environ.get("BLORIDIUM_MODEL"))
    if mpath:
        return (f'similarity v{matching.SIMILARITY_VERSION} &ndash; random-forest prognosis '
                f'(model <code>{escape(mpath.name)}</code>, trained on A/B measurements, '
                'see docs/HANDOVER-2026-11-19-rf-dataset.md). <b>Treat it as a rough '
                'indication only:</b> the model was trained on 99 sounds, does not beat '
                'a constant guess on held-out data (R&sup2; &lt; 0), and the underlying '
                'similarity score is known to saturate (see FIXES_TODO.md)')
    return (f'similarity v{matching.PLACEHOLDER_VERSION} &ndash; deterministic placeholder '
            '(no trained model found; set BLORIDIUM_MODEL to enable the RF prognosis)')


def start_cleanup_thread(app) -> threading.Thread | None:
    """Delete expired artifacts even when no requests arrive.

    The remaining TTL is short (1 h), so a request-triggered cleanup alone
    would not keep the privacy promise after a quiet period.
    """
    if os.environ.get("BLORIDIUM_CLEANUP_THREAD", "1") == "0":
        return None
    interval = float(os.environ.get("CLEANUP_INTERVAL_S", "30"))

    def loop():
        while True:
            time.sleep(interval)
            try:
                app.cleanup()
            except Exception:
                app.logger.exception("artifact cleanup failed")

    t = threading.Thread(target=loop, name="bloridium-cleanup", daemon=True)
    t.start()
    return t


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("MAX_UPLOAD_MB", "8")) * 1024 * 1024
    app.data_dir = Path(os.environ.get("DATA_DIR") or (Path(__file__).parent / "data"))
    app.data_dir.mkdir(parents=True, exist_ok=True)
    app.ttl_hours = float(os.environ.get("DATA_TTL_HOURS", "1"))

    def page(body: str) -> str:
        return PAGE.format(conv=convert.CONVERSION_VERSION, body=body)

    app.cleanup_interval_s = float(os.environ.get("CLEANUP_INTERVAL_S", "30"))
    app._last_cleanup = 0.0

    def cleanup():
        """Delete upload dirs older than the TTL.

        Several gunicorn workers may run this at the same time, so every
        filesystem step tolerates the other worker having deleted the entry
        first (previously: FileNotFoundError -> HTTP 500 on a random request).
        """
        cutoff = time.time() - app.ttl_hours * 3600
        for d in list(app.data_dir.iterdir()):
            try:
                if d.is_dir() and d.stat().st_mtime < cutoff:
                    shutil.rmtree(d, ignore_errors=True)
            except FileNotFoundError:
                continue

    @app.before_request
    def _cleanup():
        # at most once per interval per worker instead of on every request
        now = time.time()
        if now - app._last_cleanup >= app.cleanup_interval_s:
            app._last_cleanup = now
            app.cleanup()

    app.cleanup = cleanup
    app.cleanup_thread = start_cleanup_thread(app)

    @app.errorhandler(413)
    def too_large(e):
        return page(f'<p class="err">Upload too large '
                    f'(limit {app.config["MAX_CONTENT_LENGTH"] // 1024 // 1024} MB).</p>'
                    f'<p><a href="/">back</a></p>'), 413

    @app.get("/")
    def index():
        return page(index_body(_score_note()))

    @app.get("/privacy")
    def privacy():
        return page(PRIVACY_BODY)

    @app.get("/health")
    def health():
        return "ok\n"

    @app.post("/upload")
    def upload():
        f = request.files.get("file")
        if f is None or not f.filename:
            return page('<p class="err">No file selected.</p><p><a href="/">back</a></p>'), 400
        data = f.read()
        try:
            report = convert.process_upload(f.filename, data, app.data_dir,
                                            model_path=os.environ.get("BLORIDIUM_MODEL"))
        except convert.UploadError as e:
            return page(f'<p class="err">Invalid upload: {escape(str(e))}</p>'
                        '<p><a href="/">back</a></p>'), 400
        return page(_results_html(report))

    @app.get("/download/<token>")
    def download(token):
        if not TOKEN_RE.fullmatch(token):
            abort(404)
        tdir = app.data_dir / token
        if not (tdir / "result.zip").exists():
            abort(404)
        # Claim the token atomically: the second concurrent request gets 404.
        # The unique suffix avoids colliding with a stale directory from a
        # crashed earlier download.
        sending = app.data_dir / f".{token}.{uuid.uuid4().hex}.sending"
        try:
            os.rename(tdir, sending)
        except OSError:
            abort(404)
        try:
            # send_file opens the file now; unlinking it before the response
            # has been transmitted is safe on Unix (deployment) because the
            # open descriptor keeps the data readable.
            resp = send_file(sending / "result.zip", as_attachment=True,
                             download_name=_zip_name(sending))
        except Exception:
            shutil.rmtree(sending, ignore_errors=True)
            raise

        @after_this_request
        def _delete_after_download(response):
            shutil.rmtree(sending, ignore_errors=True)
            return response

        return resp

    @app.after_request
    def _no_store(response):
        if request.endpoint in {"upload", "download"}:
            response.headers["Cache-Control"] = "no-store"
        return response

    return app


def _zip_name(tdir: Path) -> str:
    import json
    try:
        return json.loads((tdir / "report.json").read_text(encoding="utf-8")).get("zip_name") \
            or "bloridium.zip"
    except Exception:
        return "bloridium.zip"


def _results_html(report: dict) -> str:
    rows = []
    for s in report["sounds"]:
        pens = "; ".join(s.get("penalties") or []) or "–"
        if s.get("std") is not None:
            pens = f"±{s['std']} (RF tree std); " + pens
        width = max(2, round(s["score"]))
        rows.append(
            f"<tr><td><code>{escape(s['location'])}</code></td>"
            f"<td>{escape(s['name'])}</td><td>{escape(s['category'])}</td>"
            f'<td class="score" title="{escape(pens)}">{s["score"]:.1f}</td>'
            f'<td class="bar"><div style="width:{width}%"></div></td>'
            f'<td title="{escape(", ".join(s["unmapped"]))}">{len(s["unmapped"])}</td></tr>')
    errs = "".join(f'<li>Message {e["index"]}: {escape(e["error"])}</li>'
                   for e in report.get("errors", []))
    matcher = escape(report.get("matcher") or "")
    model = f", model <code>{escape(Path(report['model']).name)}</code>" if report.get("model") else ""
    return f"""
<h1>Bloridium Tool v{convert.CONVERSION_VERSION}</h1>
<p class="sub">Results for <code>{escape(report['source_file'])}</code>:
  {report['num_sounds']} sounds converted, {report['num_errors']} errors,
  {report['skipped_messages']} non-sound messages skipped &ndash;
  avg predicted score <b>{report['avg_score']:.1f}</b>
  (similarity {escape(report.get('similarity_version', ''))}, {matcher}{model})</p>
<p><a href="/download/{report['token']}"><button>Download ZIP ({escape(report['zip_name'])})</button></a></p>
<p class="note">One-time download: the ZIP is deleted from the server after it
has been sent, and at the latest after one hour. report.json is inside the ZIP.</p>
<table><tr><th>Loc</th><th>Name</th><th>Category</th><th>Score</th><th></th>
<th>not in MIDI map</th></tr>
{''.join(rows)}
</table>
{('<p class="err"><b>Errors:</b></p><ul>' + errs + '</ul>') if errs else ''}
<p><a href="/">Convert another file</a></p>
{footer(report.get('similarity_version', '').lstrip('v'))}
"""


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
