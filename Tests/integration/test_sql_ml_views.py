from __future__ import annotations

import os


REQUIRED_VIEWS = [
    "dbo.vw_job_matching",
    "dbo.vw_ml_jobs",
    "dbo.vw_ml_salary_training",
    "dbo.vw_ml_classification_training",
    "dbo.vw_ml_segmentation_training",
]


def main() -> None:
    try:
        import pyodbc
    except ImportError as exc:
        raise RuntimeError("pyodbc is required for SQL integration checks") from exc

    connection_string = os.getenv(
        "DW_DATAJOBS_CONNECTION_STRING",
        "Driver={ODBC Driver 17 for SQL Server};Server=localhost;Database=DW_DataJobs;Trusted_Connection=yes;TrustServerCertificate=yes;",
    )
    with pyodbc.connect(connection_string) as connection:
        cursor = connection.cursor()
        for view_name in REQUIRED_VIEWS:
            schema, name = view_name.split(".")
            row = cursor.execute(
                """
                SELECT COUNT(*)
                FROM INFORMATION_SCHEMA.VIEWS
                WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?;
                """,
                schema,
                name,
            ).fetchone()
            if not row or int(row[0]) != 1:
                raise RuntimeError(f"Missing SQL view: {view_name}")
    print("SQL ML/matching views exist")


if __name__ == "__main__":
    main()
