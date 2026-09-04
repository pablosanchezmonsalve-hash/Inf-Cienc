"""Obras fuera del universo en repositorios de datos y acceso abierto (PD-04).

LA PREGUNTA QUE ESTE CONECTOR RESPONDE
    `openalex_cobertura.py` (V2-26, `PD-02`) ya pregunta "¿qué le atribuye a
    esta institución un índice bibliográfico grande que el universo no
    tiene?". Queda una pregunta distinta que ninguna fuente del proyecto
    hacía: **¿qué produjeron estas personas que NINGÚN índice bibliográfico
    indexa bien?** Datasets, software, preprints, pósters, materiales
    depositados. DataCite, Europe PMC y Zenodo sí los ven; Scopus, SciVal y
    OpenAlex no, o sólo en parte.

    Las tres fuentes ya están en el proyecto desde el 2026-09-03, pero
    preguntándoles otra cosa: `datacite.py`, `europepmc.py` y `zenodo.py`
    consultan **por DOI del universo** para recuperar el ORCID de sus
    autores. Eso sólo puede mirar hacia adentro. Este conector invierte la
    dirección: parte de los ORCID que el proyecto ya confirmó y de la
    afiliación institucional declarada, y trae lo que esas tres fuentes
    tienen y el universo no.

CÓMO BUSCA, Y POR QUÉ DE DOS MANERAS
    · **Por ORCID** (`via = orcid`): un identificador de persona, no una
      cadena de texto. Se usan sólo los ORCID vigentes de
      `data/enriched/authors_orcid.csv`, descontando los que
      `config/orcid_revisado.yml` marca como `retiradas` — un ORCID que una
      persona ya declaró incorrecto para esa firma no puede fundar la
      recuperación de obras suyas. Es la vía fuerte.
    · **Por afiliación** (`via = afiliacion`): la cadena institucional
      declarada en el registro. Es matching por cadena suelta, que la regla
      `I-05` prohíbe como base de una atribución — por eso aquí NUNCA
      atribuye nada: sólo propone un candidato que una persona tiene que
      confirmar. Se conserva porque recupera obras de firmas sin ORCID (267
      de 589), que la vía fuerte no puede ver por construcción.

    Ninguna de las dos vías decide nada. Las dos alimentan la misma cola.

QUÉ NO ES CADA HALLAZGO
    Una obra que estas fuentes traen y el universo no tiene **no es
    automáticamente producción institucional**. Puede ser:

      · producción real fuera de Scopus —el caso que interesa—;
      · un homónimo, cuando llegó por la vía de afiliación;
      · un tipo documental que el universo excluye a propósito;
      · **otra versión de una obra ya contada**: Zenodo acuña un DOI nuevo
        por versión, además del DOI de concepto, y DataCite indexa
        preprints cuya versión publicada sí está en Scopus. La
        deduplicación por DOI no los colapsa: son DOI distintos para la
        misma obra. Este modo de fallo es propio de estas tres fuentes y
        por eso la revisión tiene un veredicto que ningún otro indicador
        del proyecto necesita.

QUÉ NO HACE, Y NO ES NEGOCIABLE
    **No añade nada al universo** (`D-16`, `D-206`, Regla 5 de
    `docs/METODOLOGIA_FUERA_DE_SCOPUS.md`). Escribe una cola de revisión en
    la capa interna. Sólo lo que una persona confirma, una por una, llega a
    contarse como `PD-04`, y aun entonces con su propio denominador, en su
    propia sección, sin citas ni FWCI: SciVal no mide nada de esto.

    **No pisa las resoluciones ya tomadas.** Reejecutarlo conserva la
    columna `resolucion` de cada fila que siga existiendo, emparejada por
    `(fuente, id_fuente)`. Una corrida nueva no puede borrar el trabajo
    humano de la corrida anterior.

LAS PLANTILLAS DE BÚSQUEDA NO ESTÁN EN ESTE ARCHIVO
    Viven en `config/sources.yml`, campo `consulta_obras`, con `{orcid}` y
    `{institucion}` como únicos marcadores. Otra institución que replique la
    plataforma cambia `config/institution.yml` y esas plantillas, nunca
    `src/` (guardarraíl técnico de `CLAUDE.md`). Si una API cambia el nombre
    de su campo de búsqueda, se corrige la configuración, no el código.

EL CONTRATO DE BÚSQUEDA DE LAS TRES APIS NO ESTÁ VERIFICADO DESDE AQUÍ
    La política de red del entorno de desarrollo bloquea `api.datacite.org`,
    `www.ebi.ac.uk` y `zenodo.org` (403 en el CONNECT del proxy, comprobado
    el 2026-09-03). Los conectores por DOI sí se corrieron contra el corpus
    real desde otra red, pero contra el endpoint de recuperación, no contra
    el de búsqueda: la forma de la respuesta paginada es distinta y está
    tomada de la documentación, no verificada. Por eso, exactamente como
    `openalex_cobertura.py`: se comprueba la forma antes de usarla y, si no
    se reconoce, se guarda cruda y el programa se detiene diciendo dónde
    está. No se adivina.

USO
    python3 src/enrich/obras_externas.py --test          lógica, sin red
    python3 src/enrich/obras_externas.py --limit 5       5 ORCID por fuente
    python3 src/enrich/obras_externas.py --fuente zenodo una sola fuente
    python3 src/enrich/obras_externas.py --solo-afiliacion
    python3 src/enrich/obras_externas.py                 la consulta entera

Salida
    internal/obras_externas_cobertura.csv   la cola de revisión (capa interna)
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
sys.path.insert(0, str(Path(__file__).resolve().parent))
from datacite import _id_orcid  # noqa: E402  (misma forma de nameIdentifiers)
from openalex_cobertura import normalizar_doi  # noqa: E402

CACHE = c.ROOT / "data" / "cache" / "obras_externas"
SALIDA = "obras_externas_cobertura.csv"
PENDIENTE = "PENDIENTE_REVISION_HUMANA"
SOURCES = c.load_config("sources.yml")["fuentes"]
INSTITUCION = c.load_config("institution.yml")
VENTANA = INSTITUCION["ventana_temporal"]

# Pausa de cortesía por fuente. Zenodo pide más que las otras dos: su API
# pública limita a 60 peticiones por minuto para clientes sin token.
PAUSA = {"datacite": 0.20, "europepmc": 0.20, "zenodo": 1.2}

# Tamaño de página por fuente. Zenodo limita a 25 sin autenticación y
# responde HTTP 400 si se pide más —comprobado en la corrida del 2026-09-04,
# que devolvía «Page size cannot be greater than 25»—. Pedir 100 a las tres
# hacía que Zenodo rechazara CUALQUIER consulta, incluida la de texto libre,
# y el error parecía de sintaxis cuando era de tamaño.
TAMANO_PAGINA = {"datacite": 100, "europepmc": 100, "zenodo": 25}
POR_DEFECTO = 100


def pagina_de(fuente: str) -> int:
    return TAMANO_PAGINA.get(fuente, POR_DEFECTO)


class ContratoDesconocido(Exception):
    """La respuesta de búsqueda no tiene la forma esperada."""


# ───────────────────────────────────────────────── de dónde salen las consultas

def orcid_vigentes() -> list[dict]:
    """Los ORCID que este proyecto sostiene hoy, sin los retirados.

    Un ORCID que `config/orcid_revisado.yml` lista en `retiradas` fue
    declarado incorrecto para esa firma por una decisión humana previa
    (`D-08`). Usarlo para recuperar obras "de esa persona" reconstruiría,
    del lado de las obras, exactamente el error que esa decisión ya
    descartó del lado de los autores.
    """
    ruta = c.ROOT / "data" / "enriched" / "authors_orcid.csv"
    if not ruta.exists():
        return []
    df = pd.read_csv(ruta, dtype=str).fillna("")

    retiradas: set[tuple[str, str]] = set()
    rev = c.ROOT / "config" / "orcid_revisado.yml"
    if rev.exists():
        data = c.load_config("orcid_revisado.yml") or {}
        for r in data.get("retiradas") or []:
            retiradas.add((str(r.get("firma", "")).strip(),
                           str(r.get("orcid", "")).strip()))

    vigentes, vistos = [], set()
    for _, r in df.iterrows():
        firma, orcid = r["nombre_en_fuente"].strip(), r["orcid"].strip()
        if not orcid or (firma, orcid) in retiradas or orcid in vistos:
            continue
        vistos.add(orcid)
        vigentes.append({"orcid": orcid, "firma": firma,
                         "confianza": r.get("confianza", "")})
    return vigentes


def plantillas(fuente: str) -> dict:
    """`consulta_obras` de una fuente, tal como la declara sources.yml."""
    spec = SOURCES.get(f"{fuente}_api", {})
    return spec.get("consulta_obras") or {}


def plantillas_de(fuente: str, clave: str) -> list[str]:
    """Las plantillas candidatas de una consulta, en orden de preferencia.

    `sources.yml` admite una cadena o una lista. La lista existe por Zenodo:
    migró a InvenioRDM y el campo por el que se busca un ORCID cambió de
    nombre, sin que se haya podido comprobar desde ningún entorno con red
    cuál sirve hoy. Declarar las dos y dejar que la primera corrida lo
    resuelva es más honesto que elegir una a ciegas y publicar el cero que
    devuelva la equivocada.
    """
    tpl = plantillas(fuente).get(clave)
    if not tpl:
        raise KeyError(f"sources.yml: falta consulta_obras.{clave} en {fuente}_api")
    return [tpl] if isinstance(tpl, str) else list(tpl)


def consulta(fuente: str, clave: str, valor: str, i: int = 0) -> str:
    """Sustituye `{orcid}`/`{institucion}` en la plantilla `i` de esa clave."""
    return plantillas_de(fuente, clave)[i].format(orcid=valor, institucion=valor)


def elegir_plantilla(fuente: str, clave: str, valores: list[str],
                     sondas: int = 8) -> tuple[int, str]:
    """Cuál de las plantillas candidatas responde, decidido UNA vez.

    Probar la alternativa cada vez que una consulta vuelve vacía duplicaría
    las peticiones sin motivo: la mayoría de las firmas no tiene ningún
    depósito, y «cero resultados» es ahí la respuesta correcta, no un
    síntoma. Se sondea con unos pocos valores al principio y se fija la
    plantilla que devuelva algo para el resto de la corrida.

    Si ninguna devuelve nada, no se puede distinguir «el campo de búsqueda
    es otro» de «esta institución no tiene depósitos aquí»: se dice, se usa
    la primera, y la corrida sigue.
    """
    candidatas = plantillas_de(fuente, clave)
    if len(candidatas) == 1:
        return 0, "única plantilla declarada"
    motivos = []
    for i, tpl in enumerate(candidatas):
        rechazada = None
        for valor in valores[:sondas]:
            try:
                if buscar(fuente, consulta(fuente, clave, valor, i), max_paginas=1):
                    return i, f"responde con {valores.index(valor) + 1} sonda(s)"
            except urllib.error.HTTPError as e:
                # 400/422 no es «no hay resultados»: es la API diciendo que no
                # entiende la consulta. Zenodo devolvió 400 a su primera
                # plantilla el 2026-09-04, en la corrida real desde la máquina
                # del usuario. Una plantilla rechazada se descarta y se pasa
                # a la siguiente; tratarla como error fatal tiraba la corrida
                # entera y con ella el trabajo ya hecho de las otras fuentes.
                if e.code not in (400, 422):
                    raise
                rechazada = f"la API la rechaza con HTTP {e.code}"
                break
        motivos.append(f"[{i}] {rechazada or 'sin resultados en las sondas'}")
    return -1, "ninguna plantilla sirve · " + " · ".join(motivos)


# ─────────────────────────────────────────── una página de resultados por fuente
#
# Cada adaptador hace DOS cosas y ninguna más: construir la URL de una página
# y leer esa página. La normalización de cada obra vive aparte, para que el
# autotest pueda ejercitarla sobre una respuesta guardada sin tocar la red.

def _url_datacite(q: str, cursor: str | None) -> str:
    p = {"query": q, "page[size]": pagina_de("datacite"), "page[cursor]": cursor or "1"}
    return f"{SOURCES['datacite_api']['endpoint']}?{urllib.parse.urlencode(p)}"


def _pagina_datacite(data: dict) -> tuple[list[dict], str | None, int | None]:
    if not isinstance(data, dict) or not isinstance(data.get("data"), list):
        raise ContratoDesconocido("la respuesta de DataCite no trae 'data' como lista")
    total = (data.get("meta") or {}).get("total")
    siguiente = ((data.get("links") or {}).get("next") or "") or None
    if siguiente:
        # DataCite devuelve la URL entera de la página siguiente; sólo
        # interesa el cursor, para no reconstruir la consulta desde ella.
        cur = urllib.parse.parse_qs(urllib.parse.urlparse(siguiente).query).get("page[cursor]")
        siguiente = cur[0] if cur else None
    return data["data"], siguiente, total


def _obra_datacite(item: dict) -> dict:
    at = item.get("attributes") or {}
    titulos = at.get("titles") or []
    creators = at.get("creators") or []
    return {
        "id_fuente": at.get("doi") or item.get("id") or "",
        "doi": normalizar_doi(at.get("doi")),
        "titulo": (titulos[0].get("title") if titulos and isinstance(titulos[0], dict) else "") or "",
        "anio": str(at.get("publicationYear") or ""),
        "tipo": ((at.get("types") or {}).get("resourceTypeGeneral") or ""),
        "autores": [{"nombre": (cr.get("name") or "").strip(),
                     "orcid": _id_orcid(cr.get("nameIdentifiers")),
                     "afiliacion": _afiliacion_datacite(cr)}
                    for cr in creators if isinstance(cr, dict)],
    }


def _afiliacion_datacite(creator: dict) -> str:
    """DataCite da `affiliation` como lista de cadenas o de dicts con `name`."""
    af = creator.get("affiliation")
    if isinstance(af, str):
        return af
    nombres = []
    for a in af or []:
        if isinstance(a, dict):
            nombres.append(str(a.get("name") or ""))
        elif isinstance(a, str):
            nombres.append(a)
    return "; ".join(n for n in nombres if n)


def _url_europepmc(q: str, cursor: str | None) -> str:
    p = {"query": q, "format": "json", "resultType": "core",
         "pageSize": pagina_de("europepmc"), "cursorMark": cursor or "*"}
    return f"{SOURCES['europepmc_api']['endpoint']}?{urllib.parse.urlencode(p)}"


def _pagina_europepmc(data: dict) -> tuple[list[dict], str | None, int | None]:
    if not isinstance(data, dict) or "resultList" not in data:
        raise ContratoDesconocido("la respuesta de Europe PMC no trae 'resultList'")
    res = (data.get("resultList") or {}).get("result")
    if not isinstance(res, list):
        raise ContratoDesconocido("resultList.result no es una lista")
    return res, (data.get("nextCursorMark") or None), data.get("hitCount")


def _obra_europepmc(item: dict) -> dict:
    autores = []
    for a in ((item.get("authorList") or {}).get("author") or []):
        if not isinstance(a, dict):
            continue
        ident = a.get("authorId") or {}
        orcid = ident.get("value", "") if str(ident.get("type", "")).upper() == "ORCID" else ""
        afs = (a.get("authorAffiliationDetailsList") or {}).get("authorAffiliation") or []
        af = "; ".join(str(x.get("affiliation") or "") for x in afs if isinstance(x, dict))
        autores.append({"nombre": (a.get("fullName") or "").strip(),
                        "orcid": orcid, "afiliacion": af})
    if not autores and item.get("authorString"):
        # `resultType=core` normalmente trae authorList; si la respuesta viene
        # en modo reducido, la cadena libre es lo único que hay. Se conserva
        # como un solo "autor" para no perder el dato, marcado como tal.
        autores = [{"nombre": item["authorString"].strip(), "orcid": "", "afiliacion": ""}]
    return {
        "id_fuente": f"{item.get('source', '')}:{item.get('id', '')}".strip(":"),
        "doi": normalizar_doi(item.get("doi")),
        "titulo": (item.get("title") or "").strip(),
        "anio": str(item.get("pubYear") or ""),
        "tipo": _tipo_europepmc(item),
        "autores": autores,
    }


def _tipo_europepmc(item: dict) -> str:
    tipos = (item.get("pubTypeList") or {}).get("pubType") or []
    if isinstance(tipos, str):
        return tipos
    return "; ".join(str(t) for t in tipos if t)


def _url_zenodo(q: str, cursor: str | None) -> str:
    p = {"q": q, "size": pagina_de("zenodo"), "page": cursor or "1"}
    return f"{SOURCES['zenodo_api']['endpoint']}?{urllib.parse.urlencode(p)}"


def _pagina_zenodo(data: dict) -> tuple[list[dict], str | None, int | None]:
    if not isinstance(data, dict) or "hits" not in data:
        raise ContratoDesconocido("la respuesta de Zenodo no trae 'hits'")
    hits = (data.get("hits") or {}).get("hits")
    if not isinstance(hits, list):
        raise ContratoDesconocido("hits.hits no es una lista")
    total = (data.get("hits") or {}).get("total")
    if isinstance(total, dict):          # InvenioRDM lo da como {"value": N}
        total = total.get("value")
    return hits, None, total             # la paginación por página la lleva el llamador


def _creador_zenodo(cr: dict) -> dict:
    """Un autor de Zenodo, venga en la forma heredada o en la de InvenioRDM.

    Zenodo migró a InvenioRDM y las dos serializaciones conviven según el
    endpoint y la versión de la API:

        heredada    {"name": …, "orcid": …, "affiliation": …}
        InvenioRDM  {"person_or_org": {"name": …, "identifiers":
                                       [{"scheme": "orcid", "identifier": …}]},
                     "affiliations": [{"name": …}]}

    La corrida del 2026-09-03 sobre el corpus verificó la forma HEREDADA en
    el endpoint de recuperación por DOI (`src/enrich/zenodo.py`), pero el
    endpoint de BÚSQUEDA no se ha podido probar desde ningún entorno con red.
    Leer sólo la heredada habría devuelto un autor vacío por cada obra si la
    búsqueda sirviera la otra: la cola se llenaría de filas sin autor, sin
    que nada fallara — que es exactamente el modo de fallo silencioso que
    este proyecto no admite. Se aceptan las dos y se rechaza cualquier
    tercera.
    """
    if "person_or_org" in cr:
        po = cr.get("person_or_org") or {}
        orcid = ""
        for ident in po.get("identifiers") or []:
            if isinstance(ident, dict) and str(ident.get("scheme", "")).lower() == "orcid":
                orcid = str(ident.get("identifier") or "").rstrip("/").split("/")[-1]
                break
        afiliaciones = [str(a.get("name") or "") for a in (cr.get("affiliations") or [])
                        if isinstance(a, dict)]
        return {"nombre": (po.get("name") or "").strip(), "orcid": orcid,
                "afiliacion": "; ".join(a for a in afiliaciones if a)}
    if "name" in cr:
        return {"nombre": (cr.get("name") or "").strip(),
                "orcid": (cr.get("orcid") or "").strip(),
                "afiliacion": (cr.get("affiliation") or "").strip()}
    raise ContratoDesconocido(
        "un creator de Zenodo no trae ni 'name' ni 'person_or_org': "
        f"claves {sorted(cr)[:6]}")


def _obra_zenodo(item: dict) -> dict:
    md = item.get("metadata") or {}
    rt = md.get("resource_type") or {}
    tipo = rt.get("type") or ""
    if rt.get("subtype"):
        tipo = f"{tipo}/{rt['subtype']}"
    fecha = str(md.get("publication_date") or "")
    return {
        "id_fuente": str(item.get("doi") or item.get("id") or ""),
        "doi": normalizar_doi(item.get("doi") or (md.get("doi") if isinstance(md, dict) else "")),
        "titulo": (md.get("title") or item.get("title") or "").strip(),
        "anio": fecha[:4] if len(fecha) >= 4 and fecha[:4].isdigit() else "",
        "tipo": tipo,
        "autores": [_creador_zenodo(cr) for cr in (md.get("creators") or [])
                    if isinstance(cr, dict)],
    }


ADAPTADORES = {
    "datacite": {"url": _url_datacite, "pagina": _pagina_datacite,
                 "obra": _obra_datacite, "cursor": True},
    "europepmc": {"url": _url_europepmc, "pagina": _pagina_europepmc,
                  "obra": _obra_europepmc, "cursor": True},
    "zenodo": {"url": _url_zenodo, "pagina": _pagina_zenodo,
               "obra": _obra_zenodo, "cursor": False},
}


# ─────────────────────────────────────────────────────────────────────────  red

def _cache_path(fuente: str, url: str) -> Path:
    clave = re.sub(r"[^a-zA-Z0-9]+", "_", url)[-140:]
    return CACHE / fuente / (clave + ".json")


def pedir(fuente: str, url: str) -> dict:
    """Una página. Cachea en disco: reejecutar no vuelve a golpear la API."""
    path = _cache_path(fuente, url)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))

    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "InformeCienciometrico/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        # El cuerpo de un 4xx suele decir EXACTAMENTE qué parámetro sobra
        # —Zenodo respondía «Page size cannot be greater than 25»— y se
        # perdía entero: el error llegaba como «HTTP 400» a secas y parecía
        # un problema de sintaxis de la consulta.
        try:
            detalle = e.read().decode("utf-8", "replace")[:400]
        except Exception:
            detalle = ""
        if detalle:
            e.msg = f"{e.msg} · {detalle}"
        raise
    finally:
        time.sleep(PAUSA.get(fuente, 0.5))

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


def _guardar_crudo(fuente: str, data: dict) -> Path:
    destino = CACHE / fuente / "ultima_respuesta.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return destino


def buscar(fuente: str, q: str, max_paginas: int | None = None) -> list[dict]:
    """Todas las páginas de una consulta, ya normalizadas a obras."""
    ad = ADAPTADORES[fuente]
    obras: list[dict] = []
    cursor: str | None = None
    pagina_n = 0
    while True:
        url = ad["url"](q, cursor)
        data = pedir(fuente, url)
        try:
            crudas, siguiente, _ = ad["pagina"](data)
        except ContratoDesconocido as e:
            destino = _guardar_crudo(fuente, data)
            raise ContratoDesconocido(
                f"{e}\n  Respuesta cruda en {destino.relative_to(c.ROOT)}") from e
        obras += [ad["obra"](x) for x in crudas if isinstance(x, dict)]
        pagina_n += 1
        if max_paginas and pagina_n >= max_paginas:
            break
        if ad["cursor"]:
            if not siguiente or siguiente == cursor or not crudas:
                break
            cursor = siguiente
        else:
            if len(crudas) < pagina_de(fuente):
                break
            cursor = str(pagina_n + 1)
    return obras


# ────────────────────────────────────────────────────────────── de obra a fila

def _autor_del_hallazgo(obra: dict, via: str, valor: str) -> tuple[str, str, str]:
    """Quién, entre los autores de la obra, sostiene el vínculo institucional.

    Sin esto, revisar a mano exigiría abrir cada obra para saber cuál de los
    N autores es el vínculo con la institución — que es justo lo que la
    consulta ya sabía y se perdería al extraer.
    """
    autores = obra.get("autores") or []
    if via == "orcid":
        for a in autores:
            if (a.get("orcid") or "").rstrip("/").split("/")[-1] == valor:
                return a.get("nombre", ""), valor, a.get("afiliacion", "")
        # La fuente respondió a la consulta por ORCID pero no lo repite en el
        # registro. Es un dato ausente, no una contradicción: se declara.
        return "", valor, ""
    clave = valor.casefold()
    for a in autores:
        if clave in (a.get("afiliacion") or "").casefold():
            return a.get("nombre", ""), (a.get("orcid") or ""), a.get("afiliacion", "")
    return "", "", ""


def cribar(obras: list[dict], fuente: str, via: str, valor: str,
           firma: str, dois_universo: set[str]) -> list[dict]:
    """Las obras que el universo no tiene, con la evidencia de cada una.

    Una obra SIN DOI no se puede contrastar contra el universo por clave: no
    se descarta ni se afirma que falte — entra a la cola con su motivo
    dicho, para que la revisión humana decida mirando la obra.
    """
    filas = []
    for o in obras:
        doi = o.get("doi") or ""
        if doi and doi in dois_universo:
            continue
        nombre, orcid, afiliacion = _autor_del_hallazgo(o, via, valor)
        filas.append({
            "fuente": fuente,
            "id_fuente": o.get("id_fuente", ""),
            "doi": doi,
            "titulo": o.get("titulo", ""),
            "anio": o.get("anio", ""),
            "tipo": o.get("tipo", ""),
            "via": via,
            "consulta": valor,
            "firma_uft": firma,
            "autor_en_la_fuente": nombre,
            "orcid_en_la_fuente": orcid,
            "afiliacion_declarada": afiliacion,
            "motivo": ("con DOI, y ese DOI no está en el universo" if doi
                       else "sin DOI: no se puede contrastar contra el universo por clave"),
        })
    return filas


def colapsar(filas: list[dict]) -> tuple[list[dict], int]:
    """Una fila por obra: `(fuente, id_fuente)` es la clave de identidad.

    La misma obra puede llegar dos veces por vías distintas —por el ORCID de
    un coautor y por la afiliación de otro—. Eso es evidencia MÁS FUERTE
    para esa obra, nunca una obra más (Regla 3 de
    `docs/METODOLOGIA_FUERA_DE_SCOPUS.md`): las vías y las firmas se acumulan
    en la misma fila, separadas por '|'.
    """
    por_clave: dict[tuple[str, str], dict] = {}
    colapsadas = 0
    for f in filas:
        clave = (f["fuente"], f["id_fuente"])
        if clave not in por_clave:
            por_clave[clave] = dict(f)
            continue
        colapsadas += 1
        ya = por_clave[clave]
        for campo in ("via", "consulta", "firma_uft"):
            valores = [v for v in ya[campo].split("|") if v]
            if f[campo] and f[campo] not in valores:
                ya[campo] = "|".join(valores + [f[campo]])
        for campo in ("autor_en_la_fuente", "orcid_en_la_fuente", "afiliacion_declarada"):
            if not ya[campo] and f[campo]:
                ya[campo] = f[campo]
    return list(por_clave.values()), colapsadas


def marcar_corroboracion(filas: list[dict]) -> list[dict]:
    """Qué obras trae más de una de las tres fuentes, por DOI.

    Tres registros del mismo DOI en DataCite, Europe PMC y Zenodo son UNA
    obra corroborada tres veces, no tres obras. La corroboración se anota
    aquí y el recuento la resta al agregar (`build 09`), nunca antes: quien
    revisa necesita ver las tres, quien cuenta necesita una.
    """
    por_doi: dict[str, set[str]] = {}
    for f in filas:
        if f["doi"]:
            por_doi.setdefault(f["doi"], set()).add(f["fuente"])
    for f in filas:
        otras = sorted(por_doi.get(f["doi"], set()) - {f["fuente"]}) if f["doi"] else []
        f["corroborada_por"] = "|".join(otras)
    return filas


def conservar_resoluciones(nuevas: list[dict], previas: pd.DataFrame | None) -> tuple[list[dict], int]:
    """Reejecutar no borra lo que una persona ya decidió.

    La cola se reconstruye entera en cada corrida, pero la columna
    `resolucion` es trabajo humano, no un dato recuperado de la API:
    sobrescribirla con `PENDIENTE` devolvería a cero cada revisión al
    refrescar la fuente.
    """
    previo: dict[tuple[str, str], str] = {}
    if previas is not None and not previas.empty:
        for _, r in previas.iterrows():
            previo[(str(r.get("fuente", "")), str(r.get("id_fuente", "")))] = \
                str(r.get("resolucion", "") or PENDIENTE)
    conservadas = 0
    for f in nuevas:
        anterior = previo.get((f["fuente"], f["id_fuente"]))
        if anterior and anterior != PENDIENTE:
            f["resolucion"] = anterior
            conservadas += 1
        else:
            f["resolucion"] = PENDIENTE
    return nuevas, conservadas


# ──────────────────────────────────────────────────────────────────── autotest

DATACITE_BUSQUEDA = {
    "data": [{
        "id": "10.5281/zenodo.1", "type": "dois",
        "attributes": {
            "doi": "10.5281/ZENODO.1",
            "titles": [{"title": "Dataset de prueba"}],
            "publicationYear": 2024,
            "types": {"resourceTypeGeneral": "Dataset"},
            "creators": [{
                "name": "Pérez, Ana",
                "nameIdentifiers": [{"nameIdentifierScheme": "ORCID",
                                     "nameIdentifier": "https://orcid.org/0000-0001-0000-0001"}],
                "affiliation": [{"name": "Universidad Finis Terrae"}],
            }],
        },
    }],
    "links": {"next": "https://api.datacite.org/dois?page%5Bcursor%5D=abc"},
    "meta": {"total": 1},
}

EUROPEPMC_BUSQUEDA = {
    "hitCount": 1,
    "nextCursorMark": "AoE=",
    "resultList": {"result": [{
        "id": "39000001", "source": "MED", "doi": "10.1000/EPMC.1",
        "title": "Preprint de prueba", "pubYear": "2023",
        "pubTypeList": {"pubType": ["preprint"]},
        "authorList": {"author": [{
            "fullName": "Perez A",
            "authorId": {"type": "ORCID", "value": "0000-0001-0000-0001"},
            "authorAffiliationDetailsList": {
                "authorAffiliation": [{"affiliation": "Universidad Finis Terrae, Chile"}]},
        }]},
    }]},
}

ZENODO_BUSQUEDA = {
    "hits": {"total": 1, "hits": [{
        "id": 77, "doi": "10.5281/zenodo.77",
        "metadata": {
            "title": "Software de prueba",
            "publication_date": "2025-04-01",
            "resource_type": {"type": "software"},
            "creators": [{"name": "Pérez, Ana", "orcid": "0000-0001-0000-0001",
                          "affiliation": "Universidad Finis Terrae"}],
        },
    }]},
}


def autotest() -> int:
    casos = []

    def caso(n, ok, obs=None):
        casos.append((n, ok, obs))

    # ── la forma de cada respuesta paginada
    items, cur, total = _pagina_datacite(DATACITE_BUSQUEDA)
    caso("DataCite: una página, cursor siguiente y total",
         len(items) == 1 and cur == "abc" and total == 1, (len(items), cur, total))
    o = _obra_datacite(items[0])
    caso("DataCite: DOI normalizado a minúsculas", o["doi"] == "10.5281/zenodo.1", o["doi"])
    caso("DataCite: tipo, año y afiliación extraídos",
         o["tipo"] == "Dataset" and o["anio"] == "2024"
         and o["autores"][0]["afiliacion"] == "Universidad Finis Terrae", o)
    caso("DataCite: ORCID leído de nameIdentifiers",
         o["autores"][0]["orcid"] == "0000-0001-0000-0001", o["autores"])

    items, cur, total = _pagina_europepmc(EUROPEPMC_BUSQUEDA)
    caso("Europe PMC: una página y su cursorMark", len(items) == 1 and cur == "AoE=", (items, cur))
    o = _obra_europepmc(items[0])
    caso("Europe PMC: id compuesto fuente:id", o["id_fuente"] == "MED:39000001", o["id_fuente"])
    caso("Europe PMC: ORCID sólo si authorId.type es ORCID",
         o["autores"][0]["orcid"] == "0000-0001-0000-0001", o["autores"])

    items, cur, total = _pagina_zenodo(ZENODO_BUSQUEDA)
    caso("Zenodo: una página, sin cursor (pagina por número)",
         len(items) == 1 and cur is None, (items, cur))
    o = _obra_zenodo(items[0])
    caso("Zenodo: año tomado de publication_date", o["anio"] == "2025", o["anio"])
    caso("Zenodo: tipo con subtipo cuando lo hay", o["tipo"] == "software", o["tipo"])

    # ── contratos rotos: se detienen, no adivinan
    for nombre, fn, roto in (
        ("DataCite", _pagina_datacite, {"data": "no es lista"}),
        ("Europe PMC", _pagina_europepmc, {"resultList": {"result": 3}}),
        ("Zenodo", _pagina_zenodo, {"hits": {"hits": None}}),
    ):
        try:
            fn(roto)
            ok = False
        except ContratoDesconocido:
            ok = True
        caso(f"{nombre}: una respuesta con otra forma levanta ContratoDesconocido", ok)

    # ── el cribado contra el universo
    obras = [
        {"id_fuente": "a", "doi": "10.1/ya", "titulo": "Ya en el universo", "anio": "2024",
         "tipo": "Dataset", "autores": [{"nombre": "P A", "orcid": "0000-0001-0000-0001", "afiliacion": ""}]},
        {"id_fuente": "b", "doi": "10.1/nueva", "titulo": "Nueva", "anio": "2024",
         "tipo": "Dataset", "autores": [{"nombre": "P A", "orcid": "0000-0001-0000-0001", "afiliacion": ""}]},
        {"id_fuente": "c", "doi": "", "titulo": "Sin DOI", "anio": "2024",
         "tipo": "Poster", "autores": [{"nombre": "P A", "orcid": "", "afiliacion": ""}]},
    ]
    filas = cribar(obras, "zenodo", "orcid", "0000-0001-0000-0001", "Pérez A.", {"10.1/ya"})
    caso("lo que ya está en el universo no entra a la cola", len(filas) == 2, [f["doi"] for f in filas])
    caso("una obra sin DOI entra con su motivo dicho, no se descarta",
         any(f["motivo"].startswith("sin DOI") for f in filas), filas)
    caso("el autor que sostiene el vínculo queda identificado",
         filas[0]["autor_en_la_fuente"] == "P A", filas[0])

    # ── una obra hallada por dos vías es una obra, con más evidencia
    dobles = [
        {"fuente": "zenodo", "id_fuente": "z1", "doi": "10.1/x", "titulo": "t", "anio": "2024",
         "tipo": "Dataset", "via": "orcid", "consulta": "0000-0001-0000-0001",
         "firma_uft": "Pérez A.", "autor_en_la_fuente": "Pérez, Ana",
         "orcid_en_la_fuente": "0000-0001-0000-0001", "afiliacion_declarada": "", "motivo": "m"},
        {"fuente": "zenodo", "id_fuente": "z1", "doi": "10.1/x", "titulo": "t", "anio": "2024",
         "tipo": "Dataset", "via": "afiliacion", "consulta": "Universidad Finis Terrae",
         "firma_uft": "", "autor_en_la_fuente": "", "orcid_en_la_fuente": "",
         "afiliacion_declarada": "Universidad Finis Terrae", "motivo": "m"},
    ]
    unicas, colapsadas = colapsar(dobles)
    caso("dos vías sobre la misma obra dan UNA fila", len(unicas) == 1 and colapsadas == 1, unicas)
    caso("las dos vías quedan anotadas en esa fila",
         unicas[0]["via"] == "orcid|afiliacion", unicas[0]["via"])
    caso("el dato que sólo traía una de las dos no se pierde",
         unicas[0]["afiliacion_declarada"] == "Universidad Finis Terrae", unicas[0])

    # ── corroboración entre fuentes distintas
    cruzadas = marcar_corroboracion([
        {"fuente": "datacite", "id_fuente": "d1", "doi": "10.1/x"},
        {"fuente": "zenodo", "id_fuente": "z1", "doi": "10.1/x"},
        {"fuente": "europepmc", "id_fuente": "e1", "doi": "10.1/solo"},
    ])
    caso("una obra en dos fuentes queda marcada como corroborada",
         cruzadas[0]["corroborada_por"] == "zenodo"
         and cruzadas[1]["corroborada_por"] == "datacite", cruzadas)
    caso("una obra en una sola fuente no se marca",
         cruzadas[2]["corroborada_por"] == "", cruzadas[2])

    # ── reejecutar no borra decisiones humanas
    previas = pd.DataFrame([
        {"fuente": "zenodo", "id_fuente": "z1", "resolucion": "CONFIRMADO_PRODUCCION_UFT"},
        {"fuente": "zenodo", "id_fuente": "z2", "resolucion": PENDIENTE},
    ])
    refrescadas, conservadas = conservar_resoluciones(
        [{"fuente": "zenodo", "id_fuente": "z1"}, {"fuente": "zenodo", "id_fuente": "z2"},
         {"fuente": "zenodo", "id_fuente": "z3"}], previas)
    caso("una resolución humana previa sobrevive a la reejecución",
         refrescadas[0]["resolucion"] == "CONFIRMADO_PRODUCCION_UFT", refrescadas[0])
    caso("una fila nueva nace pendiente", refrescadas[2]["resolucion"] == PENDIENTE, refrescadas[2])
    caso("se informa cuántas se conservaron", conservadas == 1, conservadas)

    # ── Zenodo sirve dos serializaciones distintas del mismo autor
    heredada = _obra_zenodo(ZENODO_BUSQUEDA["hits"]["hits"][0])
    caso("Zenodo, forma heredada: nombre, ORCID y afiliación",
         heredada["autores"][0] == {"nombre": "Pérez, Ana",
                                    "orcid": "0000-0001-0000-0001",
                                    "afiliacion": "Universidad Finis Terrae"},
         heredada["autores"][0])
    invenio = _obra_zenodo({"doi": "10.5281/zenodo.78", "metadata": {
        "title": "t", "publication_date": "2025-01-01",
        "resource_type": {"type": "dataset"},
        "creators": [{"person_or_org": {
            "name": "Pérez, Ana",
            "identifiers": [{"scheme": "orcid",
                             "identifier": "https://orcid.org/0000-0001-0000-0001"}]},
            "affiliations": [{"name": "Universidad Finis Terrae"}]}]}})
    caso("Zenodo, forma InvenioRDM: el mismo autor, leído igual",
         invenio["autores"][0] == heredada["autores"][0], invenio["autores"][0])
    try:
        _obra_zenodo({"metadata": {"creators": [{"otra_cosa": 1}]}})
        ok = False
    except ContratoDesconocido:
        ok = True
    caso("un creator con una tercera forma se detiene, no devuelve un autor vacío", ok)

    # ── las plantillas salen de sources.yml, no del código
    caso("la consulta por ORCID se arma desde sources.yml",
         consulta("zenodo", "por_orcid", "0000-0001-0000-0001")
         == 'creators.orcid:"0000-0001-0000-0001"',
         consulta("zenodo", "por_orcid", "0000-0001-0000-0001"))
    caso("Zenodo declara varias plantillas candidatas por vía",
         len(plantillas_de("zenodo", "por_orcid")) >= 2
         and len(plantillas_de("zenodo", "por_afiliacion")) >= 2)
    caso("la última candidata es texto libre, sin nombre de campo",
         ":" not in plantillas_de("zenodo", "por_orcid")[-1],
         plantillas_de("zenodo", "por_orcid")[-1])
    caso("la segunda candidata es la de InvenioRDM",
         "person_or_org" in plantillas_de("zenodo", "por_orcid")[1])
    caso("una fuente con una sola plantilla no gasta sondas",
         elegir_plantilla("datacite", "por_orcid", ["0000-0001-0000-0001"])
         == (0, "única plantilla declarada"))
    caso("la consulta por afiliación se arma desde sources.yml",
         'Universidad Finis Terrae' in consulta("europepmc", "por_afiliacion",
                                                INSTITUCION["institucion"]["nombre_canonico"]))
    caso("ninguna cadena de consulta está escrita en este archivo",
         "creators.orcid:" not in Path(__file__).read_text(encoding="utf-8")
         .split("DATACITE_BUSQUEDA")[0])

    # ── el tamaño de página lo fija cada API, no una constante global
    caso("Zenodo pide 25 por página, no 100", pagina_de("zenodo") == 25, pagina_de("zenodo"))
    caso("las otras dos siguen en 100",
         pagina_de("datacite") == 100 and pagina_de("europepmc") == 100)
    caso("la URL de Zenodo lleva ese tamaño",
         "size=25" in _url_zenodo("x", None), _url_zenodo("x", None))
    caso("una fuente desconocida cae en el valor por defecto", pagina_de("otra") == 100)

    # ── una plantilla que la API rechaza se descarta, no tumba la corrida
    import types
    _buscar_real = globals()["buscar"]
    llamadas = []

    def _falso(fuente, q, max_paginas=None):
        llamadas.append(q)
        if "creators.orcid" in q:
            raise urllib.error.HTTPError(q, 400, "BAD REQUEST", None, None)
        return [{"id_fuente": "z1"}]

    globals()["buscar"] = _falso
    try:
        i, motivo = elegir_plantilla("zenodo", "por_orcid", ["0000-0001-0000-0001"])
        caso("un HTTP 400 descarta esa plantilla y prueba la siguiente", i == 1, (i, motivo))
        caso("y el motivo describe con qué sonda respondió la buena",
             "responde" in motivo, motivo)
        caso("la plantilla rechazada se probó antes que la buena",
             any("creators.orcid" in q for q in llamadas), llamadas)

        def _todo_400(fuente, q, max_paginas=None):
            raise urllib.error.HTTPError(q, 400, "BAD REQUEST", None, None)

        globals()["buscar"] = _todo_400
        i2, m2 = elegir_plantilla("zenodo", "por_orcid", ["0000-0001-0000-0001"])
        caso("si ninguna sirve, se devuelve -1 para saltar la vía", i2 == -1, (i2, m2))

        def _500(fuente, q, max_paginas=None):
            raise urllib.error.HTTPError(q, 500, "SERVER ERROR", None, None)

        globals()["buscar"] = _500
        try:
            elegir_plantilla("zenodo", "por_orcid", ["0000-0001-0000-0001"])
            ok = False
        except urllib.error.HTTPError:
            ok = True
        caso("un 500 NO se confunde con una plantilla mala: se propaga", ok)
    finally:
        globals()["buscar"] = _buscar_real

    # ── los ORCID retirados no fundan búsquedas
    vigentes = orcid_vigentes()
    retirados = {(str(r.get("firma", "")).strip(), str(r.get("orcid", "")).strip())
                 for r in (c.load_config("orcid_revisado.yml") or {}).get("retiradas") or []}
    caso("ningún ORCID retirado entra a la lista de consulta",
         not any((v["firma"], v["orcid"]) in retirados for v in vigentes),
         [v for v in vigentes if (v["firma"], v["orcid"]) in retirados][:3])
    caso("hay ORCID vigentes que consultar", len(vigentes) > 0, len(vigentes))

    fallos = [n for n, ok, _ in casos if not ok]
    for n, ok, obs in casos:
        marca = "OK  " if ok else "FALLA"
        print(f"  {marca} {n}" + (f"  ({obs})" if not ok and obs is not None else ""))
    print(f"\n{len(casos) - len(fallos)}/{len(casos)} comprobaciones")
    return 1 if fallos else 0


# ────────────────────────────────────────────────────────────────────── main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--test", action="store_true", help="verifica la lógica sin red")
    ap.add_argument("--limit", type=int, help="cuántos ORCID consultar por fuente (prueba)")
    ap.add_argument("--fuente", choices=sorted(ADAPTADORES), help="una sola fuente")
    ap.add_argument("--solo-afiliacion", action="store_true",
                    help="omite la vía por ORCID (sólo la consulta institucional)")
    args = ap.parse_args()

    c.banner("OBRAS FUERA DEL UNIVERSO EN REPOSITORIOS DE DATOS Y ACCESO ABIERTO (PD-04)")
    if args.test:
        return autotest()

    universo = c.INTERIM / "publications_universe.csv"
    if not universo.exists():
        sys.exit("Falta data/interim/publications_universe.csv. "
                 "Ejecute:  python3 src/audit/run_all.py")
    uni = pd.read_csv(universo, dtype=str)
    dois_universo = {normalizar_doi(d) for d in uni["doi"].dropna()} - {""}

    institucion = INSTITUCION["institucion"]["nombre_canonico"]
    vigentes = orcid_vigentes()
    if args.limit:
        vigentes = vigentes[:args.limit]
    fuentes = [args.fuente] if args.fuente else sorted(ADAPTADORES)

    print(f"  universo          : {len(uni)} publicaciones · {len(dois_universo)} con DOI")
    print(f"  ORCID vigentes    : {len(vigentes)} (sin los retirados de config/orcid_revisado.yml)")
    print(f"  fuentes           : {', '.join(fuentes)}")
    print(f"  ventana declarada : {VENTANA['anio_inicio']}–{VENTANA['anio_fin']}"
          "  (no filtra la cola: la partición por ventana la hace el build 09)")

    filas: list[dict] = []
    fallos: list[str] = []
    for fuente in fuentes:
        print(f"\n  ── {fuente}")
        consultas: list[tuple[str, str, str]] = []
        if not args.solo_afiliacion:
            consultas += [("orcid", v["orcid"], v["firma"]) for v in vigentes]
        consultas.append(("afiliacion", institucion, ""))

        # Qué plantilla de consulta sirve se decide aquí, una vez por fuente
        # y por vía, con unas pocas sondas — no en cada una de las 322
        # consultas. Sólo Zenodo declara más de una candidata hoy.
        elegida: dict[str, int] = {}
        for via in sorted({v for v, _, _ in consultas}):
            valores = [val for vv, val, _ in consultas if vv == via]
            try:
                i, motivo = elegir_plantilla(fuente, f"por_{via}", valores)
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
                fallos.append(f"{fuente}/{via}: no se pudo consultar ({e})")
                i, motivo = -1, str(e)
            except (KeyError, ContratoDesconocido) as e:
                fallos.append(f"{fuente}/{via}: {e}")
                i, motivo = -1, str(e)
            if i < 0:
                # Esta vía queda fuera de la corrida. Lo que ya recuperaron las
                # otras fuentes se conserva y se escribe: perder el trabajo de
                # dos APIs porque una tercera rechaza su consulta no ayuda a
                # nadie, y la cola declara al final qué quedó sin consultar.
                print(f"     por_{via}: SIN CONSULTAR · {motivo}")
                continue
            elegida[via] = i
            if len(plantillas_de(fuente, f"por_{via}")) > 1:
                print(f"     plantilla por_{via}: "
                      f"{plantillas_de(fuente, f'por_{via}')[i]}  ({motivo})")

        recuperadas = 0
        for via, valor, firma in consultas:
            if via not in elegida:
                continue
            try:
                q = consulta(fuente, f"por_{via}", valor, elegida[via])
            except KeyError as e:
                sys.exit(f"\n  {e}")
            try:
                obras = buscar(fuente, q)
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
                fallos.append(f"{fuente}/{via} «{valor}»: {e}")
                continue
            except ContratoDesconocido as e:
                fallos.append(f"{fuente}/{via}: contrato inesperado · {e}")
                break
            recuperadas += len(obras)
            filas += cribar(obras, fuente, via, valor, firma, dois_universo)
        print(f"     obras recuperadas : {recuperadas}")
        print(f"     fuera del universo: {sum(1 for f in filas if f['fuente'] == fuente)}")

    if not filas:
        print("\n  Ninguna obra fuera del universo. No se escribe ningún archivo.")
        return 0

    filas, colapsadas = colapsar(filas)
    filas = marcar_corroboracion(filas)

    ruta = c.INTERNAL / SALIDA
    previas = pd.read_csv(ruta, dtype=str) if ruta.exists() else None
    filas, conservadas = conservar_resoluciones(filas, previas)

    df = pd.DataFrame(filas).assign(
        tipo_hallazgo="PD-04_obra_en_repositorio_externo_fuera_del_universo",
        severidad="media",
        consecuencia="Una fuente de outputs no tradicionales la atribuye a una firma o "
                     "a la afiliación institucional y el universo no la tiene; puede ser "
                     "producción fuera de Scopus, un homónimo, un tipo documental "
                     "excluido a propósito, u otra versión de una obra ya contada",
        fecha_consulta=date.today().isoformat())
    c.write_internal(df, SALIDA)

    print(f"\n  filas en la cola   : {len(df)}  ({colapsadas} halladas por más de una vía)")
    print(f"  corroboradas       : {sum(1 for f in filas if f['corroborada_por'])}"
          " (el mismo DOI en más de una fuente)")
    print(f"  resoluciones vivas : {conservadas} conservadas de la corrida anterior")
    if fallos:
        print(f"\n  NO SE PUDO CONSULTAR ({len(fallos)}):")
        for f in fallos[:10]:
            print(f"    ⚠ {f}")
        if len(fallos) > 10:
            print(f"    … y {len(fallos) - 10} más")
        print("  La cola se escribe igual con lo recuperado; esas vías faltan.")

    print("\n  Es una COLA DE REVISIÓN, no un ajuste del corpus: nada de esto entra en el")
    print("  universo (D-206, Regla 5 de docs/METODOLOGIA_FUERA_DE_SCOPUS.md). Sólo lo")
    print("  que una persona confirme una por una llega a contarse como PD-04.")
    print(f"\n  Siguiente: python3 src/review/build_obras_externas_review.py")
    print(f"  OK · internal/{SALIDA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
