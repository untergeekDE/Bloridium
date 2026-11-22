# Spec: Web app privacy page + one-time retention

Date: 2026-11-22

## Intent

The public Bloridium converter (`bloridium.frankruft.de`) must be able to
state truthfully what happens to an upload. The operator decided:

- uploads are **not used for training**;
- uploaded content and generated output are **deleted after conversion /
  delivery**.

The latter needs a code change: today `/data/<token>/` is kept for 24 h and
`report.json` contains a full parameter dump intended as training data.

## Goals

- Add a `/privacy` page linked from the footer (and a short note near the
  upload form).
- Promise and implement:
  - the uploaded file is processed in memory and never written to disk;
  - the generated ZIP/report is kept only for delivery, deleted immediately
    after the one-time download;
  - if never downloaded, it is deleted automatically after one hour;
  - no training on uploaded data.
- Keep server access/error logs, but truncate the client IP: keep the first
  three IPv4 octets and replace the last with `.xxx`; for IPv6 replace the last
  group with `:xxxx`.
- Remove the training payload (`features.params`) from `report.json` and the
  corresponding README/docstring claims.
- Make the download link one-time: after it has been served, the token
  directory is gone.

## Non-goals

- No change to the conversion/score algorithms.
- No accounts, cookies, analytics, or consent banner.
- No sound-count cap / rate limiting in this change (separate hardening, see
  `docs/FINDINGS.md`-style follow-up).
- No rewrite of historical specs/plans.

## Approaches considered

1. **One-time download + 1 h fallback** (chosen). Keeps the current results
   page; strongest honest promise without removing server storage entirely.
2. Short window (e.g. 1 h) with repeated downloads and a delete button. Weaker
   promise; more UI.
3. No server storage: stream the ZIP from memory in the upload response.
   Strongest privacy, but removes the results/download page and the
   convenience of re-downloading.

## Design

### Retention lifecycle

- `POST /upload` still writes `DATA_DIR/<token>/{result.zip,report.json}`.
- `GET /download/<token>` atomically renames the token dir to a unique
  `.<token>.<uuid>.sending` dir, opens `result.zip` with `send_file`, and
  deletes the renamed dir in `after_this_request(...)`.
  - A second concurrent/subsequent GET gets 404.
  - `send_file` opens the file before the response is returned; unlinking it
    immediately afterwards is safe on Unix/macOS (deployment is Linux). This
    is also testable with Flask's test client, unlike `call_on_close`.
  - If `send_file` raises, the renamed dir is removed immediately.
- `GET /report/<token>` and its link are removed; `report.json` remains inside
  the ZIP.
- A daemon cleanup thread in each worker deletes any directory older than
  `DATA_TTL_HOURS` every `CLEANUP_INTERVAL_S` seconds. This makes the one-hour
  promise independent of incoming traffic. Existing `before_request` cleanup
  stays as a cheap additional sweep.
- Defaults: `DATA_TTL_HOURS=1`, `CLEANUP_INTERVAL_S=30`. The thread can be
  disabled with `BLORIDIUM_CLEANUP_THREAD=0` (tests).
- Deployment files (`compose.yaml`, user unit, Quadlet) get
  `DATA_TTL_HOURS=1`.

### Report / training

- Remove `"features": {"params": ...}` from each sound in `report.json`.
- Keep the fields needed for the result page/MANIFEST: location, name,
  category, mapped/unmapped/ignored, score, std, matcher, score_parts,
  penalties.
- Update README + `convert.py`/`matching.py` docstrings: uploads are not used
  for training; the RF model is trained on the operator's own A/B recordings.
- `MANIFEST.md` stays inside the ZIP; it contains filename, timestamp and
  per-sound rows.

### Privacy page

`GET /privacy` with static HTML, linked as `Privacy` in the footer and
`Imprint` to `https://www.untergeek.de/cc/`. Content (English, matching the
UI):

- Controller: J. Eggers, Herbartstr. 17, D-60316 Frankfurt/M, Germany;
  contact via the Imprint page.
- Uploaded file: processed in memory, not stored.
- Generated ZIP/report: stored only to deliver the one-time download; deleted
  immediately after download, otherwise automatically after one hour.
- No training on uploaded data; the score model was trained on the operator's
  own measurements.
- No cookies, analytics, tracking, third-party fonts/CDNs; external links are
  only contacted when clicked.
- Server logs: truncated IP address (last IPv4 octet / IPv6 group replaced by
  `xxx`), time, requested path (including the random token), status, size,
  referer, user-agent; used for operation/security; rotated according to the
  server configuration.
- Legal basis: Art. 6(1)(b)/(f) GDPR; rights; complaint to the Hessian data
  protection authority.
- Score is an estimate, not an automated decision with legal effect.
- Download links are bearer links and work once.

The results page notes: "One-time download — the ZIP is deleted from the server
immediately after download (at the latest after one hour)."

### Anonymized Apache logs

The vhost derives a masked address with `mod_rewrite` and uses it in both log
formats:

```apache
RewriteEngine On
RewriteCond %{REMOTE_ADDR} "^(\d{1,3}\.\d{1,3}\.\d{1,3})\.\d{1,3}$"
RewriteRule ^ - [E=ANON_IP:%1.xxx]
RewriteCond %{REMOTE_ADDR} "^([0-9A-Fa-f:]*:)[0-9A-Fa-f]{1,4}$"
RewriteRule ^ - [E=ANON_IP:%1xxxx]

LogFormat "%{ANON_IP}e %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\"" bloridium_combined
CustomLog ${APACHE_LOG_DIR}/bloridium_access.log bloridium_combined
ErrorLogFormat "[%{u}t] [%{ANON_IP}e] [%-m:%l] [pid %P] %7F: %E: %M"
ErrorLog ${APACHE_LOG_DIR}/bloridium_error.log
```

Verified locally with Apache 2.4.67: the access log contains
`127.0.0.xxx` and the error-log format interpolates the same masked value
without `%a`. Requests are never logged with the full client address.

### Browser caching

Result pages/downloads get `Cache-Control: no-store` so converted data does
not remain in a shared browser cache.

## Risks / open points

- Exact Apache/logrotate and journald retention is server configuration, not
  in this repo. The page should either state "rotated regularly" or the
  operator supplies concrete periods.
- If the server is rented, the hosting provider should be named as a
  processor; the draft can say "hosting infrastructure used to operate this
  site".
- A crash between rename and `call_on_close` leaves a `.sending` directory;
  the cleanup thread removes it after the TTL. It is not reachable by token
  routes.

## Tests

- `GET /privacy` returns 200, contains "deleted", "not used for training",
  and the footer links to it.
- Upload → download once → 200; second download 404; token dir gone;
  `/report/<token>` 404.
- `report.json` no longer contains `features`.
- Cleanup deletes an old token dir and a stale `.sending` dir.
- Existing Flask/upload tests updated for the removed report link/features.
