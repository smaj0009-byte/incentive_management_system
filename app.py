import streamlit as st
import sales
import production

st.set_page_config(
    page_title="Incentive Management System",
    layout="wide"
)

# Header layout
col1, col2 = st.columns([6,2])

with col1:
    st.title("Incentive Management System")

with col2:
    st.image("logo.png", use_container_width=True)

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