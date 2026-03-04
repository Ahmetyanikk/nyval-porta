import streamlit as st
from pathlib import Path
from services.validation_service import validate_single_upload, validate_multi_upload, MAX_MB_DEFAULT
from services.docx_service import fill_nda_docx
from services.storage_service import make_batch_root, save_vault_files
st.set_page_config(page_title="NYVAL - Dépôt de Données Sécurisé", page_icon="❄️", layout="centered")
from services.pdf_service import generate_nda_pdf


# Load Dark Tech CSS
css_path = Path("assets/styles.css")
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# Header
st.title("NYVAL - Dépôt de Données Sécurisé")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("assets/logonyval.png", width=360)
st.markdown(
    "Ce portail est destiné à la transmission des données de consommation pour la réalisation de votre Audit Flash. "
    "Les données sont cryptées et traitées sous 48h par notre moteur d’intelligence énergétique."
)

st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

# NDA inputs (5 fields)

st.markdown("<div class='ny-card-title'>Informations NDA</div>", unsafe_allow_html=True)

company_name = st.text_input("Company Name *", placeholder="Ex: STEF")
legal_form = st.text_input("Legal Form *", placeholder="Ex: SAS, SARL, SA")
rep_fullname = st.text_input("Representative Name & Last Name *", placeholder="Ex: Jean Dupont")
job_title = st.text_input("Job Title *", placeholder="Ex: Directeur des Opérations")
hq_address = st.text_input("Headquarters Address *", placeholder="Adresse complète")

st.markdown(
    "<div class='ny-help'>Les 5 champs ci-dessus sont requis pour générer un NDA valide.</div>",
    unsafe_allow_html=True
)

generate_pdf = st.button("Générer un NDA (PDF)")

if generate_pdf:
    missing_nda = []
    if not company_name.strip(): missing_nda.append("Company Name")
    if not legal_form.strip(): missing_nda.append("Legal Form")
    if not rep_fullname.strip(): missing_nda.append("Representative Name & Last Name")
    if not job_title.strip(): missing_nda.append("Job Title")
    if not hq_address.strip(): missing_nda.append("Headquarters Address")

    if missing_nda:
        st.error("Veuillez remplir les champs relatifs à l'accord de confidentialité.: " + ", ".join(missing_nda))
    else:
        pdf_bytes = generate_nda_pdf(company_name, legal_form, rep_fullname, job_title, hq_address)
        st.download_button(
            "Télécharger le NDA (PDF)",
            data=pdf_bytes,
            file_name=f"NYVAL_NDA_{company_name.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )


st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# Upload vault sections

st.markdown("<div class='ny-card-title'>Dépôt de Données</div>", unsafe_allow_html=True)



# ENEDIS (Vault)
#st.markdown("<div class='ny-vault'>", unsafe_allow_html=True)
st.markdown("<div class='ny-vault-title'>Export ENEDIS (Point 10 minutes - 12 mois) *</div>", unsafe_allow_html=True)

enedis_file = st.file_uploader(" ", type=["csv", "xlsx"], key="enedis")

st.markdown(
    "<div class='ny-help'>Format .csv ou .xlsx uniquement. L’exactitude de l’audit dépend de la précision de ce fichier.</div>",
    unsafe_allow_html=True
)
st.markdown("<div class='ny-help'>Limite: 25 MB par fichier.</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

# Invoices (Vault)
#st.markdown("<div class='ny-vault'>", unsafe_allow_html=True)
st.markdown("<div class='ny-vault-title'>Justificatifs de Facturation (Dernier trimestre complet) *</div>", unsafe_allow_html=True)

invoice_files = st.file_uploader(" ", type=["pdf"], accept_multiple_files=True, key="invoices")

st.markdown(
    "<div class='ny-help'>Exports PDF originaux (recto-verso) récupérés sur votre portail fournisseur. Indispensable pour l’analyse du TURPE et des puissances souscrites.</div>",
    unsafe_allow_html=True
)
st.markdown("<div class='ny-help'>Limite: 25 MB par fichier.</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

# WMS (Vault)
#st.markdown("<div class='ny-vault'>", unsafe_allow_html=True)
st.markdown("<div class='ny-vault-title'>Cartographie des Flux Logistiques (Entrées / Sorties Quai) *</div>", unsafe_allow_html=True)

wms_file = st.file_uploader(" ", type=["csv", "xlsx"], key="wms")

st.markdown(
    "<div class='ny-help'>Fichier Excel (.xlsx) ou CSV issu de votre WMS. Doit idéalement contenir les créneaux d’entrées/sorties de marchandises et le volume de palettes.</div>",
    unsafe_allow_html=True
)
st.markdown("<div class='ny-help'>Limite: 25 MB par fichier.</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
# Confirmation checkbox
st.markdown("**Je confirme que les données transmises sont exactes et j'accepte le protocole de confidentialité NYVAL** *")
accept = st.checkbox("J'accepte")

# Link to protocol (for now we link NDA template, or you can replace with real URL)
protocol_url = None  # set to a real URL if client provides one
if protocol_url:
    st.markdown(f"[Consulter le protocole de confidentialité NYVAL]({protocol_url})")
else:
    nda_url = "https://github.com/Ahmetyanikk/nyval-porta/blob/main/assets/NDA%20NYVALmod%C3%A8le%20type.pdf"

    st.markdown(
        f"<a href='{nda_url}' target='_blank' style='color: rgba(70,240,255,0.95); text-decoration: none; font-weight: 700;'>"
        "Consulter le protocole de confidentialité NYVAL"
        "</a>",
        unsafe_allow_html=True
    )

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

# Submit button behavior (UI only for now)
submit = st.button("Submit →")

if submit:
    missing = []
    if not company_name.strip(): missing.append("Company Name")
    if not legal_form.strip(): missing.append("Legal Form")
    if not rep_fullname.strip(): missing.append("Representative Name & Last Name")
    if not job_title.strip(): missing.append("Job Title")
    if not hq_address.strip(): missing.append("Headquarters Address")
    if enedis_file is None: missing.append("Export ENEDIS file")
    if not invoice_files: missing.append("Invoice PDFs")
    if wms_file is None: missing.append("WMS file")
    if not accept: missing.append("Protocol acceptance")

    # File validation (types + size limit)
    errors = []
    if enedis_file is not None:
        errors += validate_single_upload(enedis_file, (".csv", ".xlsx"), MAX_MB_DEFAULT)
    if invoice_files:
        errors += validate_multi_upload(invoice_files, (".pdf",), MAX_MB_DEFAULT)
    if wms_file is not None:
        errors += validate_single_upload(wms_file, (".csv", ".xlsx"), MAX_MB_DEFAULT)

    if missing:
        st.error("Champs manquants: " + ", ".join(missing))
    elif errors:
        st.error("Problèmes fichiers:")
        for e in errors:
            st.write(f"- {e}")
    else:
        # Save files to local folders
        batch_root = make_batch_root(company_name)

        saved_all = []
        saved_all += save_vault_files(batch_root, "enedis", enedis_file)
        saved_all += save_vault_files(batch_root, "invoices", invoice_files)
        saved_all += save_vault_files(batch_root, "wms", wms_file)

        st.success("Merci. Vos données ont été déposées avec succès.")

        # Confirmation summary
        
        st.markdown("<div class='ny-card-title'>Résumé du dépôt</div>", unsafe_allow_html=True)

        st.write(f"Company: {company_name}")
        st.write(f"Batch: {batch_root}")

        counts = {"enedis": 0, "invoices": 0, "wms": 0}
        for s in saved_all:
            counts[s.vault] += 1

        st.write(f"ENEDIS files saved: {counts['enedis']}")
        st.write(f"Invoice PDFs saved: {counts['invoices']}")
        st.write(f"WMS files saved: {counts['wms']}")

        st.markdown("### Fichiers enregistrés")
        for s in saved_all:
            size_mb = round(s.size_bytes / (1024 * 1024), 2) if s.size_bytes else 0
            st.write(f"- [{s.vault}] {s.original_name} ({size_mb} MB)")

        st.markdown("</div>", unsafe_allow_html=True)
