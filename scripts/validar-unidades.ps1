# Validación institucional de unidades académicas — asistente para Windows.
#
# POR QUÉ EXISTE
#   T-02 pide confirmar el vocabulario de unidades académicas y la jerarquía
#   escuela -> facultad contra el conocimiento real de la institución, no
#   contra un catálogo que no existe. Es la misma clase de tarea que la
#   revisión de identidad de autor -encadenar generar, abrir, recoger el CSV
#   descargado y aplicarlo en el orden justo- así que sigue el mismo patrón
#   que scripts\revisar-identidad.ps1 en vez de inventar uno nuevo.
#
# QUÉ NO HACE
#   No decide nada. Abre la página, recoge lo que usted marcó y lo aplica a
#   config\matching_rules.yml. El criterio institucional lo pone usted.
#
# USO
#   Clic derecho sobre este archivo -> «Ejecutar con PowerShell»
#   o, desde una consola:  .\scripts\validar-unidades.ps1

$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\_comun.ps1"

Titulo "Validacion de unidades academicas (T-02)"

# ── 1. Situarse en la raíz del proyecto ──────────────────────────────────────
$raiz = Entrar-Raiz "src\review\build_unit_validation.py"

# ── 2. Python y dependencias ──────────────────────────────────────────────────
$py = Buscar-Python
Asegurar-Dependencias $py

# ── 3. Autoprueba sin red ────────────────────────────────────────────────────
Titulo "Paso 1 de 5 - Probar la logica (sin internet)"
& $py src\review\apply_unit_validation.py --test | Select-Object -Last 3
if ($LASTEXITCODE -ne 0) {
    Malo "La autoprueba fallo. No siga: lo que aplique podria no ser lo que decida."
    Read-Host "`n  Enter para cerrar"; exit 1
}
Ok "Autoprueba correcta"

# ── 4. Datos de la auditoría ─────────────────────────────────────────────────
Titulo "Paso 2 de 5 - Preparar los datos"
if (Test-Path "internal\matching_log.csv") {
    Ok "Los datos de la auditoria ya estan"
} else {
    Write-Host "  Ejecutando la auditoria (tarda menos de un minuto)..."
    & $py src\audit\run_all.py | Out-Null
    if ($LASTEXITCODE -ne 0) { Malo "Fallo la auditoria"; Read-Host "`n  Enter"; exit 1 }
    Ok "Auditoria completada"
}

# ── 5. Generar la página de validación ───────────────────────────────────────
Titulo "Paso 3 de 5 - Generar la pagina de validacion"
& $py src\review\build_unit_validation.py
if ($LASTEXITCODE -ne 0) { Malo "Fallo la generacion"; Read-Host "`n  Enter"; exit 1 }

$pagina = Join-Path $raiz "internal\validacion_unidades.html"
if (-not (Test-Path $pagina)) {
    Malo "No se genero la pagina"; Read-Host "`n  Enter"; exit 1
}

Write-Host ""
Write-Host "  Abriendo la pagina en el navegador..." -ForegroundColor Cyan
Start-Process $pagina

Titulo "Ahora le toca a usted"
Write-Host "  En la pagina que acaba de abrirse:"
Write-Host ""
Write-Host "    1. Cada unidad trae la evidencia real -la afiliacion tal como"
Write-Host "       la escribio Scopus- para juzgar si el nombre deducido es"
Write-Host "       razonable."
Write-Host "    2. Marque 'Si, es correcto' o 'No, corregir' por cada unidad y"
Write-Host "       por cada jerarquia escuela -> facultad."
Write-Host "    3. Si corrigio antes y volvio a abrir la pagina, sus respuestas"
Write-Host "       siguen marcadas: no se pierden."
Write-Host "    4. Cuando termine (o cuando quiera parar), pulse"
Write-Host "       'Exportar respuestas (CSV)'." -ForegroundColor Cyan
Write-Host ""
Write-Host "  Puede cerrar esta ventana y volver a ejecutar este script cuando"
Write-Host "  haya exportado. No se pierde nada: puede responder por partes."
Write-Host ""

$r = Read-Host "  Ya exporto el CSV y quiere aplicarlo ahora? (s/n)"
if ($r -notmatch '^[sSyY]') {
    Write-Host ""
    Write-Host "  De acuerdo. Vuelva a lanzar este script cuando haya exportado."
    Read-Host "`n  Enter para cerrar"; exit 0
}

# ── 6. Recoger el CSV descargado ─────────────────────────────────────────────
Titulo "Paso 4 de 5 - Recoger el archivo exportado"
$destino = Join-Path $raiz "internal\unit_validation_decisions.csv"

$descargas = Join-Path $env:USERPROFILE "Downloads"
$cand = @()
if (Test-Path $descargas) {
    # Dos extensiones por el mismo motivo que en revisar-identidad.ps1: abierta
    # como archivo local la herramienta baja un .csv; servida como pagina
    # publicada, la extension puede caer a .txt. El contenido es el mismo y
    # apply_unit_validation.py lee por ruta, no por extension.
    $cand = @(Get-ChildItem (Join-Path $descargas "unit_validation_decisions*.csv"),
                            (Join-Path $descargas "unit_validation_decisions*.txt") `
              -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending)
}

if ($cand.Count -gt 0) {
    $nuevo = $cand[0]
    Write-Host "  Encontrado en Descargas:"
    Write-Host "    $($nuevo.Name)  ($($nuevo.LastWriteTime))"
    Write-Host ""
    $r = Read-Host "  Copiarlo a internal\unit_validation_decisions.csv? (s/n)"
    if ($r -match '^[sSyY]') {
        if (Test-Path $destino) {
            $dirResp = Join-Path $raiz "internal\.respaldos"
            New-Item -ItemType Directory -Force -Path $dirResp | Out-Null
            $sello = Get-Date -Format "yyyyMMdd-HHmmss"
            Copy-Item $destino (Join-Path $dirResp "unit_validation_decisions-$sello.csv")
            Ok "Respaldo del anterior en internal\.respaldos\"
        }
        Copy-Item $nuevo.FullName $destino -Force
        Ok "Copiado a internal\unit_validation_decisions.csv"
    }
} else {
    Aviso "No encuentro ningun unit_validation_decisions*.csv en Descargas"
    Write-Host "  Si lo guardo en otro sitio, muevalo a mano a:"
    Write-Host "    $destino" -ForegroundColor Cyan
    Read-Host "`n  Enter cuando este puesto"
}

if (-not (Test-Path $destino)) {
    Malo "Sigue sin haber internal\unit_validation_decisions.csv"
    Read-Host "`n  Enter para cerrar"; exit 1
}

# ── 7. Aplicar ───────────────────────────────────────────────────────────────
Titulo "Paso 5 de 5 - Aplicar las respuestas"
Write-Host "  Primero SIN escribir nada, para que vea que haria:" -ForegroundColor Cyan
Write-Host ""
& $py src\review\apply_unit_validation.py --dry-run
if ($LASTEXITCODE -ne 0) {
    Malo "La comprobacion en seco fallo. No se ha escrito nada."
    Read-Host "`n  Enter para cerrar"; exit 1
}

Write-Host ""
$r = Read-Host "  Es lo que esperaba? Aplicar de verdad? (s/n)"
if ($r -notmatch '^[sSyY]') {
    Write-Host "  No se ha escrito nada."
    Read-Host "`n  Enter para cerrar"; exit 0
}

& $py src\review\apply_unit_validation.py
if ($LASTEXITCODE -ne 0) { Malo "Fallo la aplicacion"; Read-Host "`n  Enter"; exit 1 }

# ── 8. Reconstruir lo que depende de esas respuestas ─────────────────────────
Titulo "Reconstruyendo el sitio"
Write-Host "  Las respuestas no llegan al sitio solas: hay que reconstruirlo."
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
Write-Host "  Para incorporar las respuestas al proyecto:" -ForegroundColor Cyan
Write-Host "    git add internal\unit_validation_decisions.csv config\matching_rules.yml STATE.md docs\"
Write-Host "    git commit -m `"T-02: validacion de unidades aplicada`""
Write-Host "    git push"

Read-Host "`n  Enter para cerrar"
