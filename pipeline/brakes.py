from app.db import SessionLocal
from app.models import UsageEvent, Engagement

def total_spend(engagement_id: int) -> float:
    db = SessionLocal()
    rows = db.query(UsageEvent).filter(UsageEvent.engagement_id == engagement_id).all()
    db.close()
    return round(sum(r.cost_usd or 0 for r in rows), 6)

def over_budget(engagement_id: int) -> bool:
    db = SessionLocal()
    eng = db.get(Engagement, engagement_id)
    db.close()
    if not eng:
        return False
    return total_spend(engagement_id) >= (eng.budget_usd or 5.0)
