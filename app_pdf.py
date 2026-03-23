"""
Mini Acrobat — Gestionnaire de PDF local avec Streamlit
Lancement : streamlit run app_pdf.py
Dépendances : pip install streamlit pypdf pillow
"""

import io
import streamlit as st
from pypdf import PdfWriter, PdfReader

st.set_page_config(page_title="Mini Acrobat", page_icon="📄", layout="wide")
st.title("📄 Mini Acrobat — Gestionnaire de PDF")

# ── Session state ──────────────────────────────────────────────────────────────
if "pages" not in st.session_state:
    # Each entry: {"label": str, "reader": PdfReader, "page_index": int, "rotation": int}
    st.session_state.pages = []
if "keep" not in st.session_state:
    st.session_state.keep = []

# ── 1. UPLOAD ──────────────────────────────────────────────────────────────────
st.header("1 · Importer des fichiers PDF")
uploaded_files = st.file_uploader(
    "Glisser-déposer ou sélectionner plusieurs fichiers PDF",
    type="pdf",
    accept_multiple_files=True,
    key="uploader",
)

if st.button("📥 Charger les fichiers sélectionnés") and uploaded_files:
    st.session_state.pages = []
    for f in uploaded_files:
        reader = PdfReader(io.BytesIO(f.read()))
        for i in range(len(reader.pages)):
            st.session_state.pages.append(
                {
                    "label": f"{f.name} — p.{i + 1}",
                    "reader": reader,
                    "page_index": i,
                    "rotation": 0,
                }
            )
    st.session_state.keep = [True] * len(st.session_state.pages)
    st.success(f"{len(st.session_state.pages)} page(s) chargée(s).")

if not st.session_state.pages:
    st.info("Importez au moins un fichier PDF pour commencer.")
    st.stop()

pages = st.session_state.pages
keep = st.session_state.keep

# ── 2. ORGANISATION & FUSION / SUPPRESSION ────────────────────────────────────
st.header("2 · Organiser les pages")

col_order, col_table = st.columns([1, 2])

with col_order:
    st.subheader("Réordonner")
    st.caption("Entrez le nouvel ordre (numéros séparés par des virgules, base 1).")
    default_order = ", ".join(str(i + 1) for i in range(len(pages)))
    order_input = st.text_input("Nouvel ordre", value=default_order)
    if st.button("✅ Appliquer l'ordre"):
        try:
            new_order = [int(x.strip()) - 1 for x in order_input.split(",")]
            if sorted(new_order) != list(range(len(pages))):
                st.error("Chaque numéro de page doit apparaître exactement une fois.")
            else:
                st.session_state.pages = [pages[i] for i in new_order]
                st.session_state.keep = [keep[i] for i in new_order]
                st.rerun()
        except ValueError:
            st.error("Format invalide. Exemple : 3, 1, 2")

with col_table:
    st.subheader("Pages · cocher pour conserver")
    for idx, page in enumerate(pages):
        c1, c2, c3, c4 = st.columns([0.5, 3, 1.5, 1.5])
        with c1:
            keep[idx] = st.checkbox("", value=keep[idx], key=f"keep_{idx}")
        with c2:
            st.write(f"**{idx + 1}.** {page['label']}")
        with c3:
            rot_options = [0, 90, 180, 270]
            page["rotation"] = st.selectbox(
                "Rotation",
                options=rot_options,
                index=rot_options.index(page["rotation"]),
                key=f"rot_{idx}",
                label_visibility="collapsed",
            )
        with c4:
            st.caption(f"↻ {page['rotation']}°")

st.session_state.keep = keep

# ── 3. ROTATION GLOBALE ────────────────────────────────────────────────────────
st.header("3 · Rotation globale")
col_r1, col_r2, col_r3 = st.columns(3)
with col_r1:
    if st.button("↻ +90° (toutes)"):
        for p in st.session_state.pages:
            p["rotation"] = (p["rotation"] + 90) % 360
        st.rerun()
with col_r2:
    if st.button("↻ +180° (toutes)"):
        for p in st.session_state.pages:
            p["rotation"] = (p["rotation"] + 180) % 360
        st.rerun()
with col_r3:
    if st.button("↺ Remettre à 0° (toutes)"):
        for p in st.session_state.pages:
            p["rotation"] = 0
        st.rerun()

# ── 4. APERÇU RÉSUMÉ ───────────────────────────────────────────────────────────
selected_count = sum(keep)
st.info(
    f"**{selected_count}** page(s) sélectionnée(s) sur {len(pages)} seront incluses dans le PDF final."
)

# ── 5. TÉLÉCHARGEMENT ─────────────────────────────────────────────────────────
st.header("4 · Générer et télécharger")

if st.button("⚙️ Générer le PDF final", type="primary", disabled=selected_count == 0):
    writer = PdfWriter()
    for idx, page in enumerate(pages):
        if not keep[idx]:
            continue
        pdf_page = page["reader"].pages[page["page_index"]]
        if page["rotation"] != 0:
            pdf_page = pdf_page.rotate(page["rotation"])
        writer.add_page(pdf_page)

    buf = io.BytesIO()
    writer.write(buf)
    buf.seek(0)
    st.session_state["pdf_output"] = buf.read()
    st.success("PDF généré avec succès !")

if "pdf_output" in st.session_state:
    st.download_button(
        label="⬇️ Télécharger le PDF",
        data=st.session_state["pdf_output"],
        file_name="document_final.pdf",
        mime="application/pdf",
    )

# ── Réinitialisation ───────────────────────────────────────────────────────────
st.divider()
if st.button("🗑️ Réinitialiser tout"):
    for key in ["pages", "keep", "pdf_output"]:
        st.session_state.pop(key, None)
    st.rerun()
