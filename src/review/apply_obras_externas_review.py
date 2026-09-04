"""Aplica las decisiones de la revisión de obras en repositorios externos (PD-04).

QUÉ HACE
    Lee `internal/obras_externas_decisiones.csv` —exportado desde
    `internal/revision_obras_externas.html`— y actualiza la columna
    `resolucion` de `internal/obras_externas_cobertura.csv`, fila por
    `(fuente, id_fuente)`.

    El DOI solo NO sirve como clave: la misma obra puede estar en las tres
    fuentes con el mismo DOI, y cada una se decide por separado porque la
    evidencia que aporta cada fuente es distinta. Hay además obras sin DOI,
    que con esa clave se pisarían todas entre sí.

QUÉ NO HACE
    **No toca `data/interim/publications_universe.csv` ni ningún artefacto
    Scopus/SciVal.** Marcar «uft» aquí no agrega la obra al corpus: la vuelve
    contable como `PD-04`, en su propia sección, con su propio denominador y
    sin ningún indicador de impacto (`D-206`, `D-313`, Regla 5 de
    `docs/METODOLOGIA_FUERA_DE_SCOPUS.md`).

    Sólo `CONFIRMADO_PRODUCCION_UFT` se cuenta. Los tres descartes se guardan
    en vez de borrarse: distinguir «no es de esta institución» de «es una
    versión de algo ya contado» es lo que permite saber, más adelante, si la
    cola está llena de homónimos o de duplicación de versiones — dos problemas
    con soluciones distintas.

Uso:
    python3 src/review/apply_obras_externas_review.py --test     lógica, sin tocar nada
    python3 src/review/apply_obras_externas_review.py --dry-run  qué haría
    python3 src/review/apply_obras_externas_review.py            aplica de verdad
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
COBERTURA = ROOT / "internal" / "obras_externas_cobertura.csv"
DECISIONES = ROOT / "internal" / "obras_externas_decisiones.csv"
RESPALDOS = ROOT / "internal" / ".respaldos"

PENDIENTE = "PENDIENTE_REVISION_HUMANA"

VEREDICTO_A_RESOLUCION = {
    "uft": "CONFIRMADO_PRODUCCION_UFT",
    "error": "DESCARTADO_ATRIBUCION_ERRONEA",
    "tipo": "DESCARTADO_TIPO_EXCLUIDO_A_PROPOSITO",
    # Propio de estas tres fuentes: Zenodo acuña un DOI por versión y un DOI
    # de concepto; DataCite indexa preprints cuya versión publicada ya está
    # en Scopus. La obra SÍ es de esta institución — por eso no es
    # 'atribución errónea' — pero contarla duplicaría una obra ya contada.
    "version": "DESCARTADO_VERSION_DE_OBRA_YA_CONTADA",
}


def clave(fuente: str, id_fuente: str) -> tuple[str, str]:
    return (str(fuente).strip(), str(id_fuente).strip())


def leer_decisiones(ruta: Path) -> pd.DataFrame:
    # Se salta la cabecera de comentario por POSICIÓN, no con
    # `pd.read_csv(comment='#')`: eso trunca en la primera almohadilla esté
    # donde esté, y una nota como «ítem #3» perdería la mitad en silencio
    # (mismo bug ya corregido en decisiones.py::leer()).
    lineas = ruta.read_text(encoding="utf-8-sig").splitlines()
    i = 0
    while i < len(lineas) and lineas[i].startswith("#"):
        i += 1
    d = pd.read_csv(io.StringIO("\n".join(lineas[i:])), dtype=str).fillna("")
    faltan = {"fuente", "id_fuente", "veredicto"} - set(d.columns)
    if faltan:
        sys.exit(f"Faltan columnas en {ruta.name}: {sorted(faltan)}")
    return d


def aplicar(cobertura: pd.DataFrame,
            decisiones: pd.DataFrame) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Devuelve la tabla actualizada, los cambios aplicados y los avisos."""
    cambios, avisos = [], []
    cobertura = cobertura.copy()
    indice = {clave(r["fuente"], r["id_fuente"]): i
              for i, r in cobertura.reset_index(drop=True).iterrows()}
    cobertura = cobertura.reset_index(drop=True)

    for _, r in decisiones.iterrows():
        veredicto = str(r["veredicto"]).strip().lower()
        if veredicto not in VEREDICTO_A_RESOLUCION:
            continue  # 'pendiente' u otro valor sin resolver: no se toca la fila
        k = clave(r["fuente"], r["id_fuente"])
        if k not in indice:
            avisos.append(f"{k[0]} · {k[1]}: no está en "
                          "internal/obras_externas_cobertura.csv "
                          "(¿corrida distinta a la que generó la revisión?)")
            continue
        fila = indice[k]
        nueva = VEREDICTO_A_RESOLUCION[veredicto]
        actual = cobertura.at[fila, "resolucion"]
        if actual == nueva:
            continue
        cobertura.at[fila, "resolucion"] = nueva
        cambios.append(f"{k[0]} · {k[1]}: {actual} → {nueva}")

    return cobertura, cambios, avisos


def autotest() -> int:
    casos = []

    def caso(n, ok, obs=None):
        casos.append((n, ok, obs))

    cobertura = pd.DataFrame([
        {"fuente": "zenodo", "id_fuente": "z1", "doi": "10.1/x", "resolucion": PENDIENTE},
        {"fuente": "datacite", "id_fuente": "d1", "doi": "10.1/x", "resolucion": PENDIENTE},
        {"fuente": "europepmc", "id_fuente": "e1", "doi": "", "resolucion": PENDIENTE},
        {"fuente": "europepmc", "id_fuente": "e2", "doi": "", "resolucion": PENDIENTE},
        {"fuente": "zenodo", "id_fuente": "z2", "doi": "10.1/y", "resolucion": PENDIENTE},
    ])
    decisiones = pd.DataFrame([
        {"fuente": "zenodo", "id_fuente": "z1", "veredicto": "uft"},
        {"fuente": "datacite", "id_fuente": "d1", "veredicto": "version"},
        {"fuente": "europepmc", "id_fuente": "e1", "veredicto": "error"},
        {"fuente": "europepmc", "id_fuente": "e2", "veredicto": "pendiente"},
        {"fuente": "zenodo", "id_fuente": "z9", "veredicto": "uft"},
    ])
    res, cambios, avisos = aplicar(cobertura, decisiones)

    def resol(fuente, idf):
        m = (res["fuente"] == fuente) & (res["id_fuente"] == idf)
        return res.loc[m, "resolucion"].iloc[0]

    caso("un veredicto 'uft' actualiza la resolución",
         resol("zenodo", "z1") == "CONFIRMADO_PRODUCCION_UFT", resol("zenodo", "z1"))
    caso("'version' tiene su propia resolución, distinta de un descarte por error",
         resol("datacite", "d1") == "DESCARTADO_VERSION_DE_OBRA_YA_CONTADA",
         resol("datacite", "d1"))
    caso("el mismo DOI en dos fuentes se decide por separado",
         resol("zenodo", "z1") != resol("datacite", "d1"))
    caso("un veredicto 'error' actualiza la resolución",
         resol("europepmc", "e1") == "DESCARTADO_ATRIBUCION_ERRONEA")
    caso("'pendiente' no toca la fila", resol("europepmc", "e2") == PENDIENTE)
    caso("dos filas sin DOI no se pisan entre sí",
         resol("europepmc", "e1") != resol("europepmc", "e2"))
    caso("una fila que ya no existe en la cola se avisa, no revienta",
         any("z9" in a for a in avisos), avisos)
    caso("una fila sin decisión queda intacta", resol("zenodo", "z2") == PENDIENTE)
    caso("tres cambios reales aplicados", len(cambios) == 3, cambios)

    res2, cambios2, _ = aplicar(res, decisiones)
    caso("aplicar dos veces las mismas decisiones es idempotente",
         len(cambios2) == 0, cambios2)

    caso("sólo 'uft' produce una resolución contable",
         sum(1 for v in VEREDICTO_A_RESOLUCION.values()
             if not v.startswith("DESCARTADO")) == 1)

    fallos = [n for n, ok, _ in casos if not ok]
    for n, ok, obs in casos:
        marca = "OK  " if ok else "FALLA"
        print(f"  {marca} {n}" + (f"  ({obs})" if not ok and obs is not None else ""))
    print(f"\n{len(casos) - len(fallos)}/{len(casos)} comprobaciones")
    return 1 if fallos else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--test", action="store_true",
                    help="verifica la lógica con datos sintéticos, sin tocar nada")
    ap.add_argument("--dry-run", action="store_true", help="muestra qué haría, sin escribir")
    args = ap.parse_args()

    print("=" * 78)
    print("APLICAR LA REVISIÓN DE OBRAS EN REPOSITORIOS EXTERNOS (PD-04)")
    print("=" * 78)

    if args.test:
        return autotest()

    if not COBERTURA.exists():
        sys.exit(f"Falta {COBERTURA.relative_to(ROOT)}. Ejecute: "
                  "python3 src/enrich/obras_externas.py")
    if not DECISIONES.exists():
        sys.exit(f"Falta {DECISIONES.relative_to(ROOT)}.\n"
                  "Se exporta desde internal/revision_obras_externas.html "
                  "(se genera con python3 src/review/build_obras_externas_review.py).")

    cobertura = pd.read_csv(COBERTURA, dtype=str).fillna("")
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
    respaldo = RESPALDOS / f"obras_externas_cobertura_{datetime.now().strftime('%Y%m%dT%H%M%S')}.csv"
    respaldo.write_text(COBERTURA.read_text(encoding="utf-8"), encoding="utf-8")
    resultado.to_csv(COBERTURA, index=False, encoding="utf-8")

    confirmadas = int((resultado["resolucion"] == "CONFIRMADO_PRODUCCION_UFT").sum())
    print(f"\n  OK · {COBERTURA.relative_to(ROOT)} actualizado")
    print(f"       Respaldo en {respaldo.relative_to(ROOT)}")
    print(f"       Confirmadas en total: {confirmadas} (las que contará PD-04)")
    print("\n  Esto NO modifica el universo publicado. Para que la cifra nueva llegue")
    print("  al sitio: python3 src/build/build_all.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
