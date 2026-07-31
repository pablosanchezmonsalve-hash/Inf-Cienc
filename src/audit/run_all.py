"""Ejecuta la auditoría completa de Fase 1 en orden.

Uso:
    python3 src/audit/run_all.py

Los scripts tienen dependencias entre sí: 04 consume el log de 03, y 05 consume
las salidas de 02, 03 y 04. El orden no es opcional.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

STEPS = [
    "01_inventory",
    "02_reconcile_sources",
    "03_affiliation_variants",
    "04_author_population",
    "05_validation_rules",
]


def main() -> None:
    for step in STEPS:
        importlib.import_module(step).main()
    print("\n" + "=" * 78)
    print("AUDITORÍA DE FASE 1 COMPLETA")
    print("=" * 78)


if __name__ == "__main__":
    main()
