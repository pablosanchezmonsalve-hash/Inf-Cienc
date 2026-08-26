# Candidatos de ORCID por afiliación declarada (T-19) — asistente para Windows.
#
# POR QUÉ EXISTE
#   Igual que consultar-scopus.ps1: encadenar los pasos a mano falla de un
#   modo que no dice qué salió mal. Este script prueba la lógica primero,
#   pide las credenciales de ORCID de forma visible (ver mas abajo por qué),
#   y sólo entonces consulta el registro público.
#
# QUÉ HACE ESTE PENDIENTE (T-19)
#   Busca en el registro público de ORCID a quien declara "Universidad Finis
#   Terrae" como afiliación, y lo cruza contra las firmas del corpus que
#   todavía no tienen ORCID asignado. Es la única vía que alcanza a alguien
#   sin ninguna publicación con DOI --las otras dos vías (Crossref, ORCID por
#   DOI) exigen una obra compartida que ancle la coincidencia.
#
#   Por eso NO asigna nada solo: dos homónimos en la misma universidad son
#   indistinguibles por este método. Deja candidatos en
#   internal\orcid_candidatos_afiliacion.csv para revisión humana --
#   exactamente la cola "Candidato por afiliación" de make revision.
#
# USO
#   Clic derecho sobre este archivo -> «Ejecutar con PowerShell»
#   o, desde una consola:  .\scripts\ampliar-orcid-afiliacion.ps1

$ErrorActionPreference = 'Stop'

function Titulo($t) {
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor DarkCyan
    Write-Host "  $t" -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor DarkCyan
}
function Ok($t)    { Write-Host "  [OK]    $t" -ForegroundColor Green }
function Aviso($t) { Write-Host "  [!]     $t" -ForegroundColor Yellow }
function Malo($t)  { Write-Host "  [ERROR] $t" -ForegroundColor Red }

Titulo "Candidatos de ORCID por afiliacion (T-19)"

# ── 1. Situarse en la raíz del proyecto ──────────────────────────────────────
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz
Write-Host "  Proyecto: $raiz"

if (-not (Test-Path "src\enrich\orcid_afiliacion.py")) {
    Malo "No encuentro src\enrich\orcid_afiliacion.py"
    Write-Host "  Este script debe estar dentro de la carpeta del proyecto, en scripts\."
    Read-Host "`n  Enter para cerrar"; exit 1
}
Ok "Carpeta del proyecto correcta"

# ── 2. Python ────────────────────────────────────────────────────────────────
function Probar-Python($cmd) {
    try {
        $v = & $cmd --version 2>&1 | Out-String
    } catch { return $null }
    if ($LASTEXITCODE -ne 0) { return $null }
    if ($v -notmatch 'Python\s+3\.\d+') { return $null }
    return $v.Trim()
}

$py = $null; $ver = $null
foreach ($cmd in @('py', 'python', 'python3')) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { continue }
    $v = Probar-Python $cmd
    if ($v) { $py = $cmd; $ver = $v; break }
}

if (-not $py) {
    $candidatos = @(
        "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe"
        "$env:ProgramFiles\Python3*\python.exe"
        "${env:ProgramFiles(x86)}\Python3*\python.exe"
        "C:\Python3*\python.exe"
    )
    foreach ($patron in $candidatos) {
        foreach ($ruta in (Get-ChildItem $patron -ErrorAction SilentlyContinue |
                           Sort-Object FullName -Descending)) {
            $v = Probar-Python $ruta.FullName
            if ($v) { $py = $ruta.FullName; $ver = $v; break }
        }
        if ($py) { break }
    }
    if ($py) { Aviso "Python no esta en el PATH; se usara la ruta completa" }
}

if (-not $py) {
    Malo "No encuentro Python instalado"
    Write-Host ""
    Write-Host "  Instalelo asi:" -ForegroundColor Cyan
    Write-Host "    1. Abra https://www.python.org/downloads/"
    Write-Host "    2. Descargue la version para Windows y ejecutela."
    Write-Host "    3. IMPORTANTE: en la PRIMERA pantalla marque"
    Write-Host "       'Add python.exe to PATH' antes de pulsar Install." -ForegroundColor Cyan
    Write-Host "    4. Cierre esta ventana, abra una nueva, y vuelva a ejecutar."
    Read-Host "`n  Enter para cerrar"; exit 1
}
Ok "Python encontrado: $ver"

# ── 3. Dependencias ──────────────────────────────────────────────────────────
& $py -c "import pandas, yaml" 2>$null
if ($LASTEXITCODE -ne 0) {
    Aviso "Faltan dependencias. Instalando..."
    & $py -m pip install -r requirements.txt --quiet
    if ($LASTEXITCODE -ne 0) { Malo "Fallo la instalacion"; Read-Host "`n  Enter"; exit 1 }
}
Ok "Dependencias listas"

# ── 4. Autoprueba sin red ────────────────────────────────────────────────────
Titulo "Paso 1 de 3 - Probar la logica (sin internet, sin credenciales)"
& $py src\enrich\orcid_afiliacion.py --test
if ($LASTEXITCODE -ne 0) {
    Malo "La autoprueba fallo. El problema no son las credenciales."
    Read-Host "`n  Enter para cerrar"; exit 1
}

# ── 5. Datos de la auditoría ─────────────────────────────────────────────────
Titulo "Paso 2 de 3 - Preparar los datos"
if (Test-Path "internal\matching_log.csv") {
    Ok "Los datos de la auditoria ya estan"
} else {
    Write-Host "  Ejecutando la auditoria (tarda menos de un minuto)..."
    & $py src\audit\run_all.py | Out-Null
    if ($LASTEXITCODE -ne 0) { Malo "Fallo la auditoria"; Read-Host "`n  Enter"; exit 1 }
    Ok "Auditoria completada"
}

# ── 6. Credenciales ──────────────────────────────────────────────────────────
# Mismas credenciales que verificar-orcid.ps1 (ORCID_CLIENT_ID/SECRET), y en
# texto visible por el mismo motivo: pegar dentro de un prompt oculto
# (-AsSecureString) fallo silenciosamente en la consola de un usuario real
# (D-257, SESSION_NOTES.md). Si ya las definio en esta misma ventana, no
# vuelve a pedirlas.
Titulo "Paso 3 de 3 - Credenciales de ORCID y consulta"
Write-Host "  Se obtienen gratis en https://orcid.org -> Developer tools."
Write-Host "  Se piden en texto visible. No se guardan en ningun archivo."
Write-Host ""

if (-not $env:ORCID_CLIENT_ID) {
    $env:ORCID_CLIENT_ID = (Read-Host "  Client ID (APP-...)").Trim()
}
if (-not $env:ORCID_CLIENT_SECRET) {
    $env:ORCID_CLIENT_SECRET = (Read-Host "  Client Secret").Trim()
}
if (-not $env:ORCID_CLIENT_ID -or -not $env:ORCID_CLIENT_SECRET) {
    Malo "Faltan credenciales"; Read-Host "`n  Enter"; exit 1
}
if ($env:ORCID_CLIENT_ID.Length -lt 10 -or $env:ORCID_CLIENT_SECRET.Length -lt 10) {
    Malo "Una credencial capturada es demasiado corta. Probablemente el pegado fallo."
    Write-Host "  Vuelva a ejecutar el script e intente escribiendola directamente," -ForegroundColor Yellow
    Write-Host "  o pegue con clic derecho en vez de Ctrl+V." -ForegroundColor Yellow
    Read-Host "`n  Enter para cerrar"; exit 1
}
Ok "Credenciales cargadas en esta sesion"

& $py src\enrich\orcid_afiliacion.py
$exito = ($LASTEXITCODE -eq 0)

if (-not $exito) {
    Malo "La consulta fallo. Lea el mensaje de arriba: dice que paso y que hacer."
    Read-Host "`n  Enter para cerrar"; exit 1
}

Titulo "Terminado"
Write-Host "  Resultado en: internal\orcid_candidatos_afiliacion.csv"
Write-Host ""
Write-Host "  Esto NO asigna ningun ORCID solo: son candidatos para revisar," -ForegroundColor Cyan
Write-Host "  igual que la cola 'Candidato por afiliacion' de make revision." -ForegroundColor Cyan
Write-Host "  Corra scripts\revisar-identidad.ps1 para decidir sobre ellos." -ForegroundColor Cyan
Write-Host ""
Write-Host "  Para incorporar el resultado de la consulta al proyecto:" -ForegroundColor Cyan
Write-Host "    git add internal\orcid_candidatos_afiliacion.csv"
Write-Host "    git commit -m `"T-19: candidatos de ORCID por afiliacion actualizados`""
Write-Host "    git push"

Read-Host "`n  Enter para cerrar"
