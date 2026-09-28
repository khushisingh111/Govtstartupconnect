# SETU — continuation after Antigravity session expiry

## What was completed

- Government matching endpoint now accepts the complete challenge: context, desired outcome, capabilities, skills, KPI, sector and geography.
- Matching uses a hybrid pipeline: SBERT semantic similarity + capability relevance + sector relevance.
- `all-MiniLM-L6-v2` is configured as the SBERT model and CPU execution is enforced.
- If Sentence Transformers is unavailable, the prototype uses a deterministic CPU fallback so the demo still runs. Install `core-apis/requirements.txt` on the target machine to enable SBERT.
- Startup embeddings are cached, and the cache records its engine/model so a fallback cache cannot silently be reused after SBERT is installed.
- Startup data comes from `data/startups.json` / CSV import, not hardcoded recommendation logic.
- DPIIT demo verification is file-backed rather than a hardcoded company registry. It is explicitly a demo source; it is not live DPIIT access.
- Match cards now show semantic fit, SETU Score, risk, sector/location, matched capabilities and evidence counts.
- The government form now captures the complete problem instead of relying on a generic `mobile app` field.
- Added tests for electricity-outage and smart-waste challenges.

## Validation

`tests/test_matching.py` passes:

- Electricity challenge: PowerGrid Analytics and other energy startups rank above MediReach/EduSpark.
- Smart waste challenge: CleanGrid Robotics ranks above MediReach.
- Frontend JavaScript syntax check passes.
- Python compilation checks pass.

## Important before the judge demo

Run:

```bash
pip install -r core-apis/requirements.txt
cd core-apis
python -m uvicorn main:app --reload
```

The first SBERT run may download `all-MiniLM-L6-v2`. Do not claim live DPIIT/GeM/PFMS integration unless official access has actually been connected. The bundled startup registry is demo/sample data.
