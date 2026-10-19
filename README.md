# WeazlBook — R05 engineering prototype

**Local reader simulator is running at http://localhost:5000.** It opens the user's
`~/Downloads/neuromancer.epub` directly, plus the supplied
`Alice's Adventures in Wonderland.md` in this repository. Neuromancer is not copied
into this project.

This repository continues the supplied R04 packaging study. The original ZIP,
PDF, handoff and extracted `baseline/` are preserved. R05 is **not a finished or
physically validated reader**. See [status](docs/STATUS.md) for the exact limits.

## Use the reader

```bash
.venv/bin/python -m reader.web --book ~/Downloads/neuromancer.epub --book "Alice's Adventures in Wonderland.md" --port 5000
```

Open [localhost:5000](http://localhost:5000). Left/right turn pages; **M** or MARK
saves a named bookmark; the contents/marks/library panels navigate the book.
Font sizes 20, 24 and 28 px reflow IBM Plex Mono. State is stored locally in
`.reader-state/web/`. Export/import is under “Reading notes & state.” The server
binds only to loopback. No cloud account, remote font or hosted service is used.

Alternative desktop window / headless render:

```bash
.venv/bin/python -m reader fixtures --gui
.venv/bin/python -m reader --render fixtures/local.epub artifacts/reader-preview.png
```

Main menu shows completion and READ status. Settings holds unlock/duress codes;
About reads the editable root `about.md`. Reset simulator safely restores demo
state after testing duress. See [device controls and wipe limits](docs/DEVICE_CONTROLS.md).

## Build and verify

The current checkout has an isolated Python 3.12 environment and ESP-IDF tools.
Recreate with `bash tools/bootstrap.sh` (downloads dependencies once); subsequent
reading and ordinary builds use local files.

```bash
.venv/bin/python tools/fixtures.py
.venv/bin/python -m pytest -q
.venv/bin/cmake -S . -B build -G Ninja
.venv/bin/cmake --build build
.venv/bin/ctest --test-dir build --output-on-failure
.venv/bin/python tools/native_validation.py
.venv/bin/python tools/fonts.py
bash tools/idf.sh build
.venv/bin/python cad/build.py
.venv/bin/python tools/plates.py
```

Firmware build output: `firmware/build/weazlbook_r05.bin`, ELF, map, bootloader and
partition table. No board has been flashed. **The display initialization/update
path is still gated**, so this is a bring-up build, not working panel firmware.
Native EPUB/PDF/Markdown parser and UI sources are compiled into it; desktop tests are
separately recorded. Read [formats](docs/FORMATS.md) before testing a book.

CAD exports: `artifacts/cad/assembly.step`, individual `step/` and `stl/`, fit
`coupons/`, engineering `views/`. `reference_envelopes.step` is explicitly
non-printable component/keepout reference geometry. Source is `cad/build.py` and
`cad/parameters.json`.

Slicer projects: `artifacts/plates/` — Kobra S1, confirmed 0.4 mm nozzle,
provisional Polymaker PolyLite ABS. Seven independent jobs, including separate95A TPU key faces; no ACE required.
[Printing and calibration](docs/PRINTING.md) explains the speed/flow assumptions.

## Engineering records

- [Status and remaining gates](docs/STATUS.md)
- [Assembly and measurements](docs/ASSEMBLY.md), [measurement register](docs/MEASUREMENTS.csv)
- [Electronics and bring-up](docs/ELECTRONICS.md), [BOM](docs/BOM.csv)
- [Portable state](docs/STATE.md), [supported formats](docs/FORMATS.md)
- [Dependency and license notices](docs/DEPENDENCIES.md)
- `evidence/`: actual build/test/slicer logs and machine-readable checks.

New project code and parametric CAD are MIT licensed. Supplied R04 assets retain
their original rights; IBM Plex Mono is separately SIL OFL licensed. Nothing here
grants rights to distribute books imported by the reader.
