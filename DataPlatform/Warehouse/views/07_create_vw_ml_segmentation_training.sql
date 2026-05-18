USE DW_DataJobs;
GO

CREATE OR ALTER VIEW dbo.vw_ml_segmentation_training AS
SELECT *
FROM dbo.vw_ml_jobs
WHERE job_title IS NOT NULL
  AND job_title_short IS NOT NULL;
GO
