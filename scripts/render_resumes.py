#!/usr/bin/env python3
"""Render tailored resumes into a clean, exact-format 1-page template.

This is the rendering ENGINE for the Job Search OS template. It ships with ONE
example role ("example") built from placeholder bullets so you can run it
immediately and see a 1-page PDF. Replace the placeholders with your own real,
ledger-backed content (see profile/evidence-ledger.md) before using it for a
real application.

Layout it produces (matches a common 1-page format): 0.5in margins,
Times New Roman ~10.5pt, small-caps bold centered name, ruled UPPERCASE section
headers, "Company - title; location" with right-aligned dates, italic project
sub-headers, middot bullets, an Education row, and labeled Additional-Information
lines.

Renders HTML -> PDF via headless Chrome/Chromium.
Run:  python3 scripts/render_resumes.py [slug]
      (no slug renders every role in ROLES)
"""
import os, subprocess, sys

# --- Paths ---------------------------------------------------------------
# ROOT is the repo root (this file lives in <repo>/scripts/).
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Point CHROME at your local Chrome/Chromium. The script falls back to a few
# common locations; override with the CHROME env var if yours lives elsewhere.
CHROME = os.environ.get("CHROME") or next(
    (p for p in [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
    ] if os.path.exists(p)),
    "google-chrome",
)

# --- Your contact line (EDIT THIS) --------------------------------------
# &nbsp; and &bull; render as non-breaking spaces and bullet separators.
CONTACT = ("you@example.com &nbsp;&bull;&nbsp; (555) 555-0100 &nbsp;&bull;&nbsp; "
           "linkedin.com/in/your-handle &nbsp;&bull;&nbsp; github.com/your-handle")

# --- Your education (EDIT THIS) -----------------------------------------
EDUCATION = {
    "school": "State University",
    "lines": ["Bachelor of Science",
              "Major: Your Major",
              "Optional certificate or honor line"],
    "date": "May 2020",
}

CSS = """
@page { size: Letter; margin: 0.5in; }
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family: "Times New Roman", Times, serif; font-size: 10.5pt; line-height: 1.16; color:#000; }
.name { text-align:center; font-weight:bold; font-size: 19pt; font-variant: small-caps; letter-spacing:.5pt; }
.contact { text-align:center; font-size: 10.5pt; margin-bottom: 5pt; }
.summary { text-align:justify; margin-bottom: 3pt; }
h2 { font-size: 11pt; font-weight:bold; text-transform:uppercase; letter-spacing:.5pt;
     border-bottom: 1.4px solid #000; margin: 7pt 0 3pt; padding-bottom:1pt; }
.job { display:flex; justify-content:space-between; align-items:baseline; }
.job .l { } .job .r { white-space:nowrap; padding-left:8pt; }
.sub { font-style:italic; margin-top:2pt; }
ul { list-style:none; margin: 1pt 0 2pt; }
li { position:relative; padding-left:11pt; text-align:justify; margin-bottom:1.5pt; }
li:before { content:"\\00B7"; position:absolute; left:2pt; font-weight:bold; }
.edu { display:flex; justify-content:space-between; align-items:baseline; }
.edu .mid { flex:1; padding-left:14pt; }
.add div { margin-bottom:1.5pt; }
"""

def li(items): return "<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>"

def render_html(d):
    parts = [f'<div class="name">{d["name"]}</div>',
             f'<div class="contact">{CONTACT}</div>',
             f'<div class="summary">{d["summary"]}</div>',
             '<h2>Experience</h2>']
    for job in d["experience"]:
        parts.append(f'<div class="job"><span class="l"><b>{job["company"]}</b> &ndash; <i>{job["title"]}</i>; {job["loc"]}</span><span class="r">{job["date"]}</span></div>')
        if job.get("bullets"): parts.append(li(job["bullets"]))
        for sp in job.get("subprojects", []):
            parts.append(f'<div class="sub">{sp["title"]}</div>')
            parts.append(li(sp["bullets"]))
    e = EDUCATION
    parts.append('<h2>Education</h2>')
    parts.append(f'<div class="edu"><span class="l"><b>{e["school"]}</b></span>'
                 f'<span class="mid">{"<br>".join(e["lines"])}</span>'
                 f'<span class="r">{e["date"]}</span></div>')
    parts.append('<h2>Additional Information</h2>')
    parts.append('<div class="add">' + "".join(f"<div>{x}</div>" for x in d["additional"]) + '</div>')
    body = "\n".join(parts)
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"

def render(slug, d):
    outdir = os.path.join(ROOT, "companies", d["dir"])
    os.makedirs(outdir, exist_ok=True)
    hp = os.path.join(outdir, f"{slug}.html")
    pp = os.path.join(outdir, f"{slug}.pdf")
    open(hp, "w").write(render_html(d))
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pp}", f"file://{hp}"],
                   capture_output=True)
    pages = "?"
    try:
        from pypdf import PdfReader
        pages = len(PdfReader(pp).pages)
    except Exception:
        pass
    print(f"{slug}: {pp}  pages={pages}")
    return pp

# ---- Shared bullet bank -------------------------------------------------
# Keep ALL of your resume bullets here, keyed by a short id. Each bullet must
# trace to an entry in profile/evidence-ledger.md (zero fabrication). Reusing
# from one bank keeps every resume consistent and easy to retarget per role.
# Use plain text, no em dashes (use commas/parentheses); the &ndash; entity is
# only for date ranges and the "Company - title" separator.
B = {
 "role1_a": "Led a cross-functional team that shipped X, improving Y by Z% against baseline",
 "role1_b": "Built an evaluation framework (N test cases, holdback experiments) to validate the product before launch, and designed the guardrails that kept it compliant in production",
 "proj_a":  "Owned the roadmap and $X budget for an initiative, sequencing deployments and allocating resources to hit quarterly objectives",
 "proj_b":  "Designed and delivered a system that automated a manual expert-review workflow, reducing turnaround time by Z%",
 "proj_c":  "Consolidated N legacy systems into one platform serving X users, streamlining core workflows and reducing operational overhead",
 "edu_a":   "Designed the experiment, collected quantitative and qualitative data, and evaluated the hypothesis",
}

# ---- Additional-information block (EDIT THIS) ---------------------------
ADDITIONAL = [
    "<b>Technical Skills:</b> Python, SQL, (your tools here)",
    "<b>Product &amp; AI:</b> Roadmap and backlog management, Agile/Scrum, evaluation frameworks, AI/ML product development",
    "<b>Languages:</b> Fluent in English",
    "<b>Work Eligibility:</b> Eligible to work in the U.S. with no restrictions",
]

# ---- doc() helper: assemble one resume ---------------------------------
# Pattern for building a role. Add your own real jobs to the `exp` list. The
# example below has one current role plus one set of project sub-bullets so the
# page is full but stays at 1 page. Add or remove bullets to fit exactly 1 page.
def doc(summary, subprojects, additional=None):
    """
    summary:     a 3-4 line tailored summary string (your voice, no em dashes).
    subprojects: list of (sub-title, [bullet keys]) shown under the prior role.
    additional:  optional override for the Additional Information block.
    """
    exp = [
        # --- Current / most recent role (bullets straight from the bank) ---
        {"company": "Current Company", "title": "Product Manager",
         "loc": "City, ST", "date": "2024 &ndash; Present",
         "bullets": [B["role1_a"], B["role1_b"]]},
        # --- A prior role with italic project sub-headers ---
        {"company": "Prior Company", "title": "Consultant",
         "loc": "City, ST &ndash; Selected Experiences", "date": "2020 &ndash; 2024",
         "subprojects": [{"title": t, "bullets": [B[k] for k in ks]} for t, ks in subprojects]},
        # --- An earlier role ---
        {"company": "Earlier Company", "title": "Research Associate",
         "loc": "City, ST", "date": "2017 &ndash; 2020",
         "bullets": [B["edu_a"]]},
    ]
    return {"dir": None, "name": "Jane Rivera", "summary": summary,
            "experience": exp, "additional": additional or ADDITIONAL}

# ---- Per-role definitions ----------------------------------------------
# To ADD A ROLE you are applying to:
#   1. Write a tailored 3-4 line summary that leads with what the JD weights most.
#   2. Pick which project sub-bullets to surface (reorder/swap per role).
#   3. Set ROLES["your-slug"] = doc(summary, [(sub-title, [bullet keys]), ...])
#   4. Set ROLES["your-slug"]["dir"] = "your-slug"
#   5. Run: python3 scripts/render_resumes.py your-slug  and confirm pages=1.
ROLES = {}

ROLES["example"] = doc(
    "Product manager with N years building software in regulated, high-stakes "
    "domains. I work hands-on with the product, from strategy through the "
    "evaluation and guardrails that keep it reliable in production. I shipped X "
    "that improved Y by Z%, and I own roadmaps end to end. Technical fluency in "
    "Python, SQL, and (your stack).",
    [("Flagship Initiative &ndash; Lead Product Manager", ["proj_a", "proj_b"]),
     ("Platform Consolidation &ndash; Product Manager", ["proj_c"])],
)
ROLES["example"]["dir"] = "example"

if __name__ == "__main__":
    sel = sys.argv[1] if len(sys.argv) > 1 else None
    for slug, d in ROLES.items():
        if sel and slug != sel: continue
        render(slug, d)
