# Ziel

Eine Suite von Utilities und Skills, um Synthesizer-Programme von einem
Synthesizer (Blofeld) auf einen anderen (Iridium) zu übertragen.

Nutze den ähnlichen Aufbau und entwickle Tools, um Unterschiede im Klang
zu messen und durch Detailkorrekturen anzugleichen.

## Beschreibung

Iridium-Synthesizer ist Nachfolger Blofeld-Synthesizer. Es gibt Ähnlichkeiten:
- 3 Oszillatoren
- Wavetable- und VA-Synthese
- 2 Filter
- Modulationsmatrix

Unterschiede: Iridium
- Zusätzliche Synthesemodelle

## Hardware (verifiziert, Stand: aktuelle Runde)

- Waldorf Iridium Keyboard Synthesizer mit SOM2 Upgrade
- Waldorf Blofeld Synthesizer mit SL Sampling License (Firmware 1.24)
- Focusrite Scarlett 18i8 Audio Interface (USB, 20 Eingänge @ 48 kHz)
	- Iridium verbunden mit Eingang 5/6
	- Blofeld verbunden mit Eingang 3/4
- Beide Synths **direkt per USB am Mac** (primärer MIDI-Weg, Launchpad abgeschaltet):
	- Blofeld: CoreMIDI-Port `Blofeld` (bidirektional; Identity Reply: Hersteller `3E`, Modell `13`, FW 1.24); Global Channel = **MIDI-Kanal 5**; **SINGLE MODE aktiv** (umgeschaltet via Shift+Sound/Multi; verifiziert: nur Kanal 5 antwortet). Achtung: Modus ist per Kanal-Scan NICHT allein erkennbar, da Multi-Parts auf beliebigen Kanälen liegen dürfen.
	- Iridium: USB-Endpunkt `Iridium Keyboard (MIDI 2.0) MIDI 2.0` (MIDI-1.0-Bytes werden als UMP zugestellt); Parts 1-4 auf **MIDI-Kanal 6-9**. Der Endpunkt `Synth` empfängt derzeit nichts.
- Novation Launchpad Pro 3 nur als **Fallback** (MIDI-Interface per DIN, falls USB nicht greift; abgeschaltet):
	- Iridium MIDI Out -> Launchpad MIDI In
	- Launchpad MIDI Out2 -> Blofeld MIDI In
	- CoreMIDI-Port `Launchpad Pro MK3 LPProMK3 DIN` (Blofeld antwortet dort auf Kanal 5, aber nur Out-Richtung nutzbar; Identity-Reply auf DIN ist das Launchpad selbst: `00 20 29`)

Hinweis: Blofeld zusätzlich per USB = mögliche USB-Erdschleife (derzeit ok).

## Manuals

`~/Nextcloud/AAA Musik/Manuals`:
- `Blofeld.pdf` (Bedienhandbuch, inkl. Multi Mode / SysEx-Dumps)
- `iridium_desk_kb_manual_os3.pdf`
- `Iridium_os4_SOMv2_manual.pdf` (SOM2: USB-Ports "Computer" / "USB CTRL")

## Verifizierte Messungen (Schritt 1: Verbindung + Sound messen)

`python3 scripts/step1_verify_connection.py` => beide "VERBUNDEN, Sound messbar":
- Blofeld: Note auf Kanal 5 -> Scarlett In 3/4, Peak ca. -17 dBFS
- Iridium: Note auf Kanal 6 (Part 1) -> Scarlett In 5/6, Peak ca. -28 dBFS

Blofeld-Kanaele/Mode: `python3 scripts/check_blofeld_mode.py`
(zeigt empfangende Kanaele + Identity + GLBD. Stand: SINGLE MODE aktiv, nur Kanal 5 antwortet.
Modus am Geraet aendern: Shift+Sound/Multi. Kanal-Scan erkennt den Modus NICHT allein,
da Multi-Parts auf beliebigen Kanaelen liegen duerfen. Release-Reste vorher per
All-Notes-Off beseitigen!)

## Prinzipien

- Frage nach, bevor du Hardware-Einstellungen am Geraet aenderst.
- Aufnahme immer ueber Scarlett 18i8 (Blofeld In 3/4, Iridium In 5/6), 48 kHz.
- Vor Kanal-Scans All Notes Off (CC123) auf allen Kanaelen + Release abwarten.
- Siehe `README.md` (Setup/Nutzung), `docs/FINDINGS.md` (alle Funde),
  `docs/STATUS.md` (Werkzeug-Inventar + Plan fuer die naechste Session).
