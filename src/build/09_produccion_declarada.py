"""Build 09 — Producción declarada por las Facultades, fuera de Scopus.

QUÉ RESUELVE
    Una Facultad puede publicar en su propio sitio una lista de producción
    que Scopus no indexa completa. Eso es evidencia real de producción
    institucional, pero no es un dato Scopus/SciVal: no tiene criterio de
    indexación equivalente, y SciVal no lo mide, así que no existe citas ni
    FWCI para ninguno de estos registros. Mezclarlo en los gráficos que ya
    asumen Scopus+SciVal presentaría datos con calidad y comparabilidad
    distintas como si fueran la misma medición — exactamente lo que este
    proyecto evita a propósito.

    Este build publica, en cambio, un CORPUS PARALELO DECLARADO: sólo
    RECUENTOS (nunca impacto) por Facultad × año, en su propia sección del
    sitio (`produccion-ampliada.html`), nunca mezclado con
    `data/processed/produccion.json` ni ningún otro artefacto Scopus/SciVal.
    Sigue el principio ya declarado en `src/review/build_hallazgos.py` y
    `docs/DECISIONS.md` (D-206, D-341): "si alguna vez entrara, entraría
    como corpus paralelo declarado, con su propia entrada en
    config/sources.yml y su propio denominador".

MECANISMO GENERAL, NO HARDCODEADO A UNA FACULTAD (PD-01)
    Este script no menciona "Medicina" en ningún lado. Descubre qué fuentes
    aportan producción declarada iterando `config/sources.yml` y quedándose
    con las que traen `corpus_paralelo_declarado: true` — hoy sólo
    `facultad_medicina_publicaciones`. Otra Facultad que sume su propio
    listado más adelante sólo necesita: (a) un conector que escriba un JSON
    con el mismo esquema (ver el docstring de
    `src/enrich/facultad_medicina_publicaciones.py`), y (b) su propia
    entrada en `sources.yml` con esa misma bandera. Nada de este archivo
    cambia.

    Si ninguna fuente trae la bandera (clon fresco del proyecto, u otra
    institución que replica el sistema sin ningún listado propio), el build
    igual corre y publica un artefacto con listas vacías — este dato es
    opcional por diseño, a diferencia de la auditoría (`08_...`), que si
    falta SÍ detiene el build.

    PASO A PASO PARA PD-01
    1. Lee cada JSON declarado, valida que cada registro traiga `facultad`,
       `anio`, `doi`, `en_universo_scopus` — lo que falte se cuenta en
       `registros_invalidos`, nunca se descarta en silencio.
    2. Deduplica por (facultad, doi) normalizado, sólo entre registros CON
       doi — sin doi no hay clave confiable, así que esos nunca se
       deduplican (límite conocido, declarado en el resumen, no inventado).
    3. Separa `en_universo_scopus` (ya contado en el resto del sitio — pura
       divulgación) de `fuera_del_universo` (el conjunto nuevo real).
    4. Dentro de `fuera_del_universo`, separa por la ventana temporal del
       proyecto (`config/institution.yml`, hoy 2023-2025): `en_ventana` es
       el recuento principal; `fuera_de_ventana`/`sin_anio` NUNCA se ocultan
       — van a una nota de transparencia aparte.
    5. Agrega `en_ventana` por (facultad, año) para la tabla principal.

SEGUNDA FUENTE, DE OTRA NATURALEZA (PD-02)
    `internal/openalex_cobertura.csv` (V2-26) es OpenAlex atribuyéndole a la
    institución obras que el universo Scopus no tiene — no una Facultad
    declarando su propia lista editorial. Cada candidato pasa por revisión
    humana caso por caso, vía `internal/revision_cobertura_openalex.html` y
    `src/review/apply_openalex_review.py`, antes de contarse aquí como
    `CONFIRMADO_PRODUCCION_UFT`: los que siguen `PENDIENTE_REVISION_HUMANA`
    NUNCA se cuentan como producción confirmada, y ese recuento pendiente se
    publica igual, para que no quede oculto que existen candidatos aún sin
    resolver.

    Esta fuente no trae `facultad` —es evidencia por autor, no una
    declaración editorial de una unidad— así que no entra al mecanismo de
    `corpus_paralelo_declarado` ni a la tabla Facultad × año: tiene su
    propia sección, con su propia tabla por año.

    El total combinado (`total_fuera_de_scopus`) NO es un tercer indicador
    con su propia entrada en `sources.yml`: es aritmética sobre PD-01 y
    PD-02 —unión por DOI normalizado, restando lo que aparece en ambas
    fuentes— declarada aquí en vez de dejar que cada consumidor la repita o
    la haga mal.

Salida:
    data/processed/produccion_declarada.json
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import common_build as b

if sys.platform == "win32":
    # La consola de Windows usa cp1252 por defecto: revienta cualquier print()
    # con caracteres como "→"/"✗"/"⚠". Mismo patrón que src/enrich/orcid_openalex.py.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CAMPOS_REQUERIDOS = {"facultad", "anio", "doi", "en_universo_scopus"}


def _fuentes_declaradas() -> list[dict]:
    """Entradas de config/sources.yml con corpus_paralelo_declarado: true."""
    out = []
    for clave, spec in b.SOURCES.items():
        if spec.get("corpus_paralelo_declarado"):
            out.append({"clave": clave, "spec": spec})
    return out


def _leer_registros(spec: dict) -> tuple[list[dict], list[str]]:
    ruta = b.ROOT / spec["salida_declarada"]
    if not ruta.exists():
        return [], [f"falta {ruta.relative_to(b.ROOT)}"]
    registros = json.loads(ruta.read_text(encoding="utf-8"))
    validos, invalidos = [], []
    for r in registros:
        if CAMPOS_REQUERIDOS - set(r.keys()):
            invalidos.append(r.get("titulo", "(sin título)"))
            continue
        validos.append(r)
    return validos, invalidos


def _deduplicar(registros: list[dict], clave_unidad=lambda r: r["facultad"]) -> tuple[list[dict], int]:
    """Agrupa por (unidad, doi normalizado) entre los que TIENEN doi.

    Sin doi no hay clave confiable — esos registros nunca se deduplican
    (se documenta como límite conocido, no se inventa una clave). `unidad`
    es `facultad` por defecto (PD-01, siempre canónica); PD-03 pasa
    `facultad or unidad_declarada` porque no todas sus filas tienen
    Facultad validada, y dos filas de la MISMA unidad en bruto con el mismo
    DOI siguen siendo el mismo duplicado que hay que colapsar.
    """
    con_doi, sin_doi = [], []
    for r in registros:
        (con_doi if r.get("doi") else sin_doi).append(r)

    vistos: dict[tuple[str, str], dict] = {}
    colapsados = 0
    for r in con_doi:
        clave = (clave_unidad(r), str(r["doi"]).strip().lower())
        if clave in vistos:
            colapsados += 1
            continue
        vistos[clave] = r
    return list(vistos.values()) + sin_doi, colapsados


def _dois(registros: list[dict]) -> set[str]:
    return {str(r["doi"]).strip().lower() for r in registros if r.get("doi")}


def _anio_valido(r: dict, inicio: int, fin: int) -> str:
    """'en_ventana' | 'fuera_de_ventana' | 'sin_anio'."""
    crudo = str(r.get("anio") or "").strip()
    if not crudo.isdigit():
        return "sin_anio"
    return "en_ventana" if inicio <= int(crudo) <= fin else "fuera_de_ventana"


def _particionar_por_ventana(registros: list[dict], inicio: int, fin: int
                              ) -> tuple[list[dict], list[dict], list[dict]]:
    """(en_ventana, fuera_de_ventana, sin_anio) — una sola pasada, reutilizada
    por PD-01/PD-02/PD-03: las tres fuentes separan su recuento principal de
    lo que queda fuera de la ventana temporal exactamente de la misma forma,
    aunque el resto de su procesamiento difiera."""
    por_ventana = defaultdict(list)
    for r in registros:
        por_ventana[_anio_valido(r, inicio, fin)].append(r)
    return por_ventana["en_ventana"], por_ventana["fuera_de_ventana"], por_ventana["sin_anio"]


def _por_facultad_anio(registros: list[dict]) -> list[dict]:
    """Cuenta por (facultad, año) y devuelve la lista ordenada {facultad,
    anio, n} — la tabla principal de PD-01 y PD-03 (PD-02 no tiene facultad
    y agrega sólo por año, así que no comparte este helper)."""
    conteo = Counter((r["facultad"], int(r["anio"])) for r in registros)
    return sorted(
        ({"facultad": f, "anio": a, "n": n} for (f, a), n in conteo.items()),
        key=lambda x: (x["facultad"], x["anio"]),
    )


OPENALEX_COBERTURA = b.ROOT / "internal" / "openalex_cobertura.csv"


def _leer_openalex_cobertura() -> tuple[list[dict], bool]:
    """Filas de internal/openalex_cobertura.csv (V2-26), si existe.

    Es capa interna —cada fila trae `motivo`/`consecuencia` que no se
    publican—; este build sólo cuenta, nunca reexpone las filas."""
    if not OPENALEX_COBERTURA.exists():
        return [], False
    with OPENALEX_COBERTURA.open(encoding="utf-8") as f:
        return list(csv.DictReader(f)), True


AUTOARCHIVO_PRODUCCION = b.ROOT / "data" / "enriched" / "autoarchivo_produccion.json"


def _leer_autoarchivo_produccion() -> tuple[list[dict], bool]:
    """Filas de data/enriched/autoarchivo_produccion.json (PD-03), si existe."""
    if not AUTOARCHIVO_PRODUCCION.exists():
        return [], False
    return json.loads(AUTOARCHIVO_PRODUCCION.read_text(encoding="utf-8")), True


OBRAS_EXTERNAS = b.ROOT / "internal" / "obras_externas_cobertura.csv"


def _leer_obras_externas() -> tuple[list[dict], bool]:
    """Filas de internal/obras_externas_cobertura.csv (PD-04), si existe.

    Capa interna —cada fila trae `motivo`/`consecuencia` y la afiliación en
    bruto, que no se publican—; este build sólo cuenta, nunca reexpone las
    filas."""
    if not OBRAS_EXTERNAS.exists():
        return [], False
    with OBRAS_EXTERNAS.open(encoding="utf-8") as f:
        return list(csv.DictReader(f)), True


def main() -> None:
    b.banner("BUILD 09 — PRODUCCIÓN DECLARADA POR LAS FACULTADES (FUERA DE SCOPUS)")

    ventana = b.INSTITUTION["ventana_temporal"]
    inicio, fin = ventana["anio_inicio"], ventana["anio_fin"]

    fuentes_meta = []
    todos_validos: list[dict] = []
    total_leido = 0
    total_invalidos = 0

    for f in _fuentes_declaradas():
        clave, spec = f["clave"], f["spec"]
        registros, invalidos = _leer_registros(spec)
        total_leido += len(registros) + len(invalidos)
        total_invalidos += len(invalidos)
        todos_validos.extend(registros)
        fuentes_meta.append({
            "clave": clave,
            "nombre": spec.get("nombre"),
            "conector": spec.get("conector"),
            "fecha_ejecucion": spec.get("fecha_ejecucion"),
            "registros_leidos": len(registros),
            "registros_invalidos": len(invalidos),
        })

    deduplicados, colapsados = _deduplicar(todos_validos)

    en_universo = [r for r in deduplicados if r.get("en_universo_scopus")]
    fuera_del_universo = [r for r in deduplicados if not r.get("en_universo_scopus")]

    en_ventana, fuera_de_ventana, sin_anio = _particionar_por_ventana(fuera_del_universo, inicio, fin)
    por_facultad_anio = _por_facultad_anio(en_ventana)

    conteo_fuera = Counter(r["facultad"] for r in fuera_de_ventana)
    conteo_sin_anio = Counter(r["facultad"] for r in sin_anio)
    facultades = sorted(set(conteo_fuera) | set(conteo_sin_anio))
    fuera_de_ventana_o_sin_anio = [
        {"facultad": fac, "fuera_de_ventana": conteo_fuera.get(fac, 0),
         "sin_anio": conteo_sin_anio.get(fac, 0)}
        for fac in facultades
    ]

    fecha_ejecucion_mas_reciente = max(
        (fm["fecha_ejecucion"] for fm in fuentes_meta if fm["fecha_ejecucion"]),
        default=None,
    )

    resumen = {
        "total_leido": total_leido,
        "registros_invalidos": total_invalidos,
        "duplicados_colapsados_por_doi": colapsados,
        "en_universo_scopus": len(en_universo),
        "fuera_del_universo": len(fuera_del_universo),
        "en_ventana": len(en_ventana),
        "fuera_de_ventana": len(fuera_de_ventana),
        "sin_anio": len(sin_anio),
    }

    # ── PD-02: producción confirmada por revisión de cobertura OpenAlex ──
    # Fuente distinta de PD-01 en naturaleza (ver docstring del módulo): sin
    # 'facultad', no entra al mecanismo de corpus_paralelo_declarado ni a la
    # tabla Facultad × año — tiene su propia sección, agregada sólo por año.
    filas_oa, existe_oa = _leer_openalex_cobertura()
    confirmadas_oa = [r for r in filas_oa if r.get("resolucion") == "CONFIRMADO_PRODUCCION_UFT"]
    pendientes_oa = sum(1 for r in filas_oa if r.get("resolucion") == "PENDIENTE_REVISION_HUMANA")
    descartadas_oa = sum(1 for r in filas_oa if (r.get("resolucion") or "").startswith("DESCARTADO"))

    oa_en_ventana, oa_fuera_de_ventana, oa_sin_anio = _particionar_por_ventana(confirmadas_oa, inicio, fin)

    conteo_oa_por_anio = Counter(int(r["anio"]) for r in oa_en_ventana)
    oa_por_anio = sorted(
        ({"anio": anio, "n": n} for anio, n in conteo_oa_por_anio.items()),
        key=lambda x: x["anio"],
    )

    resumen_oa = {
        "total_evaluados": len(filas_oa),
        "confirmadas": len(confirmadas_oa),
        "en_ventana": len(oa_en_ventana),
        "fuera_de_ventana": len(oa_fuera_de_ventana),
        "sin_anio": len(oa_sin_anio),
        "pendientes_revision_humana": pendientes_oa,
        "descartadas": descartadas_oa,
    }

    openalex_cobertura = {
        "disponible": existe_oa,
        "fuente": {
            "nombre": b.SOURCES.get("openalex_api", {}).get("nombre"),
            "conector": "src/enrich/openalex_cobertura.py",
            # La ruta de la herramienta de revisión NO viaja en el artefacto
            # público: `internal/` dejó de versionarse (D-SEC-01) y la
            # compuerta de CI de `main` rechaza cualquier mención suya en
            # `data/processed/`. Ninguna vista la consumía; la página nombra
            # la herramienta en prosa, donde es una indicación de método.
        },
        "resumen": resumen_oa,
        "por_anio": oa_por_anio,
        "nota": b.nota("PD-02"),
        "procedencia": b.procedencia(
            "PD-02",
            cubiertas=len(oa_en_ventana),
            n=len(confirmadas_oa),
            unidad="publicaciones confirmadas",
            corte=b.SOURCES.get("openalex_api", {}).get("fecha_ejecucion"),
        ) if existe_oa else None,
    }

    # ── PD-03: producción autoarchivada en el repositorio institucional ──
    # Tercera fuente, de otra naturaleza que PD-01 y PD-02: no es una
    # Facultad declarando su sitio (PD-01) ni una API externa con revisión
    # caso por caso (PD-02) — es la hoja AUTOARCHIVOS que biblioteca cura,
    # con Facultad/Escuela declarada EN BRUTO fila por fila (ver docstring
    # del módulo y de autoarchivo_produccion.py). Sólo las filas con
    # `facultad` VALIDADA entran a la tabla Facultad × año y al total
    # combinado; las que no, se cuentan aparte como `unidades_sin_mapeo`
    # (transparencia, nunca ocultas, nunca forzadas a una Facultad).
    filas_aa, existe_aa = _leer_autoarchivo_produccion()
    dedup_aa, colapsados_aa = _deduplicar(
        filas_aa, clave_unidad=lambda r: r.get("facultad") or r.get("unidad_declarada", ""))

    en_universo_aa = [r for r in dedup_aa if r.get("en_universo_scopus")]
    fuera_del_universo_aa = [r for r in dedup_aa if not r.get("en_universo_scopus")]

    aa_en_ventana, aa_fuera_de_ventana, aa_sin_anio = _particionar_por_ventana(fuera_del_universo_aa, inicio, fin)

    aa_en_ventana_con_facultad = [r for r in aa_en_ventana if r.get("facultad")]
    aa_en_ventana_sin_facultad = [r for r in aa_en_ventana if not r.get("facultad")]
    fuera_universo_con_facultad_aa = [r for r in fuera_del_universo_aa if r.get("facultad")]

    aa_por_facultad_anio = _por_facultad_anio(aa_en_ventana_con_facultad)

    conteo_sin_mapeo = Counter(r["unidad_declarada"] for r in aa_en_ventana_sin_facultad)
    aa_unidades_sin_mapeo = sorted(
        ({"unidad_declarada": u, "n": n} for u, n in conteo_sin_mapeo.items()),
        key=lambda x: (-x["n"], x["unidad_declarada"]),
    )

    resumen_aa = {
        "total_leido": len(filas_aa),
        "duplicados_colapsados_por_doi": colapsados_aa,
        "en_universo_scopus": len(en_universo_aa),
        "fuera_del_universo": len(fuera_del_universo_aa),
        "con_facultad_validada": len(fuera_universo_con_facultad_aa),
        "en_ventana_con_facultad": len(aa_en_ventana_con_facultad),
        "en_ventana_sin_facultad": len(aa_en_ventana_sin_facultad),
        "fuera_de_ventana": len(aa_fuera_de_ventana),
        "sin_anio": len(aa_sin_anio),
    }

    autoarchivo_produccion = {
        "disponible": existe_aa,
        "fuente": {
            "nombre": b.SOURCES.get("autoarchivo_biblioteca", {}).get("nombre"),
            "conector": "src/enrich/autoarchivo_produccion.py",
        },
        "resumen": resumen_aa,
        "por_facultad_anio": aa_por_facultad_anio,
        "unidades_sin_mapeo": aa_unidades_sin_mapeo,
        "nota": b.nota("PD-03"),
        "procedencia": b.procedencia(
            "PD-03",
            cubiertas=len(aa_en_ventana_con_facultad),
            n=len(fuera_universo_con_facultad_aa),
            unidad="publicaciones autoarchivadas",
            corte=b.SOURCES.get("autoarchivo_biblioteca", {}).get("fecha_export"),
        ) if existe_aa else None,
    }

    # ── PD-04: obras en repositorios de datos y acceso abierto ──
    # Cuarta fuente. Comparte NIVEL con PD-02 —cada obra pasa por revisión
    # humana antes de contarse— pero no su mecanismo: PD-02 recupera de un
    # índice bibliográfico por ROR institucional; ésta recupera de tres
    # repositorios de outputs no tradicionales, por ORCID confirmado y por
    # afiliación declarada. Tampoco trae `facultad` (es evidencia por obra,
    # no una declaración editorial de una unidad), así que va por año, como
    # PD-02, y nunca a la tabla Facultad x año.
    #
    # La misma obra puede estar en dos o en las tres fuentes con el mismo
    # DOI. Se cuenta UNA vez: son la misma obra corroborada dos veces, no dos
    # obras (Regla 3 de docs/METODOLOGIA_FUERA_DE_SCOPUS.md). Las obras sin
    # DOI no se pueden colapsar por clave y se cuentan una por fila — límite
    # conocido, declarado en el resumen, no escondido.
    filas_oe, existe_oe = _leer_obras_externas()
    confirmadas_oe = [r for r in filas_oe if r.get("resolucion") == "CONFIRMADO_PRODUCCION_UFT"]
    pendientes_oe = sum(1 for r in filas_oe if r.get("resolucion") == "PENDIENTE_REVISION_HUMANA")
    descartadas_oe = sum(1 for r in filas_oe if (r.get("resolucion") or "").startswith("DESCARTADO"))
    descartadas_version_oe = sum(
        1 for r in filas_oe if r.get("resolucion") == "DESCARTADO_VERSION_DE_OBRA_YA_CONTADA")

    oe_en_ventana, oe_fuera_de_ventana, oe_sin_anio = _particionar_por_ventana(
        confirmadas_oe, inicio, fin)

    dois_oe = _dois(oe_en_ventana)
    sin_doi_oe = sum(1 for r in oe_en_ventana if not r.get("doi"))
    oe_obras_en_ventana = len(dois_oe) + sin_doi_oe
    corroboradas_oe = len(oe_en_ventana) - oe_obras_en_ventana

    # El recuento por año se hace sobre obras, no sobre filas: si el mismo
    # DOI está confirmado en dos fuentes, su año se cuenta una vez.
    vistos: set[str] = set()
    conteo_oe_por_anio: Counter = Counter()
    for r in oe_en_ventana:
        doi = (r.get("doi") or "").strip().lower()
        if doi:
            if doi in vistos:
                continue
            vistos.add(doi)
        conteo_oe_por_anio[int(r["anio"])] += 1
    oe_por_anio = sorted(
        ({"anio": anio, "n": n} for anio, n in conteo_oe_por_anio.items()),
        key=lambda x: x["anio"],
    )

    conteo_oe_por_fuente = Counter(r.get("fuente", "") for r in oe_en_ventana)
    oe_por_fuente = sorted(
        ({"fuente": f, "n": n} for f, n in conteo_oe_por_fuente.items() if f),
        key=lambda x: (-x["n"], x["fuente"]),
    )

    resumen_oe = {
        "total_evaluados": len(filas_oe),
        "confirmadas": len(confirmadas_oe),
        "en_ventana": oe_obras_en_ventana,
        "filas_en_ventana": len(oe_en_ventana),
        "corroboradas_entre_fuentes": corroboradas_oe,
        "sin_doi_en_ventana": sin_doi_oe,
        "fuera_de_ventana": len(oe_fuera_de_ventana),
        "sin_anio": len(oe_sin_anio),
        "pendientes_revision_humana": pendientes_oe,
        "descartadas": descartadas_oe,
        "descartadas_por_ser_otra_version": descartadas_version_oe,
    }

    obras_externas = {
        "disponible": existe_oe,
        "fuente": {
            "nombre": "DataCite, Europe PMC y Zenodo",
            "conector": "src/enrich/obras_externas.py",
        },
        "resumen": resumen_oe,
        "por_anio": oe_por_anio,
        "por_fuente": oe_por_fuente,
        "nota": b.nota("PD-04"),
        "procedencia": b.procedencia(
            "PD-04",
            cubiertas=oe_obras_en_ventana,
            n=len(confirmadas_oe),
            unidad="obras confirmadas",
            # La fecha de referencia de PD-04 es la de la consulta que armó la
            # cola, no la fecha de corte de SciVal: `procedencia()` cae en esa
            # por defecto, y mostrarla aquí publicaría un corte que no tiene
            # ninguna relación con este dato (lo advierte su propio docstring).
            corte=max((r.get("fecha_consulta") or "" for r in filas_oe), default="") or None,
        ) if existe_oe else None,
    }

    # ── Total combinado: unión por DOI entre PD-01, PD-02, PD-03 y PD-04 ──
    # No es un cuarto indicador con fuente propia: es la suma de los tres de
    # arriba, restando lo que más de una fuente ya declara (verificado: hay
    # solapamiento real entre las tres, no sólo entre pares — Medicina
    # aparece declarada en su propio sitio Y autoarchivada por sus autores).
    dois_pd01 = _dois(en_ventana)
    dois_pd02 = _dois(oa_en_ventana)
    dois_pd03 = _dois(aa_en_ventana_con_facultad)
    dois_pd04 = dois_oe
    union_dois = dois_pd01 | dois_pd02 | dois_pd03 | dois_pd04
    sin_doi_pd01 = sum(1 for r in en_ventana if not r.get("doi"))
    sin_doi_pd02 = sum(1 for r in oa_en_ventana if not r.get("doi"))
    sin_doi_pd03 = sum(1 for r in aa_en_ventana_con_facultad if not r.get("doi"))
    sin_doi_pd04 = sin_doi_oe
    total_en_ventana = (len(union_dois) + sin_doi_pd01 + sin_doi_pd02
                        + sin_doi_pd03 + sin_doi_pd04)
    # PD-04 aporta su recuento YA colapsado entre sus tres fuentes: sumar sus
    # filas aquí contaría dos veces la corroboración que ese indicador ya
    # descontó, y el número de 'repetidas entre fuentes' dejaría de cuadrar.
    duplicados_entre_fuentes = (
        len(en_ventana) + len(oa_en_ventana) + len(aa_en_ventana_con_facultad)
        + oe_obras_en_ventana - total_en_ventana
    )

    total_fuera_de_scopus = {
        "en_ventana": total_en_ventana,
        "pd01_en_ventana": len(en_ventana),
        "pd02_en_ventana": len(oa_en_ventana),
        "pd03_en_ventana": len(aa_en_ventana_con_facultad),
        "pd04_en_ventana": oe_obras_en_ventana,
        "duplicados_entre_fuentes": duplicados_entre_fuentes,
    } if (fuentes_meta or existe_oa or existe_aa or existe_oe) else None

    salida = {
        "meta": b.build_meta(),
        "fuentes": fuentes_meta,
        "ventana": {"inicio": inicio, "fin": fin},
        "resumen": resumen,
        "por_facultad_anio": por_facultad_anio,
        "fuera_de_ventana_o_sin_anio": fuera_de_ventana_o_sin_anio,
        "nota": b.nota("PD-01"),
        "procedencia": b.procedencia(
            "PD-01",
            cubiertas=len(en_ventana),
            n=len(fuera_del_universo),
            unidad="publicaciones declaradas",
            corte=fecha_ejecucion_mas_reciente,
        ) if fuentes_meta else None,
        "openalex_cobertura": openalex_cobertura,
        "autoarchivo_produccion": autoarchivo_produccion,
        "obras_externas": obras_externas,
        "total_fuera_de_scopus": total_fuera_de_scopus,
    }
    b.write_json(salida, "produccion_declarada.json")

    if not fuentes_meta and not existe_oa and not existe_aa and not existe_oe:
        print("  ninguna fuente declarada: ni config/sources.yml, ni "
              "internal/openalex_cobertura.csv, ni data/enriched/autoarchivo_produccion.json, "
              "ni internal/obras_externas_cobertura.csv")
        print("  OK · data/processed/produccion_declarada.json (vacío, sin fuentes)")
        return

    if fuentes_meta:
        print(f"  fuentes declaradas   : {len(fuentes_meta)}")
        print(f"  total leído          : {total_leido} ({total_invalidos} inválido(s))")
        print(f"  duplicados colapsados: {colapsados} (por facultad+DOI)")
        print(f"  en universo Scopus   : {len(en_universo)} (divulgación, no headline)")
        print(f"  fuera del universo   : {len(fuera_del_universo)}")
        print(f"    en ventana {inicio}-{fin} : {len(en_ventana)}")
        print(f"    fuera de ventana        : {len(fuera_de_ventana)}")
        print(f"    sin año                 : {len(sin_anio)}")
    else:
        print("  PD-01: ninguna fuente con 'corpus_paralelo_declarado: true'")

    if existe_oa:
        print(f"\n  OpenAlex evaluados   : {len(filas_oa)} (V2-26)")
        print(f"  confirmadas          : {len(confirmadas_oa)}")
        print(f"    en ventana {inicio}-{fin} : {len(oa_en_ventana)}")
        print(f"    fuera de ventana        : {len(oa_fuera_de_ventana)}")
        print(f"    sin año                 : {len(oa_sin_anio)}")
        print(f"  pendientes de revisión: {pendientes_oa} (no se cuentan)")
        print(f"  descartadas          : {descartadas_oa}")
    else:
        print("\n  PD-02: falta internal/openalex_cobertura.csv (correr "
              "src/enrich/openalex_cobertura.py)")

    if existe_aa:
        print(f"\n  Autoarchivo leído   : {len(filas_aa)} ({colapsados_aa} duplicados colapsados)")
        print(f"  fuera del universo  : {len(fuera_del_universo_aa)}")
        print(f"    con Facultad validada, en ventana {inicio}-{fin} : {len(aa_en_ventana_con_facultad)}")
        print(f"    sin Facultad validada, en ventana {inicio}-{fin}: {len(aa_en_ventana_sin_facultad)}"
              " (no se cuentan por Facultad)")
        print(f"    fuera de ventana                        : {len(aa_fuera_de_ventana)}")
        print(f"    sin año                                 : {len(aa_sin_anio)}")
    else:
        print("\n  PD-03: falta data/enriched/autoarchivo_produccion.json (correr "
              "src/enrich/autoarchivo_produccion.py)")

    if existe_oe:
        print(f"\n  Repositorios externos: {len(filas_oe)} evaluados (PD-04)")
        print(f"  confirmadas          : {len(confirmadas_oe)} filas")
        print(f"    en ventana {inicio}-{fin} : {oe_obras_en_ventana} obras"
              f" ({corroboradas_oe} corroboradas entre fuentes, contadas una vez)")
        print(f"    fuera de ventana        : {len(oe_fuera_de_ventana)}")
        print(f"    sin año                 : {len(oe_sin_anio)}")
        print(f"  pendientes de revisión: {pendientes_oe} (no se cuentan)")
        print(f"  descartadas          : {descartadas_oe}"
              f" ({descartadas_version_oe} por ser otra versión de una obra ya contada)")
    else:
        print("\n  PD-04: falta internal/obras_externas_cobertura.csv (correr "
              "src/enrich/obras_externas.py)")

    if total_fuera_de_scopus:
        print(f"\n  TOTAL fuera de Scopus, en ventana: {total_fuera_de_scopus['en_ventana']}"
              f"  ({len(en_ventana)} PD-01 + {len(oa_en_ventana)} PD-02"
              f" + {len(aa_en_ventana_con_facultad)} PD-03"
              f" + {oe_obras_en_ventana} PD-04"
              f" - {duplicados_entre_fuentes} repetidas entre fuentes)")

    print("\n  OK · data/processed/produccion_declarada.json")


if __name__ == "__main__":
    main()
