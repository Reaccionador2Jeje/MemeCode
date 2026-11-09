param(
    [ValidateSet("install", "update", "uninstall")]
    [string]$Action = "install"
)
$ErrorActionPreference = "Stop"
$Repo = "https://github.com/Reaccionador2Jeje/MemeCode.git"
$MemingoRepo = "https://github.com/Reaccionador2Jeje/Memingo.git"
$MemingoBranch = "feat/arch-aur-packaging"
$AppDir = if ($env:MEMECODE_HOME) { $env:MEMECODE_HOME } else { Join-Path $env:LOCALAPPDATA "MemeCode" }
$BinDir = Join-Path $env:LOCALAPPDATA "Programs\MemeCode\bin"
$Launcher = Join-Path $BinDir "memecode.cmd"
function Say([string]$Message) { Write-Host ""; Write-Host "[MemeCode] $Message" -ForegroundColor Cyan }
function Fail([string]$Message) { throw "[MemeCode] ERROR: $Message" }

if ($Action -eq "uninstall") {
    if (Test-Path $AppDir) {
        $answer = Read-Host "¿Desinstalar MemeCode de $AppDir? [y/N]"
        if ($answer -notin @("y", "Y", "yes", "YES")) { Say "Cancelado."; exit 0 }
        Remove-Item -Recurse -Force $AppDir
    }
    if (Test-Path $Launcher) { Remove-Item -Force $Launcher }
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath) {
        $parts = $userPath -split ";" | Where-Object { $_.TrimEnd("\") -ne $BinDir.TrimEnd("\") }
        [Environment]::SetEnvironmentVariable("Path", ($parts -join ";"), "User")
    }
    Say "MemeCode desinstalado. Tus proyectos y claves externas no se modificaron."
    exit 0
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Fail "No se encontró Git. Instala Git for Windows." }
$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) { $PythonCommand = "py"; $PythonArgs = @("-3") }
else {
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) { Fail "No se encontró Python 3. Instala Python 3 y activa Add Python to PATH." }
    $PythonCommand = $py.Source
    $PythonArgs = @()
}
New-Item -ItemType Directory -Force -Path (Split-Path $AppDir), $BinDir | Out-Null
if (Test-Path (Join-Path $AppDir ".git")) {
    Say "Actualizando MemeCode..."
    & git -C $AppDir pull --ff-only origin main
    if ($LASTEXITCODE -ne 0) { Fail "No se pudo actualizar. Revisa tus cambios locales." }
} elseif (Test-Path $AppDir) {
    Fail "$AppDir existe pero no es un repositorio Git. Muévelo o define MEMECODE_HOME."
} else {
    Say "Descargando MemeCode..."
    & git clone --depth 1 $Repo $AppDir
    if ($LASTEXITCODE -ne 0) { Fail "No se pudo clonar MemeCode." }
}
$tempDir = Join-Path ([IO.Path]::GetTempPath()) ("memecode-" + [guid]::NewGuid().ToString("N"))
try {
    New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
    Say "Descargando Memingo..."
    & git clone --depth 1 --branch $MemingoBranch $MemingoRepo (Join-Path $tempDir "Memingo")
    if ($LASTEXITCODE -ne 0) { Fail "No se pudo descargar Memingo." }
    $venvPython = Join-Path $AppDir ".venv\Scripts\python.exe"
    if (-not (Test-Path $venvPython)) {
        Say "Creando entorno Python aislado..."
        & $PythonCommand @PythonArgs -m venv (Join-Path $AppDir ".venv")
        if ($LASTEXITCODE -ne 0) { Fail "No se pudo crear el entorno virtual." }
    }
    Say "Instalando o actualizando Memingo..."
    & $venvPython -m pip install --upgrade (Join-Path $tempDir "Memingo")
    if ($LASTEXITCODE -ne 0) { Fail "No se pudo instalar Memingo." }
    & $venvPython -m py_compile (Join-Path $AppDir "runtime\agent.py") (Join-Path $AppDir "runtime\host_bridge.py")
    if ($LASTEXITCODE -ne 0) { Fail "Falló la comprobación de Python." }
    $memingoExe = Join-Path $AppDir ".venv\Scripts\memingo.exe"
    if (-not (Test-Path $memingoExe)) { Fail "Memingo no quedó disponible en el entorno virtual." }
    Copy-Item -Force (Join-Path $PSScriptRoot "install.ps1") (Join-Path $AppDir "install.ps1")
    @'
@echo off
setlocal
set "APP_DIR=%LOCALAPPDATA%\MemeCode"
if defined MEMECODE_HOME set "APP_DIR=%MEMECODE_HOME%"
set "PY=%APP_DIR%\.venv\Scripts\python.exe"
set "AGENT=%APP_DIR%\runtime\agent.py"
if not exist "%PY%" (
  echo MemeCode no esta instalado correctamente.
  exit /b 1
)
if /i "%~1"=="doctor" (
  "%PY%" --version
  "%APP_DIR%\.venv\Scripts\memingo.exe" --help >nul 2>&1 && echo Memingo: OK || echo Memingo: revisar
  "%PY%" -m py_compile "%AGENT%" "%APP_DIR%\runtime\host_bridge.py" && echo Python: OK
  if defined MEMECODE_API_KEY (echo API: clave presente en esta sesion) else (echo API: falta MEMECODE_API_KEY)
  exit /b
)
if /i "%~1"=="update" (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%APP_DIR%\install.ps1" -Action update
  exit /b %ERRORLEVEL%
)
if /i "%~1"=="uninstall" (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%APP_DIR%\install.ps1" -Action uninstall
  exit /b %ERRORLEVEL%
)
if /i "%~1"=="help" (
  echo Uso: memecode [doctor^|update^|uninstall^|tarea...]
  echo Sin argumentos abre el chat en la carpeta actual.
  exit /b 0
)
if "%~1"=="" (
  "%PY%" "%AGENT%" --workspace . --chat
) else (
  "%PY%" "%AGENT%" %*
)
exit /b %ERRORLEVEL%
'@ | Set-Content -Encoding ASCII $Launcher
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $pathParts = @()
    if ($userPath) { $pathParts = @($userPath -split ";" | Where-Object { $_ }) }
    if ($pathParts -notcontains $BinDir) {
        $pathParts += $BinDir
        [Environment]::SetEnvironmentVariable("Path", ($pathParts -join ";"), "User")
    }
    if (($env:Path -split ";") -notcontains $BinDir) { $env:Path += ";$BinDir" }
    Say "¡Instalación completada!"
    Say "Ejecuta: memecode"
    Say "Comprueba la instalación con: memecode doctor"
} finally {
    if (Test-Path $tempDir) { Remove-Item -Recurse -Force $tempDir }
}
