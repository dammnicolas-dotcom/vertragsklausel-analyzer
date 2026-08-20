import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from schema import Klausel, Klauseltyp, Risikostufe, Vertragsanalyse


def test_klausel_ohne_risikobegruendung():
    klausel = Klausel(
        typ=Klauseltyp.LAUFZEIT,
        originaltext="Der Vertrag laeuft auf unbestimmte Zeit.",
        zusammenfassung="Unbefristeter Vertrag.",
        risikostufe=Risikostufe.KEIN,
    )
    assert klausel.risikobegruendung is None
    assert klausel.beleg_verifiziert is None


def test_vertragsanalyse_mit_mehreren_klauseln():
    analyse = Vertragsanalyse(
        klauseln=[
            Klausel(
                typ=Klauseltyp.HAFTUNG,
                originaltext="Der Auftragnehmer haftet unbegrenzt.",
                zusammenfassung="Unbegrenzte Haftung des Auftragnehmers.",
                risikostufe=Risikostufe.HOCH,
                risikobegruendung="Einseitig zulasten des Auftragnehmers, kein Haftungsausschluss ueblich.",
            )
        ],
        gesamteinschaetzung="Vertrag enthaelt eine risikobehaftete Klausel.",
    )
    assert len(analyse.klauseln) == 1
    assert analyse.klauseln[0].risikostufe == Risikostufe.HOCH
