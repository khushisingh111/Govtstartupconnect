"""
PFMS (Public Financial Management System) Adapter Implementation.

PRD Section 21:
"PFMS: payment_reference(milestone) -> reference
MVP mock: Generates a mock reference.
Real target: Department's existing payment process or PFMS."
"""

import hashlib
from datetime import datetime
from integrations.base import PFMSAdapter


class MockPFMSAdapter(PFMSAdapter):
    """
    Mock PFMS payment reference generator conforming to standard PFMS treasury transaction formats.
    """

    def generate_payment_reference(self, milestone_id: int, amount: float, department: str) -> str:
        date_str = datetime.utcnow().strftime("%Y%m%d")
        dept_code = "".join([w[0] for w in department.split() if w]).upper()[:3] or "GOV"
        hash_seed = f"{milestone_id}-{amount}-{datetime.utcnow().timestamp()}"
        unique_suffix = hashlib.md5(hash_seed.encode()).hexdigest()[:6].upper()
        return f"PFMS-{dept_code}-{date_str}-{milestone_id:04d}-{unique_suffix}"


pfms_adapter = MockPFMSAdapter()
