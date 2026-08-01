"""Utilidades compartidas por el build de artefactos publicables.

BARRERA DE CAPAS (decisión D-22): este módulo lee de `data/interim/` y
`config/`. Nunca de `data/raw/` ni de `internal/`. La única excepción es
`internal/matching_log.csv`, del que se extraen exclusivamente los campos
publicables (autor, eid, año, unidad) — nunca la cadena de afiliación cruda ni
el método de detección. Ver `docs/LAYERS.md`.
"""

from __future__ import annotations

import json
import math
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config"
INTERIM = ROOT / "data" / "interim"
INTERNAL = ROOT / "internal"
PROCESSED = ROOT / "data" / "processed"
DOCS = ROOT / "docs"

# Campos de la capa interna que jamás pueden aparecer en un artefacto público.
# La verificación automática (05_verify_public_layer.py) falla si los encuentra.
CAMPOS_PROHIBIDOS = (
    "afiliacion_declarada_raw",
    "metodo_blando",
    "metodo_duro_publicacion",
    "confianza",
    "resolucion",
    "clave_normalizada",
    "clave_apellido",
    "cadena_afiliacion",
)


def load_config(name: str) -> dict:
    with open(CONFIG / name, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


INSTITUTION = load_config("institution.yml")
SOURCES = load_config("sources.yml")["fuentes"]
INDICATORS = load_config("indicators.yml")


def slugify(text: str) -> str:
    """Identificador seguro para nombres de archivo y URLs.

    NO es único por sí solo: la normalización quita acentos y guiones, de modo
    que 'Orellana-Donoso M.' y 'Orellana Donoso M.' colapsan al mismo valor.
    Use `unique_slugs()` para asignar identificadores a un conjunto de firmas.
    """
    base = unicodedata.normalize("NFD", str(text))
    base = "".join(ch for ch in base if unicodedata.category(ch) != "Mn")
    base = re.sub(r"[^a-zA-Z0-9]+", "-", base).strip("-").lower()
    return base or "sin-nombre"


def unique_slugs(names) -> dict[str, str]:
    """Asigna un identificador único a cada firma, sin fusionar variantes.

    Dos formas de firma distintas ('Díaz F.' y 'Diaz F.') producen el mismo
    slug base. Colapsarlas en un solo archivo sería exactamente el colapso
    automático de variantes que prohíbe la decisión D-08: una ficha
    sobrescribiría a la otra y el ranking mostraría menos personas de las
    detectadas.

    Cuando un slug base es reclamado por más de una firma, TODAS las firmas en
    conflicto reciben un sufijo derivado del nombre exacto. El sufijo depende
    sólo del nombre, no del orden de iteración, por lo que el identificador es
    estable entre builds y entre cargas de datos distintas.
    """
    import hashlib
    from collections import Counter

    names = list(names)
    bases = {n: slugify(n) for n in names}
    colisionados = {b for b, c in Counter(bases.values()).items() if c > 1}

    out: dict[str, str] = {}
    for n in names:
        base = bases[n]
        if base in colisionados:
            h = hashlib.sha1(n.encode("utf-8")).hexdigest()[:4]
            out[n] = f"{base}-{h}"
        else:
            out[n] = base
    return out


def clean(value):
    """Convierte NaN/NaT a None para que el JSON no lleve 'NaN' inválido."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if pd.isna(value):
        return None
    return value


def to_num(value):
    v = clean(value)
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if math.isnan(f):
        return None
    return int(f) if f.is_integer() else round(f, 4)


def split_multi(value) -> list[str]:
    """Separa un campo multivaluado de SciVal ('|') conservando el orden."""
    v = clean(value)
    if v is None:
        return []
    return [p.strip() for p in str(v).split("|") if p.strip() and p.strip() != "-"]


def load_universe() -> pd.DataFrame:
    return pd.read_csv(INTERIM / "publications_universe.csv", dtype=str)


def load_authors() -> pd.DataFrame:
    return pd.read_csv(INTERIM / "authors_master_draft.csv", dtype=str)


_JERARQUIA = load_config("matching_rules.yml")["unidad_academica"].get("jerarquia", {})


def facultad_de(unidad: str) -> str:
    """Facultad a la que pertenece una unidad académica.

    Una escuela sin entrada en la jerarquía se devuelve tal cual: no se infiere
    a qué facultad pertenece.
    """
    entrada = _JERARQUIA.get(unidad)
    return entrada["facultad"] if entrada else unidad


def load_authorship() -> pd.DataFrame:
    """Pares autor x publicación, restringidos a las columnas publicables.

    El archivo de origen es capa interna; aquí se proyecta sólo lo que puede
    publicarse. Los campos de trazabilidad del matching se descartan en la
    lectura, no más adelante: así no pueden filtrarse por descuido.
    """
    df = pd.read_csv(INTERNAL / "matching_log.csv", dtype=str)
    return df[["eid", "anio", "nombre_en_fuente", "unidad_academica",
               "posicion_autor", "n_autores_total"]].copy()


def denominadores() -> dict:
    return INDICATORS["denominadores"]


def indicador(code: str) -> dict:
    return INDICATORS["indicadores"][code]


def nota(code: str) -> dict | None:
    """Nota metodológica y advertencia destacada de un indicador, si tiene."""
    spec = INDICATORS["indicadores"].get(code, {})
    texto = spec.get("advertencia")
    if not texto:
        return None
    return {"texto": texto, "destacada": bool(spec.get("advertencia_destacada"))}


def build_meta() -> dict:
    """Procedencia del build. Se incrusta en todos los artefactos."""
    scival = SOURCES["scival_export"]
    return {
        "institucion": INSTITUTION["institucion"]["nombre_canonico"],
        "institucion_corta": INSTITUTION["institucion"]["nombre_corto"],
        "titulo_plataforma": INSTITUTION["presentacion"]["titulo_plataforma"],
        "ventana": {
            "inicio": INSTITUTION["ventana_temporal"]["anio_inicio"],
            "fin": INSTITUTION["ventana_temporal"]["anio_fin"],
        },
        "fuentes": ["Scopus", "SciVal"],
        "fecha_corte_citas": scival["fecha_corte"],
        "fecha_export": scival["fecha_export"],
        "fecha_build": date.today().isoformat(),
        "denominadores": denominadores(),
        "advertencia_global": (
            "Los indicadores describen la producción indexada en Scopus. "
            "La cobertura de la base no es uniforme entre disciplinas."
        ),
    }


def write_json(payload, name: str, subdir: str | None = None) -> Path:
    target = PROCESSED / subdir if subdir else PROCESSED
    target.mkdir(parents=True, exist_ok=True)
    path = target / name
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))
    return path


def banner(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def require_validation() -> None:
    """Regla de barrera: sin auditoría válida no hay build (decisión D-22)."""
    report = INTERIM / "validation_report.csv"
    if not report.exists():
        sys.exit("BUILD ABORTADO: falta data/interim/validation_report.csv. "
                 "Ejecute antes `python3 src/audit/run_all.py`.")
    df = pd.read_csv(report)
    bloqueantes = df[(df["resultado"] == "FALLA") & (df["severidad"] == "bloqueante")]
    if len(bloqueantes):
        print(bloqueantes.to_string(index=False))
        sys.exit(f"BUILD ABORTADO: {len(bloqueantes)} regla(s) bloqueante(s) fallando.")
