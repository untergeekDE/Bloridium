# Quellen-Dossier: rolfw (Rolf Wöhrmann, Waldorf) zum Fehlen einer SysEx-Schicht bei Quantum/Iridium

- **Recherche-Datum:** 2026-11-08
- **Projekt:** Bloridium (Iridium Keyboard OS 4 / SOM2, Mac, USB-MIDI — Gerät antwortet auf keinerlei SysEx)
- **Kernbehauptung:** Waldorf hat für Quantum/Iridium **keinen SysEx-Layer** geplant/implementiert. Patch-/Sample-Transfer läuft dateibasiert (SD/USB, `.qpat`/`.map`). Belegt durch direkte Aussage des Waldorf-CEO rolfw (Gearspace, 11.02.2019) sowie Foren-Konsens (2023/2026).
- **Evidenzlevel-Legende:** **(a)** = Primärquelle direkt gesehen (Handbuch/PDF/Changelog/eigene Datei) · **(b)** = Sekundärquelle Forum/Such-Snippet · **(c)** = Schlussfolgerung/Vermutung
- **Methodischer Hinweis:** gearspace.com blockiert direktes Scraping (403). Alle Gearspace-Zitate stammen aus Suchmaschinen-Snippets (Tavily), die den vollständigen Post-Text lieferten. **web.archive.org enthält keine Snapshots der betroffenen Seiten** (CDX-API geprüft, siehe `raw/wayback_cdx_results.txt`). Roh-Snippets liegen unter `docs/sources/raw/`.

---

## Quelle 1 — rolfw: „We have no plans for plain old Sysex" (Primärbeleg, CEO-Aussage)

| Feld | Inhalt |
|---|---|
| Behauptung | Sample-Transfer zum Quantum läuft nur per SD-Karte; **kein „plain old Sysex"** geplant; stattdessen prüfen sie direkte USB-Verbindung (Mass-Storage-Idee) |
| Exaktes Zitat | „Sample transfer to the machine currently is done via SD card. **We have no plans for plain old Sysex, but like to invest in a direct USB connection.** No promises about when and if at all, but the idea is that you connect Quantum to your computer and Quantum's sample storage appears as an external drive on your computer." (voller Post: `raw/rolfw_quantum_p293_snippet.txt`) |
| Autor | **rolfw** = Rolf Wöhrmann (Waldorf-CEO, Software-Entwickler Quantum/Iridium laut Handbuch-Impressum), Gearspace "5 year member", joined Feb 8, 2019 |
| Datum | **11. Februar 2019** |
| Thread | „Waldorf Quantum" (Thread-Starter patrickdafunk, 4. Apr 2017), **Seite 293**, Beitrag **#8,765** |
| URL | https://gearspace.com/threads/waldorf-quantum.1147680/page-293 |
| Kontext (Frage) | **prophei, #8,764, 11.02.2019:** „Rolf, What is the sampler format of the Quantum? … It would be incredible to be able to organize the samples externally, and then just load everything in. Also, was my email regarding the sequencer behavior we discussed clear enough? R" — rolfw beantwortet u. a. das externe Organisieren von Samples |
| Wayback-Snapshot | **nein** — CDX-API: kein Snapshot von page-293 oder Post #8,765 (nur 2 irrelevante 301-Redirects von 2019er post-URLs) |
| Evidenzlevel | **(b)** — Wortlaut über Suchmaschinen-Snippet (vollständiger Post-Text), nicht direkt per HTTP gesehen (403). Aussage ist aber durch Folgepost #9,936 (prophei: „understood rolfw this way, yes") doppelt bestätigt |
| Ablage | Snippet: `docs/sources/raw/rolfw_quantum_p293_snippet.txt` |

**Korroborierende rolfw-Aussagen:**
- Quantum page-332, **#9,936** (prophei, 1. Jul 2019): „I am not an expert in this field, but understood rolfw this way, yes." (zur USB-Disk-Mode-Frage) — **(b)**
- Quantum page-334, **#10,004** (rolfw, 13. Jul 2019, zu OS 2.0): „Lastly, it makes a reasonable fist of importing raw DX7 patches in sysex." — DX7-SysEx ist nur ein **dateibasierter Fremdformat-Parser**, keine eigene SysEx-Schnittstelle — **(b)**

## Quelle 2 — Paul_xyz/SerErris: „no sysex layer in quantum/iridium", „no librarian"

| Feld | Inhalt |
|---|---|
| Behauptung | Quantum/Iridium haben keine SysEx-Schicht; Patches werden physisch per USB-Stick/SD transferiert; es gibt keinen Librarian |
| Exakte Zitate | Paul_xyz **#4,810** (6. Nov 2023): „It's my understanding that **there is no sysex layer in quantum/iridium**." · SerErris **#4,813** (Nummer aus Snippet-Reihenfolge erschlossen): „yes, **patches are physically transferred via usb stick/sd card. there is no librarian** and Rolf said early on there would be no editor as the hardware is its own editor" · SerErris #4,811: DX7-Import sei „just … a parser that converts a DX7 sysex file to quantum/iridium parameters" |
| Autor | Paul_xyz (Lives for gear, joined Jul 2019 — Power-User mit Quantum + allen Iridium-Modellen), SerErris (Lives for gear) |
| Datum | **6. November 2023** |
| Thread | „Waldorf Iridium", **Seite 161**, Beiträge **#4,809–#4,816** (Frage #4,809 SerErris: „I am looking for a Sysex definition of the Iridium Midi Implementation. Has anyone found anything?") |
| URL | https://gearspace.com/threads/waldorf-iridium.1314350/page-161 |
| Wayback-Snapshot | **nein** für Seite 161; nur Thread-Hauptseite (Seite 1) gesichert (2021–2023) |
| Evidenzlevel | **(b)** |
| Ablage | `docs/sources/raw/paul_xyz_iridium_p161_snippet.txt` |

## Quelle 3 — Korrektur: „fully defined Sysex documentation" bezog sich auf Korg 01/W, nicht Iridium

| Feld | Inhalt |
|---|---|
| Behauptung | Das oft zitierte „fully defined Sysex documentation for every single parameter and patch format" ist **kein** Iridium-Zitat |
| Exaktes Zitat | „**I actually love my Korg01W User Guide.** It has a fully defined Sysex documentation for every single parameter and patch format and such. Even for the Sequential Prophet-10 Rev4 it was only partially correct and available, and nothing for Novation Summit. For the later one I created the complete Sysex documentation via Reverse Engineering, but I do not want to do this again for Iridium." |
| Autor | Beitrag auf Iridium-Seite 161 direkt vor #4,809 (Snippet zeigt #4,808, 6. Nov 2023; Urheber im Snippet nicht eindeutig) — **(b)** mit Einschränkung |
| URL | https://gearspace.com/threads/waldorf-iridium.1314350/page-161 |
| Hinweis | In früherer Recherche fälschlich als „Aug 2026" datiert — das war das Tavily-Crawl-Datum der Seite; die Posts sind vom **6. Nov 2023** |

## Quelle 4 — Quantum page-520 (2026): Dokumentationsanfrage bei Waldorf erfolglos; qpat selbst erzeugen

| Feld | Inhalt |
|---|---|
| Behauptung | Mehrfache Doku-Anfrage bei Waldorf ohne Erfolg; Autor baut daher autosamplerT mit qpat-Export |
| Exaktes Zitat | „**I have requested documentation multiple times from Waldorf without succes.** Anyhow my autosamplerT now creates sfz, qpat and map files. qpats give a full turnkey patch, and they contain the map that can be exported on its own anyway." |
| Autor | Unbekannter Gearspace-User (verweist auf github.com/timandtheocean/autosamplerT) |
| Datum | laut Snippet **3. Aug 2026**; exakte Beitragsnummer nicht aus Snippets ersichtlich (Seite 520, Bereich #15,6xx) — ehrlich dokumentierte Lücke |
| URL | https://gearspace.com/threads/waldorf-quantum.1147680/page-520 |
| Wayback-Snapshot | **nein** (kein Snapshot von page-520/521) |
| Evidenzlevel | **(b)** |
| Ablage | `docs/sources/raw/quantum_p520_snippet.txt` |
| Zusatz | Paul_xyz, page-505, **#15,149** (8. Feb 2024): „Is there documentation on best practices of a map file for the Quantum/Iridium?" → „**not seen any official documentation for that.**" — **(b)** |

## Quelle 5 — feijai (Editor-Entwickler): Waldorf liefert SysEx-Specs nur für Nicht-Quantum/Iridium

| Feld | Inhalt |
|---|---|
| Exaktes Zitat | „When Waldorf releases a machine with sysex (**not the Quantum/Iridium**) they're still very willing to work with you. I'm working on the M editor right now, and wrote the first Kyra editor with help from Waldorf and Manuel." |
| Autor | feijai (Entwickler von Editor-/Sysex-Tools, KnobKraft-Autor) |
| Datum | 24. Mai 2023 |
| URL | https://gearspace.com/threads/hydrasynth-patch-editors-and-sysex-spec.1395298 |
| Evidenzlevel | **(b)** |

## Quelle 6 — Primärquellen Waldorf (Handbuch/Changelog/FAQ) — **(a)**

- **Iridium Keyboard Manual** (226 S., files.kraftmusic.com `Waldorf_Iridium_Keyboard_User_Manual.pdf`): genau **eine** „SysEx"-Erwähnung = generischer Glossar-Eintrag („System Exclusive Data…“). Kein MIDI-Implementation-Kapitel, kein SysEx-Menü. `Global>MIDI>Inputs` (S. 180) bietet nur Port-On/Off (DIN In / USB Controller In / USB Computer In), Layer-Kanäle, Local Keyboard, MPE.
- **Changelog OS 4.0.6** (`Quantum_Iridium_changeLog_OS_4.0.6.pdf`, downloads.waldorfmusic.com): einziges „SysEx" im 3.3.0-Teil = UMP-Transport-Typen („message types 1 (MIDI 1UP), 2 (System), **3 (SysEx)**, 4 (Channel Voice), 15 (Streaming…)“), MIDI-CI nur „Management". Kein SysEx-Dump-Feature in irgendeiner Version.
- **waldorfmusic.com FAQ** (faq-iridium/faq-quantum/faq-iridium-keyboard/faq-iridium-core): Patch-Import/Export nur `Load>Actions>Import/Export` von SD/USB; DX7-`.syx`-Import dateibasiert (ab OS 2.0); „USB … only sends and receives MIDI via USB“. Kein SysEx-Eintrag.
- **Waldorf-SysEx-Docs existieren nur für andere Geräte:** Legacy (stromeko: `F0 3E <model> <dev> <cmd>…`, Model-IDs 0x00/0x03/0x0E/0x0F/0x13 — **keiner für Quantum/Iridium**) und Waldorf M (`M_SYSEX_rev_03.pdf`: `F0 3E 30 00 <MSG_ID>…F7`, MSG 0x70–0x7D u. a. 0x74 Request Single Sound).

---

## Zusammenfassende Bewertung

| Aussage | Evidenz |
|---|---|
| rolfw sagte am 11.02.2019 wörtlich: „We have no plans for plain old Sysex" (Kontext: Sample-Transfer → SD-Karte, USB-Mass-Storage als Idee) | **(b)** Primärquellen-Charakter (CEO im eigenen Produkt-Thread), Wortlaut via Snippet, Wayback ohne Snapshot |
| Quantum/Iridium haben keine SysEx-Anwendungsschicht (kein Dump, kein Request, keine Identity Reply) | **(b)** Foren-Konsens #4,810–4,813 + **(a)** Handbuch/Changelog/FAQ + **(a)** eigene Geräte-Tests (0 Antworten auf alle SysEx-Sweeps) |
| DIN vs USB macht keinen Unterschied | **(c)** Schlussfolgerung: fehlender Handler geräteseitig, nicht transportseitig; UMP-Typ 3 ist reiner Transport |
| Patch-Transfer nur filebasiert (.qpat/.map via SD/USB, `Load>Actions>Import/Export`) | **(a)** FAQ/Handbuch + **(b)** Foren |

**Offene Lücke (ehrlich dokumentiert):** Kein Wayback-Snapshot der Gearspace-Seiten 293/520/Iridium-161; exakte Beitragsnummer des page-520-Posts unbekannt; Gearspace-Zitate nicht per Direktabruf verifizierbar (403) — Snippets lieferten jedoch den vollständigen Post-Text.
