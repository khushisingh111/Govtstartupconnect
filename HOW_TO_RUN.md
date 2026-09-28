# SETU — Running the Prototype

This folder contains working code for all 6 modules, wired together so the
website actually reads and writes real data — nothing here is mock/fake data.

## How the pieces connect

```
frontend/  (HTML/CSS/JS)
    |  fetch() calls
    v
core-apis/main.py   <-- the only file that imports the others
    |         |            |
    v         v            v
database/  scoring-engine/  matching-nlp/   contracts-finance/
models.py   scoring.py       matching.py     contracts.py
database.py
```

`core-apis/main.py` is the single server you run. It serves the frontend
AND exposes the APIs, so you only need one terminal running.

## How to run it (one time setup)

1. Open a terminal in this folder (the one with `database/`, `frontend/`, etc. inside it)
2. Install the required packages:
   ```bash
   pip install -r core-apis/requirements.txt
   ```
3. Start the server:
   ```bash
   cd core-apis
   python -m uvicorn main:app --reload
   ```
4. Open your browser to: **http://localhost:8000**

That's it — the website will load from the startup registry in `data/startups.json`.
The demo registry is intentionally file-backed so startup recommendations are not
hardcoded into the matching code.

## What's real vs demo

- **Real**: the scoring formula, the matching algorithm, the database writes,
  the API contracts — all of it runs live when you use the site.
- **Demo-only**: the 8 starter startups are seeded automatically so the page
  isn't empty before your team registers real ones. The matching approach
  is keyword-overlap (not a full embeddings model yet) — see the comment at
  the top of `matching-nlp/matching.py` for how to upgrade it later.

## Where each team member's work goes

Everyone can keep working inside their own folder exactly as planned in
`docs/team-build-plan.md` — nothing about that plan changes. This just fills
in each folder with a working first version instead of an empty README.
