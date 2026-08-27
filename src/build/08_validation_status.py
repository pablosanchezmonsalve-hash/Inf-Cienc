"""Build 08 — Estado de la auditoría de datos, para publicar (V2-27).

QUÉ RESUELVE
    `docs/VALIDATION_REPORT.md` (`src/audit/05_validation_rules.py`) ya
    prueba, regla por regla, que el corpus es internamente consistente —
    pero vive sólo en `docs/`, dentro del repositorio: nadie que mire el
    sitio publicado puede verlo. Un informe que se declara metodológicamente
    riguroso y no deja ver su propia auditoría le pide al lector que confíe
    sin poder comprobar.

QUÉ PUBLICA, Y QUÉ NO
    Las 30 reglas SON publicables tal cual: son hechos sobre la consistencia
    del pipeline (¿hay EID repetidos?, ¿cuadra la suma por año?, ¿está la
    fecha de corte declarada?), no notas de depuración interna ni datos de
    ninguna persona. Se publica la tabla completa — igual que
    `docs/VALIDATION_REPORT.md`, no un resumen que esconda cuál regla es la
    que falla.

    Lo que NO se publica es el resto de `data/interim/` ni `internal/`: esta
    es la única lectura de `data/interim/validation_report.csv` que cruza a
    capa pública, y sólo las cinco columnas que ya son la tabla de
    `docs/VALIDATION_REPORT.md`.

CAPA
    Este script SÍ escribe a `data/processed/` (capa pública) — es la
    excepción declarada a la regla general de que `src/audit/` nunca escribe
    ahí. Léase con `05_verify_public_layer.py`: si algún día una regla
    empezara a describir algo interno (una firma sin forma de persona, una
    afiliación cruda), la compuerta pública/interna seguiría corriendo
    después de este script y lo atraparía igual.

Salida:
    data/processed/validacion.json
"""

from __future__ import annotations

import sys

import pandas as pd

import common_build as b

if sys.platform == "win32":
    # La consola de Windows usa cp1252 por defecto: revienta cualquier print()
    # con caracteres como "→"/"✗"/"⚠". Mismo patrón que src/enrich/orcid_openalex.py.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPORTE = b.ROOT / "data" / "interim" / "validation_report.csv"


def main() -> None:
    b.banner("BUILD 08 — ESTADO DE LA AUDITORÍA DE DATOS")

    if not REPORTE.exists():
        sys.exit(f"Falta {REPORTE.relative_to(b.ROOT)}. Ejecute: python3 src/audit/run_all.py")

    df = pd.read_csv(REPORTE, dtype=str)
    reglas = df.to_dict("records")
    fallas = df[df["resultado"] == "FALLA"]
    bloqueantes = fallas[fallas["severidad"] == "bloqueante"]

    salida = {
        "meta": b.build_meta(),
        "reglas_evaluadas": len(df),
        "pasan": len(df) - len(fallas),
        "fallan": len(fallas),
        "bloqueantes_fallando": len(bloqueantes),
        "reglas": reglas,
    }
    b.write_json(salida, "validacion.json")

    print(f"  reglas evaluadas     : {len(df)}")
    print(f"  pasan                : {len(df) - len(fallas)}")
    print(f"  fallan               : {len(fallas)}")
    print(f"  bloqueantes fallando : {len(bloqueantes)}")
    print("\n  OK · data/processed/validacion.json")


if __name__ == "__main__":
    main()
