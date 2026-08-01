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

import common_build as b


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
            extra={"etiqueta_valor": "formas de firma"}),
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
        "I-05": {"nombre": b.indicador("I-05")["nombre"],
                 "datos": [{"valor": f"Top {k} %", "n": sum(1 for p in pct if p <= k)}
                           for k in (1, 5, 10, 25)],
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

    b.write_json(series, "series.json")
    b.write_json(b.build_meta(), "meta.json")
    print(f"  series: {len([k for k in series if k != 'meta'])} indicadores")


if __name__ == "__main__":
    main()
