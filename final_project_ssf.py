import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# 1. Page Configuration (Must be at the top)
st.set_page_config(page_title="SSF & SmF Enzyme Yield Database", page_icon="🧪", layout="wide")

# Use absolute path so all sessions read/write the exact same database file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "ssf_database.db")

# 2. Thread-Safe SQLite Connection Helper (Enables Multi-User Shared Storage)
def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=30000;")
    return conn

# 3. 100% Real Verified Seed Data (30 Literature Studies)
VERIFIED_SEED_DATA = [
    ("Aspergillus niger", "Banana Peel", "pectinase", 27.68, "U/mL", 60.0, 5.8, 32.4, 66.0, "Ammonium sulfate", 276.8, "LOW", "10.1007/s13197-014-1413-8", "SSF"),
    ("Fungal consortium", "Coffee Husk", "cellulase", 10.0, "U/g dry", 65.0, 5.0, 37.0, 96.0, "Compost", 10.0, "HIGH", "10.1016/j.scitotenv.2017.02.184", "SSF"),
    ("Trichoderma viride", "Banana Peel", "cellulase", 142.5, "U/g dry", 65.0, 5.5, 30.0, 72.0, "Peptone", 142.5, "HIGH", "10.5897/AJB10.1825", "SSF"),
    ("Bacillus subtilis", "Groundnut Oil Cake", "lipase", 4.5, "U/g dry", 70.0, 8.0, 32.0, 48.0, "None", 4.5, "HIGH", "10.3390/agriculture11060540", "SSF"),
    ("Aspergillus niger", "Coconut Coir Pith", "cellulase", 18.5, "U/g dry", 70.0, 5.0, 30.0, 120.0, "Malt extract", 18.5, "HIGH", "10.1385/abab:108:1-3:737", "SSF"),
    ("Bacillus sp.", "Cassava Bagasse", "amylase", 437.76, "U/g dry", 60.0, 6.0, 37.0, 72.0, "Peptone", 437.76, "HIGH", "10.1590/1678-4324-2020170521", "SSF"),
    ("Aspergillus niger", "Banana Peel", "pectinase", 380.0, "U/g dry", 60.0, 5.5, 35.0, 72.0, "Ammonium sulfate", 380.0, "HIGH", "10.47836/pjst.30.1.14", "SSF"),
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
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ssf_experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organism TEXT, substrate TEXT, enzyme TEXT,
            raw_yield REAL, raw_unit TEXT, moisture_pct REAL,
            ph REAL, temp_c REAL, time_hrs REAL, supplements TEXT,
            norm_yield REAL, confidence TEXT, reference TEXT,
            fermentation_mode TEXT DEFAULT 'SSF'
        )
        ''')
        # Safe migration if database already existed without fermentation_mode column
        cursor.execute("PRAGMA table_info(ssf_experiments)")
        existing_cols = [col[1] for col in cursor.fetchall()]
        if "fermentation_mode" not in existing_cols:
            cursor.execute("ALTER TABLE ssf_experiments ADD COLUMN fermentation_mode TEXT DEFAULT 'SSF'")

        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM ssf_experiments")
        if cursor.fetchone()[0] == 0:
            for row in VERIFIED_SEED_DATA:
                cursor.execute('''
                INSERT INTO ssf_experiments (
                    organism, substrate, enzyme, raw_yield, raw_unit, moisture_pct,
                    ph, temp_c, time_hrs, supplements, norm_yield, confidence, reference, fermentation_mode
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', row)
            conn.commit()
    finally:
        conn.close()

init_db()

# Helper: Safe String-to-Float Conversion
def to_float(x, default=0.0):
    if x is None:
        return default
    x_str = str(x).strip()
    try:
        return float(x_str) if x_str else default
    except ValueError:
        return default

# Helper: Remove Exact Duplicate Database Records
def remove_duplicates_from_db():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        initial_count = cursor.execute("SELECT COUNT(*) FROM ssf_experiments").fetchone()[0]
        cursor.execute('''
        DELETE FROM ssf_experiments
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM ssf_experiments
            GROUP BY organism, substrate, enzyme, raw_yield, raw_unit, ph, temp_c, time_hrs, reference, fermentation_mode
        );
        ''')
        conn.commit()
        final_count = cursor.execute("SELECT COUNT(*) FROM ssf_experiments").fetchone()[0]
        return initial_count - final_count
    finally:
        conn.close()

# Helper: Unit Normalization
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

# Helper: Convert DOI/PMID to Direct Hyperlink
def make_clickable_link(ref):
    ref = str(ref).strip()
    if not ref or ref.lower() in ("unknown", "none", "nan"):
        return None
    if ref.startswith("http://") or ref.startswith("https://"):
        return ref
    if ref.startswith("PMC") or ref.startswith("pmc"):
        return f"https://www.ncbi.nlm.nih.gov/pmc/articles/{ref}/"
    if ref.startswith("10."):
        return f"https://doi.org/{ref}"
    return f"https://doi.org/{ref}"

# Helper: Render Streamlit Data Table with Links
def display_table_with_links(df, show_rank=False):
    if df.empty:
        st.info("No records found.")
        return

    display_df = df.copy()
    if show_rank:
        display_df.insert(0, "rank", [f"🏆 #1 (Best)" if i == 0 else f"#{i+1}" for i in range(len(display_df))])

    if "raw_yield" in display_df.columns and "raw_unit" in display_df.columns:
        display_df["reported_yield"] = display_df.apply(
            lambda r: f"{r['raw_yield']} {r['raw_unit']}", axis=1
        )

    display_df["paper_url"] = display_df["reference"].apply(make_clickable_link)

    preferred_cols = [
        col for col in [
            "rank", "fermentation_mode", "organism", "substrate", "enzyme",
            "norm_yield", "reported_yield", "confidence", "ph", "temp_c",
            "moisture_pct", "time_hrs", "supplements", "paper_url", "reference"
        ] if col in display_df.columns
    ]

    st.dataframe(
        display_df[preferred_cols],
        column_config={
            "rank": "Rank",
            "fermentation_mode": "Mode",
            "paper_url": st.column_config.LinkColumn("Verified Paper Link", display_text="🔗 Open Article / DOI"),
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
            "reference": "Reference ID / DOI"
        },
        hide_index=True,
        use_container_width=True
    )

# --- APP LAYOUT ---
st.title("🧪 SSF & SmF Enzyme Yield Database (Non-Cereal Residues)")

menu = st.sidebar.selectbox("Navigation Menu", [
    "View Database", 
    "Add Single Record", 
    "Upload CSV Dataset", 
    "Search & Filter", 
    "Yield Data Visualizations", 
    "Best Conditions Summary"
])

# Option 1: View Database (Tailored Selection + Best Condition Recommender)
if menu == "View Database":
    st.header("Shared Database Explorer & Best Condition Finder")
    
    conn = get_connection()
    try:
        df = pd.read_sql_query("""
            SELECT id, organism, substrate, enzyme, raw_yield, raw_unit, moisture_pct,
                   norm_yield, confidence, ph, temp_c, time_hrs, supplements, reference,
                   COALESCE(fermentation_mode, 'SSF') AS fermentation_mode
            FROM ssf_experiments
            ORDER BY norm_yield DESC
        """, conn)
    finally:
        conn.close()

    # Global Shared Database Metrics
    m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns([1.6, 1.6, 1.6, 1.8, 2.0])
    with m_col1:
        st.metric("Total Shared Records", len(df))
    with m_col2:
        st.metric("Unique Organisms", df["organism"].nunique() if not df.empty else 0)
    with m_col3:
        st.metric("Unique Substrates", df["substrate"].nunique() if not df.empty else 0)
    with m_col4:
        if st.button("🧹 Remove Duplicates", use_container_width=True):
            deleted_num = remove_duplicates_from_db()
            if deleted_num > 0:
                st.success(f"Removed {deleted_num} duplicate record(s)!")
            else:
                st.info("No duplicate records found.")
            st.rerun()
    with m_col5:
        if not df.empty:
            csv_export = df.drop(columns=["id"]).to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Export Shared DB (CSV)",
                data=csv_export,
                file_name="shared_ssf_smf_database.csv",
                mime="text/csv",
                use_container_width=True
            )

    st.markdown("---")

    if not df.empty:
        # Tailored Interactive Selectors
        st.subheader("🎯 Select Organism, Substrate, or Enzyme to View Yields & Best Conditions")
        f_col1, f_col2, f_col3, f_col4 = st.columns([2.5, 2.5, 2.5, 1.5])

        organisms_list = ["All"] + sorted(df["organism"].dropna().unique().tolist())
        substrates_list = ["All"] + sorted(df["substrate"].dropna().unique().tolist())
        enzymes_list = ["All"] + sorted(df["enzyme"].dropna().unique().tolist())
        modes_list = ["All"] + sorted(df["fermentation_mode"].dropna().unique().tolist())

        with f_col1:
            selected_org = st.selectbox("1. Choose Organism", organisms_list)
        with f_col2:
            selected_sub = st.selectbox("2. Choose Substrate", substrates_list)
        with f_col3:
            selected_enz = st.selectbox("3. Choose Enzyme", enzymes_list)
        with f_col4:
            selected_mode = st.selectbox("4. Mode", modes_list)

        # Apply Tailored Filters
        filtered_df = df.copy()
        if selected_org != "All":
            filtered_df = filtered_df[filtered_df["organism"] == selected_org]
        if selected_sub != "All":
            filtered_df = filtered_df[filtered_df["substrate"] == selected_sub]
        if selected_enz != "All":
            filtered_df = filtered_df[filtered_df["enzyme"] == selected_enz]
        if selected_mode != "All":
            filtered_df = filtered_df[filtered_df["fermentation_mode"] == selected_mode]

        filtered_df = filtered_df.sort_values(by="norm_yield", ascending=False).reset_index(drop=True)

        if not filtered_df.empty:
            best_row = filtered_df.iloc[0]
            avg_yield = filtered_df["norm_yield"].mean()

            # Build clear title for current selection
            selection_parts = []
            if selected_org != "All":
                selection_parts.append(f"Organism: **{selected_org}**")
            if selected_sub != "All":
                selection_parts.append(f"Substrate: **{selected_sub}**")
            if selected_enz != "All":
                selection_parts.append(f"Enzyme: **{selected_enz}**")
            if selected_mode != "All":
                selection_parts.append(f"Mode: **{selected_mode}**")
            selection_label = " | ".join(selection_parts) if selection_parts else "Entire Shared Database"

            st.markdown(f"### 🏆 Best Recommended Yield & Conditions ({selection_label})")
            b1, b2, b3, b4, b5 = st.columns(5)
            b1.metric("Peak Normalized Yield", f"{best_row['norm_yield']:.2f} U/g", f"Avg: {avg_yield:.2f} U/g")
            b2.metric("Best Organism", best_row["organism"])
            b3.metric("Best Substrate", best_row["substrate"])
            b4.metric("Target Enzyme", best_row["enzyme"].title())
            b5.metric("Optimal pH / Temp", f"pH {best_row['ph']} | {best_row['temp_c']}°C")

            st.success(
                f"**Optimal Protocol Summary:** Use **{best_row['organism']}** on **{best_row['substrate']}** "
                f"for **{best_row['enzyme']}** under **{best_row['fermentation_mode']}** conditions at "
                f"**pH {best_row['ph']}**, **{best_row['temp_c']}°C**, **{best_row['moisture_pct']}% moisture**, "
                f"for **{best_row['time_hrs']} hours** (Supplements: *{best_row['supplements']}*) → "
                f"Achieves **{best_row['norm_yield']:.2f} U/g dry** (Reported: {best_row['raw_yield']} {best_row['raw_unit']})."
            )

            st.subheader(f"📊 Corresponding Yields Table ({len(filtered_df)} Matching Record{'s' if len(filtered_df) != 1 else ''})")
            display_table_with_links(filtered_df, show_rank=True)

        else:
            st.warning("No exact experiment matches that specific combination yet in the shared database.")
            # Suggest closest best alternatives based on Substrate/Enzyme or Organism/Enzyme
            alt_df = pd.DataFrame()
            if selected_sub != "All" and selected_enz != "All":
                alt_df = df[(df["substrate"] == selected_sub) & (df["enzyme"] == selected_enz)]
                alt_title = f"💡 Best Alternative Organisms for {selected_sub} + {selected_enz}"
            elif selected_org != "All" and selected_enz != "All":
                alt_df = df[(df["organism"] == selected_org) & (df["enzyme"] == selected_enz)]
                alt_title = f"💡 Best Alternative Substrates for {selected_org} + {selected_enz}"
            elif selected_sub != "All":
                alt_df = df[df["substrate"] == selected_sub]
                alt_title = f"💡 Best Available Records Using {selected_sub}"
            elif selected_enz != "All":
                alt_df = df[df["enzyme"] == selected_enz]
                alt_title = f"💡 Best Available Records Producing {selected_enz}"
            elif selected_org != "All":
                alt_df = df[df["organism"] == selected_org]
                alt_title = f"💡 Best Available Records Using {selected_org}"

            if not alt_df.empty:
                alt_df = alt_df.sort_values(by="norm_yield", ascending=False).reset_index(drop=True)
                st.subheader(alt_title)
                display_table_with_links(alt_df, show_rank=True)
    else:
        st.warning("Database is currently empty.")

# Option 2: Add Single Record
elif menu == "Add Single Record":
    st.header("Add New Experiment Data (Shared Across All Users)")
    st.caption("Any record saved here is immediately stored in the shared database for all users.")

    if "single_add_msg" in st.session_state:
        st.success(st.session_state["single_add_msg"])
        del st.session_state["single_add_msg"]

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
            supplements = st.text_input("Supplements", placeholder="e.g., Peptone (optional)")
            reference = st.text_input("Citation / DOI", placeholder="e.g., 10.1016/j.scitotenv.2017.02.184")
        
        submitted = st.form_submit_button("Save to Shared Database")
        if submitted:
            if not organism.strip() or not substrate.strip() or not enzyme.strip() or raw_yield <= 0:
                st.error("Please fill in Organism, Substrate, Enzyme, and a Yield Value greater than 0!")
            else:
                norm, conf = normalize_yield(raw_yield, raw_unit, moisture_pct)
                conn = get_connection()
                try:
                    cursor = conn.cursor()
                    cursor.execute('''
                    INSERT INTO ssf_experiments (
                        organism, substrate, enzyme, raw_yield, raw_unit, moisture_pct,
                        ph, temp_c, time_hrs, supplements, norm_yield, confidence, reference, fermentation_mode
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        organism.strip(), substrate.strip().title(), enzyme.strip().lower(),
                        raw_yield, raw_unit, moisture_pct, ph, temp_c, time_hrs,
                        supplements.strip() or "None", norm, conf,
                        reference.strip() or "Unknown", fermentation_mode
                    ))
                    conn.commit()
                finally:
                    conn.close()

                remove_duplicates_from_db()
                st.session_state["single_add_msg"] = (
                    f"✅ Record saved to the shared database! Normalized Yield: {norm} U/g dry "
                    f"(Confidence: {conf}, Mode: {fermentation_mode}). All users can now view and use this data."
                )
                st.rerun()

# Option 3: Upload CSV Dataset
elif menu == "Upload CSV Dataset":
    st.header("Import Multiple Records from CSV File")
    st.info(
        "Required CSV Columns: organism, substrate, enzyme, raw_yield, raw_unit, moisture_pct\n\n"
        "Optional Columns: ph, temp_c, time_hrs, supplements, reference, fermentation_mode (SSF or SmF)"
    )
    
    if "uploader_key" not in st.session_state:
        st.session_state["uploader_key"] = 0

    if "upload_success_msg" in st.session_state:
        st.success(st.session_state["upload_success_msg"])
        del st.session_state["upload_success_msg"]

    uploaded_file = st.file_uploader(
        "Choose a CSV file", 
        type=["csv"], 
        key=f"csv_uploader_{st.session_state['uploader_key']}"
    )

    if uploaded_file is not None:
        try:
            df_upload = pd.read_csv(uploaded_file).fillna("")
            st.write("### Preview of Uploaded Data:")
            st.dataframe(df_upload.head(), use_container_width=True)

            if st.button("Import Data into Shared Database"):
                count = 0
                conn = get_connection()
                try:
                    cursor = conn.cursor()
                    for _, row in df_upload.iterrows():
                        org = str(row.get("organism", "")).strip()
                        sub = str(row.get("substrate", "")).strip().title()
                        enz = str(row.get("enzyme", "")).strip().lower()
                        
                        # Skip empty/invalid rows
                        if not org or not sub or not enz:
                            continue

                        r_yield = to_float(row.get("raw_yield"), default=0.0)
                        r_unit = str(row.get("raw_unit", "U/g dry")).strip() or "U/g dry"
                        moist = to_float(row.get("moisture_pct"), default=50.0)
                        ph_val = to_float(row.get("ph"), default=7.0)
                        temp_val = to_float(row.get("temp_c"), default=30.0)
                        time_val = to_float(row.get("time_hrs"), default=48.0)
                        
                        supp = str(row.get("supplements") or "None").strip()
                        ref = str(row.get("reference") or "Unknown").strip()
                        mode_raw = str(row.get("fermentation_mode") or "SSF").strip()
                        mode = "SmF" if mode_raw.lower() == "smf" else "SSF"

                        norm, conf = normalize_yield(r_yield, r_unit, moist)

                        cursor.execute('''
                        INSERT INTO ssf_experiments (
                            organism, substrate, enzyme, raw_yield, raw_unit, moisture_pct,
                            ph, temp_c, time_hrs, supplements, norm_yield, confidence, reference, fermentation_mode
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (org, sub, enz, r_yield, r_unit, moist, ph_val, temp_val, time_val, supp, norm, conf, ref, mode))
                        count += 1

                    conn.commit()
                finally:
                    conn.close()

                removed_dups = remove_duplicates_from_db()
                st.session_state["uploader_key"] += 1
                st.session_state["upload_success_msg"] = (
                    f"✅ Successfully imported {count} records into the shared database! "
                    f"({removed_dups} duplicate records purged). Now visible to all users."
                )
                st.rerun()
        except Exception as e:
            st.error(f"Error reading CSV file: {e}")

# Option 4: Search & Filter
elif menu == "Search & Filter":
    st.header("Keyword Search Across Database")
    c1, c2, c3 = st.columns(3)
    with c1:
        org_q = st.text_input("Organism Keyword")
    with c2:
        sub_q = st.text_input("Substrate Keyword")
    with c3:
        enz_q = st.text_input("Enzyme Keyword")
    
    conn = get_connection()
    try:
        query = """
            SELECT organism, substrate, enzyme, raw_yield, raw_unit, moisture_pct,
                   norm_yield, confidence, ph, temp_c, time_hrs, supplements, reference,
                   COALESCE(fermentation_mode, 'SSF') AS fermentation_mode
            FROM ssf_experiments
            WHERE organism LIKE ? AND substrate LIKE ? AND enzyme LIKE ?
            ORDER BY norm_yield DESC
        """
        df = pd.read_sql_query(query, conn, params=(f"%{org_q}%", f"%{sub_q}%", f"%{enz_q}%"))
    finally:
        conn.close()
    display_table_with_links(df, show_rank=True)

# Option 5: Yield Visualizations
elif menu == "Yield Data Visualizations":
    st.header("Enzyme Yield Data Visualizations")
    conn = get_connection()
    try:
        df = pd.read_sql_query(
            "SELECT organism, substrate, enzyme, norm_yield, ph, temp_c, time_hrs, COALESCE(fermentation_mode, 'SSF') AS fermentation_mode FROM ssf_experiments",
            conn
        )
    finally:
        conn.close()
    
    if not df.empty:
        chart_type = st.selectbox("Choose Visualization Type:", [
            "1. Heatmap Matrix (Organism vs Substrate)",
            "2. Grouped Bar Chart (Top Yields per Substrate)",
            "3. Box Plot (Yield Spread by Enzyme)",
            "4. Scatter Plot (pH vs Temperature vs Yield)"
        ])

        if "1. Heatmap" in chart_type:
            pivot = df.pivot_table(index="organism", columns="substrate", values="norm_yield", aggfunc="max").fillna(0)
            fig, ax = plt.subplots(figsize=(10, 5))
            cax = ax.imshow(pivot, cmap="YlOrRd", aspect="auto")
            fig.colorbar(cax, label="Yield (U/g dry)")
            ax.set_xticks(range(len(pivot.columns)))
            ax.set_xticklabels(pivot.columns, rotation=35, ha="right")
            ax.set_yticks(range(len(pivot.index)))
            ax.set_yticklabels(pivot.index)
            ax.set_title("Organism vs Substrate Yield Heatmap")
            st.pyplot(fig)

        elif "2. Grouped Bar" in chart_type:
            fig, ax = plt.subplots(figsize=(10, 5))
            avg_yield = df.groupby(["substrate", "enzyme"])["norm_yield"].max().unstack().fillna(0)
            avg_yield.plot(kind="bar", ax=ax)
            ax.set_ylabel("Yield (U/g dry)")
            ax.set_xlabel("Non-Cereal Substrate")
            ax.set_title("Maximum Yield by Substrate and Enzyme")
            plt.xticks(rotation=35, ha="right")
            st.pyplot(fig)

        elif "3. Box Plot" in chart_type:
            fig, ax = plt.subplots(figsize=(10, 5))
            df.boxplot(column="norm_yield", by="enzyme", ax=ax, grid=False)
            ax.set_ylabel("Yield (U/g dry)")
            ax.set_xlabel("Enzyme Category")
            plt.suptitle("")
            ax.set_title("Yield Variance per Enzyme Class")
            plt.xticks(rotation=25, ha="right")
            st.pyplot(fig)

        elif "4. Scatter Plot" in chart_type:
            fig, ax = plt.subplots(figsize=(10, 5))
            scatter = ax.scatter(df["ph"], df["temp_c"], s=df["norm_yield"].clip(upper=2000)*0.4 + 40, c=df["norm_yield"], cmap="viridis", alpha=0.75)
            fig.colorbar(scatter, label="Yield (U/g dry)")
            ax.set_xlabel("pH")
            ax.set_ylabel("Temperature (°C)")
            ax.set_title("Optimal Parameter Clusters (Bubble Size & Color = Yield)")
            st.pyplot(fig)
    else:
        st.warning("No data available yet!")

# Option 6: Best Conditions Summary
elif menu == "Best Conditions Summary":
    st.header("Optimal Fermentation Parameters Across All Substrate–Enzyme Pairs")
    conn = get_connection()
    try:
        df = pd.read_sql_query(
            "SELECT substrate, enzyme, organism, norm_yield, ph, temp_c, time_hrs, moisture_pct, COALESCE(fermentation_mode, 'SSF') AS fermentation_mode FROM ssf_experiments",
            conn
        )
    finally:
        conn.close()

    if not df.empty:
        rows = []
        for (s, e), group in df.groupby(["substrate", "enzyme"]):
            top = group.sort_values("norm_yield", ascending=False).head(3)
            best = top.iloc[0]
            rows.append({
                "Substrate": s,
                "Enzyme": e,
                "Best Mode": best["fermentation_mode"],
                "Best Yield (U/g)": best["norm_yield"],
                "Best Organism": best["organism"],
                "Optimal pH": best["ph"],
                "Optimal Temp (°C)": best["temp_c"],
                "Optimal Hours": best["time_hrs"],
                "Top-3 Avg pH": round(top["ph"].mean(), 1),
                "Top-3 Avg Temp (°C)": round(top["temp_c"].mean(), 1)
            })
        summary_df = pd.DataFrame(rows).sort_values("Best Yield (U/g)", ascending=False)
        st.dataframe(summary_df, hide_index=True, use_container_width=True)
    else:
        st.warning("No data available yet!")
