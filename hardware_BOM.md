# WeazlBook — Hardware BOM and Shopping List

**Design baseline:** R04  
**Quantity:** Parts for one WeazlBook  
**Sourcing checked:** 2026-10-19  
**Preference:** Amazon where the correct item could be verified.

Your existing **6 × 6 tactile switches cover BACK and MARK—we need two**. Astra should adapt the key carriers to their actual height and leg layout.

The exact mainboard, display parts, battery, and rubber cap have clearer purchase routes through their manufacturers. Prices below are the displayed prices that could be verified, excluding shipping and tax. Current Amazon offer prices and delivery dates were not reliably exposed.

## Core parts

| Buy | Part | Purchase link | What to select / notes |
|---|---|---|---|
| **1 pack** | **EC Buying five-way navigation module** | **[Amazon — B0D8T4YQ3Y](https://www.amazon.com/dp/B0D8T4YQ3Y)** | The module used in R04. This listing is a **five-pack**; we use one and keep four spares. Current price was not exposed in the retrieved listing. |
| **1 card** | **SanDisk 32 GB High Endurance microSDHC** | **[Amazon — B07P14QHB7](https://www.amazon.com/dp/B07P14QHB7)** | Model **SDSQQNR-032G-GN6IA**. More capacity than this reader needs; an existing suitable card can save this purchase. |
| **1 board** | **LOLIN / WEMOS S3 PRO v1.0.0** | **[WEMOS-linked AliExpress listing](https://www.aliexpress.com/item/1005004931357085.html)** | Exact long board with **16 MB flash, 8 MB PSRAM, microSD socket, USB-C, and battery charging**. No exact Amazon listing was verified. Current price and inventory need checking on AliExpress. [Manufacturer specifications](https://www.wemos.cc/en/latest/s3/s3_pro.html). |
| **1 panel** | **Good Display GDEY0397T81P** | **[Good Display shop](https://buy-lcd.com/products/gdem0397t81p)** | Select **“EPD”** for the panel alone. Displayed base price: **$14.88**. The current heading identifies **GDEY0397T81P**, despite the older `gdem` text in the URL. See the availability note below. |
| **1 adapter** | **Good Display DESPI-C02** | **[Good Display shop](https://buy-lcd.com/products/development-kit-connection-adapter-board-for-eaper-display-demo-kit)** | Displayed price: **$8.50**. This is the small adapter selected for R04. Its shop title includes “HAT adapter,” so order by the exact **DESPI-C02** model. |
| **1 battery** | **Adafruit #1578 — protected 3.7 V, 500 mAh LiPo** | **[Adafruit](https://www.adafruit.com/product/1578)** | **$7.95**, shown in stock when checked. Includes protection and a JST-PH lead. Adafruit explicitly permits charging at **500 mA or less**, matching our selected charging rate. |
| **2 caps** | **Sprintek 109-00060 black rubber cap** | **[Sprintek store](https://store.sprintek.com/category/flexpoint-pointing-stick)** | **$1 each** at this quantity. One for the reader and one spare. Find **109-00060** on the page. Astra’s printed stem adapter connects it to our navigation module. |

### Check the display availability first

**Both Good Display shop pages returned “0 in stock” alongside their ordering controls.** That may reflect their default option state, but immediate availability is unconfirmed. Check the selected variant before relying on a shipping date.

The [panel page](https://buy-lcd.com/products/gdem0397t81p) also offers **“EPD with adapter board.”** You can use that option if it specifies the **DESPI-C02**; then omit the separate adapter. The separate displayed prices total **$23.38**, but the selected bundle price was not verified.

References: [current GDEY0397T81P manufacturer page](https://www.good-display.com/product/613.html) and [DESPI-C02 manufacturer page](https://www.good-display.com/product/516.html).

## Amazon supplies — buy only what is missing from the bench

| Buy if needed | Item | Amazon link | Purpose |
|---|---|---|---|
| **1 kit** | **BNTECHGO 28 AWG stranded silicone wire** | **[10-color kit](https://www.amazon.com/dp/B01M5EY57C)** | Ten colors, 10 ft each, with stranded tinned-copper conductors. Plenty for the internal harness and future builds. Keep the battery’s factory leads. |
| **1 roll** | **Tapes Master polyimide tape, ¼″ wide** | **[Polyimide tape](https://www.amazon.com/dp/B01LZRMJVR)** | Thin electrical insulation and tidy routing around boards and solder joints. |
| **1 assortment** | **Eventronic small heat-shrink tubing** | **[2:1 heat-shrink assortment](https://www.amazon.com/dp/B072PCQ2LW)** | Insulating harness connections. The assortment includes small sizes suitable for this work. |
| **Optional** | **USB-C data cable** | **[Cable Matters 6″ USB-A → USB-C, three-pack](https://www.amazon.com/dp/B07PDHZM71)** | Reuse an existing data-capable cable if available. This option supports charging and USB data; choose it only if a short cable and USB-A host connection suit the setup. |

Supporting manufacturer references:

- [BNTECHGO 28 AWG, 10 colors × 10 ft, stranded tinned-copper silicone wire](https://bntechgo.com/bntechgo-28-gauge-silicone-wire-kit-ultra-flexible-10-colors-each-10-ft-high-temp-200-c-600v-28-awg-silicone-wire-16-strands-of-tinned-copper-wire-stranded-wire-for-model-battery/)
- [Tapes Master ¼″ × 36 yd polyimide tape](https://tapesmaster.com/products/1-mil-kapton-tape-polyimide-1-4-x-36-yds)
- [Cable Matters Slim Series USB-A to USB-C cables — USB 2.0 data support](https://www.cablematters.com/pc-1131-123-3-pack-usb-type-c-usb-c-to-type-a-usb-a-cable.aspx)

## Already covered, or waiting on Astra

- **BACK/MARK switches:** use two existing 6 × 6 tactiles.
- **Shell materials:** existing acid green, black, cyan, and magenta filaments.
- **USB connector, charging circuit, and microSD socket:** included on the selected S3 PRO board. See the [WEMOS specifications](https://www.wemos.cc/en/latest/s3/s3_pro.html).
- **Screws, threaded inserts, gasket/padding thickness, and any USB-sensing components:** Astra should specify these from the finished mechanical and electrical design. Those dimensions are not frozen yet.

## Update for Astra

> I already have 6 × 6 tactile switches. Use those for BACK and MARK; confirm their plunger height and leg layout before finalizing the carriers.

