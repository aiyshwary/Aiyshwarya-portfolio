"""
Generates professional, emoji-free PDFs for all projects defined in projects.json.
Outputs directly to assets/projects/ with consistent typography throughout.
"""

import json
import os
import textwrap
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit

# ── Palette ─────────────────────────────────────────────────────────────────
COLOR_BG        = HexColor("#0f1117")   # dark page background
COLOR_HEADER_BG = HexColor("#1a1d2e")   # header block
COLOR_ACCENT    = HexColor("#38bdf8")   # sky-blue accent (matches portfolio)
COLOR_BODY      = HexColor("#cbd5e1")   # body text (light slate)
COLOR_SUBTLE    = HexColor("#64748b")   # labels / section headers
COLOR_WHITE     = HexColor("#f1f5f9")   # title / headings
COLOR_BULLET_BG = HexColor("#1e2435")   # bullet card background
COLOR_TECH_BG   = HexColor("#172033")   # tech pill background
COLOR_DIVIDER   = HexColor("#2e3650")   # divider lines

# ── Typography ───────────────────────────────────────────────────────────────
FONT            = "Helvetica"
FONT_BOLD       = "Helvetica-Bold"

SIZE_TITLE      = 20
SIZE_SUMMARY    = 10
SIZE_SECTION    = 9       # section label (OVERVIEW, IMPACT, etc.)
SIZE_BODY       = 10
SIZE_BULLET     = 10
SIZE_TECH       = 8.5
SIZE_FOOTER     = 8

# ── Layout ───────────────────────────────────────────────────────────────────
PAGE_W, PAGE_H  = A4
MARGIN_L        = 2.2 * cm
MARGIN_R        = 2.2 * cm
MARGIN_T        = 2.0 * cm
MARGIN_B        = 2.0 * cm
CONTENT_W       = PAGE_W - MARGIN_L - MARGIN_R
LINE_H_BODY     = 15      # px between body lines
LINE_H_BULLET   = 15

HEADER_H        = 3.8 * cm


def draw_rounded_rect(c, x, y, w, h, r, fill_color, stroke=False):
    c.saveState()
    c.setFillColor(fill_color)
    if stroke:
        c.setStrokeColor(COLOR_DIVIDER)
        c.setLineWidth(0.5)
    else:
        c.setStrokeColor(fill_color)
    c.roundRect(x, y, w, h, r, fill=1, stroke=1 if stroke else 0)
    c.restoreState()


def wrapped_lines(text, font, size, max_width):
    """Return list of lines that fit within max_width."""
    return simpleSplit(text, font, size, max_width)


def draw_text_block(c, text, x, y, font, size, color, max_width, line_height):
    """Draw wrapped text, return new y position."""
    c.setFont(font, size)
    c.setFillColor(color)
    lines = wrapped_lines(text, font, size, max_width)
    for line in lines:
        c.drawString(x, y, line)
        y -= line_height
    return y


def generate_pdf(project, out_path):
    c = canvas.Canvas(out_path, pagesize=A4)
    c.setTitle(project["title"])
    c.setAuthor("Aiyshwarya Aruchamy")

    # ── Page background ──────────────────────────────────────────────────────
    c.setFillColor(COLOR_BG)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # ── Header block ─────────────────────────────────────────────────────────
    header_y = PAGE_H - HEADER_H
    draw_rounded_rect(c, 0, header_y, PAGE_W, HEADER_H, 0, COLOR_HEADER_BG)

    # Accent top stripe
    c.setFillColor(COLOR_ACCENT)
    c.rect(0, PAGE_H - 4, PAGE_W, 4, fill=1, stroke=0)

    # Title
    c.setFont(FONT_BOLD, SIZE_TITLE)
    c.setFillColor(COLOR_WHITE)
    c.drawString(MARGIN_L, PAGE_H - 1.3 * cm, project["title"])

    # GitHub URL (small, accent colour)
    if project.get("github"):
        c.setFont(FONT, 8)
        c.setFillColor(COLOR_ACCENT)
        c.drawString(MARGIN_L, PAGE_H - 1.9 * cm, project["github"])

    # Tech pills
    techs = project.get("techs", [])
    pill_x = MARGIN_L
    pill_y = PAGE_H - 2.85 * cm
    pill_h = 0.48 * cm
    pill_pad = 0.28 * cm
    for tech in techs:
        c.setFont(FONT_BOLD, SIZE_TECH)
        tw = c.stringWidth(tech, FONT_BOLD, SIZE_TECH)
        pill_w = tw + 2 * pill_pad
        if pill_x + pill_w > PAGE_W - MARGIN_R:
            break
        draw_rounded_rect(c, pill_x, pill_y, pill_w, pill_h, 3, COLOR_TECH_BG)
        c.setFillColor(COLOR_ACCENT)
        c.setFont(FONT_BOLD, SIZE_TECH)
        c.drawString(pill_x + pill_pad, pill_y + 0.12 * cm, tech)
        pill_x += pill_w + 0.2 * cm

    # ── Body content ─────────────────────────────────────────────────────────
    y = header_y - 0.6 * cm

    # Helper: section label
    def section_label(label, ypos):
        c.setFont(FONT_BOLD, SIZE_SECTION)
        c.setFillColor(COLOR_ACCENT)
        c.drawString(MARGIN_L, ypos, label.upper())
        ypos -= 0.15 * cm
        # thin divider
        c.setStrokeColor(COLOR_DIVIDER)
        c.setLineWidth(0.5)
        c.line(MARGIN_L, ypos, PAGE_W - MARGIN_R, ypos)
        return ypos - 0.35 * cm

    # ── OVERVIEW ─────────────────────────────────────────────────────────────
    y = section_label("Overview", y)
    y = draw_text_block(c, project["summary"], MARGIN_L, y,
                        FONT, SIZE_BODY, COLOR_BODY, CONTENT_W, LINE_H_BODY)

    y -= 0.5 * cm

    # ── IMPACT ───────────────────────────────────────────────────────────────
    y = section_label("Impact", y)
    y = draw_text_block(c, project["impact"], MARGIN_L, y,
                        FONT, SIZE_BODY, COLOR_BODY, CONTENT_W, LINE_H_BODY)

    y -= 0.5 * cm

    # ── KEY DETAILS ──────────────────────────────────────────────────────────
    y = section_label("Key Details", y)

    bullets = project.get("bullets", [])
    bullet_pad_x = 0.35 * cm
    bullet_pad_y = 0.25 * cm
    bullet_inner_w = CONTENT_W - 2 * bullet_pad_x - 0.6 * cm  # minus dash + gap

    for bullet in bullets:
        # Measure height needed
        lines = wrapped_lines(bullet, FONT, SIZE_BULLET, bullet_inner_w)
        block_h = len(lines) * LINE_H_BULLET + 2 * bullet_pad_y

        # Page overflow: start new page
        if y - block_h < MARGIN_B + 0.5 * cm:
            c.showPage()
            c.setFillColor(COLOR_BG)
            c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
            # accent stripe on continuation pages
            c.setFillColor(COLOR_ACCENT)
            c.rect(0, PAGE_H - 4, PAGE_W, 4, fill=1, stroke=0)
            c.setFillColor(HexColor("#1a1d2e"))
            c.rect(0, PAGE_H - 0.8 * cm, PAGE_W, 0.8 * cm, fill=1, stroke=0)
            c.setFont(FONT, 7)
            c.setFillColor(COLOR_SUBTLE)
            c.drawString(MARGIN_L, PAGE_H - 0.55 * cm, project["title"] + " (continued)")
            y = PAGE_H - 1.3 * cm

        draw_rounded_rect(c, MARGIN_L, y - block_h, CONTENT_W, block_h, 4,
                          COLOR_BULLET_BG, stroke=True)

        # Dash bullet
        c.setFont(FONT_BOLD, SIZE_BULLET)
        c.setFillColor(COLOR_ACCENT)
        c.drawString(MARGIN_L + bullet_pad_x, y - bullet_pad_y - LINE_H_BULLET + 3, "-")

        # Bullet text
        text_x = MARGIN_L + bullet_pad_x + 0.55 * cm
        text_y = y - bullet_pad_y
        c.setFont(FONT, SIZE_BULLET)
        c.setFillColor(COLOR_BODY)
        for line in lines:
            c.drawString(text_x, text_y, line)
            text_y -= LINE_H_BULLET

        y -= block_h + 0.2 * cm

    # ── Footer ────────────────────────────────────────────────────────────────
    def draw_footer(canvas_obj):
        canvas_obj.setFillColor(COLOR_DIVIDER)
        canvas_obj.rect(0, MARGIN_B - 0.4 * cm, PAGE_W, 0.5, fill=1, stroke=0)
        canvas_obj.setFont(FONT, SIZE_FOOTER)
        canvas_obj.setFillColor(COLOR_SUBTLE)
        canvas_obj.drawString(MARGIN_L, MARGIN_B - 0.6 * cm, "Aiyshwarya Aruchamy  |  Portfolio Project")
        canvas_obj.drawRightString(PAGE_W - MARGIN_R, MARGIN_B - 0.6 * cm,
                                   "github.com/aiyshwary")

    draw_footer(c)
    c.save()
    print(f"  Generated: {out_path}")


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "projects.json")
    out_dir   = os.path.join(base_dir, "assets", "projects")
    os.makedirs(out_dir, exist_ok=True)

    with open(json_path) as f:
        projects = json.load(f)

    print(f"Generating {len(projects)} PDFs...\n")
    for p in projects:
        pdf_rel = p.get("pdf", "")
        if not pdf_rel:
            print(f"  Skipping {p['title']} — no pdf field")
            continue
        out_path = os.path.join(base_dir, pdf_rel)
        generate_pdf(p, out_path)

    print("\nDone.")
