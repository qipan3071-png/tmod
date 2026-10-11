# ============================================================================
#  按时开工：可选地等到 DeepSeek 非高峰后再跑一轮完整验收+装机
#
#  高峰时段是 DeepSeek API 的计价窗口，不是 Cursor 的（见 开发说明.md「〇」）：
#    工作日北京 09:00-12:00 与 14:00-18:00（UTC 01:00-04:00、06:00-10:00）；
#    周末和中国法定节假日全天非高峰。旧文档的 08:00 比官网早一小时，已作废。
#
#  本脚本只做本机 tModLoader 流水线（不写代码、不消耗 DeepSeek token），
#  因此默认不等待高峰。只有当前会话走 DeepSeek、需要避开其 2 倍价时，
#  才加 -WaitForDeepSeekOffPeak。
#
#  用法：powershell -NoProfile -ExecutionPolicy Bypass -File tools\scheduled_work.ps1
#  日志：E:\开发\.scheduled-work.log
# ============================================================================
param(
    [string]$LogFile = 'E:\开发\.scheduled-work.log',
    [int]$PollSeconds = 300,
    [switch]$WaitForDeepSeekOffPeak
)

function Write-Log($message) {
    $line = '[{0}] {1}' -f (Get-Date -Format 'yyyy/MM/dd HH:mm:ss'), $message
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
}

function Test-DeepSeekPeak([datetime]$time) {
    # DeepSeek official: Mon-Fri 01:00-04:00 and 06:00-10:00 UTC = Beijing 09:00-12:00 and 14:00-18:00.
    # Weekends are off-peak. Chinese public holidays are also off-peak; this helper only skips Sat/Sun.
    if ($time.DayOfWeek -eq 'Saturday' -or $time.DayOfWeek -eq 'Sunday') {
        return $false
    }

    $hour = $time.Hour
    return (($hour -ge 9 -and $hour -lt 12) -or ($hour -ge 14 -and $hour -lt 18))
}

if ($WaitForDeepSeekOffPeak) {
    Write-Log 'scheduled_work started; waiting for DeepSeek off-peak (weekday Beijing 09-12 and 14-18).'

    while (Test-DeepSeekPeak (Get-Date)) {
        Start-Sleep -Seconds $PollSeconds
    }
} else {
    Write-Log 'scheduled_work started; not waiting on DeepSeek peak (local pipeline, no DeepSeek tokens).'
}

Write-Log ('window open at {0} - probing build first' -f (Get-Date -Format 'HH:mm:ss'))

# 探测编译：只有干净才继续（避免撞上代理的在制品）
$probeMods = Join-Path 'E:\开发\.tml-build-w17' 'Mods'
New-Item -ItemType Directory -Force $probeMods | Out-Null

foreach ($name in @('InnoVault.tmod', 'WastelandSoulCN.tmod')) {
    $src = Join-Path 'E:\开发\.tml-build\Mods' $name
    $dst = Join-Path $probeMods $name

    if ((Test-Path $src) -and -not (Test-Path $dst)) {
        Copy-Item $src $dst -Force -ErrorAction SilentlyContinue
    }
}

$probe = & dotnet 'e:\steam\steamapps\common\tModLoader\tModLoader.dll' -build 'E:\开发\WastelandSoul' -tmlsavedirectory 'E:\开发\.tml-build-w17' 2>&1
$probeLine = ($probe | Select-String -Pattern 'Compilation finished' | Select-Object -Last 1)

if (-not ($probeLine -match '0 errors and 0 warnings')) {
    Write-Log ('in-progress tree (build not clean): {0} - skip this round.' -f $probeLine)
    exit 0
}

Write-Log 'tree compiles clean - running full pipeline'

$pipeline = & powershell -NoProfile -ExecutionPolicy Bypass -File 'E:\开发\tools\ws_pipeline.ps1' -WaitForGame 900 2>&1
$result = ($pipeline | Select-String -Pattern 'PIPELINE RESULT' | Select-Object -Last 1)

Add-Content -Path $LogFile -Value ($pipeline | Select-Object -Last 12) -Encoding UTF8
Write-Log ('pipeline done: {0}' -f $result)

& 'C:\Users\p老师\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe' 'E:\开发\tools\make_handoff_report.py' 2>&1 |
    Add-Content -Path $LogFile -Encoding UTF8

Write-Log 'handoff report refreshed; scheduled_work finished.'
