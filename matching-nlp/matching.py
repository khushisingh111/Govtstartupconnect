"""
Matching & NLP module.

For the hackathon prototype this uses a lightweight keyword-overlap approach
(tokenize + normalise + score by shared terms) rather than a full embeddings
model, so it has no heavy external dependencies and still demonstrates the
real mechanism: read the problem statement, extract what it needs, compare
against each startup's declared tags, rank by fit.

Swapping in sentence-transformers later only means replacing `_similarity()`
below — the rest of the pipeline (extract -> score -> rank) stays the same.
"""

import re

STOPWORDS = {
    "the", "a", "an", "and", "or", "for", "to", "of", "in", "on", "with",
    "at", "by", "is", "are", "be", "this", "that", "it", "as", "using",
}


def _tokenize(text: str):
    words = re.findall(r"[a-zA-Z]+", text.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def _similarity(problem_tokens: set, startup_tokens: set) -> float:
    if not problem_tokens or not startup_tokens:
        return 0.0
    overlap = problem_tokens & startup_tokens
    # Jaccard-style overlap, scaled 0-100
    return round(100 * len(overlap) / len(problem_tokens | startup_tokens) * 3, 2)  # scaled up for visible spread


def match_startups(problem_text: str, startups: list, top_n: int = 20):
    """
    startups: list of Startup ORM objects (must have .tags, .name, .id, .current_score)
    Returns a ranked list of dicts: {startup_id, name, match_score, matched_terms, current_score}
    """
    problem_tokens = _tokenize(problem_text)
    results = []

    for s in startups:
        startup_tokens = _tokenize(s.tags or "")
        sim = _similarity(problem_tokens, startup_tokens)
        matched_terms = sorted(problem_tokens & startup_tokens)
        if sim > 0:
            results.append({
                "startup_id": s.id,
                "name": s.name,
                "match_score": min(sim, 100),
                "matched_terms": matched_terms,
                "current_score": s.current_score,
            })

    # Rank by match relevance first, then by overall trust score as a tiebreaker
    results.sort(key=lambda r: (r["match_score"], r["current_score"]), reverse=True)
    return results[:top_n]
