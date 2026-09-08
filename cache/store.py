from app.db import SessionLocal
from app.models import CacheEntry

def cache_get(tier: str, cache_key: str):
    db = SessionLocal()
    row = db.query(CacheEntry).filter(
        CacheEntry.tier == tier,
        CacheEntry.cache_key == cache_key,
        CacheEntry.status == "valid",
    ).first()
    if row:
        row.hit_count += 1
        db.commit()
        payload = row.payload
        db.close()
        return payload
    db.close()
    return None

def cache_set(tier: str, cache_key: str, payload: str):
    db = SessionLocal()
    row = CacheEntry(tier=tier, cache_key=cache_key, payload=payload, status="valid")
    db.add(row)
    db.commit()
    db.close()
