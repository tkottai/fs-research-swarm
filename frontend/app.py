import requests
import pandas as pd
import streamlit as st

API = "http://127.0.0.1:8001"

NEEDLES = [
    ("borrower", "Borrower", "Who is the legal operating company?"),
    ("ownership", "Ownership", "Who owns or controls it?"),
    ("facility", "Facility", "What $100k facility is requested?"),
    ("existing_debt", "Existing debt", "What debt is already in place?"),
    ("liquidity", "Liquidity", "What cash / liquidity is in the pack?"),
    ("earnings", "Earnings", "What profit / EBITDA is in the pack?"),
    ("adverse_media", "Adverse media", "Allegation vs fine?"),
    ("limits", "Limits", "What is unaudited or unknown?"),
]

KEYS = {
    "ownership": ["owns 80", "80%", "holdings plc"],
    "earnings": ["ebitda", "4820000", "4,820,000", "profit after tax"],
    "existing_debt": ["480000", "480,000", "term loan", "barclays"],
    "liquidity": ["410000", "410,000", "190000", "190,000", "cash equivalents"],
    "facility": ["working-capital", "working capital", "100000", "100,000"],
    "adverse_media": ["investigat", "alleged onboarding"],
    "limits": ["unaudit", "no fine"],
    "borrower": ["merchant acquir", "payments ltd"],
}

def needles_for(claim: str, quote: str) -> list[str]:
    blob = f"{claim} {quote}".lower().replace(",", "").replace("$", "")
    hits = [name for name, keys in KEYS.items() if any(k.replace(",", "") in blob for k in keys)]
    return hits or ["other"]

st.set_page_config(page_title="fs-research-swarm", layout="wide")
st.title("KYB first-pass workbench")

eid = st.sidebar.number_input("Engagement ID", min_value=1, value=1)
files = st.sidebar.file_uploader("4 documents", type=["pdf", "txt"], accept_multiple_files=True)
if st.sidebar.button("Save attachments") and files:
    for f in files:
        r = requests.post(f"{API}/engagements/{eid}/upload", files={"file": (f.name, f.getvalue(), f.type or "application/octet-stream")}, timeout=60)
        st.sidebar.write(f.name, r.status_code)

if st.button("Run swarm", type="primary"):
    r = requests.post(f"{API}/engagements/{eid}/run", timeout=300)
    st.session_state["run"] = r.json() if r.text.strip().startswith("{") else None
    st.session_state["raw"] = r.text
c1, c2 = st.columns(2)
with c1:
    if st.button("Accept file"):
        requests.post(f"{API}/engagements/{eid}/accept", json={"note": "Accept file. Loan not approved."}, timeout=15)
with c2:
    if st.button("Reject file"):
        requests.post(f"{API}/engagements/{eid}/reject", json={"note": "Reject file."}, timeout=15)

eng = requests.get(f"{API}/engagements/{eid}", timeout=10).json()
tables = requests.get(f"{API}/debug/tables", timeout=10).json()
st.header("Band 1 — Job")
st.info(eng.get("objective") or "Assess Northshore Payments Ltd for a $100,000 working-capital loan.")
st.caption("Pack = the files uploaded to this engagement.")
st.dataframe(pd.DataFrame(tables.get("sources", [])), use_container_width=True)

run = st.session_state.get("run")
if not run:
    if st.session_state.get("raw"):
        st.error(st.session_state["raw"][:2000])
    st.stop()

scores = run.get("scores") or {}
board = run.get("review_board") or {}
coverage = board.get("coverage") or scores.get("coverage") or {}
details = scores.get("details") or []
covered = coverage.get("covered") or {}

by_needle = {n: [] for n, _, _ in NEEDLES}
for row in details:
    for name in needles_for(row.get("claim") or "", row.get("quote") or ""):
        if name in by_needle:
            by_needle[name].append(row)

st.header("Band 2 — 8 needles")
st.dataframe(pd.DataFrame([
    {"Needle": title, "Question": q, "Status": "Yes" if covered.get(key) else "Missing"}
    for key, title, q in NEEDLES
]), use_container_width=True, hide_index=True)

st.header("Band 3 — Claim, quote, needle decision")
for key, title, question in NEEDLES:
    items = by_needle.get(key) or []
    with st.container(border=True):
        st.markdown(f"### {title}")
        st.caption(question + "  |  Status: " + ("Yes" if covered.get(key) else "Missing"))
        if not items:
            st.warning("Coverage may be Yes from another sentence. No card grouped here.")
            continue
        for row in items:
            grounded = row.get("quote_found")
            judge = row.get("judge_label") or "n/a"
            decision = "Pass" if grounded and judge != "overstated" else "Fail"
            st.markdown(f"**Claim:** {row.get('claim')}")
            st.markdown(f"**Quote:** {row.get('quote')}")
            st.write(f"Grounding: {'in file' if grounded else 'not in file'} · Judge: {judge} · Needle decision: **{decision}**")

st.header("Band 4 — Decision engine")
st.write("Coverage:", coverage.get("coverage_rate"), "Missing:", coverage.get("missing") or "none")
st.success(f"Board: {board.get('decision')} — {board.get('reason')}")
st.header("Analyst memo")
st.text(run.get("analyst_summary") or "")
st.header("Cache / memory")
st.dataframe(pd.DataFrame(tables.get("cache_entries", [])), use_container_width=True)
st.dataframe(pd.DataFrame(tables.get("usage_events", [])), use_container_width=True)
