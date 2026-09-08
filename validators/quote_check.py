from app.db import SessionLocal
from app.models import Source, EvidenceCard, ValidationResult
from validators.allegation_check import is_overstatement

def validate_engagement(engagement_id: int) -> dict:
    db = SessionLocal()
    cards = db.query(EvidenceCard).filter(EvidenceCard.engagement_id == engagement_id).all()
    sources = db.query(Source).filter(Source.engagement_id == engagement_id).all()
    source_text = "\n".join(source.text for source in sources)

    total = len(cards)
    sourced = 0
    quote_found = 0
    unsupported = 0
    overstatements = 0
    details = []

    for card in cards:
        has_source = bool(card.source_uri and card.quote)
        quote_ok = card.quote.strip() in source_text if card.quote else False
        overclaim = is_overstatement(card.claim, card.quote or "")

        if has_source:
            sourced += 1
        if quote_ok:
            quote_found += 1
        if overclaim:
            overstatements += 1
        if not has_source or not quote_ok or overclaim:
            unsupported += 1

        details.append({
            "claim": card.claim,
            "has_source": has_source,
            "quote_found": quote_ok,
            "overstatement": overclaim,
        })

    citation_coverage = sourced / total if total else 0
    quote_rate = quote_found / total if total else 0
    disposition = "APPROVED" if unsupported == 0 and total > 0 else "REJECTED"

    result = ValidationResult(
        engagement_id=engagement_id,
        citation_coverage_rate=citation_coverage,
        quote_verification_rate=quote_rate,
        unsupported_claim_count=unsupported,
        numeric_mismatch_count=0,
        disposition=disposition,
        details={"claims": details, "overstatement_count": overstatements},
    )
    db.add(result)
    db.commit()
    db.close()

    return {
        "engagement_id": engagement_id,
        "citation_coverage_rate": citation_coverage,
        "quote_verification_rate": quote_rate,
        "unsupported_claim_count": unsupported,
        "overstatement_count": overstatements,
        "disposition": disposition,
        "details": details,
    }
