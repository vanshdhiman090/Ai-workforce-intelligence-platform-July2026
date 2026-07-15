import os
import ast
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

for var_name, val in [("DB_USER", DB_USER), ("DB_PASSWORD", DB_PASSWORD),
                       ("DB_HOST", DB_HOST), ("DB_NAME", DB_NAME)]:
    if not val:
        raise ValueError(f"Missing required env var: {var_name}")

from sqlalchemy import URL

connection_url = URL.create(
    "postgresql",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME,
)
engine = create_engine(connection_url)

print("✅ Connected to database successfully")

df = pd.read_csv("../data/processed/jobs_clean.csv")
df["extracted_skills"] = df["extracted_skills"].apply(ast.literal_eval)

print(f"Loaded {len(df)} rows")
print(df[["title", "company", "extracted_skills"]].head(3))

print(f"Rows with at least 1 skill: {(df['extracted_skills'].apply(len) > 0).sum()}")

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

company_map = load_companies(engine, df)
print(f"Companies loaded: {len(company_map)}")
print(dict(list(company_map.items())[:5]))

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
job_id_map = load_jobs(engine, df, company_map)
print(f"Jobs loaded: {len(job_id_map)}")

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

skills_inserted = load_job_skills(engine, df, job_id_map)
print(f"Skill rows inserted: {skills_inserted}")