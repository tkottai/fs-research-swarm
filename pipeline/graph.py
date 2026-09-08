import hashlib
import json
from typing import TypedDict
from langgraph.graph import StateGraph, END
from app.db import SessionLocal
from app.models import Engagement, Memo, StageEvent
from app.synthesize import build_memo, build_analyst_summary
from validators.validate_memo import validate_memo_text
from cache.store import cache_get, cache_set
from governance.cost import log_usage
from agents.experts import run_document_expert, run_url_expert
from agents.lead import build_plan
from agents.review_board import review
from pipeline.brakes import over_budget, total_spend

class SwarmState(TypedDict, total=False):
    engagement_id: int
    plan: dict
    memo: str
    scores: dict
    board: dict
    log: list
    status: str
    spend_usd: float
    memo_id: int
    error: str

def _log(engagement_id: int, stage: str, status: str, message: str):
    db = SessionLocal()
    db.add(StageEvent(engagement_id=engagement_id, stage=stage, status=status, message=message))
    db.commit()
    db.close()

def _status(engagement_id: int, status: str):
    db = SessionLocal()
    row = db.get(Engagement, engagement_id)
    if row:
        row.status = status
        db.commit()
    db.close()

def intake(state: SwarmState) -> SwarmState:
    eid = state["engagement_id"]
    _status(eid, "intake")
    _log(eid, "intake", "ok", "engagement loaded")
    return {**state, "log": list(state.get("log", [])) + ["intake"], "status": "intake"}

def plan(state: SwarmState) -> SwarmState:
    eid = state["engagement_id"]
    db = SessionLocal()
    engagement = db.get(Engagement, eid)
    db.close()
    built = build_plan(
        engagement.company_name if engagement else "unknown",
        getattr(engagement, "objective", "") or "",
    )
    _status(eid, "plan")
    _log(eid, "lead_plan", "ok", json.dumps(built))
    return {**state, "plan": built, "log": list(state.get("log", [])) + ["lead_plan"], "status": "plan"}

def gather(state: SwarmState) -> SwarmState:
    eid = state["engagement_id"]
    _status(eid, "gather")
    doc_notes = run_document_expert(eid)
    url_notes = run_url_expert(eid)
    _log(eid, "document_expert", "ok", "; ".join(doc_notes) or "no pdf")
    _log(eid, "url_expert", "ok", "; ".join(url_notes) or "no url")
    return {**state, "log": list(state.get("log", [])) + ["gather"], "status": "gather"}

def write(state: SwarmState) -> SwarmState:
    eid = state["engagement_id"]
    if over_budget(eid):
        _status(eid, "aborted")
        _log(eid, "budget_guardrail", "abort", f"spend={total_spend(eid)}")
        return {**state, "status": "aborted", "error": "over budget"}
    _status(eid, "write")
    cache_key = hashlib.sha256(f"write:{eid}:v21".encode()).hexdigest()
    cached = cache_get("section", cache_key)
    if cached:
        memo_text = cached
        log_usage(eid, "write", "cache", "write", memo_text, cache_hit=True)
        _log(eid, "write", "cache_hit", "memo reused at $0")
        note = "write cache hit"
    else:
        memo_text = build_memo(eid, use_llm=False)
        cache_set("section", cache_key, memo_text)
        log_usage(eid, "write", "llama3.2", "write-prompt", memo_text, cache_hit=False)
        _log(eid, "write", "ok", "llm memo drafted")
        note = "write llm"
    return {**state, "memo": memo_text, "log": list(state.get("log", [])) + [note], "status": "write"}

def validate(state: SwarmState) -> SwarmState:
    eid = state["engagement_id"]
    memo_text = state.get("memo", "")
    scores = validate_memo_text(eid, memo_text)
    board = review(scores)
    db = SessionLocal()
    row = Memo(engagement_id=eid, mode="llm", body=memo_text, disposition=board["decision"])
    db.add(row)
    db.commit()
    db.refresh(row)
    memo_id = row.id
    db.close()
    _log(eid, "validate", scores["disposition"], f"unsupported={scores.get('unsupported_claim_count')}")
    _log(eid, "review_board", board["decision"], board["reason"])
    _status(eid, "needs_review")
    _log(eid, "arbitrate", "needs_review", "analyst must accept or reject")
    return {
        **state,
        "scores": scores,
        "board": board,
        "memo_id": memo_id,
        "spend_usd": total_spend(eid),
        "log": list(state.get("log", [])) + ["validate", f"review_board:{board['decision']}", "needs_review"],
        "status": "needs_review",
    }

def build_graph():
    g = StateGraph(SwarmState)
    g.add_node("intake", intake)
    g.add_node("plan", plan)
    g.add_node("gather", gather)
    g.add_node("write", write)
    g.add_node("validate", validate)
    g.set_entry_point("intake")
    g.add_edge("intake", "plan")
    g.add_edge("plan", "gather")
    g.add_edge("gather", "write")
    g.add_edge("write", "validate")
    g.add_edge("validate", END)
    return g.compile()

GRAPH = build_graph()

def run_graph(engagement_id: int) -> dict:
    result = GRAPH.invoke({"engagement_id": engagement_id, "log": []})
    return {
        "engagement_id": engagement_id,
        "memo_id": result.get("memo_id"),
        "status": result.get("status"),
        "plan": result.get("plan"),
        "memo": result.get("memo"),
        "scores": result.get("scores"),
        "review_board": result.get("board"),
        "spend_usd": result.get("spend_usd"),
        "log": result.get("log"),
        "analyst_summary": build_analyst_summary(engagement_id, result.get("board") or {}, result.get("scores") or {}),
        "engine": "langgraph",
    }
