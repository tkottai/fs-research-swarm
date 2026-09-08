from agents.coverage import score_coverage

def review(scores: dict) -> dict:
    claims = scores.get("details") or []
    coverage = score_coverage(claims)
    scores["coverage"] = coverage
    unsupported = scores.get("unsupported_claim_count", 0)
    overstatements = scores.get("overstatement_count", 0)
    parsed = scores.get("parsed_claim_count", 0)

    if parsed == 0:
        return {"decision": "REJECTED", "reason": "no parseable claims", "coverage": coverage}
    if overstatements > 0 or unsupported > 0:
        return {"decision": "REJECTED", "reason": "unsupported or overstated claims", "coverage": coverage}
    if not coverage["complete"]:
        return {
            "decision": "INCREMENTAL",
            "reason": "grounded but missing " + ", ".join(coverage["missing"]),
            "coverage": coverage,
        }
    return {"decision": "APPROVED", "reason": "sourced and assignment coverage complete", "coverage": coverage}
