#!/usr/bin/env python3
"""Step 2c: parse the saved Blofeld SNDD and print it as a parameter list.

Wrapper around bloridium.workflow (argv/exit/stdout unchanged).

Usage:  python3 scripts/step2_parse_blofeld_dump.py [dumps/blofeld_sndd_*.bin]
"""

from __future__ import annotations

import glob
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bloridium import blofeld_dump as bd
from bloridium import workflow


def main() -> int:
    if len(sys.argv) > 1:
        files = [sys.argv[1]]
    else:
        files = sorted(glob.glob(str(workflow.DUMPS / "blofeld_sndd_*.bin")))
    if not files:
        print("No dump found – run scripts/step2_read_blofeld_dump.py first.")
        return 1
    path = files[-1]
    raw = workflow.load_sndd_file(path)
    r = bd.parse_sndd(raw)
    print(f"File  : {path}")
    print(f"BB/NN : 0x{r['bb']:02X} 0x{r['nn']:02X}  (7F 00 = sound-mode edit buffer)")
    print(f"CHK   : 0x{r['chk']:02X}  ok={r['chk_ok']}")
    print(f"Name  : {r['name']!r}")
    print(f"SDATA : {len(r['sdata'])} bytes, {len(r['params'])} named parameters\n")
    for name, val in r["params"].items():
        print(f"  {name:32s} = {val}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
