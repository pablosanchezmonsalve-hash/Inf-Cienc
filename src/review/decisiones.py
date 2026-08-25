"""El formato del archivo de decisiones humanas, declarado una sola vez.

POR QUÉ EXISTE
    `build_review.py` pinta los botones y `apply_decisions.py` aplica lo que se
    pulsó. Hasta ahora cada uno tenía su propia lista de veredictos: la del
    generador vivía en `VEREDICTOS` y en los `veredictos` de cada caso, la del
    aplicador en un `isin([...])` escrito a mano, y la explicación al operador
    en la cabecera del CSV que emite el navegador. Cuatro listas para un mismo
    vocabulario.

    El patrón ya conocido en este repositorio: una lista escrita a mano deja de
    cubrirlo todo, y nadie se entera porque lo que no está en la lista
    simplemente no se procesa. Un veredicto que el generador ofrece y el
    aplicador no conoce se lee, se cuenta como leído y no hace nada.

QUÉ APORTA
    - `VOCABULARIO`: qué significa cada veredicto y qué hace al aplicarse.
    - `COLAS`: qué veredictos admite cada cola. La pregunta «¿son la misma
      persona?» no se le hace a una firma sola, y «¿este ORCID es correcto?» no
      se le hace a un grupo de variantes.
    - `leer()`: el lector del CSV, con el mismo criterio de comentarios en los
      dos scripts.
    - `orcid_valido()`: el dígito de control, para que un identificador tecleado
      a mano no se publique con una errata.

    Y el guardián: `veredictos_desconocidos()` compara lo que trae el CSV contra
    este vocabulario y devuelve la diferencia, para que quien aplique falle
    nombrándola en vez de ignorarla en silencio.
"""

from __future__ import annotations

import io
import re
from pathlib import Path

import pandas as pd

# veredicto -> (etiqueta del botón, qué hace al aplicarse)
#
# `pendiente` está aquí porque VIAJA en el CSV: es el valor por defecto de toda
# fila sin decidir. No hace nada, y decirlo explícitamente evita que el
# guardián de veredictos desconocidos lo denuncie en cada corrida.
VOCABULARIO: dict[str, tuple[str, str]] = {
    "pendiente": ("Sigo sin saber",
                  "no se aplica nada; el caso sigue en la cola"),
    "misma": ("Misma persona",
              "une las firmas en una identidad consolidada"),
    "distintas": ("Personas distintas",
                  "no une nada; sirve para detectar contradicciones"),
    "no_es_persona": ("No es una persona",
                      "descarta la firma del recuento de autores"),
    "es_persona": ("Sí es una persona",
                   "conserva la firma y la saca de la cola E-09"),
    "orcid_correcto": ("El ORCID es correcto",
                       "conserva la asignación y la etiqueta como confirmada "
                       "por revisión humana"),
    "orcid_incorrecto": ("El ORCID no es de esta persona",
                         "RETIRA la asignación: la ficha vuelve a no tener ORCID"),
    "orcid_encontrado": ("Encontré su ORCID",
                         "añade la asignación con el identificador tecleado"),
    "orcid_no_encontrado": ("Busqué y no tiene",
                            "registra que alguien buscó y no encontró registro"),
}

# Los veredictos que ofrece cada cola. Lo que no está aquí usa `POR_DEFECTO`.
POR_DEFECTO = ["misma", "distintas"]
COLAS: dict[str, list[str]] = {
    "Firma sin forma de persona": ["no_es_persona", "es_persona"],
    "ORCID sin confirmar": ["orcid_correcto", "orcid_incorrecto"],
    "ORCID no verificable": ["orcid_correcto", "orcid_incorrecto"],
    "OpenAlex discrepa": ["orcid_correcto", "orcid_incorrecto"],
    "Firma sin ORCID": ["orcid_encontrado", "orcid_no_encontrado"],
}

# Colas cuyo veredicto necesita que además se teclee un identificador.
PIDEN_ORCID = {"Firma sin ORCID"}

# Las colas que responden a la pregunta «¿qué ORCID le corresponde a esta
# firma?». Se agrupan para poder filtrarlas juntas en la página: son las que
# se verifican abriendo un registro en orcid.org, y esa es una sesión de
# trabajo distinta de la de decidir si dos firmas son la misma persona.
FAMILIA_ORCID = {
    "ORCID compartido", "ORCID en conflicto", "Fuentes en desacuerdo",
    "Mismo ORCID por afiliación", "Candidato por afiliación",
    "Candidato por afiliación (ambiguo)", "ORCID sin confirmar",
    "ORCID no verificable", "Firma sin ORCID", "OpenAlex discrepa",
}


def veredictos_de(cola: str) -> list[str]:
    return COLAS.get(cola, POR_DEFECTO)


def etiqueta(veredicto: str) -> str:
    return VOCABULARIO.get(veredicto, (veredicto, ""))[0]


def leer(path: Path) -> pd.DataFrame:
    """Lee el CSV de decisiones sin comerse las almohadillas de las notas.

    `pd.read_csv(comment='#')` trunca la línea en la primera almohadilla ESTÉ
    DONDE ESTÉ: una nota como «cotejado con el registro #2» perdía la mitad, y
    en silencio. La cabecera que emite el navegador son líneas completas de
    comentario al principio del archivo, así que se recortan por posición y el
    resto se lee entero.
    """
    texto = path.read_text(encoding="utf-8-sig")
    lineas = texto.splitlines()
    i = 0
    while i < len(lineas) and lineas[i].startswith("#"):
        i += 1
    return pd.read_csv(io.StringIO("\n".join(lineas[i:])), dtype=str).fillna("")


def firmas_de(fila) -> list[str]:
    return [x.strip() for x in str(fila["firmas"]).split("|") if x.strip()]


def veredictos_desconocidos(d: pd.DataFrame) -> list[str]:
    """Veredictos presentes en el CSV que este vocabulario no define."""
    return sorted({v for v in d.get("veredicto", []) if v and v not in VOCABULARIO})


def veredictos_fuera_de_cola(d: pd.DataFrame) -> list[tuple[str, str, str]]:
    """Filas cuyo veredicto no corresponde a la pregunta que hace su cola.

    Sólo puede ocurrir editando el CSV a mano o concatenando exportaciones de
    versiones distintas. Aplicarlo produciría un resultado que nadie decidió.
    """
    fuera = []
    for _, r in d.iterrows():
        v, cola = r.get("veredicto", ""), r.get("cola", "")
        if not v or v == "pendiente" or v not in VOCABULARIO:
            continue
        if cola in COLAS and v not in COLAS[cola]:
            fuera.append((r.get("caso_id", ""), cola, v))
        elif cola not in COLAS and v not in POR_DEFECTO:
            fuera.append((r.get("caso_id", ""), cola, v))
    return fuera


ORCID_RE = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")


def orcid_valido(s: str) -> bool:
    """Forma y dígito de control (ISO 7064 MOD 11-2), como exige el propio ORCID.

    Un identificador se teclea a mano en la página de revisión y una errata de
    un dígito produce un ORCID que existe y es de otra persona. La forma no
    basta para detectarlo; el dígito de control sí detecta el error de un solo
    carácter, que es justo el que se comete al copiar.
    """
    s = (s or "").strip()
    if not ORCID_RE.match(s):
        return False
    digitos = s.replace("-", "")
    total = 0
    for c in digitos[:15]:
        total = (total + int(c)) * 2
    resto = (12 - total % 11) % 11
    return ("X" if resto == 10 else str(resto)) == digitos[15]
