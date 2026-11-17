"""Les trois outils d'Olala 1.0 mini pour choisir une poutre : le catalogue en SQL, des calculs en Python, et les notes de projet.

Remplacez-les par les vôtres : il suffit d'une fonction Python et de sa description pour le modèle (voir TOOLS).
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

DB = Path(__file__).with_name("poutres.db")

# ---------------------------------------------------------------- notes de projet : ce que le client a décrit
NOTES = {
    "atelier-nord": "Projet Atelier Nord. Site en bord de mer, poutre à l'air libre, hors éclaboussures : usage marin_air. "
                    "Charge P = 10 kN au centre, poutre sur deux appuis, portée 4 m, gamma = 1,5, flèche limitée à L/300.",
    "hangar-sud": "Projet Hangar Sud. Local fermé et sec : usage interieur_sec. Charge P = 18 kN au centre, poutre sur deux "
                  "appuis, portée 5 m, gamma = 1,5, flèche limitée à L/250.",
    "atelier-est": "Projet Atelier Est. Structure sous abri, ouverte sur les côtés : usage exterieur_abrite. "
                   "Le dimensionnement n'est pas encore fixé.",
    "regles-chantier": "Règles de chantier : casque obligatoire, livraisons entre 7 h et 16 h, stockage des poutres à l'abri de la pluie.",
}


def search_notes(query: str) -> str:
    """Les deux notes qui partagent le plus de mots avec la recherche."""
    words = set(re.findall(r"\w{3,}", query.lower()))
    scored = sorted(((len(words & set(re.findall(r"\w{3,}", (k + " " + v).lower()))), k) for k, v in NOTES.items()), reverse=True)
    return json.dumps([{"note": k, "texte": NOTES[k]} for s, k in scored[:2] if s > 0], ensure_ascii=False)


# ---------------------------------------------------------------- catalogue, en lecture seule
def run_sql(query: str) -> str:
    if not DB.exists():
        raise RuntimeError("poutres.db manque : lancez d'abord python catalogue.py")
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        cur = con.execute(query)
        cols = [d[0] for d in cur.description or []]
        return json.dumps([dict(zip(cols, r)) for r in cur.fetchmany(60)], ensure_ascii=False)
    finally:
        con.close()


# ---------------------------------------------------------------- Python, dans un sous-processus isolé
def run_python(code: str, timeout: int = 15) -> str:
    """Exécute le script du modèle et renvoie ce qu'il imprime.

    Sur macOS, sandbox-exec coupe le réseau et interdit d'écrire hors d'un dossier temporaire. Ailleurs, le script
    tourne dans un dossier temporaire, sans variables d'environnement, avec un délai : c'est une précaution, pas une
    barrière de sécurité. Pour un usage réel, exécutez ce code dans un conteneur jetable.
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp = os.path.realpath(tmp)
        cmd = [sys.executable, "-I", "-c", code]
        if sys.platform == "darwin":
            profile = ('(version 1)(allow default)(deny network*)(deny file-write*)'
                       f'(allow file-write* (subpath "{tmp}"))(allow file-write* (literal "/dev/null"))'
                       f'(deny file-read* (subpath "{os.path.expanduser("~")}"))')
            cmd = ["sandbox-exec", "-p", profile, "/usr/bin/python3", "-I", "-c", code]
        try:
            p = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True, timeout=timeout,
                               env={"PATH": "/usr/bin:/bin", "HOME": tmp})
        except subprocess.TimeoutExpired:
            return "Erreur : délai dépassé"
        return (p.stdout + (("\nSTDERR:\n" + p.stderr) if p.returncode else ""))[:4000]


FUNCTIONS = {"search_notes": search_notes, "run_sql": run_sql, "run_python": run_python}


def _tool(name, description, param, param_description):
    return {"type": "function", "function": {"name": name, "description": description, "parameters": {
        "type": "object", "required": [param], "properties": {param: {"type": "string", "description": param_description}}}}}


TOOLS = {
    "search_notes": _tool("search_notes", "Cherche dans les notes de projet. Ce sont les seules sources sur les projets.",
                          "query", "mots à chercher, par exemple le nom du projet"),
    "run_sql": _tool("run_sql", "Exécute un SELECT sur la base SQLite du catalogue et renvoie les lignes en JSON.",
                     "query", "une requête SELECT"),
    "run_python": _tool("run_python", "Exécute un script Python 3 et renvoie sa sortie standard (utilise print).",
                        "code", "le script complet"),
}

INSTRUCTIONS = """Tu es un assistant d'ingénierie. Utilise un outil pour toute donnée et tout calcul, n'invente rien. \
Ne calcule jamais de tête, même une conversion d'unités : tout calcul passe par run_python, avec print, et ta réponse \
recopie la valeur imprimée. Réponds en français, en une ou deux phrases, avec les valeurs chiffrées et leur unité.

Schéma du catalogue :
poutres(id, designation, materiau, masse_kg_m, I_cm4, W_cm3, E_GPa, prix_eur_m, prix_statut)
usages(materiau, usage, autorise, f_d_MPa, coef_fleche, note)
  autorise = 1 si le matériau convient à cet usage. f_d_MPa : résistance de calcul pour cet usage. coef_fleche multiplie la flèche élastique.
materiaux(nom, alpha_1e6, E_GPa, limite_MPa, note)
  propriétés physiques génériques (dilatation, limite), avec ses propres noms ('Acier S235', 'PVC rigide'...) : ne la joins pas aux poutres.
Les matériaux autorisés pour un usage se lisent dans usages : SELECT materiau FROM usages WHERE usage = '...' AND autorise = 1.
Valeurs de materiau : 'S235 brut', 'S235 galvanise', 'Inox 316L', 'GL24h epicea', 'GL24h douglas ou meleze'.
Valeurs d'usage : 'interieur_sec', 'exterieur_abrite', 'exterieur_expose', 'marin_air', 'marin_eclaboussures'.
Pour l'usage, joins usages ON usages.materiau = poutres.materiau.
Poutre sur deux appuis, charge P au centre : contrainte = gamma*P*L/(4*W) <= f_d ; flèche = coef_fleche*P*L^3/(48*E*I), \
à comparer à la limite (P sans gamma). Travaille en N et en mm."""


def tools(*names: str) -> list[dict]:
    return [TOOLS[n] for n in names]
