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
. "$PSScriptRoot\_comun.ps1"

Titulo "Candidatos de ORCID por afiliacion (T-19)"

# ── 1. Situarse en la raíz del proyecto ──────────────────────────────────────
Entrar-Raiz "src\enrich\orcid_afiliacion.py" | Out-Null

# ── 2. Python y dependencias ──────────────────────────────────────────────────
$py = Buscar-Python
Asegurar-Dependencias $py

# ── 3. Autoprueba sin red ────────────────────────────────────────────────────
Titulo "Paso 1 de 3 - Probar la logica (sin internet, sin credenciales)"
& $py src\enrich\orcid_afiliacion.py --test
if ($LASTEXITCODE -ne 0) {
    Malo "La autoprueba fallo. El problema no son las credenciales."
    Read-Host "`n  Enter para cerrar"; exit 1
}

# ── 4. Datos de la auditoría ─────────────────────────────────────────────────
Titulo "Paso 2 de 3 - Preparar los datos"
if (Test-Path "internal\matching_log.csv") {
    Ok "Los datos de la auditoria ya estan"
} else {
    Write-Host "  Ejecutando la auditoria (tarda menos de un minuto)..."
    & $py src\audit\run_all.py | Out-Null
    if ($LASTEXITCODE -ne 0) { Malo "Fallo la auditoria"; Read-Host "`n  Enter"; exit 1 }
    Ok "Auditoria completada"
}

# ── 5. Credenciales ──────────────────────────────────────────────────────────
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
    $env:ORCID_CLIENT_ID = Pedir-Credencial "Client ID (APP-...)"
}
if (-not $env:ORCID_CLIENT_SECRET) {
    $env:ORCID_CLIENT_SECRET = Pedir-Credencial "Client Secret"
}
if (-not $env:ORCID_CLIENT_ID -or -not $env:ORCID_CLIENT_SECRET) {
    Malo "Faltan credenciales"; Read-Host "`n  Enter"; exit 1
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
