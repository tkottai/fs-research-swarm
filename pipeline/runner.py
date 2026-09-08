from sqlalchemy.orm import Session
from pipeline.graph import run_graph

def run_stages(db: Session, engagement_id: int) -> dict:
    return run_graph(engagement_id)
