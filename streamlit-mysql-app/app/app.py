import os
import time
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError


st.set_page_config(page_title="Sales Dashboard", layout="wide")

DB_HOST = os.getenv("DB_HOST", "mysql")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "appdb")
DB_USER = os.getenv("DB_USER", "appuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "apppassword")

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


@st.cache_resource(show_spinner=False)
def get_engine():
    return create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        future=True,
    )


def wait_for_db(retries: int = 20, delay: int = 3):
    engine = get_engine()
    last_error = None
    for _ in range(retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return engine
        except OperationalError as exc:
            last_error = exc
            time.sleep(delay)
    raise last_error


def initialize_database():
    engine = wait_for_db()
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS sales (
        id INT AUTO_INCREMENT PRIMARY KEY,
        item_name VARCHAR(100) NOT NULL,
        category VARCHAR(50) NOT NULL,
        quantity INT NOT NULL,
        unit_price DECIMAL(10,2) NOT NULL,
        sold_on DATE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
    """

    with engine.begin() as conn:
        conn.execute(text(create_table_sql))
        count = conn.execute(text("SELECT COUNT(*) FROM sales")).scalar_one()
        if count == 0:
            seed_rows = [
                ("Keyboard", "Accessories", 12, 49.99, "2026-03-01"),
                ("Mouse", "Accessories", 20, 24.99, "2026-03-02"),
                ("Monitor", "Displays", 5, 229.00, "2026-03-03"),
                ("Laptop", "Computers", 3, 1099.00, "2026-03-04"),
                ("Dock", "Accessories", 8, 119.50, "2026-03-05"),
                ("Webcam", "Peripherals", 10, 79.99, "2026-03-06"),
            ]
            conn.execute(
                text(
                    """
                    INSERT INTO sales (item_name, category, quantity, unit_price, sold_on)
                    VALUES (:item_name, :category, :quantity, :unit_price, :sold_on)
                    """
                ),
                [
                    {
                        "item_name": r[0],
                        "category": r[1],
                        "quantity": r[2],
                        "unit_price": r[3],
                        "sold_on": r[4],
                    }
                    for r in seed_rows
                ],
            )
    return engine


engine = initialize_database()


def load_data() -> pd.DataFrame:
    query = "SELECT id, item_name, category, quantity, unit_price, sold_on FROM sales ORDER BY sold_on DESC, id DESC"
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)
    if not df.empty:
        df["sold_on"] = pd.to_datetime(df["sold_on"]).dt.date
        df["revenue"] = df["quantity"] * df["unit_price"]
    return df


def insert_row(item_name: str, category: str, quantity: int, unit_price: float, sold_on: date):
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO sales (item_name, category, quantity, unit_price, sold_on)
                VALUES (:item_name, :category, :quantity, :unit_price, :sold_on)
                """
            ),
            {
                "item_name": item_name,
                "category": category,
                "quantity": quantity,
                "unit_price": unit_price,
                "sold_on": sold_on,
            },
        )


def update_row(record_id: int, item_name: str, category: str, quantity: int, unit_price: float, sold_on: date):
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE sales
                SET item_name=:item_name, category=:category, quantity=:quantity,
                    unit_price=:unit_price, sold_on=:sold_on
                WHERE id=:id
                """
            ),
            {
                "id": record_id,
                "item_name": item_name,
                "category": category,
                "quantity": quantity,
                "unit_price": unit_price,
                "sold_on": sold_on,
            },
        )


def delete_row(record_id: int):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM sales WHERE id=:id"), {"id": record_id})


st.title("Streamlit + MySQL Sales Dashboard")
st.caption("Simple CRUD app with charts, ready for containerization and Helm deployment.")

with st.sidebar:
    st.subheader("Database")
    st.write(f"Host: `{DB_HOST}`")
    st.write(f"DB: `{DB_NAME}`")
    if st.button("Refresh data"):
        st.cache_data.clear()
        st.rerun()


df = load_data()

col1, col2, col3 = st.columns(3)
col1.metric("Rows", len(df))
col2.metric("Total Quantity", int(df["quantity"].sum()) if not df.empty else 0)
col3.metric("Total Revenue", f"${df['revenue'].sum():,.2f}" if not df.empty else "$0.00")

st.divider()

with st.expander("Add record", expanded=True):
    with st.form("add_form", clear_on_submit=True):
        c1, c2, c3, c4, c5 = st.columns(5)
        item_name = c1.text_input("Item name")
        category = c2.text_input("Category")
        quantity = c3.number_input("Quantity", min_value=1, step=1, value=1)
        unit_price = c4.number_input("Unit price", min_value=0.0, step=1.0, value=10.0)
        sold_on = c5.date_input("Sold on", value=date.today())
        submitted = st.form_submit_button("Add")
        if submitted:
            if item_name and category:
                insert_row(item_name, category, int(quantity), float(unit_price), sold_on)
                st.success("Record added")
                st.rerun()
            else:
                st.error("Item name and category are required")

st.subheader("Edit or delete records")
if df.empty:
    st.info("No rows found.")
else:
    selected_id = st.selectbox("Select row ID", df["id"].tolist())
    row = df[df["id"] == selected_id].iloc[0]
    with st.form("edit_form"):
        c1, c2, c3, c4, c5 = st.columns(5)
        edit_item_name = c1.text_input("Item name", value=row["item_name"])
        edit_category = c2.text_input("Category", value=row["category"])
        edit_quantity = c3.number_input("Quantity", min_value=1, step=1, value=int(row["quantity"]))
        edit_unit_price = c4.number_input("Unit price", min_value=0.0, step=1.0, value=float(row["unit_price"]))
        edit_sold_on = c5.date_input("Sold on", value=row["sold_on"])

        update_clicked = st.form_submit_button("Save changes")
        delete_clicked = st.form_submit_button("Delete record")

        if update_clicked:
            update_row(selected_id, edit_item_name, edit_category, int(edit_quantity), float(edit_unit_price), edit_sold_on)
            st.success("Record updated")
            st.rerun()

        if delete_clicked:
            delete_row(selected_id)
            st.warning("Record deleted")
            st.rerun()

st.divider()
left, right = st.columns(2)

with left:
    st.subheader("Sales by category")
    if not df.empty:
        category_df = df.groupby("category", as_index=False)["revenue"].sum().sort_values("revenue", ascending=False)
        fig = px.bar(category_df, x="category", y="revenue", title="Revenue by category")
        st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Daily revenue")
    if not df.empty:
        daily_df = df.groupby("sold_on", as_index=False)["revenue"].sum().sort_values("sold_on")
        fig = px.line(daily_df, x="sold_on", y="revenue", markers=True, title="Revenue over time")
        st.plotly_chart(fig, use_container_width=True)

st.subheader("Data")
st.dataframe(df, use_container_width=True)
