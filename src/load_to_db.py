import os
import ast
import pandas as pd
from sqlalchemy import create_engine, text, URL
from dotenv import load_dotenv
import streamlit as st

load_dotenv()


def get_secret(key):
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key)


DB_USER = get_secret("DB_USER")
DB_PASSWORD = get_secret("DB_PASSWORD")
DB_HOST = get_secret("DB_HOST")
DB_PORT = get_secret("DB_PORT")
DB_NAME = get_secret("DB_NAME")

connection_url = URL.create(
    "postgresql",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME,
    query={"sslmode": "require"},
)
engine = create_engine(connection_url)


def load_companies(engine, df):
    unique_companies = df["company"].dropna().unique()
    company_map = {}
    with engine.begin() as conn:
        for name in unique_companies:
            result = conn.execute(
                text("SELECT company_id FROM companies WHERE company_name = :name"),
                {"name": name}
            ).fetchone()
            if result:
                company_id = result[0]
            else:
                result = conn.execute(
                    text("INSERT INTO companies (company_name) VALUES (:name) RETURNING company_id"),
                    {"name": name}
                ).fetchone()
                company_id = result[0]
            company_map[name] = company_id
    return company_map


def load_jobs(engine, df, company_map):
    job_id_map = {}
    with engine.begin() as conn:
        for idx, row in df.iterrows():
            company_id = company_map.get(row["company"])
            existing = conn.execute(
                text("SELECT job_id FROM jobs WHERE title = :title AND company_id = :company_id"),
                {"title": row["title"], "company_id": company_id}
            ).fetchone()
            if existing:
                job_id_map[idx] = existing[0]
                continue
            result = conn.execute(
                text("""
                    INSERT INTO jobs (title, company_id, location, salary_min, salary_max,
                                       has_salary_data, salary_is_predicted, created_date, category)
                    VALUES (:title, :company_id, :location, :salary_min, :salary_max,
                            :has_salary_data, :salary_is_predicted, :created_date, :category)
                    RETURNING job_id
                """),
                {
                    "title": row["title"],
                    "company_id": company_id,
                    "location": row.get("location"),
                    "salary_min": row.get("salary_min"),
                    "salary_max": row.get("salary_max"),
                    "has_salary_data": bool(row.get("has_salary_data")),
                    "salary_is_predicted": bool(row.get("salary_is_predicted")),
                    "created_date": row.get("created"),
                    "category": row.get("category"),
                }
            ).fetchone()
            job_id_map[idx] = result[0]
    return job_id_map


def load_job_skills(engine, df, job_id_map):
    rows_inserted = 0
    with engine.begin() as conn:
        for idx, row in df.iterrows():
            job_id = job_id_map[idx]
            skills = row["extracted_skills"]
            for skill in skills:
                conn.execute(
                    text("""
                        INSERT INTO job_skills (job_id, skill_name)
                        VALUES (:job_id, :skill_name)
                        ON CONFLICT DO NOTHING
                    """),
                    {"job_id": job_id, "skill_name": skill}
                )
                rows_inserted += 1
    return rows_inserted


def run_load():
    df = pd.read_csv("../data/processed/jobs_clean.csv")
    df["extracted_skills"] = df["extracted_skills"].apply(ast.literal_eval)

    company_map = load_companies(engine, df)
    job_id_map = load_jobs(engine, df, company_map)
    skills_inserted = load_job_skills(engine, df, job_id_map)

    return {
        "companies": len(company_map),
        "jobs": len(job_id_map),
        "skills": skills_inserted,
    }


if __name__ == "__main__":
    results = run_load()
    print(f"Companies loaded: {results['companies']}")
    print(f"Jobs loaded: {results['jobs']}")
    print(f"Skill rows inserted: {results['skills']}")