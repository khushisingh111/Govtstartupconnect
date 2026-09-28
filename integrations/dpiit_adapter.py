"""DPIIT adapter.

The MVP uses a registry file as a mock source because a live official lookup
requires authorised access. Startup names/numbers are NOT hardcoded in code.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any
from integrations.base import DPIITAdapter

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_PATH = os.path.join(REPO_ROOT, "data", "startups.json")


def _load_registry() -> dict:
    try:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            rows = json.load(f)
        return {str(r.get("dpiit_number", "")).strip().upper(): r for r in rows if r.get("dpiit_number")}
    except (OSError, json.JSONDecodeError):
        return {}


class MockDPIITAdapter(DPIITAdapter):
    """File-backed demo adapter. Never claims to be a live DPIIT API."""

    def verify(self, dpiit_number: str) -> Dict[str, Any]:
        cleaned = (dpiit_number or "").strip().upper()
        if not cleaned:
            return {
                "valid": False, "dpiit_number": "", "legal_name": "",
                "recognition_date": None, "source": "file_registry",
                "verified_at": datetime.utcnow().isoformat(),
                "turnover_relaxation_eligible": False,
                "experience_relaxation_eligible": False,
                "bid_security_exemption_eligible": False,
                "message": "No DPIIT registration number provided.",
            }

        record = _load_registry().get(cleaned)
        if record and str(record.get("dpiit_status", "")).lower() == "verified":
            return {
                "valid": True,
                "dpiit_number": cleaned,
                "legal_name": record.get("legal_name", ""),
                "recognition_date": record.get("recognition_date"),
                "state": record.get("state", ""),
                "source": record.get("source", "demo_registry"),
                "verified_at": datetime.utcnow().isoformat(),
                "turnover_relaxation_eligible": True,
                "experience_relaxation_eligible": True,
                "bid_security_exemption_eligible": True,
                "message": "DPIIT status verified against the configured demo registry source.",
            }

        return {
            "valid": False,
            "dpiit_number": cleaned,
            "legal_name": "",
            "recognition_date": None,
            "source": "file_registry",
            "verified_at": datetime.utcnow().isoformat(),
            "turnover_relaxation_eligible": False,
            "experience_relaxation_eligible": False,
            "bid_security_exemption_eligible": False,
            "message": f"DPIIT number '{cleaned}' not found in the configured registry. Marked as self-declared/manual review.",
        }


class RealDPIITAdapter(DPIITAdapter):
    def verify(self, dpiit_number: str) -> Dict[str, Any]:
        raise NotImplementedError(
            "Live DPIIT lookup requires authorised official access. Use the file/import adapter until then."
        )


dpiit_adapter = MockDPIITAdapter()
