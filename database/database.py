import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BASE_DIR)
for p in [BASE_DIR, REPO_ROOT]:
    if p not in sys.path:
        sys.path.insert(0, p)

from models import Base, Startup, Contract, Milestone, GovUser, Feedback, Challenge
from config import DATABASE_URL
import auth

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_demo_data():
    """Populates demo startups from the real data source (startups.json),
    government logins, and sample feedback."""
    db = SessionLocal()
    if db.query(Startup).count() > 0:
        db.close()
        return

    db.close()
    # Import full rich startup registry via the import pipeline
    from scripts.import_startups import import_startups
    import_startups()

    db = SessionLocal()
    # Ensure feedback history exists on the top startups so scores and risk reflect live data
    startups = db.query(Startup).all()
    if startups and db.query(Feedback).count() == 0:
        for s, ratings in zip(startups[:5], [[8.5, 9.0], [8.0, 8.5], [7.5, 8.0], [8.8, 9.2], [7.0]]):
            for r in ratings:
                db.add(Feedback(startup_id=s.id, rating=r, comment="Demonstrated operational milestone delivery."))
        db.commit()

    db.close()
