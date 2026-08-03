"""Verifica las asignaciones de ORCID contra el registro público de ORCID.

QUÉ RESUELVE
    `orcid_crossref.py` deduce el ORCID de una firma cruzando apellido e inicial
    contra los autores que Crossref declara en cada DOI. Eso es una HIPÓTESIS:
    'Diaz F.' y 'Díaz Fernández, Francisca' se parecen, pero parecerse no es
    serlo. Las 174 asignaciones vigentes descansan sobre esa inferencia.

    ORCID publica lo que cada persona declara sobre sí misma. Preguntándole al
    registro se puede comprobar la hipótesis en vez de sostenerla:

      ¿el titular de este ORCID declara ESTE artículo entre sus obras?
      ¿declara a esta institución entre sus afiliaciones?

    Una asignación cuyo DOI aparece en el registro del titular deja de ser una
    conjetura. Una cuyo DOI no aparece en ninguna parte pasa a ser sospechosa.

QUÉ NO HACE
    No fusiona firmas ni resuelve identidades (decisión D-08). Produce evidencia
    verificable, que alimenta la herramienta de revisión humana. La conclusión
    «estas dos firmas son la misma persona» la sigue tomando una persona.

    Tampoco reescribe `authors_orcid.csv`: emite un archivo aparte. Machacar la
    asignación original borraría de dónde vino cada dato.

CREDENCIALES
    La API pública de ORCID exige un token. Se obtiene gratis registrando un
    cliente en https://orcid.org/developer-tools y pidiendo un token de tipo
    `client_credentials` con alcance `/read-public`.

    `CLAUDE.md` prohíbe suponer disponibilidad de credenciales: este script no
    asume ninguna. Sin ellas no corre, lo dice con claridad y no falla a medias.

Uso:
    python3 src/enrich/orcid_api.py --test          verifica la lógica sin red
    python3 src/enrich/orcid_api.py                 verifica las asignaciones
    python3 src/enrich/orcid_api.py --buscar-afiliacion   busca ORCID no detectados

Salidas:
    data/enriched/orcid_verificacion.csv     una fila por asignación comprobada
    internal/orcid_hallazgos.csv             lo que exige mirada humana
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audit"))
import common as c  # noqa: E402

CACHE = c.ROOT / "data" / "cache" / "orcid"
ENRICHED = c.ROOT / "data" / "enriched"

API = "https://pub.orcid.org/v3.0"
TOKEN_URL = "https://orcid.org/oauth/token"

# Contrato mínimo que este código espera del registro. Se declara aquí para que
# un cambio de la API se lea como lo que es —un cambio de contrato— y no como un
# error difuso más abajo.
CAMPOS = {
    "obras": ("activities-summary", "works", "group"),
    "empleos": ("activities-summary", "employments", "affiliation-group"),
}


# --------------------------------------------------------------------------- #
# Credenciales
# --------------------------------------------------------------------------- #

def obtener_token(client_id: str, client_secret: str) -> str:
    """Canjea las credenciales de cliente por un token de lectura pública."""
    datos = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "/read-public",
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=datos, headers={
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)["access_token"]


def credenciales() -> str:
    """Token de acceso, del entorno. Nunca de un archivo versionado.

    Se acepta un token ya emitido (ORCID_TOKEN) o el par de credenciales de
    cliente. Ausentes las dos vías, el script se detiene explicando cómo
    obtenerlas: fallar claro es mejor que correr a medias.
    """
    tok = os.environ.get("ORCID_TOKEN")
    if tok:
        return tok.strip()

    cid = os.environ.get("ORCID_CLIENT_ID")
    sec = os.environ.get("ORCID_CLIENT_SECRET")
    if cid and sec:
        print("  canjeando credenciales de cliente por un token…")
        return obtener_token(cid.strip(), sec.strip())

    sys.exit(
        "Faltan credenciales de la API pública de ORCID.\n\n"
        "Obtenerlas es gratuito:\n"
        "  1. Inicie sesión en https://orcid.org y entre en «Developer tools».\n"
        "  2. Registre un cliente de API pública. Le darán un Client ID y un\n"
        "     Client Secret.\n"
        "  3. Expórtelos antes de ejecutar:\n\n"
        "       export ORCID_CLIENT_ID='APP-XXXXXXXX'\n"
        "       export ORCID_CLIENT_SECRET='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxx'\n\n"
        "     (En PowerShell:  $env:ORCID_CLIENT_ID = 'APP-XXXXXXXX')\n\n"
        "Nunca escriba las credenciales en un archivo del repositorio: es\n"
        "público y quedarían expuestas."
    )


# --------------------------------------------------------------------------- #
# Consulta
# --------------------------------------------------------------------------- #

def _cache_path(orcid: str, seccion: str) -> Path:
    return CACHE / f"{re.sub(r'[^0-9X-]', '', orcid)}__{seccion}.json"


def consultar(orcid: str, seccion: str, token: str, pausa: float = 0.15) -> dict | None:
    """Una sección del registro público de un ORCID. None si no existe.

    Cachea en disco: reejecutar no vuelve a golpear la API, igual que el
    conector de Crossref.
    """
    path = _cache_path(orcid, seccion)
    if path.exists():
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)

    url = f"{API}/{urllib.parse.quote(orcid)}/{seccion}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "InformeCienciometricoInstitucional/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code in (404, 409):      # ORCID inexistente o desactivado
            return None
        raise
    CACHE.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False)
    time.sleep(pausa)
    return data


# --------------------------------------------------------------------------- #
# Lectura del registro
# --------------------------------------------------------------------------- #

def dois_declarados(works: dict | None) -> set[str]:
    """DOI que el titular declara entre sus obras, en minúsculas.

    ORCID agrupa las obras por identificador: un mismo artículo puede llegar
    varias veces si lo depositaron fuentes distintas. Se aplanan los grupos.
    """
    out: set[str] = set()
    if not works:
        return out
    for grupo in works.get("group") or []:
        for ident in (grupo.get("external-ids") or {}).get("external-id") or []:
            if (ident.get("external-id-type") or "").lower() == "doi":
                v = (ident.get("external-id-value") or "").strip().lower()
                if v:
                    out.add(v)
    return out


def afiliaciones_declaradas(empleos: dict | None) -> list[str]:
    """Organizaciones que el titular declara como empleadoras."""
    out: list[str] = []
    if not empleos:
        return out
    for grupo in empleos.get("affiliation-group") or []:
        for res in grupo.get("summaries") or []:
            emp = res.get("employment-summary") or {}
            nombre = ((emp.get("organization") or {}).get("name") or "").strip()
            if nombre:
                out.append(nombre)
    return out


def coincide_institucion(nombres: list[str]) -> bool:
    """¿Alguna afiliación declarada es la institución foco?

    Reutiliza el patrón blando de `config/matching_rules.yml`: la misma regla
    que decide la pertenencia institucional en el resto del pipeline, para que
    no haya dos definiciones distintas de «es de esta institución».
    """
    return any(c.matches_institution_soft(n) for n in nombres)


# --------------------------------------------------------------------------- #
# Verificación
# --------------------------------------------------------------------------- #

def verificar(firma: str, orcid: str, dois_atribuidos: set[str],
              works: dict | None, empleos: dict | None) -> dict:
    """Contrasta una asignación firma → ORCID contra lo que declara el titular.

    El veredicto NO decide identidad: califica la evidencia. Confirmar que un
    DOI está en el registro del titular confirma que ESA publicación es suya,
    que es exactamente lo que la asignación afirmaba.
    """
    declarados = dois_declarados(works)
    afil = afiliaciones_declaradas(empleos)
    comunes = dois_atribuidos & declarados

    if works is None:
        veredicto, detalle = "sin_registro", "el ORCID no existe o no es público"
    elif comunes:
        veredicto = "confirmada"
        detalle = (f"{len(comunes)} de {len(dois_atribuidos)} DOI atribuidos "
                   "aparecen en el registro del titular")
    elif not declarados:
        veredicto = "no_verificable"
        detalle = "el titular no declara ninguna obra con DOI en su registro"
    else:
        veredicto = "sin_coincidencia"
        detalle = (f"el titular declara {len(declarados)} obras con DOI y "
                   "ninguna coincide con las atribuidas a esta firma")

    return {
        "nombre_en_fuente": firma,
        "orcid": orcid,
        "veredicto": veredicto,
        "detalle": detalle,
        "dois_atribuidos": len(dois_atribuidos),
        "dois_en_registro": len(declarados),
        "dois_coincidentes": len(comunes),
        "afiliacion_institucional_declarada": coincide_institucion(afil),
        "afiliaciones_declaradas": " | ".join(dict.fromkeys(afil))[:300],
    }


# --------------------------------------------------------------------------- #
# Autoprueba sin red
# --------------------------------------------------------------------------- #

def autotest() -> int:
    """Verifica la lógica con registros de mentira. No toca la red.

    Existe por la misma razón que la de `orcid_crossref.py`: el entorno de
    integración no tiene acceso a la API, y una lógica de verificación que nadie
    ejerce es una lógica que se rompe en silencio.
    """
    def works(*dois):
        return {"group": [
            {"external-ids": {"external-id": [
                {"external-id-type": "doi", "external-id-value": d}]}}
            for d in dois]}

    def empleos(*orgs):
        return {"affiliation-group": [
            {"summaries": [{"employment-summary": {"organization": {"name": o}}}]}
            for o in orgs]}

    casos = []

    # 1. Extracción de DOI, incluida la normalización a minúsculas.
    got = dois_declarados(works("10.1/AAA", "10.2/bbb"))
    casos.append(("extrae y normaliza DOI", got == {"10.1/aaa", "10.2/bbb"}, got))

    # 2. Un registro vacío no revienta.
    casos.append(("registro vacío", dois_declarados(None) == set(), None))
    casos.append(("obras sin DOI", dois_declarados({"group": []}) == set(), None))

    # 3. Coincidencia → confirmada.
    r = verificar("Díaz F.", "0000-1", {"10.1/aaa"}, works("10.1/AAA"), None)
    casos.append(("coincidencia confirma", r["veredicto"] == "confirmada", r["veredicto"]))

    # 4. El titular declara obras, pero ninguna es la atribuida.
    r = verificar("Díaz F.", "0000-1", {"10.9/zzz"}, works("10.1/aaa"), None)
    casos.append(("sin coincidencia", r["veredicto"] == "sin_coincidencia", r["veredicto"]))

    # 5. Registro sin obras: no se puede verificar, y NO es lo mismo que refutar.
    r = verificar("Díaz F.", "0000-1", {"10.9/zzz"}, works(), None)
    casos.append(("registro sin obras", r["veredicto"] == "no_verificable", r["veredicto"]))

    # 6. ORCID inexistente.
    r = verificar("Díaz F.", "0000-1", {"10.9/zzz"}, None, None)
    casos.append(("ORCID inexistente", r["veredicto"] == "sin_registro", r["veredicto"]))

    # 7. Afiliación institucional reconocida por el patrón del proyecto.
    inst = c.INSTITUTION["institucion"]["nombre_canonico"]
    r = verificar("Díaz F.", "0000-1", {"10.1/a"}, works("10.1/a"), empleos(inst))
    casos.append(("afiliación institucional", r["afiliacion_institucional_declarada"] is True, None))

    # 8. Otra institución NO se cuenta como propia.
    r = verificar("Díaz F.", "0000-1", {"10.1/a"}, works("10.1/a"),
                  empleos("Universidad de Chile"))
    casos.append(("otra institución", r["afiliacion_institucional_declarada"] is False, None))

    ok = True
    for nombre, paso, obs in casos:
        print(f"  {'OK  ' if paso else 'FALLA'} {nombre}" + (f"   {obs}" if not paso else ""))
        ok &= paso
    print("\n" + ("TODOS LOS CASOS OK" if ok else "HAY CASOS FALLANDO"))
    return 0 if ok else 1


# --------------------------------------------------------------------------- #

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--test", action="store_true", help="verifica la lógica sin red")
    ap.add_argument("--limit", type=int, default=None, help="máximo de ORCID a consultar")
    args = ap.parse_args()

    c.banner("VERIFICACIÓN DE ORCID CONTRA EL REGISTRO PÚBLICO")
    if args.test:
        return autotest()

    asignaciones_path = ENRICHED / "authors_orcid.csv"
    if not asignaciones_path.exists():
        sys.exit(
            "Falta data/enriched/authors_orcid.csv.\n"
            "Este script VERIFICA asignaciones existentes; no las crea.\n"
            "Ejecute primero:  python3 src/enrich/orcid_crossref.py")

    universo = c.INTERIM / "publications_universe.csv"
    if not universo.exists():
        sys.exit("Falta data/interim/publications_universe.csv. "
                 "Ejecute:  python3 src/audit/run_all.py")

    token = credenciales()

    asign = pd.read_csv(asignaciones_path, dtype=str)
    log = pd.read_csv(c.INTERNAL / "matching_log.csv", dtype=str)
    uni = pd.read_csv(universo, dtype=str)
    doi_por_eid = {r["eid"]: str(r["doi"]).strip().lower()
                   for _, r in uni.iterrows() if pd.notna(r["doi"])}
    eids_por_firma = log.groupby("nombre_en_fuente")["eid"].apply(set).to_dict()

    filas = asign.head(args.limit) if args.limit else asign
    print(f"  asignaciones a verificar: {len(filas)} de {len(asign)}")

    resultados, errores = [], 0
    for i, (_, r) in enumerate(filas.iterrows(), 1):
        if i % 25 == 0:
            print(f"    {i}/{len(filas)}…")
        firma, orcid = r["nombre_en_fuente"], r["orcid"]
        dois = {doi_por_eid[e] for e in eids_por_firma.get(firma, set())
                if e in doi_por_eid}
        try:
            works = consultar(orcid, "works", token)
            empleos = consultar(orcid, "employments", token) if works else None
        except Exception as e:
            errores += 1
            if errores <= 3:
                print(f"    aviso · {orcid}: {type(e).__name__} {e}")
            if errores > 25:
                sys.exit("ABORTADO: demasiados errores. Verifique el token y la red.")
            continue
        resultados.append(verificar(firma, orcid, dois, works, empleos))

    if not resultados:
        print("\n  Sin resultados. No se escribe ningún archivo.")
        return 1

    df = pd.DataFrame(resultados)
    ENRICHED.mkdir(parents=True, exist_ok=True)
    df.to_csv(ENRICHED / "orcid_verificacion.csv", index=False, encoding="utf-8")

    # Lo que exige mirada humana va a la capa interna, no al artefacto público:
    # una asignación sospechosa es una duda sobre una persona real.
    dudosas = df[df.veredicto.isin(["sin_coincidencia", "sin_registro"])]
    if len(dudosas):
        cola = dudosas.assign(
            tipo="V2-01_asignacion_orcid_no_verificada", severidad="alta",
            consecuencia="la asignación firma→ORCID no se confirma en el registro",
            resolucion="PENDIENTE_REVISION_HUMANA")
        c.write_internal(cola, "orcid_hallazgos.csv")

    v = df.veredicto.value_counts()
    print(f"\n  errores de red               : {errores}")
    for k in ("confirmada", "no_verificable", "sin_coincidencia", "sin_registro"):
        if k in v:
            print(f"    {k:18s} : {v[k]:>4}")
    conf = int(v.get("confirmada", 0))
    print(f"\n  asignaciones confirmadas     : {conf} de {len(df)} "
          f"({100 * conf / len(df):.1f} %)")
    print(f"  con afiliación institucional : "
          f"{int(df.afiliacion_institucional_declarada.sum())}")
    print("\n  OK · data/enriched/orcid_verificacion.csv  (recuerde versionarlo)")
    if len(dudosas):
        print(f"       internal/orcid_hallazgos.csv · {len(dudosas)} para revisar")
    return 0


if __name__ == "__main__":
    sys.exit(main())
