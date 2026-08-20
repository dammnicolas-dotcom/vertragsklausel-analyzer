# Vertragsklausel-Analyzer

LLM-gestuetztes Tool zur Vorpruefung von Vertraegen: extrahiert und klassifiziert
Klauseln (Kuendigungsfrist, Haftung, Gerichtsstand, Vertraulichkeit,
Zahlungsbedingungen, Laufzeit, Gewaehrleistung, Vertragsstrafe, Datenschutz),
vergibt eine Risikostufe (kein/niedrig/mittel/hoch) und prueft lokal, ob das
zitierte Original tatsaechlich im Vertrag steht. Nutzt die Claude API mit
strukturierter JSON-Ausgabe (Pydantic-Schema).

**Kein Ersatz fuer Rechtsberatung** - reine automatisierte Vorpruefung. Siehe
auch den Datenschutz-Hinweis in der App, bevor echte Vertragsdaten hochgeladen
werden.

Lizenz: [MIT](LICENSE)

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
  Originalzitat, Zusammenfassung, Risikostufe samt Begruendung,
  `beleg_verifiziert`).
- `src/analyzer.py` - Baut den Prompt, schickt Vertrag (Text oder PDF-Dokument-Block)
  an Claude, nutzt `client.messages.parse(..., output_format=Vertragsanalyse)` fuer
  garantiert valides JSON statt String-Parsing. Uebersetzt SDK-Fehler
  (`RateLimitError`, `AuthenticationError`, ...) in verstaendliche Meldungen
  (`AnalyseFehler`) statt eines pauschalen `except Exception`.
- `src/app.py` - Streamlit-UI (Upload/Text-Eingabe, Datenschutz-Checkbox vor der
  Analyse, Ergebnisanzeige mit Risikostufen-Badges, Token-Nutzung/Kostenschaetzung).
- Modell: `claude-opus-5` (per `.env` ueber `MODEL_ID` austauschbar, z.B. auf
  `claude-sonnet-5` fuer geringere Kosten bei hoeherem Volumen).

### Grounding-Check (Zitat-Verifikation)

Damit "Originaltext"-Zitate nicht vom Modell halluziniert/umformuliert werden,
prueft `analyzer._verify_grounding` bei Text-Input lokal (kein zusaetzlicher
API-Call, reines String-Matching mit Fuzzy-Fallback via `difflib`), ob jedes
Zitat tatsaechlich im eingegebenen Text vorkommt, und setzt
`Klausel.beleg_verifiziert`.

**Bewusste Einschraenkung:** Bei PDF-Uploads bleibt `beleg_verifiziert` auf
`None`, weil eine Verifikation eine eigene lokale PDF-Textextraktion
erfordern wuerde - das widerspraeche der Design-Entscheidung, PDFs nativ
ueber die Claude API zu verarbeiten statt eine zusaetzliche Extraction-Library
einzubinden. Ausbaustufe waere die Nutzung der Claude Citations API
(`citations: {enabled: true}` auf dem Dokument-Block); das ist aktuell aber
inkompatibel mit strukturierten Outputs (`output_config.format`) und wuerde
eine zweistufige Pipeline (erst Grounding-Pass mit Citations, dann
Struktur-Pass) erfordern.

## Bekannte Einschraenkungen

- Sehr lange Vertraege (> 32 MB als PDF) werden mit einer klaren Fehlermeldung
  abgelehnt statt automatisch in Abschnitte zerlegt zu werden (kein Chunking).
- Keine Historie/Persistenz - jede Analyse ist zustandslos, nichts wird
  gespeichert.
- Risikostufen sind eine Heuristik des Modells, keine juristische Bewertung.
- Kostenschaetzung in der UI gilt nur fuer `claude-opus-5` (Default-Modell).

## Tests

```bash
pip install pytest
pytest tests/
```

`tests/` prueft das Pydantic-Schema und die lokale Grounding-Logik (ohne
API-Calls, laeuft offline/kostenlos).

## Evaluierung (Recall gegen Golden-Set)

```bash
cd eval
python run_eval.py
```

Nicht Teil der automatisierten Test-Suite, da echte API-Calls (Kosten,
Netzwerk) noetig sind. Misst, wie viele der erwarteten Klauseltypen in
`eval/golden_set.json` tatsaechlich gefunden werden (Recall), und meldet
Zitate ohne Beleg im Quelltext. Deckt bewusst nur zwei kleine Beispielvertraege
ab (`examples/beispiel_vertrag.txt`, `examples/beispiel_vertrag_2.txt`) -
naechster Ausbauschritt waere ein groesseres Set plus Qualitaetsbewertung der
Zusammenfassungen (z.B. LLM-as-judge).
