def build_plan(company_name: str, objective: str = "") -> dict:
    goal = (objective or "").strip() or f"Produce a sourced KYB memo for {company_name}"
    loan_job = any(word in goal.lower() for word in ["loan", "facility", "credit", "lend", "working-capital", "working capital"])
    questions = [
        "What is the legal entity and how does it relate to any parent?",
        "Who owns or controls the company?",
        "What do the documents say about revenue, profit, cash and existing debt?",
        "Is adverse media an allegation or a proven enforcement outcome?",
        "What remains unknown or unaudited?",
    ]
    if loan_job:
        questions = [
            "What facility is being requested, in what amount, and for what use?",
            "What is the legal borrower versus the parent?",
            "Who owns and controls the borrower?",
            "Do the accounts show the company can service existing debt plus the requested facility?",
            "What cash, receivables, current debt and covenants are documented?",
            "Is adverse media an allegation or a fine/finding?",
            "Which figures are unaudited or missing?",
        ]
    return {
        "objective": goal,
        "questions": questions,
        "assignments": {
            "document_expert": ["pdf", "document"],
            "url_expert": ["url", "news", "web"],
        },
        "stop_rules": [
            "Answer the analyst assignment, do not invent a different job",
            "Use only uploaded source text",
            "Do not invent fines, convictions, or missing financials",
            "Unknown is allowed",
            "Do not approve or decline the loan",
        ],
    }
