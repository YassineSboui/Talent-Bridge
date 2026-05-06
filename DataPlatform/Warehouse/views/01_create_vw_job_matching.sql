USE DW_DataJobs;
GO

CREATE OR ALTER VIEW dbo.vw_job_matching AS
WITH skill_agg AS (
    SELECT
        bs.job_posting_key,
        STRING_AGG(CONVERT(NVARCHAR(MAX), sk.skill_name), N',') AS skills_csv,
        STRING_AGG(CONVERT(NVARCHAR(MAX), sk.skill_category), N',') AS skill_categories_csv
    FROM bridge.job_skill bs
    INNER JOIN dim.skill sk
        ON sk.skill_key = bs.skill_key
    GROUP BY bs.job_posting_key
),
schedule_agg AS (
    SELECT
        bsch.job_posting_key,
        STRING_AGG(CONVERT(NVARCHAR(MAX), st.schedule_type_name), N',') AS schedule_types_csv
    FROM bridge.job_schedule bsch
    INNER JOIN dim.schedule_type st
        ON st.schedule_type_key = bsch.schedule_type_key
    GROUP BY bsch.job_posting_key
)
SELECT
    f.job_posting_key,
    f.job_title,
    jc.category_name,
    c.company_name,
    l.country,
    l.city,
    f.is_work_from_home,
    f.no_degree_mention,
    f.has_health_insurance,
    f.salary_year_avg,
    f.salary_hour_avg,
    f.has_salary_info,
    p.portal_name,
    d.full_date AS posted_date,
    ISNULL(sa.skills_csv, N'') AS skills_csv,
    ISNULL(sa.skill_categories_csv, N'') AS skill_categories_csv,
    ISNULL(scha.schedule_types_csv, N'') AS schedule_types_csv
FROM fact.job_posting f
LEFT JOIN dim.[date] d
    ON d.date_key = f.date_key
LEFT JOIN dim.company c
    ON c.company_key = f.company_key
LEFT JOIN dim.[location] l
    ON l.location_key = f.location_key
LEFT JOIN dim.job_category jc
    ON jc.job_category_key = f.job_category_key
LEFT JOIN dim.job_portal p
    ON p.portal_key = f.portal_key
LEFT JOIN skill_agg sa
    ON sa.job_posting_key = f.job_posting_key
LEFT JOIN schedule_agg scha
    ON scha.job_posting_key = f.job_posting_key;
GO
