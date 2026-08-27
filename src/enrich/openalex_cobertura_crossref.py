"""Evidencia de Crossref para la revisión de cobertura OpenAlex (V2-26 bis).

QUÉ RESUELVE
    `internal/openalex_cobertura.csv` deja 414 obras que OpenAlex atribuye a
    la UFT y el universo no tiene. Decidir cada caso (D-206, D-316) exige leer
    evidencia — hoy sólo hay lo que OpenAlex mismo declara: su propia
    desambiguación de institución y de tipo documental. Es una sola fuente
    opinando sobre sí misma.

    Este script consulta Crossref por el DOI de cada caso y trae, para el
    autor que OpenAlex marcó como UFT, la afiliación que la propia
    publicación declaró en su momento —dato primario, no una segunda
    desambiguación— más el tipo documental que Crossref registra. Dos
    lecturas independientes en vez de una sola dan más para decidir en el
    mismo clic, sin decidir por nadie.

QUÉ NO HACE
    No decide nada (D-08). No toca `internal/openalex_cobertura.csv` ni su
    columna `resolucion`. No afirma que un autor SEA el de la UFT: empareja
    por apellido contra los autores que Crossref lista y muestra lo que
    encuentra, con su propio nivel de certeza (a veces varios autores
    comparten apellido, a veces ninguno coincide). Sigue siendo lectura para
    una persona, no un veredicto.

USO
    python3 src/enrich/openalex_cobertura_crossref.py            # consulta Crossref
    python3 src/enrich/openalex_cobertura_crossref.py --test     # verifica la lógica sin red
    python3 src/enrich/openalex_cobertura_crossref.py --limit 20 # prueba con pocos casos

Salida:
    internal/openalex_cobertura_crossref.csv   evidencia por caso (capa interna)
    data/cache/crossref/*.json                 respuestas cacheadas (compartido con V2-01)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

if sys.platform == "win32":
    # La consola de Windows usa cp1252 por defecto: revienta cualquier print()
    # con caracteres como "→"/"✗"/"⚠". Mismo patrón que src/enrich/orcid_openalex.py.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audit"))
import common as c  # noqa: E402

CACHE = c.ROOT / "data" / "cache" / "crossref"
FUENTE = c.ROOT / "internal" / "openalex_cobertura.csv"
CFG = c.MATCHING["enriquecimiento_externo"]["orcid"]
API = "https://api.crossref.org/works/"


# --------------------------------------------------------------------------- #
# Normalización y emparejamiento por apellido
# --------------------------------------------------------------------------- #

def _norm(text: str) -> str:
    base = unicodedata.normalize("NFD", str(text or ""))
    base = "".join(ch for ch in base if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z\s-]", " ", base.lower()).strip()


def apellido_candidato(nombre_openalex: str) -> str:
    """OpenAlex entrega 'Nombre [Segundo] Apellido': se toma el último token
    como apellido probable. Impreciso con apellidos compuestos separados por
    espacio (no por guion) — por eso el resultado se marca como candidato, no
    como identidad confirmada."""
    tokens = _norm(nombre_openalex).split()
    return tokens[-1] if tokens else ""


def autores_uft_candidatos(campo_autor_uft: str) -> list[str]:
    """`autor_uft` puede traer varias personas separadas por '; '."""
    return [a.strip() for a in str(campo_autor_uft or "").split(";") if a.strip()]


def emparejar_autor(autor_uft: str, autores_crossref: list[dict]) -> dict:
    """Busca, entre los autores que Crossref lista, a quien comparte apellido
    con el nombre que OpenAlex declaró como de la UFT.

    Devuelve certeza='sin_match' (nadie comparte apellido), 'ambiguo' (más de
    uno) o 'unico' (exactamente uno) — nunca elige entre varios candidatos.
    """
    apellido = apellido_candidato(autor_uft)
    if not apellido:
        return {"certeza": "sin_match", "afiliaciones": [], "nombre_crossref": ""}

    candidatos = []
    for a in autores_crossref:
        fam = _norm(a.get("family", ""))
        if not fam:
            continue
        if apellido in fam.split("-") or apellido == fam or fam in apellido:
            candidatos.append(a)

    if not candidatos:
        return {"certeza": "sin_match", "afiliaciones": [], "nombre_crossref": ""}

    afiliaciones = []
    nombres = []
    for a in candidatos:
        nombres.append(f"{a.get('given', '')} {a.get('family', '')}".strip())
        for af in a.get("affiliation", []) or []:
            nombre_af = af.get("name")
            if nombre_af:
                afiliaciones.append(nombre_af)

    return {
        "certeza": "unico" if len(candidatos) == 1 else "ambiguo",
        "afiliaciones": afiliaciones,
        "nombre_crossref": " | ".join(nombres),
    }


# --------------------------------------------------------------------------- #
# Consulta a Crossref (mismo patrón de caché que orcid_crossref.py)
# --------------------------------------------------------------------------- #

def _cache_path(doi: str) -> Path:
    return CACHE / (re.sub(r"[^a-zA-Z0-9]+", "_", doi)[:120] + ".json")


def consultar(doi: str, mailto: str, pausa: float = 0.12) -> dict | None:
    path = _cache_path(doi)
    if path.exists():
        with open(path, encoding="utf-8") as fh:
            return json.load(fh).get("message")

    url = API + urllib.parse.quote(doi, safe="")
    req = urllib.request.Request(url, headers={
        "User-Agent": f"InformeCienciometrico/1.0 (mailto:{mailto})",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"message": None}), encoding="utf-8")
            return None
        raise
    finally:
        time.sleep(pausa)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data.get("message")


def evidencia_de_caso(row: dict, msg: dict | None) -> dict:
    """Una fila de evidencia por caso de `openalex_cobertura.csv`."""
    base = {"openalex_id": row["openalex_id"], "doi": row.get("doi") or ""}
    if msg is None:
        return {**base, "crossref_encontrado": False, "crossref_tipo": "",
                "crossref_anio": "", "crossref_certeza_autor": "sin_registro",
                "crossref_autor": "", "crossref_afiliacion": ""}

    tipo = msg.get("type", "")
    fecha = (msg.get("published-print") or msg.get("published-online")
             or msg.get("created") or {}).get("date-parts", [[None]])[0][0]

    resultados = [emparejar_autor(a, msg.get("author", []) or [])
                  for a in autores_uft_candidatos(row.get("autor_uft"))]
    if not resultados:
        resultados = [{"certeza": "sin_match", "afiliaciones": [], "nombre_crossref": ""}]

    # Si hay varias personas candidatas en la misma obra, se reporta la mejor
    # certeza alcanzada y se concatena lo encontrado — sigue siendo evidencia
    # para leer, no una fusión de veredictos.
    orden = {"unico": 0, "ambiguo": 1, "sin_match": 2}
    mejor = min(resultados, key=lambda r: orden[r["certeza"]])
    afiliaciones = sorted({af for r in resultados for af in r["afiliaciones"]})
    nombres = " · ".join(sorted({r["nombre_crossref"] for r in resultados if r["nombre_crossref"]}))

    return {
        **base,
        "crossref_encontrado": True,
        "crossref_tipo": tipo,
        "crossref_anio": fecha or "",
        "crossref_certeza_autor": mejor["certeza"],
        "crossref_autor": nombres,
        "crossref_afiliacion": " | ".join(afiliaciones),
    }


# --------------------------------------------------------------------------- #
# Verificación offline
# --------------------------------------------------------------------------- #

def autotest() -> int:
    casos = []

    def caso(n, ok, obs=None):
        casos.append((n, ok, obs))

    r = emparejar_autor("Franco Fernando Yanine",
                         [{"family": "Yanine", "given": "Franco",
                           "affiliation": [{"name": "Universidad Finis Terrae"}]}])
    caso("apellido único coincide", r["certeza"] == "unico"
         and r["afiliaciones"] == ["Universidad Finis Terrae"], r)

    r = emparejar_autor("Carlos Henríquez‐Olguín",
                         [{"family": "Henriquez-Olguin", "given": "Carlos",
                           "affiliation": [{"name": "Univ. de Chile"}]}])
    caso("apellido compuesto sin acento empareja con acentuado", r["certeza"] == "unico", r)

    r = emparejar_autor("Juan Pérez",
                         [{"family": "Gomez", "given": "Ana", "affiliation": []}])
    caso("sin coincidencia de apellido: sin_match, no inventa", r["certeza"] == "sin_match"
         and r["afiliaciones"] == [], r)

    r = emparejar_autor("Ana Diaz",
                         [{"family": "Diaz", "given": "Marcela", "affiliation": []},
                          {"family": "Diaz", "given": "Roberto", "affiliation": []}])
    caso("dos autores comparten apellido: ambiguo, no elige", r["certeza"] == "ambiguo", r)

    fila = evidencia_de_caso(
        {"openalex_id": "W1", "doi": "10.1/x", "autor_uft": "Franco Fernando Yanine"},
        {"type": "journal-article", "published-print": {"date-parts": [[2023]]},
         "author": [{"family": "Yanine", "given": "Franco",
                     "affiliation": [{"name": "Universidad Finis Terrae"}]}]})
    caso("fila completa: encontrado, tipo y afiliación presentes",
         fila["crossref_encontrado"] and fila["crossref_tipo"] == "journal-article"
         and fila["crossref_afiliacion"] == "Universidad Finis Terrae", fila)

    fila = evidencia_de_caso({"openalex_id": "W2", "doi": "10.1/y", "autor_uft": "Nadie N."}, None)
    caso("DOI sin registro en Crossref: no revienta, queda constancia",
         fila["crossref_encontrado"] is False
         and fila["crossref_certeza_autor"] == "sin_registro", fila)

    fallos = [n for n, ok, _ in casos if not ok]
    for n, ok, obs in casos:
        marca = "OK  " if ok else "FALLA"
        print(f"  {marca} {n}" + (f"  ({obs})" if not ok else ""))
    print(f"\n{len(casos) - len(fallos)}/{len(casos)} comprobaciones")
    return 1 if fallos else 0


# --------------------------------------------------------------------------- #

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--test", action="store_true", help="verifica la lógica sin red")
    ap.add_argument("--limit", type=int, default=None, help="máximo de casos a consultar")
    ap.add_argument("--mailto", default=None, help="correo para el polite pool de Crossref")
    args = ap.parse_args()

    c.banner("EVIDENCIA CROSSREF PARA LA REVISIÓN DE COBERTURA OPENALEX (V2-26 bis)")

    if args.test:
        return autotest()

    mailto = args.mailto or CFG.get("mailto")
    if not mailto:
        sys.exit("Falta un correo de contacto. Use --mailto o declare "
                 "enriquecimiento_externo.orcid.mailto en config/matching_rules.yml")

    if not FUENTE.exists():
        sys.exit(f"Falta {FUENTE.relative_to(c.ROOT)}. Ejecute: "
                  "python3 src/enrich/openalex_cobertura.py")

    df = pd.read_csv(FUENTE, dtype=str)
    con_doi = df[df["doi"].notna() & (df["doi"] != "")]
    if args.limit:
        con_doi = con_doi.head(args.limit)

    print(f"  casos con DOI: {len(con_doi)} de {len(df)}")

    filas, sin_registro, errores = [], 0, 0
    for i, (_, r) in enumerate(con_doi.iterrows(), 1):
        if i % 50 == 0:
            print(f"    {i}/{len(con_doi)}…")
        try:
            msg = consultar(r["doi"], mailto)
        except Exception as e:  # red caída, límite de tasa, etc.
            errores += 1
            if errores <= 3:
                print(f"    aviso · {r['doi']}: {type(e).__name__} {e}")
            if errores > 25:
                sys.exit("ABORTADO: demasiados errores de red. "
                         "Verifique la conectividad con api.crossref.org.")
            continue
        if msg is None:
            sin_registro += 1
        filas.append(evidencia_de_caso(r.to_dict(), msg))

    if not filas:
        print("\n  Sin resultados. No se escribe ningún archivo.")
        return 1

    salida = pd.DataFrame(filas)
    c.write_internal(salida, "openalex_cobertura_crossref.csv")

    con_afiliacion = int((salida["crossref_afiliacion"] != "").sum())
    print(f"\n  consultados                  : {len(salida)}")
    print(f"  sin registro en Crossref     : {sin_registro}")
    print(f"  errores de red               : {errores}")
    print(f"  certeza de autor 'unico'     : {int((salida['crossref_certeza_autor'] == 'unico').sum())}")
    print(f"  certeza de autor 'ambiguo'   : {int((salida['crossref_certeza_autor'] == 'ambiguo').sum())}")
    print(f"  certeza de autor 'sin_match' : {int((salida['crossref_certeza_autor'] == 'sin_match').sum())}")
    print(f"  con afiliación recuperada    : {con_afiliacion}")
    print(f"\n  OK · internal/openalex_cobertura_crossref.csv")
    print("       python3 src/review/build_openalex_review.py la incorpora a la revisión.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
