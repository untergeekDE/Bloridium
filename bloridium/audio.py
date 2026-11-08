"""Audio-Aufnahme & -Messung über das Focusrite Scarlett 18i8 (macOS, ffmpeg/AVFoundation).

Kanalbelegung (siehe CLAUDE.md), 0-basiert:
- Blofeld  -> Scarlett-Eingänge 3/4  -> Kanäle c2/c3
- Iridium  -> Scarlett-Eingänge 5/6  -> Kanäle c4/c5
"""

from __future__ import annotations

import subprocess
import time

import numpy as np

DEVICE = "Scarlett 18i8 USB"
SAMPLERATE = 48000

# Scarlett-Eingänge pro Synth (0-basierte Kanalindizes im 20-Kanal-Stream)
CHANNELS = {
    "blofeld": (2, 3),   # Eingänge 3/4
    "iridium": (4, 5),   # Eingänge 5/6
}


def _pan_filter(channels) -> str | None:
    """ffmpeg-pan-Filter für die gewünschten Kanäle; None = alle Kanäle 1:1."""
    if channels is None:
        return None
    n = len(channels)
    if n >= 16:  # pan kennt keine Layouts > 8 Kanäle -> roh aufnehmen und in numpy slicen
        return None
    layout = f"{n}c" if n > 1 else "mono"
    mapping = "|".join(f"c{i}=c{ch}" for i, ch in enumerate(channels))
    return f"pan={layout}|{mapping}"


def record(duration: float = 2.0, channels=(2, 3), device: str = DEVICE,
           samplerate: int = SAMPLERATE, raw_channels: int = 20) -> np.ndarray:
    """Nimmt `duration` Sekunden von den Scarlett-Eingängen auf.

    `channels`: 0-basierte Kanalindizes, die zurückgegeben werden sollen
                (None = alle Kanäle des Geräts).
    Rückgabe: float32-ndarray der Form (len(channels), samples), Werte in [-1, 1].
    """
    sel = tuple(channels) if channels is not None else tuple(range(raw_channels))
    pan = _pan_filter(sel if len(sel) < 16 else None)
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-f", "avfoundation", "-i", f":{device}",
        "-t", f"{duration:.3f}",
    ]
    if pan:
        cmd += ["-af", pan]
    cmd += ["-ar", str(samplerate), "-f", "f32le", "-"]
    last_err = ""
    for _attempt in range(4):  # AVFoundation gibt das Device manchmal nicht sofort frei
        proc = subprocess.run(cmd, capture_output=True)
        if proc.returncode == 0:
            break
        last_err = proc.stderr.decode(errors="replace")
        time.sleep(1.0)
    else:
        raise RuntimeError("ffmpeg-Fehler: " + last_err)
    data = np.frombuffer(proc.stdout, dtype=np.float32)
    if pan:
        # pan hat bereits genau die gewuenschten Kanaele in Reihenfolge geliefert
        n_in = len(sel)
        if data.size % n_in:
            data = data[: data.size - (data.size % n_in)]
        return data.reshape(-1, n_in).T.copy()
    # roher Stream mit allen Geraetekanaelen -> gewuenschte spalten slicen
    if data.size % raw_channels:
        data = data[: data.size - (data.size % raw_channels)]
    data = data.reshape(-1, raw_channels)
    return data[:, list(sel)].T.copy()


def record_wav(path, duration: float = 2.0, channels=(2, 3), device: str = DEVICE,
               samplerate: int = SAMPLERATE) -> None:
    """Wie `record`, speichert aber eine WAV-Datei (16 Bit)."""
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "avfoundation", "-i", f":{device}",
        "-t", f"{duration:.3f}",
        "-af", _pan_filter(channels),
        "-ar", str(samplerate),
        "-c:a", "pcm_s16le", str(path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def measure(x: np.ndarray) -> dict:
    """Pegelmessung pro Kanal: RMS und Peak (linear + dBFS).

    x: Array der Form (channels, samples) oder (samples,).
    """
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = x[None, :]
    rms = np.sqrt(np.mean(x ** 2, axis=1)) if x.size else np.zeros(x.shape[0])
    peak = np.max(np.abs(x), axis=1) if x.size else np.zeros(x.shape[0])

    def dbfs(v):
        return np.where(v > 0, 20 * np.log10(np.maximum(v, 1e-12)), -np.inf)

    return {"rms": rms, "peak": peak, "rms_dbfs": dbfs(rms), "peak_dbfs": dbfs(peak)}


def play_and_measure(synth, channels, note: int = 60, velocity: int = 100, channel: int | None = None,
                     duration: float = 2.0, pre_roll: float = 0.3, **rec_kw):
    """Spielt eine Note auf dem Synth und misst dabei den Pegel am Scarlett.

    Sendet note_on, wartet `pre_roll` s (ffmpeg-Start), nimmt `duration` s auf
    und sendet danach note_off. `channel=None` -> Standardkanal des Synth-Objekts.
    Rückgabe: (samples, measure-Ergebnis).
    """
    ch = synth.channel if channel is None else channel
    synth.note_on(note=note, velocity=velocity, channel=ch)
    try:
        time.sleep(pre_roll)
        data = record(duration=duration, channels=channels, **rec_kw)
    finally:
        synth.note_off(note=note, channel=ch)
    return data, measure(data)
