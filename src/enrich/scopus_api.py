"""Consulta la API de Scopus para declarar la fecha de corte que el export manual no trae (T-06).

QUÉ RESUELVE
    `docs/UPDATING_REQUEST.md` pide tres cosas de la próxima carga de Scopus:
    la fecha a la que están actualizados los datos, la cadena de consulta
    exacta, y el recuento de resultados declarado. Un export manual desde la
    interfaz web las pierde con facilidad —nadie transcribe el «Data last
    updated» de la cabecera—; una consulta por API las captura solas, en el
    mismo instante en que se ejecuta.

QUÉ NO HACE
    - **No declara una fecha de corte que la API no tiene.** A diferencia de
      SciVal, la Scopus Search API no expone un campo "actualizado al". Lo que
      sí da, y es lo que este script captura, es el instante exacto de
      ejecución junto con la cadena de consulta literal — que es justo lo que
      `docs/UPDATING_REQUEST.md` §3 acepta cuando dice «si la exportación no
      la incluye, basta con anotarla aparte junto con la consulta usada».
    - **No reemplaza el corpus vigente.** El universo publicado (823,
      `D-16`) sigue viniendo del CSV en `data/raw/`. La API sólo pregunta a
      Scopus, así que el contraste es contra lo que `scopus_export` YA declara
      en `config/sources.yml` (`n_registros_leido`, hoy 818) — nunca contra el
      universo unido de 823, que mezcla registros exclusivos de SciVal que una
      consulta a Scopus no puede devolver por construcción. Si el recuento
      difiere, eso es un HALLAZGO que se imprime y se guarda — nunca una
      corrección automática del corpus. Promover un nuevo export a fuente
      primaria es una decisión aparte, posterior a este script.
    - **No escribe `config/sources.yml`.** Igual que `ror_institucion.py` con
      `config/institution.yml`: la salida se imprime lista para pegar a mano.
    - **No decide si la ventana 2023-2025 se extiende a 2026.** Usa la que hoy
      declara `config/institution.yml`. Extenderla es una decisión
      metodológica distinta, todavía abierta (ver `SESSION_NOTES.md`).

CREDENCIALES
    Nunca en este archivo ni en la línea de comandos. Se leen de variables de
    entorno:
        SCOPUS_API_KEY      obligatoria
        SCOPUS_INSTTOKEN    opcional — sólo si la suscripción lo exige

EL LÍMITE DE CONSULTA NO ESTÁ CONFIRMADO
    `CLAUDE.md` prohíbe suponer límites no confirmados. Este script no asume
    ninguno: lee las cabeceras `X-RateLimit-*` de la propia respuesta y las
    reporta, para que la primera corrida sea la que responda la pregunta en
    vez de un número copiado de la documentación general de Elsevier.

USO
    python3 src/enrich/scopus_api.py --test      lógica, sin red
    python3 src/enrich/scopus_api.py              la consulta real
    py src\\enrich\\scopus_api.py                  lo mismo, en Windows

Salidas
    data/enriched/scopus_api_consulta.json   resultado de la última consulta (SE VERSIONA)
    data/cache/scopus/<timestamp>.json       respuesta cruda, como evidencia (no versionada)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

if sys.platform == "win32":
    # La consola de Windows usa cp1252 por defecto: revienta cualquier print()
    # con caracteres como "→"/"—"/"·". Mismo patrón que src/enrich/orcid_openalex.py.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audit"))
import common as c  # noqa: E402

ENDPOINT = "https://api.elsevier.com/content/search/scopus"
CACHE = c.ROOT / "data" / "cache" / "scopus"
ENRICHED = c.ROOT / "data" / "enriched"


class ContratoDesconocido(Exception):
    """La respuesta no tiene la forma documentada de la Scopus Search API."""


# ────────────────────────────────────────────────────────── construir la consulta

def construir_consulta(institucion: dict, ventana: dict) -> str:
    """La misma cadena que `docs/UPDATING_REQUEST.md` §3 pide declarar.

    AF-ID acota por afiliación (regla de detección de mayor confianza, I-02);
    PUBYEAR con los bordes abiertos porque la sintaxis de Scopus no tiene
    "entre" inclusivo simétrico para ambos años a la vez.
    """
    afid = institucion["scopus_affiliation_id"]
    inicio, fin = ventana["anio_inicio"], ventana["anio_fin"]
    return f"AF-ID({afid}) AND PUBYEAR > {inicio - 1} AND PUBYEAR < {fin + 1}"


# ────────────────────────────────────────────────────────────── leer la respuesta

def extraer_resultado(payload: dict) -> dict:
    raiz = payload.get("search-results") if isinstance(payload, dict) else None
    if not isinstance(raiz, dict) or "opensearch:totalResults" not in raiz:
        raise ContratoDesconocido(
            "la respuesta no trae 'search-results.opensearch:totalResults'")
    crudo = raiz["opensearch:totalResults"]
    try:
        total = int(crudo)
    except (TypeError, ValueError):
        raise ContratoDesconocido(
            f"'opensearch:totalResults' no es un entero: {crudo!r}")
    return {"total_resultados": total}


def extraer_rate_limit(headers) -> dict:
    """Cabeceras `X-RateLimit-*`. Ninguna se asume presente: se reporta lo que haya."""
    get = headers.get
    return {
        "limite": get("X-RateLimit-Limit"),
        "restante": get("X-RateLimit-Remaining"),
        "restablece": get("X-RateLimit-Reset"),
    }


# ────────────────────────────────────────────────────────────────────────── red

def consultar(consulta: str, api_key: str, insttoken: str | None,
              count: int = 1, reintentos: int = 3) -> tuple[dict, dict]:
    """Ejecuta la consulta. Reintenta sólo en 429, respetando `Retry-After`.

    Manda un User-Agent descriptivo a propósito: el que pone Python por
    defecto ("Python-urllib/3.x") lo bloquean sin cuerpo algunos WAF delante
    de APIs de Elsevier, y eso se ve como un 400 sin explicación — no como el
    error de contrato que sí trae cuerpo.
    """
    params = urllib.parse.urlencode({"query": consulta, "count": count})
    url = f"{ENDPOINT}?{params}"
    headers = {"Accept": "application/json", "X-ELS-APIKey": api_key,
               "User-Agent": "InformeCienciometricoUFT/1.0 (+https://github.com/)"}
    if insttoken:
        headers["X-ELS-Insttoken"] = insttoken

    for intento in range(1, reintentos + 1):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.load(resp)
                return payload, dict(resp.headers)
        except urllib.error.HTTPError as e:
            if e.code == 429 and intento < reintentos:
                espera = int(e.headers.get("Retry-After", "5"))
                print(f"  429 Too Many Requests. Reintentando en {espera}s "
                      f"({intento}/{reintentos})...")
                time.sleep(espera)
                continue
            cuerpo = e.read().decode("utf-8", errors="replace").strip()
            diagnostico = (cuerpo[:500] if cuerpo else
                           "(sin cuerpo — típico de un WAF/proxy rechazando la petición "
                           "antes de llegar a la aplicación de Elsevier, no de un error "
                           "de la propia API)")
            content_type = e.headers.get("Content-Type", "(no declarado)")
            servidor = e.headers.get("Server", "(no declarado)")
            sys.exit(f"\n  Scopus respondió {e.code}:\n"
                      f"  Content-Type: {content_type}   Server: {servidor}\n"
                      f"  cuerpo: {diagnostico}\n\n"
                      "  Causas más probables de un 400, en orden:\n"
                      "    1. La API Key se pegó con un espacio o salto de línea de más\n"
                      "       (revise que el prompt oculto no haya capturado nada extra).\n"
                      "    2. Un proxy/antivirus corporativo está interceptando la\n"
                      "       conexión HTTPS y respondiendo él mismo, no Elsevier.\n"
                      "    3. La suscripción no tiene el Search API habilitado pese a\n"
                      "       'todas las APIs aprobadas' en el portal — confírmelo ahí.")
        except (urllib.error.URLError, TimeoutError) as e:
            sys.exit(f"\n  No se pudo consultar la API de Scopus: {e}\n\n"
                      "  Si esto corre desde un entorno con política de red\n"
                      "  restringida, ejecútelo en su máquina en vez de aquí.")

    sys.exit("  Agotados los reintentos ante 429 Too Many Requests.")


# ────────────────────────────────────────────────────────────────── autoprueba

PAYLOAD_OK = {"search-results": {"opensearch:totalResults": "823",
                                 "opensearch:startIndex": "0",
                                 "opensearch:itemsPerPage": "1"}}


def autotest() -> int:
    casos = []

    def caso(nombre, ok, obs=None):
        casos.append((nombre, ok, obs))

    consulta = construir_consulta(
        {"scopus_affiliation_id": "60105368"},
        {"anio_inicio": 2023, "anio_fin": 2025})
    caso("construye la consulta documentada en UPDATING_REQUEST.md",
         consulta == "AF-ID(60105368) AND PUBYEAR > 2022 AND PUBYEAR < 2026",
         consulta)

    r = extraer_resultado(PAYLOAD_OK)
    caso("extrae el total como entero", r == {"total_resultados": 823}, r)

    for mal, etiqueta in (
            ({"otra-cosa": {}}, "sin 'search-results'"),
            ({"search-results": {}}, "sin 'opensearch:totalResults'"),
            ({"search-results": {"opensearch:totalResults": "no-es-numero"}},
             "totalResults no numérico")):
        try:
            extraer_resultado(mal)
            caso(f"respuesta inválida ({etiqueta}) se detecta", False, "no lanzó")
        except ContratoDesconocido:
            caso(f"respuesta inválida ({etiqueta}) se detecta", True)

    rl = extraer_rate_limit({"X-RateLimit-Limit": "20000",
                             "X-RateLimit-Remaining": "19999"})
    caso("lee las cabeceras de límite presentes",
         rl == {"limite": "20000", "restante": "19999", "restablece": None}, rl)

    rl_vacio = extraer_rate_limit({})
    caso("no asume límite si la cabecera no llega",
         rl_vacio == {"limite": None, "restante": None, "restablece": None}, rl_vacio)

    ok = True
    for nombre, paso, obs in casos:
        print(f"  {'OK  ' if paso else 'FALLA'} {nombre}" + (f"   {obs}" if not paso else ""))
        ok &= paso
    print("\n" + ("TODOS LOS CASOS OK" if ok else "HAY CASOS FALLANDO"))
    return 0 if ok else 1


# ───────────────────────────────────────────────────────────────────── main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--test", action="store_true", help="verifica la lógica sin red")
    ap.add_argument("--count", type=int, default=1,
                    help="cuántos registros de muestra traer, aparte del conteo "
                         "total que la API siempre devuelve (por defecto 1; "
                         "este script no trae el corpus completo)")
    args = ap.parse_args()

    print("=" * 78)
    print("CONSULTA A LA API DE SCOPUS — fecha de corte para T-06")
    print("=" * 78)
    if args.test:
        return autotest()

    institucion = c.load_config("institution.yml")
    consulta = construir_consulta(institucion["institucion"], institucion["ventana_temporal"])
    print(f"  consulta: {consulta}")

    api_key = os.environ.get("SCOPUS_API_KEY")
    if not api_key:
        sys.exit("\n  Falta SCOPUS_API_KEY en el entorno. No se asume ninguna clave.\n"
                  "  Defínala y vuelva a ejecutar:\n"
                  "    Windows (PowerShell):  $env:SCOPUS_API_KEY = \"...\"\n"
                  "    bash:                  export SCOPUS_API_KEY=\"...\"")
    insttoken = os.environ.get("SCOPUS_INSTTOKEN") or None

    momento = datetime.now(timezone.utc)
    payload, headers = consultar(consulta, api_key, insttoken, count=args.count)

    try:
        resultado = extraer_resultado(payload)
    except ContratoDesconocido as e:
        CACHE.mkdir(parents=True, exist_ok=True)
        crudo = CACHE / f"contrato_desconocido_{momento.strftime('%Y%m%dT%H%M%SZ')}.json"
        crudo.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        sys.exit(f"\n  EL CONTRATO DE LA API NO ES EL ESPERADO: {e}\n"
                  f"  La respuesta cruda quedó en {crudo.relative_to(c.ROOT)}\n\n"
                  "  No se adivina la forma. Revise ese archivo antes de reintentar.")

    rate_limit = extraer_rate_limit(headers)

    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / f"{momento.strftime('%Y%m%dT%H%M%SZ')}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # La API sólo pregunta a Scopus, así que se compara contra lo que YA declara
    # scopus_export en sources.yml (n_registros_leido) — no contra el universo
    # unido (823, D-16), que además mezcla 5 registros exclusivos de SciVal que
    # una consulta a Scopus nunca podría devolver. Comparar contra 823 habría
    # sido una alarma falsa por construcción, no un hallazgo real.
    fuentes = c.load_config("sources.yml")["fuentes"]
    scopus_declarado = fuentes["scopus_export"]["n_registros_leido"]
    total = resultado["total_resultados"]

    salida = {
        "consulta": consulta,
        "fecha_hora_consulta_utc": momento.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_resultados": total,
        "n_registros_leido_scopus_export": scopus_declarado,
        "coincide_con_scopus_export_vigente": total == scopus_declarado,
        "rate_limit": rate_limit,
        "endpoint": ENDPOINT,
    }
    ENRICHED.mkdir(parents=True, exist_ok=True)
    (ENRICHED / "scopus_api_consulta.json").write_text(
        json.dumps(salida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"\n  total_resultados          : {total}")
    print(f"  scopus_export.n_registros_leido : {scopus_declarado}  (config/sources.yml)")
    if total != scopus_declarado:
        print("\n  HALLAZGO: el recuento de la API difiere del export de Scopus vigente.")
        print("  Eso NO actualiza el corpus solo. Una base bibliográfica crece hacia")
        print("  atrás (docs/UPDATING_REQUEST.md §2): puede ser indexación nueva desde")
        print("  el export de 2026-07-31, no un error. Revisar antes de decidir nada.")
    else:
        print("  Coincide con el export de Scopus vigente (data/raw/).")

    print(f"\n  límite de consulta reportado por la API:")
    print(f"    X-RateLimit-Limit    : {rate_limit['limite'] or '(no la envió)'}")
    print(f"    X-RateLimit-Remaining: {rate_limit['restante'] or '(no la envió)'}")

    print("\n  Para declarar T-06 en config/sources.yml, bajo scopus_export (a mano,")
    print("  NO lo escribe este script):")
    print(f'    fecha_corte: "{momento.date().isoformat()}"   '
          f'# consulta API ejecutada {salida["fecha_hora_consulta_utc"]}')
    print(f'    consulta: "{consulta}"')
    print(f'    n_resultados_declarado: {total}')
    print("\n  Esto declara el corte de una consulta NUEVA. No se aplica al export de")
    print("  data/raw/ ya cargado (docs/UPDATING_REQUEST.md §5): es para la próxima carga.")
    print(f"\n  OK · data/enriched/scopus_api_consulta.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
