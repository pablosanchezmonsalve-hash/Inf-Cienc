"""Equivalencia ortográfica entre formas de firma.

QUÉ RESUELVE Y POR QUÉ NO VIOLA D-08
    D-08 dice que el pipeline nunca fusiona identidades por heurística. Esto no
    es una heurística de identidad: es equivalencia de cadenas.

    «González-Valderrama A.», «Gonzalez-Valderrama A.» y «Gonzalez- Valderrama
    A.» no son tres firmas parecidas de las que se infiere que pertenecen a la
    misma persona. Son LA MISMA FIRMA escrita con distinta codificación de
    diacríticos y distinto espaciado. Reconocerlo no afirma nada sobre personas:
    afirma algo sobre cómo la fuente escribió una cadena.

    El argumento que lo sostiene: si detrás de una firma idéntica hubiera dos
    personas, el informe no podría separarlas de ninguna manera, ni antes ni
    después de este módulo. La ambigüedad ya estaba en la fuente. Fusionar
    variantes ortográficas no introduce un error nuevo; sólo deja de contar
    cuatro veces la ambigüedad que había una vez.

DÓNDE SE DETIENE
    Cualquier diferencia que no sea ortográfica queda PENDIENTE, porque ahí sí
    hay un juicio:

      Gutiérrez M. | Gutiérrez J.          iniciales distintas
      Ballesteros P. | Ballesteros P. P.   inicial adicional
      Orellana-Donoso M. | Orellana-Donoso M.I.
      De la Fuente M. | De la Fuente López M.   apellido materno

    Ninguno de esos se toca. Que dos firmas con inicial distinta sean la misma
    persona, o que «M.» y «M.I.» lo sean, es exactamente lo que una persona
    tiene que ir a comprobar.

LA REGLA, ESCRITA UNA SOLA VEZ
    Dos firmas son la misma si coinciden tras: descomponer en NFD, quitar los
    diacríticos, pasar a minúsculas, tratar el punto y cualquier guion como
    separador, y colapsar los espacios.
"""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
import sys

if sys.platform == "win32":
    # La consola de Windows usa cp1252 por defecto: revienta cualquier print()
    # con caracteres como "→"/"—"/"·". Mismo patrón que src/enrich/orcid_openalex.py.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# Guion ASCII y los del bloque de puntuación general: la fuente usa varios y
# ninguno significa nada distinto dentro de un apellido compuesto.
_GUIONES = re.compile(r"[-‐-―−]")


def normalizar(firma: str) -> str:
    """La forma comparable de una firma. Ver la regla en el encabezado."""
    s = unicodedata.normalize("NFD", firma)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = _GUIONES.sub(" ", s.lower()).replace(".", " ")
    return re.sub(r"\s+", " ", s).strip()


def subgrupos(firmas: list[str]) -> list[list[str]]:
    """Parte una lista de firmas en clases de equivalencia ortográfica.

    Conserva el orden de aparición dentro de cada clase y entre clases, para
    que la salida sea estable y el diff de un archivo generado sea legible.
    """
    clases: dict[str, list[str]] = defaultdict(list)
    for f in firmas:
        clases[normalizar(f)].append(f)
    return list(clases.values())


def fusionables(firmas: list[str]) -> list[list[str]]:
    """Sólo las clases con más de una forma, que son las que aportan algo."""
    return [c for c in subgrupos(firmas) if len(c) > 1]


def resolver(casos: list[tuple[str, list[str]]],
             prohibidos: set[frozenset[str]] | None = None
             ) -> tuple[list[tuple[str, list[str]]], list[tuple[str, list[str]]]]:
    """Aplica la equivalencia a una lista de casos `(caso_id, firmas)`.

    Devuelve `(resueltos, respetados)`:
      resueltos   subgrupos fusionables, con el caso del que salieron
      respetados  subgrupos que NO se fusionan porque una persona ya declaró
                  explícitamente que esas firmas son de personas distintas

    La segunda lista es la salvaguarda que importa: un veredicto humano manda
    sobre la normalización, siempre y en esa dirección. Si alguien fue a mirar
    y dijo «son dos personas», que las dos formas se escriban igual no lo
    desmiente — significa que la fuente no las distingue, no que quien revisó
    se equivocara.
    """
    prohibidos = prohibidos or set()
    resueltos, respetados = [], []
    for caso_id, firmas in casos:
        for clase in fusionables(firmas):
            if any(par <= set(clase) for par in prohibidos):
                respetados.append((caso_id, clase))
            else:
                resueltos.append((caso_id, clase))
    return resueltos, respetados


# --------------------------------------------------------------------------- #

def autotest() -> int:
    fallos = []

    def ok(cond, msg):
        if not cond:
            fallos.append(msg)

    # La regla, en sus cuatro ejes.
    ok(normalizar("González-Valderrama A.") == normalizar("Gonzalez- Valderrama A."),
       "diacríticos y espaciado deberían colapsar")
    ok(normalizar("López Arana S.") == normalizar("Lopez-Arana S."),
       "guion y espacio deberían ser el mismo separador")
    ok(normalizar("de la Fuente M.") == normalizar("De la Fuente M."),
       "las mayúsculas no deberían separar")
    ok(normalizar("Núñez-Lisboa M.") == normalizar("Nunez-Lisboa M."),
       "la eñe descompuesta debería colapsar")

    # Dónde se detiene: estos NO deben unirse.
    ok(normalizar("Gutiérrez M.") != normalizar("Gutiérrez J."),
       "iniciales distintas no son equivalencia ortográfica")
    ok(normalizar("Ballesteros P.") != normalizar("Ballesteros P. P."),
       "una inicial adicional es un juicio, no una grafía")
    ok(normalizar("Orellana-Donoso M.") != normalizar("Orellana-Donoso M.I."),
       "M. y M.I. no son la misma cadena")
    ok(normalizar("De la Fuente M.") != normalizar("De la Fuente López M."),
       "el apellido materno no es ortografía")

    # Partición de un grupo mixto: se fusiona lo ortográfico y se conserva el
    # resto separado, en vez de fusionar el grupo entero o no tocarlo.
    g = subgrupos(["Garcia J.", "García J.", "Garcia K.", "García F."])
    ok(sorted(len(c) for c in g) == [1, 1, 2], f"partición inesperada: {g}")

    # Un veredicto humano de «distintas» manda sobre la normalización.
    res, resp = resolver([("c1", ["Perez A.", "Pérez A."])],
                         prohibidos={frozenset({"Perez A.", "Pérez A."})})
    ok(res == [] and len(resp) == 1, "un veredicto humano debería bloquear la fusión")

    # Sin firmas repetidas no hay nada que resolver, y no debe inventarse nada.
    ok(fusionables(["Solo A."]) == [], "una firma sola no produce grupo")

    for f in fallos:
        print(f"  FALLA  {f}")
    print(f"  {'OK' if not fallos else 'FALLOS'} · equivalencia_ortografica: "
          f"{9 - len(fallos)}/9 comprobaciones")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(autotest())
