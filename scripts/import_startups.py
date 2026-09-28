"""
Startup Registry Importer.

PRD Section 6.3 & Section 7 of User Requirements:
Flow:
CSV / JSON / external source
        ↓
Importer / adapter
        ↓
Validation
        ↓
Startup Registry database
        ↓
Embedding generation
        ↓
Matching index
"""

import os
import sys
import json
import csv
import argparse
from datetime import datetime

# Setup paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BASE_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
for folder in ["database", "scoring-engine", "matching-nlp", "contracts-finance", "integrations"]:
    p = os.path.join(REPO_ROOT, folder)
    if p not in sys.path:
        sys.path.insert(0, p)

from database import init_db, SessionLocal
from models import Startup, GovUser
from integrations.dpiit_adapter import dpiit_adapter
from semantic_matcher import compute_and_cache_startup_embeddings
import scoring
import auth


def load_startups_from_file(file_path: str):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if file_path.endswith(".json"):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    elif file_path.endswith(".csv"):
        items = []
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Type conversions
                row["id"] = int(row["id"]) if row.get("id") else None
                row["past_deployments_count"] = int(row.get("past_deployments_count", 0))
                row["verified_evidence_count"] = int(row.get("verified_evidence_count", 0))
                row["profile_strength"] = float(row.get("profile_strength", 50.0))
                row["current_score"] = float(row.get("current_score", 0.0))
                row["turnover_lakhs"] = float(row.get("turnover_lakhs", 0.0))
                row["experience_years"] = int(row.get("experience_years", 0))
                row["is_dpiit_certified"] = str(row.get("is_dpiit_certified")).lower() in ["true", "1", "yes"]
                row["is_women_led"] = str(row.get("is_women_led")).lower() in ["true", "1", "yes"]
                row["debarred"] = str(row.get("debarred")).lower() in ["true", "1", "yes"]
                items.append(row)
        return items
    else:
        raise ValueError("Unsupported format. Use .json or .csv")


def import_startups(file_path: str = None):
    init_db()
    db = SessionLocal()

    if file_path is None:
        file_path = os.path.join(REPO_ROOT, "data", "startups.json")
        if not os.path.exists(file_path):
            file_path = os.path.join(REPO_ROOT, "data", "startups.csv")

    print(f"[*] Importing startup registry from: {file_path}")
    raw_startups = load_startups_from_file(file_path)

    demo_password_hash = auth.hash_password("Demo@123")
    imported_count = 0
    updated_count = 0
    processed_dicts = []

    for item in raw_startups:
        s_id = item.get("id")
        name = item.get("name") or item.get("display_name") or item.get("legal_name")
        email = item.get("email") or f"contact@{name.lower().replace(' ', '')}.demo"

        # DPIIT Adapter verification check (PRD Section 21)
        dpiit_number = item.get("dpiit_number")
        dpiit_check = dpiit_adapter.verify(dpiit_number)

        if dpiit_check["valid"]:
            dpiit_status = "verified"
            is_dpiit_certified = True
            verification_status = "verified"
            source = dpiit_check.get("source", "dpiit_adapter")
        elif item.get("dpiit_status") == "self_declared":
            dpiit_status = "self_declared"
            is_dpiit_certified = False
            verification_status = item.get("verification_status", "pending")
            source = item.get("source", "self_declared")
        else:
            dpiit_status = "none"
            is_dpiit_certified = False
            verification_status = item.get("verification_status", "demo")
            source = item.get("source", "demo_seed")

        # Find existing by ID or email
        existing = None
        if s_id:
            existing = db.query(Startup).filter(Startup.id == s_id).first()
        if not existing and email:
            existing = db.query(Startup).filter(Startup.email == email).first()

        startup_attrs = {
            "legal_name": item.get("legal_name") or name,
            "display_name": item.get("display_name") or name,
            "name": name,
            "email": email,
            "password_hash": demo_password_hash,
            "description": item.get("description", ""),
            "capabilities": item.get("capabilities", item.get("tags", "")),
            "products": item.get("products", ""),
            "technology_tags": item.get("technology_tags", ""),
            "tags": item.get("tags", item.get("capabilities", "")),
            "achievements": item.get("achievements", item.get("past_deployments", "")),
            "industry": item.get("industry", item.get("sector", "")),
            "sector": item.get("sector", item.get("industry", "General")),
            "maturity_level": item.get("maturity_level", "Pilot-Ready"),
            "location": item.get("location", f"{item.get('city', '')}, {item.get('state', '')}".strip(", ")),
            "state": item.get("state", "Maharashtra"),
            "city": item.get("city", "Mumbai"),
            "past_deployments": item.get("past_deployments", ""),
            "past_deployments_count": item.get("past_deployments_count", 0),
            "dpiit_status": dpiit_status,
            "dpiit_number": dpiit_number,
            "is_dpiit_certified": is_dpiit_certified,
            "is_women_led": item.get("is_women_led", False),
            "verification_status": verification_status,
            "verified_evidence_count": item.get("verified_evidence_count", 0),
            "profile_strength": item.get("profile_strength", 50.0),
            "turnover_lakhs": item.get("turnover_lakhs", 0.0),
            "experience_years": item.get("experience_years", 0),
            "debarred": item.get("debarred", False),
            "source": source,
        }

        if existing:
            for k, v in startup_attrs.items():
                setattr(existing, k, v)
            startup_obj = existing
            updated_count += 1
        else:
            if s_id:
                startup_obj = Startup(id=s_id, **startup_attrs)
            else:
                startup_obj = Startup(**startup_attrs)
            db.add(startup_obj)
            imported_count += 1

        db.flush()
        processed_dicts.append(startup_obj.to_dict())

    db.commit()

    # Recompute baseline SETU scores
    for s in db.query(Startup).all():
        s.current_score = scoring.calculate_final_score(db, s)
    db.commit()

    # Precompute and cache SBERT embeddings for fast discovery (Section 8)
    print(f"[*] Precomputing and caching SBERT embeddings for {len(processed_dicts)} startups...")
    compute_and_cache_startup_embeddings(processed_dicts)
    print("[*] Embeddings successfully generated and indexed.")

    # Ensure government demo user exists
    if db.query(GovUser).count() == 0:
        db.add(GovUser(
            name="Urban Infrastructure Officer",
            email="officer@maharashtra.gov.demo",
            password_hash=auth.hash_password("Gov@123"),
            department="Energy & Utilities",
        ))
        db.commit()

    db.close()
    print(f"[OK] Import complete: {imported_count} imported, {updated_count} updated.")
    return {"imported": imported_count, "updated": updated_count, "total": len(processed_dicts)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import startups into SETU database")
    parser.add_argument("--source", type=str, default=None, help="Path to startups.json or startups.csv")
    args = parser.parse_args()
    import_startups(args.source)
