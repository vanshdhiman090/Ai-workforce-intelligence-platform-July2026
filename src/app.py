import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, URL, text
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

connection_url = URL.create(
    "postgresql",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME,
)
engine = create_engine(connection_url)

st.title("AI Workforce Intelligence Platform")
st.write("Connected to database successfully ✅")

# ---- KPI Metrics ----
with engine.connect() as conn:
    total_jobs = conn.execute(text("SELECT COUNT(*) FROM jobs")).scalar()
    total_companies = conn.execute(text("SELECT COUNT(*) FROM companies")).scalar()

col1, col2 = st.columns(2)
col1.metric("Total Jobs", total_jobs)
col2.metric("Total Companies", total_companies)

# ---- Top Skills Chart ----
st.subheader("Top 10 In-Demand Skills")

@st.cache_data
def get_top_skills():
    with engine.connect() as conn:
        return pd.read_sql(
            text("""
                SELECT skill_name, COUNT(*) AS mentions
                FROM job_skills
                GROUP BY skill_name
                ORDER BY mentions DESC
                LIMIT 10
            """),
            conn
        )

skills_df = get_top_skills()
st.bar_chart(skills_df.set_index("skill_name"))

st.caption("Note: Based on regex-detected skill mentions in ~10% of postings. This is a lower-bound signal, not a complete market picture.")

# ---- City Filter ----
st.subheader("Explore Jobs by City")

@st.cache_data
def get_cities():
    with engine.connect() as conn:
        df = pd.read_sql(
            text("""
                SELECT DISTINCT location
                FROM jobs
                WHERE location IS NOT NULL AND location != 'Deutschland'
                ORDER BY location
            """),
            conn
        )
    return df["location"].tolist()

cities = get_cities()
selected_city = st.selectbox("Select a city", cities)

@st.cache_data
def get_jobs_by_city(city):
    with engine.connect() as conn:
        return pd.read_sql(
            text("""
                SELECT j.title, c.company_name, j.category
                FROM jobs j
                JOIN companies c ON j.company_id = c.company_id
                WHERE j.location = :city
            """),
            conn,
            params={"city": city}
        )

city_jobs_df = get_jobs_by_city(selected_city)
st.write(f"Showing {len(city_jobs_df)} jobs in {selected_city}")
st.dataframe(city_jobs_df)

# ---- Data Quality Disclaimer ----
st.subheader("Data Quality Notes")
st.caption("54% of postings (422/787) have no category assigned by the data source (Adzuna) — shown as 'Unknown' rather than excluded.")
st.caption("Only ~5.6% of postings include salary data.")