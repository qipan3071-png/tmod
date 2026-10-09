# ============================================================================
#  One-shot 07:00 shutdown (requested by the player).
#
#  Behaviour: issues `shutdown /s /t 120` (2 minutes of warning) and then deletes
#  itself so a later reboot cannot re-trigger it.
#
#  Cancel:
#    * just this shutdown:  shutdown /a
#    * the whole task:      schtasks /Delete /TN "WastelandSoul0700Shutdown" /F
#
#  Kept ASCII-only on purpose (PowerShell 5.1 without BOM mis-reads Chinese).
# ============================================================================
param(
    [int]$GraceSeconds = 120,
    [string]$LogFile = 'E:\开发\.shutdown-0700.log'
)

$line = '[{0}] 07:00 shutdown triggered (grace {1}s).' -f (Get-Date -Format 'yyyy/MM/dd HH:mm:ss'), $GraceSeconds
Add-Content -Path $LogFile -Value $line -Encoding UTF8

shutdown.exe /s /t $GraceSeconds /c 'WastelandSoul: scheduled 07:00 shutdown (run "shutdown /a" to abort)'

schtasks.exe /Delete /TN 'WastelandSoul0700Shutdown' /F 2>$null | Out-Null
Add-Content -Path $LogFile -Value ('[{0}] task removed.' -f (Get-Date -Format 'yyyy/MM/dd HH:mm:ss')) -Encoding UTF8
