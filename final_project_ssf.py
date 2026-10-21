import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# 1. Page Configuration
st.set_page_config(page_title="SSF Enzyme Yield Database", page_icon="🧪", layout="wide")

# 2. Setup SQLite Database
conn = sqlite3.connect("ssf_database.db", check_same_thread=False)
cursor = conn.cursor()

# 3. Verified Seed Data
VERIFIED_SEED_DATA = [
    ("Fungal consortium", "Coffee Husk", "cellulase", 10.0, "U/g dry", 65.0, 5.0, 37.0, 96.0, "Compost", 10.0, "HIGH", "10.1016/j.scitotenv.2017.02.184"),
    ("Aspergillus niger", "Banana Peel", "pectinase", 27.68, "U/mL", 60.0, 5.8, 35.0, 72.0, "Ammonium sulfate", 276.8, "LOW", "PMC4444909"),
    ("Aspergillus niger", "Orange Peel", "pectinase", 126.0, "U/g dry", 60.0, 5.0, 30.0, 72.0, "Citrate buffer", 126.0, "HIGH", "10.22207/JPAM.16.4.43"),
    ("Aspergillus oryzae", "Coconut Oil Cake", "protease", 1372.0, "U/g dry", 55.0, 6.0, 30.0, 24.0, "Peptone", 1372.0, "HIGH", "10.1016/j.jfoodeng.2005.05.022"),
    ("Bacillus subtilis", "Groundnut Oil Cake", "lipase", 4.5, "U/g dry", 70.0, 8.0, 32.0, 48.0, "None", 4.5, "HIGH", "10.3390/agriculture11060540"),
    ("Aspergillus niger", "Coir Pith", "cellulase", 18.5, "U/g dry", 70.0, 5.0, 30.0, 120.0, "Malt extract", 18.5, "HIGH", "10.1016/S0734-9750(97)00006-2"),
    ("Trichoderma viride", "Banana Peel", "cellulase", 142.5, "U/g dry", 65.0, 5.5, 30.0, 72.0, "Peptone", 142.5, "HIGH", "10.5897/AJB10.1825"),
    ("Aspergillus niger", "Orange Peel", "cellulase", 223.0, "U/g dry", 65.0, 5.0, 30.0, 72.0, "None", 223.0, "HIGH", "10.9734/ejnfs/2025/v17i51711"),
]

cursor.execute('''
CREATE TABLE IF NOT EXISTS ssf_experiments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organism TEXT, substrate TEXT, enzyme TEXT,
    raw_yield REAL, raw_unit TEXT, moisture_pct REAL,
    ph REAL, temp_c REAL, time_hrs REAL, supplements TEXT,
    norm_yield REAL, confidence TEXT, reference TEXT
)
''')
conn.commit()

cursor.execute("SELECT COUNT(*) FROM ssf_experiments")
if cursor.fetchone()[0] == 0:
    for row in VERIFIED_SEED_DATA:
        cursor.execute('''
        INSERT INTO ssf_experiments (organism, substrate, enzyme, raw_yield, raw_unit, moisture_pct, ph, temp_c, time_hrs, supplements, norm_yield, confidence, reference)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', row)
    conn.commit()

def normalize_yield(raw_yield, raw_unit, moisture_pct):
    unit = str(raw_unit).lower().strip()
    raw_yield = float(raw_yield)
    moisture_pct = float(moisture_pct)

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
    if not ref or ref.lower() == "unknown":
        return None
    if ref.startswith("http://") or ref.startswith("https://"):
        return ref
    if ref.startswith("PMC") or ref.startswith("pmc"):
        return f"https://www.ncbi.nlm.nih.gov/pmc/articles/{ref}/"
    if ref.startswith("10."):
        return f"https://doi.org/{ref}"
    return f"https://doi.org/{ref}"

def display_table_with_links(df):
    if df.empty:
        st.info("No records found.")
        return

    df["paper_url"] = df["reference"].apply(make_clickable_link)

    st.dataframe(
        df,
        column_config={
            "paper_url": st.column_config.LinkColumn("Verified Paper Link", display_text="🔗 Open Article / DOI"),
            "organism": "Organism",
            "substrate": "Substrate",
            "enzyme": "Enzyme",
            "norm_yield": st.column_config.NumberColumn("Yield (U/g dry)", format="%.2f U/g"),
            "confidence": "Confidence",
            "ph": "pH",
            "temp_c": "Temp (°C)",
            "time_hrs": "Hours",
            "supplements": "Supplements",
            "reference": "Reference ID / DOI"
        },
        hide_index=True,
        use_container_width=True
    )

# --- APP LAYOUT ---
st.title("🧪 SSF Enzyme Yield Database (Non-Cereal Residues)")

menu = st.sidebar.selectbox("Navigation Menu", [
    "View Database", 
    "Add Single Record", 
    "Upload CSV Dataset", 
    "Search & Filter", 
    "Yield Data Visualizations", 
    "Best Conditions Summary"
])

# Option 1: View Database
if menu == "View Database":
    st.header("All Stored Experiment Records")
    df = pd.read_sql_query("SELECT organism, substrate, enzyme, norm_yield, confidence, ph, temp_c, time_hrs, supplements, reference FROM ssf_experiments ORDER BY norm_yield DESC", conn)
    display_table_with_links(df)

# Option 2: Add Single Record
elif menu == "Add Single Record":
    st.header("Add New Experiment Data")
    with st.form("add_form"):
        organism = st.text_input("Organism Name", placeholder="e.g., Aspergillus niger")
        substrate = st.text_input("Non-Cereal Substrate", placeholder="e.g., Orange peel")
        enzyme = st.text_input("Enzyme Type", placeholder="e.g., pectinase")
        raw_yield = st.number_input("Yield Value", min_value=0.0, value=0.0)
        raw_unit = st.selectbox("Yield Unit", ["U/g dry", "U/g wet", "U/mL"])
        moisture_pct = st.number_input("Moisture %", min_value=0.0, max_value=100.0, value=60.0)
        ph = st.number_input("pH", value=5.0)
        temp_c = st.number_input("Temperature (°C)", value=30.0)
        time_hrs = st.number_input("Incubation Hours", value=72.0)
        supplements = st.text_input("Supplements", placeholder="e.g., Peptone (optional)")
        reference = st.text_input("Citation / DOI", placeholder="e.g., 10.1016/j.scitotenv.2017.02.184")
        
        submitted = st.form_submit_button("Save to Database")
        if submitted:
            if not organism or not substrate or not enzyme or raw_yield == 0:
                st.error("Please fill in Organism, Substrate, Enzyme, and Yield Value!")
            else:
                norm, conf = normalize_yield(raw_yield, raw_unit, moisture_pct)
                cursor.execute('''
                INSERT INTO ssf_experiments (organism, substrate, enzyme, raw_yield, raw_unit, moisture_pct, ph, temp_c, time_hrs, supplements, norm_yield, confidence, reference)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (organism.strip(), substrate.strip().title(), enzyme.strip().lower(), raw_yield, raw_unit, moisture_pct, ph, temp_c, time_hrs, supplements.strip(), norm, conf, reference.strip()))
                conn.commit()
                st.success(f"Record Saved! Normalized Yield: {norm} U/g dry (Confidence: {conf})")
                st.rerun()

# Option 3: Upload CSV Dataset
elif menu == "Upload CSV Dataset":
    st.header("Import Multiple Records from CSV File")
    st.info("Required CSV Columns: organism, substrate, enzyme, raw_yield, raw_unit, moisture_pct\n\nOptional Columns: ph, temp_c, time_hrs, supplements, reference")
    
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])
    if uploaded_file is not None:
        try:
            df_upload = pd.read_csv(uploaded_file).fillna("")
            st.write("### Preview of Uploaded Data:")
            st.dataframe(df_upload.head(), use_container_width=True)

            if st.button("Import Data into Database"):
                count = 0
                for _, row in df_upload.iterrows():
                    org = str(row.get("organism", "")).strip()
                    sub = str(row.get("substrate", "")).strip().title()
                    enz = str(row.get("enzyme", "")).strip().lower()
                    r_yield = float(row.get("raw_yield", 0))
                    r_unit = str(row.get("raw_unit", "U/g dry")).strip()
                    moist = float(row.get("moisture_pct", 50))
                    ph_val = float(row.get("ph") or 7.0)
                    temp_val = float(row.get("temp_c") or 30.0)
                    time_val = float(row.get("time_hrs") or 48.0)
                    supp = str(row.get("supplements") or "None").strip()
                    ref = str(row.get("reference") or "Unknown").strip()

                    norm, conf = normalize_yield(r_yield, r_unit, moist)

                    cursor.execute('''
                    INSERT INTO ssf_experiments (organism, substrate, enzyme, raw_yield, raw_unit, moisture_pct, ph, temp_c, time_hrs, supplements, norm_yield, confidence, reference)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (org, sub, enz, r_yield, r_unit, moist, ph_val, temp_val, time_val, supp, norm, conf, ref))
                    count += 1

                conn.commit()
                st.success(f"Successfully imported {count} records into the database!")
                st.rerun()
        except Exception as e:
            st.error(f"Error reading CSV file: {e}")

# Option 4: Search & Filter
elif menu == "Search & Filter":
    st.header("Search Database")
    sub = st.text_input("Substrate Filter")
    enz = st.text_input("Enzyme Filter")
    
    query = "SELECT organism, substrate, enzyme, norm_yield, confidence, ph, temp_c, time_hrs, supplements, reference FROM ssf_experiments WHERE substrate LIKE ? AND enzyme LIKE ? ORDER BY norm_yield DESC"
    df = pd.read_sql_query(query, conn, params=(f"%{sub}%", f"%{enz}%"))
    display_table_with_links(df)

# Option 5: Yield Visualizations
elif menu == "Yield Data Visualizations":
    st.header("Enzyme Yield Data Visualizations")
    df = pd.read_sql_query("SELECT organism, substrate, enzyme, norm_yield, ph, temp_c, time_hrs FROM ssf_experiments", conn)
    
    if not df.empty:
        chart_type = st.selectbox("Choose Visualization Type:", [
            "1. Heatmap Matrix (Organism vs Substrate)",
            "2. Grouped Bar Chart (Top Yields per Substrate)",
            "3. Box Plot (Yield Spread by Enzyme)",
            "4. Scatter Plot (pH vs Temperature vs Yield)"
        ])

        if "1. Heatmap" in chart_type:
            pivot = df.pivot_table(index="organism", columns="substrate", values="norm_yield", aggfunc="max").fillna(0)
            fig, ax = plt.subplots(figsize=(8, 4))
            cax = ax.imshow(pivot, cmap="YlOrRd", aspect="auto")
            fig.colorbar(cax, label="Yield (U/g dry)")
            ax.set_xticks(range(len(pivot.columns)))
            ax.set_xticklabels(pivot.columns, rotation=30, ha="right")
            ax.set_yticks(range(len(pivot.index)))
            ax.set_yticklabels(pivot.index)
            ax.set_title("Organism vs Substrate Yield Heatmap")
            st.pyplot(fig)

        elif "2. Grouped Bar" in chart_type:
            fig, ax = plt.subplots(figsize=(8, 4))
            avg_yield = df.groupby(["substrate", "enzyme"])["norm_yield"].max().unstack().fillna(0)
            avg_yield.plot(kind="bar", ax=ax)
            ax.set_ylabel("Yield (U/g dry)")
            ax.set_xlabel("Non-Cereal Substrate")
            ax.set_title("Maximum Yield by Substrate and Enzyme")
            plt.xticks(rotation=30, ha="right")
            st.pyplot(fig)

        elif "3. Box Plot" in chart_type:
            fig, ax = plt.subplots(figsize=(8, 4))
            df.boxplot(column="norm_yield", by="enzyme", ax=ax, grid=False)
            ax.set_ylabel("Yield (U/g dry)")
            ax.set_xlabel("Enzyme Category")
            plt.suptitle("")
            ax.set_title("Yield Variance per Enzyme Class")
            st.pyplot(fig)

        elif "4. Scatter Plot" in chart_type:
            fig, ax = plt.subplots(figsize=(8, 4))
            scatter = ax.scatter(df["ph"], df["temp_c"], s=df["norm_yield"]*0.8, c=df["norm_yield"], cmap="viridis", alpha=0.7)
            fig.colorbar(scatter, label="Yield (U/g dry)")
            ax.set_xlabel("pH")
            ax.set_ylabel("Temperature (°C)")
            ax.set_title("Optimal Parameter Clusters (Bubble Size = Yield)")
            st.pyplot(fig)

    else:
        st.warning("No data available yet!")

# Option 6: Best Conditions Summary
elif menu == "Best Conditions Summary":
    st.header("Optimal Fermentation Parameters")
    df = pd.read_sql_query("SELECT substrate, enzyme, organism, norm_yield, ph, temp_c, time_hrs, moisture_pct FROM ssf_experiments", conn)
    if not df.empty:
        rows = []
        for (s, e), group in df.groupby(["substrate", "enzyme"]):
            top = group.sort_values("norm_yield", ascending=False).head(3)
            best = top.iloc[0]
            rows.append({
                "Substrate": s, "Enzyme": e, "Best Yield (U/g)": best["norm_yield"],
                "Best Organism": best["organism"], "Avg pH": round(top["ph"].mean(), 1),
                "Avg Temp (°C)": round(top["temp_c"].mean(), 1), "Avg Hours": round(top["time_hrs"].mean(), 1)
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.warning("No data available yet!")
