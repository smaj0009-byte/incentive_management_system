import pandas as pd
import streamlit as st
from database import (
    create_tables,
    save_employees,
    load_employees,
    save_monthly_records,
    load_monthly_report
)

def run():

    create_tables()

    st.title("Production Incentive Calculator")

    months = [
        "January","February","March","April","May","June",
        "July","August","September","October","November","December"
    ]

    tab1, tab2, tab3, tab4 = st.tabs([
        "Employee Upload",
        "Attendance",
        "Production Entry",
        "Reports"
    ])

# --------------------------------------------------
# TAB 1 : EMPLOYEE UPLOAD
# --------------------------------------------------

    with tab1:

        month = st.selectbox("Select Month", months, key="upload_month")

        uploaded_file = st.file_uploader(
            "Upload Master Excel",
            type=["xlsx"]
        )

        if uploaded_file:

            df = pd.read_excel(
                uploaded_file,
                sheet_name="Sample Employee for upload",
                header=2
            )

            df.columns = df.columns.str.strip().str.lower()

            df["employee id"] = df["employee id"].astype(str)

            df = df.rename(columns={
                "days of month present": "days_of_month_present",
                "absent days": "absent_days"
            })

            st.dataframe(df)

            if st.button("Save Employees"):

                save_employees(df, month)

                st.success("Employees saved")

# --------------------------------------------------
# TAB 2 : ATTENDANCE
# --------------------------------------------------

    with tab2:

        month = st.selectbox("Select Month", months, key="attendance_month")

        df = load_employees(month)

        if df.empty:

            st.warning("No employees found")

        else:

            st.dataframe(
                df[
                    [
                        "employee_id",
                        "first_name",
                        "last_name",
                        "days_of_month_present",
                        "absent_days"
                    ]
                ]
            )

# --------------------------------------------------
# TAB 3 : PRODUCTION ENTRY
# --------------------------------------------------

    with tab3:

        month = st.selectbox("Select Month", months, key="production_month")

        df = load_employees(month)

        if df.empty:

            st.warning("Upload employees first")

        else:

            df.rename(columns={
                "employee_id": "employee id",
                "first_name": "employee first name",
                "last_name": "employee last name",
                "incentive_rate": "incentive @ (rs.)"
            }, inplace=True)

            departments = df["department"].unique()

            st.subheader("Department Production Quantity")

            dept_qty = {}

            for dept in departments:

                dept_qty[dept] = st.number_input(
                    f"{dept} Production",
                    min_value=0.0
                )

            df["product_qty"] = df["department"].map(dept_qty)

            if st.button("Calculate Incentives"):

                df["total_amount"] = (
                    df["incentive @ (rs.)"] * df["product_qty"]
                )

                df["per_day"] = (
                    df["total_amount"] / df["days_of_month_present"]
                )

                df["absentees_deduction"] = (
                    df["per_day"] * df["absent_days"]
                )

                df["attendance_distribution"] = 0

                for dept in df["department"].unique():

                    dept_df = df[df["department"] == dept]

                    deduction_pool = dept_df["absentees_deduction"].sum()

                    eligible = dept_df[
                        dept_df["absent_days"] == 0
                    ]

                    if len(eligible) > 0:

                        share = deduction_pool / len(eligible)

                        df.loc[
                            (df["department"] == dept)
                            & (df["absent_days"] == 0),
                            "attendance_distribution"
                        ] = share

                df["final_incentive"] = (
                    df["total_amount"]
                    - df["absentees_deduction"]
                    + df["attendance_distribution"]
                )

                st.session_state["calculated_df"] = df

            if "calculated_df" in st.session_state:

                st.dataframe(st.session_state["calculated_df"])

                if st.button("Save Month Data"):

                    save_monthly_records(
                        st.session_state["calculated_df"],
                        month
                    )

                    st.success("Saved successfully")

# --------------------------------------------------
# TAB 4 : REPORTS
# --------------------------------------------------

    with tab4:

        month = st.selectbox("Select Month", months, key="report_month")

        if st.button("Load Report"):

            report_df = load_monthly_report(month)

            if report_df.empty:

                st.warning("No report found")

            else:

                # rename for HR readability
                report_df.rename(columns={
                    "employee_id": "Employee ID",
                    "first_name": "First Name",
                    "last_name": "Last Name",
                    "department": "Department",
                    "days_of_month_present": "Days Present",
                    "absent_days": "Absent Days",
                    "product_qty": "Production Quantity",
                    "total_amount": "Total Amount",
                    "absentees_deduction": "Absentee Deduction",
                    "attendance_distribution": "Attendance Distribution",
                    "final_incentive": "Final Incentive for Department"
                }, inplace=True)

                # calculate final incentive to be disbursed
                report_df["Final Incentive to be Disbursed"] = (
                    report_df.groupby("Employee ID")[
                        "Final Incentive for Department"
                    ].transform("sum")
                )

                st.dataframe(report_df)

                file_name = "report.xlsx"

                with pd.ExcelWriter(file_name, engine="xlsxwriter") as writer:

                    report_df.to_excel(writer, index=False, sheet_name="Report")

                    workbook = writer.book
                    worksheet = writer.sheets["Report"]

                    header_format = workbook.add_format({
                        "bold": True,
                        "bg_color": "yellow"
                    })

                    for col_num, value in enumerate(report_df.columns.values):
                        worksheet.write(0, col_num, value, header_format)

                with open(file_name, "rb") as f:

                    st.download_button(
                        "Download Excel Report",
                        f,
                        f"{month}_Incentive_Report.xlsx"
                    )