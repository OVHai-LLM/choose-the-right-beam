# Choisir la bonne poutre avec Olala 1.0 mini

*[English version](README.md)*

Un artisan demande : *« Pour l'Atelier Nord, quelle est la poutre la moins chère du catalogue qui tienne la charge sans trop plier ? »* Un ingénieur répond en quelques minutes :
1. il lit la note du projet : où va la poutre, la charge, la portée ;
2. il cherche dans le catalogue les poutres autorisées à cet endroit ;
3. il vérifie chacune, de la moins chère à la plus chère, en résistance et en flèche.

Ce dépôt montre Olala 1.0 mini faire ce travail avec trois outils, d'une simple question jusqu'au dossier complet.

| Outil | Équivalent au bureau | À quoi il sert |
|---|---|---|
| `run_sql` | le catalogue du fournisseur | les poutres, leurs dimensions, leurs prix, et les matériaux autorisés selon l'usage (intérieur, bord de mer…) |
| `run_python` | une calculatrice scientifique | tous les calculs, conversions d'unités comprises |
| `search_notes` | le classeur des projets | ce que demande le client : charge, portée, lieu |

| Exemple | Ce que fait Olala 1.0 mini |
|---|---|
| [`1_questions_simples.py`](exemples/1_questions_simples.py) | Une question, un outil : un prix ou les matériaux autorisés dans le catalogue, ou un calcul en Python |
| [`2_lire_puis_calculer.py`](exemples/2_lire_puis_calculer.py) | Deux outils à la suite : lire les caractéristiques d'une poutre, puis calculer sa flèche |
| [`3_dossier_pas_a_pas.py`](exemples/3_dossier_pas_a_pas.py) | Le dossier complet, pas à pas : Olala mini lit la note du client et écrit la requête au catalogue, le code contrôle chaque étape et garde la poutre la moins chère qui tient |

## Le lancer

Il faut Python 3.10 ou plus et un endpoint compatible OpenAI qui sert Olala 1.0 mini : `llama-server` du
[fork llama.cpp](https://github.com/OVHai-LLM/llama.cpp/tree/olala-master) (fichiers GGUF), le
[fork vLLM](https://github.com/OVHai-LLM/vllm) (GPU NVIDIA) ou le serveur [mlx-engine](https://github.com/OVHai-LLM/mlx-engine)
(Mac). Les commandes sont dans la [fiche du modèle](https://huggingface.co/OVHaiLLM/Olala-v1.0-mini-7A1B).
llama.cpp, vLLM, LM Studio et Ollama officiels ne chargent pas encore l'architecture `olala`.

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env        # puis renseignez OLALA_BASE_URL, OLALA_API_KEY et OLALA_MODEL
python3 catalogue.py        # écrit poutres.db, le catalogue de démonstration
.venv/bin/python exemples/1_questions_simples.py
```

Posez votre propre question, ou choisissez un autre projet pour le dernier exemple :

```bash
.venv/bin/python exemples/2_lire_puis_calculer.py "Lis l'IPE 160 en S235 galvanise, puis calcule sa flèche pour P = 12 kN sur 4,5 m."
.venv/bin/python exemples/3_dossier_pas_a_pas.py "Hangar Sud"
```

Chaque exécution affiche les appels d'outils au fil de l'eau (`→` l'appel, `←` ce que l'outil a renvoyé), puis la réponse (`=`).

## Comment ça marche

- **[`catalogue.py`](catalogue.py)** construit le catalogue de démonstration : 40 poutres en acier et en bois lamellé-collé, leurs prix, et les règles d'usage (quel matériau est autorisé où, sa résistance de calcul, son coefficient de flèche). Les prix sont des ordres de grandeur 2026 ; c'est une démonstration, pas une base de calcul réglementaire.
- **[`outils.py`](outils.py)** contient les trois outils et les consignes données au modèle : le schéma du catalogue, les deux formules (contrainte et flèche d'une poutre sur deux appuis chargée au centre), et une règle : ne jamais calculer de tête, tout chiffre passe par `run_python`.
- **[`olala.py`](olala.py)** est la boucle d'appels d'outils : elle exécute les outils demandés par le modèle et lui renvoie les résultats jusqu'à sa réponse.

**Pourquoi le dernier exemple est découpé en étapes.** Olala 1.0 mini donne le meilleur de lui-même sur des demandes courtes et précises : lis cette note, écris cette requête. Le dossier complet enchaîne une note, une requête et jusqu'à neuf vérifications, alors l'exemple partage le travail :
1. Olala mini lit la note et rend les données du projet ; le code vérifie que chaque valeur figure bien dans la note.
2. Olala mini écrit la requête SQL des poutres autorisées ; le code l'exécute en lecture seule et contrôle les lignes (usage, autorisation, tri par prix).
3. Le code vérifie chaque poutre en résistance et en flèche, et garde la première qui tient.

Quand un contrôle échoue, le code dit au modèle ce qui ne va pas et redemande. Ce partage du travail, le modèle qui lit et écrit, le code qui contrôle, est un bon point de départ pour vos propres dossiers.

**À propos de `run_python`.** Sur macOS, le code du modèle tourne sous `sandbox-exec`, sans réseau et sans écriture hors d'un dossier temporaire. Ailleurs, il tourne dans un dossier temporaire, avec un environnement vide et un délai : c'est une précaution, pas une barrière de sécurité. Pour un usage réel, exécutez-le dans un conteneur jetable.

## L'adapter

- **Votre catalogue :** remplacez les tables de `catalogue.py`, et mettez à jour le schéma dans `outils.INSTRUCTIONS`.
- **Vos projets :** ajoutez des notes dans `outils.NOTES`, ou remplacez `search_notes` par une recherche dans vos propres documents.
- **Vos vérifications :** les règles de l'étape 3 de `3_dossier_pas_a_pas.py` sont du Python simple ; ajoutez celles de votre métier (tenue au feu, masse, longueur livrable).

## Licences et crédits

- **Ce code** est sous [licence MIT](LICENSE).
- **Olala 1.0 mini**, le modèle, est sous licence Apache 2.0.

Bibliothèques et outils utilisés :
- **[`openai`](https://github.com/openai/openai-python)** (Apache-2.0), le client Python qui appelle l'endpoint. Il apporte ses propres dépendances (`httpx2`, `httpcore2`, `anyio`, `pydantic`, `jiter`, `idna`…), sous licences Apache-2.0, BSD-3-Clause, MIT ou PSF-2.0.
- **La bibliothèque standard de Python** (PSF-2.0), dont `sqlite3`, qui embarque **[SQLite](https://www.sqlite.org/copyright.html)** (domaine public).
- **`sandbox-exec`**, intégré à macOS, isole le Python du modèle sur Mac. Il est appelé, pas distribué.

Données et formules :
- **Les caractéristiques des profilés IPE et HEA** (masse, I, W) sont les valeurs normalisées publiées pour ces profilés laminés.
- **Les règles d'usage du bois lamellé-collé** (coefficient de durée de charge, coefficient de fluage) suivent les classes de service de l'Eurocode 5, en ordre de grandeur.
- **Les formules** sont celles de la résistance des matériaux classique.
- **Les prix** sont des ordres de grandeur 2026, et les projets et les notes sont fictifs.
