from __future__ import annotations

from io import BytesIO
from pathlib import Path
from datetime import datetime
import zipfile

DOCX_TEMPLATE = Path("assets/nda_template.docx")

def fill_nda_docx(
    company_name: str,
    legal_form: str,
    rep_fullname: str,
    job_title: str,
    hq_address: str,
) -> bytes:
    if not DOCX_TEMPLATE.exists():
        raise FileNotFoundError(f"DOCX template not found: {DOCX_TEMPLATE}")

    today = datetime.now().strftime("%d/%m/%Y")

    # These exact placeholder texts exist in your DOCX (inside brackets in the template)
    mapping = {
        "NOM DE LA SOCIÉTÉ CLIENTE": company_name,
        "Forme juridique": legal_form,
        "Adresse": hq_address,
        "Nom du représentant": rep_fullname,
        "Titre": job_title,
        "Nom du signataire": rep_fullname,  # page 2 signature block uses this
    }

    with zipfile.ZipFile(DOCX_TEMPLATE, "r") as zin:
        xml = zin.read("word/document.xml").decode("utf-8")

        # Replace placeholder words
        for key, val in mapping.items():
            xml = xml.replace(key, val)

        # The template shows placeholders inside brackets, like [Adresse].
        # Remove brackets globally so output looks clean.
        xml = xml.replace("[", "").replace("]", "")

        # The template includes a date line like " /2026 en deux exemplaires."
        # Replace that with the full date.
        xml = xml.replace(" /2026 en deux exemplaires.", f" {today} en deux exemplaires.")

        # Rebuild the docx
        out = BytesIO()
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == "word/document.xml":
                    zout.writestr(item, xml.encode("utf-8"))
                else:
                    zout.writestr(item, zin.read(item.filename))

    return out.getvalue()