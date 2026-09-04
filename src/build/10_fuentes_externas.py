"""Build 10 — Artefacto público de fuentes externas al corpus Scopus.

Lee `data/interim/fuentes_externas.json` (generado por
`src/enrich/fuentes_externas.py`) y escribe `data/processed/fuentes_externas.json`,
que consume `web/fuentes-externas.html`.

AQUÍ ESTÁ LA FRONTERA ENTRE LAS DOS CAPAS, Y NO ES UN DETALLE DE FORMATO
    El artefacto de `interim/` trae una fila por PAR obra-autor, con el nombre
    de la persona a la que la fuente institucional atribuye cada trabajo. Ese
    dato NO se publica.

    No porque los nombres sean secretos —los de investigadores son públicos—
    sino porque la atribución no está verificada. La fuente declara que Fulana
    firma tal obra; nadie lo ha comprobado. `docs/LAYERS.md` §3 clasifica las
    afirmaciones no verificadas sobre personas reales como capa interna, y
    `CLAUDE.md` (`<data_governance>`) prohíbe publicarlas por defecto.

    Medido el 2026-09-04 sobre las 344 personas que la fuente nombra: sólo 132
    (38 %) se confirman cruzando el corpus Scopus, el directorio de autores por
    afiliación y los ORCID ya asignados. Y 152 nombres vienen acompañados de un
    ORCID que el proyecto tiene asignado a OTRA persona — en el inventario de
    autoarchivo la columna de ORCID lleva a menudo el identificador de algún
    coautor, no el de quien figura como autor. Publicar eso sería atribuir
    trabajos a personas equivocadas, con nombre y apellido, en una página
    pública.

QUÉ SÍ SE PUBLICA
    Las OBRAS. Que un DOI exista, esté fuera del universo Scopus y proceda de
    una fuente institucional declarada es una afirmación sobre un trabajo, no
    sobre una persona, y es del mismo nivel de evidencia que `PD-01` y `PD-03`
    ya publican: la institución lo declara, el proyecto no reverifica cada uno.

    Las filas se colapsan a obras: `interim` trae un par obra-autor por fila, y
    contarlas como publicaciones multiplicaría cada trabajo por su número de
    autores.

QUÉ SE DECLARA EN VEZ DE OCULTARSE
    `atribuciones_retenidas` dice cuántos pares obra-autor existen y no se
    publican, y `personas_nombradas_en_la_fuente` cuántas personas distintas
    hay detrás. El lector sabe que ese dato existe y por qué no está, en vez de
    no enterarse (`D-14`, y el criterio de transparencia de `PD-02`/`PD-04`
    con sus pendientes de revisión).

Salida:
  data/processed/fuentes_externas.json
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
INTERIM = ROOT / "data" / "interim" / "fuentes_externas.json"
OUT = ROOT / "data" / "processed" / "fuentes_externas.json"

# Campos de una fila de `interim` que describen la OBRA. `autor_uft` queda
# fuera a propósito: es la atribución sin verificar.
CAMPOS_OBRA = ("titulo", "doi", "anio", "escuela", "tipo")


def clave_obra(p: dict) -> str:
    """Identidad de una obra: su DOI, y si no lo tiene, su título normalizado.

    Sin esto, las 701 filas obra-autor se publicarían como 701 publicaciones,
    cuando son 435 DOI distintos: cada trabajo aparece una vez por cada persona
    a la que la fuente se lo atribuye.
    """
    doi = (p.get("doi") or "").strip().lower()
    if doi:
        return doi
    titulo = " ".join((p.get("titulo") or "").split()).lower()
    return f"titulo:{titulo}" if titulo else ""


def colapsar(publicaciones: list[dict]) -> tuple[list[dict], int]:
    """Una entrada por obra, sin la atribución nominal.

    Cada obra guarda TODAS las fuentes que la declaran, no la primera que
    aparece. Quedarse con una sola hacía que un trabajo presente en DSpace y
    en el autoarchivo contara sólo para DSpace, y el desglose por fuente
    decía que el autoarchivo aporta 46 obras cuando declara 302 filas.
    """
    obras: dict[str, dict] = {}
    for p in publicaciones:
        k = clave_obra(p)
        if not k:
            continue
        o = obras.get(k)
        if o is None:
            o = obras[k] = {c: p.get(c, "") for c in CAMPOS_OBRA}
            o["fuentes"] = []
            o["fuentes_id"] = []
        fid = p.get("fuente_id", "")
        if fid and fid not in o["fuentes_id"]:
            o["fuentes_id"].append(fid)
            o["fuentes"].append(p.get("fuente", ""))
        # Un campo puede venir vacío en una fuente y poblado en otra.
        for c in CAMPOS_OBRA:
            if not o.get(c) and p.get(c):
                o[c] = p[c]
    return list(obras.values()), len(publicaciones)


def main() -> int:
    if not INTERIM.exists():
        print("  fuentes_externas  : OMITIDO — falta data/interim/fuentes_externas.json")
        print("                       Ejecute: py src/enrich/fuentes_externas.py")
        return 0

    data = json.loads(INTERIM.read_text(encoding="utf-8"))
    obras, filas = colapsar(data.get("publicaciones") or [])
    personas = len(data.get("autores") or [])

    # Obras en las que cada fuente aparece. Una obra declarada por dos
    # fuentes cuenta en las dos, así que estas cifras suman más que el total:
    # son aportes, no obras, y la página lo dice donde se lee.
    por_fuente = Counter(f for o in obras for f in o["fuentes_id"])
    en_varias = sum(1 for o in obras if len(o["fuentes_id"]) > 1)
    sin_doi = sum(1 for o in obras if not (o.get("doi") or "").strip())

    meta = dict(data.get("meta") or {})
    meta["advertencia"] = (
        "Inventario declarado por fuentes institucionales, fuera del corpus "
        "Scopus/SciVal. Se publican las OBRAS, no a quién se le atribuye cada "
        "una: la atribución obra-persona que traen estas fuentes no está "
        "verificada, y en el inventario de autoarchivo el identificador ORCID "
        "de una fila corresponde con frecuencia a un coautor y no a quien "
        "figura como autor. Esa parte queda en la capa interna hasta que una "
        "revisión caso por caso la confirme."
    )
    meta.pop("descripcion_autores", None)

    salida = {
        "meta": meta,
        "publicaciones": obras,
        "resumen": {
            "total_publicaciones": len(obras),
            "sin_doi": sin_doi,
            "por_fuente": dict(por_fuente),
            "en_mas_de_una_fuente": en_varias,
            "atribuciones_retenidas": filas,
            "personas_nombradas_en_la_fuente": personas,
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  fuentes_externas  : {len(obras)} obras → {OUT.name}")
    print(f"                      {filas} atribuciones obra-persona retenidas "
          f"({personas} personas), no se publican")
    return 0


if __name__ == "__main__":
    sys.exit(main())
