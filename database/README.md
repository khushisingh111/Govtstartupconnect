# Database Module

Owns: startup profile database, registration/auth.

## To Do
- [ ] Finalise schema for `startups`, `feedback` tables (see /docs/team-build-plan.md)
- [ ] Set up Postgres/MySQL instance
- [ ] Build signup/login (auth tokens or sessions)
- [ ] Share final field names with Scoring module and Matching module

## Tech
Postgres/MySQL + an ORM (SQLAlchemy if Python, Prisma/Sequelize if Node)