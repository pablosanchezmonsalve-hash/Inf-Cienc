"""Candidatos de ORCID por afiliación declarada. Para revisión humana, no para publicar.

POR QUÉ ES DISTINTO DE LOS OTROS DOS CONECTORES
    `orcid_crossref.py` y `orcid_expand.py` anclan cada asignación en una
    PUBLICACIÓN COMPARTIDA: la firma y el titular del ORCID coinciden en nombre
    *y* aparecen en el mismo artículo. Esa segunda condición es la que sostiene
    la asignación.

    Esta búsqueda no la tiene. Encuentra a quien declara «Universidad Finis
    Terrae» en su registro de ORCID y compara nombres. Dos personas apellidadas
    Díaz con inicial F. en la misma universidad son indistinguibles por este
    método, y lo serían aunque el registro estuviera perfecto.

    Por eso NO escribe en `authors_orcid.csv` y no llega al sitio. Produce una
    cola de candidatos para que una persona decida, que es lo que exige
    `CLAUDE.md` en <author_master_rule>: «declarar ambigüedades de afiliación
    en vez de resolverlas arbitrariamente».

QUÉ APORTA ENTONCES
    Alcanza a quien no puede alcanzarse por DOI: alguien con ORCID que declara
    la universidad pero cuyo registro no incluye la obra —porque no lo
    sincroniza, o porque la obra es reciente—. Es la única vía que queda para
    las firmas sin ninguna publicación con DOI.

USO
    python3 src/enrich/orcid_afiliacion.py --test
    python3 src/enrich/orcid_afiliacion.py

Salida:
    internal/orcid_candidatos_afiliacion.csv   (capa interna, revisión humana)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import pandas as pd

if sys.platform == "win32":
    # La consola de Windows usa cp1252 por defecto: revienta cualquier print()
    # con caracteres como "→"/"—"/"·". Mismo patrón que src/enrich/orcid_openalex.py.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audit"))
import common as c  # noqa: E402

from orcid_crossref import clave_crossref, clave_firma  # noqa: E402
from orcid_api import credenciales  # noqa: E402

API = "https://pub.orcid.org/v3.0/expanded-search"
PAGINA = 200      # tope que acepta la API por petición


def consultar_pagina(consulta: str, inicio: int, token: str,
                     pausa: float = 0.15) -> tuple[list[dict], int]:
    """Una página de resultados. Devuelve (filas, total declarado por la API)."""
    url = (f"{API}/?q={urllib.parse.quote(consulta)}"
           f"&start={inicio}&rows={PAGINA}")
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "InformeCienciometricoInstitucional/1.0",
    })
    with urllib.request.urlopen(req, timeout=45) as resp:
        data = json.load(resp)
    time.sleep(pausa)
    filas = (data or {}).get("expanded-result") or []
    return filas, int((data or {}).get("num-found") or 0)


def titulares(filas: list[dict]) -> list[dict]:
    """Normaliza a la forma {family, given, ORCID} que usan los otros conectores."""
    salida = []
    for f in filas:
        oid = (f or {}).get("orcid-id")
        if not oid:
            continue
        salida.append({
            "family": (f.get("family-names") or "").strip(),
            "given": (f.get("given-names") or "").strip(),
            "ORCID": oid.strip(),
        })
    return salida


def cruzar(firmas_sin_orcid: list[str], gente: list[dict]) -> pd.DataFrame:
    """Cruza firmas sin ORCID contra titulares que declaran la institución.

    Cada fila es un CANDIDATO, nunca una asignación. Se declara explícitamente
    cuántos titulares coinciden con la firma y cuántas firmas coinciden con el
    titular: una coincidencia 1-a-1 es más prometedora que una 1-a-3, y quien
    revise necesita ver esa diferencia sin recalcularla.
    """
    por_clave: dict[tuple[str, str], list[dict]] = {}
    for p in gente:
        por_clave.setdefault(clave_crossref(p), []).append(p)

    # Cuántas firmas distintas reclaman cada titular.
    firmas_por_orcid: dict[str, set[str]] = {}
    for firma in firmas_sin_orcid:
        for p in por_clave.get(clave_firma(firma), []):
            firmas_por_orcid.setdefault(p["ORCID"], set()).add(firma)

    filas = []
    for firma in firmas_sin_orcid:
        clave = clave_firma(firma)
        if not clave[0]:
            continue
        cands = por_clave.get(clave, [])
        for p in cands:
            filas.append({
                "nombre_en_fuente": firma,
                "orcid": p["ORCID"],
                "nombre_declarado_en_orcid": f"{p['given']} {p['family']}".strip(),
                "titulares_que_coinciden_con_la_firma": len(cands),
                "firmas_que_coinciden_con_el_titular": len(firmas_por_orcid.get(p["ORCID"], set())),
                "tipo": "V2-04_candidato_orcid_por_afiliacion",
                "severidad": "media",
                "consecuencia": "coincide el nombre y la institución, pero NO hay "
                                "publicación compartida que lo respalde",
                "resolucion": "PENDIENTE_REVISION_HUMANA",
            })
    cols = ["nombre_en_fuente", "orcid", "nombre_declarado_en_orcid",
            "titulares_que_coinciden_con_la_firma",
            "firmas_que_coinciden_con_el_titular",
            "tipo", "severidad", "consecuencia", "resolucion"]
    return pd.DataFrame(filas, columns=cols)


def autotest() -> int:
    casos = []

    gente = titulares([
        {"orcid-id": "0000-A", "given-names": "María", "family-names": "Orellana-Donoso"},
        {"orcid-id": "0000-B", "given-names": "Francisca", "family-names": "Díaz"},
        {"orcid-id": "0000-C", "given-names": "Felipe", "family-names": "Díaz"},
        {"orcid-id": "0000-D", "given-names": "Juan", "family-names": "Pérez"},
    ])
    casos.append(("normaliza la respuesta", len(gente) == 4, gente))

    d = cruzar(["Orellana-Donoso M."], gente)
    casos.append(("coincidencia 1-a-1",
                  len(d) == 1 and d.orcid.iloc[0] == "0000-A"
                  and int(d.titulares_que_coinciden_con_la_firma.iloc[0]) == 1, d.to_dict("records")))

    # Dos homónimos: se listan LOS DOS, con el recuento a la vista. No se elige.
    d = cruzar(["Díaz F."], gente)
    casos.append(("homónimos: se listan los dos, no se elige",
                  len(d) == 2 and set(d.orcid) == {"0000-B", "0000-C"}
                  and set(d.titulares_que_coinciden_con_la_firma) == {2}, d.to_dict("records")))

    # Un titular reclamado por dos firmas distintas: también se declara.
    d = cruzar(["Perez J.", "Pérez J."], gente)
    casos.append(("un titular para dos firmas queda declarado",
                  len(d) == 2 and set(d.firmas_que_coinciden_con_el_titular) == {2},
                  d.to_dict("records")))

    # Inicial distinta no es coincidencia.
    casos.append(("inicial distinta no coincide", len(cruzar(["Díaz Z."], gente)) == 0, None))
    # Firma sin apellido utilizable no revienta.
    casos.append(("firma vacía no revienta", len(cruzar([""], gente)) == 0, None))
    # Sin resultados de ORCID no hay candidatos.
    casos.append(("sin titulares no hay candidatos", len(cruzar(["Díaz F."], [])) == 0, None))
    # La salida NUNCA trae columnas publicables de asignación.
    d = cruzar(["Orellana-Donoso M."], gente)
    casos.append(("no emite columnas de asignación publicable",
                  "confianza" not in d.columns and "fuente" not in d.columns, list(d.columns)))
    casos.append(("todo sale marcado para revisión humana",
                  (d.resolucion == "PENDIENTE_REVISION_HUMANA").all(), None))

    ok = True
    for nombre, paso, obs in casos:
        print(f"  {'OK  ' if paso else 'FALLA'} {nombre}" + (f"   {obs}" if not paso else ""))
        ok &= paso
    print("\n" + ("TODOS LOS CASOS OK" if ok else "HAY CASOS FALLANDO"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--test", action="store_true", help="verifica la lógica sin red")
    args = ap.parse_args()

    c.banner("CANDIDATOS DE ORCID POR AFILIACIÓN DECLARADA")
    if args.test:
        return autotest()

    token = credenciales()
    nombre = c.INSTITUTION["institucion"]["nombre_canonico"]
    consulta = f'affiliation-org-name:"{nombre}"'
    print(f"  consulta: {consulta}")

    gente, inicio, total = [], 0, None
    while True:
        filas, num = consultar_pagina(consulta, inicio, token)
        if total is None:
            total = num
            print(f"  titulares que declaran la institución: {total}")
        gente.extend(titulares(filas))
        inicio += PAGINA
        if inicio >= total or not filas:
            break
    print(f"  titulares recuperados: {len(gente)}")

    log = pd.read_csv(c.INTERNAL / "matching_log.csv", dtype=str)
    firmas = set(log["nombre_en_fuente"].unique())
    path_orc = c.ROOT / "data" / "enriched" / "authors_orcid.csv"
    ya = set(pd.read_csv(path_orc, dtype=str)["nombre_en_fuente"]) if path_orc.exists() else set()
    sin_orcid = sorted(firmas - ya)
    print(f"  firmas sin ORCID a cruzar: {len(sin_orcid)}")

    cand = cruzar(sin_orcid, gente)
    if not len(cand):
        print("\n  Sin candidatos. No se escribe ningún archivo.")
        return 0

    c.write_internal(cand.assign(fecha_consulta=date.today().isoformat()),
                     "orcid_candidatos_afiliacion.csv")

    unicos = cand[(cand.titulares_que_coinciden_con_la_firma == 1)
                  & (cand.firmas_que_coinciden_con_el_titular == 1)]
    print(f"\n  candidatos totales           : {len(cand)}")
    print(f"  firmas alcanzadas            : {cand.nombre_en_fuente.nunique()}")
    print(f"  de ellas, coincidencia 1-a-1 : {unicos.nombre_en_fuente.nunique()}")
    print("\n  OK · internal/orcid_candidatos_afiliacion.csv")
    print("       NADA de esto se publica: son candidatos, no asignaciones.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
