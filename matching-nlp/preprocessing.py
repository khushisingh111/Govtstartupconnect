"""
Preprocessing & Text Normalization for SETU Semantic Matching.

Aligned with SETU_PRD_and_Architecture.md Section 18.1:
"challenge_text = outcome + context + KPI names.
startup_text = capabilities + products + past deployments."

Generic technology terms ("app", "mobile", "AI", "software", "platform", "dashboard")
are downweighted / filtered so domain problems dominate discovery.
"""

import re
from typing import List, Set, Dict, Any
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from database.config import GENERIC_TECH_TERMS
except ImportError:
    GENERIC_TECH_TERMS = {
        "app", "apps", "mobile", "mobile app", "mobile application", "application",
        "software", "platform", "dashboard", "tool", "solution", "system",
        "ai", "artificial intelligence", "ml", "machine learning", "portal",
        "website", "web app", "digital", "tech", "technology", "interface"
    }

STOPWORDS = {
    "the", "a", "an", "and", "or", "for", "to", "of", "in", "on", "with",
    "at", "by", "is", "are", "be", "this", "that", "it", "as", "using",
    "from", "into", "their", "our", "all", "any", "which", "when", "whenever",
    "who", "what", "where", "how", "has", "have", "had", "will", "would",
    "should", "can", "could", "may", "might", "must", "about", "above", "after",
    "before", "between", "both", "during", "each", "few", "more", "most", "other",
    "some", "such", "than", "too", "very", "create", "develop", "provide", "platform"
}


def build_challenge_search_text(challenge: Dict[str, Any]) -> str:
    """
    Constructs a rich, domain-focused representation of the complete government challenge.
    Emphasizes outcomes and specific domain capabilities over generic tech requests.
    """
    parts = []

    # 1. Primary problem & outcome (highest weight in semantic understanding)
    title = (challenge.get("title") or "").strip()
    if title:
        parts.append(title)

    outcome = (challenge.get("desired_outcome") or challenge.get("outcome") or "").strip()
    if outcome:
        parts.append(f"Desired Outcome: {outcome}")

    context = (challenge.get("problem_context") or challenge.get("context") or challenge.get("description") or "").strip()
    if context:
        parts.append(f"Context: {context}")

    # 2. Sector and domain
    sector = (challenge.get("sector") or challenge.get("department") or "").strip()
    if sector and sector.lower() not in {"general", "general administration"}:
        parts.append(f"Sector: {sector}")

    # 3. Domain capabilities required
    capabilities = (challenge.get("capabilities_needed") or "").strip()
    if capabilities:
        parts.append(f"Required Capabilities: {capabilities}")

    # 4. Specific skills (filtered for generic tech terms)
    skills = (challenge.get("skills_needed") or challenge.get("skills") or "").strip()
    if skills:
        cleaned_skills = filter_generic_tokens(skills)
        if cleaned_skills:
            parts.append(f"Domain Focus: {', '.join(cleaned_skills)}")

    # 5. KPIs / measurable goals
    kpis = (challenge.get("kpis") or "").strip()
    if kpis:
        parts.append(f"Target Metrics: {kpis}")

    return " . ".join(parts)


def build_startup_search_text(startup: Dict[str, Any]) -> str:
    """
    Constructs a comprehensive semantic profile text for a startup.
    Integrates capabilities, products, technology, domain, and past deployments.
    """
    parts = []

    name = startup.get("display_name") or startup.get("name") or startup.get("legal_name") or ""
    if name:
        parts.append(f"Startup: {name}")

    sector = startup.get("sector") or startup.get("industry") or ""
    if sector:
        parts.append(f"Sector: {sector}")

    desc = startup.get("description") or ""
    if desc:
        parts.append(desc)

    capabilities = startup.get("capabilities") or ""
    if capabilities:
        parts.append(f"Core Capabilities: {capabilities}")

    products = startup.get("products") or ""
    if products:
        parts.append(f"Products: {products}")

    tech = startup.get("technology_tags") or ""
    if tech:
        parts.append(f"Technologies: {tech}")

    deployments = startup.get("past_deployments") or startup.get("achievements") or ""
    if deployments:
        parts.append(f"Proven Deployments: {deployments}")

    tags = startup.get("tags") or ""
    if tags:
        parts.append(f"Domain Tags: {tags}")

    return " . ".join(parts)


def tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric words."""
    if not text:
        return []
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 2]


def filter_generic_tokens(text: str) -> List[str]:
    """
    Splits comma-separated or space-separated capabilities and strips out
    generic technology phrases like 'mobile app', 'ai', 'platform'.
    """
    if not text:
        return []
    raw_items = [item.strip() for item in re.split(r"[,;|\n]+", text) if item.strip()]
    cleaned = []
    for item in raw_items:
        low = item.lower()
        if low in GENERIC_TECH_TERMS:
            continue
        # Also check if it's purely generic words
        tokens = tokenize(low)
        non_generic = [t for t in tokens if t not in GENERIC_TECH_TERMS]
        if non_generic:
            cleaned.append(item)
    return cleaned


def extract_matched_capabilities(challenge_text: str, startup_capabilities_str: str) -> List[str]:
    """
    Identifies specific capabilities declared by the startup that align
    with the government challenge, filtering out generic tech buzzwords.
    """
    if not startup_capabilities_str or not challenge_text:
        return []

    c_text_lower = challenge_text.lower()
    c_tokens = set(tokenize(challenge_text))

    candidates = [c.strip() for c in re.split(r"[,;|\n]+", startup_capabilities_str) if c.strip()]
    matched = []

    for cap in candidates:
        cap_lower = cap.lower()
        if cap_lower in GENERIC_TECH_TERMS:
            continue
        cap_tokens = set(tokenize(cap_lower))
        # Filter generic tech tokens from the capability tokens
        domain_tokens = {t for t in cap_tokens if t not in GENERIC_TECH_TERMS}
        if not domain_tokens:
            continue

        # Check if the phrase or its significant domain tokens appear in the challenge
        if cap_lower in c_text_lower:
            matched.append(cap)
        elif len(domain_tokens & c_tokens) >= 1:
            matched.append(cap)

    return matched[:5]
