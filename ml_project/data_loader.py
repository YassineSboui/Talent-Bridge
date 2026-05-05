import pyodbc
import pandas as pd
import config

DEFAULT_QUERY = """
WITH job_skills_agg AS (
    SELECT
        bs.job_posting_key,
        STRING_AGG(sk.skill_name, ', ') AS skills
    FROM [{config.DB_DATABASE}].[bridge].[job_skill] bs
    JOIN [{config.DB_DATABASE}].[dim].[skill] sk ON bs.skill_key = sk.skill_key
    GROUP BY bs.job_posting_key
)
SELECT TOP ({limit})
    fp.job_posting_key,
    fp.job_title,
    c.company_name,
    l.city,
    l.state_region,
    l.country,
    jc.category_name,
    jp.portal_name,
    s.schedule_type_name AS job_type,
    fp.is_work_from_home AS remote,
    fp.no_degree_mention,
    fp.has_health_insurance,
    fp.salary_year_avg,
    fp.salary_hour_avg,
    fp.has_salary_info,
    d.full_date AS posted_date,
    COALESCE(jsa.skills, '') AS skills
FROM [{config.DB_DATABASE}].[fact].[job_posting] fp
LEFT JOIN [{config.DB_DATABASE}].[dim].[company] c ON fp.company_key = c.company_key
LEFT JOIN [{config.DB_DATABASE}].[dim].[location] l ON fp.location_key = l.location_key
LEFT JOIN [{config.DB_DATABASE}].[dim].[job_category] jc ON fp.job_category_key = jc.job_category_key
LEFT JOIN [{config.DB_DATABASE}].[dim].[job_portal] jp ON fp.portal_key = jp.portal_key
LEFT JOIN [{config.DB_DATABASE}].[dim].[schedule_type] s ON fp.salary_rate_key = s.schedule_type_key
LEFT JOIN [{config.DB_DATABASE}].[dim].[date] d ON fp.date_key = d.date_key
LEFT JOIN job_skills_agg jsa ON fp.job_posting_key = jsa.job_posting_key
"""


def get_connection_string():
    if config.DB_USERNAME and config.DB_PASSWORD:
        return (
            f"Driver={{{config.DB_DRIVER}}};"
            f"Server={config.DB_SERVER};"
            f"Database={config.DB_DATABASE};"
            f"Uid={config.DB_USERNAME};"
            f"Pwd={config.DB_PASSWORD};"
        )
    return (
        f"Driver={{{config.DB_DRIVER}}};"
        f"Server={config.DB_SERVER};"
        f"Database={config.DB_DATABASE};"
        f"Trusted_Connection=yes;"
        f"Encrypt=yes;"
        f"TrustServerCertificate=yes;"
    )


def fetch_jobs(query: str = None, table: str = None, limit: int = 20000) -> pd.DataFrame:
    conn_str = get_connection_string()
    if query is None:
        if table:
            if "." in table:
                parts = table.split(".")
                query = f"SELECT TOP ({limit}) * FROM [{config.DB_DATABASE}].[{parts[0]}].[{parts[1]}]"
            else:
                query = f"SELECT TOP ({limit}) * FROM [{config.DB_DATABASE}].[dbo].[{table}]"
        else:
            query = DEFAULT_QUERY.format(limit=limit, config=config)
    with pyodbc.connect(conn_str) as conn:
        df = pd.read_sql(query, conn)
    return df
