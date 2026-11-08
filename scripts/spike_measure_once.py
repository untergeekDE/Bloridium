import sys, time
sys.path.insert(0, "/Users/jan/Code/Bloridium")
import numpy as np
from bloridium import midi, audio

def centroid(x, sr):
    x = np.asarray(x, dtype=np.float64)
    X = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    f = np.fft.rfftfreq(len(x), 1 / sr)
    return float((f * X).sum() / max(X.sum(), 1e-12))

irr = midi.connect("iridium")
for ch in range(16):
    irr.control_change(123, 0, channel=ch)
    irr.control_change(7, 127, channel=ch)
time.sleep(0.4)
irr.note_on(note=36, velocity=100, channel=5)   # Part 1 = MIDI ch6
time.sleep(0.2)
d = audio.record(duration=1.2, channels=None)
irr.note_off(note=36, channel=5)
irr.control_change(123, 0, channel=5)
x = np.asarray(d[list(audio.CHANNELS["iridium"]), :], dtype=np.float64).mean(axis=0)
sr = audio.SAMPLERATE
seg = x[int(0.5*sr):int(1.0*sr)]
peak = 20 * np.log10(max(np.max(np.abs(seg)), 1e-12))
print(f"IRR ch6 sustain[0.5-1.0s]: peak {peak:6.1f} dBFS  centroid {centroid(seg, sr):7.1f} Hz")
irr.close()
