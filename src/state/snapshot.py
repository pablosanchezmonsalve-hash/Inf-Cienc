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

import json
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


# Cada cifra declara su BASE: sobre qué conjunto está medida y de dónde sale.
#
# POR QUÉ HACE FALTA
#     Sin base declarada, dos cifras verdaderas parecen contradecirse. STATE.md
#     publicaba «589 formas de firma» y «240 con ORCID» mientras el sitio servía
#     556 entidades y 216: las primeras son la base cruda de la fuente, las
#     segundas la base consolidada por revisión humana. Ninguna era incorrecta;
#     lo incorrecto era presentarlas sin decir cuál era cuál, y publicar sólo la
#     que el sitio no usa.
CIFRAS = [
    ("ventana", "Ventana temporal",
     "`config/institution.yml`"),
    ("denominador_universo_total", "Publicaciones (universo)",
     "denominador `universo_total` · `D-16`"),
    ("denominador_con_metricas", "Con métricas",
     "denominador `con_metricas` · `D-16`"),
    ("denominador_con_autoria_detallada", "Con autoría detallada",
     "denominador `con_autoria_detallada` · `D-16`"),
    ("formas_de_firma", "Formas de firma en la fuente",
     "sin consolidar · `internal/matching_log.csv`"),
    ("entidades_autor", "Entidades de autor publicadas",
     "tras consolidación humana · **la que sirve el sitio**"),
    ("apariciones_firma_publicacion", "Apariciones firma × publicación",
     "filas de `internal/matching_log.csv`"),
    ("pares_autor_publicacion", "Pares firma × publicación distintos",
     "sin repetir una firma dentro de la misma publicación"),
    ("firmas_con_orcid", "Firmas con ORCID",
     "sin consolidar · `data/enriched/authors_orcid.csv`"),
    ("entidades_con_forma_de_persona", "Entidades con forma de persona",
     "descontando las marcadas por `E-09`, pendientes de revisión"),
    ("entidades_con_orcid", "Entidades con ORCID",
     "tras consolidación humana · **la que sirve el sitio**"),
    ("indicadores_evaluados", "Indicadores evaluados",
     "`config/indicators.yml`"),
    ("indicadores_publicados", "Indicadores publicados",
     "`config/indicators.yml`, `publicar: true`"),
    ("reglas", "Reglas de validación",
     "`data/interim/validation_report.csv`"),
    ("reglas_bloqueantes_fallando", "Reglas bloqueantes fallando",
     "ídem, severidad `bloqueante`"),
    ("scopus_affiliation_id", "Scopus Affiliation ID",
     "`config/institution.yml`"),
]

# Cifras que miden lo mismo sobre bases distintas. Se publican las dos SÓLO si
# difieren: mientras nadie haya consolidado nada, ambas bases coinciden y una
# segunda fila idéntica sería ruido que sugiere una distinción inexistente.
PARES_DE_BASE = [
    ("formas_de_firma", "entidades_autor"),
    ("firmas_con_orcid", "entidades_con_orcid"),
    ("apariciones_firma_publicacion", "pares_autor_publicacion"),
    ("entidades_autor", "entidades_con_forma_de_persona"),
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
        out["apariciones_firma_publicacion"] = len(m)
        out["pares_autor_publicacion"] = len(m.drop_duplicates(["nombre_en_fuente", "eid"]))
        out["formas_de_firma"] = m["nombre_en_fuente"].nunique()

    # La base consolidada se LEE del artefacto que sirve el sitio, no se
    # recalcula. Recalcularla aquí sería una segunda implementación de la
    # consolidación que vive en `src/build/common_build.py`, y dos
    # implementaciones divergen sin avisar: exactamente el defecto que estas
    # cifras vienen a cerrar. Si STATE.md y el sitio no coinciden, es que el
    # build no se ha vuelto a correr, y eso se ve en la fecha.
    pub = ROOT / "data/processed/authors.json"
    if pub.exists():
        p = json.loads(pub.read_text(encoding="utf-8")).get("parametros", {})
        if p.get("total_firmas") is not None:
            out["entidades_autor"] = p["total_firmas"]
        if p.get("firmas_con_orcid") is not None:
            out["entidades_con_orcid"] = p["firmas_con_orcid"]

    # Cuánto separa a las dos bases, para poder decirlo en vez de dejar la
    # diferencia como un misterio de dos números que no cuadran.
    cons = yaml.safe_load(leer("config/identidades_consolidadas.yml") or "{}") or {}
    grupos = cons.get("grupos") or []
    if grupos:
        out["grupos_consolidados"] = len(grupos)
        out["variantes_fusionadas"] = sum(len(g["variantes"]) for g in grupos)

    # Firmas publicadas que la regla E-09 marcó como probables fragmentos de
    # cadena de afiliación. Cuentan como entidad mientras nadie las revise
    # (`D-08`), así que el recuento de autores sobra en esa cantidad y eso se
    # dice aquí en vez de dejar que el lector lo descubra en la ficha.
    amb = ROOT / "internal/ambiguities_authors.csv"
    if amb.exists() and "entidades_autor" in out:
        a = pd.read_csv(amb, dtype=str)
        marcadas = set(a[a["tipo"] == "E-09_firma_sin_forma_de_persona"]["nombre_en_fuente"])
        # Sólo las PENDIENTES. La auditoría vuelve a marcarlas en cada corrida
        # —se calcula sobre el log, que no se toca—, así que las ya resueltas
        # siguen apareciendo aquí. Restarlas sería descontarlas dos veces:
        # `entidades_autor` viene de `authors.json`, que ya excluye las
        # descartadas.
        res = yaml.safe_load(leer("config/firmas_e09_resueltas.yml") or "{}") or {}
        resueltas = {f["firma"] for k in ("descartadas", "confirmadas")
                     for f in (res.get(k) or [])}
        # Y una firma fusionada en un grupo ya no es entidad propia.
        variantes = {v for g in grupos for v in g["variantes"]}
        pendientes = marcadas - resueltas - variantes
        out["firmas_sin_forma_de_persona"] = len(pendientes)
        out["entidades_con_forma_de_persona"] = out["entidades_autor"] - len(pendientes)
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
          "este archivo.", "",
          "Cada cifra declara su **base**: sobre qué conjunto está medida. Donde "
          "la consolidación de identidades cambia el resultado figuran las dos, "
          "porque citar una donde corresponde la otra es un error silencioso.", "",
          "| Cifra | Valor | Base |", "|---|---|---|"]

    # Una base sin su par se omite: si coinciden, la distinción no existe.
    #
    # Salvo que esa misma cifra sea la base de otro par que SÍ difiere. Sin la
    # excepción, `entidades_autor` desaparecía cuando coincidía con las formas
    # de firma, y quedaba en la tabla una cifra derivada de ella sin la base
    # contra la que compararse: exactamente lo que la columna existe para evitar.
    bases = {a for a, b in PARES_DE_BASE if b in c and c.get(a) != c[b]}
    redundantes = {b for a, b in PARES_DE_BASE
                   if a in c and b in c and c[a] == c[b] and b not in bases}
    for k, etq, base in CIFRAS:
        if k in c and k not in redundantes:
            s.append(f"| {etq} | **{c[k]}** | {base} |")

    if "entidades_autor" not in c:
        s += ["", "> **Falta la base consolidada.** No existe "
              "`data/processed/authors.json`: las cifras de autor de arriba son "
              "sólo la base cruda, que no es la que publica el sitio. Correr "
              "`make artefactos` antes que `make estado`."]
    elif c.get("variantes_fusionadas") and c.get("formas_de_firma") != c.get("entidades_autor"):
        s += ["", f"Las cifras de autor van en dos bases porque una revisión "
              f"humana declaró que **{c['variantes_fusionadas']} formas de firma "
              f"eran {c['grupos_consolidados']} personas** "
              f"(`config/identidades_consolidadas.yml`, decisión `D-08`: el "
              f"pipeline nunca fusiona por heurística). Las restantes siguen sin "
              f"consolidar y pueden incluir variantes de una misma persona."]

    # Fuera del bloque anterior: que haya consolidación y que la auditoría haya
    # marcado firmas son dos condiciones sin relación. Anidarlas dejaba la fila
    # de `E-09` en la tabla sin ninguna explicación en un despliegue nuevo.
    if c.get("firmas_sin_forma_de_persona"):
        s += ["", f"Y **{c['firmas_sin_forma_de_persona']} de las publicadas "
              "probablemente no correspondan a personas**: la auditoría las marcó "
              "como probables fragmentos de cadena de afiliación que la fuente "
              "metió en la lista de autores (regla `E-09`). Dos de las señales son "
              "invariantes de la fuente; la tercera es una heurística sobre la "
              "forma del nombre, y sola no basta. Siguen contando y con ficha: "
              "confirmarlo es una decisión de identidad, y por `D-08` la toma una "
              "persona en `make revision`."]

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
