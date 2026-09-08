Overview:  The purpose of this AI system is to research a company’s background instead of doing it manually in a KYB (Know Your Business) check. Many banks, financial institutions, and businesses that lend money to other businesses in banking & capital markets typically have a process which requires them to do a regulated research on the business. This system never approves or rejects the loan.

A Lead Researcher coordinates the swarm and the work is split into steps (Find sources -> Extract content -> Analyze -> Write up) and those steps run in parallel.    This tool is a grounded research swarm that analyzes the sourced findings against 8 needles:  - Borrower - Checks for who is the legal operating company?
Ownership - Checks for who owns or controls it?
Facility - Checks for Loan amount against and the current obligations and $XXX facility requested
Existing Debt - Checks for what debt is already in place?
Liquidity - What cash / liquidity is in the files?
Earnings - What profit / EBITDA is in the sources?
Adverse Media - Checks for reputation - Allegation vs fine?
Limits - What remains unknown?

Each of the 8 needles outputs one Card:  Each card:
Needle name (Ownership)
Claim — the finding the agent is putting on the file
Quote — the span taken from which PDF
Grounding — in file / not in file, and why
Judge — supported / overstated / unsupported
Needle decision — Pass or Fail for this question

The system starts by a user attaching in the company or client name, documents / PDFs, and optional URLs. The system plans the research, runs parallel experts (swarm), loops on gaps, audits for hallucinations (code validators & model grader), and produces an initial memo for diligence assessment, allowing a human to either Approve or Reject. 

intake
  → plan
  → gather (document expert + URL expert)
  → write
  → validate
  → review board
  → analyst accept or reject


Here are the hallucination & evaluation scoring mechanisms: 
Grounding score for how many quotes are in the files
Quality metric score on every single one of the 8 output records and coverage score to check how many of the 8 needles are (Python logic / code grader)
String matching citation coverage rate: how much of the answers is backed by sources? Does the quote exist in source? Numbers/date match? (Python logic / code grader)
Overstatement judging between claims and quotes (Model grader)
If the answer was already computed, system records $0 for that step (Caching)

Memo: 
The LLM will draft the memo from the evidence cards. In this workflow, any statement that is not backed by a real passage in the file will be considered a hallucination. The system forces every important sentence to bring proof. 
