"""Genera el punto de entrada compacto del proyecto: STATE.md y docs/DECISIONS.md.

EL PROBLEMA QUE RESUELVE
    Retomar el proyecto exigía leer PLAN.md, SESSION_NOTES.md y buena parte de
    docs/: unas 3.700 líneas. La mayoría es referencia que sólo se necesita bajo
    demanda, pero no había forma de saber qué leer sin leerlo.

LA SOLUCIÓN
    Un archivo de estado de una página, DERIVADO del repositorio y no escrito a
    mano. Al derivarse, no puede quedar desactualizado: si las cifras cambian,
    se regenera y cambia con ellas. Un resumen mantenido a mano habría sido otro
    documento más que envejece y en el que no se puede confiar.

    Incluye un mapa de lectura: qué archivo abrir para cada pregunta concreta.
    Así el resto de la documentación pasa a ser consulta puntual.

Uso:
    python3 src/state/snapshot.py

Salidas:
    STATE.md            punto de entrada, ~100 líneas
    docs/DECISIONS.md   índice de decisiones, una línea cada una
"""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]

# Qué archivo responde cada pregunta. Es el corazón del ahorro de contexto:
# convierte "leer todo por si acaso" en "abrir uno cuando hace falta".
MAPA_LECTURA = [
    ("Qué decisión se tomó y por qué", "docs/DECISIONS.md"),
    ("Qué límites tienen los datos", "docs/LIMITATIONS.md"),
    ("Cómo se calcula un indicador", "docs/INDICATORS.md"),
    ("Por qué un cálculo es válido", "docs/METHODOLOGY.md"),
    ("Qué entidades y claves hay", "docs/DATA_MODEL.md"),
    ("Qué es público y qué interno", "docs/LAYERS.md"),
    ("Cómo se ve la interfaz", "docs/UX_UI.md"),
    ("Cómo construir y publicar", "docs/DEPLOYMENT.md"),
    ("Cómo cargar datos nuevos", "docs/UPDATING.md"),
    ("Cómo adaptarlo a otra institución", "docs/REPLICATION.md"),
    ("Cómo recuperar ORCID", "docs/ORCID_GUIDE.md"),
    ("Qué falta para la V2", "docs/V2_BACKLOG.md"),
    ("Historia de cada sesión", "SESSION_NOTES.md"),
]


def leer(path: str) -> str:
    p = ROOT / path
    return p.read_text(encoding="utf-8") if p.exists() else ""


def git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                              text=True, timeout=10).stdout.strip()
    except Exception:
        return ""


def extraer_decisiones() -> list[dict]:
    """Recupera las decisiones de las tablas de SESSION_NOTES.md.

    Se extraen en vez de mantenerse aparte: duplicarlas a mano crearía dos
    listas que divergen, y la pregunta '¿cuál es la buena?' no tendría respuesta.
    """
    texto = leer("SESSION_NOTES.md")
    sesion_actual = "?"
    filas = []
    for linea in texto.splitlines():
        m_sesion = re.match(r"^## Sesión (\S+) — (.+)$", linea.strip())
        if m_sesion:
            sesion_actual = m_sesion.group(2)
            continue
        m = re.match(r"^\|\s*(D-\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|$", linea.strip())
        if m:
            filas.append({"id": m.group(1), "decision": m.group(2),
                          "fundamento": m.group(3), "fase": sesion_actual})
    return filas


def pendientes_abiertos() -> list[tuple[str, str]]:
    """Pendientes de PLAN.md que no están tachados con ~~."""
    abiertos = []
    for linea in leer("PLAN.md").splitlines():
        m = re.match(r"^\|\s*(T-\d+)\s*\|\s*([^|]+?)\s*\|", linea.strip())
        if m and "~~" not in m.group(1):
            abiertos.append((m.group(1), m.group(2)))
    return abiertos


def cifras() -> dict:
    """Las cifras canónicas, leídas de donde realmente viven."""
    out = {}
    inst = yaml.safe_load(leer("config/institution.yml") or "{}")
    ind = yaml.safe_load(leer("config/indicators.yml") or "{}")
    if inst:
        v = inst["ventana_temporal"]
        out["ventana"] = f"{v['anio_inicio']}–{v['anio_fin']}"
        out["scopus_affiliation_id"] = inst["institucion"]["scopus_affiliation_id"]
    if ind:
        out.update({f"denominador_{k}": v for k, v in ind["denominadores"].items()})
        pub = [k for k, v in ind["indicadores"].items() if v.get("publicar")]
        out["indicadores_publicados"] = len(pub)
        out["indicadores_evaluados"] = len(ind["indicadores"])

    val = ROOT / "data/interim/validation_report.csv"
    if val.exists():
        df = pd.read_csv(val)
        fallas = df[df.resultado == "FALLA"]
        out["reglas"] = len(df)
        out["reglas_fallando"] = len(fallas)
        out["reglas_bloqueantes_fallando"] = len(fallas[fallas.severidad == "bloqueante"])

    orc = ROOT / "data/enriched/authors_orcid.csv"
    if orc.exists():
        o = pd.read_csv(orc)
        out["firmas_con_orcid"] = len(o)

    log = ROOT / "internal/matching_log.csv"
    if log.exists():
        m = pd.read_csv(log, dtype=str)
        out["pares_autor_publicacion"] = len(m)
        out["formas_de_firma"] = m["nombre_en_fuente"].nunique()
    return out


def colas_internas() -> list[tuple[str, int]]:
    """Cuántas entradas espera cada cola de revisión humana."""
    out = []
    for nombre in ("ambiguities_authors", "ambiguities_publications",
                   "orcid_conflicts", "identity_candidates"):
        p = ROOT / "internal" / f"{nombre}.csv"
        if p.exists():
            out.append((nombre, len(pd.read_csv(p))))
    return out


def main() -> None:
    print("=" * 78)
    print("SNAPSHOT DE ESTADO")
    print("=" * 78)

    dec = extraer_decisiones()
    pend = pendientes_abiertos()
    c = cifras()
    colas = colas_internas()

    # ------------------------------------------------------ DECISIONS.md
    lineas = [
        "# Índice de decisiones", "",
        "**Generado** por `src/state/snapshot.py` desde las tablas de "
        "`SESSION_NOTES.md`. No editar a mano.", "",
        "Una decisión registrada aquí **no se reabre sin una razón nueva** "
        "(`CLAUDE.md`, `<memory_and_continuity>`).", "",
        "| # | Decisión | Fundamento | Fase |", "|---|---|---|---|",
    ]
    lineas += [f"| `{d['id']}` | {d['decision']} | {d['fundamento']} | {d['fase']} |"
               for d in dec]
    (ROOT / "docs/DECISIONS.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")

    # ----------------------------------------------------------- STATE.md
    # Sólo la tabla de "Estado general": PLAN.md tiene otras tablas cuya primera
    # columna también es un número, y capturarlas mezclaría fases con requisitos.
    plan = leer("PLAN.md")
    bloque = re.search(r"## Estado general\n(.*?)(?=\n## )", plan, re.S)
    fases = re.findall(r"^\| (\d) \| (.+?) \| (.+?) \|$",
                       bloque.group(1) if bloque else "", re.M)
    s = [
        "# Estado del proyecto", "",
        "> **Generado** por `python3 src/state/snapshot.py`. No editar a mano: "
        "se sobrescribe.", "",
        "**Este es el punto de entrada.** Leer sólo este archivo basta para "
        "retomar el trabajo. El resto de la documentación es consulta puntual: "
        "ver el mapa de lectura al final.", "",
        f"Último commit: `{git('rev-parse', '--short', 'HEAD')}` · "
        f"{git('log', '-1', '--pretty=%s')[:70]}",
        f"Snapshot: {date.today().isoformat()}", "",
        "---", "", "## Fases", "", "| Fase | Alcance | Estado |", "|---|---|---|",
    ]
    s += [f"| {n} | {alcance} | {estado} |" for n, alcance, estado in fases]

    s += ["", "---", "", "## Cifras canónicas", "",
          "Las que gobiernan todo lo publicado. Si alguna cambia, se regenera "
          "este archivo.", "", "| | |", "|---|---|"]
    etiquetas = {
        "ventana": "Ventana temporal",
        "denominador_universo_total": "Publicaciones (universo)",
        "denominador_con_metricas": "Con métricas",
        "denominador_con_autoria_detallada": "Con autoría detallada",
        "formas_de_firma": "Formas de firma de autor",
        "pares_autor_publicacion": "Pares autor × publicación",
        "firmas_con_orcid": "Firmas con ORCID",
        "indicadores_evaluados": "Indicadores evaluados",
        "indicadores_publicados": "Indicadores publicados",
        "reglas": "Reglas de validación",
        "reglas_bloqueantes_fallando": "Reglas bloqueantes fallando",
        "scopus_affiliation_id": "Scopus Affiliation ID",
    }
    for k, etq in etiquetas.items():
        if k in c:
            s.append(f"| {etq} | **{c[k]}** |")

    s += ["", "---", "", "## Colas de revisión humana", "",
          "Capa interna. Ninguna se resuelve automáticamente "
          "(decisión `D-08`).", "", "| Cola | Entradas |", "|---|---|"]
    s += [f"| `internal/{n}.csv` | {v} |" for n, v in colas]

    s += ["", "---", "", f"## Pendientes abiertos ({len(pend)})", "",
          "| # | Pendiente |", "|---|---|"]
    s += [f"| `{i}` | {t} |" for i, t in pend]

    s += ["", "---", "", f"## Decisiones tomadas: {len(dec)}", "",
          "Índice completo en **`docs/DECISIONS.md`**. Las de mayor alcance:", ""]
    clave = {"D-08", "D-09", "D-16", "D-18", "D-22", "D-23", "D-44"}
    s += [f"- **`{d['id']}`** — {d['decision']}" for d in dec if d["id"] in clave]

    s += ["", "---", "", "## Mapa de lectura", "",
          "Abrir sólo lo que responde la pregunta que se tiene:", "",
          "| Si necesita saber… | Abrir |", "|---|---|"]
    s += [f"| {q} | `{f}` |" for q, f in MAPA_LECTURA]

    s += ["", "---", "", "## Reconstruir todo", "",
          "```bash", "make sitio     # auditoría → validación → artefactos → dist/",
          "make estado    # regenera este archivo", "```", ""]

    (ROOT / "STATE.md").write_text("\n".join(s) + "\n", encoding="utf-8")

    n_lineas = len((ROOT / "STATE.md").read_text(encoding="utf-8").splitlines())
    print(f"  decisiones indexadas : {len(dec)}")
    print(f"  pendientes abiertos  : {len(pend)}")
    print(f"  colas internas       : {len(colas)}")
    print(f"  cifras canónicas     : {len(c)}")
    print(f"\n  OK · STATE.md ({n_lineas} líneas) y docs/DECISIONS.md")


if __name__ == "__main__":
    sys.exit(main())
