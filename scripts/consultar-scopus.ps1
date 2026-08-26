# Consulta a la API de Scopus para T-06 — asistente para Windows.
#
# POR QUÉ EXISTE
#   Igual que scripts\verificar-orcid.ps1: encadenar los pasos a mano falla de
#   un modo que no dice qué salió mal. Este script prueba la lógica primero,
#   pide la API Key en texto visible (ver más abajo por qué) y sólo entonces
#   hace la consulta real.
#
#   La API Key no se escribe en ningún archivo, no queda en el historial de la
#   consola y no hay que pegarla en ninguna parte donde pueda quedar registrada.
#
# USO
#   Clic derecho sobre este archivo -> «Ejecutar con PowerShell»
#   o, desde una consola:  .\scripts\consultar-scopus.ps1

$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\_comun.ps1"

Titulo "Consulta a la API de Scopus (T-06)"

# ── 1. Situarse en la raíz del proyecto ──────────────────────────────────────
Entrar-Raiz "src\enrich\scopus_api.py" | Out-Null

# ── 2. Python y dependencias ──────────────────────────────────────────────────
$py = Buscar-Python
Asegurar-Dependencias $py

# ── 3. Autoprueba sin red ────────────────────────────────────────────────────
# Antes de pedir la API Key: si la logica esta rota, el problema no es la
# credencial y no tiene sentido pedirla todavia.
Titulo "Paso 1 de 3 - Probar la logica (sin internet, sin credenciales)"
& $py src\enrich\scopus_api.py --test
if ($LASTEXITCODE -ne 0) {
    Malo "La autoprueba fallo. El problema no es la API Key."
    Read-Host "`n  Enter para cerrar"; exit 1
}

# ── 4. Credenciales ──────────────────────────────────────────────────────────
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
    $env:SCOPUS_API_KEY = Pedir-Credencial "API Key de Scopus" 20
}
if (-not $env:SCOPUS_API_KEY) {
    Malo "Falta la API Key"; Read-Host "`n  Enter"; exit 1
}
Ok "API Key cargada en esta sesion ($($env:SCOPUS_API_KEY.Length) caracteres)"

if (-not $env:SCOPUS_INSTTOKEN) {
    $r = Read-Host "  ¿Tiene tambien un Institutional Token (insttoken)? (s/n)"
    if ($r -match '^[sSyY]') {
        $env:SCOPUS_INSTTOKEN = Pedir-Credencial "Insttoken" 10
    }
}

# ── 5. La consulta real ──────────────────────────────────────────────────────
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
Write-Host "  si 'total_resultados' coincide con lo que ya declara scopus_export" -ForegroundColor Cyan
Write-Host "  (n_registros_leido) en config\sources.yml -- no con el universo" -ForegroundColor Cyan
Write-Host "  unido de 823, que mezcla registros exclusivos de SciVal." -ForegroundColor Cyan
Write-Host ""
Write-Host "  Cuando lo haya pegado y revisado, para incorporar el resultado" -ForegroundColor Cyan
Write-Host "  de la consulta al proyecto:"
Write-Host "    git add data\enriched\scopus_api_consulta.json config\sources.yml"
Write-Host "    git commit -m `"T-06: fecha de corte declarada desde la API de Scopus`""
Write-Host "    git push"

Read-Host "`n  Enter para cerrar"
