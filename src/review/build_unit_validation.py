"""Genera la hoja de validación institucional de unidades académicas (T-02).

QUÉ RESUELVE
    El vocabulario de unidades académicas está INFERIDO de cómo aparecen
    escritas en las afiliaciones, no tomado de un catálogo oficial: no existe
    uno disponible para el proyecto. Mientras siga inferido, el indicador `P-07`
    lleva confiabilidad baja y su advertencia lo declara.

    Resolverlo no es trabajo de código: hay que preguntarle a la universidad. Lo
    que sí es trabajo de código es dejar la pregunta hecha, con la evidencia
    delante, para que responderla cueste una lectura y no una investigación.

QUÉ PRODUCE
    Un documento con cada unidad detectada, cuántos pares la respaldan y una
    afiliación real de ejemplo, más las jerarquías escuela→facultad separadas
    entre confirmadas e inferidas. Va con instrucciones de qué se pide.

QUÉ NO HACE
    No propone nombres oficiales ni corrige los detectados. Lo que aparece es lo
    que dicen los datos.

CAPA
    Interna: incluye afiliaciones crudas como evidencia. No entra en `dist/`.

Uso:
    python3 src/review/build_unit_validation.py

Salida:
    internal/validacion_unidades.md
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "audit"))

import common as c  # noqa: E402


def es(n: int) -> str:
    """Miles con punto, como se escribe en español."""
    return f"{n:,}".replace(",", ".")


def pct(x: float) -> str:
    """Decimal con coma. El documento lo lee una persona, no una máquina."""
    return f"{x:.1f}".replace(".", ",")


def main() -> int:
    log_path = ROOT / "internal" / "matching_log.csv"
    if not log_path.exists():
        sys.exit("Falta internal/matching_log.csv. Ejecute: python3 src/audit/run_all.py")

    log = pd.read_csv(log_path, dtype=str)
    etiqueta_sin_dato = c.MATCHING["unidad_academica"]["etiqueta_sin_dato"]
    u = log["unidad_academica"].fillna(etiqueta_sin_dato)
    detectadas = u.value_counts()
    total = len(log)
    sin_dato = int(detectadas.get(etiqueta_sin_dato, 0))

    vocab = c.MATCHING["unidad_academica"]["vocabulario"]
    jer = c.MATCHING["unidad_academica"].get("jerarquia", {})

    L = [
        "# Validación institucional de unidades académicas",
        "",
        f"**Generado** el {date.today().isoformat()} por "
        "`src/review/build_unit_validation.py`. Regenerable.",
        "",
        "## Qué se pide",
        "",
        "El informe cienciométrico agrupa la producción por unidad académica. "
        "Esos nombres **no vienen de un catálogo oficial**: están deducidos de "
        "cómo aparecen escritos en las afiliaciones de Scopus, porque no había "
        "un catálogo disponible al construir la plataforma.",
        "",
        "Mientras sigan sin validar, el indicador de producción por unidad se "
        "publica con confiabilidad baja y una advertencia que lo declara. "
        "Para retirar esa advertencia hacen falta tres cosas:",
        "",
        "1. **Confirmar o corregir** el nombre oficial de cada unidad listada.",
        "2. **Señalar las que no existen** o cambiaron de nombre en el período.",
        "3. **Confirmar a qué facultad pertenece cada escuela** (segunda tabla).",
        "",
        "No hace falta responder en ningún formato especial: basta con marcar "
        "sobre este documento.",
        "",
        "---",
        "",
        "## 1. Unidades detectadas",
        "",
        # «Apariciones» y no «pares»: `total` son filas del log, y una firma
        # puede ocupar varias posiciones de un mismo trabajo. Los pares
        # distintos son menos, y llamar igual a las dos cifras es el error
        # silencioso que este proyecto persigue.
        f"Sobre **{es(total)}** apariciones firma × publicación de la ventana "
        f"{c.INSTITUTION['ventana_temporal']['anio_inicio']}–"
        f"{c.INSTITUTION['ventana_temporal']['anio_fin']}. "
        f"**{es(sin_dato)}** ({pct(100 * sin_dato / total)} %) no permiten deducir "
        "unidad y se declaran como «"
        f"{etiqueta_sin_dato}»: no se imputan.",
        "",
        "| Unidad como aparece en el informe | Pares | ¿Nombre oficial correcto? | Corrección |",
        "|---|---:|---|---|",
    ]

    for nombre, n in detectadas.items():
        if nombre == etiqueta_sin_dato:
            continue
        L.append(f"| {nombre} | {es(n)} | ☐ sí  ☐ no | |")

    L += [
        "",
        "### Variantes de escritura que se agrupan bajo cada nombre",
        "",
        "El sistema reconoce estas formas y las lleva al nombre canónico. Si "
        "falta alguna variante que use la universidad, indíquela.",
        "",
        "| Nombre canónico | Variantes reconocidas |",
        "|---|---|",
    ]
    for canonico, variantes in vocab.items():
        vs = ", ".join(f"`{v}`" for v in variantes)
        L.append(f"| {canonico} | {vs} |")

    L += [
        "",
        "---",
        "",
        "## 2. Jerarquía escuela → facultad",
        "",
        "El informe suma la producción de cada escuela a su facultad. Una "
        "jerarquía equivocada mueve publicaciones de una facultad a otra, así "
        "que es la parte más sensible de esta validación.",
        "",
        "| Escuela | Se suma a | Estado actual | ¿Correcto? | Corrección |",
        "|---|---|---|---|---|",
    ]
    for escuela, e in jer.items():
        estado = ("**confirmada**" if e.get("estado") == "confirmada"
                  else "*inferida de los datos*")
        L.append(f"| {escuela} | {e['facultad']} | {estado} | ☐ sí  ☐ no | |")

    inferidas = [k for k, v in jer.items() if v.get("estado") != "confirmada"]
    L += [
        "",
        f"**{len(inferidas)} de {len(jer)} jerarquías están inferidas**, no "
        "confirmadas. Son las que más importa revisar.",
        "",
        "¿Falta alguna escuela o instituto que deba sumar a una facultad y no "
        "aparezca en esta tabla?",
        "",
        "---",
        "",
        "## 3. Evidencia: cómo aparece cada unidad en el origen",
        "",
        "Una afiliación real por unidad, tal como la entrega Scopus. Sirve para "
        "juzgar si el nombre deducido es razonable.",
        "",
    ]
    for nombre, n in detectadas.items():
        if nombre == etiqueta_sin_dato:
            continue
        fila = log[log["unidad_academica"] == nombre].iloc[0]
        cruda = str(fila.get("afiliacion_declarada_raw", ""))[:200]
        L += [f"**{nombre}** ({es(n)} pares)", "", f"> {cruda}", ""]

    L += [
        "---",
        "",
        "## Qué pasa cuando esto vuelva respondido",
        "",
        "Las correcciones entran en `config/matching_rules.yml` —vocabulario y "
        "jerarquía— y el estado de cada jerarquía pasa de `inferida` a "
        "`confirmada`. Con eso, el indicador de producción por unidad puede "
        "subir su confiabilidad y perder la advertencia sobre vocabulario no "
        "validado. **No requiere reescribir nada del sistema.**",
        "",
        "Lo que **no** cambia: la cobertura. "
        f"{es(sin_dato)} pares seguirán sin unidad deducible porque su afiliación "
        "no la menciona, y seguirán declarándose como «"
        f"{etiqueta_sin_dato}» en vez de imputarse.",
    ]

    salida = ROOT / "internal" / "validacion_unidades.md"
    salida.write_text("\n".join(L) + "\n", encoding="utf-8")

    print("=" * 78)
    print("HOJA DE VALIDACIÓN DE UNIDADES ACADÉMICAS")
    print("=" * 78)
    print(f"  unidades detectadas   : {len(detectadas) - 1}")
    print(f"  jerarquías declaradas : {len(jer)} ({len(inferidas)} inferidas)")
    print(f"  cobertura             : {pct(100 * (total - sin_dato) / total)} % "
          f"({es(sin_dato)} pares sin unidad deducible)")
    print(f"\n  OK · {salida.relative_to(ROOT)}")
    print("       Enviar a quien administre el catálogo de unidades académicas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
