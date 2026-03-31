import streamlit as st
import sales
import production

st.set_page_config(
    page_title="Incentive Management System",
    layout="wide"
)

st.title("Incentive Management System")

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