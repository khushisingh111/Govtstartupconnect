"""
Core APIs.

This is the only module that imports the others — scoring-engine,
matching-nlp, contracts-finance, and database all sit as sibling folders,
and this file wires them together behind one set of endpoints, exactly as
laid out in docs/team-build-plan.md.
"""

import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BASE_DIR)
for folder in ["database", "scoring-engine", "matching-nlp", "contracts-finance"]:
    sys.path.insert(0, os.path.join(REPO_ROOT, folder))

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import init_db, get_db, seed_demo_data, SessionLocal
from models import Startup, Feedback, GovUser, Contract
import scoring
import matching
import contracts
import auth

app = FastAPI(title="SETU Core APIs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    init_db()
    seed_demo_data()
    db = SessionLocal()
    scoring.recompute_all_scores(db)
    db.close()


# ---------------------------------------------------------------- Schemas
class ProblemIn(BaseModel):
    title: str
    department: str
    skills_needed: str = ""
    problem_context: str = ""
    desired_outcome: str = ""
    capabilities_needed: str = ""
    kpis: str = ""
    sector: str = ""
    geography: str = "Maharashtra"
    budget_lakh: float = 25.0


class StartupRegisterIn(BaseModel):
    name: str
    email: str
    password: str
    tags: str
    achievements: str = ""
    is_dpiit_certified: bool = False
    is_women_led: bool = False
    state: str = "Maharashtra"


class GovRegisterIn(BaseModel):
    name: str
    email: str
    password: str
    department: str


class LoginIn(BaseModel):
    email: str
    password: str


class FeedbackIn(BaseModel):
    startup_id: int
    contract_id: Optional[int] = None
    rating: float
    comment: str = ""


class MilestoneUpdateIn(BaseModel):
    status: str


class ContractIn(BaseModel):
    startup_id: int
    problem_title: str
    department: str
    budget_lakh: float


# ---------------------------------------------------------------- Auth helpers
def get_current_session(db: Session, authorization: Optional[str]):
    """Reads 'Bearer <token>' from the Authorization header and resolves it
    to a session. Returns None if missing/invalid — callers decide whether
    that's fatal for their endpoint."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    return auth.get_session(db, token)


def require_session(db: Session, authorization: Optional[str]):
    session = get_current_session(db, authorization)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated. Please log in.")
    return session


# ---------------------------------------------------------------- Health
@app.get("/api/health")
def health():
    # Do not make health checks depend on model download. Report configured model
    # and whether the semantic engine package is available.
    try:
        from semantic_matcher import get_model
        model = get_model()
        engine = "SBERT" if model != "TF_IDF_FALLBACK" and hasattr(model, "encode") else "TF-IDF fallback"
    except Exception:
        engine = "unavailable"
    return {
        "status": "SETU core-apis running",
        "matching_engine": engine,
        "model": os.getenv("SBERT_MODEL_NAME", "all-MiniLM-L6-v2"),
    }


# ---------------------------------------------------------------- Auth: Startup
@app.post("/api/auth/startup/register")
def register_startup(payload: StartupRegisterIn, db: Session = Depends(get_db)):
    existing = db.query(Startup).filter(Startup.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    profile_strength = min(100, 40 + len(payload.achievements) // 4)
    startup = Startup(
        name=payload.name,
        email=payload.email,
        password_hash=auth.hash_password(payload.password),
        tags=payload.tags,
        achievements=payload.achievements,
        is_dpiit_certified=payload.is_dpiit_certified,
        is_women_led=payload.is_women_led,
        state=payload.state,
        profile_strength=profile_strength,
        verification_status="pending",
    )
    db.add(startup)
    db.commit()
    db.refresh(startup)
    scoring.update_startup_score(db, startup.id)

    token = auth.create_session(db, "startup", startup.id)
    return {"token": token, "startup_id": startup.id, "name": startup.name}


@app.post("/api/auth/startup/login")
def login_startup(payload: LoginIn, db: Session = Depends(get_db)):
    startup = db.query(Startup).filter(Startup.email == payload.email).first()
    if not startup or not startup.password_hash or not auth.verify_password(payload.password, startup.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    token = auth.create_session(db, "startup", startup.id)
    return {"token": token, "startup_id": startup.id, "name": startup.name}


# ---------------------------------------------------------------- Auth: Government
@app.post("/api/auth/gov/register")
def register_gov(payload: GovRegisterIn, db: Session = Depends(get_db)):
    existing = db.query(GovUser).filter(GovUser.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")
    gov = GovUser(
        name=payload.name,
        email=payload.email,
        password_hash=auth.hash_password(payload.password),
        department=payload.department,
    )
    db.add(gov)
    db.commit()
    db.refresh(gov)
    token = auth.create_session(db, "gov", gov.id)
    return {"token": token, "gov_id": gov.id, "name": gov.name, "department": gov.department}


@app.post("/api/auth/gov/login")
def login_gov(payload: LoginIn, db: Session = Depends(get_db)):
    gov = db.query(GovUser).filter(GovUser.email == payload.email).first()
    if not gov or not auth.verify_password(payload.password, gov.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    token = auth.create_session(db, "gov", gov.id)
    return {"token": token, "gov_id": gov.id, "name": gov.name, "department": gov.department}


@app.post("/api/auth/logout")
def logout(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if authorization and authorization.startswith("Bearer "):
        auth.revoke_session(db, authorization.removeprefix("Bearer ").strip())
    return {"message": "logged out"}


# ---------------------------------------------------------------- Startups / Profiles
@app.get("/api/startups/{startup_id}/score")
def get_score(startup_id: int, db: Session = Depends(get_db)):
    startup = db.query(Startup).filter(Startup.id == startup_id).first()
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    return {
        "startup_id": startup.id,
        "name": startup.name,
        "score": startup.current_score,
        "breakdown": {
            "policy_score": scoring.calculate_policy_score(startup),
            "profile_score": startup.profile_strength,
            "feedback_score": scoring.calculate_feedback_score(db, startup.id),
        },
        "risk": scoring.calculate_risk(db, startup),
    }


@app.get("/api/startups/{startup_id}/profile")
def get_profile(startup_id: int, db: Session = Depends(get_db)):
    """Full public profile — used for the startup profile page and for
    a government user reviewing a matched startup before selecting them."""
    startup = db.query(Startup).filter(Startup.id == startup_id).first()
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")

    feedback_history = (
        db.query(Feedback)
        .filter(Feedback.startup_id == startup_id)
        .order_by(Feedback.created_at.desc())
        .all()
    )
    contracts_list = db.query(Contract).filter(Contract.startup_id == startup_id).all()

    return {
        "startup_id": startup.id,
        "name": startup.name,
        "legal_name": startup.legal_name,
        "description": startup.description,
        "capabilities": startup.capabilities,
        "products": startup.products,
        "technology_tags": startup.technology_tags,
        "tags": startup.tags,
        "achievements": startup.achievements,
        "past_deployments": startup.past_deployments,
        "past_deployments_count": startup.past_deployments_count,
        "sector": startup.sector,
        "industry": startup.industry,
        "maturity_level": startup.maturity_level,
        "location": startup.location,
        "city": startup.city,
        "state": startup.state,
        "dpiit_status": startup.dpiit_status,
        "dpiit_number": startup.dpiit_number,
        "is_dpiit_certified": startup.is_dpiit_certified,
        "is_women_led": startup.is_women_led,
        "verification_status": startup.verification_status,
        "verified_evidence_count": startup.verified_evidence_count,
        "source": startup.source,
        "score": startup.current_score,
        "risk": scoring.calculate_risk(db, startup),
        "feedback_count": len(feedback_history),
        "feedback_history": [
            {"rating": f.rating, "date": f.created_at.strftime("%Y-%m-%d")}
            for f in feedback_history
        ],
        "past_contracts": len(contracts_list),
    }


@app.get("/api/leaderboard")
def leaderboard(limit: int = 20, db: Session = Depends(get_db)):
    top = scoring.get_leaderboard(db, limit)
    return [
        {
            "startup_id": s.id,
            "name": s.name,
            "state": s.state,
            "tags": s.tags,
            "is_dpiit_certified": s.is_dpiit_certified,
            "verification_status": s.verification_status,
            "score": s.current_score,
            "risk_level": scoring.calculate_risk(db, s)["risk_level"],
        }
        for s in top
    ]


# ---------------------------------------------------------------- AI Matching (+ risk)
@app.post("/api/match-startups")
def match_startups(payload: ProblemIn, db: Session = Depends(get_db)):
    """Problem-first semantic discovery. The complete challenge is sent to the
    matcher; generic terms such as 'mobile app' cannot replace the domain need."""
    all_startups = db.query(Startup).all()
    challenge = {
        "title": payload.title,
        "department": payload.department,
        "problem_context": payload.problem_context,
        "desired_outcome": payload.desired_outcome,
        "capabilities_needed": payload.capabilities_needed,
        "skills_needed": payload.skills_needed,
        "kpis": payload.kpis,
        "sector": payload.sector or payload.department,
        "geography": payload.geography,
    }
    ranked = matching.match_challenge_comprehensive(challenge, all_startups, top_n=20)

    by_id = {s.id: s for s in all_startups}
    for r in ranked:
        startup = by_id.get(r["startup_id"])
        if startup:
            risk = scoring.calculate_risk(db, startup)
            r["risk_level"] = risk["risk_level"]
            r["risk_score"] = risk["risk_score"]
            r["verification_status"] = startup.verification_status
            r["setu_score"] = startup.current_score

    return {
        "problem": payload.title,
        "matching_method": "SBERT semantic + capability + sector hybrid",
        "matches": ranked,
    }


# ---------------------------------------------------------------- Feedback
@app.post("/api/feedback")
def submit_feedback(payload: FeedbackIn, db: Session = Depends(get_db)):
    fb = Feedback(startup_id=payload.startup_id, contract_id=payload.contract_id, rating=payload.rating)
    db.add(fb)
    db.commit()
    new_score = scoring.update_startup_score(db, payload.startup_id)
    return {"message": "feedback recorded", "updated_score": new_score}


@app.get("/api/feedback/{startup_id}")
def list_feedback(startup_id: int, db: Session = Depends(get_db)):
    records = (
        db.query(Feedback)
        .filter(Feedback.startup_id == startup_id)
        .order_by(Feedback.created_at.desc())
        .all()
    )
    return [{"rating": f.rating, "date": f.created_at.strftime("%Y-%m-%d")} for f in records]


# ---------------------------------------------------------------- Finance / Contracts
@app.post("/api/contracts")
def create_contract(payload: ContractIn, db: Session = Depends(get_db)):
    contract = contracts.create_contract(
        db, payload.startup_id, payload.problem_title, payload.department, payload.budget_lakh
    )
    return {"contract_id": contract.id}


@app.get("/api/contracts/{contract_id}")
def get_contract(contract_id: int, db: Session = Depends(get_db)):
    data = contracts.get_contract_with_milestones(db, contract_id)
    if not data:
        raise HTTPException(status_code=404, detail="Contract not found")
    return {
        "contract_id": data["contract"].id,
        "problem_title": data["contract"].problem_title,
        "department": data["contract"].department,
        "milestones": [
            {
                "milestone_number": m.milestone_number,
                "scope": m.scope,
                "funds_allocated": m.funds_allocated,
                "status": m.status,
            }
            for m in data["milestones"]
        ],
    }


@app.get("/api/startups/{startup_id}/contracts")
def get_startup_contracts(startup_id: int, db: Session = Depends(get_db)):
    rows = db.query(Contract).filter(Contract.startup_id == startup_id).all()
    result = []
    for c in rows:
        data = contracts.get_contract_with_milestones(db, c.id)
        result.append({
            "contract_id": c.id,
            "problem_title": c.problem_title,
            "department": c.department,
            "milestones": [
                {
                    "milestone_number": m.milestone_number,
                    "scope": m.scope,
                    "funds_allocated": m.funds_allocated,
                    "status": m.status,
                }
                for m in data["milestones"]
            ],
        })
    return result


@app.put("/api/contracts/{contract_id}/milestone/{milestone_number}")
def update_milestone(contract_id: int, milestone_number: int, payload: MilestoneUpdateIn, db: Session = Depends(get_db)):
    try:
        milestone = contracts.advance_milestone(db, contract_id, milestone_number, payload.status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"milestone_number": milestone.milestone_number, "status": milestone.status}


# ---------------------------------------------------------------- Frontend
frontend_dir = os.path.join(REPO_ROOT, "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
