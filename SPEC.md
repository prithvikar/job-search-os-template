# Job Search OS — Spec Sheet (interfaces & contracts)

Companion to `DESIGN.md`. This is the machine-facing contract layer: exact I/O for each agent, file schemas, and command surface. Drop into Claude Code alongside the sub-agent files.

---

## A. Command surface (slash commands → orchestrator)

| Command | Triggers | Notes |
|---|---|---|
| `/nightly` | full batch pipeline | cron-equivalent; produces daily briefing |
| `/source` | sourcing-agent | refresh role queue |
| `/score {company} {role}` | fit-scoring-agent | writes `fit-score.md` |
| `/intel {company}` | company-intel-agent | writes `dossier.md` |
| `/compose {company} {role}` | resume-composer → critic loop | writes critic-passed resume |
| `/critic {file}` | authenticity-critic standalone | returns score + fixes |
| `/refer {company}` | referral-mapper | human-assisted capture flow |
| `/prep {company}` | interview-prep-agent | writes `prep-{company}.md` |
| `/debrief {company}` | debrief-extractor | appends interview-history |
| `/negotiate {company}` | negotiation-agent | comp data + scripts |
| `/calibrate` | scripts/calibrate.py | re-tunes scoring weights |

---

## B. Agent I/O contracts

### B.1 sourcing-agent
- **in:** `profile/constraints.md`, target company list (or discovery query)
- **tools:** Firecrawl `scrape` (GREEN sources only), web_search
- **out:** append to `pipeline/app-tracker.md` with state `SOURCED`
- **guardrail:** hard-filter on constraints BEFORE any scoring compute; dedupe against tracker

### B.2 fit-scoring-agent
- **in:** parsed JD vector, `evidence-ledger.md`, `scoring-weights.yaml`, referral reachability signal
- **out:** `companies/{company}/fit-score.md` — must include the score *decomposition* (per-term contribution), not just a number
- **contract:** every score is logged with inputs so `calibrate.py` can grade it later

### B.3 company-intel-agent
- **in:** company name, role
- **tools:** Antigravity CLI + Firecrawl (GREEN), web_search
- **out:** `dossier.md` — org structure, products, recent moves, *current* interview loop structure, discoverable interviewer chain
- **guardrail:** GREEN sources only; cite source URL per fact

### B.4 resume-composer
- **in:** parsed JD, `evidence-ledger.md`, `voice-sample.md`, `narrative-arc.md`
- **out:** `resume-{role}.md`
- **HARD INVARIANT:** selects only from ledger entries; no invented metric/tool/claim; unmet requirements → gap report to human, never fabricated
- **anti-fingerprint:** vary lead narrative per company, not synonym-swap a fixed skeleton

### B.5 authenticity-critic
- **in:** resume or outreach artifact, `voice-sample.md`, set of other submitted resumes (for cross-app check)
- **out:** `{score: int, pass: bool, fabrication_flags: [], fixes: []}`
- **contract:** pass requires score ≥ 80 AND zero fabrication flags; on fail, return specific actionable fixes; max 3 revise loops then escalate

### B.6 referral-mapper
- **in:** `dossier.md`, human-supplied network capture (CSV export / manual)
- **out:** `referral-paths.md` — ranked 2nd-degree paths + drafted intros
- **guardrail:** NO autonomous LinkedIn scrape; drafts gated by critic at higher bar; require a dossier-cited specific hook per message

### B.7 interview-prep-agent
- **in:** `dossier.md`, `interviews/interview-history.md`, role type
- **out:** `prep-{company}.md` — structured for the *actual* loop (e.g., behavioral memo for Amazon, product-sense + live prototyping for Meta AI track, estimation for Scale)

### B.8 debrief-extractor
- **in:** human-supplied raw interview recall
- **out:** append to `interview-history.md`: `{question_type, your_score, what_was_probed, value_left_on_table}`
- **effect:** auto-targets weakest question categories in next `/prep`

### B.9 negotiation-agent
- **in:** offer details, `constraints.md`, market comp data
- **tools:** web_search (live comp ranges)
- **out:** leverage points + exact scripts; gated on constraints floor
- **guardrail:** no number sent without human approval

---

## C. File schemas

### C.1 evidence-ledger entry (YAML list item)
```yaml
- id: string                 # unique
  raw: string                # the accomplishment as stated
  metrics: {key: value}      # quantified outcomes
  domain_tags: [string]
  evidence_strength: high|medium|low
  verifiable_via: [string]   # linkedin | manager-reference | public-press | github | ...
  reuse_count: int
  last_used: date
```

### C.2 fit-score.md frontmatter
```yaml
company: string
role: string
score: int                   # 0-100
decomposition:
  requirement_coverage: float
  domain_overlap: float
  seniority_match: float
  referral_reachability: float
  unmet_hard_penalty: float
gaps: [string]               # unmet requirements surfaced to human
scored_at: datetime
```

### C.3 app-tracker entry
```yaml
- company: string
  role: string
  state: SOURCED|SCORED|INTEL_DONE|DRAFTED|CRITIC_PASSED|REFERRAL_ATTEMPTED|SUBMITTED|SCREEN|ONSITE|OFFER|CLOSED
  fit_score: int
  referral_attempted: bool
  transitions:
    - {to: string, at: datetime, outcome: string, notes: string}
```

### C.4 scoring-weights.yaml
```yaml
w1_requirement_coverage: 0.30
w2_domain_overlap: 0.20
w3_seniority_match: 0.15
w4_referral_reachability: 0.25
penalty_unmet_hard: 0.40
# updated by scripts/calibrate.py against app-tracker outcomes
```

---

## D. Scraping invocation patterns

```bash
# GREEN source — render a JS-heavy career page to clean markdown
firecrawl scrape "https://boards.greenhouse.io/{company}/jobs/{id}" > companies/{company}/jd-raw.md

# Interactive flow (paginated listings)
firecrawl browser --prompt "load all role listings on this careers page, extract title+location+url"

# Antigravity CLI for multi-step intel gathering (GREEN only)
agy "Scrape {company} careers + last 6mo press; summarize org, products, recent moves into dossier format"
```

RED sources (LinkedIn) → human-assisted capture only. No script targets them.

---

## E. Definition of done (per artifact)

- **Resume:** critic ≥ 80, zero fabrication flags, every claim ledger-traceable, narrative distinct from other submissions.
- **Referral msg:** critic-passed at higher bar, dossier-cited hook, human-approved before send.
- **Fit score:** decomposition logged, gradable by calibrate.py.
- **Prep doc:** mapped to the company's *current* actual loop structure.
- **Briefing:** decision-shaped (ratify, don't author), ≤ 20 min human review.
