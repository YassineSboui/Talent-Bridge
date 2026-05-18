# BI Mini-Project

## What It Does

This mini-project visualizes IT job market trends using Power BI.

Main file:

```text
BI/PowerBI/Mission D'entreprise.pbix
```

## Why It Exists

The business objective is to understand the IT job market:

- salary trends
- job categories
- countries and remote distribution
- platform/job source trends
- demanded skills
- opportunity signals

## Main Folders

```text
BI/PowerBI/measures/
BI/PowerBI/model/
BI/PowerBI/visuals/
BI/PowerBI/screenshots/
```

## How It Works

Power BI reads the SQL Server warehouse produced by `DataPlatform`.

The dashboard should not calculate raw transformations itself. Transformation belongs in SQL/SSIS.

## Inputs

```text
DW_DataJobs SQL warehouse
fact.job_posting
dim.skill
bridge.job_skill
dim.job_category
dim.location
```

## Outputs

```text
Interactive Power BI dashboard
dashboard screenshots
DAX measures
visual plan
```

## Teacher Validation Checklist

- `.pbix` opens.
- Dashboard pages show meaningful job-market analysis.
- Measures are documented.
- Relationships are documented.
- BI layer depends on SQL warehouse, not raw CSV.
