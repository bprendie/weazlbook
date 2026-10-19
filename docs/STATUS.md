# R05 status — 2026-10-19

**Ready to use locally:** browser reader at `http://localhost:5000`, opening the
user's `~/Downloads/neuromancer.epub`; desktop reader and headless renderer; original
fixture corpus; source, native test executable, prototype CAD exports and actual
slicer projects. **The complete hardware handoff is not yet accepted.**

| Area | Evidence | State |
|---|---|---|
| R04 inputs | Three originals hashed; supplied JSON/source/research and approval PDF inspected | Preserved |
| Browser simulator | HTTP200; Chromium checks page turn, size change, named bookmark, reload, delete and restoration; no JS errors/mobile overflow | Running locally |
| Neuromancer | Desktop import:2636 blocks,984 screens at24px; native import:32 spine items, host runtime recorded | Host tested; book not redistributed |
| Desktop reading/state |11 pytest cases, including interrupted slot writes and independent book identities | Implemented/tested |
| Native EPUB/PDF |10 supported/rejection corpus cases plus C++ ownership/debounce/layout test | Host tested; compiled for ESP32 |
| Firmware | ESP-IDF5.5.6 build completes;16MB flash/8MB octal PSRAM configured | Built, **not flashed** |
| Display | SPI/reset/BUSY timeout/sleep transport compiled; frame rendering in Plex Mono exists | Initialization/refresh missing; bench gate |
| USB/storage | TinyUSB MSC and exclusive mount transitions; NVS authoritative state outside SD | Built; host-eject-only return and interruption bench tests pending |
| Power | Radios never initialized; explicit battery budget/test procedure | Sleep/low-battery work incomplete; no runtime claim |
| CAD |22 one-solid parts; valid B-reps and watertight meshes; zero part/envelope intersection volumes above0.001mm³ | Prototype, unprinted |
| Plates | Seven real3MF projects exported/reopened in Anycubic Slicer Next2.0.0.5;0.4mm S1 profile;Polymaker ABS assumptions visible | Provisional, not printed, no G-code |
| Mechanics |80×156 and14→26mm retained; real bezel pocket, blind pilots, edge clamps, adjustable driver carrier, reduced tray rim | Measurement/retention gates open |
| Electronics | Board schematic inspected; pin proposal,BOM,harness allowances,VBUS divider and recovery procedure | Documented; unbuilt/unmeasured |

## Concrete remaining gates

1. Obtain the current GDEY0397T81P panel specification/sample and finish/validate
   its exact initialization, RAM orientation, refresh modes and sleep recovery.
   Manufacturer download endpoints returned403; no generic waveform was invented.
2. Measure PH plug/lead turn with USB cable inserted, driver/ZIF/flex insertion,
   navigation stem/PCB/solder/cap travel, battery protected envelope and SD access.
   Record values in `MEASUREMENTS.csv`. R2 flex remains an unapproved assumption.
3. Finish **key-carrier mechanical retention**, driver axial retention and the
   VBUS sensing circuit mounting. A zero-collision model is not a complete load/
   assembly design. The exported enclosure is not presented as production-ready.
4. Improve native EPUB TOC/internal links/fixed-layout rejection; native PDF
   ToUnicode/CID fonts, page labels and reading-order coverage. Native subset
   failures are explicit. Desktop support is not a quiet replacement for native.
5. Complete event-driven sleep/wake and calibrated low-battery shutdown; measure
   whole-device72h profile, charge termination, USB total current and temperature.
6. Bench-test shared SPI under real panel/card activity, filesystem ownership,
   interrupted copies, card faults, NVS power cuts and recovery. Native state
   import/export has source but needs bench tests; cross-runtime coordinate
   conversion remains unfinished.
7. Print ABS coupons and establish Polymaker product/flow/shrink settings, torque,
   key preload/travel, cap retention and service sequence. Only then release full
   enclosure plates/G-code. Exact filament variant is still an assumption.

## Artifact locations

- `artifacts/cad/assembly.step`, `step/`, `stl/`, `coupons/` and
  `R05-engineering-review.pdf`.
- `artifacts/plates/{01_coupons,acid_green,black,black_cover,cyan,magenta,tpu_black}.3mf`.
- `firmware/build/weazlbook_r05.{bin,elf,map}` and accompanying flash arguments.
- `artifacts/simulator-desktop.png` and mobile screenshot are local QA captures.
- `evidence/reader-tests.txt`, `native-corpus.json`, `web-browser-tests.json`,
  `cad-checks.json`, `plate-placement.json`, slicer logs and firmware build log.

The user requested the localhost server remain available; it is intentionally
running. Restart command is in the root README. No deployment or external sharing
was performed.


## USB sideloading and Markdown update

Firmware now enters SD-backed MSC automatically on debounced VBUS connection,
commits resume, closes parsers, and gives USB exclusive card ownership. It
requires existing FAT32 and explicitly disables both formatting paths. Eject on
the computer, then unplug to remount and rescan. Host USB tests remain pending;
VBUS-only detection also pauses reading on a charge-only cable.

Desktop Markdown formatting, heading navigation and resume are implemented;
native Markdown uses bounded sections and preserves a structural text subset.
Alice is available beside Neuromancer at localhost:5000. Desktop tests: 13 passed;
C++ core tests and the 10-case existing native corpus passed. Native Alice import
completed with 10 sections. See FORMATS.md for exact typography/size limits.


## Main menu, lock, duress and About update

Implemented source: main menu completion/READ, Settings codes, About from root
`about.md`, release-based MARK/hold-MARK/chord controls, persistent native lock
with MSC gating, two-stage wipe with separate NVS journal, and idle light sleep.
Firmware wipe uses a low-priority worker and resumes only on the original SD.
The simulator has server-enforced locking and an external Reset simulator
control; its duress operation never deletes source books.

17 Python tests and disposable browser regression pass. Radio drivers are
excluded from the component graph, with a build-time guard. No board has been
flashed; actual wipe/power-cut recovery, USB gating, sleep/wake and panel behavior
remain unvalidated. See DEVICE_CONTROLS.md for exact limits and test boundaries.
