from app.db import SessionLocal, Base, engine
from app.models import Engagement, Source
from app.synthesize import build_memo
from validators.parse_claims import parse_claims

Base.metadata.create_all(bind=engine)
db = SessionLocal()

eng = db.get(Engagement, 1)
if not eng:
    db.add(Engagement(
        company_name="Northshore Payments Ltd",
        jurisdiction="UK",
        engagement_type="kyb",
        status="created",
        budget_usd=5.0,
        objective="Assess Northshore Payments Ltd for a $100,000 working-capital loan.",
    ))
    db.commit()
    eng = db.query(Engagement).order_by(Engagement.id).first()

eid = eng.id
eng.objective = "Assess Northshore Payments Ltd for a $100,000 working-capital loan. Do not approve the loan."
db.query(Source).filter(Source.engagement_id == eid).delete()
db.add(Source(engagement_id=eid, source_type="pdf", uri="accounts.pdf", text="UK merchant acquirer Northshore Payments Ltd. Revenue 4820000 EBITDA 950000. Cash and cash equivalents 410000. Requested a 100000 working-capital facility. Figures are unaudited."))
db.add(Source(engagement_id=eid, source_type="pdf", uri="debt.pdf", text="Barclays term loan outstanding principal 480000. Amount requested 100000 working capital. Current-account balance 190000."))
db.add(Source(engagement_id=eid, source_type="pdf", uri="ownership.pdf", text="Northshore Holdings plc owns 80% of Northshore Payments Ltd. Management holds the remaining 20%."))
db.add(Source(engagement_id=eid, source_type="pdf", uri="news.pdf", text="Northshore Pay is being investigated in connection with alleged onboarding failures. The article did not state that a fine had been issued."))
db.commit()
print("ENGAGEMENT", eid)
print("SOURCES", [(s.uri, len(s.text)) for s in db.query(Source).filter(Source.engagement_id==eid)])
db.close()
memo = build_memo(eid)
print(memo)
print("PARSED", len(parse_claims(memo)))
