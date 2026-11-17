"""Une question, un outil : lire le catalogue en SQL, ou faire un calcul en Python.

    python exemples/1_questions_simples.py
    python exemples/1_questions_simples.py "Quel est le prix au mètre de l'IPE 180 en S235 galvanise ?"
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from olala import run  # noqa: E402
from outils import FUNCTIONS, INSTRUCTIONS, tools  # noqa: E402

QUESTIONS = sys.argv[1:] or [
    "Quel est le prix au mètre de l'IPE 140 en S235 brut ?",
    "Quels matériaux sont autorisés pour l'usage marin_air ?",
    "Quelle est l'inertie I, en cm4, de l'IPE 200 en S235 galvanise ?",
    "Avec run_python, calcule la flèche en mm d'une poutre sur deux appuis : P = 10 kN au centre, portée 4 m, "
    "E = 210 GPa, I = 541 cm4.",
    "Acier : alpha = 12e-6 /°C. De combien grandit une tour de 300 m pour 30 °C de plus ?",
]

for q in QUESTIONS:
    print(f"\n? {q}")
    print("=", run(q, tools("run_sql", "run_python"), FUNCTIONS, system=INSTRUCTIONS))
