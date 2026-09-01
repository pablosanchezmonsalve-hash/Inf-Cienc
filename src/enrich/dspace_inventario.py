"""Contraste de ORCID contra el repositorio institucional (DSpace). Para
revisión humana, no para publicar automáticamente.

QUÉ ES LA FUENTE
    `data/raw/Inventario_Repositorio_Institucional_UFT.csv` es un volcado de
    metadatos DSpace del repositorio institucional de la UFT: tesis de
    pregrado y posgrado, y artículos, libros y capítulos autoarchivados por
    sus propios autores. Cada fila trae `dc.contributor.author` (quien
    depositó el ítem) y, cuando se declaró, `dc.identifier.orcid` — uno o
    varios ORCID separados por `||`, sin que el archivo diga cuál corresponde
    a cuál nombre cuando hay más de uno.

    El usuario del proyecto (responsable institucional) declaró en sesión que
    todo autor afiliado a la UFT que aparece en este repositorio debería tener
    su ORCID capturado ahí — es la premisa bajo la que se construye este
    conector. Sigue siendo una fuente DE TERCEROS, ajena al pipeline
    Scopus/SciVal, y por eso vale como evidencia independiente.

    LIMPIEZA APLICADA ANTES DE VERSIONAR (2026-09-01)
    El export original de DSpace trae tres columnas
    `dc.description.provenance[en|en_US|es]` con el LOG DE FLUJO DE TRABAJO
    del repositorio: quién subió cada ítem y quién lo aprobó, con su correo
    @uft.cl — presente en 2.539 de las 3.271 filas (78 %). Eso no es dato
    bibliométrico, es metadato operativo del sistema DSpace, y publicarlo en
    este repositorio (público) habría expuesto el correo de cientos de
    funcionarios y estudiantes sin que nadie lo decidiera. Se quitaron esas
    tres columnas y se reescribió el archivo en UTF-8 (el original venía en
    cp1252) antes de que tocara `data/raw/`; ninguna otra columna contenía
    correos (verificado sobre las 157 columnas originales). El original sin
    limpiar no se conserva en el repositorio.

DOS NIVELES DE EVIDENCIA, NO UNO
    - **Ancla en publicación compartida** (como `orcid_crossref.py`): la firma
      tiene una publicación en el universo Scopus/SciVal cuyo DOI también
      aparece en este inventario. Si además el nombre depositante coincide
      con la firma, es la evidencia más fuerte que este conector puede dar:
      es literalmente el mismo trabajo, declarado por la misma persona, en dos
      sistemas distintos. Si el DOI coincide pero el nombre depositante es
      OTRO coautor, el ORCID de la firma puede estar entre los varios que ese
      coautor declaró — corrobora, pero no es una declaración directa suya.
    - **Sólo por nombre, en cualquier obra propia** (como
      `orcid_afiliacion.py`): sin publicación en común, se busca a la firma
      por apellido+inicial en TODO el inventario — su propia tesis, un
      artículo que autoarchivó ella misma, lo que sea. Mismo riesgo de
      homónimos que el resto de las búsquedas por nombre de este proyecto: se
      declara la cuenta de candidatos, nunca se elige por ella.

QUÉ NO HACE
    No escribe en `authors_orcid.csv` ni decide ningún veredicto. Alimenta la
    herramienta de revisión (`build_review.py`) con una fuente de evidencia
    más; el veredicto lo sigue poniendo una persona (`D-08`).

USO
    python3 src/enrich/dspace_inventario.py            # sin red, todo local
    python3 src/enrich/dspace_inventario.py --test     # verifica la lógica

Salidas:
    data/interim/dspace_verificacion.csv   contraste para firmas CON ORCID ya
                                            asignado (confirma / contradice)
    internal/dspace_candidatos.csv         candidatos por nombre para firmas
                                            SIN ORCID asignado (capa interna)
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audit"))
import common as c  # noqa: E402

RAW_INVENTARIO = c.RAW / "Inventario_Repositorio_Institucional_UFT.csv"


def _norm(text: str) -> str:
    base = unicodedata.normalize("NFD", str(text or ""))
    base = "".join(ch for ch in base if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z\s]", " ", base.lower()).strip()


def clave_firma(nombre: str) -> tuple[str, str]:
    """Idéntica a `orcid_crossref.clave_firma`: no se reimplementa aparte para
    no divergir, se copia porque ese módulo depende de una sesión de red que
    este conector no necesita."""
    tokens = _norm(nombre.replace("-", " ")).split()
    if not tokens:
        return "", ""
    apellido = [t for t in tokens if len(t) > 1]
    iniciales = [t for t in tokens if len(t) == 1]
    return " ".join(apellido), (iniciales[0] if iniciales else "")


def clave_dspace(autor_inv: str) -> tuple[str, str]:
    """'Apellido, Nombre' de DSpace -> misma clave (apellido, inicial)."""
    if "," in autor_inv:
        apellido, dado = autor_inv.split(",", 1)
    else:
        partes = autor_inv.rsplit(" ", 1)
        apellido, dado = (partes[0], partes[1]) if len(partes) == 2 else (autor_inv, "")
    apellido = _norm(apellido.replace("-", " "))
    dado_n = _norm(dado)
    inicial = dado_n[0] if dado_n else ""
    return apellido, inicial


def _s(v) -> str:
    """pandas deja NaN (float) en celdas vacías incluso con dtype=str: `or ""`
    no lo atrapa porque nan es truthy en Python."""
    return "" if v is None or (isinstance(v, float)) else str(v)


def norm_doi(d) -> str:
    d = _s(d).strip().lower()
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", d)


def norm_orcid(o) -> str:
    return (_s(o).strip().upper()
            .replace("HTTPS://ORCID.ORG/", "").replace("HTTP://ORCID.ORG/", ""))


def leer_inventario(path: Path = RAW_INVENTARIO) -> pd.DataFrame:
    """El export nativo de DSpace viene en cp1252, pero el archivo que vive en
    `data/raw/` ya se reescribió en UTF-8 al limpiarlo de columnas de
    provenance (ver el docstring del módulo) — se lee en UTF-8, no cp1252."""
    return pd.read_csv(path, sep=";", encoding="utf-8", dtype=str,
                        on_bad_lines="skip", low_memory=False)


def indices(inv: pd.DataFrame) -> tuple[dict, dict]:
    """Construye el índice por DOI y el índice por clave de nombre.

    Cada entrada trae la lista de ORCID declarados en esa fila (puede tener
    más de uno) y el nombre depositante tal cual lo escribió DSpace, para que
    quien lea la evidencia vea de una vez si es la misma persona nombrada o
    un coautor distinto que subió el archivo.
    """
    por_doi: dict[str, list[dict]] = {}
    por_nombre: dict[tuple[str, str], list[dict]] = {}
    for _, row in inv.iterrows():
        autor = _s(row.get("dc.contributor.author")).strip()
        orcids_raw = _s(row.get("dc.identifier.orcid"))
        orcids = [norm_orcid(x) for x in orcids_raw.split("||") if x.strip()]
        tipo = _s(row.get("dc.type")).strip()
        entrada = {"autor_dspace": autor, "orcids": orcids, "tipo": tipo}

        doi = norm_doi(row.get("dc.identifier.doi"))
        if doi:
            por_doi.setdefault(doi, []).append(entrada)

        if autor and orcids:
            clave = clave_dspace(autor)
            if clave[0]:
                por_nombre.setdefault(clave, []).append(entrada)
    return por_doi, por_nombre


def verificacion_por_doi(firmas: list[str], eids_por_firma: dict[str, set],
                         doi_por_eid: dict[str, str], orcid_actual: dict[str, str],
                         por_doi: dict[str, list[dict]]) -> pd.DataFrame:
    """Contraste DOI-anclado para firmas que YA tienen un ORCID asignado."""
    filas = []
    for firma in firmas:
        actual = orcid_actual.get(firma)
        if not actual:
            continue
        eids = eids_por_firma.get(firma, set())
        dois = {norm_doi(doi_por_eid.get(e, "")) for e in eids}
        dois.discard("")
        hallazgos = [(d, h) for d in dois for h in por_doi.get(d, [])]
        if not hallazgos:
            continue

        clave_propia = clave_firma(firma)
        directos = [(d, h) for d, h in hallazgos if clave_dspace(h["autor_dspace"]) == clave_propia]
        base = directos if directos else hallazgos
        coincide = any(actual in h["orcids"] for _, h in base)
        es_directo = bool(directos)

        if coincide and es_directo:
            veredicto = "confirma_directa"
        elif coincide:
            veredicto = "confirma_indirecta"
        elif es_directo:
            veredicto = "contradice_directa"
        else:
            veredicto = "sin_coincidencia_en_dspace"

        obs = "; ".join(
            f"{d} · {h['autor_dspace']} · {'/'.join(h['orcids']) or 'sin ORCID'} ({h['tipo'] or 's/d'})"
            for d, h in hallazgos[:4])
        filas.append({
            "nombre_en_fuente": firma, "orcid_actual": actual, "veredicto": veredicto,
            "n_publicaciones_cruzadas": len({d for d, _ in hallazgos}),
            "evidencia": obs, "fuente": "Inventario Repositorio Institucional UFT",
        })
    cols = ["nombre_en_fuente", "orcid_actual", "veredicto",
            "n_publicaciones_cruzadas", "evidencia", "fuente"]
    return pd.DataFrame(filas, columns=cols)


def candidatos_por_nombre(firmas_sin_orcid: list[str],
                          por_nombre: dict[tuple[str, str], list[dict]]) -> pd.DataFrame:
    """Búsqueda por nombre en TODO el inventario, para firmas sin ORCID.

    Mismo criterio homónimo-seguro que `orcid_afiliacion.py`: declara cuántas
    personas del inventario coinciden con la firma y cuántas firmas reclaman
    cada ORCID, nunca elige entre homónimos.
    """
    firmas_por_orcid: dict[str, set[str]] = {}
    for firma in firmas_sin_orcid:
        clave = clave_firma(firma)
        if not clave[0]:
            continue
        for h in por_nombre.get(clave, []):
            for o in h["orcids"]:
                firmas_por_orcid.setdefault(o, set()).add(firma)

    filas = []
    for firma in firmas_sin_orcid:
        clave = clave_firma(firma)
        if not clave[0]:
            continue
        vistos: dict[str, dict] = {}
        for h in por_nombre.get(clave, []):
            for o in h["orcids"]:
                if o not in vistos:
                    vistos[o] = {"orcid": o, "autor_dspace": h["autor_dspace"],
                                "tipos": set(), "n_obras": 0}
                vistos[o]["tipos"].add(h["tipo"] or "s/d")
                vistos[o]["n_obras"] += 1
        for o, v in vistos.items():
            filas.append({
                "nombre_en_fuente": firma,
                "orcid": o,
                "nombre_en_dspace": v["autor_dspace"],
                "tipos_de_obra": "|".join(sorted(v["tipos"])),
                "obras_del_titular_en_el_inventario": v["n_obras"],
                "orcid_reclamado_por_n_firmas": len(firmas_por_orcid.get(o, set())),
                "tipo": "dspace_candidato_por_nombre",
                "severidad": "media",
                "consecuencia": "coincide el nombre en el repositorio institucional, "
                                "pero sin publicación en común que lo respalde",
                "resolucion": "PENDIENTE_REVISION_HUMANA",
            })
    cols = ["nombre_en_fuente", "orcid", "nombre_en_dspace", "tipos_de_obra",
            "obras_del_titular_en_el_inventario", "orcid_reclamado_por_n_firmas",
            "tipo", "severidad", "consecuencia", "resolucion"]
    return pd.DataFrame(filas, columns=cols)


def autotest() -> int:
    casos = []

    inv = pd.DataFrame([
        # Fila 1: la firma que se busca deposita su propio artículo, ORCID único.
        {"dc.contributor.author": "López-Soto, Paulo", "dc.identifier.doi": "10.1/aaa",
         "dc.identifier.orcid": "https://orcid.org/0000-0003-2559-6464", "dc.type": "Article"},
        # Fila 2: coautor distinto deposita, con 2 ORCID (uno es el nuestro).
        {"dc.contributor.author": "Balboa, Elisa", "dc.identifier.doi": "10.1/bbb",
         "dc.identifier.orcid": "https://orcid.org/0000-0003-0577-7604||https://orcid.org/0000-0002-7953-6769",
         "dc.type": "Article"},
        # Fila 3: mismo nombre que una firma, pero ORCID DISTINTO al asignado.
        {"dc.contributor.author": "Arroyo, Antonio", "dc.identifier.doi": "10.1/ccc",
         "dc.identifier.orcid": "https://orcid.org/0000-0002-6248-9257", "dc.type": "Article"},
        # Fila 4: tesis propia de alguien sin ORCID asignado todavía (candidato).
        {"dc.contributor.author": "Pérez Soto, Juan", "dc.identifier.doi": "",
         "dc.identifier.orcid": "https://orcid.org/0000-A", "dc.type": "Tesis"},
        # Fila 5: homónimo del candidato anterior, ORCID distinto.
        {"dc.contributor.author": "Pérez Rojas, Juan", "dc.identifier.doi": "",
         "dc.identifier.orcid": "https://orcid.org/0000-B", "dc.type": "Article"},
    ])
    por_doi, por_nombre = indices(inv)
    casos.append(("índice por DOI construido", len(por_doi) == 3, list(por_doi)))
    casos.append(("índice por nombre construido", len(por_nombre) >= 3, list(por_nombre)))

    eids_por_firma = {"López-Soto P.": {"e1"}, "de la Fuente M.": {"e2"}, "Arroyo A.": {"e3"}}
    doi_por_eid = {"e1": "10.1/aaa", "e2": "10.1/bbb", "e3": "10.1/ccc"}
    orcid_actual = {"López-Soto P.": "0000-0003-2559-6464",
                    "de la Fuente M.": "0000-0003-0577-7604",
                    "Arroyo A.": "0000-0003-0157-5175"}

    v = verificacion_por_doi(list(eids_por_firma), eids_por_firma, doi_por_eid,
                             orcid_actual, por_doi)
    fila = {r["nombre_en_fuente"]: r["veredicto"] for _, r in v.iterrows()}
    casos.append(("mismo nombre, mismo ORCID -> confirma_directa",
                  fila.get("López-Soto P.") == "confirma_directa", fila))
    casos.append(("otro coautor deposita, ORCID igual está en la lista -> confirma_indirecta",
                  fila.get("de la Fuente M.") == "confirma_indirecta", fila))
    casos.append(("mismo nombre, ORCID distinto -> contradice_directa",
                  fila.get("Arroyo A.") == "contradice_directa", fila))

    cand = candidatos_por_nombre(["Pérez Soto J.", "Pérez Rojas J."], por_nombre)
    casos.append(("candidato por nombre, sin homónimo, 1 obra propia",
                  len(cand[cand.nombre_en_fuente == "Pérez Soto J."]) == 1, cand.to_dict("records")))
    casos.append(("no confunde apellidos compuestos distintos (Soto vs Rojas)",
                  set(cand[cand.nombre_en_fuente == "Pérez Soto J."].orcid) == {"0000-A"}
                  and set(cand[cand.nombre_en_fuente == "Pérez Rojas J."].orcid) == {"0000-B"},
                  cand.to_dict("records")))
    casos.append(("no escribe columnas de asignación publicable",
                  "confianza" not in cand.columns and "fuente" not in cand.columns,
                  list(cand.columns)))
    casos.append(("todo candidato queda para revisión humana",
                  (cand.resolucion == "PENDIENTE_REVISION_HUMANA").all(), None))

    # Firma sin ninguna publicación cruzable: no aparece en la verificación.
    v2 = verificacion_por_doi(["Nadie N."], {}, {}, {"Nadie N.": "0000-Z"}, por_doi)
    casos.append(("firma sin DOI cruzable no genera fila", len(v2) == 0, None))

    ok = True
    for nombre, paso, obs in casos:
        print(f"  {'OK  ' if paso else 'FALLA'} {nombre}" + (f"   {obs}" if not paso else ""))
        ok &= paso
    print("\n" + ("TODOS LOS CASOS OK" if ok else "HAY CASOS FALLANDO"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--test", action="store_true", help="verifica la lógica sin leer el inventario")
    args = ap.parse_args()

    c.banner("CONTRASTE CONTRA EL REPOSITORIO INSTITUCIONAL (DSPACE)")
    if args.test:
        return autotest()

    if not RAW_INVENTARIO.exists():
        sys.exit(f"No se encontró {RAW_INVENTARIO.relative_to(c.ROOT)}.\n"
                  "Este conector no sale a red: necesita el export de DSpace en data/raw/.")

    inv = leer_inventario()
    print(f"  filas del inventario: {len(inv)}")
    por_doi, por_nombre = indices(inv)
    print(f"  publicaciones con DOI: {len(por_doi)} · claves de nombre con ORCID: {len(por_nombre)}")

    log = pd.read_csv(c.INTERNAL / "matching_log.csv", dtype=str)
    eids_por_firma = log.groupby("nombre_en_fuente")["eid"].apply(set).to_dict()
    pu = pd.read_csv(c.INTERIM / "publications_universe.csv", dtype=str)
    doi_por_eid = {r["eid"]: r.get("doi", "") for _, r in pu.iterrows()}

    ao_path = c.ROOT / "data" / "enriched" / "authors_orcid.csv"
    orcid_actual = {}
    if ao_path.exists():
        orcid_actual = {r["nombre_en_fuente"]: r["orcid"]
                       for _, r in pd.read_csv(ao_path, dtype=str).iterrows()}

    todas_las_firmas = sorted(log["nombre_en_fuente"].unique())
    con_orcid = [f for f in todas_las_firmas if orcid_actual.get(f)]
    sin_orcid = [f for f in todas_las_firmas if not orcid_actual.get(f)]

    verif = verificacion_por_doi(con_orcid, eids_por_firma, doi_por_eid, orcid_actual, por_doi)
    c.write_interim(verif, "dspace_verificacion.csv")
    resumen = verif.veredicto.value_counts().to_dict() if len(verif) else {}
    print(f"\n  firmas con ORCID cruzadas contra el inventario: {len(verif)}")
    for k, v in sorted(resumen.items()):
        print(f"    {k:28s}: {v}")
    print("  OK · data/interim/dspace_verificacion.csv")

    cand = candidatos_por_nombre(sin_orcid, por_nombre)
    if len(cand):
        c.write_internal(cand, "dspace_candidatos.csv")
        unicos = cand[cand.orcid_reclamado_por_n_firmas == 1].nombre_en_fuente.nunique()
        print(f"\n  candidatos por nombre (firmas sin ORCID): {cand.nombre_en_fuente.nunique()}")
        print(f"    de ellas, coincidencia 1-a-1 con un solo titular: {unicos}")
        print("  OK · internal/dspace_candidatos.csv")
    else:
        print("\n  Sin candidatos nuevos por nombre. No se escribe internal/dspace_candidatos.csv.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
