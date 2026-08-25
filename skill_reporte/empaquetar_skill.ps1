<#
.SYNOPSIS
    Empaqueta la skill reporte_loco_tequila en skill_reporte.zip
    excluyendo datos reales de cliente y todas las carpetas que contengan 'output'.
#>

[CmdletBinding()]
param (
    [string]$DestinationZip = "skill_reporte.zip",
    [string]$SourceDir = $PSScriptRoot
)

if ([string]::IsNullOrWhiteSpace($SourceDir)) {
    $SourceDir = (Get-Location).Path
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Empaquetando Skill: Loco Tequila -> $DestinationZip" -ForegroundColor Yellow
Write-Host " Directorio origen: $SourceDir" -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Cyan

# Eliminar zip previo si ya existe
$zipPath = Join-Path $SourceDir $DestinationZip
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
    Write-Host "[INFO] Archivo zip anterior eliminado." -ForegroundColor Gray
}

# Cargar ensamblado de compresión de .NET
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

# Abrir nuevo archivo ZIP
$zipArchive = [System.IO.Compression.ZipFile]::Open($zipPath, [System.IO.Compression.ZipArchiveMode]::Create)

# Patrones de exclusión
$excludeFolders = @("datos_reales_cliente", "*output*", ".git", "__pycache__", ".pytest_cache", ".ipynb_checkpoints", ".claude")
$excludeFiles = @($DestinationZip, "*.zip")

# Obtener todos los archivos recursivamente
$allFiles = Get-ChildItem -Path $SourceDir -Recurse -File

$count = 0
foreach ($file in $allFiles) {
    $relPath = $file.FullName.Substring($SourceDir.Length).TrimStart("\", "/")
    
    # Comprobar si pertenece a una carpeta excluida
    $skip = $false
    $pathParts = $relPath.Split([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
    
    # Evaluar carpetas padre
    if ($pathParts.Length -gt 1) {
        foreach ($part in $pathParts[0..($pathParts.Length - 2)]) {
            foreach ($pattern in $excludeFolders) {
                if ($part -like $pattern -or $part.ToLower() -like $pattern.ToLower()) {
                    $skip = $true
                    break
                }
            }
            if ($skip) { break }
        }
    }
    
    # Evaluar nombre de archivo
    if (-not $skip) {
        foreach ($fPattern in $excludeFiles) {
            if ($file.Name -like $fPattern) {
                $skip = $true
                break
            }
        }
    }
    
    if (-not $skip) {
        # Normalizar separador a '/' para compatibilidad universal
        $entryName = $relPath.Replace("\", "/")
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
            $zipArchive,
            $file.FullName,
            $entryName,
            [System.IO.Compression.CompressionLevel]::Optimal
        ) | Out-Null
        $count++
    }
}

$zipArchive.Dispose()

$zipItem = Get-Item $zipPath
$sizeMb = [Math]::Round($zipItem.Length / 1MB, 2)
$sizeKb = [Math]::Round($zipItem.Length / 1KB, 1)

Write-Host "============================================================" -ForegroundColor Green
Write-Host " [OK] Empaquetado finalizado con éxito!" -ForegroundColor Green
Write-Host " Archivo generado  : $zipPath" -ForegroundColor White
Write-Host " Archivos incluidos: $count" -ForegroundColor White
Write-Host " Tamaño final       : $sizeMb MB ($sizeKb KB)" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Green
