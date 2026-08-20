import os

import anthropic
import streamlit as st
from dotenv import load_dotenv

from analyzer import analyze_contract

load_dotenv()

st.set_page_config(page_title="Vertragsklausel-Analyzer", page_icon="\U0001F4C4")
st.title("Vertragsklausel-Analyzer")
st.caption(
    "LLM-gestuetzte Vorpruefung von Vertragsklauseln (Kuendigungsfrist, Haftung, "
    "Gerichtsstand u.a.). Ersetzt keine Rechtsberatung."
)

api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    st.warning("ANTHROPIC_API_KEY ist nicht gesetzt. Bitte in .env eintragen.")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

tab_pdf, tab_text = st.tabs(["PDF hochladen", "Text einfuegen"])

pdf_bytes = None
contract_text = None

with tab_pdf:
    uploaded = st.file_uploader("Vertrag als PDF", type=["pdf"])
    if uploaded is not None:
        pdf_bytes = uploaded.read()

with tab_text:
    contract_text = st.text_area("Vertragstext", height=300, placeholder="Vertragstext hier einfuegen...")

if st.button("Analysieren", type="primary", disabled=not (pdf_bytes or contract_text)):
    with st.spinner("Analysiere Vertrag..."):
        try:
            result = analyze_contract(client, text=contract_text or None, pdf_bytes=pdf_bytes)
        except Exception as exc:  # noqa: BLE001 - zeige Fehler direkt im UI
            st.error(f"Analyse fehlgeschlagen: {exc}")
        else:
            st.subheader("Gesamteinschaetzung")
            st.write(result.gesamteinschaetzung)

            st.subheader(f"Gefundene Klauseln ({len(result.klauseln)})")
            for klausel in result.klauseln:
                icon = "⚠️" if klausel.risikobehaftet else "✅"
                with st.expander(f"{icon} {klausel.typ.value} - {klausel.zusammenfassung}"):
                    st.markdown(f"**Originaltext:**\n> {klausel.originaltext}")
                    if klausel.risikobehaftet:
                        st.markdown(f"**Risiko:** {klausel.risikobegruendung}")
