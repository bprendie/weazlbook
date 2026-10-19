# Dependency and license record

New R05 software, CAD source and documentation use the repository MIT license.
The supplied R04 archive was not relicensed. The following third-party licenses
continue to apply. The user's EPUB remains outside the repository and release
archive. No application license is inferred from another Weazl project.

| Component | Pin | Use / license / notices |
|---|---|---|
| ESP-IDF | v5.5.6 /880a203ae603d08a94d06aa01e0d6761958e5e9e | Device framework; Apache2.0 plus component-specific notices in toolchain tree |
| esp_tinyusb | 2.0.1 | Device USB; Apache2.0; full dependency lock in firmware/dependencies.lock |
| TinyUSB | Resolved exact pin in dependencies.lock | USB core; MIT; retain managed component LICENSE |
| PDFio | 1.6.5 /5102eddff28d9b605f3e6783d50ad380f61f692e | Native PDF parser; Apache2.0; vendor/pdfio/LICENSE and NOTICE |
| PDFio TTF helper | Same PDFio source revision | Build dependency; upstream notices retained; unused font-writing code is linker-eliminated where possible |
| zlib | 1.3.1 | Native deflate; zlib license in vendor/zlib/README; archive retained under downloads |
| pugixml | v1.15 | Native XML; MIT; vendor/pugixml/LICENSE.md |
| pypdf | 6.1.1 | Desktop PDF; BSD3-Clause |
| defusedxml | 0.7.1 | Desktop XML; PSF license |
| Pillow | 11.3.0 | Desktop raster/font generation; HPND-style PIL license and dependency notices |
| CadQuery | 2.7.0 | Build-only CAD generator; Apache2.0; OpenCascade/OCP dependencies carry their own LGPL/special exceptions |
| trimesh | 4.9.0 | Build-only mesh inspection; MIT |
| ReportLab | 4.4.4 | Build-only PDF/fixtures; BSD-style license |
| CairoSVG | 2.8.2 | Build-only view conversion; LGPL3+; Cairo/font libraries have separate notices |
| Shapely | 2.1.2 | Build-only plate footprint audit; BSD3-Clause; GEOS LGPL2.1 |
| Playwright | 1.55.0 | Browser test tool only; Apache2.0; uses locally installed Chromium |
| IBM Plex Mono | Supplied R04 TTF files, SHA in input/font manifest | SIL OFL1.1; baseline/research/fonts/OFL.txt must accompany fonts/atlas |

`requirements.lock.txt` records all installed Python package versions, including
transitives. `evidence/python-dependencies.json` records their installed metadata
and declared license-file names. This is an inventory, **not a completed legal
audit of every transitive binary**. In particular CadQuery's VTK/CasADi/OCP build
dependencies and ESP-IDF's component libraries require notice review before
redistributing a bundled toolchain. They are not hidden runtime services.

PDFio local modifications are deliberate and retained as source: bounded
allocation hooks; maximum token string4096 instead of131072; ESP32 UTC metadata
date conversion uses mktime because this Newlib lacks timegm. The 2 MiB allocation
budget is shared with pugixml for native single-owner parsing. Full baseline
source revision is available in `.toolchains/pdfio/`; use a diff against that pin
when updating. Firmware reads documents only; PDF writing is not a reader feature.

No vendor display initialization was copied from an unlicensed unrelated driver.
The matching manufacturer files were identified, but direct downloads returned
403. Initialization/refresh remain explicitly unimplemented rather than silently
substituting another panel revision.
