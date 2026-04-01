import streamlit as st
import sales
import production
from pathlib import Path

st.set_page_config(
    page_title="Incentive Management System",
    layout="wide"
)

# Correct logo path
BASE_DIR = Path(__file__).parent
logo_path = BASE_DIR / "Logo.png"

# Layout for title + logo
col1, col2 = st.columns([5,3])

with col1:
    st.title("Incentive Management System")

with col2:
    if logo_path.exists():
        st.image(str(logo_path), width=260)

menu = st.sidebar.radio(
    "Navigation",
    [
        "Sales Incentives",
        "Production Incentives"
    ]
)

if menu == "Sales Incentives":
    sales.run()

elif menu == "Production Incentives":
    production.run()