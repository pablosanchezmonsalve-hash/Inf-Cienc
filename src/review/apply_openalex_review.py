"""Aplica las decisiones de la revisión de cobertura OpenAlex (V2-26).

QUÉ HACE
    Lee `internal/openalex_cobertura_decisiones.csv` —exportado desde
    `internal/revision_cobertura_openalex.html`— y actualiza la columna
    `resolucion` de `internal/openalex_cobertura.csv`, fila por
    `openalex_id`.

QUÉ NO HACE
    **No toca `data/interim/publications_universe.csv` ni ningún artefacto
    publicable.** Marcar un caso «uft» aquí no lo agrega al corpus: ampliar
    el universo es una decisión de alcance aparte, explícita, que se declara
    en `config/institution.yml` o `config/sources.yml`, nunca la consecuencia
    automática de esta revisión (`D-206`). Esta herramienta sólo deja
    constancia de que alguien miró el caso y qué concluyó.

Uso:
    python3 src/review/apply_openalex_review.py --test       lógica, sin tocar nada
    python3 src/review/apply_openalex_review.py --dry-run    qué haría, sin escribir
    python3 src/review/apply_openalex_review.py              aplica de verdad
"""

from __future__ import annotations

import argparse
import io
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

if sys.platform == "win32":
    # La consola de Windows usa cp1252 por defecto: revienta cualquier print()
    # con caracteres como "→"/"✗"/"⚠". Mismo patrón que src/enrich/orcid_openalex.py.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[2]
COBERTURA = ROOT / "internal" / "openalex_cobertura.csv"
DECISIONES = ROOT / "internal" / "openalex_cobertura_decisiones.csv"
RESPALDOS = ROOT / "internal" / ".respaldos"

VEREDICTO_A_RESOLUCION = {
    "uft": "CONFIRMADO_PRODUCCION_UFT",
    "error": "DESCARTADO_ATRIBUCION_ERRONEA",
    "tipo": "DESCARTADO_TIPO_EXCLUIDO_A_PROPOSITO",
}


def leer_decisiones(ruta: Path) -> pd.DataFrame:
    # Se salta la cabecera de comentario por POSICIÓN, no con
    # `pd.read_csv(comment='#')`: eso trunca en la primera almohadilla ESTÉ
    # DONDE ESTÉ, y una nota como «ítem #3» perdería la mitad en silencio
    # (mismo bug que ya se corrigió en decisiones.py::leer()).
    lineas = ruta.read_text(encoding="utf-8-sig").splitlines()
    i = 0
    while i < len(lineas) and lineas[i].startswith("#"):
        i += 1
    d = pd.read_csv(io.StringIO("\n".join(lineas[i:])), dtype=str).fillna("")
    faltan = {"openalex_id", "veredicto"} - set(d.columns)
    if faltan:
        sys.exit(f"Faltan columnas en {ruta.name}: {sorted(faltan)}")
    return d


def aplicar(cobertura: pd.DataFrame, decisiones: pd.DataFrame) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Devuelve la tabla actualizada, los cambios aplicados y los avisos."""
    cambios, avisos = [], []
    cobertura = cobertura.copy()
    indice = {v: i for i, v in enumerate(cobertura["openalex_id"])}

    for _, r in decisiones.iterrows():
        oid = r["openalex_id"]
        veredicto = r["veredicto"].strip().lower()
        if veredicto not in VEREDICTO_A_RESOLUCION:
            continue  # 'pendiente' u otro valor sin resolver: no se toca la fila
        if oid not in indice:
            avisos.append(f"{oid}: no está en internal/openalex_cobertura.csv "
                           "(¿corrida distinta a la que generó la revisión?)")
            continue
        fila = indice[oid]
        nueva = VEREDICTO_A_RESOLUCION[veredicto]
        actual = cobertura.at[fila, "resolucion"]
        if actual == nueva:
            continue
        cobertura.at[fila, "resolucion"] = nueva
        cambios.append(f"{oid}: {actual} → {nueva}")

    return cobertura, cambios, avisos


PENDIENTE = "PENDIENTE_REVISION_HUMANA"


def autotest() -> int:
    casos = []

    def caso(n, ok, obs=None):
        casos.append((n, ok, obs))

    cobertura = pd.DataFrame([
        {"openalex_id": "W1", "resolucion": PENDIENTE},
        {"openalex_id": "W2", "resolucion": PENDIENTE},
        {"openalex_id": "W3", "resolucion": PENDIENTE},
    ])
    decisiones = pd.DataFrame([
        {"openalex_id": "W1", "veredicto": "uft"},
        {"openalex_id": "W2", "veredicto": "error"},
        {"openalex_id": "W3", "veredicto": "pendiente"},
        {"openalex_id": "W9", "veredicto": "uft"},
    ])
    resultado, cambios, avisos = aplicar(cobertura, decisiones)

    caso("un veredicto 'uft' actualiza la resolución",
         resultado.loc[resultado["openalex_id"] == "W1", "resolucion"].iloc[0]
         == "CONFIRMADO_PRODUCCION_UFT", None)
    caso("un veredicto 'error' actualiza la resolución",
         resultado.loc[resultado["openalex_id"] == "W2", "resolucion"].iloc[0]
         == "DESCARTADO_ATRIBUCION_ERRONEA", None)
    caso("'pendiente' no toca la fila",
         resultado.loc[resultado["openalex_id"] == "W3", "resolucion"].iloc[0]
         == PENDIENTE, None)
    caso("un id que ya no existe en la cola se avisa, no revienta",
         any("W9" in a for a in avisos), avisos)
    caso("dos cambios reales aplicados", len(cambios) == 2, cambios)

    # Reaplicar las mismas decisiones no debe generar cambios de nuevo.
    resultado2, cambios2, _ = aplicar(resultado, decisiones)
    caso("aplicar dos veces las mismas decisiones es idempotente",
         len(cambios2) == 0, cambios2)

    fallos = [n for n, ok, _ in casos if not ok]
    for n, ok, obs in casos:
        marca = "OK  " if ok else "FALLA"
        print(f"  {marca} {n}" + (f"  ({obs})" if not ok and obs is not None else ""))
    print(f"\n{len(casos) - len(fallos)}/{len(casos)} comprobaciones")
    return 1 if fallos else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--test", action="store_true", help="verifica la lógica con datos sintéticos, sin tocar nada")
    ap.add_argument("--dry-run", action="store_true", help="muestra qué haría, sin escribir nada")
    args = ap.parse_args()

    if args.test:
        return autotest()

    print("=" * 78)
    print("APLICAR LA REVISIÓN DE COBERTURA OPENALEX (V2-26)")
    print("=" * 78)

    if not COBERTURA.exists():
        sys.exit(f"Falta {COBERTURA.relative_to(ROOT)}. Ejecute: "
                  "python3 src/enrich/openalex_cobertura.py")
    if not DECISIONES.exists():
        sys.exit(f"Falta {DECISIONES.relative_to(ROOT)}.\n"
                  "Se exporta desde internal/revision_cobertura_openalex.html "
                  "(se genera con python3 src/review/build_openalex_review.py).")

    cobertura = pd.read_csv(COBERTURA, dtype=str)
    decisiones = leer_decisiones(DECISIONES)
    resultado, cambios, avisos = aplicar(cobertura, decisiones)

    respondidas = decisiones[decisiones["veredicto"].str.lower().isin(VEREDICTO_A_RESOLUCION)]
    print(f"  decisiones leídas    : {len(decisiones)}")
    print(f"  con veredicto        : {len(respondidas)}")
    print(f"  cambios a aplicar    : {len(cambios)}")

    if avisos:
        print("\n  AVISOS:")
        for a in avisos:
            print(f"    ⚠ {a}")

    if not cambios:
        print("\n  Nada que escribir.")
        return 0

    print("\n  CAMBIOS:")
    for cambio in cambios[:20]:
        print(f"    · {cambio}")
    if len(cambios) > 20:
        print(f"    … y {len(cambios) - 20} más")

    if args.dry_run:
        print("\n  --dry-run: no se escribió nada.")
        return 0

    RESPALDOS.mkdir(parents=True, exist_ok=True)
    respaldo = RESPALDOS / f"openalex_cobertura_{datetime.now().strftime('%Y%m%dT%H%M%S')}.csv"
    respaldo.write_text(COBERTURA.read_text(encoding="utf-8"), encoding="utf-8")
    resultado.to_csv(COBERTURA, index=False, encoding="utf-8")

    print(f"\n  OK · {COBERTURA.relative_to(ROOT)} actualizado")
    print(f"       Respaldo en {respaldo.relative_to(ROOT)}")
    print("\n  Recordatorio: esto NO modifica el universo publicado. Ningún build "
          "hace falta reejecutar por esto solo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
