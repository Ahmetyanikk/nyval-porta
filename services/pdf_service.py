from io import BytesIO
from pathlib import Path
from fpdf import FPDF
from pypdf import PdfReader, PdfWriter
from utils.dates import today_str_fr

TEMPLATE_PATH = Path("assets/nda_template_clean.pdf")

DEBUG_BOXES = False
OPEN_SANS_REGULAR = "assets/fonts/OpenSans-Regular.ttf"
FONT_NAME = "OpenSans"

def init_font(pdf: FPDF, size: float):
    pdf.add_font(FONT_NAME, "", OPEN_SANS_REGULAR, uni=True)
    pdf.set_font(FONT_NAME, size=size)
    pdf.set_text_color(0, 0, 0)  # pure black

FIELD_CONFIG = {
    "company_name": {
        "box": (30, 153, 0, 0),     # x, y, w, h (top-left box)
        "text": (50, 178),             # x, baseline y
        "max_width": 145,
        "font_size": 10,
        "wrap": False,
    },
    "legal_form": {
        "box": (175, 153, 0, 0),
        "text": (172, 178),
        "max_width": 85,
        "font_size": 10,
        "wrap": False,
    },
    "hq_address": {
        # taller box so it can wrap to 2 lines
        "box": (290, 150, 0, 0),
        "text": (250, 167),            # y here acts like top for wrapped text
        "max_width": 85,
        "font_size":10,
        "wrap": True,
        "line_height": 11,
        "max_lines": 6,
    },
    "rep_name": {
        "box": (400, 150, 0, 0),
        "text": (450, 179),
        "max_width": 195,
        "font_size": 10,
        "wrap": False,
    },
    "job_title": {
        "box": (80, 168, 0, 0),
        "text": (110, 192),
        "max_width": 205,
        "font_size": 10,
        "wrap": False,
    },
    "date": {
        "box": (40, 740, 0,0),
        "text": (130, 760),
        "max_width": 105,
        "font_size": 10,
        "wrap": False,
    },
    "nyval_phrase": {
        "box": (25, 80, 0, 0),   # area to clear above signature
        "text": (25, 105),           # baseline y
        "max_width": 175,
        "font_size": 10,
        "wrap": False,
    },
    "nyval_signature": {
        # box used to clear any placeholder area behind signature if needed
        "box": (100, 105, 0, 0),   # signature area
        "img": (10, 140, 160, 40),   # x, y, width, height for image
    },
    "rep_name_2": {
        "box": (13, 170, 0, 0),
        "text": (25, 262),
        "max_width": 195,
        "font_size": 10,
        "wrap": False,
    },
    "job_title_2": {
        "box": (110, 170, 0, 0),
        "text": (120, 262),
        "max_width": 205,
        "font_size": 10,
        "wrap": False,
    },
}

def draw_fit_text(pdf, x, y, text, max_width, font_name=FONT_NAME, font_size=10, min_size=7):
    size = font_size
    pdf.set_font(font_name, size=size)
    pdf.set_text_color(0, 0, 0)
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
        draw_wrapped_text_n_lines(
            pdf,
            x=text_x,
            y_top=text_y,  # should be TOP of the address box
            w=box_w,
            value=value,
            font_size=cfg.get("font_size", 10),
            line_height=cfg.get("line_height", 11),
            max_lines=cfg.get("max_lines", 3),
            min_font_size=8.5,
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
    init_font(overlay1, size=11.5)
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
        init_font(overlay2, size=11.5)
        # NYVAL fixed signature block (page 2 only)
        place_field(overlay2, "nyval_phrase", "lu et approuvé")
        place_signature(overlay2, "nyval_signature")
        place_field(overlay2, "rep_name_2", rep_name)
        place_field(overlay2, "job_title_2", job_title)
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

def wrap_lines(pdf: FPDF, text: str, max_width: float, max_lines: int) -> list[str]:
    words = (text or "").split()
    if not words:
        return [""]

    lines: list[str] = []
    i = 0

    while i < len(words) and len(lines) < max_lines:
        line_words = []
        while i < len(words):
            cand = " ".join(line_words + [words[i]])
            if pdf.get_string_width(cand) <= max_width:
                line_words.append(words[i])
                i += 1
            else:
                break
        if not line_words:
            # Single word longer than width: hard cut (rare)
            lines.append(words[i])
            i += 1
        else:
            lines.append(" ".join(line_words))

    # If text still remains, truncate last line with ellipsis
    if i < len(words) and lines:
        last = lines[-1]
        ell = " ..."
        while pdf.get_string_width((last + ell).strip()) > max_width and last:
            last = last[:-1]
        lines[-1] = (last.strip() + ell).strip()

    return lines


def draw_wrapped_text_n_lines(
    pdf: FPDF,
    x: float,
    y_top: float,
    w: float,
    value: str,
    font_size: float,
    line_height: float,
    max_lines: int,
    min_font_size: float = 8.0,
):
    """
    Writes up to max_lines. If it doesn't fit, it will try to reduce font size a bit,
    then truncate with ellipsis.
    """
    size = font_size
    while True:
        pdf.set_font(FONT_NAME, size=size)
        pdf.set_text_color(0, 0, 0)

        lines = wrap_lines(pdf, value, max_width=w, max_lines=max_lines)

        # Always write within max_lines; wrap_lines already enforces it.
        # If we had to truncate heavily, shrinking helps readability.
        # We'll shrink until we reach min_font_size (optional).
        if size <= min_font_size:
            break

        # If the last line ends with ellipsis, try a slightly smaller font to fit more
        if lines and lines[-1].endswith("...") and size - 0.5 >= min_font_size:
            size -= 0.5
            continue
        break

    # Write lines
    for idx, line in enumerate(lines[:max_lines]):
        pdf.text(x, y_top + (idx + 1) * line_height, line)


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