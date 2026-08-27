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

if sys.platform == "win32":
    # La consola de Windows usa cp1252 por defecto: revienta cualquier print()
    # con caracteres como "→"/"—"/"·". Mismo patrón que src/enrich/orcid_openalex.py.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))

STEPS = ["01_publications", "02_indicators", "03_authors", "04_glossary"]

# El grafo de coautoría (C-05) va DESPUÉS de 03_authors, que es quien deja la
# consolidación de identidades aplicada, y ANTES de la compuerta 05.
#
# C-05 se publicó el 2026-08-26 (T-10), pero este artefacto —el JSON completo
# con nombres y vínculos, en data/interim/, que NO se copia a dist/— sigue
# siendo capa interna: es la herramienta de revisión (`make red`), no lo que
# ve el sitio. Lo que SÍ llega al público es distinto y vive en 02_indicators
# (resumen agregado en series.json) y en el recorte que recalcula
# `web/assets/js/grafo.js` en vivo, en el navegador, con las mismas funciones
# —mismo criterio, dos superficies—.
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
