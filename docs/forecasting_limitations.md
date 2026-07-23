# Forecasting & Trends — Data Limitation Notice

## What we checked

We queried the date range of the `jobs.created_date` field to evaluate whether
meaningful time-series forecasting (e.g., skill demand trends, posting volume
over time) could be built from the current dataset.

    SELECT MIN(created_date), MAX(created_date), COUNT(DISTINCT created_date)
    FROM jobs;

## What we found

The `created_date` field spans **2022-07-02 to 2026-07-09** — a four-year range.
However, breaking this down by daily counts revealed that the vast majority of
postings cluster tightly in a **~9-day window** (2026-06-30 to 2026-07-09),
matching exactly when the Adzuna data collection (`fetch_jobs.py`) actually ran.

The older, scattered dates (2022–2024) are almost entirely single-count days —
consistent with Adzuna aggregating syndicated/re-posted listings from other job
boards, where `created_date` reflects the *original* posting date, not when
Adzuna surfaced it to us.

## Why this blocks honest forecasting today

Real time-series forecasting requires **repeated data collection over time** —
multiple snapshots taken at consistent intervals (daily or weekly), so trends
can be measured between them. What we have is a **single snapshot**: one
scraping run, capturing whatever was live in the market during a ~9-day window,
with some incidental noise from older listings mixed in.

Building a "trend chart" or "forecast" from this data would misrepresent a
one-time sample as if it were a time series — this is exactly the kind of
false precision this project is committed to avoiding.

## What would fix this

Per the project roadmap, **Week 10 (Automation Pipeline)** calls for running
the data collection pipeline on a recurring schedule. Once `fetch_jobs.py` is
automated to run daily or weekly over an extended period, we would have real,
comparable snapshots over time — at that point, genuine trend analysis and
forecasting become possible and honest.

## Decision

Forecasting is deferred until repeated data collection is in place. No
forecast or trend visual has been built on the current single-snapshot data.