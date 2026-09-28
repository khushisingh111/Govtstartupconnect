# Matching & NLP Module

Owns: reading a government problem statement, extracting required skills/domain,
matching against startup profiles, returning ranked top-20.

## To Do
- [ ] Set up sentence-transformers or a keyword-extraction approach
- [ ] Build the tagged skills taxonomy that startup profiles map to
- [ ] Expose `/match-startups` as an API endpoint (see /docs/team-build-plan.md)

## Tech
Python + sentence-transformers (or similar lightweight NLP library)