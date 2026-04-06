import pandas as pd
import streamlit as st
from io import BytesIO

def run():

    st.title("Sales Incentive Management")

    tab1, tab2 = st.tabs(["Employee Details", "Turnover Entry"])

    # -----------------------------
    # TAB 1 — EMPLOYEE DETAILS
    # -----------------------------

    with tab1:

        st.subheader("Employee Slab Configuration")

        num_employees = st.number_input("Number of Employees", min_value=1, step=1)

        data = []

        for i in range(int(num_employees)):

            st.markdown(f"## Employee {i+1}")

            col1, col2 = st.columns(2)

            with col1:
                emp_id = st.text_input("Employee ID", key=f"id_{i}")
                name = st.text_input("Name", key=f"name_{i}")

            with col2:
                department = st.text_input("Department", key=f"dept_{i}")
                num_slabs = st.number_input("Number of Slabs", min_value=1, step=1, key=f"slabs_{i}")

            for j in range(int(num_slabs)):

                st.markdown(f"### Slab {j+1}")

                slab_type = st.selectbox(
                    "Slab Type",
                    ["range", "above", "full"],
                    key=f"type_{i}_{j}"
                )

                incentive_rate = st.number_input(
                    "Incentive Rate (%)",
                    min_value=0.0,
                    step=0.01,
                    key=f"rate_{i}_{j}"
                )

                slab_min = st.number_input(
                    "Slab Min (Cr)",
                    min_value=0.0,
                    step=0.01,
                    key=f"min_{i}_{j}"
                )

                slab_max = None

                if slab_type == "range":
                    slab_max = st.number_input(
                        "Slab Max (Cr)",
                        min_value=0.0,
                        step=0.01,
                        key=f"max_{i}_{j}"
                    )

                data.append({
                    "employee_id": emp_id,
                    "name": name,
                    "department": department,
                    "incentive_rate": incentive_rate,
                    "slab_type": slab_type,
                    "slab_min": slab_min,
                    "slab_max": slab_max
                })

        if st.button("Save Employee Details"):

            df = pd.DataFrame(data)

            st.session_state["sales_employee_data"] = df

            st.success("Employee configuration saved successfully")

            st.dataframe(df)

    # -----------------------------
    # TAB 2 — TURNOVER ENTRY
    # -----------------------------

    with tab2:

        st.subheader("Monthly Turnover Entry")

        month = st.selectbox(
            "Select Month",
            [
                "January","February","March","April","May","June",
                "July","August","September","October","November","December"
            ]
        )

        turnover = st.number_input("Enter Turnover (Rs)", min_value=0.0)

        if "sales_employee_data" not in st.session_state:

            st.warning("Please configure Employee Details first")

            return

        df = st.session_state["sales_employee_data"].copy()

        # -----------------------------
        # Incentive calculation logic
        # -----------------------------

        def calculate_incentive_value(row, turnover):

            slab_min_rs = row["slab_min"] * 10000000

            if row["slab_type"] == "range":

                slab_max_rs = row["slab_max"] * 10000000

                if turnover <= slab_min_rs:
                    return 0

                upper = min(turnover, slab_max_rs)

                return max(0, upper - slab_min_rs)

            elif row["slab_type"] == "above":

                if turnover <= slab_min_rs:
                    return 0

                return turnover - slab_min_rs

            elif row["slab_type"] == "full":

                return turnover

            return 0

        if st.button("Calculate Incentives"):

            df["incentive_value"] = df.apply(
                lambda row: calculate_incentive_value(row, turnover),
                axis=1
            )

            df["final_incentive"] = df["incentive_value"] * df["incentive_rate"] / 100

            df["incentive_value"] = df["incentive_value"].round(0)
            df["final_incentive"] = df["final_incentive"].round(0)

            st.subheader(f"Slab-wise Results — {month}")
            st.dataframe(df)

            st.subheader("Employee-wise Total")

            summary = df.groupby(
                ["employee_id", "name", "department"]
            )["final_incentive"].sum().reset_index()

            st.dataframe(summary)

            total = df["final_incentive"].sum()

            st.success(f"Total Incentive Payout (Rs): {round(total,0)}")

            # -----------------------------
            # Excel Report Generator
            # -----------------------------

            def generate_excel():

                output = BytesIO()

                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:

                    workbook = writer.book

                    header_format = workbook.add_format({
                        "bold": True,
                        "bg_color": "#FFFF00",
                        "border": 1
                    })

                    title_format = workbook.add_format({
                        "bold": True,
                        "font_size": 16
                    })

                    sheet_name = "Sales Incentive Report"

                    df.to_excel(writer, sheet_name=sheet_name, startrow=3, index=False)

                    sheet = writer.sheets[sheet_name]

                    sheet.write(0,0,"Sales Incentive Report", title_format)
                    sheet.write(1,0,f"Month: {month}")

                    for col_num, value in enumerate(df.columns.values):
                        sheet.write(3, col_num, value.replace("_"," ").title(), header_format)

                    # Employee summary table below

                    start_row = len(df) + 7

                    sheet.write(start_row-1,0,"Employee Wise Total Incentive", title_format)

                    summary.to_excel(writer, sheet_name=sheet_name, startrow=start_row, index=False)

                    for col_num, value in enumerate(summary.columns.values):
                        sheet.write(start_row, col_num, value.replace("_"," ").title(), header_format)

                output.seek(0)

                return output

            excel_file = generate_excel()

            st.download_button(
                label="Download Incentive Report (Excel)",
                data=excel_file,
                file_name=f"sales_incentive_report_{month}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )