"""Producción autoarchivada en el repositorio institucional, por unidad
declarada, fuera de Scopus (`PD-03`).

QUÉ RESUELVE
    El usuario pidió sumar "todas [las Facultades], usando el repositorio
    institucional" a `produccion-ampliada.html`. La hoja AUTOARCHIVOS de
    `data/raw/Inventario_Repositorio_Autoarchivo.xlsx` —ya en el proyecto,
    entregada por biblioteca (`config/sources.yml` -> `autoarchivo_biblioteca`)—
    es justo eso: 808 obras (artículo de revista, capítulo de libro, libro,
    ponencia — nunca tesis, a diferencia del volcado DSpace) que sus propios
    autores autoarchivaron, con DOI, año, título y la Facultad o Escuela que
    biblioteca les asignó, fila por fila. A diferencia del listado de
    Medicina (`facultad_medicina_publicaciones.py`, una sola Facultad
    declarando su propio sitio), ésta cubre a toda la institución de una vez.

    El volcado DSpace (`dspace_inventario.py`) NO sirve para esto: su
    columna `collection` es un handle opaco de DSpace (`20.500.12254/2311`),
    sin nombre de Facultad/Escuela en ningún lado del export, y
    `dc.uft.carrera` está casi siempre vacía (4 de 3.271 filas). Verificado
    antes de escribir este conector, no asumido.

EL PROBLEMA REAL: LA FACULTAD/ESCUELA VIENE EN BRUTO
    `config/sources.yml` ya lo advertía: el campo "Facultad o Escuela" de
    esta hoja "se declara EN BRUTO («Medicina», «CIDOC», etc.), sin traducir
    a `config/matching_rules.yml`". De los 35 valores distintos que trae,
    la MAYORÍA no tiene una relación escuela-facultad validada
    institucionalmente hoy: `config/matching_rules.yml` -> `jerarquia` sólo
    confirma 5 escuelas, y su `vocabulario` (regla I-07, validado el
    2026-08-26) resuelve unas pocas más directo a nivel de Facultad. Forzar
    el resto a una Facultad adivinada sería inventar una relación
    institucional — exactamente lo que `CLAUDE.md` prohíbe.

    Por eso cada registro trae DOS campos, nunca uno solo:
      - `unidad_declarada`: la cadena tal cual la escribió biblioteca —
        siempre presente, nunca se oculta.
      - `facultad`: el nombre canónico, SÓLO cuando la relación está
        validada (ver `_facultad_validada()` abajo); si no, cadena vacía.
    `mapeo_validado` lo dice explícito, para que el consumidor
    (`09_produccion_declarada.py`) nunca tenga que inferir "validado" de
    "no vacío".

QUÉ CUENTA COMO VALIDADO, Y POR QUÉ (nada de esto es una decisión nueva:
    cada caso ya estaba resuelto en otro archivo de este proyecto)
      1. La cadena, normalizada, YA ES uno de los 8 nombres de Facultad
         conocidos (`config/matching_rules.yml` -> `jerarquia` cubre 5
         escuelas bajo 3 Facultades; hay 8 Facultades nombradas en total).
      2. `common.canonical_academic_unit()` + `common.facultad_de()` —el
         mismo par de funciones que ya usa el indicador `P-07` en
         producción— resuelve la cadena (probada como escuela y como
         facultad) a un nombre de Facultad. Esto reutiliza exactamente la
         lógica ya validada por el responsable del proyecto (T-02,
         2026-08-26), no una copia nueva.
      3. Un puñado de alias explícitos, documentados uno por uno abajo
         (`ALIAS_VALIDADOS`): nombres truncados de una escuela que SÍ está
         en la jerarquía (`Nutrición` -> `Escuela de Nutrición y
         Dietética`, corroborado independientemente por
         `facultad_medicina_publicaciones.py` -> `SECCIONES_POR_ENCABEZADO`,
         que lista "Nutrición y Dietética" como sección propia de Medicina;
         `Familia` -> `Escuela de Ciencias de la Familia`, única escuela de
         "Familia" en toda la jerarquía), y las dos únicas entradas de
         `REFERENCIA_UNIDADES_AUTOARCHIVO`
         (`src/review/build_review.py`) que el usuario confirmó
         DIRECTAMENTE contra finis.cl, no "fuente externa sin verificar":
         `Educación básica` y `Educación parvularia`.

    Todo lo demás —Formación General, CIDOC, CIPEF (centros de
    investigación, no escuelas de docencia, ya documentado en
    `REFERENCIA_UNIDADES_AUTOARCHIVO`), Periodismo, Literatura, Filosofía,
    Publicidad, Ingeniería comercial, Ingeniería civil informática (las
    cuatro últimas marcadas ahí "fuente externa, sin verificar en finis.cl
    directamente"), Diseño, Arte y el resto que ni siquiera aparece en esa
    referencia— se queda en `unidad_declarada`, sin Facultad. `PD-03` NO
    los cuenta en su cifra por Facultad; se publican aparte, como nota de
    transparencia (nunca ocultos, igual que "fuera de ventana" en `PD-01`).

QUÉ NO HACE
    No deduplica (Regla 3 de `docs/METODOLOGIA_FUERA_DE_SCOPUS.md`, D-370):
    eso es trabajo del consumidor, no de la ingesta. No escribe en
    `publications_universe.csv` ni en ningún indicador de citas/FWCI
    (D-206, D-398): "declarado en el repositorio" no es "indexado en
    Scopus". No decide ORCID ni identidad — eso lo sigue haciendo
    `autoarchivo_uft.py`, sin tocarlo.

USO
    python3 src/enrich/autoarchivo_produccion.py           # sin red, todo local
    python3 src/enrich/autoarchivo_produccion.py --test    # valida el mapeo, sin leer el xlsx

Salida:
    data/enriched/autoarchivo_produccion.json   registros estructurados
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audit"))
import common as c  # noqa: E402

ROOT = c.ROOT
RAW_AUTOARCHIVO = c.RAW / "Inventario_Repositorio_Autoarchivo.xlsx"
SALIDA_JSON = ROOT / "data" / "enriched" / "autoarchivo_produccion.json"
UNIVERSO = ROOT / "data" / "interim" / "publications_universe.csv"

FACULTADES_CONOCIDAS = {
    c.normalize_text(f) for f in {
        "Facultad de Medicina y Salud", "Facultad de Ingeniería",
        "Facultad de Educación y Ciencias Sociales", "Facultad de Economía y Negocios",
        "Facultad de Derecho", "Facultad de Artes",
        "Facultad de Arquitectura, Diseño y Estudios Creativos",
        "Facultad de Humanidades y Comunicaciones",
    }
}

# Alias explícitos, validados uno por uno (ver docstring). La clave es la
# cadena EN BRUTO tal como aparece en la hoja AUTOARCHIVOS; el valor es la
# Facultad ya resuelta — nunca una escuela, para no tener que encadenar
# `facultad_de()` de nuevo sobre un alias.
ALIAS_VALIDADOS = {
    # Truncado de "Escuela de Nutrición y Dietética" (jerarquia, confirmada).
    # Corroborado por facultad_medicina_publicaciones.py: "Nutrición y
    # Dietética" es una sección propia de Medicina en el sitio de la Facultad.
    "Nutrición": "Facultad de Medicina y Salud",
    # Única escuela de "Ciencias de la Familia" en toda la jerarquía
    # (config/matching_rules.yml); "Familia" no es ambiguo en este vocabulario.
    "Familia": "Facultad de Educación y Ciencias Sociales",
    # Fila única con el nombre completo de la escuela Y la facultad ya
    # escritos en la misma cadena.
    "Escuela de Nutrición y Dietética, Facultad de Medicina": "Facultad de Medicina y Salud",
    # REFERENCIA_UNIDADES_AUTOARCHIVO (src/review/build_review.py): las
    # ÚNICAS dos entradas ahí confirmadas por el usuario DIRECTAMENTE contra
    # finis.cl, no "fuente externa sin verificar".
    "Educación básica": "Facultad de Educación y Ciencias Sociales",
    "Educación parvularia": "Facultad de Educación y Ciencias Sociales",
}
_ALIAS_NORM = {c.normalize_text(k): v for k, v in ALIAS_VALIDADOS.items()}


def _facultad_validada(unidad_declarada: str) -> str:
    """Facultad canónica si la relación está validada; "" si no.

    Tres vías, en orden — ver docstring del módulo para la evidencia de
    cada una. Nunca adivina: una unidad que no calza en ninguna vía se
    queda sin Facultad, no se le fuerza la más parecida.
    """
    if not unidad_declarada:
        return ""
    norm = c.normalize_text(unidad_declarada)

    if norm in FACULTADES_CONOCIDAS:
        return unidad_declarada

    if norm in _ALIAS_NORM:
        return _ALIAS_NORM[norm]

    # Misma lógica que P-07 en producción: probar la cadena tal cual, y con
    # los dos prefijos que el vocabulario de config/matching_rules.yml usa
    # ("Escuela de…"/"Facultad de…"), contra el vocabulario controlado
    # (regla I-07) y luego la jerarquía escuela->facultad (T-02).
    for candidata in (unidad_declarada, f"Escuela de {unidad_declarada}",
                      f"Facultad de {unidad_declarada}"):
        clave = c.normalize_text(candidata)
        if clave in c._VOCAB_LOOKUP:
            canonical = c._VOCAB_LOOKUP[clave]
            resultado = c.facultad_de(canonical)
            # facultad_de() devuelve la escuela sin cambios si no está en la
            # jerarquía (documentado ahí: "no se infiere a qué facultad
            # pertenece"). Sólo cuenta como validado si de verdad llegó a
            # nivel Facultad.
            if c.normalize_text(resultado) in FACULTADES_CONOCIDAS:
                return resultado
            return ""
    return ""


_RE_DOI = re.compile(r"^10\.\d{4,9}/\S+$")


def normalizar_doi(doi) -> str:
    """Igual que en facultad_medicina_publicaciones.py, pero además exige la
    forma `10.xxxx/algo`: esta fuente trae decenas de valores tipo
    "artículo sin doi"/"libro no tiene doi" en la misma columna DOI (texto
    libre, no un campo estructurado) — sin la validación de forma, esas
    frases se contarían como DOI reales."""
    if doi is None or (isinstance(doi, float) and pd.isna(doi)):
        return ""
    doi = str(doi).strip().lower()
    doi = re.sub(r"^https?://(dx\.|www\.)?doi\.org/", "", doi)
    doi = doi.strip(".")
    return doi if _RE_DOI.match(doi) else ""


def _texto(valor) -> str:
    return "" if valor is None or (isinstance(valor, float) and pd.isna(valor)) else str(valor).strip()


def extraer(df: pd.DataFrame) -> list[dict]:
    registros = []
    for _, row in df.iterrows():
        unidad = unicodedata.normalize("NFC", _texto(row.get("Facultad o Escuela")))
        anio_crudo = row.get("Año de publicación")
        anio = "" if pd.isna(anio_crudo) else str(int(anio_crudo)) if isinstance(anio_crudo, float) else str(anio_crudo).strip()
        facultad = _facultad_validada(unidad)
        registros.append({
            "unidad_declarada": unidad,
            "facultad": facultad,
            "mapeo_validado": bool(facultad),
            "anio": anio,
            "titulo": _texto(row.get("TÍTULO")),
            "tipo": _texto(row.get("Tipo de recurso")),
            "doi": normalizar_doi(row.get("DOI")),
        })
    return registros


def cruzar(registros: list[dict], universo: pd.DataFrame) -> list[dict]:
    doi_universo = set(universo["doi"].dropna().astype(str).str.lower().str.strip())
    for r in registros:
        r["en_universo_scopus"] = bool(r["doi"] and r["doi"] in doi_universo)
        if r["en_universo_scopus"]:
            fila = universo.loc[universo["doi"].astype(str).str.lower() == r["doi"]]
            if not fila.empty:
                r["eid_scopus"] = fila.iloc[0]["eid"]
                r["anio_scopus"] = int(fila.iloc[0]["anio"]) if pd.notna(fila.iloc[0]["anio"]) else None
    return registros


def run() -> list[dict]:
    df = pd.read_excel(RAW_AUTOARCHIVO, sheet_name="AUTOARCHIVOS")
    registros = extraer(df)
    universo = pd.read_csv(UNIVERSO)
    return cruzar(registros, universo)


def _guardar(registros: list[dict]) -> None:
    SALIDA_JSON.parent.mkdir(parents=True, exist_ok=True)
    import json
    SALIDA_JSON.write_text(
        json.dumps(registros, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    con_facultad = sum(1 for r in registros if r["facultad"])
    print(f"registros          : {len(registros)}")
    print(f"con Facultad validada: {con_facultad} ({len(registros) - con_facultad} sin mapeo)")
    print(f"con DOI            : {sum(1 for r in registros if r['doi'])}")
    print(f"en universo Scopus : {sum(1 for r in registros if r['en_universo_scopus'])}")


def test() -> int:
    fallos = []

    def caso(n, ok, obs=None):
        if not ok:
            fallos.append(f"{n}" + (f" ({obs})" if obs is not None else ""))

    caso("Facultad ya canónica se conserva",
         _facultad_validada("Facultad de Medicina y Salud") == "Facultad de Medicina y Salud")
    caso("escuela con jerarquía confirmada resuelve a su Facultad",
         _facultad_validada("Kinesiología") == "Facultad de Medicina y Salud")
    caso("vocabulario resuelve directo a Facultad (Psicología)",
         _facultad_validada("Psicología") == "Facultad de Educación y Ciencias Sociales")
    caso("alias truncado validado (Nutrición)",
         _facultad_validada("Nutrición") == "Facultad de Medicina y Salud")
    caso("alias de finis.cl (Educación básica)",
         _facultad_validada("Educación básica") == "Facultad de Educación y Ciencias Sociales")
    caso("centro de investigación NO se mapea (CIDOC)",
         _facultad_validada("CIDOC") == "")
    caso("unidad sin ninguna evidencia NO se mapea (Diseño)",
         _facultad_validada("Diseño") == "")
    caso("cadena vacía NO se mapea", _facultad_validada("") == "")

    caso("DOI válido pasa", normalizar_doi("https://doi.org/10.1016/j.aaa.2024.100136") == "10.1016/j.aaa.2024.100136")
    caso("sentinela de 'sin DOI' se descarta", normalizar_doi("artículo sin doi") == "")
    caso("DOI malformado se descarta", normalizar_doi("10.22352%20saustral20253117") == "")
    caso("DOI ausente (NaN) se descarta", normalizar_doi(float("nan")) == "")

    df = pd.DataFrame([
        {"Facultad o Escuela": "Medicina", "Año de publicación": 2024.0,
         "TÍTULO": "Obra A", "Tipo de recurso": "Artículo de revista",
         "DOI": "https://doi.org/10.1016/aaa"},
        {"Facultad o Escuela": "CIDOC", "Año de publicación": 2023.0,
         "TÍTULO": "Obra B", "Tipo de recurso": "Capítulo de libro",
         "DOI": "libro sin doi"},
    ])
    registros = extraer(df)
    caso("extraer() produce 2 registros", len(registros) == 2)
    caso("primer registro trae Facultad", registros[0]["facultad"] == "Facultad de Medicina y Salud"
         and registros[0]["mapeo_validado"] is True)
    caso("segundo registro NO trae Facultad, sí unidad_declarada",
         registros[1]["facultad"] == "" and registros[1]["unidad_declarada"] == "CIDOC"
         and registros[1]["mapeo_validado"] is False)

    universo = pd.DataFrame([{"doi": "10.1016/aaa", "eid": "e1", "anio": 2024}])
    cruzados = cruzar(registros, universo)
    caso("cruce por DOI marca en_universo_scopus", cruzados[0]["en_universo_scopus"] is True
         and cruzados[1]["en_universo_scopus"] is False)

    for f in fallos:
        print("FALLA:", f)
    print(f"\n{'TEST OK' if not fallos else 'TEST FALLÓ'} · {len(fallos)} falla(s)")
    return 1 if fallos else 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true", help="valida el mapeo, sin leer el xlsx")
    args = ap.parse_args()

    if args.test:
        sys.exit(test())

    registros = run()
    _guardar(registros)
    print("OK ·", SALIDA_JSON)


if __name__ == "__main__":
    main()
