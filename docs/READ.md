# Documentation

Shared reference material for the whole team.

## Files in this folder
- `team-build-plan.md` — database schema + API contract that every module must follow
- Pitch deck and solution write-up (add here once finalised)

## Golden Rule
No module reads another module's database directly — always go through the API.
If the real database isn't ready yet, build and test against dummy/mock data using
the field names in `team-build-plan.md`.
Any change to a table field or API response shape must be shared with the whole team immediately.