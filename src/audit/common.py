"""Utilidades compartidas por los scripts de auditoría.

Concentra: rutas, carga de configuración, lectores de cada fuente y helpers de
normalización. Ningún patrón institucional se escribe aquí: todo se lee desde
config/.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config"
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
INTERNAL = ROOT / "internal"
DOCS = ROOT / "docs"

for _d in (INTERIM, INTERNAL):
    _d.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- #
# Configuración
# --------------------------------------------------------------------------- #

def load_config(name: str) -> dict:
    with open(CONFIG / name, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


INSTITUTION = load_config("institution.yml")
SOURCES = load_config("sources.yml")["fuentes"]
MATCHING = load_config("matching_rules.yml")


def source_path(key: str) -> Path:
    return ROOT / SOURCES[key]["archivo"]


# --------------------------------------------------------------------------- #
# Lectores de fuentes
# --------------------------------------------------------------------------- #

def read_scopus() -> pd.DataFrame:
    """Export nativo de Scopus. Fuente primaria de autoría y afiliación."""
    spec = SOURCES["scopus_export"]
    return pd.read_csv(
        source_path("scopus_export"),
        dtype=str,
        encoding=spec["encoding"],
        low_memory=False,
    )


def read_scival() -> pd.DataFrame:
    """Export nativo de SciVal. Fuente primaria de métricas y áreas temáticas.

    La cabecera real está en la fila 20 del archivo (índice 19); las anteriores
    son metadatos del export. Se asevera para que un cambio de formato falle
    ruidosamente en vez de producir una tabla silenciosamente corrida
    (regla E-03).
    """
    spec = SOURCES["scival_export"]
    df = pd.read_excel(
        source_path("scival_export"),
        sheet_name=spec["hoja"],
        skiprows=spec["header_row"],
        dtype=str,
    )
    assert df.columns[0] == "Title", (
        f"E-03: cabecera inesperada en SciVal ({df.columns[0]!r}). "
        "Revisar header_row en config/sources.yml."
    )
    return df[df["EID"].notna()].reset_index(drop=True)


def read_scival_export_metadata() -> dict:
    """Las 19 filas de metadatos que preceden a la cabecera del export SciVal."""
    raw = pd.read_excel(
        source_path("scival_export"), sheet_name="Sheet0", header=None,
        nrows=SOURCES["scival_export"]["header_row"], dtype=str,
    )
    meta = {}
    for _, row in raw.iterrows():
        k = str(row[0]).strip() if pd.notna(row[0]) else ""
        v = str(row[1]).strip() if len(row) > 1 and pd.notna(row[1]) else ""
        if k and k != "nan":
            meta[k.lstrip("﻿")] = v
    return meta


def read_rdata(key: str) -> pd.DataFrame | None:
    """Objeto bibliometrixDB. Sólo referencia comparativa (decisión D-05).

    Devuelve None si el paquete `rdata` no está disponible. Estos archivos son
    fuentes de REFERENCIA, no de indicadores publicables: hacer que toda la
    auditoría dependa de poder leerlos convertiría una comparación opcional en
    un requisito de instalación. El paquete no tiene ruedas precompiladas para
    todas las versiones de Python, y la plataforma debe poder construirse sin él.
    """
    try:
        import rdata as _rdata
    except ImportError:
        return None

    obj = SOURCES[key]["objeto"]
    parsed = _rdata.read_rda(str(source_path(key)))
    return parsed[obj].reset_index(drop=True)


def read_report_sheet(sheet: str) -> pd.DataFrame:
    """Hoja del reporte manual previo. Set de validación (decisión D-15)."""
    hojas = SOURCES["reporte_excel_2026"]["hojas_utiles"]
    key = {
        "Investigadores": "investigadores",
        "Publicaciones_UFT_detalle": "publicaciones_uft_detalle",
        "Publicaciones unificadas": "publicaciones_unificadas",
    }[sheet]
    return pd.read_excel(
        source_path("reporte_excel_2026"),
        sheet_name=sheet,
        skiprows=hojas[key]["header_row"],
        dtype=str,
    )


# --------------------------------------------------------------------------- #
# Normalización
# --------------------------------------------------------------------------- #

def strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", str(text))
        if unicodedata.category(c) != "Mn"
    )


def normalize_text(text: str) -> str:
    """Minúsculas sin acentos. Para comparación, nunca para display."""
    return strip_accents(str(text)).lower().strip()


def normalize_title(title: str) -> str:
    """Título reducido a alfanuméricos. Detección de duplicados probables."""
    return re.sub(r"[^a-z0-9]", "", normalize_text(title))


def normalize_author_key(name: str) -> str:
    """Clave de agrupación de variantes de nombre (regla P-03).

    Sirve para DETECTAR posibles duplicados, nunca para fusionarlos: el colapso
    automático está deshabilitado por configuración.
    """
    cfg = MATCHING["identidad_autor"]["normalizacion_nombre"]
    out = str(name)
    if cfg.get("quitar_acentos", True):
        out = strip_accents(out)
    if cfg.get("minusculas", True):
        out = out.lower()
    if cfg.get("quitar_guiones", True):
        out = out.replace("-", " ")
    if cfg.get("quitar_puntuacion", True):
        out = re.sub(r"[^\w\s]", "", out)
    return re.sub(r"\s+", " ", out).strip()


def surname_key(name: str) -> str:
    """Apellido base normalizado, sin iniciales. Agrupa 'Yanine F.'/'Yanine F.F.'."""
    tokens = normalize_author_key(name).split()
    parts = [t for t in tokens if len(t) > 1]
    return "".join(parts[:2]) if parts else ""


# --------------------------------------------------------------------------- #
# Detección institucional
# --------------------------------------------------------------------------- #

_SOFT_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in MATCHING["deteccion_institucional"]["metodo_blando"]["patrones"]
]


def matches_institution_soft(text: str) -> bool:
    """Método blando (regla I-03) sobre una cadena de afiliación.

    Aplica los patrones de config/matching_rules.yml sobre el texto sin acentos.
    Los patrones llevan límite de palabra: la regla I-05 prohíbe el matching por
    subcadena suelta, que produce falsos positivos verificados con
    'Ministerio', 'Medizinische' y 'Ministery'.
    """
    if not isinstance(text, str):
        return False
    haystack = strip_accents(text)
    return any(p.search(haystack) for p in _SOFT_PATTERNS)


def matches_institution_hard(affiliation_ids: str) -> bool:
    """Método duro (regla I-02): Scopus Affiliation ID de la institución foco."""
    if not isinstance(affiliation_ids, str):
        return False
    target = str(INSTITUTION["institucion"]["scopus_affiliation_id"])
    return target in [x.strip() for x in affiliation_ids.split("|")]


def split_author_blocks(authors_with_affiliations: str) -> list[str]:
    """Divide 'Authors with affiliations' en un bloque por autor.

    El separador entre autores es '; '. Dentro de cada bloque, la coma separa
    nombre y afiliaciones, pero también aparece dentro de las afiliaciones: por
    eso sólo se toma el primer segmento como nombre. En 8/818 publicaciones el
    número de bloques no coincide con el de autores declarados; esa desalineación
    se registra como ambigüedad, no se corrige por heurística.
    """
    if not isinstance(authors_with_affiliations, str):
        return []
    return [b for b in authors_with_affiliations.split("; ") if b.strip()]


def author_name_from_block(block: str) -> str:
    return block.split(",")[0].strip()


def _clean_unit(unit: str) -> str:
    """Quita restos de la cadena institucional pegados a la unidad."""
    out = unit.strip()
    for suffix in MATCHING["unidad_academica"].get("sufijos_a_limpiar", []):
        out = re.sub(rf"\s*{re.escape(suffix)}\s*$", "", out, flags=re.IGNORECASE)
    return re.sub(r"[\s.,;-]+$", "", out).strip()


def extract_academic_unit(affiliation_chunk: str) -> str | None:
    """Regla I-06: unidad académica por patrón. Devuelve None si no se detecta.

    La búsqueda se restringe al texto que precede a la mención de la institución
    foco y se detiene ante cualquier marcador de otra institución. Sin esa
    restricción, un autor con doble afiliación recibe la facultad de la otra
    universidad: verificado en Fase 1, donde 'Faculty of Medicine and Nursing'
    (Universidad del País Vasco) se atribuía a 30 pares autor x publicación UFT.

    Nunca imputa: la ausencia se resuelve aguas arriba con la etiqueta
    configurada 'No determinada' (decisión D-09).
    """
    cfg = MATCHING["unidad_academica"]
    if not cfg.get("activo", True) or not isinstance(affiliation_chunk, str):
        return None

    text = affiliation_chunk
    if cfg.get("restringir_a_ventana_institucional", True):
        hit = None
        haystack = strip_accents(affiliation_chunk)
        for pattern in _SOFT_PATTERNS:
            hit = pattern.search(haystack)
            if hit:
                break
        if hit is None:
            return None
        # Se recorre hacia atrás desde la institución: la unidad correcta es la
        # más cercana, y cualquier marcador de otra institución corta la ventana.
        markers = cfg.get("marcadores_otra_institucion", [])
        designators = {
            normalize_text(d) for d in cfg.get("designadores_institucionales", [])
        }
        tokens = [t.strip() for t in affiliation_chunk[:hit.start()].split(",")]
        # Se descarta el designador colgante de la propia institución foco.
        while tokens and normalize_text(tokens[-1]).rstrip(".") in {
            d.rstrip(".") for d in designators
        }:
            tokens.pop()
        window = []
        for token in reversed(tokens):
            if any(m.lower() in token.lower() for m in markers):
                break
            window.append(token)
        candidates = window
    else:
        candidates = [t.strip() for t in text.split(",")]

    for token in candidates:
        for pattern in cfg["patrones_extraccion"]:
            m = re.search(pattern, token)
            if m:
                cleaned = _clean_unit(m.group(1))
                return cleaned or None
    return None


_VOCAB_LOOKUP = {
    normalize_text(variant): canonical
    for canonical, variants in MATCHING["unidad_academica"]["vocabulario"].items()
    for variant in variants
}


_JERARQUIA = MATCHING["unidad_academica"].get("jerarquia", {})


def facultad_de(unidad: str) -> str:
    """Facultad a la que pertenece una unidad, según config/matching_rules.yml.

    Una escuela sin entrada en la jerarquía se devuelve tal cual: no se infiere
    a qué facultad pertenece. La etiqueta de sin dato se preserva.
    """
    entrada = _JERARQUIA.get(unidad)
    return entrada["facultad"] if entrada else unidad


def canonical_academic_unit(raw_unit: str | None) -> str:
    """Mapea una variante al vocabulario controlado (regla I-07).

    El vocabulario está marcado como inferido y no validado institucionalmente.
    Las variantes fuera de él se conservan tal cual, no se fuerzan a una
    categoría existente.
    """
    if not raw_unit:
        return MATCHING["unidad_academica"]["etiqueta_sin_dato"]
    return _VOCAB_LOOKUP.get(normalize_text(raw_unit), raw_unit)


# --------------------------------------------------------------------------- #
# Salidas
# --------------------------------------------------------------------------- #

def write_interim(df: pd.DataFrame, name: str) -> Path:
    path = INTERIM / name
    df.to_csv(path, index=False, encoding="utf-8")
    return path


def write_internal(df: pd.DataFrame, name: str) -> Path:
    """Capa interna. No se publica por defecto (CLAUDE.md, <data_governance>)."""
    path = INTERNAL / name
    df.to_csv(path, index=False, encoding="utf-8")
    return path


def banner(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)
