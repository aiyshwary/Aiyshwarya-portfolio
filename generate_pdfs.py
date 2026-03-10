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
from reportlab.pdfbase import pdfmetrics
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
_NUMBERED_HDG = re.compile(r'^(\d+\.)+\s+\S')   # "1. Overview" or "4.1 Files"
_PAGE_HDR     = re.compile(
    r'^(page \d+|.*project documentation$)',
    re.IGNORECASE,
)
_ENDS_SENT    = re.compile(r'[.!?]$')
_TITLE_HDG    = re.compile(r'^[A-Z][A-Za-z0-9\s&/\-,:]{0,70}$')
_STEP_HDG     = re.compile(r'^Step\s+\d+\s*:\s+.+$', re.IGNORECASE)
_ROMAN_BULLET_RE = re.compile(r'^(?P<r>[ivxlcdm]+)\)\s*(?P<txt>.+)$', re.IGNORECASE)
_SHORT_HEADINGS = {
    "In short",
    "Core idea",
    "This makes it",
    "End-to-end pipeline explanation",
    "Configuration-driven setup",
    "One-liner summary",
}
_QUESTION_HDG_RE = re.compile(r'^What\s+.*\?$')
_LIST_VERB_RE = re.compile(
    r'^(Measures|Search|Prevent|Accept|Compute|Mark|Displays|Shows|Uses|Loads|'
    r'Trains|Predicts|Applies|Builds|Creates|Removes|Encodes|Benchmarks|'
    r'Implements|Tracks|Evaluates|Concludes|Generates|Normalizes|Splits|'
    r'Handles|Supports|Validates|Calculates|Processes|Selects|Adds|Drops|'
    r'Converts|Groups|Compares|Finds|Provides|Ensures|Updates|Locks|Assigns|'
    r'Stores|Downloads|Extracts|High)\b',
    re.IGNORECASE,
)
_KEYCAP_RE   = re.compile(r'\d\u20E3|\u20E3')

_VARSEL_RE   = re.compile(r'[\uFE00-\uFE0F]')
_SYMBOL_ONLY = set('●○■◆•►✔→←—')
_COACHING_RE = re.compile(
    r'start with this|start here|very important.*interview|for interviewers|'
    r'this is a great interview|only if interviewer|explain this step-by-step|'
    r'you can even draw|you can add:|example you can say|gold for interviews|'
    r'short version\s*\(|30.second answer|verbally:',
    re.IGNORECASE,
)


def _normalize_ws(text: str) -> str:
    """Collapse repeated whitespace to single spaces for clean alignment."""
    return re.sub(r'\s+', ' ', text).strip()


def _to_roman(n: int) -> str:
    """Convert 1..3999 to lowercase roman numerals."""
    vals = [
        (1000, 'm'), (900, 'cm'), (500, 'd'), (400, 'cd'),
        (100, 'c'), (90, 'xc'), (50, 'l'), (40, 'xl'),
        (10, 'x'), (9, 'ix'), (5, 'v'), (4, 'iv'), (1, 'i')
    ]
    out = []
    for v, s in vals:
        while n >= v:
            out.append(s)
            n -= v
    return ''.join(out)


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


def _is_list_like_line(text: str) -> bool:
    """Heuristic for short list-like lines that should not be merged."""
    if not text:
        return False
    if text.endswith(":"):
        return True
    if _TITLE_HDG.match(text) and len(text.split()) <= 7 and not _ENDS_SENT.search(text) and not _LIST_VERB_RE.match(text):
        return False
    if _NUMBERED_HDG.match(text) or _STEP_HDG.match(text):
        return False
    if _ENDS_SENT.search(text):
        return False
    words = text.split()
    if len(words) <= 6 and len(text) <= 48:
        return True
    return False


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
        cleaned = _normalize_ws(cleaned)

        if not cleaned or len(cleaned) <= 2:
            # blank line → paragraph boundary
            if not raw.strip():
                items.append(('para_break', ''))
            i += 1
            continue
        if _COACHING_RE.search(cleaned):
            i += 1
            continue
        if _PAGE_HDR.search(cleaned):
            i += 1
            continue

        orig = raw.strip()
        is_bullet = bool(re.match(r'^[●○■◆•►✔]\s', orig))

        # Numbered section headings ("1. Overview" / "4.1 Files") → section item
        if not is_bullet and _NUMBERED_HDG.match(cleaned):
            # strip leading "N. " or "N.N. " prefix
            heading = re.sub(r'^(\d+\.)+\s*', '', cleaned).strip()
            if heading:
                items.append(('section', heading))
            i += 1
            continue

        # Heuristic for short title-case headings from PDFs
        if (
            not is_bullet
            and _TITLE_HDG.match(cleaned)
            and len(cleaned.split()) <= 7
            and not _ENDS_SENT.search(cleaned)
            and not _LIST_VERB_RE.match(cleaned)
        ):
            items.append(('section', cleaned))
            i += 1
            continue

        if is_bullet:
            items.append(('bullet', cleaned))
        else:
            items.append(('body', cleaned))

        i += 1

    # Merge consecutive body lines into paragraphs.
    # Flush the buffer when:
    #   - a blank-line para_break is seen
    #   - a non-body item (section/bullet) is seen
    #   - the previous line ended a sentence AND the next starts with uppercase
    merged = []
    buf = []
    for kind, text in items:
        if kind == 'body':
            quote_break = buf and (text.startswith('"') or text.startswith('“') or buf[-1].startswith('"') or buf[-1].startswith('“'))
            colon_break = buf and (buf[-1].endswith(':') or text.endswith(':'))
            list_break = buf and (_is_list_like_line(buf[-1]) or _is_list_like_line(text))
            flush_now = (
                buf
                and _ENDS_SENT.search(buf[-1])
                and text
                and text[0].isupper()
            )
            if flush_now or list_break or quote_break or colon_break:
                merged.append(('body', ' '.join(buf)))
                buf = []
            buf.append(text)
        elif kind == 'para_break':
            if buf:
                merged.append(('body', ' '.join(buf)))
                buf = []
            merged.append(('para_break', ''))
        else:
            if buf:
                merged.append(('body', ' '.join(buf)))
                buf = []
            merged.append((kind, text))
    if buf:
        merged.append(('body', ' '.join(buf)))

    # Convert colon-ended lines into subsection headers and bulletize following lines.
    post = []
    list_mode = False
    expect_body_after_heading = False
    i = 0
    while i < len(merged):
        kind, text = merged[i]
        if kind == 'body' and text in _SHORT_HEADINGS:
            list_mode = text in {"In short", "This makes it"}
            post.append(('subsection', text))
            expect_body_after_heading = text in {"Core idea", "End-to-end pipeline explanation", "Configuration-driven setup", "One-liner summary"}
            i += 1
            continue
        if kind == 'body' and _QUESTION_HDG_RE.match(text):
            list_mode = False
            post.append(('subsection', text))
            expect_body_after_heading = True
            i += 1
            continue
        if kind == 'para_break':
            list_mode = False
            i += 1
            continue
        if kind in ('section', 'subsection'):
            # If a section line ends with ':', treat it as a list heading
            if text.endswith(':'):
                list_mode = True
                post.append(('subsection', text.rstrip(':').strip()))
                i += 1
                continue
            if text in _SHORT_HEADINGS or _QUESTION_HDG_RE.match(text):
                list_mode = text in {"In short", "This makes it"}
                post.append(('subsection', text))
                expect_body_after_heading = text in {"Core idea", "End-to-end pipeline explanation", "Configuration-driven setup", "One-liner summary"} or _QUESTION_HDG_RE.match(text)
                i += 1
                continue
            # If currently in list mode, convert short section items into bullets
            if (
                list_mode
                and kind == 'section'
                and not _STEP_HDG.match(text)
                and not _NUMBERED_HDG.match(text)
                and not text.lower().endswith('module')
                and 'centrality' not in text.lower()
            ):
                post.append(('bullet', text))
                i += 1
                continue
            list_mode = False
            post.append((kind, text))
            i += 1
            continue
        if kind == 'body' and _STEP_HDG.match(text):
            list_mode = False
            post.append(('subsection', text))
            expect_body_after_heading = False
            i += 1
            continue
        if kind == 'body':
            m = _ROMAN_BULLET_RE.match(text)
            if m:
                roman_text = m.group('txt').strip()
                if roman_text in _SHORT_HEADINGS or _QUESTION_HDG_RE.match(roman_text):
                    list_mode = roman_text in {"In short", "This makes it"}
                    post.append(('subsection', roman_text))
                    expect_body_after_heading = roman_text in {"Core idea", "End-to-end pipeline explanation", "Configuration-driven setup"} or _QUESTION_HDG_RE.match(roman_text)
                elif expect_body_after_heading:
                    post.append(('body', roman_text))
                    expect_body_after_heading = False
                else:
                    post.append(('bullet', roman_text))
                i += 1
                continue
        if kind == 'body' and text.endswith(':'):
            list_mode = True
            post.append(('subsection', text.rstrip(':').strip()))
            expect_body_after_heading = False
            i += 1
            continue

        if kind == 'bullet' and text.endswith(':'):
            list_mode = True
            post.append(('subsection', text.rstrip(':').strip()))
            i += 1
            continue

        # Auto-bulletize runs of list-like lines even without a colon heading
        # (skip for Annotation Transfer Tool to keep bullets only under subheadings)
        if title != "Annotation Transfer Tool" and kind == 'body' and _is_list_like_line(text):
            run = []
            j = i
            while j < len(merged):
                k2, t2 = merged[j]
                if k2 != 'body' or not _is_list_like_line(t2):
                    break
                run.append(t2)
                j += 1
            if len(run) >= 2:
                for t2 in run:
                    if t2 in _SHORT_HEADINGS or _QUESTION_HDG_RE.match(t2):
                        list_mode = t2 in {"In short", "This makes it"}
                        post.append(('subsection', t2))
                        expect_body_after_heading = t2 in {"Core idea", "End-to-end pipeline explanation", "Configuration-driven setup"} or _QUESTION_HDG_RE.match(t2)
                        continue
                    if t2.endswith(':'):
                        list_mode = True
                        post.append(('subsection', t2.rstrip(':').strip()))
                        expect_body_after_heading = False
                    else:
                        post.append(('bullet', t2))
                i = j
                continue

        if list_mode and kind == 'body':
            # If a quoted line appears, treat it as body and end list mode
            if (text.startswith('"') or text.startswith('“')) and (text.endswith('"') or text.endswith('”')):
                list_mode = False
                post.append(('body', text))
                post.append(('para_break', ''))
                expect_body_after_heading = False
                i += 1
                continue
            if text in _SHORT_HEADINGS or _QUESTION_HDG_RE.match(text):
                list_mode = text in {"In short", "This makes it"}
                post.append(('subsection', text))
                expect_body_after_heading = text in {"Core idea", "End-to-end pipeline explanation", "Configuration-driven setup", "One-liner summary"} or _QUESTION_HDG_RE.match(text)
                i += 1
                continue
            if (
                _STEP_HDG.match(text)
                or (_TITLE_HDG.match(text) and len(text.split()) <= 7 and not _ENDS_SENT.search(text) and not _LIST_VERB_RE.match(text))
            ):
                list_mode = False
                post.append(('subsection', text))
            else:
                post.append(('bullet', text))
            i += 1
            continue

        # Standalone quoted lines should be isolated from neighboring text
        if kind == 'body' and (text.startswith('"') or text.startswith('“')) and (text.endswith('"') or text.endswith('”')):
            post.append(('body', text))
            post.append(('para_break', ''))
            expect_body_after_heading = False
            i += 1
            continue

        post.append((kind, text))
        i += 1

    return post


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
        if self.y - height < MB:
            self.c.showPage()
            self._new_page_bg()
            self.y = PH - 0.8 * cm

    def _new_page_bg(self):
        self.c.setFillColor(C_BG)
        self.c.rect(0, 0, PW, PH, fill=1, stroke=0)
        self.c.setFillColor(C_ACCENT)
        self.c.rect(0, PH - 4, PW, 4, fill=1, stroke=0)

    def _footer(self):
        pass  # no footer text

    # ── Public drawing methods ─────────────────────────────────────────────────
    def section_label(self, label: str):
        # Avoid orphaned section labels at the bottom of a page
        min_block = 0.9 * cm + (LH * 3)
        self._need(min_block)
        self.c.setFont(FB, S_SECTION)
        self.c.setFillColor(C_ACCENT)
        self.c.drawString(ML, self.y, label.upper())
        self.y -= 0.15 * cm
        self.c.setStrokeColor(C_DIV)
        self.c.setLineWidth(0.5)
        self.c.line(ML, self.y, PW - MR, self.y)
        self.y -= 0.55 * cm

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
        # Keep heading with at least the next heading or two lines of content
        self._need(LH * 4)
        self.y -= 0.08 * cm
        self.text(content, font=FB, size=S_BODY, color=C_WHITE)

    def bullet_card(self, content: str, prefix: str = "-"):
        """Draws content inside a rounded card with a prefix (dash or number)."""
        pad_x = 0.4 * cm
        pad_y = 0.32 * cm
        prefix_w = self.c.stringWidth(prefix, FB, S_BODY)
        gap_w = 0.2 * cm
        inner_w = CW - (pad_x * 2 + prefix_w + gap_w)
        lines = simpleSplit(content, F, S_BODY, inner_w)
        block_h = len(lines) * LH + 2 * pad_y
        self._need(block_h + 0.2 * cm)

        _rrect(self.c, ML, self.y - block_h, CW, block_h, 4, C_CARD, stroke=True)

        # Center the text block vertically within the card using font metrics
        ascent = pdfmetrics.getAscent(F, S_BODY)
        descent = abs(pdfmetrics.getDescent(F, S_BODY))
        text_block_h = (ascent + descent) + (len(lines) - 1) * LH
        first_line_y = self.y - ((block_h - text_block_h) / 2) - ascent

        # Dash prefix
        self.c.setFont(FB, S_BODY)
        self.c.setFillColor(C_ACCENT)
        self.c.drawString(ML + pad_x, first_line_y, prefix)

        # Text lines
        text = self.c.beginText()
        text.setTextOrigin(ML + pad_x + prefix_w + gap_w, first_line_y)
        text.setFont(F, S_BODY)
        text.setFillColor(C_BODY)
        text.setLeading(LH)
        for line in lines:
            text.textLine(line)
        self.c.drawText(text)

        # Add a clearer gap after the card
        self.y -= block_h + 0.28 * cm

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
    w.text(_normalize_ws(project["summary"]))
    w.gap()

    # IMPACT
    w.section_label("Impact")
    w.text(_normalize_ws(project["impact"]))
    w.gap()

    # FULL TECHNICAL WALKTHROUGH (sourced from original PDF or projects.json)
    if source_items:
        w.section_label("Technical Walkthrough")
        num = 1
        for kind, content in source_items:
            if kind in ('section', 'subsection'):
                w.gap(0.15 * cm)
                w.heading(content)
                num = 1
            elif kind == 'bullet':
                w.bullet_card(content, prefix=f"{_to_roman(num)})")
                num += 1
            else:
                w.text(content)
        w.gap()

    # KEY DETAILS (structured bullets from projects.json)
    w.section_label("Key Details")
    num = 1
    for bullet in project.get("bullets", []):
        w.bullet_card(_normalize_ws(bullet), prefix=f"{num}.")
        num += 1

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
    def _coerce_walkthrough(project: dict, source_items: list) -> list:
        """Return structured walkthrough items from projects.json if present."""
        items = project.get("walkthrough")
        if isinstance(items, list) and items:
            out = []
            for it in items:
                if isinstance(it, dict):
                    kind = (it.get("kind") or "body").strip().lower()
                    text = _normalize_ws(it.get("text") or "")
                    if text:
                        out.append((kind, text))
                elif isinstance(it, str):
                    text = _normalize_ws(it)
                    if text:
                        out.append(("body", text))
            return out
        return source_items

    for p in projects:
        if not p.get("pdf"):
            continue
        source_items = parse_source_pdf(p["title"], base_dir)
        source_items = _coerce_walkthrough(p, source_items)
        n = len(source_items)
        origin = "projects.json" if p.get("walkthrough") else "source PDF"
        print(f"  [{p['title']}]  {n} walkthrough items from {origin}")
        out_path = os.path.join(base_dir, p["pdf"])
        generate_pdf(p, source_items, out_path)

    print("\nDone.")
