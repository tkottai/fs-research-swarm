from app.db import SessionLocal
from app.models import UsageEvent

INPUT_PER_1K = 0.00015
OUTPUT_PER_1K = 0.0006

def estimate_tokens(text: str) -> int:
    return max(1, len(text or "") // 4)

def log_usage(engagement_id: int, stage: str, model: str, prompt: str, output: str, cache_hit: bool = False):
    prompt_tokens = estimate_tokens(prompt)
    completion_tokens = estimate_tokens(output)
    cost = 0.0 if cache_hit else (prompt_tokens / 1000 * INPUT_PER_1K) + (completion_tokens / 1000 * OUTPUT_PER_1K)
    db = SessionLocal()
    db.add(UsageEvent(
        engagement_id=engagement_id,
        stage=stage,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_usd=round(cost, 6),
        cache_hit=cache_hit,
    ))
    db.commit()
    db.close()
    return cost
