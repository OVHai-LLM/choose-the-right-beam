# Choosing the right beam with Olala 1.0 mini

*[Version française](README.fr.md)*

A builder asks: *"For the Atelier Nord workshop, which beam from the catalogue is the cheapest one that carries the load without bending too much?"* An engineer answers in a few minutes:
1. read the project note: where the beam goes, the load, the span;
2. look up the catalogue for the beams allowed there;
3. check each one, cheapest first, for strength and deflection.

This repo shows Olala 1.0 mini doing that job with three tools, from a single question up to the full project.

| Tool | Office equivalent | What it is for |
|---|---|---|
| `run_sql` | the supplier's catalogue | beams, sizes, prices, and which materials are allowed for which use (indoors, by the sea…) |
| `run_python` | a scientific calculator | every calculation, unit conversions included |
| `search_notes` | the project binder | what the client asked for: load, span, site |

The catalogue, the notes and the prompts are in French, as the questions are.

| Example | What Olala 1.0 mini does |
|---|---|
| [`1_questions_simples.py`](exemples/1_questions_simples.py) | One question, one tool: a price or the allowed materials from the catalogue, or a calculation in Python |
| [`2_lire_puis_calculer.py`](exemples/2_lire_puis_calculer.py) | Two tools in a row: read a beam's properties, then compute its deflection |
| [`3_dossier_pas_a_pas.py`](exemples/3_dossier_pas_a_pas.py) | The full project, step by step: Olala mini reads the client's note and writes the catalogue query, the code checks every step and picks the cheapest beam that holds |

## Run it

You need Python 3.10 or later and an OpenAI-compatible endpoint that serves Olala 1.0 mini: `llama-server` from the
[llama.cpp fork](https://github.com/OVHai-LLM/llama.cpp/tree/olala-master) (GGUF files), the
[vLLM fork](https://github.com/OVHai-LLM/vllm) (NVIDIA GPU) or the [mlx-engine](https://github.com/OVHai-LLM/mlx-engine)
server (Mac). See the [model card](https://huggingface.co/OVHaiLLM/Olala-v1.0-mini-7A1B) for the commands.
Upstream llama.cpp, vLLM, LM Studio and Ollama cannot load the `olala` architecture yet.

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env        # then set OLALA_BASE_URL, OLALA_API_KEY and OLALA_MODEL
python3 catalogue.py        # writes poutres.db, the demo catalogue
.venv/bin/python exemples/1_questions_simples.py
```

Ask your own question, or pick another project for the last example:

```bash
.venv/bin/python exemples/2_lire_puis_calculer.py "Lis l'IPE 160 en S235 galvanise, puis calcule sa flèche pour P = 12 kN sur 4,5 m."
.venv/bin/python exemples/3_dossier_pas_a_pas.py "Hangar Sud"
```

Each run prints the tool calls as they happen (`→` the call, `←` what the tool returned), then the answer (`=`).

## How it works

- **[`catalogue.py`](catalogue.py)** builds the demo catalogue: 40 steel and glulam beams, their prices, and the rules of use (which material is allowed where, its design strength, its deflection factor). Prices are 2026 orders of magnitude; this is a demonstration, not a design code.
- **[`outils.py`](outils.py)** holds the three tools and the instructions given to the model: the catalogue schema, the two formulas (stress and deflection of a beam on two supports with a central load), and one rule: never calculate in your head, every number goes through `run_python`.
- **[`olala.py`](olala.py)** is the tool-calling loop: it runs the tools the model asks for and sends the results back until it answers.

**Why the last example is split into steps.** Olala 1.0 mini is at its best on short, single-purpose requests: read this note, write this query. The full project chains a note, a query and up to nine checks, so the example splits the work:
1. Olala mini reads the note and returns the project's figures; the code checks that each figure is really in the note.
2. Olala mini writes the SQL for the allowed beams; the code runs it read-only and checks the rows (use, permission, order by price).
3. The code checks each beam for strength and deflection and keeps the first one that holds.

When a check fails, the code tells the model what is wrong and asks again. That division of work, the model reading and writing, the code checking, is a good default for your own projects.

**About `run_python`.** On macOS the model's code runs under `sandbox-exec`, with no network and no writes outside a temporary folder. Elsewhere it runs in a temporary folder, with an empty environment and a time limit: a precaution, not a security boundary. For real use, run it in a throwaway container.

## Make it yours

- **Your catalogue:** replace the tables in `catalogue.py`, and update the schema in `outils.INSTRUCTIONS`.
- **Your projects:** add notes to `outils.NOTES`, or replace `search_notes` with a search over your own documents.
- **Your checks:** the rules in step 3 of `3_dossier_pas_a_pas.py` are plain Python; add the ones your trade needs (fire rating, mass, delivery length).

## Licences and credits

- **This code** is under the [MIT licence](LICENSE).
- **Olala 1.0 mini**, the model, is under the Apache 2.0 licence.

Libraries and tools used:
- **[`openai`](https://github.com/openai/openai-python)** (Apache-2.0), the Python client used to call the endpoint. It brings its own dependencies (`httpx2`, `httpcore2`, `anyio`, `pydantic`, `jiter`, `idna`…), under Apache-2.0, BSD-3-Clause, MIT or PSF-2.0 licences.
- **Python's standard library** (PSF-2.0), including `sqlite3`, which embeds **[SQLite](https://www.sqlite.org/copyright.html)** (public domain).
- **`sandbox-exec`**, built into macOS, isolates the model's Python on a Mac. It is called, not distributed.

Data and formulas:
- **IPE and HEA section properties** (mass, I, W) are the standard values published for these hot-rolled profiles.
- **The rules of use for glulam** (load-duration factor, creep factor) follow Eurocode 5 service classes, as orders of magnitude.
- **The formulas** are classical beam theory.
- **Prices** are 2026 orders of magnitude, and the projects and notes are fictional.
