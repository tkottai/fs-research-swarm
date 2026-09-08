from fastapi import FastAPI, Depends, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import Base, engine, get_db
from app.models import Engagement, Memo, Source, EvidenceCard, ValidationResult, StageEvent, CacheEntry, UsageEvent
from app.synthesize import build_memo
from pipeline.runner import run_stages
from extractors.pdf import extract_pdf_text

Base.metadata.create_all(bind=engine)
app = FastAPI(title="fs-research-swarm", version="0.5.0")

class EngagementIn(BaseModel):
    company_name: str
    jurisdiction: str = "US"
    engagement_type: str = "kyb"
    budget_usd: float = 5.0

class DecisionIn(BaseModel):
    note: str = ""

class ObjectiveIn(BaseModel):
    objective: str = ""

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/engagements")
def create_engagement(payload: EngagementIn, db: Session = Depends(get_db)):
    row = Engagement(company_name=payload.company_name, jurisdiction=payload.jurisdiction, engagement_type=payload.engagement_type, budget_usd=payload.budget_usd, status="created")
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "company_name": row.company_name, "status": row.status}

@app.get("/engagements/{engagement_id}")
def get_engagement(engagement_id: int, db: Session = Depends(get_db)):
    row = db.get(Engagement, engagement_id)
    if not row:
        return {"error": "not found"}
    return {
        "id": row.id,
        "company_name": row.company_name,
        "jurisdiction": row.jurisdiction,
        "engagement_type": row.engagement_type,
        "status": row.status,
        "analyst_decision": row.analyst_decision,
        "analyst_note": row.analyst_note,
        "budget_usd": row.budget_usd,
        "objective": row.objective,
    }

@app.post("/engagements/{engagement_id}/objective")
def set_objective(engagement_id: int, payload: ObjectiveIn, db: Session = Depends(get_db)):
    row = db.get(Engagement, engagement_id)
    if not row:
        return {"error": "not found"}
    row.objective = payload.objective
    db.commit()
    return {"id": row.id, "objective": row.objective}

@app.post("/engagements/{engagement_id}/upload")
async def upload_source(engagement_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    data = await file.read()
    name = file.filename or "upload.bin"
    if name.lower().endswith(".pdf"):
        text = extract_pdf_text(data)
        source_type = "pdf"
    else:
        text = data.decode("utf-8", errors="ignore")
        source_type = "url"
    row = Source(engagement_id=engagement_id, source_type=source_type, uri=name, text=text)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "uri": row.uri, "source_type": row.source_type, "chars": len(row.text)}

@app.post("/engagements/{engagement_id}/run")
def run_pipeline(engagement_id: int, db: Session = Depends(get_db)):
    return run_stages(db, engagement_id)

@app.post("/engagements/{engagement_id}/accept")
def accept_engagement(engagement_id: int, payload: DecisionIn, db: Session = Depends(get_db)):
    row = db.get(Engagement, engagement_id)
    if not row:
        return {"error": "not found"}
    row.status = "accepted"
    row.analyst_decision = "accept"
    row.analyst_note = payload.note
    db.commit()
    return {"id": row.id, "status": row.status, "note": row.analyst_note}

@app.post("/engagements/{engagement_id}/reject")
def reject_engagement(engagement_id: int, payload: DecisionIn, db: Session = Depends(get_db)):
    row = db.get(Engagement, engagement_id)
    if not row:
        return {"error": "not found"}
    row.status = "rejected_by_analyst"
    row.analyst_decision = "reject"
    row.analyst_note = payload.note
    db.commit()
    return {"id": row.id, "status": row.status, "note": row.analyst_note}

@app.get("/debug/tables")
def debug_tables(db: Session = Depends(get_db)):
    return {
        "engagements": [{"id": r.id, "company_name": r.company_name, "status": r.status, "objective": (r.objective or "")[:80]} for r in db.query(Engagement).all()],
        "sources": [{"id": r.id, "uri": r.uri, "source_type": r.source_type, "chars": len(r.text or "")} for r in db.query(Source).all()],
        "evidence_cards": [{"id": r.id, "claim": r.claim[:80]} for r in db.query(EvidenceCard).all()],
        "memos": [{"id": r.id, "disposition": r.disposition} for r in db.query(Memo).all()],
        "validation_results": [{"id": r.id, "disposition": r.disposition, "unsupported": r.unsupported_claim_count} for r in db.query(ValidationResult).all()],
        "stage_events": [{"id": r.id, "stage": r.stage, "status": r.status, "message": r.message[:180]} for r in db.query(StageEvent).order_by(StageEvent.id.desc()).limit(25).all()],
        "cache_entries": [{"id": r.id, "tier": r.tier, "hit_count": r.hit_count} for r in db.query(CacheEntry).all()],
        "usage_events": [{"id": r.id, "stage": r.stage, "model": r.model, "cost_usd": r.cost_usd, "cache_hit": r.cache_hit} for r in db.query(UsageEvent).order_by(UsageEvent.id.desc()).limit(25).all()],
    }
