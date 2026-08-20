"""Ejecuta el build completo de artefactos publicables.

Uso:
    python3 src/build/build_all.py

Precondición: la auditoría debe haber corrido y no tener fallas bloqueantes
(`python3 src/audit/run_all.py`). El build aborta si no se cumple.

El paso 05 es una compuerta: si detecta capa interna en un artefacto público,
el build falla con código distinto de cero.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

STEPS = ["01_publications", "02_indicators", "03_authors", "04_glossary"]

# El grafo de coautoría (C-05) va DESPUÉS de 03_authors, que es quien deja la
# consolidación de identidades aplicada, y ANTES de la compuerta 05. Escribe en
# data/interim/, que no se copia a dist/: C-05 sigue diferido y el grafo lleva
# nombres de personas y sus vínculos. Cuando T-03 se resuelva y el indicador
# pase a publicarse, lo que cambia es el destino del artefacto, no el cálculo.
DERIVADOS = ["grafo_coautoria"]


def main() -> int:
    for step in STEPS:
        importlib.import_module(step).main()

    for derivado in DERIVADOS:
        importlib.import_module(derivado).main()

    codigo = importlib.import_module("05_verify_public_layer").main()

    print("\n" + "=" * 78)
    if codigo == 0:
        print("BUILD COMPLETO · artefactos en data/processed/")
    else:
        print("BUILD FALLIDO · la verificación de capas encontró problemas")
    print("=" * 78)
    return codigo


if __name__ == "__main__":
    sys.exit(main())
