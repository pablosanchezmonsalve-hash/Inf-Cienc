"""Ficha de la institución en ROR (V2-20). Cierra dos placeholders y contrasta variantes.

QUÉ RESUELVE
    `config/institution.yml` declara dos identificadores en `null`, con el
    motivo escrito al lado: «placeholder: no verificado en Fase 1».

        ror_id: null
        isni: null

    ROR es el registro público de organizaciones de investigación. Su ficha
    trae el identificador ROR, el ISNI cuando existe, y —lo que más importa
    aquí— **los nombres bajo los que la institución está registrada**: forma
    oficial, alias, acrónimos y etiquetas en otros idiomas.

    Ese último punto es lo que convierte esto en algo más que rellenar dos
    campos. `<author_master_rule>` de `CLAUDE.md` exige detectar las variantes
    institucionales del nombre. Hoy la detección blanda es UN patrón escrito a
    mano en `config/matching_rules.yml`. Contrastarlo contra un vocabulario
    público dice si ese patrón se deja fuera alguna forma con la que la
    institución se firma de verdad.

QUÉ NO HACE
    - **No escribe `config/institution.yml`.** Ese archivo es el contrato de
      replicabilidad: lo que otra institución edita para reutilizar la
      plataforma. Y un identificador de organización es una afirmación sobre
      esa organización. Se imprime la línea exacta y la pega una persona.
    - **No elige entre candidatos.** Si más de una organización responde al
      patrón institucional, el caso se encola en la capa interna. Elegir por
      parecido de cadena es justo lo que la regla `I-05` prohíbe.
    - **No cambia el patrón de detección.** Reporta las formas que se le
      escapan; ampliarlo es una decisión, porque cada patrón nuevo puede traer
      falsos positivos y este proyecto ya tiene 16 verificados.

EL CONTRATO DE LA API NO ESTÁ VERIFICADO DESDE ESTE REPOSITORIO
    `CLAUDE.md` prohíbe suponer disponibilidad de endpoints no confirmados. El
    entorno donde se escribió este archivo **no alcanza `api.ror.org`**: la
    política de red del contenedor deniega la conexión. De modo que:

    - se admiten las DOS formas de respuesta conocidas de ROR —la de `v2`, con
      `names[]` y `locations[]`, y la de `v1`, con `name`, `aliases`,
      `acronyms` y `country`—, y se detecta cuál llegó en vez de suponerla;
    - si no encaja ninguna, **no se adivina**: se guarda la respuesta cruda y
      el programa se detiene diciendo dónde está, para que el contrato se
      corrija con lo que la API haya devuelto de verdad;
    - `--json` permite trabajar sobre una respuesta guardada a mano, sin red.

    La lógica de extracción y de contraste sí está verificada, con `--test`.

USO
    python3 src/enrich/ror_institucion.py --test        lógica, sin red
    python3 src/enrich/ror_institucion.py               consulta ROR
    python3 src/enrich/ror_institucion.py --json r.json sobre una respuesta guardada

Salidas
    data/enriched/ror_institucion.json   la ficha recuperada (SE VERSIONA)
    internal/ror_candidatos.csv          sólo si hay ambigüedad (capa interna)
    data/cache/ror/*.json                respuestas cacheadas (no versionadas)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audit"))
import common as c  # noqa: E402

CACHE = c.ROOT / "data" / "cache" / "ror"
ENRICHED = c.ROOT / "data" / "enriched"
INTERNAL = c.ROOT / "internal"

# v2 es la vigente; v1 sigue publicada. Se prueban en ese orden porque no se ha
# podido confirmar cuál responde hoy desde este repositorio.
APIS = ("https://api.ror.org/v2/organizations",
        "https://api.ror.org/organizations")

INSTITUCION = c.load_config("institution.yml")["institucion"]


class ContratoDesconocido(Exception):
    """La respuesta no tiene ninguna de las formas conocidas.

    Se distingue de un error de red a propósito: uno se reintenta y el otro se
    corrige. Confundirlos hace que alguien reintente veinte veces algo que no
    va a cambiar solo.
    """


# ───────────────────────────────────────────────── extracción de la respuesta

def extraer(item: dict) -> dict:
    """Normaliza una organización de ROR a la forma que usa este proyecto.

    Devuelve siempre las mismas claves, vengan de `v2` o de `v1`. `nombres` es
    la lista con la que se hace el contraste, y va sin duplicar y en orden
    estable para que dos corridas produzcan el mismo archivo.
    """
    if not isinstance(item, dict) or not item.get("id"):
        raise ContratoDesconocido("la organización no trae 'id'")

    nombres: list[str] = []
    display = None
    pais = None
    isni = None

    if "names" in item:                                   # forma v2
        for n in item.get("names") or []:
            v = (n or {}).get("value")
            if not v:
                continue
            nombres.append(v)
            if "ror_display" in (n.get("types") or []):
                display = v
        for loc in item.get("locations") or []:
            det = (loc or {}).get("geonames_details") or {}
            pais = pais or det.get("country_name")
        for ext in item.get("external_ids") or []:
            if (ext or {}).get("type", "").lower() == "isni":
                isni = (ext.get("preferred")
                        or next(iter(ext.get("all") or []), None)) or isni

    elif "name" in item:                                  # forma v1
        display = item["name"]
        nombres.append(item["name"])
        nombres += [x for x in (item.get("aliases") or []) if x]
        nombres += [x for x in (item.get("acronyms") or []) if x]
        nombres += [l.get("label") for l in (item.get("labels") or [])
                    if isinstance(l, dict) and l.get("label")]
        pais = ((item.get("country") or {}).get("country_name"))
        ext = (item.get("external_ids") or {}).get("ISNI") or {}
        if isinstance(ext, dict):
            isni = ext.get("preferred") or next(iter(ext.get("all") or []), None)

    else:
        raise ContratoDesconocido(
            "la organización no trae ni 'names' (v2) ni 'name' (v1)")

    # Sin duplicar, conservando el orden de llegada: el orden de un `set` cambia
    # entre corridas y el archivo versionado produciría un diff cada vez.
    vistos, unicos = set(), []
    for n in nombres:
        if n not in vistos:
            vistos.add(n)
            unicos.append(n)

    return {
        "ror_id": item["id"],
        "nombre_en_ror": display or (unicos[0] if unicos else None),
        "nombres": unicos,
        "pais": pais,
        "isni": isni,
        "estado": item.get("status"),
    }


def items_de(payload: dict) -> list[dict]:
    if not isinstance(payload, dict) or "items" not in payload:
        raise ContratoDesconocido("la respuesta no trae 'items'")
    return payload["items"] or []


# ─────────────────────────────────────────────────────────────── el contraste

def candidatos(fichas: list[dict]) -> list[dict]:
    """Los que responden al patrón institucional del propio proyecto.

    El criterio NO se inventa aquí: es `matches_institution_soft`, la misma
    función que decide si una cadena de afiliación es de la institución. Usar
    otra —parecido de cadena, distancia de edición— significaría que ROR y el
    corpus se filtran con reglas distintas, y entonces el contraste posterior
    no compararía lo que dice comparar.
    """
    return [f for f in fichas if any(c.matches_institution_soft(n)
                                     for n in f["nombres"])]


def contraste(ficha: dict) -> dict:
    """Qué nombres de ROR captura el patrón de detección, y cuáles no.

    Los que no captura son el hallazgo: formas registradas de la institución
    que una cadena de afiliación podría traer y que hoy no se detectarían por
    la vía blanda. No se corrige nada; se declara.
    """
    capturados = [n for n in ficha["nombres"] if c.matches_institution_soft(n)]
    return {
        "capturados": capturados,
        "no_capturados": [n for n in ficha["nombres"] if n not in capturados],
    }


# ────────────────────────────────────────────────────────────────────── red

def consultar(consulta: str, pausa_cache: bool = True) -> tuple[dict, str]:
    """Pregunta a ROR. Devuelve la respuesta y el endpoint que contestó.

    Cachea en disco: reejecutar no vuelve a golpear la API, igual que los
    conectores de Crossref y de ORCID.
    """
    clave = hashlib.sha1(consulta.encode("utf-8")).hexdigest()[:16]
    cacheado = CACHE / f"{clave}.json"
    if pausa_cache and cacheado.exists():
        guardado = json.loads(cacheado.read_text(encoding="utf-8"))
        return guardado["respuesta"], guardado["endpoint"]

    ultimo = None
    for base in APIS:
        url = f"{base}?query={urllib.parse.quote(consulta)}"
        req = urllib.request.Request(url, headers={
            "Accept": "application/json",
            "User-Agent": "InformeCienciometrico/1.0 (+https://github.com/)"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.load(resp)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            ultimo = f"{base}: {e}"
            continue
        CACHE.mkdir(parents=True, exist_ok=True)
        cacheado.write_text(json.dumps({"endpoint": base, "respuesta": payload},
                                       ensure_ascii=False), encoding="utf-8")
        return payload, base

    sys.exit(f"No se pudo consultar ROR.\n  Último error: {ultimo}\n\n"
             "Si su red bloquea api.ror.org, guarde a mano la respuesta de\n"
             f"  {APIS[0]}?query={urllib.parse.quote(consulta)}\n"
             "y ejecute:  python3 src/enrich/ror_institucion.py --json <archivo>")


# ────────────────────────────────────────────────────────────────── autoprueba

V2 = {"items": [{
    "id": "https://ror.org/EJEMPLO2",
    "status": "active",
    "names": [{"value": "Universidad Finis Terrae", "types": ["ror_display", "label"]},
              {"value": "Finis Terrae University", "types": ["label"]},
              {"value": "UFT", "types": ["acronym"]}],
    "locations": [{"geonames_details": {"country_name": "Chile"}}],
    "external_ids": [{"type": "isni", "all": ["0000 0000 0000 0000"], "preferred": None}],
}]}

V1 = {"items": [{
    "id": "https://ror.org/EJEMPLO1",
    "name": "Universidad Finis Terrae",
    "aliases": ["Universidad Finis-Terrae"],
    "acronyms": ["UFT"],
    "labels": [{"label": "Finis Terrae University", "iso639": "en"}],
    "country": {"country_name": "Chile", "country_code": "CL"},
    "status": "active",
    "external_ids": {"ISNI": {"all": ["0000 0000 0000 0000"], "preferred": None}},
}]}


def autotest() -> int:
    casos = []

    def caso(nombre, ok, obs=None):
        casos.append((nombre, ok, obs))

    v2 = extraer(V2["items"][0])
    caso("extrae la forma v2", v2["ror_id"] == "https://ror.org/EJEMPLO2"
         and v2["nombre_en_ror"] == "Universidad Finis Terrae"
         and v2["pais"] == "Chile" and v2["isni"] == "0000 0000 0000 0000"
         and "UFT" in v2["nombres"], v2)

    v1 = extraer(V1["items"][0])
    caso("extrae la forma v1", v1["ror_id"] == "https://ror.org/EJEMPLO1"
         and v1["pais"] == "Chile" and v1["isni"] == "0000 0000 0000 0000"
         and "Universidad Finis-Terrae" in v1["nombres"]
         and "Finis Terrae University" in v1["nombres"], v1)

    caso("las dos formas dan las mismas claves", set(v1) == set(v2), (set(v1) ^ set(v2)))

    # Lo que NO se hace: adivinar. Una forma desconocida se declara.
    for mal, etiqueta in ((({"id": "https://ror.org/X"}), "sin names ni name"),
                          ({"names": [{"value": "X"}]}, "sin id")):
        try:
            extraer(mal)
            caso(f"forma desconocida ({etiqueta}) se detecta", False, "no lanzó")
        except ContratoDesconocido:
            caso(f"forma desconocida ({etiqueta}) se detecta", True)

    try:
        items_de({"resultados": []})
        caso("respuesta sin 'items' se detecta", False, "no lanzó")
    except ContratoDesconocido:
        caso("respuesta sin 'items' se detecta", True)

    # El orden de los nombres es estable: el archivo se versiona y un `set`
    # produciría un diff distinto en cada corrida.
    caso("el orden de los nombres es determinista",
         extraer(V1["items"][0])["nombres"] == extraer(V1["items"][0])["nombres"])

    # Candidatos: se filtra con el patrón del proyecto, no con parecido.
    otra = {"id": "https://ror.org/OTRA", "name": "Universidad de Chile",
            "aliases": [], "acronyms": ["UCH"], "labels": [],
            "country": {"country_name": "Chile"}, "status": "active"}
    fichas = [extraer(V1["items"][0]), extraer(otra)]
    cand = candidatos(fichas)
    caso("una organización ajena no es candidata",
         [f["ror_id"] for f in cand] == ["https://ror.org/EJEMPLO1"], cand)

    gemela = dict(otra, id="https://ror.org/GEMELA", name="Instituto Finis Terrae")
    caso("dos candidatos NO se desempatan aquí",
         len(candidatos(fichas + [extraer(gemela)])) == 2)

    # Contraste: el acrónimo es justo lo que el patrón no captura, y es el
    # hallazgo que justifica todo esto.
    ct = contraste(extraer(V1["items"][0]))
    caso("el acrónimo se reporta como no capturado", "UFT" in ct["no_capturados"], ct)
    caso("la forma con guion sí se captura",
         "Universidad Finis-Terrae" in ct["capturados"], ct)
    caso("la etiqueta en inglés se captura",
         "Finis Terrae University" in ct["capturados"], ct)

    ok = True
    for nombre, paso, obs in casos:
        print(f"  {'OK  ' if paso else 'FALLA'} {nombre}" + (f"   {obs}" if not paso else ""))
        ok &= paso
    print("\n" + ("TODOS LOS CASOS OK" if ok else "HAY CASOS FALLANDO"))
    return 0 if ok else 1


# ───────────────────────────────────────────────────────────────────── main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--test", action="store_true", help="verifica la lógica sin red")
    ap.add_argument("--json", metavar="ARCHIVO",
                    help="usa una respuesta de ROR guardada a mano")
    ap.add_argument("--sin-cache", action="store_true", help="ignora la caché")
    args = ap.parse_args()

    print("=" * 78)
    print("FICHA DE LA INSTITUCIÓN EN ROR")
    print("=" * 78)
    if args.test:
        return autotest()

    consulta = INSTITUCION["nombre_canonico"]
    print(f"  consulta: «{consulta}»")

    if args.json:
        payload = json.loads(Path(args.json).read_text(encoding="utf-8"))
        origen = args.json
    else:
        payload, origen = consultar(consulta, pausa_cache=not args.sin_cache)
    print(f"  origen  : {origen}")

    crudo = CACHE / "ultima_respuesta.json"
    try:
        fichas = [extraer(i) for i in items_de(payload)]
    except ContratoDesconocido as e:
        CACHE.mkdir(parents=True, exist_ok=True)
        crudo.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                         encoding="utf-8")
        sys.exit(f"\n  EL CONTRATO DE LA API NO ES EL ESPERADO: {e}\n"
                 f"  La respuesta cruda quedó en {crudo.relative_to(c.ROOT)}\n\n"
                 "  No se adivina la forma. Envíe ese archivo y la extracción se\n"
                 "  corrige con lo que la API devolvió de verdad.")

    print(f"  organizaciones devueltas: {len(fichas)}")
    cand = candidatos(fichas)

    if not cand:
        print("\n  NINGUNA responde al patrón institucional de "
              "config/matching_rules.yml.")
        print("  No se propone nada: puede que la institución no esté en ROR, o")
        print("  que esté con un nombre que este proyecto no reconoce. Las dos")
        print("  cosas son hallazgos, y ninguna se resuelve eligiendo la primera.")
        return 1

    if len(cand) > 1:
        INTERNAL.mkdir(exist_ok=True)
        pd.DataFrame([{
            "ror_id": f["ror_id"], "nombre_en_ror": f["nombre_en_ror"],
            "pais": f["pais"], "nombres": " | ".join(f["nombres"]),
            "tipo": "V2-20_varias_organizaciones_coinciden",
            "severidad": "media",
            "consecuencia": "el patrón institucional coincide con más de una organización",
            "resolucion": "PENDIENTE_REVISION_HUMANA",
            "fecha_consulta": date.today().isoformat(),
        } for f in cand]).to_csv(INTERNAL / "ror_candidatos.csv", index=False,
                                 encoding="utf-8")
        print(f"\n  {len(cand)} organizaciones coinciden. NO se elige ninguna.")
        print("  Encoladas en internal/ror_candidatos.csv para revisión humana.")
        return 1

    f = cand[0]
    ct = contraste(f)
    salida = dict(f, contraste=ct, consulta=consulta,
                  fecha_consulta=date.today().isoformat(), endpoint=origen)
    ENRICHED.mkdir(parents=True, exist_ok=True)
    (ENRICHED / "ror_institucion.json").write_text(
        json.dumps(salida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"\n  ROR   : {f['ror_id']}")
    print(f"  nombre: {f['nombre_en_ror']}")
    print(f"  país  : {f['pais']}   estado: {f['estado']}")
    print(f"  ISNI  : {f['isni'] or '(no declarado en ROR)'}")

    print(f"\n  nombres registrados: {len(f['nombres'])}")
    for n in ct["capturados"]:
        print(f"    [detectado]    {n}")
    for n in ct["no_capturados"]:
        print(f"    [NO detectado] {n}")

    if ct["no_capturados"]:
        print("\n  HALLAZGO. Esas formas están registradas para la institución y el")
        print("  patrón blando de config/matching_rules.yml NO las reconoce. Si una")
        print("  cadena de afiliación llegara sólo con una de ellas, no se")
        print("  detectaría. Ampliar el patrón es una decisión, no una consecuencia:")
        print("  la regla I-05 prohíbe el matching por subcadena y este proyecto ya")
        print("  tiene 16 falsos positivos verificados.")

    ror_corto = f["ror_id"].rsplit("/", 1)[-1]
    print("\n  Para cerrar los placeholders, en config/institution.yml:")
    print(f'    ror_id: "{ror_corto}"        # verificado en ROR, {salida["fecha_consulta"]}')
    if f["isni"]:
        print(f'    isni: "{f["isni"]}"   # declarado en la ficha de ROR')
    print("\n  NO se escribe solo: ese archivo es el contrato de replicabilidad y")
    print("  un identificador de organización es una afirmación sobre ella.")
    print(f"\n  OK · data/enriched/ror_institucion.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
