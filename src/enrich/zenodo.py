"""Enriquecimiento de ORCID desde Zenodo (preservación de datos CERN).

Zenodo es un repositorio de datos de investigación del CERN, parte de la
infraestructura OpenAIRE. Su API REST pública no requiere autenticación.

QUÉ APORTA
    1. **Datasets, software, posters, presentaciones** que Scopus/OpenAlex no cubren.
    2. **ORCID declarado por autores** al depositar.
    3. **Preservación long-term** de outputs no tradicionales.

QUÉ NO HACE
    - No consolida identidades.
    - No reescribe asignaciones vigentes.
    - No cubre publicaciones de revistas (solo depósitos).

USO
    python3 src/enrich/zenodo.py --test
    python3 src/enrich/zenodo.py --limit 25
    python3 src/enrich/zenodo.py

Salidas:
    data/enriched/authors_orcid.csv    asignaciones nuevas (SE VERSIONA)
    internal/zenodo_log.csv            traza de cada hallazgo
    data/cache/zenodo/*.json           respuestas cacheadas (no versionadas)
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

CACHE = c.ROOT / "data" / "cache" / "zenodo"
ENRICHED = c.ROOT / "data" / "enriched"
API = "https://zenodo.org/api/records"
FUENTE = "Zenodo"


class ContratoDesconocido(Exception):
    """La respuesta no tiene la forma esperada."""


# ────────────────────────────────────────────────── extracción de la respuesta

def extraer(data: dict) -> dict:
    """Normaliza un registro de Zenodo a lo que este proyecto necesita.

    Zenodo expone autores en `metadata.creators`. Cada creator tiene `name`
    y opcionalmente `orcid`.
    """
    if not isinstance(data, dict) or "metadata" not in data:
        raise ContratoDesconocido("la respuesta no trae 'metadata'")

    metadata = data.get("metadata") or {}
    creators = metadata.get("creators")
    if not isinstance(creators, list) or not creators:
        raise ContratoDesconocido("metadata.creators no es una lista no vacía")

    autores = []

    for c_item in creators:
        nombre = (c_item.get("name") or "").strip()
        orcid = (c_item.get("orcid") or "").strip()

        if nombre:
            # Zenodo usa formato "Apellido, Nombre" o "Nombre Apellido"
            if "," in nombre:
                partes = [p.strip() for p in nombre.split(",", 1)]
                apellido = partes[0]
                dado = partes[1] if len(partes) > 1 else ""
            else:
                partes = nombre.split()
                apellido = partes[-1] if partes else ""
                dado = " ".join(partes[:-1]) if len(partes) > 1 else ""

            autores.append({
                "family": apellido,
                "given": dado,
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

    params = urllib.parse.urlencode({
        "q": f"doi:{doi}",
        "format": "json",
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

    # Zenodo devuelve una lista de resultados; tomar el primero si existe
    hits = (data.get("hits") or {}).get("hits") or []
    result = hits[0] if hits else None

    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False) if result else "null",
                    encoding="utf-8")
    return result


# ────────────────────────────────────────────────────────────────── autotest

ZENODO_EJEMPLO = {
    "metadata": {
        "creators": [
            {"name": "Diaz, Marcela", "orcid": "0000-0002-1825-0097"},
            {"name": "Perez, Juan", "orcid": ""},
        ]
    }
}


def autotest() -> int:
    casos = []

    def caso(n, ok, obs=None):
        casos.append((n, ok, obs))

    d = extraer(ZENODO_EJEMPLO)
    caso("extrae creadores con ORCID",
         d["autores"][0]["ORCID"] == "0000-0002-1825-0097", d)
    caso("creador sin ORCID queda None",
         d["autores"][1]["ORCID"] is None, d)
    caso("apellido y dado se separan (formato coma)",
         d["autores"][0]["family"] == "Diaz" and d["autores"][0]["given"] == "Marcela", d)

    # Probar formato sin coma
    d2 = extraer({"metadata": {"creators": [{"name": "Marcela Diaz", "orcid": "0000-0002-1825-0097"}]}})
    caso("apellido y dado se separan (formato espacio)",
         d2["autores"][0]["family"] == "Diaz" and d2["autores"][0]["given"] == "Marcela", d2)

    try:
        extraer({"metadata": {"creators": []}})
        caso("metadata sin creators se detecta", False, "no lanzó")
    except ContratoDesconocido:
        caso("metadata sin creators se detecta", True)

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

    c.banner("ENRIQUECIMIENTO DESDE ZENODO")
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

    print(f"\n  DOI que Zenodo no tiene          : {sin_obra}")
    print(f"  errores de red                   : {errores}")

    if not hallazgos:
        print("\n  Sin asignaciones nuevas. No se escribe authors_orcid.csv.")
        return 0

    hoy = date.today().isoformat()
    h = pd.DataFrame(hallazgos)
    c.write_internal(h.assign(fecha_consulta=hoy), "zenodo_log.csv")

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
