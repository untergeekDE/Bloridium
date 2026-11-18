# Design: `bloridium explore` – OS4 pid exploration on the Iridium (NRPN capture)

Date: 2026-11-12
Status: draft for approval

## Intent & Why

The user wants to know which **OS4 pids** the Iridium actually sends when you turn a panel
control – the rdb-2023 pids in `docs/midi-maps/iridium_os4_cc_list.csv` are **unverified** on OS4
(observed deviations: 1024/1027/1045/1046/1055,
3113 on sound change; see HANDOVER-2026-11-09/10, plan point 2 and open
points). For that, a program should say **which parameter to turn next**, and then **record
pid + value via NRPN** and assign it to the parameter.

That is the data basis for the step after next: a working
OS4 `.mimap` and with that **the Iridium as an editor for the Blofeld**
(Blofeld CC → Iridium pid, see `zugehoeriger_blofeld_param` in the CSV).

User decision (2026-11-12): **approach B – one interactive session,
state directly in the CSV** (see Approaches).

## Goals

- New subcommand `bloridium explore` (interactive; the Phase-1 CLI style stays argparse;
  the interactivity is deliberate and wanted here – a loop of prompt + recording).
- List of parameters to explore: `docs/midi-maps/iridium_os4_cc_list.csv`,
  filtered to `os4_verified == "nein"`, sorted: `essential=yes` first, then
  `nutzung_pct` descending, then `cc` ascending. Filters: `--essential`,
  `--grep PAT`, `--only-cc 0,2,7`.
- Per parameter: prompt "turn the panel now, then Enter"; afterwards decode the NRPN capture
  (pid + 14-bit value), book it into the CSV and append to
  `recordings/explore_log.jsonl`. Immediate save after each booking
  (crash-safe, resumable: a new run continues with the still-open ones).
- `--list` shows the verification status of all 116 CCs (also `--json`).
- Read-only: the tool **sends no MIDI** (the Iridium ignores incoming NRPN
  anyway; the CC7=0-silence danger is thereby completely eliminated).

## Non-Goals

- **No .mimap emit** in this step (was approach C, not chosen): CSV + JSONL
  are the data basis; `.mimap`/editor mapping is generated from them later.
- No MIDI sending (no CC test, no PC), no audio, no notes.
- No change to other subcommands; `scripts/monitor_live.py` stays unchanged
  (manual capture still possible).
- No SQLite DB for the explore state – files remain the source of truth
  (consistent with the CLI design 2026-11-08).

## Anti-Goals

- The existing 8 CSV columns (`cc,pid,iridium_param,zugehoeriger_blofeld_param,
  nutzung_pct,essential,pid_quelle,os4_verified`) remain **unchanged and in
  this order**; new columns are only **appended** (nothing reads the CSV
  programmatically today, only humans – checked 2026-11-12).
- No new runtime dependencies (stdlib + mido, as before).
- No live MIDI in tests.

## Constraints (empirically verified)

- **NRPN format** (capture `recordings/midi_monitor_20261109_090256.log`,
  Iridium USB ports, channel B5 = ch6 = Part 1): a panel turn sends
  `CC99 (0x63) = pid MSB`, `CC98 (0x62) = pid LSB`, `CC6 = value MSB`,
  `CC38 (0x26) = value LSB`. Example `63 18 / 62 29 / 06 7F / 26 7F`
  → pid `(0x18<<7)|0x29 = 3113`, value `(0x7F<<7)|0x7F = 16383` (sound change).
  → Decode: `pid = (cc99<<7)|cc98`, `value = (cc6<<7)|cc38` (14-bit).
  `CC99/CC98 = 127` = NRPN off (reset); `CC121` (Reset All Controllers) resets
  the NRPN state; `CC101/100` (RPN) are ignored.
- **Port/channel today:** the Iridium is on the Launchpad DIN
  (`midi.DEFAULT_PORTS["iridium"]["in"]` = "Launchpad Pro MK3 LPProMK3 DIN"),
  the Iridium USB is **off** because of the ground loop. NRPN comes on the Part-1 channel
  ch6 (0-based 5). Default `--channel 5`.
- On the Iridium **Global > MIDI = on** and **Send NRPN = on**
  must be set (OS manual: "Iridium doesn't react on incoming NRPN" – the exploration is
  exclusively outgoing-reading).
- One panel turn produces **several NRPN** (value sweep) → book min/max/last,
  all values into the log. Pid 3113 (sound change) can occur – it is
  booked normally (most frequent pid wins, all in the log).
- Environment: macOS (CoreMIDI), Python ≥ 3.10, mido.

## Approaches

- **A – two commands (`explore next` / `explore capture`), state in JSON:**
  more flexible between the steps, but more typing, state drift.
  *Not chosen (2026-11-12).*
- **B – one interactive session, state directly in the CSV (CHOSEN 2026-11-12):**
  `bloridium explore` works through the open parameters in a loop
  (prompt → panel turn → Enter → record NRPN → book → next).
  The CSV is the only state → resumable, crash-safe (save after each booking),
  human-readable. *Chosen.*
- **C – session like B plus direct .mimap emit:** biggest immediate benefit, but two
  jobs in one tool. *Not chosen;* emit comes as its own command once
  the CSV data basis exists.

## How

### Layout

- `bloridium/explore.py` – pure, hardware-free logic (testable):
  - `NrpnDecoder.feed(msg) -> NrpnEvent | None` (state machine over mido messages,
    see Constraints); `NrpnEvent = (pid, value14)`.
  - `NEW_COLUMNS = ["pid_os4", "nrpn_min", "nrpn_max", "nrpn_last", "explore_ts", "explore_msgs"]`
  - `load_cc_list(path) -> (fieldnames, rows)` – missing new columns = `""`.
  - `save_cc_list(path, fieldnames, rows, backup=False)` – appends new columns;
    `backup=True` creates `iridium_os4_cc_list.csv.bak` once per session.
  - `pending_rows(rows, essential, grep, only_cc) -> rows` (filter + sorting).
  - `book_row(row, events, ts) -> dict` – sets `pid_os4` (most frequent pid =
    winner), `nrpn_min/max/last` **over the events of the winning pid**,
    `explore_msgs` = **number of NRPN events of the winning pid** (int),
    `explore_ts`, `os4_verified="ja"`;
    `abweichung = (pid_os4 != pid)` for the log.
  - `append_log(log_path, entry)` – one JSON line per capture.
- `bloridium/cli.py` – `cmd_explore(args)`:
  - Flags: `--csv PATH` (default `docs/midi-maps/iridium_os4_cc_list.csv`),
    `--log PATH` (default `recordings/explore_log.jsonl`),
    `--essential`, `--grep PAT`, `--only-cc 0,2,7`, `--list`, `--json`,
    `--port NAME` (default `midi.DEFAULT_PORTS["iridium"]["in"]`),
    `--channel N` (default 5), `--listen S` (default 1.5 s of silence = end of capture).
  - `--list`: table `cc | iridium_param | pid(rdb) | os4_verified | pid_os4 |
    nrpn_last` (+ `--json`); needs no MIDI.
  - Session: open MIDI in (exit 2 + port list if unreachable) →
    compute pending → loop:
    1. Progress `[verified X/116]` + next parameter output:
       `CC{cc}  {iridium_param}` / `expected rdb pid {pid}` /
       `Blofeld counterpart: {zugehoeriger_blofeld_param} ({nutzung_pct}%, essential={essential})`.
    2. Clear the input buffer, prompt: `Turn the panel now, then Enter  [s=skip without booking, q=quit]`.
       `q`/EOF/Ctrl+C → clean exit (state is already booked), exit 0.
       `s` → next parameter, without state change.
    3. Enter → capture: `Synth.receive()` loop until `--listen` s without a new
       message; feed the decoder, CCs are counted/logged (if a .mimap
       is loaded and the panel additionally sends CC).
    4. Events empty → **stay on the same parameter** (Enter again = capture again;
       `s`/`q` as before), but with a differentiated diagnosis:
       - no MIDI message received on the port at all → hint: "Global > MIDI
         = on? Send NRPN = on? Plug in the Iridium USB briefly and set
         `--port` (DIN possibly delivers no panel NRPN – see builder-check Q1)?"
       - messages received, but no NRPN among them → hint: "Send NRPN = on?
         right part/channel (default ch6 = Part 1)?"
       - NRPN only seen on **another channel** → hint with the observed
         channel ("NRPN came on ch{N} – `--channel {N-1}`?").
       Messages on other channels are neither decoded nor booked
       (the DIN port otherwise also carries the Blofeld on ch5).
    5. Events present → `book_row`, `append_log` (ts, cc, iridium_param,
       pid_rdb, pid_os4, abweichung, nrpn_min/max/last, n_msgs, werte, cc_gesehen,
       port, channel), save CSV (with a one-time `.bak` at session start),
       print the result: `Pid {pid_os4}` + **`DEVIATION from rdb pid {pid}`**
       on deviation + `values {min}..{max} (last {last}), {n} NRPNs`.
    6. next parameter; list empty → "all captured parameters verified", exit 0.
  - Exit codes consistent with the CLI design: 0 ok, 1 error, 2 hardware unreachable.

### Example session (output sketch)

```
bloridium explore --essential
[0/116 verified]  next: CC0  Filter1 Cutoff
  expected rdb pid 966  |  Blofeld counterpart: Filter 1 Cutoff (93.8%, essential)
Turn the panel now, then Enter  [s=skip, q=quit]
> <Enter>
  NRPN: Pid 1024  *** DEVIATION from rdb pid 966 ***  values 0..16383 (last 8712), 14 NRPNs
  booked: iridium_os4_cc_list.csv (os4_verified=ja, pid_os4=1024) + recordings/explore_log.jsonl
[1/116 verified]  next: CC2  Filter1 Reso ...
```

### Tests (`tests/test_explore.py`, offline, no live MIDI)

- NRPN decoder against the capture from `recordings/midi_monitor_20261109_090256.log`
  (`63 18/62 29/06 7F/26 7F` → pid 3113, value 16383), multiple values, reset cases
  (CC99/98=127, CC121), RPN CCs ignored.
- CSV load/save roundtrip on `tmp_path`: column append, `.bak`,
  `pending_rows` (filter essential/grep/only-cc, sorting nutzung_pct).
- `book_row` + `append_log` (JSONL one line, abweichung flag).
- CLI smoke with monkeypatched `midi.connect` (fake synth with `receive()` queue)
  and monkeypatched `input` (`["", "q"]`): session books into tmp CSV, appends the log,
  prints DEVIATION; `--list` (text + `--json`); no in-port → exit 2.

## Builder-Check (subagent 2026-11-12)

Builder's questions, sorted:

- **Q1 (to the user – hardware fact):** does the **Launchpad DIN**
  really deliver panel NRPN, or did the NRPN capture only come via the Iridium **USB**
  ports (USB was briefly on on 2026-11-09; currently off because of the ground loop)?
  Default stays DIN with `--port` override; an empty first capture gets a
  targeted USB hint (see How, step 4). The user's answer follows before approval.
- **Q2 (decision, builder-callable):** strictly filter the channel (default ch6 /
  0-based 5 = Part 1, `--channel` override); prompt hint "Part 1 active on the Iridium?". Anchored in How.
- **Q3 (decision):** `explore_msgs` = number of NRPN events of the winning pid (int).
  Anchored in How.
- **Q4 (decision):** diagnose empty captures in three levels (nothing received /
  only CC / NRPN on another channel) with targeted hints. Anchored in How, step 4.
- **Q5 (decision):** `nrpn_min/max/last` only over winning-pid events; all events
  (all pids) into the JSONL log. Anchored in How.

## What's left to the builder

- Exact prompt/table texts (plain text, no colors – consistent with the CLI).
- Capture loop: reuse `Synth.receive(timeout=...)` from `midi.py`.
- Several different pids in one capture: most frequent wins, all into the log.
- Whether `--listen` should also serve as "max. total duration of the capture" (proposal: only silence-end, total duration = unlimited until Enter-silence).
