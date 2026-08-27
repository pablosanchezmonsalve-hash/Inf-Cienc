"""Build 01 — Publicaciones y facetas de filtro.

Salidas:
  data/processed/publications.json
  data/processed/facets.json
"""

from __future__ import annotations

from collections import Counter

import sys

import common_build as b

if sys.platform == "win32":
    # La consola de Windows usa cp1252 por defecto: revienta cualquier print()
    # con caracteres como "→"/"—"/"·". Mismo patrón que src/enrich/orcid_openalex.py.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")



def main() -> None:
    b.banner("BUILD 01 — PUBLICACIONES Y FACETAS")
    b.require_validation()

    uni = b.load_universe()
    authorship = b.load_authorship()
    # Las firmas E-09 encoladas (fragmentos de cadena de afiliación, no
    # personas) no tienen ficha propia y no deben aparecer como coautor en
    # ninguna vista pública — ni en esta tabla ni, sobre todo, en un futuro
    # grafo de coautoría (C-05), donde un fragmento con seis firmantes UFT
    # dibujaría seis colaboraciones que no existen. `DESCARTADAS` ya excluye
    # las CONFIRMADAS en `load_authorship()`; esto cierra la misma puerta
    # para las que siguen pendientes de revisión.
    sin_e09 = authorship[~authorship["nombre_en_fuente"].isin(b.firmas_e09_encoladas())]
    autores_por_eid = (sin_e09.groupby("eid")["nombre_en_fuente"]
                       .apply(lambda s: sorted(set(s))).to_dict())
    unidades_por_eid = (authorship.dropna(subset=["unidad_academica"])
                        .groupby("eid")["unidad_academica"]
                        .apply(lambda s: sorted(set(s))).to_dict())

    registros = []
    for _, r in uni.iterrows():
        eid = r["eid"]
        registros.append({
            "eid": eid,
            "titulo": b.clean(r["titulo"]),
            "anio": b.to_num(r["anio"]),
            "doi": b.clean(r["doi"]),
            "tipo": b.clean(r["tipo_documental"]),
            "fuente": b.clean(r["fuente_titulo"]),
            "tipo_fuente": b.clean(r["source_type"]),
            "editorial": b.clean(r["editorial"]),
            "idioma": b.clean(r["idioma"]),
            "citas": b.to_num(r["citas"]),
            "fwci": b.to_num(r["fwci"]),
            "percentil_citacion": b.to_num(r["percentil_citacion"]),
            "sjr_percentil": b.to_num(r["sjr_percentil"]),
            "open_access": b.split_multi(r["open_access"]),
            "n_autores": b.to_num(r["n_autores"]),
            "autores_uft": autores_por_eid.get(eid, []),
            "n_paises": b.to_num(r["n_paises"]),
            "paises": b.split_multi(r["paises"]),
            "n_instituciones": b.to_num(r["n_instituciones"]),
            # La lista, no sólo el recuento. Sin ella C-04 —instituciones
            # colaboradoras— era el único indicador publicado que no se podía
            # recalcular sobre un recorte, y la sección de colaboración habría
            # tenido un gráfico que ignora el filtro sin decirlo.
            "instituciones": b.split_multi(r["instituciones"]),
            "es_internacional": (r["es_internacional"] == "True")
            if b.clean(r["es_internacional"]) is not None else None,
            "asjc": b.split_multi(r["asjc"]),
            "qs_area": b.split_multi(r["qs_area"]),
            "topic": b.clean(r["topic"]),
            "ods": b.split_multi(r["ods"]),
            "unidades": unidades_por_eid.get(eid, []),
            # Banderas de disponibilidad: gobiernan qué se puede mostrar
            "tiene_metricas": r["tiene_metricas"] == "True",
            "tiene_autoria": r["tiene_autoria_detallada"] == "True",
        })

    b.write_json({"meta": b.build_meta(), "publicaciones": registros},
                 "publications.json")
    print(f"  publicaciones: {len(registros)}")

    # ------------------------------------------------------------- facetas
    def contar(key, multi=False):
        c = Counter()
        for reg in registros:
            val = reg[key]
            if multi:
                for v in (val or []):
                    c[v] += 1
            elif val is not None:
                c[val] += 1
        return [{"valor": k, "n": v} for k, v in c.most_common()]

    # 'Sin dato declarado' es una opción real de filtro, no un hueco (D-24/D-27).
    sin_oa = sum(1 for r in registros if not r["open_access"])
    sin_unidad = sum(1 for r in registros if not r["unidades"])

    facetas = {
        "meta": b.build_meta(),
        "anio": contar("anio"),
        "tipo": contar("tipo"),
        "qs_area": contar("qs_area", multi=True),
        "asjc": contar("asjc", multi=True),
        "unidad": contar("unidades", multi=True) + [
            {"valor": "Sin dato declarado", "n": sin_unidad}],
        "open_access": contar("open_access", multi=True) + [
            {"valor": "Sin dato declarado", "n": sin_oa}],
        "pais": contar("paises", multi=True),
        "internacional": [
            {"valor": "Internacional",
             "n": sum(1 for r in registros if r["es_internacional"] is True)},
            {"valor": "Nacional",
             "n": sum(1 for r in registros if r["es_internacional"] is False)},
            {"valor": "Sin dato declarado",
             "n": sum(1 for r in registros if r["es_internacional"] is None)},
        ],
    }
    b.write_json(facetas, "facets.json")
    print(f"  facetas: {sum(len(v) for k, v in facetas.items() if k != 'meta')} valores")


if __name__ == "__main__":
    main()
