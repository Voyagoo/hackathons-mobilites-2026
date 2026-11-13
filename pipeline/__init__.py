"""Data pipeline for the "equal access to jobs" track.

Run the steps in order from the repo root:

    uv run python -m pipeline.step1_communes
    uv run python -m pipeline.step2_network_inputs
    uv run python -m pipeline.step3_travel_times --limit 20   # smoke test
    uv run python -m pipeline.step3_travel_times              # full run
    uv run python -m pipeline.step4_access

Every step writes to data/processed/. The Dash app only reads those files.
"""
