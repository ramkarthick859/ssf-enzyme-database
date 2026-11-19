import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# 1. Page Configuration
st.set_page_config(
    page_title="BioCatalyst Bench | SSF & SmF Yield Explorer",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "ssf_database.db")

# Custom UI Styling: Always-open sidebar + distinct bioprocess cards
st.markdown(
    """
    <style>
        /* Keep left sidebar open and visible */
        [data-testid="stSidebar"] {
            min-width: 265px !important;
            max-width: 265px !important;
            transform: none !important;
            visibility: visible !important;
        }
        [data-testid="collapsedControl"] {
            display: none !important;
        }

        /* Custom header banner */
        .app-banner {
            background: linear-gradient(120deg, #0f2942 0%, #165b63 100%);
            padding: 1.25rem 1.5rem;
            border-radius: 14px;
            color: #ffffff;
            margin-bottom: 1rem;
            box-shadow: 0 4px 14px rgba(15, 41, 66, 0.14);
        }
        .app-banner h1 {
            margin: 0;
            font-size: 1.65rem;
            color: #ffffff;
        }
        .app-banner p {
            margin: 0.35rem 0 0 0;
            color: #d9f2f2;
            font-size: 0.95rem;
        }

        /* Highlight card for optimal conditions */
        .best-card {
            background: #f2fbf9;
            border-left: 5px solid #0e8a7d;
            border-radius: 10px;
            padding: 1rem 1.2rem;
            margin: 0.75rem 0 1rem 0;
            color: #102a43;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# 2. Thread-Safe SQLite Connection Helper
def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=30000;")
    return conn


# 3. Verified Seed Data (Non-overlapping organism + substrate + enzyme where possible)
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
                cursor.execute(
                    """
                    INSERT INTO ssf_experiments (
                        organism, substrate, enzyme, raw_yield, raw_unit, moisture_pct,
                        ph, temp_c, time_hrs, supplements, norm_yield, confidence, reference, fermentation_mode
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    row,
                )
            conn.commit()
    finally:
        conn.close()


init_db()


def to_float(x, default=0.0):
    if x is None:
        return default
    x_str = str(x).strip()
    try:
        return float(x_str) if x_str else default
    except ValueError:
        return default


def remove_duplicates_from_db():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        initial_count = cursor.execute("SELECT COUNT(*) FROM ssf_experiments").fetchone()[0]
        cursor.execute(
            """
            DELETE FROM ssf_experiments
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM ssf_experiments
                GROUP BY LOWER(TRIM(organism)), LOWER(TRIM(substrate)), LOWER(TRIM(enzyme)),
                         fermentation_mode, reference
            );
            """
        )
        conn.commit()
        final_count = cursor.execute("SELECT COUNT(*) FROM ssf_experiments").fetchone()[0]
        return initial_count - final_count
    finally:
        conn.close()


def normalize_yield(raw_yield, raw_unit, moisture_pct):
    unit = str(raw_unit).lower().strip()
    raw_yield = to_float(raw_yield, default=0.0)
    moisture_pct = to_float(moisture_pct, default=50.0)

    if "dry" in unit or "u/gds" in unit:
        return round(raw_yield, 2), "HIGH"
    elif "wet" in unit or unit == "u/g":
        dry_factor = 1.0 - (moisture_pct / 100.0)
        return (round(raw_yield / dry_factor, 2), "MEDIUM") if dry_factor > 0 else (round(raw_yield, 2), "LOW")
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


def display_table_with_links(df, show_rank=False):
    if df.empty:
        st.info("No matching records found.")
        return

    display_df = df.copy()
    if show_rank:
        display_df.insert(0, "rank", ["🏆 #1" if i == 0 else f"#{i+1}" for i in range(len(display_df))])

    if "raw_yield" in display_df.columns and "raw_unit" in display_df.columns:
        display_df["reported_yield"] = display_df.apply(
            lambda r: f"{r['raw_yield']} {r['raw_unit']}", axis=1
        )

    display_df["paper_url"] = display_df["reference"].apply(make_clickable_link)

    preferred_cols = [
        col
        for col in [
            "rank",
            "fermentation_mode",
            "organism",
            "substrate",
            "enzyme",
            "norm_yield",
            "reported_yield",
            "confidence",
            "ph",
            "temp_c",
            "moisture_pct",
            "time_hrs",
            "supplements",
            "paper_url",
            "reference",
        ]
        if col in display_df.columns
    ]

    st.dataframe(
        display_df[preferred_cols],
        column_config={
            "rank": "Rank",
            "fermentation_mode": "Mode",
            "paper_url": st.column_config.LinkColumn("Paper Link", display_text="🔗 Open DOI"),
            "organism": "Organism",
            "substrate": "Substrate",
            "enzyme": "Enzyme",
            "norm_yield": st.column_config.NumberColumn("Normalized Yield (U/g dry)", format="%.2f U/g"),
            "reported_yield": "Reported Yield",
            "confidence": "Confidence",
            "ph": "pH",
            "temp_c": "Temp (°C)",
            "moisture_pct": "Moisture (%)",
            "time_hrs": "Hours",
            "supplements": "Supplements",
            "reference": "DOI / Reference",
        },
        hide_index=True,
        use_container_width=True,
    )


def load_all_data():
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


def top_n_with_other(df, col, metric="norm_yield", agg="max", n=10):
    grouped = getattr(df.groupby(col)[metric], agg)().sort_values(ascending=False)
    if len(grouped) <= n:
        return grouped
    top_part = grouped.iloc[:n]
    other_val = grouped.iloc[n:].max() if agg == "max" else grouped.iloc[n:].mean()
    return pd.concat([top_part, pd.Series({f"Other ({len(grouped)-n})": other_val})])


# --- BANNER & ALWAYS-OPEN SIDEBAR RADIO NAVIGATION ---
st.markdown(
    """
    <div class="app-banner">
        <h1>🧬 BioCatalyst Bench — SSF & SmF Enzyme Yield Database</h1>
        <p>Non-cereal agro-industrial residues • Normalized enzyme activity • Matplotlib visual analytics</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### 🧭 Navigation")
    menu = st.radio(
        "Select Module",
        [
            "View Database",
            "Search & Filter",
            "Add Single Record",
            "Upload CSV Dataset",
            "Yield Data Visualizations",
            "Best Conditions Summary",
        ],
        label_visibility="collapsed",
    )
    st.markdown("---")
    df_side = load_all_data()
    st.caption(f"Total records: **{len(df_side)}**")

df = load_all_data()

# --- 1. VIEW DATABASE (Clean Database View, Metrics, Dedup & Export) ---
if menu == "View Database":
    st.subheader("📋 Complete Shared Database")

    c1, c2, c3, c4, c5 = st.columns([1.4, 1.4, 1.4, 1.8, 2.0])
    c1.metric("Total Records", len(df))
    c2.metric("Organisms", df["organism"].nunique() if not df.empty else 0)
    c3.metric("Substrates", df["substrate"].nunique() if not df.empty else 0)
    with c4:
        if st.button("🧹 Clean Duplicates", use_container_width=True):
            removed = remove_duplicates_from_db()
            st.toast(f"Removed {removed} duplicate record(s)." if removed else "No duplicates found.")
            st.rerun()
    with c5:
        if not df.empty:
            csv_bytes = df.drop(columns=["id"]).to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Export Dataset (CSV)",
                data=csv_bytes,
                file_name="ssf_smf_enzyme_database.csv",
                mime="text/csv",
                use_container_width=True,
            )

    display_table_with_links(df, show_rank=False)

# --- 2. SEARCH & FILTER (Tailored Selectors + Keyword Search + Best Condition Recommender) ---
elif menu == "Search & Filter":
    st.subheader("🔎 Search, Filter & Best Condition Recommender")

    p1, p2, p3, p4 = st.columns(4)
    if "preset_enzyme" not in st.session_state:
        st.session_state["preset_enzyme"] = "All"
    if "preset_mode" not in st.session_state:
        st.session_state["preset_mode"] = "All"

    if p1.button("Reset Filters", use_container_width=True):
        st.session_state["preset_enzyme"] = "All"
        st.session_state["preset_mode"] = "All"
        st.rerun()
    if p2.button("Top Pectinases", use_container_width=True):
        st.session_state["preset_enzyme"] = "pectinase"
        st.rerun()
    if p3.button("Top Xylanases", use_container_width=True):
        st.session_state["preset_enzyme"] = "xylanase"
        st.rerun()
    if p4.button("SSF Only", use_container_width=True):
        st.session_state["preset_mode"] = "SSF"
        st.rerun()

    if not df.empty:
        f1, f2, f3, f4 = st.columns([2.4, 2.4, 2.2, 1.4])
        org_options = ["All"] + sorted(df["organism"].dropna().unique().tolist())
        sub_options = ["All"] + sorted(df["substrate"].dropna().unique().tolist())
        enz_options = ["All"] + sorted(df["enzyme"].dropna().unique().tolist())
        mode_options = ["All"] + sorted(df["fermentation_mode"].dropna().unique().tolist())

        default_enz_idx = enz_options.index(st.session_state["preset_enzyme"]) if st.session_state["preset_enzyme"] in enz_options else 0
        default_mode_idx = mode_options.index(st.session_state["preset_mode"]) if st.session_state["preset_mode"] in mode_options else 0

        selected_org = f1.selectbox("Organism", org_options)
        selected_sub = f2.selectbox("Substrate", sub_options)
        selected_enz = f3.selectbox("Enzyme", enz_options, index=default_enz_idx)
        selected_mode = f4.selectbox("Mode", mode_options, index=default_mode_idx)

        k1, k2, k3 = st.columns(3)
        org_kw = k1.text_input("Organism Keyword", placeholder="e.g., Aspergillus, Bacillus")
        sub_kw = k2.text_input("Substrate Keyword", placeholder="e.g., Peel, Bagasse, Cake")
        supp_kw = k3.text_input("Supplement / DOI Keyword", placeholder="e.g., Peptone, 10.1016")

        filtered = df.copy()
        if selected_org != "All":
            filtered = filtered[filtered["organism"] == selected_org]
        if selected_sub != "All":
            filtered = filtered[filtered["substrate"] == selected_sub]
        if selected_enz != "All":
            filtered = filtered[filtered["enzyme"] == selected_enz]
        if selected_mode != "All":
            filtered = filtered[filtered["fermentation_mode"] == selected_mode]
        if org_kw.strip():
            filtered = filtered[filtered["organism"].str.contains(org_kw.strip(), case=False, na=False)]
        if sub_kw.strip():
            filtered = filtered[filtered["substrate"].str.contains(sub_kw.strip(), case=False, na=False)]
        if supp_kw.strip():
            mask = (
                filtered["supplements"].str.contains(supp_kw.strip(), case=False, na=False)
                | filtered["reference"].str.contains(supp_kw.strip(), case=False, na=False)
            )
            filtered = filtered[mask]

        filtered = filtered.sort_values(by="norm_yield", ascending=False).reset_index(drop=True)

        tab_res, tab_alt = st.tabs(["🏆 Best Conditions & Matching Records", "💡 Closest Alternatives"])

        with tab_res:
            if not filtered.empty:
                best = filtered.iloc[0]
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Peak Normalized Yield", f"{best['norm_yield']:.2f} U/g", f"Mean: {filtered['norm_yield'].mean():.2f} U/g")
                m2.metric("Top Organism", best["organism"])
                m3.metric("Top Substrate", best["substrate"])
                m4.metric("pH / Temp / Time", f"pH {best['ph']} • {best['temp_c']}°C • {best['time_hrs']}h")

                st.markdown(
                    f"""
                    <div class="best-card">
                        <strong>Recommended Protocol ({best['fermentation_mode']}):</strong>
                        Use <strong>{best['organism']}</strong> on <strong>{best['substrate']}</strong> to produce
                        <strong>{best['enzyme']}</strong> at <strong>pH {best['ph']}</strong>, <strong>{best['temp_c']}°C</strong>,
                        <strong>{best['moisture_pct']}% moisture</strong> for <strong>{best['time_hrs']} hrs</strong>
                        (Supplements: <em>{best['supplements']}</em>) → <strong>{best['norm_yield']:.2f} U/g dry</strong>
                        (Reported: {best['raw_yield']} {best['raw_unit']}).
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                display_table_with_links(filtered, show_rank=True)
            else:
                st.warning("No records match your exact filters.")

        with tab_alt:
            alt = pd.DataFrame()
            if selected_sub != "All" and selected_enz != "All":
                alt = df[(df["substrate"] == selected_sub) & (df["enzyme"] == selected_enz)]
            elif selected_org != "All" and selected_enz != "All":
                alt = df[(df["organism"] == selected_org) & (df["enzyme"] == selected_enz)]
            elif selected_enz != "All":
                alt = df[df["enzyme"] == selected_enz]
            elif selected_sub != "All":
                alt = df[df["substrate"] == selected_sub]

            if not alt.empty:
                display_table_with_links(alt.sort_values("norm_yield", ascending=False).head(15), show_rank=True)
            else:
                st.info("Select a substrate or enzyme above to see closest alternative combinations.")

# --- 3. ADD SINGLE RECORD ---
elif menu == "Add Single Record":
    st.subheader("➕ Add Experiment Record")
    if "single_add_msg" in st.session_state:
        st.success(st.session_state.pop("single_add_msg"))

    with st.form("add_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            organism = st.text_input("Organism Name", placeholder="e.g., Aspergillus niger")
            substrate = st.text_input("Non-Cereal Substrate", placeholder="e.g., Orange Peel")
            enzyme = st.text_input("Enzyme Type", placeholder="e.g., pectinase")
            fermentation_mode = st.selectbox("Fermentation Mode", ["SSF", "SmF"])
            raw_yield = st.number_input("Yield Value", min_value=0.0, value=0.0)
            raw_unit = st.selectbox("Yield Unit", ["U/g dry", "U/g wet", "U/mL"])
        with col_b:
            moisture_pct = st.number_input("Moisture %", min_value=0.0, max_value=100.0, value=60.0)
            ph = st.number_input("pH", value=5.0)
            temp_c = st.number_input("Temperature (°C)", value=30.0)
            time_hrs = st.number_input("Incubation Hours", value=72.0)
            supplements = st.text_input("Supplements", placeholder="e.g., Peptone")
            reference = st.text_input("DOI / Citation", placeholder="e.g., 10.1016/j.biortech.2009.08.087")

        if st.form_submit_button("Save Record"):
            if not organism.strip() or not substrate.strip() or not enzyme.strip() or raw_yield <= 0:
                st.error("Please enter Organism, Substrate, Enzyme, and a Yield Value > 0.")
            else:
                norm, conf = normalize_yield(raw_yield, raw_unit, moisture_pct)
                conn = get_connection()
                try:
                    conn.execute(
                        """
                        INSERT INTO ssf_experiments (
                            organism, substrate, enzyme, raw_yield, raw_unit, moisture_pct,
                            ph, temp_c, time_hrs, supplements, norm_yield, confidence, reference, fermentation_mode
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            organism.strip(),
                            substrate.strip().title(),
                            enzyme.strip().lower(),
                            raw_yield,
                            raw_unit,
                            moisture_pct,
                            ph,
                            temp_c,
                            time_hrs,
                            supplements.strip() or "None",
                            norm,
                            conf,
                            reference.strip() or "Unknown",
                            fermentation_mode,
                        ),
                    )
                    conn.commit()
                finally:
                    conn.close()
                remove_duplicates_from_db()
                st.session_state["single_add_msg"] = f"Saved! Normalized Yield: {norm:.2f} U/g dry ({conf} confidence)."
                st.rerun()

# --- 4. UPLOAD CSV DATASET ---
elif menu == "Upload CSV Dataset":
    st.subheader("📤 Bulk Import via CSV")
    st.info("Required columns: `organism, substrate, enzyme, raw_yield, raw_unit, moisture_pct` | Optional: `ph, temp_c, time_hrs, supplements, reference, fermentation_mode`")

    if "uploader_key" not in st.session_state:
        st.session_state["uploader_key"] = 0
    if "upload_success_msg" in st.session_state:
        st.success(st.session_state.pop("upload_success_msg"))

    uploaded_file = st.file_uploader("Upload CSV", type=["csv"], key=f"csv_up_{st.session_state['uploader_key']}")
    if uploaded_file is not None:
        df_up = pd.read_csv(uploaded_file).fillna("")
        st.dataframe(df_up.head(10), use_container_width=True)
        if st.button("Import Into Database"):
            added = 0
            conn = get_connection()
            try:
                for _, row in df_up.iterrows():
                    org = str(row.get("organism", "")).strip()
                    sub = str(row.get("substrate", "")).strip().title()
                    enz = str(row.get("enzyme", "")).strip().lower()
                    if not org or not sub or not enz:
                        continue
                    r_yield = to_float(row.get("raw_yield"), 0.0)
                    r_unit = str(row.get("raw_unit", "U/g dry")).strip() or "U/g dry"
                    moist = to_float(row.get("moisture_pct"), 50.0)
                    ph_val = to_float(row.get("ph"), 7.0)
                    temp_val = to_float(row.get("temp_c"), 30.0)
                    time_val = to_float(row.get("time_hrs"), 48.0)
                    supp = str(row.get("supplements") or "None").strip()
                    ref = str(row.get("reference") or "Unknown").strip()
                    mode = "SmF" if str(row.get("fermentation_mode") or "SSF").strip().lower() == "smf" else "SSF"
                    norm, conf = normalize_yield(r_yield, r_unit, moist)
                    conn.execute(
                        """
                        INSERT INTO ssf_experiments (
                            organism, substrate, enzyme, raw_yield, raw_unit, moisture_pct,
                            ph, temp_c, time_hrs, supplements, norm_yield, confidence, reference, fermentation_mode
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (org, sub, enz, r_yield, r_unit, moist, ph_val, temp_val, time_val, supp, norm, conf, ref, mode),
                    )
                    added += 1
                conn.commit()
            finally:
                conn.close()
            dups = remove_duplicates_from_db()
            st.session_state["uploader_key"] += 1
            st.session_state["upload_success_msg"] = f"Imported {added} rows ({dups} duplicates cleaned)."
            st.rerun()

# --- 5. YIELD DATA VISUALIZATIONS (Matplotlib Only, Top-N + Other, Dynamic Sizing) ---
elif menu == "Yield Data Visualizations":
    st.subheader("📈 Matplotlib Enzyme Yield Visualizations")
    if df.empty:
        st.warning("No data available.")
    else:
        ctrl1, ctrl2, ctrl3 = st.columns(3)
        top_n = ctrl1.selectbox("Show Top Categories", [8, 12, 15, 20], index=1)
        enz_filter = ctrl2.selectbox("Filter Enzyme (Optional)", ["All"] + sorted(df["enzyme"].dropna().unique().tolist()))
        use_log = ctrl3.checkbox("Log Scale for Yield", value=False)

        vdf = df.copy()
        if enz_filter != "All":
            vdf = vdf[vdf["enzyme"] == enz_filter]

        t1, t2 = st.tabs(["Top Substrates & Organisms", "Enzyme Yield Distribution"])

        with t1:
            c_left, c_right = st.columns(2)
            with c_left:
                s_series = top_n_with_other(vdf, "substrate", n=top_n).sort_values(ascending=True)
                fig, ax = plt.subplots(figsize=(7, max(4.2, len(s_series) * 0.36)))
                ax.barh(s_series.index, s_series.values, color="#165b63")
                if use_log:
                    ax.set_xscale("log")
                ax.set_xlabel("Max Normalized Yield (U/g dry)")
                ax.set_title(f"Top {top_n} Substrates (+ Other)")
                ax.grid(axis="x", linestyle="--", alpha=0.4)
                plt.tight_layout()
                st.pyplot(fig)

            with c_right:
                o_series = top_n_with_other(vdf, "organism", n=top_n).sort_values(ascending=True)
                fig, ax = plt.subplots(figsize=(7, max(4.2, len(o_series) * 0.36)))
                ax.barh(o_series.index, o_series.values, color="#0e8a7d")
                if use_log:
                    ax.set_xscale("log")
                ax.set_xlabel("Max Normalized Yield (U/g dry)")
                ax.set_title(f"Top {top_n} Organisms (+ Other)")
                ax.grid(axis="x", linestyle="--", alpha=0.4)
                plt.tight_layout()
                st.pyplot(fig)

        with t2:
            top_enz = vdf.groupby("enzyme")["norm_yield"].median().sort_values(ascending=False).head(top_n).index.tolist()
            bdf = vdf[vdf["enzyme"].isin(top_enz)]
            fig, ax = plt.subplots(figsize=(10, 4.8))
            data_groups = [bdf[bdf["enzyme"] == e]["norm_yield"].values for e in top_enz]
            ax.boxplot(data_groups, tick_labels=top_enz, vert=True, patch_artist=True)
            if use_log:
                ax.set_yscale("log")
            ax.set_ylabel("Normalized Yield (U/g dry)")
            ax.set_title("Normalized Yield Distribution by Enzyme Class")
            plt.xticks(rotation=25, ha="right")
            ax.grid(axis="y", linestyle="--", alpha=0.4)
            plt.tight_layout()
            st.pyplot(fig)

# --- 6. BEST CONDITIONS SUMMARY ---
elif menu == "Best Conditions Summary":
    st.subheader("🎯 Optimal Conditions by Substrate & Enzyme Pair")
    if df.empty:
        st.warning("No data available.")
    else:
        rows = []
        for (sub, enz), grp in df.groupby(["substrate", "enzyme"]):
            top3 = grp.sort_values("norm_yield", ascending=False).head(3)
            best = top3.iloc[0]
            rows.append(
                {
                    "Substrate": sub,
                    "Enzyme": enz,
                    "Best Mode": best["fermentation_mode"],
                    "Best Yield (U/g)": best["norm_yield"],
                    "Best Organism": best["organism"],
                    "Optimal pH": best["ph"],
                    "Optimal Temp (°C)": best["temp_c"],
                    "Optimal Hours": best["time_hrs"],
                    "Top-3 Avg pH": round(top3["ph"].mean(), 1),
                    "Top-3 Avg Temp (°C)": round(top3["temp_c"].mean(), 1),
                }
            )
        summary_df = pd.DataFrame(rows).sort_values("Best Yield (U/g)", ascending=False)
        st.dataframe(summary_df, hide_index=True, use_container_width=True)
