# Power BI Role Links Setup

Talent Bridge opens Power BI dashboards through external buttons. Power BI is not mounted inside the application.

## Recommended Setup

Publish separate Power BI reports for each role:

| Talent Bridge role | Power BI report |
| --- | --- |
| Candidate | Candidate KPI report |
| Recruiter | Recruiter KPI report |
| Admin | Full KPI report |

This keeps the demo simple and avoids showing users pages that do not belong to their role.

## Environment Variables

Configure the report URLs in the backend environment:

```text
TALENTBRIDGE_POWERBI_CANDIDATE_URL=<candidate report url>
TALENTBRIDGE_POWERBI_RECRUITER_URL=<recruiter report url>
TALENTBRIDGE_POWERBI_ADMIN_URL=<admin report url>
```

If these variables are empty, the app falls back to the original project report URL.

## App Behavior

The backend endpoint is:

```text
GET /api/v1/admin/powerbi
```

It returns only the link allowed for the authenticated role:

- Candidate receives only the candidate dashboard link.
- Recruiter receives only the recruiter dashboard link.
- Admin receives only the full admin dashboard link.

No Azure App Registration, service principal, embed token, or Power BI iframe is required.
