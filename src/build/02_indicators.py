"""Build 02 — KPIs y series preagregadas.

Todo indicador emitido lleva su denominador, su confiabilidad y su nota
metodológica, tomados de `config/indicators.yml`. Un indicador con
`publicar: false` no se emite.

Salidas:
  data/processed/kpis.json
  data/processed/series.json
  data/processed/meta.json
"""

from __future__ import annotations

import statistics
from collections import Counter

import pandas as pd

import common_build as b
import sys

import grafo_coautoria as GC

if sys.platform == "win32":
    # La consola de Windows usa cp1252 por defecto: revienta cualquier print()
    # con caracteres como "→"/"—"/"·". Mismo patrón que src/enrich/orcid_openalex.py.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")



def main() -> None:
    b.banner("BUILD 02 — KPIS Y SERIES")
    b.require_validation()

    uni = b.load_universe()
    authorship = b.load_authorship()
    den = b.denominadores()

    anios = [b.to_num(a) for a in uni["anio"]]
    citas = [b.to_num(c) for c in uni["citas"] if b.to_num(c) is not None]
    fwci = [b.to_num(f) for f in uni["fwci"] if b.to_num(f) is not None]
    pct = [b.to_num(p) for p in uni["percentil_citacion"] if b.to_num(p) is not None]
    intl = sum(1 for x in uni["es_internacional"] if x == "True")

    def nota_firmas():
        return b.nota_p06(authorship["nombre_en_fuente"].nunique())

    def kpi(code, valor, sufijo=None, extra=None):
        spec = b.indicador(code)
        item = {
            "codigo": code,
            "nombre": spec["nombre"],
            "valor": valor,
            "sufijo": sufijo,
            "denominador": den.get(spec.get("denominador"), None),
            "denominador_nombre": spec.get("denominador"),
            "confiabilidad": spec["confiabilidad"],
            "nota": b.nota(code),
        }
        if extra:
            item.update(extra)
        return item

    kpis = [
        kpi("P-01", len(uni)),
        kpi("I-01", sum(citas)),
        kpi("I-02", round(sum(citas) / den["con_metricas"], 2)),
        kpi("I-03", round(statistics.mean(fwci), 2),
            extra={"mediana": round(statistics.median(fwci), 2),
                   "referencia": 1.0,
                   "referencia_etiqueta": "promedio mundial"}),
        kpi("C-01", round(100 * intl / den["con_metricas"], 1), sufijo="%"),
        kpi("P-06", authorship["nombre_en_fuente"].nunique(),
            extra={"etiqueta_valor": "formas de firma", "nota": nota_firmas()}),
    ]

    b.write_json({"meta": b.build_meta(), "kpis": kpis}, "kpis.json")
    for k in kpis:
        print(f"  {k['codigo']:6s} {k['nombre'][:38]:40s} {k['valor']}{k['sufijo'] or ''}")

    # --------------------------------------------------------------- series
    def por_anio(mask=None):
        c = Counter()
        for i, a in enumerate(anios):
            if a is None:
                continue
            if mask is None or mask(i):
                c[a] += 1
        return [{"anio": k, "n": c[k]} for k in sorted(c)]

    def multi_top(col, n=20):
        c = Counter()
        for v in uni[col]:
            for item in b.split_multi(v):
                c[item] += 1
        return [{"valor": k, "n": v} for k, v in c.most_common(n)]

    fwci_por_anio, citas_por_anio, sin_citas = [], [], []
    for a in sorted({x for x in anios if x is not None}):
        vals = [b.to_num(f) for f, y in zip(uni["fwci"], uni["anio"])
                if b.to_num(y) == a and b.to_num(f) is not None]
        cs = [b.to_num(f) for f, y in zip(uni["citas"], uni["anio"])
              if b.to_num(y) == a and b.to_num(f) is not None]
        # Un año sin ninguna publicación con métricas es posible en una carga
        # parcial. Se declara como año sin dato, que es lo que es; calcular una
        # media sobre cero elementos aborta el build y no dice nada.
        fwci_por_anio.append(
            {"anio": a, "n": len(vals),
             "valor": round(statistics.mean(vals), 2) if vals else None,
             "mediana": round(statistics.median(vals), 2) if vals else None})
        citas_por_anio.append({"anio": a, "n": sum(cs)})
        sin_citas.append(
            {"anio": a,
             "pct": round(100 * sum(1 for c in cs if c == 0) / len(cs), 1) if cs else None})

    # Ambos indicadores declaran `con_metricas` como denominador, así que se
    # calculan sobre esas filas y no sobre el universo entero: la diferencia son
    # las 7 publicaciones sin métricas, que si no aparecían como «sin dato» y
    # contradecían la propia nota del gráfico.
    con_metricas = uni[uni["tiene_metricas"] == "True"]

    oa = Counter()
    for v in con_metricas["open_access"]:
        vals = b.split_multi(v)
        if not vals:
            oa["Sin dato declarado"] += 1
        for item in vals:
            oa[item] += 1
    # Una publicación puede ser Gold en la revista y Green en el repositorio a la
    # vez: las barras no son partes de un total y no deben leerse como tales.
    oa_multi = sum(1 for v in con_metricas["open_access"] if len(b.split_multi(v)) > 1)

    sjr_pct = [b.to_num(p) for p in con_metricas["sjr_percentil"]
               if b.to_num(p) is not None]
    # Menor percentil = mejor posición: verificado contra el propio SJR
    # (corr -0,50) y contra CiteScore (corr -0,58) sobre estos mismos datos.
    cuartiles = [
        {"valor": "Q1", "n": sum(1 for p in sjr_pct if p <= 25)},
        {"valor": "Q2", "n": sum(1 for p in sjr_pct if 25 < p <= 50)},
        {"valor": "Q3", "n": sum(1 for p in sjr_pct if 50 < p <= 75)},
        {"valor": "Q4", "n": sum(1 for p in sjr_pct if p > 75)},
        {"valor": "Sin dato declarado", "n": len(con_metricas) - len(sjr_pct)},
    ]

    n_aut = [b.to_num(x) for x in uni["n_autores"] if b.to_num(x) is not None]
    bins = [(1, 1), (2, 3), (4, 6), (7, 10), (11, 20), (21, 10_000)]
    equipo = [{"valor": f"{lo}" if lo == hi else (f"{lo}-{hi}" if hi < 1000 else f"{lo}+"),
               "n": sum(1 for x in n_aut if lo <= x <= hi)} for lo, hi in bins]

    unidades_raw = authorship["unidad_academica"].fillna("No determinada")
    unidad = Counter(unidades_raw)

    # C-05 — red de coautoría. Reutiliza las mismas funciones de
    # grafo_coautoria.py (no una segunda cuenta): éste es el número que la
    # capa interna ya audita en data/interim/coauthorship_graph.json, y
    # series.json declara aquí el resumen público sobre el corpus completo,
    # sin filtrar — el recorte en vivo lo recalcula vista_explorador.js con
    # el mismo criterio (grafo.js, puerto verificado contra este mismo Python).
    fragmentos_e09 = b.firmas_e09_encoladas()
    unidades_persona = (authorship.dropna(subset=["unidad_academica"])
                        .groupby("nombre_en_fuente")["unidad_academica"].first().to_dict())
    g_c05 = GC.construir(zip(authorship["nombre_en_fuente"], authorship["eid"]),
                          excluir=fragmentos_e09, unidades=unidades_persona)
    comp_c05 = GC.componentes(g_c05["nodos"], g_c05["aristas"])
    coms_c05 = GC.comunidades(g_c05["nodos"], g_c05["aristas"])
    tam_c05 = GC._tamanos(comp_c05)
    conectadas_c05 = sum(1 for n in g_c05["nodos"] if tam_c05[comp_c05[n]] > 1)
    # Agregación a nivel de facultad: las escuelas suman a su facultad según la
    # jerarquía declarada en config. Kinesiología y Nutrición cuentan dentro de
    # Facultad de Medicina, no como unidades separadas.
    facultad = Counter(unidades_raw.map(b.facultad_de))

    series = {
        "meta": b.build_meta(),
        "P-02": {"nombre": b.indicador("P-02")["nombre"], "datos": por_anio(),
                 "nota": b.nota("P-02")},
        "P-03": {"nombre": b.indicador("P-03")["nombre"],
                 "datos": [{"valor": k, "n": v} for k, v in
                           Counter(uni["tipo_documental"].dropna()).most_common()],
                 "nota": b.nota("P-03")},
        "P-05": {"nombre": b.indicador("P-05")["nombre"],
                 "datos": [{"valor": k, "n": v} for k, v in
                           Counter(uni["fuente_titulo"].dropna()).most_common(20)],
                 "nota": b.nota("P-05"),
                 "total_fuentes": int(uni["source_id"].nunique())},
        "P-07": {"nombre": b.indicador("P-07")["nombre"],
                 "datos": [{"valor": k, "n": v} for k, v in facultad.most_common()],
                 "detalle_escuelas": [{"valor": k, "n": v, "facultad": b.facultad_de(k)}
                                      for k, v in unidad.most_common()],
                 "nota": b.nota("P-07")},
        "I-01": {"nombre": b.indicador("I-01")["nombre"], "datos": citas_por_anio,
                 "nota": b.nota("I-01")},
        "I-04": {"nombre": b.indicador("I-04")["nombre"], "datos": fwci_por_anio,
                 "sin_citas_pct": sin_citas, "nota": b.nota("I-04")},
        # Cada umbral viaja con lo que cabría ESPERAR bajo el promedio mundial:
        # por definición, el top k % de la distribución mundial contiene el k %
        # de las publicaciones. Sin esa referencia, «75 en el top 10 %» no dice
        # si es mucho o poco, y el lector no tiene forma de saberlo.
        "I-05": {"nombre": b.indicador("I-05")["nombre"],
                 "datos": [{"valor": f"Top {k} %",
                            "n": sum(1 for p in pct if p <= k),
                            "esperado": round(len(pct) * k / 100, 1)}
                           for k in (1, 5, 10, 25)],
                 "base_percentil": len(pct),
                 "nota": b.nota("I-05")},
        "R-01": {"nombre": b.indicador("R-01")["nombre"], "datos": cuartiles,
                 "nota": b.nota("R-01")},
        "A-01": {"nombre": b.indicador("A-01")["nombre"],
                 "datos": [{"valor": k, "n": v} for k, v in oa.most_common()],
                 "con_varias_etiquetas": oa_multi, "nota": b.nota("A-01")},
        "C-01": {"nombre": b.indicador("C-01")["nombre"],
                 "datos": [{"valor": "Internacional", "n": intl},
                           {"valor": "Nacional", "n": den["con_metricas"] - intl}],
                 "nota": b.nota("C-01")},
        "C-03": {"nombre": b.indicador("C-03")["nombre"], "datos": multi_top("paises", 15), "nota": b.nota("C-03")},
        "C-04": {"nombre": b.indicador("C-04")["nombre"], "datos": multi_top("instituciones", 15), "nota": b.nota("C-04")},
        "C-06": {"nombre": b.indicador("C-06")["nombre"], "datos": equipo,
                 "media": round(statistics.mean(n_aut), 1),
                 "mediana": statistics.median(n_aut), "nota": b.nota("C-06")},
        "C-05": {"nombre": b.indicador("C-05")["nombre"],
                 "resumen": {
                     "personas": len(g_c05["nodos"]),
                     "personas_con_coautoria": conectadas_c05,
                     "personas_aisladas": len(g_c05["nodos"]) - conectadas_c05,
                     "aristas": len(g_c05["aristas"]),
                     "publicaciones_con_dos_o_mas_personas": g_c05["publicaciones_con_dos_o_mas"],
                     "componentes": len(set(comp_c05.values())),
                     "componente_mayor": max(tam_c05.values()) if tam_c05 else 0,
                     "comunidades_louvain": len(set(coms_c05.values())),
                 },
                 "nota": b.nota("C-05")},
        "T-05": {"nombre": b.indicador("T-05")["nombre"], "datos": multi_top("qs_area", 10), "nota": b.nota("T-05")},
        "T-01": {"nombre": b.indicador("T-01")["nombre"], "datos": multi_top("asjc", 20), "nota": b.nota("T-01")},
        "T-04": {"nombre": b.indicador("T-04")["nombre"],
                 "datos": multi_top("ods", 20), "nota": b.nota("T-04"),
                 "con_ods": int(sum(1 for v in uni["ods"] if b.split_multi(v)))},
    }
    # La multivaluación se declara en config/indicators.yml, no aquí: un gráfico
    # cuyas barras no suman el total tiene que decirlo, y quién lo dice es la
    # ficha del indicador. El front lo usa para rotular el eje.
    for code, blk in series.items():
        if code != "meta" and b.indicador(code).get("multivaluado"):
            blk["multivaluado"] = True

    # Sello de procedencia por indicador. La cobertura REAL sólo se conoce aquí,
    # donde están los datos: fuera de estos casos el indicador se calcula sobre
    # su denominador completo. Publicar un N global para todos sería el error
    # que este proyecto persigue —el denominador cambia según el indicador—.
    cobertura_real = {
        "T-04": series["T-04"]["con_ods"],
        "A-01": len(con_metricas) - oa["Sin dato declarado"],
        "R-01": sum(d["n"] for d in cuartiles if d["valor"] != "Sin dato declarado"),
    }
    for code, blk in series.items():
        if code != "meta":
            blk["procedencia"] = b.procedencia(code, cobertura_real.get(code))

    # P-07 se calcula sobre pares autor x publicación, no sobre publicaciones:
    # una publicación firmada por gente de dos unidades aparece en las dos. Con
    # el denominador de publicaciones el sello daba 94,1 %, cuando la cobertura
    # que mide la auditoría (regla I-06) es del 63,8 %.
    series["P-07"]["procedencia"] = b.procedencia(
        "P-07",
        cubiertas=sum(v for k, v in unidad.items() if k != "No determinada"),
        n=sum(unidad.values()),
        unidad="pares autor × publicación")

    # C-05 tampoco se calcula sobre publicaciones: su denominador es personas,
    # no filas del universo, así que necesita el mismo tipo de sobrescritura
    # explícita que P-07 (el N genérico del indicador daría 0, sin denominador
    # declarado en config/indicators.yml a propósito — ver la nota ahí).
    series["C-05"]["procedencia"] = b.procedencia(
        "C-05", cubiertas=conectadas_c05, n=len(g_c05["nodos"]), unidad="personas")

    b.write_json(series, "series.json")
    b.write_json(b.build_meta(), "meta.json")
    print(f"  series: {len([k for k in series if k != 'meta'])} indicadores")

    catalogo()


def catalogo() -> None:
    """Los 40 indicadores evaluados, publicados o no, con por qué.

    EL PROBLEMA QUE RESUELVE
        El sitio publica 27 indicadores y no dice nada de los otros 13. El
        criterio —qué se midió, qué se descartó y por qué— vivía sólo en
        `docs/`, que no es el sitio. Un lector no puede distinguir «no se
        calculó» de «se calculó y salió mal» de «no se puede calcular sin
        inventar el dato», y las tres cosas significan lo contrario.

    POR QUÉ VIVE AQUÍ
        Se construye desde `config/indicators.yml`, el mismo archivo del que
        salen los KPI y las series de arriba. Un catálogo mantenido aparte
        diría lo que alguien recordó, no lo que el sitio publica: la única
        garantía de que «publicado» signifique publicado es que las dos cosas
        se lean del mismo sitio.

        La cobertura medida viene de `data/interim/indicator_feasibility.csv`,
        que la calcula sobre los datos. Ninguna cifra de esta vista está
        escrita a mano.
    """
    # Estado: publicado, o la razón de no estarlo. El orden importa —un
    # indicador no calculable que además fuera V2 es, ante todo, no calculable—.
    ETIQUETAS = {
        "publicado": ("Publicado", "Se calcula y se muestra en el sitio."),
        "no_calculable": ("No calculable", "La fuente no entrega el dato. "
                          "Aproximarlo sería inventar la métrica."),
        "fuera_de_alcance": ("Fuera de alcance", "Excluido por decisión de "
                             "alcance del proyecto, no por falta de datos."),
        "diferido": ("Diferido a V2", "Calculable y verificado, pero no se "
                     "publica en esta versión."),
    }
    CATEGORIAS = {"descriptivo": "Producción y descripción", "impacto": "Impacto",
                  "colaboracion": "Colaboración", "tematico": "Áreas temáticas"}

    fact = {}
    p = b.ROOT / "data" / "interim" / "indicator_feasibility.csv"
    if p.exists():
        fact = {r["codigo"]: r for _, r in pd.read_csv(p).fillna("").iterrows()}

    den = b.denominadores()
    filas = []
    for code, spec in b.INDICATORS["indicadores"].items():
        if spec.get("publicar"):
            estado = "publicado"
        elif spec.get("estado") in ("no_calculable", "fuera_de_alcance"):
            estado = spec["estado"]
        else:
            estado = "diferido"

        nombre_den = spec.get("denominador")
        f = fact.get(code, {})
        filas.append({
            "codigo": code,
            "nombre": spec["nombre"],
            "categoria": spec.get("categoria"),
            "categoria_etiqueta": CATEGORIAS.get(spec.get("categoria"), "Otros"),
            # La procedencia se afirma sólo de lo que se calcula. Un indicador
            # no calculable no tiene fuente: tiene un motivo, y ese motivo va en
            # su propia fila. Poner «Scopus · SciVal» sugeriría que el dato
            # vendría de ahí, y de los cuatro no calculables sólo es cierto para
            # dos —a `X-03` le falla la cobertura y a `X-04` la ventana, no la
            # fuente—. Una etiqueta única para los cuatro sería falsa en la
            # mitad.
            "fuente": (b.FUENTE_POR_INDICADOR.get(code, "Scopus · SciVal")
                       if estado in ("publicado", "diferido") else None),
            "denominador": nombre_den,
            "denominador_valor": den.get(nombre_den),
            "confiabilidad": spec.get("confiabilidad"),
            "estado": estado,
            "estado_etiqueta": ETIQUETAS[estado][0],
            "estado_detalle": ETIQUETAS[estado][1],
            # `razon` explica por qué no se publica; `advertencia` cualifica lo
            # que sí se publica. No son lo mismo y no se funden en un campo.
            "razon": spec.get("razon"),
            "que_falta": spec.get("que_falta"),
            "advertencia": spec.get("advertencia"),
            "advertencia_destacada": bool(spec.get("advertencia_destacada")),
            "cobertura": f.get("cobertura_medida") or None,
            "definicion": f.get("nota_metodologica") or None,
        })

    resumen = {e: sum(1 for r in filas if r["estado"] == e) for e in ETIQUETAS}
    b.write_json({"meta": b.build_meta(), "resumen": resumen,
                  "categorias": CATEGORIAS, "etiquetas_estado": ETIQUETAS,
                  "indicadores": filas}, "catalogo.json")
    print("  catálogo: " + " · ".join(
        f"{n} {ETIQUETAS[e][0].lower()}" for e, n in resumen.items() if n))


if __name__ == "__main__":
    main()
