"""Build the R04 approval sheet from the current layout ledger and renders.

This is a review document, not a production drawing or a fabrication template.
Run from any directory; images are read again on each run.
"""
from __future__ import annotations

import json
from pathlib import Path
from html import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "source/component_layout.json"
OUTPUT = ROOT / "WeazlBook_R04_approval.pdf"
RENDERS = ROOT / "render"
FONTS = ROOT.parent / "research/fonts"
MM = 72 / 25.4
PW, PH = landscape(A4)
M = 32

pdfmetrics.registerFont(TTFont("Plex", str(FONTS / "IBMPlexMono-Regular.ttf")))
pdfmetrics.registerFont(TTFont("Plex-Semi", str(FONTS / "IBMPlexMono-SemiBold.ttf")))
pdfmetrics.registerFontFamily("Plex", normal="Plex", bold="Plex-Semi")

INK = colors.HexColor("#141A19")
DARK = colors.HexColor("#111516")
ACID = colors.HexColor("#9EE20A")
PAPER = colors.HexColor("#F5F6F0")
MUTED = colors.HexColor("#55615C")
RULE = colors.HexColor("#CCD2C6")
BLUE = colors.HexColor("#08779B")
CELL = colors.HexColor("#68786A")
NAV = colors.HexColor("#217957")
S3 = colors.HexColor("#364550")
MAGENTA = colors.HexColor("#B80A57")
AMBER = colors.HexColor("#A76205")

DATA = json.loads(LEDGER.read_text())
PARTS = {p["name"]: p for p in DATA["parts"]}
SHELL = [(7, 0), (73, 0), (80, 7), (80, 141), (73, 156),
         (7, 156), (0, 141), (0, 7)]


def para(c, text, x, top, width, size=11, color=INK, bold=False,
         leading=None, max_height=None):
    st = ParagraphStyle("p", fontName="Plex-Semi" if bold else "Plex",
                        fontSize=size, leading=leading or size * 1.28,
                        textColor=color, spaceAfter=0, allowWidows=0,
                        allowOrphans=0, splitLongWords=1)
    p = Paragraph(text, st)
    _, h = p.wrap(width, 10000)
    if max_height is not None and h > max_height + 0.5:
        raise ValueError(f"Paragraph too high: {h:.1f} > {max_height}: {text[:100]}")
    p.drawOn(c, x, top - h)
    return top - h


def line(c, x1, y1, x2, y2, color=RULE, width=0.6, dash=None):
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(width)
    if dash:
        c.setDash(dash)
    c.line(x1, y1, x2, y2)
    c.restoreState()


def base(c, page, title, subtitle, dark=False):
    c.setFillColor(DARK if dark else (colors.white if page == 4 else PAPER))
    c.rect(0, 0, PW, PH, stroke=0, fill=1)
    c.setFillColor(ACID)
    c.rect(M, PH - 19, PW - 2 * M, 4, stroke=0, fill=1)
    c.setFont("Plex-Semi", 25 if page != 1 else 30)
    c.setFillColor(ACID if dark else INK)
    c.drawString(M, PH - 54, title)
    para(c, subtitle, M, PH - 66, PW - 2 * M, 11,
         colors.HexColor("#CFD7CB") if dark else MUTED, max_height=32)
    c.setFillColor(colors.HexColor("#B3C1AD") if dark else MUTED)
    c.setFont("Plex", 9)
    c.drawString(M, 18, "WEAZLBOOK / R04 / APPROVAL MOCKUP - NOT PRINT-READY")
    c.drawRightString(PW - M, 18, f"{page:02d} / 04")


def image_fit(c, name, x, y, width, height):
    path = RENDERS / name
    if not path.exists():
        return False
    img = ImageReader(str(path))
    iw, ih = img.getSize()
    scale = min(width / iw, height / ih)
    w, h = iw * scale, ih * scale
    c.drawImage(img, x + (width - w) / 2, y + (height - h) / 2,
                w, h, preserveAspectRatio=True, mask="auto")
    return True


def poly(c, pts, fill=None, stroke=INK, width=1):
    p = c.beginPath()
    p.moveTo(*pts[0])
    for pt in pts[1:]:
        p.lineTo(*pt)
    p.close()
    c.setStrokeColor(stroke)
    c.setLineWidth(width)
    if fill is not None:
        c.setFillColor(fill)
    c.drawPath(p, fill=int(fill is not None), stroke=1)


def plan_xy(x, y, ox, oy):
    return ox + x * MM, oy + (156 - y) * MM


def plan_rect(c, ox, oy, x, y, w, h, color, fill_alpha=.13,
              dash=None, width=1, fill=True):
    px, py = plan_xy(x, y + h, ox, oy)
    c.saveState()
    c.setLineWidth(width)
    c.setStrokeColor(color)
    if dash:
        c.setDash(dash)
    if fill:
        c.setFillColor(color)
        c.setFillAlpha(fill_alpha)
        c.rect(px, py, w * MM, h * MM, stroke=0, fill=1)
        c.setFillAlpha(1)
    c.rect(px, py, w * MM, h * MM, stroke=1, fill=0)
    c.restoreState()


def badge(c, label, x, y, color=INK, radius=8):
    c.saveState()
    c.setFillColor(color)
    c.circle(x, y, radius, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Plex-Semi", 11)
    c.drawCentredString(x, y - 3.7, label)
    c.restoreState()


def dim_h(c, x1, x2, y, label, text_offset=5, color=INK):
    line(c, x1, y, x2, y, color, .65)
    line(c, x1, y - 3, x1, y + 3, color, .65)
    line(c, x2, y - 3, x2, y + 3, color, .65)
    c.setFont("Plex", 11)
    c.setFillColor(color)
    c.drawCentredString((x1 + x2) / 2, y + text_offset, label)


def dim_v(c, x, y1, y2, label):
    line(c, x, y1, x, y2, INK, .65)
    line(c, x - 3, y1, x + 3, y1, INK, .65)
    line(c, x - 3, y2, x + 3, y2, INK, .65)
    c.saveState()
    c.translate(x - 7, (y1 + y2) / 2)
    c.rotate(90)
    c.setFont("Plex", 11)
    c.setFillColor(INK)
    c.drawCentredString(0, 0, label)
    c.restoreState()


def front_outline(c, ox, oy, fill=colors.white):
    poly(c, [plan_xy(x, y, ox, oy) for x, y in SHELL], fill, INK, 1.05)


def front_plan(c, ox, oy):
    front_outline(c, ox, oy)
    plan_rect(c, ox, oy, 11.88, 9, 56.24, 96.62, MUTED, .04)
    plan_rect(c, ox, oy, 14.08, 11.2, 51.84, 86.4, MUTED, fill=False, dash=[2, 2])
    plan_rect(c, ox, oy, 10, 122, 65.3, 25.4, S3, .14)
    plan_rect(c, ox, oy, 7.13, 54, 22, 41, BLUE, .20)
    plan_rect(c, ox, oy, 7.7, 48, 20.8, 6, BLUE, .08, [3, 2])
    plan_rect(c, ox, oy, 40, 75, 32, 38, CELL, .20)
    plan_rect(c, ox, oy, 41, 76, 30, 36, CELL, fill=False, width=.5)
    plan_rect(c, ox, oy, 11.5, 91, 40.5, 25, AMBER, .17, [3, 2])
    plan_rect(c, ox, oy, 28, 117, 31, 25, NAV, .20)
    plan_rect(c, ox, oy, 59, 117, 12, 25, NAV, .07, [3, 2])
    for x in (18, 50):
        plan_rect(c, ox, oy, x, 143, 12, 10, MAGENTA, .18)
    plan_rect(c, ox, oy, 2.4, 124, 7, 12.7, AMBER, .20, [2, 2])
    # Access space, not a fictitious USB extension cable.
    plan_rect(c, ox, oy, 0, 135.5, 11, 15.5, INK, .03, [2, 2])
    for label, x, y, col in [
        ("1", 40, 26, MUTED), ("2", 18.13, 71, BLUE),
        ("3", 56, 89, CELL), ("4", 40, 129.5, NAV),
        ("5", 68.5, 145, S3), ("6", 24, 148, MAGENTA),
        ("6", 56, 148, MAGENTA), ("7", 33, 107.5, AMBER)]:
        badge(c, label, *plan_xy(x, y, ox, oy), col)
    # Cross is the photo-estimated nav stem datum; not a hole pattern.
    sx, sy = plan_xy(40, 129.5, ox, oy)
    c.saveState()
    c.setStrokeColor(NAV)
    c.setDash([2, 2])
    c.circle(sx, sy, 7 * MM, fill=0, stroke=1)
    c.restoreState()


def side(c, ox, oy, components=False, paper_check=False):
    def p(z, y):
        return ox + z * MM, oy + (156 - y) * MM
    poly(c, [p(0, 0), p(14, 0), p(26, 156), p(0, 156)],
         colors.white, INK, 1.05)
    if components:
        # Rear cover inner surface: nominal, not a tolerance model.
        line(c, *p(11.8, 0), *p(23.8, 156), MUTED, .7, [3, 2])
        # Each rectangle is an X-projection. Overlap in this view can be
        # between components that occupy different X positions.
        for z, y, dz, dy, col, dashed in [
            (2.2, 9, 1.02, 96.62, MUTED, False),
            (3.22, 8.7, 1.28, 97.22, MUTED, True),
            (5.5, 54, 8, 41, BLUE, True),
            (9.5, 75, 7, 38, CELL, True),
            (3, 91, 5, 25, AMBER, True),
            (9.4, 117, 3.1, 25, NAV, True),
            (3.4, 122, 6, 15, NAV, True),
            (14, 122, 1.6, 25.4, S3, False),
            (15.6, 125.7, 3.25, 18.2, S3, True),
            (15.6, 128.7, 5.5, 8.4, AMBER, True),
            (14.9, 124, 6.2, 12.7, AMBER, True),
            (15.6, 137.8, 3.8, 9.1, S3, True),
            (3.5, 143, 9, 10, MAGENTA, True),
        ]:
            plan_rect(c, ox, oy, z, y, dz, dy, col, .20,
                      [2, 2] if dashed else None, .6)
    # Nominal cap protrusion, kept distinct from the shell depth.
    plan_rect(c, ox, oy, -3.95, 124.7, 3.95, 9.6, MAGENTA,
              .12 if components else 0, [2, 2], .7, fill=components)
    # Top dimension sits inside the depth envelope; its label is outside
    # the profile so it cannot collide with the view heading.
    top_dim_y = oy + 156 * MM - 9
    dim_h(c, ox, ox + 14 * MM, top_dim_y, "", 0)
    c.setFillColor(INK)
    c.setFont("Plex", 11)
    c.drawString(ox + 14 * MM + 8, top_dim_y - 4, "14")
    dim_h(c, ox, ox + 26 * MM, oy - 13, "26", -13)
    if paper_check:
        line(c, *p(-4.5, 129.5), ox - 29, p(0, 129.5)[1], MUTED, .65)
        para(c, "3.95<br/>nub", ox - 50, p(0, 129.5)[1] + 14,
             40, 11, MUTED)


def overview(c):
    base(c, 1, "weazlbook", "R04 / ORIGINAL TAPER / DIMENSIONAL APPROVAL", True)
    para(c, "80 x 156 mm shell<br/>14 mm top / 26 mm grip",
         491, PH - 41, 315, 12, ACID, bold=True, max_height=40)
    image_fit(c, "assembled.png", 40, 129, 254, 379)
    image_fit(c, "left_profile.png", 318, 146, 117, 361)
    image_fit(c, "rear_open.png", 480, 129, 293, 379)
    para(c, "01  ASSEMBLED", 49, 112, 252, 12, ACID, True)
    para(c, "Portrait screen. Black cap.<br/>Separate BACK / MARK keys.",
         49, 93, 262, 11, colors.HexColor("#CFD7CB"), max_height=34)
    para(c, "02  SIDE", 321, 112, 143, 12, ACID, True)
    para(c, "Taper excludes<br/>3.95 mm nub.", 321, 93, 147, 11,
         colors.HexColor("#CFD7CB"), max_height=34)
    para(c, "03  REAR OPEN", 486, 112, 286, 12, ACID, True)
    para(c, "Actual rear view: left/right reverse.<br/>Blocks show reserved occupied space.",
         486, 93, 294, 11, colors.HexColor("#CFD7CB"), max_height=34)
    line(c, M, 48, PW - M, 48, colors.HexColor("#344138"))
    para(c, "Screen content is illustrative. This review approves shape and packaging direction.",
         M, 41, PW - 2 * M, 11, colors.HexColor("#CFD7CB"), max_height=17)
    c.showPage()


def dimensional_layout(c):
    base(c, 2, "SPACE FOR THE HARDWARE", "Exact drawing scale 1:1 at 100% print. All dimensions in mm; X right, Y down, Z into the case.")
    ox, oy, sx = 63, 58, 337
    para(c, "FRONT PROJECTION", ox, 515, 245, 11, INK, True)
    para(c, "Z PROJECTION", sx - 13, 515, 126, 11, INK, True)
    front_plan(c, ox, oy)
    side(c, sx, oy, components=True)
    dim_v(c, 43, oy, oy + 156 * MM, "156")
    dim_h(c, ox, ox + 80 * MM, oy - 13, "80", -13)
    rx, rw, top = 445, PW - 445 - M, 513
    entries = [
        ("1", MUTED, "DISPLAY", "56.24 x 96.62 at X11.88 / Y9."),
        ("2", BLUE, "DRIVER LEFT", "22 x 41 at X7.13 / Y54; Z5.5-13.5."),
        ("3", CELL, "CELL BAY RIGHT", "32 x 38 at X40 / Y75; Z9.5-16.5."),
        ("4", NAV, "FIVE-WAY NAV", "31 x 25 at X28 / Y117; rear <=Z12.5.*"),
        ("5", S3, "LOLIN S3 PRO", "65.3 x 25.4 at X10 / Y122; PCB Z14-15.6.*"),
        ("6", MAGENTA, "BACK / MARK", "12 x 10 bays, X18 and X50 / Y143; 9 deep.*"),
        ("7", AMBER, "FPC FOLD ALLOWANCE", "X11.5-52 / Y91-116 / Z3-8. Provisional."),
    ]
    for lab, col, title, desc in entries:
        badge(c, lab, rx + 8, top - 8, col)
        para(c, title, rx + 25, top, rw - 25, 11, col, True)
        para(c, desc, rx + 25, top - 16, rw - 25, 11, INK,
             max_height=30)
        top -= 49
    line(c, rx, top + 5, PW - M, top + 5)
    y = para(c, "* Reserved assembly dimensions. Published PCB footprints do not establish installed height.",
             rx, top - 7, rw, 11, MUTED)
    y = para(c, "Side view projects every X position. Some apparent overlaps are parts side by side in X.",
             rx, y - 9, rw, 11, MUTED)
    para(c, "Front projection reverses when viewed from the rear. Dashed outlines are allowances; amber also marks the PH plug/lead check.",
         rx, y - 9, rw, 11, MUTED, max_height=58)
    c.showPage()


def linked(c, label, url, x, top, width, color=INK):
    return para(c, f'<link href="{escape(url, quote=True)}" color="{color.hexval()}">{escape(label)}</link>',
                x, top, width, 11, color)


def fit_ledger(c):
    base(c, 3, "PUBLISHED PARTS / RESERVED SPACE", "Source links are attached to each part name. Full manufacturer geometry and measured assemblies remain distinct.")
    x = M
    widths = [184, 210, PW - 2 * M - 394]
    xs = [x, x + widths[0], x + widths[0] + widths[1]]
    top = 491
    c.setFillColor(INK)
    c.rect(x, top - 27, PW - 2 * M, 27, stroke=0, fill=1)
    for title, xx, ww in zip(["PART / SOURCE", "PUBLISHED", "R04 PACKAGING ALLOWANCE"], xs, widths):
        para(c, title, xx + 9, top - 7, ww - 18, 11, colors.white, True)
    rows = [
        ("1  DISPLAY", "GDEY0397T81P", "56.24 x 96.62 x 0.92<br/>Tolerance: +/-0.2/0.2/0.1", "Glass Z2.2-3.22 includes upper tolerance.<br/>A separate insulation space sits behind.", 45),
        ("2  DRIVER", "DESPI-C02", "41 x 22 PCB.<br/>24-pin FPC; 3.3 V SPI.", "8 mm full-depth space, Z5.5-13.5.<br/>6 mm header projection; height unmeasured.", 45),
        ("3  BATTERY", "Adafruit 1578 500mAh", "29 x 36 x 4.75 catalog.<br/>Protected 500 mAh cell.", "Cell envelope 30 x 36 x 6;<br/>bay 32 x 38 x 7. Retain factory leads.", 45),
        ("4  NAV MODULE", "EC Buying navigation", "31 x 25 PCB; holes 3 dia.<br/>Stem location photo-derived.", "Rear limit Z12.5 is provisional.<br/>12 mm for side header and wiring.", 45),
        ("5  MAINBOARD", "LOLIN S3 PRO", "65.3 x 25.4 PCB.<br/>USB + microSD onboard.", "PCB Z14-15.6; local connectors to Z21.1.<br/>Port/plug shapes are simplified allowances.", 45),
        ("6  TWO TACTILES", "2 x Omron B3F-1000", "6 x 6 x 4.3 each.<br/>7.7 lead-inclusive width.", "Each installed bay 12 x 10 x 9.<br/>Printed keys and guides above the switches.", 45),
        ("CAP + ADAPTER", "Sprintek 109-00060 rubber cap", "Fits 2.4 mm square or<br/>3.15 mm round Sprintek stem.", "Shown cap dia.9.6 x 2.3 is provisional.<br/>Keep dia.14 sweep; measure adapter/socket.", 45),
    ]
    top -= 27
    for i, (title, name, published, reserve, rh) in enumerate(rows):
        c.setFillColor(colors.white if i % 2 == 0 else colors.HexColor("#EAEDE4"))
        c.rect(x, top - rh, PW - 2 * M, rh, stroke=0, fill=1)
        para(c, title, xs[0] + 9, top - 7, widths[0] - 18, 11, INK, True)
        url = PARTS[name]["source"]
        label = {"Adafruit 1578 500mAh": "Adafruit #1578",
                 "Sprintek 109-00060 rubber cap": "Sprintek 109-00060",
                 "2 x Omron B3F-1000": "Omron B3F-1000",
                 "EC Buying navigation": "EC Buying / Amazon"}.get(name, name)
        linked(c, label + " >", url, xs[0] + 9, top - 22, widths[0] - 18, BLUE)
        para(c, published, xs[1] + 9, top - 7, widths[1] - 18, 11, INK, max_height=rh - 10)
        para(c, reserve, xs[2] + 9, top - 7, widths[2] - 18, 11, INK, max_height=rh - 10)
        line(c, x, top - rh, PW - M, top - rh)
        top -= rh
    # The panel source is also the source of the 33.66 mm FPC drawing.
    text_width = 650
    y = para(c, "FPC: 33.66 mm published tail reach. R2 fold and seated-tip Y93 are proposed; the driver carrier needs insertion-depth adjustment.",
             M, 135, text_width, 11, AMBER, max_height=32)
    y = para(c, "PH/JST region reaches Z21.1. Only about 0.2-0.6 mm nominal rear-cover clearance remains locally; this is a measured-fit gate.",
             M, y - 8, text_width, 11, INK, max_height=32)
    para(c, "Amber blocks are FPC and plug/lead check space. Colored strands show harness corridors, not a final wire count or pinout.",
         M, y - 8, text_width, 11, MUTED, max_height=32)
    if image_fit(c, "inside_cover.png", 706, 40, 104, 104):
        para(c, "INSIDE COVER", 703, 35, 111, 9.5, MUTED)
    c.showPage()


def paper_front(c, ox, oy):
    front_outline(c, ox, oy, colors.white)
    plan_rect(c, ox, oy, 8, 5, 64, 103.8, INK, fill=False, width=.65)
    plan_rect(c, ox, oy, 14.08, 11.2, 51.84, 86.4, INK, fill=False, width=.7)
    tx, ty = plan_xy(40, 42, ox, oy)
    c.setFillColor(MUTED)
    c.setFont("Plex", 11)
    c.drawCentredString(tx, ty, "READING AREA")
    c.drawCentredString(tx, ty - 16, "51.84 x 86.40")
    c.saveState()
    c.setStrokeColor(INK)
    cx, cy = plan_xy(40, 129.5, ox, oy)
    c.circle(cx, cy, 4.8 * MM, stroke=1, fill=0)
    c.setDash([2, 2])
    c.circle(cx, cy, 7 * MM, stroke=1, fill=0)
    c.restoreState()
    for xx in (19, 51):
        plan_rect(c, ox, oy, xx, 145.5, 10, 6, INK, fill=False)
    # No fastener locations: this page is for hand spacing, not drilling.


def paper_check(c):
    base(c, 4, "ONE-TO-ONE PAPER CHECK", "Approve hand spacing and profile. The outline is not a drill, cut or production template.")
    ox, oy, sx = 62, 58, 348
    para(c, "FRONT / 1:1", ox, 515, 230, 11, INK, True)
    para(c, "SIDE / 1:1", sx - 10, 515, 120, 11, INK, True)
    paper_front(c, ox, oy)
    side(c, sx, oy, paper_check=True)
    dim_v(c, 43, oy, oy + 156 * MM, "156")
    dim_h(c, ox, ox + 80 * MM, oy - 13, "80", -13)
    rx, rw, y = 471, PW - 471 - M, 508
    y = para(c, "FOUR MEASUREMENTS TO CLOSE", rx, y, rw, 12, INK, True)
    gates = [
        ("01 / DISPLAY ASSEMBLY", "Delivered GDEY panel suffix; adapter height, slot position and insertion depth; gentle FPC fold with strain relief."),
        ("02 / NAV + CAP", "Stem and cap socket, installed depth, lateral sweep and select travel. Keep the carrier replaceable."),
        ("03 / USB + BATTERY PLUG", "Actual housings, cable boot and lead turn together. The left opening is an open recess; the PH check volume is provisional."),
        ("04 / CELL + SERVICE", "Protected cell thickness and wire exit; rear-cover clearance and rear-only microSD access. Retain factory battery leads."),
    ]
    y -= 15
    for title, body in gates:
        y = para(c, title, rx, y, rw, 11, BLUE, True)
        y = para(c, body, rx, y - 4, rw, 11, INK)
        y -= 14
    line(c, rx, y + 4, PW - M, y + 4)
    y = para(c, "Print at 100% / Actual Size.<br/>Disable Fit to Page.<br/>Verify this bar measures 50 mm.",
             rx, y - 7, rw, 11, INK)
    bar_y = y - 17
    dim_h(c, rx, rx + 50 * MM, bar_y, "50 mm", -17)
    para(c, "Short 28 AWG device harness.<br/>No measured runtime or working firmware is represented by this mockup.",
         rx, bar_y - 32, rw, 11, MUTED, max_height=46)
    c.showPage()


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    c = Canvas(str(OUTPUT), pagesize=(PW, PH), pageCompression=1,
               invariant=1, initialFontName="Plex")
    c.setTitle("WeazlBook R04 - dimensional approval mockup")
    c.setAuthor("WeazlBook")
    c.setSubject("Original tapered body, component packaging, provisional fit gates and 1:1 paper check")
    overview(c)
    dimensional_layout(c)
    fit_ledger(c)
    paper_check(c)
    c.save()
    print(OUTPUT)


if __name__ == "__main__":
    main()
