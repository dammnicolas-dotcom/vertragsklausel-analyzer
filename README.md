# Vertragsklausel-Analyzer

LLM-gestuetztes Tool zur Vorpruefung von Vertraegen: extrahiert und klassifiziert
Klauseln (Kuendigungsfrist, Haftung, Gerichtsstand, Vertraulichkeit,
Zahlungsbedingungen, Laufzeit, Gewaehrleistung, Vertragsstrafe, Datenschutz)
und flaggt ungewoehnliche oder einseitige Formulierungen. Nutzt die Claude API
mit strukturierter JSON-Ausgabe (Pydantic-Schema).

**Kein Ersatz fuer Rechtsberatung** - reine automatisierte Vorpruefung.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# ANTHROPIC_API_KEY in .env eintragen
```

## Starten

```bash
cd src
streamlit run app.py
```

Vertrag entweder als PDF hochladen (native PDF-Verarbeitung ueber die Claude API,
keine lokale Textextraktion noetig) oder Text direkt einfuegen.

## Architektur

- `src/schema.py` - Pydantic-Schema fuer die strukturierte Ausgabe (Klauseltyp,
  Originalzitat, Zusammenfassung, Risikoflag samt Begruendung).
- `src/analyzer.py` - Baut den Prompt, schickt Vertrag (Text oder PDF-Dokument-Block)
  an Claude, nutzt `client.messages.parse(..., output_format=Vertragsanalyse)` fuer
  garantiert valides JSON statt String-Parsing.
- `src/app.py` - Streamlit-UI (Upload/Text-Eingabe, Ergebnisanzeige).
- Modell: `claude-opus-5` (per `.env` ueber `MODEL_ID` austauschbar, z.B. auf
  `claude-sonnet-5` fuer geringere Kosten bei hoeherem Volumen).

## Tests

```bash
pip install pytest
pytest tests/
```

`tests/` prueft aktuell nur das Pydantic-Schema (ohne API-Calls). Ein Beispielvertrag
liegt unter `examples/beispiel_vertrag.txt` zum manuellen Testen der Analyse.
