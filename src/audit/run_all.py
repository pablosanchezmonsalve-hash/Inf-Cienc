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

import pandas as pd

if sys.platform == "win32":
    # La consola de Windows usa cp1252 por defecto: revienta cualquier print()
    # con caracteres como "→"/"✗"/"⚠". Mismo patrón que src/enrich/orcid_openalex.py.
    # Es el único __main__ de la auditoría que dependía, por accidente de
    # orden de import, del guard de 01_inventory.py para no reventar aquí.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))

STEPS = [
    "01_inventory",
    "02_reconcile_sources",
    "03_affiliation_variants",
    "04_author_population",
    "05_validation_rules",
]


def main() -> int:
    for step in STEPS:
        importlib.import_module(step).main()

    # Código de salida distinto de cero si hay reglas bloqueantes fallando. El
    # build tiene su propia compuerta (`require_validation()`), pero este script
    # también se ejecuta suelto y en un paso de CI llamado «validación»: que
    # terminara en verde con una regla bloqueante rota haría que el fallo
    # apareciera un paso más tarde y en otro sitio.
    import common as c  # noqa: E402  (los pasos ajustan sys.path)

    report = pd.read_csv(c.INTERIM / "validation_report.csv")
    bloqueantes = report[(report["resultado"] == "FALLA")
                         & (report["severidad"] == "bloqueante")]

    print("\n" + "=" * 78)
    if len(bloqueantes):
        print(f"AUDITORÍA DETENIDA · {len(bloqueantes)} regla(s) bloqueante(s) fallando")
        print("=" * 78)
        print(bloqueantes.to_string(index=False))
        return 1
    print("AUDITORÍA DE FASE 1 COMPLETA")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
