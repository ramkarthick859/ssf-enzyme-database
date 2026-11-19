import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# 1. Page Configuration
st.set_page_config(
    page_title="THE BIOCATALYST ARCHIVE | SSF & SmF Specimen Index",
    page_icon="🏛️",
    layout="wide",
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "ssf_database.db")

# 2. Natural History / Specimen Archive Editorial Styling
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

        .stApp {
            background-color: #f6f3ec;
            color: #1c2226;
            font-family: 'Plus Jakarta Sans', sans-serif;
        }

        /* Top Archival Masthead */
        .masthead {
            background: linear-gradient(135deg, #162127 0%, #24343d 60%, #2d4c48 100%);
            border: 1px solid #3c5452;
            border-radius: 16px;
            padding: 1.6rem 2rem;
            color: #f6f3ec;
            margin-bottom: 1rem;
            box-shadow: 0 12px 28px rgba(22, 33, 39, 0.16);
        }
        .masthead-eyebrow {
            font-size: 0.75rem;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            color: #9ec5b8;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }
        .masthead h1 {
            font-family: 'Cormorant Garamond', serif;
            font-size: 2.35rem;
            font-weight: 700;
            line-height: 1.1;
            margin: 0;
            color: #fffdf9;
        }
        .masthead p {
            margin: 0.5rem 0 0 0;
            color: #d6dfd9;
            font-size: 0.96rem;
            max-width: 820px;
        }

        /* Specimen Plate / Field Note Card */
        .specimen-plate {
            background: #fffdf9;
            border: 1px solid #dfd8c8;
            border-left: 5px solid #2d6a5b;
            border-radius: 12px;
            padding: 1.15rem 1.4rem;
            margin: 0.85rem 0 1.15rem 0;
            box-shadow: 0 4px 14px rgba(28, 34, 38, 0.05);
        }
        .specimen-code {
            font-size: 0.74rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #2d6a5b;
            font-weight: 700;
        }
        .specimen-title {
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.55rem;
            font-weight: 700;
            color: #162127;
            margin: 0.15rem 0 0.4rem 0;
        }
        .tag-pill {
            display: inline-block;
            background: #eef4f1;
            color: #214e43;
            border: 1px solid #c6ddd4;
            border-radius: 999px;
            padding: 0.18rem 0.65rem;
            font-size: 0.78rem;
            font-weight: 600;
            margin-right: 0.35rem;
            margin-top: 0.25rem;
        }

        /* Metric tiles styled like museum index plaques */
        div[data-testid="stMetric"] {
            background-color: #fffdf9;
            border: 1px solid #dfd8c8;
            border-radius: 12px;
            padding: 0.85rem 1rem;
            box-shadow: 0 2px 8px rgba(28, 34, 38, 0.04);
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
    ("Aspergillus awamori", "Grape Pomace
