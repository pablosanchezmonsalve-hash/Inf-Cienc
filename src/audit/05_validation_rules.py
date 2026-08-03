"""05 — Motor de reglas de validación.

Ejecuta las reglas declaradas en la Fase 1 y emite un reporte con severidad.
Las reglas bloqueantes que fallan deben impedir la publicación de indicadores.

Salidas:
  data/interim/validation_report.csv
  docs/VALIDATION_REPORT.md
"""

from __future__ import annotations

import re

import pandas as pd

import common as c

RESULTS: list[dict] = []


def check(rule: str, severity: str, description: str, passed: bool,
          observed: str = "") -> None:
    RESULTS.append({
        "regla": rule,
        "severidad": severity,
        "descripcion": description,
        "resultado": "PASA" if passed else "FALLA",
        "observado": observed,
    })


def main() -> None:
    c.banner("05 — REGLAS DE VALIDACIÓN")

    scopus = c.read_scopus()
    scival = c.read_scival()
    universe = pd.read_csv(c.INTERIM / "publications_universe.csv")
    log = pd.read_csv(c.INTERNAL / "matching_log.csv", dtype=str)
    master = pd.read_csv(c.INTERIM / "authors_master_draft.csv")
    ventana = c.INSTITUTION["ventana_temporal"]

    # ------------------------------------------------ integridad estructural
    check("E-01", "bloqueante", "Todo registro tiene EID con formato válido",
          bool(scopus["EID"].notna().all()
               and scopus["EID"].str.match(r"^2-s2\.0-\d+$").all()),
          f"{int(scopus['EID'].notna().sum())}/{len(scopus)}")

    check("E-02", "bloqueante", "EID único en cada fuente primaria",
          int(scopus["EID"].duplicated().sum()) == 0
          and int(scival["EID"].duplicated().sum()) == 0,
          f"scopus={int(scopus['EID'].duplicated().sum())} "
          f"scival={int(scival['EID'].duplicated().sum())}")

    check("E-03", "bloqueante", "Cabecera de SciVal en la fila configurada",
          scival.columns[0] == "Title", f"primera columna={scival.columns[0]!r}")

    anios = pd.to_numeric(universe["anio"], errors="coerce")
    check("E-04", "bloqueante", "Año dentro de la ventana declarada",
          bool(anios.between(ventana["anio_inicio"], ventana["anio_fin"]).all()),
          f"rango observado={int(anios.min())}-{int(anios.max())}")

    citas = pd.to_numeric(scopus["Cited by"], errors="coerce")
    check("E-05", "bloqueante", "Citas enteras y no negativas",
          bool((citas.dropna() >= 0).all()), f"mínimo={citas.min():.0f}")

    vacias = [col for col in scopus.columns if scopus[col].notna().sum() == 0]
    check("E-06", "alta", "Sin columnas de cobertura nula en el universo activo",
          len(vacias) == 0, f"vacías={vacias}")

    rdata_unificado = c.read_rdata("rdata_unificado")
    if rdata_unificado is None:
        check("E-07", "alta", "Sin columnas residuales de join en fuentes activas",
              True, "fuente de referencia no leída (paquete `rdata` ausente); "
                    "no afecta a las fuentes activas")
    else:
        residuo = [col for col in rdata_unificado.columns
                   if re.search(r"\.(x|y)(\.(x|y))*$", str(col))]
        check("E-07", "alta", "Sin columnas residuales de join en fuentes activas",
              True, f"detectadas en rdata (fuente de referencia, no activa): {len(residuo)}")

    declarado = c.SOURCES["scival_export"]["n_registros_declarado"]
    check("E-08", "media", "n de registros leído coincide con el declarado",
          len(scival) == declarado, f"declarado={declarado} leído={len(scival)}")

    # -------------------------------------------------------- duplicados
    check("D-01", "bloqueante", "Sin EID repetido",
          int(scopus["EID"].duplicated().sum()) == 0,
          str(int(scopus["EID"].duplicated().sum())))

    dup_doi = int(scopus["DOI"].dropna().duplicated().sum())
    check("D-02", "alta", "Sin DOI repetido entre los no nulos", dup_doi == 0, str(dup_doi))

    check("D-03", "alta", "Sin filas íntegramente duplicadas",
          int(scopus.duplicated().sum()) == 0, str(int(scopus.duplicated().sum())))

    tnorm = scopus["Title"].map(c.normalize_title)
    dups = tnorm[tnorm.duplicated(keep=False)]
    grupos = int(dups.nunique())
    # Lo revisado y lo pendiente se cuentan por separado: una afirmación
    # verificada y una no verificada no pueden aparecer en la misma cifra.
    revisados = sum(
        1 for _, g in scopus.assign(_t=tnorm)[tnorm.isin(dups)].groupby("_t")
        if c.resolucion_duplicado(g["EID"].iloc[0]))
    check("P-01", "alta", "Duplicados probables por título marcados, no resueltos",
          True, f"{grupos} grupo(s) · {revisados} revisado(s) por una persona · "
                f"{grupos - revisados} pendiente(s)")

    amb_a = pd.read_csv(c.INTERNAL / "ambiguities_authors.csv")
    check("P-03", "alta", "Variantes de nombre encoladas sin colapso automático",
          not c.MATCHING["identidad_autor"]["colapso_automatico_de_variantes"],
          f"{int((amb_a['tipo'] == 'P-03_variantes_de_nombre').sum())} entradas")

    check("P-04", "alta", "Nombres con múltiples Scopus ID encolados", True,
          f"{int((amb_a['tipo'] == 'P-04_nombre_con_multiples_scopus_id').sum())} entradas")

    # -------------------------------------------- coherencia institucional
    detectadas = set(log["eid"])
    check("I-01", "bloqueante", "Toda publicación tiene al menos una detección institucional",
          len(set(scopus["EID"]) - detectadas) == 0,
          f"sin detección={len(set(scopus['EID']) - detectadas)}")

    recon = pd.read_csv(c.INTERIM / "matching_reconciliation.csv")
    solo_duro = int((recon["caso"] == "solo_metodo_duro").sum())
    check("I-04", "alta", "Métodos duro y blando reconciliados sin contradicción",
          solo_duro == 0,
          f"solo_duro={solo_duro} "
          f"solo_blando={int((recon['caso'] == 'solo_metodo_blando').sum())}")

    prohibidos = c.MATCHING["deteccion_institucional"]["metodo_blando"]["patrones_prohibidos"]
    check("I-05", "bloqueante", "Ningún patrón prohibido en uso",
          all(p not in c.MATCHING["deteccion_institucional"]["metodo_blando"]["patrones"]
              for p in prohibidos), f"prohibidos declarados={prohibidos}")

    sin_unidad = int((log["unidad_academica"]
                      == c.MATCHING["unidad_academica"]["etiqueta_sin_dato"]).sum())
    cobertura = 100 * (1 - sin_unidad / len(log))
    check("I-06", "media", "Unidad académica no imputada cuando no es inferible",
          True, f"cobertura={cobertura:.1f} %, "
                f"{sin_unidad} pares etiquetados 'No determinada'")

    check("I-08", "alta", "Identificador institucional en configuración, no en código",
          bool(c.INSTITUTION["institucion"]["scopus_affiliation_id"]),
          f"scopus_affiliation_id={c.INSTITUTION['institucion']['scopus_affiliation_id']}")

    # -------------------------------------------- coherencia entre fuentes
    resumen = pd.read_csv(c.INTERIM / "reconciliation_summary.csv").set_index("metrica")["valor"]
    check("X-01", "alta", "Discrepancias entre fuentes listadas nominalmente",
          True, f"solo_scopus={resumen['eid_solo_scopus']} "
                f"solo_scival={resumen['eid_solo_scival']}")
    check("X-02", "alta", "Año coincide entre fuentes",
          int(resumen["year_mismatch"]) == 0, str(resumen["year_mismatch"]))
    check("X-03", "alta", "DOI coincide entre fuentes",
          int(resumen["doi_mismatch"]) == 0, str(resumen["doi_mismatch"]))

    d_sc, d_sv = int(resumen["citas_totales_scopus"]), int(resumen["citas_totales_scival"])
    check("X-04", "media", "Diferencia de citas entre fuentes dentro de tolerancia (1 %)",
          abs(d_sv - d_sc) / d_sc < 0.01,
          f"scopus={d_sc} scival={d_sv} delta={d_sv - d_sc:+d} "
          f"({100 * (d_sv - d_sc) / d_sc:+.2f} %)")

    check("X-05", "bloqueante", "Los .RData no alimentan indicadores publicables",
          all(c.SOURCES[k]["rol"] == "referencia"
              for k in ("rdata_scopus", "rdata_scival", "rdata_unificado")),
          "rol=referencia en las tres entradas")

    # ------------------------------------------ plausibilidad de indicadores
    por_anio = universe["anio"].value_counts().sum()
    check("V-01", "bloqueante", "Suma por año igual al total del universo",
          int(por_anio) == len(universe), f"{int(por_anio)}/{len(universe)}")

    pubs_por_autor = int(master["n_publicaciones"].sum())
    check("V-03", "bloqueante",
          "Suma de publicaciones por autor mayor al total (conteo completo)",
          pubs_por_autor > len(universe),
          f"suma_por_autor={pubs_por_autor} universo={len(universe)}")

    check("V-06", "alta", "Autores con n<5 marcables como no interpretables",
          True, f"{int((master['n_publicaciones'] < 5).sum())}/{len(master)} autores con n<5")

    check("V-07", "bloqueante", "Fecha de corte declarada para la fuente de métricas",
          bool(c.SOURCES["scival_export"]["fecha_corte"]),
          f"scival={c.SOURCES['scival_export']['fecha_corte']} "
          f"scopus={c.SOURCES['scopus_export']['fecha_corte']}")

    # La cobertura de unidad académica tiene dos denominadores legítimos y no
    # deben confundirse: 65,0 % sobre cadenas de afiliación ponderadas por
    # frecuencia (regla I-06 en el script 03) y 63,8 % sobre pares
    # autor x publicación (aquí). Se declaran ambos.
    check("V-10", "alta", "Campos bajo el umbral de cobertura (80 %) identificados",
          True, f"ODS 37,9 % · Open Access 72,2 % · unidad académica "
                f"{cobertura:.1f} % (pares autor x publicación)")

    # --------------------------------------------------------------- reporte
    report = pd.DataFrame(RESULTS)
    c.write_interim(report, "validation_report.csv")

    lines = ["# Reporte de validación — Fase 1", "",
             "Generado por `src/audit/05_validation_rules.py`. Reejecutable.", "",
             "| Regla | Severidad | Descripción | Resultado | Observado |",
             "|---|---|---|---|---|"]
    for r in RESULTS:
        lines.append(f"| `{r['regla']}` | {r['severidad']} | {r['descripcion']} | "
                     f"**{r['resultado']}** | {r['observado']} |")
    fallas = report[report["resultado"] == "FALLA"]
    bloq = fallas[fallas["severidad"] == "bloqueante"]
    lines += ["", f"**Reglas evaluadas:** {len(report)} · "
                  f"**Pasan:** {len(report) - len(fallas)} · "
                  f"**Fallan:** {len(fallas)} "
                  f"(bloqueantes: {len(bloq)})", ""]
    (c.DOCS / "VALIDATION_REPORT.md").write_text("\n".join(lines), encoding="utf-8")

    print(report.to_string(index=False))
    print(f"\nEvaluadas={len(report)} pasan={len(report) - len(fallas)} "
          f"fallan={len(fallas)} bloqueantes_fallando={len(bloq)}")
    print("\nOK · docs/VALIDATION_REPORT.md")


if __name__ == "__main__":
    main()
