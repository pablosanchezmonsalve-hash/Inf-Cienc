"""Build 06 — Ensamblado del sitio estático desplegable.

Copia `web/` y `data/processed/` a `dist/`, que es lo único que se despliega.

Es también la barrera física de capas: `data/raw/` e `internal/` no se copian
nunca. Si un día alguien los necesitara en el sitio, tendría que modificar este
archivo explícitamente, no olvidarse de excluirlos.

Salida:
  dist/
"""

from __future__ import annotations

import shutil
import subprocess
import sys

import common_build as b

DIST = b.ROOT / "dist"
WEB = b.ROOT / "web"

# Directorios que jamás se copian al bundle desplegable (docs/LAYERS.md §6).
NUNCA_DESPLEGAR = ("data/raw", "internal")


def prerenderizar() -> None:
    """Escribe el HTML de las páginas en el build en vez de en el navegador.

    Ejecuta los constructores de marcado de `web/assets/js/vista.js` bajo Node,
    contra los mismos artefactos JSON que consumiría el navegador. No hay una
    segunda implementación del marcado: es el mismo código.

    Node es un requisito BLANDO. Si no está, el sitio se ensambla igual y
    funciona igual mientras haya JavaScript en el cliente; lo que se pierde es
    el contenido sin JS y el LCP corto. Abortar el build entero por eso sería
    desproporcionado, pero callarlo dejaría un sitio peor sin que nadie lo
    notara: por eso se avisa en voz alta.
    """
    guion = b.ROOT / "src" / "build" / "prerender.mjs"
    try:
        r = subprocess.run(["node", str(guion), str(DIST)],
                           capture_output=True, text=True, check=False)
    except FileNotFoundError:
        print("  pre-renderizado  : OMITIDO — no hay Node en el entorno.")
        print("                     El sitio requerirá JavaScript para mostrar contenido.")
        return
    print(r.stdout.rstrip())
    if r.returncode != 0:
        print(r.stderr.rstrip())
        sys.exit("BUILD ABORTADO: el pre-renderizado falló.")


def main() -> None:
    b.banner("BUILD 06 — ENSAMBLADO DEL SITIO")

    if not (b.PROCESSED / "meta.json").exists():
        sys.exit("BUILD ABORTADO: faltan artefactos. Ejecute antes el build completo.")

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    shutil.copytree(WEB, DIST, dirs_exist_ok=True)
    shutil.copytree(b.PROCESSED, DIST / "data", dirs_exist_ok=True)

    # Verificación explícita de que la capa interna no viajó.
    for prohibido in NUNCA_DESPLEGAR:
        nombre = prohibido.split("/")[-1]
        colados = [p for p in DIST.rglob("*") if p.is_dir() and p.name == nombre]
        if colados:
            sys.exit(f"BUILD ABORTADO: '{prohibido}' apareció en dist/: {colados}")

    prerenderizar()

    paginas = sorted(p.name for p in DIST.glob("*.html"))
    fichas = len(list((DIST / "data" / "author").glob("*.json")))
    peso = sum(p.stat().st_size for p in DIST.rglob("*") if p.is_file()) / 1024

    print(f"  páginas          : {len(paginas)} · {', '.join(paginas)}")
    print(f"  fichas de autor  : {fichas}")
    print(f"  peso total       : {peso:.0f} KB")
    print("  capa interna     : no incluida (verificado)")
    print("\n  Servir con:  python3 -m http.server -d dist 8000")


if __name__ == "__main__":
    main()
