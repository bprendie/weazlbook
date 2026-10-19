# Device controls, privacy and recovery

Main menu lists books with completion and a persistent READ marker. The
simulator calculates progress from text anchors, supports mark read/unread,
and marks READ when advancing onto the last page. Firmware progress is an
approximation across source sections/pages; pressing NEXT past the final page
marks READ. Revisiting earlier pages does not clear READ.

Tap MARK to save. Hold MARK for at least 600 ms, then release, to recall marks.
BACK + MARK takes precedence. BACK exits a submenu or returns to the library.
The simulator has the equivalent Esc + M chord and keyboard arrow navigation.

Settings contains Unlock code and Duress code. Both use 4–16 arrows, must be
different, and must have the same length to avoid one completing as a prefix
of the other. Setup asks for the sequence twice. While locked, a matching
duress sequence acts immediately: **there is no execution confirmation**.
No default duress code is installed.

Device lock persists in internal NVS. Native MSC refuses to start while locked
or while a wipe is pending; connecting a USB cable never unlocks the reader.
Unlocking with a cable already connected requires reconnecting it to enter
transfer mode. Controls are inactive during an existing USB host session;
eject and unplug before locking or entering a duress code. Physical SD removal
is outside this lock's protection. Books are not encrypted at rest.

## Two-stage wipe

The firmware first records wipe intent in a separate `wipe` NVS partition,
including the SD card identity. It restarts into the wipe path before normal
reader operation. Stage 1 erases the user NVS partitions (state and settings,
including codes) and recursively removes every file/directory from the SD root,
including `about.md`, exports, hidden files and non-book files. Firmware,
bootloader, partition table and wipe journal are retained.

Stage 2 is a low-priority task that overwrites the complete logical SD address
space in 4 KiB writes. It commits a checkpoint after each 4 MiB, yielding between
writes. On power loss it resumes from the last committed checkpoint, repeating
at most that chunk. A different SD card is rejected. Errors retain the journal
and prevent USB export; reconnect power and the original card to resume.

While wiping, new card writes/reading and USB export remain unavailable: new
books would otherwise be destroyed by the ongoing overwrite. Completion creates
a new FAT32 filesystem and blank About scaffold, clears the wipe journal and
reboots into first-time settings. Battery exhaustion does not cancel the job.

This is a **logical overwrite**, not a guaranteed forensic purge. An SD
controller can retain inaccessible/remapped data. No verified SD sanitize
command or cryptographic erase is implemented. NIST discusses the limitations
of overwriting flash in [SP 800-88 Rev. 1, Table A-8](https://nvlpubs.nist.gov/nistpubs/specialpublications/nist.sp.800-88r1.pdf);
use the current sanitization standard when evaluating a deployed device.
Wipe timing, fault recovery, filesystem durability and actual SD behavior are
**not hardware validated**. Do not rely on this prototype for sensitive data.

## About

`about.md` lives at the root of the FAT32 disk, with a blank name/contact/return
instructions scaffold created only when the file does not already exist. Edit
it using an ordinary text editor over USB; About renders it with the Markdown
reader. It is available only when unlocked. The simulator reads the repository
root `about.md` afresh when About is opened. It is separate from the book list.

## Simulator testing

Lock/code state is now enforced by the local server and stored in `device.json`,
not browser localStorage. Locked book actions, raster pages and state exports
are denied. This remains a local simulation, not an encrypted security product.

Duress clears both reading-state slots, drops the virtual library, clears both
codes and persists a tombstone so restart cannot reload the books. Original
book files and repository `about.md` are never deleted. It does not pretend to
perform a physical SD overwrite. **Reset simulator**, outside the device UI,
restores the demo library and blank state/codes, including while locked. That
button exists only in the simulator. Regression tests use disposable state at
port 5001; they do not wipe the live port-5000 state.

## Power and radios

Firmware uses a restricted component graph and fails the build if Wi-Fi,
Bluetooth or coexistence drivers are added. There is no radio setting in the
UI, no network provisioning, and no remote-access service on the device.

After two seconds without controls, firmware requests light sleep with buttons
and VBUS-level changes as wake sources. No sleep during code entry, an active
USB session or wiping. RAM/state are retained; no automatic deep sleep is
implemented yet. See [Espressif sleep modes](https://docs.espressif.com/projects/esp-idf/en/v5.2/esp32s3/api-reference/system/sleep_modes.html).
Actual wake latency, switch bounce and current draw need bench validation.
Panel initialization is still gated, so display sleep/refresh sequencing remains
a separate hardware bring-up task. Do not infer measured battery life from the
presence of power-saving code.
