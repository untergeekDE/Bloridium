"""Spike (throwaway): kann gemma4:12b-it-qat ein spec-pair PNG (A|B|delta) als
vision model strukturiert klassifizieren? Offline, synthetische Signale.

Run: python3 scripts/spike_specdiff_gemma4.py
"""
import base64
import json
import sys
import urllib.request
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bloridium.sim_embed import render_spec_pair_png  # noqa: E402

SR = 48000
OUT = Path(__file__).resolve().parent.parent / "recordings" / "spike_specdiff"
OUT.mkdir(parents=True, exist_ok=True)


def synth(dur=2.0):
    t = np.arange(int(SR * dur)) / SR
    a = sum((1.0 / k) * np.sin(2 * np.pi * 110 * k * t) for k in range(1, 9))
    a += 0.05 * np.random.default_rng(1).standard_normal(t.size)
    b = a.copy()
    # B lauter in den Hoehen (ab 4 kHz) zwischen 0.5-1.5 s -> "punctual, high, temporal multiple"
    tt = t[(t >= 0.5) & (t <= 1.5)]
    hi = np.zeros_like(t)
    for k in range(40, 60):
        hi += np.sin(2 * np.pi * 110 * k * t)
    mask = ((t >= 0.5) & (t <= 1.5)).astype(float)
    b = b + 0.8 * hi * mask + 0.05 * np.random.default_rng(2).standard_normal(t.size)
    return a, b


def ask_vision(png: Path, model="gemma4:12b-it-qat"):
    prompt = (
        "The image shows a spectrogram comparison, three panels left to right: "
        "A = original (Blofeld), B = converted (Iridium), delta = B - A in dB "
        "(blue = B quieter, gray = 0, red = B louder). x = time, y = frequency (log).\n"
        "Classify the delta panel and answer with ONLY a JSON object, no prose:\n"
        '{"severity": "light|medium|heavy", "spread": "even|punctual", '
        '"temporal": "even|periodical|single|multiple|increasing|decreasing", '
        '"bands": ["low"|"mid"|"high" (list of those affected)], '
        '"summary": "one sentence"}'
        "\nlow < 250 Hz, mid 250-2000 Hz, high > 2000 Hz."
    )
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt,
                      "images": [base64.b64encode(png.read_bytes()).decode()]}],
        "options": {"temperature": 0.0, "num_predict": 300},
        "stream": False,
    }
    req = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())["message"]["content"]


if __name__ == "__main__":
    a, b = synth()
    png = render_spec_pair_png(a, b, SR, OUT / "spike_pair.png")
    print("png:", png, png.stat().st_size, "bytes")
    txt = ask_vision(png)
    print("raw answer:", txt[:600])
    try:
        js = json.loads(txt[txt.index("{"):txt.rindex("}") + 1])
        print("parsed OK:", json.dumps(js, indent=1))
    except Exception as e:
        print("PARSE FAIL:", e)
