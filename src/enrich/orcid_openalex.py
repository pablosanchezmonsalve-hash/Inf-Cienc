"""Enriquecimiento y contraste desde OpenAlex (V2-19).

QUÉ APORTA, Y QUÉ NO — LA PARTE QUE HAY QUE LEER ANTES DEL CÓDIGO
    `docs/FUENTES_Y_APIS.md` presentaba a OpenAlex como «una segunda fuente
    independiente de ORCID». **Esa afirmación era falsa y este archivo la
    corrige.** OpenAlex ingiere Crossref entre sus fuentes: un ORCID que
    OpenAlex devuelve puede ser literalmente el que Crossref depositó. Que las
    dos coincidan no confirma nada que no supiéramos, porque no son
    independientes — es la misma evidencia contada dos veces.

    Este proyecto ya distingue «verificado» —dos fuentes independientes— de
    «declarado por el titular» —una sola—, y publica esa diferencia en cada
    ficha de autor. Contar una coincidencia con OpenAlex como verificación
    inflaría el recuento de comprobaciones independientes con comprobaciones
    circulares, que es exactamente lo que `03_authors.py` evita para las
    asignaciones que salen del propio registro de ORCID.

    Lo que OpenAlex SÍ aporta, sin discusión:

    1. **ORCID donde no había ninguno.** 349 formas de firma no tienen
       identificador por ninguna de las tres vías actuales. Cualquiera que
       OpenAlex traiga es cobertura nueva, venga de donde venga.
    2. **Contraste institucional por ROR.** Cada autoría de OpenAlex trae la
       institución desambiguada con su identificador ROR. Las publicaciones que
       este proyecto atribuye a la institución y OpenAlex no, son un hallazgo:
       o su desambiguación falló, o el patrón blando detectó de más — y hay 16
       falsos positivos verificados en el historial del proyecto.

       La dirección contraria —producción que OpenAlex atribuye y nosotros no—
       **no es alcanzable por esta vía** y conviene no fingir que sí: sólo se
       consultan los DOI del universo, y el universo ya está filtrado por la
       institución. Encontrar lo que falta exige preguntar por institución, que
       es otra consulta. Anotado como `V2-26`.

QUÉ NO HACE
    - No consolida identidades (`D-08`). Los desacuerdos se encolan.
    - No reescribe asignaciones vigentes: sólo añade donde no había.
    - No usa el `author.id` de OpenAlex para fusionar firmas. Es una
      desambiguación por agrupamiento y fusionar por ella sería justo la
      «consolidación automática por similitud» que `V2_BACKLOG` §6 descarta.
    - No toca el patrón de detección institucional: reporta las diferencias.

DEPENDENCIA DECLARADA CON V2-20
    El contraste institucional necesita el ROR de la institución, que hoy es
    `null` en `config/institution.yml`. Sin él, esa mitad no corre y se dice;
    no se sustituye por una comparación de nombres, que es lo que la regla
    `I-05` prohíbe.

EL CONTRATO DE LA API NO ESTÁ VERIFICADO DESDE ESTE REPOSITORIO
    La política de red del entorno de desarrollo bloquea `api.openalex.org`,
    igual que `api.crossref.org` y `pub.orcid.org`. Por eso el conector
    comprueba la forma de la respuesta antes de usarla y, si no la reconoce,
    guarda la cruda y se detiene diciendo dónde está, en vez de adivinar.
    La lógica de extracción, emparejamiento y contraste sí está verificada
    (`--test`), y el emparejamiento NO se reescribe aquí: se importa de
    `orcid_crossref.py` para que no puedan divergir.

USO
    python3 src/enrich/orcid_openalex.py --test      lógica, sin red
    python3 src/enrich/orcid_openalex.py --limit 25  prueba corta
    python3 src/enrich/orcid_openalex.py             el corpus entero

Salidas
    data/enriched/authors_orcid.csv        asignaciones nuevas (SE VERSIONA)
    internal/openalex_log.csv              traza de cada hallazgo
    internal/openalex_desacuerdos.csv      un ORCID distinto del vigente
    internal/openalex_deteccion.csv        contraste institucional por ROR
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
    # La consola de Windows usa cp1252 por defecto, que no tiene "→" ni "─":
    # revienta el print final después de que todo el trabajo ya se guardó.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audit"))
import common as c  # noqa: E402

# El emparejamiento se IMPORTA. Reescribirlo aquí crearía dos reglas para una
# misma pregunta —«¿qué autor de esta publicación es esta firma?»— y bastaría
# tocar una para que las asignaciones dejaran de ser comparables entre sí.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from orcid_crossref import emparejar  # noqa: E402

CACHE = c.ROOT / "data" / "cache" / "openalex"
ENRICHED = c.ROOT / "data" / "enriched"
API = "https://api.openalex.org/works/"
CFG = c.MATCHING["enriquecimiento_externo"]["orcid"]
FUENTE = "OpenAlex"


class ContratoDesconocido(Exception):
    """La respuesta no tiene la forma esperada. No se adivina."""


# ────────────────────────────────────────────────── extracción de la respuesta

def extraer(data: dict) -> dict:
    """Normaliza una obra de OpenAlex a lo que este proyecto necesita.

    Los autores salen con las claves de Crossref —`family`, `given`, `ORCID`—
    porque `emparejar` está escrito contra esa forma y se reutiliza tal cual.

    OpenAlex da el nombre completo en `display_name`, no partido. Se parte por
    el ÚLTIMO token como apellido, que es la convención de `display_name`
    («Marcela Díaz»). Es una heurística y por eso `emparejar` sigue exigiendo
    coincidencia de apellido e inicial: un apellido mal partido no coincide y
    la asignación no se hace, que es el fallo correcto.
    """
    if not isinstance(data, dict) or "authorships" not in data:
        raise ContratoDesconocido("la obra no trae 'authorships'")

    autores, rors = [], set()
    for a in data.get("authorships") or []:
        au = (a or {}).get("author") or {}
        nombre = (au.get("display_name") or "").strip()
        orcid = (au.get("orcid") or "").strip()
        partes = nombre.split()
        autores.append({
            "family": partes[-1] if partes else "",
            "given": " ".join(partes[:-1]) if len(partes) > 1 else "",
            # `emparejar` espera la forma de Crossref: URL o nada.
            "ORCID": orcid or None,
        })
        for inst in (a.get("institutions") or []):
            ror = ((inst or {}).get("ror") or "").strip()
            if ror:
                rors.add(ror.rstrip("/").split("/")[-1])

    return {"autores": autores, "rors": sorted(rors),
            "citas": data.get("cited_by_count")}


# ─────────────────────────────────────────────────────────────────────── red

def _cache_path(doi: str) -> Path:
    return CACHE / (re.sub(r"[^a-zA-Z0-9]+", "_", doi)[:120] + ".json")


def consultar(doi: str, mailto: str, pausa: float = 0.12) -> dict | None:
    """Una obra por DOI. Cachea: reejecutar no vuelve a golpear la API.

    Un 404 no es un error: significa que OpenAlex no tiene ese DOI, que es un
    resultado. Confundirlo con un fallo de red haría reintentar algo que no va
    a cambiar.
    """
    path = _cache_path(doi)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8")) or None

    url = API + urllib.parse.quote(f"https://doi.org/{doi}", safe=":/")
    req = urllib.request.Request(url + f"?mailto={urllib.parse.quote(mailto)}",
                                 headers={"Accept": "application/json",
                                          "User-Agent": f"InformeCienciometrico/1.0 (mailto:{mailto})"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            data = {}
        else:
            raise
    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    time.sleep(pausa)
    return data or None


# ───────────────────────────────────────────────────────────────── contraste

def ror_institucional() -> str | None:
    """El ROR de la institución, si V2-20 ya se ejecutó.

    Se busca primero en `config/institution.yml`, que es donde una persona lo
    pega, y sólo después en el artefacto del conector. Ese orden importa: el
    archivo de configuración es la declaración, el artefacto es el hallazgo.
    """
    declarado = (c.load_config("institution.yml")["institucion"].get("ror_id") or "")
    if declarado:
        return declarado.rstrip("/").split("/")[-1]
    ficha = ENRICHED / "ror_institucion.json"
    if ficha.exists():
        rid = json.loads(ficha.read_text(encoding="utf-8")).get("ror_id") or ""
        return rid.rstrip("/").split("/")[-1] or None
    return None


def contraste_deteccion(eid: str, rors: list[str], ror_uft: str) -> dict | None:
    """Publicaciones que este proyecto atribuye a la institución y OpenAlex no.

    UNA SOLA DIRECCIÓN, Y CONVIENE SABER POR QUÉ
        La dirección contraria —«OpenAlex la atribuye y nosotros no»— sería la
        interesante: producción institucional sin contar. **Pero es inalcanzable
        por esta vía**, y decirlo importa más que dejar el código como si
        pudiera encontrarla.

        Este conector consulta los DOI del universo, y el universo se construye
        filtrando los exports por la institución: toda publicación que se
        consulta ES una que ya detectamos. Encontrar las que faltan exige
        preguntar a OpenAlex *por institución* —`filter=institutions.ror:…`— y
        comparar el resultado con el universo, que es otra consulta y otro
        problema. Queda anotado como `V2-26`.

    Lo que sí encuentra tiene dos lecturas y ninguna es automática: o la
    desambiguación de OpenAlex no reconoció la afiliación, o el patrón blando
    de este proyecto es demasiado laxo y detectó de más. La segunda importa:
    hay 16 falsos positivos verificados en el historial del proyecto.
    """
    if ror_uft in rors:
        return None
    return {
        "eid": eid,
        "detectada_por_el_proyecto": True,
        "atribuida_por_openalex": False,
        "rors_en_openalex": " | ".join(rors) or "(ninguno)",
        "tipo": "V2-19_openalex_no_atribuye_la_institucion",
        "severidad": "media",
        "consecuencia": "o OpenAlex no desambiguó la afiliación, o la detección "
                        "blanda de este proyecto es demasiado laxa",
        "resolucion": "PENDIENTE_REVISION_HUMANA",
    }


# ────────────────────────────────────────────────────────────────── autotest

OBRA = {
    "id": "https://openalex.org/W1",
    "cited_by_count": 7,
    "authorships": [
        {"author": {"id": "https://openalex.org/A1",
                    "display_name": "Marcela Díaz",
                    "orcid": "https://orcid.org/0000-0002-1825-0097"},
         "institutions": [{"ror": "https://ror.org/EJEMPLO", "display_name": "X"}]},
        {"author": {"id": "https://openalex.org/A2",
                    "display_name": "Juan Pérez", "orcid": None},
         "institutions": []},
    ],
}


def autotest() -> int:
    casos = []

    def caso(n, ok, obs=None):
        casos.append((n, ok, obs))

    d = extraer(OBRA)
    caso("parte el nombre en apellido e inicial",
         d["autores"][0]["family"] == "Díaz" and d["autores"][0]["given"] == "Marcela", d)
    caso("un autor sin ORCID no inventa uno", d["autores"][1]["ORCID"] is None, d)
    caso("recoge los ROR de las autorías", d["rors"] == ["EJEMPLO"], d)

    try:
        extraer({"id": "W2"})
        caso("obra sin 'authorships' se detecta", False, "no lanzó")
    except ContratoDesconocido:
        caso("obra sin 'authorships' se detecta", True)

    # El emparejamiento es el importado: se comprueba que la forma que produce
    # `extraer` sirve para alimentarlo, no la regla en sí (ya tiene su prueba).
    m = emparejar(["Díaz M."], d["autores"])
    caso("la forma extraída alimenta a `emparejar`",
         len(m) == 1 and m[0]["orcid"] == "0000-0002-1825-0097", m)

    caso("una firma sin autor equivalente no se asigna",
         emparejar(["Inexistente Z."], d["autores"]) == [], None)

    # Nombres compuestos: el apellido va al final en `display_name`, y un
    # apellido de dos palabras se parte mal. Debe FALLAR el emparejamiento, no
    # asignar de más: es el fallo correcto.
    compuesto = extraer({"authorships": [
        {"author": {"display_name": "Ana Arenas Massa",
                    "orcid": "https://orcid.org/0000-0003-3188-0189"},
         "institutions": []}]})
    caso("un apellido compuesto no produce una asignación errónea",
         emparejar(["Arenas-Massa A."], compuesto["autores"]) == [],
         emparejar(["Arenas-Massa A."], compuesto["autores"]))

    # Contraste institucional: sólo habla cuando OpenAlex no atribuye.
    caso("coincidir no genera hallazgo",
         contraste_deteccion("e1", ["UFT"], "UFT") is None)
    f = contraste_deteccion("e1", ["OTRA"], "UFT")
    caso("OpenAlex sin la institución es hallazgo",
         f and f["rors_en_openalex"] == "OTRA", f)
    f = contraste_deteccion("e2", [], "UFT")
    caso("una obra sin ninguna institución también es hallazgo",
         f and f["rors_en_openalex"] == "(ninguno)", f)
    caso("el hallazgo no se corrige solo",
         f["resolucion"] == "PENDIENTE_REVISION_HUMANA")

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

    c.banner("ENRIQUECIMIENTO Y CONTRASTE DESDE OPENALEX")
    if args.test:
        return autotest()

    universo = c.INTERIM / "publications_universe.csv"
    if not universo.exists():
        sys.exit("Falta data/interim/publications_universe.csv. "
                 "Ejecute:  python3 src/audit/run_all.py")
    mailto = CFG.get("mailto")
    if not mailto:
        sys.exit("Falta enriquecimiento_externo.orcid.mailto en config/matching_rules.yml")

    uni = pd.read_csv(universo, dtype=str)
    log = pd.read_csv(c.INTERNAL / "matching_log.csv", dtype=str)
    firmas_por_eid = log.groupby("eid")["nombre_en_fuente"].apply(list).to_dict()

    path_vig = ENRICHED / "authors_orcid.csv"
    vig = (pd.read_csv(path_vig, dtype=str) if path_vig.exists()
           else pd.DataFrame(columns=["nombre_en_fuente", "orcid",
                                      "publicaciones_de_respaldo", "confianza", "fuente"]))
    ya = dict(zip(vig["nombre_en_fuente"], vig["orcid"]))

    ror_uft = ror_institucional()
    if ror_uft:
        print(f"  ROR institucional: {ror_uft}  (el contraste de detección corre)")
    else:
        print("  ROR institucional: SIN DECLARAR — el contraste de detección NO corre.")
        print("    Ejecute antes:  python3 src/enrich/ror_institucion.py   (V2-20)")

    con_doi = uni[uni["doi"].notna() & (uni["doi"].astype(str).str.strip() != "")]
    filas = con_doi.head(args.limit) if args.limit else con_doi
    print(f"  publicaciones con DOI            : {len(filas)} de {len(uni)}")
    print(f"  asignaciones vigentes            : {len(vig)}")

    hallazgos, discrepancias, errores, sin_obra = [], [], 0, 0
    for i, (_, r) in enumerate(filas.iterrows(), 1):
        if i % 50 == 0:
            print(f"    {i}/{len(filas)}…  hallazgos: {len(hallazgos)}")
        doi = str(r["doi"]).strip()
        try:
            data = consultar(doi, mailto)
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
        if ror_uft:
            d = contraste_deteccion(r["eid"], obra["rors"], ror_uft)
            if d:
                discrepancias.append(d)

    print(f"\n  DOI que OpenAlex no tiene        : {sin_obra}")
    print(f"  errores de red                   : {errores}")

    hoy = date.today().isoformat()
    if discrepancias:
        c.write_internal(pd.DataFrame(discrepancias).assign(fecha_consulta=hoy),
                         "openalex_deteccion.csv")
        print(f"  OpenAlex no atribuye la institución: {len(discrepancias)} "
              "publicaciones que este proyecto sí le atribuye")

    if not hallazgos:
        print("\n  Sin asignaciones nuevas. No se escribe authors_orcid.csv.")
        return 0

    h = pd.DataFrame(hallazgos)
    c.write_internal(h.assign(fecha_consulta=hoy), "openalex_log.csv")

    nuevas, desac, concordantes = [], [], 0
    for firma, g in h.groupby("firma"):
        conteo = g.groupby("orcid")["eid"].nunique().sort_values(ascending=False)
        if len(conteo) > 1 and conteo.iloc[0] == conteo.iloc[1]:
            continue                       # empate: no se decide mirando nombres
        orcid, respaldo = conteo.index[0], int(conteo.iloc[0])
        if firma in ya:
            if ya[firma] != orcid:
                desac.append({
                    "nombre_en_fuente": firma, "orcid": f"{ya[firma]} | {orcid}",
                    "tipo": "V2-19_openalex_discrepa_de_la_asignacion_vigente",
                    "detalle": "la asignación vigente NO se ha modificado",
                    "severidad": "alta", "resolucion": "PENDIENTE_REVISION_HUMANA"})
            else:
                concordantes += 1
            continue
        nuevas.append({"nombre_en_fuente": firma, "orcid": orcid,
                       "publicaciones_de_respaldo": respaldo,
                       "confianza": "alta" if respaldo > 1 else "media",
                       "fuente": FUENTE})

    if desac:
        c.write_internal(pd.DataFrame(desac).assign(fecha_consulta=hoy),
                         "openalex_desacuerdos.csv")

    print(f"\n  asignaciones nuevas              : {len(nuevas)}")
    print(f"  concordantes con las vigentes    : {concordantes}")
    print("    NO cuentan como verificación: OpenAlex ingiere Crossref, así que")
    print("    coincidir con él no es coincidir con una fuente independiente.")
    print(f"  desacuerdos encolados            : {len(desac)}")

    if nuevas:
        salida = pd.concat([vig, pd.DataFrame(nuevas)], ignore_index=True)
        salida = salida.sort_values("nombre_en_fuente", kind="stable")
        salida.to_csv(path_vig, index=False, encoding="utf-8")
        print(f"  cobertura                        : {len(vig)} → {len(salida)}")
        print(f"\n  OK · data/enriched/authors_orcid.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
