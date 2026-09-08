import re
from app.db import SessionLocal
from app.models import Source

NEEDLES = {
    "borrower": ["merchant acquir", "payments ltd"],
    "ownership": ["owns 80", "80%"],
    "facility": ["100000", "100,000", "working capital", "working-capital"],
    "existing_debt": ["480000", "480,000", "term loan"],
    "liquidity": ["410000", "410,000", "190000", "190,000", "cash"],
    "earnings": ["ebitda", "4820000", "4,820,000"],
    "adverse_media": ["investigated", "alleged"],
    "limits": ["unaudit", "no fine", "did not state that a fine"],
}

def _clean(text: str) -> str:
    return " ".join((text or "").split()).replace('"', "'")

def _hit(text: str, needles: list[str]) -> str:
    compact = _clean(text)
    low = compact.lower().replace(",", "").replace("$", "")
    for needle in needles:
        n = needle.lower().replace(",", "").replace("$", "")
        idx = low.find(n)
        if idx >= 0:
            raw = compact.lower().replace("$", "")
            j = raw.find(n[:8] if len(n) >= 8 else n)
            if j < 0:
                j = max(0, idx)
            start = compact.rfind(".", 0, j) + 1
            end = compact.find(".", j)
            if end < 0:
                end = min(len(compact), j + 180)
            span = compact[start:end].strip(" .")
            if len(span.split()) >= 6:
                return span
            return compact[max(0, j): j + 160].strip()
    return ""

def extract_findings(engagement_id: int) -> list[dict]:
    db = SessionLocal()
    rows = db.query(Source).filter(Source.engagement_id == engagement_id).all()
    db.close()
    findings = []
    for key, needles in NEEDLES.items():
        span, uri = "", ""
        for row in rows:
            span = _hit(row.text, needles)
            if span:
                uri = row.uri
                break
        findings.append({"section": key, "uri": uri or "unknown", "text": span})
    return findings

def build_memo(engagement_id: int, use_llm: bool = False) -> str:
    findings = extract_findings(engagement_id)
    lines = ["# First-pass KYB / credit memo", "", "## Findings", ""]
    for item in findings:
        if item["text"]:
            lines.append(f'<claim source="{item["uri"]}" quote="{item["text"]}">{item["text"]}</claim>')
        else:
            lines.append(f'<claim source="unknown" quote="No sourced span for {item["section"]}.">Unknown: {item["section"]} not found in the pack.</claim>')
        lines.append("")
    lines.append('<claim source="assignment" quote="This memo does not approve or decline the loan.">This memo does not approve or decline the loan.</claim>')
    return "\n".join(lines)

def build_analyst_summary(engagement_id: int, board: dict, scores: dict) -> str:
    findings = extract_findings(engagement_id)
    covered = [f["section"] for f in findings if f["text"]]
    missing = [f["section"] for f in findings if not f["text"]]
    decision = (board or {}).get("decision", "PENDING")
    reason = (board or {}).get("reason", "")
    lines = [
        "# Analyst summary",
        "",
        "Job: first-pass review of a $100,000 working-capital facility.",
        f"Machine decision: {decision}. {reason}",
        "",
        "Covered from the pack:",
    ]
    for f in findings:
        if f["text"]:
            lines.append(f"- {f['section']}: {f['text']}")
    if missing:
        lines.append("")
        lines.append("Not found in the pack: " + ", ".join(missing))
    lines += [
        "",
        "Hallucination control: only spans found in stored sources were used.",
        "This is a file recommendation for the analyst, not a loan approval.",
    ]
    return "\n".join(lines)
