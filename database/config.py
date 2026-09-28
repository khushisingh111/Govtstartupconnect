"""
SETU Platform Configuration & Business Rules.

"Rules are data" — PRD Section 1.5, 7.1, 7.2, 18.1.
Scoring weights, matching weights, thresholds, and generic technology filter lists
are defined here as configurable parameters rather than hardcoded throughout code.
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BASE_DIR)
DEFAULT_DB_PATH = os.path.join(REPO_ROOT, "core-apis", "setu.db").replace("\\", "/")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# Matching Engine Weights (PRD 18.1 & User Specification)
MATCHING_SEMANTIC_WEIGHT = float(os.getenv("MATCHING_SEMANTIC_WEIGHT", "0.70"))
MATCHING_CAPABILITY_WEIGHT = float(os.getenv("MATCHING_CAPABILITY_WEIGHT", "0.20"))
MATCHING_SECTOR_WEIGHT = float(os.getenv("MATCHING_SECTOR_WEIGHT", "0.10"))

# SBERT Model Configuration
SBERT_MODEL_NAME = os.getenv("SBERT_MODEL_NAME", "all-MiniLM-L6-v2")

# SETU Score Weights (PRD Section 7.1: Fit = 40, Profile = 30, Feedback = 30)
SETU_WEIGHT_FIT = float(os.getenv("SETU_WEIGHT_FIT", "0.40"))
SETU_WEIGHT_PROFILE = float(os.getenv("SETU_WEIGHT_PROFILE", "0.30"))
SETU_WEIGHT_FEEDBACK = float(os.getenv("SETU_WEIGHT_FEEDBACK", "0.30"))

# Risk Thresholds (PRD Section 7.2)
# Score >= 70: Low risk; 50 <= Score < 70: Medium risk; Score < 50: High risk
RISK_THRESHOLD_LOW = float(os.getenv("RISK_THRESHOLD_LOW", "70.0"))
RISK_THRESHOLD_MEDIUM = float(os.getenv("RISK_THRESHOLD_MEDIUM", "50.0"))

# Generic technology stop words / low-signal terms that must NOT dominate semantic matching
# (Prevents healthcare/education apps from falsely matching electricity challenges)
GENERIC_TECH_TERMS = {
    "app", "apps", "mobile", "mobile app", "mobile application", "application",
    "software", "platform", "dashboard", "tool", "solution", "system",
    "ai", "artificial intelligence", "ml", "machine learning", "portal",
    "website", "web app", "digital", "tech", "technology", "interface"
}

# Domain Sectors Taxonomy
SECTOR_TAXONOMY = [
    "Energy / Utilities",
    "Municipal Infrastructure & Waste",
    "Water & Sanitation",
    "Public Health & Healthcare",
    "Urban Transport & Mobility",
    "Education & Skilling",
    "Agriculture & Rural Development",
    "Disaster Management & Safety",
]
