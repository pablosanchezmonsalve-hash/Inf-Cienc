# Verificación de ORCID contra el registro público — asistente para Windows.
#
# POR QUÉ EXISTE
#   La guía pedía encadenar seis comandos, poner variables de entorno a mano y
#   no confundir el formato del documento con el comando. Eso falla, y falla
#   de un modo que no dice qué salió mal. Este script hace la secuencia entera
#   y comprueba cada paso antes del siguiente.
#
#   Pide las credenciales de forma interactiva: el secret no se escribe en
#   ningún archivo, no queda en el historial de la consola y no hay que pegarlo
#   en ninguna parte donde pueda quedar registrado.
#
# USO
#   Clic derecho sobre este archivo -> «Ejecutar con PowerShell»
#   o, desde una consola:  .\scripts\verificar-orcid.ps1

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

Titulo "Verificacion de ORCID contra el registro publico"

# ── 1. Situarse en la raíz del proyecto ──────────────────────────────────────
# El script vive en scripts/, así que la raíz es su carpeta padre. Funciona
# aunque se lance con doble clic desde cualquier sitio.
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz
Write-Host "  Proyecto: $raiz"

if (-not (Test-Path "src\enrich\orcid_api.py")) {
    Malo "No encuentro src\enrich\orcid_api.py"
    Write-Host "  Este script debe estar dentro de la carpeta del proyecto, en scripts\."
    Read-Host "`n  Enter para cerrar"; exit 1
}
Ok "Carpeta del proyecto correcta"

# ── 2. Python ────────────────────────────────────────────────────────────────
$py = $null
foreach ($cmd in @('py', 'python', 'python3')) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) { $py = $cmd; break }
}
if (-not $py) {
    Malo "No encuentro Python instalado"
    Write-Host "  Instalelo desde https://www.python.org/downloads/ y marque"
    Write-Host "  la casilla 'Add Python to PATH' durante la instalacion."
    Read-Host "`n  Enter para cerrar"; exit 1
}
Ok "Python encontrado como '$py'  ($(& $py --version 2>&1))"

# ── 3. Dependencias ──────────────────────────────────────────────────────────
& $py -c "import pandas, yaml" 2>$null
if ($LASTEXITCODE -ne 0) {
    Aviso "Faltan dependencias. Instalando..."
    & $py -m pip install -r requirements.txt --quiet
    if ($LASTEXITCODE -ne 0) { Malo "Fallo la instalacion"; Read-Host "`n  Enter"; exit 1 }
}
Ok "Dependencias listas"

# ── 4. Autoprueba sin red ────────────────────────────────────────────────────
# Se ejecuta ANTES de pedir credenciales: si la logica esta rota, el problema
# no son las credenciales y no tiene sentido pedirlas.
Titulo "Paso 1 de 4 - Probar la logica (sin internet, sin credenciales)"
& $py src\enrich\orcid_api.py --test
if ($LASTEXITCODE -ne 0) {
    Malo "La autoprueba fallo. El problema no son las credenciales."
    Read-Host "`n  Enter para cerrar"; exit 1
}

# ── 5. Auditoría, si hace falta ──────────────────────────────────────────────
Titulo "Paso 2 de 4 - Preparar los datos"
if (Test-Path "data\interim\publications_universe.csv") {
    Ok "Los datos de la auditoria ya estan"
} else {
    Write-Host "  Ejecutando la auditoria (tarda menos de un minuto)..."
    & $py src\audit\run_all.py | Out-Null
    if ($LASTEXITCODE -ne 0) { Malo "Fallo la auditoria"; Read-Host "`n  Enter"; exit 1 }
    Ok "Auditoria completada"
}

# ── 6. Credenciales ──────────────────────────────────────────────────────────
Titulo "Paso 3 de 4 - Credenciales de ORCID"
Write-Host "  Se obtienen gratis en https://orcid.org -> Developer tools."
Write-Host "  El secret se pide oculto: no se guarda ni queda en el historial."
Write-Host ""

if ($env:ORCID_CLIENT_ID) {
    Ok "Client ID ya definido en el entorno: $env:ORCID_CLIENT_ID"
} else {
    $env:ORCID_CLIENT_ID = (Read-Host "  Client ID (APP-...)").Trim()
}
if (-not $env:ORCID_CLIENT_SECRET) {
    $sec = Read-Host "  Client Secret" -AsSecureString
    $env:ORCID_CLIENT_SECRET = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))
}
if (-not $env:ORCID_CLIENT_ID -or -not $env:ORCID_CLIENT_SECRET) {
    Malo "Faltan credenciales"; Read-Host "`n  Enter"; exit 1
}
Ok "Credenciales cargadas en esta sesion"

# ── 7. Prueba corta, luego el resto ──────────────────────────────────────────
Titulo "Paso 4 de 4 - Prueba con 10 firmas"
Write-Host "  Se empieza por 10 a proposito: si el contrato de la API no es el"
Write-Host "  esperado, se ve aqui y no despues de 174 peticiones."
Write-Host ""
& $py src\enrich\orcid_api.py --limit 10

if ($LASTEXITCODE -ne 0) {
    Malo "La prueba con 10 fallo."
    Write-Host "  Copie TODO lo que aparece arriba y enviemelo: si el fallo es de"
    Write-Host "  contrato de la API, se corrige con lo que haya devuelto."
    Read-Host "`n  Enter para cerrar"; exit 1
}

Titulo "La prueba funciono"
$r = Read-Host "  Ejecutar ahora las 174 restantes? (s/n)"
if ($r -match '^[sSyY]') {
    & $py src\enrich\orcid_api.py
    if ($LASTEXITCODE -ne 0) { Malo "Fallo la ejecucion completa" }
    else {
        Titulo "Terminado"
        Write-Host "  Resultado en: data\enriched\orcid_verificacion.csv"
        Write-Host ""
        Write-Host "  Para incorporarlo al proyecto:" -ForegroundColor Cyan
        Write-Host "    git add data\enriched\orcid_verificacion.csv"
        Write-Host "    git commit -m `"Verificacion de ORCID contra el registro publico`""
        Write-Host "    git push"
    }
} else {
    Write-Host "  De acuerdo. Vuelva a lanzar este script cuando quiera continuar."
}

Read-Host "`n  Enter para cerrar"
