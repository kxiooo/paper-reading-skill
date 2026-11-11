# ============================================================
# OpenDataLoader PDF Preprocessing Script (Windows PowerShell)
# Usage: .\_meta\preprocess-pdf.ps1 <pdf-path> [--MergeTables]
# Output: _staging\parsed\<name>\<name>.md + images
#
# 工具路径解析优先级：
#   1. 环境变量 JAVA_BIN / OPENDATALOADER_JAR / PYTHON_BIN
#   2. PATH 中的 java / python
#   3. JAVA_HOME
#   4. 通过 python 自动定位 opendataloader-pdf 的 jar
# ============================================================

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$PdfPath,
    [switch]$MergeTables
)

$ErrorActionPreference = "Continue"

# ---------- Tool paths ----------
$JavaBin   = $env:JAVA_BIN
$JarPath   = $env:OPENDATALOADER_JAR
$PythonBin = $env:PYTHON_BIN

if (-not $PythonBin) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { $PythonBin = $cmd.Source }
}

if (-not $JavaBin) {
    $cmd = Get-Command java -ErrorAction SilentlyContinue
    if ($cmd) {
        $JavaBin = $cmd.Source
    }
    elseif ($env:JAVA_HOME) {
        $candidate = Join-Path $env:JAVA_HOME "bin\java.exe"
        if (Test-Path $candidate) { $JavaBin = $candidate }
    }
}

if (-not $JarPath -and $PythonBin) {
    $candidate = & $PythonBin -c "import opendataloader_pdf, pathlib; print(pathlib.Path(opendataloader_pdf.__file__).parent / 'jar' / 'opendataloader-pdf-cli.jar')" 2>$null
    if ($candidate -and (Test-Path $candidate)) { $JarPath = $candidate }
}

$VaultRoot = Resolve-Path "$PSScriptRoot\.."
$ScriptDir = $PSScriptRoot

# ---------- Validate ----------
if (-not (Test-Path $PdfPath)) {
    Write-Error "[ERROR] File not found: $PdfPath"
    exit 1
}
if (-not $JavaBin -or -not (Test-Path $JavaBin)) {
    Write-Error "[ERROR] Java not found. Set JAVA_BIN or JAVA_HOME (Java 17+ required)."
    exit 1
}
if (-not $JarPath -or -not (Test-Path $JarPath)) {
    Write-Error "[ERROR] OpenDataLoader JAR not found. Set OPENDATALOADER_JAR, or run: pip install opendataloader-pdf"
    exit 1
}

# ---------- Output paths ----------
$PdfBaseName = [System.IO.Path]::GetFileNameWithoutExtension($PdfPath)
$Slug = [regex]::Replace($PdfBaseName, '[^a-zA-Z0-9_\-]', '-') -replace '--+', '-' -replace '^-|-$', ''
$OutputDir = Join-Path $VaultRoot "_staging\parsed\$Slug"

Write-Host "============================================"
Write-Host "OpenDataLoader PDF Preprocessing (Windows)"
Write-Host "============================================"
Write-Host "PDF:     $PdfPath"
Write-Host "Output:  $OutputDir\"
Write-Host "Java:    $JavaBin"
Write-Host "JAR:     $JarPath"
Write-Host "Mode:    Local (deterministic, images inline or external)"
Write-Host "============================================"

New-Item -ItemType Directory -Path "$OutputDir\images" -Force | Out-Null

# Use a temp dir with an ASCII-only path to avoid Chinese-character issues with Java
$TempDir = "$env:TEMP\odlpdf-$Slug"
$TempPdf = "$TempDir\$Slug.pdf"
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
Copy-Item $PdfPath $TempPdf -Force

# Run OpenDataLoader via cmd.exe to avoid PowerShell native-command encoding issues
Write-Host "--------------------------------------------"
Write-Host "Running OpenDataLoader..."
$logFile = "$OutputDir\opendataloader.log"

$cmdLine = "`"$JavaBin`" -jar `"$JarPath`" --markdown-with-images -o `"$TempDir`" --content-safety-off all `"$TempPdf`""
$null = cmd /c $cmdLine 2> "$TempDir\stderr.log"
$exitCode = $LASTEXITCODE
Get-Content "$TempDir\stderr.log" -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "  [JAVA] $_" }
Write-Host "  [OK] OpenDataLoader process completed (exit code $exitCode)"

# Copy results from temp dir to output dir even if Java had warnings
Write-Host "  [COPY] Moving results to $OutputDir"
Get-ChildItem "$TempDir\*.md" -ErrorAction SilentlyContinue | Copy-Item -Destination $OutputDir -Force
Get-ChildItem "$TempDir\*.json" -ErrorAction SilentlyContinue | Copy-Item -Destination $OutputDir -Force

# Find and copy images (different versions use different names)
$ImgSrcDir = Get-ChildItem "$TempDir\*_images" -Directory -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $ImgSrcDir) { $ImgSrcDir = Get-ChildItem "$TempDir\images" -Directory -ErrorAction SilentlyContinue | Select-Object -First 1 }
if ($ImgSrcDir) {
    New-Item -ItemType Directory -Path "$OutputDir\images" -Force | Out-Null
    Get-ChildItem "$ImgSrcDir\*" -ErrorAction SilentlyContinue | Copy-Item -Destination "$OutputDir\images\" -Force
    # Fix image paths in markdown: replace temp path with local images/ path
    foreach ($mdFile in Get-ChildItem "$OutputDir\*.md") {
        $content = [System.IO.File]::ReadAllText($mdFile.FullName)
        $escapedTempPath = [regex]::Escape($ImgSrcDir.FullName)
        $content = $content -replace $escapedTempPath, "images"
        [System.IO.File]::WriteAllText($mdFile.FullName, $content, [System.Text.UTF8Encoding]::new($false))
    }
    Write-Host "  [IMAGES] Copied and paths fixed"
}
Remove-Item -Recurse -Force $TempDir -ErrorAction SilentlyContinue

# Check output
$MdFile = Get-ChildItem "$OutputDir\*.md" -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $MdFile) {
    Write-Host "[ERROR] No Markdown generated"
    exit 1
}
Write-Host "  [FILE] $($MdFile.FullName)"
Write-Host ""

# ---------- Optional enhancements ----------
if (-not $PythonBin -or -not (Test-Path $PythonBin)) {
    Write-Host "[WARN] Python not found; skipping table / formula / validation enhancements."
    Write-Host "=== Done! Output: $($MdFile.FullName) ==="
    exit 0
}

# Table enhancement: Docling pipe-table merge (optional)
if ($MergeTables) {
    $MergeScript = Join-Path $ScriptDir "merge-docling-tables.py"
    if (Test-Path $MergeScript) {
        Write-Host "--------------------------------------------"
        Write-Host "Docling table enhancement..."
        try {
            & $PythonBin $MergeScript $PdfPath $MdFile.FullName 2>&1 | ForEach-Object { "  $_" }
            Write-Host "  [OK] Tables converted"
        }
        catch {
            Write-Host "  [WARN] Table enhancement failed: $_"
        }
    }
    else {
        Write-Host "  merge-docling-tables.py not found, skipping."
    }
}

# Formula enhancement: Unicode math -> LaTeX
$LatexScript = Join-Path $ScriptDir "latex-formulas.py"
if (Test-Path $LatexScript) {
    Write-Host "--------------------------------------------"
    Write-Host "LaTeX formula enhancement (rule engine)..."
    try {
        & $PythonBin $LatexScript $MdFile.FullName 2>&1 | ForEach-Object { "  $_" }
        Write-Host "  [OK] Formulas converted"
    }
    catch {
        Write-Host "  [WARN] Formula enhancement failed: $_"
    }
}

# Quality validation
Write-Host "--------------------------------------------"
Write-Host "Quality validation..."
$ValidateScript = Join-Path $ScriptDir "validate-preprocess.py"
if (Test-Path $ValidateScript) {
    try {
        & $PythonBin $ValidateScript $MdFile.FullName 2>&1 | ForEach-Object { "  $_" }
        if ($LASTEXITCODE -ne 0) {
            Write-Host ""
            Write-Host "[ERROR] Validation failed - output may be incomplete."
            exit 1
        }
    }
    catch {
        Write-Host "  [WARN] Validation script failed: $_"
    }
}
else {
    Write-Host "  validate-preprocess.py not found, skipping validation."
}

Write-Host ""
Write-Host "=== Done! Output: $($MdFile.FullName) ==="
