"""Build 07 — Jerarquía institucional para el motor de visualización (treemap).

QUÉ ES
    Reorganiza en árbol (Raíz > Facultad > Escuela) los mismos números que
    `P-07` ya publica en `series.json` de forma plana. No recalcula nada
    nuevo sobre producción: `n_publicaciones` es el mismo pares-autor×publicación
    que `02_indicators.py` ya declaró, con el mismo denominador y la misma
    advertencia (63,8 % de cobertura, vocabulario no validado
    institucionalmente). Cambia la FORMA del dato, no el dato.

QUÉ AÑADE, Y CON QUÉ CUIDADO
    Citas totales por unidad, sumadas sobre las mismas parejas autor×publicación
    de `P-07` — por eso hereda su mismo efecto de doble conteo (una publicación
    con autores de dos escuelas suma sus citas en ambas), declarado aquí en vez
    de escondido.

    Deliberadamente NO incluye FWCI ni percentil de citación agregados por
    unidad. `D-18` ya estableció que el FWCI de un autor no es el promedio de
    sus publicaciones — agregarlo por facultad es el mismo error de
    composición. Sumar citas crudas es una operación aditiva; promediar un
    índice normalizado por campo no lo es.

Salida:
    data/processed/hierarchy.json
"""

from __future__ import annotations

import sys
from collections import defaultdict
from statistics import median

import pandas as pd

if sys.platform == "win32":
    # La consola de Windows usa cp1252 por defecto: revienta cualquier print()
    # con caracteres como "→"/"✗"/"⚠". Mismo patrón que src/enrich/orcid_openalex.py.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import common_build as b


def _stats_por_unidad(authorship: pd.DataFrame, citas_por_eid: dict) -> dict[str, dict]:
    """Una fila por par autor×publicación con `unidad_academica` no nula.

    Mismo universo de filas que P-07 (`02_indicators.py`): no se filtra nada
    adicional aquí.
    """
    filas = authorship.dropna(subset=["unidad_academica"])
    por_unidad: dict[str, list] = defaultdict(list)
    for eid, unidad in zip(filas["eid"], filas["unidad_academica"]):
        por_unidad[unidad].append(citas_por_eid.get(eid))

    salida = {}
    for unidad, lista_citas in por_unidad.items():
        con_dato = [c for c in lista_citas if c is not None]
        salida[unidad] = {
            "n_publicaciones": len(lista_citas),
            "citas_totales": int(sum(con_dato)) if con_dato else 0,
            "citas_mediana": round(median(con_dato), 1) if con_dato else None,
            "con_citas": len(con_dato),
        }
    return salida


def _nodo(nombre: str, stats: dict, hijos: list | None = None) -> dict:
    n = {
        "nombre": nombre,
        "n_publicaciones": stats["n_publicaciones"],
        "citas_totales": stats["citas_totales"],
        "citas_mediana": stats["citas_mediana"],
    }
    if hijos is not None:
        n["hijos"] = hijos
    return n


def _sumar(nodos: list[dict]) -> dict:
    return {
        "n_publicaciones": sum(n["n_publicaciones"] for n in nodos),
        "citas_totales": sum(n["citas_totales"] for n in nodos),
        "citas_mediana": None,  # una mediana de medianas no es la mediana del conjunto
    }


def construir(authorship: pd.DataFrame, uni: pd.DataFrame) -> dict:
    citas_por_eid = {eid: b.to_num(c) for eid, c in zip(uni["eid"], uni["citas"])}
    stats = _stats_por_unidad(authorship, citas_por_eid)

    escuelas_por_facultad: dict[str, list[dict]] = defaultdict(list)
    for unidad, s in stats.items():
        facultad = b.facultad_de(unidad)
        # Una unidad SIN entrada en la jerarquía es su propia facultad (mismo
        # criterio que `facultad_de()`): la escuela no se repite como hijo de
        # sí misma en ese caso.
        if facultad == unidad:
            escuelas_por_facultad[facultad]  # asegura la clave, sin hijo propio
        else:
            escuelas_por_facultad[facultad].append(_nodo(unidad, s))

    facultades = []
    for facultad, escuelas in escuelas_por_facultad.items():
        stats_facultad = stats.get(facultad)
        if stats_facultad is None:
            # La facultad no tiene pares propios (todo su volumen viene de
            # escuelas hijas): se suma desde ellas.
            stats_facultad = _sumar(escuelas) if escuelas else \
                {"n_publicaciones": 0, "citas_totales": 0, "citas_mediana": None}
        elif escuelas:
            # La facultad SÍ tiene pares propios (firmas declaradas
            # directamente en la facultad, sin escuela) Y además tiene
            # escuelas hijas: se suman ambos, sin perder ninguno.
            propio = stats_facultad
            agregado = _sumar(escuelas)
            stats_facultad = {
                "n_publicaciones": propio["n_publicaciones"] + agregado["n_publicaciones"],
                "citas_totales": propio["citas_totales"] + agregado["citas_totales"],
                "citas_mediana": propio["citas_mediana"],
            }
        facultades.append(_nodo(facultad, stats_facultad, hijos=escuelas or None))

    facultades.sort(key=lambda n: -n["n_publicaciones"])
    for f in facultades:
        if f.get("hijos"):
            f["hijos"].sort(key=lambda n: -n["n_publicaciones"])

    raiz_stats = _sumar(facultades)
    raiz = _nodo(b.build_meta()["institucion_corta"], raiz_stats, hijos=facultades)

    return {
        "meta": b.build_meta(),
        "metodologia": {
            "n_publicaciones": "Pares autor × publicación, mismo criterio y "
                "cobertura que P-07 (docs/INDICATORS.md). Una publicación con "
                "autores de dos unidades cuenta en ambas.",
            "citas_totales": "Suma de `citas` (Scopus) sobre las mismas parejas "
                "autor × publicación de n_publicaciones — hereda su mismo "
                "efecto de doble conteo entre unidades.",
            "excluido_a_proposito": "FWCI y percentil de citación agregados por "
                "unidad. D-18: el FWCI de un autor no es el promedio de sus "
                "publicaciones; agregarlo por facultad repetiría ese error.",
        },
        "advertencia": b.nota("P-07")["texto"] if b.nota("P-07") else None,
        "procedencia": b.procedencia(
            "P-07",
            # "No determinada" es categoría de primera clase (D-09), se
            # muestra en el árbol, pero no cuenta como cobertura resuelta:
            # mismo criterio que el 63,8 % que docs/AUDIT_REPORT.md declara
            # para P-07 — si no se resta aquí, el sello mentiría "100 %".
            cubiertas=raiz_stats["n_publicaciones"]
                - stats.get("No determinada", {"n_publicaciones": 0})["n_publicaciones"],
            n=len(authorship),
            unidad="pares autor × publicación",
        ),
        "raiz": raiz,
    }


def main() -> None:
    b.banner("BUILD 07 — JERARQUÍA INSTITUCIONAL (TREEMAP)")
    b.require_validation()

    uni = b.load_universe()
    authorship = b.load_authorship()

    arbol = construir(authorship, uni)
    b.write_json(arbol, "hierarchy.json")

    n_facultades = len(arbol["raiz"]["hijos"])
    n_escuelas = sum(len(f.get("hijos") or []) for f in arbol["raiz"]["hijos"])
    print(f"  facultades           : {n_facultades}")
    print(f"  escuelas (hijas)     : {n_escuelas}")
    print(f"  pares autor×pub      : {arbol['raiz']['n_publicaciones']}")
    print(f"  citas totales (raíz) : {arbol['raiz']['citas_totales']}")
    print("\n  OK · data/processed/hierarchy.json")


if __name__ == "__main__":
    main()
