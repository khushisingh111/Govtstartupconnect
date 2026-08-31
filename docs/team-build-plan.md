# SETU Platform — Team Build Plan (Schema + API Contract)

## 1. Build Priority Order

| Order | Owner | What to finish |
|---|---|---|
| 1 — Start now | Database module | Finalise the database schema below (structure only, not full data) |
| 2 — Parallel | Scoring, Matching, Contracts modules | Scoring engine, NLP matching, contract/milestone module — use dummy data until real DB is ready |
| 3 | Database + Matching modules | Core APIs — connect scoring + matching outputs into one clean API layer |
| 4 — Last | Frontend module | Frontend dashboards — UI/layout can start early with dummy data; real integration last |

## 2. Database Schema

### 2.1 Startup Table

| Field | Type | Used by |
|---|---|---|
| id | Integer (Primary Key) | All modules |
| name | Text | Frontend, Matching |
| specialization / domain tags | Text / Array | Matching (NLP) |
| achievements / past work | Text | Scoring (profile strength) |
| is_dpiit_certified | Boolean | Scoring (policy weight) |
| state | Text | Scoring (policy weight) |
| is_women_led | Boolean | Scoring (policy weight) |
| verification_status | Text (pending/verified) | Scoring, Frontend |
| profile_strength | Float (0-100) | Scoring |
| current_score | Float | Scoring, Matching, Frontend |

### 2.2 Feedback Table

| Field | Type | Notes |
|---|---|---|
| id | Integer (Primary Key) | — |
| startup_id | Integer (Foreign Key) | Links to Startup |
| contract_id | Integer | Links to Contract table |
| rating | Float (out of 10) | Feeds back into scoring formula |
| created_at | DateTime | — |

### 2.3 Contract & Milestone Tables

| Field | Type | Notes |
|---|---|---|
| contract_id | Integer (Primary Key) | — |
| startup_id | Integer (Foreign Key) | Links to Startup |
| problem_statement_id | Integer | Links to the posted problem |
| milestone_number | Integer (1-4) | — |
| scope | Text | What must be delivered |
| funds_allocated | Float | Budget for this milestone |
| status | Text | planned / in_progress / delivered / paid |

## 3. API Contract

### 3.1 Scoring & Leaderboard API

| Endpoint | Method | Input | Output |
|---|---|---|---|
| /startup-score/{id} | GET | startup id | { startup_id, name, score } |
| /leaderboard | GET | limit (default 20) | list of { startup_id, name, score } |
| /recompute-score/{id} | POST | startup id | { startup_id, new_score } |
| /feedback | POST | { startup_id, contract_id, rating } | { message, updated_score } |

### 3.2 Matching & NLP API

| Endpoint | Method | Input | Output |
|---|---|---|---|
| /match-startups | POST | { problem_statement_text } | ranked top-20 list of { startup_id, name, match_score } |

### 3.3 Contract & Milestone API

| Endpoint | Method | Input | Output |
|---|---|---|---|
| /contracts | POST | { startup_id, problem_statement_id, milestones[] } | { contract_id } |
| /contracts/{id} | GET | contract id | full contract + milestone status |
| /contracts/{id}/milestone/{n} | PUT | { status, funds_released } | updated milestone |

## 4. Golden Rule

- No module reads another module's database directly — always go through the API.
- If the real database isn't ready yet, build and test against dummy/mock data using the same field names above.
- Any change to a table field or API response shape must be shared with the whole team immediately.
