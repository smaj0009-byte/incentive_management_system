import pandas as pd
import streamlit as st

def run():

    st.title("Sales Incentive Calculator")

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

            incentive_rate = st.number_input("Incentive Rate (%)", key=f"rate_{i}_{j}")

            slab_min = st.number_input("Slab Min (Cr)", key=f"min_{i}_{j}")

            slab_max = None
            if slab_type == "range":
                slab_max = st.number_input("Slab Max (Cr)", key=f"max_{i}_{j}")

            data.append({
                "employee_id": emp_id,
                "name": name,
                "department": department,
                "incentive_rate": incentive_rate,
                "slab_type": slab_type,
                "slab_min": slab_min,
                "slab_max": slab_max
            })

    turnover = st.number_input("Enter Turnover (Cr)", min_value=0.0)

    def calculate_incentive_value(row, turnover):
        slab_min = row["slab_min"] if pd.notna(row["slab_min"]) else 0

        if row["slab_type"] == "range":
            return max(0, row["slab_max"] - slab_min)

        elif row["slab_type"] == "above":
            return max(0, turnover - slab_min)

        elif row["slab_type"] == "full":
            return turnover

        return 0

    if st.button("Calculate Incentives"):

        df = pd.DataFrame(data)

        df["incentive_value_cr"] = df.apply(
            lambda row: calculate_incentive_value(row, turnover), axis=1
        )

        df["rate_decimal"] = df["incentive_rate"] / 100

        df["final_incentive"] = df["incentive_value_cr"] * 10000000 * df["rate_decimal"]

        df["incentive_value_cr"] = df["incentive_value_cr"].round(2)
        df["final_incentive"] = df["final_incentive"].round(0)

        st.subheader("Slab-wise Results")
        st.dataframe(df)

        st.subheader("Employee-wise Total")

        summary = df.groupby(
            ["employee_id", "name", "department"]
        )["final_incentive"].sum().reset_index()

        st.dataframe(summary)

        total = df["final_incentive"].sum()

        st.success(f"Total Incentive Payout (Rs): {round(total, 0)}")