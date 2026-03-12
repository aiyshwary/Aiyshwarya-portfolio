# Import missing modules

import re
import os
from PyPDF2 import PdfReader as pypdf
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import json

# Define missing constants
SRC_MAP = {}
SRC_DIR = "assets/projects"


# Implement simpleSplit function with text wrapping
from reportlab.pdfbase.pdfmetrics import stringWidth
def simpleSplit(text, font, size, width):
    """Split text into lines that fit within the given width."""
    words = text.split()
    if not words:
        return ['']
    lines = []
    current = words[0]
    for word in words[1:]:
        test = current + ' ' + word
        if stringWidth(test, font, size) <= width:
            current = test
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines

# Define missing constants
ML = 40  # Left margin
MR = 40  # Right margin
PH, PW = A4  # Page height and width

# Define missing constants
LH = 14  # Line height
CW = PW - (ML + MR)  # Content width
C_DIV = HexColor("#DDDDDD")

# Define additional constants
HDR_H = 50  # Header height in points
C_BODY = HexColor("#000000")

# Define additional missing constants
MB = 40  # Bottom margin

# Define missing constants (reset to match other PDFs)
C_BG = HexColor("#FFFFFF")  # White background for consistency
C_ACCENT = HexColor("#007BFF")  # Blue accent (matches tech pill)
C_WHITE = HexColor("#FFFFFF")
C_HDR = HexColor("#222B45")  # Darker header for contrast
C_CARD = HexColor("#F5F6FA")  # Light card background
C_TECH = HexColor("#007BFF")
S_SECTION = 14  # Section font size
S_TITLE = 18  # Title font size
S_TECH = 10  # Tech font size

# Use built-in ReportLab fonts
F = "Helvetica"  # Regular font
FB = "Helvetica-Bold"  # Bold font

# Define missing font size constant
S_BODY = 12  # Body font size

def fix_video_rag_text(rebuilt):
    i = 0
    while i < len(rebuilt):
        kind, text = rebuilt[i]
        clean = text
        clean = clean.replace('for interviewers', '').replace('interviewers', '').replace('interviewer', '').replace('as an interview answer', '').strip()
        rebuilt[i] = (kind, clean)
        # Remove all "interviewer" or coaching language from any body/section/subsection
        if any(word in text.lower() for word in ['interviewer', 'for interviewers', 'as an interview answer', 'coaching note']):
            i += 1
            continue
        # Remove leading/trailing quotes from all bodies in this section
        if kind == 'body' and text.startswith('Vector storage for'):
            rebuilt[i] = ('bullet', text)
            i += 1
            continue
        if kind == 'body' and text.startswith('Similarity-based retrieval'):
            rebuilt[i] = ('bullet', text)
            i += 1
            continue
        i += 1
    # Merge split summary lines at the end for Video RAG Retrieval Project
    merged = []
    i = 0
    while i < len(rebuilt):
        kind, text = rebuilt[i]
        # Look for the summary start
        if text.strip().startswith('“I built a Visual RAG system'):
            merged_text = text.strip()
            # Merge all following body lines that are part of the same summary
            while (i + 1 < len(rebuilt)
                   and rebuilt[i + 1][0] == 'body'
                   and not rebuilt[i + 1][1].strip().startswith('“')):
                merged_text += ' ' + rebuilt[i + 1][1].strip()
                i += 1
            merged.append(('body', merged_text))
            i += 1
            continue
        merged.append((kind, text))
        i += 1
    return merged

# ── Text-cleaning helpers ─────────────────────────────────────────────────────
_NUMBERED_HDG = re.compile(r'^(\d+\.)+\s+\S')   # "1. Overview" or "4.1 Files"
_PAGE_HDR     = re.compile(
    r'^(page \d+|.*project documentation$)',
    re.IGNORECASE,
)
_ENDS_SENT    = re.compile(r'[.!?]$')
_TITLE_HDG    = re.compile(r'^[A-Z][A-Za-z0-9\s&/\-,:]{0,70}$')
_STEP_HDG     = re.compile(r'^Step\s+\d+\s*:\s+.+$', re.IGNORECASE)
# Verb / past-participle phrases that describe a metric, not name a section.
_INTERP_VERB_RE = re.compile(
    r'^(?:Indicates?|Identifies?|Acts?\s+as\b|Connected\s+to\b|'
    r'Considered\s|Helps?\s|Suggests?)\b', re.IGNORECASE)
_ROMAN_BULLET_RE = re.compile(r'^(?P<r>[ivxlcdm]+)\)\s*(?P<txt>.+)$', re.IGNORECASE)
_SHORT_HEADINGS = {
    "In short",
    "Core idea",
    "This makes it",
    "End-to-end pipeline explanation",
    "Configuration-driven setup",
    "One-liner summary",
    "Script",
    "Two ways to run the system",
    "Full automation",
    "Step-by-step execution",
    "Interactive demo",
    "Business logic",
    "What happens here",
    "Fine-Tuning",
    "Inference",
    "Results",
}
_QUESTION_HDG_RE = re.compile(r'^What\s+.*\?$')
_LIST_VERB_RE = re.compile(
    r'^(Measures|Search|Prevent|Accept|Compute|Mark|Displays|Shows|Uses|Loads|'
    r'Trains|Predicts|Applies|Builds|Creates|Removes|Encodes|Benchmarks|'
    r'Implements|Tracks|Evaluates|Concludes|Generates|Normalizes|Splits|'
    r'Handles|Supports|Validates|Calculates|Processes|Selects|Adds|Drops|'
    r'Converts|Groups|Compares|Finds|Provides|Ensures|Updates|Locks|Assigns|'
    r'Stores|Downloads|Extracts|Used)\b',
    re.IGNORECASE,
)
_KEYCAP_RE   = re.compile(r'\d\u20E3|\u20E3')

_VARSEL_RE   = re.compile(r'[\uFE00-\uFE0F]')
_SYMBOL_ONLY = set('●○■◆•►✔→←—')
_COACHING_RE = re.compile(
    r'start with this|start here|very important.*interview|for interviewers|'
    r'this is a great interview|only if interviewer|explain this step-by-step|'
    r'explain this in steps|this acts as a human-in-the-loop|'
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

    # Deduplicate: remove consecutive or repeated blocks that PDF extraction
    # sometimes produces (e.g. overlapping text layers in the source PDF).
    seen = set()
    deduped = []
    for line in raw_lines:
        key = line.strip()
        if not key:
            deduped.append(line)          # keep blank lines for paragraph breaks
            continue
        if key in seen:
            continue                       # skip exact duplicate lines
        seen.add(key)
        deduped.append(line)
    raw_lines = deduped

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
                # Guard: if the next line is too long to be a heading
                # (>7 words, ends with sentence punctuation, starts with
                # a quote, or contains a filename like .py/.js), skip the
                # marker — let normal classification handle it.
                too_long = len(heading.split()) > 7
                ends_sent = bool(_ENDS_SENT.search(heading))
                starts_quote = heading[:1] in ('"', '"', "'")
                has_filename = bool(re.search(r'\.\w{1,4}[)\s,:]', heading))
                if too_long or ends_sent or starts_quote or has_filename:
                    # Just skip the marker line, don't consume the next line
                    i += 1
                    continue
                if heading and not _COACHING_RE.search(heading) and len(heading) > 3:
                    kind = 'subsection' if is_numbered else 'section'
                    items.append((kind, heading))
            i = j + 1
            continue

        # ── Regular line ─────────────────────────────────────────────────────
        cleaned = _strip_emojis(raw.strip())
        # Remove leading isolated bullet/symbol chars
        cleaned = re.sub(r'^[●○■◆•►✔\-]\s+', '', cleaned).strip()
        if title == "Bus Reservation And Ticketing System":
            cleaned = re.sub(r'^(?:[ivxlcdm]+\))\s*', '', cleaned, flags=re.IGNORECASE)
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

        # Strip trailing parenthetical coaching notes, e.g. "(very important)",
        # "(start here)", so the core text can match heading heuristics.
        cleaned_no_paren = re.sub(r'\s*\([^)]{0,80}\)\s*$', '', cleaned).strip()
        if not cleaned_no_paren:
            cleaned_no_paren = cleaned

        # Numbered section headings ("1. Overview" / "4.1 Files") → section item
        if not is_bullet and _NUMBERED_HDG.match(cleaned_no_paren):
            # strip leading "N. " or "N.N. " prefix
            heading = re.sub(r'^(\d+\.)+\s*', '', cleaned_no_paren).strip()
            if heading:
                items.append(('section', heading))
            i += 1
            continue

        # Heuristic for short title-case headings from PDFs
        if (
            not is_bullet
            and _TITLE_HDG.match(cleaned_no_paren)
            and len(cleaned_no_paren.split()) <= 7
            and not _ENDS_SENT.search(cleaned_no_paren)
            and not _LIST_VERB_RE.match(cleaned_no_paren)
        ):
            items.append(('section', cleaned_no_paren))
            i += 1
            continue

        # Lines with em/en dashes surrounded by spaces (e.g. "System components — 30-second walk-through")
        # Check if the part before the dash qualifies as a heading.
        # Only match dashes with spaces around them (not compound words like "learning–based").
        m_dash = re.search(r'\s[\u2013\u2014]\s', cleaned_no_paren)
        if not is_bullet and m_dash:
            before_dash = cleaned_no_paren[:m_dash.start()].strip()
            total_words = len(cleaned_no_paren.split())
            if (
                before_dash
                and _TITLE_HDG.match(before_dash)
                and 2 <= len(before_dash.split()) <= 5
                and total_words <= 8
                and not _ENDS_SENT.search(before_dash)
                and not _LIST_VERB_RE.match(before_dash)
                and not _ENDS_SENT.search(cleaned_no_paren)
            ):
                items.append(('section', cleaned_no_paren))
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
            list_break = buf and (
                _is_list_like_line(buf[-1])
                or (_is_list_like_line(text) and text[:1].isupper())
            )
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

    # Merge consecutive bullets/body when the previous line ends with an arrow →
    # (indicates a continuation, e.g. "Find similar images → reuse annotations →"
    #  + "export back to CVAT" should be one bullet).
    arrow_merged = []
    for kind, text in merged:
        if arrow_merged and arrow_merged[-1][1].rstrip().endswith('→') and kind in ('bullet', 'body'):
            prev_kind, prev_text = arrow_merged[-1]
            arrow_merged[-1] = (prev_kind, prev_text.rstrip() + ' ' + text)
        else:
            arrow_merged.append((kind, text))
    merged = arrow_merged

    # Convert colon-ended lines into subsection headers and bulletize following lines.
    post = []
    list_mode = False
    findings_mode = False  # True after "Key Findings" etc. – allows longer bullet items
    list_remaining = 0           # >0 for count-based lists ("has N items")
    expect_body_after_heading = False
    two_way_mode = False
    two_way_count = 1
    i = 0
    while i < len(merged):
        kind, text = merged[i]
        if two_way_mode and text in {"Full automation", "Step-by-step execution"}:
            post.append(('bullet', f"{two_way_count}) {text}"))
            two_way_count += 1
            expect_body_after_heading = True
            if two_way_count > 2:
                two_way_mode = False
            i += 1
            continue
        if kind == 'bullet' and (text in _SHORT_HEADINGS or _QUESTION_HDG_RE.match(text)):
            list_mode = text in {"In short", "This makes it", "Script", "What happens here", "Results"}
            post.append(('subsection', text))
            expect_body_after_heading = text in {
                "Core idea",
                "End-to-end pipeline explanation",
                "Configuration-driven setup",
                "One-liner summary",
                "Full automation",
                "Step-by-step execution",
                "Interactive demo",
                "Fine-Tuning",
                "Inference",
            } or _QUESTION_HDG_RE.match(text)
            i += 1
            continue
        if kind == 'body' and text in _SHORT_HEADINGS:
            list_mode = text in {"In short", "This makes it", "Script", "Business logic", "What happens here", "Results"}
            post.append(('subsection', text))
            expect_body_after_heading = text in {
                "Core idea",
                "End-to-end pipeline explanation",
                "Configuration-driven setup",
                "One-liner summary",
                "Full automation",
                "Step-by-step execution",
                "Interactive demo",
                "Fine-Tuning",
                "Inference",
            }
            if text == "Two ways to run the system":
                two_way_mode = True
                two_way_count = 1
            else:
                two_way_mode = False
            i += 1
            continue
        if kind == 'body' and _QUESTION_HDG_RE.match(text):
            list_mode = False
            post.append(('subsection', text))
            expect_body_after_heading = True
            i += 1
            continue
        # Short verb-only bullet items (e.g. "Shows", "Displays") → subsection + list_mode
        if kind == 'bullet' and _LIST_VERB_RE.match(text) and len(text.split()) == 1 and not _ENDS_SENT.search(text):
            list_mode = True
            post.append(('subsection', text))
            i += 1
            continue
        if kind == 'para_break':
            # Don't reset list_mode here; let section headings reset it instead.
            # This allows lists to span across blank lines in the source PDF.
            two_way_mode = False
            i += 1
            continue
        if kind in ('section', 'subsection'):
            # If we're expecting body text after a heading (e.g. after "Fine-Tuning"),
            # convert section-classified items into body unless they are recognized headings.
            if expect_body_after_heading and text not in _SHORT_HEADINGS and not _QUESTION_HDG_RE.match(text) and not text.endswith(':') and not _STEP_HDG.match(text):
                post.append(('body', text))
                expect_body_after_heading = False
                i += 1
                continue
            # Section heading introducing a component walkthrough
            # (e.g. "System components — 30-second walk-through")
            if re.search(r'\bcomponents?\b', text, re.IGNORECASE) and re.search(r'walk-?through', text, re.IGNORECASE):
                list_mode = True
                list_remaining = 0
                post.append((kind, text))
                i += 1
                continue
            # Section heading introducing a tech/concept list
            # (e.g. "Technologies & Concepts Used")
            if re.search(r'\b(?:Technologies|Tech Stack|Concepts?\s+Used)\b', text, re.IGNORECASE):
                list_mode = True
                list_remaining = 0
                post.append((kind, text))
                i += 1
                continue
            # Section heading introducing findings / conclusions
            # (e.g. "Key Findings", "Key Takeaways")
            if re.search(r'\bKey\s+(?:Findings|Takeaways|Results)\b', text, re.IGNORECASE):
                list_mode = True
                findings_mode = True
                list_remaining = 0
                post.append((kind, text))
                i += 1
                continue
            # Section line introducing a counted list (e.g. "The system has 5 main modules")
            m_count = re.search(r'\b(?:has|have|with|contains?)\s+(\d+)\s+', text, re.IGNORECASE)
            if m_count:
                list_mode = True
                list_remaining = int(m_count.group(1))
                post.append(('body', text))
                i += 1
                continue
            # If a section line ends with ':', treat it as a list heading
            if text.endswith(':'):
                list_mode = True
                s = text.rstrip(':').strip()
                s = s[0].upper() + s[1:] if s else s
                post.append(('subsection', s))
                i += 1
                continue
            if text in _SHORT_HEADINGS or _QUESTION_HDG_RE.match(text):
                list_mode = text in {"In short", "This makes it", "Script", "Business logic", "What happens here", "Results"}
                post.append(('subsection', text))
                expect_body_after_heading = text in {
                    "Core idea",
                    "End-to-end pipeline explanation",
                    "Configuration-driven setup",
                    "One-liner summary",
                    "Full automation",
                    "Step-by-step execution",
                    "Interactive demo",
                    "Fine-Tuning",
                    "Inference",
                } or _QUESTION_HDG_RE.match(text)
                if text == "Two ways to run the system":
                    two_way_mode = True
                    two_way_count = 1
                else:
                    two_way_mode = False
                i += 1
                continue
            # Step headings ("Step 1: Authentication") → subsection + list_mode
            if _STEP_HDG.match(text):
                list_mode = True
                list_remaining = 0
                post.append(('subsection', text))
                i += 1
                continue
            # Section items that start with a verb / past-participle phrase
            # (e.g. "Indicates how fast…", "Considered a super-spreader…") are
            # interpretation lines, not real headings → bullet.
            if kind == 'section' and _INTERP_VERB_RE.match(text):
                post.append(('bullet', text))
                i += 1
                continue
            # If currently in list mode, convert short section items into bullets
            if (
                list_mode
                and kind == 'section'
                and not _NUMBERED_HDG.match(text)
                and not text.lower().endswith('module')
                and not text.endswith('Centrality')  # real headings, e.g. "Closeness Centrality"
            ):
                # Long section items (>=7 words) signal end of list → body
                # Exception: items starting with Wh-words (Who/What/How…) are
                # clearly list continuations, and findings_mode allows longer items.
                _is_wh = bool(re.match(r'^(?:Who|What|How|When|Where|Why|Which)\b', text))
                if len(text.split()) >= 7 and not findings_mode and not _is_wh:
                    list_mode = False
                    post.append(('body', text))
                else:
                    post.append(('bullet', text))
                    if list_remaining > 0:
                        list_remaining -= 1
                        if list_remaining == 0:
                            list_mode = False
                i += 1
                continue
            list_mode = False
            findings_mode = False
            post.append((kind, text))
            i += 1
            continue
        if kind == 'body' and _STEP_HDG.match(text):
            list_mode = True
            list_remaining = 0
            two_way_mode = False
            post.append(('subsection', text))
            expect_body_after_heading = False
            i += 1
            continue
        if kind == 'body':
            m = _ROMAN_BULLET_RE.match(text)
            if m:
                roman_text = m.group('txt').strip()
                if two_way_mode and roman_text in {"Full automation", "Step-by-step execution"}:
                    post.append(('bullet', f"{two_way_count}) {roman_text}"))
                    two_way_count += 1
                    expect_body_after_heading = True
                    i += 1
                    continue
                if roman_text in _SHORT_HEADINGS or _QUESTION_HDG_RE.match(roman_text):
                    list_mode = roman_text in {"In short", "This makes it", "Script", "Business logic", "What happens here", "Results"}
                    post.append(('subsection', roman_text))
                    expect_body_after_heading = roman_text in {
                        "Core idea",
                        "End-to-end pipeline explanation",
                        "Configuration-driven setup",
                        "One-liner summary",
                        "Full automation",
                        "Step-by-step execution",
                        "Interactive demo",
                        "Fine-Tuning",
                        "Inference",
                    } or _QUESTION_HDG_RE.match(roman_text)
                elif expect_body_after_heading:
                    post.append(('body', roman_text))
                    expect_body_after_heading = False
                else:
                    post.append(('bullet', roman_text))
                i += 1
                continue
        if kind == 'body' and text.endswith(':'):
            # If the colon-line starts lowercase, it's a sentence continuation
            # (e.g. "supporting\nmultiple architectures:").  Merge it into the
            # previous body item instead of promoting to a subsection heading.
            if text[0].islower() and post and post[-1][0] == 'body':
                prev_k, prev_t = post[-1]
                post[-1] = ('body', prev_t + ' ' + text)
                list_mode = True
                two_way_mode = False
                expect_body_after_heading = False
                i += 1
                continue
            list_mode = True
            two_way_mode = False
            s = text.rstrip(':').strip()
            s = s[0].upper() + s[1:] if s else s
            post.append(('subsection', s))
            expect_body_after_heading = False
            i += 1
            continue

        if kind == 'bullet' and text.endswith(':'):
            list_mode = True
            two_way_mode = False
            s = text.rstrip(':').strip()
            s = s[0].upper() + s[1:] if s else s
            post.append(('subsection', s))
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
                        list_mode = t2 in {"In short", "This makes it", "Script", "What happens here"}
                        post.append(('subsection', t2))
                        expect_body_after_heading = t2 in {
                            "Core idea",
                            "End-to-end pipeline explanation",
                            "Configuration-driven setup",
                            "One-liner summary",
                            "Full automation",
                            "Step-by-step execution",
                            "Interactive demo",
                        } or _QUESTION_HDG_RE.match(t2)
                        continue
                    if t2.endswith(':'):
                        list_mode = True
                        post.append(('subsection', t2.rstrip(':').strip()))
                        expect_body_after_heading = False
                    elif _LIST_VERB_RE.match(t2) and len(t2.split()) == 1 and not _ENDS_SENT.search(t2):
                        # Short verb-only items (e.g. "Shows") → subsection + list_mode
                        list_mode = True
                        post.append(('subsection', t2))
                    else:
                        post.append(('bullet', t2))
                i = j
                continue

        if list_mode and kind == 'body':
            # If a quoted line appears, treat it as body and end list mode
            if (text.startswith('"') or text.startswith('“')) and (text.endswith('"') or text.endswith('”')):
                list_mode = False
                two_way_mode = False
                post.append(('body', text))
                post.append(('para_break', ''))
                expect_body_after_heading = False
                i += 1
                continue
            if text in _SHORT_HEADINGS or _QUESTION_HDG_RE.match(text):
                list_mode = text in {"In short", "This makes it", "Script", "Business logic", "What happens here", "Results"}
                post.append(('subsection', text))
                expect_body_after_heading = text in {
                    "Core idea",
                    "End-to-end pipeline explanation",
                    "Configuration-driven setup",
                    "One-liner summary",
                    "Full automation",
                    "Step-by-step execution",
                    "Interactive demo",
                    "Fine-Tuning",
                    "Inference",
                } or _QUESTION_HDG_RE.match(text)
                if text == "Two ways to run the system":
                    two_way_mode = True
                    two_way_count = 1
                else:
                    two_way_mode = False
                i += 1
                continue
            if (
                _STEP_HDG.match(text)
                or (_TITLE_HDG.match(text) and len(text.split()) <= 7 and not _ENDS_SENT.search(text) and not _LIST_VERB_RE.match(text))
            ):
                list_mode = False
                two_way_mode = False
                post.append(('subsection', text))
            else:
                # Long lines (>7 words) likely signal the end of a list —
                # treat as body and exit list mode.  Exception: lines that
                # start with a label pattern like "Word (file.py):" or
                # "ANN build (build_faiss.py):" are still list items even if long.
                is_labeled = bool(re.match(r'^[A-Z][\w\s]{0,30}\(', text))
                if len(text.split()) > 7 and not is_labeled and not findings_mode:
                    list_mode = False
                    two_way_mode = False
                    post.append(('body', text))
                elif two_way_mode and text in {"Full automation", "Step-by-step execution"}:
                    post.append(('bullet', f"{two_way_count}) {text}"))
                    two_way_count += 1
                    expect_body_after_heading = True
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
        # Standalone filenames (e.g. "Correcting_matching.py") → bullet
        if kind == 'body' and re.match(r'^[\w\-\.]+\.\w{1,4}$', text) and not _ENDS_SENT.search(text):
            post.append(('bullet', text))
            i += 1
            continue
        post.append((kind, text))
        i += 1

    # Project-specific cleanup: keep fare formula under Business logic as equation text.
    if title == "Bus Reservation And Ticketing System":
        normalized = []
        i = 0
        while i < len(post):
            kind, text = post[i]
            normalized.append((kind, text))
            if kind == 'subsection' and text == 'Business logic':
                j = i + 1
                business_bullets = []
                while j < len(post) and post[j][0] == 'bullet':
                    business_bullets.append(post[j][1].strip())
                    j += 1

                # Combine any split fare-formula bullets into one equation
                if len(business_bullets) >= 3:
                    b1, b2, b3 = business_bullets[0], business_bullets[1], business_bullets[2]
                    if b1.startswith('Total Fare =') and b2.startswith('(') and b3.startswith('+'):
                        eq = f"{b1} {b2} {b3}".replace('fare \u2013 20%', 'fare \u00d7 0.80').replace('fare - 20%', 'fare \u00d7 0.80')
                        normalized.append(('equation', eq))
                        i = j
                        continue

                if len(business_bullets) >= 2:
                    b1, b2 = business_bullets[0], business_bullets[1]
                    if b1.startswith('Total Fare =') and b2.startswith('+'):
                        eq = f"{b1} {b2}".replace('fare \u2013 20%', 'fare \u00d7 0.80').replace('fare - 20%', 'fare \u00d7 0.80')
                        normalized.append(('equation', eq))
                        i = j
                        continue

                if len(business_bullets) >= 1:
                    b1 = business_bullets[0]
                    if b1.startswith('Total Fare ='):
                        eq = b1.replace('fare \u2013 20%', 'fare \u00d7 0.80').replace('fare - 20%', 'fare \u00d7 0.80')
                        normalized.append(('equation', eq))
                        i = j
                        continue
            i += 1
        post = normalized

    # Project-specific cleanup: insert "Inference" sub-headings under each
    # centrality metric in the Raccoon network analysis project.
    if title == "Mammalia Raccoon Proximity Network Analysis":
        _CENTRALITY_HDGS = {
            "Closeness Centrality", "Betweenness Centrality",
            "Clustering Coefficient", "Eigenvector Centrality",
            "PageRank Algorithm",
        }
        # Raccoon-specific inference lines start with "Raccoon #" or contain
        # project-specific observations (not generic metric descriptions).
        _RACCOON_INF_RE = re.compile(
            r'^(?:Raccoon\s*#|Can\s+spread|Removing\s+or\s+vaccinating|'
            r'Infection\s+here|Connected\s+to\s+other|Considered\s+a\s+super|'
            r'Helps\s+rank)',
            re.IGNORECASE,
        )
        rebuilt = []
        i = 0
        while i < len(post):
            kind, text = post[i]
            if kind == 'section' and text in _CENTRALITY_HDGS:
                rebuilt.append((kind, text))
                i += 1
                # Collect all items until the next section heading or end
                desc_items = []
                inf_items = []
                in_inference = False
                while i < len(post) and not (post[i][0] == 'section' and post[i][1] not in _CENTRALITY_HDGS and not _RACCOON_INF_RE.match(post[i][1])):
                    pk, pt = post[i]
                    # Stop at the next centrality heading or a non-inference section
                    if pk == 'section' and pt in _CENTRALITY_HDGS:
                        break
                    if pk == 'section' and pt in {"Key Findings", "Technologies & Concepts Used"}:
                        break
                    if pk == 'subsection':
                        break
                    if not in_inference and _RACCOON_INF_RE.match(pt):
                        in_inference = True
                    if in_inference:
                        inf_items.append(('bullet', pt))
                    else:
                        desc_items.append(('bullet', pt))
                    i += 1
                for item in desc_items:
                    rebuilt.append(item)
                if inf_items:
                    rebuilt.append(('subsection', 'Inference'))
                    for item in inf_items:
                        rebuilt.append(item)
            else:
                rebuilt.append((kind, text))
                i += 1
        post = rebuilt

    # Project-specific cleanup for Object Detection Extension:
    # 1. "Training" should break out of "multiple architectures" list → subsection
    # 2. Items under "Output includes" should be bullets
    # 3. Items under "Key Observations" should be bullets
    if title == "Object Detection Extension":
        rebuilt = []
        i = 0
        while i < len(post):
            kind, text = post[i]
            # "Training" inside the architecture bullet list → subsection
            if kind == 'bullet' and text == 'Training':
                rebuilt.append(('subsection', 'Training'))
                i += 1
                continue
            # Body items under "Output includes" → bullets
            if kind == 'body' and i >= 2 and any(
                post[j][0] == 'subsection' and post[j][1] == 'Output includes'
                for j in range(max(0, i - 5), i)
                if j < len(post)
            ):
                # Check there's no intervening section/subsection heading
                intervening_hdg = False
                for j in range(i - 1, max(0, i - 5) - 1, -1):
                    if post[j][0] == 'subsection' and post[j][1] == 'Output includes':
                        break
                    if post[j][0] in ('section', 'subsection'):
                        intervening_hdg = True
                        break
                if not intervening_hdg:
                    rebuilt.append(('bullet', text))
                    i += 1
                    continue
            # Items under "Key Observations" → section becomes bullet
            if kind == 'section' and i >= 1:
                # Find the nearest preceding section/subsection
                for j in range(i - 1, max(0, i - 6) - 1, -1):
                    if post[j][0] in ('section', 'subsection'):
                        if post[j][1] == 'Key Observations':
                            rebuilt.append(('bullet', text))
                            i += 1
                            break
                        elif post[j][0] == 'section' and post[j][1] != 'Key Observations':
                            # Check if that section is itself under Key Observations
                            # (it could be a sibling bullet-converted section)
                            pass
                        else:
                            break
                else:
                    rebuilt.append((kind, text))
                    i += 1
                    continue
                if i <= len(post) and rebuilt and rebuilt[-1] == ('bullet', text):
                    continue
            # Body items after Key Observations section → bullets too
            if kind == 'body' and i >= 1:
                for j in range(i - 1, max(0, i - 8) - 1, -1):
                    pk, pt = post[j]
                    if pk == 'section' and pt == 'Key Observations':
                        rebuilt.append(('bullet', text))
                        i += 1
                        break
                    if pk == 'section' and pt != 'Key Observations':
                        continue  # could be a sibling under Key Observations
                    if pk in ('subsection',):
                        break
                else:
                    rebuilt.append((kind, text))
                    i += 1
                    continue
                if rebuilt and rebuilt[-1] == ('bullet', text):
                    continue
            rebuilt.append((kind, text))
            i += 1
        post = rebuilt

    # Project-specific cleanup for Online Event Management System.
    # The source PDF uses a flat bullet-list style which the generic
    # parser mis-classifies: action lines under "Key Actors" become
    # section headings, entity names under "Core Database Modules" become
    # bullets, etc.  We fix the structure in a single pass by tracking
    # which *logical section* we are inside.
    if title == "Online Event Management System":
        # ── Known headings for each structural level ─────────────────
        _OEM_SECTIONS = {
            "Key Actors", "Core Database Modules",
            "Database Design Highlights", "Important SQL Features Used",
            "Overall Summary",
        }
        _OEM_DB_ENTITIES = {
            "User", "Event Details", "Event Discount",
            "Special Preference", "User Booking", "Amount", "Admin",
        }
        _OEM_SQL_SUBSECTIONS = {"Queries", "Views", "Indexes"}
        _OEM_ACTOR_SUBSECTIONS = {"User", "Admin"}

        rebuilt = []
        cur_section = None    # tracks the current top-level section
        cur_subsection = None  # tracks the current subsection
        i = 0
        while i < len(post):
            kind, text = post[i]

            # ── Promote items that should be section headings ────────
            if text in _OEM_SECTIONS:
                rebuilt.append(('section', text))
                cur_section = text
                cur_subsection = None
                i += 1
                continue

            # ── Key Actors: "User" / "Admin" → subsection,
            #    everything else → bullet ─────────────────────────────
            if cur_section == "Key Actors":
                if text in _OEM_ACTOR_SUBSECTIONS:
                    rebuilt.append(('subsection', text))
                    cur_subsection = text
                    i += 1
                    continue
                # "Adds, updates, or deletes" is already a valid subsection
                if kind == 'subsection':
                    rebuilt.append((kind, text))
                    cur_subsection = text
                    i += 1
                    continue
                # Everything else under Key Actors is a bullet
                if kind in ('section', 'body'):
                    rebuilt.append(('bullet', text))
                    i += 1
                    continue

            # ── Core Database Modules ────────────────────────────────
            if cur_section == "Core Database Modules":
                # Entity names → subsection
                if text in _OEM_DB_ENTITIES:
                    rebuilt.append(('subsection', text))
                    cur_subsection = text
                    i += 1
                    continue
                # Description lines (currently subsection from colon
                # handler like "Stores registered user details") → body
                if kind == 'subsection':
                    rebuilt.append(('body', text + ':'))
                    i += 1
                    continue
                # Sentences → body
                if kind in ('body', 'bullet') and text.endswith('.'):
                    rebuilt.append(('body', text))
                    i += 1
                    continue
                # Short items → bullet
                if kind == 'bullet':
                    rebuilt.append(('bullet', text))
                    i += 1
                    continue
                # Body items that are short list-like lines → bullet
                if kind == 'body' and not text.endswith('.'):
                    rebuilt.append(('bullet', text))
                    i += 1
                    continue
                # Section-classified items that are actually bullets
                if kind == 'section':
                    rebuilt.append(('bullet', text))
                    i += 1
                    continue

            # ── Database Design Highlights: items → bullets ──────────
            if cur_section == "Database Design Highlights":
                if kind != 'section':
                    rebuilt.append(('bullet', text))
                    i += 1
                    continue

            # ── Important SQL Features Used ──────────────────────────
            if cur_section == "Important SQL Features Used":
                # Queries / Views / Indexes → subsection
                if text in _OEM_SQL_SUBSECTIONS:
                    rebuilt.append(('subsection', text))
                    cur_subsection = text
                    i += 1
                    continue
                # "Examples" → subsection
                if text == "Examples" or kind == 'subsection':
                    rebuilt.append(('subsection', text))
                    cur_subsection = text
                    i += 1
                    continue
                # Everything else → bullet
                if kind in ('section', 'body', 'bullet'):
                    rebuilt.append(('bullet', text))
                    i += 1
                    continue

            # ── Default: keep as-is ──────────────────────────────────
            rebuilt.append((kind, text))
            i += 1
        post = rebuilt

    # Project-specific cleanup for Sentiment Analysis Extension.
    # Several one-word heading names (Methodology, Applications, Deployment,
    # Conclusion) are misclassified as bullets.  Short sentence-like items
    # that belong under Deployment are misclassified as section headings.
    if title == "Sentiment Analysis Extension":
        _SA_SUBSECTION_NAMES = {
            "Methodology", "Applications", "Deployment", "Conclusion",
        }
        rebuilt = []
        i = 0
        cur_sub = None
        while i < len(post):
            kind, text = post[i]

            # Promote known names to subsection headings
            if text in _SA_SUBSECTION_NAMES:
                rebuilt.append(('subsection', text))
                cur_sub = text
                i += 1
                continue

            # Under "Deployment": body/section items → bullets
            if cur_sub == "Deployment" and kind in ('body', 'section'):
                rebuilt.append(('bullet', text))
                i += 1
                continue

            # Track current subsection for other subsections
            if kind == 'subsection':
                cur_sub = text

            # Body items right after Methodology that describe the process → bullets
            if cur_sub == "Methodology" and kind == 'body' and not text.endswith('.'):
                rebuilt.append(('bullet', text))
                i += 1
                continue

            rebuilt.append((kind, text))
            i += 1
        post = rebuilt
    # Project-specific cleanup for Synthetic Image Generation.
    if title == "Synthetic Image Generation":
        rebuilt = []
        i = 0
        while i < len(post):
            kind, text = post[i]

            # 1. "End-to-end pipeline explanation (...)" → section heading,
            #    strip the parenthetical coaching note.
            if 'End-to-end pipeline explanation' in text:
                import re as _re
                clean = _re.sub(r'\s*\([^)]*\)\s*$', '', text).strip()
                rebuilt.append(('section', clean))
                i += 1
                continue

            # 2. "Why synthetic data?" → section heading
            if text == 'Why synthetic data?':
                rebuilt.append(('section', text))
                i += 1
                continue

            # 3. Under "Two paths": "Or auto-annotate..." body → bullet
            if kind == 'body' and text.startswith('Or auto-annotate'):
                rebuilt.append(('bullet', text))
                i += 1
                continue

            # 4. "Two strategies" subsection: the merged body line with two
            #    strategies separated by arrow text → split into 2 bullets.
            if kind == 'body' and 'Spread-out placement' in text and 'Clustered placement' in text:
                # Split on "Clustered" since the two strategies were merged
                idx_split = text.find('Clustered placement')
                if idx_split > 0:
                    part1 = text[:idx_split].strip()
                    part2 = text[idx_split:].strip()
                    rebuilt.append(('bullet', part1))
                    rebuilt.append(('bullet', part2))
                else:
                    rebuilt.append(('bullet', text))
                i += 1
                continue

            # 5. "This increases" / "This helps" / "This step simplifies" →
            #    body text (not subsection heading) so it reads naturally.
            if kind == 'subsection' and text in {'This increases', 'This helps', 'This step simplifies'}:
                rebuilt.append(('body', text + ':'))
                i += 1
                continue

            # 6. Remove coaching notes: "If interviewer asks...",
            #    "You can say", and the response body after it.
            if 'interviewer asks' in text.lower():
                i += 1
                continue
            if text == 'You can say':
                # Also skip the body line that follows
                i += 1
                if i < len(post) and post[i][0] == 'body':
                    i += 1
                continue

            rebuilt.append((kind, text))
            i += 1
        post = rebuilt

    # Project-specific cleanup for Multi-Agent Architecture.
    # The source PDF has a table (Component | Responsible for) that the
    # text extractor fragments into many broken lines.  We replace the
    # entire "Core components & their roles" section with properly
    # merged entries, and fix several other structural issues.
    if title == "Multi-Agent Architecture":
        # ── 1. Build replacement items for the components table ──────
        _COMP_TABLE = [
            ('subsection', 'PlannerAgent / LLMPlanner'),
            ('body', 'Translate objectives into steps. Can be deterministic or LLM-assisted.'),
            ('subsection', 'ExecutorAgent'),
            ('body', 'Implements the actual data transformations (load, assign_quarter, aggregate, churn, validate, reflect).'),
            ('subsection', 'ValidatorAgent / LLMValidator'),
            ('body', 'Checks totals, churn sanity, etc. Optionally asks an LLM to review outputs.'),
            ('subsection', 'ReflectionAgent'),
            ('body', 'Scores results and returns suggestions ("investigate lost clients", "retry aggregation", etc.).'),
            ('subsection', 'MemoryManager'),
            ('body', 'Tracks short-term step outputs, compresses summaries to long-term memory, maintains idempotency and a tiny semantic index.'),
            ('subsection', 'CircuitBreaker'),
            ('body', 'Stops repeating failing steps after a threshold.'),
            ('subsection', 'MetricsCollector'),
            ('body', 'Simple in-process counters & timers written to metrics.json.'),
            ('subsection', 'GraphRunner'),
            ('body', 'Executes a dependency graph, honouring depends_on and allowing parallelism.'),
            ('subsection', 'SemanticMemory'),
            ('body', 'Deterministic vector store used by agents/LLMs for retrieval.'),
        ]

        # Text markers for the table region
        _TABLE_START = 'Component Responsible for'
        _TABLE_END_TEXTS = {'Tools package', 'Deterministic helpers called by executors'}

        rebuilt = []
        i = 0
        while i < len(post):
            kind, text = post[i]

            # "Every execution is a closed-loop..." → body (not subsection)
            if text.startswith('Every execution is a closed-loop'):
                rebuilt.append(('body', text + ':'))
                i += 1
                continue

            # Run-loop agent lines → bullets
            if kind == 'body' and any(text.startswith(p) for p in [
                'Planner –', 'Executor –', 'Validator –',
                'Reflection –', 'Orchestrator –',
            ]):
                rebuilt.append(('bullet', text))
                i += 1
                continue

            # "Component Responsible for" table header → replace with
            # the cleaned table and skip all broken table lines.
            if text == _TABLE_START:
                # Emit the table header row is already the section heading,
                # skip it and all table rows until we hit "Tools package"
                i += 1
                while i < len(post):
                    pk, pt = post[i]
                    if pt in _TABLE_END_TEXTS:
                        break
                    i += 1
                # Insert cleaned table
                rebuilt.extend(_COMP_TABLE)
                continue

            # "Retries with exponential backoff" section + "(configurable...)" body → merge
            if text == 'Retries with exponential backoff':
                merged_text = text
                if i + 1 < len(post) and post[i + 1][1].startswith('(configurable'):
                    merged_text += ' ' + post[i + 1][1]
                    i += 2
                else:
                    i += 1
                rebuilt.append(('body', merged_text))
                continue

            # "Memory managers are called throughout" section + body → merge to body
            if text == 'Memory managers are called throughout':
                merged_text = text
                if i + 1 < len(post) and post[i + 1][0] == 'body':
                    merged_text += ' ' + post[i + 1][1]
                    i += 2
                else:
                    i += 1
                rebuilt.append(('body', merged_text))
                continue

            # "Graph execution" as bullet → subsection
            if kind == 'bullet' and text == 'Graph execution':
                rebuilt.append(('subsection', text))
                i += 1
                continue

            # "Final note" as bullet → subsection
            if kind == 'bullet' and text == 'Final note':
                rebuilt.append(('subsection', text))
                i += 1
                continue

            # Reliability items (dash-separated) → bullets
            if kind == 'body' and ' – ' in text and any(text.startswith(p) for p in [
                'Retries & backoff', 'Circuit breaker', 'Idempotency',
                'Metrics', 'Logs', 'Tests',
            ]):
                rebuilt.append(('bullet', text))
                i += 1
                continue

            # "open" continuation line after Circuit breaker → merge with previous
            if kind == 'body' and 'open' in text[:10] and 'abort' in text and rebuilt and rebuilt[-1][1].startswith('Circuit breaker'):
                prev_k, prev_t = rebuilt[-1]
                rebuilt[-1] = (prev_k, prev_t + ' ' + text)
                i += 1
                continue

            # Multi-agent collaboration items (Separation, Pluggability, etc.) → bullets
            # "Separation of concerns" may arrive as bullet+body split (continuation)
            if ' – ' in text and any(text.startswith(p) for p in [
                'Separation of concerns', 'Pluggability', 'Deterministic fallbacks',
            ]):
                merged = text
                # If the line ends with a comma, the next body line is a continuation
                while (i + 1 < len(post)
                       and post[i + 1][0] == 'body'
                       and post[i + 1][1][0].islower()):
                    merged += ' ' + post[i + 1][1]
                    i += 1
                rebuilt.append(('bullet', merged))
                i += 1
                continue

            # Tools package items → bullets
            if kind == 'body' and any(text.startswith(p) for p in [
                'DataLoader', 'Validator –', 'SemanticMemory –', 'MemoryManager –',
            ]):
                rebuilt.append(('bullet', text))
                i += 1
                continue

            # "Workflow highlights from tests" items → bullets
            if kind == 'body' and any(text.startswith(p) for p in [
                'Chunking', 'GraphRunner correctly', 'Circuit breaker trips',
                'LLMPlanner respects', 'Semantic memory returns',
                'Orchestrator accepts',
            ]):
                rebuilt.append(('bullet', text))
                i += 1
                continue

            # Memory model items → bullets
            if kind == 'body' and any(text.startswith(p) for p in [
                'Short-term', 'Long-term', 'Semantic –',
            ]):
                rebuilt.append(('bullet', text))
                i += 1
                continue

            # Post-run reflection items → bullets
            if kind == 'body' and any(text.startswith(p) for p in [
                'Reflection suggestions', 'Metrics and logs',
                'Visualizations generated',
            ]):
                rebuilt.append(('bullet', text))
                i += 1
                continue

            # "Orchestrator runs load_data" subsection + fragmented bullets/body → merge
            if text.startswith('Orchestrator runs load_data'):
                merged = text + ':'
                i += 1
                # Absorb following bullets/body until we hit a section or
                # "Orchestrator persists" (which starts a new sentence)
                while i < len(post):
                    nk, nt = post[i]
                    if nk == 'section':
                        break
                    if nt.startswith('Orchestrator persists'):
                        # This is a separate sentence – keep it as body
                        break
                    merged += ' ' + nt
                    i += 1
                rebuilt.append(('body', merged))
                continue

            rebuilt.append((kind, text))
            i += 1
        post = rebuilt

    return post


# ── Drawing utilities ─────────────────────────────────────────────────────────
def _rrect(cv, x, y, w, h, r, fill, stroke=False):
    """Draw a rounded rectangle."""
    cv.setFillColor(fill)
    cv.roundRect(x, y, w, h, r, fill=1, stroke=stroke)


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
        self.y -= block_h + 0.5 * cm

    def equation(self, content: str):
        """Draw an equation at normal body font size."""
        self._need(LH)
        self.c.setFont(F, S_BODY)
        self.c.setFillColor(C_BODY)
        self.c.drawString(ML + 0.45 * cm, self.y, content)
        self.y -= LH

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

    # Special center alignment for Video RAG Retrieval Project summary lines
    def center_text(writer, content, font=F, size=S_BODY):
        lines = simpleSplit(content, font, size, CW)
        writer._need(len(lines) * LH)
        writer.c.setFont(font, size)
        writer.c.setFillColor(C_BODY)
        for line in lines:
            text_width = writer.c.stringWidth(line, font, size)
            x = ML + (CW - text_width) / 2
            writer._need(LH)
            writer.c.drawString(x, writer.y, line)
            writer.y -= LH

    # FULL TECHNICAL WALKTHROUGH (sourced from original PDF or projects.json)
    if source_items:
        # Center-align the first two body lines if this is Video RAG Retrieval Project
        if project["title"] == "Video RAG Retrieval Project":
            # Find the indices of the summary and problem statement
            filtered_items = []
            centered_sections = {"One-line summary", "Problem statement"}
            i = 0
            while i < len(source_items):
                kind, content = source_items[i]
                if kind == "section" and content in centered_sections:
                    # Add the section label as usual
                    filtered_items.append((kind, content))
                    # Center-align the next body if present
                    if i + 1 < len(source_items) and source_items[i+1][0] == "body":
                        filtered_items.append(("centered_body", source_items[i+1][1]))
                        i += 1
                else:
                    filtered_items.append((kind, content))
                i += 1
            source_items = filtered_items
        # Remove walkthrough items that duplicate the Key Details bullets,
        # the overview/impact text, or the project title/github URL.
        key_bullets = {_normalize_ws(b) for b in project.get("bullets", [])}
        skip_texts = set(key_bullets)
        # Also skip lines that are substrings of the summary/impact
        summary_norm = _normalize_ws(project.get("summary", ""))
        impact_norm = _normalize_ws(project.get("impact", ""))
        github_url = (project.get("github") or "").strip()
        title_text = project.get("title", "").strip()

        filtered_items = []
        # Structural labels already rendered by the PDF template
        _STRUCT_LABELS = {"OVERVIEW", "IMPACT", "TECHNICAL WALKTHROUGH", "KEY DETAILS",
                          "Overview", "Impact", "Technical Walkthrough", "Key Details"}
        tech_names = {t.strip() for t in project.get("techs", [])}
        for k, t in source_items:
            t_norm = _normalize_ws(t)
            if t_norm in skip_texts:
                continue
            if t_norm == title_text:
                continue
            if github_url and t_norm == github_url:
                continue
            # Skip structural section labels that the template already renders
            if t_norm in _STRUCT_LABELS:
                continue
            # Skip tech pill names echoed from the source PDF header
            if t_norm in tech_names:
                continue
            # Skip lines that are part of the already-shown summary or impact
            if len(t_norm) > 30 and (t_norm in summary_norm or t_norm in impact_norm):
                continue
            filtered_items.append((k, t))

        w.section_label("Technical Walkthrough")
        num = 1
        under_step = False
        for kind, content in filtered_items:
            if kind in ('section', 'subsection'):
                w.gap(0.15 * cm)
                w.heading(content)
                num = 1
                under_step = bool(_STEP_HDG.match(content))
            elif kind == 'centered_body':
                center_text(w, content)
            elif kind == 'body':
                under_step = False
                if content.endswith(':'):
                    num = 1
                w.text(content, indent=0.4 * cm)
            elif kind == 'bullet':
                m = re.match(r'^(\d+)\)\s+(.*)$', content)
                if m:
                    w.bullet_card(m.group(2), prefix=m.group(1))
                elif under_step:
                    w.bullet_card(content, prefix="-")
                else:
                    w.bullet_card(content, prefix=f"{_to_roman(num)})")
                    num += 1
            elif kind == 'equation':
                w.equation(content)
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
