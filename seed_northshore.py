from app.db import SessionLocal, Base, engine
from app.models import Engagement, Source

Base.metadata.create_all(bind=engine)
db = SessionLocal()
eng = db.get(Engagement, 1)
if not eng:
    eng = Engagement(id=1, company_name="Northshore Payments Ltd", jurisdiction="UK", engagement_type="kyb", status="created", budget_usd=5.0,
                     objective="Assess Northshore Payments Ltd for a $100,000 working-capital loan. Confirm identity, ownership, profit, debt, liquidity, and adverse media. Do not approve the loan.")
    db.add(eng)
    db.flush()
else:
    eng.objective = "Assess Northshore Payments Ltd for a $100,000 working-capital loan. Confirm identity, ownership, profit, debt, liquidity, and adverse media. Do not approve the loan."

db.query(Source).filter(Source.engagement_id == 1).delete()

docs = {
"Northshore_FY2025_Management_Accounts.pdf": """
NORTHSHORE PAYMENTS LTD is a UK merchant acquirer trading as Northshore Pay.
Merchant acquiring revenue 4,820,000 EBITDA 950,000 Profit after tax 565,000
Cash and cash equivalents 410,000 Trade receivables 620,000
Net debt / EBITDA 0.07x These figures are unaudited management accounts.
The Company has requested a $100,000 working-capital facility to cover settlement timing gaps and a planned sales-hire.
""",
"Northshore_Debt_and_Banking_Schedule.pdf": """
Average FY2025 current-account balance: $190,000
Outstanding principal at 31 Dec 2025: $480,000 term loan with Barclays Bank UK PLC
Amount requested: $100,000 working-capital revolving credit
Chargeback reserve held with the sponsor bank: $75,000
This schedule does not approve the requested facility.
""",
"Northshore_Group_Structure_and_Ownership.pdf": """
Northshore Holdings plc owns 80% of Northshore Payments Ltd.
The remaining 20% of Northshore Payments Ltd is held by management.
Voting control of the operating company sits with Northshore Holdings plc through its 80% shareholding.
""",
"Northshore_Adverse_Media_Brief.pdf": """
Northshore Pay is being investigated in connection with alleged onboarding failures.
The article did not state that a fine had been issued.
No fine amount should be treated as a verified fact from this document.
""",
}
for uri, text in docs.items():
    db.add(Source(engagement_id=1, source_type="pdf", uri=uri, text=text.strip()))
db.commit()
print("seeded", db.query(Source).filter(Source.engagement_id==1).count(), "sources")
db.close()
