# AI Workforce Intelligence Platform

A transparent skills-demand intelligence tool for the German job market — built for HR and L&D teams who need directional signal on in-demand skills, with explicit data quality reporting instead of false precision.

**🔗 Live app:** https://ai-workforce-intelligence-platform-july2026-kvvfa6vrauzrcnulce.streamlit.app/

---

## What this is

Most "market intelligence" dashboards present numbers with false confidence — clean charts that hide messy, incomplete, or biased source data. This project does the opposite: every insight is paired with an explicit statement of its limitations, so an HR Director can act on the signal without being misled by it.

Built end-to-end: live data ingestion from a public job-postings API, a normalized PostgreSQL database (hosted on Neon), a Power BI dashboard, and a deployed interactive Streamlit app with an AI-powered executive interpretation layer.

## Who it's for

- **HR Directors** — want a fast read on where the talent market is heading, without needing to trust a black-box number.
- **Workforce / L&D Planners** — need to know which skills to build internally vs. hire externally.
- **Hiring Teams / Recruiters** — want to benchmark a company's current job postings against what the broader market is actually asking for.

## Key features

- **Live market snapshot** — total postings, companies, and top in-demand skills, pulled from real German job listings (Adzuna API).
- **City-level exploration** — filter live postings by location.
- **Skills Gap Analysis** — select any company with detected skill data and see exactly which in-demand market skills are missing from their current hiring profile, as a precise set difference (not a vague estimate).
- **AI Executive Insight** — a Gemini-powered layer that turns the raw skills-gap numbers into a structured, four-part executive briefing (Hiring Focus, Market Comparison, Recommendation, Strategic Risk). The AI only narrates and interprets numbers already computed by SQL — it never calculates statistics or invents data itself.
- **Self-service data refresh** — a password-protected button that re-runs the full ingestion → cleaning → loading pipeline on demand, so the live dataset can be refreshed without redeploying code.
- **Explicit data quality reporting** — every known limitation in the data is surfaced in the app itself, not hidden in a footnote (see below).

## Data quality — reported, not hidden

This is the core design principle of the project. Specific, documented findings:

| Finding | Detail |
|---|---|
| Skill detection is a lower bound | Only ~10–15% of postings have a detectable skill mention, because the source API truncates job descriptions at ~500 characters — often cutting off the requirements section before any keyword match is possible. This was diagnosed by reading real description samples, not assumed. |
| Category coverage gap | 54% of postings (422/787) have no category assigned by the source — shown explicitly as "Unknown" rather than silently excluded or hidden in aggregate charts. |
| Salary data is sparse | Only ~5.6% of postings include salary figures — any salary-based claim is flagged with this sample size. |
| Skills Gap Analysis coverage | Currently usable for 105 of 558 companies (~19%), up from an initial 74 after expanding the skill-detection vocabulary from 7 to 25 terms. Coverage remains capped by the description-truncation issue above, not by vocabulary size. |
| Forecasting is deliberately not offered | The dataset is fundamentally a single ingestion snapshot (with some source-side noise from re-posted listings spanning multiple years). Time-series forecasting requires repeated data collection over time — building a trend chart on this data would misrepresent a snapshot as a time series. See `docs/forecasting_limitations.md` for the full investigation. |

## Architecture

```
Adzuna API
    │
    ▼
fetch_jobs.py        (paginated ingestion, exponential backoff on 5xx)
    │
    ▼
clean_data.py         (dedup, missing-value handling, skill extraction via regex)
    │
    ▼
PostgreSQL (Neon)      (companies / jobs / job_skills — normalized, 3NF)
    │
    ├──▶ Power BI       (executive dashboard)
    │
    └──▶ Streamlit app  (interactive UI, deployed on Streamlit Community Cloud)
              │
              └──▶ Gemini API   (executive insight narration only — never calculates)
```

The pipeline (`run_pipeline.py`) chains ingestion → cleaning → loading with return-code failure detection and timestamped logging, so a failed step never silently corrupts the next one. It is idempotent by design: re-running it never creates duplicate rows.

## Tech stack

- **Ingestion & processing:** Python, pandas, `requests`
- **Database:** PostgreSQL, hosted on Neon (cloud), SQLAlchemy for connection management
- **BI:** Power BI Desktop
- **App:** Streamlit, deployed on Streamlit Community Cloud
- **AI:** Google Gemini API (`gemini-flash-latest`)
- **Testing:** pytest — unit coverage for skill-extraction regex correctness and skills-gap set-difference logic
- **Version control:** Git / GitHub

## Project structure

```
├── src/
│   ├── fetch_jobs.py       # API ingestion
│   ├── clean_data.py       # Cleaning + skill extraction
│   ├── load_to_db.py       # Idempotent database loader
│   ├── run_pipeline.py     # Orchestrator with logging
│   ├── ai_insights.py      # Gemini-powered executive interpretation
│   └── app.py              # Streamlit application
├── sql/
│   ├── schema.sql          # Database schema (3 normalized tables)
│   └── analysis_queries.sql
├── tests/
│   ├── test_clean_data.py
│   └── test_skills_gap.py
├── docs/
│   └── forecasting_limitations.md
├── powerbi/
│   └── workforce_dashboard.pbix
└── requirements.txt
```

## Running it locally

```bash
git clone https://github.com/vanshdhiman090/Ai-workforce-intelligence-platform-July2026.git
cd Ai-workforce-intelligence-platform-July2026
python -m venv src/.venv
source src/.venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
ADZUNA_APP_ID=your_id
ADZUNA_APP_KEY=your_key
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=5432
DB_NAME=your_db_name
GEMINI_API_KEY=your_gemini_key
REFRESH_PASSWORD=your_chosen_password
```

Run the full pipeline once to populate the database:

```bash
python src/run_pipeline.py
```

Launch the app:

```bash
streamlit run src/app.py
```

## Testing

```bash
pytest tests/ -v
```

## What I'd do with more time

- Expand skill-detection coverage further, or move to a source with full (non-truncated) job descriptions
- Automate scheduled re-ingestion (GitHub Actions) so the dataset accumulates real historical snapshots — the actual prerequisite for honest forecasting
- Add CI (test suite running automatically on every push) and a Dockerfile for containerized deployment
- Broaden the AI layer to a natural-language Q&A interface over the dataset, constrained to verified SQL results

## Author

Built by Vansh Dhiman as an end-to-end portfolio project spanning data engineering, analytics engineering, BI, and applied AI integration.