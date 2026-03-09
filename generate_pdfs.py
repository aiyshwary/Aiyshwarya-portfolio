"""
Generates comprehensive, professional PDFs for all portfolio projects.

Content is sourced from TWO places:
  - projects.json  → structured title, github, techs, summary, impact, bullets
  - Project_Explanation_Detailed copy/*.pdf → full technical walkthrough (cleaned)

All emojis, orphaned bullet symbols, and interview-coaching notes are stripped.
Font sizes are uniform (10 pt body) throughout every PDF.
"""

import json
import os
import re

import pypdf
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

# ── Colour palette ────────────────────────────────────────────────────────────
C_BG      = HexColor("#0f1117")
C_HDR     = HexColor("#1a1d2e")
C_ACCENT  = HexColor("#38bdf8")
C_BODY    = HexColor("#cbd5e1")
C_SUBTLE  = HexColor("#64748b")
C_WHITE   = HexColor("#f1f5f9")
C_CARD    = HexColor("#1e2435")
C_TECH    = HexColor("#172033")
C_DIV     = HexColor("#2e3650")

# ── Typography — one body size used everywhere ────────────────────────────────
F   = "Helvetica"
FB  = "Helvetica-Bold"
S_TITLE   = 20
S_SECTION = 9      # section-label caps
S_BODY    = 10     # every paragraph, bullet, heading in the body
S_TECH    = 8.5
S_FOOTER  = 8
LH        = 15     # line height (pts)

# ── Page geometry ─────────────────────────────────────────────────────────────
PW, PH = A4
ML = 2.2 * cm
MR = 2.2 * cm
MB = 2.0 * cm
CW = PW - ML - MR     # usable content width
HDR_H = 3.8 * cm

# ── Source-PDF directory + title → filename map ───────────────────────────────
SRC_DIR = "Project_Explanation_Detailed copy"

SRC_MAP = {
    "Annotation Transfer Tool":                   "Annotation Transfer Tool.pdf",
    "Bus Reservation And Ticketing System":        "Bus Reservation and Ticketing System.pdf",
    "Facial Emotion Recognition":                  "Facial Emotion Recognition.pdf",
    "Hybrid Search & Retrieval POC":               "Hybrid Search & Retrieval POC.pdf",
    "Image Classification Extension":              "Image Classification Extension.pdf",
    "Mammalia Raccoon Proximity Network Analysis": "Mammalia Raccoon Proximity Network Analysis.pdf",
    "Object Detection Extension":                  "Object Detection Extension.pdf",
    "Online Event Management System":              "Online Event Management System.pdf",
    "Sentiment Analysis Extension":                "Sentiment Analysis Extension.pdf",
    "Synthetic Image Generation":                  "Synthetic Image Generation.pdf",
    "Multi-Agent Architecture":                    "Multi-Agent-Architecture.pdf",
    "Video RAG Retrieval Project":                 "Video RAG Retrieval Project.pdf",
    "Traffic Monitoring System":                   "Traffic Monitoring System.pdf",
}

# ── Text-cleaning helpers ─────────────────────────────────────────────────────
_KEYCAP_RE   = re.compile(r'\d\u20E3|\u20E3')
_VARSEL_RE   = re.compile(r'[\uFE00-\uFE0F]')
_SYMBOL_ONLY = set('●○■◆•►✔→←—')

# Lines containing any of these phrases are interview coaching → skip
_COACHING_RE = re.compile(
    r'start with this|start here|very important.*interview|for interviewers|'
    r'this is a great interview|only if interviewer|explain this step-by-step|'
    r'you can even draw|you can add:|example you can say|gold for interviews|'
    r'short version\s*\(|30.second answer|verbally:',
    re.IGNORECASE,
)


def _strip_emojis(text: str) -> str:
    """Remove emoji codepoints and keycap/variation-selector sequences."""
    text = _KEYCAP_RE.sub('', text)
    text = _VARSEL_RE.sub('', text)
    out = []
    for ch in text:
        cp = ord(ch)
        if not (0x1F000 <= cp <= 0x1FFFF or 0x2600 <= cp <= 0x27BF or cp == 0x20E3):
            out.append(ch)
    return ''.join(out)


def _is_pure_marker(raw: str) -> bool:
    """True if a line consists entirely of emoji/symbol chars (section divider)."""
    stripped = raw.strip()
    if not stripped:
        return False
    after = _strip_emojis(stripped)
    after = ''.join(c for c in after if c not in _SYMBOL_ONLY)
    return not after.strip()


def parse_source_pdf(title: str, base_dir: str) -> list:
    """
    Extract the source PDF for *title*, clean it, and return a list of
    (kind, text) tuples where kind is one of:
        'section'    – bold section heading  (came after a 🔹-style marker)
        'subsection' – bold step heading     (came after a 1⃣-style marker)
        'bullet'     – bullet point          (original line began with ● / •)
        'body'       – regular paragraph text
    """
    filename = SRC_MAP.get(title)
    if not filename:
        return []
    path = os.path.join(base_dir, SRC_DIR, filename)
    if not os.path.exists(path):
        return []

    try:
        reader = pypdf.PdfReader(path)
    except Exception as e:
        print(f"  Warning: could not read {path}: {e}")
        return []

    raw_lines = []
    for page in reader.pages:
        raw_lines.extend((page.extract_text() or '').split('\n'))

    items = []
    i = 0
    while i < len(raw_lines):
        raw = raw_lines[i]

        if _is_pure_marker(raw):
            # Was it a *numbered* step marker (contained a digit)?
            is_numbered = bool(re.search(r'\d', raw))
            # Advance to the next non-empty line — that becomes the heading
            j = i + 1
            while j < len(raw_lines) and not raw_lines[j].strip():
                j += 1
            if j < len(raw_lines):
                heading = _strip_emojis(raw_lines[j].strip())
                # Drop trailing parenthetical coaching notes, e.g. "(start here)"
                heading = re.sub(r'\s*\([^)]{0,80}\)\s*$', '', heading).strip()
                if heading and not _COACHING_RE.search(heading) and len(heading) > 3:
                    kind = 'subsection' if is_numbered else 'section'
                    items.append((kind, heading))
            i = j + 1
            continue

        # ── Regular line ─────────────────────────────────────────────────────
        cleaned = _strip_emojis(raw.strip())
        # Remove leading isolated bullet/symbol chars
        cleaned = re.sub(r'^[●○■◆•►✔\-]\s+', '', cleaned).strip()

        if not cleaned or len(cleaned) <= 2:
            i += 1
            continue
        if _COACHING_RE.search(cleaned):
            i += 1
            continue

        # Keep lines that are only digits or punctuation if they look like
        # table-style data (e.g. "1. Overview" or "PHP 8.3 (server-side…)")
        orig = raw.strip()
        is_bullet = bool(re.match(r'^[●○■◆•►✔]\s', orig))

        if is_bullet:
            items.append(('bullet', cleaned))
        else:
            items.append(('body', cleaned))

        i += 1

    return items


# ── Drawing utilities ─────────────────────────────────────────────────────────
def _rrect(cv, x, y, w, h, r, fill, stroke=False):
    cv.saveState()
    cv.setFillColor(fill)
    cv.setStrokeColor(C_DIV if stroke else fill)
    if stroke:
        cv.setLineWidth(0.5)
    cv.roundRect(x, y, w, h, r, fill=1, stroke=1 if stroke else 0)
    cv.restoreState()


class Writer:
    """Tracks the y cursor, handles page overflow, and draws every element."""

    def __init__(self, cv, title: str):
        self.c = cv
        self.title = title
        self.y = PH - HDR_H - 0.6 * cm

    # ── Internal ──────────────────────────────────────────────────────────────
    def _need(self, height: float):
        """Ensure *height* pts are available; start a new page if not."""
        if self.y - height < MB + 0.4 * cm:
            self._footer()
            self.c.showPage()
            self._new_page_bg()
            self.y = PH - 1.5 * cm

    def _new_page_bg(self):
        self.c.setFillColor(C_BG)
        self.c.rect(0, 0, PW, PH, fill=1, stroke=0)
        self.c.setFillColor(C_ACCENT)
        self.c.rect(0, PH - 4, PW, 4, fill=1, stroke=0)
        self.c.setFillColor(C_HDR)
        self.c.rect(0, PH - 1.0 * cm, PW, 1.0 * cm, fill=1, stroke=0)
        self.c.setFont(F, 8)
        self.c.setFillColor(C_SUBTLE)
        self.c.drawString(ML, PH - 0.65 * cm, self.title + " — continued")

    def _footer(self):
        self.c.setFillColor(C_DIV)
        self.c.rect(0, MB - 0.4 * cm, PW, 0.5, fill=1, stroke=0)
        self.c.setFont(F, S_FOOTER)
        self.c.setFillColor(C_SUBTLE)
        self.c.drawString(ML, MB - 0.65 * cm,
                          "Aiyshwarya Aruchamy  |  Portfolio Project")
        self.c.drawRightString(PW - MR, MB - 0.65 * cm, "github.com/aiyshwary")

    # ── Public drawing methods ─────────────────────────────────────────────────
    def section_label(self, label: str):
        self._need(0.9 * cm)
        self.c.setFont(FB, S_SECTION)
        self.c.setFillColor(C_ACCENT)
        self.c.drawString(ML, self.y, label.upper())
        self.y -= 0.15 * cm
        self.c.setStrokeColor(C_DIV)
        self.c.setLineWidth(0.5)
        self.c.line(ML, self.y, PW - MR, self.y)
        self.y -= 0.38 * cm

    def text(self, content: str, font=F, size=S_BODY, color=None, indent=0.0):
        if color is None:
            color = C_BODY
        lines = simpleSplit(content, font, size, CW - indent)
        self._need(len(lines) * LH)
        self.c.setFont(font, size)
        self.c.setFillColor(color)
        for line in lines:
            self._need(LH)
            self.c.drawString(ML + indent, self.y, line)
            self.y -= LH

    def heading(self, content: str):
        """Bold sub-heading inside the walkthrough section."""
        self.y -= 0.08 * cm
        self.text(content, font=FB, size=S_BODY, color=C_WHITE)

    def bullet_card(self, content: str):
        """Draws content inside a rounded card with a dash prefix."""
        inner_w = CW - 0.9 * cm
        lines = simpleSplit(content, F, S_BODY, inner_w)
        block_h = len(lines) * LH + 0.5 * cm
        self._need(block_h + 0.2 * cm)
        _rrect(self.c, ML, self.y - block_h, CW, block_h, 4, C_CARD, stroke=True)
        self.c.setFont(FB, S_BODY)
        self.c.setFillColor(C_ACCENT)
        self.c.drawString(ML + 0.3 * cm, self.y - 0.25 * cm - LH + 4, "-")
        self.c.setFont(F, S_BODY)
        self.c.setFillColor(C_BODY)
        ty = self.y - 0.25 * cm
        for line in lines:
            self.c.drawString(ML + 0.9 * cm, ty, line)
            ty -= LH
        self.y -= block_h + 0.18 * cm

    def gap(self, h: float = 0.4 * cm):
        self.y -= h

    def finish(self):
        self._footer()
        self.c.save()


# ── PDF generator ─────────────────────────────────────────────────────────────
def generate_pdf(project: dict, source_items: list, out_path: str):
    cv = canvas.Canvas(out_path, pagesize=A4)
    cv.setTitle(project["title"])
    cv.setAuthor("Aiyshwarya Aruchamy")

    # ── Page 1 background ────────────────────────────────────────────────────
    cv.setFillColor(C_BG)
    cv.rect(0, 0, PW, PH, fill=1, stroke=0)

    # ── Header block ─────────────────────────────────────────────────────────
    cv.setFillColor(C_HDR)
    cv.rect(0, PH - HDR_H, PW, HDR_H, fill=1, stroke=0)
    cv.setFillColor(C_ACCENT)
    cv.rect(0, PH - 4, PW, 4, fill=1, stroke=0)

    # Title
    cv.setFont(FB, S_TITLE)
    cv.setFillColor(C_WHITE)
    cv.drawString(ML, PH - 1.3 * cm, project["title"])

    # GitHub URL
    if project.get("github"):
        cv.setFont(F, 8)
        cv.setFillColor(C_ACCENT)
        cv.drawString(ML, PH - 1.95 * cm, project["github"])

    # Tech pills
    px = ML
    py = PH - 2.88 * cm
    ph = 0.48 * cm
    pad = 0.28 * cm
    for tech in project.get("techs", []):
        tw = cv.stringWidth(tech, FB, S_TECH)
        pill_w = tw + 2 * pad
        if px + pill_w > PW - MR:
            break
        _rrect(cv, px, py, pill_w, ph, 3, C_TECH)
        cv.setFillColor(C_ACCENT)
        cv.setFont(FB, S_TECH)
        cv.drawString(px + pad, py + 0.12 * cm, tech)
        px += pill_w + 0.2 * cm

    # ── Body ─────────────────────────────────────────────────────────────────
    w = Writer(cv, project["title"])

    # OVERVIEW
    w.section_label("Overview")
    w.text(project["summary"])
    w.gap()

    # IMPACT
    w.section_label("Impact")
    w.text(project["impact"])
    w.gap()

    # FULL TECHNICAL WALKTHROUGH (sourced from original PDF, fully cleaned)
    if source_items:
        w.section_label("Technical Walkthrough")
        for kind, content in source_items:
            if kind in ('section', 'subsection'):
                w.gap(0.15 * cm)
                w.heading(content)
            elif kind == 'bullet':
                w.bullet_card(content)
            else:
                w.text(content)
        w.gap()

    # KEY DETAILS (structured bullets from projects.json)
    w.section_label("Key Details")
    for bullet in project.get("bullets", []):
        w.bullet_card(bullet)

    w.finish()
    print(f"  Generated: {out_path}")


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(base_dir, "projects.json")) as f:
        projects = json.load(f)

    out_dir = os.path.join(base_dir, "assets", "projects")
    os.makedirs(out_dir, exist_ok=True)

    print(f"Generating {len(projects)} comprehensive PDFs...\n")
    for p in projects:
        if not p.get("pdf"):
            continue
        source_items = parse_source_pdf(p["title"], base_dir)
        n = len(source_items)
        print(f"  [{p['title']}]  {n} walkthrough items from source PDF")
        out_path = os.path.join(base_dir, p["pdf"])
        generate_pdf(p, source_items, out_path)

    print("\nDone.")
