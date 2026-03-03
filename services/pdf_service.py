from io import BytesIO
from pathlib import Path
from fpdf import FPDF
from pypdf import PdfReader, PdfWriter
from utils.dates import today_str_fr

TEMPLATE_PATH = Path("assets/NDA NYVALmodèle type.pdf")

DEBUG_BOXES = False
FONT_NAME = "Helvetica"

FIELD_CONFIG = {
    "company_name": {
        "box": (70, 156, 50, 10),     # x, y, w, h (top-left box)
        "text": (50, 160),             # x, baseline y
        "max_width": 145,
        "font_size": 10,
        "wrap": False,
    },
    "legal_form": {
        "box": (120, 156, 50, 10),
        "text": (200, 160),
        "max_width": 85,
        "font_size": 10,
        "wrap": False,
    },
    "hq_address": {
        # taller box so it can wrap to 2 lines
        "box": (300, 156, 40, 20),
        "text": (300, 145),            # y here acts like top for wrapped text
        "max_width": 85,
        "font_size":4,
        "wrap": True,
        "line_height": 11,
        "max_lines": 2,
    },
    "rep_name": {
        "box": (425, 150, 100, 16),
        "text": (450, 160),
        "max_width": 195,
        "font_size": 10,
        "wrap": False,
    },
    "job_title": {
        "box": (80, 168, 50, 10),
        "text": (80, 175),
        "max_width": 205,
        "font_size": 10,
        "wrap": False,
    },
    "date": {
        "box": (50, 740, 70, 16),
        "text": (50, 740),
        "max_width": 105,
        "font_size": 10,
        "wrap": False,
    },
    "nyval_phrase": {
        "box": (25, 120, 180, 14),   # area to clear above signature
        "text": (25, 120),           # baseline y
        "max_width": 175,
        "font_size": 10,
        "wrap": False,
    },
    "nyval_signature": {
        # box used to clear any placeholder area behind signature if needed
        "box": (100, 90, 180, 60),   # signature area
        "img": (100, 90, 160, 50),   # x, y, width, height for image
    },
}

def draw_fit_text(pdf, x, y, text, max_width, font_name=FONT_NAME, font_size=10, min_size=7):
    size = font_size
    pdf.set_font(font_name, size=size)
    while pdf.get_string_width(text) > max_width and size > min_size:
        size -= 0.5
        pdf.set_font(font_name, size=size)
    pdf.text(x, y, text)

def cover_placeholder(pdf, x, y, w, h, debug=False):
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(x, y, w, h, style="F")
    if debug:
        pdf.set_draw_color(255, 0, 0)
        pdf.rect(x, y, w, h, style="D")

def draw_wrapped_text(pdf, x, y_top, text, w, font_size=9.5, line_height=11, max_lines=2):
    """
    Wrap into max_lines using multi_cell inside the box width.
    """
    pdf.set_font(FONT_NAME, size=font_size)
    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(x, y_top)
    pdf.multi_cell(w=w, h=line_height, txt=text, border=0)
    # Box height limits the visible lines. If you want strict max_lines truncation,
    # we can implement manual wrap later.

def place_field(pdf, field_name, value):
    cfg = FIELD_CONFIG[field_name]
    box_x, box_y, box_w, box_h = cfg["box"]
    text_x, text_y = cfg["text"]

    cover_placeholder(pdf, box_x, box_y, box_w, box_h, debug=DEBUG_BOXES)

    if cfg.get("wrap"):
        draw_wrapped_text_two_lines(
            pdf,
            x=text_x,
            y_top=text_y,  # text_y should represent TOP of the address area
            w=box_w,
            value=value,
            font_size=cfg.get("font_size", 9.5),
            line_height=cfg.get("line_height", 11),
        )
    else:
        draw_fit_text(
            pdf,
            text_x,
            text_y,
            value,
            max_width=cfg["max_width"],
            font_size=cfg["font_size"],
        )

from io import BytesIO
from fpdf import FPDF
from pypdf import PdfReader, PdfWriter
from utils.dates import today_str_fr

def generate_nda_pdf(company_name: str, legal_form: str, rep_name: str, job_title: str, hq_address: str) -> bytes:
    reader = PdfReader(str(TEMPLATE_PATH))
    writer = PdfWriter()

    # -------------------------
    # Page 1 overlay: fields
    # -------------------------
    page1 = reader.pages[0]
    w1 = float(page1.mediabox.width)
    h1 = float(page1.mediabox.height)

    overlay1 = FPDF(unit="pt", format=(w1, h1))
    overlay1.add_page()
    overlay1.set_auto_page_break(False)

    place_field(overlay1, "company_name", company_name)
    place_field(overlay1, "legal_form", legal_form)
    place_field(overlay1, "hq_address", hq_address)
    place_field(overlay1, "rep_name", rep_name)
    place_field(overlay1, "job_title", job_title)
    place_field(overlay1, "date", today_str_fr())

    overlay1_bytes = bytes(overlay1.output(dest="S"))
    overlay1_reader = PdfReader(BytesIO(overlay1_bytes))
    page1.merge_page(overlay1_reader.pages[0])
    writer.add_page(page1)

    # -------------------------
    # Page 2 overlay: signature
    # -------------------------
    if len(reader.pages) >= 2:
        page2 = reader.pages[1]
        w2 = float(page2.mediabox.width)
        h2 = float(page2.mediabox.height)

        overlay2 = FPDF(unit="pt", format=(w2, h2))
        overlay2.add_page()
        overlay2.set_auto_page_break(False)

        # NYVAL fixed signature block (page 2 only)
        place_field(overlay2, "nyval_phrase", "lu et approuvé")
        place_signature(overlay2, "nyval_signature")

        overlay2_bytes = bytes(overlay2.output(dest="S"))
        overlay2_reader = PdfReader(BytesIO(overlay2_bytes))
        page2.merge_page(overlay2_reader.pages[0])
        writer.add_page(page2)

        # Add remaining pages untouched (if any)
        for i in range(2, len(reader.pages)):
            writer.add_page(reader.pages[i])
    else:
        # If there is no page 2, just output page 1 (rare)
        pass

    out = BytesIO()
    writer.write(out)
    return out.getvalue()

def wrap_two_lines(pdf: FPDF, text: str, max_width: float) -> tuple[str, str]:
    words = (text or "").split()
    if not words:
        return "", ""

    line1_words = []
    i = 0
    while i < len(words):
        candidate = (" ".join(line1_words + [words[i]])).strip()
        if pdf.get_string_width(candidate) <= max_width:
            line1_words.append(words[i])
            i += 1
        else:
            break

    line1 = " ".join(line1_words).strip()
    rest = words[i:]

    if not rest:
        return line1, ""

    line2_words = []
    for w in rest:
        candidate = (" ".join(line2_words + [w])).strip()
        if pdf.get_string_width(candidate) <= max_width:
            line2_words.append(w)
        else:
            break

    line2 = " ".join(line2_words).strip()

    # If still more words remain, truncate and add ellipsis
    remaining = rest[len(line2_words):]
    if remaining:
        # try to add "..." within width
        ell = "..."
        while pdf.get_string_width((line2 + ell).strip()) > max_width and line2_words:
            line2_words.pop()
            line2 = " ".join(line2_words).strip()
        line2 = (line2 + " ...").strip()

    return line1, line2

def draw_wrapped_text_two_lines(pdf: FPDF, x: float, y_top: float, w: float, value: str, font_size=9.5, line_height=11):
    pdf.set_font(FONT_NAME, size=font_size)
    pdf.set_text_color(0, 0, 0)

    l1, l2 = wrap_two_lines(pdf, value, max_width=w)

    # y_top is the top of the address box. We write baselines using line_height.
    pdf.text(x, y_top + line_height, l1)
    if l2:
        pdf.text(x, y_top + 2 * line_height, l2)


from pathlib import Path

SIGNATURE_PATH = Path("assets/signature_nyval.png")

def place_signature(pdf: FPDF, field_name: str):
    cfg = FIELD_CONFIG[field_name]
    box_x, box_y, box_w, box_h = cfg["box"]

    # Clear area (white)
    cover_placeholder(pdf, box_x, box_y, box_w, box_h, debug=DEBUG_BOXES)

    if not SIGNATURE_PATH.exists():
        # Keep it explicit so you notice immediately during testing
        raise FileNotFoundError(f"Signature file missing: {SIGNATURE_PATH}")

    img_x, img_y, img_w, img_h = cfg["img"]
    pdf.image(str(SIGNATURE_PATH), x=img_x, y=img_y, w=img_w, h=img_h)