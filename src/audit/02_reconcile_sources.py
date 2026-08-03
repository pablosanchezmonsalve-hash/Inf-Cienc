"""02 — Reconciliación entre fuentes y construcción del universo canónico.

Aplica las reglas X-01..X-07 y D-01..D-03, P-01..P-02.
Materializa la decisión de universo: unión de ambas fuentes primarias con
banderas de disponibilidad (config/institution.yml → universo_publicaciones).

Salidas:
  data/interim/publications_universe.csv
  data/interim/reconciliation_summary.csv
  internal/ambiguities_publications.csv
"""

from __future__ import annotations

import pandas as pd

import common as c


def main() -> None:
    c.banner("02 — RECONCILIACIÓN DE FUENTES Y UNIVERSO CANÓNICO")

    scopus = c.read_scopus()
    scival = c.read_scival()

    eid_scopus = set(scopus["EID"].dropna())
    eid_scival = set(scival["EID"].dropna())
    ambos = eid_scopus & eid_scival
    solo_scopus = eid_scopus - eid_scival
    solo_scival = eid_scival - eid_scopus

    print(f"X-01 · en ambas fuentes : {len(ambos)}")
    print(f"X-01 · sólo en Scopus   : {len(solo_scopus)}")
    print(f"X-01 · sólo en SciVal   : {len(solo_scival)}")

    # ---------------------------------------------------------------- universo
    estrategia = c.INSTITUTION["universo_publicaciones"]["estrategia"]
    if estrategia == "union":
        universo = sorted(eid_scopus | eid_scival)
    elif estrategia == "interseccion":
        universo = sorted(ambos)
    elif estrategia == "scopus":
        universo = sorted(eid_scopus)
    elif estrategia == "scival":
        universo = sorted(eid_scival)
    else:
        raise ValueError(f"estrategia de universo desconocida: {estrategia!r}")

    sc_idx = scopus.set_index("EID")
    sv_idx = scival.set_index("EID")

    def sv_val(v, col):
        """Valor de SciVal normalizando el guion, que es su marcador de ausencia."""
        if v is None:
            return None
        raw = v.get(col)
        if raw is None or (isinstance(raw, float) and pd.isna(raw)):
            return None
        raw = str(raw).strip()
        return None if raw in ("-", "", "nan") else raw

    rows = []
    for eid in universo:
        in_sc, in_sv = eid in eid_scopus, eid in eid_scival
        s = sc_idx.loc[eid] if in_sc else None
        v = sv_idx.loc[eid] if in_sv else None
        paises = sv_val(v, "Country/Region")
        n_paises = sv_val(v, "Number of Countries/Regions")
        rows.append({
            "eid": eid,
            "titulo": (s["Title"] if in_sc else v["Title"]),
            "anio": (s["Year"] if in_sc else v["Year"]),
            "doi": (s["DOI"] if in_sc else v["DOI"]),
            "tipo_documental": (s["Document Type"] if in_sc else v["Publication type"]),
            "fuente_titulo": (s["Source title"] if in_sc else v["Scopus Source title"]),
            "en_scopus": in_sc,
            "en_scival": in_sv,
            # Banderas de disponibilidad: el denominador de cada indicador se
            # deriva de aquí, no de un total único.
            "tiene_metricas": in_sv,
            "tiene_autoria_detallada": in_sc,
            "tiene_area_tematica": in_sv,
            "citas_scopus": (s["Cited by"] if in_sc else None),
            "citas_scival": (v["Citations"] if in_sv else None),
            # --- atributos que consume el build (Fase 3) -------------------
            # Se materializan aquí para que src/build/ no lea de data/raw/
            # (decisión D-22). Se excluyen las columnas de cobertura nula
            # detectadas por la regla E-06 (pendiente T-07).
            "source_id": sv_val(v, "Source ID"),
            "source_type": sv_val(v, "Source type"),
            "issn": sv_val(v, "ISSN"),
            "editorial": sv_val(v, "Publisher"),
            "idioma": (s["Language of Original Document"] if in_sc else None),
            "citas": sv_val(v, "Citations"),
            "fwci": sv_val(v, "Field-Weighted Citation Impact"),
            "percentil_citacion": sv_val(
                v, "Outputs in Top Citation Percentiles, per percentile"),
            "field_citation_average": sv_val(v, "Field-Citation Average"),
            "sjr": sv_val(v, "SJR (publication year)"),
            "sjr_percentil": sv_val(v, "SJR percentile (publication year) *"),
            "citescore": sv_val(v, "CiteScore (publication year)"),
            "citescore_percentil": sv_val(
                v, "CiteScore percentile (publication year) *"),
            "snip": sv_val(v, "SNIP (publication year)"),
            "open_access": sv_val(v, "Open Access"),
            "n_autores": sv_val(v, "Number of Authors"),
            "n_paises": n_paises,
            "paises": paises,
            "n_instituciones": sv_val(v, "Number of Institutions"),
            "instituciones": sv_val(v, "Institutions"),
            "asjc": sv_val(v, "All Science Journal Classification (ASJC) field name"),
            "qs_area": sv_val(v, "Quacquarelli Symonds (QS) Subject area field name"),
            "topic": sv_val(v, "Topic name"),
            "ods": sv_val(v, "Sustainable Development Goals (2025)"),
            "es_internacional": (int(n_paises) > 1) if n_paises else None,
        })
    universe = pd.DataFrame(rows)

    # ------------------------------------------------- coherencia entre fuentes
    comunes = universe[universe["en_scopus"] & universe["en_scival"]]
    year_mismatch, doi_mismatch, cite_diff = [], [], []
    for eid in comunes["eid"]:
        s, v = sc_idx.loc[eid], sv_idx.loc[eid]
        if str(s["Year"]).strip() != str(v["Year"]).strip():
            year_mismatch.append(eid)
        ds, dv = str(s["DOI"]).strip().lower(), str(v["DOI"]).strip().lower()
        if ds not in ("nan", "-", "") and dv not in ("nan", "-", "") and ds != dv:
            doi_mismatch.append(eid)
        try:
            d = int(float(v["Citations"])) - int(float(s["Cited by"]))
            if d:
                cite_diff.append({"eid": eid, "citas_scopus": int(float(s["Cited by"])),
                                  "citas_scival": int(float(v["Citations"])), "delta": d})
        except (TypeError, ValueError):
            pass

    print(f"X-02 · discrepancia de año entre fuentes : {len(year_mismatch)}")
    print(f"X-03 · discrepancia de DOI entre fuentes : {len(doi_mismatch)}")
    print(f"X-04 · publicaciones con distinto conteo de citas: {len(cite_diff)}")

    tot_sc = pd.to_numeric(scopus["Cited by"], errors="coerce").sum()
    tot_sv = pd.to_numeric(scival["Citations"], errors="coerce").sum()
    print(f"X-04 · citas totales Scopus={tot_sc:.0f} SciVal={tot_sv:.0f} "
          f"delta={tot_sv - tot_sc:+.0f} ({100 * (tot_sv - tot_sc) / tot_sc:+.2f} %)")

    # ------------------------------------------------------- duplicados (D, P)
    dup_eid = int(scopus["EID"].duplicated().sum())
    dois = scopus["DOI"].dropna()
    dup_doi = int(dois.duplicated().sum())
    print(f"D-01 · EID duplicados: {dup_eid}")
    print(f"D-02 · DOI duplicados (excluyendo ausentes): {dup_doi}")

    scopus = scopus.assign(_tnorm=scopus["Title"].map(c.normalize_title))
    dup_titles = scopus[scopus.duplicated("_tnorm", keep=False)].sort_values("_tnorm")
    print(f"P-01 · grupos con título normalizado repetido: {dup_titles['_tnorm'].nunique()}")

    # ---------------------------------------------------------- capa interna
    amb = []
    for eid in sorted(solo_scopus):
        r = sc_idx.loc[eid]
        amb.append({
            "tipo": "X-01_solo_en_scopus", "severidad": "alta", "eid": eid,
            "anio": r["Year"], "detalle": str(r["Title"])[:150],
            "consecuencia": "sin FWCI ni clasificación temática; excluida de indicadores de impacto normalizado",
            "resolucion": "PENDIENTE_REVISION_HUMANA",
        })
    for eid in sorted(solo_scival):
        r = sv_idx.loc[eid]
        amb.append({
            "tipo": "X-01_solo_en_scival", "severidad": "alta", "eid": eid,
            "anio": r["Year"], "detalle": str(r["Title"])[:150],
            "consecuencia": "sin detalle de autoría; no atribuible a autores de la institución",
            "resolucion": "PENDIENTE_REVISION_HUMANA",
        })
    for _, grp in dup_titles.groupby("_tnorm"):
        eids = list(grp["EID"])
        for _, r in grp.iterrows():
            # Un grupo revisado por una persona se sigue declarando —la
            # coincidencia de título es real— pero como caso resuelto, no como
            # duplicado pendiente. La resolución vive en config, con su
            # evidencia; aquí sólo se lee.
            res = c.resolucion_duplicado(r["EID"])
            amb.append({
                "tipo": "P-01_duplicado_probable_por_titulo",
                "severidad": "informativa" if res else "alta",
                "eid": r["EID"], "anio": r["Year"],
                "detalle": f"{str(r['Title'])[:100]} | tipo={r['Document Type']} | doi={r['DOI']}",
                "consecuencia": (f"revisado: {res['veredicto']} — {res['evidencia'][:120]}"
                                 if res else
                                 f"agrupado con {[e for e in eids if e != r['EID']]}"),
                "resolucion": (f"RESUELTO_{res['veredicto'].upper()} "
                               f"({res['revisado_por']}, {res['fecha']})"
                               if res else "NO_RESOLVER_AUTOMATICAMENTE"),
            })
    for eid in year_mismatch:
        amb.append({"tipo": "X-02_year_mismatch", "severidad": "alta", "eid": eid,
                    "anio": sc_idx.loc[eid]["Year"],
                    "detalle": f"scopus={sc_idx.loc[eid]['Year']} scival={sv_idx.loc[eid]['Year']}",
                    "consecuencia": "afecta series temporales",
                    "resolucion": "PENDIENTE_REVISION_HUMANA"})
    for eid in doi_mismatch:
        amb.append({"tipo": "X-03_doi_mismatch", "severidad": "alta", "eid": eid,
                    "anio": sc_idx.loc[eid]["Year"],
                    "detalle": f"scopus={sc_idx.loc[eid]['DOI']} scival={sv_idx.loc[eid]['DOI']}",
                    "consecuencia": "afecta enlaces públicos",
                    "resolucion": "PENDIENTE_REVISION_HUMANA"})

    amb_df = pd.DataFrame(amb)

    resumen = pd.DataFrame([
        {"metrica": "eid_en_ambas_fuentes", "valor": len(ambos)},
        {"metrica": "eid_solo_scopus", "valor": len(solo_scopus)},
        {"metrica": "eid_solo_scival", "valor": len(solo_scival)},
        {"metrica": "universo_estrategia", "valor": estrategia},
        {"metrica": "universo_total", "valor": len(universe)},
        {"metrica": "con_metricas", "valor": int(universe["tiene_metricas"].sum())},
        {"metrica": "con_autoria_detallada", "valor": int(universe["tiene_autoria_detallada"].sum())},
        {"metrica": "con_area_tematica", "valor": int(universe["tiene_area_tematica"].sum())},
        {"metrica": "eid_duplicados", "valor": dup_eid},
        {"metrica": "doi_duplicados", "valor": dup_doi},
        {"metrica": "grupos_titulo_duplicado", "valor": int(dup_titles["_tnorm"].nunique())},
        {"metrica": "year_mismatch", "valor": len(year_mismatch)},
        {"metrica": "doi_mismatch", "valor": len(doi_mismatch)},
        {"metrica": "publicaciones_con_delta_citas", "valor": len(cite_diff)},
        {"metrica": "citas_totales_scopus", "valor": int(tot_sc)},
        {"metrica": "citas_totales_scival", "valor": int(tot_sv)},
    ])

    c.write_interim(universe, "publications_universe.csv")
    c.write_interim(resumen, "reconciliation_summary.csv")
    c.write_interim(pd.DataFrame(cite_diff), "citation_deltas.csv")
    c.write_internal(amb_df, "ambiguities_publications.csv")

    print(f"\nUNIVERSO CANÓNICO ({estrategia}): {len(universe)} publicaciones")
    print(f"  con métricas          : {int(universe['tiene_metricas'].sum())}")
    print(f"  con autoría detallada : {int(universe['tiene_autoria_detallada'].sum())}")
    print("\nDistribución por año (universo completo):")
    print(universe["anio"].value_counts().sort_index().to_string())
    print(f"\nOK · internal/ambiguities_publications.csv ({len(amb_df)} entradas)")


if __name__ == "__main__":
    main()
