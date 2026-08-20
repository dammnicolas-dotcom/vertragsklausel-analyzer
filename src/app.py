import os

import anthropic
import streamlit as st
from dotenv import load_dotenv

from analyzer import AnalyseFehler, MODEL_ID, analyze_contract

load_dotenv()

# Grobe Kostenschaetzung, nur fuer claude-opus-5 (Stand siehe README); bei
# anderem MODEL_ID wird keine Kostenschaetzung angezeigt, um keine falschen
# Zahlen zu suggerieren.
PREISE_PRO_1M_TOKEN = {"claude-opus-5": (5.0, 25.0)}

RISIKO_ANZEIGE = {
    "kein": ("⚪", "kein Risiko"),
    "niedrig": ("🟡", "niedriges Risiko"),
    "mittel": ("🟠", "mittleres Risiko"),
    "hoch": ("🔴", "hohes Risiko"),
}

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

with st.expander("Hinweis zu Datenschutz und Verarbeitung", expanded=False):
    st.markdown(
        "Der Vertragsinhalt wird zur Analyse an die Claude API (Anthropic) uebertragen. "
        "Lade keine echten Mandanten- oder Kundenvertraege mit personenbezogenen Daten hoch, "
        "ohne vorher zu pruefen, ob dies datenschutzrechtlich zulaessig ist (z.B. durch "
        "Schwaerzen/Anonymisieren sensibler Passagen). Dieses Tool speichert nichts dauerhaft "
        "und ist ein Prototyp, kein produktiv freigegebenes System."
    )

einverstanden = st.checkbox(
    "Ich bin berechtigt, diesen Vertrag zu verarbeiten und habe den Datenschutzhinweis gelesen."
)

tab_pdf, tab_text = st.tabs(["PDF hochladen", "Text einfuegen"])

pdf_bytes = None
contract_text = None

with tab_pdf:
    uploaded = st.file_uploader("Vertrag als PDF", type=["pdf"])
    if uploaded is not None:
        pdf_bytes = uploaded.read()

with tab_text:
    contract_text = st.text_area("Vertragstext", height=300, placeholder="Vertragstext hier einfuegen...")

analysieren_disabled = not einverstanden or not (pdf_bytes or contract_text)
if st.button("Analysieren", type="primary", disabled=analysieren_disabled):
    with st.spinner("Analysiere Vertrag..."):
        try:
            ergebnis = analyze_contract(client, text=contract_text or None, pdf_bytes=pdf_bytes)
        except AnalyseFehler as exc:
            st.error(str(exc))
        else:
            result = ergebnis.analyse

            usage_line = f"Tokens: {ergebnis.input_tokens} Input / {ergebnis.output_tokens} Output"
            preise = PREISE_PRO_1M_TOKEN.get(MODEL_ID)
            if preise:
                kosten = (ergebnis.input_tokens / 1_000_000 * preise[0]) + (
                    ergebnis.output_tokens / 1_000_000 * preise[1]
                )
                usage_line += f" (~${kosten:.4f})"
            st.caption(usage_line)

            st.subheader("Gesamteinschaetzung")
            st.write(result.gesamteinschaetzung)

            st.subheader(f"Gefundene Klauseln ({len(result.klauseln)})")
            for klausel in result.klauseln:
                icon, label = RISIKO_ANZEIGE[klausel.risikostufe.value]
                with st.expander(f"{icon} {klausel.typ.value} - {klausel.zusammenfassung}"):
                    st.markdown(f"**Risikostufe:** {label}")
                    st.markdown(f"**Originaltext:**\n> {klausel.originaltext}")
                    if klausel.beleg_verifiziert is True:
                        st.caption("✅ Zitat im Quelltext verifiziert")
                    elif klausel.beleg_verifiziert is False:
                        st.caption("⚠️ Zitat konnte NICHT im Quelltext gefunden werden - moeglicherweise vom Modell umformuliert")
                    else:
                        st.caption("ℹ️ Zitat-Verifikation bei PDF-Uploads nicht verfuegbar")
                    if klausel.risikostufe.value != "kein":
                        st.markdown(f"**Begruendung:** {klausel.risikobegruendung}")
