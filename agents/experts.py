from app.db import SessionLocal
from app.models import Source, EvidenceCard

def run_document_expert(engagement_id: int) -> list[str]:
    db = SessionLocal()
    sources = db.query(Source).filter(
        Source.engagement_id == engagement_id,
        Source.source_type.in_(["pdf", "document"]),
    ).all()
    made = []
    for source in sources:
        exists = db.query(EvidenceCard).filter(
            EvidenceCard.engagement_id == engagement_id,
            EvidenceCard.source_uri == source.uri,
            EvidenceCard.quote == source.text.strip(),
        ).first()
        if exists:
            made.append(f"reuse {source.uri}")
            continue
        db.add(EvidenceCard(
            engagement_id=engagement_id,
            claim=source.text.strip(),
            quote=source.text.strip(),
            source_uri=source.uri,
            confidence=1.0,
        ))
        made.append(f"extract {source.uri}")
    db.commit()
    db.close()
    return made

def run_url_expert(engagement_id: int) -> list[str]:
    db = SessionLocal()
    sources = db.query(Source).filter(
        Source.engagement_id == engagement_id,
        Source.source_type.in_(["url", "news", "web"]),
    ).all()
    made = []
    for source in sources:
        exists = db.query(EvidenceCard).filter(
            EvidenceCard.engagement_id == engagement_id,
            EvidenceCard.source_uri == source.uri,
            EvidenceCard.quote == source.text.strip(),
        ).first()
        if exists:
            made.append(f"reuse {source.uri}")
            continue
        db.add(EvidenceCard(
            engagement_id=engagement_id,
            claim=source.text.strip(),
            quote=source.text.strip(),
            source_uri=source.uri,
            confidence=1.0,
        ))
        made.append(f"extract {source.uri}")
    db.commit()
    db.close()
    return made
