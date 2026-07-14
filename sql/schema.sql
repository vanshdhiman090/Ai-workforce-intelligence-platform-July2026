CREATE TABLE companies (
    company_id SERIAL PRIMARY KEY,
    company_name TEXT NOT NULL UNIQUE
);

CREATE TABLE jobs (
    job_id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    company_id INTEGER REFERENCES companies(company_id),
    location TEXT,
    salary_min NUMERIC,
    salary_max NUMERIC,
    has_salary_data BOOLEAN,
    salary_is_predicted BOOLEAN,
    created_date DATE,
    category TEXT
);

CREATE TABLE job_skills (
    job_id INTEGER REFERENCES jobs(job_id),
    skill_name TEXT NOT NULL,
    PRIMARY KEY (job_id, skill_name)
);