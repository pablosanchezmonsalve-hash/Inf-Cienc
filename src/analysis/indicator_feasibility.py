"""Fase 2 — Verificación de factibilidad de los indicadores candidatos.

Mide, sobre los datos reales, si cada indicador del catálogo puede calcularse y
con qué cobertura. Ningún indicador entra al catálogo sin pasar por aquí: la
columna "disponible" de docs/INDICATORS.md es salida de este script.

No calcula los indicadores para su publicación (eso es Fase 3). Sólo determina
si son calculables y con qué confiabilidad.

Salida:
  data/interim/indicator_feasibility.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audit"))
import common as c  # noqa: E402

RESULTS: list[dict] = []



def _tamano_red(log: pd.DataFrame) -> dict[str, int]:
    """Qué tamaño tendría la red de coautoría con los datos de hoy.

    Se cuenta sobre PERSONAS, aplicando la consolidación de identidades
    vigente, y sobre pares DISTINTOS: una firma repetida dentro de una misma
    publicación no es una coautoría consigo misma.
    """
    import itertools
    import yaml

    # Se lee el YAML directamente en vez de importar el mapa del build: este
    # módulo es de análisis y no depende de la capa de construcción.
    ruta = c.ROOT / "config" / "identidades_consolidadas.yml" if hasattr(c, "ROOT") \
        else Path(__file__).resolve().parents[2] / "config" / "identidades_consolidadas.yml"
    mapa: dict[str, str] = {}
    if ruta.exists():
        cfg = yaml.safe_load(ruta.read_text(encoding="utf-8")) or {}
        mapa = {v: g["canonica"] for g in (cfg.get("grupos") or [])
                for v in g["variantes"]}

    persona = log["nombre_en_fuente"].map(lambda n: mapa.get(n, n))
    par = pd.DataFrame({"persona": persona, "eid": log["eid"]}).drop_duplicates()
    por_pub = par.groupby("eid")["persona"].apply(list)
    multi = [p for p in por_pub if len(p) > 1]
    aristas = {tuple(sorted(x)) for ps in multi
               for x in itertools.combinations(sorted(set(ps)), 2)}
    nodos = {p for a in aristas for p in a}
    return {"pares": len(par), "pubs": int(par["eid"].nunique()),
            "pubs_multi": len(multi), "aristas": len(aristas), "nodos": len(nodos)}


def record(code: str, nombre: str, categoria: str, disponible: str,
           cobertura: str, confiabilidad: str, prioridad: str, nota: str) -> None:
    RESULTS.append({
        "codigo": code, "indicador": nombre, "categoria": categoria,
        "disponible": disponible, "cobertura_medida": cobertura,
        "confiabilidad": confiabilidad, "prioridad_v1": prioridad,
        "nota_metodologica": nota,
    })


def numeric(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_numeric(df[col].replace("-", np.nan), errors="coerce")


def h_index(values: pd.Series) -> int:
    vals = sorted([v for v in values if pd.notna(v)], reverse=True)
    return sum(1 for i, v in enumerate(vals, 1) if v >= i)


def main() -> None:
    c.banner("FASE 2 — FACTIBILIDAD DE INDICADORES")

    scival = c.read_scival()
    universe = pd.read_csv(c.INTERIM / "publications_universe.csv")
    log = pd.read_csv(c.INTERNAL / "matching_log.csv", dtype=str)
    master = pd.read_csv(c.INTERIM / "authors_master_draft.csv")

    n_uni = len(universe)
    n_met = int(universe["tiene_metricas"].sum())
    n_aut = int(universe["tiene_autoria_detallada"].sum())

    # ------------------------------------------------ descriptivos / desempeño
    record("P-01", "Publicaciones totales", "descriptivo", "sí",
           f"{n_uni}/{n_uni} (100 %)", "alta", "V1",
           "Conteo de publicaciones únicas. Denominador institucional base.")

    por_anio = universe["anio"].value_counts().sort_index()
    # Se formatea como texto, no se vuelca el diccionario: `dict()` sobre una
    # Series conserva los `np.int64` de pandas, y el repr de esos objetos
    # —«{2023: np.int64(228)}»— acababa impreso tal cual. Mientras esta cadena
    # vivía en una nota interna de factibilidad era feo; desde que el catálogo
    # la publica, es una página pública enseñando el tipo de dato de su propio
    # intérprete. Esta columna la lee una persona.
    record("P-02", "Producción anual", "descriptivo", "sí",
           f"{int(por_anio.sum())}/{n_uni} · "
           + " · ".join(f"{int(a)}: {int(n)}" for a, n in por_anio.items()),
           "alta", "V1",
           "Serie de 3 puntos. Insuficiente para tendencia de largo plazo.")

    tipos = universe["tipo_documental"].value_counts()
    record("P-03", "Distribución por tipo documental", "descriptivo", "sí",
           f"{int(universe['tipo_documental'].notna().sum())}/{n_uni} · "
           f"{len(tipos)} tipos", "alta", "V1",
           "Permite excluir tipos no citables del cálculo de impacto.")

    record("P-04", "Revistas/fuentes distintas", "descriptivo", "sí",
           f"{scival['Source ID'].nunique()} Source ID en {n_met} publicaciones",
           "alta", "V1", "Source ID de SciVal es mejor clave que el ISSN.")

    record("P-05", "Ranking de fuentes por volumen", "descriptivo", "sí",
           f"{scival['Scopus Source title'].nunique()} títulos", "alta", "V1",
           "Volumen, no calidad. No ordenar por métrica de revista por defecto.")

    record("P-06", "Autores afiliados distintos", "descriptivo", "parcial",
           f"{len(master)} formas de firma", "media", "V1",
           "589 formas de firma, no 589 personas: 123 variantes de nombre y 20 "
           "perfiles Scopus fragmentados sin resolver (ver LIMITATIONS §2).")

    unidad_ok = int((log["unidad_academica"] != "No determinada").sum())
    record("P-07", "Producción por unidad académica", "descriptivo", "parcial",
           f"{unidad_ok}/{len(log)} pares ({100 * unidad_ok / len(log):.1f} %)",
           "baja", "V1 con advertencia",
           "Cobertura 63,8 % y vocabulario no validado institucionalmente. "
           "Además el sesgo de cobertura de Scopus distorsiona la comparación "
           "entre unidades. Requiere advertencia visible obligatoria.")

    idioma = c.read_scopus()["Language of Original Document"]
    record("P-08", "Distribución por idioma", "descriptivo", "sí",
           f"{idioma.notna().sum()}/{n_aut} · {idioma.nunique()} idiomas",
           "alta", "V2", "Bajo valor analítico inmediato; útil para cobertura.")

    # ------------------------------------------------------------- impacto
    citas = numeric(scival, "Citations")
    record("I-01", "Citas totales", "impacto", "sí",
           f"{int(citas.notna().sum())}/{n_uni} · total={int(citas.sum())}",
           "alta", "V1",
           "Fuente única SciVal, corte 2026-07-22. Scopus reporta 3.909 "
           "(Δ +26); se adopta SciVal por declarar fecha de corte.")

    record("I-02", "Citas por publicación", "impacto", "sí",
           f"{citas.sum() / n_met:.2f} sobre {n_met} publicaciones con métrica",
           "alta", "V1",
           "Denominador = publicaciones con métrica (816), no 823. "
           "Declarar denominador junto al valor.")

    fwci = numeric(scival, "Field-Weighted Citation Impact")
    record("I-03", "FWCI institucional", "impacto", "sí",
           f"{int(fwci.notna().sum())}/{n_uni} · media={fwci.mean():.2f} "
           f"mediana={fwci.median():.2f}", "media", "V1",
           "Se calcula sobre el conjunto, NUNCA como promedio de FWCI "
           "individuales. Mediana (0,41) muy por debajo de la media (0,87): "
           "distribución fuertemente asimétrica, mostrar ambas.")

    sin_citas_2025 = int((citas[scival["Year"] == "2025"] == 0).sum())
    n_2025 = int((scival["Year"] == "2025").sum())
    record("I-04", "FWCI por año", "impacto", "parcial",
           f"2023={fwci[scival['Year'] == '2023'].mean():.2f} · "
           f"2024={fwci[scival['Year'] == '2024'].mean():.2f} · "
           f"2025={fwci[scival['Year'] == '2025'].mean():.2f}",
           "baja", "V1 con advertencia",
           f"El {100 * sin_citas_2025 / n_2025:.0f} % de las publicaciones de "
           "2025 no tiene citas aún. El FWCI del año más reciente no es "
           "comparable con el de 2023.")

    # Semántica del percentil determinada empíricamente, no supuesta.
    top = numeric(scival, "Outputs in Top Citation Percentiles, per percentile")
    corr = top.corr(citas)
    top10 = int((top <= 10).sum())
    record("I-05", "Publicaciones en el top 10 % de citación", "impacto", "sí",
           f"{top10}/{n_met} ({100 * top10 / n_met:.1f} %) · "
           f"corr(percentil, citas)={corr:.2f}", "alta", "V1",
           "La columna entrega el percentil de la publicación, donde menor = "
           "mejor. Semántica verificada empíricamente: correlación -0,66 con "
           "citas; las 3 más citadas tienen percentil 1-3 y las no citadas "
           "56-78. El nombre de la columna no lo declara.")

    views = numeric(scival, "Views")
    record("I-06", "Visualizaciones (Views)", "impacto", "sí",
           f"{int(views.notna().sum())}/{n_uni} · total={int(views.sum())}",
           "media", "V2",
           "Visibilidad, NO impacto. Reportar en módulo separado y nunca "
           "junto a citas sin distinguirlas.")

    # ---------------------------------------------- métricas de revista
    sjrp = numeric(scival, "SJR percentile (publication year) *")
    q1 = int((sjrp <= 25).sum())
    record("R-01", "Publicaciones en revistas Q1 (percentil SJR)", "impacto", "parcial",
           f"{q1}/{int(sjrp.notna().sum())} cubiertos "
           f"({100 * q1 / sjrp.notna().sum():.1f} %) · cobertura "
           f"{100 * sjrp.notna().sum() / n_met:.1f} %", "media", "V1",
           "Métrica de la REVISTA, no del artículo. 'Q1' = percentil <= 25. "
           "Nunca presentar como calidad del trabajo individual.")

    csp = numeric(scival, "CiteScore percentile (publication year) *")
    record("R-02", "Percentil CiteScore de la fuente", "impacto", "sí",
           f"{int(csp.notna().sum())}/{n_met} "
           f"({100 * csp.notna().sum() / n_met:.1f} %)", "media", "V2",
           "Alternativa a SJR. Elegir uno como principal para no duplicar "
           "lecturas del mismo fenómeno.")

    record("R-03", "SNIP de la fuente", "impacto", "sí",
           f"{int(numeric(scival, 'SNIP (publication year)').notna().sum())}/{n_met}",
           "media", "V2", "Tercera métrica de revista. Redundante para V1.")

    # ------------------------------------------------------- colaboración
    npais = numeric(scival, "Number of Countries/Regions")
    intl = int((npais > 1).sum())
    record("C-01", "Colaboración internacional", "colaboracion", "sí",
           f"{intl}/{n_met} ({100 * intl / n_met:.1f} %)", "alta", "V1",
           "Definida como publicación con más de un país. Indicador robusto: "
           "cobertura 100 % de las publicaciones con métrica.")

    ninst = numeric(scival, "Number of Institutions")
    solo = int((ninst == 1).sum())
    record("C-02", "Publicaciones sin colaboración institucional", "colaboracion", "sí",
           f"{solo}/{n_met} ({100 * solo / n_met:.1f} %)", "alta", "V1",
           "Una sola institución participante. Complemento de C-01.")

    record("C-03", "Países colaboradores", "colaboracion", "sí",
           f"{int(npais.notna().sum())}/{n_met} · media={npais.mean():.2f} países",
           "alta", "V1", "Lista multivaluada; el ranking de países no es sumable.")

    record("C-04", "Instituciones colaboradoras", "colaboracion", "sí",
           f"{int(ninst.notna().sum())}/{n_met} · media={ninst.mean():.2f}",
           "alta", "V1",
           "SciVal advierte truncamiento en 'Affiliation names'. Usar "
           "Institution IDs como clave.")

    # Las cifras se MIDEN aquí en vez de escribirse. La anterior decía
    # «derivable de 1207 pares autor x publicación» y 1207 son las FILAS del
    # log, o sea apariciones: una firma que ocupa tres posiciones de la misma
    # publicación —«School of Psychology», un fragmento de cadena de afiliación
    # que la regla E-09 ya detecta— se contaba tres veces. Los pares distintos
    # son 1205, y sobre todo no son lo que describe a este indicador: lo que
    # describe una red es cuántas publicaciones tienen DOS o más personas UFT,
    # porque las demás no producen ninguna arista.
    red = _tamano_red(log)
    record("C-05", "Red de coautoría autor-autor", "colaboracion", "parcial",
           f"{red['aristas']} pares de coautoría entre {red['nodos']} personas, "
           f"derivados de las {red['pubs_multi']} publicaciones con 2+ personas UFT "
           f"(de {red['pubs']}); {red['pares']} pares persona x publicación",
           "media", "V2",
           "Técnicamente derivable, pero hereda las variantes de nombre sin "
           "resolver: la red tendría nodos duplicados. Diferido hasta T-03.")

    nau = numeric(scival, "Number of Authors")
    record("C-06", "Autores por publicación", "colaboracion", "sí",
           f"{int(nau.notna().sum())}/{n_met} · media={nau.mean():.2f} "
           f"mediana={nau.median():.0f}", "alta", "V1",
           "Media 7,0 y mediana 5: distribución asimétrica, preferir mediana.")

    roles = scival["Scopus Author ID First Author"].replace("-", np.nan)
    record("C-07", "Liderazgo autoral (primer/último/correspondencia)",
           "colaboracion", "parcial",
           f"first={int(roles.notna().sum())}/{n_met} "
           f"({100 * roles.notna().sum() / n_met:.1f} %)", "media", "V2",
           "Requiere cruzar Scopus Author ID con la tabla maestra, que tiene "
           "20 perfiles fragmentados. Diferido hasta T-04.")

    # ------------------------------------------------- conceptuales/temáticos
    def multivalued(col: str) -> tuple[int, int, int]:
        s = scival[col].replace("-", np.nan).dropna()
        vals = [v.strip() for x in s for v in str(x).split("|")]
        return len(s), len(set(vals)), len(vals)

    cov, cats, asg = multivalued("All Science Journal Classification (ASJC) field name")
    record("T-01", "Áreas temáticas ASJC", "tematico", "sí",
           f"{cov}/{n_met} · {cats} categorías · {asg} asignaciones",
           "media", "V1",
           "Clasifica la REVISTA, no el artículo. Multivaluado: las "
           "asignaciones (1.796) exceden las publicaciones (816). No "
           "presentar como partición ni sumar porcentajes a 100 %.")

    cov, cats, _ = multivalued("Topic name")
    record("T-02", "Topics de SciVal", "tematico", "sí",
           f"{cov}/{n_met} ({100 * cov / n_met:.1f} %) · {cats} topics",
           "media", "V2",
           "Clúster de co-citación asignado al documento: mejor granularidad "
           "que ASJC. 632 topics para 794 publicaciones: demasiado disperso "
           "para vista principal. Útil en la ficha de publicación.")

    prom = numeric(scival, "Topic Prominence Percentile")
    record("T-03", "Prominencia temática", "tematico", "sí",
           f"{int(prom.notna().sum())}/{n_met}", "baja", "V2",
           "Mide la atención del campo, NO el desempeño de la institución en él. "
           "Alto riesgo de malinterpretación; requiere glosario si se publica.")

    cov, cats, asg = multivalued("Sustainable Development Goals (2025)")
    record("T-04", "Objetivos de Desarrollo Sostenible", "tematico", "parcial",
           f"{cov}/{n_met} ({100 * cov / n_met:.1f} %) · {cats} ODS",
           "baja", "V1 sólo como recuento",
           "Cobertura 38 %. Publicable únicamente como 'n publicaciones con "
           "ODS asignado', nunca como distribución porcentual del total.")

    cov, cats, _ = multivalued("Quacquarelli Symonds (QS) Subject area field name")
    record("T-05", "Áreas QS (agregado grueso)", "tematico", "sí",
           f"{cov}/{n_met} · {cats} áreas", "media", "V1",
           "Sólo 5 categorías: útil como vista de entrada antes de bajar a "
           "ASJC. Multivaluado igual que ASJC.")

    # ------------------------------------------------------- acceso abierto
    oa = scival["Open Access"]
    record("A-01", "Publicaciones en acceso abierto", "descriptivo", "parcial",
           f"{int(oa.notna().sum())}/{n_met} ({100 * oa.notna().mean():.1f} %)",
           "media", "V1 con advertencia",
           "La ausencia de valor NO equivale a 'no OA'. Reportar como "
           "'n con estado OA declarado', con la no-cobertura visible.")

    # ------------------------------------------------------- nivel autor
    sv_idx = scival.set_index("EID")
    merged = log.merge(
        sv_idx[["Citations", "Field-Weighted Citation Impact"]],
        left_on="eid", right_index=True, how="left")
    merged["cit"] = pd.to_numeric(merged["Citations"].replace("-", np.nan), errors="coerce")

    por_autor = merged.groupby("nombre_en_fuente").agg(
        n_pub=("eid", "nunique"), citas=("cit", "sum"))
    por_autor["h"] = merged.groupby("nombre_en_fuente")["cit"].apply(h_index)
    n5 = int((por_autor["n_pub"] >= 5).sum())

    record("AU-01", "Publicaciones por autor", "descriptivo", "sí",
           f"{len(por_autor)} autores · {n5} con n>=5", "media", "V1",
           "Conteo completo: la suma por autor (1.205) excede el total de "
           "publicaciones (823). No presentar como total institucional.")

    record("AU-02", "Citas por autor", "impacto", "sí",
           f"{int(por_autor['citas'].sum())} citas atribuidas (conteo completo)",
           "media", "V1",
           "Atribución completa: una publicación con 3 autores afiliados aporta sus "
           "citas 3 veces. No sumable a nivel institucional.")

    record("AU-03", "h-index en ventana 2023-2025", "impacto", "parcial",
           f"calculable para {len(por_autor)} autores · "
           f"max={int(por_autor['h'].max())} · "
           f"{int((por_autor['h'] <= 1).sum())} autores con h<=1",
           "baja", "V1 sólo en ficha, etiquetado",
           "NO es el h-index de carrera. Con ventana de 3 años, 497 de 589 "
           "autores tienen h<=1: el indicador no discrimina. Etiquetar "
           "siempre 'h-index en ventana 2023-2025'.")

    record("AU-04", "FWCI por autor", "impacto", "no", "—", "no aplicable",
           "descartado",
           "El FWCI de un autor no es el promedio de los FWCI de sus "
           "publicaciones. SciVal no entrega FWCI a nivel autor en este "
           "export. Calcularlo sería inventar una métrica. Se declara no "
           "disponible (CLAUDE.md: placeholder metodológico).")

    record("AU-05", "ORCID en ficha de autor", "descriptivo", "no",
           "0/589", "no disponible", "placeholder V1",
           "No existe en ninguna fuente. Recuperable vía Crossref por DOI "
           "(cobertura 97,7 %) — pendiente T-01. El campo se muestra con "
           "leyenda 'no disponible', no se oculta.")

    record("AU-06", "Evolución temporal por autor", "descriptivo", "sí",
           f"{len(por_autor)} autores con anio_min/anio_max", "media", "V1",
           "Con 3 años, es un gráfico de 3 puntos. Presentar como barras, no "
           "como línea de tendencia.")

    # --------------------------------------------------------- no calculables
    record("X-01", "Autocitas / tasa de autocitación", "impacto", "no",
           "el export declara 'Self-citations: -'", "no disponible",
           "descartado V1",
           "SciVal no incluyó autocitas en este export. Requiere reexportar "
           "con la opción activada.")

    record("X-02", "Benchmarking con otras instituciones", "impacto", "no",
           "sin datos de instituciones comparables", "no disponible",
           "fuera de alcance V1",
           "Excluido explícitamente por PROJECT_SPEC <out_of_scope_for_v1>.")

    record("X-03", "Indicadores de financiamiento", "descriptivo", "no",
           "306/818 (37,4 %) en Scopus", "insuficiente", "descartado V1",
           "Cobertura demasiado baja para reportar sin sesgo.")

    record("X-04", "Tendencia de largo plazo", "descriptivo", "no",
           "ventana 2023-2025", "no disponible", "fuera de alcance V1",
           "Sin datos previos a 2023. Tres puntos no sostienen una tendencia.")

    # ------------------------------------------------------------- salida
    df = pd.DataFrame(RESULTS)
    c.write_interim(df, "indicator_feasibility.csv")

    print(df.groupby(["categoria", "disponible"]).size().to_string())
    print(f"\nTotal de indicadores evaluados: {len(df)}")
    print(df["prioridad_v1"].value_counts().to_string())
    print("\nOK · data/interim/indicator_feasibility.csv")


if __name__ == "__main__":
    main()
