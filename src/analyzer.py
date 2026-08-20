"""Kernlogik: Vertragstext/-PDF an Claude schicken und strukturiert auswerten lassen."""
import base64
import os

import anthropic

from schema import Vertragsanalyse

MODEL_ID = os.environ.get("MODEL_ID", "claude-opus-5")

SYSTEM_PROMPT = """Du bist ein juristischer Assistent, der Vertragsklauseln analysiert.

Gehe den Vertrag systematisch durch und extrahiere jede relevante Klausel
(u.a. Kuendigungsfrist, Haftung, Gerichtsstand, Vertraulichkeit,
Zahlungsbedingungen, Laufzeit, Gewaehrleistung, Vertragsstrafe, Datenschutz).
Ordne jede Klausel genau einem Typ zu; nutze "Sonstiges" nur wenn wirklich
keine andere Kategorie passt.

Markiere eine Klausel als risikobehaftet, wenn sie:
- einseitig zulasten einer Partei formuliert ist,
- von markt- bzw. gesetzesueblichen Standards abweicht (z.B. ungewoehnlich
  lange Kuendigungsfristen, weitreichender Haftungsausschluss,
  ungewoehnlicher Gerichtsstand),
- vage oder auslegungsbeduerftig formuliert ist.

Zitiere bei jeder Klausel den Originaltext woertlich. Antworte ausschliesslich
auf Deutsch. Dies ist keine Rechtsberatung, sondern eine automatisierte
Vorpruefung."""


def _build_document_block(file_bytes: bytes, media_type: str) -> dict:
    data = base64.standard_b64encode(file_bytes).decode("utf-8")
    return {
        "type": "document",
        "source": {"type": "base64", "media_type": media_type, "data": data},
    }


def analyze_contract(
    client: anthropic.Anthropic,
    *,
    text: str | None = None,
    pdf_bytes: bytes | None = None,
) -> Vertragsanalyse:
    """Analysiert einen Vertrag (entweder als reiner Text oder als PDF-Bytes)."""
    if not text and not pdf_bytes:
        raise ValueError("Entweder text oder pdf_bytes muss angegeben werden.")

    content: list[dict] = []
    if pdf_bytes:
        content.append(_build_document_block(pdf_bytes, "application/pdf"))
        content.append({"type": "text", "text": "Analysiere die Klauseln in diesem Vertrag."})
    else:
        content.append({"type": "text", "text": f"Analysiere die Klauseln in diesem Vertrag:\n\n{text}"})

    response = client.messages.parse(
        model=MODEL_ID,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
        output_format=Vertragsanalyse,
    )
    return response.parsed_output
