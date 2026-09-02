"""
Scoring & Leaderboard module.

Pure scoring logic — no web framework here on purpose, so this can be
unit-tested or swapped independently of how it's served (core-apis wraps it).
"""

WEIGHT_POLICY = 0.40
WEIGHT_PROFILE = 0.30
WEIGHT_FEEDBACK = 0.30


def calculate_policy_score(startup) -> float:
    """Policy alignment score, out of 100. Explainable on purpose — no black box."""
    score = 0
    if startup.is_dpiit_certified:
        score += 50
    if startup.state == "Maharashtra":
        score += 25
    if startup.is_women_led:
        score += 25
    return min(score, 100)


def calculate_feedback_score(db, startup_id: int) -> float:
    """Average past feedback rating (out of 10), converted to a 0-100 scale."""
    from models import Feedback
    records = db.query(Feedback).filter(Feedback.startup_id == startup_id).all()
    if not records:
        return 50.0  # neutral default for startups with no pilot history yet
    avg_rating = sum(r.rating for r in records) / len(records)
    return avg_rating * 10


def calculate_final_score(db, startup) -> float:
    policy_score = calculate_policy_score(startup)
    profile_score = startup.profile_strength
    feedback_score = calculate_feedback_score(db, startup.id)

    final_score = (
        policy_score * WEIGHT_POLICY
        + profile_score * WEIGHT_PROFILE
        + feedback_score * WEIGHT_FEEDBACK
    )
    return round(final_score, 2)


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
    """Called once at startup so demo data has scores immediately."""
    from models import Startup
    for startup in db.query(Startup).all():
        startup.current_score = calculate_final_score(db, startup)
    db.commit()


def get_leaderboard(db, limit: int = 20):
    from models import Startup
    return (
        db.query(Startup)
        .order_by(Startup.current_score.desc())
        .limit(limit)
        .all()
    )


def calculate_risk(db, startup) -> dict:
    """
    Pilot-risk estimate for a startup, on a 0-100 scale (higher = riskier).
    Explainable by design: three visible factors, no hidden model.
    """
    from models import Feedback

    # 1. Track record: no pilot history yet is inherently riskier than a proven one
    records = db.query(Feedback).filter(Feedback.startup_id == startup.id).all()
    if not records:
        track_record_risk = 60  # unproven — moderate-high risk by default
    else:
        avg_rating = sum(r.rating for r in records) / len(records)
        track_record_risk = max(0, 100 - (avg_rating * 10))

    # 2. Profile completeness: thin profiles carry more execution risk
    profile_risk = max(0, 100 - startup.profile_strength)

    # 3. Compliance standing: DPIIT recognition lowers procedural/legal risk
    compliance_risk = 0 if startup.is_dpiit_certified else 40

    risk_score = round(
        track_record_risk * 0.5 + profile_risk * 0.3 + compliance_risk * 0.2, 1
    )

    if risk_score < 30:
        level = "Low"
    elif risk_score < 60:
        level = "Medium"
    else:
        level = "High"

    return {
        "risk_score": risk_score,
        "risk_level": level,
        "factors": {
            "track_record_risk": round(track_record_risk, 1),
            "profile_risk": round(profile_risk, 1),
            "compliance_risk": compliance_risk,
        },
    }
