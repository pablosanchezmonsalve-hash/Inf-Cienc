"""Evidencia de identidad desde la búsqueda por afiliación de Scopus
Author Search (`data/raw/Scopus_Author_Search_UFT.csv`).

QUÉ ES LA FUENTE
    Un export de Scopus Author Search por afiliación "Universidad Finis
    Terrae", entregado por el responsable del proyecto el 2026-09-02: 812
    perfiles de autor (Nombre "Apellido, Nombre", Scopus Author ID, N° de
    documentos, Área temática, ORCID cuando Scopus lo tiene). Distinta en
    naturaleza de todo lo demás que este proyecto usa de Scopus: no es el
    export nativo de publicaciones (`scopus_export`, 823 filas, ventana
    2023-2025), es el directorio de AUTORES que Scopus asocia a la
    institución — sin ventana temporal declarada, y sin que el usuario
    haya aplicado ningún filtro de año (confirmado en sesión: "búsqueda
    por afiliación", nada más). El recuento de documentos de cada perfil
    es el que ve Scopus Author Search, no el que cae dentro del corpus de
    este proyecto — los dos números casi nunca van a coincidir, y este
    conector nunca los mezcla sin decirlo.

QUÉ RESUELVE
    Dos preguntas distintas, con dos salidas distintas:

    1. `internal/scopus_author_search_multiples_id.csv` — nombres que esta
       fuente lista con MÁS DE UN Scopus Author ID. El detector automático
       del proyecto (`P-04`, `src/audit/04_author_population.py`) sólo ve
       fragmentación cuando los dos identificadores aparecen, dentro del
       corpus de 823 publicaciones, bajo la MISMA cadena de nombre exacta
       — no puede ver un identificador cuyas publicaciones caen fuera del
       corpus, ni conectar dos identificadores que aparecen bajo dos
       grafías distintas del mismo nombre (verificado con casos reales
       antes de escribir este conector: "Esis Villarroel, Ivette S." tiene
       un segundo perfil con 14 documentos invisible al detector; "Caffarena,
       Paula" tiene sus dos identificadores en el corpus, pero uno de ellos
       bajo "Barcenilla, Paula Caffarena" — apellidos en otro orden). Esta
       fuente SÍ los ve, porque Scopus ya agrupó por identificador antes de
       exportar. Cada candidato se cruza contra el corpus (¿aparece cada ID
       ahí, bajo qué nombre, con cuántas publicaciones?) y contra
       `internal/ambiguities_authors.csv` (¿ya estaba conocido, o es nuevo?).

       Un segundo detector (`candidatos_fragmentacion_orcid`, agregado
       2026-09-03) cubre lo que el primero tampoco ve: dos identificadores
       que NO comparten nombre en ninguna de las dos fuentes, y sólo se
       conectan por compartir el mismo ORCID. Caso real que lo motivó:
       "Fortuny, Esteban Fortuny" (esta fuente, Auth-ID 57203373183)
       comparte ORCID con "Fortuny E." (el corpus del proyecto, Auth-ID
       59254638800) — ningún nombre en común entre las dos filas, así que
       `candidatos_multiples_id` —que agrupa por nombre exacto dentro de
       esta misma fuente— no podía verlo. Sus candidatos viajan en el mismo
       CSV y la misma cola de revisión: es la misma pregunta ("¿perfil
       Scopus fragmentado?"), sólo cambia de dónde sale la evidencia.

    2. `internal/scopus_author_search_orcid.csv` — contraste de los ORCID
       que trae esta fuente (50 de 812 filas) contra
       `data/enriched/authors_orcid.csv`. Tercera fuente independiente de
       ORCID además de Crossref y el registro público de ORCID — declarado
       por Scopus mismo en el perfil del autor, no inferido por apellido.

QUÉ NO HACE
    No decide nada (D-08). No fusiona identidades, no sube ni baja ninguna
    confianza existente, no escribe en `data/enriched/authors_orcid.csv`.
    Un ORCID que contradice al ya asignado se reporta como conflicto —igual
    que hace `orcid_crossref.py`— nunca se resuelve solo. No toca
    `publications_universe.csv` ni ningún indicador.

USO
    python3 src/enrich/scopus_author_search.py            # todo local, sin red
    python3 src/enrich/scopus_author_search.py --test     # valida el parseo

Salidas (capa interna):
    internal/scopus_author_search_multiples_id.csv
    internal/scopus_author_search_orcid.csv
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import pandas as pd

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audit"))
import common as c  # noqa: E402

FUENTE = c.ROOT / "data" / "raw" / "Scopus_Author_Search_UFT.csv"
RAW_SCOPUS = c.ROOT / c.SOURCES["scopus_export"]["archivo"]
MATCHING_LOG = c.INTERNAL / "matching_log.csv"
AMBIGUEDADES = c.INTERNAL / "ambiguities_authors.csv"
AUTHORS_ORCID = c.ROOT / "data" / "enriched" / "authors_orcid.csv"

_RE_AUTOR_ID = re.compile(r"(.+?)\s+\((\d+)\)$")
_RE_ORCID = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")


# --------------------------------------------------------------------------- #
# Lectura de la fuente (CSV multilínea, con cabecera de reporte antes de la
# fila de columnas reales — mismo problema que resolvió facultad_medicina_
# publicaciones.py para otro formato de exportación distinto)
# --------------------------------------------------------------------------- #

def leer_fuente(path: Path = FUENTE) -> list[dict]:
    texto = path.read_text(encoding="utf-8-sig")
    lineas = texto.splitlines(keepends=True)
    inicio = next(i for i, ln in enumerate(lineas) if ln.startswith('"Author Name"'))
    lector = csv.DictReader(io.StringIO("".join(lineas[inicio:])))
    filas = []
    for r in lector:
        nombre = (r.get("Author Name") or "").strip()
        if not nombre:
            continue
        orcid = (r.get("Orc_ID") or "").strip()
        filas.append({
            "nombre": nombre,
            "auth_id": (r.get("Auth-ID") or "").strip(),
            "n_documentos": (r.get("Number of Documents") or "").strip(),
            "areas": [a.strip() for a in (r.get("Subject Area") or "").splitlines() if a.strip()],
            "orcid": orcid if _RE_ORCID.match(orcid) else "",
        })
    return filas


# --------------------------------------------------------------------------- #
# Normalización — mismo criterio que el resto de src/enrich/: cada conector
# lleva su propia copia pequeña (D-y las notas de docs/METODOLOGIA_FUERA_DE_
# SCOPUS.md sobre normalizar_doi aplican igual aquí; ver también
# build_review.py::_firma_corta_p04, copia deliberada de la misma función en
# 04_author_population.py porque un módulo que empieza con dígito no es
# importable).
# --------------------------------------------------------------------------- #

def _norm(text: str) -> str:
    base = unicodedata.normalize("NFD", str(text or ""))
    base = "".join(ch for ch in base if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z\s]", " ", base.lower()).strip()


def firma_corta(nombre_completo: str) -> str:
    """'Apellido, Nombre' -> 'Apellido N.' — la forma abreviada con la que
    firman las publicaciones y con la que indexa authors_orcid.csv. Misma
    lógica que _firma_corta()/_firma_corta_p04 (04_author_population.py,
    build_review.py): no se reimporta por el nombre de módulo con dígito
    inicial, se copia — es la convención ya establecida en este proyecto."""
    partes = nombre_completo.split(",")
    corta = partes[0].strip()
    if len(partes) > 1:
        iniciales = "".join(p[0] + "." for p in partes[1].split() if p[:1].isalpha())
        corta = f"{corta} {iniciales}".strip()
    return corta


def scopus_id_map(scopus: pd.DataFrame) -> dict[str, set[str]]:
    """'Author full names' -> {Scopus Author ID}. Misma extracción que
    scopus_id_map() en 04_author_population.py, copiada por la misma razón
    de no poder importar un módulo con nombre que empieza en dígito."""
    out: dict[str, set[str]] = defaultdict(set)
    for full in scopus["Author full names"].dropna():
        for part in full.split("; "):
            m = _RE_AUTOR_ID.match(part.strip())
            if m:
                out[m.group(1).strip()].add(m.group(2))
    return out


def ids_reverse_map(ids_por_nombre: dict[str, set[str]]) -> dict[str, set[str]]:
    """Scopus Author ID -> {nombres bajo los que aparece en el corpus}."""
    out: dict[str, set[str]] = defaultdict(set)
    for nombre, sids in ids_por_nombre.items():
        for sid in sids:
            out[sid].add(nombre)
    return out


def publicaciones_por_id(scopus: pd.DataFrame) -> dict[str, int]:
    """Scopus Author ID -> cuántas publicaciones del corpus firma."""
    out: dict[str, int] = defaultdict(int)
    for full in scopus["Author full names"].dropna():
        vistos_en_esta_fila = set()
        for part in full.split("; "):
            m = _RE_AUTOR_ID.match(part.strip())
            if m:
                vistos_en_esta_fila.add(m.group(2))
        for sid in vistos_en_esta_fila:
            out[sid] += 1
    return out


def auth_ids_por_firma(scopus: pd.DataFrame, matching_log: pd.DataFrame) -> dict[str, set[str]]:
    """Firma resuelta del proyecto -> {Scopus Author ID} que le corresponde en
    el corpus, por POSICIÓN de autor dentro de cada EID — no por nombre solo.

    Un EID con varios coautores UFT mezclaría el identificador de uno con la
    firma de otro si se buscara sólo por nombre: "Author full names" trae a
    TODOS los autores de la publicación en una sola cadena. Bug real,
    encontrado y corregido en la revisión de 2026-09-03 (candidatos "Bustos
    Arriagada"/"Simón"/"Santibañez" daban resultados cruzados hasta que se
    cruzó por `posicion_autor`) antes de reportar nada — se corrige aquí de
    la misma forma, no sólo a mano."""
    eid_posiciones: dict[str, dict[int, str]] = {}
    for eid, full in zip(scopus["EID"], scopus["Author full names"].fillna("")):
        pos_a_id = {}
        for i, parte in enumerate(full.split("; "), start=1):
            m = _RE_AUTOR_ID.match(parte.strip())
            if m:
                pos_a_id[i] = m.group(2)
        eid_posiciones[eid] = pos_a_id

    out: dict[str, set[str]] = defaultdict(set)
    for _, r in matching_log.iterrows():
        try:
            pos = int(r["posicion_autor"])
        except (TypeError, ValueError):
            continue
        sid = eid_posiciones.get(r["eid"], {}).get(pos)
        if sid:
            out[r["nombre_en_fuente"]].add(sid)
    return out


# --------------------------------------------------------------------------- #
# 1. Nombres con más de un Scopus Author ID
# --------------------------------------------------------------------------- #

def candidatos_multiples_id(filas_fuente: list[dict], ids_por_nombre: dict[str, set[str]],
                             ids_reverso: dict[str, set[str]], pubs_por_id: dict[str, int],
                             clave_conocida: set[str]) -> list[dict]:
    por_nombre: dict[str, list[dict]] = defaultdict(list)
    for f in filas_fuente:
        por_nombre[f["nombre"]].append(f)

    out = []
    for nombre, filas in sorted(por_nombre.items()):
        ids_distintos = {f["auth_id"] for f in filas if f["auth_id"]}
        if len(ids_distintos) < 2:
            continue

        detalle_ids = []
        for f in sorted(filas, key=lambda x: x["auth_id"]):
            sid = f["auth_id"]
            en_corpus_mismo_nombre = sid in ids_por_nombre.get(nombre, set())
            otros_nombres = ids_reverso.get(sid, set()) - {nombre}
            detalle_ids.append(
                f"{sid} (SciVal: {f['n_documentos']} docs"
                + (f", ORCID {f['orcid']}" if f["orcid"] else "")
                + f"; corpus: {'SI, ' + str(pubs_por_id.get(sid, 0)) + ' pub.' if en_corpus_mismo_nombre else 'no bajo este nombre'}"
                + (f"; también aparece como: {' / '.join(sorted(otros_nombres))}" if otros_nombres else "")
                + ")"
            )

        out.append({
            "nombre_scopus": nombre,
            "n_ids": len(ids_distintos),
            "auth_ids": " | ".join(sorted(ids_distintos)),
            "ya_conocido_en_ambiguities": nombre in clave_conocida,
            "detalle": " || ".join(detalle_ids),
            "nota": ("Puede ser un perfil Scopus fragmentado (misma persona, dos "
                     "identificadores) o una homonimia — esta fuente no lo decide, "
                     "igual que la regla P-04 del proyecto (D-08)."),
            # Por defecto, pendiente: la decide una persona
            # (apply_scopus_author_decisions.py la actualiza, nunca este script).
            "resolucion": "PENDIENTE_REVISION_HUMANA",
            "nota_resolucion": "",
        })
    return out


# --------------------------------------------------------------------------- #
# 1b. Fragmentación visible sólo por ORCID cruzado — nombre distinto en cada
#     fuente, así que candidatos_multiples_id() (agrupa por nombre EXACTO
#     dentro de esta misma fuente) estructuralmente no puede verla. Caso real
#     que la motivó: "Fortuny, Esteban Fortuny" (Scopus Author Search,
#     Auth-ID 57203373183) comparte ORCID con "Fortuny E." (el corpus del
#     proyecto, Auth-ID 59254638800) — mismo ORCID, ningún nombre en común.
# --------------------------------------------------------------------------- #

def candidatos_fragmentacion_orcid(filas_fuente: list[dict], orcid_proyecto: dict[str, str],
                                   auth_ids_por_firma_map: dict[str, set[str]],
                                   nombres_ya_cubiertos: set[str] = frozenset()) -> list[dict]:
    """El mismo ORCID bajo un Scopus Author ID de esta fuente y bajo un Scopus
    Author ID DISTINTO ya asociado, en el corpus del proyecto, a una firma con
    ese mismo ORCID. Salida con las mismas columnas que candidatos_multiples_id
    para que viajen en la misma cola de revisión — es el mismo tipo de
    pregunta ("¿es un perfil Scopus fragmentado?"), sólo que la evidencia que
    lo trae es distinta.

    `nombres_ya_cubiertos` son los nombres que candidatos_multiples_id() ya
    reportó: cuando ese nombre tiene 2+ Auth-ID EN ESTA MISMA FUENTE, el cruce
    por ORCID contra el corpus casi siempre redescubre el mismo par —pasó con
    "Esis Villarroel, Ivette S." una vez que tuvo ORCID asignado— y duplicar
    la fila rompería la unicidad de `nombre_scopus` de la que depende
    apply_scopus_author_decisions.py para aplicar un veredicto."""
    firma_por_orcid = {orcid: firma for firma, orcid in orcid_proyecto.items() if orcid}

    out = []
    for f in filas_fuente:
        if not f["orcid"] or not f["auth_id"] or f["nombre"] in nombres_ya_cubiertos:
            continue
        firma = firma_por_orcid.get(f["orcid"])
        if not firma:
            continue
        ids_conocidos = auth_ids_por_firma_map.get(firma, set())
        if not ids_conocidos or f["auth_id"] in ids_conocidos:
            continue
        ids_todos = sorted(ids_conocidos | {f["auth_id"]})
        out.append({
            "nombre_scopus": f["nombre"],
            "n_ids": len(ids_todos),
            "auth_ids": " | ".join(ids_todos),
            "ya_conocido_en_ambiguities": False,
            "detalle": (f"{f['auth_id']} (Scopus Author Search: {f['n_documentos']} docs"
                        + (f", ORCID {f['orcid']}" if f["orcid"] else "") + ") || "
                        + " / ".join(sorted(ids_conocidos))
                        + f" (corpus del proyecto, bajo la firma '{firma}', mismo ORCID {f['orcid']})"),
            "nota": ("Detectado por convergencia de ORCID entre Scopus Author Search y el "
                     "corpus del proyecto — no por nombre repetido en esta fuente, a diferencia "
                     "de los demás candidatos de esta cola. Puede ser un perfil Scopus "
                     "fragmentado (misma persona, dos identificadores) o coincidencia de "
                     "ORCID — esta fuente no lo decide, igual que la regla P-04 del "
                     "proyecto (D-08)."),
            "resolucion": "PENDIENTE_REVISION_HUMANA",
            "nota_resolucion": "",
        })
    return out


# --------------------------------------------------------------------------- #
# 2. Contraste de ORCID
# --------------------------------------------------------------------------- #

def contraste_orcid(filas_fuente: list[dict], firmas_uft: set[str],
                     orcid_proyecto: dict[str, str]) -> list[dict]:
    out = []
    for f in filas_fuente:
        if not f["orcid"]:
            continue
        corta = firma_corta(f["nombre"])
        en_poblacion = corta in firmas_uft
        actual = orcid_proyecto.get(corta, "")
        if not en_poblacion:
            resolucion = "sin_firma_uft_en_el_proyecto"
        elif not actual:
            resolucion = "nuevo"
        elif actual == f["orcid"]:
            resolucion = "coincide"
        else:
            resolucion = "contradice"
        out.append({
            "nombre_scopus": f["nombre"],
            "firma_corta": corta,
            "auth_id": f["auth_id"],
            "orcid_scopus_author_search": f["orcid"],
            "en_poblacion_uft": en_poblacion,
            "orcid_ya_asignado_en_el_proyecto": actual,
            "resolucion": resolucion,
        })
    return out


# --------------------------------------------------------------------------- #

def _clave_conocida_p04() -> set[str]:
    if not AMBIGUEDADES.exists():
        return set()
    df = pd.read_csv(AMBIGUEDADES, dtype=str)
    p04 = df[df["tipo"] == "P-04_nombre_con_multiples_scopus_id"]
    return set(p04["clave"].dropna())


def _firmas_uft() -> set[str]:
    if not MATCHING_LOG.exists():
        return set()
    return set(pd.read_csv(MATCHING_LOG, dtype=str)["nombre_en_fuente"].dropna())


def _orcid_proyecto() -> dict[str, str]:
    if not AUTHORS_ORCID.exists():
        return {}
    df = pd.read_csv(AUTHORS_ORCID, dtype=str)
    return dict(zip(df["nombre_en_fuente"], df["orcid"]))


def _matching_log() -> pd.DataFrame:
    if not MATCHING_LOG.exists():
        return pd.DataFrame(columns=["eid", "posicion_autor", "nombre_en_fuente"])
    return pd.read_csv(MATCHING_LOG, dtype=str)


def run() -> tuple[list[dict], list[dict]]:
    filas_fuente = leer_fuente()
    scopus = pd.read_csv(RAW_SCOPUS, encoding=c.SOURCES["scopus_export"]["encoding"],
                          header=c.SOURCES["scopus_export"]["header_row"])
    ids_por_nombre = scopus_id_map(scopus)
    ids_reverso = ids_reverse_map(ids_por_nombre)
    pubs_por_id = publicaciones_por_id(scopus)
    orcid_proyecto = _orcid_proyecto()

    multiples_id = candidatos_multiples_id(
        filas_fuente, ids_por_nombre, ids_reverso, pubs_por_id, _clave_conocida_p04())
    fragmentacion = candidatos_fragmentacion_orcid(
        filas_fuente, orcid_proyecto, auth_ids_por_firma(scopus, _matching_log()),
        {r["nombre_scopus"] for r in multiples_id})
    orcid = contraste_orcid(filas_fuente, _firmas_uft(), orcid_proyecto)
    return multiples_id + fragmentacion, orcid


def _guardar(multiples_id: list[dict], orcid: list[dict]) -> None:
    c.write_internal(pd.DataFrame(multiples_id), "scopus_author_search_multiples_id.csv")
    c.write_internal(pd.DataFrame(orcid), "scopus_author_search_orcid.csv")

    nuevos = sum(1 for r in multiples_id if not r["ya_conocido_en_ambiguities"])
    por_orcid = sum(1 for r in multiples_id if "convergencia de ORCID" in r["nota"])
    print(f"candidatos de identidad fragmentada : {len(multiples_id)}"
          f" ({nuevos} nuevos, {len(multiples_id) - nuevos} ya conocidos en ambiguities_authors.csv;"
          f" {por_orcid} por convergencia de ORCID entre fuentes, "
          f"{len(multiples_id) - por_orcid} por nombre repetido en esta fuente)")

    por_res = defaultdict(int)
    for r in orcid:
        por_res[r["resolucion"]] += 1
    print(f"ORCID evaluados en Scopus Author Search: {len(orcid)}")
    for res in ("coincide", "contradice", "nuevo", "sin_firma_uft_en_el_proyecto"):
        print(f"  {res:32s}: {por_res.get(res, 0)}")


# --------------------------------------------------------------------------- #

def autotest() -> int:
    casos = []

    def caso(n, ok, obs=None):
        casos.append((n, ok, obs))

    caso("firma_corta: 'Apellido, Nombre Segundo' -> 'Apellido N.S.'",
         firma_corta("Ávalos-Allele, Daniela") == "Ávalos-Allele D.")
    caso("firma_corta: sin coma no revienta", firma_corta("Solo Apellido") == "Solo Apellido")

    scopus = pd.DataFrame({"Author full names": [
        "Pérez, Juan (57000000001); Gómez, Ana (57000000002)",
        "Pérez, Juan (57000000001)",
    ]})
    ids = scopus_id_map(scopus)
    caso("scopus_id_map agrupa por nombre completo",
         ids["Pérez, Juan"] == {"57000000001"} and ids["Gómez, Ana"] == {"57000000002"}, ids)

    rev = ids_reverse_map(ids)
    caso("ids_reverse_map invierte nombre<->id",
         rev["57000000001"] == {"Pérez, Juan"}, rev)

    pubs = publicaciones_por_id(scopus)
    caso("publicaciones_por_id cuenta 2 para el que aparece dos veces",
         pubs["57000000001"] == 2 and pubs["57000000002"] == 1, pubs)

    # Caso completo: un nombre con 2 Auth-ID en la fuente nueva, uno de ellos
    # visible en el corpus bajo OTRO nombre (mismo patrón que "Caffarena, Paula").
    scopus2 = pd.DataFrame({"Author full names": [
        "Soto, Marta (57111111111)",
        "Marta Soto, Barrera (57222222222)",
    ]})
    ids2 = scopus_id_map(scopus2)
    rev2 = ids_reverse_map(ids2)
    pubs2 = publicaciones_por_id(scopus2)
    filas_fuente = [
        {"nombre": "Soto, Marta", "auth_id": "57111111111", "n_documentos": "3", "areas": [], "orcid": ""},
        {"nombre": "Soto, Marta", "auth_id": "57222222222", "n_documentos": "1", "areas": [], "orcid": ""},
        {"nombre": "Nadie, Solo", "auth_id": "57999999999", "n_documentos": "1", "areas": [], "orcid": ""},
    ]
    cand = candidatos_multiples_id(filas_fuente, ids2, rev2, pubs2, set())
    caso("candidatos_multiples_id: sólo agrupa nombres con 2+ ID distintos",
         len(cand) == 1 and cand[0]["nombre_scopus"] == "Soto, Marta", cand)
    caso("detecta el ID que aparece bajo otro nombre en el corpus",
         "Marta Soto, Barrera" in cand[0]["detalle"], cand)
    caso("nombre con un solo ID no se reporta", all(c2["nombre_scopus"] != "Nadie, Solo" for c2 in cand))

    cand_conocido = candidatos_multiples_id(filas_fuente, ids2, rev2, pubs2, {"Soto, Marta"})
    caso("ya_conocido_en_ambiguities se marca cuando la clave ya existe",
         cand_conocido[0]["ya_conocido_en_ambiguities"] is True)

    # auth_ids_por_firma: por posición de autor, no por nombre solo — un EID
    # con dos coautores UFT no puede mezclar el ID de uno con la firma del
    # otro (caso real: "Bustos Arriagada, Edson" daba resultados cruzados
    # hasta que se cruzó por posición, 2026-09-03).
    scopus3 = pd.DataFrame({
        "EID": ["e1", "e1", "e2"],
        "Author full names": [
            "Uno, A. (111); Dos, B. (222)",
            "Uno, A. (111); Dos, B. (222)",
            "Tres, C. (333)",
        ],
    })
    ml3 = pd.DataFrame([
        {"eid": "e1", "posicion_autor": "1", "nombre_en_fuente": "Uno A."},
        {"eid": "e1", "posicion_autor": "2", "nombre_en_fuente": "Dos B."},
        {"eid": "e2", "posicion_autor": "1", "nombre_en_fuente": "Tres C."},
    ])
    aidf = auth_ids_por_firma(scopus3, ml3)
    caso("auth_ids_por_firma no mezcla coautores del mismo EID",
         aidf["Uno A."] == {"111"} and aidf["Dos B."] == {"222"} and aidf["Tres C."] == {"333"}, aidf)

    # candidatos_fragmentacion_orcid: mismo patrón que motivó su existencia
    # ("Fortuny, Esteban Fortuny" en Scopus Author Search comparte ORCID con
    # "Fortuny E." del corpus, bajo un Scopus Author ID distinto).
    filas_frag = [
        {"nombre": "Cuatro, D. Cuatro", "auth_id": "444", "n_documentos": "2", "areas": [], "orcid": "0000-0001-1111-222X"},
        {"nombre": "Cinco, E.", "auth_id": "555", "n_documentos": "1", "areas": [], "orcid": ""},
    ]
    orcid_proy3 = {"Cuatro D.": "0000-0001-1111-222X"}
    aidf3 = {"Cuatro D.": {"999"}}
    frag = candidatos_fragmentacion_orcid(filas_frag, orcid_proy3, aidf3)
    caso("detecta el mismo ORCID bajo un Auth-ID distinto al ya conocido",
         len(frag) == 1 and frag[0]["nombre_scopus"] == "Cuatro, D. Cuatro"
         and frag[0]["auth_ids"] == "444 | 999", frag)
    caso("candidato de fragmentación por ORCID no se marca ya_conocido_en_ambiguities",
         frag[0]["ya_conocido_en_ambiguities"] is False, frag)

    caso("mismo Auth-ID ya conocido no se reporta (no es fragmentación)",
         len(candidatos_fragmentacion_orcid(
             [{"nombre": "Cuatro, D.", "auth_id": "999", "n_documentos": "1", "areas": [], "orcid": "0000-0001-1111-222X"}],
             orcid_proy3, aidf3)) == 0)
    caso("ORCID sin firma ya conocida en el proyecto no se reporta",
         len(candidatos_fragmentacion_orcid(
             [{"nombre": "Nadie, N.", "auth_id": "1", "n_documentos": "1", "areas": [], "orcid": "0000-0009-9999-999X"}],
             orcid_proy3, aidf3)) == 0)
    caso("firma ya conocida sin ningún Auth-ID propio en el corpus no se reporta (sin evidencia)",
         len(candidatos_fragmentacion_orcid(filas_frag, orcid_proy3, {})) == 0)
    caso("un nombre que candidatos_multiples_id ya reportó no se duplica aquí",
         len(candidatos_fragmentacion_orcid(filas_frag, orcid_proy3, aidf3,
                                            {"Cuatro, D. Cuatro"})) == 0)

    # Contraste de ORCID
    orcid_rows = [
        {"nombre": "Pérez, Juan", "auth_id": "1", "n_documentos": "1", "areas": [], "orcid": "0000-0001-2222-333X"},
        {"nombre": "Gómez, Ana", "auth_id": "2", "n_documentos": "1", "areas": [], "orcid": "0000-0001-4444-555X"},
        {"nombre": "Nadie, Solo", "auth_id": "3", "n_documentos": "1", "areas": [], "orcid": "0000-0001-6666-777X"},
        {"nombre": "Sin ORCID, X", "auth_id": "4", "n_documentos": "1", "areas": [], "orcid": ""},
    ]
    firmas_uft = {"Pérez J.", "Gómez A."}
    orcid_proy = {"Pérez J.": "0000-0001-2222-333X", "Gómez A.": "0000-0009-9999-999X"}
    contraste = contraste_orcid(orcid_rows, firmas_uft, orcid_proy)
    por_nombre = {r["nombre_scopus"]: r for r in contraste}
    caso("ORCID igual -> coincide", por_nombre["Pérez, Juan"]["resolucion"] == "coincide")
    caso("ORCID distinto -> contradice", por_nombre["Gómez, Ana"]["resolucion"] == "contradice")
    caso("firma fuera de la población UFT -> sin_firma_uft_en_el_proyecto",
         por_nombre["Nadie, Solo"]["resolucion"] == "sin_firma_uft_en_el_proyecto")
    caso("fila sin ORCID no se reporta", "Sin ORCID, X" not in por_nombre)
    caso("firma en población pero sin ORCID todavía -> nuevo",
         contraste_orcid(
             [{"nombre": "Gómez, Ana", "auth_id": "2", "n_documentos": "1", "areas": [], "orcid": "0000-0001-4444-555X"}],
             {"Gómez A."}, {})[0]["resolucion"] == "nuevo")

    fallos = [n for n, ok, _ in casos if not ok]
    for n, ok, obs in casos:
        marca = "OK  " if ok else "FALLA"
        print(f"  {marca} {n}" + (f"  ({obs})" if not ok and obs is not None else ""))
    print(f"\n{len(casos) - len(fallos)}/{len(casos)} comprobaciones")
    return 1 if fallos else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--test", action="store_true", help="valida la lógica, sin leer los archivos reales")
    args = ap.parse_args()

    if args.test:
        return autotest()

    if not FUENTE.exists():
        sys.exit(f"Falta {FUENTE.relative_to(c.ROOT)}.")

    multiples_id, orcid = run()
    _guardar(multiples_id, orcid)
    print("\nOK · internal/scopus_author_search_multiples_id.csv")
    print("     internal/scopus_author_search_orcid.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
