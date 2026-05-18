USE DW_DataJobs;
GO

CREATE OR ALTER VIEW cv.vw_analysis_summary AS
SELECT
    ar.analysis_id,
    ar.created_at,
    ar.file_name,
    ar.candidate_name,
    ar.email,
    ar.target_role,
    ar.preferred_country,
    ar.remote_preference,
    ar.years_of_experience,
    ar.seniority_level,
    ar.quality_label,
    ar.quality_score,
    ar.structure_score,
    ar.content_score,
    COUNT(DISTINCT askill.skill_name) AS extracted_skill_count,
    COUNT(DISTINCT jmr.job_posting_key) AS saved_match_count,
    MAX(jmr.match_score) AS best_match_score,
    AVG(jmr.match_score) AS avg_match_score
FROM cv.analysis_run ar
LEFT JOIN cv.analysis_skill askill
    ON askill.analysis_id = ar.analysis_id
LEFT JOIN cv.job_match_result jmr
    ON jmr.analysis_id = ar.analysis_id
GROUP BY
    ar.analysis_id,
    ar.created_at,
    ar.file_name,
    ar.candidate_name,
    ar.email,
    ar.target_role,
    ar.preferred_country,
    ar.remote_preference,
    ar.years_of_experience,
    ar.seniority_level,
    ar.quality_label,
    ar.quality_score,
    ar.structure_score,
    ar.content_score;
GO

CREATE OR ALTER VIEW cv.vw_match_detail AS
SELECT
    jmr.analysis_id,
    ar.created_at,
    ar.candidate_name,
    ar.target_role,
    ar.quality_label,
    ar.quality_score,
    jmr.rank_num,
    jmr.job_posting_key,
    f.job_title,
    jc.category_name,
    c.company_name,
    l.country,
    l.city,
    f.is_work_from_home,
    f.has_salary_info,
    f.salary_year_avg,
    f.no_degree_mention,
    f.has_health_insurance,
    jmr.match_score,
    jmr.skills_score,
    jmr.role_score,
    jmr.experience_score,
    jmr.education_score,
    jmr.location_score,
    jmr.opportunity_score,
    jmr.matched_skills_csv,
    jmr.missing_skills_csv,
    jmr.explanation
FROM cv.job_match_result jmr
INNER JOIN cv.analysis_run ar
    ON ar.analysis_id = jmr.analysis_id
INNER JOIN fact.job_posting f
    ON f.job_posting_key = jmr.job_posting_key
LEFT JOIN dim.job_category jc
    ON jc.job_category_key = f.job_category_key
LEFT JOIN dim.company c
    ON c.company_key = f.company_key
LEFT JOIN dim.[location] l
    ON l.location_key = f.location_key;
GO

CREATE OR ALTER VIEW cv.vw_candidate_skill AS
SELECT
    ar.analysis_id,
    ar.created_at,
    ar.candidate_name,
    ar.target_role,
    askill.skill_name
FROM cv.analysis_skill askill
INNER JOIN cv.analysis_run ar
    ON ar.analysis_id = askill.analysis_id;
GO
