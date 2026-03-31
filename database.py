import sqlite3
import pandas as pd

DB_NAME = "incentive.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def create_tables():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        month TEXT,
        employee_id TEXT,
        first_name TEXT,
        last_name TEXT,
        department TEXT,
        incentive_rate REAL,
        days_of_month_present REAL,
        absent_days REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS production_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        month TEXT,
        employee_id TEXT,
        first_name TEXT,
        last_name TEXT,
        department TEXT,
        days_of_month_present REAL,
        absent_days REAL,
        product_qty REAL,
        total_amount REAL,
        absentees_deduction REAL,
        attendance_distribution REAL,
        final_incentive REAL
    )
    """)

    conn.commit()
    conn.close()


def save_employees(df, month):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM employees WHERE month=?", (month,))

    for _, row in df.iterrows():

        cursor.execute(
            """
            INSERT INTO employees
            (month, employee_id, first_name, last_name,
             department, incentive_rate,
             days_of_month_present, absent_days)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                month,
                row["employee id"],
                row["employee first name"],
                row["employee last name"],
                row["department"],
                row["incentive @ (rs.)"],
                row["days_of_month_present"],
                row["absent_days"]
            )
        )

    conn.commit()
    conn.close()


def load_employees(month):

    conn = get_connection()

    df = pd.read_sql(
        "SELECT * FROM employees WHERE month=?",
        conn,
        params=(month,)
    )

    conn.close()

    return df


def save_monthly_records(df, month):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM production_records WHERE month=?", (month,))

    for _, row in df.iterrows():

        cursor.execute(
            """
            INSERT INTO production_records
            (month, employee_id, first_name, last_name,
             department, days_of_month_present, absent_days,
             product_qty, total_amount,
             absentees_deduction, attendance_distribution,
             final_incentive)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                month,
                row["employee id"],
                row["employee first name"],
                row["employee last name"],
                row["department"],
                row["days_of_month_present"],
                row["absent_days"],
                row["product_qty"],
                row["total_amount"],
                row["absentees_deduction"],
                row["attendance_distribution"],
                row["final_incentive"]
            )
        )

    conn.commit()
    conn.close()


def load_monthly_report(month):

    conn = get_connection()

    df = pd.read_sql(
        "SELECT * FROM production_records WHERE month=?",
        conn,
        params=(month,)
    )

    conn.close()

    return df