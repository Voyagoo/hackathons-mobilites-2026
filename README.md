# Access to Work | Île-de-France

An interactive map of how many of the region's 6.1 million jobs residents can reach within 30, 45 or 60 minutes, by public transport at five times of day and by car.

> Challenge 2 — Mobility and employment

## About the project

This project was developed as part of the Hackaviz Mobilités 2026 (special dataviz edition), organised by Île-de-France Mobilités from 2 to 26 November 2026. To learn more, see the [Participants' guide](https://github.com/hackathons-mobilites/hackaviz_2026/blob/main/README.md).

**Team**

- TODO: Name
- TODO: Name
- TODO: Name

## The problem and value proposition

<!-- What problem does your project address? Who are the target users? -->



## The solution

<!-- Your solution and how it works overall, the data used, and how it addresses the problem -->

TODO

Link to the dataviz: TODO

Data used:

| Data | Source | Licence |
| --- | --- | --- |
| Jobs by place of work, census 2023 (EMP1) | [INSEE via data.gouv.fr](https://www.data.gouv.fr/datasets/emploi-au-lieu-de-travail-selon-le-statut-le-temps-de-travail-et-lage-quinquennal-donnees-detaillees-emp1) | Licence Ouverte |
| Employed residents by place of work and mode, census 2023 (NAV2A/NAV2B) | [INSEE via data.gouv.fr](https://www.data.gouv.fr/datasets/deplacements-domicile-travail-selon-le-sexe-le-lieu-de-travail-et-le-moyen-de-transport-donnees-detaillees-nav2a-et-nav2b) | Licence Ouverte |
| Population by commune, 2023 | [INSEE](https://www.insee.fr/fr/statistiques/8680726) | Licence Ouverte |
| Median income by commune (Filosofi) | [data.gouv.fr](https://www.data.gouv.fr/datasets/revenu-des-francais-a-la-commune) | Licence Ouverte |
| Commune boundaries 2025 (ADMIN EXPRESS) | [IGN via data.gouv.fr](https://www.data.gouv.fr/datasets/communes-cantons-et-epci-2025-admin-express-cog-plus-ign) | Licence Ouverte |
| Paris arrondissement boundaries | [Ville de Paris](https://opendata.paris.fr/explore/dataset/arrondissements/) | ODbL |
| Employment zones (composition) | [data.iledefrance.fr](https://data.iledefrance.fr/explore/dataset/base-des-zones-demploi/information/) | Licence Ouverte |
| Public transport timetables (GTFS) | [Île-de-France Mobilités](https://prim.iledefrance-mobilites.fr/en/jeux-de-donnees/offre-horaires-tc-gtfs-idfm) | ODbL |
| Street network (OpenStreetMap extract) | [Geofabrik](https://download.geofabrik.de/europe/france/ile-de-france.html) | ODbL 1.0 |

Travel times are computed with [Conveyal R5](https://github.com/conveyal/r5) through [r5py](https://r5py.readthedocs.io/).

## Challenges overcome and data issues

<!-- Main problems encountered and how you solved them, plus recommendations to IDFM
     on data and API openings that would have helped your project -->

TODO

## What's next?

<!-- How you would develop the project with more time: next use cases, resources needed -->

TODO

## Installation and usage

The results the app reads are versioned in `data/processed/` (about 18 MB), so the app runs right after a clone. Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run uvicorn app.main:server --reload
```

Then open http://127.0.0.1:8000.

To rebuild the results from the raw data (several GB, not versioned; sources in the table above), you also need a Java JDK 21 or later for r5py:

```bash
# Commune table: jobs, residents, income
uv run python -m pipeline.communes
# GTFS zip and OpenStreetMap extract
uv run python -m pipeline.network_inputs
# Travel-time matrices (r5py), about 1 hour
uv run python -m pipeline.travel_times
# Move routing points the router cannot reach, then recompute public transport
uv run python -m pipeline.fix_unroutable_anchors
uv run python -m pipeline.travel_times --force --scenarios transit_tue_0830 transit_tue_0500 transit_tue_2230 transit_tue_1200 transit_sat_0830
# Jobs reachable and equality indicators
uv run python -m pipeline.access
# Optional rail overlay for the map
uv run python -m pipeline.extra_rail_lines
```

## Deployment

The image contains the app and `data/processed/` only (no router, no Java). One worker needs about 520 MB of memory.

```bash
docker build -f deploy/Dockerfile -t access-to-work .
docker run -d --name access-to-work --restart unless-stopped -p 127.0.0.1:8050:8000 access-to-work
```

To try it locally first: `docker run --rm -p 8050:8000 access-to-work`, then open http://localhost:8050.

Put a reverse proxy with HTTPS (for example Caddy or nginx) in front of `127.0.0.1:8050`.

## Licence

The code and documentation of this project are licensed under [MIT](https://github.com/hackathons-mobilites/hackaviz_2026/blob/main/Docs/License.md).
