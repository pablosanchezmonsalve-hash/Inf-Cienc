# Revisión de la brecha de cobertura OpenAlex (V2-26) — asistente para Windows.
#
# POR QUÉ EXISTE
#   V2-26 dejó 414 obras que OpenAlex atribuye a la UFT y el universo (Scopus)
#   no tiene. Decidir cada caso —¿producción real fuera de Scopus, error de
#   atribución, o tipo documental excluido a propósito?— es criterio humano,
#   no algo que un script resuelva solo. Mismo patrón que
#   scripts\validar-unidades.ps1: generar, abrir, recoger el CSV exportado,
#   aplicar.
#
# QUÉ NO HACE
#   No agrega nada al universo publicado. Marcar «Sí, es UFT» aquí NO mete la
#   obra en publications_universe.csv — sólo deja constancia de que alguien
#   revisó el caso. Por eso este asistente no reconstruye el sitio al final:
#   no hay nada del build que dependa de esta revisión.
#
# USO
#   Clic derecho sobre este archivo -> «Ejecutar con PowerShell»
#   o, desde una consola:  .\scripts\revisar-cobertura-openalex.ps1

$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\_comun.ps1"

Titulo "Revision de cobertura OpenAlex (V2-26)"

# ── 1. Situarse en la raíz del proyecto ──────────────────────────────────────
$raiz = Entrar-Raiz "src\review\build_openalex_review.py"

# ── 2. Python y dependencias ──────────────────────────────────────────────────
$py = Buscar-Python
Asegurar-Dependencias $py

# ── 3. Autoprueba sin red ────────────────────────────────────────────────────
Titulo "Paso 1 de 4 - Probar la logica (sin internet)"
& $py src\review\apply_openalex_review.py --test | Select-Object -Last 3
if ($LASTEXITCODE -ne 0) {
    Malo "La autoprueba fallo. No siga: lo que aplique podria no ser lo que decida."
    Read-Host "`n  Enter para cerrar"; exit 1
}
Ok "Autoprueba correcta"

# ── 4. Datos de la corrida de OpenAlex ───────────────────────────────────────
Titulo "Paso 2 de 4 - Verificar los datos"
if (-not (Test-Path "internal\openalex_cobertura.csv")) {
    Malo "Falta internal\openalex_cobertura.csv"
    Write-Host "  Ejecute primero:  py src\enrich\openalex_cobertura.py"
    Read-Host "`n  Enter para cerrar"; exit 1
}
Ok "internal\openalex_cobertura.csv esta"

# ── 5. Generar la página de revisión ─────────────────────────────────────────
Titulo "Paso 3 de 4 - Generar la pagina de revision"
& $py src\review\build_openalex_review.py
if ($LASTEXITCODE -ne 0) { Malo "Fallo la generacion"; Read-Host "`n  Enter"; exit 1 }

$pagina = Join-Path $raiz "internal\revision_cobertura_openalex.html"
if (-not (Test-Path $pagina)) {
    Malo "No se genero la pagina"; Read-Host "`n  Enter"; exit 1
}

Write-Host ""
Write-Host "  Abriendo la pagina en el navegador..." -ForegroundColor Cyan
Start-Process $pagina

Titulo "Ahora le toca a usted"
Write-Host "  En la pagina que acaba de abrirse:"
Write-Host ""
Write-Host "    1. Cada obra trae quien es el autor UFT segun OpenAlex, la"
Write-Host "       institucion tal como la declara, el DOI, el año y las citas."
Write-Host "       Ordenadas por citacion: las mas citadas son las mas faciles"
Write-Host "       de verificar primero."
Write-Host "    2. Marque 'Si, es UFT', 'No, error de OpenAlex', o 'Tipo excluido"
Write-Host "       a proposito' por cada obra."
Write-Host "    3. Puede buscar por titulo/autor/DOI, y filtrar solo pendientes."
Write-Host "    4. Si reviso antes y volvio a abrir la pagina, sus respuestas"
Write-Host "       siguen marcadas: no se pierden."
Write-Host "    5. Cuando termine (o cuando quiera parar), pulse"
Write-Host "       'Exportar decisiones (CSV)'." -ForegroundColor Cyan
Write-Host ""
Write-Host "  Puede cerrar esta ventana y volver a ejecutar este script cuando"
Write-Host "  haya exportado. No se pierde nada: puede revisar por partes."
Write-Host ""

$r = Read-Host "  Ya exporto el CSV y quiere aplicarlo ahora? (s/n)"
if ($r -notmatch '^[sSyY]') {
    Write-Host ""
    Write-Host "  De acuerdo. Vuelva a lanzar este script cuando haya exportado."
    Read-Host "`n  Enter para cerrar"; exit 0
}

# ── 6. Recoger el CSV descargado ─────────────────────────────────────────────
Titulo "Paso 4 de 4 - Recoger y aplicar"
$destino = Join-Path $raiz "internal\openalex_cobertura_decisiones.csv"

$descargas = Join-Path $env:USERPROFILE "Downloads"
$cand = @()
if (Test-Path $descargas) {
    $cand = @(Get-ChildItem (Join-Path $descargas "openalex_cobertura_decisiones*.csv"),
                            (Join-Path $descargas "openalex_cobertura_decisiones*.txt") `
              -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending)
}

if ($cand.Count -gt 0) {
    $nuevo = $cand[0]
    Write-Host "  Encontrado en Descargas:"
    Write-Host "    $($nuevo.Name)  ($($nuevo.LastWriteTime))"
    Write-Host ""
    $r = Read-Host "  Copiarlo a internal\openalex_cobertura_decisiones.csv? (s/n)"
    if ($r -match '^[sSyY]') {
        if (Test-Path $destino) {
            $dirResp = Join-Path $raiz "internal\.respaldos"
            New-Item -ItemType Directory -Force -Path $dirResp | Out-Null
            $sello = Get-Date -Format "yyyyMMdd-HHmmss"
            Copy-Item $destino (Join-Path $dirResp "openalex_cobertura_decisiones-$sello.csv")
            Ok "Respaldo del anterior en internal\.respaldos\"
        }
        Copy-Item $nuevo.FullName $destino -Force
        Ok "Copiado a internal\openalex_cobertura_decisiones.csv"
    }
} else {
    Aviso "No encuentro ningun openalex_cobertura_decisiones*.csv en Descargas"
    Write-Host "  Si lo guardo en otro sitio, muevalo a mano a:"
    Write-Host "    $destino" -ForegroundColor Cyan
    Read-Host "`n  Enter cuando este puesto"
}

if (-not (Test-Path $destino)) {
    Malo "Sigue sin haber internal\openalex_cobertura_decisiones.csv"
    Read-Host "`n  Enter para cerrar"; exit 1
}

Write-Host "  Primero SIN escribir nada, para que vea que haria:" -ForegroundColor Cyan
Write-Host ""
& $py src\review\apply_openalex_review.py --dry-run
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

& $py src\review\apply_openalex_review.py
if ($LASTEXITCODE -ne 0) { Malo "Fallo la aplicacion"; Read-Host "`n  Enter"; exit 1 }

Titulo "Terminado"
Write-Host "  internal\openalex_cobertura.csv quedo actualizado con sus decisiones."
Write-Host "  Recuerde: esto NO modifica el universo publicado ni requiere"
Write-Host "  reconstruir el sitio."
Write-Host ""
Write-Host "  Para incorporar las respuestas al proyecto:" -ForegroundColor Cyan
Write-Host "    git add internal\openalex_cobertura.csv internal\openalex_cobertura_decisiones.csv"
Write-Host "    git commit -m `"V2-26: revision humana de la brecha de cobertura`""
Write-Host "    git push"

Read-Host "`n  Enter para cerrar"
