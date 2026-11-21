# Skills

Agent skills shipped with this repo (see `README.md` → "Optimised for agentic use").
Point your agent at this folder, or copy the skill into your runtime's skills
directory:

- **OpenCode**: add `"skills": ["./skills"]` to `opencode.json` in the repo root, or
  copy `skills/bloridium/` to `.opencode/skills/bloridium/` (project-local,
  gitignored) or `~/.config/opencode/skills/bloridium/` (global).
- **Claude Code / Codex / Gemini / …**: copy `skills/bloridium/` to
  `.claude/skills/bloridium/` (project) or to the user-global location
  `~/.claude/skills/bloridium/` resp. the cross-runtime alias
  `~/.agents/skills/bloridium/`.

Skill ID after install: `bloridium`.

## bloridium

`bloridium/SKILL.md` — the complete Bloridium workflow: read sounds from a Waldorf
Blofeld (documented SysEx, spec v1.04), convert them to Waldorf Iridium `.qpat`
files, transfer via USB stick/SD card, select sounds with MIDI program change
(Favorites), tweak parameters live over MIDI CC, and measure the Blofeld-vs-Iridium
similarity (A/B recordings + score 0–100, specdiff, prognosis).

The skill deliberately covers **only documented device interfaces** — Blofeld SysEx
per the official spec, Iridium MIDI CC / program change / notes and `.qpat` files.
The Iridium has no documented SysEx layer; patches reach it only as `.qpat` files on
a transfer medium.
