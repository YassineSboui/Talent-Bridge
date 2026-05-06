USE DW_DataJobs;
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = N'cv')
    EXEC(N'CREATE SCHEMA cv');
GO

CREATE TABLE cv.analysis_run (
    analysis_id BIGINT IDENTITY(1,1) NOT NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_cv_analysis_run_created_at DEFAULT SYSUTCDATETIME(),
    file_name NVARCHAR(500) NULL,
    candidate_name NVARCHAR(300) NULL,
    email NVARCHAR(300) NULL,
    target_role NVARCHAR(150) NULL,
    preferred_country NVARCHAR(150) NULL,
    remote_preference NVARCHAR(50) NULL,
    years_of_experience DECIMAL(5,2) NULL,
    seniority_level NVARCHAR(50) NULL,
    quality_label NVARCHAR(30) NULL,
    quality_score INT NULL,
    structure_score INT NULL,
    content_score INT NULL,
    raw_extraction_json NVARCHAR(MAX) NULL,
    quality_json NVARCHAR(MAX) NULL,
    CONSTRAINT PK_cv_analysis_run PRIMARY KEY CLUSTERED (analysis_id)
);
GO

CREATE TABLE cv.analysis_skill (
    analysis_id BIGINT NOT NULL,
    skill_name NVARCHAR(150) NOT NULL,
    CONSTRAINT PK_cv_analysis_skill PRIMARY KEY CLUSTERED (analysis_id, skill_name),
    CONSTRAINT FK_cv_analysis_skill_run FOREIGN KEY (analysis_id)
        REFERENCES cv.analysis_run(analysis_id)
        ON DELETE CASCADE
);
GO

CREATE TABLE cv.job_match_result (
    analysis_id BIGINT NOT NULL,
    rank_num INT NOT NULL,
    job_posting_key INT NOT NULL,
    match_score DECIMAL(6,2) NOT NULL,
    skills_score DECIMAL(6,2) NULL,
    role_score DECIMAL(6,2) NULL,
    experience_score DECIMAL(6,2) NULL,
    education_score DECIMAL(6,2) NULL,
    location_score DECIMAL(6,2) NULL,
    opportunity_score DECIMAL(6,2) NULL,
    matched_skills_csv NVARCHAR(MAX) NULL,
    missing_skills_csv NVARCHAR(MAX) NULL,
    explanation NVARCHAR(MAX) NULL,
    CONSTRAINT PK_cv_job_match_result PRIMARY KEY CLUSTERED (analysis_id, rank_num),
    CONSTRAINT FK_cv_job_match_result_run FOREIGN KEY (analysis_id)
        REFERENCES cv.analysis_run(analysis_id)
        ON DELETE CASCADE,
    CONSTRAINT FK_cv_job_match_result_job FOREIGN KEY (job_posting_key)
        REFERENCES fact.job_posting(job_posting_key)
);
GO

CREATE NONCLUSTERED INDEX IX_cv_analysis_run_created_at
ON cv.analysis_run (created_at DESC)
INCLUDE (target_role, quality_label, quality_score);
GO

CREATE NONCLUSTERED INDEX IX_cv_job_match_result_job
ON cv.job_match_result (job_posting_key)
INCLUDE (analysis_id, rank_num, match_score);
GO
