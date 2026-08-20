import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from analyzer import _quote_in_source, _verify_grounding, _normalize
from schema import Klausel, Klauseltyp, Risikostufe, Vertragsanalyse

SOURCE = """
§ 3 Haftung
Der Auftragnehmer haftet fuer alle Schaeden, gleich welcher Art, unbegrenzt,
auch fuer leichte Fahrlaessigkeit.
"""


def test_exakte_uebereinstimmung_wird_erkannt():
    quote = "Der Auftragnehmer haftet fuer alle Schaeden, gleich welcher Art, unbegrenzt,"
    assert _quote_in_source(quote, _normalize(SOURCE))


def test_leicht_abweichende_formatierung_wird_noch_erkannt():
    quote = "Der Auftragnehmer haftet fuer alle Schaeden, gleich welcher Art,\nunbegrenzt"
    assert _quote_in_source(quote, _normalize(SOURCE))


def test_frei_erfundenes_zitat_wird_nicht_erkannt():
    quote = "Der Auftraggeber zahlt eine jaehrliche Praemie von 10000 EUR."
    assert not _quote_in_source(quote, _normalize(SOURCE))


def test_verify_grounding_setzt_flag_pro_klausel():
    analyse = Vertragsanalyse(
        klauseln=[
            Klausel(
                typ=Klauseltyp.HAFTUNG,
                originaltext="Der Auftragnehmer haftet fuer alle Schaeden, gleich welcher Art, unbegrenzt,",
                zusammenfassung="Unbegrenzte Haftung.",
                risikostufe=Risikostufe.HOCH,
                risikobegruendung="Einseitig.",
            ),
            Klausel(
                typ=Klauseltyp.SONSTIGES,
                originaltext="Dieser Satz steht so nicht im Vertrag.",
                zusammenfassung="Halluziniert.",
                risikostufe=Risikostufe.KEIN,
            ),
        ],
        gesamteinschaetzung="Test.",
    )

    _verify_grounding(analyse, SOURCE)

    assert analyse.klauseln[0].beleg_verifiziert is True
    assert analyse.klauseln[1].beleg_verifiziert is False
