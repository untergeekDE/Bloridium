"""OS4-Pid-Exploration am Iridium: NRPN-Mitschnitt dekodieren + in die CC-Liste buchen.

Rein lesend – dieses Modul sendet kein MIDI. NRPN-Format (Mitschnitt
recordings/midi_monitor_20261109_090256.log, ch6 = Part 1):
  CC99 = Pid-MSB, CC98 = Pid-LSB, CC6 = Wert-MSB, CC38 = Wert-LSB (14-bit).
  CC99/CC98 = 127 -> NRPN aus (Reset); CC121 (Reset All Controllers) resetet alles;
  CC101/100 (RPN) werden ignoriert.
"""

from __future__ import annotations

# (pid, value14)
NrpnEvent = tuple[int, int]


class NrpnDecoder:
    """State-Machine ueber control_change-Messages eines gewaehlten Kanals.

    feed(msg) -> NrpnEvent, sobald Pid (CC99+CC98) und Wert (CC6+CC38) komplett
    sind; danach werden die Daten-Bytes zurueckgesetzt (Pid bleibt – der Dreh
    am selben Parameter liefert danach weitere Events ohne neues CC99/98).
    """

    def __init__(self) -> None:
        self._msb: int | None = None
        self._lsb: int | None = None
        self._dmsb: int | None = None
        self._dlsb: int | None = None

    def _reset_all(self) -> None:
        self._msb = self._lsb = self._dmsb = self._dlsb = None

    def feed(self, msg) -> NrpnEvent | None:
        if msg.type != "control_change":
            return None
        c, v = msg.control, msg.value
        if c == 99:                      # NRPN MSB (127 = NRPN aus)
            self._msb = None if v == 127 else v
        elif c == 98:                    # NRPN LSB (127 = NRPN aus)
            self._lsb = None if v == 127 else v
        elif c == 6:                     # Data MSB
            self._dmsb = v
        elif c == 38:                    # Data LSB
            self._dlsb = v
        elif c == 121:                   # Reset All Controllers
            self._reset_all()
            return None
        else:                            # inkl. CC101/100 (RPN): ignorieren
            return None
        if (self._msb is not None and self._lsb is not None
                and self._dmsb is not None and self._dlsb is not None):
            event = ((self._msb << 7) | self._lsb, (self._dmsb << 7) | self._dlsb)
            self._dmsb = self._dlsb = None
            return event
        return None
