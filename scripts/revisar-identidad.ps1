# Revisión de identidad de autor — asistente para Windows.
#
# POR QUÉ EXISTE
#   La revisión pedía encadenar cinco comandos, saber cuál de ellos regenera qué,
#   guardar un archivo descargado en la carpeta correcta con el nombre correcto, y
#   después acordarse de reconstruir el sitio y el estado. Son siete pasos en el
#   orden justo, y la decisión D-85 ya dejó escrito lo que pasa con eso: una
#   instrucción que se puede copiar mal se copiará mal.
#
#   Existía el asistente para la verificación de ORCID y no para esto, que es
#   justo la parte donde una persona toma decisiones sobre personas reales.
#
# QUÉ NO HACE
#   No decide nada. Abre la página, recoge lo que usted decidió y lo aplica.
#   El veredicto lo pone usted (decisión D-08).
#
# USO
#   Clic derecho sobre este archivo -> «Ejecutar con PowerShell»
#   o, desde una consola:  .\scripts\revisar-identidad.ps1

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

Titulo "Revision de identidad de autor"

# ── 1. Situarse en la raíz del proyecto ──────────────────────────────────────
# El script vive en scripts/, así que la raíz es su carpeta padre. Funciona
# aunque se lance con doble clic desde cualquier sitio.
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz
Write-Host "  Proyecto: $raiz"

if (-not (Test-Path "src\review\build_review.py")) {
    Malo "No encuentro src\review\build_review.py"
    Write-Host "  Este script debe estar dentro de la carpeta del proyecto, en scripts\."
    Read-Host "`n  Enter para cerrar"; exit 1
}
Ok "Carpeta del proyecto correcta"

# ── 2. Python ────────────────────────────────────────────────────────────────
# Que el comando EXISTA no significa que funcione. Windows instala unos alias de
# ejecucion para `python` y `python3` que no son Python: son un atajo a la
# Microsoft Store y responden a --version con un mensaje de error (decision D-88).
function Probar-Python($cmd) {
    try {
        $v = & $cmd --version 2>&1 | Out-String
    } catch { return $null }
    if ($LASTEXITCODE -ne 0) { return $null }
    if ($v -notmatch 'Python\s+3\.\d+') { return $null }   # descarta el atajo de la Store
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
    Write-Host "  Lo que responde en su equipo es el atajo de Windows a la" -ForegroundColor Yellow
    Write-Host "  Microsoft Store, que NO es Python. Por eso falla." -ForegroundColor Yellow
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
# Antes de tocar nada: si la logica de aplicacion esta rota, mejor saberlo ahora
# que despues de una hora decidiendo.
Titulo "Paso 1 de 5 - Probar la logica (sin internet)"
& $py src\review\apply_decisions.py --test | Select-Object -Last 3
if ($LASTEXITCODE -ne 0) {
    Malo "La autoprueba fallo. No siga: lo que aplique podria no ser lo que decida."
    Read-Host "`n  Enter para cerrar"; exit 1
}
& $py src\review\merge_decisions.py --test | Select-Object -Last 3
if ($LASTEXITCODE -ne 0) {
    Malo "La autoprueba de la fusion fallo. No siga."
    Read-Host "`n  Enter para cerrar"; exit 1
}
Ok "Autoprueba correcta"

# ── 5. Datos de la auditoría ─────────────────────────────────────────────────
# Las colas se calculan sobre los datos de la auditoria. Volver a correrla NO
# borra sus decisiones: internal\identity_decisions.csv es su exportacion y
# ningun script de la auditoria lo toca.
Titulo "Paso 2 de 5 - Preparar los datos"
if ((Test-Path "data\interim\authors_master_draft.csv") -and
    (Test-Path "internal\matching_log.csv")) {
    Ok "Los datos de la auditoria ya estan"
} else {
    Write-Host "  Ejecutando la auditoria (tarda menos de un minuto)..."
    & $py src\audit\run_all.py | Out-Null
    if ($LASTEXITCODE -ne 0) { Malo "Fallo la auditoria"; Read-Host "`n  Enter"; exit 1 }
    Ok "Auditoria completada"
}

# ── 6. Generar la página de revisión ─────────────────────────────────────────
Titulo "Paso 3 de 5 - Generar la pagina de revision"
& $py src\review\build_review.py
if ($LASTEXITCODE -ne 0) { Malo "Fallo la generacion"; Read-Host "`n  Enter"; exit 1 }
& $py src\review\build_unit_validation.py | Out-Null

$pagina = Join-Path $raiz "internal\revision_identidad.html"
if (-not (Test-Path $pagina)) {
    Malo "No se genero la pagina"; Read-Host "`n  Enter"; exit 1
}

Write-Host ""
Write-Host "  Abriendo la pagina en el navegador..." -ForegroundColor Cyan
Start-Process $pagina

Titulo "Ahora le toca a usted"
Write-Host "  En la pagina que acaba de abrirse:"
Write-Host ""
Write-Host "    1. El filtro ya viene en 'Solo pendientes'. Lo que usted decidio"
Write-Host "       antes sigue guardado y aparece marcado."
Write-Host "    2. Empiece por la cola 'ORCID sin confirmar': son las unicas que"
Write-Host "       el sitio publica hoy diciendo que nadie las respalda."
Write-Host "    3. Cada caso trae enlace al registro del titular y la lista de"
Write-Host "       publicaciones que hay que comparar."
Write-Host "    4. Cuando termine (o cuando quiera parar), pulse"
Write-Host "       'Exportar decisiones (CSV)'." -ForegroundColor Cyan
Write-Host ""
Write-Host "  Puede cerrar esta ventana y volver a ejecutar este script cuando"
Write-Host "  haya exportado. No se pierde nada."
Write-Host ""

$r = Read-Host "  Ya exporto el CSV y quiere aplicarlo ahora? (s/n)"
if ($r -notmatch '^[sSyY]') {
    Write-Host ""
    Write-Host "  De acuerdo. Vuelva a lanzar este script cuando haya exportado."
    Read-Host "`n  Enter para cerrar"; exit 0
}

# ── 7. Recoger el CSV descargado ─────────────────────────────────────────────
# El paso que mas falla: el navegador lo deja en Descargas y hay que moverlo a
# internal\ con el nombre exacto. Se busca el mas reciente y se copia.
Titulo "Paso 4 de 5 - Recoger el archivo exportado"
$destino = Join-Path $raiz "internal\identity_decisions.csv"

$descargas = Join-Path $env:USERPROFILE "Downloads"
$cand = @()
if (Test-Path $descargas) {
    # El @() no sobra: sin el, un unico resultado llega como escalar y no como
    # array, y `.Count` sobre un escalar no significa lo mismo en Windows
    # PowerShell 5.1 que en 7.
    # Se buscan las DOS extensiones. Abierta como archivo local la herramienta
    # baja un .csv; servida como pagina publicada la entrega la capacidad de
    # descarga del anfitrion, que cae a .txt cuando el .csv no esta habilitado
    # en esa vista. El contenido es el mismo y apply_decisions.py lee por ruta.
    $cand = @(Get-ChildItem (Join-Path $descargas "identity_decisions*.csv"),
                            (Join-Path $descargas "identity_decisions*.txt") `
              -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending)
}

if ($cand.Count -gt 0) {
    $nuevo = $cand[0]
    Write-Host "  Encontrado en Descargas:"
    Write-Host "    $($nuevo.Name)  ($($nuevo.LastWriteTime))"
    Write-Host ""
    $r = Read-Host "  Fusionarlo con internal\identity_decisions.csv? (s/n)"
    if ($r -match '^[sSyY]') {
        # Respaldo antes de sustituir. NO se copia el archivo nuevo encima del
        # vigente: la pagina de revision solo pinta la cola VIVA, asi que un
        # caso decidido en una ronda anterior cuya ambiguedad ya no se vuelve
        # a detectar desaparece del formulario -- no porque se haya revocado,
        # sino porque ya no hay nada que preguntar. Copiar encima perderia esa
        # decision en silencio. Paso el 2026-08-26: 38 grupos consolidados
        # quedaron en 16 con un Copy-Item directo (D-263, SESSION_NOTES.md).
        # merge_decisions.py une por caso_id: el nuevo gana donde coincide, lo
        # que solo esta en el vigente se conserva.
        if (Test-Path $destino) {
            $dirResp = Join-Path $raiz "internal\.respaldos"
            New-Item -ItemType Directory -Force -Path $dirResp | Out-Null
            $sello = Get-Date -Format "yyyyMMdd-HHmmss"
            Copy-Item $destino (Join-Path $dirResp "identity_decisions-$sello.csv")
            Ok "Respaldo del vigente en internal\.respaldos\"
        }
        & $py src\review\merge_decisions.py $nuevo.FullName
        if ($LASTEXITCODE -ne 0) { Malo "Fallo la fusion"; Read-Host "`n  Enter"; exit 1 }
        Ok "Fusionado en internal\identity_decisions.csv"
    }
} else {
    Aviso "No encuentro ningun identity_decisions*.csv en Descargas"
    Write-Host "  Si lo guardo en otro sitio, muevalo a mano a:"
    Write-Host "    $destino" -ForegroundColor Cyan
    Read-Host "`n  Enter cuando este puesto"
}

if (-not (Test-Path $destino)) {
    Malo "Sigue sin haber internal\identity_decisions.csv"
    Read-Host "`n  Enter para cerrar"; exit 1
}

# ── 8. Aplicar ───────────────────────────────────────────────────────────────
# Primero en seco. Aplicar sin ver antes que se va a aplicar es lo que convierte
# una errata en un dato publicado.
Titulo "Paso 5 de 5 - Aplicar las decisiones"
Write-Host "  Primero SIN escribir nada, para que vea que haria:" -ForegroundColor Cyan
Write-Host ""
& $py src\review\apply_decisions.py --dry-run
if ($LASTEXITCODE -ne 0) {
    Malo "La comprobacion en seco fallo. No se ha escrito nada."
    Write-Host "  Lea el motivo arriba: suele ser una contradiccion entre dos"
    Write-Host "  decisiones, o un ORCID mal tecleado. Corrijalo en la pagina,"
    Write-Host "  vuelva a exportar y ejecute este script otra vez."
    Read-Host "`n  Enter para cerrar"; exit 1
}

Write-Host ""
$r = Read-Host "  Es lo que esperaba? Aplicar de verdad? (s/n)"
if ($r -notmatch '^[sSyY]') {
    Write-Host "  No se ha escrito nada."
    Read-Host "`n  Enter para cerrar"; exit 0
}

& $py src\review\apply_decisions.py
if ($LASTEXITCODE -ne 0) { Malo "Fallo la aplicacion"; Read-Host "`n  Enter"; exit 1 }

# ── 9. Reconstruir lo que depende de esas decisiones ─────────────────────────
Titulo "Reconstruyendo el sitio"
Write-Host "  Las decisiones no llegan al sitio solas: hay que reconstruirlo."
Write-Host ""
foreach ($paso in @(
    @("Auditoria",   "src\audit\run_all.py"),
    @("Factibilidad","src\analysis\indicator_feasibility.py"),
    @("Artefactos",  "src\build\build_all.py"),
    @("Sitio",       "src\build\06_assemble_site.py"),
    @("Estado",      "src\state\snapshot.py"))) {
    Write-Host "  $($paso[0])..."
    & $py $paso[1] | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Malo "Fallo en $($paso[0]). Ejecute a mano para ver el detalle:"
        Write-Host "    $py $($paso[1])" -ForegroundColor Cyan
        Read-Host "`n  Enter para cerrar"; exit 1
    }
    Ok $paso[0]
}

Titulo "Terminado"
Write-Host "  El sitio esta reconstruido en dist\ y STATE.md actualizado."
Write-Host ""
Write-Host "  Para verlo en el navegador:" -ForegroundColor Cyan
Write-Host "    $py -m http.server -d dist 8000"
Write-Host "    y abra http://localhost:8000"
Write-Host ""
Write-Host "  Para incorporar las decisiones al proyecto:" -ForegroundColor Cyan
Write-Host "    git add internal\identity_decisions.csv config\ STATE.md docs\"
Write-Host "    git commit -m `"Decisiones de identidad aplicadas`""
Write-Host "    git push"

Read-Host "`n  Enter para cerrar"
