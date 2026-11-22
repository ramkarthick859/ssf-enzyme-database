import base64, io, os, sqlite3, requests
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(page_title="THE BIOCATALYST ARCHIVE", page_icon="🏛️", layout="wide")

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ssf_database.db")
COLS = ["organism", "substrate", "enzyme", "raw_yield", "raw_unit", "moisture_pct", "ph", "temp_c",
        "time_hrs", "supplements", "norm_yield", "confidence", "reference", "fermentation_mode"]
DEDUPE = ["organism", "substrate", "enzyme", "raw_yield", "raw_unit", "norm_yield", "reference", "fermentation_mode"]


# ---------- GitHub sync ----------
def secret(key, default=""):
    try:
        if key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    return os.environ.get(key, default).strip()


GH_TOKEN, GH_REPO = secret("GITHUB_TOKEN"), secret("GITHUB_REPO")
GH_BRANCH = secret("GITHUB_BRANCH", "main")
GH_PATH = secret("GITHUB_CSV_PATH", "data/user_uploads.csv")
GH_OK = bool(GH_TOKEN and GH_REPO)
GH_URL = f"https://api.github.com/repos/{GH_REPO}/contents/{GH_PATH}"
GH_HEAD = {"Authorization": f"Bearer {GH_TOKEN}", "Accept": "application/vnd.github+json"}


def fetch_github_csv():
    """Returns (DataFrame, sha_or_None)."""
    empty = pd.DataFrame(columns=COLS)
    if not GH_OK:
        return empty, None
    r = requests.get(GH_URL, headers=GH_HEAD, params={"ref": GH_BRANCH}, timeout=15)
    if r.status_code == 404:
        return empty, None
    r.raise_for_status()
    j = r.json()
    raw = base64.b64decode(j.get("content", ""))
    if not raw.strip():
        return empty, j.get("sha")
    df = pd.read_csv(io.BytesIO(raw))
    for c in COLS:
        if c not in df.columns:
            df[c] = ""
    return df[COLS], j.get("sha")


def push_github_csv(df, sha, msg):
    body = {"message": msg, "branch": GH_BRANCH,
            "content": base64.b64encode(df[COLS].to_csv(index=False).encode()).decode()}
    if sha:
        body["sha"] = sha
    r = requests.put(GH_URL, headers=GH_HEAD, json=body, timeout=20)
    return (True, "Committed to GitHub") if r.status_code in (200, 201) else (False, f"GitHub error {r.status_code}: {r.text}")


# ---------- Database ----------
SEED = [
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

INSERT_SQL = f"INSERT INTO ssf_experiments ({','.join(COLS)}) VALUES ({','.join('?' * len(COLS))})"


def db():
    conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def num(x, default=0.0):
    try:
        s = str(x).strip()
        return float(s) if s and s.lower() != "nan" else default
    except ValueError:
        return default


def normalize_yield(raw, unit, moisture):
    unit, raw, moisture = str(unit).lower().strip(), num(raw), num(moisture, 50.0)
    if "dry" in unit or "u/gds" in unit:
        return round(raw, 2), "HIGH"
    if "wet" in unit or unit == "u/g":
        f = 1.0 - moisture / 100.0
        return (round(raw / f, 2), "MEDIUM") if f > 0 else (round(raw, 2), "LOW")
    if "ml" in unit:
        return round(raw * 10.0, 2), "LOW"
    return round(raw, 2), "LOW"


def make_row(r, recompute=False):
    """Turn a dict/Series into a DB tuple. recompute=True recalculates normalized yield."""
    org, sub, enz = (str(r.get(k, "")).strip() for k in ("organism", "substrate", "enzyme"))
    if not (org and sub and enz):
        return None
    raw, mo = num(r.get("raw_yield")), num(r.get("moisture_pct"), 50.0)
    unit = str(r.get("raw_unit", "")).strip() or "U/g dry"
    if recompute:
        ny, cf = normalize_yield(raw, unit, mo)
    else:
        ny, cf = num(r.get("norm_yield")), str(r.get("confidence", "")).strip() or "LOW"
    mode = "SmF" if str(r.get("fermentation_mode", "SSF")).strip().lower() == "smf" else "SSF"
    return (org, sub, enz, raw, unit, mo, num(r.get("ph"), 5.0), num(r.get("temp_c"), 30.0),
            num(r.get("time_hrs"), 72.0), str(r.get("supplements", "")).strip() or "None",
            ny, cf, str(r.get("reference", "")).strip() or "Unknown", mode)


def insert_rows(cur, rows):
    """Insert rows that don't already exist. Returns number added."""
    added = 0
    for row in rows:
        cur.execute(
            """SELECT 1 FROM ssf_experiments WHERE organism=? AND substrate=? AND enzyme=?
               AND ABS(COALESCE(raw_yield,0)-?)<1e-6 AND COALESCE(raw_unit,'')=?
               AND ABS(COALESCE(norm_yield,0)-?)<1e-6 AND COALESCE(reference,'')=?
               AND COALESCE(fermentation_mode,'SSF')=? LIMIT 1""",
            (row[0], row[1], row[2], row[3], row[4], row[10], row[12], row[13]),
        )
        if cur.fetchone() is None:
            cur.execute(INSERT_SQL, row)
            added += 1
    return added


def init_db():
    conn = db()
    try:
        cur = conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS ssf_experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, organism TEXT, substrate TEXT, enzyme TEXT,
            raw_yield REAL, raw_unit TEXT, moisture_pct REAL, ph REAL, temp_c REAL, time_hrs REAL,
            supplements TEXT, norm_yield REAL, confidence TEXT, reference TEXT,
            fermentation_mode TEXT DEFAULT 'SSF')""")
        cur.execute("PRAGMA table_info(ssf_experiments)")
        if "fermentation_mode" not in [c[1] for c in cur.fetchall()]:
            cur.execute("ALTER TABLE ssf_experiments ADD COLUMN fermentation_mode TEXT DEFAULT 'SSF'")
        cur.execute("SELECT COUNT(*) FROM ssf_experiments")
        if cur.fetchone()[0] == 0:
            insert_rows(cur, SEED)
        if GH_OK:  # pull saved user uploads from GitHub
            try:
                gh_df, _ = fetch_github_csv()
                insert_rows(cur, [r for r in (make_row(x) for _, x in gh_df.iterrows()) if r])
            except Exception:
                pass
        conn.commit()
    finally:
        conn.close()


def save_records(rows):
    """Save to SQLite and commit to GitHub CSV. Returns (inserted, gh_ok, message)."""
    if not rows:
        return 0, False, "No valid rows to save."
    conn = db()
    try:
        inserted = insert_rows(conn.cursor(), rows)
        conn.commit()
    finally:
        conn.close()
    if not GH_OK:
        return inserted, False, "GitHub secrets (GITHUB_TOKEN & GITHUB_REPO) are not configured."
    try:
        gh_df, sha = fetch_github_csv()
        combined = pd.concat([gh_df, pd.DataFrame(rows, columns=COLS)], ignore_index=True)
        combined = combined.drop_duplicates(subset=DEDUPE, keep="first")
        ok, msg = push_github_csv(combined, sha, f"Add {inserted} specimen record(s)")
        return inserted, ok, msg
    except Exception as e:
        return inserted, False, f"GitHub commit failed: {e}"


def doi_link(ref):
    ref = str(ref).strip()
    if not ref or ref.lower() in ("unknown", "none", "nan"):
        return None
    if ref.startswith("http"):
        return ref
    if ref.lower().startswith("pmc"):
        return f"https://www.ncbi.nlm.nih.gov/pmc/articles/{ref}/"
    return f"https://doi.org/{ref}"


def load_data():
    conn = db()
    try:
        return pd.read_sql_query(
            "SELECT id, " + ",".join(COLS[:-1]) + ", COALESCE(fermentation_mode,'SSF') AS fermentation_mode "
            "FROM ssf_experiments ORDER BY norm_yield DESC", conn)
    finally:
        conn.close()


def render_table(df):
    if df.empty:
        st.info("No specimen records match this query.")
        return
    out = df.copy()
    out.insert(0, "rank", [f"#{i + 1}" for i in range(len(out))])
    out["reported"] = out["raw_yield"].astype(str) + " " + out["raw_unit"]
    out["doi_link"] = out["reference"].apply(doi_link)
    cols = ["rank", "fermentation_mode", "organism", "substrate", "enzyme", "norm_yield", "reported",
            "confidence", "ph", "temp_c", "moisture_pct", "time_hrs", "supplements", "doi_link"]
    st.dataframe(
        out[cols],
        column_config={
            "doi_link": st.column_config.LinkColumn("Archive DOI", display_text="View Paper"),
            "norm_yield": st.column_config.NumberColumn("Norm Yield (U/g dry)", format="%.2f"),
        },
        hide_index=True, use_container_width=True,
    )


# ---------- Style ----------
st.markdown("""
<style>
.stApp, [data-testid="stHeader"] {background-color:#0b1115 !important; color:#f1f5f9;}
[data-testid="stSidebar"] {background-color:#111a20 !important; border-right:1px solid #243642;}
.masthead {background:linear-gradient(135deg,#132028,#183b34); border:1px solid #2c4a46;
           border-radius:16px; padding:1.4rem 1.8rem; margin-bottom:1rem;}
.masthead h1 {margin:0; color:#fff;} .masthead p {margin:.4rem 0 0; color:#cbd5e1;}
.plate {background:#121b22; border:1px solid #263744; border-left:5px solid #34d399;
        border-radius:12px; padding:1rem 1.3rem; margin:.8rem 0 1rem;}
.pill {display:inline-block; background:#172e29; color:#a7f3d0; border:1px solid #2b594d;
       border-radius:999px; padding:.2rem .7rem; font-size:.8rem; margin:.3rem .3rem 0 0;}
div[data-testid="stMetric"] {background:#121b22; border:1px solid #263744; border-radius:12px; padding:.8rem 1rem;}
</style>
""", unsafe_allow_html=True)

init_db()
df = load_data()

with st.sidebar:
    st.markdown("### 🏛️ Archive Navigation")
    page = st.radio("Section", ["Specimen Catalogue", "Batch & Yield Calculator", "Head-to-Head Comparator",
                                "Add / Import Data", "Matplotlib Plates"], label_visibility="collapsed")
    st.markdown("---")
    st.caption(f"Catalogued specimens: {len(df)}")
    st.caption(f"GitHub CSV sync: {'Active (' + GH_PATH + ')' if GH_OK else 'Not configured'}")

st.markdown("""<div class="masthead"><h1>The BioCatalyst Archive</h1>
<p>Curated solid-state (SSF) and submerged (SmF) enzyme records across non-cereal agro-industrial residues.</p></div>""",
            unsafe_allow_html=True)

# ---------- 1. Catalogue ----------
if page == "Specimen Catalogue":
    with st.expander("🎯 Lab & Constraint Filters", expanded=True):
        c1, c2, c3 = st.columns(3)
        max_temp = c1.slider("Max Incubation Temp (°C)", 20.0, 95.0, 95.0, step=1.0)
        mode_choice = c2.selectbox("Fermentation Regime", ["All", "SSF", "SmF"])
        conf_only = c3.checkbox("HIGH confidence (dry-basis) only")

    base = df[df["temp_c"] <= max_temp]
    if mode_choice != "All":
        base = base[base["fermentation_mode"] == mode_choice]
    if conf_only:
        base = base[base["confidence"] == "HIGH"]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Active Specimens", len(base))
    m2.metric("Peak Activity (U/g dry)", f"{base['norm_yield'].max():.2f}" if len(base) else "0.00")
    m3.metric("Median Activity (U/g dry)", f"{base['norm_yield'].median():.2f}" if len(base) else "0.00")
    m4.metric("Enzyme Taxa", base["enzyme"].nunique())

    f1, f2, f3, f4 = st.columns(4)
    org = f1.selectbox("Organism", ["All"] + sorted(base["organism"].dropna().unique()))
    sub = f2.selectbox("Substrate Matrix", ["All"] + sorted(base["substrate"].dropna().unique()))
    enz = f3.selectbox("Enzyme", ["All"] + sorted(base["enzyme"].dropna().unique()))
    kw = f4.text_input("Keyword (Supplement / DOI)", placeholder="e.g., Peptone or 10.1016").strip()

    view = base
    for col, val in (("organism", org), ("substrate", sub), ("enzyme", enz)):
        if val != "All":
            view = view[view[col] == val]
    if kw:
        mask = False
        for col in ("supplements", "reference", "organism", "substrate"):
            mask = mask | view[col].str.contains(kw, case=False, na=False)
        view = view[mask]
    view = view.sort_values("norm_yield", ascending=False).reset_index(drop=True)

    if not view.empty:
        t = view.iloc[0]
        rng = lambda c, u="": f"{view[c].min()}–{view[c].max()}{u} (med {view[c].median():.1f})"
        st.markdown(f"""
        <div class="plate">
          <b>Featured Reference Specimen • {t['fermentation_mode']} • {t['confidence']} Confidence</b>
          <h3><em>{t['organism']}</em> on {t['substrate']} — {t['enzyme'].title()}</h3>
          Measured at <b>pH {t['ph']}</b>, <b>{t['temp_c']}°C</b>, <b>{t['moisture_pct']}% moisture</b>,
          <b>{t['time_hrs']} hrs</b> (Supplement: <em>{t['supplements']}</em>) yielding
          <b>{t['norm_yield']:.2f} U/g dry</b> (Reported: {t['raw_yield']} {t['raw_unit']}).<br>
          <span class="pill">pH: {rng('ph')}</span><span class="pill">Temp: {rng('temp_c', '°C')}</span>
          <span class="pill">Moisture: {rng('moisture_pct', '%')}</span><span class="pill">Incubation: {rng('time_hrs', 'h')}</span>
        </div>""", unsafe_allow_html=True)

    render_table(view)
    if not base.empty:
        st.download_button("Export Filtered Catalogue (CSV)", base.drop(columns=["id"]).to_csv(index=False).encode(),
                           file_name="biocatalyst_archive_filtered.csv", mime="text/csv")

# ---------- 2. Calculator ----------
elif page == "Batch & Yield Calculator":
    st.subheader("⚖️ Solid-State Batch Water & Total Activity Calculator")
    st.caption("Estimate water/buffer for a target moisture level and total enzyme units for a chosen entry.")
    labels = [f"{r.organism} | {r.substrate} | {r.enzyme} ({r.norm_yield:.1f} U/g dry)" for r in df.itertuples()]
    idx = st.selectbox("Select Reference Specimen", range(len(labels)), format_func=lambda i: labels[i])
    rec = df.iloc[idx]
    left, right = st.columns(2)
    with left:
        dry = st.number_input("Dry Substrate Mass (g)", min_value=1.0, value=100.0, step=10.0)
        target = st.slider("Target Moisture (%)", 20.0, 85.0, float(min(max(rec["moisture_pct"], 20), 85)), step=1.0)
    with right:
        water = dry * (target / 100) / (1 - target / 100)
        st.metric("Estimated Water / Buffer to Add", f"{water:.1f} mL")
        st.metric("Total Wet Batch Mass", f"{dry + water:.1f} g")
        st.metric("Estimated Total Enzyme Activity", f"{dry * rec['norm_yield']:,.1f} U")

# ---------- 3. Comparator ----------
elif page == "Head-to-Head Comparator":
    st.subheader("⚔️ Side-by-Side Specimen Comparator")
    if len(df) >= 2:
        opts = [f"#{i + 1}: {r.organism} on {r.substrate} [{r.enzyme}]" for i, r in enumerate(df.itertuples())]
        ca, cb = st.columns(2)
        a = ca.selectbox("Specimen A", range(len(opts)), index=0, format_func=lambda i: opts[i])
        b = cb.selectbox("Specimen B", range(len(opts)), index=1, format_func=lambda i: opts[i])
        fields = [("Organism", "organism"), ("Substrate", "substrate"), ("Enzyme", "enzyme"),
                  ("Mode", "fermentation_mode"), ("Norm Yield (U/g dry)", "norm_yield"), ("pH", "ph"),
                  ("Temp (°C)", "temp_c"), ("Moisture (%)", "moisture_pct"), ("Time (hrs)", "time_hrs"),
                  ("Supplements", "supplements")]
        comp = pd.DataFrame({
            "Metric": [f[0] for f in fields],
            "Specimen A": [str(df.iloc[a][f[1]]) for f in fields],
            "Specimen B": [str(df.iloc[b][f[1]]) for f in fields],
        })
        st.dataframe(comp, hide_index=True, use_container_width=True)

# ---------- 4. Add / Import ----------
elif page == "Add / Import Data":
    if st.session_state.get("status_banner"):
        st.success(st.session_state.pop("status_banner"))

    if GH_OK:
        st.info(f"Connected to GitHub `{GH_REPO}` (`{GH_PATH}` on `{GH_BRANCH}`). New records commit automatically.")
    else:
        st.warning("Add `GITHUB_TOKEN` and `GITHUB_REPO` in Streamlit Secrets to commit uploads permanently.")

    tab_one, tab_csv = st.tabs(["Add Single Specimen", "Import CSV File"])

    with tab_one:
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
                    row = make_row({"organism": org, "substrate": sub.title(), "enzyme": enz.lower(),
                                    "raw_yield": ry, "raw_unit": ru, "moisture_pct": mo, "ph": ph,
                                    "temp_c": tc, "time_hrs": hr, "supplements": sp, "reference": rf,
                                    "fermentation_mode": mode}, recompute=True)
                    n, ok, msg = save_records([row])
                    st.session_state["status_banner"] = (
                        f"Database updated ({n} new row, normalized yield = {row[10]:.2f} U/g dry [{row[11]}]) "
                        + ("and synced to GitHub." if ok else f"({msg})"))
                    st.rerun()
                else:
                    st.error("Fill in Organism, Substrate, Enzyme, and Raw Yield > 0.")

    with tab_csv:
        up = st.file_uploader("Upload CSV", type=["csv"])
        if up is not None:
            up_df = pd.read_csv(up).fillna("")
            st.dataframe(up_df.head(8), use_container_width=True)
            if st.button("Import CSV Rows"):
                rows = []
                for _, r in up_df.iterrows():
                    r = r.copy()
                    r["substrate"] = str(r.get("substrate", "")).strip().title()
                    r["enzyme"] = str(r.get("enzyme", "")).strip().lower()
                    row = make_row(r, recompute=True)
                    if row:
                        rows.append(row)
                n, ok, msg = save_records(rows)
                st.session_state["status_banner"] = (
                    f"Database updated ({n} new record(s) imported) "
                    + (f"and committed to `{GH_PATH}` on GitHub." if ok else f"({msg})"))
                st.rerun()

# ---------- 5. Plots ----------
elif page == "Matplotlib Plates":
    st.subheader("📈 Custom Matplotlib Specimen Plates")
    plt.style.use("dark_background")

    c1, c2 = st.columns([1.2, 1])
    focus = c1.selectbox("1. What do you want to focus on?", ["Substrate", "Organism", "Enzyme"])
    stat = c2.selectbox("2. Yield summary to plot", ["Peak Yield (Max)", "Typical Yield (Median)", "All Individual Runs"])

    others = {"Substrate": ["organism", "enzyme"], "Organism": ["substrate", "enzyme"], "Enzyme": ["organism", "substrate"]}
    main = focus.lower()
    sec, ter = others[focus]
    items = sorted(df[main].dropna().unique())
    picked = st.multiselect(f"3. Select one or more {focus}s to inspect", items, default=items[:3])
    breakdown = st.selectbox("4. Plot / break down against", [sec.title(), ter.title(), "None (Direct Comparison)"])

    sub_df = df[df[main].isin(picked)] if picked else df
    if sub_df.empty:
        st.warning("No records match your selection.")
    else:
        left, right = st.columns(2)

        with left:
            fig, ax = plt.subplots(figsize=(6.8, 4.5))
            fig.patch.set_facecolor("#121b22")
            ax.set_facecolor("#121b22")
            if stat == "All Individual Runs":
                o = sub_df.sort_values("norm_yield")
                ax.barh([f"{a} | {b}" for a, b in zip(o[main], o[sec])], o["norm_yield"], color="#38bdf8")
            else:
                fn = "max" if "Max" in stat else "median"
                if breakdown.startswith("None"):
                    g = sub_df.groupby(main)["norm_yield"].agg(fn).sort_values()
                    ax.barh(g.index, g.values, color="#38bdf8")
                else:
                    bc = breakdown.lower()
                    piv = sub_df.pivot_table(index=main, columns=bc, values="norm_yield", aggfunc=fn)
                    top = sub_df.groupby(bc)["norm_yield"].max().nlargest(6).index
                    piv[[c for c in top if c in piv.columns]].plot(kind="barh", ax=ax, width=0.78)
                    ax.legend(title=breakdown, fontsize=8, title_fontsize=8)
            ax.set_ylabel(focus)
            ax.set_xlabel(f"{stat} (U/g dry)")
            ax.set_title(f"{focus} Yield Breakdown")
            ax.grid(axis="x", linestyle="--", alpha=0.25)
            plt.tight_layout()
            st.pyplot(fig)

        with right:
            fig, ax = plt.subplots(figsize=(6.8, 4.5))
            fig.patch.set_facecolor("#121b22")
            ax.set_facecolor("#121b22")
            ax.scatter(sub_df["temp_c"], sub_df["norm_yield"], c="#34d399", alpha=0.85, edgecolors="#0b1115", s=65)
            ax.set_xlabel("Incubation Temperature (°C)")
            ax.set_ylabel("Normalized Yield (U/g dry)")
            ax.set_title("Temperature vs. Yield for Selected Items")
            ax.grid(True, linestyle="--", alpha=0.25)
            plt.tight_layout()
            st.pyplot(fig)
