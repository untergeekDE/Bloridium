"""Internal measurement helpers: verified Blofeld load + stereo/descriptor features.

Block 0 of the measurement plan: every SNDD dump is read back from the edit buffer
and byte-compared before it is used for a measurement.
"""
from __future__ import annotations

import time

import numpy as np

from bloridium import audio, blofeld_dump as bd, waldorf

SR = audio.SAMPLERATE
NOTE_HZ = 261.63  # C4


def load_sndd_actual(bl, sdata: bytes, retries: int = 3, wait: float = 0.35):
    """Send SNDD and return the SDATA the device actually holds (or None).

    The Blofeld normalises out-of-range values (e.g. Osc 3 Shape 18 -> 1), so a
    byte-identical readback is not always possible. Callers measure the *actual*
    state and record the effective value.
    """
    sdata = bytes(sdata)
    body = [0x3E, 0x13, 0x00, 0x10, 0x7F, 0x00, *sdata]
    body.append(bd.checksum(sdata))
    for _attempt in range(retries + 1):
        if bl.inp:
            while bl.inp.poll() is not None:
                pass
        bl.send_sysex(body)
        time.sleep(wait)
        bl.send_sysex(bd.build_sndr(0x7F, 0x00))
        deadline = time.time() + 2.0
        while time.time() < deadline:
            m = bl.inp.poll() if bl.inp else None
            if m is None:
                time.sleep(0.005)
                continue
            if m.type != "sysex":
                continue
            if waldorf.parse_sysex(m.data).get("cmd") != 0x10:
                continue
            return bd.parse_sndd(bytes([0xF0, *m.data, 0xF7]))["sdata"]
    return None


def load_sndd_verified(bl, sdata: bytes, retries: int = 2, wait: float = 0.35) -> bool:
    """Send SNDD to the edit buffer and verify it by reading the buffer back."""
    sdata = bytes(sdata)
    body = [0x3E, 0x13, 0x00, 0x10, 0x7F, 0x00, *sdata]
    body.append(bd.checksum(sdata))
    for _attempt in range(retries + 1):
        if bl.inp:
            while bl.inp.poll() is not None:
                pass
        bl.send_sysex(body)
        time.sleep(wait)
        bl.send_sysex(bd.build_sndr(0x7F, 0x00))
        deadline = time.time() + 2.0
        while time.time() < deadline:
            m = bl.inp.poll() if bl.inp else None
            if m is None:
                time.sleep(0.005)
                continue
            if m.type != "sysex":
                continue
            if waldorf.parse_sysex(m.data).get("cmd") != 0x10:
                continue
            got = bd.parse_sndd(bytes([0xF0, *m.data, 0xF7]))
            if got["sdata"] == sdata:
                return True
            break
    return False


def capture(bl, irr, note: int = 60, vel: int = 100, dur: float = 2.0,
            pre: float = 0.35) -> np.ndarray:
    """Play the same note on both synths, return all 20 channels."""
    for ch in range(16):
        bl.control_change(123, 0, channel=ch)
        bl.control_change(7, 127, channel=ch)
    irr.silence_part()
    time.sleep(0.05)
    bl.note_on(note=note, velocity=vel)
    irr.note_on(note=note, velocity=vel)
    try:
        time.sleep(pre)
        data = audio.record(duration=dur, channels=None)
    finally:
        bl.note_off(note=note)
        irr.note_off(note=note)
    return data


# ---- descriptors ---------------------------------------------------------

_BANDS = [(60, 180), (180, 500), (500, 1200), (1200, 2600), (2600, 5500), (5500, 12000)]


def _bands_db(x: np.ndarray) -> np.ndarray:
    X = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    f = np.fft.rfftfreq(len(x), 1 / SR)
    e = np.array([np.sqrt(np.sum(X[(f >= lo) & (f < hi)] ** 2)) for lo, hi in _BANDS])
    e = 20 * np.log10(e + 1e-12)
    return e - np.median(e)


def desc(x: np.ndarray) -> np.ndarray:
    """Compact, phase-insensitive descriptor: centroid, level, 6 relative bands."""
    x = np.asarray(x, dtype=np.float64)
    X = np.abs(np.fft.rfft((x - x.mean()) * np.hanning(len(x))))
    f = np.fft.rfftfreq(len(x), 1 / SR)
    cen = float((f * X).sum() / max(X.sum(), 1e-12))
    rms = float(np.sqrt(np.mean(x ** 2)))
    return np.concatenate([[np.log2(max(cen, 10) / 1000.0), 20 * np.log10(max(rms, 1e-9)) / 10],
                           _bands_db(x) / 10])


def pan_desc(L: np.ndarray, R: np.ndarray) -> np.ndarray:
    """Stereo descriptor: static balance, temporal pan movement, L/R timbre, level."""
    L = np.asarray(L, dtype=np.float64)
    R = np.asarray(R, dtype=np.float64)
    rl, rr = np.sqrt(np.mean(L ** 2)), np.sqrt(np.mean(R ** 2))
    pan_db = 20 * np.log10(max(rl, 1e-9) / max(rr, 1e-9))
    # temporal pan movement in 50 ms frames (auto-pan)
    n = min(len(L), len(R))
    fr = 2400
    series = []
    for i in range(0, n - fr, fr):
        a = np.sqrt(np.mean(L[i:i + fr] ** 2))
        b = np.sqrt(np.mean(R[i:i + fr] ** 2))
        series.append(20 * np.log10(max(a, 1e-9) / max(b, 1e-9)))
    pan_std = float(np.std(series)) if series else 0.0
    XL = np.abs(np.fft.rfft(L * np.hanning(len(L))))
    XR = np.abs(np.fft.rfft(R * np.hanning(len(R))))
    f = np.fft.rfftfreq(len(L), 1 / SR)
    cenL = float((f * XL).sum() / max(XL.sum(), 1e-12))
    cenR = float((f * XR).sum() / max(XR.sum(), 1e-12))
    lvl = 20 * np.log10(max(np.sqrt(np.mean(((L + R) / 2) ** 2)), 1e-9))
    return np.array([pan_db / 10, pan_std / 5,
                     np.log2(max(cenL, 10) / 1000), np.log2(max(cenR, 10) / 1000),
                     lvl / 10])


def classify(db, di, thr=2.0):
    mb, mi = float(np.linalg.norm(db)), float(np.linalg.norm(di))
    if mb < thr and mi < thr:
        return "n/a", mb, mi, None
    if mb < thr:
        return "Mismatch", mb, mi, None
    if mi < thr:
        return "defekt", mb, mi, None
    cos = float(np.dot(db, di) / (mb * mi))
    if cos >= 0.80 and 0.5 <= mi / mb <= 2.0:
        return "OK", mb, mi, cos
    if cos >= 0.50:
        return "teilweise", mb, mi, cos
    return "Mismatch", mb, mi, cos
