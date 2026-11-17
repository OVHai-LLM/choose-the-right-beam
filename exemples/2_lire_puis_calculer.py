"""Deux outils à la suite : lire les caractéristiques d'une poutre dans le catalogue, puis calculer sa flèche.

    python exemples/2_lire_puis_calculer.py
    python exemples/2_lire_puis_calculer.py "Lis l'IPE 160 en S235 galvanise, puis calcule sa flèche pour P = 12 kN sur 4,5 m."
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from olala import run  # noqa: E402
from outils import FUNCTIONS, INSTRUCTIONS, tools  # noqa: E402

QUESTIONS = sys.argv[1:] or [
    "Lis dans la base l'IPE 140 en S235 brut, puis calcule sa flèche en mm pour P = 10 kN au centre, "
    "sur deux appuis, portée 4 m, sans coef_fleche.",
    "Quelle est la flèche admissible en mm du projet Hangar Sud ? Lis sa note, puis calcule-la avec run_python.",
]

for q in QUESTIONS:
    print(f"\n? {q}")
    print("=", run(q, tools("search_notes", "run_sql", "run_python"), FUNCTIONS, system=INSTRUCTIONS))
