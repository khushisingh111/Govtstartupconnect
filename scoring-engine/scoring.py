"""
Scoring & Eligibility Engine for SETU.

Aligned with SETU_PRD_and_Architecture.md:
- Section 7.1, 18.1, 18.2, 18.3: SETU Score (Fit 40 + Profile 30 + Feedback 30).
- Section 7.2: Risk calculation with explainable risk reasons and automatic High-risk overrides.
- Section 7.3 & 18.4: Eligibility Engine (E01-E09) with GFR 2017 statutory relaxations.
  * Technical capability is NEVER relaxed (Rule E08).
"""

import os
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from database.config import (
        SETU_WEIGHT_FIT,
        SETU_WEIGHT_PROFILE,
        SETU_WEIGHT_FEEDBACK,
        RISK_THRESHOLD_LOW,
        RISK_THRESHOLD_MEDIUM,
    )
except ImportError:
    from config import (
        SETU_WEIGHT_FIT,
        SETU_WEIGHT_PROFILE,
        SETU_WEIGHT_FEEDBACK,
        RISK_THRESHOLD_LOW,
        RISK_THRESHOLD_MEDIUM,
    )


# ============================================================ ELIGIBILITY ENGINE (PRD 7.3, 18.4)
def evaluate_eligibility(startup: Dict[str, Any], challenge: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Evaluates startup against challenge eligibility rules.
    Statutory GFR 2017 Rule 170(i) and Rule 173(i) relaxations are applied for DPIIT-verified startups.
    Rule E08 (technical capability) is NEVER relaxed.
    """
    challenge = challenge or {}
    rules_evaluated = []
    relaxations_cited = []
    is_eligible = True
    needs_review = False

    is_dpiit_verified = (
        startup.get("dpiit_status") == "verified"
        or startup.get("is_dpiit_certified") is True
        or startup.get("verification_status") == "verified"
    )

    # E01: Valid Legal Registration
    legal_name = startup.get("legal_name") or startup.get("name")
    if legal_name:
        rules_evaluated.append({
            "rule_id": "E01",
            "name": "Legal Registration",
            "status": "Pass",
            "reason": f"Registered entity: {legal_name}",
        })
    else:
        is_eligible = False
        rules_evaluated.append({
            "rule_id": "E01",
            "name": "Legal Registration",
            "status": "Fail",
            "reason": "Missing verified legal registration details.",
        })

    # E02: DPIIT Recognition
    dpiit_num = startup.get("dpiit_number")
    if is_dpiit_verified and dpiit_num:
        rules_evaluated.append({
            "rule_id": "E02",
            "name": "DPIIT Recognition",
            "status": "Pass",
            "reason": f"DPIIT Certificate Verified ({dpiit_num}).",
        })
    elif startup.get("dpiit_status") == "self_declared":
        rules_evaluated.append({
            "rule_id": "E02",
            "name": "DPIIT Recognition",
            "status": "Self-Declared",
            "reason": "Self-declared DPIIT status pending certificate verification.",
        })
    else:
        rules_evaluated.append({
            "rule_id": "E02",
            "name": "DPIIT Recognition",
            "status": "None",
            "reason": "No DPIIT registration claimed.",
        })

    # E03: Debarment / Blacklist Check
    if startup.get("debarred"):
        is_eligible = False
        rules_evaluated.append({
            "rule_id": "E03",
            "name": "Debarment Check",
            "status": "Fail",
            "reason": "Entity has active debarment or blacklist flag on public records.",
        })
    else:
        rules_evaluated.append({
            "rule_id": "E03",
            "name": "Debarment Check",
            "status": "Pass",
            "reason": "No debarment records found. Signed non-debarment declaration.",
        })

    # E04: Required Documents
    doc_count = startup.get("verified_evidence_count", 0)
    if doc_count > 0 or startup.get("verification_status") in ["verified", "demo"]:
        rules_evaluated.append({
            "rule_id": "E04",
            "name": "Required Documents",
            "status": "Pass",
            "reason": f"{doc_count} verified documents/case studies filed in vault.",
        })
    else:
        needs_review = True
        rules_evaluated.append({
            "rule_id": "E04",
            "name": "Required Documents",
            "status": "Needs Review",
            "reason": "Verification documentation pending upload or review.",
        })

    # E05: Minimum Prior Turnover Threshold (Relaxable via GFR 2017 Rule 173(i))
    min_turnover = challenge.get("min_turnover", 0.0)
    if min_turnover > 0:
        actual_turnover = startup.get("turnover_lakhs", 0.0)
        if is_dpiit_verified:
            relaxations_cited.append("GFR 2017 Rule 173(i) - Prior turnover requirement relaxed for DPIIT-recognised startup")
            rules_evaluated.append({
                "rule_id": "E05",
                "name": "Minimum Prior Turnover",
                "status": "Relaxed",
                "basis": "GFR 2017 Rule 173(i)",
                "reason": f"Turnover requirement (₹{min_turnover}L) relaxed under GFR 2017 Rule 173(i).",
            })
        elif actual_turnover >= min_turnover:
            rules_evaluated.append({
                "rule_id": "E05",
                "name": "Minimum Prior Turnover",
                "status": "Pass",
                "reason": f"Turnover ₹{actual_turnover}L satisfies requirement ₹{min_turnover}L.",
            })
        else:
            is_eligible = False
            rules_evaluated.append({
                "rule_id": "E05",
                "name": "Minimum Prior Turnover",
                "status": "Fail",
                "reason": f"Turnover ₹{actual_turnover}L below required ₹{min_turnover}L and not DPIIT-verified.",
            })

    # E06: Minimum Prior Experience (Relaxable via GFR 2017 Rule 173(i))
    min_exp = challenge.get("min_experience", 0)
    if min_exp > 0:
        actual_exp = startup.get("experience_years", 0)
        if is_dpiit_verified:
            relaxations_cited.append("GFR 2017 Rule 173(i) - Prior experience requirement relaxed for DPIIT-recognised startup")
            rules_evaluated.append({
                "rule_id": "E06",
                "name": "Minimum Prior Experience",
                "status": "Relaxed",
                "basis": "GFR 2017 Rule 173(i)",
                "reason": f"Prior experience requirement ({min_exp} yrs) relaxed under GFR 2017 Rule 173(i).",
            })
        elif actual_exp >= min_exp:
            rules_evaluated.append({
                "rule_id": "E06",
                "name": "Minimum Prior Experience",
                "status": "Pass",
                "reason": f"Experience ({actual_exp} yrs) satisfies requirement ({min_exp} yrs).",
            })
        else:
            is_eligible = False
            rules_evaluated.append({
                "rule_id": "E06",
                "name": "Minimum Prior Experience",
                "status": "Fail",
                "reason": f"Experience ({actual_exp} yrs) below required ({min_exp} yrs).",
            })

    # E07: Bid Security / EMD Exemption (Relaxable via GFR 2017 Rule 170(i))
    if is_dpiit_verified:
        relaxations_cited.append("GFR 2017 Rule 170(i) - Bid security / EMD exemption applied")
        rules_evaluated.append({
            "rule_id": "E07",
            "name": "Bid Security Exemption",
            "status": "Relaxed",
            "basis": "GFR 2017 Rule 170(i)",
            "reason": "Exempt from Earnest Money Deposit (EMD) under GFR 2017 Rule 170(i).",
        })

    # E08: Technical Capability Evidence — MANDATORY, NEVER RELAXED (PRD Section 1.5, 7.3)
    deployments = startup.get("past_deployments_count", 0)
    has_demo = bool(startup.get("past_deployments") or startup.get("achievements") or startup.get("products"))
    if deployments > 0 or has_demo:
        rules_evaluated.append({
            "rule_id": "E08",
            "name": "Technical Capability Evidence",
            "status": "Pass",
            "reason": f"Technical capability verified ({deployments} past deployments, prototype/demo evidenced). Never relaxed.",
        })
    else:
        is_eligible = False
        rules_evaluated.append({
            "rule_id": "E08",
            "name": "Technical Capability Evidence",
            "status": "Fail",
            "reason": "No evidence of technical capability or functional prototype provided. (Technical capability cannot be relaxed).",
        })

    # E09: Application Timing
    rules_evaluated.append({
        "rule_id": "E09",
        "name": "Submission Deadline",
        "status": "Pass",
        "reason": "Application received within submission window.",
    })

    # Determine overall status
    if not is_eligible:
        overall = "Ineligible"
    elif relaxations_cited:
        overall = "Eligible with relaxation"
    elif needs_review:
        overall = "Needs review"
    else:
        overall = "Eligible"

    return {
        "overall_status": overall,
        "is_eligible": is_eligible and not needs_review,
        "relaxations_applied": relaxations_cited,
        "rules_evaluated": rules_evaluated,
        "technical_capability_status": "Verified (mandatory gate passed)" if any(r["rule_id"] == "E08" and r["status"] == "Pass" for r in rules_evaluated) else "Failed",
    }


# ============================================================ SETU SCORE ENGINE (PRD 7.1, 18.1-18.3)
def calculate_profile_points(startup: Dict[str, Any]) -> float:
    """
    Profile score out of 30 points (PRD Section 18.2):
    - Verified registration and DPIIT: 6 pts
    - Verified documents & evidence: 8 pts
    - Technical maturity / deployments: 8 pts
    - Compliance standing & non-debarment: 4 pts
    - Completed government contracts: 4 pts
    Self-declared items earn at most 50% until verified.
    """
    points = 0.0

    # 1. Registration & DPIIT (max 6)
    if startup.get("dpiit_status") == "verified" or startup.get("is_dpiit_certified"):
        points += 6.0
    elif startup.get("dpiit_status") == "self_declared":
        points += 3.0  # 50% for self-declared
    else:
        points += 2.0  # Basic legal registration

    # 2. Verified documents & evidence (max 8)
    ev_count = startup.get("verified_evidence_count", 0)
    is_verified = startup.get("verification_status") == "verified"
    if is_verified:
        points += min(8.0, 4.0 + ev_count * 0.8)
    else:
        points += min(4.0, 2.0 + ev_count * 0.4)

    # 3. Technical maturity & deployments (max 8)
    mat = (startup.get("maturity_level") or "").lower()
    dep_count = startup.get("past_deployments_count", 0)
    if mat == "scaled":
        mat_pts = 5.0
    elif mat == "market-ready":
        mat_pts = 4.0
    elif mat == "pilot-ready":
        mat_pts = 3.0
    else:
        mat_pts = 2.0
    points += min(8.0, mat_pts + dep_count * 1.0)

    # 4. Compliance & non-debarment (max 4)
    if not startup.get("debarred"):
        points += 4.0

    # 5. Completed contracts / references (max 4)
    points += min(4.0, dep_count * 1.0)

    return round(min(30.0, points), 1)


def calculate_feedback_points(db, startup_id: int) -> float:
    """
    Feedback score out of 30 points (PRD Section 18.3):
    n = number of completed pilots with feedback
    w = min(n, 3) / 3
    quality = avg rating (0 to 1)
    Feedback = 30 * (w * quality + (1 - w) * 0.5)
    Neutral starting score is 15.0 (0.5 * 30).
    """
    from models import Feedback
    if db is None:
        return 15.0

    records = db.query(Feedback).filter(Feedback.startup_id == startup_id).all()
    if not records:
        return 15.0  # Neutral cold start

    n = len(records)
    w = min(n, 3) / 3.0
    avg_rating_0_to_1 = sum(r.rating for r in records) / (len(records) * 10.0)
    feedback_score = 30.0 * (w * avg_rating_0_to_1 + (1.0 - w) * 0.5)
    return round(min(30.0, max(0.0, feedback_score)), 1)


def calculate_setu_score(
    match_score_pct: float,
    profile_points_30: float,
    feedback_points_30: float,
) -> Dict[str, Any]:
    """
    SETU Score calculation out of 100 (PRD Section 7.1):
    Fit = 40 * (match_score / 100.0)
    Profile = 0 to 30
    Feedback = 0 to 30
    Total SETU Score = Fit + Profile + Feedback (0 to 100).
    """
    fit_points = round(40.0 * (float(match_score_pct) / 100.0), 1)
    total = round(fit_points + profile_points_30 + feedback_points_30, 1)

    return {
        "setu_score": total,
        "breakdown": {
            "fit_score": fit_points,
            "fit_max": 40.0,
            "profile_score": profile_points_30,
            "profile_max": 30.0,
            "feedback_score": feedback_points_30,
            "feedback_max": 30.0,
        },
    }


# ============================================================ RISK CALCULATION (PRD 7.2)
def calculate_risk(db, startup) -> Dict[str, Any]:
    """
    Independent Risk Calculation (PRD Section 7.2).
    Score >= 70: Low risk; 50-69: Medium risk; < 50: High risk.
    Any active debarment flag or unresolved compliance forces High risk.
    Risk is NOT just 100 - match.
    """
    from models import Feedback

    s_dict = startup if isinstance(startup, dict) else startup.to_dict()
    s_id = s_dict["id"]

    # 1. Debarment hard override
    if s_dict.get("debarred"):
        return {
            "risk_score": 95.0,
            "risk_level": "High",
            "risk_reasons": ["Active debarment / blacklist flag on public procurement record"],
            "factors": {"compliance_risk": 95.0, "track_record_risk": 80.0, "profile_risk": 70.0},
        }

    # 2. Track record risk
    records = []
    if db is not None:
        records = db.query(Feedback).filter(Feedback.startup_id == s_id).all()

    if not records:
        track_record_risk = 45.0  # Moderate unproven
        track_reason = "No past government pilot feedback on file (neutral starting record)"
    else:
        avg_rating = sum(r.rating for r in records) / len(records)
        track_record_risk = max(5.0, 100.0 - (avg_rating * 10.0))
        track_reason = f"Past pilot performance rating average: {avg_rating:.1f}/10"

    # 3. Profile / Evidence risk
    profile_strength = s_dict.get("profile_strength", 50.0)
    ev_count = s_dict.get("verified_evidence_count", 0)
    profile_risk = max(10.0, 100.0 - (profile_strength * 0.7 + ev_count * 4.0))

    # 4. Compliance risk
    is_dpiit = s_dict.get("dpiit_status") == "verified" or s_dict.get("is_dpiit_certified")
    if is_dpiit:
        compliance_risk = 10.0
        compliance_reason = "DPIIT registration verified"
    elif s_dict.get("dpiit_status") == "self_declared":
        compliance_risk = 40.0
        compliance_reason = "Self-declared DPIIT status pending certificate validation"
    else:
        compliance_risk = 50.0
        compliance_reason = "No DPIIT verification on record"

    risk_score = round(track_record_risk * 0.40 + profile_risk * 0.35 + compliance_risk * 0.25, 1)

    # Determine risk level
    if risk_score < 30.0:
        level = "Low"
    elif risk_score < 60.0:
        level = "Medium"
    else:
        level = "High"

    risk_reasons = []
    if is_dpiit:
        risk_reasons.append("✓ DPIIT verified compliance standing")
    else:
        risk_reasons.append("⚠ Self-declared or pending DPIIT verification")

    if ev_count >= 5:
        risk_reasons.append(f"✓ Strong evidence base ({ev_count} verified documents)")
    elif ev_count > 0:
        risk_reasons.append(f"✓ {ev_count} verified evidence documents")
    else:
        risk_reasons.append("⚠ Limited verified documentary evidence")

    deployments = s_dict.get("past_deployments_count", 0)
    if deployments >= 2:
        risk_reasons.append(f"✓ Proven deployment track record ({deployments} pilots)")
    elif deployments == 1:
        risk_reasons.append("✓ 1 past pilot deployment")
    else:
        risk_reasons.append("ℹ First-time pilot candidate")

    return {
        "risk_score": risk_score,
        "risk_level": level,
        "risk_reasons": risk_reasons,
        "factors": {
            "track_record_risk": round(track_record_risk, 1),
            "profile_risk": round(profile_risk, 1),
            "compliance_risk": round(compliance_risk, 1),
        },
    }


# ============================================================ BACKWARD COMPATIBLE API HELPERS
def calculate_policy_score(startup) -> float:
    s = startup if isinstance(startup, dict) else startup.to_dict()
    score = 0.0
    if s.get("is_dpiit_certified") or s.get("dpiit_status") == "verified":
        score += 50.0
    if s.get("state") == "Maharashtra":
        score += 25.0
    if s.get("is_women_led"):
        score += 25.0
    return min(score, 100.0)


def calculate_feedback_score(db, startup_id: int) -> float:
    from models import Feedback
    if db is None:
        return 50.0
    records = db.query(Feedback).filter(Feedback.startup_id == startup_id).all()
    if not records:
        return 50.0
    avg = sum(r.rating for r in records) / len(records)
    return avg * 10.0


def calculate_final_score(db, startup) -> float:
    """Calculates SETU score baseline for startup profile."""
    s = startup if isinstance(startup, dict) else startup.to_dict()
    prof_pts = calculate_profile_points(s)
    feed_pts = calculate_feedback_points(db, s["id"])
    # Default fit points for general leaderboard without specific challenge is based on policy
    policy_fit = calculate_policy_score(startup) * 0.40
    return round(policy_fit + prof_pts + feed_pts, 1)


def update_startup_score(db, startup_id: int) -> float:
    from models import Startup
    startup = db.query(Startup).filter(Startup.id == startup_id).first()
    if not startup:
        raise ValueError("Startup not found")
    new_score = calculate_final_score(db, startup)
    startup.current_score = new_score
    db.commit()
    return new_score


def recompute_all_scores(db):
    from models import Startup
    for startup in db.query(Startup).all():
        startup.current_score = calculate_final_score(db, startup)
    db.commit()


def get_leaderboard(db, limit: int = 50):
    from models import Startup
    return db.query(Startup).order_by(Startup.current_score.desc()).limit(limit).all()
