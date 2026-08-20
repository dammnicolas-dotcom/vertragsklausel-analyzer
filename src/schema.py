"""Pydantic-Schema fuer die strukturierte Klauselanalyse."""
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Klauseltyp(str, Enum):
    KUENDIGUNGSFRIST = "Kuendigungsfrist"
    HAFTUNG = "Haftung"
    GERICHTSSTAND = "Gerichtsstand"
    VERTRAULICHKEIT = "Vertraulichkeit"
    ZAHLUNGSBEDINGUNGEN = "Zahlungsbedingungen"
    LAUFZEIT = "Laufzeit"
    GEWAEHRLEISTUNG = "Gewaehrleistung"
    VERTRAGSSTRAFE = "Vertragsstrafe"
    DATENSCHUTZ = "Datenschutz"
    SONSTIGES = "Sonstiges"


class Klausel(BaseModel):
    typ: Klauseltyp
    originaltext: str = Field(description="Woertliches Zitat der Klausel aus dem Vertrag")
    zusammenfassung: str = Field(description="Kurze Zusammenfassung in einfacher Sprache")
    risikobehaftet: bool = Field(description="True, wenn die Formulierung ungewoehnlich, einseitig oder riskant ist")
    risikobegruendung: Optional[str] = Field(
        default=None, description="Falls risikobehaftet: warum genau"
    )


class Vertragsanalyse(BaseModel):
    klauseln: List[Klausel]
    gesamteinschaetzung: str = Field(description="Kurzes Gesamtfazit zum Vertrag (2-3 Saetze)")
