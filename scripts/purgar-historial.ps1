<#
    purgar-historial.ps1 — Expulsión definitiva de data/raw/ e internal/ del historial git.

    DESTRUCTIVO. Reescribe el historial de TODAS las ramas del remoto y hace
    force-push. Requiere la sesión autenticada del propietario (credential
    manager) con permiso de administración y, si main tiene protección de rama,
    desactivarla primero (Settings -> Branches).

    Uso:
        .\scripts\purgar-historial.ps1                        # modo interactivo (pide confirmar)
        .\scripts\purgar-historial.ps1 -Confirmar -Fuerza   # no pide (solo si entiendes el riesgo)

    Se puede interrumpir en cualquier punto; antes de cada paso destructivo
    pide confirmación. Crear el mirror de backup NO es destructivo y es el
    primer paso.
#>
[CmdletBinding()]
param(
    [string]$Remoto = "https://github.com/pablosanchezmonsalve-hash/Inf-Cienc.git",
    [switch]$Fuerza
)

$ErrorActionPreference = "Stop"

# ── helpers de mensaje (estilo del proyecto) ───────────────────────────────
function Traza  { Write-Host "[traza]  $args" -ForegroundColor DarkGray }
function Ok     { Write-Host "[ok]     $args" -ForegroundColor Green }
function Aviso  { Write-Host "[aviso]  $args" -ForegroundColor Yellow }
function Errorf { Write-Host "[error]  $args" -ForegroundColor Red }

function Confirmar($mensaje) {
    if ($Fuerza) { return $true }
    $r = Read-Host "$mensaje  (s/N)"
    return ($r -match '^\s*[sS]')
}

# ── 0. Saneamiento de variables ────────────────────────────────────────────
$root  = Split-Path -Parent $PSScriptRoot                # raíz del repo
$origen = Split-Path -Leaf $root                          # nombre del proyecto
$tmp   = Join-Path $env:TEMP "$origen`-purga"             # clon de trabajo efímero
$bak   = Join-Path $root "..\$origen`-backup-mirror.git"  # mirror de respaldo
$bak   = [IO.Path]::GetFullPath($bak)

Write-Host "══════════════════════════════════════════════════════════════"
Write-Host "  PURGA DE HISTORIAL — $origen (D-SEC-01/D-SEC-02)"
Write-Host "  Remoto:  $Remoto"
Write-Host "  Respaldo: $bak"
Write-Host "══════════════════════════════════════════════════════════════"
Aviso "Esta operación REESCRIBE el historial y hace force-push a TODAS las ramas."
Aviso "Los hashes de los commits cambiarán e invalidará clones/PRs existentes."

if (-not $Fuerza) {
    if (-not (Confirmar "¿Entiendes el riesgo y deseas continuar?")) { Errorf "Abortado."; exit 1 }
}

# ── 1. Comprobar auth y git ───────────────────────────────────────────────
Traza "Comprobando acceso de lectura al remoto ..."
$probe = git ls-remote $Remoto HEAD 2>&1
if ($LASTEXITCODE -ne 0) {
    Errorf "No se pudo leer el remoto. Verifique credenciales de GitHub (git credential-manager)."
    exit 1
}
Ok "Acceso al remoto OK."

# ── 2. Mirror de backup (no destructivo) ─────────────────────────────────
if (Test-Path $bak) {
    Aviso "Ya existe un backup en: $bak"
    if (-not (Confirmar "¿Sobrescribirlo?")) { Errorf "Abortado."; exit 1 }
    Remove-Item -Recurse -Force $bak
}
Traza "Creando mirror de respaldo ..."
git clone --mirror $Remoto $bak
if ($LASTEXITCODE -ne 0) { Errorf "Falló el mirror de respaldo. NO continuo sin backup."; exit 1 }
Ok "Mirror de respaldo creado: $bak"

# ── 3. Asegurar git-filter-repo ──────────────────────────────────────────
$has = git filter-repo --version 2>$null; if ($LASTEXITCODE -ne 0) { $has = $null }
if (-not $has) {
    Aviso "git-filter-repo no está instalado. Se instalará vía pip."
    if (-not (Confirmar "¿Instalar ahora?")) { Errorf "Abortado."; exit 1 }
    py -m pip install --user git-filter-repo
    if ($LASTEXITCODE -ne 0) { Errorf "Falló la instalación de git-filter-repo."; exit 1 }
    # Localizar el ejecutable recién instalado y añadirlo al PATH de esta sesión.
    # `pip install --user` lo coloca en %USER_BASE%\Scripts o en un subdirectorio
    # PythonXY\Scripts, según la estructura del intérprete: se busca, no se asume.
    $pyUser = py -c "import site; print(site.USER_BASE)" 2>$null
    $encontrado = $null
    if ($pyUser) {
        # Candidatos: Scripts directo y cada PythonXY\Scripts bajo USER_BASE
        $candidatos = @(Join-Path $pyUser "Scripts")
        foreach ($sub in @(Get-ChildItem $pyUser -Directory -Filter "Python*" -ErrorAction SilentlyContinue)) {
            $candidatos += Join-Path $sub.FullName "Scripts"
        }
        foreach ($dir in $candidatos) {
            $exe = Join-Path $dir "git-filter-repo.exe"
            if (Test-Path $exe) { $encontrado = $exe; break }
        }
    }
    if ($encontrado) {
        $env:PATH = "$([IO.Path]::GetDirectoryName($encontrado));$env:PATH"
        Ok "git-filter-repo localizado: $encontrado"
    } elseif (-not (git filter-repo --version 2>$null)) {
        Errorf "git-filter-repo instalado pero no localizado en PATH."
        Errorf "Añádalo manualmente o siga la Sección 4 de docs/SEGURIDAD_PURGA.md."
        exit 1
    }
}
Ok "git-filter-repo listo: $(git filter-repo --version)"

# ── 4. Clon fresco de trabajo ────────────────────────────────────────────
if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
Traza "Clonando (todas las ramas) a $tmp ..."
git clone --no-local --no-hardlinks $bak $tmp
if ($LASTEXITCODE -ne 0) { Errorf "Falló el clon de trabajo."; exit 1 }
Push-Location $tmp
try {
    git fetch --all --tags 2>$null

    # ── 5. Purga ─────────────────────────────────────────────────────────
    if (-not $Fuerza) {
        if (-not (Confirmar "¿REESCRIBIR el historial eliminando data/raw/ e internal/? Este paso es irreversible.")) {
            Errorf "Abortado (sin cambios). ¿desea conservar el mirror de respaldo? Sí, se conserva."
            exit 2
        }
    }
    Traza "filter-repo: eliminando data/raw/ e internal/ de toda la historia ..."
    git filter-repo --path data/raw/ --path internal/ --invert-paths --force
    if ($LASTEXITCODE -ne 0) { Errorf "Falló la purga."; exit 1 }
    Ok "Purga completada en el clon."

    # ── 6. Re-asociar remoto y force-push ────────────────────────────────
    Traza "Re-asociando remoto y haciendo force-push ..."
    git remote add origin $Remoto
    if (-not $Fuerza) {
        if (-not (Confirmar "¿FORCE-PUSH a $Remoto (todas las ramas + tags)? Reescribirá el remoto.")) {
            Errorf "Abortado antes del push. El clon purgado queda en $tmp; el remoto NO se tocó."
            exit 2
        }
    }
    git push origin --force --all
    if ($LASTEXITCODE -ne 0) { Errorf "Falló el force-push de ramas."; exit 1 }
    git push origin --force --tags
    if ($LASTEXITCODE -ne 0) { Aviso "No había tags o falló el push de tags." }
    Ok "Force-push completado."

    # ── 7. Verificación ──────────────────────────────────────────────────
    Traza "Verificando historial limpio ..."
    $res = git log --all --oneline -- data/raw internal/
    if ($res) {
        Aviso "ADVERTENCIA: aún hay commits con data/raw/ o internal/:"
        Write-Host $res
        exit 3
    }
    Ok "Historial limpio: sin data/raw/ ni internal/ en ninguna rama."
}
finally {
    Pop-Location
}

# ── 8. Cierre ────────────────────────────────────────────────────────────
Write-Host ""
Ok "Purga finalizada. Recuerde:"
Aviso "  1) Re-cree internal/README.md en main (fue eliminado con internal/) y ajuste .gitignore."
Aviso "  2) Vuelva a activar la protección de rama de main si la desactivó."
Aviso "  3) Rotar secretos ORCID/Scopus (el repo era público)."
Aviso "  4) Los clientes/clones existentes deben re-clonar (los hashes cambiaron)."
Aviso "  5) El clon purgado temporal queda en: $tmp (puede borrarlo)."
Aviso "  Backup previo a la purga: $bak"
