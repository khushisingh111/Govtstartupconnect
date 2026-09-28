# Contracts & Finance Module

Owns: the milestone/contract module — structuring the 4-milestone breakdown,
tracking scope and funds per milestone, logging status changes, keeping the
transaction ledger, and handling feedback submission after completion.

## To Do
- [ ] Design `contracts` and `milestones` tables (see /docs/team-build-plan.md)
- [ ] Build create/update/read APIs for contracts
- [ ] On completion, call the Scoring module's `/feedback` endpoint

## Tech
Backend + database — no payment gateway needed, just track state and amounts