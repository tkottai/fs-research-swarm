from app.db import SessionLocal
from app.models import Source, EvidenceCard

db = SessionLocal()
sources = db.query(Source).filter(Source.engagement_id == 1).all()

for source in sources:
    text = source.text.strip()
    card = EvidenceCard(
        engagement_id=1,
        claim=text,
        quote=text,
        source_uri=source.uri,
        confidence=1.0,
    )
    db.add(card)

db.commit()
print(f"Created {len(sources)} evidence cards")
db.close()
