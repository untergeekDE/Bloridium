#!/usr/bin/env python3
"""fetch_models.py – download Phase-B models (idempotent, starts no server).

- CLAP-GGUF (Q8_0) to models/ via huggingface_hub (skip if present)
- `ollama pull <model>` (default lfm3-omni:2b; ollama serve must run separately)
- optional `--pip-clap-cpp`: pip install clap-cpp (Python binding for the embedding)

Usage:  python3 scripts/fetch_models.py [--models-dir D] [--ollama-model M]
         [--skip-ollama] [--pip-clap-cpp]
Exit: 0 ok, 1 on error.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bloridium import sim_embed

CLAP_REPO = "gorse-io/larger_clap_music_and_speech-GGUF"


def _hf_download(models_dir: Path) -> Path:
    from huggingface_hub import hf_hub_download
    return Path(hf_hub_download(CLAP_REPO, sim_embed.CLAP_GGUF_NAME,
                                local_dir=str(models_dir)))


def _run(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    return subprocess.run(cmd).returncode


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--models-dir", default=str(sim_embed.DEFAULT_MODELS_DIR))
    ap.add_argument("--ollama-model", default=sim_embed.DEFAULT_OLLAMA_MODEL)
    ap.add_argument("--skip-ollama", action="store_true")
    ap.add_argument("--pip-clap-cpp", action="store_true")
    args = ap.parse_args(argv)

    models_dir = Path(args.models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)
    gguf = models_dir / sim_embed.CLAP_GGUF_NAME
    ok = True

    if gguf.exists():
        print(f"GGUF present (skip): {gguf}")
    else:
        try:
            p = _hf_download(models_dir)
            print(f"GGUF downloaded: {p}")
        except Exception as e:
            print(f"ERROR GGUF download: {e}", file=sys.stderr)
            ok = False

    if not args.skip_ollama:
        if _run(["ollama", "pull", args.ollama_model]) != 0:
            print("ERROR ollama pull", file=sys.stderr)
            ok = False

    if args.pip_clap_cpp:
        if _run([sys.executable, "-m", "pip", "install", "clap-cpp"]) != 0:
            print("ERROR pip install clap-cpp", file=sys.stderr)
            ok = False

    print("OK" if ok else "ERROR")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
