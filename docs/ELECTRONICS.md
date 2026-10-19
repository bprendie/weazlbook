# Electronics, pin proposal and bring-up

Design basis: WEMOS S3 PRO v1.0.0 schematic downloaded to
`downloads/s3_pro_schematic.pdf`, rendered and inspected during this session.
The [official board page](https://www.wemos.cc/en/latest/s3/s3_pro.html) identifies
16 MB quad-SPI flash and 8 MB octal-SPI PSRAM. Verify the delivered PCB revision.
Do not connect prototype wiring until polarity/continuity are checked.

[R05 connection and added-divider schematic](wiring.svg) accompanies the full
stock board schematic; it is not a replacement PCB fabrication drawing.

## Signal table

All external logic is 3.3 V, common ground. Native USB D−19/D+20 remain on PCB.

| Signal | GPIO | Board connection / external termination | Pull / wake / route |
|---|---:|---|---|
| SPI MOSI | 11 | J2 pin 6 → C02 SDI; onboard SD | Output; display corridor X33–35 |
| SPI SCK | 12 | J2 pin 4 → C02 SCK; onboard SD | Output; same corridor |
| SPI MISO | 13 | J2 pin 5; onboard SD | SD only; no C02 connection |
| SD CS | 46 | Onboard SD, already routed | Existing strap pin; do not add switch loads |
| EPD CS | 48 | J2 pin 2 → C02 CS | Idle high; independent SD/EPD transactions |
| EPD D/C | 47 | J2 pin 7 → C02 D/C | Output |
| EPD reset | 21 | J2 pin 8 → C02 RES | Output |
| EPD BUSY | 18 | Exposed GPIO18 → C02 BUSY | Input; 15-second timeout implemented |
| 3.3 V | — | J2 pin 3 → C02 3.3 V | Never VIN/VBUS |
| Ground | — | J2 pin 9 → C02 GND | Common return |
| UP / DOWN | 4 / 5 | Nav contacts after continuity mapping | Active-low internal pullups; RTC-capable candidates |
| LEFT / RIGHT | 6 / 7 | Nav contacts after continuity mapping | Same |
| SELECT | 8 | Nav center after continuity mapping | Same |
| BACK / MARK | 9 / 10 | Independent B3F switches to ground | Same; unused I²C connector nets repurposed |
| VBUS valid | 17 | Added divider output | No internal pull; sense only |
| VBAT ADC | 3 | Existing 100k/100k divider via JP2 | Battery measurement, **not USB detection** |
| RGB LED | 38 | Existing board LED | Not initialized; standby load still measured |

J2 numbering is schematic pin numbering, **not a guessed cable color/order**.
Identify connector pin 1 physically and continuity-check every cable conductor.
J2 pin1 GPIO45 (TS CS) and pin10 GPIO14 (TFT LED) are left unused. No peripheral
uses flash/PSRAM pins 26–37 or boot strap GPIO0/45. GPIO3 and46 retain the stock
board connections. The schematic labels only two board mounting holes.

## Power and sensing

Keep the stock source-sharing circuit: VBUS → D1 → VIN/LDO, and Q1 connecting
VBAT to VIN under VBUS control. TP4054 has R6=2k in the inspected drawing; nominal
500 mA charge setting is separate from USB operating load. Retain Adafruit pack
protection and factory 24 AWG leads. The device harness uses 28 AWG stranded wire.

Proposed VBUS monitor: 18.0 kΩ 1% from VBUS to GPIO17; 27.0 kΩ 1% from GPIO17
to GND; optional 1 nF C0G across the lower resistor. Nominal output is 0.6×VBUS
(2.64 V at4.4 V, 3.15 V at5.25 V). Worst resistor-ratio tolerance gives roughly
2.62–3.18 V over those endpoints. Check actual ESP32 thresholds, regulated supply
and intended source range on the bench. Nominal detach RC is 27 µs, but measure
the complete signal and verify the required detach timing. **Do not wire VBUS
directly into GPIO17.** Use insulated assembly and strain relief; its carrier is
still an explicit CAD gate. A self-powered TinyUSB configuration uses this pin.

The prototype USB configuration describes a self-powered device and allows
500 mA USB configuration power. This does not enforce total charger+reader draw.
Verify source negotiation/current and pre-enumeration behavior before claiming
USB compliance. No generic charger module has been added to hide this issue.

## Harness cut allowances (trim only after dry fit)

| Harness | Conductors | Initial cut allowance | Routing |
|---|---:|---:|---|
| C02 | 8 × 28 AWG | 130 mm each | Stock header to X33–35 corridor to mainboard display port |
| Nav contacts | 6 × 28 AWG (five + common) | 65 mm each | Right-side12 mm reservation; retain service loop |
| BACK/MARK | 4 × 28 AWG | 45 mm each | Chin to mainboard; strain relief before solder joints |
| VBUS sense | 3 × 28 AWG | 50 mm each | Board VBUS/GND/17 to insulated divider |
| Battery | Factory pair | Preserve supplied~100 mm | Bay lead notch, upper board edge, PH fit-check region |

Nav supply pin remains disconnected only **after** confirming the five switches
work as isolated contacts to common ground with no leakage/coupling through
module LEDs/resistors. Do not infer the module's physical pinout from labels.

## Firmware and recovery

Pinned ESP-IDF5.5.6 (`880a203ae603d08a94d06aa01e0d6761958e5e9e`) and
esp_tinyusb2.0.1, with transitive versions in `firmware/dependencies.lock`.
Build: `bash tools/idf.sh build`. Firmware checks reported flash/PSRAM sizes at
boot and reserves64 KiB internal allocation pool for DMA/internal needs.
SD and display share SPI2; each transfer uses its own CS through IDF's bus driver.

Native USB mass storage is entered automatically after debounced VBUS detection,
including when booting with the cable attached, but only while unlocked and
with no pending wipe. A locked device never starts MSC. MARK then SELECT remains a manual
retry from the library. Use a preformatted FAT32 card and copy supported books
into the volume root (the device mounts that root as `/books`).
Before handoff: commit internal NVS state, export snapshot, release reader parser
objects, close files, and change TinyUSB mount owner to USB. Reader access is
stopped for the entire host session. Reclaim currently requires physical detach
after host eject; host-eject-only return and interruption testing remain pending.
VBUS detection currently also enters transfer on a power-only charger; unplug to
resume reading. Host-enumeration-aware charge-only reading is not implemented.
Both mount auto-format and the TinyUSB-specific formatting path are explicitly
disabled (`format_if_mount_failed=false`, `do_not_format=true`). The mounted
filesystem type is checked at boot and after reclaim; non-FAT32 cards are
rejected without erasing them. A reclaim failure stops the reader until restart.
USB operation follows the [Espressif MSC ownership API](https://docs.espressif.com/projects/esp-usb/en/latest/esp32s3/usb_device.html).
Actual host enumeration, writes, eject and detach remain bench gates.

No automatic flash operation has been performed. For local recovery, disconnect
the battery if required for a controlled bring-up, hold BOOT/IO0, pulse RESET/EN,
release BOOT, then `bash tools/idf.sh -p /dev/ttyACM0 flash` using the actual device
path. The ROM boot path is separate from application MSC. Application logs use
UART0 in this build; do not assume CDC serial is exposed while MSC is running.
Preserve NVS partitions when updating the application; do not erase all flash.

## Bench checklist (all pending)

1. Verify battery polarity unplugged, rail resistance and C02 RESE=2.2 Ω /47 µH.
2. Power via current-limited source; verify rails, charger current and source share
   with both battery and USB. Record charge termination under reader load.
3. Verify VBUS monitor voltages/detach timing, total source current and temperature.
4. Confirm memory modes from boot log, SD card geometry and no automatic format.
5. Obtain matching current panel initialization sequence. Firmware has SPI/reset/
   BUSY/sleep transport but **initialization and refresh currently return unsupported**.
   Vendor sample/spec downloads returned HTTP403 in this session. Validate full,
   fast and partial updates, portrait mapping, ghosting and timeout recovery.
6. Map/debounce all controls. Verify held-key wake behavior and external pullups if
   needed before enabling sleep. Event-driven GPIO wake and low-battery shutdown
   are still unfinished; the current10 ms input loop is a bring-up loop.
7. Test USB ownership/copy interruption/replug/eject on Linux, Windows and macOS.
   None has been bench tested against this hardware.
8. Whole-device three-day target: radios off,2h/day reading,45s/page,22h/day standby.
   Measure battery-side current and confirm `6*I_reading+66*I_standby<=400mAh` for
   an illustrative20% reserve. No48/72h runtime result or RF result is claimed.


## Current power/privacy build

The component graph is restricted to the reader and its dependencies; a CMake
guard rejects esp_wifi, bt and esp_coex. The UI has no radio setting or label.
Light sleep is requested after two seconds without input, using buttons and
VBUS-level transitions as wake sources. Code entry, USB sessions and wiping
remain awake. Deep sleep and panel power sequencing await hardware validation.
A separate `wipe` NVS partition at 0x720000 holds resumable erase intent/progress;
flash the updated partition table during initial bring-up. Do not deploy this
partition layout over an unknown existing flash layout without reviewing it.
See DEVICE_CONTROLS.md for lock, duress and recovery behavior.
