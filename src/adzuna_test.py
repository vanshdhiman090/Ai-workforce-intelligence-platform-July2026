import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

# =========================================================
# CONFIG — change project scope here, never inside functions
# =========================================================
COUNTRY = "de"
QUERIES = [
    "data analyst",
    "data engineer",
    "business intelligence",
    "python developer",
]
RESULTS_PER_PAGE = 20
PAGES_PER_QUERY = 15   # ~300 records per query → up to ~1,200 total (before cross-query overlap)
MAX_RETRIES = 3        # retries per page on transient (5xx) errors

RAW_OUTPUT_PATH = "data/raw/jobs_raw.csv"

# =========================================================
# Load API credentials
# =========================================================
load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

if not APP_ID or not APP_KEY:
    raise ValueError("Missing Adzuna credentials — check your .env file (ADZUNA_APP_ID / ADZUNA_APP_KEY)")


# =========================================================
# Fetch a single page for a given query, with retry + backoff
# =========================================================
def fetch_page(query, page_number, max_retries=MAX_RETRIES):
    url = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/{page_number}"
    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "results_per_page": RESULTS_PER_PAGE,
        "what": query
    }

    for attempt in range(max_retries):
        response = requests.get(url, params=params)

        if response.status_code == 200:
            return response

        if 500 <= response.status_code < 600:
            # Transient server-side error — worth retrying with backoff
            wait_time = 2 ** (attempt + 1)  # 2s, 4s, 8s
            print(f"Server error {response.status_code} on attempt {attempt + 1}/{max_retries}, "
                  f"retrying in {wait_time}s...")
            time.sleep(wait_time)
            continue

        # Non-transient error (e.g. 401, 403, 404) — retrying won't help
        print(f"Non-retryable error {response.status_code} — giving up on this page.")
        return response

    # Retries exhausted — return the last response as-is so caller can inspect it
    print(f"All {max_retries} retries exhausted for '{query}' page {page_number}.")
    return response


# =========================================================
# Collect jobs across all queries and pages
# =========================================================
all_jobs = []

for query in QUERIES:
    print(f"\n=== Query: '{query}' ===")

    for page in range(1, PAGES_PER_QUERY + 1):
        print(f"Fetching page {page}...")

        try:
            response = fetch_page(query, page)

            if response.status_code != 200:
                print(f"Warning: failed on '{query}' page {page} — status {response.status_code}. "
                      f"Moving to next query.")
                break

            data = response.json()
            results = data.get("results", [])

            if not results:
                print(f"No more results for '{query}' at page {page} — moving to next query.")
                break

            all_jobs.extend(results)
            print(f"Collected {len(results)} jobs")

            time.sleep(1)  # be polite to the API between successful requests

        except Exception as e:
            print(f"Error on '{query}' page {page}: {e}")
            break

print(f"\nTotal jobs collected across all queries: {len(all_jobs)}")


# =========================================================
# Flatten nested JSON into flat records
# =========================================================
records = []

for job in all_jobs:
    records.append({
        "title": job.get("title"),
        "company": job.get("company", {}).get("display_name"),
        "location": job.get("location", {}).get("display_name"),
        "salary_min": job.get("salary_min"),
        "salary_max": job.get("salary_max"),
        "salary_is_predicted": job.get("salary_is_predicted"),
        "created": job.get("created"),
        "category": job.get("category", {}).get("label"),
        "description": job.get("description"),
    })

df = pd.DataFrame(records)


# =========================================================
# Sanity checks — always look before you save
# =========================================================
print("\nDataFrame shape:", df.shape)
print("\nFirst 5 rows:")
print(df.head())

total_rows = len(df)
unique_titles = df['title'].nunique()
unique_pairs = df.drop_duplicates(subset=['title', 'company']).shape[0]

print(f"\nTotal rows: {total_rows}")
print(f"Unique titles: {unique_titles}")
print(f"Unique (title+company) pairs: {unique_pairs}")
print(f"Duplicate rate: {(1 - unique_pairs / total_rows) * 100:.1f}%")


# =========================================================
# Save raw CSV — deliberately NOT deduped here.
# Dedup strategy is a Day 4/5 cleaning decision, not ingestion.
# =========================================================
os.makedirs("data/raw", exist_ok=True)
df.to_csv(RAW_OUTPUT_PATH, index=False, encoding="utf-8-sig")

print(f"\nCSV saved successfully to {RAW_OUTPUT_PATH}")