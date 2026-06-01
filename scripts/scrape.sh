#!/usr/bin/env bash
# GREEN-source scraping wrappers. RED sources (LinkedIn) are NOT targeted here by design.
set -euo pipefail

company="${1:?usage: scrape.sh <company> <careers_url>}"
url="${2:?provide a GREEN-source URL (career page / ATS JD / news)}"
outdir="companies/${company}"
mkdir -p "$outdir"

# Render a JS-heavy page to clean markdown
firecrawl scrape "$url" > "${outdir}/jd-raw.md"
echo "wrote ${outdir}/jd-raw.md"

# Example interactive flow (uncomment as needed):
# firecrawl browser --prompt "load all role listings; extract title+location+url"
# agy "Scrape ${company} careers + last 6mo press; summarize into dossier format"
