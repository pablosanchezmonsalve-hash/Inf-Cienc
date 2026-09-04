"""Consolida publicaciones de fuentes no-Scopus/SciVal en data/interim/.

Lee las tres fuentes institucionales (Facultad de Medicina, DSpace,
Autoarchivo), cruza contra el universo Scopus para retener sólo las obras
fuera de él, y escribe un JSON unificado en data/interim/ que el build
consume sin tocar data/raw/.

Este script vive en src/enrich/ (puede leer data/raw/) y no en src/build/
(D-22: el build no lee data/raw/).

Salidas:
  data/interim/fuentes_externas.json
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import pandas as pd

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
UNIVERSO = ROOT / "data" / "interim" / "publications_universe.csv"
FACMED_JSON = ROOT / "data" / "enriched" / "facultad_medicina_publicaciones.json"
DSPACE_RAW = ROOT / "data" / "raw" / "Inventario_Repositorio_Institucional_UFT.csv"
AUTOARCHIVO_XLSX = ROOT / "data" / "raw" / "Inventario_Repositorio_Autoarchivo.xlsx"
OUT = ROOT / "data" / "interim" / "fuentes_externas.json"

TIPOS_DSPACE_MANTENER = {
    "Article", "Artículo", "Artículo de revista",
    "Book", "Libro", "Book chapter", "Capítulo de libro",
    "book-chapter", "Book Chapter",
}

FUENTE_FACMED = "Facultad de Medicina y Salud"
FUENTE_DSPACE = "Repositorio institucional DSpace"
FUENTE_AUTOARCHIVO = "Autoarchivo de biblioteca"


def normalizar_doi(doi) -> str:
    if doi is None:
        return ""
    try:
        if pd.isna(doi):
            return ""
    except (TypeError, ValueError):
        pass
    doi = str(doi).strip().lower()
    if doi in ("", "nan", "none"):
        return ""
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    doi = re.sub(r"^doi:\s*", "", doi)
    return doi.strip(".").strip()


def _txt(v) -> str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except (TypeError, ValueError):
        pass
    return str(v).strip()


def cargar_universo() -> set[str]:
    u = pd.read_csv(UNIVERSO, dtype=str)
    return {normalizar_doi(x) for x in u["doi"].dropna() if normalizar_doi(x)}


def articulos_facmed(univ: set[str]) -> list[dict]:
    if not FACMED_JSON.exists():
        return []
    d = json.loads(FACMED_JSON.read_text(encoding="utf-8"))
    filas = []
    for r in d:
        if r["en_universo_scopus"]:
            continue
        autor = (r.get("autor_uft") or "").strip()
        if not autor:
            continue
        filas.append({
            "titulo": (r.get("titulo") or "").strip(),
            "autor_uft": autor,
            "doi": normalizar_doi(r.get("doi")),
            "anio": (r.get("anio") or "").strip(),
            "escuela": (r.get("seccion") or "").strip(),
            "tipo": "Artículo",
            "fuente": FUENTE_FACMED,
            "fuente_id": "facmed",
        })
    return filas


def _tipo_dspace(dc, es) -> str:
    for x in (dc, es):
        if isinstance(x, str) and x in TIPOS_DSPACE_MANTENER:
            return x
    return ""


def articulos_dspace(univ: set[str]) -> list[dict]:
    if not DSPACE_RAW.exists():
        return []
    d = pd.read_csv(DSPACE_RAW, sep=";", dtype=str, encoding="utf-8")
    filas = []
    for _, r in d.iterrows():
        tipo = _tipo_dspace(r.get("dc.type"), r.get("dc.type[es]"))
        if not tipo:
            continue
        doi = normalizar_doi(r.get("dc.identifier.doi"))
        if not doi or doi in univ:
            continue
        titulo = _txt(r.get("dc.title"))
        autores = _txt(r.get("dc.contributor.author"))
        for a in [x.strip() for x in autores.split(";") if x.strip()]:
            filas.append({
                "titulo": titulo,
                "autor_uft": a,
                "doi": doi,
                "anio": "",
                "escuela": "",
                "tipo": tipo,
                "fuente": FUENTE_DSPACE,
                "fuente_id": "dspace",
            })
    return filas


def articulos_autoarchivo(univ: set[str]) -> list[dict]:
    if not AUTOARCHIVO_XLSX.exists():
        return []
    xl = pd.ExcelFile(AUTOARCHIVO_XLSX)
    df = xl.parse("AUTOARCHIVOS", dtype=str)
    filas = []
    for _, r in df.iterrows():
        titulo = _txt(r.get("TÍTULO"))
        if not titulo:
            continue
        doi = normalizar_doi(r.get("DOI"))
        if not doi or doi in univ:
            continue
        for a in [x.strip() for x in _txt(r.get("Autor")).split(";") if x.strip()]:
            filas.append({
                "titulo": titulo,
                "autor_uft": a,
                "doi": doi,
                "anio": _txt(r.get("Año de publicación")),
                "escuela": _txt(r.get("Facultad o Escuela")),
                "tipo": _txt(r.get("Tipo de recurso")),
                "fuente": FUENTE_AUTOARCHIVO,
                "fuente_id": "autoarchivo",
            })
    return filas


def main() -> int:
    univ = cargar_universo()

    articulos = []
    articulos += articulos_facmed(univ)
    articulos += articulos_dspace(univ)
    articulos += articulos_autoarchivo(univ)

    vistos = set()
    unicos = []
    for a in articulos:
        k = (a["autor_uft"], (a["doi"] or a["titulo"] or "").upper())
        if k in vistos:
            continue
        vistos.add(k)
        unicos.append(a)

    autores_map = defaultdict(lambda: {"facultad_medicina": 0, "dspace": 0, "autoarchivo": 0})
    for a in unicos:
        src = a["fuente_id"]
        if src == "facmed":
            autores_map[a["autor_uft"]]["facultad_medicina"] += 1
        elif src == "dspace":
            autores_map[a["autor_uft"]]["dspace"] += 1
        elif src == "autoarchivo":
            autores_map[a["autor_uft"]]["autoarchivo"] += 1

    autores = []
    for nombre, conteo in sorted(autores_map.items()):
        total = sum(conteo.values())
        autores.append({
            "nombre": nombre,
            "obras_facultad_medicina": conteo["facultad_medicina"],
            "obras_dspace": conteo["dspace"],
            "obras_autoarchivo": conteo["autoarchivo"],
            "total": total,
        })

    por_fuente = defaultdict(int)
    for a in unicos:
        por_fuente[a["fuente_id"]] += 1

    salida = {
        "meta": {
            "titulo": "Producción fuera del corpus Scopus",
            "descripcion": (
                "Publicaciones con autores afiliados a la UFT recuperadas de "
                "fuentes institucionales no indexadas en Scopus/SciVal."
            ),
            "fuentes": [FUENTE_FACMED, FUENTE_DSPACE, FUENTE_AUTOARCHIVO],
            "universo_scopus_dois": len(univ),
            "fecha_generacion": date.today().isoformat(),
            "advertencia": (
                "Este listado es un inventario declarado. Los autores no estan "
                "verificados individualmente (D-08 impide fusion automatica). "
                "La afiliacion a la UFT se asume por la fuente institucional, "
                "no por verificacion humana."
            ),
        },
        "publicaciones": unicos,
        "autores": autores,
        "resumen": {
            "total_publicaciones": len(unicos),
            "total_autores": len(autores),
            "por_fuente": dict(por_fuente),
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"fuentes_externas: {len(unicos)} publicaciones, {len(autores)} autores → {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
