from sqlalchemy import String, Float, Integer, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base

class Engagement(Base):
    __tablename__ = "engagements"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_name: Mapped[str] = mapped_column(String)
    jurisdiction: Mapped[str] = mapped_column(String, default="US")
    engagement_type: Mapped[str] = mapped_column(String, default="kyb")
    status: Mapped[str] = mapped_column(String, default="created")
    budget_usd: Mapped[float] = mapped_column(Float, default=5.0)
    analyst_decision: Mapped[str] = mapped_column(String, default="")
    analyst_note: Mapped[str] = mapped_column(Text, default="")
    objective: Mapped[str] = mapped_column(Text, default="")

class Source(Base):
    __tablename__ = "sources"
    id: Mapped[int] = mapped_column(primary_key=True)
    engagement_id: Mapped[int] = mapped_column(ForeignKey("engagements.id"))
    source_type: Mapped[str] = mapped_column(String)
    uri: Mapped[str] = mapped_column(String)
    text: Mapped[str] = mapped_column(Text, default="")

class EvidenceCard(Base):
    __tablename__ = "evidence_cards"
    id: Mapped[int] = mapped_column(primary_key=True)
    engagement_id: Mapped[int] = mapped_column(ForeignKey("engagements.id"))
    claim: Mapped[str] = mapped_column(Text)
    quote: Mapped[str] = mapped_column(Text)
    source_uri: Mapped[str] = mapped_column(String)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)

class ValidationResult(Base):
    __tablename__ = "validation_results"
    id: Mapped[int] = mapped_column(primary_key=True)
    engagement_id: Mapped[int] = mapped_column(ForeignKey("engagements.id"))
    citation_coverage_rate: Mapped[float] = mapped_column(Float, default=0)
    quote_verification_rate: Mapped[float] = mapped_column(Float, default=0)
    unsupported_claim_count: Mapped[int] = mapped_column(Integer, default=0)
    numeric_mismatch_count: Mapped[int] = mapped_column(Integer, default=0)
    disposition: Mapped[str] = mapped_column(String, default="PENDING")
    details: Mapped[dict] = mapped_column(JSONB, default=dict)

class Memo(Base):
    __tablename__ = "memos"
    id: Mapped[int] = mapped_column(primary_key=True)
    engagement_id: Mapped[int] = mapped_column(ForeignKey("engagements.id"))
    mode: Mapped[str] = mapped_column(String, default="llm")
    body: Mapped[str] = mapped_column(Text, default="")
    disposition: Mapped[str] = mapped_column(String, default="PENDING")

class StageEvent(Base):
    __tablename__ = "stage_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    engagement_id: Mapped[int] = mapped_column(Integer)
    stage: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    message: Mapped[str] = mapped_column(Text, default="")

class CacheEntry(Base):
    __tablename__ = "cache_entries"
    id: Mapped[int] = mapped_column(primary_key=True)
    tier: Mapped[str] = mapped_column(String)
    cache_key: Mapped[str] = mapped_column(String)
    payload: Mapped[str] = mapped_column(Text, default="")
    hit_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="valid")

class UsageEvent(Base):
    __tablename__ = "usage_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    engagement_id: Mapped[int] = mapped_column(Integer)
    stage: Mapped[str] = mapped_column(String)
    model: Mapped[str] = mapped_column(String, default="")
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False)
