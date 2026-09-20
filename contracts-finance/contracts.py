"""
Contracts & Finance module.

Owns the 4-milestone contract lifecycle. No payment gateway — this only
tracks state and amounts, which is all a pilot-stage procurement register
needs (actual disbursal happens through PFMS in the real system).
"""

from datetime import datetime

ACTIVE_STATUSES = ["planned", "in_progress", "delivered"]  # not yet "paid"/closed


def has_active_pilot(db, startup_id: int) -> bool:
    """
    Checks whether a startup is already running an active pilot with ANY
    department. Used to stop two departments from selecting the same
    startup for a pilot at the same time — a gap flagged during review.
    """
    from models import Contract, Milestone

    contract_ids = [c.id for c in db.query(Contract).filter(Contract.startup_id == startup_id).all()]
    if not contract_ids:
        return False

    active_milestone = (
        db.query(Milestone)
        .filter(Milestone.contract_id.in_(contract_ids), Milestone.status.in_(ACTIVE_STATUSES))
        .first()
    )
    return active_milestone is not None


def create_contract(db, startup_id: int, problem_title: str, department: str, total_budget: float):
    from models import Contract, Milestone

    if has_active_pilot(db, startup_id):
        raise ValueError(
            "This startup already has an active pilot in progress with another department. "
            "A startup can only run one active pilot at a time."
        )

    contract = Contract(startup_id=startup_id, problem_title=problem_title, department=department)
    db.add(contract)
    db.commit()
    db.refresh(contract)

    scopes = [
        "Prototype / demo ready",
        "Deployed at pilot site",
        "Field-tested, data collected",
        "Final report & validation",
    ]
    share = round(total_budget / 4, 2)
    for i, scope in enumerate(scopes, start=1):
        db.add(Milestone(
            contract_id=contract.id,
            milestone_number=i,
            scope=scope,
            funds_allocated=share,
            status="planned",
        ))
    db.commit()
    return contract


def get_contract_with_milestones(db, contract_id: int):
    from models import Contract, Milestone
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        return None
    milestones = (
        db.query(Milestone)
        .filter(Milestone.contract_id == contract_id)
        .order_by(Milestone.milestone_number)
        .all()
    )
    return {"contract": contract, "milestones": milestones}


def advance_milestone(db, contract_id: int, milestone_number: int, new_status: str):
    from models import Milestone
    valid_statuses = ["planned", "in_progress", "delivered", "paid"]
    if new_status not in valid_statuses:
        raise ValueError(f"status must be one of {valid_statuses}")

    milestone = (
        db.query(Milestone)
        .filter(Milestone.contract_id == contract_id, Milestone.milestone_number == milestone_number)
        .first()
    )
    if not milestone:
        raise ValueError("Milestone not found")
    milestone.status = new_status
    db.commit()
    return milestone
