OVERCLAIM_WORDS = ["fined", "guilty", "convicted", "sentenced", "liable"]
SAFE_WORDS = ["investigated", "investigation", "alleged", "accused"]

def is_overstatement(claim: str, quote: str) -> bool:
    claim_l = claim.lower()
    quote_l = quote.lower()
    claim_has_verdict = any(word in claim_l for word in OVERCLAIM_WORDS)
    quote_is_only_allegation = any(word in quote_l for word in SAFE_WORDS)
    return claim_has_verdict and quote_is_only_allegation
