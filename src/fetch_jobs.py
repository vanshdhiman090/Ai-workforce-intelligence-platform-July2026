import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
RAW_OUTPUT_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "jobs_raw.csv")

COUNTRY = "de"
QUERIES = ["data analyst", "data engineer", "business intelligence", "python developer"]
RESULTS_PER_PAGE = 20
PAGES_PER_QUERY = 15
MAX_RETRIES = 3

load_dotenv()
APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")


def fetch_page(query, page_number, max_retries=MAX_RETRIES):
    url = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/{page_number}"
    params = {"app_id": APP_ID, "app_key": APP_KEY, "results_per_page": RESULTS_PER_PAGE, "what": query}
    response = None
    for attempt in range(max_retries):
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response
        if 500 <= response.status_code < 600:
            time.sleep(2 ** (attempt + 1))
            continue
        return response
    return response


def run_fetch():
    if not APP_ID or not APP_KEY:
        raise ValueError("Missing Adzuna credentials — check ADZUNA_APP_ID / ADZUNA_APP_KEY")

    all_jobs = []
    for query in QUERIES:
        print(f"\n=== Query: '{query}' ===")
        for page in range(1, PAGES_PER_QUERY + 1):
            print(f"Fetching page {page}...")
            try:
                response = fetch_page(query, page)
                if response.status_code != 200:
                    print(f"Warning: status {response.status_code} — moving to next query.")
                    break
                results = response.json().get("results", [])
                if not results:
                    print(f"No more results for '{query}' at page {page}.")
                    break
                all_jobs.extend(results)
                print(f"Collected {len(results)} jobs")
                time.sleep(1)
            except Exception as e:
                print(f"Error on '{query}' page {page}: {e}")
                break

    print(f"\nTotal jobs collected across all queries: {len(all_jobs)}")

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

    os.makedirs(os.path.dirname(RAW_OUTPUT_PATH), exist_ok=True)
    df.to_csv(RAW_OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"\nCSV saved successfully to {RAW_OUTPUT_PATH}")
    return len(df)


if __name__ == "__main__":
    total = run_fetch()
    print(f"Total jobs collected: {total}")