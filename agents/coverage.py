SECTIONS = [
    ("borrower", ["payments ltd", "merchant acquir", "legal"]),
    ("ownership", ["owns 80", "80%", "management", "holdings"]),
    ("facility", ["100,000", "100000", "working-capital", "working capital"]),
    ("existing_debt", ["term loan", "480,000", "480000", "barclays", "senior"]),
    ("liquidity", ["cash", "410,000", "190,000", "receivable", "75,000"]),
    ("earnings", ["ebitda", "revenue", "4,820,000", "profit"]),
    ("adverse_media", ["investigat", "alleged", "fine"]),
    ("limits", ["unaudit", "does not approve", "not approve", "unknown"]),
]

def score_coverage(claims: list[dict]) -> dict:
    blob = " ".join(
        f"{c.get('claim','')} {c.get('quote','')}" for c in claims
    ).lower()
    covered = {}
    missing = []
    for name, keys in SECTIONS:
        ok = any(k in blob for k in keys)
        covered[name] = ok
        if not ok:
            missing.append(name)
    required = [n for n, _ in SECTIONS]
    return {
        "required": required,
        "covered": covered,
        "missing": missing,
        "coverage_rate": round((len(required) - len(missing)) / len(required), 2) if required else 0,
        "complete": len(missing) == 0,
    }
