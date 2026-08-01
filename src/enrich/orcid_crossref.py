"""Enriquecimiento de ORCID desde Crossref (pendiente V2-01).

ORCID no existe en los exports de Scopus ni de SciVal. Crossref lo expone por
DOI de forma pública y gratuita, y el corpus tiene DOI en el 97,7 % de los
registros.

QUÉ HACE
    Por cada DOI, consulta Crossref y extrae los ORCID declarados por autor.
    Luego intenta asociarlos a las formas de firma institucionales detectadas en esa misma
    publicación, comparando apellido normalizado e inicial del nombre.

QUÉ NO HACE
    No consolida identidades. Si una firma aparece con más de un ORCID a lo
    largo de sus publicaciones, el conflicto se encola sin resolver
    (decisión D-08). Un ORCID asignado por coincidencia de apellido e inicial
    es una hipótesis, no un hecho: por eso cada asignación lleva su nivel de
    confianza y el número de publicaciones que la respaldan.

USO
    python3 src/enrich/orcid_crossref.py            # consulta Crossref
    python3 src/enrich/orcid_crossref.py --test     # verifica la lógica offline
    python3 src/enrich/orcid_crossref.py --limit 50 # prueba con pocos DOI

Salidas:
    data/enriched/authors_orcid.csv    asignaciones publicables (SE VERSIONA)
    internal/orcid_conflicts.csv       conflictos y ambigüedades (capa interna)
    internal/identity_candidates.csv   firmas que comparten ORCID (capa interna)
    data/cache/crossref/*.json         respuestas cacheadas (no versionadas)

El resultado NO va a data/interim/: ese directorio contiene derivados que se
regeneran sin salida a red, y por eso está fuera del control de versiones. Este
archivo, en cambio, requiere ~800 consultas a Crossref para reconstruirse. Es
dato nuevo, no un intermedio, y pertenece al repositorio.
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

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audit"))
import common as c  # noqa: E402

CACHE = c.ROOT / "data" / "cache" / "crossref"
ENRICHED = c.ROOT / "data" / "enriched"
API = "https://api.crossref.org/works/"

CFG = c.MATCHING["enriquecimiento_externo"]["orcid"]


# --------------------------------------------------------------------------- #
# Normalización de nombres
# --------------------------------------------------------------------------- #

def _norm(text: str) -> str:
    base = unicodedata.normalize("NFD", str(text or ""))
    base = "".join(ch for ch in base if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z\s]", " ", base.lower()).strip()


def clave_firma(nombre: str) -> tuple[str, str]:
    """Descompone una firma Scopus ('Orellana-Donoso M.I.') en apellido e inicial.

    Scopus escribe 'Apellido[-Compuesto] I.I.'. El apellido puede tener varias
    palabras; las iniciales van al final y son tokens de una sola letra.
    """
    tokens = _norm(nombre.replace("-", " ")).split()
    if not tokens:
        return "", ""
    apellido = [t for t in tokens if len(t) > 1]
    iniciales = [t for t in tokens if len(t) == 1]
    return " ".join(apellido), (iniciales[0] if iniciales else "")


def clave_crossref(autor: dict) -> tuple[str, str]:
    """Misma descomposición para un autor de Crossref (family / given)."""
    apellido = _norm(autor.get("family", "").replace("-", " "))
    dado = _norm(autor.get("given", ""))
    inicial = dado[0] if dado else ""
    return apellido, inicial


# --------------------------------------------------------------------------- #
# Consulta a Crossref
# --------------------------------------------------------------------------- #

def _cache_path(doi: str) -> Path:
    return CACHE / (re.sub(r"[^a-zA-Z0-9]+", "_", doi)[:120] + ".json")


def consultar(doi: str, mailto: str, pausa: float = 0.12) -> dict | None:
    """Devuelve el registro de Crossref para un DOI, o None si no existe.

    Cachea en disco: reejecutar no vuelve a golpear la API.
    """
    path = _cache_path(doi)
    if path.exists():
        with open(path, encoding="utf-8") as fh:
            return json.load(fh).get("message")

    url = API + urllib.parse.quote(doi, safe="")
    # El 'polite pool' de Crossref pide identificarse con un correo de contacto.
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


# --------------------------------------------------------------------------- #
# Emparejamiento
# --------------------------------------------------------------------------- #

def emparejar(firmas_uft: list[str], autores_crossref: list[dict]) -> list[dict]:
    """Asocia firmas institucionales con autores de Crossref dentro de UNA publicación.

    Sólo asigna cuando la coincidencia es inequívoca: exactamente un autor de
    Crossref comparte apellido e inicial con la firma. Si coinciden varios, el
    caso se marca ambiguo y no se asigna nada — dos hermanos o dos homónimos en
    la misma publicación no pueden distinguirse por el nombre.
    """
    resultados = []
    for firma in firmas_uft:
        ap, ini = clave_firma(firma)
        if not ap:
            continue
        candidatos = [a for a in autores_crossref
                      if clave_crossref(a) == (ap, ini)]
        if not candidatos:
            # Reintento por apellido, SÓLO cuando Crossref no declara nombre de
            # pila. Aceptar cualquier apellido coincidente asignaría el ORCID de
            # 'Diaz, Marcela' a la firma 'Diaz F.': iniciales que se contradicen
            # son evidencia de que son personas distintas, no de coincidencia
            # parcial.
            candidatos = [a for a in autores_crossref
                          if clave_crossref(a) == (ap, "")]
            preciso = False
        else:
            preciso = True

        if len(candidatos) == 1 and candidatos[0].get("ORCID"):
            orcid = candidatos[0]["ORCID"].rstrip("/").split("/")[-1]
            resultados.append({
                "firma": firma, "orcid": orcid,
                "match": "apellido+inicial" if preciso else "solo_apellido",
                "ambiguo": False,
            })
        elif len(candidatos) > 1:
            resultados.append({"firma": firma, "orcid": None,
                               "match": "multiple", "ambiguo": True})
    return resultados


def candidatos_de_identidad(asignaciones: pd.DataFrame) -> pd.DataFrame:
    """Firmas distintas que comparten ORCID: candidatas a ser la misma persona.

    NO se fusionan (decisión D-08). Compartir ORCID es evidencia fuerte, pero la
    asignación firma->ORCID es a su vez una hipótesis basada en apellido e
    inicial: encadenar dos hipótesis no produce un hecho. Se emite como cola de
    revisión para que una persona confirme.

    El valor está en lo que la agrupación por apellido NO encuentra: 'Gubbins V.'
    y 'Foxley V.G.' no comparten apellido, pero sí ORCID.
    """
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audit"))

    filas = []
    for orcid, grp in asignaciones.groupby("orcid"):
        firmas = sorted(grp["nombre_en_fuente"])
        if len(firmas) < 2:
            continue
        claves = {c.surname_key(f) for f in firmas}
        filas.append({
            "tipo": "V2-01_firmas_con_orcid_compartido",
            "severidad": "alta",
            "orcid": orcid,
            "firmas": " | ".join(firmas),
            "n_firmas": len(firmas),
            # Si las claves de apellido difieren, la cola P-03 nunca las habría
            # agrupado: es un hallazgo que sólo aporta el identificador.
            "hallazgo_nuevo": len(claves) > 1,
            "confianza_minima": grp["confianza"].min(),
            "consecuencia": "firmas distintas comparten identificador persistente",
            "resolucion": "PENDIENTE_CONFIRMACION_HUMANA",
        })
    return pd.DataFrame(filas)


def consolidar(hallazgos: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Agrega por firma. Un solo ORCID consistente se asigna; varios, se encolan."""
    asignaciones, conflictos = [], []
    for firma, grp in hallazgos.groupby("firma"):
        orcids = sorted({o for o in grp["orcid"].dropna() if o})
        n_apoyo = int(grp["orcid"].notna().sum())
        solo_apellido = bool((grp["match"] == "solo_apellido").all()) if n_apoyo else False

        if len(orcids) == 1:
            asignaciones.append({
                "nombre_en_fuente": firma,
                "orcid": orcids[0],
                "publicaciones_de_respaldo": n_apoyo,
                # Un único respaldo por apellido suelto es la evidencia más
                # débil que el sistema acepta; se marca como tal.
                "confianza": "media" if (n_apoyo == 1 or solo_apellido) else "alta",
                "fuente": "Crossref",
            })
        elif len(orcids) > 1:
            conflictos.append({
                "tipo": "V2-01_orcid_en_conflicto", "severidad": "alta",
                "nombre_en_fuente": firma, "detalle": "|".join(orcids),
                "consecuencia": "la firma aparece con más de un ORCID entre sus publicaciones",
                "resolucion": "NO_RESOLVER_AUTOMATICAMENTE",
            })
        if (grp["ambiguo"]).any():
            conflictos.append({
                "tipo": "V2-01_homonimia_en_publicacion", "severidad": "media",
                "nombre_en_fuente": firma, "detalle": "",
                "consecuencia": "varios autores de Crossref comparten apellido e inicial en la misma publicación",
                "resolucion": "PENDIENTE_REVISION_HUMANA",
            })
    return pd.DataFrame(asignaciones), pd.DataFrame(conflictos)


# --------------------------------------------------------------------------- #
# Verificación offline de la lógica
# --------------------------------------------------------------------------- #

FIXTURES = [
    # (firmas institucionales, autores Crossref, ORCID esperado por firma)
    (["Mujika I."],
     [{"family": "Mujika", "given": "Iñigo", "ORCID": "https://orcid.org/0000-0002-1milk"},
      {"family": "Dergaa", "given": "Ismail"}],
     {"Mujika I.": "0000-0002-1milk"}),
    # Acentos y guiones no deben impedir la coincidencia
    (["Castro-Sepúlveda M."],
     [{"family": "Castro Sepulveda", "given": "Mauricio",
       "ORCID": "http://orcid.org/0000-0003-2222"}],
     {"Castro-Sepúlveda M.": "0000-0003-2222"}),
    # Homonimia dentro de la publicación: no se asigna nada
    (["Garcia J."],
     [{"family": "Garcia", "given": "Juan", "ORCID": "https://orcid.org/0000-1"},
      {"family": "Garcia", "given": "Jose", "ORCID": "https://orcid.org/0000-2"}],
     {}),
    # Inicial que se contradice: NO se asigna, aunque el apellido coincida
    (["Diaz F."],
     [{"family": "Diaz", "given": "Marcela", "ORCID": "https://orcid.org/0000-3"}],
     {}),
    # Crossref sin nombre de pila: se acepta por apellido, con confianza menor
    (["Simón L."],
     [{"family": "Simon", "ORCID": "https://orcid.org/0000-4"}],
     {"Simón L.": "0000-4"}),
    # Autor sin ORCID declarado: no se inventa
    (["Ferre A."],
     [{"family": "Ferre", "given": "Andres"}],
     {}),
]


def autotest() -> int:
    fallos = 0
    for i, (firmas, autores, esperado) in enumerate(FIXTURES, 1):
        got = {r["firma"]: r["orcid"] for r in emparejar(firmas, autores) if r["orcid"]}
        ok = got == esperado
        print(f"  fixture {i}: {'OK  ' if ok else 'FALLA'} {got} {'' if ok else f'!= {esperado}'}")
        fallos += 0 if ok else 1

    # Consolidación: un mismo ORCID en dos publicaciones = confianza alta;
    # dos ORCID distintos = conflicto sin asignar.
    df = pd.DataFrame([
        {"firma": "A.", "orcid": "0000-1", "match": "apellido+inicial", "ambiguo": False},
        {"firma": "A.", "orcid": "0000-1", "match": "apellido+inicial", "ambiguo": False},
        {"firma": "B.", "orcid": "0000-2", "match": "apellido+inicial", "ambiguo": False},
        {"firma": "B.", "orcid": "0000-3", "match": "apellido+inicial", "ambiguo": False},
    ])
    asig, conf = consolidar(df)
    ok_a = len(asig) == 1 and asig.iloc[0]["nombre_en_fuente"] == "A." \
        and asig.iloc[0]["confianza"] == "alta"
    ok_c = len(conf) == 1 and conf.iloc[0]["tipo"] == "V2-01_orcid_en_conflicto"
    print(f"  consolidación asignación: {'OK' if ok_a else 'FALLA'}")
    print(f"  consolidación conflicto : {'OK' if ok_c else 'FALLA'}")
    fallos += (0 if ok_a else 1) + (0 if ok_c else 1)

    print(f"\n{'TODOS LOS CASOS OK' if not fallos else f'{fallos} CASO(S) FALLANDO'}")
    return fallos


# --------------------------------------------------------------------------- #

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--test", action="store_true", help="verifica la lógica sin red")
    ap.add_argument("--limit", type=int, default=None, help="máximo de DOI a consultar")
    ap.add_argument("--mailto", default=None, help="correo para el polite pool de Crossref")
    args = ap.parse_args()

    c.banner("ENRIQUECIMIENTO DE ORCID DESDE CROSSREF (V2-01)")

    if args.test:
        return autotest()

    mailto = args.mailto or CFG.get("mailto")
    if not mailto:
        sys.exit("Falta un correo de contacto. Use --mailto o declare "
                 "enriquecimiento_externo.orcid.mailto en config/matching_rules.yml")

    # data/interim/ no se versiona: se regenera con la auditoría. Sin ese paso
    # previo este script no tiene sobre qué trabajar, y conviene decirlo con
    # claridad en vez de dejar escapar un FileNotFoundError.
    universo = c.INTERIM / "publications_universe.csv"
    if not universo.exists():
        sys.exit(
            "Falta data/interim/publications_universe.csv.\n"
            "Ese archivo se genera con la auditoría y no se versiona.\n"
            "Ejecute primero:  python3 src/audit/run_all.py"
        )

    uni = pd.read_csv(universo, dtype=str)
    log = pd.read_csv(c.INTERNAL / "matching_log.csv", dtype=str)
    firmas_por_eid = log.groupby("eid")["nombre_en_fuente"].apply(lambda s: sorted(set(s))).to_dict()

    con_doi = uni[uni["doi"].notna()]
    if args.limit:
        con_doi = con_doi.head(args.limit)

    print(f"  publicaciones con DOI: {len(con_doi)} de {len(uni)} "
          f"({100 * len(con_doi) / len(uni):.1f} %)")

    hallazgos, sin_registro, errores = [], 0, 0
    for i, (_, r) in enumerate(con_doi.iterrows(), 1):
        if i % 100 == 0:
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
        if not msg:
            sin_registro += 1
            continue
        hallazgos += emparejar(firmas_por_eid.get(r["eid"], []), msg.get("author", []))

    if not hallazgos:
        print("\n  Sin hallazgos. No se escribe ningún archivo.")
        return 1

    df = pd.DataFrame(hallazgos)
    asignaciones, conflictos = consolidar(df)

    ENRICHED.mkdir(parents=True, exist_ok=True)
    asignaciones.to_csv(ENRICHED / "authors_orcid.csv", index=False, encoding="utf-8")
    if len(conflictos):
        c.write_internal(conflictos, "orcid_conflicts.csv")

    candidatos = candidatos_de_identidad(asignaciones)
    if len(candidatos):
        c.write_internal(candidatos, "identity_candidates.csv")

    total_firmas = log["nombre_en_fuente"].nunique()
    print(f"\n  DOI sin registro en Crossref : {sin_registro}")
    print(f"  errores de red               : {errores}")
    print(f"  firmas con ORCID asignado    : {len(asignaciones)} de {total_firmas} "
          f"({100 * len(asignaciones) / total_firmas:.1f} %)")
    if len(asignaciones):
        print(f"    confianza alta : {int((asignaciones['confianza'] == 'alta').sum())}")
        print(f"    confianza media: {int((asignaciones['confianza'] == 'media').sum())}")
    print(f"  conflictos encolados         : {len(conflictos)}")
    if len(candidatos):
        nuevos = int(candidatos["hallazgo_nuevo"].sum())
        colapsables = int((candidatos["n_firmas"] - 1).sum())
        print(f"  firmas que comparten ORCID   : {len(candidatos)} grupos "
              f"({colapsables} firmas colapsables)")
        print(f"    de ellos, hallazgos que el apellido no detectaba: {nuevos}")
    print("\n  OK · data/enriched/authors_orcid.csv  (recuerde versionarlo)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
