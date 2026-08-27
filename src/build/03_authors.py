"""Build 03 — Ranking de autores y fichas individuales.

Emite una ficha por autor como archivo independiente (decisión D-21): la ficha
de una persona no debe obligar a descargar el corpus completo.

ALCANCE DE PUBLICACIÓN (T-11, confirmado por el responsable): se publican todas
las firmas y el ranking se muestra por defecto filtrado a n >= 5 (decisión
D-29). Ambos valores son parámetros de `config/publication.yml`; cambiarlos no
requiere tocar código.

Salidas:
  data/processed/authors.json
  data/processed/author/<slug>.json
"""

from __future__ import annotations

import statistics
from collections import Counter

import sys

import common_build as b

if sys.platform == "win32":
    # La consola de Windows usa cp1252 por defecto: revienta cualquier print()
    # con caracteres como "→"/"—"/"·". Mismo patrón que src/enrich/orcid_openalex.py.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


PUBLICATION = b.load_config("publication.yml")["fichas_autor"]

FUENTE_REGISTRO = "ORCID (declarado por el titular)"

# Las asignaciones que salieron de la revisión humana no tienen veredicto y no
# lo tendrán: `orcid_api.py` contrasta DOI atribuidos contra DOI declarados, y
# estas nacieron SIN publicación compartida —por eso hacía falta que alguien
# las mirara—. Dejarlas sin etiqueta las presentaba como si nadie las hubiera
# comprobado, que es lo contrario de lo que ocurrió.
FUENTE_REVISION = "Revisión humana (candidato por afiliación confirmado)"
FUENTE_BUSQUEDA = "Revisión humana (búsqueda manual en el registro)"


# canónica -> las formas de firma que se fusionaron en ella.
CONSOLIDADAS: dict[str, list[str]] = {}
for _v, _c in b.CONSOLIDACION.items():
    CONSOLIDADAS.setdefault(_c, []).append(_v)
for _c in CONSOLIDADAS:
    CONSOLIDADAS[_c].sort()


def _frase_consolidacion(n_fusionadas: int) -> str:
    """Cómo se fusionaron las firmas, separando los dos niveles de evidencia.

    Decir «revisión humana caso por caso» de un grupo que unió una
    normalización de cadena sería atribuir a una persona una decisión que nadie
    tomó. Los grupos ortográficos no son un juicio sobre personas —son la misma
    firma escrita con otros diacríticos o separadores—, y el lector tiene
    derecho a saber cuáles son cuáles.
    """
    orig = b.ORIGEN_CONSOLIDACION
    humanas = sum(1 for c in CONSOLIDADAS if orig.get(c, "humana") in ("humana", "mixta"))
    ortog = sum(1 for c in CONSOLIDADAS if orig.get(c) == "ortografica")
    t = f"{n_fusionadas} se fusionaron en {len(CONSOLIDADAS)} personas"
    if ortog and humanas:
        return (t + f": {humanas} tras una revisión humana caso por caso y {ortog} "
                "por ser la misma firma escrita con distintos diacríticos o "
                "separadores")
    if ortog:
        return (t + ", por ser la misma firma escrita con distintos diacríticos o "
                "separadores")
    return t + " tras una revisión humana caso por caso"


def cargar_orcid() -> dict[str, dict]:
    """Asignaciones de ORCID, si el enriquecimiento ya se ejecutó (V2-01).

    El archivo es opcional: sin él las fichas muestran el placeholder declarado.
    Nunca se inventa un ORCID ni se deja el campo en blanco silencioso.

    Cuando además existe la verificación contra el registro público de ORCID,
    cada asignación viaja con su veredicto. La distinción importa: `confianza`
    es lo que opina nuestra heurística de emparejamiento —apellido e inicial
    coincidentes en Crossref—, mientras que el veredicto es lo que dice el
    titular en su propio registro. Cuando ambos están, manda el segundo.
    """
    path = b.ROOT / "data" / "enriched" / "authors_orcid.csv"
    if not path.exists():
        return {}
    import pandas as pd
    df = pd.read_csv(path, dtype=str)

    verif: dict[str, dict] = {}
    vpath = b.ROOT / "data" / "enriched" / "orcid_verificacion.csv"
    if vpath.exists():
        vdf = pd.read_csv(vpath, dtype=str)
        verif = {r["nombre_en_fuente"]: r for _, r in vdf.iterrows()}

    salida: dict[str, dict] = {}
    conflictos: list[str] = []
    for _, r in df.iterrows():
        # Asignaciones que una revisión humana declaró que no son de esta
        # firma. La fila se conserva en el CSV —de ahí viene el dato— y aquí
        # simplemente no se usa.
        if r["nombre_en_fuente"] in b.ORCID_RETIRADO:
            continue
        # Las asignaciones están indexadas por la firma tal cual aparece en la
        # fuente; las fichas, por su forma canónica. Sin canonizar aquí, una
        # persona consolidada perdería el ORCID de todas sus variantes salvo
        # el de la que da nombre al grupo.
        nombre = b.canonizar(r["nombre_en_fuente"])
        v = verif.get(r["nombre_en_fuente"])
        cand = {
            "orcid": r["orcid"],
            "confianza": r["confianza"],
            "publicaciones_de_respaldo": b.to_num(r["publicaciones_de_respaldo"]),
            "fuente": r["fuente"],
            # None cuando la verificación no se ha ejecutado. No es lo mismo
            # que «no verificada»: es que nadie ha mirado todavía, y la ficha
            # debe poder decir esa diferencia.
            "veredicto": v["veredicto"] if v is not None else None,
            "dois_coincidentes": b.to_num(v["dois_coincidentes"]) if v is not None else None,
            # Se resuelve con la firma SIN canonizar, que es la forma sobre la
            # que se pronunció quien revisó; el mapa está indexado por la
            # canónica y para entonces esa distinción ya se perdió.
            "comprobado_a_mano": r["nombre_en_fuente"] in b.ORCID_CONFIRMADO,
        }
        previo = salida.get(nombre)
        if previo is None:
            salida[nombre] = cand
            continue
        # Una persona consolidada suele traer ORCID desde varias de sus
        # variantes. Antes ganaba la última fila del CSV, o sea el orden de
        # ordenación del archivo: la evidencia que se enseñaba dependía de un
        # detalle sin significado. Ahora gana la más fuerte, siempre la misma.
        if previo["orcid"] != cand["orcid"]:
            conflictos.append(f"{nombre}: {previo['orcid']} vs {cand['orcid']}")
            continue          # no se elige: se declara y se deja el primero
        if _fuerza(cand) > _fuerza(previo):
            salida[nombre] = cand

    if conflictos:
        # No se resuelve por su cuenta: dos identificadores distintos para una
        # persona que alguien declaró única es un hallazgo, no un desempate.
        print("  AVISO · variantes consolidadas con ORCID distintos:")
        for c in conflictos:
            print(f"    {c}")
    return salida


def _fuerza(a: dict) -> int:
    """Cuánto respalda una asignación, para quedarse con la mejor.

    El orden no es caprichoso: arriba está lo que apoyan dos fuentes
    independientes; después, el juicio de una persona; después, lo que sólo
    afirma el titular; y al final lo que nadie ha podido contrastar.
    """
    if a["veredicto"] == "confirmada" and a["fuente"] != FUENTE_REGISTRO:
        return 4
    if a["fuente"] == FUENTE_REVISION:
        return 3
    if a["veredicto"] == "confirmada":
        return 2
    return 1


# Qué se le enseña al lector para cada veredicto. `sin_coincidencia` NO dice
# que la asignación sea falsa —eso exige una revisión humana que aún no se ha
# hecho—, dice que la evidencia disponible no la respalda. La diferencia entre
# «es incorrecta» y «no está confirmada» es la que separa un dato de una
# acusación sobre una persona con nombre y apellido.
# La CLASE viaja aparte del veredicto: dos veredictos distintos pueden merecer
# el mismo tratamiento visual, y un mismo veredicto puede merecer dos según de
# dónde venga la asignación. Derivarla del veredicto ataba las dos cosas.
VEREDICTO_PUBLICO = {
    "confirmada": ("verificado", "verificado",
                   "El titular declara en su propio registro de ORCID al menos "
                   "una de las publicaciones que aquí se le atribuyen."),
    "no_verificable": ("neutro", "no verificable",
                       "El titular no declara ninguna obra con DOI en su "
                       "registro de ORCID, de modo que no hay nada contra qué "
                       "contrastar la asignación."),
    "sin_coincidencia": ("sin-confirmar", "sin confirmar",
                         "El titular declara obras en su registro de ORCID, "
                         "pero ninguna coincide con las atribuidas a esta "
                         "firma. Pendiente de revisión humana."),
    "sin_registro": ("neutro", "registro no accesible",
                     "El ORCID no existe o su registro no es público."),
}

# Una asignación encontrada preguntando al registro «¿quién declara este DOI?»
# sale SIEMPRE confirmada, porque se la encontró justamente por declararlo.
# El veredicto no aporta ahí una segunda comprobación: repite la primera.
#
# Llamarlo «verificado» sugeriría al lector que dos fuentes independientes
# coinciden, y no es el caso: la fuente es una sola, el propio titular. Se
# etiqueta por lo que realmente es, que además dice más y no menos.
VEREDICTO_DE_REVISION = (
    "revisado",
    "confirmado por revisión",
    "El titular declara esta institución en su registro de ORCID y una persona "
    "confirmó, caso por caso, que corresponde a esta firma. No hay publicación "
    "compartida que lo respalde: el respaldo es el juicio de quien revisó.")
VEREDICTO_DEL_REGISTRO = (
    "declarado",
    "declarado por el titular",
    "Esta asignación se encontró preguntando al registro de ORCID quién "
    "declara esta publicación entre sus obras: la afirma el propio titular. "
    "No hay aquí una segunda comprobación independiente.")

# Cuando una persona miró el registro del titular y respaldó una asignación que
# la comprobación automática no podía resolver. Pisa al veredicto automático
# porque responde la misma pregunta con más evidencia, no con otra distinta.
VEREDICTO_COMPROBADO_A_MANO = (
    "revisado",
    "comprobado por revisión",
    "La comprobación automática no pudo resolver esta asignación —el titular no "
    "declara obras con DOI, o ninguna coincide—. Una persona abrió su registro "
    "y la respaldó caso por caso.")
VEREDICTO_DE_BUSQUEDA = (
    "revisado",
    "encontrado por revisión",
    "Ninguna de las vías automáticas encontró identificador para esta firma. "
    "Una persona lo buscó en el registro de ORCID y lo encontró. El respaldo es "
    "su juicio, no una publicación compartida.")


# Firmas que una persona buscó en el registro sin encontrarlas, en su forma
# canónica: el veredicto se emite sobre la firma de la fuente y las fichas se
# indexan por la canónica.
SIN_REGISTRO = {b.canonizar(f) for f in b.ORCID_SIN_REGISTRO}

ESTADO_POR_FUENTE = {
    "Crossref": "Recuperado desde Crossref",
    FUENTE_REGISTRO: "Recuperado del registro público de ORCID",
    FUENTE_REVISION: "Confirmado en revisión humana",
    FUENTE_BUSQUEDA: "Encontrado en el registro por búsqueda manual",
}


def estado_orcid(nombre: str, fuente: str | None) -> str:
    """De dónde salió el identificador, o por qué no hay ninguno.

    Decía «Recuperado desde Crossref» para TODA asignación, incluidas las 48
    que vinieron del registro de ORCID y las 18 que salió a buscar una persona.
    Era una afirmación sobre la procedencia del dato, y era falsa en 66 fichas.

    Y distingue tres ausencias que no son la misma: nadie ha mirado, alguien
    miró y no encontró, y no hay fuente que lo aporte.
    """
    if fuente:
        return ESTADO_POR_FUENTE.get(fuente, f"Recuperado desde {fuente}")
    if nombre in SIN_REGISTRO:
        return ("Buscado en el registro de ORCID por una revisión humana, "
                "sin encontrarlo")
    return "No disponible en las fuentes actuales"


def h_index(citas: list[int]) -> int:
    vals = sorted([c for c in citas if c is not None], reverse=True)
    return sum(1 for i, c in enumerate(vals, 1) if c >= i)


def main() -> None:
    b.banner("BUILD 03 — AUTORES Y FICHAS")
    b.require_validation()

    uni = b.load_universe().set_index("eid")
    authorship = b.load_authorship()
    master = b.load_authors().set_index("nombre_en_fuente")

    n_min = PUBLICATION["n_minimo_ranking_por_defecto"]
    umbral_interpretable = b.INDICATORS["reglas_transversales"]["n_minimo_interpretable"]

    # Identificadores únicos por firma: dos variantes distintas nunca comparten
    # archivo (ver common_build.unique_slugs y decisión D-08).
    slugs = b.unique_slugs(sorted(authorship["nombre_en_fuente"].unique()))
    colisiones = sum(1 for n, s in slugs.items() if s != b.slugify(n))

    orcid_map = cargar_orcid()

    # Las fichas de la corrida anterior se BORRAN antes de escribir las nuevas.
    # Sin esto quedaban huérfanas: al consolidar identidades desaparecen firmas
    # y cambian slugs —una variante que dejó de colisionar pierde su sufijo—, y
    # los archivos viejos seguían en disco y viajaban al sitio. Se servían 610
    # fichas para 556 firmas, y las 54 sobrantes mostraban datos de antes de la
    # revisión sin decirlo en ninguna parte.
    dir_fichas = b.PROCESSED / "author"
    borradas = 0
    if dir_fichas.exists():
        for viejo_json in dir_fichas.glob("*.json"):
            viejo_json.unlink()
            borradas += 1

    resumen, fichas = [], 0
    for nombre, grp in authorship.groupby("nombre_en_fuente"):
        slug = slugs[nombre]
        eids = sorted(set(grp["eid"]))
        m = master.loc[nombre] if nombre in master.index else None

        pubs, citas_list = [], []
        for eid in eids:
            if eid not in uni.index:
                continue
            r = uni.loc[eid]
            c = b.to_num(r["citas"])
            citas_list.append(c)
            pubs.append({
                "eid": eid,
                "titulo": b.clean(r["titulo"]),
                "anio": b.to_num(r["anio"]),
                "doi": b.clean(r["doi"]),
                "tipo": b.clean(r["tipo_documental"]),
                "fuente": b.clean(r["fuente_titulo"]),
                "citas": c,
                "percentil_citacion": b.to_num(r["percentil_citacion"]),
                "tiene_metricas": r["tiene_metricas"] == "True",
            })
        pubs.sort(key=lambda p: (-(p["anio"] or 0), p["titulo"] or ""))

        validos = [c for c in citas_list if c is not None]
        n_pub = len(pubs)
        total_citas = sum(validos)
        unidades = sorted({u for u in grp["unidad_academica"].dropna()
                           if u != "No determinada"})
        top10 = sum(1 for p in pubs
                    if p["percentil_citacion"] is not None and p["percentil_citacion"] <= 10)
        por_anio = Counter(p["anio"] for p in pubs if p["anio"])

        scopus_ids = (b.clean(m["scopus_author_ids"]) if m is not None else None)
        # Identidad no consolidada: se declara, no se enlaza con otras firmas
        # (docs/AUTHOR_PROFILE.md §4).
        n_ids = b.to_num(m["n_scopus_author_ids"]) if m is not None else None
        # Varios Scopus Author ID sobre una firma SIN consolidar es una duda:
        # puede haber dos personas detrás. Sobre una firma consolidada por
        # revisión humana ya no lo es: es la consecuencia esperada de haber
        # unido varias variantes, cada una con su identificador. Marcarla
        # igual presentaría como incertidumbre justo lo que se acaba de
        # resolver.
        #
        # PERO ESO NO VALE PARA UNA CONSOLIDACIÓN ORTOGRÁFICA. Ahí las grafías
        # unidas cuelgan del MISMO nombre completo en la fuente, así que los
        # varios identificadores no son «uno por variante»: son la duda P-04
        # original, intacta. Tratarlas igual apagaba la advertencia de una
        # ficha sobre la que nadie había decidido nada —«De la Fuente López M.»
        # perdió la suya— y eso es exactamente lo que la bandera existe para
        # impedir.
        variantes = CONSOLIDADAS.get(nombre, [])
        revisada = b.ORIGEN_CONSOLIDACION.get(nombre) in ("humana", "mixta")
        identidad_ambigua = bool(n_ids and n_ids > 1) and not (variantes and revisada)

        veredicto = (orcid_map.get(nombre) or {}).get("veredicto")
        coincidentes = (orcid_map.get(nombre) or {}).get("dois_coincidentes")
        fuente_orcid = (orcid_map.get(nombre) or {}).get("fuente")
        clase, etiqueta, detalle = VEREDICTO_PUBLICO.get(veredicto, (None, None, None))

        if fuente_orcid == FUENTE_BUSQUEDA:
            clase, etiqueta, detalle = VEREDICTO_DE_BUSQUEDA
        elif fuente_orcid == FUENTE_REVISION:
            clase, etiqueta, detalle = VEREDICTO_DE_REVISION
        elif veredicto == "confirmada" and fuente_orcid == FUENTE_REGISTRO:
            # Circular por construcción: se la encontró por declarar el DOI.
            clase, etiqueta, detalle = VEREDICTO_DEL_REGISTRO
        elif veredicto == "confirmada" and coincidentes:
            # La confirmación se cuantifica: «verificado» respaldado por diez
            # publicaciones y por una no son la misma afirmación, y el lector
            # no tiene por qué suponer cuál de las dos está leyendo.
            detalle = (f"El titular declara en su propio registro de ORCID "
                       f"{coincidentes} de las publicaciones que aquí se le "
                       f"atribuyen." if coincidentes > 1 else
                       "El titular declara en su propio registro de ORCID una "
                       "de las publicaciones que aquí se le atribuyen.")
        elif (orcid_map.get(nombre) or {}).get("comprobado_a_mano"):
            # VA AL FINAL de la cadena, y eso es la decisión, no el orden en que
            # se escribió: la comprobación humana levanta una asignación que la
            # vía automática no pudo resolver, pero NO pisa a una que sí resolvió.
            # «Verificado» significa que dos fuentes independientes coinciden;
            # sustituirlo por el juicio de una persona sería cambiar evidencia
            # más fuerte por más débil y presentarlo como una mejora.
            clase, etiqueta, detalle = VEREDICTO_COMPROBADO_A_MANO

        ficha = {
            "meta": b.build_meta(),
            "id": slug,
            "nombre_en_fuente": nombre,
            "unidades_academicas": unidades or ["No determinada"],
            "scopus_author_ids": scopus_ids.split("|") if scopus_ids else [],
            # Placeholder declarado, nunca omitido (decisión D-07). Cuando el
            # enriquecimiento desde Crossref se ha ejecutado, el ORCID viaja con
            # su confianza: una asignación por apellido e inicial es una
            # hipótesis verificable, no un hecho. Y cuando se ha contrastado
            # contra el registro del titular, viaja además el veredicto, que es
            # evidencia de la fuente y no opinión de nuestra heurística.
            "orcid": (orcid_map.get(nombre) or {}).get("orcid"),
            "orcid_confianza": (orcid_map.get(nombre) or {}).get("confianza"),
            "orcid_respaldo": (orcid_map.get(nombre) or {}).get("publicaciones_de_respaldo"),
            "orcid_veredicto": veredicto,
            "orcid_veredicto_etiqueta": etiqueta,
            "orcid_veredicto_clase": clase,
            "orcid_veredicto_detalle": detalle,
            "orcid_dois_coincidentes": (orcid_map.get(nombre) or {}).get("dois_coincidentes"),
            "orcid_estado": estado_orcid(nombre, fuente_orcid),
            "identidad_no_consolidada": identidad_ambigua,
            # Qué formas de firma se fusionaron aquí y por decisión de quién.
            # Sin esto, una ficha con 34 publicaciones repartidas entre tres
            # variantes no se podría rastrear hasta la fuente.
            "variantes_consolidadas": variantes,
            "indicadores": {
                "n_publicaciones": n_pub,
                "citas_totales": total_citas,
                "citas_por_publicacion": round(total_citas / n_pub, 2) if n_pub else None,
                # h-index sólo cuando la muestra lo hace mínimamente legible
                "h_index_ventana": h_index(validos) if n_pub >= umbral_interpretable else None,
                "publicaciones_top10": top10,
                "interpretable": n_pub >= umbral_interpretable,
            },
            "evolucion": [{"anio": a, "n": por_anio[a]} for a in sorted(por_anio)],
            "publicaciones": pubs,
            "advertencia_muestra_reducida": n_pub < umbral_interpretable,
            # El umbral viaja con la ficha: el texto de la advertencia lo
            # necesita, y hasta ahora el front lo tenía escrito a mano. Cambiarlo
            # en config/publication.yml debe cambiar las 589 fichas.
            "umbral_interpretable": umbral_interpretable,
        }
        b.write_json(ficha, f"{slug}.json", subdir="author")
        fichas += 1

        resumen.append({
            "id": slug,
            "nombre": nombre,
            "n_publicaciones": n_pub,
            "citas": total_citas,
            "citas_por_publicacion": round(total_citas / n_pub, 2) if n_pub else None,
            "publicaciones_top10": top10,
            "unidades": unidades or ["No determinada"],
            "anio_min": min(por_anio) if por_anio else None,
            "anio_max": max(por_anio) if por_anio else None,
            "interpretable": n_pub >= umbral_interpretable,
            "identidad_no_consolidada": identidad_ambigua,
            "variantes_consolidadas": variantes,
            # El ORCID viaja también en el listado, no sólo en la ficha: es el
            # único identificador persistente que distingue dos firmas parecidas,
            # y esconderlo en el detalle obliga a abrir 589 fichas para usarlo.
            "orcid": (orcid_map.get(nombre) or {}).get("orcid"),
            "orcid_confianza": (orcid_map.get(nombre) or {}).get("confianza"),
            "orcid_veredicto": veredicto,
            "orcid_veredicto_etiqueta": etiqueta,
            "orcid_veredicto_clase": clase,
        })

    resumen.sort(key=lambda a: (-a["n_publicaciones"], a["nombre"]))

    n_fusionadas = sum(len(v) for v in CONSOLIDADAS.values())
    # Las descartadas cuentan en el origen: la fuente sí las traía. Sin este
    # término, descartar cuatro firmas haría que el texto dijera que la fuente
    # detectó 585, y la fuente detectó 589.
    n_firmas_origen = (len(resumen) - len(CONSOLIDADAS) + n_fusionadas
                       + len(b.DESCARTADAS))
    n_sin_revisar = len(resumen) - len(CONSOLIDADAS)
    n_encoladas = len(b.firmas_e09_encoladas())

    payload = {
        "meta": b.build_meta(),
        "autores": resumen,
        "parametros": {
            "n_minimo_ranking_por_defecto": n_min,
            "n_minimo_interpretable": umbral_interpretable,
            "total_firmas": len(resumen),
            "firmas_interpretables": sum(1 for a in resumen if a["interpretable"]),
            "firmas_con_orcid": sum(1 for a in resumen if a["orcid"]),
            # Recuento agregado, que es lo publicable: el detalle nominal de
            # qué firma no se confirma vive en la capa interna (CLAUDE.md,
            # <data_governance>).
            #
            # Se cuenta por ETIQUETA, no por veredicto. Las asignaciones que
            # salieron del propio registro también traen veredicto
            # «confirmada», pero por construcción: sumarlas aquí inflaría el
            # recuento de verificaciones independientes con comprobaciones
            # circulares.
            "firmas_con_orcid_verificado": sum(
                1 for a in resumen if a["orcid_veredicto_etiqueta"] == "verificado"),
            "firmas_con_orcid_declarado_por_titular": sum(
                1 for a in resumen
                if a["orcid_veredicto_etiqueta"] == "declarado por el titular"),
            "firmas_con_orcid_confirmado_por_revision": sum(
                1 for a in resumen
                if a["orcid_veredicto_etiqueta"] == "confirmado por revisión"),
            # Por etiqueta como los tres de arriba, y no por veredicto: cuando
            # una persona comprueba a mano una asignación que la vía automática
            # no pudo resolver, el veredicto de origen no cambia —nadie
            # reescribe `orcid_verificacion.csv`— pero la ficha ya no dice «sin
            # confirmar». Contando por veredicto, el recuento seguiría
            # denunciando durante años algo que ya se resolvió.
            "firmas_con_orcid_sin_confirmar": sum(
                1 for a in resumen if a["orcid_veredicto_etiqueta"] == "sin confirmar"),
            "firmas_con_orcid_comprobado_a_mano": sum(
                1 for a in resumen
                if a["orcid_veredicto_etiqueta"] in ("comprobado por revisión",
                                                     "encontrado por revisión")),
        },
        "nota": b.nota_p06(len(resumen)),
        # El texto se construye con las cifras del momento en vez de fijarlo:
        # decía «sin un identificador persistente no es posible consolidar»
        # justo cuando una persona acababa de consolidar 30 grupos, y decía
        # 589 junto a un recuento de 556.
        "advertencia_identidad": (
            (f"Cada ficha corresponde a una forma de firma, no necesariamente a una "
             f"persona distinta. De las {n_firmas_origen} detectadas en la fuente, "
             + _frase_consolidacion(n_fusionadas)
             # Sin esta cláusula la frase deja de cuadrar en cuanto se descarta
             # algo: el origen las suma y ninguna otra parte las resta.
             + (f" y {len(b.DESCARTADAS)} se descartaron por no ser personas sino "
                "fragmentos de cadena de afiliación" if b.DESCARTADAS else "")
             + f". Las {n_sin_revisar} restantes siguen sin consolidar: pueden "
             f"incluir variantes de una misma persona."
             if CONSOLIDADAS else
             "Cada ficha corresponde a una forma de firma, no necesariamente a una "
             "persona distinta. Las variantes de nombre no se consolidan por "
             "heurística: requieren revisión humana, aún pendiente.")
            # Ni siquiera «una forma de firma»: hay fichas que probablemente no
            # correspondan a ninguna persona. Decirlo aquí y no sólo en la nota
            # del indicador, porque esta es la página donde esas fichas se ven.
            + (f" Además, {n_encoladas} de estas fichas son PROBABLES fragmentos "
               "de cadena de afiliación que la fuente metió en la lista de "
               "autores. La auditoría las detectó y están pendientes de revisión "
               "humana: confirmarlo o descartarlo lo decide una persona, no el "
               "pipeline." if n_encoladas else "")
        ),
    }
    b.write_json(payload, "authors.json")

    n_pubs = [a["n_publicaciones"] for a in resumen]
    print(f"  firmas               : {len(resumen)}")
    print(f"  fichas generadas     : {fichas}"
          + (f"  (se borraron {borradas} de la corrida anterior)" if borradas else ""))
    print(f"  slugs desambiguados  : {colisiones} (variantes que colapsaban)")
    print(f"  con n >= {umbral_interpretable} (interpretables): "
          f"{sum(1 for a in resumen if a['interpretable'])}")
    print(f"  identidad no consolidada: {sum(1 for a in resumen if a['identidad_no_consolidada'])}")
    print(f"  con ORCID               : {len(orcid_map)}"
          f"{'  (enriquecimiento no ejecutado)' if not orcid_map else ''}")
    etq_vistas = [a["orcid_veredicto_etiqueta"] for a in resumen
                  if a["orcid_veredicto_etiqueta"]]
    if etq_vistas:
        glosa = (("verificado", "verificado contra el registro"),
                 ("declarado por el titular", "declarado por el titular (sin 2.ª fuente)"),
                 ("confirmado por revisión", "confirmado por revisión humana"),
                 ("comprobado por revisión", "comprobado a mano en el registro"),
                 ("encontrado por revisión", "encontrado a mano en el registro"),
                 ("no verificable", "sin obras con DOI que contrastar"),
                 ("sin confirmar", "SIN CONFIRMAR — revisión humana"),
                 ("registro no accesible", "registro no accesible"))
        for k, texto in glosa:
            if etq_vistas.count(k):
                print(f"    {texto:42s}: {etq_vistas.count(k)}")
        # Otra lista escrita a mano junto a las etiquetas que enumera. Si
        # aparece una etiqueta nueva, este bucle la omitiría en silencio y el
        # desglose dejaría de sumar el total sin decir por qué.
        huerfanas = sorted(set(etq_vistas) - {k for k, _ in glosa})
        if huerfanas:
            print(f"    AVISO · etiquetas sin glosa en este desglose: {huerfanas}")
    else:
        print("    (verificación contra ORCID no ejecutada)")
    print(f"  mediana de publicaciones: {statistics.median(n_pubs)}")


if __name__ == "__main__":
    main()
