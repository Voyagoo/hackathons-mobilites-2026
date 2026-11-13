"""Data pipeline for the "equal access to jobs" track.

Run the steps in order from the repo root:

    uv run python -m pipeline.communes
    uv run python -m pipeline.network_inputs
    uv run python -m pipeline.travel_times --limit 20   # smoke test
    uv run python -m pipeline.travel_times              # full run
    uv run python -m pipeline.access

Every step writes to data/processed/. The Dash app only reads those files.
"""
