from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Startup, Contract, Milestone, GovUser, Feedback
import auth

# SQLite for the demo/prototype. Swap this one line for Postgres later:
# DATABASE_URL = "postgresql://user:password@localhost:5432/setu"
DATABASE_URL = "sqlite:///./setu.db"

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
    """Populates demo startups, a demo government login, and some feedback
    history so the leaderboard/risk numbers aren't flat on first run."""
    db = SessionLocal()
    if db.query(Startup).count() > 0:
        db.close()
        return

    demo_startups = [
        dict(name="Trafica Systems", email="contact@trafica.demo", tags="computer vision, IoT, traffic sensors, analytics",
             achievements="Piloted adaptive signal control for 6 junctions in Pune Smart City, 2024.",
             is_dpiit_certified=True, state="Maharashtra", is_women_led=False, profile_strength=78, verification_status="verified"),
        dict(name="AquaSense Labs", email="contact@aquasense.demo", tags="water quality, IoT sensors, sanitation, analytics",
             achievements="Deployed leak-detection sensors across 3 municipal wards.",
             is_dpiit_certified=True, state="Maharashtra", is_women_led=True, profile_strength=70, verification_status="verified"),
        dict(name="MediReach", email="contact@medireach.demo", tags="telemedicine, mobile app, rural health, NLP",
             achievements="Ran teleconsultation pilots in 2 primary health centres.",
             is_dpiit_certified=True, state="Karnataka", is_women_led=True, profile_strength=82, verification_status="verified"),
        dict(name="AgroYield AI", email="contact@agroyield.demo", tags="agriculture, satellite imagery, crop analytics, mobile app",
             achievements="Yield prediction model validated on 400 acres in Nashik.",
             is_dpiit_certified=False, state="Maharashtra", is_women_led=False, profile_strength=60, verification_status="pending"),
        dict(name="EduSpark", email="contact@eduspark.demo", tags="education, mobile app, NLP, learning analytics",
             achievements="Adaptive learning app used by 5 government schools.",
             is_dpiit_certified=True, state="Delhi", is_women_led=False, profile_strength=65, verification_status="verified"),
        dict(name="CleanGrid Robotics", email="contact@cleangrid.demo", tags="waste management, robotics, IoT sensors",
             achievements="Automated waste-sorting unit piloted at one MRF facility.",
             is_dpiit_certified=True, state="Gujarat", is_women_led=False, profile_strength=58, verification_status="verified"),
        dict(name="SafeStreet Analytics", email="contact@safestreet.demo", tags="computer vision, traffic sensors, public safety, analytics",
             achievements="CCTV-based incident detection deployed on 2 highway stretches.",
             is_dpiit_certified=False, state="Maharashtra", is_women_led=False, profile_strength=55, verification_status="pending"),
        dict(name="JalRakshak", email="contact@jalrakshak.demo", tags="water quality, sanitation, IoT sensors, mobile app",
             achievements="Groundwater monitoring network across 12 villages.",
             is_dpiit_certified=True, state="Rajasthan", is_women_led=True, profile_strength=72, verification_status="verified"),
    ]

    demo_password_hash = auth.hash_password("Demo@123")

    created = []
    for s in demo_startups:
        startup = Startup(password_hash=demo_password_hash, **s)
        db.add(startup)
        created.append(startup)
    db.commit()

    # A little feedback history on the first three, so risk/scores vary realistically
    for startup, ratings in zip(created[:3], [[8.5, 9.0], [7.0], [9.2, 8.8, 9.0]]):
        for r in ratings:
            db.add(Feedback(startup_id=startup.id, rating=r))
    db.commit()

    # One demo government login
    if db.query(GovUser).count() == 0:
        db.add(GovUser(
            name="Urban Transport Officer",
            email="officer@maharashtra.gov.demo",
            password_hash=auth.hash_password("Gov@123"),
            department="Urban Transport",
        ))
        db.commit()

    db.close()
