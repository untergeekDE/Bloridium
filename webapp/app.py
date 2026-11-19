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
import time
from html import escape
from pathlib import Path

from flask import Flask, abort, request, send_file

import convert
import matching

TOKEN_RE = re.compile(r"[0-9a-f]{32}")

def footer(sim_ver: str) -> str:
    return ('<footer>Info on <a href="https://untergeek.de">untergeek.de</a> &middot; '
            'Repository of conversion tools: '
            '<a href="https://github.com/untergeekDE/Bloridium">github.com/untergeekDE/Bloridium</a>'
            f' &middot; conversion v{convert.CONVERSION_VERSION} / similarity v{sim_ver}</footer>')

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
   or single sound as .bin/.hex)</p>
<p>Download as a ZIP with Iridium *.qpat file(s) to import from SD or USB</p>
<form method="post" action="/upload" enctype="multipart/form-data">
  <input type="file" name="file" required>
  <button type="submit">Convert</button>
</form>
<p class="note"><b>NOTE:</b> Due to a host of technical issues, the converted sound is a very
  crude approximation on what you get on the Blofeld. Use it as a starting point,
  not as a 1:1 representation.</p>
<p class="note">The predicted match score shown after conversion is {score_note}.</p>
{footer(_active_sim_version())}
"""


def _active_sim_version() -> str:
    mpath = matching.resolve_model_path(os.environ.get("BLORIDIUM_MODEL"))
    return matching.SIMILARITY_VERSION if mpath else matching.PLACEHOLDER_VERSION


def _score_note() -> str:
    mpath = matching.resolve_model_path(os.environ.get("BLORIDIUM_MODEL"))
    if mpath:
        return (f'similarity v{matching.SIMILARITY_VERSION} &ndash; random-forest prognosis '
                f'(model <code>{escape(mpath.name)}</code>, trained on A/B measurements, '
                'see docs/HANDOVER-2026-11-19-rf-dataset.md)')
    return (f'similarity v{matching.PLACEHOLDER_VERSION} &ndash; deterministic placeholder '
            '(no trained model found; set BLORIDIUM_MODEL to enable the RF prognosis)')


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("MAX_UPLOAD_MB", "8")) * 1024 * 1024
    app.data_dir = Path(os.environ.get("DATA_DIR") or (Path(__file__).parent / "data"))
    app.data_dir.mkdir(parents=True, exist_ok=True)
    app.ttl_hours = float(os.environ.get("DATA_TTL_HOURS", "24"))

    def page(body: str) -> str:
        return PAGE.format(conv=convert.CONVERSION_VERSION, body=body)

    def cleanup():
        cutoff = time.time() - app.ttl_hours * 3600
        for d in app.data_dir.iterdir():
            if d.is_dir() and d.stat().st_mtime < cutoff:
                for f in d.iterdir():
                    f.unlink(missing_ok=True)
                d.rmdir()

    @app.before_request
    def _cleanup():
        cleanup()

    @app.errorhandler(413)
    def too_large(e):
        return page(f'<p class="err">Upload too large '
                    f'(limit {app.config["MAX_CONTENT_LENGTH"] // 1024 // 1024} MB).</p>'
                    f'<p><a href="/">back</a></p>'), 413

    @app.get("/")
    def index():
        return page(index_body(_score_note()))

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
        p = app.data_dir / token / "result.zip"
        if not p.exists():
            abort(404)
        return send_file(p, as_attachment=True, download_name=_zip_name(app.data_dir / token))

    @app.get("/report/<token>")
    def report_json(token):
        if not TOKEN_RE.fullmatch(token):
            abort(404)
        p = app.data_dir / token / "report.json"
        if not p.exists():
            abort(404)
        return send_file(p, mimetype="application/json")

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
            f"<td>{s['mapped']}</td><td>{len(s['unmapped'])}</td></tr>")
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
<p><a href="/download/{report['token']}"><button>Download ZIP ({escape(report['zip_name'])})</button></a>
   <a href="/report/{report['token']}">report.json</a></p>
<table><tr><th>Loc</th><th>Name</th><th>Category</th><th>Score</th><th></th>
<th>mapped</th><th>unmapped</th></tr>
{''.join(rows)}
</table>
{('<p class="err"><b>Errors:</b></p><ul>' + errs + '</ul>') if errs else ''}
<p><a href="/">Convert another file</a></p>
{footer(report.get('similarity_version', '').lstrip('v'))}
"""


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
