"""Orquesta un conector de enriquecimiento redirigiendo TODA salida a informes/.

Evita escribir en internal/ (colas de revisión) y data/enriched (datos
versionados). Usa un directorio de trabajo aislado informes/run/<conector>
como base y re-enruta los puntos de escritura conocidos, incluidos los
`ENRICHED`/`CACHE` locales que cada conector define al importar.

Uso:
    python informes/_fork_runner.py <script_del_conector> [args del conector...]
"""
from __future__ import annotations

import argparse
import glob
import importlib
import shutil
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "audit"))
sys.path.insert(0, str(ROOT / "src" / "enrich"))

import common as c  # noqa: E402

OUT = ROOT / "informes" / "run"


def _importar_script(script: Path):
    """Importa el script como módulo con nombre distinto de __main__.

    Así el bloque `if __name__ == "__main__"` NO se ejecuta: podemos parchear
    las constantes (ENRICHED, CACHE) ANTES de llamar a main() a mano.
    """
    name = script.stem
    if name in sys.modules:
        del sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, script)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("script", help="ruta al script del conector (relativa a ROOT)")
    args, extras = ap.parse_known_args()

    script = (ROOT / args.script).resolve()
    if not script.exists():
        print(f"No existe el script: {script}")
        return 2

    base = OUT / script.stem
    if base.exists():
        shutil.rmtree(base)
    for sub in ("internal", "enriched", "interim", "cache"):
        (base / sub).mkdir(parents=True, exist_ok=True)

    # Siembra los datos versionados vigentes como COPIA del fork: el conector
    # lee y escribe en las mismas rutas; sin copia, leería cero y la fusión
    # perdería las asignaciones ya consolidadas. La escritura sólo va al fork.
    for origen, sub in ((ROOT / "data" / "enriched", "enriched"),
                        (ROOT / "data" / "interim", "interim"),
                        (ROOT / "data" / "cache", "cache")):
        if origen.exists():
            for p in origen.rglob("*"):
                if p.is_file() and p.suffix in {".csv", ".json"}:
                    rel = p.relative_to(origen)
                    destino = base / sub / rel
                    destino.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(p, destino)
            if any(origen.rglob("*")):
                print(f"  [fork] sembrado {sub}: copia de {origen.relative_to(ROOT)}")

    original_internal = c.INTERNAL

    def write_internal(df, name, **kw):
        path = base / "internal" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False, encoding="utf-8")
        print(f"  [fork] write_internal -> {path.relative_to(ROOT)}")
        return path

    def write_csv_vig(salida, path, **kw):
        """Intercepta to_csv directos hacia data/enriched (authors_orcid)."""
        objetivo = base / "enriched" / path.name
        print(f"  [fork] to_csv directo {path} -> {objetivo.relative_to(ROOT)}")
        salida.to_csv(objetivo, index=False, encoding="utf-8")
        return objetivo

    c.write_internal = write_internal
    c.ENRICHED = base / "enriched"
    # NÓTESE: c.INTERNAL se deja apuntando al REAL: las lecturas (matching_log,
    # universe) deben venir del árbol versionado. El aislamiento de escrituras
    # se consigue redirigiendo c.write_internal (colas) y ENRICHED/CACHE y las
    # escrituras directas .to_csv hacia data/enriched (fork), no el acceso de
    # lectura. Si el módulo escribiera DIRECTAMENTE a c.INTERNAL (p.ej.
    # ror_institucion), ese archivo iría al real: para esos casos se avisa.

    print("=" * 70)
    print(f"FORK a {base.relative_to(ROOT)}")
    print(f"script : {script.relative_to(ROOT)}")
    print(f"argv   : {extras}")
    print("=" * 70)

    exit_code = 1
    try:
        mod = _importar_script(script)

        # Parchea constantes locales de ruta SI el módulo las define.
        for attr, sub in (("ENRICHED", "enriched"), ("CACHE", "cache")):
            if hasattr(mod, attr):
                setattr(mod, attr, base / sub)

        # argv para el conector.
        sys.argv = [str(script)] + extras

        # Monitorea escrituras directas hacia data/enriched.
        import pandas as pd  # noqa: F401
        real_enriched = ROOT / "data" / "enriched"
        if hasattr(mod, "main"):
            exit_code = mod.main() or 0
        else:
            print("[runner] el script no define main(); nada que orquestar")
            exit_code = 0

        # Verificación post: nada real tocado.
        tocado = [str(p) for p in real_enriched.rglob("*") if p.is_file()]
        nuevos = [p for p in tocado if not (p in glob.glob(str(real_enriched / "*")))]
        escritos = [p for p in real_enriched.rglob("*.csv")
                    if p.suffix and p.name in {"authors_orcid.csv"}]
        # Si el módulo escribió al enriched real, el archivo tendría mtime reciente.
        for p in escritos:
            if p.stat().st_mtime > (base.stat().st_mtime or 0):
                print(f"  [AVISO] ¡el módulo escribió al enriched REAL: {p}")
    except SystemExit as e:
        exit_code = e.code if isinstance(e.code, int) else 1
        print(f"\n[runner] el conector salió con código {exit_code}")
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        exit_code = 1
    finally:
        c.INTERNAL = original_internal

    print(f"\nfork listo. Revisar informe en {base.relative_to(ROOT)}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())