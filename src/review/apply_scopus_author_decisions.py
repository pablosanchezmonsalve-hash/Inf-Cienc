"""Aplica decisiones humanas a `internal/scopus_author_search_multiples_id.csv`.

Mismo patrón que `apply_openalex_review.py`: lee un CSV de veredictos
pequeño y actualiza la columna `resolucion` de la cola por nombre_scopus.
No decide nada por sí mismo (D-08); sólo dice qué decidió una persona.

Uso:
    python3 src/review/apply_scopus_author_decisions.py --test       lógica, sin tocar nada
    python3 src/review/apply_scopus_author_decisions.py --dry-run    qué haría, sin escribir
    python3 src/review/apply_scopus_author_decisions.py              aplica de verdad
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

import pandas as pd

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
COLA = ROOT / "internal" / "scopus_author_search_multiples_id.csv"
DECISIONES = ROOT / "internal" / "scopus_author_search_decisiones.csv"

VEREDICTO_A_RESOLUCION = {
    "misma": "CONFIRMADO_MISMA_PERSONA",
    "distintas": "CONFIRMADO_PERSONAS_DISTINTAS",
    "pendiente": "PENDIENTE_REVISION_HUMANA",
}


def leer_decisiones(ruta: Path) -> pd.DataFrame:
    # Mismo patrón que decisiones.py::leer(): saltar la cabecera de
    # comentario por POSICIÓN, no con pd.read_csv(comment='#') — eso trunca
    # en la primera almohadilla esté donde esté.
    lineas = ruta.read_text(encoding="utf-8-sig").splitlines()
    i = 0
    while i < len(lineas) and lineas[i].startswith("#"):
        i += 1
    d = pd.read_csv(io.StringIO("\n".join(lineas[i:])), dtype=str).fillna("")
    faltan = {"nombre_scopus", "veredicto"} - set(d.columns)
    if faltan:
        sys.exit(f"Faltan columnas en {ruta.name}: {sorted(faltan)}")
    return d


def aplicar(cola: pd.DataFrame, decisiones: pd.DataFrame) -> tuple[pd.DataFrame, list[str], list[str]]:
    cambios, avisos = [], []
    cola = cola.copy()
    indice = {v: i for i, v in enumerate(cola["nombre_scopus"])}

    for _, r in decisiones.iterrows():
        nombre = r["nombre_scopus"]
        veredicto = r["veredicto"].strip().lower()
        if veredicto not in VEREDICTO_A_RESOLUCION:
            continue
        if nombre not in indice:
            avisos.append(f"{nombre}: no está en {COLA.name} "
                           "(¿corrida distinta a la que generó la cola?)")
            continue
        fila = indice[nombre]
        nueva = VEREDICTO_A_RESOLUCION[veredicto]
        actual = cola.at[fila, "resolucion"]
        nota = r.get("nota", "")
        if actual == nueva and cola.at[fila, "nota_resolucion"] == nota:
            continue
        cola.at[fila, "resolucion"] = nueva
        cola.at[fila, "nota_resolucion"] = nota
        cambios.append(f"{nombre}: {actual} -> {nueva}")

    return cola, cambios, avisos


def autotest() -> int:
    casos = []

    def caso(n, ok, obs=None):
        casos.append((n, ok, obs))

    cola = pd.DataFrame([
        {"nombre_scopus": "A, Uno", "resolucion": "PENDIENTE_REVISION_HUMANA", "nota_resolucion": ""},
        {"nombre_scopus": "B, Dos", "resolucion": "PENDIENTE_REVISION_HUMANA", "nota_resolucion": ""},
    ])
    decisiones = pd.DataFrame([
        {"nombre_scopus": "A, Uno", "veredicto": "misma", "nota": "confirmado"},
        {"nombre_scopus": "B, Dos", "veredicto": "pendiente", "nota": "sin evidencia"},
        {"nombre_scopus": "C, Tres", "veredicto": "misma", "nota": "no existe"},
    ])
    resultado, cambios, avisos = aplicar(cola, decisiones)

    caso("veredicto 'misma' actualiza resolucion",
         resultado.loc[resultado["nombre_scopus"] == "A, Uno", "resolucion"].iloc[0]
         == "CONFIRMADO_MISMA_PERSONA")
    caso("veredicto 'pendiente' deja explícita la nota aunque la resolucion no cambie",
         resultado.loc[resultado["nombre_scopus"] == "B, Dos", "nota_resolucion"].iloc[0] == "sin evidencia")
    caso("nombre que no existe en la cola se avisa, no revienta", any("C, Tres" in a for a in avisos))
    caso("dos cambios reales aplicados", len(cambios) == 2, cambios)

    resultado2, cambios2, _ = aplicar(resultado, decisiones)
    caso("aplicar dos veces las mismas decisiones es idempotente", len(cambios2) == 0, cambios2)

    fallos = [n for n, ok, _ in casos if not ok]
    for n, ok, obs in casos:
        marca = "OK  " if ok else "FALLA"
        print(f"  {marca} {n}" + (f"  ({obs})" if not ok and obs is not None else ""))
    print(f"\n{len(casos) - len(fallos)}/{len(casos)} comprobaciones")
    return 1 if fallos else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.test:
        return autotest()

    print("=" * 78)
    print("APLICAR DECISIONES — SCOPUS AUTHOR SEARCH, MÚLTIPLES SCOPUS ID")
    print("=" * 78)

    if not COLA.exists():
        sys.exit(f"Falta {COLA.relative_to(ROOT)}. Ejecute: "
                  "python3 src/enrich/scopus_author_search.py")
    if not DECISIONES.exists():
        sys.exit(f"Falta {DECISIONES.relative_to(ROOT)}.")

    cola = pd.read_csv(COLA, dtype=str)
    decisiones = leer_decisiones(DECISIONES)
    resultado, cambios, avisos = aplicar(cola, decisiones)

    print(f"  decisiones leídas : {len(decisiones)}")
    print(f"  cambios a aplicar : {len(cambios)}")
    if avisos:
        print("\n  AVISOS:")
        for a in avisos:
            print(f"    - {a}")
    if not cambios:
        print("\n  Nada que escribir.")
        return 0

    print("\n  CAMBIOS:")
    for cambio in cambios:
        print(f"    - {cambio}")

    if args.dry_run:
        print("\n  --dry-run: no se escribió nada.")
        return 0

    resultado.to_csv(COLA, index=False, encoding="utf-8")
    print(f"\n  OK - {COLA.relative_to(ROOT)} actualizado")
    return 0


if __name__ == "__main__":
    sys.exit(main())
