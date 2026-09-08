import json
import os
import httpx

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "llama3.2")

def judge_claim(claim: str, quote: str) -> dict:
    prompt = f"""You are a KYB faithfulness judge.
Compare the CLAIM to the QUOTE.
Return ONLY JSON with keys:
label: supported | partial | overstated | unsupported
confidence: number between 0 and 1
rationale: short sentence

CLAIM: {claim}
QUOTE: {quote}
"""
    try:
        response = httpx.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": JUDGE_MODEL, "prompt": prompt, "stream": False},
            timeout=90.0,
        )
        response.raise_for_status()
        text = response.json().get("response", "")
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            data = json.loads(text[start:end + 1])
            label = str(data.get("label", "unsupported")).lower()
            if label not in {"supported", "partial", "overstated", "unsupported"}:
                label = "unsupported"
            return {
                "label": label,
                "confidence": float(data.get("confidence", 0.5)),
                "rationale": str(data.get("rationale", ""))[:300],
            }
    except Exception as e:
        return {"label": "unsupported", "confidence": 0.0, "rationale": f"judge_error: {e}"}
    return {"label": "unsupported", "confidence": 0.0, "rationale": "judge_parse_failed"}
