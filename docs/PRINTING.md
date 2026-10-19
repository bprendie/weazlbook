# Kobra S1 / 0.4 mm / Polymaker ABS

User confirmed the machine, nozzle, ABS preference, Polymaker brand and desire for
high speed. Exact product variant and spool calibration are not established.
Working assumption: **PolyLite ABS**, not ABS Pro/Max/PC-ABS. Check the spool label.

The user subsequently specified **95A TPU buttons**. BACK/MARK now use separate
removable TPU faces over rigid ABS plungers. The nav nub retains its selected
rubber cap. The additional `tpu_black.3mf` plate holds two key faces and a fit
coupon. Hard guides, flange, travel stop and switch-load path stay ABS.

TPU profile uses the installed Generic TPU Kobra S1 0.4 profile, with 15 mm/s first
layer,20 mm/s outer/top,25 mm/s inner/infill,2 mm³/s flow limit,100% rectilinear
infill,3 walls and supports off. Feed from an external spool. Hardness95A is
confirmed; the TPU product/temperatures remain provisional inherited settings.
The 0.9 mm front pad, shallow retaining lip and0.1 mm nominal fit clearance need
the printed face/core coupon before release. The ABS speed target does not apply
to flexible keys. Check that compression adds acceptable feel without preload.

Projects in `artifacts/plates/` are exported and reopened by installed
**Anycubic Slicer Next 2.0.0.5**, using its actual Kobra S1 0.4 mm machine profile.
Machine settings are copied into `cad/print_profiles/machine.json`; no existing
user profiles were changed. These are real slicer project archives with project
settings and plate/model metadata, not renamed mesh ZIPs.

No parts have been printed. The projects are prototypes, not final production
plates. No printer-ready G-code is supplied. Fit/retention gates remain in
`docs/MEASUREMENTS.csv`; resolve them before a final enclosure print.

## Provisional process

| Setting | Value |
|---|---:|
| Layer / initial layer | 0.20 / 0.20 mm |
| Walls / top / bottom | 4 / 5 / 5 layers |
| Infill | 25% gyroid |
| Nozzle / bed | 260 / 100 °C |
| Outer / inner walls | 70 / 150 mm/s |
| Sparse infill | 200 mm/s ceiling |
| Top / small gaps | 60 mm/s |
| First layer | 30 mm/s |
| Nominal / outer acceleration | 5000 / 2000 mm/s² |
| Provisional volumetric cap | 12 mm³/s |
| Main fan / auxiliary | Off / off; 20% overhang cooling ceiling |
| Brim | 8 mm outer brim |
| Support | Normal automatic; inspect carrier bridges and cover before slicing |
| Shrink compensation | None; measure coupons before setting |

The [current manufacturer PolyLite ABS page](https://shop.polymaker.com/products/polylite-abs/)
lists 50–200 mm/s. Twelve mm³/s is an engineering starting point, **not a measured
Polymaker flow rating**. At 0.45 mm width × 0.20 mm height it limits long extrusion
moves to roughly 133 mm/s, even if their speed ceiling is 200. Raise the flow cap
only after a flow/strength test demonstrates clean extrusion; 18 mm³/s would be
needed to sustain that rectangular-section approximation at 200 mm/s. Do not use
the printer's headline maximum as a filament guarantee.

Separate acid green, black, cyan and magenta jobs work without an ACE. The cover
is rotated so its sloped outer rear plane lies on the bed; inspect edge facets
and support. Shell prints front down. Small inserts and keys are printed flat.
The shell front bevel starts above its bed-contact face; brim helps ABS adhesion.

## Economical check order

1. Confirm spool product, dry/use enclosed printing per its instructions. Run
   temperature, flow and extrusion multiplier calibration on this actual spool.
2. Print screw pilots 1.5–1.9 mm. Match a selected M2 screw; measure torque and
   pullout before choosing the final pilot. No heat-set insert is assumed.
3. Print nav sockets 2.45–2.65 mm and key guide/slider. These are **test sizes**,
   not a claim that the delivered navigation stem is 2.4 mm. Measure both axes.
4. Print the local PH/USB wall and cover sections. Fit both connectors together,
   preserving factory battery leads. Record cable boot and lead-turn travel.
5. Test a dummy flex strip on the R2 coupon; do not force the actual panel onto an
   unapproved bend. Obtain/measure permitted flex topology before installation.
6. Only after measurements update `cad/parameters.json`, regenerate CAD, rerun
   interference checks and export fresh plates. A final print still needs service,
   button preload and drop/impact tests.
