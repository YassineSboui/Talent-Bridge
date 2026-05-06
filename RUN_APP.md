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
