from pathlib import Path
import requests

API = "http://127.0.0.1:8001/engagements/1/upload"
folders = [
    Path("/Users/tariqkottai/Documents/Programming Practice"),
    Path("/Users/tariqkottai/Documents/Programming Practice/fs-research-swarm"),
    Path.home() / "Desktop",
    Path.home() / "Downloads",
]
files = []
for folder in folders:
    if folder.exists():
        files.extend(folder.glob("Northshore*.pdf"))
        files.extend(folder.glob("*.pdf"))

seen = set()
uniq = []
for f in files:
    if f.name not in seen:
        seen.add(f.name)
        uniq.append(f)

print("FOUND", len(uniq), "pdfs")
for f in uniq:
    print(" ", f)

if not uniq:
    raise SystemExit("No PDFs found")

for f in uniq:
    r = requests.post(API, files={"file": (f.name, f.read_bytes(), "application/pdf")})
    print(f.name, r.status_code, r.text[:200])
