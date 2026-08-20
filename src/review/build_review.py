"""Genera la herramienta de revisión humana de identidad de autor.

QUÉ RESUELVE
    Las colas `internal/ambiguities_authors.csv`, `identity_candidates.csv` y
    `orcid_conflicts.csv` declaran ambigüedades pero no las resuelven: la
    decisión «estas dos firmas son la misma persona» es una afirmación sobre
    alguien real y sólo la puede tomar una persona (decisión `D-08`).

    Revisarlas a mano sobre los CSV es impracticable: para cada grupo hay que
    cruzar cuatro archivos distintos. Esta herramienta hace ese cruce y presenta
    cada caso con toda su evidencia junta.

QUÉ NO HACE
    No decide. No propone una respuesta por defecto. No fusiona nada. Emite un
    archivo de decisiones que una persona ha tomado, con su fecha.

LA EVIDENCIA QUE APORTA
    Además de lo que ya estaba en las colas, calcula dos señales que ningún
    archivo tenía y que son las que de verdad deciden un caso:

    - **Coautoría directa**: si dos firmas aparecen en la MISMA publicación, son
      casi con seguridad personas distintas. Nadie firma dos veces el mismo
      artículo. Es el descarte más limpio que existe.
    - **Solapamiento de años y de coautores**: dos firmas que nunca coinciden en
      el tiempo y no comparten a nadie son un perfil fragmentado más probable
      que dos personas homónimas.

CAPA
    Interna. La salida vive en `internal/` y nunca entra en `dist/`: el
    ensamblado sólo copia `web/` y `data/processed/`.

Uso:
    python3 src/review/build_review.py

Salida:
    internal/revision_identidad.html    página autónoma, se abre en el navegador
"""

from __future__ import annotations

import html
import json
import re
import sys
import urllib.parse
from collections import defaultdict
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

import decisiones as D
import equivalencia_ortografica as EQ

ROOT = Path(__file__).resolve().parents[2]
INTERNAL = ROOT / "internal"
INTERIM = ROOT / "data" / "interim"
ENRICHED = ROOT / "data" / "enriched"


def cargar() -> dict:
    """Lee lo que existe y declara lo que falta, en vez de reventar."""
    faltan = []

    def leer(path: Path, nombre: str) -> pd.DataFrame | None:
        if not path.exists():
            faltan.append(f"{nombre} ({path.relative_to(ROOT)})")
            return None
        return pd.read_csv(path, dtype=str)

    d = {
        "amb": leer(INTERNAL / "ambiguities_authors.csv", "cola de ambigüedades"),
        "cand": leer(INTERNAL / "identity_candidates.csv", "candidatos por ORCID"),
        "conf": leer(INTERNAL / "orcid_conflicts.csv", "conflictos de ORCID"),
        "master": leer(INTERIM / "authors_master_draft.csv", "borrador de tabla maestra"),
        "log": leer(INTERNAL / "matching_log.csv", "log de emparejamiento"),
        "orcid": leer(ENRICHED / "authors_orcid.csv", "ORCID enriquecido"),
        # Opcional: sólo existe si se ha corrido `src/enrich/orcid_api.py`.
        # Sin él la herramienta funciona igual, con una señal menos.
        "verif": leer(ENRICHED / "orcid_verificacion.csv", "verificación contra ORCID"),
        # Opcionales también: los generan los conectores de ampliación. Sin
        # ellos la herramienta funciona igual, con dos colas menos.
        "afil": leer(INTERNAL / "orcid_candidatos_afiliacion.csv",
                     "candidatos de ORCID por afiliación"),
        "desac": leer(INTERNAL / "orcid_desacuerdos.csv",
                      "desacuerdos entre Crossref y el registro de ORCID"),
        # Para enseñar de qué publicaciones se habla, con su DOI: verificar un
        # ORCID a mano es abrir el registro del titular y comparar obras, y sin
        # los títulos delante eso obliga a cruzar tres archivos.
        "uni": leer(INTERIM / "publications_universe.csv", "universo de publicaciones"),
    }
    # Lo que YA se decidió. Sin esto la página vuelve a preguntar en cada
    # corrida todo lo que alguien ya resolvió —52 de los 114 casos actuales—,
    # y una cola de pendientes que incluye lo resuelto no es una cola de
    # pendientes. El navegador guarda su propio avance, pero sólo en la máquina
    # donde se trabajó: el registro que perdura es este archivo.
    dpath = INTERNAL / "identity_decisions.csv"
    d["dec"] = D.leer(dpath) if dpath.exists() else None
    if d["master"] is None or d["log"] is None:
        sys.exit(
            "Faltan insumos que genera la auditoría:\n  - " + "\n  - ".join(faltan) +
            "\n\nEjecute primero:  python3 src/audit/run_all.py")
    return d


def perfiles(master: pd.DataFrame, log: pd.DataFrame, orcid: pd.DataFrame | None,
             verif: pd.DataFrame | None = None, uni: pd.DataFrame | None = None) -> dict:
    """Ficha de evidencia por forma de firma."""
    # Veredicto de la verificación contra el registro público, si se ejecutó.
    ver = {}
    if verif is not None:
        ver = {r["nombre_en_fuente"]: (r["veredicto"], r.get("dois_coincidentes"),
                                      r.get("afiliacion_institucional_declarada"))
               for _, r in verif.iterrows()}
    orc = {}
    if orcid is not None:
        orc = {r["nombre_en_fuente"]: (r["orcid"], r.get("confianza"), r.get("fuente"))
               for _, r in orcid.iterrows()}
    # eid -> (año, título, DOI). El DOI puede faltar: 2,3 % del corpus no tiene.
    obras = {}
    if uni is not None:
        obras = {r["eid"]: (r.get("anio"), r.get("titulo"), r.get("doi"))
                 for _, r in uni.iterrows()}

    eids_por_firma = log.groupby("nombre_en_fuente")["eid"].apply(set).to_dict()
    firmas_por_eid = log.groupby("eid")["nombre_en_fuente"].apply(set).to_dict()

    out = {}
    for _, r in master.iterrows():
        n = r["nombre_en_fuente"]
        eids = eids_por_firma.get(n, set())
        # Coautores: otras firmas institucionales que comparten publicación.
        coaut = set()
        for e in eids:
            coaut |= firmas_por_eid.get(e, set())
        coaut.discard(n)
        o = orc.get(n, (None, None, None))
        v = ver.get(n)
        out[n] = {
            "nombre": n,
            "n_pub": int(r["n_publicaciones"]),
            "anios": f"{r['anio_min']}–{r['anio_max']}",
            "anio_min": int(r["anio_min"]), "anio_max": int(r["anio_max"]),
            "unidades": [u for u in str(r["unidades_academicas"]).split("|") if u],
            "scopus": [s for s in str(r["scopus_author_ids"] or "").split("|") if s and s != "nan"],
            "orcid": o[0], "orcid_confianza": o[1], "orcid_fuente": o[2],
            "orcid_veredicto": v[0] if v else None,
            "orcid_dois_coincidentes": v[1] if v else None,
            "orcid_afiliacion_ok": (str(v[2]).lower() == "true") if v else None,
            "eids": sorted(eids), "coautores": sorted(coaut),
            "obras": [(e,) + obras.get(e, (None, None, None)) for e in sorted(eids)],
        }
    return out


def _evidencia_orcid(firmas: list[str], orcid: str) -> str:
    """Con qué respaldo entró ese ORCID en cada firma.

    La cola decía que varias firmas comparten identificador y ahí se acababa.
    Pero no todas las asignaciones pesan igual: una declarada por el titular en
    su registro no es lo mismo que una deducida de un DOI, y una respaldada por
    cuatro publicaciones no es lo mismo que una por una sola. Sin eso, quien
    revisa tenía que ir a buscar el CSV para decidir; con eso, decide leyendo.

    Importa además por una razón concreta de este corpus: el vínculo con
    Crossref se hace por apellido e inicial DENTRO de una publicación. Cuando
    dos firmas con apellidos distintos comparten identificador, la coincidencia
    no puede venir del nombre —tuvo que venir del identificador que el autor
    depositó—, y eso es evidencia de otra naturaleza.
    """
    try:
        o = pd.read_csv(ROOT / "data" / "enriched" / "authors_orcid.csv", dtype=str)
    except Exception:
        return ""
    filas = o[(o.orcid == orcid) & (o.nombre_en_fuente.isin(firmas))]
    if filas.empty:
        return ""
    partes = [f"{r['nombre_en_fuente']} ({r['fuente']}, confianza {r['confianza']}, "
              f"{r['publicaciones_de_respaldo']} pub.)" for _, r in filas.iterrows()]
    return "Respaldo de cada asignación: " + " · ".join(partes) + "."


def cruces(a: dict, b: dict) -> dict:
    """Las tres señales que deciden un caso, calculadas entre dos firmas."""
    comunes = set(a["eids"]) & set(b["eids"])
    coaut = set(a["coautores"]) & set(b["coautores"])
    solapan = not (a["anio_max"] < b["anio_min"] or b["anio_max"] < a["anio_min"])
    return {
        # Firmar dos veces el mismo artículo no ocurre: si comparten publicación,
        # son personas distintas. Es el descarte más limpio que existe.
        "publicaciones_comunes": len(comunes),
        "coautores_comunes": len(coaut - {a["nombre"], b["nombre"]}),
        "anios_solapan": solapan,
        "misma_unidad": bool(set(a["unidades"]) & set(b["unidades"])
                             - {"No determinada"}),
        "mismo_orcid": bool(a["orcid"] and a["orcid"] == b["orcid"]),
        # Que ambas firmas tengan el ORCID confirmado contra el registro es la
        # evidencia más fuerte disponible: ya no es una inferencia por apellido.
        "orcid_verificado": (a.get("orcid_veredicto") == "confirmada"
                             and b.get("orcid_veredicto") == "confirmada"),
        "mismo_scopus": bool(set(a["scopus"]) & set(b["scopus"])),
    }


def umbral_interpretable() -> int:
    """Desde cuántas publicaciones vale la pena buscar un ORCID a mano.

    No es un número nuevo: es `n_minimo_interpretable`, el umbral que este
    proyecto ya usa para decidir cuándo un indicador individual dice algo. Una
    firma por debajo de él tiene una o dos publicaciones y su búsqueda manual
    en el registro devuelve homónimos indistinguibles; por encima, hay obra
    suficiente para reconocer a la persona. Inventar aquí un segundo umbral
    sería añadir un parámetro que nadie podría justificar frente al primero.
    """
    cfg = yaml.safe_load((ROOT / "config" / "indicators.yml").read_text(encoding="utf-8"))
    return int(cfg["reglas_transversales"]["n_minimo_interpretable"])


def casos(d: dict, perf: dict) -> list[dict]:
    """Un caso por grupo a revisar, con su evidencia ya cruzada."""
    out = []

    def firmas_de(nombres):
        return [perf[n] for n in nombres if n in perf]

    # ── Firmas que comparten ORCID (D-44). La evidencia más fuerte, primero.
    if d["cand"] is not None:
        for _, r in d["cand"].iterrows():
            fs = firmas_de(r["firmas"].split(" | "))
            if len(fs) < 2:
                continue

            # Igual que en la cola de variantes: lo que sólo se diferencia en
            # diacríticos o separadores no se pregunta, porque no es un juicio.
            # Aquí importa más todavía: un caso cuyas tres formas son la misma
            # cadena —«Henriquez-Olguin C.», «Henriquez-Olguín C.»,
            # «Henríquez-Olguín C.»— no plantea ninguna duda de identidad, y
            # ocupaba un puesto en la cola de prioridad 1.
            clases = EQ.subgrupos([f["nombre"] for f in fs])
            por_nombre = {f["nombre"]: f for f in fs}
            rep = [por_nombre[c[0]] for c in clases]
            agrupadas = [c for c in clases if len(c) > 1]
            if len(rep) < 2:
                continue

            ctx = ("El apellido no las agrupa: este hallazgo sólo lo aporta "
                   "el identificador persistente."
                   if r.get("hallazgo_nuevo") == "True" else
                   "El apellido también las agrupa.")
            if agrupadas:
                detalle = " · ".join(" = ".join(v) for v in agrupadas)
                ctx += f" Ya unidas por equivalencia ortográfica: {detalle}."
            ctx += " " + _evidencia_orcid([f["nombre"] for f in rep], r["orcid"])

            out.append({
                "id": f"orcid-{r['orcid']}", "cola": "ORCID compartido",
                "prioridad": 1,
                "titulo": f"{len(rep)} firmas comparten {r['orcid']}",
                "contexto": ctx,
                "firmas": rep, "cruces": cruces(rep[0], rep[1]) if len(rep) == 2 else None,
            })

    # ── Una firma con más de un ORCID.
    if d["conf"] is not None:
        for _, r in d["conf"].iterrows():
            f = perf.get(r["nombre_en_fuente"])
            if not f:
                continue
            out.append({
                "id": f"conf-{r['nombre_en_fuente']}", "cola": "ORCID en conflicto",
                "prioridad": 1,
                "titulo": f"{r['nombre_en_fuente']} aparece con {len(r['detalle'].split('|'))} ORCID",
                "contexto": ("Una misma forma de firma recibe identificadores distintos "
                             "según la publicación: o son dos personas que firman igual, "
                             "o una de las asignaciones es incorrecta. ORCID: "
                             + r["detalle"].replace("|", " · ")),
                "firmas": [f], "cruces": None,
            })

    # ── Crossref y el registro de ORCID no coinciden (V2-03). Uno de los dos
    #    está equivocado, y cuál no se decide mirando los nombres.
    if d["desac"] is not None:
        for _, r in d["desac"].iterrows():
            f = perf.get(r["nombre_en_fuente"])
            if not f:
                continue
            out.append({
                "id": f"desac-{r['nombre_en_fuente']}", "cola": "Fuentes en desacuerdo",
                "prioridad": 1,
                "titulo": f"{r['nombre_en_fuente']}: dos fuentes, dos ORCID",
                "contexto": f"{r['detalle']}. Identificadores: "
                            + str(r["orcid"]).replace("|", " · ")
                            + ". La asignación vigente NO se ha modificado.",
                "firmas": [f], "cruces": None,
            })

    # ── Candidatos por afiliación (V2-04). Van DESPUÉS de todo lo anclado en
    #    una publicación compartida, porque su evidencia es más débil: coincide
    #    el nombre y la institución, y nada más.
    if d["afil"] is not None:
        af = d["afil"].copy()
        af["tf"] = af["titulares_que_coinciden_con_la_firma"].astype(int)
        af["ft"] = af["firmas_que_coinciden_con_el_titular"].astype(int)

        # Varias firmas apuntando al mismo titular: eso SÍ es una pista fuerte
        # de identidad, y por eso sube de prioridad respecto del resto.
        for orcid, g in af[af.ft > 1].groupby("orcid"):
            fs = firmas_de(sorted(set(g["nombre_en_fuente"])))
            if len(fs) < 2:
                continue
            out.append({
                "id": f"afil-multi-{orcid}", "cola": "Mismo ORCID por afiliación",
                "prioridad": 1,
                "titulo": f"{len(fs)} firmas apuntan a {orcid}",
                "contexto": "Varias formas de firma coinciden en nombre con el mismo "
                            f"titular, que declara la institución: «{g['nombre_declarado_en_orcid'].iloc[0]}». "
                            "Sugiere que son la misma persona. NO se ha fusionado nada.",
                "firmas": fs, "cruces": cruces(fs[0], fs[1]) if len(fs) == 2 else None,
            })

        for _, r in af[(af.tf == 1) & (af.ft == 1)].iterrows():
            f = perf.get(r["nombre_en_fuente"])
            if not f:
                continue
            out.append({
                "id": f"afil-{r['nombre_en_fuente']}", "cola": "Candidato por afiliación",
                "prioridad": 4,
                "titulo": f"{r['nombre_en_fuente']} → {r['orcid']}?",
                "contexto": "Este titular declara la institución en su registro de ORCID y "
                            f"se llama «{r['nombre_declarado_en_orcid']}». Coincidencia única "
                            "en ambos sentidos. No hay ninguna publicación compartida que "
                            "lo respalde: por eso es un candidato y no una asignación.",
                "firmas": [f], "cruces": None,
            })

        for _, r in af[af.tf > 1].iterrows():
            f = perf.get(r["nombre_en_fuente"])
            if not f:
                continue
            out.append({
                "id": f"afil-amb-{r['nombre_en_fuente']}-{r['orcid']}",
                "cola": "Candidato por afiliación (ambiguo)", "prioridad": 4,
                "titulo": f"{r['nombre_en_fuente']}: {r['tf']} titulares posibles",
                "contexto": f"«{r['nombre_declarado_en_orcid']}» es uno de {r['tf']} titulares "
                            "que declaran la institución y coinciden en apellido e inicial "
                            "con esta firma. El nombre no basta para elegir.",
                "firmas": [f], "cruces": None,
            })

    # ── Asignaciones YA PUBLICADAS cuya evidencia no las respalda.
    #
    # Estas tres colas no existían y son la parte del problema que nadie estaba
    # mirando: las anteriores preguntan a quién asignar un ORCID que aún no se
    # ha asignado, y éstas preguntan por los que el sitio YA publica en una
    # ficha con nombre y apellido. Una asignación equivocada publicada es peor
    # que una ausencia declarada, porque atribuye a una persona la obra de otra.
    umbral = umbral_interpretable()
    for n, f in sorted(perf.items()):
        v, o = f.get("orcid_veredicto"), f.get("orcid")

        if o and v in ("sin_coincidencia", "sin_registro"):
            detalle = ("El titular declara obras en su registro y NINGUNA "
                       "coincide con las atribuidas a esta firma."
                       if v == "sin_coincidencia" else
                       "El identificador no existe o su registro no es público.")
            out.append({
                "id": f"ver-{n}", "cola": "ORCID sin confirmar", "prioridad": 1,
                "titulo": f"{n} → {o}: ¿es suyo?",
                "contexto": f"{detalle} La ficha pública de esta firma lleva hoy la "
                            "marca «sin confirmar». Abra el registro del titular y "
                            "compárelo con las publicaciones de abajo.",
                "firmas": [f], "cruces": None,
            })

        elif o and v == "no_verificable":
            out.append({
                "id": f"noverif-{n}", "cola": "ORCID no verificable", "prioridad": 5,
                "titulo": f"{n} → {o}: sin nada contra qué contrastar",
                "contexto": "El titular no declara ninguna obra con DOI en su registro, "
                            "de modo que la comprobación automática no puede decir ni "
                            "que sí ni que no. Queda su nombre, su afiliación declarada "
                            "y el juicio de quien mire.",
                "firmas": [f], "cruces": None,
            })

        elif not o and f["n_pub"] >= umbral:
            out.append({
                "id": f"sinorcid-{n}", "cola": "Firma sin ORCID", "prioridad": 6,
                "titulo": f"{n}: {f['n_pub']} publicaciones y ningún ORCID",
                "contexto": "Ninguna de las tres vías automáticas encontró identificador "
                            f"para esta firma. Con {f['n_pub']} publicaciones es de las "
                            "pocas que una búsqueda manual en el registro puede resolver. "
                            "Si lo encuentra, tecléelo: se comprueba el dígito de control "
                            "antes de aplicarlo.",
                "firmas": [f], "cruces": None,
            })

    if d["amb"] is None:
        return sorted(out, key=lambda c: (c["prioridad"], c["titulo"]))

    # ── Variantes de nombre (P-03), agrupadas por clave de apellido.
    p03 = d["amb"][d["amb"].tipo.str.startswith("P-03")]
    for clave, g in p03.groupby("clave"):
        fs = firmas_de(sorted(set(g["nombre_en_fuente"])))
        if len(fs) < 2:
            continue

        # LO ORTOGRÁFICO NO SE PREGUNTA. Las formas que sólo se diferencian en
        # diacríticos o separadores son la misma cadena, así que se colapsan
        # antes de encolar: preguntarle a una persona si «Henriquez-Olguin C.»
        # y «Henríquez-Olguín C.» son la misma gasta su atención en algo que no
        # es un juicio, y la atención es justo el recurso escaso de esta cola.
        clases = EQ.subgrupos([f["nombre"] for f in fs])
        por_nombre = {f["nombre"]: f for f in fs}
        rep = [por_nombre[c[0]] for c in clases]
        agrupadas = {c[0]: c for c in clases if len(c) > 1}

        # Si al colapsar queda una sola forma, no queda nada que decidir.
        if len(rep) < 2:
            continue

        ctx = "Mismo apellido normalizado. Agrupadas por heurística, sin evidencia de identidad."
        if agrupadas:
            detalle = " · ".join(" = ".join(v) for v in agrupadas.values())
            ctx += (f" Ya unidas por equivalencia ortográfica, no hace falta"
                    f" decidirlas: {detalle}.")
        out.append({
            "id": f"p03-{clave}", "cola": "Variantes de nombre", "prioridad": 2,
            "titulo": " · ".join(f["nombre"] for f in rep),
            "contexto": ctx,
            "firmas": rep, "cruces": cruces(rep[0], rep[1]) if len(rep) == 2 else None,
        })

    # ── Firmas sin forma de persona (E-09): fragmentos de cadena de afiliación.
    #
    # Va primero de todo porque no pregunta lo mismo que las demás. El resto de
    # colas pregunta «¿son la misma persona?»; ésta pregunta si hay alguna
    # persona. Y mientras no se responda, cada una tiene ficha pública y deja a
    # su publicación sin autoría UFT nombrada.
    e09 = d["amb"][d["amb"].tipo.str.startswith("E-09")]
    for _, r in e09.iterrows():
        f = perf.get(r["nombre_en_fuente"])
        out.append({
            "id": f"e09-{r['clave']}", "cola": "Firma sin forma de persona",
            "prioridad": 0, "titulo": r["clave"],
            "contexto": (f"{r['consecuencia']}. Señales: "
                         + r["detalle"].replace(" · ", "; ")),
            # El vocabulario de esta cola —«¿hay aquí una persona?»— lo declara
            # `decisiones.COLAS`: preguntar «¿son la misma?» sobre una firma
            # sola no significa nada.
            "firmas": [f] if f else [], "cruces": None,
        })

    # ── Un nombre con varios Scopus Author ID (P-04): perfil fragmentado u homonimia.
    p04 = d["amb"][d["amb"].tipo.str.startswith("P-04")]
    for _, r in p04.iterrows():
        f = perf.get(r["nombre_en_fuente"])
        # La auditoría ya midió dos cosas sobre este caso. Se usan para ordenar
        # la cola y para decir qué lecturas siguen en pie, nunca para decidir.
        uft = str(r.get("en_poblacion_uft", "True")) == "True"
        coo = int(float(r.get("coocurren_en_publicaciones") or 0))

        ctx = ("Un mismo nombre completo con varios identificadores de Scopus: "
               "perfil fragmentado en la fuente, u homonimia. IDs: "
               + r["detalle"].replace("|", " · "))
        if coo:
            ctx += (f". Los dos identificadores firman {coo} publicación(es) EN COMÚN, "
                    "así que «perfil fragmentado» queda descartado: la fuente no puede "
                    "haber repartido entre dos identificadores los trabajos de una "
                    "persona dentro de un mismo trabajo. Queda decidir entre homonimia "
                    "y error de la fuente")
        if not uft:
            ctx += (". FUERA DE LA POBLACIÓN UFT: esta firma no aparece en el log de "
                    "matching, así que no tiene ficha, no cuenta en «autores UFT "
                    "distintos» y no entraría en la red de coautoría. La ambigüedad "
                    "es real y por eso se declara, pero no afecta a ninguna cifra "
                    "publicada")

        out.append({
            # Prioridad 3 mientras toca a la población que el informe describe;
            # 5 cuando no. No se oculta ni se da por resuelto: se ordena. Diez de
            # los veinte casos son coautores externos, y mezclarlos con los diez
            # que sí son UFT hacía la cola el doble de larga sin ningún efecto
            # sobre el informe.
            "id": f"p04-{r['clave']}", "cola": "Varios Scopus ID",
            "prioridad": 3 if uft else 5,
            "titulo": r["clave"],
            "contexto": ctx,
            "firmas": [f] if f else [], "cruces": None,
        })

    return sorted(out, key=lambda c: (c["prioridad"], c["titulo"]))


def sembrar(cs: list[dict], dec: pd.DataFrame | None) -> tuple[int, list[str]]:
    """Marca cada caso con lo que una persona ya decidió, si lo decidió.

    POR QUÉ HACE FALTA
        La cola se reconstruye en cada corrida desde la auditoría, que se
        calcula sobre el log y no sabe nada de revisiones. Sin esto, `make
        revision` volvía a preguntar los 52 casos ya resueltos como si nadie los
        hubiera mirado, y quien abría la página veía «0 de 141 resueltos».

        El navegador guarda el avance en `localStorage`, pero eso vive en una
        máquina y se pierde al limpiar el navegador. El registro que perdura es
        `internal/identity_decisions.csv`, que está en el repositorio.

    QUÉ DEVUELVE
        Cuántos casos venían decididos, y los `caso_id` del CSV que ya no
        corresponden a ningún caso vivo. Esos huérfanos importan: son decisiones
        que se tomaron y que hoy no se aplicarían a nada —porque la firma se
        consolidó, o porque la cola cambió de nombre—, y callarlos sería perder
        trabajo humano en silencio.
    """
    if dec is None:
        return 0, []
    previas = {}
    for _, r in dec.iterrows():
        v = str(r.get("veredicto") or "")
        if v and v != "pendiente":
            previas[str(r["caso_id"])] = {
                "veredicto": v, "nota": str(r.get("nota") or ""),
                "fecha": str(r.get("fecha") or ""),
                "orcid": str(r.get("orcid_propuesto") or ""),
            }
    n = 0
    for c in cs:
        if c["id"] in previas:
            c["previa"] = previas[c["id"]]
            n += 1
    return n, sorted(set(previas) - {c["id"] for c in cs})


# ─────────────────────────────────────────────────────────────── plantilla

CSS = """
:root{--plano:#f1f5f6;--sup:#fff;--sup2:#eaf1f2;--tinta:#10222b;--tinta2:#4a5f68;
--tinta3:#5a6b71;--linea:#dbe6e8;--marca:#22577A;--accion:#1a6d78;--viva:#38A3A5;
--si:#2fa36b;--no:#cc3f5c;--duda:#d4a017;--radio:6px}
*{box-sizing:border-box}
body{margin:0;font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
background:var(--plano);color:var(--tinta)}
header{background:var(--marca);color:#fff;padding:1.1rem 0;border-bottom:2px solid var(--viva)}
.c{max-width:1100px;margin:0 auto;padding:0 1.5rem}
h1{margin:0;font-size:1.15rem;font-weight:650}
header p{margin:.3rem 0 0;font-size:.82rem;color:#c7f9cc}
.barra{position:sticky;top:0;z-index:10;background:var(--sup);border-bottom:1px solid var(--linea);
padding:.7rem 0;font-size:.85rem}
.barra .c{display:flex;gap:1rem;align-items:center;flex-wrap:wrap}
.avance{font-variant-numeric:tabular-nums}
.avance b{color:var(--marca)}
select,button{font:inherit;font-size:.85rem;border-radius:4px;border:1px solid #bccdd2;
background:var(--sup);color:var(--tinta);padding:.35rem .6rem;cursor:pointer}
button.pri{background:var(--marca);color:#fff;border-color:var(--marca);font-weight:600}
main{padding:1.5rem 0 4rem}
.caso{background:var(--sup);border:1px solid var(--linea);border-radius:var(--radio);
padding:1.1rem 1.25rem;margin-bottom:1rem}
.caso[data-decidido="1"]{opacity:.5}
.caso h2{margin:0 0 .2rem;font-size:1.02rem}
.cola{font-size:.68rem;text-transform:uppercase;letter-spacing:.08em;font-weight:700;
color:var(--tinta3);background:var(--sup2);border:1px solid var(--linea);
border-radius:999px;padding:.1rem .5rem;display:inline-block;margin-bottom:.4rem}
.ctx{font-size:.84rem;color:var(--tinta2);margin:.3rem 0 .9rem}
table{border-collapse:collapse;width:100%;font-size:.84rem;margin-bottom:.8rem}
th,td{text-align:left;padding:.4rem .55rem;border-bottom:1px solid var(--linea);vertical-align:top}
th{background:var(--sup2);font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;
color:var(--tinta2);font-weight:650}
td.n{text-align:right;font-variant-numeric:tabular-nums}
.mono{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.92em}
.senales{display:flex;flex-wrap:wrap;gap:.4rem;margin-bottom:.9rem}
.s{font-size:.78rem;border-radius:999px;padding:.15rem .6rem;border:1px solid}
.s.fuerte-no{background:#fdeaed;border-color:var(--no);color:#8a1f33}
.s.fuerte-si{background:#e8f6ef;border-color:var(--si);color:#155e3c}
.s.neutra{background:var(--sup2);border-color:var(--linea);color:var(--tinta2)}
.dec{display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;
border-top:1px solid var(--linea);padding-top:.8rem}
.dec button{border-width:1.5px}
.dec button[aria-pressed="true"][data-v="misma"],
.dec button[aria-pressed="true"][data-v="es_persona"]{background:var(--si);color:#fff;border-color:var(--si)}
.dec button[aria-pressed="true"][data-v="distintas"],
.dec button[aria-pressed="true"][data-v="no_es_persona"]{background:var(--no);color:#fff;border-color:var(--no)}
.dec button[aria-pressed="true"][data-v="pendiente"]{background:var(--duda);color:#fff;border-color:var(--duda)}
.dec input{flex:1;min-width:180px;font:inherit;font-size:.84rem;padding:.35rem .55rem;
border:1px solid #bccdd2;border-radius:4px;background:var(--sup);color:var(--tinta)}
.aviso{background:#fdf6e7;border:1px solid #c8901a55;border-left:3px solid #c8901a;
border-radius:4px;padding:.7rem .9rem;font-size:.85rem;color:#6a4a05;margin-bottom:1.2rem}
.visibles{color:var(--tinta3);font-size:.8rem;font-variant-numeric:tabular-nums}
.enlaces{display:flex;flex-wrap:wrap;gap:.9rem;align-items:baseline;margin:0 0 .8rem;font-size:.82rem}
.enlaces a{color:var(--accion);font-weight:600}
.obras{background:var(--sup2);border:1px solid var(--linea);border-radius:4px;
padding:.6rem .85rem;margin-bottom:.9rem}
.obras-t{margin:0 0 .35rem;font-size:.78rem;color:var(--tinta2)}
.obras ol{margin:0;padding-left:1.2rem;font-size:.82rem}
.obras li{margin-bottom:.25rem}
.obras .anio{font-variant-numeric:tabular-nums;color:var(--tinta3);margin-right:.3rem}
.obras .sindoi{color:var(--tinta3);font-style:italic}
.dec button[aria-pressed="true"][data-v="orcid_correcto"],
.dec button[aria-pressed="true"][data-v="orcid_encontrado"]{background:var(--si);color:#fff;border-color:var(--si)}
.dec button[aria-pressed="true"][data-v="orcid_incorrecto"]{background:var(--no);color:#fff;border-color:var(--no)}
.dec button[aria-pressed="true"][data-v="orcid_no_encontrado"]{background:var(--tinta2);color:#fff;border-color:var(--tinta2)}
.dec input.orcid{flex:0 0 auto;min-width:250px;font-family:ui-monospace,Menlo,Consolas,monospace}
.dec input.orcid.malo{border-color:var(--no);background:#fdeaed}
.oculto{display:none!important}
footer{border-top:1px solid var(--linea);padding:1.5rem 0;font-size:.8rem;color:var(--tinta2)}
"""

JS = """
const CASOS = __DATOS__;
const CLAVE = 'revision_identidad_v1';
let dec = {};
try { dec = JSON.parse(localStorage.getItem(CLAVE) || '{}'); } catch (e) { dec = {}; }

/* Lo ya decidido viene del CSV del repositorio; lo de este navegador es trabajo
   en curso. Manda el navegador SÓLO donde hay una entrada suya: se crea al
   pulsar un botón, así que su presencia significa una decisión deliberada de
   esta sesión. Donde no la hay, se siembra lo que el CSV registra. */
CASOS.forEach(c => { if (c.previa && !dec[c.id]) dec[c.id] = { ...c.previa }; });

function guardar() {
  try { localStorage.setItem(CLAVE, JSON.stringify(dec)); } catch (e) {}
  pintarAvance();
}

function pintarAvance() {
  const n = Object.values(dec).filter(d => d && d.veredicto && d.veredicto !== 'pendiente').length;
  document.getElementById('avance').innerHTML =
    `<b>${n}</b> de ${CASOS.length} resueltos · <b>${CASOS.length - n}</b> pendientes`;
  document.querySelectorAll('.caso').forEach(el => {
    const d = dec[el.dataset.id];
    el.dataset.decidido = (d && d.veredicto && d.veredicto !== 'pendiente') ? '1' : '0';
  });
  filtrar();
}

function filtrar() {
  const f = document.getElementById('filtro').value;
  const fam = document.getElementById('familia').value;
  document.querySelectorAll('.caso').forEach(el => {
    const d = dec[el.dataset.id];
    const resuelto = !!(d && d.veredicto && d.veredicto !== 'pendiente');
    el.classList.toggle('oculto',
      (f === 'pendientes' && resuelto) || (f === 'resueltos' && !resuelto)
      || (fam !== 'todas' && el.dataset.familia !== fam));
  });
  const vis = document.querySelectorAll('.caso:not(.oculto)').length;
  document.getElementById('visibles').textContent = `${vis} a la vista`;
}

/* El identificador se comprueba mientras se teclea: el dígito de control
   detecta el error de un carácter, que es el que se comete al copiar. Aquí sólo
   se avisa; quien decide de verdad es apply_decisions.py, que se niega a
   aplicar uno inválido. */
function orcidValido(v) {
  if (!/^\\d{4}-\\d{4}-\\d{4}-\\d{3}[\\dX]$/.test(v)) return false;
  const d = v.replace(/-/g, '');
  let t = 0;
  for (let i = 0; i < 15; i++) t = (t + Number(d[i])) * 2;
  const r = (12 - t % 11) % 11;
  return (r === 10 ? 'X' : String(r)) === d[15];
}

document.addEventListener('click', e => {
  const b = e.target.closest('.dec button[data-v]');
  if (!b) return;
  const id = b.closest('.caso').dataset.id;
  const v = b.dataset.v;
  const actual = dec[id] || {};
  dec[id] = { ...actual, veredicto: actual.veredicto === v ? null : v,
              fecha: new Date().toISOString().slice(0, 10) };
  b.closest('.dec').querySelectorAll('button[data-v]').forEach(o =>
    o.setAttribute('aria-pressed', String(dec[id].veredicto === o.dataset.v)));
  guardar();
});

document.addEventListener('input', e => {
  const campo = e.target.closest('.dec input[data-campo]');
  if (!campo) return;
  const id = campo.closest('.caso').dataset.id;
  const clave = campo.dataset.campo;
  dec[id] = { ...(dec[id] || {}), [clave]: campo.value };
  if (clave === 'orcid') {
    const v = campo.value.trim().toUpperCase();
    campo.classList.toggle('malo', v !== '' && !orcidValido(v));
  }
  try { localStorage.setItem(CLAVE, JSON.stringify(dec)); } catch (err) {}
});

document.getElementById('filtro').addEventListener('change', filtrar);
document.getElementById('familia').addEventListener('change', filtrar);

document.getElementById('exportar').addEventListener('click', () => {
  const esc = v => `"${String(v ?? '').replace(/"/g, '""')}"`;
  const cab = [
    '# Decisiones de identidad de autor — revisión humana',
    '# Generado por internal/revision_identidad.html',
    `# Exportado: ${new Date().toISOString().slice(0, 10)}`,
    __LEYENDA__,
  ].join('\\n');
  const cols = ['caso_id', 'cola', 'firmas', 'veredicto', 'orcid_propuesto', 'nota', 'fecha'];
  const filas = CASOS.map(c => {
    const d = dec[c.id] || {};
    return [c.id, c.cola, c.firmas.map(f => f.nombre).join(' | '),
            d.veredicto || 'pendiente', (d.orcid || '').trim().toUpperCase(),
            d.nota || '', d.fecha || ''].map(esc).join(',');
  });
  const csv = [cab, cols.join(','), ...filas].join('\\n');
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob(['\\ufeff' + csv], { type: 'text/csv;charset=utf-8' }));
  a.download = 'identity_decisions.csv';
  a.click();
});

/* Borra el trabajo de ESTE navegador y vuelve a lo que registra el CSV. No
   borra el registro: un botón que destruyera 52 decisiones ya tomadas, sin
   deshacer, no debería existir en una herramienta cuya salida se aplica al
   sitio. */
document.getElementById('limpiar').addEventListener('click', () => {
  if (!confirm('Se borra lo decidido en ESTE navegador. Lo ya registrado en '
    + 'internal/identity_decisions.csv se conserva. ¿Continuar?')) return;
  dec = {};
  CASOS.forEach(c => { if (c.previa) dec[c.id] = { ...c.previa }; });
  guardar();
  document.querySelectorAll('.caso').forEach(pintarCaso);
});

function pintarCaso(el) {
  const d = dec[el.dataset.id] || {};
  el.querySelectorAll('.dec button[data-v]').forEach(b =>
    b.setAttribute('aria-pressed', String(d.veredicto === b.dataset.v)));
  el.querySelectorAll('.dec input[data-campo]').forEach(i => {
    i.value = d[i.dataset.campo] || '';
    if (i.dataset.campo === 'orcid') {
      i.classList.toggle('malo', i.value !== '' && !orcidValido(i.value.toUpperCase()));
    }
  });
}

document.querySelectorAll('.caso').forEach(pintarCaso);
pintarAvance();
"""


def señales_html(cr: dict | None) -> str:
    if not cr:
        return ""
    s = []
    if cr["publicaciones_comunes"]:
        s.append(("fuerte-no", f"Firman juntas {cr['publicaciones_comunes']} publicación(es) "
                               "— casi seguro personas distintas"))
    else:
        s.append(("neutra", "Nunca firman la misma publicación"))
    if cr["mismo_orcid"]:
        s.append(("fuerte-si", "Mismo ORCID"))
    if cr.get("orcid_verificado"):
        s.append(("fuerte-si", "ORCID verificado contra el registro: el titular "
                               "declara estas publicaciones como suyas"))
    if cr["mismo_scopus"]:
        s.append(("fuerte-si", "Mismo Scopus Author ID"))
    if cr["coautores_comunes"]:
        s.append(("neutra", f"{cr['coautores_comunes']} coautor(es) en común"))
    else:
        s.append(("neutra", "Sin coautores en común"))
    s.append(("neutra", "Años solapados" if cr["anios_solapan"] else "Años sin solapar"))
    if cr["misma_unidad"]:
        s.append(("neutra", "Misma unidad académica"))
    return ('<div class="senales">'
            + "".join(f'<span class="s {k}">{html.escape(t)}</span>' for k, t in s)
            + "</div>")


def _verif(f: dict) -> str:
    """Celda de verificación contra el registro público de ORCID.

    Vacía si la verificación no se ha ejecutado: ausencia de dato y resultado
    negativo no pueden verse igual (decisión D-09).
    """
    v = f.get("orcid_veredicto")
    if not v:
        return '<span style="color:#5a6b71">—</span>'
    etiquetas = {
        "confirmada": ("fuerte-si", f"sí · {f.get('orcid_dois_coincidentes') or 0} DOI"),
        "sin_coincidencia": ("fuerte-no", "ningún DOI coincide"),
        "no_verificable": ("neutra", "el titular no declara obras"),
        "sin_registro": ("fuerte-no", "ORCID inexistente"),
    }
    clase, txt = etiquetas.get(v, ("neutra", v))
    afil = ' · afiliación institucional declarada' if f.get("orcid_afiliacion_ok") else ""
    return f'<span class="s {clase}">{html.escape(txt + afil)}</span>'


# Cuántas publicaciones se enseñan por firma antes de resumir el resto. Seis
# caben de un vistazo; con las 38 de la firma más prolífica, el caso deja de
# leerse y la página pasa de 300 KB.
MAX_OBRAS = 6

INICIALES = re.compile(r"^(?:[^\W\d_]\.?){1,3}$")


def apellido_de(firma: str) -> str:
    """El apellido de una forma de firma, para poder buscarlo en un registro.

    `clave_apellido` de la tabla maestra no sirve aquí: está pensada para
    emparejar, y por eso «Orellana-Donoso» le llega como «orellanadonoso». Un
    buscador no encuentra eso. Se recortan las iniciales del final, que es lo
    único que Scopus añade al apellido en esta forma de firma.
    """
    partes = firma.split()
    while len(partes) > 1 and INICIALES.match(partes[-1]):
        partes.pop()
    return " ".join(partes)


def enlaces_html(f: dict) -> str:
    """A dónde ir para comprobarlo con los ojos.

    La herramienta reunía la evidencia que YA teníamos y ahí se detenía: para
    verificar de verdad hay que abrir el registro del titular y mirar sus obras,
    y eso obligaba a copiar el identificador a mano en otra pestaña. Verificar
    manualmente 27 casos así son 27 copias y pegas, y en la número 12 alguien se
    equivoca de fila.

    Sólo se enlaza a lo que existe: sin ORCID no hay registro que abrir, y sin
    Scopus Author ID no hay perfil de Scopus. Un enlace roto que promete
    evidencia es peor que ningún enlace.
    """
    e = []
    if f.get("orcid"):
        e.append((f"https://orcid.org/{f['orcid']}",
                  "Registro del titular en ORCID", ""))
    # Búsqueda de texto libre con la firma tal como la imprime la fuente: es lo
    # que una persona teclearía. No se le añade un filtro por institución porque
    # la sintaxis avanzada del buscador web no está documentada como estable, y
    # `CLAUDE.md` prohíbe suponer comportamiento de un endpoint no confirmado.
    busq = urllib.parse.quote(f["nombre"])
    e.append((f"https://orcid.org/orcid-search/search?searchQuery={busq}",
              f"Buscar «{f['nombre']}» en ORCID", ""))
    for sid in f.get("scopus", []):
        e.append((f"https://www.scopus.com/authid/detail.uri?authorId={sid}",
                  f"Perfil {sid} en Scopus", " (requiere suscripción)"))
    return ('<div class="enlaces">'
            + "".join(f'<a href="{html.escape(u)}" target="_blank" rel="noopener">'
                      f"{html.escape(t)}</a>{html.escape(n)}" for u, t, n in e)
            + "</div>")


def obras_html(fs: list[dict]) -> str:
    """Las publicaciones atribuidas a la firma, con su DOI.

    Es lo que se compara contra el registro del titular: si ninguna de estas
    obras aparece allí, la asignación no se sostiene. Sin DOI no hay enlace y se
    dice —el 2,3 % del corpus no lo tiene—, en vez de enseñar un vínculo muerto.
    """
    bloques = ""
    for f in fs:
        obras = f.get("obras") or []
        filas = ""
        for _eid, anio, titulo, doi in obras[:MAX_OBRAS]:
            t = html.escape(str(titulo or "(sin título en el universo)"))
            enl = (f'<a href="https://doi.org/{html.escape(str(doi))}" target="_blank" '
                   f'rel="noopener" class="mono">{html.escape(str(doi))}</a>'
                   if doi and str(doi) != "nan" else '<span class="sindoi">sin DOI</span>')
            filas += f'<li><span class="anio">{html.escape(str(anio or "—"))}</span> {t} — {enl}</li>'
        if not filas:
            continue
        resto = max(0, len(obras) - MAX_OBRAS)
        bloques += (f'<div class="obras"><p class="obras-t">Publicaciones atribuidas a '
                    f'<strong>{html.escape(f["nombre"])}</strong>'
                    + (f" (se muestran {MAX_OBRAS} de {len(obras)})" if resto else "")
                    + f"</p><ol>{filas}</ol></div>")
    return bloques


def tabla_firmas(fs: list[dict]) -> str:
    if not fs:
        return '<p class="ctx">Sin perfil disponible para esta firma.</p>'
    filas = ""
    for f in fs:
        filas += (
            f'<tr><td><strong>{html.escape(f["nombre"])}</strong></td>'
            f'<td class="n">{f["n_pub"]}</td><td class="n">{html.escape(f["anios"])}</td>'
            f'<td>{html.escape(" · ".join(f["unidades"]) or "—")}</td>'
            f'<td class="mono">{html.escape(" ".join(f["scopus"]) or "—")}</td>'
            f'<td class="mono">{html.escape(f["orcid"] or "—")}'
            + (f' <span style="color:#5a6b71">({html.escape(f["orcid_confianza"])})</span>'
               if f["orcid"] and f["orcid_confianza"] else "")
            + f"</td><td>{_verif(f)}</td></tr>")
    return ('<table><thead><tr><th>Forma de firma</th><th>Pub.</th><th>Años</th>'
            '<th>Unidad académica</th><th>Scopus ID</th><th>ORCID</th>'
            '<th>Verificado</th></tr></thead>'
            f"<tbody>{filas}</tbody></table>")


def botones(caso: dict) -> str:
    """Los botones de una cola salen del vocabulario compartido, no de aquí.

    Antes cada cola traía sus etiquetas escritas al lado del caso y el aplicador
    tenía su propia lista de veredictos válidos. Dos listas para un vocabulario:
    la clase de defecto que este repositorio ya conoce. Ahora ofrecer un botón
    que nadie sabe aplicar es imposible, porque ofrecerlo y aplicarlo leen el
    mismo diccionario.
    """
    return "\n        ".join(
        f'<button type="button" data-v="{v}" aria-pressed="false">'
        f"{html.escape(D.etiqueta(v))}</button>"
        for v in D.veredictos_de(caso["cola"]))


def leyenda() -> str:
    """La explicación de cada veredicto que viaja en la cabecera del CSV.

    Se genera desde `decisiones.VOCABULARIO` en vez de escribirse al lado: era
    la cuarta copia de la misma lista, y la que más fácil envejecía porque nadie
    la lee hasta que alguien abre el CSV en un editor.
    """
    return ",\n    ".join(
        json.dumps(f"# {v}: {que_hace}", ensure_ascii=False)
        for v, (_etq, que_hace) in D.VOCABULARIO.items())


def render(cs: list[dict], meta: dict) -> str:
    cuerpo = ""
    for c in cs:
        # Los enlaces y las obras sólo en las colas de ORCID: son las que se
        # resuelven abriendo un registro y comparando publicaciones. En las
        # demás la pregunta se responde con la evidencia ya cruzada, y añadir
        # 141 listas de publicaciones costaría el triple de página sin usarse.
        orc = c["cola"] in D.FAMILIA_ORCID
        campo = ('<input type="text" data-campo="orcid" class="orcid" '
                 'placeholder="ORCID encontrado (0000-0000-0000-0000)" '
                 'pattern="\\d{4}-\\d{4}-\\d{4}-\\d{3}[\\dXx]">'
                 if c["cola"] in D.PIDEN_ORCID else "")
        cuerpo += f"""
    <article class="caso" data-id="{html.escape(c['id'])}" data-decidido="0"
             data-familia="{'orcid' if orc else 'identidad'}">
      <span class="cola">{html.escape(c['cola'])}</span>
      <h2>{html.escape(c['titulo'])}</h2>
      <p class="ctx">{html.escape(c['contexto'])}</p>
      {señales_html(c['cruces'])}
      {tabla_firmas(c['firmas'])}
      {"".join(enlaces_html(f) for f in c['firmas']) if orc else ""}
      {obras_html(c['firmas']) if orc else ""}
      <div class="dec">
        {botones(c)}
        <button type="button" data-v="pendiente" aria-pressed="false">Sigo sin saber</button>
        {campo}
        <input type="text" data-campo="nota" placeholder="Nota (opcional): en qué te basaste">
      </div>
    </article>"""

    datos = json.dumps([{"id": c["id"], "cola": c["cola"],
                         "firmas": [{"nombre": f["nombre"]} for f in c["firmas"]],
                         "previa": c.get("previa")}
                        for c in cs], ensure_ascii=False)

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Revisión de identidad de autor — capa interna</title>
<style>{CSS}</style>
</head>
<body>
<header><div class="c">
  <h1>Revisión de identidad de autor</h1>
  <p>Capa interna · {meta['casos'] - meta['decididos']} pendientes de
     {meta['casos']} casos · generado el {meta['fecha']} desde
     {meta['firmas']} formas de firma</p>
</div></header>

<div class="barra"><div class="c">
  <span class="avance" id="avance"></span>
  <select id="filtro" aria-label="Filtrar por estado">
    <option value="pendientes">Sólo pendientes</option>
    <option value="todos">Todos los casos</option>
    <option value="resueltos">Sólo resueltos</option>
  </select>
  <select id="familia" aria-label="Filtrar por tipo de pregunta">
    <option value="todas">Las dos preguntas</option>
    <option value="orcid">Sólo ORCID: ¿qué identificador le corresponde?</option>
    <option value="identidad">Sólo identidad: ¿son la misma persona?</option>
  </select>
  <span class="visibles" id="visibles"></span>
  <button type="button" class="pri" id="exportar">Exportar decisiones (CSV)</button>
  <button type="button" id="limpiar">Borrar todo</button>
</div></div>

<main class="c">
  <div class="aviso">
    <strong>Esta página no decide nada por usted.</strong>
    Reúne la evidencia dispersa en cuatro archivos y la presenta junta; el
    veredicto lo pone usted. Las decisiones se guardan en este navegador
    mientras trabaja: <strong>expórtelas a CSV antes de cerrar</strong>, y
    guarde el archivo como <span class="mono">internal/identity_decisions.csv</span>.
    Nada de lo que marque aquí modifica el sitio público por sí solo.
  </div>
  <div class="aviso">
    <strong>Cómo se verifica un ORCID a mano.</strong>
    Abra «Registro del titular en ORCID» y compare las obras que declara con
    las publicaciones que aparecen aquí bajo su firma. Una coincidencia basta
    para confirmar. Si el titular no declara ninguna obra, quedan su nombre y
    las afiliaciones que declara: eso es un indicio, no una prueba, y conviene
    dejarlo dicho en la nota. Si no coincide nada y las afiliaciones son de
    otra institución, marque que el ORCID no es de esta persona: la asignación
    se retira y la ficha vuelve a no tener identificador, que es preferible a
    atribuirle la obra de otro.
  </div>
  <div class="aviso">
    <strong>Cómo leer las señales.</strong>
    «Firman juntas N publicaciones» es el descarte más limpio: nadie firma dos
    veces el mismo artículo, así que si dos formas de firma aparecen en el mismo
    trabajo son personas distintas. «Mismo ORCID» y «Mismo Scopus Author ID»
    apuntan en sentido contrario, pero recuerde que la asignación de ORCID es a
    su vez una hipótesis por apellido e inicial. El resto son indicios, no
    pruebas.
  </div>
  {cuerpo}
</main>

<footer class="c">
  Generado por <span class="mono">src/review/build_review.py</span>.
  Regenerable. No se despliega: el ensamblado del sitio sólo copia
  <span class="mono">web/</span> y <span class="mono">data/processed/</span>.
</footer>

<script>{JS.replace("__DATOS__", datos).replace("__LEYENDA__", leyenda())}</script>
</body>
</html>
"""


def main() -> int:
    print("=" * 78)
    print("HERRAMIENTA DE REVISIÓN DE IDENTIDAD DE AUTOR")
    print("=" * 78)

    d = cargar()
    perf = perfiles(d["master"], d["log"], d["orcid"], d["verif"], d["uni"])
    cs = casos(d, perf)
    if not cs:
        print("  No hay casos que revisar. No se escribe nada.")
        return 0
    decididos, huerfanos = sembrar(cs, d["dec"])

    salida = INTERNAL / "revision_identidad.html"
    salida.write_text(render(cs, {
        "casos": len(cs), "fecha": date.today().isoformat(), "firmas": len(perf),
        "decididos": decididos,
    }), encoding="utf-8")

    por_cola: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for c in cs:
        por_cola[c["cola"]][0] += 1
        por_cola[c["cola"]][1] += 0 if c.get("previa") else 1
    descartables = sum(1 for c in cs
                       if c["cruces"] and c["cruces"]["publicaciones_comunes"])

    print(f"  {'cola':<34} {'casos':>6} {'pendientes':>11}")
    for cola, (n, pend) in sorted(por_cola.items(), key=lambda x: -x[1][1]):
        print(f"  {cola:<34} {n:>6} {pend:>11}")
    print(f"\n  casos totales                 : {len(cs)}")
    print(f"  ya decididos                  : {decididos} "
          "(leídos de internal/identity_decisions.csv)")
    print(f"  PENDIENTES                    : {len(cs) - decididos}")
    print(f"  descartables por coautoría    : {descartables} "
          "(firman juntas, luego son personas distintas)")
    if huerfanos:
        # Una decisión que ya no encaja con ningún caso no se aplica y no lo
        # diría: el operador vería su número de resueltos bajar sin explicación.
        print(f"\n  AVISO · {len(huerfanos)} decisión(es) del CSV sin caso vivo "
              "que las reciba:")
        for cid in huerfanos[:10]:
            print(f"    {cid}")
        if len(huerfanos) > 10:
            print(f"    … y {len(huerfanos) - 10} más")
    print(f"\n  OK · {salida.relative_to(ROOT)}")
    print("       Ábralo en el navegador. Exporte a internal/identity_decisions.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
