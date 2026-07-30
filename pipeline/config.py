"""Central configuration: paths, company normalization, business-unit descriptions.

Paths are computed relative to this file so the whole `dashboard/` folder can be
copied anywhere (including onto a Windows machine) as long as it stays as a
sibling of the company folders (ASLM/, Google/, MSFT/, TSMC/, Vertiv /, ...).
"""
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent
DASHBOARD_DIR = PIPELINE_DIR.parent
SOURCE_DIR = DASHBOARD_DIR.parent  # "Earnings Call AI mkt" folder

DATA_DIR = DASHBOARD_DIR / "data"
PARSED_DIR = DATA_DIR / "parsed"
QOQ_DIR = DATA_DIR / "qoq"
INDEX_FILE = PARSED_DIR / "index.json"

for d in (DATA_DIR, PARSED_DIR, QOQ_DIR):
    d.mkdir(parents=True, exist_ok=True)

# Folder name (as found on disk, stripped) -> canonical company name.
# Add an entry here when a new company folder is introduced.
COMPANY_FOLDER_MAP = {
    "ASLM": "ASML",
    "ASML": "ASML",
    "Google": "Google/Alphabet",
    "MSFT": "Microsoft",
    "TSMC": "TSMC",
    "Vertiv": "Vertiv",
}

# Folders to ignore entirely when walking SOURCE_DIR.
IGNORED_DIR_NAMES = {"dashboard", ".git", "__pycache__"}

QUARTERS = ("Q1", "Q2")

# Short, static descriptions of each company's business units / segments,
# used to populate the "what is this BU" text in the dashboard. Purely
# descriptive copy - not derived from any single document.
BUSINESS_UNIT_DESCRIPTIONS = {
    "Microsoft": {
        "Productivity and Business Processes": "Office/Microsoft 365, LinkedIn, and Dynamics 365 - productivity software and business applications.",
        "Intelligent Cloud": "Azure and other cloud/server products, plus enterprise services.",
        "More Personal Computing": "Windows, Surface devices, Xbox/gaming, and Search & news advertising (Bing/Edge/Copilot).",
    },
    "Google/Alphabet": {
        "Google Services": "Search & other advertising, YouTube ads, Google Network, and subscriptions/platforms/devices (YouTube Premium/Music, Google One, Pixel, etc.) - Alphabet's core consumer and advertising business.",
        "Google Cloud": "Google Cloud Platform (GCP) infrastructure and platform services plus Google Workspace collaboration tools.",
        "Other Bets": "Early-stage businesses outside Google's core, e.g. Waymo (autonomous driving).",
    },
    "TSMC": {
        "HPC": "High-Performance Computing - data center CPUs/GPUs and AI accelerator chips.",
        "Smartphone": "Chips for mobile handsets.",
        "IoT": "Internet-of-Things chips.",
        "Automotive": "Chips for automotive applications.",
        "DCE": "Digital Consumer Electronics.",
        "Others": "Other platforms not separately broken out.",
    },
    "ASML": {
        "New Systems": "Sales of new lithography systems (EUV/DUV) to chipmakers.",
        "Installed Base Management": "Service, upgrades and field options on ASML's installed base of systems - the recurring/service side of the business.",
    },
    "Vertiv": {
        "AMER": "Americas region - data center power, thermal and IT infrastructure sales & services.",
        "APAC": "Asia Pacific region - data center power, thermal and IT infrastructure sales & services.",
        "EMEA": "Europe, Middle East & Africa region - data center power, thermal and IT infrastructure sales & services.",
    },
}

DOC_TYPES = ("press_release", "presentation", "transcript", "financial_statement", "other")
