# Scoring & Leaderboard Module

Owns: the formula that turns policy weightings + profile data + past feedback
into a single point score per startup, and keeps a leaderboard updated.

## To Do
- [ ] Design the weighted scoring formula (policy + profile + feedback)
- [ ] Keep the logic transparent/explainable — government users need to see why a score is what it is
- [ ] Accept feedback data as input after contracts complete, so scores update over time
- [ ] Expose scoring + leaderboard as API endpoints (see /docs/team-build-plan.md)

## Tech
Python — structured weighted scoring logic, not a black-box ML model