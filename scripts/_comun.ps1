# Funciones compartidas por los asistentes de PowerShell del proyecto.
#
# POR QUÉ EXISTE
#   Los cuatro asistentes (consultar-scopus, ampliar-orcid-afiliacion,
#   verificar-orcid, revisar-identidad) repetían las mismas ~80 líneas de
#   detección de Python y las mismas cuatro funciones de mensaje. Una
#   corrección aquí -antes de este archivo- exigía tocar los cuatro por
#   separado y confiar en no olvidar ninguno; de hecho, uno de los cuatro
#   quedó con un mensaje desactualizado varias sesiones sin que nadie lo
#   notara. Ahora se corrige una vez.
#
# USO
#   Al principio de cada asistente, antes de usar cualquier función de este
#   archivo:
#       . "$PSScriptRoot\_comun.ps1"
#   Este archivo no se ejecuta solo -- no tiene "Ejecutar con PowerShell" con
#   sentido propio, es una biblioteca.
#
# POR QUÉ LAS FUNCIONES DEVUELVEN VALORES EN VEZ DE USAR $script:
#   `$PSScriptRoot` dentro de una función definida aquí SÍ coincide con la
#   carpeta scripts\ (porque este archivo también vive ahí), pero `$script:`
#   como mecanismo para "guardar y que el que llama lo lea después" es frágil
#   al mezclar dot-sourcing entre archivos: no vale la pena arriesgarlo. Cada
#   función que produce algo lo devuelve con `return`, y quien llama lo
#   recibe con `$x = Nombre-Funcion`.

function Titulo($t) {
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor DarkCyan
    Write-Host "  $t" -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor DarkCyan
}
function Ok($t)    { Write-Host "  [OK]    $t" -ForegroundColor Green }
function Aviso($t) { Write-Host "  [!]     $t" -ForegroundColor Yellow }
function Malo($t)  { Write-Host "  [ERROR] $t" -ForegroundColor Red }

# Entra a la raíz del proyecto (la carpeta padre de scripts\) y comprueba que
# un archivo conocido del repositorio exista ahí, como prueba de que este
# script se está ejecutando dentro de la copia correcta del proyecto.
# Devuelve la ruta de la raíz.
function Entrar-Raiz([string]$archivoClave) {
    $raiz = Split-Path -Parent $PSScriptRoot
    Set-Location $raiz
    Write-Host "  Proyecto: $raiz"

    if (-not (Test-Path $archivoClave)) {
        Malo "No encuentro $archivoClave"
        Write-Host "  Este script debe estar dentro de la carpeta del proyecto, en scripts\."
        Read-Host "`n  Enter para cerrar"; exit 1
    }
    Ok "Carpeta del proyecto correcta"
    return $raiz
}

# Que el comando EXISTA no significa que funcione. Windows instala unos alias
# de ejecución para `python` y `python3` que no son Python: son un atajo a la
# Microsoft Store y responden a --version con un mensaje de error (D-88).
function Probar-Python([string]$cmd) {
    try {
        $v = & $cmd --version 2>&1 | Out-String
    } catch { return $null }
    if ($LASTEXITCODE -ne 0) { return $null }
    if ($v -notmatch 'Python\s+3\.\d+') { return $null }   # descarta el atajo de la Store
    return $v.Trim()
}

# Busca un intérprete de Python 3 real: primero en el PATH, luego en las
# rutas donde el instalador oficial lo deja por defecto si no está en el
# PATH. Se detiene con instrucciones de instalación si no encuentra ninguno.
# Devuelve el comando o ruta completa a usar (para `& $py ...`).
function Buscar-Python {
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
        Write-Host "  Lo que responde en su equipo puede ser el atajo de Windows a la" -ForegroundColor Yellow
        Write-Host "  Microsoft Store, que NO es Python. Por eso falla." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Instalelo asi:" -ForegroundColor Cyan
        Write-Host "    1. Abra https://www.python.org/downloads/"
        Write-Host "    2. Descargue la version para Windows y ejecutela."
        Write-Host "    3. IMPORTANTE: en la PRIMERA pantalla del instalador marque"
        Write-Host "       'Add python.exe to PATH' antes de pulsar Install." -ForegroundColor Cyan
        Write-Host "    4. Cierre esta ventana, abra una nueva, y vuelva a ejecutar"
        Write-Host "       este script."
        Write-Host ""
        Write-Host "  La Microsoft Store tambien sirve: busque 'Python 3' e instalelo"
        Write-Host "  desde ahi. Lo que no sirve es el atajo vacio que hay ahora."
        Read-Host "`n  Enter para cerrar"; exit 1
    }
    Ok "Python encontrado: $ver"
    return $py
}

# Instala pandas/PyYAML si faltan. $py es lo que devolvió Buscar-Python.
function Asegurar-Dependencias([string]$py) {
    & $py -c "import pandas, yaml" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Aviso "Faltan dependencias. Instalando..."
        & $py -m pip install -r requirements.txt --quiet
        if ($LASTEXITCODE -ne 0) { Malo "Fallo la instalacion"; Read-Host "`n  Enter"; exit 1 }
    }
    Ok "Dependencias listas"
}

# Pide una credencial en texto visible y valida que no sea sospechosamente
# corta (síntoma de un pegado fallido -- D-257, SESSION_NOTES.md: pegar
# dentro de un prompt oculto capturó 1 carácter en vez del texto completo en
# la consola de un usuario real, sin ningún error visible). $etiqueta es lo
# que se muestra en el prompt; $minimo es la longitud mínima esperada.
function Pedir-Credencial([string]$etiqueta, [int]$minimo = 10) {
    $valor = (Read-Host "  $etiqueta").Trim()
    if ($valor -and $valor.Length -lt $minimo) {
        Malo "Se capturaron $($valor.Length) caracteres para '$etiqueta'; se esperaban al menos $minimo."
        Write-Host "  Probablemente el pegado fallo. Vuelva a ejecutar el script e intente" -ForegroundColor Yellow
        Write-Host "  escribiendola directamente, o pegue con clic derecho en vez de Ctrl+V." -ForegroundColor Yellow
        Read-Host "`n  Enter para cerrar"; exit 1
    }
    return $valor
}
