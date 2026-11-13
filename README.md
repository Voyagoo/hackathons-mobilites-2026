# [Project name]

TODO: one-line description of what the project does (keep it very short).

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

Data used: see [docs/data_sources.md](docs/data_sources.md).

## Challenges overcome and data issues

<!-- Main problems encountered and how you solved them, plus recommendations to IDFM
     on data and API openings that would have helped your project -->

TODO

## What's next?

<!-- How you would develop the project with more time: next use cases, resources needed -->

TODO

## Installation and usage

Requires Python 3.12, [uv](https://docs.astral.sh/uv/) and a Java JDK 21 or later (for r5py).

```bash
uv sync

# Pipeline (writes to data/processed/)
uv run python -m pipeline.step1_communes          # commune table: jobs, residents, income
uv run python -m pipeline.step2_network_inputs    # GTFS zip + OpenStreetMap extract
uv run python -m pipeline.step3_travel_times      # travel-time matrices (r5py), slow
uv run python -m pipeline.step4_access            # jobs reachable + equality indicators

# Dash app
uv run uvicorn app.main:server --reload
```

The `data/` folder is not versioned; see [docs/data_sources.md](docs/data_sources.md) to download the data.

## Licence

The code and documentation of this project are licensed under [MIT](https://github.com/hackathons-mobilites/hackaviz_2026/blob/main/Docs/License.md).
