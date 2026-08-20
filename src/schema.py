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


class Risikostufe(str, Enum):
    KEIN = "kein"
    NIEDRIG = "niedrig"
    MITTEL = "mittel"
    HOCH = "hoch"


class Klausel(BaseModel):
    typ: Klauseltyp
    originaltext: str = Field(description="Woertliches Zitat der Klausel aus dem Vertrag")
    zusammenfassung: str = Field(description="Kurze Zusammenfassung in einfacher Sprache")
    risikostufe: Risikostufe = Field(
        description="kein/niedrig: unauffaellig oder geringfuegig vom Standard abweichend. "
        "mittel: spuerbar einseitig oder ungewoehnlich. hoch: stark einseitig, ungewoehnlich "
        "riskant oder mit erheblichem finanziellem/rechtlichem Nachteil verbunden."
    )
    risikobegruendung: Optional[str] = Field(
        default=None, description="Falls risikostufe != kein: warum genau"
    )
    beleg_verifiziert: Optional[bool] = Field(
        default=None,
        description="Wird lokal nachtraeglich gesetzt (nicht vom Modell): True, wenn das "
        "Zitat im Quelltext gefunden wurde. None, wenn keine Verifikation moeglich war (PDF).",
    )


class Vertragsanalyse(BaseModel):
    klauseln: List[Klausel]
    gesamteinschaetzung: str = Field(description="Kurzes Gesamtfazit zum Vertrag (2-3 Saetze)")
