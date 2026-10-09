# Read-only recon: dump the IL of Terraria.NPC.FindFrame / NPC.VanillaFindFrame /
# NPCLoader.FindFrame straight out of the tModLoader.dll that ships in the install.
#
#   E:\开发\tools\dump_findframe_il.ps1
#   E:\开发\tools\dump_findframe_il.ps1 -Out E:\开发\.tmp-3d\other.txt -Types Terraria.NPC
#
# Why this tool exists: "what frame numbers does vanilla actually walk on" must be
# MEASURED, never guessed. Batch 43 (2026-10-09) used it to pin down
# "vanilla town-NPC walk cycle = body frames 2..13, standing frame = 0" and to prove
# that tML calls VanillaFindFrame BEFORE the ModNPC.FindFrame override.
# Do not install ILSpy for this; Cecil + this script is enough.
#
# NOTE: this machine's PowerShell execution policy forbids running .ps1 directly
# ("running scripts is disabled on this system"), so always invoke it as:
#     powershell -NoProfile -ExecutionPolicy Bypass -File E:\开发\tools\dump_findframe_il.ps1
# Also keep this file pure ASCII: Windows PowerShell 5.1 mis-decodes UTF-8 .ps1
# files without a BOM (non-ASCII path literals turn into mojibake).
param(
    [string]$Assembly = 'E:\steam\steamapps\common\tModLoader\tModLoader.dll',
    [string]$Cecil    = 'E:\steam\steamapps\common\tModLoader\Libraries\mono.cecil\0.11.6\lib\netstandard2.0\Mono.Cecil.dll',
    [string]$Out      = '',
    [string[]]$Types  = @('Terraria.NPC', 'Terraria.ModLoader.NPCLoader'),
    [string[]]$Methods = @('FindFrame', 'VanillaFindFrame')
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrEmpty($Out)) {
    $repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
    $Out = Join-Path $repoRoot '.tmp-3d\findframe_il.txt'
}

Add-Type -Path $Cecil
$asm = [Mono.Cecil.AssemblyDefinition]::ReadAssembly($Assembly)

$lines = New-Object System.Collections.Generic.List[string]
$found = 0

foreach ($typeName in $Types) {
    $type = $asm.MainModule.GetType($typeName)
    if (-not $type) { $lines.Add("!! type not found: $typeName"); continue }

    foreach ($m in $type.Methods) {
        if ($Methods -notcontains $m.Name) { continue }
        $found++
        $params = ($m.Parameters | ForEach-Object { "$($_.ParameterType.FullName) $($_.Name)" }) -join ', '
        $lines.Add("==================== $typeName :: $($m.Name)($params) ====================")
        if (-not $m.HasBody) { $lines.Add('  <no body>'); continue }
        foreach ($v in $m.Body.Variables) { $lines.Add("  LOCAL V_$($v.Index) $($v.VariableType.FullName)") }
        foreach ($ins in $m.Body.Instructions) {
            $operand = if ($ins.Operand -ne $null) { $ins.Operand.ToString() } else { '' }
            $lines.Add(("  IL_{0:X4}: {1,-14} {2}" -f $ins.Offset, $ins.OpCode.Name, $operand))
        }
    }
}

$dir = Split-Path -Parent $Out
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
$lines | Set-Content -Encoding UTF8 -Path $Out
Write-Host ("wrote {0} lines ({1} methods) -> {2}" -f $lines.Count, $found, $Out)
