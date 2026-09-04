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
# El respaldo lleva fecha y hora, y NUNCA se sobrescribe: una segunda corrida
# ocurre justo después de un fallo parcial, que es cuando el remoto ya puede
# estar reescrito. Reemplazar el mirror anterior por uno del remoto YA purgado
# borraría la única copia del historial original en el momento exacto en que
# hace falta.
$sello = Get-Date -Format "yyyyMMdd-HHmmss"
$bak   = Join-Path $root "..\$origen`-backup-mirror-$sello.git"
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
    Errorf "Ya existe un respaldo con este sello de tiempo: $bak"
    Errorf "No se sobrescribe ningún respaldo. Muevalo o espere un segundo."
    exit 1
}
$previos = @(Get-ChildItem (Split-Path -Parent $bak) -Directory `
             -Filter "$origen-backup-mirror-*.git" -ErrorAction SilentlyContinue)
if ($previos.Count -gt 0) {
    Aviso "Ya hay $($previos.Count) respaldo(s) de corridas anteriores:"
    foreach ($d in $previos) { Aviso "    $($d.Name)" }
    Aviso "Se conservan todos. Si una corrida anterior ya purgó el remoto, el"
    Aviso "respaldo BUENO es el MAS ANTIGUO, no el que se va a crear ahora."
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
    # `--path internal/ --invert-paths` se llevaba también internal/README.md,
    # que docs/SEGURIDAD_PURGA.md §2 manda conservar («conservar solo
    # internal/README.md»). El callback hace la excepción dentro del filtro,
    # en vez de dejar que haya que recrear el archivo a mano después.
    #
    # Las cadenas de Python van con comillas SIMPLES a propósito: PowerShell
    # maltrata las comillas dobles al pasar argumentos a un ejecutable nativo,
    # y el callback llegaría roto a git.
    $filtro = "return None if (filename.startswith(b'data/raw/') or (filename.startswith(b'internal/') and filename != b'internal/README.md')) else filename"
    Traza "filter-repo: eliminando data/raw/ e internal/ de toda la historia ..."
    Traza "             (se conserva internal/README.md)"
    git filter-repo --force --filename-callback $filtro
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
    # --atomic: o entran todas las ramas o no entra ninguna. Sin él, si main
    # tiene protección de rama el resto se reescribe y main no, y el remoto
    # queda con dos historiales incompatibles conviviendo entre ramas.
    git push origin --force --atomic --all
    if ($LASTEXITCODE -ne 0) {
        Errorf "Falló el force-push de ramas. No se escribió NINGUNA (--atomic)."
        Errorf "Causa habitual: main tiene protección de rama. Desactívela en"
        Errorf "Settings -> Branches y vuelva a ejecutar; el remoto sigue intacto."
        exit 1
    }
    git push origin --force --tags
    if ($LASTEXITCODE -ne 0) { Aviso "No había tags o falló el push de tags." }
    Ok "Force-push completado."

    # ── 7. Verificación ──────────────────────────────────────────────────
    Traza "Verificando historial limpio ..."
    # Se excluye internal/README.md: ahora se conserva a propósito, y sin la
    # exclusión esta comprobación daría una falsa alarma en cada corrida.
    $res = git log --all --oneline -- data/raw internal/ ':!internal/README.md'
    if ($res) {
        Aviso "ADVERTENCIA: aún hay commits con data/raw/ o internal/:"
        Write-Host $res
        exit 3
    }
    Ok "Historial limpio: sin data/raw/ ni internal/ en ninguna rama."

    # Comprobar sólo lo que debe desaparecer no basta: un filtro equivocado que
    # se llevara además la capa pública pasaría en silencio, y sin
    # data/processed/ el despliegue no puede ensamblar el sitio (D-SEC-02).
    Traza "Verificando que la capa pública sobrevivió ..."
    $pub = git ls-tree -r --name-only HEAD -- data/processed
    if (-not $pub) {
        Errorf "La capa pública data/processed/ NO está en el árbol tras la purga."
        Errorf "El remoto ya fue reescrito: restaure desde $bak antes de nada más."
        exit 3
    }
    Ok "Capa pública intacta: $(@($pub).Count) artefacto(s) en data/processed/."
    $rme = git ls-tree -r --name-only HEAD -- internal/README.md
    if ($rme) { Ok "internal/README.md conservado." }
    else { Aviso "internal/README.md no está en HEAD: recréelo (ver cierre)." }
}
finally {
    Pop-Location
}

# ── 8. Cierre ────────────────────────────────────────────────────────────
Write-Host ""
Ok "Purga finalizada. Recuerde:"
Aviso "  1) internal/README.md se conservó: compruebe que .gitignore sigue con la"
Aviso "     excepción !internal/README.md y que nada más de internal/ está indexado."
Aviso "  2) Vuelva a activar la protección de rama de main si la desactivó."
Aviso "  3) Rotar secretos ORCID/Scopus (el repo era público)."
Aviso "  4) Los clientes/clones existentes deben re-clonar (los hashes cambiaron)."
Aviso "  5) El clon purgado temporal queda en: $tmp (puede borrarlo)."
Aviso "  Backup previo a la purga: $bak"
