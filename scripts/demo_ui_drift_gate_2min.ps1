param(
  [string]$OutRoot = "runs/demo_ui",
  [string]$TaxonomyPath = "taxonomy/tone_taxonomy.v1.json",
  [string]$GoldsetPath = "data/goldset.jsonl",
  [int]$ApiPort = 8081,
  [int]$UiPort = 8090,
  [switch]$SkipServers
)

$ErrorActionPreference = "Stop"

function Invoke-ToneSightJson {
  param(
    [string[]]$CliArgs,
    [int[]]$AllowedExitCodes = @(0)
  )
  $raw = & python -m tonesight_ns8.cli @CliArgs
  if ($AllowedExitCodes -notcontains $LASTEXITCODE) {
    throw "Command failed: python -m tonesight_ns8.cli $($CliArgs -join ' ')"
  }
  $parsed = $raw | ConvertFrom-Json
  if ($null -ne $parsed -and -not ($parsed.PSObject.Properties.Name -contains "exit_code")) {
    $parsed | Add-Member -NotePropertyName "exit_code" -NotePropertyValue $LASTEXITCODE
  }
  return $parsed
}

Write-Host "[1/6] Baseline eval"
$baseline = Invoke-ToneSightJson @(
  "eval",
  "--goldset", $GoldsetPath,
  "--out-root", $OutRoot,
  "--taxonomy", $TaxonomyPath,
  "--threshold-l1", "3"
)
$runA = Join-Path $OutRoot $baseline.run_id

Write-Host "[2/6] Candidate eval (intentional stricter threshold for gate regression)"
$candidate = Invoke-ToneSightJson @(
  "eval",
  "--goldset", $GoldsetPath,
  "--out-root", $OutRoot,
  "--taxonomy", $TaxonomyPath,
  "--threshold-l1", "0"
)
$runB = Join-Path $OutRoot $candidate.run_id

Write-Host "[3/6] Compare (write artifact)"
$compare = Invoke-ToneSightJson @(
  "compare", $runA, $runB,
  "--top-n", "10",
  "--write"
)

Write-Host "[4/6] Gate (expect fail/regressed)"
$gate = Invoke-ToneSightJson @(
  "gate",
  "--run-a", $runA,
  "--run-b", $runB
) -AllowedExitCodes @(0, 2, 3)

$compareDir = Join-Path (Join-Path (Join-Path $runB "comparisons") (Split-Path $runA -Leaf)) ""
$gateArtifactPath = Join-Path $compareDir "gate_result.json"
New-Item -ItemType Directory -Path $compareDir -Force | Out-Null
$gateJson = $gate | ConvertTo-Json -Depth 50
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($gateArtifactPath, $gateJson + "`n", $utf8NoBom)

Write-Host "[5/6] Build index artifacts for UI"
Invoke-ToneSightJson @("index-runs", "--out-root", $OutRoot) | Out-Null
Invoke-ToneSightJson @("index-runs-json", "--out-root", $OutRoot) | Out-Null

$apiUrl = "http://127.0.0.1:$ApiPort"
$uiUrl = "http://127.0.0.1:$UiPort"
$runAId = Split-Path $runA -Leaf
$runBId = Split-Path $runB -Leaf
$uiDetailUrl = "$uiUrl/index.html?run=$runBId&panel=detail"
$uiCompareUrl = "$uiUrl/index.html?run=$runBId&panel=compare"
$uiGateUrl = "$uiUrl/index.html?run=$runBId&panel=gate"

if (-not $SkipServers) {
  Write-Host "[6/6] Start static API + UI servers"
  $apiProc = Start-Process -FilePath python -ArgumentList @("server/app.py", "--runs-root", $OutRoot, "--host", "127.0.0.1", "--port", "$ApiPort") -PassThru
  $uiProc = Start-Process -FilePath python -ArgumentList @("-m", "http.server", "$UiPort", "--directory", "ui") -PassThru
}

Write-Host ""
Write-Host "Demo artifacts:"
Write-Host "  baseline_run: $runA"
Write-Host "  candidate_run: $runB"
Write-Host "  compare_summary: $(Join-Path $compareDir 'compare_summary.json')"
Write-Host "  gate_result: $gateArtifactPath"
Write-Host "  index_json: $(Join-Path $OutRoot 'index.json')"
Write-Host ""
Write-Host "Gate decision: $($gate.decision) (exit_code=$($gate.exit_code))"
Write-Host ""
Write-Host "Endpoints:"
Write-Host "  API health: $apiUrl/health"
Write-Host "  API index:  $apiUrl/api/index"
Write-Host "  Compare:    $apiUrl/api/compare/$runAId/$runBId"
Write-Host "  Gate:       $apiUrl/api/gate/$runAId/$runBId"
Write-Host "  UI:         $uiUrl/index.html"
Write-Host "  UI detail:  $uiDetailUrl"
Write-Host "  UI compare: $uiCompareUrl"
Write-Host "  UI gate:    $uiGateUrl"

if (-not $SkipServers) {
  Write-Host ""
  Write-Host "Server processes:"
  Write-Host "  API PID: $($apiProc.Id)"
  Write-Host "  UI PID:  $($uiProc.Id)"
  Write-Host "Stop with:"
  Write-Host "  Stop-Process -Id $($apiProc.Id),$($uiProc.Id)"
}
