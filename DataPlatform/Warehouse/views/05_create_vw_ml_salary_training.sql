USE DW_DataJobs;
GO

CREATE OR ALTER VIEW dbo.vw_ml_salary_training AS
SELECT *
FROM dbo.vw_ml_jobs
WHERE salary_year_avg IS NOT NULL
  AND salary_year_avg BETWEEN 10000 AND 400000;
GO
