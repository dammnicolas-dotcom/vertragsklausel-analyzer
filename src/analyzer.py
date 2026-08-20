"""Kernlogik: Vertragstext/-PDF an Claude schicken und strukturiert auswerten lassen."""
import base64
import difflib
import os
import re
from dataclasses import dataclass

import anthropic

from schema import Vertragsanalyse

MODEL_ID = os.environ.get("MODEL_ID", "claude-opus-5")

# Harte Grenze der Claude API fuer PDF-Dokumente (Messages API, base64).
MAX_PDF_BYTES = 32 * 1024 * 1024

# Ab welcher Uebereinstimmung (0-1) ein Zitat als im Quelltext vorhanden gilt.
GROUNDING_MATCH_THRESHOLD = 0.85

SYSTEM_PROMPT = """Du bist ein juristischer Assistent, der Vertragsklauseln analysiert.

Gehe den Vertrag systematisch durch und extrahiere jede relevante Klausel
(u.a. Kuendigungsfrist, Haftung, Gerichtsstand, Vertraulichkeit,
Zahlungsbedingungen, Laufzeit, Gewaehrleistung, Vertragsstrafe, Datenschutz).
Ordne jede Klausel genau einem Typ zu; nutze "Sonstiges" nur wenn wirklich
keine andere Kategorie passt.

Vergib eine Risikostufe (kein/niedrig/mittel/hoch) danach, wie stark eine
Klausel:
- einseitig zulasten einer Partei formuliert ist,
- von markt- bzw. gesetzesueblichen Standards abweicht (z.B. ungewoehnlich
  lange Kuendigungsfristen, weitreichender Haftungsausschluss,
  ungewoehnlicher Gerichtsstand, unverhaeltnismaessige Vertragsstrafen),
- vage oder auslegungsbeduerftig formuliert ist.

Zitiere bei jeder Klausel den Originaltext woertlich und moeglichst
unveraendert aus dem Vertrag (keine Paraphrase) - das Zitat wird
anschliessend automatisch gegen den Quelltext geprueft. Antworte
ausschliesslich auf Deutsch. Dies ist keine Rechtsberatung, sondern eine
automatisierte Vorpruefung."""


class AnalyseFehler(Exception):
    """Nutzerfreundlicher Fehler, der API-Fehler in eine verstaendliche Meldung uebersetzt."""


@dataclass
class AnalyseErgebnis:
    analyse: Vertragsanalyse
    input_tokens: int
    output_tokens: int


def _build_document_block(file_bytes: bytes, media_type: str) -> dict:
    data = base64.standard_b64encode(file_bytes).decode("utf-8")
    return {
        "type": "document",
        "source": {"type": "base64", "media_type": media_type, "data": data},
    }


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _quote_in_source(quote: str, source_norm: str) -> bool:
    """Prueft lokal (ohne API-Call), ob ein Zitat im Quelltext vorkommt.

    Exaktes Substring-Matching schlaegt schon bei kleinsten Abweichungen
    (Zeilenumbrueche, Anfuehrungszeichen) fehl, deshalb zusaetzlich ein
    Fuzzy-Fallback ueber den laengsten gemeinsamen Block.
    """
    quote_norm = _normalize(quote)
    if not quote_norm:
        return False
    if quote_norm in source_norm:
        return True

    matcher = difflib.SequenceMatcher(None, source_norm, quote_norm)
    match = matcher.find_longest_match(0, len(source_norm), 0, len(quote_norm))
    return (match.size / len(quote_norm)) >= GROUNDING_MATCH_THRESHOLD


def _verify_grounding(analyse: Vertragsanalyse, source_text: str) -> None:
    """Setzt beleg_verifiziert je Klausel anhand eines lokalen Textabgleichs.

    Nur fuer Text-Input moeglich - bei PDFs bleibt das Feld None, weil eine
    Verifikation eine eigene lokale PDF-Textextraktion erfordern wuerde
    (bewusst nicht eingebaut, siehe README: native PDF-Verarbeitung ueber
    die Claude API statt lokaler Extraktion).
    """
    source_norm = _normalize(source_text)
    for klausel in analyse.klauseln:
        klausel.beleg_verifiziert = _quote_in_source(klausel.originaltext, source_norm)


def analyze_contract(
    client: anthropic.Anthropic,
    *,
    text: str | None = None,
    pdf_bytes: bytes | None = None,
) -> AnalyseErgebnis:
    """Analysiert einen Vertrag (entweder als reiner Text oder als PDF-Bytes)."""
    if not text and not pdf_bytes:
        raise ValueError("Entweder text oder pdf_bytes muss angegeben werden.")
    if pdf_bytes and len(pdf_bytes) > MAX_PDF_BYTES:
        raise AnalyseFehler(
            f"PDF ist zu gross ({len(pdf_bytes) / 1_048_576:.1f} MB). "
            f"Die Claude API akzeptiert maximal {MAX_PDF_BYTES / 1_048_576:.0f} MB pro Dokument."
        )

    content: list[dict] = []
    if pdf_bytes:
        content.append(_build_document_block(pdf_bytes, "application/pdf"))
        content.append({"type": "text", "text": "Analysiere die Klauseln in diesem Vertrag."})
    else:
        content.append({"type": "text", "text": f"Analysiere die Klauseln in diesem Vertrag:\n\n{text}"})

    try:
        response = client.messages.parse(
            model=MODEL_ID,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": content}],
            output_format=Vertragsanalyse,
        )
    except anthropic.BadRequestError as exc:
        raise AnalyseFehler(f"Ungueltige Anfrage an die Claude API: {exc.message}") from exc
    except anthropic.AuthenticationError as exc:
        raise AnalyseFehler("Der ANTHROPIC_API_KEY ist ungueltig oder abgelaufen.") from exc
    except anthropic.RateLimitError as exc:
        raise AnalyseFehler("Rate-Limit der Claude API erreicht. Bitte kurz warten und erneut versuchen.") from exc
    except anthropic.APIStatusError as exc:
        raise AnalyseFehler(f"Claude API Fehler ({exc.status_code}): {exc.message}") from exc
    except anthropic.APIConnectionError as exc:
        raise AnalyseFehler("Keine Verbindung zur Claude API moeglich. Internetverbindung pruefen.") from exc

    analyse = response.parsed_output
    if text:
        _verify_grounding(analyse, text)

    return AnalyseErgebnis(
        analyse=analyse,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )
