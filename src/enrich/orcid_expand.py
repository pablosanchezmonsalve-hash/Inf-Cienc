"""Ampliación de cobertura de ORCID preguntándole al registro, no al editor.

POR QUÉ EXISTE
    `orcid_crossref.py` sólo encuentra un ORCID cuando el editor lo transmitió
    a Crossref al publicar. Eso depende de que alguien lo escribiera en el
    formulario de envío, y muchas veces no ocurre: hoy cubre 174 de 589 formas
    de firma.

    El registro de ORCID sabe más. Un titular puede haber incorporado una obra
    a su registro por vías que Crossref no refleja —sincronización con Scopus,
    con DataCite, o a mano—. Preguntar «¿quién declara este DOI?» encuentra
    asignaciones que la vía del editor no ve.

QUÉ HACE
    Por cada DOI del universo consulta `expanded-search` con `doi-self`, que
    devuelve los titulares que declaran esa obra con su nombre. Después empareja
    esos nombres con las firmas UFT detectadas en ESA misma publicación.

QUÉ NO HACE
    No inventa cobertura. Sólo asigna cuando exactamente un titular de los
    encontrados comparte apellido e inicial con la firma, que es la MISMA regla
    de `orcid_crossref.py` —se importa de allí, no se reescribe, para que no
    puedan divergir—.

    No resuelve desacuerdos. Si Crossref y ORCID atribuyen ORCID distintos a la
    misma firma, el caso se encola sin tocar la asignación vigente: uno de los
    dos está equivocado y decidir cuál no es automatizable.

UNA DIFERENCIA QUE HAY QUE TENER PRESENTE
    Crossref entrega la lista COMPLETA de autores de la publicación, así que
    detectar ambigüedad —dos homónimos firmando el mismo artículo— es fiable.
    Esta búsqueda sólo devuelve a quienes TIENEN registro en ORCID y declaran
    la obra. Si de dos homónimos sólo uno tiene ORCID, aquí parecerá
    inequívoco y allí no. Por eso las asignaciones nuevas se cruzan además
    contra las de Crossref, y por eso su confianza nunca sube por encima de la
    que da el número de publicaciones que las respaldan.

USO
    python3 src/enrich/orcid_expand.py --test      # lógica, sin red
    python3 src/enrich/orcid_expand.py --limit 25  # prueba corta
    python3 src/enrich/orcid_expand.py             # el corpus entero

Salidas:
    data/enriched/authors_orcid.csv        asignaciones, fusionadas (SE VERSIONA)
    internal/orcid_ampliacion_log.csv      traza de cada hallazgo (capa interna)
    internal/orcid_desacuerdos.csv         Crossref vs. ORCID (capa interna)
    data/cache/orcid_search/*.json         respuestas cacheadas (no versionadas)
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
    # La consola de Windows usa cp1252 por defecto: revienta cualquier print()
    # con caracteres como "→"/"✗"/"⚠". Mismo patrón que src/enrich/orcid_openalex.py.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audit"))
import common as c  # noqa: E402

# La regla de emparejamiento y la de credenciales se IMPORTAN. Reescribirlas
# aquí crearía dos reglas que se documentan como una sola y que empezarían a
# divergir en cuanto alguien corrigiese sólo una.
from orcid_crossref import clave_firma, emparejar  # noqa: E402
from orcid_api import credenciales  # noqa: E402

CACHE = c.ROOT / "data" / "cache" / "orcid_search"
ENRICHED = c.ROOT / "data" / "enriched"
API = "https://pub.orcid.org/v3.0/expanded-search"

FUENTE = "ORCID (declarado por el titular)"


# --------------------------------------------------------------------------- #
# Consulta
# --------------------------------------------------------------------------- #

def _cache_path(doi: str) -> Path:
    return CACHE / (re.sub(r"[^a-zA-Z0-9]+", "_", doi)[:120] + ".json")


def buscar_por_doi(doi: str, token: str, pausa: float = 0.12) -> list[dict] | None:
    """Titulares de ORCID que declaran este DOI entre sus obras.

    Devuelve la lista en la forma que espera `emparejar()`: los mismos campos
    que usa Crossref, para poder reutilizar la función sin adaptadores.
    None si la consulta falla de forma recuperable.
    """
    path = _cache_path(doi)
    if path.exists():
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)

    # doi-self busca el DOI entre las obras DEL TITULAR. `doi` a secas también
    # acierta en obras donde sólo se le cita, que no es lo que se pregunta.
    q = f'doi-self:"{doi}"'
    url = f"{API}/?q={urllib.parse.quote(q)}&rows=100"
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "InformeCienciometricoInstitucional/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            data = {"expanded-result": []}
        else:
            raise

    autores = extraer(data)
    CACHE.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(autores, fh, ensure_ascii=False)
    time.sleep(pausa)
    return autores


def extraer(data: dict) -> list[dict]:
    """Normaliza la respuesta de expanded-search a la forma de Crossref.

    `expanded-result` puede venir a null cuando no hay coincidencias; eso no es
    un error, es cero resultados, y confundirlo con un fallo haría reintentar
    consultas que ya respondieron bien.
    """
    filas = (data or {}).get("expanded-result") or []
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


# --------------------------------------------------------------------------- #
# Consolidación
# --------------------------------------------------------------------------- #

def consolidar(hallazgos: pd.DataFrame, vigentes: pd.DataFrame
               ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Convierte hallazgos por publicación en asignaciones por firma.

    Una firma se queda con el ORCID que más publicaciones respaldan. Si empatan
    dos, no se decide: es exactamente el caso que no se puede resolver mirando
    los nombres.
    """
    ya = dict(zip(vigentes["nombre_en_fuente"], vigentes["orcid"])) if len(vigentes) else {}

    nuevas, desacuerdos = [], []
    for firma, g in hallazgos.groupby("firma"):
        conteo = g.groupby("orcid")["eid"].nunique().sort_values(ascending=False)
        if len(conteo) > 1 and conteo.iloc[0] == conteo.iloc[1]:
            desacuerdos.append({
                "nombre_en_fuente": firma, "orcid": " | ".join(conteo.index),
                "tipo": "V2-02_orcid_empatados_en_el_registro",
                "detalle": f"{len(conteo)} ORCID distintos declaran obras de esta firma, "
                           f"con {int(conteo.iloc[0])} publicaciones cada uno",
            })
            continue

        orcid, respaldo = conteo.index[0], int(conteo.iloc[0])

        # Desacuerdo con lo que Crossref ya había dicho. No se toca la
        # asignación vigente: que dos fuentes se contradigan es un hallazgo,
        # no un empate que gane la última en llegar.
        if firma in ya and ya[firma] != orcid:
            desacuerdos.append({
                "nombre_en_fuente": firma, "orcid": f"{ya[firma]} (Crossref) | {orcid} (ORCID)",
                "tipo": "V2-03_desacuerdo_entre_fuentes",
                "detalle": "Crossref y el registro de ORCID atribuyen identificadores "
                           "distintos a la misma firma",
            })
            continue

        if firma in ya:
            continue   # coinciden: nada nuevo que añadir

        nuevas.append({
            "nombre_en_fuente": firma,
            "orcid": orcid,
            "publicaciones_de_respaldo": respaldo,
            "confianza": "alta" if respaldo >= 2 else "media",
            "fuente": FUENTE,
        })

    cols_d = ["nombre_en_fuente", "orcid", "tipo", "detalle"]
    return (pd.DataFrame(nuevas, columns=["nombre_en_fuente", "orcid",
                                          "publicaciones_de_respaldo", "confianza", "fuente"]),
            pd.DataFrame(desacuerdos, columns=cols_d))


# --------------------------------------------------------------------------- #
# Autoprueba sin red
# --------------------------------------------------------------------------- #

def autotest() -> int:
    casos = []

    # 1. Una respuesta normal se normaliza a la forma de Crossref.
    data = {"expanded-result": [
        {"orcid-id": "0000-0002-1111-2222", "given-names": "María",
         "family-names": "Orellana-Donoso"}]}
    r = extraer(data)
    casos.append(("normaliza expanded-search",
                  r == [{"family": "Orellana-Donoso", "given": "María",
                         "ORCID": "0000-0002-1111-2222"}], r))

    # 2. `expanded-result: null` es cero resultados, no un fallo.
    casos.append(("expanded-result nulo = 0 resultados",
                  extraer({"expanded-result": None}) == [], None))
    casos.append(("respuesta vacía = 0 resultados", extraer({}) == [], None))

    # 3. El emparejamiento importado se comporta igual que en Crossref.
    autores = extraer({"expanded-result": [
        {"orcid-id": "0000-0002-1111-2222", "given-names": "María",
         "family-names": "Orellana-Donoso"}]})
    m = emparejar(["Orellana-Donoso M."], autores)
    casos.append(("empareja apellido+inicial",
                  len(m) == 1 and m[0]["orcid"] == "0000-0002-1111-2222", m))

    # 4. Iniciales que se contradicen NO son coincidencia parcial.
    m = emparejar(["Orellana-Donoso J."], autores)
    casos.append(("inicial distinta no asigna",
                  all(x.get("orcid") is None for x in m), m))

    # 5. Dos homónimos en la misma publicación: no se asigna nada.
    dos = extraer({"expanded-result": [
        {"orcid-id": "0000-0001-1111-1111", "given-names": "María", "family-names": "Díaz"},
        {"orcid-id": "0000-0002-2222-2222", "given-names": "Manuel", "family-names": "Díaz"}]})
    m = emparejar(["Díaz M."], dos)
    casos.append(("homónimos en la misma publicación no asignan",
                  all(x.get("orcid") is None for x in m), m))

    # 6. Consolidación: gana el ORCID con más publicaciones de respaldo.
    h = pd.DataFrame([
        {"firma": "Ferre A.", "orcid": "0000-A", "eid": "e1"},
        {"firma": "Ferre A.", "orcid": "0000-A", "eid": "e2"},
        {"firma": "Ferre A.", "orcid": "0000-B", "eid": "e3"}])
    nuevas, des = consolidar(h, pd.DataFrame(columns=["nombre_en_fuente", "orcid"]))
    casos.append(("gana el mejor respaldado",
                  len(nuevas) == 1 and nuevas.orcid.iloc[0] == "0000-A"
                  and int(nuevas.publicaciones_de_respaldo.iloc[0]) == 2, nuevas.to_dict("records")))
    casos.append(("respaldo 2 => confianza alta",
                  nuevas.confianza.iloc[0] == "alta", None))

    # 7. Empate: no se decide.
    h = pd.DataFrame([
        {"firma": "Díaz F.", "orcid": "0000-A", "eid": "e1"},
        {"firma": "Díaz F.", "orcid": "0000-B", "eid": "e2"}])
    nuevas, des = consolidar(h, pd.DataFrame(columns=["nombre_en_fuente", "orcid"]))
    casos.append(("empate no asigna",
                  len(nuevas) == 0 and len(des) == 1
                  and des.tipo.iloc[0] == "V2-02_orcid_empatados_en_el_registro", des.to_dict("records")))

    # 8. Desacuerdo con Crossref: se encola y NO se pisa lo vigente.
    h = pd.DataFrame([{"firma": "Rojas D.", "orcid": "0000-NUEVO", "eid": "e1"}])
    vig = pd.DataFrame([{"nombre_en_fuente": "Rojas D.", "orcid": "0000-VIEJO"}])
    nuevas, des = consolidar(h, vig)
    casos.append(("desacuerdo con Crossref se encola",
                  len(nuevas) == 0 and len(des) == 1
                  and des.tipo.iloc[0] == "V2-03_desacuerdo_entre_fuentes", des.to_dict("records")))

    # 9. Coincidencia con Crossref: no duplica.
    vig = pd.DataFrame([{"nombre_en_fuente": "Rojas D.", "orcid": "0000-NUEVO"}])
    nuevas, des = consolidar(h, vig)
    casos.append(("coincidencia no duplica", len(nuevas) == 0 and len(des) == 0, None))

    # 10. Una firma sin apellido utilizable no revienta el emparejamiento.
    casos.append(("firma vacía no revienta", emparejar([""], autores) == [], None))
    casos.append(("clave_firma vacía", clave_firma("") == ("", ""), None))

    ok = True
    for nombre, paso, obs in casos:
        print(f"  {'OK  ' if paso else 'FALLA'} {nombre}" + (f"   {obs}" if not paso else ""))
        ok &= paso
    print("\n" + ("TODOS LOS CASOS OK" if ok else "HAY CASOS FALLANDO"))
    return 0 if ok else 1


# --------------------------------------------------------------------------- #

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--test", action="store_true", help="verifica la lógica sin red")
    ap.add_argument("--limit", type=int, default=None, help="máximo de DOI a consultar")
    args = ap.parse_args()

    c.banner("AMPLIACIÓN DE COBERTURA DE ORCID DESDE EL REGISTRO")
    if args.test:
        return autotest()

    universo = c.INTERIM / "publications_universe.csv"
    if not universo.exists():
        sys.exit("Falta data/interim/publications_universe.csv. "
                 "Ejecute:  python3 src/audit/run_all.py")

    token = credenciales()

    uni = pd.read_csv(universo, dtype=str)
    log = pd.read_csv(c.INTERNAL / "matching_log.csv", dtype=str)
    firmas_por_eid = log.groupby("eid")["nombre_en_fuente"].apply(list).to_dict()

    path_vig = ENRICHED / "authors_orcid.csv"
    vigentes = (pd.read_csv(path_vig, dtype=str) if path_vig.exists()
                else pd.DataFrame(columns=["nombre_en_fuente", "orcid",
                                           "publicaciones_de_respaldo",
                                           "confianza", "fuente"]))

    con_doi = uni[uni["doi"].notna() & (uni["doi"].astype(str).str.strip() != "")]
    filas = con_doi.head(args.limit) if args.limit else con_doi
    print(f"  publicaciones con DOI a consultar: {len(filas)} de {len(uni)}")
    print(f"  asignaciones vigentes            : {len(vigentes)}")

    hallazgos, errores, con_resultado = [], 0, 0
    for i, (_, r) in enumerate(filas.iterrows(), 1):
        if i % 50 == 0:
            print(f"    {i}/{len(filas)}…  hallazgos: {len(hallazgos)}")
        doi = str(r["doi"]).strip()
        firmas = firmas_por_eid.get(r["eid"], [])
        if not firmas:
            continue
        try:
            autores = buscar_por_doi(doi, token)
        except Exception as e:
            errores += 1
            if errores <= 3:
                print(f"    aviso · {doi}: {type(e).__name__} {e}")
            if errores > 25:
                sys.exit("ABORTADO: demasiados errores. Verifique el token y la red.")
            continue
        if not autores:
            continue
        con_resultado += 1
        for m in emparejar(firmas, autores):
            if m.get("orcid"):
                hallazgos.append({"firma": m["firma"], "orcid": m["orcid"],
                                  "eid": r["eid"], "doi": doi, "match": m["match"]})

    print(f"\n  DOI con algún titular en ORCID   : {con_resultado}")
    print(f"  errores de red                   : {errores}")

    if not hallazgos:
        print("\n  Sin hallazgos. No se escribe ningún archivo.")
        return 1

    hdf = pd.DataFrame(hallazgos)
    c.write_internal(hdf.assign(fecha_consulta=date.today().isoformat()),
                     "orcid_ampliacion_log.csv")

    nuevas, desacuerdos = consolidar(hdf, vigentes)
    if len(desacuerdos):
        c.write_internal(desacuerdos.assign(
            severidad="alta", resolucion="PENDIENTE_REVISION_HUMANA"),
            "orcid_desacuerdos.csv")

    if len(nuevas):
        salida = pd.concat([vigentes, nuevas], ignore_index=True)
        salida = salida.sort_values("nombre_en_fuente", kind="stable")
        salida.to_csv(path_vig, index=False, encoding="utf-8")

    total_firmas = log["nombre_en_fuente"].nunique()
    antes, ahora = len(vigentes), len(vigentes) + len(nuevas)
    print(f"\n  asignaciones nuevas              : {len(nuevas)}")
    print(f"  desacuerdos encolados            : {len(desacuerdos)}")
    print(f"\n  cobertura antes                  : {antes}/{total_firmas} "
          f"({100*antes/total_firmas:.1f} %)")
    print(f"  cobertura ahora                  : {ahora}/{total_firmas} "
          f"({100*ahora/total_firmas:.1f} %)")
    print("\n  OK · data/enriched/authors_orcid.csv  (recuerde versionarlo)")
    print("       Reejecute src/enrich/orcid_api.py para verificar las nuevas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
