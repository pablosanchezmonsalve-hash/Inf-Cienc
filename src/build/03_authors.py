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
    """
    path = b.ROOT / "data" / "enriched" / "authors_orcid.csv"
    if not path.exists():
        return {}
    import pandas as pd
    df = pd.read_csv(path, dtype=str)
    return {r["nombre_en_fuente"]: {
        "orcid": r["orcid"],
        "confianza": r["confianza"],
        "publicaciones_de_respaldo": b.to_num(r["publicaciones_de_respaldo"]),
        "fuente": r["fuente"],
    } for _, r in df.iterrows()}


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

        ficha = {
            "meta": b.build_meta(),
            "id": slug,
            "nombre_en_fuente": nombre,
            "unidades_academicas": unidades or ["No determinada"],
            "scopus_author_ids": scopus_ids.split("|") if scopus_ids else [],
            # Placeholder declarado, nunca omitido (decisión D-07). Cuando el
            # enriquecimiento desde Crossref se ha ejecutado, el ORCID viaja con
            # su confianza: una asignación por apellido e inicial es una
            # hipótesis verificable, no un hecho.
            "orcid": (orcid_map.get(nombre) or {}).get("orcid"),
            "orcid_confianza": (orcid_map.get(nombre) or {}).get("confianza"),
            "orcid_respaldo": (orcid_map.get(nombre) or {}).get("publicaciones_de_respaldo"),
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
    print(f"  mediana de publicaciones: {statistics.median(n_pubs)}")


if __name__ == "__main__":
    main()
