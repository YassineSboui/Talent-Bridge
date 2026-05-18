USE DW_DataJobs;
GO

CREATE OR ALTER VIEW dbo.vw_ml_jobs AS
SELECT
    job_posting_key,
    job_title,
    category_name AS job_title_short,
    company_name,
    country AS job_country,
    city,
    portal_name AS job_via,
    schedule_types_csv AS job_schedule_type,
    is_work_from_home AS job_work_from_home,
    no_degree_mention AS job_no_degree_mention,
    has_health_insurance AS job_health_insurance,
    posted_date AS job_posted_date,
    salary_year_avg,
    salary_hour_avg,
    skills_csv AS job_skills,
    skill_categories_csv AS job_type_skills
FROM dbo.vw_job_matching;
GO
