# Job Search OS — Functional & Technical Design Doc

**Status:** v1.0 spec · **Runtime:** Claude Code + Antigravity CLI (scraping) + Firecrawl (JS rendering)
**Last updated:** 2026-05-28

---

## 0. TL;DR

A file-based, agentic job-search pipeline that runs mostly overnight and presents you a decision-shaped morning briefing. It is **not** a content-generation tool. It is a **credibility-and-coverage optimization system operating in an adversarial environment** — the adversary being the recruiter-side ATS + AI detector + verification stack.

The four things that make it defensible (and that most "AI job apps" get wrong):

1. **Evidence ledger** — every resume claim traces to a source-tagged, verifiable accomplishment. Fabrication is structurally impossible, not just discouraged.
2. **Authenticity critic** — an adversarial sub-agent red-teams every artifact the way the opposing AI would, *before* a human sees it.
3. **Referral-first scoring** — network reachability is an input to fit score, because 6% of applications produce 37% of hires.
4. **Calibrated outcome loop** — fit scores are falsifiable predictions graded against real callback data; interview debriefs become labeled training data.

---

## 1. Problem statement & threat model

### 1.1 The 2026 hiring reality (design constraints, not background)

| Reality | Source signal | Design consequence |
|---|---|---|
| ATS rejects ~75% of resumes in <5s | 2026 ATS benchmarks | Machine-readability is a hard gate, not a nicety |
| ~78% of applications now contain AI content | hiring reports | Volume is commoditized; volume ≠ edge |
| ~77–83% of employers screen for "too AI-generated" text | Resume Now / employer surveys | **Polish is now a negative signal** |
| 62% reject resumes lacking authentic personal detail | Resume Now | Specificity > eloquence |
| Recruiters moving to upstream verification (employment data, social checks, skills tests) | TA trust-crisis reporting | A claim that fails a reference check is net-negative |
| Referrals: 6% of apps → 37% of hires; 40–65% interview rate vs 2–8% cold | multiple 2026 referral reports | Referral coverage is the dominant lever |
| Proprietary-tool name-dropping = instant fraud flag | recruiter firsthand reports | Never claim what the ledger can't verify |

### 1.2 Objective function

```
maximize   Σ (credible_signal_per_application × referral_coverage)
subject to fabrication = 0
           detectability < adversary_threshold
           claims survive reference/skills verification
           human_time ≤ ~20 min/day on decision-shaped surface
```

The naive objective ("more tailored applications") is explicitly rejected. We optimize signal density and conversion, not throughput.

### 1.3 Non-goals

- Mass auto-apply / spray-and-pray.
- Autonomous sending of anything (all sends are human-gated).
- Scraping platforms in violation of their TOS (see §6).
- Generating any claim a human can't defend in an interview room.

---

## 2. System overview

```
                          ┌─────────────────────────┐
                          │   orchestrator (nightly) │
                          └────────────┬────────────┘
        ┌──────────────┬───────────────┼───────────────┬──────────────┐
        ▼              ▼               ▼               ▼              ▼
 ┌────────────┐ ┌────────────┐ ┌─────────────┐ ┌────────────┐ ┌─────────────┐
 │ sourcing   │ │fit-scoring │ │company-intel│ │  resume-   │ │authenticity │
 │  agent     │ │  agent     │ │   agent     │ │ composer   │ │  critic     │◄─┐
 └────────────┘ └────────────┘ └─────────────┘ └─────┬──────┘ └──────┬──────┘  │
                                                      │  loop until pass│         │
                                                      └────────────────┘─────────┘
        ┌──────────────┬───────────────┬───────────────┬──────────────┐
        ▼              ▼               ▼               ▼              ▼
 ┌────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ ┌─────────────┐
 │ referral-  │ │ interview-  │ │  debrief-   │ │negotiation │ │  briefing   │
 │  mapper    │ │ prep-agent  │ │ extractor   │ │  agent     │ │  writer     │
 └────────────┘ └─────────────┘ └─────────────┘ └────────────┘ └─────────────┘

 Tooling layer:  Claude Code (orchestration, file I/O, reasoning)
                 Antigravity CLI + Firecrawl (JS-heavy scraping: career pages, ATS JDs, news)
                 Human-in-the-loop capture (LinkedIn / network — NEVER autonomous scrape)
```

### 2.1 Execution modes

- **Nightly batch** (cron): sourcing → scoring → intel → compose → critic → referral-map → briefing. Produces `pipeline/daily-briefing-{date}.md`.
- **On-demand**: any single agent invocable from Claude Code (`/source`, `/score {company}`, `/prep {company}`, etc. via slash-command wrappers).
- **Post-interview**: `debrief-extractor` run manually after each interview.

### 2.2 The 20-minute morning loop

The human is a **ratifier**, not an author. The briefing presents pre-built decisions:
- Roles scored + ranked (with the score *explained*).
- Resumes drafted + critic-passed (you approve/edit, then send).
- Referral paths drafted (you approve/send).
- Prep queued for upcoming interviews.

Autonomy is full on reversible actions (research, draft, score). It **stops hard** at every irreversible action (any send, any negotiation number).

---

## 3. Data model (state = the moat)

All state is markdown + YAML frontmatter, version-controlled in git. Append-only where possible. Provenance on every claim.

### 3.1 Directory tree

```
job-search-os/
├── CLAUDE.md                      # system constitution (loaded every session)
├── DESIGN.md                      # this doc
├── SPEC.md                        # interface/contract spec sheet
├── profile/
│   ├── evidence-ledger.md         # atomic, source-tagged accomplishments (THE spine)
│   ├── voice-sample.md            # real writing samples for style grounding
│   ├── constraints.md             # comp floor, location, visa, dealbreakers
│   └── narrative-arc.md           # the throughline a recruiter should infer
├── context-library/
│   ├── domain-glossary.md         # YOUR real domain terms (DICOM/HL7/PACS etc.)
│   └── frameworks.md              # how you actually reason, in your words
├── companies/
│   ├── _template/                 # copy this per target
│   └── {company}/
│       ├── dossier.md
│       ├── jd-{role}.md
│       ├── fit-score.md
│       ├── resume-{role}.md
│       └── referral-paths.md
├── pipeline/
│   ├── app-tracker.md             # state machine per application
│   ├── scoring-weights.yaml       # tunable; updated by calibration loop
│   └── daily-briefing-{date}.md
├── interviews/
│   ├── prep-{company}.md
│   └── interview-history.md       # compounding eval loop
├── sub-agents/                    # agent definitions (see §4)
└── scripts/
    ├── scrape.sh                  # Antigravity + Firecrawl wrappers
    └── calibrate.py               # scoring calibration harness
```

### 3.2 Core schema — `evidence-ledger.md` entry

```yaml
- id: vax-platform-01
  raw: "Owned roadmap for state vaccine distribution platform serving 4M residents"
  metrics: {scale: "4M residents", uptime: "99.9%", timeline: "8mo to GA"}
  domain_tags: [healthcare, HL7, public-sector, roadmap-ownership]
  evidence_strength: high        # high | medium | low
  verifiable_via: [linkedin, manager-reference, public-press]
  reuse_count: 3
  last_used: 2026-05-20
```

**Invariant:** the composer may ONLY select from ledger entries. It may rephrase for fit; it may NOT invent a metric, tool, or claim. Unmet JD requirements surface as gaps to the human — never as fabricated content.

### 3.3 `app-tracker.md` state machine

```
States: SOURCED → SCORED → INTEL_DONE → DRAFTED → CRITIC_PASSED
        → REFERRAL_ATTEMPTED → SUBMITTED → SCREEN → ONSITE → OFFER → CLOSED
Each transition logs: timestamp, outcome, notes.
Outcomes feed the calibration harness (§5.3).
```

---

## 4. Agent specifications

Each sub-agent has: **scope**, **inputs**, **tools**, **output contract**, **guardrails**. Full definitions in `/sub-agents/`. Summary:

| Agent | Scope | Key tools | Output |
|---|---|---|---|
| `sourcing` | Find + dedupe roles vs constraints | Firecrawl scrape (career pages/ATS), web search | role queue |
| `fit-scoring` | Calibrated role↔profile score incl. referral reachability | ledger read, scoring-weights.yaml | `fit-score.md` |
| `company-intel` | Build dossier from safe sources | Antigravity+Firecrawl, web search | `dossier.md` |
| `resume-composer` | Assemble from ledger ONLY | ledger read, JD parse | `resume-{role}.md` |
| `authenticity-critic` | Adversarial pre-screen | rubric (§4.1) | pass/fail + fixes |
| `referral-mapper` | Map warm paths, draft intros | human-assisted capture | `referral-paths.md` |
| `interview-prep` | Company-specific prep | dossier + interview-history | `prep-{company}.md` |
| `debrief-extractor` | Interview → labeled data | — | append `interview-history.md` |
| `negotiation` | Market data + leverage + scripts | web search, constraints | scripts |
| `briefing-writer` | Assemble decision surface | all of the above | `daily-briefing-{date}.md` |

### 4.1 `authenticity-critic` rubric (the adversarial gate)

Scores each artifact 0–100 on a rubric derived from how the opposing system scores. **Threshold to pass: ≥ 80, AND zero fabrication flags.**

| Check | Fail condition | Weight |
|---|---|---|
| Buzzword density | generic superlatives w/o evidence | 20 |
| Metric concreteness | claims lack specific, quantified outcomes | 20 |
| Demonstrated > claimed | skills asserted not shown via scope/outcome | 15 |
| Voice match | diverges from `voice-sample.md` cadence | 15 |
| Machine-readability | format breaks ATS parse | 10 |
| Fabrication scan | any claim not traceable to ledger `verifiable_via` | **HARD FAIL** |
| Cross-application fingerprint | structurally identical to other submitted resumes | 10 |
| Verification survivability | lead claims can't survive reference/skills check | 10 |

On fail → return specific fixes → composer revises → re-score. Max 3 loops, then escalate to human with the gap.

---

## 5. Scoring & calibration

### 5.1 Fit score

```
fit = w1·requirement_coverage      # from ledger match to parsed JD vector
    + w2·domain_overlap
    + w3·seniority_match
    + w4·referral_reachability      # reachability is PART of fit
    − penalty·unmet_hard_requirements
```

Weights live in `pipeline/scoring-weights.yaml`, default `{w1:0.30, w2:0.20, w3:0.15, w4:0.25, penalty:0.40}`.

### 5.2 Why referral_reachability is in the score

A 70-fit role with a warm 2nd-degree path beats an 85-fit role with zero network penetration. Conversion math (37% of hires from 6% of apps; 40–65% vs 2–8% interview rates) dominates marginal fit. This is the single biggest correction vs. naive designs.

### 5.3 Calibration harness (`scripts/calibrate.py`)

The score is a **prediction you can grade**. After outcomes land in `app-tracker.md`:
- Bucket predicted-fit vs actual callback/advance rate.
- Compute calibration gap per bucket.
- Suggest weight adjustments (gradient on logged outcomes).
- Flag systematic over/under-confidence.

Same pattern as a trading-system backtest validator: the model must be falsifiable and self-correcting, or the score is astrology.

---

## 6. Scraping architecture & legal boundary

### 6.1 Tooling

- **Antigravity CLI** (Google): terminal agent — multi-step reasoning, tool calling, persistent history. Good at driving JS-heavy flows.
- **Firecrawl** (via MCP or CLI): renders JS, returns clean markdown. `scrape` for static-after-render pages, `browser` for interactive. Install: `npx -y firecrawl-cli@latest init --all --browser`.

### 6.2 GREEN sources — autonomous scrape OK

Company career pages, ATS-hosted JDs (Greenhouse/Lever/Ashby URLs), funding/news, engineering blogs, public interview-experience sites (Exponent/Glassdoor/IGotAnOffer), conference speaker lists, public GitHub orgs.

### 6.3 RED sources — NEVER autonomous scrape

**LinkedIn and any login-walled platform.** Rationale (this is a strategy decision, not just compliance):
- Scraping LinkedIn violates its User Agreement; detection bans the *scraping* account — i.e., YOUR account.
- Your LinkedIn identity + network is the core asset of the referral channel (the dominant lever). Banning it torches the highest-value part of the pipeline.
- Mass-personalized scraped outreach has the same fingerprint recruiters now hunt as synthetic-candidate fraud (velocity, location signals, templated tone).

### 6.4 Sanctioned network discovery (human-in-the-loop)

- LinkedIn's own connections **export** (CSV) + official API surface where available.
- **Manual capture**: you browse logged in as yourself; the agent structures what *you* surface.
- Public, non-LinkedIn org mapping (team pages, GitHub, conference lists).

Network discovery is human-gated for the **same reason** sends are: it concentrates legal + credibility risk.

---

## 7. Human-in-the-loop gates

| Action | Autonomy |
|---|---|
| Sourcing, scoring, intel, drafting, critic scoring | ✅ full auto |
| Network discovery / LinkedIn capture | 🟡 human-assisted |
| Any send (application, referral msg, follow-up) | 🔴 human approval required |
| Any negotiation number | 🔴 human approval required |
| Any claim flagged `evidence_strength: medium/low` | 🔴 human review required |

---

## 8. Build sequence (MVP → full)

Sequenced to validate the riskiest assumption first (does output survive the adversary?).

1. **Core loop:** `evidence-ledger` + `resume-composer` + `authenticity-critic`. Proves output quality.
2. **Falsifiability:** `app-tracker` + calibration harness. Scores become gradable immediately.
3. **Dominant lever:** `referral-mapper` (human-assisted capture).
4. **Compounding moat:** interview debrief loop.
5. **Remainder:** sourcing automation, intel, negotiation, briefing polish.

---

## 9. Risks & mitigations (pressure-tested as the recruiter/adversary)

| Failure mode | Adversary detects via | Mitigation |
|---|---|---|
| Tailoring fingerprint | near-duplicate resumes across one candidate | vary at narrative level, not synonym-swap; critic cross-app check |
| Verification wall | reference/skills test vs claim | `evidence_strength` + `verifiable_via`; refuse to lead with unverifiable claims |
| AI-text detection | "too polished" phrasing | voice-match gate; specificity over eloquence |
| Templated outreach | low reply + velocity signals | referral drafts held to higher critic bar; require dossier-cited hook |
| Score drift | — (internal) | calibration harness feeds outcomes back into weights |
| LinkedIn ban | scraping detection | RED-source policy; human-assisted capture only |
| Disclosure norms | direct "did you use AI?" | never produce anything you can't honestly own |

---

## 10. Substack article hooks (for later write-up)

Threadable narrative angles this build supports:
- "I treated the recruiter's AI as an adversary and redesigned my job search as a security problem."
- "The counterintuitive move: making my resume *less* polished to beat the AI detector."
- "Why referral reachability belongs in your fit score — the 6%/37% rule."
- "Building a falsifiable job search: my fit scores were predictions I could grade."
- "The one automation that would've gotten me banned (and the human-in-the-loop fix)."
- Architecture deep-dive: file-based agent state as a compounding personal moat.
