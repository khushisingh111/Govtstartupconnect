from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Startup(Base):
    __tablename__ = "startups"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    password_hash = Column(String, nullable=True)
    tags = Column(Text, default="")              # comma-separated skills/domain tags
    achievements = Column(Text, default="")
    is_dpiit_certified = Column(Boolean, default=False)
    state = Column(String, default="")
    is_women_led = Column(Boolean, default=False)
    verification_status = Column(String, default="pending")
    profile_strength = Column(Float, default=50.0)   # 0-100, derived from achievements length/quality
    current_score = Column(Float, default=0.0)


class GovUser(Base):
    __tablename__ = "gov_users"
    id = Column(Integer, primary_key=True)
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
    id = Column(Integer, primary_key=True)
    startup_id = Column(Integer, ForeignKey("startups.id"))
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=True)
    rating = Column(Float)                         # out of 10
    created_at = Column(DateTime, default=datetime.utcnow)


class Contract(Base):
    __tablename__ = "contracts"
    id = Column(Integer, primary_key=True)
    startup_id = Column(Integer, ForeignKey("startups.id"))
    problem_title = Column(String, default="")
    department = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class Milestone(Base):
    __tablename__ = "milestones"
    id = Column(Integer, primary_key=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"))
    milestone_number = Column(Integer)             # 1-4
    scope = Column(Text, default="")
    funds_allocated = Column(Float, default=0.0)
    status = Column(String, default="planned")     # planned / in_progress / delivered / paid
