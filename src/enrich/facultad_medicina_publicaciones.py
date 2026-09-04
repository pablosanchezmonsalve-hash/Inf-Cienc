"""Colecta y cruza las publicaciones listadas en el sitio de la Facultad de
Medicina y Salud UFT (V2-27).

QUÉ RESUELVE
    `https://facultadmedicina.finis.cl/investigacion-y-postgrado/publicaciones/`
    publica la producción de la Facultad (Medicina por año, Enfermería,
    Nutrición y Dietética, y Libros) con su DOI. Este script la baja vía la
    API REST de WordPress, la estructura en registros (sección, año, título,
    primer autor, autor de correspondencia, autores UFT, DOI) y la cruza
    contra el universo Scopus (`data/interim/publications_universe.csv`) para
    separar lo que la Facultad declara que ya está en el corpus de lo que
    publica por fuera de él.

QUÉ NO HACE
    No inserta nada en el corpus Scopus (D-314: confirmar que una obra es
    producción real UFT no la convierte en parte del universo — ampliarlo
    sería mezclar criterios de indexación distintos). Nunca toca
    `data/interim/publications_universe.csv` ni ningún indicador que
    reporte citas/FWCI (eso sólo existe para lo indexado en Scopus, vía
    SciVal). Sí alimenta, como RECUENTO (nunca impacto), el indicador
    PD-01 "Producción declarada por las Facultades, fuera de Scopus" —
    ver `src/build/09_produccion_declarada.py` — que lo muestra en una
    sección aparte del sitio, no en los gráficos de producción/impacto.

ESQUEMA DE SALIDA (convención para cualquier conector de este tipo)
    Cada registro trae `facultad` (nombre CANÓNICO, el mismo que usa
    `config/matching_rules.yml` -> unidad_academica.jerarquia.*.facultad;
    NO la cadena cruda del sitio), `anio` (string, "" si no declarado),
    `doi` (normalizado, "" si no hay), `en_universo_scopus` (bool), y
    `eid_scopus`/`anio_scopus` SÓLO cuando `en_universo_scopus` es
    verdadero (no siempre están las tres claves). Otra Facultad que sume
    su propio listado más adelante escribe a su propio
    `data/enriched/<algo>_publicaciones.json` con este mismo esquema, y
    se declara en `config/sources.yml` con `corpus_paralelo_declarado:
    true` — `09_produccion_declarada.py` la descubre sola, sin que este
    archivo ni ningún otro nombren esa Facultad.

USO
    python3 src/enrich/facultad_medicina_publicaciones.py            # baja y estructura
    python3 src/enrich/facultad_medicina_publicaciones.py --test     # valida el parser sin red

Salida:
    data/enriched/facultad_medicina_publicaciones.json   registros estructurados, con 'facultad'
    internal/facultad_medicina_cruce.csv                 cruce contra el universo (capa interna)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

import pandas as pd

if sys.platform == "win32":
    # Mismo patrón que el resto de src/enrich: la consola cp1252 revienta
    # cualquier print() con acentos/guiones. Clave con títulos en español.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audit"))
import common as c  # noqa: E402

ROOT = c.ROOT
URL_PAGE = (
    "https://facultadmedicina.finis.cl/wp-json/wp/v2/pages"
    "?slug=publicaciones&_fields=id,title,link,content"
)
SALIDA_JSON = ROOT / "data" / "enriched" / "facultad_medicina_publicaciones.json"
SALIDA_CSV = ROOT / "internal" / "facultad_medicina_cruce.csv"

# Nombre CANÓNICO, el mismo que usa `config/matching_rules.yml` ->
# unidad_academica.jerarquia.*.facultad — no la cadena cruda del sitio
# ("Facultad de Medicina"). Es la convención que sigue cualquier conector de
# "producción declarada": sin este campo, `09_produccion_declarada.py` no
# puede agrupar por facultad sin hardcodear un nombre de facultad en el
# pipeline de build.
FACULTAD = "Facultad de Medicina y Salud"
UNIVERSO = ROOT / "data" / "interim" / "publications_universe.csv"

# Muestra reducida del marcado real de la página (ver SESSION_NOTES 2026-09-01):
# permite --test sin red ni archivos externos. Reproduce los patrones del
# `publicaciones` de WordPress (id 10009): badges, h4, dl de autores y Ver DOI.
FIXTURE = (
    "<h2 class='mb-4'>Producción académica disponible</h2>"
    "<h2>Publicaciones por año</h2>"
    "<h2>2025: 2 publicaciones</h2>"
    """<div class="row g-4 sima-pub-results">
      <div class="col-md-6 col-xl-4 sima-pub-item">
        <article class="card h-100 border-0 shadow-sm sima-pub-card">
          <div class="card-body p-4 d-flex flex-column">
            <div class="d-flex justify-content-between align-items-start gap-3 mb-3">
              <span class="badge rounded-pill text-bg-dark">#001</span>
              <span class="badge rounded-pill text-bg-light">2025</span>
            </div>
            <h4 class="h6 mb-3">Unraveling the association between obesity and climacteric symptoms</h4>
            <dl class="row small mb-3 sima-pub-meta">
              <dt class="col-sm-4 text-muted fw-normal">Primer autor</dt>
              <dd class="col-sm-8 mb-2">Aedo, Sócrates</dd>
              <dt class="col-sm-4 text-muted fw-normal">Autor/a correspondencia</dt>
              <dd class="col-sm-8 mb-2">Aedo, Sócrates</dd>
              <dt class="col-sm-4 text-muted fw-normal">Autor/a UFT</dt>
              <dd class="col-sm-8 mb-2">Aedo, Sócrates</dd>
            </dl>
            <div class="mt-auto">
              <a class="btn btn-sm btn-outline-primary mt-2" href="https://doi.org/10.1097/GME.0000000000002620" target="_blank" rel="noopener noreferrer">Ver DOI</a>
            </div>
          </div>
        </article>
      </div>
    </div>"""
    "<h2>Producción editorial disponible</h2>"
    """<div class="col-md-6 col-xl-4 sima-pub-item">
      <article class="card h-100 border-0 shadow-sm sima-pub-card">
        <div class="card-body p-4 d-flex flex-column">
          <h4 class="h6 mb-3">Médico y escarabajo</h4>
          <dl class="row small mb-3 sima-pub-meta">
            <dt class="col-sm-4 text-muted fw-normal">Primer autor</dt>
            <dd class="col-sm-8 mb-2">Autor, Nombre</dd>
          </dl>
        </div>
      </article>
    </div>"""
)


def _pagina_con(content: str) -> dict:
    return json.loads(
        json.dumps(
            [{"id": 10009, "title": {"rendered": "Publicaciones"},
              "content": {"rendered": content}}]
        )
    )

# Encabezados h2 que NO son grupos de año reales: agrupan bloques auxiliares.
BLOQUES_AUXILIARES = {
    "Producción académica disponible",
    "Publicaciones por año",
}

SECCIONES_POR_ENCABEZADO = {
    "Publicaciones por año": "Escuela de Medicina",
    "Publicaciones por autor últimos 10 años": "Enfermería",
    "Publicaciones disponibles": "Nutrición y Dietética",
    "Producción editorial disponible": "Libros",
}

_RE_GRUPO_ANIO = re.compile(r"^\d{4}:\s*\d+\s+publicaciones$")


def _seccion_de_encabezado(lab: str) -> str:
    """Mapea un h2 de la página a una sección. Los grupos por año
    ("2025: 136 publicaciones") pertenecen a Escuela de Medicina."""
    if _RE_GRUPO_ANIO.match(lab):
        return "Escuela de Medicina"
    return SECCIONES_POR_ENCABEZADO.get(lab, lab)


def normalizar_doi(doi: str) -> str:
    """Reduce a un DOI a secas y en minúsculas para el cruce."""
    if not doi:
        return ""
    doi = doi.strip()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
    doi = re.sub(r"^doi:\s*", "", doi, flags=re.IGNORECASE)
    doi = doi.strip(".")
    return doi.lower()


def limpiar_html(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()


def extraer(pages_json: dict) -> list[dict]:
    """Parsea la respuesta de wp-json y devuelve los registros estructurados.

    La página guarda todo en `content.rendered`. Cada publicación es un div
    `.sima-pub-item` con: badge índice, badge año, `<h4>` título, un `<dl>`
    con Primer autor / Autor/a correspondencia / Autor/a UFT, y un enlace
    "Ver DOI". La sección (escuela) se deduce del `<h2>` más cercano que la
    precede (los grupos "YYYY: N publicaciones" pertenecen a Medicina).
    """
    if isinstance(pages_json, list):
        pages_json = pages_json[0]
    content = pages_json.get("content", {}).get("rendered", "")

    # Posición y etiqueta de cada encabezado h2 (define la sección actual).
    h2s = [
        (m.start(), limpiar_html(m.group(1)))
        for m in re.finditer(r'<h2[^>]*>(.*?)</h2>', content, re.S)
    ]

    registros = []
    for m in re.finditer(r'<div class="col-md-6 col-xl-4 sima-pub-item"', content):
        pos = m.start()
        # sección = último h2 que está antes de este item
        seccion = "?"
        for p, lab in h2s:
            if p < pos:
                seccion = _seccion_de_encabezado(lab)
            else:
                break

        bloque = content[pos:]
        cierre = bloque.find("</article>")
        if cierre != -1:
            bloque = bloque[: cierre + 10]

        # badges: índice y año
        badges = re.findall(r'<span class="badge[^"]*"[^>]*>(.*?)</span>', bloque, re.S)
        indice = ""
        anio = ""
        for b in badges:
            t = limpiar_html(b)
            if re.fullmatch(r"#\d+", t):
                indice = t
            elif re.fullmatch(r"\d{4}", t):
                anio = t

        # título
        tm = re.search(r"<h4[^>]*>(.*?)</h4>", bloque, re.S)
        titulo = limpiar_html(tm.group(1)) if tm else ""

        # pares dt/dd del dl
        campos = {}
        for dt, dd in re.findall(r"<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>", bloque, re.S):
            campos[limpiar_html(dt)] = limpiar_html(dd)

        # DOI
        doi = ""
        am = re.search(r'<a[^>]*href="([^"]*doi[^"]*)"[^>]*>Ver DOI', bloque, re.I)
        if am:
            doi = normalizar_doi(am.group(1))

        registros.append(
            {
                "facultad": FACULTAD,
                "indice": indice,
                "seccion": seccion,
                "anio": anio,
                "titulo": titulo,
                "primer_autor": campos.get("Primer autor", ""),
                "autor_correspondencia": campos.get("Autor/a correspondencia", ""),
                "autor_uft": campos.get("Autor/a UFT", ""),
                "doi": doi,
            }
        )
    return registros


def cruzar(registros: list[dict], universo: pd.DataFrame) -> list[dict]:
    """Marca cada registro como en-universo si su DOI está en Scopus."""
    doi_universo = set(
        universo["doi"].dropna().astype(str).str.lower().str.strip()
    )
    for r in registros:
        r["en_universo_scopus"] = bool(r["doi"] and r["doi"] in doi_universo)
        if r["en_universo_scopus"]:
            fila = universo.loc[universo["doi"].astype(str).str.lower() == r["doi"]]
            if not fila.empty:
                r["eid_scopus"] = fila.iloc[0]["eid"]
                r["anio_scopus"] = int(fila.iloc[0]["anio"]) if pd.notna(fila.iloc[0]["anio"]) else None
    return registros


def run() -> list[dict]:
    """Baja la página vía wp-json y estructura los registros."""
    with urllib.request.urlopen(URL_PAGE, timeout=60) as resp:
        pages = json.loads(resp.read().decode("utf-8"))

    registros = extraer(pages)
    universo = pd.read_csv(UNIVERSO)
    registros = cruzar(registros, universo)
    return registros


def _guardar(registros: list[dict]) -> None:
    SALIDA_JSON.parent.mkdir(parents=True, exist_ok=True)
    SALIDA_CSV.parent.mkdir(parents=True, exist_ok=True)
    SALIDA_JSON.write_text(
        json.dumps(registros, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    df = pd.DataFrame(registros)

    claves = [
        "facultad", "indice", "seccion", "anio", "titulo", "primer_autor",
        "autor_correspondencia", "autor_uft", "doi",
        "en_universo_scopus", "eid_scopus", "anio_scopus",
    ]
    df[claves].to_csv(
        SALIDA_CSV, index=False, encoding="utf-8", na_rep=""
    )
    print(f"registros        : {len(registros)}")
    print(f"con DOI          : {sum(1 for r in registros if r['doi'])}")
    print(f"en universo Scopus: {sum(1 for r in registros if r['en_universo_scopus'])}")


def test() -> int:
    """Valida el parser contra un fragmento del marcado real, sin red."""
    registros = extraer(_pagina_con(FIXTURE))
    fallos = []
    if len(registros) != 2:
        fallos.append(f"esperaba 2 registros, hay {len(registros)}")
    por_doi = {r["doi"]: r for r in registros if r["doi"]}
    p = por_doi.get("10.1097/gme.0000000000002620")
    if not p:
        fallos.append("no se encontró el DOI 10.1097/gme.0000000000002620")
    elif not (p["seccion"] == "Escuela de Medicina" and p["anio"] == "2025"):
        fallos.append(f"campos mal: {p}")
    if any(r.get("facultad") != FACULTAD for r in registros):
        fallos.append("algún registro no trae 'facultad' == FACULTAD")
    libros = [r for r in registros if r["seccion"] == "Libros"]
    if not libros or libros[0]["titulo"] != "Médico y escarabajo":
        fallos.append(f"sección Libros/editorial mal parseada: {libros}")
    for f in fallos:
        print("FALLA:", f)
    print(f"TEST OK · registros={len(registros)}, DOIs={sum(1 for r in registros if r['doi'])}")
    return 1 if fallos else 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true", help="valida el parser sin red")
    args = ap.parse_args()

    if args.test:
        sys.exit(test())

    registros = run()
    _guardar(registros)
    print("OK ·", SALIDA_JSON, "y", SALIDA_CSV)


if __name__ == "__main__":
    main()