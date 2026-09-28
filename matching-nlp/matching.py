"""
Matching & NLP Module for SETU.

PRD Section 18.1:
Transforms SETU into a genuine data-driven, semantic, explainable startup discovery system.
Uses Sentence Transformers (all-MiniLM-L6-v2) on CPU, hybrid capability/sector scoring,
precomputed embedding caches, and dynamic match explanation generation.
"""

import os
import sys
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from preprocessing import (
    build_challenge_search_text,
    build_startup_search_text,
    extract_matched_capabilities,
    tokenize,
    GENERIC_TECH_TERMS,
)
from semantic_matcher import (
    match_startups_semantic,
    compute_and_cache_startup_embeddings,
    get_model,
)
from explanations import generate_match_explanation


def _to_startup_dict(s) -> Dict[str, Any]:
    """Helper to convert Startup ORM model or dict to standard dict."""
    if isinstance(s, dict):
        return s
    if hasattr(s, "to_dict"):
        return s.to_dict()
    # ORM object fallback
    return {
        "id": getattr(s, "id", 0),
        "name": getattr(s, "name", ""),
        "display_name": getattr(s, "display_name", getattr(s, "name", "")),
        "legal_name": getattr(s, "legal_name", getattr(s, "name", "")),
        "description": getattr(s, "description", ""),
        "capabilities": getattr(s, "capabilities", getattr(s, "tags", "")),
        "products": getattr(s, "products", ""),
        "technology_tags": getattr(s, "technology_tags", ""),
        "tags": getattr(s, "tags", ""),
        "industry": getattr(s, "industry", ""),
        "sector": getattr(s, "sector", ""),
        "maturity_level": getattr(s, "maturity_level", "Pilot-Ready"),
        "location": getattr(s, "location", ""),
        "state": getattr(s, "state", ""),
        "city": getattr(s, "city", ""),
        "past_deployments": getattr(s, "past_deployments", getattr(s, "achievements", "")),
        "past_deployments_count": getattr(s, "past_deployments_count", 0),
        "dpiit_status": getattr(s, "dpiit_status", "verified" if getattr(s, "is_dpiit_certified", False) else "none"),
        "dpiit_number": getattr(s, "dpiit_number", None),
        "is_dpiit_certified": getattr(s, "is_dpiit_certified", False),
        "is_women_led": getattr(s, "is_women_led", False),
        "verification_status": getattr(s, "verification_status", "pending"),
        "verified_evidence_count": getattr(s, "verified_evidence_count", 0),
        "profile_strength": getattr(s, "profile_strength", 50.0),
        "current_score": getattr(s, "current_score", 0.0),
        "debarred": getattr(s, "debarred", False),
        "turnover_lakhs": getattr(s, "turnover_lakhs", 0.0),
        "experience_years": getattr(s, "experience_years", 0),
    }


def match_startups(problem_text: str, startups: list, top_n: int = 20) -> List[Dict[str, Any]]:
    """
    Backward-compatible entry point for existing API endpoints.
    Now powered by the real semantic engine rather than shallow keyword overlap!
    """
    challenge = {
        "title": problem_text,
        "desired_outcome": "",
        "problem_context": problem_text,
        "capabilities_needed": problem_text,
        "skills_needed": problem_text,
        "sector": "",
    }
    return match_challenge_comprehensive(challenge, startups, top_n=top_n)


def match_challenge_comprehensive(
    challenge: Dict[str, Any],
    startups: list,
    top_n: int = 50,
) -> List[Dict[str, Any]]:
    """
    Primary semantic discovery pipeline for SETU:
    1. Preprocesses challenge & startup data (filtering generic tech noise).
    2. Runs SBERT semantic similarity + capability + sector matching.
    3. Generates data-driven explainable reasons.
    4. Returns ranked candidates with rich metadata.
    """
    startup_dicts = [_to_startup_dict(s) for s in startups]
    if not startup_dicts:
        return []

    # Semantic hybrid ranking
    ranked_candidates = match_startups_semantic(challenge, startup_dicts, top_n=top_n)

    results = []
    for cand in ranked_candidates:
        s = cand["startup"]
        match_score = cand["match_score"]
        sem_sim = cand["semantic_similarity"]

        # Generate explainable reasons dynamically
        explanation = generate_match_explanation(challenge, s, match_score, sem_sim)

        # Matched terms for backward-compatibility
        matched_terms = explanation["matched_capabilities"] or [s.get("sector", "General")]

        results.append({
            "startup_id": s["id"],
            "name": s["name"],
            "legal_name": s["legal_name"],
            "display_name": s["display_name"],
            "match_score": match_score,
            "semantic_match_pct": match_score,
            "semantic_similarity": sem_sim,
            "capability_relevance": cand["capability_relevance"],
            "sector_relevance": cand["sector_relevance"],
            "matched_terms": matched_terms,
            "why_matched": explanation["why_matched"],
            "matched_capabilities": explanation["matched_capabilities"],
            "semantic_relevance": explanation["semantic_relevance"],
            "domain": explanation["domain"],
            "sector": s.get("sector", ""),
            "location": s.get("location", f"{s.get('city', '')}, {s.get('state', '')}".strip(", ")),
            "state": s.get("state", ""),
            "dpiit_status": s.get("dpiit_status", "self_declared"),
            "dpiit_number": s.get("dpiit_number"),
            "is_dpiit_certified": s.get("is_dpiit_certified", False),
            "verification_status": s.get("verification_status", "pending"),
            "verified_evidence_count": s.get("verified_evidence_count", 0),
            "past_deployments_count": s.get("past_deployments_count", 0),
            "profile_strength": s.get("profile_strength", 50.0),
            "current_score": s.get("current_score", 0.0),
            "turnover_lakhs": s.get("turnover_lakhs", 0.0),
            "experience_years": s.get("experience_years", 0),
            "debarred": s.get("debarred", False),
        })

    return results
