"""01 — Inventario de archivos y columnas.

Genera de forma reproducible los inventarios exigidos por PROMPT_FASE_1 §3 y §4.

Salidas:
  data/interim/inventory_files.csv
  data/interim/inventory_columns.csv
"""

from __future__ import annotations

import pandas as pd

import common as c


def profile_columns(df: pd.DataFrame, source: str) -> pd.DataFrame:
    n = len(df)
    rows = []
    for col in df.columns:
        s = df[col]
        non_null = int(s.notna().sum())
        # En estos exports el guion suelto es el marcador de dato ausente.
        useful = int((s.notna() & (s.astype(str).str.strip() != "-")).sum())
        sample = ""
        vals = s.dropna()
        if len(vals):
            sample = str(vals.iloc[0])[:120]
        rows.append({
            "fuente": source,
            "campo": str(col),
            "n_filas": n,
            "no_nulos": non_null,
            "pct_no_nulos": round(100 * non_null / n, 1) if n else 0.0,
            "con_valor_util": useful,
            "pct_con_valor_util": round(100 * useful / n, 1) if n else 0.0,
            "cardinalidad": int(s.nunique(dropna=True)),
            "ejemplo": sample,
        })
    return pd.DataFrame(rows)


def main() -> None:
    c.banner("01 — INVENTARIO DE ARCHIVOS Y COLUMNAS")

    scopus = c.read_scopus()
    scival = c.read_scival()
    meta = c.read_scival_export_metadata()

    frames = {
        "scopus_export": scopus,
        "scival_export": scival,
        "reporte_investigadores": c.read_report_sheet("investigadores"),
        "reporte_detalle": c.read_report_sheet("publicaciones_detalle"),
        "reporte_unificadas": c.read_report_sheet("publicaciones_unificadas"),
    }

    # Los .RData son fuentes de referencia (decisión D-05). Si el paquete
    # `rdata` no está instalado se omiten del inventario y se declara: la
    # auditoría no depende de ellos.
    rdata_omitidos = []
    for key in ("rdata_scopus", "rdata_scival", "rdata_unificado"):
        df = c.read_rdata(key)
        if df is None:
            rdata_omitidos.append(key)
        else:
            frames[key] = df

    files = []
    for key, df in frames.items():
        spec = c.SOURCES.get(key, {})
        files.append({
            "clave": key,
            "archivo": spec.get("archivo", "(hoja de reporte_excel_2026)"),
            "formato": spec.get("formato", "xlsx"),
            "rol": spec.get("rol", "validacion"),
            "filas": len(df),
            "columnas": df.shape[1],
            "fecha_corte": spec.get("fecha_corte"),
            "ventana_declarada": spec.get("ventana_declarada"),
        })
    files_df = pd.DataFrame(files)

    cols_df = pd.concat(
        [profile_columns(df, key) for key, df in frames.items()],
        ignore_index=True,
    )

    c.write_interim(files_df, "inventory_files.csv")
    c.write_interim(cols_df, "inventory_columns.csv")

    print(files_df.to_string(index=False))
    if rdata_omitidos:
        print(f"\n  aviso · fuentes de referencia omitidas (paquete `rdata` no "
              f"instalado): {', '.join(rdata_omitidos)}")

    print("\n--- Metadatos declarados por el export de SciVal ---")
    for k, v in meta.items():
        print(f"  {k}: {v}")

    vacias = cols_df[cols_df["pct_no_nulos"] == 0.0]
    print(f"\nE-06 · columnas con 0 % de cobertura: {len(vacias)}")
    for _, r in vacias.iterrows():
        print(f"    {r['fuente']} :: {r['campo']}")

    # Grupos no capturantes: con grupos normales pandas avisa que el patrón
    # tiene captura y sugiere str.extract, aunque aquí sólo interesa el booleano.
    residuo = cols_df[cols_df["campo"].str.contains(r"\.(?:x|y)(?:\.(?:x|y))*$", regex=True)]
    print(f"\nE-07 · columnas residuales de join: {len(residuo)}")
    for _, r in residuo.iterrows():
        print(f"    {r['fuente']} :: {r['campo']}")

    print("\nOK · data/interim/inventory_files.csv, inventory_columns.csv")


if __name__ == "__main__":
    main()
