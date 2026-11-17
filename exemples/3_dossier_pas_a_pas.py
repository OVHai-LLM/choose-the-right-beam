"""Le dossier complet, mené pas à pas : Olala 1.0 mini lit et interroge, le code vérifie chaque étape.

1. Olala mini lit la note du projet et en extrait les données (usage, charge, portée, gamma, limite de flèche).
   Le code contrôle que chaque valeur figure bien dans la note, sinon il la fait relire.
2. Olala mini écrit la requête SQL des poutres autorisées pour cet usage, de la moins chère à la plus chère.
   Le code l'exécute en lecture seule et contrôle les lignes (usage, autorisation, tri), sinon il la fait corriger.
3. Le code vérifie chaque poutre (contrainte et flèche) et garde la première qui tient.

Découper ainsi est ce qui rend le résultat fiable : chaque étape est courte, le modèle fait ce qu'il fait bien (lire,
écrire du SQL) et le code contrôle ce qu'il renvoie avant de passer à la suivante.

    python exemples/3_dossier_pas_a_pas.py
    python exemples/3_dossier_pas_a_pas.py "Hangar Sud"
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from olala import run  # noqa: E402
from outils import FUNCTIONS, INSTRUCTIONS, run_sql, search_notes, tools  # noqa: E402

PROJET = " ".join(sys.argv[1:]) or "Atelier Nord"
CHAMPS = ("usage", "P_kN", "L_m", "gamma", "limite_div")


def json_dans(texte: str):
    """Le premier objet ou tableau JSON d'une réponse, même s'il est suivi d'autre texte."""
    for i, c in enumerate(texte):
        if c in "[{":
            try:
                return json.JSONDecoder().raw_decode(texte[i:])[0]
            except json.JSONDecodeError:
                continue
    return None


def nombres(texte: str) -> set[float]:
    return {float(n.replace(",", ".")) for n in re.findall(r"\d+(?:[.,]\d+)?", texte)}


# 1. La note du projet --------------------------------------------------------------------------
print(f"Projet : {PROJET}\n\n1. Lire la note")
note = json.loads(search_notes(PROJET))
if not note:
    sys.exit(f"Aucune note pour le projet {PROJET}.")
texte = note[0]["texte"]
demande = (f"Cherche la note du projet {PROJET} avec search_notes. Réponds uniquement par un objet JSON avec les clés "
           "usage (texte), P_kN, L_m, gamma et limite_div (nombres ; si la flèche est limitée à L/N, limite_div vaut N).")
projet = None
for essai in range(2):
    reponse = run(demande, tools("search_notes"), FUNCTIONS, system=INSTRUCTIONS)
    lu = json_dans(reponse)
    if not isinstance(lu, dict) or any(k not in lu for k in CHAMPS):
        probleme = "ta réponse ne contient pas toutes les clés demandées"
    else:
        # Le code vérifie que chaque valeur vient bien de la note, pas d'ailleurs.
        faux = [k for k in CHAMPS[1:] if not isinstance(lu[k], (int, float)) or float(lu[k]) not in nombres(texte)]
        faux += [] if str(lu["usage"]) in texte else ["usage"]
        if not faux:
            projet = lu
            break
        probleme = f"ces valeurs ne figurent pas dans la note : {', '.join(faux)} ; recopie-les telles qu'elles y sont écrites"
    print(f"    contrôle : {probleme} ; nouvelle demande")
    demande += f"\n\nAttention, à l'essai précédent {probleme}."
if projet is None:
    sys.exit("Les données du projet n'ont pas pu être lues correctement.")
print("   ", projet)

# 2. Les poutres autorisées ---------------------------------------------------------------------
print("\n2. Interroger le catalogue")
demande = (f"Écris une requête SQLite qui liste les poutres autorisées pour l'usage {projet['usage']} : designation, materiau, "
           "prix_eur_m, W_cm3, I_cm4, E_GPa, f_d_MPa, coef_fleche, ainsi que usages.usage et usages.autorise, triées par "
           "prix croissant. Réponds uniquement par la requête, sans explication.")
poutres = None
for essai in range(2):
    reponse = run(demande, system=INSTRUCTIONS, verbose=False)
    m = re.search(r"(SELECT\b.*?)(?:;|```|$)", reponse, re.S | re.I)
    sql = m.group(1).strip() if m else ""
    print(f"    requête : {' '.join(sql.split())[:160]}")
    try:
        lignes = json.loads(run_sql(sql)) if sql else []  # le code exécute la requête, en lecture seule
    except Exception as e:
        lignes, probleme = None, f"la requête a échoué : {e}"
    else:
        if not lignes:
            probleme = "la requête ne renvoie aucune ligne"
        elif any(k not in lignes[0] for k in ("prix_eur_m", "W_cm3", "I_cm4", "E_GPa", "f_d_MPa", "coef_fleche", "usage", "autorise")):
            probleme = "il manque des colonnes demandées"
        elif any(r["usage"] != projet["usage"] or r["autorise"] != 1 for r in lignes):
            probleme = (f"des lignes ne sont pas pour l'usage {projet['usage']} avec autorise = 1 ; "
                        f"filtre avec WHERE usages.usage = '{projet['usage']}' AND usages.autorise = 1")
        elif any(x["prix_eur_m"] > y["prix_eur_m"] for x, y in zip(lignes, lignes[1:])):
            probleme = "les lignes ne sont pas triées par prix croissant"
        else:
            poutres = lignes
            break
    print(f"    contrôle : {probleme} ; nouvelle demande")
    demande += f"\n\nAttention, à l'essai précédent {probleme}."
if poutres is None:
    sys.exit("Le catalogue n'a pas pu être interrogé correctement.")
print(f"    {len(poutres)} poutres autorisées pour {projet['usage']}, de {poutres[0]['prix_eur_m']} à {poutres[-1]['prix_eur_m']} €/m")

# 3. La vérification, par le code ---------------------------------------------------------------
print("\n3. Vérifier chaque poutre (code)")
P, L = projet["P_kN"] * 1e3, projet["L_m"] * 1e3  # N, mm
for b in poutres:
    contrainte = projet["gamma"] * P * L / (4 * b["W_cm3"] * 1e3)  # MPa
    fleche = b["coef_fleche"] * P * L**3 / (48 * b["E_GPa"] * 1e3 * b["I_cm4"] * 1e4)  # mm
    ok = contrainte <= b["f_d_MPa"] and fleche <= L / projet["limite_div"]
    print(f"    {b['designation']:>8} {b['materiau']:<24} {b['prix_eur_m']:>7.2f} €/m  "
          f"contrainte {contrainte:6.1f}/{b['f_d_MPa']} MPa  flèche {fleche:5.1f}/{L / projet['limite_div']:.1f} mm  "
          f"{'tient' if ok else 'non'}")
    if ok:
        print(f"\n= {b['designation']} en {b['materiau']}, {b['prix_eur_m']:.2f} € le mètre, "
              f"soit {b['prix_eur_m'] * projet['L_m']:.2f} € pour {projet['L_m']} m.")
        break
else:
    print("\n= Aucune poutre du catalogue ne tient pour ce projet.")
