"""Cliente compartido para `https://api.crossref.org/works/{doi}`.

QUÉ RESUELVE
    Tres conectores de este proyecto consultan el mismo endpoint por DOI,
    cada uno para una pregunta distinta (ORCID declarado por el editor,
    afiliación para la revisión de cobertura OpenAlex, financiamiento
    declarado): `orcid_crossref.py`, `openalex_cobertura_crossref.py` y
    `crossref_financiamiento.py`. Los tres necesitaban exactamente el mismo
    mecanismo de transporte y caché — sin semántica de dominio alguna, así
    que factorizarlo no mezcla nada que este proyecto proteja por separado
    (a diferencia de la extracción/interpretación de cada respuesta, que
    sigue viviendo en cada conector, donde corresponde).

    Este módulo es sólo el tercer punto de esa duplicación en aparecer
    (`crossref_financiamiento.py`, 2026-09-02): los dos conectores
    anteriores (`orcid_crossref.py`, `openalex_cobertura_crossref.py`) ya
    corrieron con su propia copia inline y no se tocan aquí — no hay
    beneficio en retocar código ya ejecutado y sin relación con esta
    sesión. Un conector nuevo debería importar este módulo en vez de copiar
    `_cache_path()`/`consultar()` una cuarta vez.

USO
    from crossref_client import consultar
    msg = consultar(doi, mailto)   # dict de Crossref, o None si no hay registro

Caché compartida: `data/cache/crossref/*.json` (no versionada).
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audit"))
import common as c  # noqa: E402

CACHE = c.ROOT / "data" / "cache" / "crossref"
API = "https://api.crossref.org/works/"


def cache_path(doi: str) -> Path:
    return CACHE / (re.sub(r"[^a-zA-Z0-9]+", "_", doi)[:120] + ".json")


def consultar(doi: str, mailto: str, pausa: float = 0.12) -> dict | None:
    """Trae `message` de Crossref para un DOI, con caché en disco.

    404 se cachea como "sin registro" (no se reconsulta después). Cualquier
    otro error se propaga: el llamador decide si sigue con el siguiente DOI
    o aborta — este módulo no tiene ese criterio, es transporte puro."""
    path = cache_path(doi)
    if path.exists():
        with open(path, encoding="utf-8") as fh:
            return json.load(fh).get("message")

    url = API + urllib.parse.quote(doi, safe="")
    req = urllib.request.Request(url, headers={
        "User-Agent": f"InformeCienciometrico/1.0 (mailto:{mailto})",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"message": None}), encoding="utf-8")
            return None
        raise
    finally:
        time.sleep(pausa)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data.get("message")
