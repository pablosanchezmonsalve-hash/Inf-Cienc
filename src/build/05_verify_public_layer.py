"""Build 05 — Verificación automática de la barrera pública/interna (T-12).

La separación de capas no puede depender de que nadie se equivoque al escribir
un build (decisión D-23). Este script recorre todo `data/processed/` y falla si
encuentra rastro de la capa interna.

Falla el build con código distinto de cero: es una compuerta, no un aviso.

Salida:
  docs/BUILD_VERIFICATION.md
"""

from __future__ import annotations

import json
import sys

import common_build as b

FALLAS: list[dict] = []


def revisar(obj, ruta: str, archivo: str) -> None:
    """Recorre el JSON buscando claves prohibidas en cualquier profundidad."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in b.CAMPOS_PROHIBIDOS:
                FALLAS.append({
                    "archivo": archivo, "ruta": f"{ruta}.{k}",
                    "problema": "campo de capa interna presente en artefacto público",
                })
            revisar(v, f"{ruta}.{k}", archivo)
    elif isinstance(obj, list):
        # Sin muestreo: una compuerta que sólo mira una parte no es una
        # compuerta. La lista más larga de los artefactos tiene 823 elementos y
        # el recorrido completo de los 596 archivos cuesta menos de un segundo.
        for i, v in enumerate(obj):
            revisar(v, f"{ruta}[{i}]", archivo)


def main() -> int:
    b.banner("BUILD 05 — VERIFICACIÓN DE BARRERA PÚBLICA/INTERNA")

    archivos = sorted(b.PROCESSED.rglob("*.json"))
    if not archivos:
        sys.exit("BUILD ABORTADO: no hay artefactos en data/processed/.")

    for path in archivos:
        rel = path.relative_to(b.PROCESSED).as_posix()
        with open(path, encoding="utf-8") as fh:
            revisar(json.load(fh), "$", rel)

    # Procedencia obligatoria: un artefacto sin fecha de corte no es
    # interpretable fuera de contexto (regla V-07 de Fase 1).
    sin_meta = []
    for path in archivos:
        if path.parent.name == "author":
            continue
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict) and "meta" not in data and path.name != "meta.json":
            sin_meta.append(path.name)
    for nombre in sin_meta:
        FALLAS.append({"archivo": nombre, "ruta": "$.meta",
                       "problema": "artefacto sin bloque de procedencia"})

    total_kb = sum(p.stat().st_size for p in archivos) / 1024
    fichas = len(list((b.PROCESSED / "author").glob("*.json")))

    print(f"  artefactos revisados : {len(archivos)} ({total_kb:.0f} KB)")
    print(f"  fichas de autor      : {fichas}")
    print(f"  campos prohibidos    : {len(b.CAMPOS_PROHIBIDOS)} vigilados")
    print(f"  fallas               : {len(FALLAS)}")

    lineas = [
        "# Verificación del build", "",
        "Generado por `src/build/05_verify_public_layer.py`. Reejecutable.", "",
        f"- Artefactos revisados: **{len(archivos)}** ({total_kb:.0f} KB)",
        f"- Fichas de autor: **{fichas}**",
        f"- Campos de capa interna vigilados: {', '.join(f'`{c}`' for c in b.CAMPOS_PROHIBIDOS)}",
        "",
    ]
    if FALLAS:
        lineas += ["## Fallas", "", "| Archivo | Ruta | Problema |", "|---|---|---|"]
        lineas += [f"| `{f['archivo']}` | `{f['ruta']}` | {f['problema']} |" for f in FALLAS]
        for f in FALLAS:
            print(f"    FALLA · {f['archivo']} :: {f['ruta']} — {f['problema']}")
    else:
        lineas.append("**Sin fallas.** Ningún artefacto público contiene campos de la "
                      "capa interna y todos declaran su procedencia.")
    (b.DOCS / "BUILD_VERIFICATION.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")

    return 1 if FALLAS else 0


if __name__ == "__main__":
    sys.exit(main())
