param(
    [switch]$SkipSql,
    [switch]$SkipDashboard,
    [switch]$SkipBrowser,
    [switch]$NoInstall,
    [switch]$RunChecks,
    [string]$SqlServer = "localhost",
    [string]$SqlDatabase = "DW_DataJobs",
    [string]$SqlUser,
    [string]$SqlPassword
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent (Split-Path -Parent $ScriptDir)
$BackendDir = Join-Path $Root "Backend\TalentBridgeAPI"
$FrontendDir = Join-Path $Root "Frontend\TalentBridgeWeb"
$DashboardPath = Join-Path $Root "BI\PowerBI\Mission D'entreprise.pbix"
$SqlDir = Join-Path $Root "DataPlatform\Warehouse\views"

function Write-Step($Message) {
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Write-Ok($Message) {
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Warn($Message) {
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Test-Command($Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Test-PythonModule($Name) {
    $Script = "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('$Name') else 1)"
    $null = & python -c $Script 2>$null
    return $LASTEXITCODE -eq 0
}

function Get-SqlcmdAuthArgs {
    if ([string]::IsNullOrWhiteSpace($SqlUser)) {
        return @("-E")
    }

    if ([string]::IsNullOrWhiteSpace($SqlPassword)) {
        throw "SqlPassword is required when SqlUser is provided."
    }

    return @("-U", $SqlUser, "-P", $SqlPassword)
}

function Test-SqlServerConnection {
    param(
        [string[]]$AuthArgs
    )

    $ConnectionArgs = @("-S", $SqlServer, "-d", $SqlDatabase) + $AuthArgs + @(
        "-l", "5",
        "-b",
        "-Q", "SET NOCOUNT ON; SELECT 1 AS ok;"
    )

    $Output = & sqlcmd @ConnectionArgs 2>&1
    $SqlExitCode = $LASTEXITCODE
    if ($SqlExitCode -eq 0) {
        return $true
    }

    Write-Warn "Cannot connect to SQL Server '$SqlServer' database '$SqlDatabase'."
    if ($Output) {
        $Output | Select-Object -First 4 | ForEach-Object {
            Write-Warn $_.ToString()
        }
    }

    if ($SqlServer -eq "localhost" -or $SqlServer -eq ".") {
        $LocalService = Get-Service -Name MSSQLSERVER -ErrorAction SilentlyContinue
        if ($LocalService -and $LocalService.Status -ne "Running") {
            Write-Warn "Local SQL Server service MSSQLSERVER is $($LocalService.Status). Start it from an elevated PowerShell: Start-Service MSSQLSERVER"
        }
    }

    Write-Warn "If you use SQL Express, rerun with: .\start_talent_bridge.ps1 -SqlServer '.\SQLEXPRESS'"
    Write-Warn "To start the app without applying SQL scripts, rerun with: .\start_talent_bridge.ps1 -SkipSql"
    return $false
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor DarkCyan
Write-Host "         Talent Bridge Launcher" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor DarkCyan
Write-Host "Root: $Root"

if (-not (Test-Path $BackendDir)) {
    throw "Backend directory not found: $BackendDir"
}

if (-not (Test-Path $FrontendDir)) {
    throw "Frontend directory not found: $FrontendDir"
}

if (-not (Test-Command python)) {
    throw "Python was not found in PATH. Install Python or add it to PATH."
}

if (-not (Test-Command npm)) {
    throw "npm was not found in PATH. Install Node.js first."
}

$SqlAvailable = $false

if (-not $SkipSql) {
    Write-Step "Applying SQL Server views/tables"
    if (Test-Command sqlcmd) {
        $SqlAuthArgs = @(Get-SqlcmdAuthArgs)
        $SqlAvailable = Test-SqlServerConnection -AuthArgs $SqlAuthArgs

        if (-not $SqlAvailable) {
            Write-Warn "SQL preparation skipped because SQL Server is not reachable."
        } else {
            $SqlScripts = @(
                "01_create_vw_job_matching.sql",
                "02_create_cv_analysis_tables.sql",
                "03_create_cv_bi_views.sql",
                "04_create_vw_ml_jobs.sql",
                "05_create_vw_ml_salary_training.sql",
                "06_create_vw_ml_classification_training.sql",
                "07_create_vw_ml_segmentation_training.sql"
            )

            foreach ($ScriptName in $SqlScripts) {
                $ScriptPath = Join-Path $SqlDir $ScriptName
                if (Test-Path $ScriptPath) {
                    Write-Host "Running $ScriptName"
                    $SqlScriptArgs = @("-S", $SqlServer, "-d", $SqlDatabase) + $SqlAuthArgs + @("-b", "-i", $ScriptPath)
                    $Output = & sqlcmd @SqlScriptArgs 2>&1
                    $SqlExitCode = $LASTEXITCODE
                    if ($Output) {
                        $Output | Out-Host
                    }
                    if ($SqlExitCode -ne 0) {
                        throw "SQL script failed: $ScriptName"
                    }
                } else {
                    Write-Warn "Missing SQL script: $ScriptPath"
                }
            }
            Write-Ok "SQL preparation finished"
        }
    } else {
        Write-Warn "sqlcmd not found. Skipping SQL preparation. Run SQL scripts manually if needed."
    }
} else {
    Write-Warn "SQL preparation skipped"
}

if ($RunChecks) {
    Write-Step "Running verification checks"
    Push-Location $Root
    python -m compileall -q "Backend\TalentBridgeAPI" "NLP" "DocumentAI" "Recommendation" "MachineLearning" "Tests"
    if (-not $?) { throw "Python compile check failed" }
    python "Tests\smoke\test_demo_logic.py"
    if (-not $?) { throw "AI smoke test failed" }
    python "Tests\smoke\test_platform_workflows.py"
    if (-not $?) { throw "Platform workflow smoke test failed" }
    if (-not $SkipSql) {
        if (-not $SqlAvailable) {
            Write-Warn "SQL view integration check skipped because SQL Server is not reachable."
        } else {
            python "Tests\integration\test_sql_ml_views.py"
            if (-not $?) { throw "SQL view integration check failed" }
        }
    }
    Pop-Location
    Write-Ok "Verification checks passed"
}

if (-not $NoInstall) {
    Write-Step "Checking backend dependencies"
    $BackendDependencies = @(
        @{ Module = "fastapi"; Package = "fastapi>=0.100.0" },
        @{ Module = "uvicorn"; Package = "uvicorn[standard]>=0.23.0" },
        @{ Module = "multipart"; Package = "python-multipart>=0.0.6" },
        @{ Module = "fitz"; Package = "pymupdf>=1.23.0" },
        @{ Module = "deep_translator"; Package = "deep-translator>=1.11.0" },
        @{ Module = "langdetect"; Package = "langdetect>=1.0.9" }
    )
    $MissingBackendPackages = @()
    foreach ($Dependency in $BackendDependencies) {
        if (-not (Test-PythonModule $Dependency.Module)) {
            $MissingBackendPackages += $Dependency.Package
        }
    }
    if ($MissingBackendPackages.Count -gt 0) {
        Write-Host "Missing backend packages. Running pip install..."
        & python -m pip install @MissingBackendPackages
        if (-not $?) { throw "Backend dependency install failed" }
    } else {
        Write-Ok "Backend dependencies already installed"
    }

    Write-Step "Checking frontend dependencies"
    $NodeModules = Join-Path $FrontendDir "node_modules"
    if (-not (Test-Path $NodeModules)) {
        Write-Host "node_modules not found. Running npm install..."
        Push-Location $FrontendDir
        npm install
        Pop-Location
    } else {
        Write-Ok "Frontend dependencies already installed"
    }
} else {
    Write-Warn "Dependency install skipped"
}

Write-Step "Starting FastAPI backend"
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-Command", "python run_server.py serve"
) -WorkingDirectory $BackendDir -WindowStyle Normal
Write-Ok "Backend starting at http://localhost:8000"

Start-Sleep -Seconds 3

Write-Step "Starting Vue frontend"
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-Command", "npm run dev"
) -WorkingDirectory $FrontendDir -WindowStyle Normal
Write-Ok "Frontend starting at http://localhost:5173"

Start-Sleep -Seconds 3

if (-not $SkipDashboard) {
    Write-Step "Opening Power BI dashboard"
    if (Test-Path $DashboardPath) {
        Invoke-Item $DashboardPath
        Write-Ok "Dashboard opened: $DashboardPath"
    } else {
        Write-Warn "Power BI dashboard not found: $DashboardPath"
    }
} else {
    Write-Warn "Dashboard opening skipped"
}

if (-not $SkipBrowser) {
    Write-Step "Opening browser"
    Start-Process "http://localhost:5173"
    Start-Process "http://localhost:8000/docs"
    Write-Ok "Opened Talent Bridge frontend and API docs"
} else {
    Write-Warn "Browser opening skipped"
}

Write-Host ""
Write-Host "Talent Bridge is starting." -ForegroundColor Green
Write-Host "Frontend:  http://localhost:5173" -ForegroundColor Green
Write-Host "Backend:   http://localhost:8000" -ForegroundColor Green
Write-Host "API docs:  http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Demo users:" -ForegroundColor Green
Write-Host "  candidate@talentbridge.local / candidate123" -ForegroundColor Green
Write-Host "  recruiter@talentbridge.local / recruiter123" -ForegroundColor Green
Write-Host "  admin@talentbridge.local / admin123" -ForegroundColor Green
Write-Host ""
Write-Host "Close the backend/frontend PowerShell windows to stop the app." -ForegroundColor Yellow
