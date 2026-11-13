# The Last Kilometres to Work

**Hackathon Mobilités 2026 · Défi 2 — Mobilités et emploi**

Which suburban employment hubs in Île-de-France are difficult to reach without a car, and where could a short cycling or bus connection from a station improve access?

Our first case study will cover **one employment hub, two or three nearby stations and three residential starting points**. The hub and improvement scenario are still to be selected.

## Get started

Requirements: **Python 3.11+**, **uv**, and VS Code with the Python and Jupyter extensions.

1. Download the six CSV files listed below and place them at the project root, beside this README. Keep the filenames unchanged.
2. Run `uv sync` from the project folder.
3. Open a notebook, select the project's **.venv** Python kernel, then choose **Restart Kernel and Run All**.

Raw downloads and `.venv/` are excluded by `.gitignore`; teammates download their own copies. The notebooks leave raw files unchanged. Optional Parquet exports go to `data/cleaned/` when `SAVE_CLEANED = True`.

## Datasets

These are the six local inputs used by the current notebooks. Source links are starting points for downloading them; confirm the licence, reference period and export format before sharing results.

| Dataset and source | Expected filename | What we use it for |
|---|---|---|
| [INSEE MOBPRO 2023](https://www.insee.fr/fr/statistiques/9004795) | `FD_MOBPRO_2023.csv` | Residence/workplace geography, usual main commuting mode and statistical weights. |
| MOBPRO variable dictionary, from the same INSEE download | `varmod_mobpro_2023.csv` | Definitions, category codes and commune names. Read this first. |
| [IDFM railway stations by line](https://data.iledefrance-mobilites.fr/explore/dataset/emplacement-des-gares-idf/information/) | `emplacement-des-gares-idf.csv` | Station locations, station IDs and listed rail connections. |
| [IDFM transport-line reference](https://data.iledefrance-mobilites.fr/explore/dataset/referentiel-des-lignes/information/) | `referentiel-des-lignes.csv` | Line IDs, names, modes, operators and statuses. |
| [PRIM average weekly service outside school holidays](https://prim.iledefrance-mobilites.fr/fr/jeux-de-donnees/offre_hebdomadaire_moyenne_hors_vacances) | `offre_hebdomadaire_moyenne_hors_vacances.csv` | Average service counts by stop, line, hour and weekday. |
| [PRIM cycling facilities](https://prim.iledefrance-mobilites.fr/jeux-de-donnees/amenagements-velo-en-ile-de-france) | `amenagements-velo-en-ile-de-france.csv` | Cycling-related features, classifications and geometry near stations and workplaces. |

The current readers expect **semicolon-separated UTF-8 CSVs**. For each download, record its source URL, download date, reference period, licence and geographic coverage. For spatial data, also record the coordinate reference system and measurement units.

## Notebook guide

| Notebook | Purpose | Default scope |
|---|---|---|
| [00 — MOBPRO dictionary](notebooks/00_mobpro_dictionary.ipynb) | Understand variables and codes. | Full dictionary |
| [01 — MOBPRO](notebooks/01_mobpro.ipynb) | Inspect commuting records and weights. | First 10,000 rows |
| [02 — Stations](notebooks/02_stations.ipynb) | Explore station locations and listed lines. | Full file |
| [03 — Lines](notebooks/03_lines.ipynb) | Explore transport modes, operators and statuses. | Full file |
| [04 — Service offer](notebooks/04_service_offer.ipynb) | Inspect service-count fields and hourly coverage. | First 20,000 rows |
| [05 — Cycling](notebooks/05_cycling.ipynb) | Explore feature categories and representative points. | Full file |
| [06 — Commuting by commune](notebooks/06_commuting_by_commune.ipynb) | Compare weighted commuting-mode shares across Île-de-France communes. | Full MOBPRO scan in chunks |

**First-row samples are not representative.** Notebooks 01 and 04 offer an optional `RUN_FULL_SCAN`; notebook 06 scans the full MOBPRO source by default.

Reusable dataset functions live in [scripts/datasets/](scripts/datasets/); shared reading, inspection and export helpers live in [scripts/exploration.py](scripts/exploration.py). Transport and cycling sources are currently explored separately; connections between datasets remain to be built.

## Analysis rules

- **Count workers with weights:** sum valid `IPONDI` values. Row counts and estimated workers are different; neither is a daily trip count.
- **Choose the population:** `REGION = "11"` selects Île-de-France residents; `REGLT = "11"` selects people working there. Notebook 06 defaults to residence; choose `GEOGRAPHY = "workplace"` to study employment destinations.
- **Keep codes as text:** `COMMUNE` identifies residence and `DCLT` workplace geography. Use INSEE codes, not postal codes. Notebook 06 groups Paris workplace arrondissements into `75056`.
- **State the denominator:** current mode shares include mode 1, “no transport.” High car use alone does not establish car dependence.
- **Check transport identifiers and dates:** repeated station IDs can represent different lines; listed lines may include planned services. Average service counts cannot establish exact transfers.
- **Check actual routes:** representative cycling points do not establish a usable route. Verify geometry, crossings, restrictions and units before measuring access.

## Team workflow and next steps

1. Explore the notebooks and record findings, data issues and assumptions in a GitHub issue.
2. Shortlist three employment hubs, then choose one based on commuting patterns and data availability.
3. Add local business-park boundaries and workplace entrances, plus commune boundaries for maps.
4. Build a baseline map of station-to-workplace access. Use [dated GTFS schedules](https://prim.iledefrance-mobilites.fr/jeux-de-donnees/offre-horaires-tc-gtfs-idfm) and a routable street/path network for journey comparisons.
5. Compare the baseline with one clearly labelled cycling or bus scenario. Specify the weekday, outbound and return times, walking, waiting, transfers and cycling assumptions.
6. Share a visual story with source links, methods, limitations and readable tables alongside charts.

Use a branch and pull request for each focused contribution. Include what changed, how to reproduce it and whether results use a sample or the full dataset. Keep raw inputs unchanged and check licences before committing derived data.

**First milestone:** a verified map of one employment hub and its station connections, supported by commuting and service-level evidence.

[Official hackathon dataset catalogue](https://airtable.com/appdkuZ71MaQ2sGyB/shra9C5uK1cxeAmkb/tblC8dlSqeplzyg0A)
