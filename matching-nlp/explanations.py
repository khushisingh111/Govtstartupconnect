"""
Dynamic Match Explanation Engine for SETU.

PRD Section 18.1 & Section 4 of User Requirements:
"Every decision is explainable.
Why this matched:
✓ Power distribution monitoring
✓ Real-time outage detection
✓ Utility infrastructure
✓ IoT telemetry
Semantic relevance: High
Domain: Energy / Utilities
Capability overlap: Power monitoring, outage detection
The explanation must be generated from actual startup data and challenge data."
"""

import re
from typing import Dict, Any, List
from preprocessing import extract_matched_capabilities, tokenize, GENERIC_TECH_TERMS


def generate_match_explanation(
    challenge: Dict[str, Any],
    startup: Dict[str, Any],
    match_score: float,
    semantic_sim: float,
) -> Dict[str, Any]:
    """
    Dynamically generates explainable match rationale using real challenge & startup data.
    Strictly avoids hardcoded explanations or boilerplate.
    """
    challenge_title = challenge.get("title") or ""
    challenge_context = f"{challenge_title} {challenge.get('desired_outcome', '')} {challenge.get('problem_context', '')} {challenge.get('capabilities_needed', '')}"
    challenge_tokens = set(tokenize(challenge_context)) - GENERIC_TECH_TERMS

    # 1. Extract overlapping capabilities
    matched_caps = extract_matched_capabilities(
        challenge_context,
        startup.get("capabilities") or startup.get("tags") or ""
    )

    # 2. Extract overlapping technology items
    tech_tags = startup.get("technology_tags") or ""
    tech_list = [t.strip() for t in re.split(r"[,;]+", tech_tags) if t.strip()]
    matched_tech = []
    for t in tech_list:
        if t.lower() not in GENERIC_TECH_TERMS:
            t_tokens = set(tokenize(t))
            if t_tokens & challenge_tokens:
                matched_tech.append(t)

    # 3. Compile "Why this matched" dynamic bullet points
    why_matched = []

    # Add core capability matches
    for cap in matched_caps[:3]:
        why_matched.append(cap)

    # Add relevant technology or product capabilities
    for tech in matched_tech[:2]:
        if tech not in why_matched:
            why_matched.append(tech)

    # Add domain alignment if applicable
    s_sector = startup.get("sector") or startup.get("industry") or ""
    c_sector = challenge.get("sector") or ""
    if s_sector and (s_sector.lower() in challenge_context.lower() or (c_sector and c_sector.lower() in s_sector.lower())):
        why_matched.append(f"Domain alignment: {s_sector}")

    # Add deployment evidence if relevant
    deployments = startup.get("past_deployments_count") or 0
    if deployments > 0:
        why_matched.append(f"Proven field record ({deployments} previous deployments)")

    # Fallback if sparse (ensure at least 2 data-driven reasons)
    if not why_matched:
        if s_sector:
            why_matched.append(f"Specialized in {s_sector}")
        if startup.get("products"):
            why_matched.append(f"Product suite: {startup.get('products')}")

    # 4. Semantic relevance level
    if match_score >= 75.0:
        relevance_label = "High"
    elif match_score >= 50.0:
        relevance_label = "Medium"
    else:
        relevance_label = "Low"

    # 5. Domain / sector
    domain = s_sector or "General Innovation"

    # 6. Capability overlap summary
    cap_overlap_str = ", ".join(matched_caps) if matched_caps else "General domain alignment"

    return {
        "match_percentage": round(match_score, 1),
        "semantic_relevance": relevance_label,
        "domain": domain,
        "why_matched": why_matched,
        "matched_capabilities": matched_caps,
        "capability_overlap": cap_overlap_str,
        "matched_technologies": matched_tech,
    }
