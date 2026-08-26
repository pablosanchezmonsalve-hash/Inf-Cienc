# Consulta a la API de Scopus para T-06 — asistente para Windows.
#
# POR QUÉ EXISTE
#   Igual que scripts\verificar-orcid.ps1: encadenar los pasos a mano falla de
#   un modo que no dice qué salió mal. Este script prueba la lógica primero,
#   pide la API Key de forma oculta y sólo entonces hace la consulta real.
#
#   La API Key no se escribe en ningún archivo, no queda en el historial de la
#   consola y no hay que pegarla en ninguna parte donde pueda quedar registrada.
#
# USO
#   Clic derecho sobre este archivo -> «Ejecutar con PowerShell»
#   o, desde una consola:  .\scripts\consultar-scopus.ps1

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

Titulo "Consulta a la API de Scopus (T-06)"

# ── 1. Situarse en la raíz del proyecto ──────────────────────────────────────
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz
Write-Host "  Proyecto: $raiz"

if (-not (Test-Path "src\enrich\scopus_api.py")) {
    Malo "No encuentro src\enrich\scopus_api.py"
    Write-Host "  Este script debe estar dentro de la carpeta del proyecto, en scripts\."
    Read-Host "`n  Enter para cerrar"; exit 1
}
Ok "Carpeta del proyecto correcta"

# ── 2. Python ────────────────────────────────────────────────────────────────
# Que el comando EXISTA no significa que funcione. Windows instala unos alias de
# ejecucion para `python` y `python3` que no son Python: son un atajo a la
# Microsoft Store y responden a --version con un mensaje de error.
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
    Write-Host "    3. IMPORTANTE: en la PRIMERA pantalla del instalador marque"
    Write-Host "       'Add python.exe to PATH' antes de pulsar Install." -ForegroundColor Cyan
    Write-Host "    4. Cierre esta ventana, abra una nueva, y vuelva a ejecutar"
    Write-Host "       este script."
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
# Antes de pedir la API Key: si la logica esta rota, el problema no es la
# credencial y no tiene sentido pedirla todavia.
Titulo "Paso 1 de 3 - Probar la logica (sin internet, sin credenciales)"
& $py src\enrich\scopus_api.py --test
if ($LASTEXITCODE -ne 0) {
    Malo "La autoprueba fallo. El problema no es la API Key."
    Read-Host "`n  Enter para cerrar"; exit 1
}

# ── 5. Credenciales ──────────────────────────────────────────────────────────
# Se pide en TEXTO VISIBLE, no oculto ("-AsSecureString"). No es descuido: se
# probó oculto primero y pegar (Ctrl+V) dentro de un prompt enmascarado falla
# en algunas consolas de Windows -- captura 1 caracter basura en vez del texto
# pegado, sin ningun aviso de error. Visible pero correcto es mejor que oculto
# y roto. Nadie mas ve esta ventana, y no queda en el historial de comandos
# (solo los comandos quedan ahi, no lo que se escribe como respuesta a
# Read-Host).
Titulo "Paso 2 de 3 - API Key de Scopus"
Write-Host "  Se pide en texto visible (pegar oculto falla en algunas consolas"
Write-Host "  de Windows). No se guarda en ningun archivo ni en el historial."
Write-Host ""

if (-not $env:SCOPUS_API_KEY) {
    $env:SCOPUS_API_KEY = (Read-Host "  API Key de Scopus").Trim()
}
if (-not $env:SCOPUS_API_KEY) {
    Malo "Falta la API Key"; Read-Host "`n  Enter"; exit 1
}
if ($env:SCOPUS_API_KEY.Length -lt 20) {
    Malo "La API Key capturada tiene $($env:SCOPUS_API_KEY.Length) caracteres; una clave de Elsevier tiene 32."
    Write-Host "  Probablemente el pegado fallo. Vuelva a ejecutar el script e intente" -ForegroundColor Yellow
    Write-Host "  escribiendola directamente, o pegue con clic derecho en vez de Ctrl+V." -ForegroundColor Yellow
    Read-Host "`n  Enter para cerrar"; exit 1
}
Ok "API Key cargada en esta sesion ($($env:SCOPUS_API_KEY.Length) caracteres)"

if (-not $env:SCOPUS_INSTTOKEN) {
    $r = Read-Host "  ¿Tiene tambien un Institutional Token (insttoken)? (s/n)"
    if ($r -match '^[sSyY]') {
        $env:SCOPUS_INSTTOKEN = (Read-Host "  Insttoken").Trim()
    }
}

# ── 6. La consulta real ──────────────────────────────────────────────────────
Titulo "Paso 3 de 3 - Consultar Scopus"
& $py src\enrich\scopus_api.py
$exito = ($LASTEXITCODE -eq 0)

if (-not $exito) {
    Malo "La consulta fallo. Lea el mensaje de arriba: dice qué pasó y qué hacer."
    Read-Host "`n  Enter para cerrar"; exit 1
}

Titulo "Terminado"
Write-Host "  Resultado en: data\enriched\scopus_api_consulta.json"
Write-Host ""
Write-Host "  Arriba tiene el bloque listo para pegar en config\sources.yml," -ForegroundColor Cyan
Write-Host "  bajo scopus_export. Este script NO lo pega solo: revise primero" -ForegroundColor Cyan
Write-Host "  si el recuento coincide con el universo publicado (823)." -ForegroundColor Cyan
Write-Host ""
Write-Host "  Cuando lo haya pegado y revisado, para incorporar el resultado" -ForegroundColor Cyan
Write-Host "  de la consulta al proyecto:"
Write-Host "    git add data\enriched\scopus_api_consulta.json config\sources.yml"
Write-Host "    git commit -m `"T-06: fecha de corte declarada desde la API de Scopus`""
Write-Host "    git push"

Read-Host "`n  Enter para cerrar"
