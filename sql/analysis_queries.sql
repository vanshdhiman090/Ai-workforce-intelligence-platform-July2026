-- ============================================
-- Analytical queries: Day 7
-- Database: workforce_intelligence
-- ============================================

-- Query 1: Top 10 most in-demand skills
-- NOTE: Based on regex-detected skill mentions in ~10% of postings
-- (Day 4 limitation). This is a lower-bound signal, not a complete
-- market picture — only 7 distinct skills currently in vocabulary.
SELECT skill_name, COUNT(*) AS mentions
FROM job_skills
GROUP BY skill_name
ORDER BY mentions DESC
LIMIT 10;

-- Query 2: Top 10 cities by job postings
-- NOTE: Excludes rows where location = 'Deutschland' (country-level
-- only, no specific city given by Adzuna) to avoid misrepresenting
-- a non-city value as a top location.
SELECT location, COUNT(*) AS job_count
FROM jobs
WHERE location IS NOT NULL AND location != 'Deutschland'
GROUP BY location
ORDER BY job_count DESC
LIMIT 10;

-- Query 3: Job count per category
-- NOTE: 422 of 787 jobs (~54%) fall under "Unknown" category —
-- this is a major data quality gap, not a real category, and must
-- be disclosed explicitly wherever this breakdown is presented.
SELECT category, COUNT(*) AS job_count
FROM jobs
GROUP BY category
ORDER BY job_count DESC;

-- Query 4: Top 10 companies by number of job postings
SELECT c.company_name, COUNT(j.job_id) AS job_count
FROM jobs j
JOIN companies c ON j.company_id = c.company_id
GROUP BY c.company_name
ORDER BY job_count DESC
LIMIT 10;