"""Einfache Recall-Messung gegen ein kleines Golden-Set.

Kein automatisierter Teil der Test-Suite (kostet echte API-Calls) - manuell
ausfuehren mit:

    cd eval && python run_eval.py

Misst nur Recall der Klauseltypen (wurden die erwarteten Kategorien
gefunden?), keine Bewertung der Qualitaet von Zusammenfassung/Risikostufe -
das waere der naechste Ausbauschritt (z.B. LLM-as-judge oder manuelles
Review-Label pro Klausel).
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import anthropic
from dotenv import load_dotenv

from analyzer import analyze_contract

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY nicht gesetzt - eval abgebrochen.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    with open(os.path.join(os.path.dirname(__file__), "golden_set.json"), encoding="utf-8") as f:
        golden_set = json.load(f)

    recalls = []
    for fall in golden_set:
        with open(os.path.join(BASE_DIR, fall["datei"]), encoding="utf-8") as f:
            vertragstext = f.read()

        ergebnis = analyze_contract(client, text=vertragstext)
        gefunden = {k.typ.value for k in ergebnis.analyse.klauseln}
        erwartet = set(fall["erwartete_typen"])
        treffer = gefunden & erwartet
        fehlend = erwartet - gefunden
        recall = len(treffer) / len(erwartet) if erwartet else 1.0
        recalls.append(recall)

        print(f"\n{fall['name']}: Recall {recall:.0%} ({len(treffer)}/{len(erwartet)})")
        if fehlend:
            print(f"  Nicht gefunden: {sorted(fehlend)}")
        nicht_verifiziert = [k.typ.value for k in ergebnis.analyse.klauseln if k.beleg_verifiziert is False]
        if nicht_verifiziert:
            print(f"  Zitate ohne Beleg im Quelltext: {nicht_verifiziert}")

    print(f"\nDurchschnittlicher Recall: {sum(recalls) / len(recalls):.0%}")


if __name__ == "__main__":
    main()
