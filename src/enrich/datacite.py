"""Enriquecimiento de ORCID desde DataCite (datasets y repositorios).

DataCite es un registro de DOI para datos de investigación, software, y otros
outputs no tradicionales. Su API REST pública no requiere autenticación para
lectura.

QUÉ APORTA
    1. **Datasets** que Scopus/OpenAlex no cubren (data papers, software).
    2. **Contribuyentes** con ORCID en datasets depositados por la institución.
    3. **Cobertura complementaria**: DataCite indexa repositorios institucionales
       (Zenodo, Figshare, institutional repos) que las bases bibliográficas
       principales ignoran.

QUÉ NO HACE
    - No consolida identidades.
    - No reescribe asignaciones vigentes.
    - No distingue autores de contribuidores no científicos.

USO
    python3 src/enrich/datacite.py --test
    python3 src/enrich/datacite.py --limit 25
    python3 src/enrich/datacite.py

Salidas:
    data/enriched/authors_orcid.csv    asignaciones nuevas (SE VERSIONA)
    internal/datacite_log.csv          traza de cada hallazgo
    data/cache/datacite/*.json         respuestas cacheadas (no versionadas)
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

CACHE = c.ROOT / "data" / "cache" / "datacite"
ENRICHED = c.ROOT / "data" / "enriched"
API = "https://api.datacite.org/dois"
FUENTE = "DataCite"


class ContratoDesconocido(Exception):
    """La respuesta no tiene la forma esperada."""


# ────────────────────────────────────────────────── extracción de la respuesta

def extraer(data: dict) -> dict:
    """Normaliza un DOI de DataCite a lo que este proyecto necesita.

    DataCite expone autores en `data.creators` o `data.contributors`.
    Solo se toman los que tengan ORCID (creadores y contribuidores con role
    igual a "Researcher" o "ContactPerson").
    """
    if not isinstance(data, dict) or "data" not in data:
        raise ContratoDesconocido("la respuesta no trae 'data'")

    attrs = (data.get("data") or {}).get("attributes") or {}
    creators = attrs.get("creators")
    if not isinstance(creators, list) or not creators:
        raise ContratoDesconocido("data.attributes.creators no es una lista no vacía")

    autores = []

    for c_item in creators:
        nombre = (c_item.get("name") or "").strip()
        orcid_url = (c_item.get("nameIdentifiers") or {}).get(
            "nameIdentifier", {}
        )
        if isinstance(orcid_url, dict):
            orcid_url = orcid_url.get("nameIdentifier", "")
        orcid = ""
        if "orcid.org" in str(orcid_url):
            orcid = str(orcid_url).rstrip("/").split("/")[-1]

        if nombre:
            partes = nombre.split()
            autores.append({
                "family": partes[-1] if partes else "",
                "given": " ".join(partes[:-1]) if len(partes) > 1 else "",
                "ORCID": orcid or None,
            })

    for cont in attrs.get("contributors") or []:
        role = (cont.get("contributorType") or "").strip()
        if role not in ("Researcher", "ContactPerson", "HostingInstitution"):
            continue
        nombre = (cont.get("name") or "").strip()
        orcid_url = (cont.get("nameIdentifiers") or {}).get(
            "nameIdentifier", {}
        )
        if isinstance(orcid_url, dict):
            orcid_url = orcid_url.get("nameIdentifier", "")
        orcid = ""
        if "orcid.org" in str(orcid_url):
            orcid = str(orcid_url).rstrip("/").split("/")[-1]

        if nombre:
            partes = nombre.split()
            autores.append({
                "family": partes[-1] if partes else "",
                "given": " ".join(partes[:-1]) if len(partes) > 1 else "",
                "ORCID": orcid or None,
            })

    return {"autores": autores}


# ─────────────────────────────────────────────────────────────────────── red

def _cache_path(doi: str) -> Path:
    return CACHE / (re.sub(r"[^a-zA-Z0-9]+", "_", doi)[:120] + ".json")


def consultar(doi: str, pausa: float = 0.12) -> dict | None:
    """Un DOI por consulta. Cachea en disco."""
    path = _cache_path(doi)
    if path.exists():
        raw = path.read_text(encoding="utf-8")
        return json.loads(raw) if raw.strip() else None

    url = f"{API}/{urllib.parse.quote(doi, safe='')}"
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

DATACITE_EJEMPLO = {
    "data": {
        "type": "dois",
        "id": "10.1234/ejemplo",
        "attributes": {
            "creators": [
                {
                    "name": "Marcela Diaz",
                    "nameIdentifiers": {
                        "nameIdentifier": {
                            "nameIdentifierScheme": "ORCID",
                            "nameIdentifier": "https://orcid.org/0000-0002-1825-0097",
                        }
                    },
                },
                {"name": "Juan Perez", "nameIdentifiers": {}},
            ],
            "contributors": [
                {
                    "name": "Ana Test",
                    "contributorType": "Researcher",
                    "nameIdentifiers": {
                        "nameIdentifier": {
                            "nameIdentifierScheme": "ORCID",
                            "nameIdentifier": "https://orcid.org/0000-0001-1111-1111",
                        }
                    },
                },
                {
                    "name": "Editor X",
                    "contributorType": "Editor",
                    "nameIdentifiers": {},
                },
            ],
        },
    }
}


def autotest() -> int:
    casos = []

    def caso(n, ok, obs=None):
        casos.append((n, ok, obs))

    d = extraer(DATACITE_EJEMPLO)
    caso("extrae creadores con ORCID",
         d["autores"][0]["ORCID"] == "0000-0002-1825-0097", d)
    caso("creador sin ORCID queda None",
         d["autores"][1]["ORCID"] is None, d)
    caso("extrae contribuidores Researcher",
         any(a["ORCID"] == "0000-0001-1111-1111" for a in d["autores"]), d)
    caso("no extrae editores",
         not any("Editor" in (a.get("given", "") + " " + a.get("family", ""))
                  for a in d["autores"]), d)

    try:
        extraer({"data": {"attributes": {}}})
        caso("data sin creators se detecta", False, "no lanzó")
    except ContratoDesconocido:
        caso("data sin creators se detecta", True)

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

    c.banner("ENRIQUECIMIENTO DESDE DATACITE")
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

    print(f"\n  DOI que DataCite no tiene        : {sin_obra}")
    print(f"  errores de red                   : {errores}")

    if not hallazgos:
        print("\n  Sin asignaciones nuevas. No se escribe authors_orcid.csv.")
        return 0

    hoy = date.today().isoformat()
    h = pd.DataFrame(hallazgos)
    c.write_internal(h.assign(fecha_consulta=hoy), "datacite_log.csv")

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
