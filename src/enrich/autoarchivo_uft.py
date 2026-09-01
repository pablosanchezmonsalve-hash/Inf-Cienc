"""Contraste contra el inventario de autoarchivo del repositorio institucional
(hoja curada por el equipo de biblioteca, no el volcado crudo de DSpace).

QUÉ ES LA FUENTE, Y EN QUÉ SE DIFERENCIA DE `dspace_inventario.py`
    `data/raw/Inventario_Repositorio_Autoarchivo.xlsx`, hoja «AUTOARCHIVOS»:
    808 obras (2004–2026) que el equipo de biblioteca catalogó a mano al
    autoarchivarlas — trae, por cada una, quién solicitó la subida
    («Autor»), el DOI, el ORCID de esa persona, y su **Facultad o Escuela**
    declarada por la propia biblioteca. Es una fuente DISTINTA del volcado de
    metadatos DSpace (`dspace_inventario.py`): aquella es el sistema
    hablando, ésta es una persona de biblioteca clasificando a mano — y las
    dos pueden confirmarse o contradecirse entre sí, cosa que ya ocurrió
    (ver `contradice_directa` de `Arroyo A.` en ambas).

    Misma premisa declarada por el usuario en sesión: todo autor afiliado
    debería tener su ORCID capturado aquí. Vale lo mismo que en el otro
    conector — es evidencia de un tercero, nunca sube nada a 'verificado'.

DOS PRODUCTOS, DE NATURALEZA DISTINTA
    - ORCID: mismo patrón exacto que `dspace_inventario.py` —
      confirmación/contradicción directa (mismo nombre) o candidato (sin
      publicación en común) — porque es la misma clase de pregunta con la
      misma clase de respuesta.
    - Facultad o Escuela: NO se traduce al vocabulario controlado de
      `config/matching_rules.yml` ni se aplica a `unidad_academica`. Esa
      traducción es exactamente el trabajo que exigió `T-02` — una persona
      con criterio institucional decidiendo qué "CIDOC" o "Familia"
      significan en la jerarquía oficial — y este conector no lo adivina.
      Sólo declara el candidato en bruto, para revisión humana aparte.

USO
    python3 src/enrich/autoarchivo_uft.py            # sin red, todo local
    python3 src/enrich/autoarchivo_uft.py --test      # verifica la lógica

Salidas:
    data/interim/autoarchivo_verificacion.csv   contraste de ORCID (firmas
                                                 que ya tienen uno asignado)
    internal/autoarchivo_candidatos.csv         candidatos de ORCID por
                                                 nombre (firmas sin ninguno)
    internal/autoarchivo_unidad_candidatos.csv  candidatos de Facultad o
                                                 Escuela para firmas con
                                                 'No determinada' — SIN
                                                 traducir al vocabulario,
                                                 sólo declarados
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

RAW_AUTOARCHIVO = c.RAW / "Inventario_Repositorio_Autoarchivo.xlsx"


def _norm(text: str) -> str:
    base = unicodedata.normalize("NFD", str(text or ""))
    base = "".join(ch for ch in base if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z\s]", " ", base.lower()).strip()


def clave_firma(nombre: str) -> tuple[str, str]:
    """Idéntica a `orcid_crossref.clave_firma` / `dspace_inventario.clave_firma`."""
    tokens = _norm(nombre.replace("-", " ")).split()
    if not tokens:
        return "", ""
    apellido = [t for t in tokens if len(t) > 1]
    iniciales = [t for t in tokens if len(t) == 1]
    return " ".join(apellido), (iniciales[0] if iniciales else "")


def clave_autoarchivo(nombre: str) -> tuple[str, str]:
    """'Apellido[-Compuesto], Nombre' -> misma clave (apellido, inicial)."""
    nombre = str(nombre or "")
    if "," not in nombre:
        return "", ""
    apellido, dado = nombre.split(",", 1)
    apellido_n = _norm(apellido.replace("-", " "))
    dado_n = _norm(dado)
    return apellido_n, (dado_n[0] if dado_n else "")


def norm_doi(d) -> str:
    d = "" if d is None or isinstance(d, float) else str(d)
    d = d.strip().lower()
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", d)


def norm_orcid(o) -> str:
    o = "" if o is None or isinstance(o, float) else str(o)
    return (o.strip().upper()
            .replace("HTTPS://ORCID.ORG/", "").replace("HTTP://ORCID.ORG/", ""))


ORCID_RE = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")


def leer_autoarchivo(path: Path = RAW_AUTOARCHIVO) -> pd.DataFrame:
    return pd.read_excel(path, sheet_name="AUTOARCHIVOS")


def indices(df: pd.DataFrame) -> tuple[dict, dict]:
    """Índice por DOI y por clave de nombre. El ORCID de esta hoja es de UNA
    sola persona por fila (quien solicitó la subida) — a diferencia del
    volcado DSpace, aquí no hay listas separadas por '||'."""
    por_doi: dict[str, dict] = {}
    por_nombre: dict[tuple[str, str], list[dict]] = {}
    for _, row in df.iterrows():
        autor = "" if pd.isna(row.get("Autor")) else str(row["Autor"]).strip()
        orcid = norm_orcid(row.get("ORCID"))
        orcid_valido = bool(ORCID_RE.match(orcid))
        escuela = ("" if pd.isna(row.get("Facultad o Escuela"))
                  else str(row["Facultad o Escuela"]).strip())
        tipo = "" if pd.isna(row.get("Tipo de recurso")) else str(row["Tipo de recurso"]).strip()
        entrada = {"autor": autor, "orcid": orcid if orcid_valido else "",
                  "escuela": escuela, "tipo": tipo}

        doi = norm_doi(row.get("DOI"))
        if doi and doi not in ("articulo sin doi",):
            por_doi.setdefault(doi, []).append(entrada)

        if autor:
            clave = clave_autoarchivo(autor)
            if clave[0]:
                por_nombre.setdefault(clave, []).append(entrada)
    return por_doi, por_nombre


def verificacion_por_doi(firmas: list[str], eids_por_firma: dict[str, set],
                         doi_por_eid: dict[str, str], orcid_actual: dict[str, str],
                         por_doi: dict[str, list[dict]]) -> pd.DataFrame:
    filas = []
    for firma in firmas:
        actual = orcid_actual.get(firma)
        if not actual:
            continue
        eids = eids_por_firma.get(firma, set())
        dois = {norm_doi(doi_por_eid.get(e, "")) for e in eids}
        dois.discard("")
        hallazgos = [(d, h) for d in dois for h in por_doi.get(d, []) if h["orcid"]]
        if not hallazgos:
            continue

        clave_propia = clave_firma(firma)
        directos = [(d, h) for d, h in hallazgos if clave_autoarchivo(h["autor"]) == clave_propia]
        base = directos if directos else hallazgos
        coincide = any(actual == h["orcid"] for _, h in base)
        es_directo = bool(directos)

        if coincide and es_directo:
            veredicto = "confirma_directa"
        elif coincide:
            veredicto = "confirma_indirecta"
        elif es_directo:
            veredicto = "contradice_directa"
        else:
            veredicto = "sin_coincidencia"

        obs = "; ".join(f"{d} · {h['autor']} · {h['orcid'] or 'sin ORCID'} ({h['tipo'] or 's/d'})"
                        for d, h in hallazgos[:4])
        filas.append({
            "nombre_en_fuente": firma, "orcid_actual": actual, "veredicto": veredicto,
            "n_publicaciones_cruzadas": len({d for d, _ in hallazgos}),
            "evidencia": obs, "fuente": "Inventario de autoarchivo (biblioteca UFT)",
        })
    cols = ["nombre_en_fuente", "orcid_actual", "veredicto",
            "n_publicaciones_cruzadas", "evidencia", "fuente"]
    return pd.DataFrame(filas, columns=cols)


def candidatos_por_nombre(firmas_sin_orcid: list[str],
                          por_nombre: dict[tuple[str, str], list[dict]]) -> pd.DataFrame:
    firmas_por_orcid: dict[str, set[str]] = {}
    for firma in firmas_sin_orcid:
        clave = clave_firma(firma)
        if not clave[0]:
            continue
        for h in por_nombre.get(clave, []):
            if h["orcid"]:
                firmas_por_orcid.setdefault(h["orcid"], set()).add(firma)

    filas = []
    for firma in firmas_sin_orcid:
        clave = clave_firma(firma)
        if not clave[0]:
            continue
        vistos: dict[str, dict] = {}
        for h in por_nombre.get(clave, []):
            if not h["orcid"]:
                continue
            if h["orcid"] not in vistos:
                vistos[h["orcid"]] = {"orcid": h["orcid"], "autor": h["autor"],
                                      "tipos": set(), "n_obras": 0}
            vistos[h["orcid"]]["tipos"].add(h["tipo"] or "s/d")
            vistos[h["orcid"]]["n_obras"] += 1
        for orcid, v in vistos.items():
            filas.append({
                "nombre_en_fuente": firma, "orcid": orcid,
                "nombre_en_autoarchivo": v["autor"],
                "tipos_de_obra": "|".join(sorted(v["tipos"])),
                "obras_del_titular_en_el_inventario": v["n_obras"],
                "orcid_reclamado_por_n_firmas": len(firmas_por_orcid.get(orcid, set())),
                "tipo": "autoarchivo_candidato_por_nombre", "severidad": "media",
                "consecuencia": "coincide el nombre en el inventario de autoarchivo, "
                                "pero sin publicación en común que lo respalde",
                "resolucion": "PENDIENTE_REVISION_HUMANA",
            })
    cols = ["nombre_en_fuente", "orcid", "nombre_en_autoarchivo", "tipos_de_obra",
            "obras_del_titular_en_el_inventario", "orcid_reclamado_por_n_firmas",
            "tipo", "severidad", "consecuencia", "resolucion"]
    return pd.DataFrame(filas, columns=cols)


def candidatos_de_unidad(firmas_no_determinada: list[str],
                         por_nombre: dict[tuple[str, str], list[dict]]) -> pd.DataFrame:
    """Candidatos de Facultad/Escuela para firmas con 'No determinada'.

    NO traduce al vocabulario de `config/matching_rules.yml`: declara el
    texto tal cual lo escribió la biblioteca. Un mismo apellido+inicial con
    escuelas distintas en distintas obras se declara TAL CUAL —homónimos o
    una persona que cambió de unidad, no se decide aquí— para que la
    revisión humana lo vea, no para que se pierda en un value_counts().
    """
    filas = []
    for firma in firmas_no_determinada:
        clave = clave_firma(firma)
        if not clave[0]:
            continue
        por_escuela: dict[str, dict] = {}
        for h in por_nombre.get(clave, []):
            if not h["escuela"]:
                continue
            e = h["escuela"]
            if e not in por_escuela:
                por_escuela[e] = {"escuela": e, "autor": h["autor"], "n_obras": 0}
            por_escuela[e]["n_obras"] += 1
        for e, v in por_escuela.items():
            filas.append({
                "nombre_en_fuente": firma,
                "escuela_declarada_en_autoarchivo": v["escuela"],
                "nombre_en_autoarchivo": v["autor"],
                "obras_con_esta_escuela": v["n_obras"],
                "escuelas_distintas_para_esta_firma": len(por_escuela),
                "resolucion": "PENDIENTE_REVISION_HUMANA",
            })
    cols = ["nombre_en_fuente", "escuela_declarada_en_autoarchivo", "nombre_en_autoarchivo",
            "obras_con_esta_escuela", "escuelas_distintas_para_esta_firma", "resolucion"]
    return pd.DataFrame(filas, columns=cols)


def autotest() -> int:
    casos = []

    df = pd.DataFrame([
        {"Autor": "López-Soto, Paulo", "DOI": "10.1/aaa", "ORCID": "0000-0003-2559-6464",
         "Tipo de recurso": "Artículo de revista", "Facultad o Escuela": "Medicina"},
        {"Autor": "Otro Y.", "DOI": "10.1/bbb", "ORCID": "0000-0002-7953-6769",
         "Tipo de recurso": "Artículo de revista", "Facultad o Escuela": "Kinesiología"},
        {"Autor": "Arroyo, Antonio", "DOI": "10.1/ccc", "ORCID": "0000-0002-6248-9257",
         "Tipo de recurso": "Artículo de revista", "Facultad o Escuela": "Medicina"},
        {"Autor": "Pérez Soto, Juan", "DOI": None, "ORCID": "0000-0001-2345-6789",
         "Tipo de recurso": "Tesis", "Facultad o Escuela": "Derecho"},
        {"Autor": "Pérez Rojas, Juan", "DOI": None, "ORCID": "0000-0009-8765-4321",
         "Tipo de recurso": "Artículo de revista", "Facultad o Escuela": "Psicología"},
        {"Autor": "Contreras Díaz, Ana", "DOI": None, "ORCID": "AUTOR NO POSEE ORCID",
         "Tipo de recurso": "Artículo de revista", "Facultad o Escuela": "Enfermería"},
        {"Autor": "Contreras Díaz, Ana", "DOI": None, "ORCID": None,
         "Tipo de recurso": "Tesis", "Facultad o Escuela": "Medicina"},
    ])
    por_doi, por_nombre = indices(df)
    casos.append(("índice por DOI construido", len(por_doi) == 3, list(por_doi)))
    casos.append(("un placeholder de ORCID no cuenta como ORCID",
                  all(not h["orcid"] for h in por_nombre.get(clave_autoarchivo("Contreras Díaz, Ana"), []))
                  or clave_autoarchivo("Contreras Díaz, Ana") not in por_nombre, None))

    eids_por_firma = {"López-Soto P.": {"e1"}, "de la Fuente M.": {"e2"}, "Arroyo A.": {"e3"}}
    doi_por_eid = {"e1": "10.1/aaa", "e2": "10.1/bbb", "e3": "10.1/ccc"}
    orcid_actual = {"López-Soto P.": "0000-0003-2559-6464",
                    "de la Fuente M.": "0000-0002-7953-6769",
                    "Arroyo A.": "0000-0003-0157-5175"}

    v = verificacion_por_doi(list(eids_por_firma), eids_por_firma, doi_por_eid,
                             orcid_actual, por_doi)
    fila = {r["nombre_en_fuente"]: r["veredicto"] for _, r in v.iterrows()}
    casos.append(("mismo nombre, mismo ORCID -> confirma_directa",
                  fila.get("López-Soto P.") == "confirma_directa", fila))
    casos.append(("otro depositante, ORCID igual -> confirma_indirecta",
                  fila.get("de la Fuente M.") == "confirma_indirecta", fila))
    casos.append(("mismo nombre, ORCID distinto -> contradice_directa",
                  fila.get("Arroyo A.") == "contradice_directa", fila))

    cand = candidatos_por_nombre(["Pérez Soto J.", "Pérez Rojas J."], por_nombre)
    casos.append(("candidatos por nombre, sin cruzarse entre homónimos",
                  set(cand[cand.nombre_en_fuente == "Pérez Soto J."].orcid) == {"0000-0001-2345-6789"}
                  and set(cand[cand.nombre_en_fuente == "Pérez Rojas J."].orcid) == {"0000-0009-8765-4321"},
                  cand.to_dict("records")))

    cu = candidatos_de_unidad(["López-Soto P.", "Contreras Díaz A."], por_nombre)
    casos.append(("candidato de unidad para firma sin homónimo",
                  set(cu[cu.nombre_en_fuente == "López-Soto P."].escuela_declarada_en_autoarchivo)
                  == {"Medicina"}, cu.to_dict("records")))
    casos.append(("dos escuelas distintas para la misma firma se declaran las DOS, no se elige",
                  set(cu[cu.nombre_en_fuente == "Contreras Díaz A."].escuela_declarada_en_autoarchivo)
                  == {"Enfermería", "Medicina"}, cu.to_dict("records")))
    casos.append(("no se inventa columna de vocabulario oficial",
                  "unidad_canonica" not in cu.columns and "facultad" not in cu.columns,
                  list(cu.columns)))

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

    c.banner("CONTRASTE CONTRA EL INVENTARIO DE AUTOARCHIVO (BIBLIOTECA UFT)")
    if args.test:
        return autotest()

    if not RAW_AUTOARCHIVO.exists():
        sys.exit(f"No se encontró {RAW_AUTOARCHIVO.relative_to(c.ROOT)}.\n"
                  "Este conector no sale a red: necesita el inventario en data/raw/.")

    df = leer_autoarchivo()
    print(f"  filas del inventario: {len(df)}")
    por_doi, por_nombre = indices(df)
    print(f"  publicaciones con DOI: {len(por_doi)} · claves de nombre: {len(por_nombre)}")

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
    c.write_interim(verif, "autoarchivo_verificacion.csv")
    resumen = verif.veredicto.value_counts().to_dict() if len(verif) else {}
    print(f"\n  firmas con ORCID cruzadas: {len(verif)}")
    for k, v in sorted(resumen.items()):
        print(f"    {k:22s}: {v}")
    print("  OK · data/interim/autoarchivo_verificacion.csv")

    cand = candidatos_por_nombre(sin_orcid, por_nombre)
    if len(cand):
        c.write_internal(cand, "autoarchivo_candidatos.csv")
        unicos = cand[cand.orcid_reclamado_por_n_firmas == 1].nombre_en_fuente.nunique()
        print(f"\n  candidatos por nombre (firmas sin ORCID): {cand.nombre_en_fuente.nunique()}"
              f" (1-a-1: {unicos})")
        print("  OK · internal/autoarchivo_candidatos.csv")
    else:
        print("\n  Sin candidatos nuevos de ORCID.")

    nd = log[log["unidad_academica"] == "No determinada"]
    firmas_nd = sorted(nd["nombre_en_fuente"].unique())
    cu = candidatos_de_unidad(firmas_nd, por_nombre)
    if len(cu):
        c.write_internal(cu, "autoarchivo_unidad_candidatos.csv")
        print(f"\n  candidatos de Facultad/Escuela para 'No determinada': "
              f"{cu.nombre_en_fuente.nunique()} de {len(firmas_nd)} firmas")
        print("  OK · internal/autoarchivo_unidad_candidatos.csv "
              "(en bruto, SIN traducir al vocabulario — revisión humana aparte)")
    else:
        print("\n  Sin candidatos de unidad.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
