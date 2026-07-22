import os
import re
import pandas as pd

# ============================================================
# Project Paths
# ============================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

RAW_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "jobs_raw.csv")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
OUTPUT_PATH = os.path.join(PROCESSED_DIR, "jobs_clean.csv")

os.makedirs(PROCESSED_DIR, exist_ok=True)

# ============================================================
# Load Raw Dataset
# ============================================================

df = pd.read_csv(RAW_PATH)

print("=" * 60)
print("RAW DATASET OVERVIEW")
print("=" * 60)
print(df.info())

print("\nMissing Values")
print(df.isnull().sum())
print(f"\nTotal rows: {len(df)}")

# ============================================================
# Remove Duplicate Job Listings
# ============================================================

before = len(df)

df_clean = df.drop_duplicates(
    subset=["title", "company", "location"]
).copy()

after = len(df_clean)
duplicates_removed = before - after
duplicate_percentage = (duplicates_removed / before) * 100

print("\n" + "=" * 60)
print("DUPLICATE ANALYSIS")
print("=" * 60)
print(f"Rows before cleaning : {before}")
print(f"Rows after cleaning  : {after}")
print(f"Duplicates removed   : {duplicates_removed}")
print(f"Duplicate rate       : {duplicate_percentage:.1f}%")

# ============================================================
# Handle Missing Company Values
# Decision: fill with "Unknown" rather than drop the row —
# title/location/skills data is still valid and usable even
# without a company name.
# ============================================================

missing_company_before = df_clean["company"].isnull().sum()
df_clean["company"] = df_clean["company"].fillna("Unknown")

print("\n" + "=" * 60)
print("MISSING COMPANY HANDLING")
print("=" * 60)
print(f"Rows with missing company filled as 'Unknown': {missing_company_before}")

# ============================================================
# Salary Data Flagging
# Decision: keep salary fields, but add an explicit flag so
# downstream analysis/dashboards never present salary stats
# without acknowledging the small sample size.
# ============================================================

df_clean["has_salary_data"] = df_clean["salary_min"].notna()
salary_coverage = df_clean["has_salary_data"].sum()
salary_coverage_pct = (salary_coverage / len(df_clean)) * 100

print("\n" + "=" * 60)
print("SALARY DATA COVERAGE")
print("=" * 60)
print(f"Rows with salary data: {salary_coverage} / {len(df_clean)} ({salary_coverage_pct:.1f}%)")
print("NOTE: Salary analysis should always be reported alongside this")
print("sample size — coverage is too thin to treat as representative.")

# ============================================================
# Extract Skills from Job Description
# Fixed: word-boundary regex matching instead of substring
# matching, to avoid false positives (e.g. "Excel" matching
# inside "excellent").
#
# Expanded (Day 11): added common tech/data role skills beyond
# the original 7, to improve detection coverage. Note: coverage
# is still fundamentally capped by Adzuna's ~500-character
# description truncation, which often cuts off the requirements
# section before any keyword list could match it.
# ============================================================

SKILLS = [
    "Python",
    "SQL",
    "Power BI",
    "Excel",
    "Tableau",
    "AWS",
    "Azure",
    "Java",
    "JavaScript",
    "React",
    "Docker",
    "Kubernetes",
    "Git",
    "Salesforce",
    "SAP",
    "Machine Learning",
    "Data Analysis",
    "Scrum",
    "Agile",
    "Jira",
    "Linux",
    "C#",
    ".NET",
    "Node.js",
    "TypeScript"
]


def extract_skills(description, skill_list=SKILLS):
    """
    Extract predefined technical skills from a job description
    using word-boundary matching to avoid substring false positives.
    """
    if pd.isna(description):
        return []

    found = [
        skill
        for skill in skill_list
        if re.search(rf"\b{re.escape(skill.lower())}\b", description.lower())
    ]
    return found


df_clean["extracted_skills"] = (
    df_clean["description"]
    .apply(extract_skills)
)

# ============================================================
# Save Clean Dataset
# ============================================================

df_clean.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8-sig"
)

print("\n" + "=" * 60)
print("DATA CLEANING COMPLETE")
print("=" * 60)
print(f"Clean dataset saved to:\n{OUTPUT_PATH}")
print(f"\nFinal dataset contains {len(df_clean)} job records.")

print("\nSample of extracted_skills (first 10 rows):")
print(df_clean[["title", "extracted_skills"]].head(10).to_string())