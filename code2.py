import base64
import io
import os
import sqlite3
import requests
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(
    page_title="THE BIOCATALYST ARCHIVE | SSF & SmF Specimen Index",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "ssf_database.db")

RECORD_COLUMNS = [
    "organism",
    "substrate",
    "enzyme",
    "raw_yield",
    "raw_unit",
    "moisture_pct",
    "ph",
    "temp_c",
    "time_hrs",
    "supplements",
    "norm_yield",
    "confidence",
    "reference",
    "fermentation_mode",
]


def _get_secret(key, default=""):
    try:
        if key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    return os.environ.get(key, default).strip()


GITHUB_TOKEN = _get_secret("GITHUB_TOKEN")
GITHUB_REPO = _get_secret("GITHUB_REPO")  # e.g., "username/repo-name"
GITHUB_BRANCH = _get_secret("GITHUB_BRANCH", "main")
GITHUB_CSV_PATH = _get_secret("GITHUB_CSV_PATH", "data/user_uploads.csv")


def github_configured():
    return bool(GITHUB_TOKEN and GITHUB_REPO)


def _github_headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def fetch_github_csv():
    """Fetch user_uploads.csv from GitHub. Returns (DataFrame, sha_or_None)."""
    if not github_configured():
        return pd.DataFrame(columns=RECORD_COLUMNS), None

    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_CSV_PATH}"
    resp = requests.get(url, headers=_github_headers(), params={"ref": GITHUB_BRANCH}, timeout=15)
    if resp.status_code == 404:
        return pd.DataFrame(columns=RECORD_COLUMNS), None
    resp.raise_for_status()

    payload = resp.json()
    sha = payload.get("sha")
    content_b64 = payload.get("content", "")
    if not content_b64:
        return pd.DataFrame(columns=RECORD_COLUMNS), sha

    raw_bytes = base64.b64decode(content_b64)
    if not raw_bytes.strip():
        return pd.DataFrame(columns=RECORD_COLUMNS), sha

    csv_df = pd.read_csv(io.BytesIO(raw_bytes))
    for col in RECORD_COLUMNS:
        if col not in csv_df.columns:
            csv_df[col] = ""
    return csv_df[RECORD_COLUMNS], sha


def push_github_csv(df_user_rows, sha=None, commit_msg="Update user_uploads.csv from BioCatalyst Archive"):
    """Commit updated user_uploads.csv back to GitHub."""
    if not github_configured():
        return False, "GitHub secrets (GITHUB_TOKEN / GITHUB_REPO) are not configured."

    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_CSV_PATH}"
    if sha is None:
        check = requests.get(url, headers=_github_headers(), params={"ref": GITHUB_BRANCH}, timeout=15)
        if check.status_code == 200:
            sha = check.json().get("sha")

    csv_bytes = df_user_rows[RECORD_COLUMNS].to_csv(index=False).encode("utf-8")
    body = {
        "message": commit_msg,
        "content": base64.b64encode(csv_bytes).decode("ascii"),
        "branch": GITHUB_BRANCH,
    }
    if sha:
        body["sha"] = sha

    put_resp = requests.put(url, headers=_github_headers(), json=body, timeout=20)
    if put_resp.status_code in (200, 201):
        return True, "Committed to GitHub"
    return False, f"GitHub API error {put_resp.status_code}: {put_resp.text}"


st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

        .stApp {
            background-color: #0b1115 !important;
            color: #f1f5f9 !important;
            font-family: 'Plus Jakarta Sans', sans-serif;
        }
        [data-testid="stHeader"] {
            background-color: #0b1115 !important;
        }
        .stApp p, .stApp label, .stApp span, .stApp div, .stApp li {
            color: #f1f5f9;
        }

        /* Left Sidebar Navigation */
        [data-testid="stSidebar"] {
            background-color: #111a20 !important;
            border-right: 1px solid #243642 !important;
            min-width: 265px !important;
            max-width: 265px !important;
            transform: none !important;
            visibility: visible !important;
        }
        [data-testid="stSidebar"] * {
            color: #f1f5f9 !important;
        }
        [data-testid="collapsedControl"] {
            display: none !important;
        }

        /* Top Archival Masthead */
        .masthead {
            background: linear-gradient(135deg, #132028 0%, #192c36 55%, #183b34 100%);
            border: 1px solid #2c4a46;
            border-radius: 16px;
            padding: 1.5rem 1.9rem;
            color: #f1f5f9 !important;
            margin-bottom: 1rem;
            box-shadow: 0 12px 28px rgba(0, 0, 0, 0.45);
        }
        .masthead-eyebrow {
            font-size: 0.75rem;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            color: #6ee7b7 !important;
            font-weight: 700;
            margin-bottom: 0.3rem;
        }
        .masthead h1 {
            font-family: 'Cormorant Garamond', serif;
            font-size: 2.25rem;
            font-weight: 700;
            line-height: 1.1;
            margin: 0;
            color: #ffffff !important;
        }
        .masthead p {
            margin: 0.45rem 0 0 0;
            color: #cbd5e1 !important;
            font-size: 0.95rem;
            max-width: 820px;
        }

        /* Specimen Plate / Field Note Card */
        .specimen-plate {
            background: #121b22 !important;
            border: 1px solid #263744 !important;
            border-left: 5px solid #34d399 !important;
            border-radius: 12px;
            padding: 1.15rem 1.4rem;
            margin: 0.85rem 0 1.15rem 0;
            box-shadow: 0 6px 18px rgba(0, 0, 0, 0.35);
        }
        .specimen-plate, .specimen-plate * {
            color: #f1f5f9 !important;
        }
        .specimen-code {
            font-size: 0.75rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #6ee7b7 !important;
            font-weight: 700;
        }
        .specimen-title {
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.55rem;
            font-weight: 700;
            color: #ffffff !important;
            margin: 0.15rem 0 0.4rem 0;
        }
        .tag-pill {
            display: inline-block;
            background: #172e29 !important;
            color: #a7f3d0 !important;
            border: 1px solid #2b594d !important;
            border-radius: 999px;
            padding: 0.2rem 0.7rem;
            font-size: 0.8rem;
            font-weight: 600;
            margin-right: 0.35rem;
            margin-top: 0.3rem;
        }

        /* Dark Metric Plaques */
        div[data-testid="stMetric"] {
            background-color: #121b22 !important;
            border: 1px solid #263744 !important;
            border-radius: 12px;
            padding: 0.85rem 1rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }
        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] [data-testid="stMetricValue"],
        div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
            color: #ffffff !important;
        }
        [data-testid="stMetricValue"] {
            font-weight: 700 !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=30000;")
    return conn


VERIFIED_SEED_DATA = [
    ("Aspergillus niger", "Banana Peel", "pectinase", 27.68, "U/mL", 60.0, 5.8, 32.4, 66.0, "Ammonium sulfate", 276.8, "LOW", "10.1007/s13197-014-1413-8", "SSF"),
    ("Fungal consortium", "Coffee Husk", "cellulase", 10.0, "U/g dry", 65.0, 5.0, 37.0, 96.0, "Compost", 10.0, "HIGH", "10.1016/j.scitotenv.2017.02.184", "SSF"),
    ("Trichoderma viride", "Banana Peel", "cellulase", 142.5, "U/g dry", 65.0, 5.5, 30.0, 72.0, "Peptone", 142.5, "HIGH", "10.5897/AJB10.1825", "SSF"),
    ("Bacillus subtilis", "Groundnut Oil Cake", "lipase", 4.5, "U/g dry", 70.0, 8.0, 32.0, 48.0, "None", 4.5, "HIGH", "10.3390/agriculture11060540", "SSF"),
    ("Aspergillus niger", "Coconut Coir Pith", "cellulase", 18.5, "U/g dry", 70.0, 5.0, 30.0, 120.0, "Malt extract", 18.5, "HIGH", "10.1385/abab:108:1-3:737", "SSF"),
    ("Bacillus sp.", "Cassava Bagasse", "amylase", 437.76, "U/g dry", 60.0, 6.0, 37.0, 72.0, "Peptone", 437.76, "HIGH", "10.1590/1678-4324-2020170521", "SSF"),
    ("Aspergillus awamori", "Grape Pomace", "xylanase", 340.0, "U/g dry", 65.0, 5.0, 30.0, 96.0, "Glucose", 340.0, "HIGH", "10.1007/s12010-007-8077-z", "SSF"),
    ("Aspergillus niger", "Mango Peel", "pectinase", 540.0, "U/g dry", 65.0, 5.0, 30.0, 72.0, "Yeast extract", 540.0, "HIGH", "10.3390/molecules16108419", "SSF"),
    ("Bacillus amyloliquefaciens", "Soybean Meal", "protease", 106.41, "U/mL", 55.0, 7.0, 37.0, 48.0, "None", 1064.1, "LOW", "10.1002/jsfa.13209", "SSF"),
    ("Bacillus subtilis", "Potato Peel", "amylase", 600.0, "U/mL", 80.0, 7.0, 50.0, 48.0, "YPS broth", 6000.0, "LOW", "10.1007/s11274-005-9049-5", "SmF"),
    ("Bacillus licheniformis", "Potato Peel", "amylase", 270.0, "U/mL", 65.0, 9.0, 90.0, 48.0, "YPS broth", 2700.0, "LOW", "10.1007/s11274-005-9049-5", "SmF"),
    ("Aspergillus niger", "Sunflower Head", "pectinase", 450.0, "U/g dry", 60.0, 5.0, 30.0, 72.0, "Peptone", 450.0, "HIGH", "10.1016/j.biortech.2005.09.015", "SSF"),
    ("Aspergillus niger C28B25", "Coffee Pulp", "pectinase", 310.0, "U/g dry", 65.0, 5.0, 30.0, 72.0, "Citrate buffer", 310.0, "HIGH", "10.1016/0141-0229(93)90146-s", "SSF"),
    ("Aspergillus niger", "Citrus Peel", "pectinase", 220.0, "U/g dry", 60.0, 5.0, 30.0, 72.0, "Ammonium nitrate", 220.0, "HIGH", "10.1016/j.jrras.2015.11.003", "SSF"),
    ("Aspergillus flavus", "Palm Kernel Cake", "mannanase", 180.0, "U/g dry", 55.0, 5.5, 30.0, 96.0, "Urea", 180.0, "HIGH", "10.1007/s12010-010-9124-8", "SSF"),
    ("Aspergillus sp. LPB-5", "Oil Palm Fruit Bunch", "xylanase", 315.0, "U/g dry", 65.0, 5.0, 30.0, 96.0, "None", 315.0, "HIGH", "10.1016/j.biortech.2019.121361", "SSF"),
    ("Fungal strain", "Cottonseed Cake", "protease", 520.0, "U/g dry", 55.0, 6.5, 35.0, 72.0, "Lysine", 520.0, "HIGH", "10.22207/JPAM.10.2.55", "SSF"),
    ("Neobacillus sedimentimangrovi", "Sugarcane Bagasse", "cellulase", 160.0, "U/g dry", 70.0, 7.0, 37.0, 48.0, "None", 160.0, "HIGH", "10.1002/jobm.202200684", "SSF"),
    ("Yarrowia lipolytica", "Mustard Oil Cake", "lipase", 110.0, "U/g dry", 55.0, 7.0, 30.0, 72.0, "Olive oil", 110.0, "HIGH", "10.3389/fsufs.2022.1006467", "SSF"),
    ("Sporotrichum thermophile", "Sesame Oil Cake", "phytase", 180.0, "U/g dry", 60.0, 5.0, 45.0, 120.0, "Glucose", 180.0, "HIGH", "10.1385/ABAB:133:3:239", "SSF"),
    ("Trichoderma harzianum", "Shrimp Waste", "chitinase", 85.0, "U/g dry", 65.0, 6.0, 30.0, 96.0, "Colloidal chitin", 85.0, "HIGH", "10.1080/10826068.2024.2313631", "SSF"),
    ("Pseudonocardia carboxydivorans", "Shrimp Shell Waste", "chitinase", 42.0, "U/g dry", 60.0, 7.5, 32.0, 120.0, "Seawater", 42.0, "HIGH", "10.3390/fermentation7040247", "SSF"),
    ("Bacillus velezensis", "Pomegranate Peel", "tannase", 95.0, "U/g dry", 60.0, 6.0, 37.0, 72.0, "Tannic acid", 95.0, "HIGH", "10.1007/s13399-021-01850-9", "SSF"),
    ("Bacillus circulans", "Corncob", "xylanase", 240.0, "U/g dry", 60.0, 7.0, 37.0, 48.0, "Yeast extract", 240.0, "HIGH", "10.1016/j.bej.2006.09.020", "SSF"),
    ("Aspergillus niger", "Corncob", "xylanase", 512.0, "U/g dry", 65.0, 5.0, 30.0, 96.0, "Peptone", 512.0, "HIGH", "10.1016/j.biortech.2006.09.022", "SSF"),
    ("Aspergillus niger", "Pomelo Peel", "pectinase", 185.0, "U/g dry", 60.0, 5.0, 30.0, 72.0, "Citrate buffer", 185.0, "HIGH", "10.21315/tlsr2021.32.1.1", "SSF"),
    ("Trichoderma reesei", "Sugarcane Bagasse", "cellulase", 160.0, "U/g dry", 70.0, 5.0, 28.0, 120.0, "Urea", 160.0, "HIGH", "10.1016/j.procbio.2004.06.012", "SSF"),
    ("Aspergillus niger", "Apple Pomace", "pectinase", 850.0, "U/g dry", 65.0, 4.5, 30.0, 96.0, "Glucose", 850.0, "HIGH", "10.1016/j.biortech.2009.08.087", "SSF"),
    ("Aspergillus oryzae", "Coconut Oil Cake", "protease", 1372.0, "U/g dry", 55.0, 6.0, 30.0, 48.0, "Peptone", 1372.0, "HIGH", "10.1016/j.jfoodeng.2005.05.022", "SSF"),
]

INSERT_SQL = """
INSERT INTO ssf_experiments (
    organism, substrate, enzyme, raw_yield, raw_unit, moisture_pct,
    ph, temp_c, time_hrs, supplements, norm_yield, confidence, reference, fermentation_mode
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def to_float(x, default=0.0):
    if x is None:
        return default
    try:
        s = str(x).strip()
        return float(s) if s and s.lower() != "nan" else default
    except ValueError:
        return default


def _record_exists(cursor, row):
    cursor.execute(
        """
        SELECT 1 FROM ssf_experiments
        WHERE organism = ? AND substrate = ? AND enzyme = ?
          AND ABS(COALESCE(raw_yield, 0) - COALESCE(?, 0)) < 1e-6
          AND COALESCE(raw_unit, '') = COALESCE(?, '')
          AND ABS(COALESCE(norm_yield, 0) - COALESCE(?, 0)) < 1e-6
          AND COALESCE(reference, '') = COALESCE(?, '')
          AND COALESCE(fermentation_mode, 'SSF') = COALESCE(?, 'SSF')
        LIMIT 1
        """,
        (row[0], row[1], row[2], row[3], row[4], row[10], row[12], row[13]),
    )
    return cursor.fetchone() is not None


def sync_from_github_into_db(cursor):
    """Pull rows from GitHub CSV and insert any missing records into SQLite."""
    if not github_configured():
        return 0
    try:
        gh_df, _ = fetch_github_csv()
    except Exception:
        return 0

    added = 0
    for _, r in gh_df.iterrows():
        org = str(r.get("organism", "")).strip()
        sub = str(r.get("substrate", "")).strip()
        enz = str(r.get("enzyme", "")).strip()
        if not org or not sub or not enz:
            continue
        row = (
            org,
            sub,
            enz,
            to_float(r.get("raw_yield"), 0.0),
            str(r.get("raw_unit", "U/g dry")).strip() or "U/g dry",
            to_float(r.get("moisture_pct"), 50.0),
            to_float(r.get("ph"), 5.0),
            to_float(r.get("temp_c"), 30.0),
            to_float(r.get("time_hrs"), 72.0),
            str(r.get("supplements", "None")).strip() or "None",
            to_float(r.get("norm_yield"), 0.0),
            str(r.get("confidence", "LOW")).strip() or "LOW",
            str(r.get("reference", "Unknown")).strip() or "Unknown",
            str(r.get("fermentation_mode", "SSF")).strip() or "SSF",
        )
        if not _record_exists(cursor, row):
            cursor.execute(INSERT_SQL, row)
            added += 1
    return added


def init_db():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ssf_experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                organism TEXT, substrate TEXT, enzyme TEXT,
                raw_yield REAL, raw_unit TEXT, moisture_pct REAL,
                ph REAL, temp_c REAL, time_hrs REAL, supplements TEXT,
                norm_yield REAL, confidence TEXT, reference TEXT,
                fermentation_mode TEXT DEFAULT 'SSF'
            )
            """
        )
        cursor.execute("PRAGMA table_info(ssf_experiments)")
        existing_cols = [col[1] for col in cursor.fetchall()]
        if "fermentation_mode" not in existing_cols:
            cursor.execute("ALTER TABLE ssf_experiments ADD COLUMN fermentation_mode TEXT DEFAULT 'SSF'")
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM ssf_experiments")
        if cursor.fetchone()[0] == 0:
            for row in VERIFIED_SEED_DATA:
                cursor.execute(INSERT_SQL, row)
            conn.commit()

        sync_from_github_into_db(cursor)
        conn.commit()
    finally:
        conn.close()


init_db()


def save_records_and_commit_github(new_rows):
    """Save new records into SQLite and commit updated user_uploads.csv to GitHub."""
    if not new_rows:
        return 0, False, "No valid rows to save."

    conn = get_connection()
    inserted = 0
    try:
        cursor = conn.cursor()
        for row in new_rows:
            if not _record_exists(cursor, row):
                cursor.execute(INSERT_SQL, row)
                inserted += 1
        conn.commit()
    finally:
        conn.close()

    if not github_configured():
        return inserted, False, "GitHub secrets (GITHUB_TOKEN & GITHUB_REPO) are not configured."

    try:
        gh_df, sha = fetch_github_csv()
        new_df = pd.DataFrame(new_rows, columns=RECORD_COLUMNS)
        combined = pd.concat([gh_df, new_df], ignore_index=True)
        combined = combined.drop_duplicates(
            subset=["organism", "substrate", "enzyme", "raw_yield", "raw_unit", "norm_yield", "reference", "fermentation_mode"],
            keep="first",
        )
        ok, msg = push_github_csv(
            combined,
            sha=sha,
            commit_msg=f"Add {inserted} specimen record(s) to {GITHUB_CSV_PATH}",
        )
        return inserted, ok, msg
    except Exception as exc:
        return inserted, False, f"GitHub commit failed: {exc}"


def normalize_yield(raw_yield, raw_unit, moisture_pct):
    unit = str(raw_unit).lower().strip()
    raw_yield = to_float(raw_yield, 0.0)
    moisture_pct = to_float(moisture_pct, 50.0)
    if "dry" in unit or "u/gds" in unit:
        return round(raw_yield, 2), "HIGH"
    elif "wet" in unit or unit == "u/g":
        factor = 1.0 - (moisture_pct / 100.0)
        return (round(raw_yield / factor, 2), "MEDIUM") if factor > 0 else (round(raw_yield, 2), "LOW")
    elif "ml" in unit:
        return round(raw_yield * 10.0, 2), "LOW"
    return round(raw_yield, 2), "LOW"


def make_clickable_link(ref):
    ref = str(ref).strip()
    if not ref or ref.lower() in ("unknown", "none", "nan"):
        return None
    if ref.startswith("http://") or ref.startswith("https://"):
        return ref
    if ref.lower().startswith("pmc"):
        return f"https://www.ncbi.nlm.nih.gov/pmc/articles/{ref}/"
    return f"https://doi.org/{ref}"


def load_data():
    conn = get_connection()
    try:
        return pd.read_sql_query(
            """
            SELECT id, organism, substrate, enzyme, raw_yield, raw_unit, moisture_pct,
                   norm_yield, confidence, ph, temp_c, time_hrs, supplements, reference,
                   COALESCE(fermentation_mode, 'SSF') AS fermentation_mode
            FROM ssf_experiments
            ORDER BY norm_yield DESC
            """,
            conn,
        )
    finally:
        conn.close()


def render_table(df, show_rank=True):
    if df.empty:
        st.info("No specimen records match this query.")
        return
    out = df.copy()
    if show_rank:
        out.insert(0, "rank", [f"#{i+1}" for i in range(len(out))])
    out["reported"] = out.apply(lambda r: f"{r['raw_yield']} {r['raw_unit']}", axis=1)
    out["doi_link"] = out["reference"].apply(make_clickable_link)
    cols = [
        c for c in [
            "rank", "fermentation_mode", "organism", "substrate", "enzyme",
            "norm_yield", "reported", "confidence", "ph", "temp_c",
            "moisture_pct", "time_hrs", "supplements", "doi_link"
        ] if c in out.columns
    ]
    st.dataframe(
        out[cols],
        column_config={
            "doi_link": st.column_config.LinkColumn("Archive DOI", display_text="View Paper"),
            "norm_yield": st.column_config.NumberColumn("Norm Yield (U/g dry)", format="%.2f"),
        },
        hide_index=True,
        use_container_width=True,
    )


df = load_data()

# --- LEFT SIDEBAR: NAVIGATION ONLY ---
with st.sidebar:
    st.markdown("### 🏛️ Archive Navigation")
    page = st.radio(
        "Section",
        [
            "Specimen Catalogue",
            "Batch & Yield Calculator",
            "Head-to-Head Comparator",
            "Add / Import Data",
            "Matplotlib Plates",
        ],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption(f"Catalogued specimens: {len(df)}")
    if github_configured():
        st.caption(f"GitHub CSV sync: Active ({GITHUB_CSV_PATH})")
    else:
        st.caption("GitHub CSV sync: Not configured")

# --- MASTHEAD ---
st.markdown(
    """
    <div class="masthead">
        <div class="masthead-eyebrow">Bioprocess Specimen & Literature Repository</div>
        <h1>The BioCatalyst Archive</h1>
        <p>Curated solid-state (SSF) and submerged (SmF) enzyme records across non-cereal agro-industrial residues.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- 1. SPECIMEN CATALOGUE, CONSTRAINT RECOMMENDER & OPERATING WINDOW ---
if page == "Specimen Catalogue":
    with st.expander("🎯 Lab & Constraint Filters", expanded=True):
        f_c1, f_c2, f_c3 = st.columns(3)
        max_temp = f_c1.slider("Max Incubation Temp (°C)", 20.0, 95.0, 95.0, step=1.0)
        mode_choice = f_c2.selectbox("Fermentation Regime", ["All", "SSF", "SmF"])
        conf_only = f_c3.checkbox("HIGH confidence (dry-basis) only", value=False)

    filtered_base = df[df["temp_c"] <= max_temp].copy()
    if mode_choice != "All":
        filtered_base = filtered_base[filtered_base["fermentation_mode"] == mode_choice]
    if conf_only:
        filtered_base = filtered_base[filtered_base["confidence"] == "HIGH"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active Specimens", len(filtered_base))
    c2.metric("Peak Activity (U/g dry)", f"{filtered_base['norm_yield'].max():.2f}" if not filtered_base.empty else "0.00")
    c3.metric("Median Activity (U/g dry)", f"{filtered_base['norm_yield'].median():.2f}" if not filtered_base.empty else "0.00")
    c4.metric("Enzyme Taxa", filtered_base["enzyme"].nunique() if not filtered_base.empty else 0)

    f1, f2, f3, f4 = st.columns(4)
    org_sel = f1.selectbox("Organism", ["All"] + sorted(filtered_base["organism"].dropna().unique().tolist()))
    sub_sel = f2.selectbox("Substrate Matrix", ["All"] + sorted(filtered_base["substrate"].dropna().unique().tolist()))
    enz_sel = f3.selectbox("Enzyme", ["All"] + sorted(filtered_base["enzyme"].dropna().unique().tolist()))
    kw_sel = f4.text_input("Keyword (Supplement / DOI)", placeholder="e.g., Peptone or 10.1016")

    view = filtered_base.copy()
    if org_sel != "All":
        view = view[view["organism"] == org_sel]
    if sub_sel != "All":
        view = view[view["substrate"] == sub_sel]
    if enz_sel != "All":
        view = view[view["enzyme"] == enz_sel]
    if kw_sel.strip():
        q = kw_sel.strip()
        view = view[
            view["supplements"].str.contains(q, case=False, na=False)
            | view["reference"].str.contains(q, case=False, na=False)
            | view["organism"].str.contains(q, case=False, na=False)
            | view["substrate"].str.contains(q, case=False, na=False)
        ]

    view = view.sort_values("norm_yield", ascending=False).reset_index(drop=True)

    if not view.empty:
        top = view.iloc[0]
        p_min, p_med, p_max = view["ph"].min(), view["ph"].median(), view["ph"].max()
        t_min, t_med, t_max = view["temp_c"].min(), view["temp_c"].median(), view["temp_c"].max()
        m_min, m_med, m_max = view["moisture_pct"].min(), view["moisture_pct"].median(), view["moisture_pct"].max()
        h_min, h_med, h_max = view["time_hrs"].min(), view["time_hrs"].median(), view["time_hrs"].max()

        st.markdown(
            f"""
            <div class="specimen-plate">
                <div class="specimen-code">Featured Reference Specimen • {top['fermentation_mode']} • {top['confidence']} Confidence</div>
                <div class="specimen-title"><em>{top['organism']}</em> on {top['substrate']} — {top['enzyme'].title()}</div>
                <div>
                    Measured at <strong>pH {top['ph']}</strong>, <strong>{top['temp_c']}°C</strong>,
                    <strong>{top['moisture_pct']}% moisture</strong>, and <strong>{top['time_hrs']} hrs</strong>
                    (Supplement: <em>{top['supplements']}</em>) yielding <strong>{top['norm_yield']:.2f} U/g dry</strong>
                    (Reported: {top['raw_yield']} {top['raw_unit']}).
                </div>
                <div style="margin-top:0.5rem;">
                    <span class="tag-pill">pH Window: {p_min}–{p_max} (med {p_med:.1f})</span>
                    <span class="tag-pill">Temp Window: {t_min}–{t_max}°C (med {t_med:.1f}°C)</span>
                    <span class="tag-pill">Moisture: {m_min}–{m_max}% (med {m_med:.1f}%)</span>
                    <span class="tag-pill">Incubation: {h_min}–{h_max}h (med {h_med:.1f}h)</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_table(view, show_rank=True)

    if not filtered_base.empty:
        csv_data = filtered_base.drop(columns=["id"]).to_csv(index=False).encode("utf-8")
        st.download_button("Export Filtered Catalogue (CSV)", data=csv_data, file_name="biocatalyst_archive_filtered.csv", mime="text/csv")

# --- 2. BATCH & YIELD CALCULATOR ---
elif page == "Batch & Yield Calculator":
    st.subheader("⚖️ Solid-State Batch Water & Total Activity Calculator")
    st.caption("Estimate water/buffer addition for a target moisture level and total enzyme units for a chosen literature entry.")

    if not df.empty:
        labels = [
            f"{r['organism']} | {r['substrate']} | {r['enzyme']} ({r['norm_yield']:.1f} U/g dry)"
            for _, r in df.iterrows()
        ]
        idx = st.selectbox("Select Reference Specimen", range(len(labels)), format_func=lambda i: labels[i])
        rec = df.iloc[idx]

        col_l, col_r = st.columns(2)
        with col_l:
            dry_mass_g = st.number_input("Dry Substrate Mass (g)", min_value=1.0, value=100.0, step=10.0)
            target_moist = st.slider("Target Moisture (%)", min_value=20.0, max_value=85.0, value=float(rec["moisture_pct"]), step=1.0)
        with col_r:
            m_frac = target_moist / 100.0
            water_ml = dry_mass_g * (m_frac / (1.0 - m_frac))
            total_wet_g = dry_mass_g + water_ml
            est_total_units = dry_mass_g * rec["norm_yield"]

            st.metric("Estimated Water / Buffer to Add", f"{water_ml:.1f} mL")
            st.metric("Total Wet Batch Mass", f"{total_wet_g:.1f} g")
            st.metric("Estimated Total Enzyme Activity", f"{est_total_units:,.1f} U")

# --- 3. HEAD-TO-HEAD COMPARATOR ---
elif page == "Head-to-Head Comparator":
    st.subheader("⚔️ Side-by-Side Specimen Comparator")
    if len(df) >= 2:
        opts = [
            f"#{i+1}: {r['organism']} on {r['substrate']} [{r['enzyme']}]"
            for i, (_, r) in enumerate(df.iterrows())
        ]
        c_a, c_b = st.columns(2)
        a_idx = c_a.selectbox("Specimen A", range(len(opts)), index=0, format_func=lambda i: opts[i])
        b_idx = c_b.selectbox("Specimen B", range(len(opts)), index=min(1, len(opts) - 1), format_func=lambda i: opts[i])

        row_a = df.iloc[a_idx]
        row_b = df.iloc[b_idx]

        comp_df = pd.DataFrame({
            "Metric": ["Organism", "Substrate", "Enzyme", "Mode", "Norm Yield (U/g dry)", "pH", "Temp (°C)", "Moisture (%)", "Time (hrs)", "Supplements"],
            "Specimen A": [row_a["organism"], row_a["substrate"], row_a["enzyme"], row_a["fermentation_mode"], row_a["norm_yield"], row_a["ph"], row_a["temp_c"], row_a["moisture_pct"], row_a["time_hrs"], row_a["supplements"]],
            "Specimen B": [row_b["organism"], row_b["substrate"], row_b["enzyme"], row_b["fermentation_mode"], row_b["norm_yield"], row_b["ph"], row_b["temp_c"], row_b["moisture_pct"], row_b["time_hrs"], row_b["supplements"]],
        })
        st.dataframe(comp_df, hide_index=True, use_container_width=True)

# --- 4. ADD / IMPORT DATA ---
elif page == "Add / Import Data":
    if "status_banner" in st.session_state and st.session_state["status_banner"]:
        st.success(st.session_state["status_banner"])
        st.session_state["status_banner"] = ""

    if github_configured():
        st.info(f"Connected to GitHub repository `{GITHUB_REPO}` (`{GITHUB_CSV_PATH}` on branch `{GITHUB_BRANCH}`). New records will be committed automatically.")
    else:
        st.warning("Add `GITHUB_TOKEN` and `GITHUB_REPO` in Streamlit App Settings → Secrets so uploaded records commit permanently to your GitHub CSV.")

    tab_single, tab_csv = st.tabs(["Add Single Specimen", "Import CSV File"])
    with tab_single:
        with st.form("single_entry"):
            a, b = st.columns(2)
            org = a.text_input("Organism")
            sub = a.text_input("Substrate")
            enz = a.text_input("Enzyme")
            mode = a.selectbox("Mode", ["SSF", "SmF"])
            ry = a.number_input("Raw Yield", min_value=0.0, value=0.0)
            ru = a.selectbox("Unit", ["U/g dry", "U/g wet", "U/mL"])

            mo = b.number_input("Moisture %", min_value=0.0, max_value=100.0, value=60.0)
            ph = b.number_input("pH", value=5.0)
            tc = b.number_input("Temp (°C)", value=30.0)
            hr = b.number_input("Time (hrs)", value=72.0)
            sp = b.text_input("Supplements", value="None")
            rf = b.text_input("DOI / Reference", value="Unknown")

            if st.form_submit_button("Save Specimen"):
                if org.strip() and sub.strip() and enz.strip() and ry > 0:
                    ny, cf = normalize_yield(ry, ru, mo)
                    row = (
                        org.strip(),
                        sub.strip().title(),
                        enz.strip().lower(),
                        ry,
                        ru,
                        mo,
                        ph,
                        tc,
                        hr,
                        sp.strip() or "None",
                        ny,
                        cf,
                        rf.strip() or "Unknown",
                        mode,
                    )
                    inserted, gh_ok, gh_msg = save_records_and_commit_github([row])
                    sync_note = "and synced to GitHub." if gh_ok else f"({gh_msg})"
                    st.session_state["status_banner"] = (
                        f"Database updated successfully ({inserted} new row added, normalized yield = {ny:.2f} U/g dry [{cf}]) {sync_note}"
                    )
                    st.rerun()
                else:
                    st.error("Fill in Organism, Substrate, Enzyme, and Raw Yield > 0.")

    with tab_csv:
        up = st.file_uploader("Upload CSV", type=["csv"])
        if up is not None:
            up_df = pd.read_csv(up).fillna("")
            st.dataframe(up_df.head(8), use_container_width=True)
            if st.button("Import CSV Rows"):
                rows_to_save = []
                for _, r in up_df.iterrows():
                    o = str(r.get("organism", "")).strip()
                    s = str(r.get("substrate", "")).strip().title()
                    e = str(r.get("enzyme", "")).strip().lower()
                    if not o or not s or not e:
                        continue
                    ry = to_float(r.get("raw_yield"), 0.0)
                    ru = str(r.get("raw_unit", "U/g dry")).strip() or "U/g dry"
                    mo = to_float(r.get("moisture_pct"), 50.0)
                    ny, cf = normalize_yield(ry, ru, mo)
                    mode = "SmF" if str(r.get("fermentation_mode", "SSF")).strip().lower() == "smf" else "SSF"
                    rows_to_save.append(
                        (
                            o, s, e, ry, ru, mo,
                            to_float(r.get("ph"), 7.0),
                            to_float(r.get("temp_c"), 30.0),
                            to_float(r.get("time_hrs"), 48.0),
                            str(r.get("supplements") or "None").strip(),
                            ny, cf,
                            str(r.get("reference") or "Unknown").strip(),
                            mode,
                        )
                    )
                inserted, gh_ok, gh_msg = save_records_and_commit_github(rows_to_save)
                sync_note = f"and committed to `{GITHUB_CSV_PATH}` on GitHub." if gh_ok else f"({gh_msg})"
                st.session_state["status_banner"] = (
                    f"Database updated successfully ({inserted} new record(s) imported) {sync_note}"
                )
                st.rerun()

# --- 5. MATPLOTLIB PLATES ---
elif page == "Matplotlib Plates":
    st.subheader("📈 Custom Matplotlib Specimen Plates")
    if not df.empty:
        plt.style.use("dark_background")

        c_dim, c_metric = st.columns([1.2, 1])
        focus_dim = c_dim.selectbox(
            "1. What do you want to focus on?",
            ["Substrate", "Organism", "Enzyme"],
        )
        agg_stat = c_metric.selectbox(
            "2. Yield summary to plot",
            ["Peak Yield (Max)", "Typical Yield (Median)", "All Individual Runs"],
        )

        col_map = {
            "Substrate": ("substrate", "organism", "enzyme"),
            "Organism": ("organism", "substrate", "enzyme"),
            "Enzyme": ("enzyme", "organism", "substrate"),
        }
        primary_col, sec_col, tert_col = col_map[focus_dim]

        available_items = sorted(df[primary_col].dropna().unique().tolist())
        selected_items = st.multiselect(
            f"3. Select one or more {focus_dim}s to inspect",
            options=available_items,
            default=available_items[:3],
        )

        breakdown_by = st.selectbox(
            "4. Plot / break down against",
            [sec_col.title(), tert_col.title(), "None (Direct Comparison)"],
        )

        sub_df = df[df[primary_col].isin(selected_items)].copy() if selected_items else df.copy()

        if sub_df.empty:
            st.warning("No records match your selection.")
        else:
            left, right = st.columns(2)

            with left:
                fig, ax = plt.subplots(figsize=(6.8, 4.5))
                fig.patch.set_facecolor("#121b22")
                ax.set_facecolor("#121b22")

                if agg_stat == "All Individual Runs":
                    ordered = sub_df.sort_values("norm_yield", ascending=True)
                    labels = [f"{r[primary_col]} | {r[sec_col]}" for _, r in ordered.iterrows()]
                    ax.barh(labels, ordered["norm_yield"].values, color="#38bdf8")
                    ax.set_ylabel(f"{focus_dim} & {sec_col.title()}")
                else:
                    stat_fn = "max" if "Max" in agg_stat else "median"
                    if breakdown_by == "None (Direct Comparison)":
                        grp = sub_df.groupby(primary_col)["norm_yield"].agg(stat_fn).sort_values(ascending=True)
                        ax.barh(grp.index, grp.values, color="#38bdf8")
                        ax.set_ylabel(focus_dim)
                    else:
                        b_col = breakdown_by.lower()
                        piv = sub_df.pivot_table(
                            index=primary_col,
                            columns=b_col,
                            values="norm_yield",
                            aggfunc=stat_fn,
                        )
                        top_cats = sub_df.groupby(b_col)["norm_yield"].max().nlargest(6).index
                        piv = piv[[c for c in top_cats if c in piv.columns]]
                        piv.plot(kind="barh", ax=ax, width=0.78)
                        ax.legend(title=breakdown_by, fontsize=8, title_fontsize=8)
                        ax.set_ylabel(focus_dim)

                ax.set_xlabel(f"{agg_stat} (U/g dry)")
                ax.set_title(f"{focus_dim} Yield Breakdown")
                ax.grid(axis="x", linestyle="--", alpha=0.25)
                plt.tight_layout()
                st.pyplot(fig)

            with right:
                fig, ax = plt.subplots(figsize=(6.8, 4.5))
                fig.patch.set_facecolor("#121b22")
                ax.set_facecolor("#121b22")
                ax.scatter(
                    sub_df["temp_c"],
                    sub_df["norm_yield"],
                    c="#34d399",
                    alpha=0.85,
                    edgecolors="#0b1115",
                    s=65,
                )
                ax.set_xlabel("Incubation Temperature (°C)")
                ax.set_ylabel("Normalized Yield (U/g dry)")
                ax.set_title("Temperature vs. Yield for Selected Items")
                ax.grid(True, linestyle="--", alpha=0.25)
                plt.tight_layout()
                st.pyplot(fig)
