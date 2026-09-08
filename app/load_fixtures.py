from pathlib import Path
from app.db import SessionLocal
from app.models import Source

ENGAGEMENT_ID = 1
FIXTURE_DIR = Path("fixtures/northshore")

FILES = {
    "website.txt": "url",
    "group_structure.txt": "pdf",
    "news.txt": "news",
}

db = SessionLocal()

for filename, source_type in FILES.items():
    path = FIXTURE_DIR / filename
    text = path.read_text()
    row = Source(
        engagement_id=ENGAGEMENT_ID,
        source_type=source_type,
        uri=str(path),
        text=text,
    )
    db.add(row)

db.commit()
print("Loaded sources for engagement 1")
db.close()
