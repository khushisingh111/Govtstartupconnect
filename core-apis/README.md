# Core APIs

Owns: the API layer that sits between the ML modules (scoring, matching) and
the frontend — taking outputs from scoring/matching and serving them in a
clean, consistent format the dashboards can consume.

## To Do
- [ ] Wrap scoring-engine + matching-nlp outputs in a consistent response format
- [ ] Handle requests from frontend and route to the right internal module
- [ ] Keep response formats in sync with /docs/team-build-plan.md

## Tech
FastAPI or Flask (pairs naturally with the Python ML side)