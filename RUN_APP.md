# Run Talent Bridge

From the repository root:

```powershell
.\start_talent_bridge.ps1
```

With verification before startup:

```powershell
.\start_talent_bridge.ps1 -RunChecks
```

Double-click alternative:

```text
start_talent_bridge.bat
```

Options:

```powershell
.\start_talent_bridge.ps1 -SkipSql
.\start_talent_bridge.ps1 -SkipDashboard
.\start_talent_bridge.ps1 -SkipBrowser
.\start_talent_bridge.ps1 -NoInstall
```

SQL troubleshooting:

```powershell
# Use this if you only want to start the app and skip SQL view/table setup.
.\start_talent_bridge.ps1 -SkipSql

# Use this if your SQL Server instance is SQL Express.
.\start_talent_bridge.ps1 -SqlServer ".\SQLEXPRESS"

# Use this if SQL Server authentication is configured instead of Windows auth.
.\start_talent_bridge.ps1 -SqlServer "localhost" -SqlUser "sa" -SqlPassword "your_password"
```

If you see `Named Pipes Provider` or `Login timeout expired`, SQL Server is not reachable at the configured server name.
Start the SQL Server service from an elevated PowerShell, then rerun the launcher:

```powershell
Start-Service MSSQLSERVER
```

URLs:

```text
Frontend: http://localhost:5173
Backend docs: http://localhost:8000/docs
```

Demo users:

```text
candidate@talentbridge.local / candidate123
recruiter@talentbridge.local / recruiter123
admin@talentbridge.local / admin123
```
