"""Evidencia de Crossref para financiamiento declarado (la fuente
complementaria que `X-03` pedía).

QUÉ RESUELVE
    `config/indicators.yml` -> `X-03` ("Indicadores de financiamiento") está
    sin publicar: "Cobertura 37,4 %: insuficiente para reportar sin sesgo",
    y declara qué falta: "Fuente complementaria de financiamiento". Ese
    37,4 % sale de `Funding Details`/`Funding Texts` en el export nativo de
    Scopus (306 de 818 filas) — un campo real, ya en el proyecto, que hasta
    ahora ningún paso del pipeline extraía (no llega a
    `publications_universe.csv`: verificado, no está entre sus columnas).

    Este conector hace dos cosas, no una: (1) extrae por fin el campo de
    Scopus que ya existía y no se usaba, y (2) consulta Crossref por DOI,
    que trae financiamiento de una fuente DISTINTA (el `funder` que el
    editor registró directamente en Crossref, con su propio identificador
    del Crossref Funder Registry) — no una segunda copia del mismo dato.

QUÉ NO HACE
    No decide si `X-03` se publica. Subir su cobertura por encima del umbral
    que hoy lo bloquea es una pregunta que sólo se responde con las cifras
    reales de esta consulta —que este script no puede generar en un entorno
    sin salida a red (ver más abajo)—, y aun con esas cifras, publicar un
    indicador nuevo sigue siendo la decisión de alcance que el propio
    `X-03` no toma por sí solo. No fusiona el nombre de financiador que
    declaró Scopus con el que declaró Crossref: son dos fuentes con su
    propio texto libre, y decidir que "CONICYT" y "Agencia Nacional de
    Investigación y Desarrollo" son la misma entidad —lo son, cambió de
    nombre— es exactamente el tipo de normalización de vocabulario que este
    proyecto no hace sin validación institucional (mismo principio que
    `config/matching_rules.yml` -> `unidad_academica.vocabulario`). Se
    reportan las dos cadenas, una al lado de la otra, para que una persona
    decida.

EL CONTRATO DE LA API NO ESTÁ VERIFICADO DESDE ESTE REPOSITORIO
    La política de red de este entorno bloquea `api.crossref.org` (mismo
    hallazgo que ya documentan `openalex_cobertura.py` y
    `facultad_medicina_publicaciones.py` para sus propios dominios;
    comprobado aquí con una consulta real, que devolvió
    `CONNECT tunnel failed, response 403`). El conector usa
    `crossref_client.py` (mismo patrón de caché y manejo de errores que
    `orcid_crossref.py`/`openalex_cobertura_crossref.py` —que SÍ corrieron,
    en una sesión con acceso de red real; factorizado a un módulo
    compartido porque este conector es ya la tercera copia del mismo
    transporte, y los dos anteriores no se tocan por no tener relación con
    esta sesión) — y su lógica de parseo está probada con `--test`, sin
    red. Ejecutarlo de verdad queda para una máquina con acceso a
    `api.crossref.org`.

USO
    python3 src/enrich/crossref_financiamiento.py             # consulta Crossref
    python3 src/enrich/crossref_financiamiento.py --test      # verifica la lógica, sin red
    python3 src/enrich/crossref_financiamiento.py --limit 20  # prueba con pocos casos

Salida:
    data/enriched/crossref_financiamiento.csv   evidencia por publicación
    data/cache/crossref/*.json                  respuestas cacheadas (compartido con V2-01/V2-26 bis)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audit"))
import common as c  # noqa: E402
from crossref_client import consultar  # noqa: E402

RAW_SCOPUS = c.ROOT / c.SOURCES["scopus_export"]["archivo"]
SALIDA = c.ROOT / "data" / "enriched" / "crossref_financiamiento.csv"
CFG = c.MATCHING["enriquecimiento_externo"]["orcid"]


def normalizar_doi(doi) -> str:
    if doi is None or (isinstance(doi, float) and pd.isna(doi)):
        return ""
    doi = str(doi).strip()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
    return doi


def financiadores_scopus(funding_details) -> list[str]:
    """`Funding Details` es texto libre separado por ';': una entrada por
    financiador (a veces repetida, una vez con el número de proyecto entre
    paréntesis y otra sin él — artefacto del export, no se colapsa: cada
    entrada es lo que Scopus escribió, tal cual)."""
    if funding_details is None or (isinstance(funding_details, float) and pd.isna(funding_details)):
        return []
    return [f.strip() for f in str(funding_details).split(";") if f.strip()]


def financiadores_crossref(msg: dict) -> list[dict]:
    """`message.funder` de Crossref: cada entrada trae `name`, a veces `DOI`
    (identificador del Crossref Funder Registry — un registro real, no un
    invento de este proyecto) y `award` (lista de números de proyecto)."""
    out = []
    for f in msg.get("funder", []) or []:
        nombre = f.get("name", "")
        if not nombre:
            continue
        out.append({
            "nombre": nombre,
            "funder_doi": f.get("DOI", "") or "",
            "proyectos": ", ".join(f.get("award", []) or []),
        })
    return out


def _texto_financiador(f: dict) -> str:
    """'Nombre (funder DOI) [proyectos]', omitiendo lo que falte."""
    texto = f["nombre"]
    if f["funder_doi"]:
        texto += f" ({f['funder_doi']})"
    if f["proyectos"]:
        texto += f" [{f['proyectos']}]"
    return texto


def evidencia_de_publicacion(row: dict, msg: dict | None) -> dict:
    fin_scopus = financiadores_scopus(row.get("Funding Details"))
    base = {
        "eid": row.get("EID", ""),
        "doi": row.get("_doi_norm", ""),
        "scopus_financiado": bool(fin_scopus),
        "scopus_financiadores": " | ".join(fin_scopus),
    }
    if msg is None:
        return {**base, "crossref_encontrado": False, "crossref_financiado": False,
                "crossref_financiadores": ""}

    fin_crossref = financiadores_crossref(msg)
    return {
        **base,
        "crossref_encontrado": True,
        "crossref_financiado": bool(fin_crossref),
        "crossref_financiadores": " | ".join(_texto_financiador(f) for f in fin_crossref),
    }


def autotest() -> int:
    casos = []

    def caso(n, ok, obs=None):
        casos.append((n, ok, obs))

    caso("Scopus: separa por ';' y conserva cada entrada tal cual",
         financiadores_scopus("ANID, (123); ANID") == ["ANID, (123)", "ANID"])
    caso("Scopus: NaN no revienta, lista vacía", financiadores_scopus(float("nan")) == [])
    caso("Scopus: None no revienta, lista vacía", financiadores_scopus(None) == [])

    fin = financiadores_crossref({"funder": [
        {"name": "ANID", "DOI": "10.13039/501100002850", "award": ["FB210015", "1251441"]},
        {"name": "Sin DOI ni award"},
    ]})
    caso("Crossref: extrae nombre, DOI de financiador y proyectos",
         fin[0]["nombre"] == "ANID" and fin[0]["funder_doi"] == "10.13039/501100002850"
         and fin[0]["proyectos"] == "FB210015, 1251441", fin)
    caso("Crossref: financiador sin DOI/award no revienta",
         fin[1]["nombre"] == "Sin DOI ni award" and fin[1]["funder_doi"] == "" and fin[1]["proyectos"] == "", fin)
    caso("Crossref: sin 'funder' en el mensaje -> lista vacía",
         financiadores_crossref({}) == [])

    fila = evidencia_de_publicacion(
        {"EID": "e1", "_doi_norm": "10.1016/x", "Funding Details": "ANID, (123)"},
        {"funder": [{"name": "ANID", "DOI": "10.13039/501100002850", "award": ["123"]}]})
    caso("fila completa: coincide financiado en las dos fuentes",
         fila["scopus_financiado"] and fila["crossref_financiado"]
         and "ANID" in fila["crossref_financiadores"], fila)

    fila = evidencia_de_publicacion(
        {"EID": "e2", "_doi_norm": "10.1016/y", "Funding Details": None}, None)
    caso("sin financiamiento en Scopus, DOI sin registro en Crossref: no revienta",
         not fila["scopus_financiado"] and fila["crossref_encontrado"] is False
         and not fila["crossref_financiado"], fila)

    fila = evidencia_de_publicacion(
        {"EID": "e3", "_doi_norm": "10.1016/z", "Funding Details": None},
        {"funder": [{"name": "Wellcome Trust"}]})
    caso("Crossref encuentra financiamiento que Scopus no declaraba",
         not fila["scopus_financiado"] and fila["crossref_financiado"], fila)

    caso("normalizar_doi limpia el prefijo de URL",
         normalizar_doi("https://doi.org/10.1016/J.AAA.2024") == "10.1016/J.AAA.2024")
    caso("normalizar_doi con NaN no revienta", normalizar_doi(float("nan")) == "")

    fallos = [n for n, ok, _ in casos if not ok]
    for n, ok, obs in casos:
        marca = "OK  " if ok else "FALLA"
        print(f"  {marca} {n}" + (f"  ({obs})" if not ok else ""))
    print(f"\n{len(casos) - len(fallos)}/{len(casos)} comprobaciones")
    return 1 if fallos else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--test", action="store_true", help="verifica la lógica sin red")
    ap.add_argument("--limit", type=int, default=None, help="máximo de publicaciones a consultar")
    ap.add_argument("--mailto", default=None, help="correo para el polite pool de Crossref")
    args = ap.parse_args()

    c.banner("EVIDENCIA CROSSREF PARA FINANCIAMIENTO DECLARADO (X-03)")

    if args.test:
        return autotest()

    mailto = args.mailto or CFG.get("mailto")
    if not mailto:
        sys.exit("Falta un correo de contacto. Use --mailto o declare "
                 "enriquecimiento_externo.orcid.mailto en config/matching_rules.yml")

    df = pd.read_csv(RAW_SCOPUS, encoding=c.SOURCES["scopus_export"]["encoding"],
                      header=c.SOURCES["scopus_export"]["header_row"])
    df["_doi_norm"] = df["DOI"].map(normalizar_doi)
    con_doi = df[df["_doi_norm"] != ""]
    if args.limit:
        con_doi = con_doi.head(args.limit)

    print(f"  publicaciones con DOI: {len(con_doi)} de {len(df)}")
    print(f"  con Funding Details ya en Scopus (todo el export): "
          f"{int(df['Funding Details'].notna().sum())} de {len(df)}")

    filas, sin_registro, errores = [], 0, 0
    for i, (_, r) in enumerate(con_doi.iterrows(), 1):
        if i % 50 == 0:
            print(f"    {i}/{len(con_doi)}…")
        try:
            msg = consultar(r["_doi_norm"], mailto)
        except Exception as e:  # red caída, límite de tasa, etc.
            errores += 1
            if errores <= 3:
                print(f"    aviso · {r['_doi_norm']}: {type(e).__name__} {e}")
            if errores > 25:
                sys.exit("ABORTADO: demasiados errores de red. "
                         "Verifique la conectividad con api.crossref.org.")
            continue
        if msg is None:
            sin_registro += 1
        filas.append(evidencia_de_publicacion(r.to_dict(), msg))

    if not filas:
        print("\n  Sin resultados. No se escribe ningún archivo.")
        return 1

    salida = pd.DataFrame(filas)
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    salida.to_csv(SALIDA, index=False, encoding="utf-8")

    solo_scopus = int((salida["scopus_financiado"] & ~salida["crossref_financiado"]).sum())
    solo_crossref = int((~salida["scopus_financiado"] & salida["crossref_financiado"]).sum())
    ambas = int((salida["scopus_financiado"] & salida["crossref_financiado"]).sum())
    ninguna = int((~salida["scopus_financiado"] & ~salida["crossref_financiado"]).sum())
    print(f"\n  consultados en Crossref      : {len(salida)}")
    print(f"  sin registro en Crossref     : {sin_registro}")
    print(f"  errores de red               : {errores}")
    print(f"  financiado en ambas fuentes  : {ambas}")
    print(f"  sólo en Scopus                : {solo_scopus}")
    print(f"  sólo en Crossref               : {solo_crossref}")
    print(f"  sin financiamiento declarado en ninguna: {ninguna}")
    print(f"  cobertura combinada (al menos una fuente): "
          f"{100 * (ambas + solo_scopus + solo_crossref) / len(salida):.1f} %"
          f"  (Scopus solo: {100 * df['Funding Details'].notna().sum() / len(df):.1f} %)")
    print(f"\n  OK · {SALIDA.relative_to(c.ROOT)}")
    print("       Esta cifra es la que decide si X-03 (config/indicators.yml) "
          "cruza el umbral que hoy lo mantiene sin publicar — decisión "
          "aparte, no automática.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
