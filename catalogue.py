"""Le catalogue fictif de la démonstration : poutres en acier et en bois, leurs prix, et les usages autorisés.

Prix publics HT 2026 en ordre de grandeur, inox non vérifié (voir prix_statut). Hypothèses : appuis simples,
charge au centre, sans poids propre, gamma = 1,5 en résistance, flèche sous charge de service, charge traitée
comme permanente pour le fluage du bois. C'est un catalogue de démonstration, pas une base de calcul réglementaire.

    python catalogue.py        # écrit poutres.db à côté de ce fichier
"""
import os
import sqlite3
import sys

PROFILS = {  # designation : masse kg/m, Iy cm4, Wy cm3
    "IPE 100": (8.1, 171, 34.2), "IPE 120": (10.4, 318, 53.0), "IPE 140": (12.9, 541, 77.3),
    "IPE 160": (15.8, 869, 109), "IPE 180": (18.8, 1317, 146), "IPE 200": (22.4, 1943, 194),
    "HEA 100": (16.7, 349, 72.8), "HEA 120": (19.9, 606, 106),
}
ACIERS = {  # materiau : EUR/kg HT, E GPa, statut du prix
    "S235 brut": (2.2, 210, "releve 2026, peinture non comptee"),
    "S235 galvanise": (4.2, 210, "2,2 + 2,0 de galvanisation ; fourchette 2,8 a 4,2"),
    "Inox 316L": (9.0, 200, "NON VERIFIE, sur devis"),
}
BOIS = [(80, 160), (100, 200), (100, 240), (120, 240), (100, 280), (120, 280), (120, 320), (140, 320)]
BOIS_MAT = {  # materiau : EUR/m3 HT, statut
    "GL24h epicea": (1300, "milieu de 1000 a 1600 EUR/m3 HT, 2026"),
    "GL24h douglas ou meleze": (1600, "HYPOTHESE, haut de fourchette"),
}
INT, ABR, EXP, AIR, ECL = ("interieur_sec", "exterieur_abrite", "exterieur_expose",
                           "marin_air", "marin_eclaboussures")
USAGES = [  # materiau, usage, autorise, f_d MPa, coef fleche (fluage), note
    ("S235 brut", INT, 1, 235, 1.0, "peinture non comptee"),
    ("S235 brut", ABR, 0, 235, 1.0, "corrosion"),
    ("S235 brut", EXP, 0, 235, 1.0, "corrosion"),
    ("S235 brut", AIR, 0, 235, 1.0, "corrosion"),
    ("S235 brut", ECL, 0, 235, 1.0, "corrosion"),
    ("S235 galvanise", INT, 1, 235, 1.0, ""),
    ("S235 galvanise", ABR, 1, 235, 1.0, ""),
    ("S235 galvanise", EXP, 1, 235, 1.0, ""),
    ("S235 galvanise", AIR, 1, 235, 1.0, "C5 : zinc 2,2 a 4,4 um/an, 70 um sur l'ame, 16 a 32 ans ; duplex pour aller au-dela"),
    ("S235 galvanise", ECL, 0, 235, 1.0, "50 a 100 um/an cites ; duplex minimum, non chiffre ici"),
    ("Inox 316L", INT, 1, 220, 1.0, ""),
    ("Inox 316L", ABR, 1, 220, 1.0, ""),
    ("Inox 316L", EXP, 1, 220, 1.0, ""),
    ("Inox 316L", AIR, 1, 220, 1.0, "taches possibles sans rincage"),
    ("Inox 316L", ECL, 1, 220, 1.0, "minimum en bord de mer ; risque de crevasse, entretien a prevoir"),
    ("GL24h epicea", INT, 1, 15.4, 1.6, "EC5 classe 1 : kmod 0,8, kdef 0,6"),
    ("GL24h epicea", ABR, 1, 15.4, 1.8, "EC5 classe 2 : kmod 0,8, kdef 0,8"),
    ("GL24h epicea", EXP, 0, 12.5, 3.0, "epicea reserve a l'interieur ou a l'abri"),
    ("GL24h epicea", AIR, 0, 12.5, 3.0, "epicea reserve a l'interieur ou a l'abri"),
    ("GL24h epicea", ECL, 0, 12.5, 3.0, "epicea reserve a l'interieur ou a l'abri"),
    ("GL24h douglas ou meleze", INT, 1, 15.4, 1.6, ""),
    ("GL24h douglas ou meleze", ABR, 1, 15.4, 1.8, ""),
    ("GL24h douglas ou meleze", EXP, 1, 12.5, 3.0, "EC5 classe 3 : kmod 0,65, kdef 2,0"),
    ("GL24h douglas ou meleze", AIR, 0, 12.5, 3.0, "hors du perimetre de cette demonstration"),
    ("GL24h douglas ou meleze", ECL, 0, 12.5, 3.0, "hors du perimetre de cette demonstration"),
]
MATERIAUX = [  # nom, alpha 1e-6/K, E GPa, limite MPa (traction), note
    ("Acier S235", 12, 210, 235, "limite elastique"),
    ("Inox 316L", 16, 200, 220, "limite elastique"),
    ("Aluminium 6060-T6", 23, 70, 140, "limite elastique"),
    ("Bois GL24h (fil)", 4, 11.5, 19.2, "traction caracteristique, ordre de grandeur"),
    ("Beton C25/30", 10, 31, 2.6, "traction moyenne : c'est le beton qui fissure"),
    ("PVC rigide", 70, 3, 55, "alpha 60 a 80, limite d'ecoulement 55 a 58 selon fiches"),
]


def build(path):
    if os.path.exists(path):
        os.remove(path)
    c = sqlite3.connect(path)
    c.executescript("""
      CREATE TABLE poutres(id INTEGER PRIMARY KEY, designation TEXT, materiau TEXT,
        masse_kg_m REAL, I_cm4 REAL, W_cm3 REAL, E_GPa REAL, prix_eur_m REAL, prix_statut TEXT);
      CREATE TABLE usages(materiau TEXT, usage TEXT, autorise INT, f_d_MPa REAL,
        coef_fleche REAL, note TEXT);
      CREATE TABLE materiaux(nom TEXT, alpha_1e6 REAL, E_GPa REAL, limite_MPa REAL, note TEXT);
    """)
    sql = ("INSERT INTO poutres(designation,materiau,masse_kg_m,I_cm4,W_cm3,E_GPa,prix_eur_m,prix_statut)"
           " VALUES(?,?,?,?,?,?,?,?)")
    for mat, (eur, e, st) in ACIERS.items():
        for d, (m, i, w) in PROFILS.items():
            c.execute(sql, (d, mat, m, i, w, e, round(m * eur, 2), st))
    for mat, (eur, st) in BOIS_MAT.items():
        for b, h in BOIS:
            vol = b * h / 1e6
            c.execute(sql, (f"{b}x{h}", mat, round(vol * 450, 1), round(b * h**3 / 12 / 1e4),
                            round(b * h**2 / 6 / 1e3), 11.5, round(vol * eur, 2), st))
    c.executemany("INSERT INTO usages VALUES(?,?,?,?,?,?)", USAGES)
    c.executemany("INSERT INTO materiaux VALUES(?,?,?,?,?)", MATERIAUX)
    c.commit()
    return c



def main():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "poutres.db")
    c = build(path)
    n = c.execute("SELECT COUNT(*) FROM poutres").fetchone()[0]
    print(f"{path} : {n} poutres, {len(USAGES)} règles d'usage, {len(MATERIAUX)} matériaux")


if __name__ == "__main__":
    sys.exit(main())
