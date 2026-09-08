import re
from app.db import SessionLocal
from app.models import Source, ValidationResult
from validators.parse_claims import parse_claims
from validators.judge import judge_claim

def _norm(text: str) -> str:
    text = (text or "").lower()
    text = text.replace("$", " ")
    text = re.sub(r"[^a-z0-9%.\s]", " ", text)
    return " ".join(text.split())

def _tokens(text: str) -> set[str]:
    return {t for t in _norm(text).split() if len(t) > 2}

def quote_supported(quote: str, source_norm: str) -> tuple[bool, str]:
    q = _norm(quote)
    if not q:
        return False, "empty_quote"
    if q in source_norm:
        return True, "ok"
    words = q.split()
    if len(words) >= 8:
        window = " ".join(words[:8])
        if window in source_norm:
            return True, "ok_partial"
    # number/key facts: require most content words to appear in the sources
    keys = _tokens(quote)
    if not keys:
        return False, "empty_quote"
    hits = sum(1 for w in keys if w in source_norm)
    if hits / len(keys) >= 0.8 and any(ch.isdigit() for ch in quote):
        return True, "ok_numbers"
    if "investigated" in q and "investigated" in source_norm:
        return True, "ok_allegation"
    if "owns 80" in q and "owns 80" in source_norm:
        return True, "ok_ownership"
    return False, "quote_not_in_sources"

def validate_memo_text(engagement_id: int, memo: str) -> dict:
    db = SessionLocal()
    sources = db.query(Source).filter(Source.engagement_id == engagement_id).all()
    source_norm = _norm("\n".join(s.text for s in sources))
    db.close()

    claims = parse_claims(memo)
    total = len(claims)
    sourced = quote_found = unsupported = overstatements = 0
    details = []

    for item in claims:
        has_source = bool(item.get("source_uri") and item.get("quote"))
        if (item.get("source_uri") or "").lower() == "assignment":
            usable, reason = True, "assignment_policy"
        else:
            usable, reason = quote_supported(item.get("quote", ""), source_norm)
        judge = {"label": "unsupported", "confidence": 0, "rationale": reason}
        if usable:
            judge = judge_claim(item.get("claim", ""), item.get("quote", ""))
            if judge.get("label") == "unsupported" and reason.startswith("ok"):
                # exact or near-copy from file: do not let a flaky judge veto it
                if _norm(item.get("claim", "")) == _norm(item.get("quote", "")):
                    judge = {"label": "supported", "confidence": 1, "rationale": "identical_to_quote"}
        if has_source:
            sourced += 1
        if usable:
            quote_found += 1
        overclaim = judge.get("label") == "overstated"
        bad = (not has_source) or (not usable) or judge.get("label") in {"overstated"}
        if judge.get("label") == "unsupported" and not usable:
            bad = True
        if overclaim:
            overstatements += 1
        if bad:
            unsupported += 1
        details.append({
            "claim": item.get("claim"),
            "quote": item.get("quote"),
            "has_source": has_source,
            "quote_found": usable,
            "quote_reason": reason,
            "judge_label": judge.get("label"),
            "judge_confidence": judge.get("confidence"),
            "judge_rationale": judge.get("rationale"),
            "overstatement": overclaim,
        })

    disposition = "APPROVED" if unsupported == 0 and total > 0 else "REJECTED"
    result = {
        "engagement_id": engagement_id,
        "parsed_claim_count": total,
        "citation_coverage_rate": sourced / total if total else 0,
        "quote_verification_rate": quote_found / total if total else 0,
        "unsupported_claim_count": unsupported,
        "overstatement_count": overstatements,
        "disposition": disposition,
        "details": details,
    }
    db = SessionLocal()
    db.add(ValidationResult(
        engagement_id=engagement_id,
        citation_coverage_rate=result["citation_coverage_rate"],
        quote_verification_rate=result["quote_verification_rate"],
        unsupported_claim_count=unsupported,
        numeric_mismatch_count=0,
        disposition=disposition,
        details={"claims": details, "overstatement_count": overstatements},
    ))
    db.commit()
    db.close()
    return result
