[CmdletBinding()]
param(
    [switch]$NoEditable
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot

$installArguments = @('-m', 'pip', 'install', '--no-warn-script-location')
if (-not $NoEditable) {
    $installArguments += '-e'
}
$installArguments += $ProjectRoot

& python @installArguments
if ($LASTEXITCODE -ne 0) {
    throw "Package installation failed with exit code $LASTEXITCODE."
}

$ScriptsDirectory = (& python -c "import sysconfig; print(sysconfig.get_path('scripts'))").Trim()
if (-not (Test-Path -LiteralPath $ScriptsDirectory -PathType Container)) {
    throw "Python reported a missing Scripts directory: $ScriptsDirectory"
}

$UserPath = [Environment]::GetEnvironmentVariable('Path', 'User')
$Entries = @($UserPath -split ';' | Where-Object { $_ })
$NormalizedScripts = $ScriptsDirectory.TrimEnd('\')
$AlreadyPresent = $Entries | Where-Object { $_.TrimEnd('\') -ieq $NormalizedScripts }

if (-not $AlreadyPresent) {
    $NewUserPath = (($Entries + $ScriptsDirectory) -join ';')
    [Environment]::SetEnvironmentVariable('Path', $NewUserPath, 'User')
    Write-Host "Added to your user PATH: $ScriptsDirectory"
    Write-Host 'Open a new terminal for the persisted PATH change to take effect.'
} else {
    Write-Host "Already on your user PATH: $ScriptsDirectory"
}

if (-not (($env:Path -split ';') | Where-Object { $_.TrimEnd('\') -ieq $NormalizedScripts })) {
    $env:Path = "$env:Path;$ScriptsDirectory"
}

$Launcher = Join-Path $ScriptsDirectory 'tree-age.exe'
if (-not (Test-Path -LiteralPath $Launcher -PathType Leaf)) {
    throw "Installation completed but the launcher was not found: $Launcher"
}

& $Launcher --help | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "The tree-age launcher did not start successfully."
}
Write-Host 'tree-age is installed and ready.'
