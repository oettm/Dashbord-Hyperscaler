# Earnings QoQ Dashboard

Extracts KPIs from the earnings press releases / presentations / financial
statements / transcripts sitting in the sibling company folders (`ASLM/`,
`Google/`, `MSFT/`, `TSMC/`, `Vertiv /`), builds a Q1-vs-Q2 comparison per
company and across companies, and serves it all through a local Streamlit
dashboard - including a per-company business-unit breakdown.

This `dashboard/` folder is self-contained and expects to live as a sibling
of those company folders (i.e. inside `Earnings Call AI mkt/`). Don't move it
out on its own.

## 1. Setup (Windows, Python 3.13, virtualenv)

```powershell
cd "Earnings Call AI mkt\dashboard"
py -3.13 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Run the extraction pipeline

```powershell
python -m pipeline.run_pipeline
python -m pipeline.build_qoq
```

- `run_pipeline` walks the company folders, extracts text from every PDF /
  PPTX / XLSX it finds, runs it through the matching company parser, and
  writes one JSON file per document to `data/parsed/`, plus a
  `data/parsed/index.json` registry (file hash -> parsed output).
- `build_qoq` reads everything in `data/parsed/` and writes the three files
  the dashboard actually reads, into `data/qoq/`:
  - `company_quarter_records.json` - one consolidated record per company per quarter
  - `qoq_comparison.json` - Q1 vs Q2, per company, per KPI and per business unit
  - `cross_company.json` - one ranking table per KPI, across all companies

**Incremental re-runs**: `run_pipeline` hashes every source file and skips
anything already in `index.json` with a matching hash - so re-running after
adding new files only (re-)processes what changed. To force a full re-parse
(e.g. after editing a parser), run `python -m pipeline.run_pipeline --force`.
`build_qoq` is cheap and always rebuilds its three output files from whatever
is currently in `data/parsed/`, so just re-run it after any `run_pipeline` run.

## 3. Adding a new quarter (e.g. Q3) or a new company

- **New quarter for an existing company that uses `Q1/`, `Q2/` subfolders**
  (ASML, TSMC, Vertiv): drop the files into a new `Q3/` folder next to the
  existing ones, keeping filenames that mention the document type
  (`press release` / `presentation` or `slides` / `transcript` / `FS`).
- **Google/Microsoft** (no per-quarter subfolders): keep using filenames that
  contain the quarter, e.g. `...Q3...` or `...FY26Q3...`.
- Then re-run step 2. New quarters beyond Q1/Q2 are picked up by discovery
  automatically, but the QoQ comparison (`build_qoq.py`) is currently written
  specifically for a Q1-vs-Q2 pair - extending it to Q1/Q2/Q3 is a small
  change to `build_qoq_comparison()` (loop over an ordered quarter list
  instead of hardcoding "Q1"/"Q2").
- **A brand-new company**: add its folder name -> canonical name mapping in
  `pipeline/config.py` (`COMPANY_FOLDER_MAP`), add a business-unit
  description dict entry in `BUSINESS_UNIT_DESCRIPTIONS`, and write a parser
  module in `pipeline/parsers/` (copy the closest existing one - `asml.py` if
  its press release has clean two-column tables, `tsmc.py` if it's prose,
  `google.py` if you need a transcript-prose fallback). Wire it into
  `PARSER_MODULES` in `run_pipeline.py`.

## 4. Launch the dashboard

```powershell
streamlit run app.py
```

Opens at `http://localhost:8501`. Five views in the sidebar:

- **Per-company** - headline KPI tiles + full Q1-vs-Q2 KPI table for one company.
- **Cross-company** - pick a KPI, see every company ranked by Q1 level, Q2
  level, or QoQ % growth, plus a grouped bar chart.
- **Business units** - per company, each segment's description, Q1-vs-Q2
  revenue/operating income/margin, and any outlook mentioned for it (falls
  back to company-level guidance, labeled as such, when a document doesn't
  break guidance out by segment).
- **Map** - HQ and production/data-center sites for all five companies on a
  world map (color = company, larger marker = HQ), plus a table of every
  site. This data is **manually curated from public sources** (company
  newsroom/investor pages), not extracted from the earnings documents, and
  for companies with dozens-to-hundreds of sites (Vertiv, Microsoft, Google)
  it's a representative subset rather than exhaustive. To add/edit sites,
  update `FACILITIES` in `pipeline/config.py` - each entry is
  `{"name", "type", "country", "lat", "lon"}`; a new company needs a new key
  in that dict, using the same company name as everywhere else in the
  pipeline (`COMPANY_FOLDER_MAP`'s canonical name).
- **Qualitative notes** - management commentary quotes pulled from the press
  releases/transcripts, Q1 next to Q2.

Missing data (a company with no Q2 folder, or a KPI not present in any of a
quarter's documents) always renders as **"not available"** rather than a
zero, a blank, or an error. The dashboard re-reads `data/qoq/` on every page
load (cached on file modification time), so after re-running the pipeline
just refresh the browser tab - no restart needed.

## What's in this dataset today (known limitations)

- **Microsoft**: no press release in this dataset. All KPIs come from
  `Microsoft statements.xlsx`, which as of this data drop is only populated
  through Q1 FY26 - Q2 FY26 columns exist as empty headers with no data, and
  the only Q2 artifact is a 5-slide, image-only "Outlook" deck (no text
  layer, so nothing is extracted from it). MSFT therefore shows as **Q2 not
  available** end-to-end, same as Vertiv.
- **Vertiv**: no Q2 folder at all in this dataset - Q1-only, by design.
- **Google/Alphabet Q2**: no press release file present; KPIs for Q2 are
  parsed from the CFO's prose remarks in the earnings call transcript
  instead (labeled `extraction_source: transcript_prose_fallback` in the
  parsed JSON) - slightly less robust than the table-based parsing used
  everywhere else, since it depends on the transcript's exact phrasing.
- **TSMC**: reports natively in NTD. Cross-company KPIs are converted to USD
  using that quarter's own revenue-implied NTD/USD rate (stored as
  `implied_ntd_per_usd`) rather than a fixed rate, so it moves with the
  actual quarter. TSMC's cash-flow statement table also changes column
  count between Q1 and Q2 filings (adds a "six months cumulative" column
  pair) - the parser detects the column count and picks the standalone-
  quarter figure rather than assuming a fixed position; worth spot-checking
  if TSMC's own filing format changes again in Q3.
  TSMC doesn't carry meaningful leverage, so we report a net cash position
  instead of a leverage ratio (unlike Vertiv, which reports net leverage as
  a multiple).
  TSMC's platform revenue mix (HPC/Smartphone/IoT/...) is only extracted
  when the presentation deck's chart has a text layer - it did for Q1 in
  this dataset but not for Q2, so that one field can legitimately be "not
  available" for a quarter where everything else is populated.
- **No OCR**: MSFT's two PPTX decks render every slide as a flattened image
  with no extractable text. The pipeline detects this (`extraction_status:
  "no_text_layer"` in the parsed JSON) and skips KPI extraction from them
  rather than guessing. If you want to pull numbers/guidance text out of
  those slides too, add OCR (`pytesseract` + a Tesseract binary install on
  Windows) - this was intentionally left out to avoid a native-binary
  dependency for one company's supplementary slides when its numbers are
  already fully covered by the XLSX.

## Project layout

```
dashboard/
  pipeline/
    config.py        paths, company-folder normalization, BU descriptions, FACILITIES (map data)
    discover.py       walks the source folder, classifies every file
    extract_text.py   PDF/PPTX text extraction, file hashing
    parsers/          one module per company (asml, google, tsmc, vertiv, msft) + common.py helpers
    run_pipeline.py   incremental driver -> data/parsed/*.json
    build_qoq.py      aggregation -> data/qoq/*.json
  dashboard_app/
    utils.py          data loading, formatting, company color map
    views/            one module per dashboard tab
  app.py              streamlit entry point
  data/
    parsed/           one JSON per source document + index.json (the incremental cache)
    qoq/              the three files the dashboard reads
  requirements.txt
```
