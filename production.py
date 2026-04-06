import pandas as pd
import streamlit as st
import io
from database import (
    create_tables,
    save_employees,
    load_employees,
    save_monthly_records,
    load_monthly_report,
    update_incentive_rate
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

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Save Employees"):
                    save_employees(df, month)
                    st.success("Employees saved")

            with col2:
                if st.button("Edit Employee Incentive Details"):

                    existing = load_employees(month)

                    if existing.empty:
                        st.warning("No employees uploaded yet")

                    else:

                        st.subheader("Edit Incentive Rates")

                        for index, row in existing.iterrows():

                            new_rate = st.number_input(
                                f"{row['first_name']} {row['last_name']} ({row['employee_id']})",
                                value=float(row["incentive_rate"]),
                                key=f"edit_rate_{index}"
                            )

                            if st.button(f"Update {row['employee_id']}", key=f"update_{index}"):

                                update_incentive_rate(
                                    row["employee_id"],
                                    month,
                                    new_rate
                                )

                                st.success("Updated successfully")

# --------------------------------------------------
# TAB 2 : ATTENDANCE
# --------------------------------------------------

    with tab2:

        month = st.selectbox("Select Month", months, key="attendance_month")

        st.subheader("Upload Attendance Record (Optional)")

        attendance_file = st.file_uploader(
            "Upload Attendance Excel",
            type=["xlsx"]
        )

        if attendance_file:

            att_df = pd.read_excel(attendance_file)

            att_df.columns = att_df.columns.str.strip().str.lower()

            st.dataframe(att_df)

            if st.button("Update Attendance"):

                import sqlite3

                conn = sqlite3.connect("incentive.db")
                cursor = conn.cursor()

                for _, row in att_df.iterrows():

                    cursor.execute(
                        """
                        UPDATE employees
                        SET days_of_month_present=?,
                            absent_days=?
                        WHERE employee_id=? AND month=?
                        """,
                        (
                            row["days_of_month_present"],
                            row["absent_days"],
                            row["employee id"],
                            month
                        )
                    )

                conn.commit()
                conn.close()

                st.success("Attendance updated")

        st.subheader("Current Attendance")

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

            days_of_month = st.number_input(
                "Days of Month",
                min_value=1,
                value=30
            )

            if st.button("Calculate Incentives"):

                df["total_amount"] = (
                    df["incentive @ (rs.)"] * df["product_qty"]
                )

                df["per_day"] = df["total_amount"] / days_of_month

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

                st.dataframe(report_df)

                # Rename Columns
                report_df = report_df.rename(columns={
                    "employee_id":"Employee ID",
                    "first_name":"First Name",
                    "last_name":"Last Name",
                    "department":"Department",
                    "days_of_month_present":"Days Present",
                    "absent_days":"Absent Days",
                    "product_qty":"Product Quantity",
                    "total_amount":"Total Amount",
                    "absentees_deduction":"Absent Deduction",
                    "attendance_distribution":"Attendance Bonus",
                    "final_incentive":"Final Incentive"
                })

                output = io.BytesIO()

                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:

                    report_df.to_excel(writer,index=False,sheet_name="Report")

                    workbook = writer.book
                    worksheet = writer.sheets["Report"]

                    header_format = workbook.add_format({
                        'bold': True,
                        'bg_color': '#FFFF00'
                    })

                    for col_num, value in enumerate(report_df.columns.values):
                        worksheet.write(0, col_num, value, header_format)

                st.download_button(
                    label="Download Excel Report",
                    data=output.getvalue(),
                    file_name=f"{month}_incentive_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )