"""Producción institucional que el universo no tiene (V2-26).

LA PREGUNTA QUE ESTE PROYECTO TODAVÍA NO PODÍA RESPONDER
    `docs/LIMITATIONS.md` declara que el corpus describe producción **indexada
    en Scopus**, y que la cobertura de esa base no es uniforme entre
    disciplinas: castiga a humanidades, ciencias sociales y a la publicación en
    español. Es una advertencia honesta, y hasta ahora era sólo cualitativa.

    Nadie podía decir de qué tamaño es la brecha, porque todo lo que el
    pipeline mira sale del propio universo, y el universo ya está filtrado por
    la institución. `orcid_openalex.py` (V2-19) tropezó con eso: su contraste
    sólo puede correr en una dirección —lo que nosotros atribuimos y OpenAlex
    no— porque únicamente consulta DOI que ya estaban dentro.

    Esta consulta va al revés. Le pregunta a OpenAlex **quién publica desde
    esta institución** en la ventana declarada, y compara esa lista contra el
    universo. Lo que aparece allí y no aquí es la brecha, medida.

QUÉ NO ES CADA HALLAZGO
    Una obra que OpenAlex atribuye a la institución y el universo no tiene
    **no es automáticamente producción perdida**. Puede ser:

      · producción real fuera de Scopus —el caso que interesa—;
      · una atribución equivocada de la desambiguación de OpenAlex;
      · un tipo documental que el universo excluye a propósito;
      · una obra fuera de la ventana por una fecha aproximada.

    Por eso el resultado es una **cola de revisión en la capa interna**, con la
    evidencia de cada caso, y no un número publicable ni un ajuste del corpus.

QUÉ NO HACE, Y NO ES NEGOCIABLE
    **No añade nada al universo.** Scopus y OpenAlex indexan con criterios
    distintos; sumarlos produce una cifra que nadie puede reconciliar
    (`D-206`). Si algún día esta producción entrara, entraría como corpus
    paralelo declarado, con su propia entrada en `config/sources.yml` y su
    propio denominador (`D-16`), por decisión de una persona.

DEPENDE DE V2-20
    Necesita el ROR de la institución para preguntar por ella. Sin él no corre
    y lo dice; buscar por nombre sería matching por cadena suelta, que la regla
    `I-05` prohíbe y que aquí traería la producción de cualquier homónimo.

EL CONTRATO DE LA API NO ESTÁ VERIFICADO DESDE ESTE REPOSITORIO
    La política de red del entorno de desarrollo bloquea `api.openalex.org`.
    Se comprueba la forma de la respuesta antes de usarla y, si no se reconoce,
    se guarda cruda y el programa se detiene diciendo dónde está.

USO
    python3 src/enrich/openalex_cobertura.py --test      lógica, sin red
    python3 src/enrich/openalex_cobertura.py --limit 2   dos páginas, prueba
    python3 src/enrich/openalex_cobertura.py             la consulta entera
    python3 src/enrich/openalex_cobertura.py --json f    sobre una respuesta guardada

Salida
    internal/openalex_cobertura.csv   la brecha, caso por caso (capa interna)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import pandas as pd

if sys.platform == "win32":
    # La consola de Windows usa cp1252 por defecto, que no tiene "→" ni "─":
    # revienta el print final después de que todo el trabajo ya se guardó.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audit"))
import common as c  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from orcid_openalex import ContratoDesconocido, ror_institucional  # noqa: E402

CACHE = c.ROOT / "data" / "cache" / "openalex_cobertura"
API = "https://api.openalex.org/works"
CFG = c.MATCHING["enriquecimiento_externo"]["orcid"]
VENTANA = c.load_config("institution.yml")["ventana_temporal"]


def normalizar_doi(doi: str | None) -> str:
    """Un DOI comparable: sin prefijo de URL y en minúsculas.

    Scopus lo exporta como `10.xxxx/yyy` y OpenAlex como
    `https://doi.org/10.xxxx/yyy`. Comparar sin normalizar daría el 100 % de
    brecha, que es un resultado espectacular y falso.
    """
    d = (doi or "").strip().lower()
    for p in ("https://doi.org/", "http://doi.org/", "doi:"):
        if d.startswith(p):
            d = d[len(p):]
    return d


def autores_de_la_institucion(w: dict, ror: str) -> tuple[str, str]:
    """Quién, entre los autores de la obra, es el que trae la institución que
    hizo matchear el filtro — y con qué nombre la declara OpenAlex.

    Sin esto, revisar a mano cuál de los N autores de una obra es el vínculo
    UFT exigiría abrir cada DOI uno por uno. El filtro de la consulta ya lo
    sabe (`institutions.ror:…`); sólo hacía falta no descartarlo al extraer.
    """
    nombres, declaradas = [], []
    for a in w.get("authorships") or []:
        for inst in a.get("institutions") or []:
            if (inst.get("ror") or "").rstrip("/").endswith(ror):
                autor = (a.get("author") or {}).get("display_name")
                if autor and autor not in nombres:
                    nombres.append(autor)
                declarada = inst.get("display_name")
                if declarada and declarada not in declaradas:
                    declaradas.append(declarada)
                break
    return "; ".join(nombres), "; ".join(declaradas)


def extraer_obras(payload: dict, ror: str = "") -> tuple[list[dict], str | None]:
    """Normaliza una página de resultados y devuelve el cursor siguiente."""
    if not isinstance(payload, dict) or "results" not in payload:
        raise ContratoDesconocido("la respuesta no trae 'results'")
    obras = []
    for w in payload.get("results") or []:
        if not isinstance(w, dict):
            continue
        autor_uft, institucion_declarada = autores_de_la_institucion(w, ror) if ror else ("", "")
        obras.append({
            "openalex_id": w.get("id"),
            "doi": normalizar_doi(w.get("doi")),
            "titulo": (w.get("title") or w.get("display_name") or "").strip(),
            "anio": w.get("publication_year"),
            "tipo": w.get("type"),
            "citas_openalex": w.get("cited_by_count"),
            "autor_uft": autor_uft,
            "institucion_declarada": institucion_declarada,
        })
    cursor = ((payload.get("meta") or {}).get("next_cursor"))
    return obras, cursor


def brecha(obras: list[dict], dois_universo: set[str],
           anio_min: int, anio_max: int) -> list[dict]:
    """Obras de OpenAlex que el universo no tiene, con su motivo probable.

    Se separa el caso «sin DOI» del caso «con DOI que no está»: sin DOI no se
    puede afirmar que falte —podría ser la misma obra que el universo tiene por
    otro identificador— y decir lo contrario sería inventar brecha.
    """
    fuera = []
    for o in obras:
        if o["doi"] and o["doi"] in dois_universo:
            continue
        anio = o.get("anio")
        if isinstance(anio, int) and not (anio_min <= anio <= anio_max):
            motivo = f"fuera de la ventana declarada ({anio_min}–{anio_max})"
        elif not o["doi"]:
            motivo = "OpenAlex no le asigna DOI: no se puede afirmar que falte"
        else:
            motivo = "con DOI, y ese DOI no está en el universo"
        fuera.append(dict(o, motivo=motivo))
    return fuera


def consultar(ror: str, cursor: str, mailto: str, pausa: float = 0.2) -> dict:
    """Una página de obras de la institución. Cachea por cursor."""
    filtro = (f"institutions.ror:{ror},"
              f"from_publication_date:{VENTANA['anio_inicio']}-01-01,"
              f"to_publication_date:{VENTANA['anio_fin']}-12-31")
    url = (f"{API}?filter={urllib.parse.quote(filtro, safe=':,')}"
           f"&per-page=200&cursor={urllib.parse.quote(cursor)}"
           f"&mailto={urllib.parse.quote(mailto)}")
    clave = f"{ror}_{cursor}".replace("*", "INICIO").replace("/", "_")[:120]
    path = CACHE / f"{clave}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "User-Agent": f"InformeCienciometrico/1.0 (mailto:{mailto})"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.load(resp)
    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    time.sleep(pausa)
    return data


# ────────────────────────────────────────────────────────────────── autotest

RORTEST = "0225snd59"

PAGINA = {
    "meta": {"count": 3, "next_cursor": "SIGUIENTE"},
    "results": [
        {"id": "https://openalex.org/W1", "doi": "https://doi.org/10.1/AAA",
         "title": "Ya en el universo", "publication_year": 2024,
         "type": "article", "cited_by_count": 5,
         "authorships": [{"author": {"display_name": "Autora Uno"},
                           "institutions": [{"display_name": "Universidad Finis Terrae",
                                              "ror": f"https://ror.org/{RORTEST}"}]}]},
        {"id": "https://openalex.org/W2", "doi": "https://doi.org/10.2/bbb",
         "title": "Falta, con DOI", "publication_year": 2024,
         "type": "article", "cited_by_count": 0,
         "authorships": [{"author": {"display_name": "Autor Dos"},
                           "institutions": [{"display_name": "Otra Universidad",
                                              "ror": "https://ror.org/otra"}]},
                          {"author": {"display_name": "Autora Tres"},
                           "institutions": [{"display_name": "Universidad Finis Terrae",
                                              "ror": f"https://ror.org/{RORTEST}"}]}]},
        {"id": "https://openalex.org/W3", "doi": None,
         "title": "Sin DOI", "publication_year": 2025, "type": "book-chapter"},
    ],
}


def autotest() -> int:
    casos = []

    def caso(n, ok, obs=None):
        casos.append((n, ok, obs))

    caso("el prefijo de URL del DOI no cuenta como diferencia",
         normalizar_doi("https://doi.org/10.1/AAA") == "10.1/aaa"
         and normalizar_doi("10.1/aaa") == "10.1/aaa", None)
    caso("un DOI ausente no revienta", normalizar_doi(None) == "", None)

    obras, cursor = extraer_obras(PAGINA, RORTEST)
    caso("extrae la página y su cursor", len(obras) == 3 and cursor == "SIGUIENTE", cursor)
    caso("identifica al autor con la institución que hizo matchear el filtro",
         obras[0]["autor_uft"] == "Autora Uno"
         and obras[0]["institucion_declarada"] == "Universidad Finis Terrae", obras[0])
    caso("entre varios autores, sólo trae al que declara la institución",
         obras[1]["autor_uft"] == "Autora Tres", obras[1])
    caso("sin autorías no revienta, queda vacío", obras[2]["autor_uft"] == "", obras[2])

    try:
        extraer_obras({"meta": {}})
        caso("respuesta sin 'results' se detecta", False, "no lanzó")
    except ContratoDesconocido:
        caso("respuesta sin 'results' se detecta", True)

    universo = {"10.1/aaa"}
    f = brecha(obras, universo, 2023, 2025)
    caso("lo que ya está en el universo no es brecha",
         [x["titulo"] for x in f] == ["Falta, con DOI", "Sin DOI"], f)
    caso("una obra sin DOI no se afirma como faltante",
         "no se puede afirmar" in [x for x in f if x["titulo"] == "Sin DOI"][0]["motivo"], f)
    caso("con DOI ausente sí se declara",
         [x for x in f if x["titulo"] == "Falta, con DOI"][0]["motivo"]
         == "con DOI, y ese DOI no está en el universo", f)

    fuera = brecha([{"openalex_id": "W", "doi": "10.9/z", "titulo": "Vieja",
                     "anio": 2019, "tipo": "article", "citas_openalex": 1}],
                   universo, 2023, 2025)
    caso("una obra fuera de la ventana se separa del resto",
         "fuera de la ventana" in fuera[0]["motivo"], fuera)

    # El caso que más importa: comparar sin normalizar daría 100 % de brecha.
    sin_normalizar = brecha(obras, {"https://doi.org/10.1/AAA"}, 2023, 2025)
    caso("sin normalizar el DOI la brecha saldría inflada",
         len(sin_normalizar) == 3 and len(f) == 2, (len(sin_normalizar), len(f)))

    ok = True
    for n, paso, obs in casos:
        print(f"  {'OK  ' if paso else 'FALLA'} {n}" + (f"   {obs}" if not paso else ""))
        ok &= paso
    print("\n" + ("TODOS LOS CASOS OK" if ok else "HAY CASOS FALLANDO"))
    return 0 if ok else 1


# ───────────────────────────────────────────────────────────────────── main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--test", action="store_true", help="verifica la lógica sin red")
    ap.add_argument("--limit", type=int, default=None, help="máximo de páginas")
    ap.add_argument("--json", metavar="ARCHIVO", help="una respuesta guardada a mano")
    args = ap.parse_args()

    c.banner("COBERTURA: PRODUCCIÓN INSTITUCIONAL QUE EL UNIVERSO NO TIENE")
    if args.test:
        return autotest()

    ror = ror_institucional()
    if not ror:
        sys.exit("Falta el ROR de la institución.\n\n"
                 "  Esta consulta pregunta por institución, y sin identificador la\n"
                 "  única alternativa sería buscar por nombre: matching por cadena\n"
                 "  suelta, que la regla I-05 prohíbe y que aquí traería la\n"
                 "  producción de cualquier homónimo.\n\n"
                 "  Ejecute antes:  python3 src/enrich/ror_institucion.py   (V2-20)\n"
                 "  y pegue el ror_id en config/institution.yml.")

    universo = c.INTERIM / "publications_universe.csv"
    if not universo.exists():
        sys.exit("Falta data/interim/publications_universe.csv. "
                 "Ejecute:  python3 src/audit/run_all.py")
    uni = pd.read_csv(universo, dtype=str)
    dois = {normalizar_doi(d) for d in uni["doi"].dropna()} - {""}
    print(f"  ROR institucional : {ror}")
    print(f"  ventana declarada : {VENTANA['anio_inicio']}–{VENTANA['anio_fin']}")
    print(f"  universo          : {len(uni)} publicaciones · {len(dois)} con DOI")

    obras: list[dict] = []
    if args.json:
        pagina, _ = extraer_obras(json.loads(Path(args.json).read_text(encoding="utf-8")), ror)
        obras = pagina
        total = len(obras)
    else:
        mailto = CFG.get("mailto")
        if not mailto:
            sys.exit("Falta enriquecimiento_externo.orcid.mailto en config/matching_rules.yml")
        cursor, n_pag, total = "*", 0, None
        while cursor:
            try:
                data = consultar(ror, cursor, mailto)
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
                sys.exit(f"\n  No se pudo consultar OpenAlex: {e}\n"
                         "  Si su red lo bloquea, guarde una respuesta a mano y use --json.")
            try:
                pagina, cursor = extraer_obras(data, ror)
            except ContratoDesconocido as e:
                CACHE.mkdir(parents=True, exist_ok=True)
                crudo = CACHE / "ultima_respuesta.json"
                crudo.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                                 encoding="utf-8")
                sys.exit(f"\n  EL CONTRATO DE LA API NO ES EL ESPERADO: {e}\n"
                         f"  Respuesta cruda en {crudo.relative_to(c.ROOT)}\n\n"
                         "  No se adivina la forma. Envíe ese archivo y se corrige.")
            if total is None:
                total = (data.get("meta") or {}).get("count")
                print(f"  OpenAlex atribuye : {total} obras a esta institución")
            obras += pagina
            n_pag += 1
            print(f"    página {n_pag}: {len(pagina)} obras  (acumulado {len(obras)})")
            if not pagina or (args.limit and n_pag >= args.limit):
                break

    fuera = brecha(obras, dois, VENTANA["anio_inicio"], VENTANA["anio_fin"])
    en_comun = len(obras) - len(fuera)

    print(f"\n  obras recuperadas : {len(obras)}")
    print(f"  ya en el universo : {en_comun}")
    print(f"  NO en el universo : {len(fuera)}")
    if fuera:
        por_motivo: dict[str, int] = {}
        for x in fuera:
            por_motivo[x["motivo"]] = por_motivo.get(x["motivo"], 0) + 1
        for m, n in sorted(por_motivo.items(), key=lambda t: -t[1]):
            print(f"    {n:>5}  {m}")

    if not fuera:
        print("\n  Sin brecha detectada. No se escribe ningún archivo.")
        return 0

    df = pd.DataFrame(fuera).assign(
        tipo_hallazgo="V2-26_obra_institucional_fuera_del_universo",
        severidad="media",
        consecuencia="OpenAlex la atribuye a la institución y el universo no la tiene; "
                     "puede ser producción fuera de Scopus, una atribución errónea, "
                     "o un tipo documental excluido a propósito",
        resolucion="PENDIENTE_REVISION_HUMANA",
        fecha_consulta=date.today().isoformat())
    c.write_internal(df, "openalex_cobertura.csv")

    print("\n  Es una COLA DE REVISIÓN, no un ajuste del corpus: nada de esto entra")
    print("  en el universo. Scopus y OpenAlex indexan con criterios distintos y")
    print("  sumarlos produce una cifra que nadie puede reconciliar (D-206).")
    print("\n  OK · internal/openalex_cobertura.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
