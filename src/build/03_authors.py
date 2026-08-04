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

import common_build as b

PUBLICATION = b.load_config("publication.yml")["fichas_autor"]


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

    salida = {}
    for _, r in df.iterrows():
        nombre = r["nombre_en_fuente"]
        v = verif.get(nombre)
        salida[nombre] = {
            "orcid": r["orcid"],
            "confianza": r["confianza"],
            "publicaciones_de_respaldo": b.to_num(r["publicaciones_de_respaldo"]),
            "fuente": r["fuente"],
            # None cuando la verificación no se ha ejecutado. No es lo mismo
            # que «no verificada»: es que nadie ha mirado todavía, y la ficha
            # debe poder decir esa diferencia.
            "veredicto": v["veredicto"] if v is not None else None,
            "dois_coincidentes": b.to_num(v["dois_coincidentes"]) if v is not None else None,
        }
    return salida


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
FUENTE_REGISTRO = "ORCID (declarado por el titular)"
VEREDICTO_DEL_REGISTRO = (
    "declarado",
    "declarado por el titular",
    "Esta asignación se encontró preguntando al registro de ORCID quién "
    "declara esta publicación entre sus obras: la afirma el propio titular. "
    "No hay aquí una segunda comprobación independiente.")


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
        identidad_ambigua = bool(n_ids and n_ids > 1)

        veredicto = (orcid_map.get(nombre) or {}).get("veredicto")
        coincidentes = (orcid_map.get(nombre) or {}).get("dois_coincidentes")
        fuente_orcid = (orcid_map.get(nombre) or {}).get("fuente")
        clase, etiqueta, detalle = VEREDICTO_PUBLICO.get(veredicto, (None, None, None))

        if veredicto == "confirmada" and fuente_orcid == FUENTE_REGISTRO:
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
            "orcid_estado": ("Recuperado desde Crossref"
                             if nombre in orcid_map
                             else "No disponible en las fuentes actuales"),
            "identidad_no_consolidada": identidad_ambigua,
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
            "firmas_con_orcid_sin_confirmar": sum(
                1 for a in resumen if a["orcid_veredicto"] == "sin_coincidencia"),
        },
        "nota": b.nota("P-06"),
        "advertencia_identidad": (
            "Cada ficha corresponde a una forma de firma, no necesariamente a una "
            "persona distinta. Sin un identificador persistente como ORCID no es "
            "posible consolidar variantes de nombre."
        ),
    }
    b.write_json(payload, "authors.json")

    n_pubs = [a["n_publicaciones"] for a in resumen]
    print(f"  firmas               : {len(resumen)}")
    print(f"  fichas generadas     : {fichas}")
    print(f"  slugs desambiguados  : {colisiones} (variantes que colapsaban)")
    print(f"  con n >= {umbral_interpretable} (interpretables): "
          f"{sum(1 for a in resumen if a['interpretable'])}")
    print(f"  identidad no consolidada: {sum(1 for a in resumen if a['identidad_no_consolidada'])}")
    print(f"  con ORCID               : {len(orcid_map)}"
          f"{'  (enriquecimiento no ejecutado)' if not orcid_map else ''}")
    etq_vistas = [a["orcid_veredicto_etiqueta"] for a in resumen
                  if a["orcid_veredicto_etiqueta"]]
    if etq_vistas:
        for k, texto in (("verificado", "verificado contra el registro"),
                         ("declarado por el titular", "declarado por el titular (sin 2.ª fuente)"),
                         ("no verificable", "sin obras con DOI que contrastar"),
                         ("sin confirmar", "SIN CONFIRMAR — revisión humana"),
                         ("registro no accesible", "registro no accesible")):
            if etq_vistas.count(k):
                print(f"    {texto:42s}: {etq_vistas.count(k)}")
    else:
        print("    (verificación contra ORCID no ejecutada)")
    print(f"  mediana de publicaciones: {statistics.median(n_pubs)}")


if __name__ == "__main__":
    main()
