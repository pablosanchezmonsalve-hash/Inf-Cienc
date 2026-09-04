"""Build 09 — Produce el artefacto JSON de fuentes externas para el sitio.

Lee data/interim/fuentes_externas.json (generado por src/enrich/fuentes_externas.py)
y escribe data/processed/fuentes_externas.json con el formato que consume la
página web/fuentes-externas.html.

Salida:
  data/processed/fuentes_externas.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
INTERIM = ROOT / "data" / "interim" / "fuentes_externas.json"
OUT = ROOT / "data" / "processed" / "fuentes_externas.json"


def main() -> int:
    if not INTERIM.exists():
        print("  fuentes_externas  : OMITIDO — falta data/interim/fuentes_externas.json")
        print("                       Ejecute: py src/enrich/fuentes_externas.py")
        return 0

    data = json.loads(INTERIM.read_text(encoding="utf-8"))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    n = data["resumen"]["total_publicaciones"]
    a = data["resumen"]["total_autores"]
    print(f"  fuentes_externas  : {n} publicaciones, {a} autores → {OUT.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
