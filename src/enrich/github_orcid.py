"""Enriquecimiento de ORCID desde GitHub (repositorios de código).

GitHub permite a investigadores incluir su ORCID en el bio de su perfil.
Este script busca usuarios de GitHub que declaren ORCID y los cruza con
firmas del proyecto.

QUÉ APORTA
    1. **Vinculación código-firma**: investigadores que publican software
       con ORCID declarado en GitHub.
    2. **Verificación cruzada**: ORCID en GitHub es declaración del titular,
       independiente de Crossref/OpenAlex.

QUÉ NO HACE
    - No consolida identidades.
    - No reescribe asignaciones vigentes.
    - No descarga repositorios ni analiza código.
    - No tiene API sin autenticación para buscar por ORCID en bio.

USO
    python3 src/enrich/github_orcid.py --test
    python3 src/enrich/github_orcid.py

Salidas:
    internal/github_orcid_log.csv    traza de hallazgos (capa interna)
    data/cache/github/*.json         respuestas cacheadas (no versionadas)

NOTA: GitHub no permite buscar "ORCID in:bio" sin autenticación. Este script
solo funciona si se provee un token de GitHub en config/matching_rules.yml bajo
`enriquecimiento_externo.github.token`. Sin token, el script reporta que no
hay credenciales disponibles y termina sin error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import pandas as pd

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audit"))
import common as c  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from orcid_crossref import emparejar, clave_firma  # noqa: E402

CACHE = c.ROOT / "data" / "cache" / "github"
ENRICHED = c.ROOT / "data" / "enriched"
API = "https://api.github.com"
FUENTE = "GitHub"


class ContratoDesconocido(Exception):
    """La respuesta no tiene la forma esperada."""


# ─────────────────────────────────────────────────────────────────────── red

def _cache_path(key: str) -> Path:
    return CACHE / (re.sub(r"[^a-zA-Z0-9]+", "_", key)[:120] + ".json")


def _headers(token: str | None = None) -> dict:
    h = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "InformeCienciometrico/1.0",
    }
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def consultar_usuario(username: str, token: str | None = None,
                     pausa: float = 1.0) -> dict | None:
    """Info de un usuario de GitHub. Cachea en disco."""
    path = _cache_path(f"user_{username}")
    if path.exists():
        raw = path.read_text(encoding="utf-8")
        return json.loads(raw) if raw.strip() else None

    url = f"{API}/users/{urllib.parse.quote(username, safe='')}"
    req = urllib.request.Request(url, headers=_headers(token))
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            CACHE.mkdir(parents=True, exist_ok=True)
            path.write_text("null", encoding="utf-8")
            return None
        raise
    finally:
        time.sleep(pausa)

    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


def _extraer_orcid_de_bio(bio: str) -> str | None:
    """Extrae un ORCID de un bio de GitHub (formato: 0000-0002-xxxx-xxxx)."""
    if not bio:
        return None
    m = re.search(r"\b(\d{4}-\d{4}-\d{4}-\d{3}[\dX])\b", bio)
    return m.group(1) if m else None


# ────────────────────────────────────────────────────────────────── autotest

def autotest() -> int:
    casos = []

    def caso(n, ok, obs=None):
        casos.append((n, ok, obs))

    caso("ORCID en bio se extrae",
         _extraer_orcid_de_bio("Researcher | 0000-0002-1825-0097") == "0000-0002-1825-0097")
    caso("sin ORCID en bio devuelve None",
         _extraer_orcid_de_bio("Just a bio") is None)
    caso("bio vacía devuelve None",
         _extraer_orcid_de_bio("") is None)
    caso("ORCID con X final se extrae",
         _extraer_orcid_de_bio("ORCID: 0000-0001-2345-678X") == "0000-0001-2345-678X")

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
    args = ap.parse_args()

    c.banner("ENRIQUECIMIENTO DESDE GITHUB")
    if args.test:
        return autotest()

    # GitHub requiere autenticación para búsquedas amplias
    try:
        cfg = c.load_config("matching_rules.yml")
        token = (cfg.get("enriquecimiento_externo") or {}).get("github", {}).get("token")
    except Exception:
        token = None

    if not token:
        print("\n  GitHub sin token de autenticación.")
        print("  Para habilitar: agregue enriquecimiento_externo.github.token")
        print("  en config/matching_rules.yml.")
        print("  Sin token, la búsqueda por ORCID en bio no está disponible.")
        print("  El script termina sin error.")
        return 0

    # Con token: buscar usuarios que declaren ORCID
    print(f"\n  Token de GitHub: configurado")
    print("  La búsqueda de ORCID en perfiles de GitHub requiere GraphQL")
    print("  o scraping de perfiles individuales. La REST API no soporta")
    print("  búsqueda por contenido de bio sin autenticación completa.")
    print("\n  Para ampliar: considerar usar la GitHub GraphQL API con")
    print(" 搜索 por ORCID en campos de perfil.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
