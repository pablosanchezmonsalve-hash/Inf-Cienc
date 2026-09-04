"""Build 06 — Ensamblado del sitio estático desplegable.

Copia `web/` y `data/processed/` a `dist/`, que es lo único que se despliega.

Es también la barrera física de capas: `data/raw/` e `internal/` no se copian
nunca. Si un día alguien los necesitara en el sitio, tendría que modificar este
archivo explícitamente, no olvidarse de excluirlos.

Salida:
  dist/
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys

import common_build as b

if sys.platform == "win32":
    # La consola de Windows usa cp1252 por defecto: revienta cualquier print()
    # con caracteres como "→"/"✗"/"⚠". Mismo patrón que src/enrich/orcid_openalex.py.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


DIST = b.ROOT / "dist"
WEB = b.ROOT / "web"

# Directorios que jamás se copian al bundle desplegable (docs/LAYERS.md §6).
NUNCA_DESPLEGAR = ("data/raw", "internal")


def expandir_cabeceras() -> None:
    """Compone el `<head>` de cada página desde una sola plantilla (V2-16).

    Las dieciséis líneas de cabecera estaban copiadas en las once páginas, y la
    del catálogo se creó copiando la de metodología: así es como diez copias se
    vuelven once y una se queda atrás. Ahora cada página declara sólo lo suyo
    —`data-titulo` y `data-descripcion`— y aquí se expande.

    TRES COMPROBACIONES, Y NINGUNA ES DECORATIVA
        1. Toda página tiene el marcador. Una que no lo tenga se quedaría sin
           hoja de estilo y sin el guion de tema, y el build lo diría.
        2. La expansión deja dentro la hoja de estilo. Si la plantilla se
           rompiera, el sitio saldría sin CSS y pasaría todas las demás
           comprobaciones: el HTML sería válido, sólo ilegible.
        3. La plantilla no viaja a dist/. Si lo hiciera sería una página
           huérfana, y la guarda de cobertura de `estructura.mjs` la
           denunciaría —pero es mejor no crearla que confiar en que otro la
           cace—.
    """
    plantilla = DIST / "_cabecera.html"
    if not plantilla.exists():
        sys.exit("BUILD ABORTADO: falta web/_cabecera.html")
    # El comentario explicativo del archivo no viaja: es documentación para
    # quien lo edite, no marcado para el navegador.
    cuerpo = re.sub(r"^<!--.*?-->\n", "", plantilla.read_text(encoding="utf-8"), flags=re.S)
    plantilla.unlink()

    sin_marcador, sin_css = [], []
    for pagina in sorted(DIST.glob("*.html")):
        s = pagina.read_text(encoding="utf-8")
        m = re.search(r'<head\s+data-titulo="([^"]*)"\s+data-descripcion="([^"]*)"\s*>\s*</head>',
                      s, re.S)
        if not m:
            sin_marcador.append(pagina.name)
            continue
        head = (cuerpo.replace("{{titulo}}", m.group(1))
                      .replace("{{descripcion}}", m.group(2)))
        s = s[:m.start()] + "<head>\n" + head + "</head>" + s[m.end():]
        if 'href="assets/css/app.css"' not in s:
            sin_css.append(pagina.name)
        pagina.write_text(s, encoding="utf-8")

    if sin_marcador or sin_css:
        if sin_marcador:
            print("  PÁGINAS SIN MARCADOR DE CABECERA:")
            for n in sin_marcador:
                print(f"    · {n}")
        if sin_css:
            print("  PÁGINAS QUE QUEDARON SIN HOJA DE ESTILO:")
            for n in sin_css:
                print(f"    · {n}")
        sys.exit("BUILD ABORTADO: la cabecera no se expandió en todas las páginas.")

    print(f"  cabeceras        : {len(list(DIST.glob('*.html')))} expandidas "
          "desde web/_cabecera.html")


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
                           capture_output=True, encoding="utf-8", errors="replace",
                           check=False)
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

    expandir_cabeceras()
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
