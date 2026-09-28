"""
Integration Adapters Base Interfaces.

Aligned with SETU_PRD_and_Architecture.md Section 21:
"Every adapter has an interface, a mock for demo and tests, and a real
implementation added when access exists. Modules depend only on the interface."
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class DPIITAdapter(ABC):
    """Adapter interface for DPIIT / Startup India verification."""

    @abstractmethod
    def verify(self, dpiit_number: str) -> Dict[str, Any]:
        """
        Verify startup DPIIT recognition.
        Returns:
            {
                "valid": bool,
                "dpiit_number": str,
                "legal_name": str,
                "recognition_date": str,
                "source": str,
                "turnover_relaxation_eligible": bool,
                "experience_relaxation_eligible": bool,
                "bid_security_exemption_eligible": bool,
            }
        """
        pass


class GeMAdapter(ABC):
    """Adapter interface for Government e-Marketplace (GeM) handoff."""

    @abstractmethod
    def export_handoff_pack(self, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a GeM-compliant handoff archive and manifest.
        """
        pass


class PFMSAdapter(ABC):
    """Adapter interface for Public Financial Management System (PFMS)."""

    @abstractmethod
    def generate_payment_reference(self, milestone_id: int, amount: float, department: str) -> str:
        """
        Generate or fetch payment reference identifier.
        """
        pass
