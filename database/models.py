"""
SETU Database Models (SQLAlchemy ORM).

Aligned with SETU_PRD_and_Architecture.md:
Section 17 (Data Model) & Section 6.3 (Startup Registry).
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Startup(Base):
    __tablename__ = "startups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    legal_name = Column(String, nullable=True)
    display_name = Column(String, nullable=True)
    name = Column(String, nullable=False)  # Kept for backward compatibility
    email = Column(String, unique=True, nullable=True)
    password_hash = Column(String, nullable=True)

    # Rich descriptive profile fields
    description = Column(Text, default="")
    capabilities = Column(Text, default="")         # Comma-separated or narrative capabilities
    products = Column(Text, default="")             # Offered products/solutions
    technology_tags = Column(Text, default="")      # Technologies used
    tags = Column(Text, default="")                 # Comma-separated tags (backward compatible)
    achievements = Column(Text, default="")

    # Categorization
    industry = Column(String, default="")
    sector = Column(String, default="")
    maturity_level = Column(String, default="Pilot-Ready")  # Prototype, Pilot-Ready, Market-Ready, Scaled

    # Location
    location = Column(String, default="")
    state = Column(String, default="Maharashtra")
    city = Column(String, default="")

    # Track record & DPIIT
    past_deployments = Column(Text, default="")
    past_deployments_count = Column(Integer, default=0)
    dpiit_status = Column(String, default="self_declared")  # "verified", "self_declared", "none"
    dpiit_number = Column(String, nullable=True)
    is_dpiit_certified = Column(Boolean, default=False)
    is_women_led = Column(Boolean, default=False)

    # Verification & Evidence
    verification_status = Column(String, default="pending")  # "verified", "pending", "rejected", "demo"
    verified_evidence_count = Column(Integer, default=0)
    profile_strength = Column(Float, default=50.0)           # 0-100 score
    current_score = Column(Float, default=0.0)              # SETU Score (Fit 40 + Profile 30 + Feedback 30)

    # Procurement & Eligibility attributes
    debarred = Column(Boolean, default=False)                # Blacklist check (Rule E03)
    turnover_lakhs = Column(Float, default=0.0)              # Prior annual turnover (Rule E05)
    experience_years = Column(Integer, default=0)            # Prior operational experience (Rule E06)
    source = Column(String, default="system_seed")           # "csv_import", "dpiit_adapter", "system_seed"
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "startup_id": self.id,
            "legal_name": self.legal_name or self.name,
            "display_name": self.display_name or self.name,
            "name": self.name,
            "email": self.email,
            "description": self.description,
            "capabilities": self.capabilities,
            "products": self.products,
            "technology_tags": self.technology_tags,
            "tags": self.tags,
            "industry": self.industry,
            "sector": self.sector,
            "maturity_level": self.maturity_level,
            "location": self.location or f"{self.city}, {self.state}".strip(", "),
            "state": self.state,
            "city": self.city,
            "past_deployments": self.past_deployments,
            "past_deployments_count": self.past_deployments_count,
            "dpiit_status": self.dpiit_status,
            "dpiit_number": self.dpiit_number,
            "is_dpiit_certified": self.is_dpiit_certified,
            "is_women_led": self.is_women_led,
            "verification_status": self.verification_status,
            "verified_evidence_count": self.verified_evidence_count,
            "profile_strength": self.profile_strength,
            "current_score": self.current_score,
            "debarred": self.debarred,
            "turnover_lakhs": self.turnover_lakhs,
            "experience_years": self.experience_years,
            "source": self.source,
        }


class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    problem_context = Column(Text, default="")
    current_baseline = Column(Text, default="")
    desired_outcome = Column(Text, default="")
    kpis = Column(Text, default="")
    budget_min = Column(Float, default=5.0)
    budget_max = Column(Float, default=25.0)
    budget_lakh = Column(Float, default=25.0)
    timeline = Column(String, default="3-6 months")
    department = Column(String, default="General Administration")
    sector = Column(String, default="General")
    geography = Column(String, default="Maharashtra")
    data_classification = Column(String, default="Internal")
    capabilities_needed = Column(Text, default="")
    skills_needed = Column(Text, default="")
    status = Column(String, default="Published")
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "problem_context": self.problem_context,
            "current_baseline": self.current_baseline,
            "desired_outcome": self.desired_outcome,
            "kpis": self.kpis,
            "budget_lakh": self.budget_lakh,
            "timeline": self.timeline,
            "department": self.department,
            "sector": self.sector,
            "geography": self.geography,
            "data_classification": self.data_classification,
            "capabilities_needed": self.capabilities_needed,
            "skills_needed": self.skills_needed,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else "",
        }


class GovUser(Base):
    __tablename__ = "gov_users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    department = Column(String, default="")


class Session(Base):
    __tablename__ = "sessions"
    token = Column(String, primary_key=True)
    user_type = Column(String)     # "startup" or "gov"
    user_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, autoincrement=True)
    startup_id = Column(Integer, ForeignKey("startups.id"))
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=True)
    rating = Column(Float)                         # out of 10
    comment = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class Contract(Base):
    __tablename__ = "contracts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    startup_id = Column(Integer, ForeignKey("startups.id"))
    problem_title = Column(String, default="")
    department = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class Milestone(Base):
    __tablename__ = "milestones"
    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"))
    milestone_number = Column(Integer)             # 1-4
    scope = Column(Text, default="")
    funds_allocated = Column(Float, default=0.0)
    status = Column(String, default="planned")     # planned / in_progress / delivered / paid
    evidence_url = Column(String, nullable=True)
    payment_reference = Column(String, nullable=True)
    due_date = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
