"""Audio recording & measurement via the Focusrite Scarlett 18i8 (macOS, ffmpeg/AVFoundation).

Channel assignment (see CLAUDE.md), 0-based:
- Blofeld  -> Scarlett inputs 3/4  -> channels c2/c3
- Iridium  -> Scarlett inputs 5/6  -> channels c4/c5
"""

from __future__ import annotations

import subprocess
import time

import numpy as np

from . import config as _config

# Built-in defaults (single source of truth: config.DEFAULTS; the user-editable
# bloridium.yaml overrides them at runtime - see settings()).
DEVICE = _config.DEFAULTS["audio"]["device"]       # "Scarlett 18i8 USB"
SAMPLERATE = _config.DEFAULTS["audio"]["samplerate"]  # 48000

# Audio interface inputs per synth (0-based channel indices in the raw stream)
CHANNELS = {k: tuple(v) for k, v in _config.DEFAULTS["audio"]["channels"].items()}


def settings(config_path=None) -> dict:
    """Effective audio settings: YAML config (bloridium.yaml) over built-in defaults.

    Returns {"device", "samplerate", "raw_channels", "channels": {synth: [..]}}.
    """
    return _config.audio_settings(_config.load_config(config_path))


def _pan_filter(channels) -> str | None:
    """ffmpeg pan filter for the desired channels; None = all channels 1:1."""
    if channels is None:
        return None
    n = len(channels)
    if n >= 16:  # pan has no layouts > 8 channels -> record raw and slice in numpy
        return None
    layout = f"{n}c" if n > 1 else "mono"
    mapping = "|".join(f"c{i}=c{ch}" for i, ch in enumerate(channels))
    return f"pan={layout}|{mapping}"


def record(duration: float = 2.0, channels=(2, 3), device: str | None = None,
           samplerate: int | None = None, raw_channels: int | None = None,
           config_path=None) -> np.ndarray:
    """Records `duration` seconds from the audio interface inputs.

    `channels`: 0-based channel indices to return
                (None = all channels of the device).
    `device`/`samplerate`/`raw_channels`: None = take from the YAML config
    (bloridium.yaml) or the built-in defaults.
    Returns: float32 array of shape (len(channels), samples), values in [-1, 1].
    """
    s = settings(config_path)
    device = device if device is not None else s["device"]
    samplerate = samplerate if samplerate is not None else s["samplerate"]
    raw_channels = raw_channels if raw_channels is not None else s["raw_channels"]
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
    to = duration + 20.0   # Timeout: ffmpeg/AVFoundation kann sonst ewig hängen (2026-11-20)
    for _attempt in range(4):  # AVFoundation sometimes does not release the device immediately
        try:
            proc = subprocess.run(cmd, capture_output=True, timeout=to)
        except subprocess.TimeoutExpired:
            last_err = f"ffmpeg timeout (>{to:.0f}s) — Aufnahme hing"
            time.sleep(1.0)
            continue
        if proc.returncode == 0:
            break
        last_err = proc.stderr.decode(errors="replace")
        time.sleep(1.0)
    else:
        raise RuntimeError("ffmpeg error: " + last_err)
    data = np.frombuffer(proc.stdout, dtype=np.float32)
    if pan:
        # pan already delivered exactly the desired channels in order
        n_in = len(sel)
        if data.size % n_in:
            data = data[: data.size - (data.size % n_in)]
        return data.reshape(-1, n_in).T.copy()
    # raw stream with all device channels -> slice the desired columns
    if data.size % raw_channels:
        data = data[: data.size - (data.size % raw_channels)]
    data = data.reshape(-1, raw_channels)
    return data[:, list(sel)].T.copy()


def record_wav(path, duration: float = 2.0, channels=(2, 3), device: str | None = None,
               samplerate: int | None = None, config_path=None) -> None:
    """Like `record`, but saves a WAV file (16 bit). None args come from the YAML config."""
    s = settings(config_path)
    device = device if device is not None else s["device"]
    samplerate = samplerate if samplerate is not None else s["samplerate"]
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "avfoundation", "-i", f":{device}",
        "-t", f"{duration:.3f}",
        "-af", _pan_filter(channels),
        "-ar", str(samplerate),
        "-c:a", "pcm_s16le", str(path),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=duration + 20.0)
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"ffmpeg timeout (>{duration + 20.0:.0f}s) — Aufnahme hing") from e


def measure(x: np.ndarray) -> dict:
    """Level measurement per channel: RMS and peak (linear + dBFS).

    x: array of shape (channels, samples) or (samples,).
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
    """Plays a note on the synth and measures the level at the Scarlett.

    Sends note_on, waits `pre_roll` s (ffmpeg startup), records `duration` s,
    then sends note_off. `channel=None` -> default channel of the synth object.
    Returns: (samples, measure result).
    """
    ch = synth.channel if channel is None else channel
    synth.note_on(note=note, velocity=velocity, channel=ch)
    try:
        time.sleep(pre_roll)
        data = record(duration=duration, channels=channels, **rec_kw)
    finally:
        synth.note_off(note=note, channel=ch)
    return data, measure(data)
