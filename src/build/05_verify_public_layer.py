"""Build 05 — Verificación automática de la barrera pública/interna (T-12).

La separación de capas no puede depender de que nadie se equivoque al escribir
un build (decisión D-23). Este script recorre todo `data/processed/` y falla si
encuentra rastro de la capa interna.

Falla el build con código distinto de cero: es una compuerta, no un aviso.

Salida:
  docs/BUILD_VERIFICATION.md
"""

from __future__ import annotations

import json
import re
import sys

import common_build as b

if sys.platform == "win32":
    # La consola de Windows usa cp1252 por defecto: revienta cualquier print()
    # con caracteres como "→"/"✗"/"⚠". Mismo patrón que src/enrich/orcid_openalex.py.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


FALLAS: list[dict] = []

# Rastro del intérprete en un texto destinado a leerse.
#
# Apareció publicado: la cobertura de `P-02` decía «{2023: np.int64(228)}»
# porque `dict()` sobre una Series de pandas conserva los tipos de numpy y su
# repr acaba impreso tal cual. Mientras esa cadena vivió en una nota interna fue
# fea; el día que el catálogo la publicó, pasó a ser una página enseñando el
# tipo de dato de su propio intérprete.
#
# Se vigila aquí y no con un barrido a mano porque un barrido encuentra lo que
# ya está, no lo que alguien añada mañana.
# Rastro del intérprete, en dos mitades que se cazan distinto.
#
# La primera —`np.int64(…)`, `dtype`, `<class '…'>`— lleva puntuación o mayúscula
# que no aparece en prosa y basta con buscarla.
#
# La segunda —`nan`, `None`, `NaT`— son palabras, y ahí el patrón importa. La
# primera versión usó `nan\b` y marcó «Poz**nan** Studies» y «se asig**nan** al
# documento». La segunda comparaba la cadena entera, y eso sólo caza
# `str(elemento)`: dejaba pasar la interpolación, que es exactamente cómo se
# rompió `P-02` —«308/823 (nan %)» pasaba—. Con frontera de LETRA unicode se
# cierran las dos: «Poznan» lleva `z` delante, «asignan` lleva `g`,
# «Nanotecnología» lleva `o` detrás, y los tres quedan fuera por la frontera y
# no por la puntuación.
#
# MEDIDO, no supuesto: 16 casos sintéticos sin discrepancias y **0 marcas sobre
# las 34.736 cadenas de los 564 artefactos publicados**. Ese segundo número es el
# que hace adoptable el patrón; si alguien lo endurece, querrá saber contra qué
# se midió.
#
# COSTE RESIDUAL DECLARADO, y no está donde parecía. La frontera es de LETRA, así
# que el guión no la cruza: cualquier cadena donde `nan` quede entre guiones pasa
# por marcada. Eso apunta a los IDENTIFICADORES DE AUTOR antes que a los títulos.
#
#   · `id` de autor: son slugs con guión —`abara-j-f`—, y `Nan` es un nombre de
#     pila corriente en la fuente china. Una firma «Nan Y.» daría el id `nan-y`,
#     que esta guarda marcaría, y abortaría el build por una persona real.
#   · Título en inglés: «None of the above: …» también, pero es el caso menos
#     probable de los dos y no el que hay que tener presente.
#
# Hoy no ocurre ninguno: 0 apariciones de `nan`, `None` o `NaT` como token suelto
# en los 556 id de autor y en las 34.736 cadenas publicadas. Cuando ocurra, lo
# que hay que afinar es la frontera —incluir el guión— y no quitar la guarda.
#
# ALCANCE: esto recorre `data/processed/**/*.json`, no `dist/*.html`. El catálogo
# queda cubierto porque su JSON está aguas arriba de la página, pero un
# constructor que formatee un valor directo al HTML se saltaría la compuerta. Si
# algún día lo hay, este es el sitio que hay que ampliar.
_LETRA = r"[^\W\d_]"
REPR_DE_INTERPRETE = re.compile(
    r"np\.(int|float|str_|bool_)\d*\(|numpy\.|dtype[:(=]|<class '|"
    rf"Name: \w+, dtype|Timestamp\(|"
    rf"(?<!{_LETRA})nan(?!{_LETRA})|(?<!{_LETRA})None(?!{_LETRA})|"
    rf"(?<!{_LETRA})NaT(?!{_LETRA})")


def revisar(obj, ruta: str, archivo: str) -> None:
    """Recorre el JSON buscando claves prohibidas en cualquier profundidad."""
    if isinstance(obj, str) and REPR_DE_INTERPRETE.search(obj):
        FALLAS.append({
            "archivo": archivo, "ruta": ruta,
            "problema": f"repr del intérprete en un texto publicable: {obj[:80]!r}",
        })
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in b.CAMPOS_PROHIBIDOS:
                FALLAS.append({
                    "archivo": archivo, "ruta": f"{ruta}.{k}",
                    "problema": "campo de capa interna presente en artefacto público",
                })
            revisar(v, f"{ruta}.{k}", archivo)
    elif isinstance(obj, list):
        # Sin muestreo: una compuerta que sólo mira una parte no es una
        # compuerta. La lista más larga de los artefactos tiene 823 elementos y
        # el recorrido completo de los 596 archivos cuesta menos de un segundo.
        for i, v in enumerate(obj):
            revisar(v, f"{ruta}[{i}]", archivo)


def main() -> int:
    b.banner("BUILD 05 — VERIFICACIÓN DE BARRERA PÚBLICA/INTERNA")

    archivos = sorted(b.PROCESSED.rglob("*.json"))
    if not archivos:
        sys.exit("BUILD ABORTADO: no hay artefactos en data/processed/.")

    for path in archivos:
        rel = path.relative_to(b.PROCESSED).as_posix()
        with open(path, encoding="utf-8") as fh:
            revisar(json.load(fh), "$", rel)

    # Procedencia obligatoria: un artefacto sin fecha de corte no es
    # interpretable fuera de contexto (regla V-07 de Fase 1).
    sin_meta = []
    for path in archivos:
        if path.parent.name == "author":
            continue
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict) and "meta" not in data and path.name != "meta.json":
            sin_meta.append(path.name)
    for nombre in sin_meta:
        FALLAS.append({"archivo": nombre, "ruta": "$.meta",
                       "problema": "artefacto sin bloque de procedencia"})

    total_kb = sum(p.stat().st_size for p in archivos) / 1024
    fichas = len(list((b.PROCESSED / "author").glob("*.json")))

    print(f"  artefactos revisados : {len(archivos)} ({total_kb:.0f} KB)")
    print(f"  fichas de autor      : {fichas}")
    print(f"  campos prohibidos    : {len(b.CAMPOS_PROHIBIDOS)} vigilados")
    print(f"  fallas               : {len(FALLAS)}")

    lineas = [
        "# Verificación del build", "",
        "Generado por `src/build/05_verify_public_layer.py`. Reejecutable.", "",
        f"- Artefactos revisados: **{len(archivos)}** ({total_kb:.0f} KB)",
        f"- Fichas de autor: **{fichas}**",
        f"- Campos de capa interna vigilados: {', '.join(f'`{c}`' for c in b.CAMPOS_PROHIBIDOS)}",
        "",
    ]
    if FALLAS:
        lineas += ["## Fallas", "", "| Archivo | Ruta | Problema |", "|---|---|---|"]
        lineas += [f"| `{f['archivo']}` | `{f['ruta']}` | {f['problema']} |" for f in FALLAS]
        for f in FALLAS:
            print(f"    FALLA · {f['archivo']} :: {f['ruta']} — {f['problema']}")
    else:
        lineas.append("**Sin fallas.** Ningún artefacto público contiene campos de la "
                      "capa interna y todos declaran su procedencia.")
    (b.DOCS / "BUILD_VERIFICATION.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")

    return 1 if FALLAS else 0


if __name__ == "__main__":
    sys.exit(main())
