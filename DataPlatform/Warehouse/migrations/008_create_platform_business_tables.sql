USE DW_DataJobs;
GO

CREATE SCHEMA platform;
GO

CREATE TABLE platform.[user] (
    user_id INT IDENTITY(1,1) PRIMARY KEY,
    email NVARCHAR(255) NOT NULL UNIQUE,
    password_hash NVARCHAR(255) NOT NULL,
    full_name NVARCHAR(255) NOT NULL,
    role_name NVARCHAR(50) NOT NULL,
    status_name NVARCHAR(50) NOT NULL DEFAULT 'active',
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE platform.company (
    company_id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    industry NVARCHAR(255) NULL,
    location NVARCHAR(255) NULL,
    website NVARCHAR(500) NULL,
    description NVARCHAR(MAX) NULL,
    created_by INT NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE platform.candidate_profile (
    user_id INT PRIMARY KEY,
    title NVARCHAR(255) NULL,
    location NVARCHAR(255) NULL,
    preferred_country NVARCHAR(255) NULL,
    skills_json NVARCHAR(MAX) NULL,
    education_json NVARCHAR(MAX) NULL,
    experience_summary NVARCHAR(MAX) NULL,
    visibility BIT NOT NULL DEFAULT 1
);
GO

CREATE TABLE platform.recruiter_profile (
    user_id INT PRIMARY KEY,
    title NVARCHAR(255) NULL,
    phone NVARCHAR(100) NULL,
    company_id INT NULL
);
GO

CREATE TABLE platform.job_offer (
    job_id INT IDENTITY(1,1) PRIMARY KEY,
    company_id INT NOT NULL,
    title NVARCHAR(255) NOT NULL,
    category NVARCHAR(255) NOT NULL,
    country NVARCHAR(255) NULL,
    city NVARCHAR(255) NULL,
    is_remote BIT NOT NULL DEFAULT 0,
    schedule_type NVARCHAR(255) NULL,
    description NVARCHAR(MAX) NULL,
    required_skills_json NVARCHAR(MAX) NULL,
    salary_year_avg DECIMAL(12,2) NULL,
    status_name NVARCHAR(50) NOT NULL DEFAULT 'draft',
    created_by INT NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE platform.cv_document (
    cv_id INT IDENTITY(1,1) PRIMARY KEY,
    owner_id INT NOT NULL,
    file_name NVARCHAR(500) NOT NULL,
    storage_path NVARCHAR(1000) NULL,
    extraction_json NVARCHAR(MAX) NULL,
    quality_json NVARCHAR(MAX) NULL,
    uploaded_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE platform.application (
    application_id INT IDENTITY(1,1) PRIMARY KEY,
    candidate_id INT NOT NULL,
    job_id INT NOT NULL,
    cover_letter NVARCHAR(MAX) NULL,
    status_name NVARCHAR(50) NOT NULL DEFAULT 'submitted',
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE platform.shortlist (
    shortlist_id INT IDENTITY(1,1) PRIMARY KEY,
    job_id INT NOT NULL,
    candidate_id INT NOT NULL,
    created_by INT NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE platform.notification (
    notification_id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,
    title NVARCHAR(255) NOT NULL,
    message NVARCHAR(MAX) NOT NULL,
    type_name NVARCHAR(50) NOT NULL DEFAULT 'info',
    is_read BIT NOT NULL DEFAULT 0,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE platform.audit_log (
    audit_id INT IDENTITY(1,1) PRIMARY KEY,
    actor_id INT NULL,
    action_name NVARCHAR(255) NOT NULL,
    entity_type NVARCHAR(255) NOT NULL,
    entity_id INT NULL,
    details_json NVARCHAR(MAX) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE TABLE platform.ai_processing_job (
    ai_job_id INT IDENTITY(1,1) PRIMARY KEY,
    type_name NVARCHAR(255) NOT NULL,
    status_name NVARCHAR(50) NOT NULL,
    user_id INT NULL,
    entity_id INT NULL,
    error_message NVARCHAR(MAX) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 NULL
);
GO
