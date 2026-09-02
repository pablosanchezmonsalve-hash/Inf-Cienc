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

MECANISMO GENERAL, NO HARDCODEADO A UNA FACULTAD
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

QUÉ HACE, PASO A PASO
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

Salida:
    data/processed/produccion_declarada.json
"""

from __future__ import annotations

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


def _deduplicar(registros: list[dict]) -> tuple[list[dict], int]:
    """Agrupa por (facultad, doi normalizado) entre los que TIENEN doi.

    Sin doi no hay clave confiable — esos registros nunca se deduplican
    (se documenta como límite conocido, no se inventa una clave).
    """
    con_doi, sin_doi = [], []
    for r in registros:
        (con_doi if r.get("doi") else sin_doi).append(r)

    vistos: dict[tuple[str, str], dict] = {}
    colapsados = 0
    for r in con_doi:
        clave = (r["facultad"], str(r["doi"]).strip().lower())
        if clave in vistos:
            colapsados += 1
            continue
        vistos[clave] = r
    return list(vistos.values()) + sin_doi, colapsados


def _anio_valido(r: dict, inicio: int, fin: int) -> str:
    """'en_ventana' | 'fuera_de_ventana' | 'sin_anio'."""
    crudo = str(r.get("anio") or "").strip()
    if not crudo.isdigit():
        return "sin_anio"
    return "en_ventana" if inicio <= int(crudo) <= fin else "fuera_de_ventana"


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

    por_ventana = defaultdict(list)
    for r in fuera_del_universo:
        por_ventana[_anio_valido(r, inicio, fin)].append(r)
    en_ventana = por_ventana["en_ventana"]
    fuera_de_ventana = por_ventana["fuera_de_ventana"]
    sin_anio = por_ventana["sin_anio"]

    conteo_principal = Counter(
        (r["facultad"], int(r["anio"])) for r in en_ventana
    )
    por_facultad_anio = sorted(
        (
            {"facultad": facultad, "anio": anio, "n": n}
            for (facultad, anio), n in conteo_principal.items()
        ),
        key=lambda x: (x["facultad"], x["anio"]),
    )

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
    }
    b.write_json(salida, "produccion_declarada.json")

    if not fuentes_meta:
        print("  ninguna fuente con 'corpus_paralelo_declarado: true' en config/sources.yml")
        print("  OK · data/processed/produccion_declarada.json (vacío, sin fuentes)")
        return

    print(f"  fuentes declaradas   : {len(fuentes_meta)}")
    print(f"  total leído          : {total_leido} ({total_invalidos} inválido(s))")
    print(f"  duplicados colapsados: {colapsados} (por facultad+DOI)")
    print(f"  en universo Scopus   : {len(en_universo)} (divulgación, no headline)")
    print(f"  fuera del universo   : {len(fuera_del_universo)}")
    print(f"    en ventana {inicio}-{fin} : {len(en_ventana)}")
    print(f"    fuera de ventana        : {len(fuera_de_ventana)}")
    print(f"    sin año                 : {len(sin_anio)}")
    print("\n  OK · data/processed/produccion_declarada.json")


if __name__ == "__main__":
    main()
