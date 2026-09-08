import re

FULL_RE = re.compile(r'<claim\b([^>]*)>(.*?)</claim>', re.IGNORECASE | re.DOTALL)
SELF_RE = re.compile(r'<claim\b([^>]*)/>', re.IGNORECASE | re.DOTALL)
OPEN_RE = re.compile(r'<claim\b([^>]*)>', re.IGNORECASE | re.DOTALL)
PAIR_RE = re.compile(r'(\w+)="([^"]*)"')

def _attrs(blob: str) -> dict:
    return {k.lower(): v for k, v in PAIR_RE.findall(blob or "")}

def parse_claims(memo: str) -> list[dict]:
    memo = memo or ""
    claims = []

    for match in FULL_RE.finditer(memo):
        attrs = _attrs(match.group(1))
        inner = (match.group(2) or "").strip()
        quote = attrs.get("quote", "").strip()
        source = attrs.get("source", "").strip()
        claim = (inner or attrs.get("fact") or quote).strip()
        claims.append({"source_uri": source, "quote": quote, "claim": claim})

    if claims:
        return claims

    for match in list(SELF_RE.finditer(memo)) + list(OPEN_RE.finditer(memo)):
        attrs = _attrs(match.group(1))
        quote = attrs.get("quote", "").strip()
        source = attrs.get("source", "").strip()
        fact = (attrs.get("fact") or attrs.get("claim") or "").strip()
        # nearby sentence before the tag
        start = max(0, match.start() - 180)
        prefix = re.sub(r'\s+', ' ', memo[start:match.start()]).strip()
        claim = fact or prefix or quote
        claims.append({"source_uri": source, "quote": quote, "claim": claim})

    return claims
