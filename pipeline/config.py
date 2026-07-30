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

# Static reference data for the "Map" view: HQ + a representative set of
# production/manufacturing sites per company. This is manually curated public
# information (company investor-relations / newsroom pages, current as of
# mid-2026) - it is NOT derived from the earnings documents, and for
# companies with dozens of sites (Vertiv: ~30 manufacturing/assembly
# facilities in 40+ countries; Microsoft/Google: hundreds of data centers)
# this is a representative subset, not an exhaustive list. Update by hand if
# a site closes/opens or a new company is added.
FACILITIES = {
    "ASML": [
        {"name": "Veldhoven", "type": "HQ + Manufacturing", "country": "Netherlands", "lat": 51.4204, "lon": 5.4048},
        {"name": "San Diego, CA", "type": "Manufacturing (EUV/DUV light sources)", "country": "USA", "lat": 32.7157, "lon": -117.1611},
        {"name": "Wilton, CT", "type": "Manufacturing & R&D (mechatronics, optics)", "country": "USA", "lat": 41.1954, "lon": -73.4370},
        {"name": "Linkou", "type": "Manufacturing (reticle handlers, YieldStar)", "country": "Taiwan", "lat": 25.0839, "lon": 121.3654},
        {"name": "Tainan", "type": "R&D & Manufacturing (HMI e-beam)", "country": "Taiwan", "lat": 22.9997, "lon": 120.2270},
    ],
    "TSMC": [
        {"name": "Hsinchu", "type": "HQ + Fabs", "country": "Taiwan", "lat": 24.8138, "lon": 120.9675},
        {"name": "Tainan", "type": "Fabs 14/18 (advanced nodes)", "country": "Taiwan", "lat": 22.9997, "lon": 120.2270},
        {"name": "Taichung", "type": "Fab 15 (+ Fab 25 under construction)", "country": "Taiwan", "lat": 24.1477, "lon": 120.6736},
        {"name": "Kaohsiung", "type": "Fab 22", "country": "Taiwan", "lat": 22.6273, "lon": 120.3014},
        {"name": "Phoenix, AZ", "type": "Fab 21", "country": "USA", "lat": 33.4484, "lon": -112.0740},
        {"name": "Kumamoto", "type": "Fab (JASM)", "country": "Japan", "lat": 32.8032, "lon": 130.7079},
        {"name": "Dresden", "type": "Fab (ESMC, under construction)", "country": "Germany", "lat": 51.0504, "lon": 13.7373},
    ],
    "Microsoft": [
        {"name": "Redmond, WA", "type": "HQ", "country": "USA", "lat": 47.6740, "lon": -122.1215},
        {"name": "Quincy, WA", "type": "Data center", "country": "USA", "lat": 47.2343, "lon": -119.8524},
        {"name": "Boydton, VA", "type": "Data center", "country": "USA", "lat": 36.6676, "lon": -78.3819},
        {"name": "San Antonio, TX", "type": "Data center", "country": "USA", "lat": 29.4241, "lon": -98.4936},
        {"name": "Mount Pleasant, WI", "type": "Data center (Fairwater - largest AI campus)", "country": "USA", "lat": 42.7261, "lon": -87.8834},
        {"name": "Dublin", "type": "Data center", "country": "Ireland", "lat": 53.3498, "lon": -6.2603},
    ],
    "Google/Alphabet": [
        {"name": "Mountain View, CA", "type": "HQ (Googleplex)", "country": "USA", "lat": 37.4220, "lon": -122.0841},
        {"name": "The Dalles, OR", "type": "Data center", "country": "USA", "lat": 45.5946, "lon": -121.1787},
        {"name": "Council Bluffs, IA", "type": "Data center", "country": "USA", "lat": 41.2619, "lon": -95.8608},
        {"name": "St. Ghislain", "type": "Data center", "country": "Belgium", "lat": 50.4542, "lon": 3.8189},
        {"name": "Hamina", "type": "Data center", "country": "Finland", "lat": 60.5696, "lon": 27.1978},
        {"name": "Singapore", "type": "Data center", "country": "Singapore", "lat": 1.3521, "lon": 103.8198},
        {"name": "Changhua County", "type": "Data center", "country": "Taiwan", "lat": 24.0518, "lon": 120.5161},
    ],
    "Vertiv": [
        {"name": "Westerville, OH", "type": "HQ", "country": "USA", "lat": 40.1262, "lon": -82.9291},
        {"name": "Ironton, OH", "type": "Manufacturing", "country": "USA", "lat": 38.5320, "lon": -82.6821},
        {"name": "Lincoln, NE", "type": "Manufacturing (power distribution)", "country": "USA", "lat": 40.8136, "lon": -96.7026},
        {"name": "Neuhausen am Rheinfall", "type": "Regional HQ (EMEA)", "country": "Switzerland", "lat": 47.6890, "lon": 8.6156},
        {"name": "Shenzhen", "type": "Regional HQ (APAC)", "country": "China", "lat": 22.5431, "lon": 114.0579},
        {"name": "Thane", "type": "Manufacturing & Regional office", "country": "India", "lat": 19.2183, "lon": 72.9781},
    ],
}
