"""Fusiona un CSV de decisiones recién exportado con el vigente, por caso_id.

QUÉ RESUELVE
    `internal/revision_identidad.html` sólo pinta la cola VIVA de
    ambigüedades: las que la auditoría sigue detectando hoy. Un caso resuelto
    en una ronda anterior, cuya consolidación hace que la ambigüedad que lo
    originó no vuelva a detectarse, **desaparece del formulario** — no porque
    se haya revocado, sino porque ya no hay nada que preguntar.

    Reemplazar `internal/identity_decisions.csv` con la exportación nueva
    (`Copy-Item -Force`, lo que hacía este script antes de esta corrección)
    pierde esas filas en silencio. Y como `apply_decisions.py` regenera
    `config/identidades_consolidadas.yml` **entero** desde ese CSV en cada
    corrida, perder filas no deja el archivo desactualizado: lo deja
    INCOMPLETO — una consolidación histórica que retrocede sin que nada lo
    anuncie. Pasó de verdad el 2026-08-26: 38 grupos comiteados quedaron en
    16 tras un reemplazo directo, detectado por `git diff` antes de comitear
    (ver `SESSION_NOTES.md`, `D-263`).

QUÉ HACE
    Une por `caso_id`. Donde el caso está en los dos archivos, gana el
    nuevo — es una re-exportación más reciente, y si alguien cambió de
    opinión eso es lo que hay que respetar (`D-08`: la decisión humana manda,
    y la más reciente es la vigente). Donde el caso sólo está en el viejo, se
    conserva tal cual: sigue siendo una decisión humana vigente; que la cola
    actual no la vuelva a preguntar no la revoca.

    Cuando un caso cambia de un veredicto YA DECIDIDO a otro distinto (no
    `pendiente → algo`, sino `misma → distintas` o similar), se avisa: puede
    ser una corrección deliberada, pero es la clase de cambio que vale la
    pena que alguien vea antes de aplicar.

USO
    python3 src/review/merge_decisions.py --test          lógica, sin archivos
    python3 src/review/merge_decisions.py <nuevo.csv>      fusiona contra
                                                            internal/identity_decisions.csv
                                                            y sobrescribe ese mismo archivo
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import decisiones as D  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DESTINO = ROOT / "internal" / "identity_decisions.csv"

COLUMNAS = ["caso_id", "cola", "firmas", "veredicto", "orcid_propuesto", "nota", "fecha"]

ENCABEZADO = """# Decisiones de identidad de autor — revisión humana
# Fusionado por src/review/merge_decisions.py: incluye la exportación más
# reciente MÁS las decisiones de rondas anteriores cuyo caso ya no aparece
# en la cola viva (ver D-263 en SESSION_NOTES.md). No editar a mano.
# pendiente: no se aplica nada; el caso sigue en la cola
# misma: une las firmas en una identidad consolidada
# distintas: no une nada; sirve para detectar contradicciones
# no_es_persona: descarta la firma del recuento de autores
# es_persona: conserva la firma y la saca de la cola E-09
# orcid_correcto: conserva la asignación y la etiqueta como confirmada por revisión humana
# orcid_incorrecto: RETIRA la asignación: la ficha vuelve a no tener ORCID
# orcid_encontrado: añade la asignación con el identificador tecleado
# orcid_no_encontrado: registra que alguien buscó y no encontró registro
"""


def _con_columnas(d: pd.DataFrame) -> pd.DataFrame:
    for c in COLUMNAS:
        if c not in d.columns:
            d[c] = ""
    return d[COLUMNAS]


def fusionar(viejo: pd.DataFrame, nuevo: pd.DataFrame
            ) -> tuple[pd.DataFrame, list[tuple[str, str, str]]]:
    """Devuelve (fusión, cambios_reales).

    `cambios_reales` son casos presentes en ambos con un veredicto YA
    DECIDIDO distinto en cada uno (ni uno de los dos es `pendiente`) — un
    cambio de opinión, no una decisión nueva sobre algo que antes no se
    sabía. Se reportan; no se bloquean, porque un cambio de opinión humano es
    exactamente lo que `D-08` autoriza a decidir a una persona.
    """
    viejo = _con_columnas(viejo.copy())
    nuevo = _con_columnas(nuevo.copy())

    solo_viejo = viejo[~viejo.caso_id.isin(set(nuevo.caso_id))]
    fusion = pd.concat([nuevo, solo_viejo], ignore_index=True)
    fusion = fusion.sort_values("caso_id", kind="stable").reset_index(drop=True)

    vv = viejo.set_index("caso_id")["veredicto"]
    nv = nuevo.set_index("caso_id")["veredicto"]
    cambios = []
    for cid in set(viejo.caso_id) & set(nuevo.caso_id):
        vo, vn = vv[cid], nv[cid]
        if vo != vn and vo != "pendiente" and vn != "pendiente":
            cambios.append((cid, vo, vn))

    return fusion, sorted(cambios)


def escribir(fusion: pd.DataFrame, destino: Path) -> None:
    cuerpo = fusion.to_csv(index=False, quoting=1)  # QUOTE_ALL, como exporta la página
    destino.write_text(ENCABEZADO + cuerpo, encoding="utf-8")


def autotest() -> int:
    casos = []

    def caso(nombre, ok, obs=None):
        casos.append((nombre, ok, obs))

    def df(filas):
        return pd.DataFrame(filas, columns=["caso_id", "cola", "firmas", "veredicto"])

    viejo = df([
        ("a", "Variantes de nombre", "X | Y", "misma"),
        ("b", "Variantes de nombre", "P | Q", "misma"),   # huérfano: no vuelve en 'nuevo'
        ("c", "Variantes de nombre", "M | N", "pendiente"),
    ])
    nuevo = df([
        ("a", "Variantes de nombre", "X | Y", "misma"),   # sin cambios
        ("c", "Variantes de nombre", "M | N", "distintas"),  # recién decidido
        ("d", "Variantes de nombre", "R | S", "misma"),   # caso nuevo
    ])

    fusion, cambios = fusionar(viejo, nuevo)
    caso("conserva el huérfano del viejo",
         "b" in set(fusion.caso_id), fusion.caso_id.tolist())
    caso("incorpora el caso nuevo",
         "d" in set(fusion.caso_id), fusion.caso_id.tolist())
    caso("no duplica el que está en los dos",
         (fusion.caso_id == "a").sum() == 1, fusion)
    caso("pendiente -> decidido no se reporta como cambio real",
         cambios == [], cambios)
    caso("todas las columnas esperadas están presentes",
         list(fusion.columns) == COLUMNAS, list(fusion.columns))
    caso("sin caso_id duplicados en la fusión",
         len(fusion) == len(set(fusion.caso_id)), None)

    # Cambio real: misma -> distintas en ambos lados, ninguno pendiente.
    viejo2 = df([("z", "Variantes de nombre", "A | B", "misma")])
    nuevo2 = df([("z", "Variantes de nombre", "A | B", "distintas")])
    _, cambios2 = fusionar(viejo2, nuevo2)
    caso("un cambio de opinión real SÍ se reporta",
         cambios2 == [("z", "misma", "distintas")], cambios2)

    # El nuevo manda cuando hay conflicto de contenido, no sólo de veredicto.
    viejo3 = df([("w", "Variantes de nombre", "A | B", "misma")])
    nuevo3 = df([("w", "Variantes de nombre", "A | B | C", "misma")])
    fusion3, _ = fusionar(viejo3, nuevo3)
    caso("el nuevo gana el contenido de la fila cuando el caso_id coincide",
         fusion3[fusion3.caso_id == "w"].firmas.iloc[0] == "A | B | C", fusion3)

    # Reescritura y relectura con decisiones.leer(): el formato debe sobrevivir.
    tmp = ROOT / "internal" / ".autotest_merge.csv"
    fusion, _ = fusionar(viejo, nuevo)
    escribir(fusion, tmp)
    releido = D.leer(tmp)
    tmp.unlink()
    caso("el archivo escrito se relee con decisiones.leer() sin perder filas",
         len(releido) == len(fusion), (len(releido), len(fusion)))

    ok = True
    for nombre, paso, obs in casos:
        print(f"  {'OK  ' if paso else 'FALLA'} {nombre}" + (f"   {obs}" if not paso else ""))
        ok &= paso
    print("\n" + ("TODOS LOS CASOS OK" if ok else "HAY CASOS FALLANDO"))
    return 0 if ok else 1


def main() -> int:
    print("=" * 78)
    print("FUSIÓN DE DECISIONES DE IDENTIDAD")
    print("=" * 78)

    if len(sys.argv) == 2 and sys.argv[1] == "--test":
        return autotest()

    if len(sys.argv) != 2:
        sys.exit("Uso: python3 src/review/merge_decisions.py <nuevo.csv>\n"
                 "     python3 src/review/merge_decisions.py --test")

    nuevo_path = Path(sys.argv[1])
    if not nuevo_path.exists():
        sys.exit(f"No existe: {nuevo_path}")

    nuevo = D.leer(nuevo_path)
    if not DESTINO.exists():
        print(f"  {DESTINO.relative_to(ROOT)} no existe todavía: se crea desde el nuevo, sin fusión.")
        escribir(_con_columnas(nuevo), DESTINO)
        print(f"\n  OK · {len(nuevo)} decisiones escritas")
        return 0

    viejo = D.leer(DESTINO)
    fusion, cambios = fusionar(viejo, nuevo)

    huerfanos = len(viejo) - len(set(viejo.caso_id) & set(nuevo.caso_id))
    print(f"  vigente antes de fusionar : {len(viejo)} filas")
    print(f"  exportación nueva         : {len(nuevo)} filas")
    print(f"  huérfanas preservadas     : {huerfanos} "
          "(casos que ya no están en la cola viva, pero siguen decididos)")
    print(f"  fusión                    : {len(fusion)} filas")

    if cambios:
        print(f"\n  {len(cambios)} caso(s) cambiaron de un veredicto decidido a otro distinto:")
        for cid, vo, vn in cambios:
            print(f"    {cid}: «{vo}» → «{vn}»")
        print("  Si fue intencional (cambió de opinión), no hace falta hacer nada más.")

    escribir(fusion, DESTINO)
    print(f"\n  OK · {DESTINO.relative_to(ROOT)} actualizado ({len(fusion)} filas)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
