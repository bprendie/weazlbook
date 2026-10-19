# WeazlBook — Astra / Codex engineering handoff

**Baseline:** approved R04 design direction and dimensioned packaging study  
**Handoff date:** 2026-10-19  
**Requested outcome:** editable engineering CAD, printable parts and Kobra S1 print plates, electronics documentation, and a working local book-reader software stack.

## 1. Your assignment

You are Astra working in Codex. Take WeazlBook from the R04 packaging study into a buildable, repairable reader. Work in the project files, make concrete engineering decisions, implement the software, and verify everything the available environment permits. Carry the project forward beyond a plan or another appearance render.

The user has approved the form and proposed component arrangement. Preserve that direction while resolving its remaining fit issues. R04 contains dimensioned component envelopes and reproducible renders; it does **not** establish manufactured fit, completed electrical validation, working firmware, or measured battery life.

Proceed autonomously with reversible design and implementation work. Use the repository's applicable instructions and existing tooling. If no project exists, establish one. Ask targeted questions only when an actual missing measurement or consequential product change prevents a decision, after completing the unaffected work. Hardware measurements require hardware: record the exact measurement needed and make the affected feature adjustable instead of inventing a value.

The result should feel like a personal reading deck someone built and can keep maintaining. The user's brief is: **Gibson, DIY, Weazl. “Zero DRM, zero bullshit.”**

## 2. Inputs and authority

Read these companion assets if supplied:

| Asset | Purpose |
|---|---|
| `WeazlBook_R04_approval.pdf` | Four-page approval study: assembled views, dimensioned packing, component ledger, and a 1:1 paper check. |
| `WeazlBook_R04_source.zip` | Reproducible mockup source, component ledger, research records, render images, and IBM Plex Mono with its license. |
| `WeazlBook_R04_mockup.png` | Overall appearance and arrangement. |
| `WeazlBook_R04_front.png` | Larger assembled view. |
| `WeazlBook_R04_fit_plan.png` | Quick reference for the dimensioned packing. |

After extracting the source ZIP, inspect:

- `weazlbook_mockup_r04/source/component_layout.json`
- `weazlbook_mockup_r04/source/build_mockup.py`
- `weazlbook_mockup_r04/source/PACKAGE_NOTES.txt`
- `research/mainboard/mechanical_research.json`
- `research/nav/mechanical_reference.json`
- `research/display_headerless/headerless_display_mechanical_audit.json`
- `research/display_alternatives/alternative_reference.json`
- `research/display_alternatives/fpc_routing_proposal.json`
- `research/fonts/`

Use this handoff for product requirements and the **final R04 ledger/source** for the packaging baseline. Earlier research contains superseded trial placements: for example, older BACK/MARK keepouts were 12 × 12 mm; final R04 uses **12 × 10 mm**.

Manufacturer drawings and measured delivered parts determine real component geometry. If they contradict an allowance, report the conflict and fix the local engineering. Do not silently scale hardware to match a render.

If companion files are absent, state that and begin from the dimensions and requirements below. Do not claim to have inspected unavailable assets. Keep the approved R04 files intact and produce a clearly versioned engineering revision.

## 3. Approved product and industrial design

### Form and materials

- Portrait, first-generation Game Boy arrangement: screen above, navigation nub centered beneath it, two small lower keys.
- **80 mm wide × 156 mm tall. Nominal depth tapers from 14 mm at the top to 26 mm at the lower grip.** These shell dimensions exclude approximately 3.95 mm of provisional nub projection.
- Flat front; wedge develops toward the rear. Preserve the angular, faceted outline and broad lower hand-holding area. Earlier 12/24 mm endpoints are not the R04 packing solution.
- Acid-green primary shell, black bezel and removable rear service cover. Visible FDM character, exposed service screws, crisp facets, restrained cyan and magenta printed inserts.
- The visual reference is a rough, dystopian personal deck with a Cybertruck-like wedge. Keep the deliberately severe grip geometry while removing burrs and accidental cutting edges.
- **“NEVER TAX THE GIG” belongs quietly inside the back cover.** This conveys the Weazl ethos. No large exterior logo or invented mascot is required; the original patch artwork is not included.
- Color accents are separate printed pieces. They are not status LEDs.
- Native USB-C power/data opens on the **lower left side**, aligned with the actual mainboard connector and a broad cable recess.
- microSD is accessible behind the removable rear cover. No external card slot has been validated.
- Battery, mainboard, controls, and display support should be serviceable. Use repeatable mechanical retention, a documented assembly sequence, and strain relief.

The known printer carried into this handoff is an **Anycubic Kobra S1**. Available filament colors are acid green, black, cyan, and magenta. Confirm the actual machine profile, nozzle, material chemistry, and slicer before machine-specific output. An ACE unit or automatic multicolor system has not been established. Separate-color printing and manual assembly must work.

### Reading and controls

- Monochrome e-paper; **IBM Plex Mono throughout the reading UI and book text**.
- DRM-free EPUB and supported born-digital, text-heavy PDF.
- Reject scanned books without useful text. No OCR or conversion of every page into an image.
- Local library, independent resume position for every book, and multiple bookmarks per book.
- Five-way mechanical navigation: up/down/left/right plus center press for SELECT.
- Separate **BACK** and **MARK** keys. The nub supplies SELECT; there is no third lower SELECT key.
- A black rubber cap provides the requested pointing-stick feel. The selected switch is a digital five-way mechanism, not a verified isometric TrackPoint.
- Wi-Fi and Bluetooth off during normal reading. Accounts, cloud services, telemetry, subscriptions, online activation, and DRM must not be dependencies of the reading path.
- Standard local files, portable reading state, documented interfaces, and a recoverable local flashing process.
- **Two to three days of light/moderate use** is the battery target. Establish a test profile and measure it.

## 4. Selected parts

Dimensions below distinguish published dimensions from design allowances. Links resolve to the source register in section 11.

| Qty | Part | Published information | R04 allowance / engineering note |
|---|---|---|---|
| 1 | Good Display **GDEY0397T81P** | 3.97-inch B/W; 480 × 800 in portrait; SSD1677; 24-pin, 0.5 mm FPC. Glass 56.24 ±0.20 × 96.62 ±0.20 × 0.92 ±0.10 mm; active area 51.84 × 86.40 mm. [Panel][panel] [Drawing][panel-drawing] | Raw panel with its required driver. Bare thickness excludes removable protective film. Confirm delivered suffix. |
| 1 | Good Display **DESPI-C02** | 41 × 22 mm PCB, 3.3 V interface, compatible 24-pin FPC. [Adapter][adapter] [Manual][adapter-manual] | Rotated in the case. **8 mm complete depth** and approximately **6 mm stock right-angle header projection** are allowances, not a published maximum. Retain the stock header in the initial design. |
| 1 | **WEMOS / LOLIN S3 PRO v1.0.0** | 65.3 × 25.4 mm PCB; ESP32-S3-WROOM-1; **16 MB quad-SPI flash, 8 MB octal-SPI PSRAM**, onboard microSD, one native USB-C, battery port with nominal 500 mA charging. [Board][board] [Drawing][board-drawing] | Component face points rearward. PCB thickness 1.6 mm and connector heights remain provisional. Storage uses the onboard card socket; no separate SD breakout is needed. |
| 1 | **Adafruit #1578**, protected 1S 500 mAh LiPo | Catalog 29 × 36 × 4.75 mm; 3.7 V nominal; supplier permits charge current up to 500 mA. [Cell][cell] [Drawing][cell-drawing] | Design cell envelope **30 × 36 × 6 mm** inside a **32 × 38 × 7 mm bay**. This envelope is our allowance, not a manufacturer maximum. |
| 1 | **EC Buying five-way navigation module**, Amazon B0D8T4YQ3Y | Seller dimensioned photo gives **31 × 25 mm PCB** and 3 mm holes. [Listing][nav] | Stem location, hole centers, height, travel, connector details, and pin behavior need measurement. Reserve 12 mm beyond the header-side PCB edge for header plus wire routing. |
| 1 | **Sprintek 109-00060** black rubber cap | Manufacturer lists compatibility with 2.4 mm square or 3.15 mm round Sprintek stems. [Cap][cap-fit] | Requires a printed adapter to the actual navigation stem. Shown cap Ø9.6 × 2.3 mm and Ø14 mm sweep zone are provisional. |
| 2 | **Omron B3F-1000** tactiles | 6 × 6 mm body; 4.3 mm seat-to-plunger height; lead-inclusive width about 7.7 mm and leads 3.5 mm below seating plane. See tolerances in drawing. [Switch][switch] | Separate printed BACK/MARK keys and carriers; each installed bay is **12 × 10 × 9 mm**. Include legs, solder, guides, retention, and mechanical stops. |
| 1 | Compatible microSD card | Capacity and card model are not frozen. | Use the board's socket; qualify the chosen card and filesystem. The 16 MB flash is not 1 GB of book storage. |
| As needed | Wiring, insulation, retention, fasteners, minor sensing components | Produce a complete build BOM with exact specifications. | Short **28 AWG device harness**. Retain the battery's factory protection and leads; its linked drawing specifies 24 AWG. Native USB D+/D− remain on the board. |

The current panel page pairs GDEY0397T81P with DESPI-C02. A vendor purchase URL still contains the legacy **GDEM** name; that is not proof of an interchangeable panel/controller revision. Check the delivered current part and its documentation.

The battery catalog and its older linked drawing differ slightly. Measure the protected pack including tape, PCM, and lead exit. Keep the pouch free from compression and screw tips. Preserve factory leads rather than modifying the protected pack to satisfy the 28 AWG harness preference.

## 5. Mechanical baseline

### Coordinate frame and enclosure

All coordinates are **millimetres**, viewed from the front:

- X increases rightward.
- Y increases downward.
- Z increases toward the rear from the front plane.
- Rear views mirror the apparent left/right positions.

The nominal rear plane is:

`Zrear(Y) = 14 + 12 × Y / 156 = 14 + Y / 13`

R04 uses nominal 2.4 mm shell walls. The cover is described as 2.2 mm; the blocking geometry's inner rear face is approximately `Zrear(Y) − 2.25`. These are starting parameters for engineering, not validated print tolerances. The faceted end edges do not have the full nominal depth everywhere.

The outer XY polygon, in order, is:

`[(7,0), (73,0), (80,7), (80,141), (73,156), (7,156), (0,141), (0,7)]`

Use the supplied CAD source for the detailed front bevel and cavity outline.

### Final R04 placements

Ranges are occupied or reserved volumes, not guaranteed clearance around a finished assembly.

| Item | X range | Y range | Z range / datum |
|---|---:|---:|---|
| Display glass | 11.88–68.12 | 9–105.62 | 2.20–3.22 |
| Active reading area | 14.08–65.92 | 11.20–97.60 | Display face |
| Display backing/insulation allowance | 11.58–68.42 | 8.70–105.92 | 3.22–4.50 |
| DESPI-C02 body envelope | 7.13–29.13 | 54–95 | 5.50–13.50 |
| Driver header | Along driver short edge | Extends toward Y48 | Include terminations separately |
| Battery bay | 40–72 | 75–113 | 9.50–16.50 |
| Conservative cell envelope | 41–71 | 76–112 | 9.70–15.70 |
| Battery tray outer envelope | 39.30–72.70 | 74.30–113.70 | 8.60–16.90 |
| Navigation PCB | 28–59 | **117–142** | PCB 9.40–11.00; rear envelope to **12.50** |
| Navigation stem | **40** | **129.50** | XY offset is photo-derived |
| Nav header and wires | 59–71 | 117–142 | 8.50–12.50 |
| Mainboard PCB | **10–75.30** | **122–147.40** | **14.00–15.60**, component side rear |
| Mainboard module region | 49.80–75.30 | 125.70–143.90 | 15.60–18.85 |
| BACK installed bay | **18–30** | **143–153** | **3.50–12.50** |
| MARK installed bay | **50–62** | **143–153** | **3.50–12.50** |

Printed lower key faces are approximately 10 × 6 mm, centered at (24,148.5) and (56,148.5), protruding about 1.5 mm. Their actual guides and stops require engineering.

### Connectors and routing

| Region | R04 reserved envelope / constraint |
|---|---|
| USB-C housing | X9.5–17.8, Y137.8–146.9, Z15.6–19.4; mouth faces −X. |
| Open USB cable recess | Approximately X−3–11, Y135.5–151, Z12.8–23.3. Check a real cable boot and insertion travel. |
| Board battery socket | X9.1–16, Y128.7–137.1, Z15.6–21.1. |
| Mating battery plug allowance | X3.2–9.2, Y129.2–136.6, Z15.8–20.8. |
| PH plug/lead fit-check region | X2.4–9.4, Y124–136.7, Z14.9–21.1. This amber region is unresolved. |
| Display harness corridor | Runs through X33–35 between driver and battery tray; approaches the mainboard above the PCB at about Z16.3 to clear its support. |
| Full FPC routing allowance | X11.5–52, Y91–116, Z3–8. The smaller visible amber turn block is only X11.5–52, Y105–116, Z4.55–8. |

The USB and battery connectors occupy the same end of the mainboard. Validate them **with both the USB cable and battery plug inserted**. Colored strands in the mockup show routing corridors, not a verified wire count or final pinout.

The mainboard's source-photo frame has antenna upward, coordinates u across the 25.4 mm width and v along the 65.3 mm length. R04 maps it into device coordinates as:

`X = 75.3 − v; Y = 147.4 − u`

Connector photo estimates are approximately ±0.5 mm and must not become manufacturing datums without verification.

### Preserve these R04 collision repairs

- Service-post centers: **(6.2,9), (73.8,9), (4.4,68), (75.2,68), (15,150.4), (65,150.4)**. The illustrated radius is 2.45 mm; screw/insert design remains provisional.
- Mainboard supports have real underlap: X10–26/Y121–123; X72–75.3/Y121–123; X36–45/Y146.4–148.9. Their top is Z14.
- The glass relief pocket starts at Z2.1 over X11.58–68.42/Y8.7–105.92.
- The battery tray has a lead notch around X53.5–59/Y112.8–114.2/Z14.9–17.3.
- Battery wires end at the amber PH check region; the render intentionally does not assert a successful tight lead turn.

The closest nominal separations explain why production tolerances matter: nav rear to mainboard underside is 1.5 mm; nav PCB to lower key bays is 1.0 mm; key bays to the inner bottom are about 0.6 mm; battery tray to the sloping cover is about 0.57 mm at its closest point. Some post-to-component gaps are approximately 0.28–0.55 mm. These are model calculations, not validated manufacturing margins.

### FPC geometry and the proposed fold

With the panel upright and its flex exiting downward, the real tail **doglegs left**. The contact tongue is near the panel's left edge; it is not centered.

The drawing gives an unfolded extension of **33.66 ±0.30 mm to the tip**, a 12.50 ±0.10 mm contact tongue, approximately 0.10 ±0.03 mm flex thickness, and a 0.30 ±0.05 mm stiffened end. The tongue center is approximately global X18.13. [Panel drawing][panel-drawing]

R04 proposes a U-loop leaving Y105.62/Z3.3, returning at Z7.3, with **R2** and a **seated tip near Y93**. Its modeled maximum Y is approximately 115.00. The length accounting is approximately 7.38 mm outgoing straight + 6.28 mm semicircle + 20.00 mm return.

This proposed bend occupies a different material interval from the drawing's marked fold reference near 15 mm beyond the glass. No manufacturer-approved minimum bend radius was established. **R2 is an engineering assumption requiring validation.** The seated tip datum is not the connector mouth. Provide several millimetres of driver-carrier adjustment for actual ZIF insertion depth, preserve the native tail topology, and check contact-face orientation, stiffener clearance, assembly access, and strain relief.

## 6. Close these physical gates

Produce an evidence register with columns for feature, source/measurement, provisional value, measured value, resulting clearance, status, and affected CAD parameter.

| Gate | Required resolution |
|---|---|
| Battery plug and lead exit | Highest-priority local fit issue. The provisional plug ends at X3.2 while the inner wall is at X2.4: only **0.8 mm** remains for a turn. Measure mated length, insertion overlap, wire exit, lead bend, and cable boot together. The amber region also has only approximately 0.2–0.6 mm of provisional rear clearance. |
| FPC and driver | Measure the complete adapter on both sides, header/termination envelope, connector slot height, actual insertion, tail shape, and an acceptable bend location/radius. Validate the installation sequence. |
| Navigation and cap | Measure PCB holes, stem offset/profile, switch stack, rear solder, lateral and press travel, and rubber cap socket. Print replaceable adapter/carrier coupons before freezing them. |
| Thumb force | Carry loads through a rigid nav carrier into the chin/frame. The glass, flex, and battery must not support thumb force. Provide key travel stops with no resting preload. |
| Mainboard and USB | Verify board thickness, component heights, support contact, screw access, and cable insertion. The official drawing identifies only two mainboard holes at the antenna end; do not invent four mounting holes. |
| Battery and card service | Confirm protected-cell envelope, polarity, lead exit/slack, tray retention, and actual SD extraction direction/travel with the cover removed. |
| RF | The compact antenna placement does not establish the usual RF keepout or tested performance. Preserve the compact reading design; measure performance if optional wireless features are enabled. |

Resolve these with local carriers, recess details, connector routing, and serviceable mounts before proposing a larger shell. If the exact hardware makes the accepted envelope impossible, show the conflicting solids and dimensions, quantify the smallest necessary change, and ask one concrete question. Do not shrink components, omit plugs, force a flex bend, or export intersecting solids as a finished enclosure.

## 7. Electronics and bring-up

### Derive the wiring from the actual board

Create a schematic and connection table showing connector orientation, signal name, GPIO, voltage, pull-up/down, wake behavior, and physical wire route. Check delivered board revisions and boot-strapping/memory restrictions before allocating free GPIOs.

Observed S3 PRO v1.0.0 connections are microSD MOSI11/SCK12/MISO13/CS46, native USB D−19/D+20, battery ADC divider GPIO3, and RGB LED GPIO38. These are existing nets, not a complete proposed pinout. The display connector shares SPI; preserve independent chip selects and coordinate access. [Schematic][board-schematic]

Configure and verify the selected flash and PSRAM modes at boot. Reserve internal memory for DMA/driver requirements and explicitly budget PSRAM, task stacks, fonts, parsing, and caches.

### Power and USB

The stock schematic includes discrete source sharing: **VBUS → D1 → VIN/LDO**, with **Q1 connecting VBAT to VIN under VBUS control**. Verify its transition behavior rather than adding a generic charger/power-path module by default. The 500 mA charging setting is separate from the running reader's USB load. [Schematic][board-schematic]

Use the selected protected battery and verify polarity electrically. Measure actual charge current, termination under reading load, total source current, low-battery behavior, and enclosure temperature. The selected pack has no thermistor, so battery-temperature monitoring is not an established feature. [Cell][cell]

Resolve native USB attach/detach properly for a battery-powered device. Espressif documents VBUS monitoring for self-powered USB. The board's GPIO3 divider senses **VBAT**, not USB presence; the reviewed schematic has no obvious MCU VBUS-sense net. Check the actual revision and provide a suitable safe sensing arrangement if needed, with its components, GPIO, and occupied space in the BOM/CAD. Direct 5 V into an ESP32 GPIO is not acceptable. [USB documentation][usb] [Schematic][board-schematic]

Validate current available from the intended USB sources while charging and operating; configuration must reflect the actual device. Provide an accessible boot/recovery procedure through native USB and the board's service controls. Keep USB D+/D− on the stock PCB.

### Display and inputs

Use the current **GDEY0397T81P / SSD1677** driver configuration. DESPI-C02 supplies the necessary display power circuitry; a bare raw panel is not a standalone SPI module. The current C02 manual specifies **RESE 2.2 Ω for SSD controllers** and a 47 µH inductor. Verify the delivered adapter and setting. [Panel][panel] [Adapter manual][adapter-manual]

Bring up reset, BUSY, update completion, full/fast/partial refresh, and display sleep with bounded timeouts. Validate ghosting and recovery on the actual panel.

Continuity-map the five-way module before final wiring. Evaluate using its five contacts with common ground and 3.3 V input pull-ups while leaving its supply pin disconnected; confirm any LEDs/resistors do not cause leakage or coupling in that configuration. Do not infer a pin mapping from generic module labels. Map BACK and MARK independently.

Choose appropriate wake-capable inputs, verify pull behavior during sleep, debounce presses, and handle a held control without immediate repeated wakeups. [Sleep documentation][sleep]

## 8. Firmware and local software

### Architecture and implementation baseline

Use **ESP-IDF with C/C++** as the default starting point; pin a supported toolchain and dependency versions after checking their primary documentation. A justified alternative is acceptable if it meets the same hardware, memory, power, licensing, and reproducibility requirements.

Separate hardware drivers, input events, document parsing, semantic book representation, layout/pagination, monochrome rendering, persistent state, and USB/storage ownership. Keep parser/layout/state logic host-testable. Use narrow interfaces and incremental processing instead of loading whole books or the whole library into RAM.

The 480 × 800 1-bit framebuffer is **48,000 bytes**; two such buffers are 96,000 bytes before other allocations. Document actual memory peaks on representative books. Cache by chapter or source page and invalidate by source hash, layout settings, and renderer version. Bound decompression, object counts, nesting, and parsing work so malformed files fail clearly.

Keep a reproducible offline reading path. Internet access may help development or optional maintenance, but opening and reading a local book must not require it.

### EPUB

Implement DRM-free reflowable EPUB import: ZIP/container discovery, package metadata, spine order, navigation/TOC, and XHTML text structure. Preserve headings, paragraphs, emphasis, chapter boundaries, and useful internal links while normalizing fonts and layout to Plex Mono.

Declare supported versions/features and deliberate handling of illustrations, tables, mathematical material, footnotes, and unusual writing modes. Ignoring embedded fonts does not justify rejecting a readable EPUB merely because it contains font obfuscation metadata. Reject actual unsupported protected content with a clear reason; do not build a DRM-removal feature.

Opening, navigating, resuming, and bookmarking representative EPUBs must work end to end. A metadata list or extracted text dump is not a completed reader.

### Text-heavy PDF

The intended primary capability is **on-device text extraction and reflow of supported born-digital PDFs**. Preserve source page numbers/labels and usable paragraph/reading order while presenting the text in Plex Mono.

Begin with a feasibility spike on this hardware and a representative corpus. Correct extraction needs PDF objects/resources, cross-reference handling, compressed streams, character encodings/Unicode mappings, and positioned-text interpretation. Replacing the output font removes publisher font rasterization; it does not remove the need to decode the original character mappings.

Document the supported PDF subset and explicit failures: encryption, unsupported filters, missing usable character mappings, unreliable reading order, malformed files, or image-only pages. A PDF containing some pictures is not automatically a scanned book. For mixed or partially unreadable documents, disclose omitted/unsupported pages rather than reporting a silently incomplete import.

Do not claim arbitrary page-faithful PDF rendering or OCR. An **optional, fully offline desktop preprocessor** may broaden compatibility or accelerate imports, with a documented portable output format. It must not quietly replace the native PDF requirement. If practical native support proves infeasible, present measured memory/runtime/coverage evidence and a concrete tradeoff before changing the product scope.

### Typography and UI

Use **IBM Plex Mono** for the interface and reading text, with regular/semibold resources or a documented raster/subset build. Preserve the bundled SIL Open Font License. Define Unicode coverage, punctuation/diacritics, missing-glyph behavior, and font-size choices. Make unsupported characters visible rather than silently dropping them. [Font source][plex]

Prioritize readable text, simple library navigation, per-book bookmark lists, font-size adjustment, and fast next/previous page actions. Suggested default controls are left/right for pages, up/down for menus, center press to select, BACK to step out, and MARK to save/manage a bookmark. Make any contextual or long-press behavior discoverable. Avoid accidental page-repeat and unnecessary full-screen animations.

Measure end-to-end page-turn latency separately from the panel's own update time. Select refresh waveforms from the actual display documentation and tune periodic full refresh using observed ghosting.

### Resume and bookmarks

Each book needs independent automatic resume and **multiple named bookmarks**. Use a stable content-derived book ID so renaming or moving the source file preserves state.

Use reflow-independent positions: EPUB spine item plus logical text anchor/offset or supported CFI; PDF source-page identity plus text anchor/offset. Save enough context to recover positions after a layout change. Displayed reader page numbers alone are insufficient.

Keep authoritative state separate from disposable pagination caches. Provide a versioned, human-readable local export/import format carrying book identity, resume, bookmarks, and source coordinates. Handle missing or changed books without deleting unrelated state.

Use recoverable persistence, such as a journal or two-slot records with sequence numbers and integrity checks. Verify power-loss recovery; a filename rename alone is not proof of durable FAT writes. Choose and document where authoritative state lives while the host owns the SD card.

### USB file transfer

Provide native USB mass-storage transfer mode for local book copying. USB serial may serve diagnostics, but it is not the book-transfer interface.

**The exposed filesystem has one owner at a time.** Before giving the host block access, persist state, stop reader access, flush/close files, and release the filesystem. After release/eject or cable removal, safely reacquire it, inspect changes, and rebuild only necessary indexes. Never run independent host and firmware writers against the same mounted FAT volume.

Charging should also work without entering transfer mode. Handle interrupted copies, cable removal, renamed files, missing/corrupt cards, and host eject without losing unrelated reading state. Validate transfer on available desktop operating systems and disclose any not tested. Avoid sleep transitions that break an active transfer. [USB documentation][usb]

### Power target

Use event-driven input, sleep between operations, idle/sleep the display appropriately, and avoid continuous SD polling. Measure the **whole assembly**, including regulator, charger, SD card, indicator circuits, and input leakage. A dark RGB LED does not establish zero standby consumption.

Use an explicit initial three-day profile, for example **2 hours reading per day, a page turn every 45 seconds during reading, and 22 hours daily standby**, with radios off. Include wake frequency, font/layout settings, refresh policy, card model, and ambient conditions in the results.

With an illustrative 20% reserve from a 500 mAh pack, the 72-hour budget is:

`6 × I_reading + 66 × I_standby ≤ 400 mAh`

Currents are average **battery-side mA**; reading includes refreshes and sleep between page turns. The resulting whole-period average is about 5.6 mA. This is a budget, not a predicted or measured runtime. Measure 48-hour and 72-hour performance, charge behavior, and orderly low-battery shutdown before claiming the target.

### Licensing and sovereignty

Keep source, build steps, book/state formats, and recovery paths available locally. Prefer dependencies whose licenses support the intended open, repairable project; record each dependency's exact version, license, notices, and obligations. Font licensing is distinct from application licensing.

Do not assume another Weazl project's repository license automatically governs this one. Establish an explicit license choice for this repository and audit transitive dependencies, especially document engines. Required runtime services, commercial activation tiers, proprietary file locks, and hidden analytics conflict with the brief.

## 9. Required deliverables

Choose a sensible repository layout and deliver the following:

| Area | Concrete output |
|---|---|
| Parametric CAD | Editable native source, centralized dimensions/allowances, assembly STEP, individual part STEP files, and regenerable exports. CadQuery is a natural continuation of R04; another maintainable parametric system is acceptable with a reason. |
| Printable parts | Valid, manifold STL/3MF meshes in millimetres for shell, service cover, bezel, carriers, keys, cap adapter, and color inserts. Component envelopes and amber keepouts must not appear as printable hardware. |
| Engineering views | Dimensioned front/side/section views, exploded assembly, actual enclosure clearances, connector access, fastener engagement, and the battery/nav/display load paths. Generate these from the engineering geometry. |
| Fit coupons | Small, clearly labeled tests for nav-stem/cap fit, key guide/travel, critical connector clearance, and selected screw/insert fits. Include an economical print/check sequence. |
| Print plates | Real slicer-readable **3MF projects/plates** for the verified Kobra S1 profile, separated by color/material as needed. Record slicer/version, nozzle/profile, orientation, supports, layer/perimeter settings, and quantities. Label any provisional profile. |
| Electronics | Full BOM, documented schematic/pin table, power and USB sensing decisions, connector polarity/orientation, harness lengths/routes, and assembly/bring-up instructions. |
| Firmware | Buildable source, pinned dependencies, flash/PSRAM configuration, partition plan, display/input/storage drivers, reader UI, EPUB/PDF paths, bookmarks, USB mode, and power management. |
| Local tooling | Reproducible build/flash commands, font asset generation, fixture tools, and any optional offline importer. No mandatory hosted service. |
| Validation | Meaningful automated test results, firmware build evidence, mesh/interference checks, slicer inspection, and a separate physical-test checklist with actual results where hardware exists. |
| Documentation | README, assembly guide, supported-format matrix, portable state specification, BOM/source register, license notices, decisions, and unresolved measurement/issues list. |

A generic multi-mesh archive is not a verified slicer project. Inspect the exported meshes and plate arrangement in a real slicer when available. Only generate printer-ready G-code after the exact machine/material profile is known. Label unprinted parts as unprinted.

R04's simplified retention, decorative intersections, illustrative fasteners, and component blocks require engineering. Create genuine pockets, joints, screw access, support surfaces, and assembly clearance before calling a part ready to print.

## 10. Execution sequence and acceptance

1. **Inspect and establish the project.** Read supplied assets and applicable repository instructions. Reconcile the BOM and final R04 coordinates, record unresolved measurements, pin the initial toolchain, and create a concise work plan.
2. **Resolve highest-risk interfaces early.** Audit the PH/USB fit and display FPC routing in CAD; produce targeted coupons and measurement requests. In parallel, prove the native PDF extraction approach with bounded memory and a documented corpus.
3. **Implement the hardware foundation.** Display, nav/buttons, SD, power-state handling, and exclusive USB filesystem ownership. If hardware is unavailable, build the firmware and host test harness, and mark bench tests pending.
4. **Complete reading behavior.** EPUB first, then the supported native PDF path; Plex Mono layout, library navigation, multiple books/bookmarks, portable state, and recovery.
5. **Finish engineering CAD and plates.** Replace provisional interfaces with measured ones when available; verify solids, mounting loads, tolerances, wiring, and assembly access. Export and inspect the actual deliverables.
6. **Validate and package.** Run the meaningful software/build checks and available physical tests. Ship source, outputs, instructions, and an evidence-based status report.

Acceptance must include:

- Measured or explicitly provisional clearance at the FPC, battery plug/USB, nav stack, battery tray, and rear cover.
- A retained 80 × 156 mm, 14-to-26 mm shell unless a documented conflict has led to an agreed change.
- A reproducible firmware build with a truthful account of what was flashed and tested.
- Representative EPUBs and text PDFs that open, paginate, navigate, and survive font-size changes; scanned/unsupported inputs get clear reasons.
- Switching among several books preserves independent progress and multiple bookmarks.
- State export/import, reboot recovery, interrupted saves, interrupted USB copies, and corrupt-file handling do not destroy unrelated bookmarks.
- Display/SD shared-bus operation and input responsiveness work under concurrent reader activity.
- Whole-device power measurements against the stated use profile, or an explicit pending hardware test with no runtime claim.
- Slicer-readable plates and serviceable assembly instructions; unverified tolerances remain visible.

Use locally generated or suitably licensed test fixtures. Test real failure modes and supported document features, not only mocks that repeat the implementation. Record command results, artifact paths, versions, and physical observations. Distinguish **implemented**, **built**, **bench-tested**, **printed**, and **validated**.

Your final report should lead with what is ready to use, provide exact artifact/build locations, explain consequential decisions, and identify the remaining concrete gates. Continue completing useful work when one physical measurement is pending. **Start by inspecting the available project and R04 inputs, then execute.**

## 11. Primary source register

These references support the selected hardware and implementation constraints. Verify delivered revisions and the documentation appropriate to pinned software versions. Source URLs with legacy filenames may serve newer document revisions; record the revision actually used.

| Reference | Source |
|---|---|
| Current panel | [Good Display GDEY0397T81P][panel] |
| Panel drawing/specification | [GDEY0397T81P PDF][panel-drawing] |
| Adapter | [Good Display DESPI-C02][adapter] |
| Adapter manual | [DESPI-C02 manual][adapter-manual] — reviewed content is Rev 2.0 despite the V1.1 filename. |
| Mainboard | [WEMOS S3 PRO][board] |
| Mainboard dimensions | [S3 PRO v1.0.0 dimension PDF][board-drawing] |
| Mainboard schematic | [S3 PRO v1.0.0 schematic PDF][board-schematic] |
| Battery | [Adafruit #1578][cell] and [linked pack drawing][cell-drawing] |
| Navigation | [EC Buying B0D8T4YQ3Y][nav] — seller evidence; not a complete tolerance drawing. |
| Rubber cap | [Sprintek store][cap-store] and [manufacturer stem compatibility][cap-fit] |
| BACK/MARK switches | [Omron B3F datasheet][switch] |
| Native USB | [Espressif ESP32-S3 USB device stack][usb] |
| Sleep/wake | [Espressif ESP32-S3 sleep modes][sleep] |
| Font and license | [IBM Plex source][plex]; bundled R04 font files include OFL.txt. |

[panel]: https://www.good-display.com/product/613.html
[panel-drawing]: https://v4.cecdn.yun300.cn/100001_1909185148/GDEY0397T81P.pdf?download=1
[adapter]: https://www.good-display.com/product/516.html
[adapter-manual]: https://v4.cecdn.yun300.cn/100001_1909185148/DESPI-C02%20Connector%20Board%20for%20E-paper%20Display%20V1.1.pdf
[board]: https://www.wemos.cc/en/latest/s3/s3_pro.html
[board-drawing]: https://www.wemos.cc/en/latest/_static/files/dim_s3_pro_v1.0.0.pdf
[board-schematic]: https://www.wemos.cc/en/latest/_static/files/sch_s3_pro_v1.0.0.pdf
[cell]: https://www.adafruit.com/product/1578
[cell-drawing]: https://cdn-shop.adafruit.com/product-files/1578/Datasheet.pdf
[nav]: https://www.amazon.com/dp/B0D8T4YQ3Y
[cap-store]: https://store.sprintek.com/category/flexpoint-pointing-stick
[cap-fit]: https://www.sprintek.com/en/order/Order.aspx
[switch]: https://components.omron.com/us-en/datasheet_pdf/A070-E1.pdf
[usb]: https://docs.espressif.com/projects/esp-usb/en/latest/esp32s3/usb_device.html
[sleep]: https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-reference/system/sleep_modes.html
[plex]: https://github.com/IBM/plex

