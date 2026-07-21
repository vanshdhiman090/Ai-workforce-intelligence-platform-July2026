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
st.success("Connected to database successfully")

# -------------------------------------------------------
# KPI Metrics
# -------------------------------------------------------

with engine.connect() as conn:
    total_jobs = conn.execute(text("SELECT COUNT(*) FROM jobs")).scalar()
    total_companies = conn.execute(text("SELECT COUNT(*) FROM companies")).scalar()

col1, col2 = st.columns(2)

col1.metric("Total Jobs", total_jobs)
col2.metric("Total Companies", total_companies)

# -------------------------------------------------------
# Top Skills
# -------------------------------------------------------

st.subheader("Top 10 In-Demand Skills")


@st.cache_data
def get_top_skills():
    with engine.connect() as conn:
        return pd.read_sql(
            text("""
                SELECT skill_name,
                       COUNT(*) AS mentions
                FROM job_skills
                GROUP BY skill_name
                ORDER BY mentions DESC
                LIMIT 10
            """),
            conn,
        )


skills_df = get_top_skills()

st.bar_chart(skills_df.set_index("skill_name"))

st.caption(
    "Note: Based on regex-detected skill mentions in ~10% of postings. "
    "This is a lower-bound signal, not a complete market picture."
)

# -------------------------------------------------------
# Explore Jobs by City
# -------------------------------------------------------

st.subheader("Explore Jobs by City")


@st.cache_data
def get_cities():
    with engine.connect() as conn:
        df = pd.read_sql(
            text("""
                SELECT DISTINCT location
                FROM jobs
                WHERE location IS NOT NULL
                  AND location != 'Deutschland'
                ORDER BY location
            """),
            conn,
        )

    return df["location"].tolist()


cities = get_cities()

selected_city = st.selectbox(
    "Select a city",
    cities
)


@st.cache_data
def get_jobs_by_city(city):
    with engine.connect() as conn:
        return pd.read_sql(
            text("""
                SELECT
                    j.title,
                    c.company_name,
                    j.category
                FROM jobs j
                JOIN companies c
                  ON j.company_id = c.company_id
                WHERE j.location = :city
            """),
            conn,
            params={"city": city},
        )


city_jobs_df = get_jobs_by_city(selected_city)

st.write(f"Showing {len(city_jobs_df)} jobs in {selected_city}")

st.dataframe(city_jobs_df)

# -------------------------------------------------------
# Company Skill Gap Analysis
# -------------------------------------------------------

st.subheader("Company Skill Gap Analysis")


@st.cache_data
def get_companies_with_skills():
    with engine.connect() as conn:
        return pd.read_sql(
            text("""
                SELECT DISTINCT c.company_name
                FROM companies c
                JOIN jobs j
                    ON c.company_id = j.company_id
                JOIN job_skills js
                    ON j.job_id = js.job_id
                ORDER BY c.company_name
            """),
            conn,
        )


@st.cache_data
def get_company_skills(company_name):
    with engine.connect() as conn:
        df = pd.read_sql(
            text("""
                SELECT DISTINCT js.skill_name
                FROM companies c
                JOIN jobs j
                    ON c.company_id = j.company_id
                JOIN job_skills js
                    ON j.job_id = js.job_id
                WHERE c.company_name = :company
                ORDER BY js.skill_name
            """),
            conn,
            params={"company": company_name},
        )

    return df


@st.cache_data
def get_market_skills():
    with engine.connect() as conn:
        df = pd.read_sql(
            text("""
                SELECT DISTINCT skill_name
                FROM job_skills
                ORDER BY skill_name
            """),
            conn,
        )

    return df


companies_df = get_companies_with_skills()

selected_company = st.selectbox(
    "Select a company",
    companies_df["company_name"]
)

company_skills_df = get_company_skills(selected_company)
market_skills_df = get_market_skills()

company_skills = set(company_skills_df["skill_name"])
market_skills = set(market_skills_df["skill_name"])

missing_skills = sorted(list(market_skills - company_skills))

if len(company_skills) == 0:

    st.warning(
        "No detected skills were found for this company."
    )

else:

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Company Skills")
        st.write(sorted(company_skills))

    with col2:
        st.markdown("### Market Skills Missing")

        if missing_skills:
            st.write(missing_skills)
        else:
            st.success("No missing skills detected.")

# -------------------------------------------------------
# Data Quality Notes
# -------------------------------------------------------

st.subheader("Data Quality Notes")

st.caption(
    "54% of postings (422/787) have no category assigned by the data source "
    "(Adzuna) — shown as 'Unknown' rather than excluded."
)

st.caption(
    "Only ~5.6% of postings include salary data."
)

st.caption(
    "Skill Gap Analysis is available only for companies with detected skills "
    "using the current regex-based extraction pipeline."
)