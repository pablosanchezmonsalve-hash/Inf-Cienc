"""Enriquecimiento de ORCID desde Europe PMC (acceso abierto biomédico).

Europe PMC indexa PubMed, PubMed Central, y repositorios de acceso abierto.
Su API REST pública no requiere autenticación.

QUÉ APORTA
    1. **Publicaciones de acceso abierto** que Scopus/OpenAlex pueden no tener.
    2. **ORCID declarado por autores** en biomedical literature.
    3. **Verificación cruzada** de asignaciones existentes contra PubMed/PMC.

QUÉ NO HACE
    - No consolida identidades.
    - No reescribe asignaciones vigentes.
    - No cubre ciencias sociales ni humanidades (enfoque biomédico).

USO
    python3 src/enrich/europepmc.py --test
    python3 src/enrich/europepmc.py --limit 25
    python3 src/enrich/europepmc.py

Salidas:
    data/enriched/authors_orcid.csv    asignaciones nuevas (SE VERSIONA)
    internal/europepmc_log.csv         traza de cada hallazgo
    data/cache/europepmc/*.json        respuestas cacheadas (no versionadas)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import pandas as pd

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audit"))
import common as c  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from orcid_crossref import emparejar, clave_firma  # noqa: E402

CACHE = c.ROOT / "data" / "cache" / "europepmc"
ENRICHED = c.ROOT / "data" / "enriched"
API = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
FUENTE = "Europe PMC"


class ContratoDesconocido(Exception):
    """La respuesta no tiene la forma esperada."""


# ────────────────────────────────────────────────── extracción de la respuesta

def extraer(data: dict) -> dict:
    """Normaliza una respuesta de Europe PMC a lo que este proyecto necesita.

    Europe PMC devuelve `resultList.result` como lista de publicaciones.
    Cada publicación tiene `authorString` (cadena libre) y `orcid` (del primer autor).
    La cadena de autores se parsea para extraer nombre + ORCID cuando está disponible.
    """
    if not isinstance(data, dict) or "resultList" not in data:
        raise ContratoDesconocido("la respuesta no trae 'resultList'")

    result_list = data.get("resultList") or {}
    results = result_list.get("result")
    if not isinstance(results, list):
        raise ContratoDesconocido("resultList.result no es una lista")

    autores_vistos = set()
    autores = []

    for pub in results:
        orcid = (pub.get("orcid") or "").strip()
        author_string = (pub.get("authorString") or "").strip()

        if not author_string:
            continue

        # Europe PMC da la cadena como "Apellido I, Apellido I, ..."
        # El ORCID es solo del primer autor (no hay ORCID por autor en la respuesta)
        partes = [a.strip() for a in author_string.split(",")]
        for i, nombre in enumerate(partes):
            if not nombre or nombre in autores_vistos:
                continue
            autores_vistos.add(nombre)

            tokens = nombre.split()
            # "Diaz M" / "Smith AB" = Surname Initial(s) (academic citation
            # format). El bloque de iniciales es el ÚLTIMO token, TODO en
            # mayúsculas — puede tener más de una letra ("AB" = A. B.).
            # Asumir que sólo un token de una letra es inicial perdía casos
            # así enteros como apellido ("Smith AB" -> family "Smith AB",
            # given ""): el apellido de la fuente nunca viene en mayúsculas,
            # así que ese último token siempre es el bloque de iniciales.
            if len(tokens) > 1 and tokens[-1].isalpha() and tokens[-1].isupper():
                apellido = " ".join(tokens[:-1])
                inicial = tokens[-1]
            else:
                apellido = " ".join(tokens)
                inicial = ""

            autores.append({
                "family": apellido,
                "given": inicial,
                "ORCID": orcid if i == 0 and orcid else None,
            })

    return {"autores": autores}


# ─────────────────────────────────────────────────────────────────────── red

def _cache_path(doi: str) -> Path:
    return CACHE / (re.sub(r"[^a-zA-Z0-9]+", "_", doi)[:120] + ".json")


def consultar(doi: str, pausa: float = 0.12) -> dict | None:
    """Una obra por DOI. Cachea en disco."""
    path = _cache_path(doi)
    if path.exists():
        raw = path.read_text(encoding="utf-8")
        return json.loads(raw) if raw.strip() else None

    params = urllib.parse.urlencode({
        "query": f"DOI:{doi}",
        "format": "json",
        "resultType": "core",
    })
    url = f"{API}?{params}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "InformeCienciometrico/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            CACHE.mkdir(parents=True, exist_ok=True)
            path.write_text("null", encoding="utf-8")
            return None
        raise
    finally:
        time.sleep(pausa)

    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


# ────────────────────────────────────────────────────────────────── autotest

EUROPEPMC_EJEMPLO = {
    "resultList": {
        "result": [
            {
                "doi": "10.1234/ejemplo",
                "authorString": "Diaz M, Perez J, Garcia L",
                "orcid": "0000-0002-1825-0097",
            }
        ]
    }
}


def autotest() -> int:
    casos = []

    def caso(n, ok, obs=None):
        casos.append((n, ok, obs))

    d = extraer(EUROPEPMC_EJEMPLO)
    caso("extrae autores de la cadena",
         len(d["autores"]) == 3, d)
    caso("primer autor tiene ORCID",
         d["autores"][0]["ORCID"] == "0000-0002-1825-0097", d)
    caso("autores posteriores no tienen ORCID",
         all(a["ORCID"] is None for a in d["autores"][1:]), d)

    try:
        extraer({"resultList": {"result": "NO-ES-LISTA"}})
        caso("result no-lista se detecta", False, "no lanzó")
    except ContratoDesconocido:
        caso("result no-lista se detecta", True)

    # Una lista vacía es un resultado legítimo: «este DOI no está en Europe PMC».
    d_vacio = extraer({"resultList": {"result": []}})
    caso("result vacío es válido y no produce autores", d_vacio["autores"] == [], d_vacio)

    # Bug real: un bloque de DOS iniciales ("AB") se perdía entero como
    # apellido porque sólo un token de una letra se reconocía como inicial.
    d_dos = extraer({"resultList": {"result": [
        {"authorString": "Smith AB, Diaz M", "orcid": ""}]}})
    caso("apellido con bloque de dos iniciales se separa bien",
         d_dos["autores"][0]["family"] == "Smith"
         and d_dos["autores"][0]["given"] == "AB", d_dos)
    caso("un autor normal en la misma cadena no se rompe",
         d_dos["autores"][1]["family"] == "Diaz"
         and d_dos["autores"][1]["given"] == "M", d_dos)

    # Apellido compuesto con guion: el guion no debe confundirse con el
    # bloque de iniciales.
    d_guion = extraer({"resultList": {"result": [
        {"authorString": "Smith-Jones AB", "orcid": ""}]}})
    caso("apellido con guion conserva el guion y separa las iniciales",
         d_guion["autores"][0]["family"] == "Smith-Jones"
         and d_guion["autores"][0]["given"] == "AB", d_guion)

    # Un solo token en mayúsculas (sin apellido separado) no debe vaciar
    # el apellido: sin guarda de longitud, "family" quedaría "".
    d_solo = extraer({"resultList": {"result": [
        {"authorString": "M", "orcid": ""}]}})
    caso("un solo token no deja el apellido vacío",
         d_solo["autores"][0]["family"] == "M"
         and d_solo["autores"][0]["given"] == "", d_solo)

    m = emparejar(["Diaz M."], d["autores"])
    caso("la forma extraída alimenta a emparejar",
         len(m) == 1 and m[0]["orcid"] == "0000-0002-1825-0097", m)

    ok = True
    for n, paso, obs in casos:
        print(f"  {'OK  ' if paso else 'FALLA'} {n}" + (f"   {obs}" if not paso else ""))
        ok &= paso
    print("\n" + ("TODOS LOS CASOS OK" if ok else "HAY CASOS FALLANDO"))
    return 0 if ok else 1


# ───────────────────────────────────────────────────────────────────── main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--test", action="store_true", help="verifica la lógica sin red")
    ap.add_argument("--limit", type=int, default=None, help="máximo de DOI a consultar")
    args = ap.parse_args()

    c.banner("ENRIQUECIMIENTO DESDE EUROPE PMC")
    if args.test:
        return autotest()

    universo = c.INTERIM / "publications_universe.csv"
    if not universo.exists():
        sys.exit("Falta data/interim/publications_universe.csv. "
                 "Ejecute:  python3 src/audit/run_all.py")

    uni = pd.read_csv(universo, dtype=str)
    log_path = c.INTERNAL / "matching_log.csv"
    log = pd.read_csv(log_path, dtype=str) if log_path.exists() else pd.DataFrame()
    firmas_por_eid = log.groupby("eid")["nombre_en_fuente"].apply(list).to_dict() if len(log) else {}

    path_vig = ENRICHED / "authors_orcid.csv"
    vig = (pd.read_csv(path_vig, dtype=str) if path_vig.exists()
           else pd.DataFrame(columns=["nombre_en_fuente", "orcid",
                                      "publicaciones_de_respaldo", "confianza", "fuente"]))
    ya = dict(zip(vig["nombre_en_fuente"], vig["orcid"]))

    con_doi = uni[uni["doi"].notna() & (uni["doi"].astype(str).str.strip() != "")]
    filas = con_doi.head(args.limit) if args.limit else con_doi
    print(f"  publicaciones con DOI            : {len(filas)} de {len(uni)}")
    print(f"  asignaciones vigentes            : {len(vig)}")

    hallazgos, errores, sin_obra = [], 0, 0
    for i, (_, r) in enumerate(filas.iterrows(), 1):
        if i % 50 == 0:
            print(f"    {i}/{len(filas)}...  hallazgos: {len(hallazgos)}")
        doi = str(r["doi"]).strip()
        try:
            data = consultar(doi)
        except Exception as e:
            errores += 1
            if errores <= 3:
                print(f"    aviso · {doi}: {type(e).__name__} {e}")
            if errores > 25:
                sys.exit("ABORTADO: demasiados errores. Verifique la red.")
            continue
        if not data:
            sin_obra += 1
            continue
        try:
            obra = extraer(data)
        except ContratoDesconocido as e:
            crudo = CACHE / "ultima_respuesta.json"
            crudo.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                             encoding="utf-8")
            sys.exit(f"\n  EL CONTRATO DE LA API NO ES EL ESPERADO: {e}\n"
                     f"  Respuesta cruda en {crudo.relative_to(c.ROOT)}\n\n"
                     "  No se adivina la forma. Envíe ese archivo y se corrige.")

        firmas = firmas_por_eid.get(r["eid"], [])
        for m in emparejar(firmas, obra["autores"]):
            if m.get("orcid"):
                hallazgos.append({"firma": m["firma"], "orcid": m["orcid"],
                                  "eid": r["eid"], "doi": doi, "match": m["match"]})

    print(f"\n  DOI que Europe PMC no tiene      : {sin_obra}")
    print(f"  errores de red                   : {errores}")

    if not hallazgos:
        print("\n  Sin asignaciones nuevas. No se escribe authors_orcid.csv.")
        return 0

    hoy = date.today().isoformat()
    h = pd.DataFrame(hallazgos)
    c.write_internal(h.assign(fecha_consulta=hoy), "europepmc_log.csv")

    nuevas, concordantes = [], 0
    for firma, g in h.groupby("firma"):
        conteo = g.groupby("orcid")["eid"].nunique().sort_values(ascending=False)
        if len(conteo) > 1 and conteo.iloc[0] == conteo.iloc[1]:
            continue
        orcid, respaldo = conteo.index[0], int(conteo.iloc[0])
        if firma in ya:
            concordantes += 1
            continue
        nuevas.append({"nombre_en_fuente": firma, "orcid": orcid,
                       "publicaciones_de_respaldo": respaldo,
                       "confianza": "alta" if respaldo > 1 else "media",
                       "fuente": FUENTE})

    print(f"\n  asignaciones nuevas              : {len(nuevas)}")
    print(f"  concordantes con las vigentes    : {concordantes}")

    if nuevas:
        salida = pd.concat([vig, pd.DataFrame(nuevas)], ignore_index=True)
        salida = salida.sort_values("nombre_en_fuente", kind="stable")
        salida.to_csv(path_vig, index=False, encoding="utf-8")
        print(f"  cobertura                        : {len(vig)} → {len(salida)}")
        print(f"\n  OK · data/enriched/authors_orcid.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
