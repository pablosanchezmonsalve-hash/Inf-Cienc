"""04 — Población de autores UFT y descomposición de la brecha 585/440/396.

Construye el borrador de la tabla maestra de autores y explica la diferencia
entre la extracción automática y el trabajo manual previo. Aplica P-03..P-05.

El colapso de variantes de nombre está DESHABILITADO por configuración: las
variantes se detectan y se encolan, nunca se fusionan (CLAUDE.md,
<author_master_rule>).

Salidas:
  data/interim/authors_master_draft.csv
  data/interim/author_population_gap.csv
  internal/ambiguities_authors.csv
"""

from __future__ import annotations

import re

import pandas as pd

import common as c


def scopus_id_map(scopus: pd.DataFrame) -> dict[str, set[str]]:
    """Nombre completo -> Scopus Author ID(s), desde 'Author full names'."""
    out: dict[str, set[str]] = {}
    for full in scopus["Author full names"].dropna():
        for part in full.split("; "):
            m = re.match(r"(.+?)\s+\((\d+)\)$", part.strip())
            if m:
                out.setdefault(m.group(1).strip(), set()).add(m.group(2))
    return out


def main() -> None:
    c.banner("04 — POBLACIÓN DE AUTORES UFT")

    scopus = c.read_scopus()
    log = pd.read_csv(c.INTERNAL / "matching_log.csv", dtype=str)
    log["anio"] = log["anio"].astype(int)

    ventana = c.INSTITUTION["ventana_temporal"]
    log = log[(log["anio"] >= ventana["anio_inicio"]) & (log["anio"] <= ventana["anio_fin"])]

    # ------------------------------------------- descomposición de la brecha
    autores_full = set(log["nombre_en_fuente"])
    autores_2425 = set(log[log["anio"] >= 2024]["nombre_en_fuente"])
    solo_2023 = autores_full - autores_2425

    detalle = c.read_report_sheet("Publicaciones_UFT_detalle")
    manual_detalle = set(detalle["Autores finis terrae afiliados"].dropna())
    investigadores = c.read_report_sheet("Investigadores")
    manual_ranking = set(investigadores["Investigador"].dropna())

    print(f"Extracción automática 2023-2025 : {len(autores_full)}")
    print(f"Extracción automática 2024-2025 : {len(autores_2425)}")
    print(f"Excel · hoja detalle  (2024-25) : {len(manual_detalle)}")
    print(f"Excel · hoja ranking  (2024-25) : {len(manual_ranking)}")
    print(f"\nAutores presentes sólo en 2023  : {len(solo_2023)}")
    print(f"Ranking contenido en detalle     : "
          f"{len(manual_ranking - manual_detalle) == 0}")
    print(f"En detalle y no en ranking       : {len(manual_detalle - manual_ranking)}")

    gap = pd.DataFrame([
        {"poblacion": "automatica_2023_2025", "n": len(autores_full),
         "ventana": "2023-2025", "fuente": "extracción reproducible"},
        {"poblacion": "automatica_2024_2025", "n": len(autores_2425),
         "ventana": "2024-2025", "fuente": "extracción reproducible"},
        {"poblacion": "manual_detalle", "n": len(manual_detalle),
         "ventana": "2024-2025", "fuente": "2026_Reporte-UFT.xlsx"},
        {"poblacion": "manual_ranking", "n": len(manual_ranking),
         "ventana": "2024-2025", "fuente": "2026_Reporte-UFT.xlsx"},
        {"poblacion": "delta_ventana_2023", "n": len(solo_2023),
         "ventana": "2023", "fuente": "autores exclusivos de 2023"},
        {"poblacion": "delta_automatica_vs_manual_misma_ventana",
         "n": len(autores_2425) - len(manual_detalle),
         "ventana": "2024-2025", "fuente": "residuo tras igualar la ventana"},
        {"poblacion": "delta_detalle_vs_ranking",
         "n": len(manual_detalle) - len(manual_ranking),
         "ventana": "2024-2025", "fuente": "deduplicación manual de variantes"},
    ])

    # -------------------------------------------- borrador de tabla maestra
    ids = scopus_id_map(scopus)
    id_by_short: dict[str, set[str]] = {}
    for full, sid in ids.items():
        parts = full.split(",")
        short = parts[0].strip()
        if len(parts) > 1:
            initials = "".join(w[0] + "." for w in parts[1].split() if w[:1].isalpha())
            short = f"{short} {initials}".strip()
        id_by_short.setdefault(short, set()).update(sid)

    rows = []
    for name, grp in log.groupby("nombre_en_fuente"):
        unidades = [u for u in grp["unidad_academica"].unique()
                    if u != c.MATCHING["unidad_academica"]["etiqueta_sin_dato"]]
        rows.append({
            "nombre_en_fuente": name,
            "clave_normalizada": c.normalize_author_key(name),
            "clave_apellido": c.surname_key(name),
            "scopus_author_ids": "|".join(sorted(id_by_short.get(name, []))) or None,
            "n_scopus_author_ids": len(id_by_short.get(name, [])),
            "orcid": None,  # placeholder declarado: no existe en las fuentes
            "n_publicaciones": grp["eid"].nunique(),
            "anio_min": int(grp["anio"].min()),
            "anio_max": int(grp["anio"].max()),
            "unidades_academicas": "|".join(sorted(unidades)) or
                                   c.MATCHING["unidad_academica"]["etiqueta_sin_dato"],
            "n_unidades_distintas": len(unidades),
            "confianza_maxima": "alta" if (grp["confianza"] == "alta").any() else "media",
            "en_ranking_manual": name in manual_ranking,
            "en_detalle_manual": name in manual_detalle,
        })
    master = pd.DataFrame(rows).sort_values("n_publicaciones", ascending=False)

    # ----------------------------------------------------- ambigüedades P-03..05
    amb = []

    for key, grp in master.groupby("clave_apellido"):
        if key and len(grp) > 1:
            for _, r in grp.iterrows():
                amb.append({
                    "tipo": "P-03_variantes_de_nombre", "severidad": "alta",
                    "clave": key, "nombre_en_fuente": r["nombre_en_fuente"],
                    "detalle": "|".join(sorted(grp["nombre_en_fuente"])),
                    "consecuencia": "posible misma persona contada varias veces",
                    "resolucion": "NO_RESOLVER_AUTOMATICAMENTE",
                })

    for full, sids in ids.items():
        if len(sids) > 1:
            amb.append({
                "tipo": "P-04_nombre_con_multiples_scopus_id", "severidad": "alta",
                "clave": full, "nombre_en_fuente": full,
                "detalle": "|".join(sorted(sids)),
                "consecuencia": "perfil Scopus fragmentado u homonimia",
                "resolucion": "NO_RESOLVER_AUTOMATICAMENTE",
            })

    by_sid: dict[str, set[str]] = {}
    for full, sids in ids.items():
        for sid in sids:
            by_sid.setdefault(sid, set()).add(full)
    for sid, names in by_sid.items():
        if len(names) > 1:
            amb.append({
                "tipo": "P-05_scopus_id_con_multiples_nombres", "severidad": "media",
                "clave": sid, "nombre_en_fuente": sorted(names)[0],
                "detalle": "|".join(sorted(names)),
                "consecuencia": "variantes de firma bajo un mismo identificador",
                "resolucion": "REVISAR_NORMALIZACION_DE_NOMBRE",
            })

    for _, r in master[master["n_unidades_distintas"] > 1].iterrows():
        amb.append({
            "tipo": "I-06_autor_con_multiples_unidades", "severidad": "media",
            "clave": r["nombre_en_fuente"], "nombre_en_fuente": r["nombre_en_fuente"],
            "detalle": r["unidades_academicas"],
            "consecuencia": "afiliación interna variable entre publicaciones",
            "resolucion": "DECLARAR_NO_RESOLVER",
        })

    for name in sorted(manual_detalle - autores_2425):
        amb.append({
            "tipo": "V-manual_no_reproducido", "severidad": "alta",
            "clave": name, "nombre_en_fuente": name, "detalle": "",
            "consecuencia": "presente en el Excel manual, no reproducido por la extracción",
            "resolucion": "PENDIENTE_REVISION_HUMANA",
        })

    amb_df = pd.DataFrame(amb)

    c.write_interim(master, "authors_master_draft.csv")
    c.write_interim(gap, "author_population_gap.csv")
    c.write_internal(amb_df, "ambiguities_authors.csv")

    print(f"\nBorrador de tabla maestra: {len(master)} autores")
    print(f"  con Scopus Author ID resuelto : {int(master['scopus_author_ids'].notna().sum())}")
    print(f"  con ORCID                     : 0  (no existe en las fuentes)")
    print(f"  con unidad académica          : "
          f"{int((master['unidades_academicas'] != 'No determinada').sum())}")
    print(f"  validados contra ranking manual: {int(master['en_ranking_manual'].sum())}")

    print("\nAmbigüedades encoladas por tipo:")
    print(amb_df["tipo"].value_counts().to_string())
    print("\nOK · internal/ambiguities_authors.csv, data/interim/authors_master_draft.csv")


if __name__ == "__main__":
    main()
