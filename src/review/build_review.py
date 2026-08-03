"""Genera la herramienta de revisión humana de identidad de autor.

QUÉ RESUELVE
    Las colas `internal/ambiguities_authors.csv`, `identity_candidates.csv` y
    `orcid_conflicts.csv` declaran ambigüedades pero no las resuelven: la
    decisión «estas dos firmas son la misma persona» es una afirmación sobre
    alguien real y sólo la puede tomar una persona (decisión `D-08`).

    Revisarlas a mano sobre los CSV es impracticable: para cada grupo hay que
    cruzar cuatro archivos distintos. Esta herramienta hace ese cruce y presenta
    cada caso con toda su evidencia junta.

QUÉ NO HACE
    No decide. No propone una respuesta por defecto. No fusiona nada. Emite un
    archivo de decisiones que una persona ha tomado, con su fecha.

LA EVIDENCIA QUE APORTA
    Además de lo que ya estaba en las colas, calcula dos señales que ningún
    archivo tenía y que son las que de verdad deciden un caso:

    - **Coautoría directa**: si dos firmas aparecen en la MISMA publicación, son
      casi con seguridad personas distintas. Nadie firma dos veces el mismo
      artículo. Es el descarte más limpio que existe.
    - **Solapamiento de años y de coautores**: dos firmas que nunca coinciden en
      el tiempo y no comparten a nadie son un perfil fragmentado más probable
      que dos personas homónimas.

CAPA
    Interna. La salida vive en `internal/` y nunca entra en `dist/`: el
    ensamblado sólo copia `web/` y `data/processed/`.

Uso:
    python3 src/review/build_review.py

Salida:
    internal/revision_identidad.html    página autónoma, se abre en el navegador
"""

from __future__ import annotations

import html
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
INTERNAL = ROOT / "internal"
INTERIM = ROOT / "data" / "interim"
ENRICHED = ROOT / "data" / "enriched"


def cargar() -> dict:
    """Lee lo que existe y declara lo que falta, en vez de reventar."""
    faltan = []

    def leer(path: Path, nombre: str) -> pd.DataFrame | None:
        if not path.exists():
            faltan.append(f"{nombre} ({path.relative_to(ROOT)})")
            return None
        return pd.read_csv(path, dtype=str)

    d = {
        "amb": leer(INTERNAL / "ambiguities_authors.csv", "cola de ambigüedades"),
        "cand": leer(INTERNAL / "identity_candidates.csv", "candidatos por ORCID"),
        "conf": leer(INTERNAL / "orcid_conflicts.csv", "conflictos de ORCID"),
        "master": leer(INTERIM / "authors_master_draft.csv", "borrador de tabla maestra"),
        "log": leer(INTERNAL / "matching_log.csv", "log de emparejamiento"),
        "orcid": leer(ENRICHED / "authors_orcid.csv", "ORCID enriquecido"),
    }
    if d["master"] is None or d["log"] is None:
        sys.exit(
            "Faltan insumos que genera la auditoría:\n  - " + "\n  - ".join(faltan) +
            "\n\nEjecute primero:  python3 src/audit/run_all.py")
    return d


def perfiles(master: pd.DataFrame, log: pd.DataFrame, orcid: pd.DataFrame | None) -> dict:
    """Ficha de evidencia por forma de firma."""
    orc = {}
    if orcid is not None:
        orc = {r["nombre_en_fuente"]: (r["orcid"], r.get("confianza"))
               for _, r in orcid.iterrows()}

    eids_por_firma = log.groupby("nombre_en_fuente")["eid"].apply(set).to_dict()
    firmas_por_eid = log.groupby("eid")["nombre_en_fuente"].apply(set).to_dict()

    out = {}
    for _, r in master.iterrows():
        n = r["nombre_en_fuente"]
        eids = eids_por_firma.get(n, set())
        # Coautores: otras firmas institucionales que comparten publicación.
        coaut = set()
        for e in eids:
            coaut |= firmas_por_eid.get(e, set())
        coaut.discard(n)
        o = orc.get(n, (None, None))
        out[n] = {
            "nombre": n,
            "n_pub": int(r["n_publicaciones"]),
            "anios": f"{r['anio_min']}–{r['anio_max']}",
            "anio_min": int(r["anio_min"]), "anio_max": int(r["anio_max"]),
            "unidades": [u for u in str(r["unidades_academicas"]).split("|") if u],
            "scopus": [s for s in str(r["scopus_author_ids"] or "").split("|") if s and s != "nan"],
            "orcid": o[0], "orcid_confianza": o[1],
            "eids": sorted(eids), "coautores": sorted(coaut),
        }
    return out


def cruces(a: dict, b: dict) -> dict:
    """Las tres señales que deciden un caso, calculadas entre dos firmas."""
    comunes = set(a["eids"]) & set(b["eids"])
    coaut = set(a["coautores"]) & set(b["coautores"])
    solapan = not (a["anio_max"] < b["anio_min"] or b["anio_max"] < a["anio_min"])
    return {
        # Firmar dos veces el mismo artículo no ocurre: si comparten publicación,
        # son personas distintas. Es el descarte más limpio que existe.
        "publicaciones_comunes": len(comunes),
        "coautores_comunes": len(coaut - {a["nombre"], b["nombre"]}),
        "anios_solapan": solapan,
        "misma_unidad": bool(set(a["unidades"]) & set(b["unidades"])
                             - {"No determinada"}),
        "mismo_orcid": bool(a["orcid"] and a["orcid"] == b["orcid"]),
        "mismo_scopus": bool(set(a["scopus"]) & set(b["scopus"])),
    }


def casos(d: dict, perf: dict) -> list[dict]:
    """Un caso por grupo a revisar, con su evidencia ya cruzada."""
    out = []

    def firmas_de(nombres):
        return [perf[n] for n in nombres if n in perf]

    # ── Firmas que comparten ORCID (D-44). La evidencia más fuerte, primero.
    if d["cand"] is not None:
        for _, r in d["cand"].iterrows():
            fs = firmas_de(r["firmas"].split(" | "))
            if len(fs) < 2:
                continue
            out.append({
                "id": f"orcid-{r['orcid']}", "cola": "ORCID compartido",
                "prioridad": 1,
                "titulo": f"{len(fs)} firmas comparten {r['orcid']}",
                "contexto": ("El apellido no las agrupa: este hallazgo sólo lo aporta "
                             "el identificador persistente."
                             if r.get("hallazgo_nuevo") == "True" else
                             "El apellido también las agrupa."),
                "firmas": fs, "cruces": cruces(fs[0], fs[1]) if len(fs) == 2 else None,
            })

    # ── Una firma con más de un ORCID.
    if d["conf"] is not None:
        for _, r in d["conf"].iterrows():
            f = perf.get(r["nombre_en_fuente"])
            if not f:
                continue
            out.append({
                "id": f"conf-{r['nombre_en_fuente']}", "cola": "ORCID en conflicto",
                "prioridad": 1,
                "titulo": f"{r['nombre_en_fuente']} aparece con {len(r['detalle'].split('|'))} ORCID",
                "contexto": ("Una misma forma de firma recibe identificadores distintos "
                             "según la publicación: o son dos personas que firman igual, "
                             "o una de las asignaciones es incorrecta. ORCID: "
                             + r["detalle"].replace("|", " · ")),
                "firmas": [f], "cruces": None,
            })

    if d["amb"] is None:
        return sorted(out, key=lambda c: (c["prioridad"], c["titulo"]))

    # ── Variantes de nombre (P-03), agrupadas por clave de apellido.
    p03 = d["amb"][d["amb"].tipo.str.startswith("P-03")]
    for clave, g in p03.groupby("clave"):
        fs = firmas_de(sorted(set(g["nombre_en_fuente"])))
        if len(fs) < 2:
            continue
        out.append({
            "id": f"p03-{clave}", "cola": "Variantes de nombre", "prioridad": 2,
            "titulo": " · ".join(f["nombre"] for f in fs),
            "contexto": "Mismo apellido normalizado. Agrupadas por heurística, sin evidencia de identidad.",
            "firmas": fs, "cruces": cruces(fs[0], fs[1]) if len(fs) == 2 else None,
        })

    # ── Un nombre con varios Scopus Author ID (P-04): perfil fragmentado u homonimia.
    p04 = d["amb"][d["amb"].tipo.str.startswith("P-04")]
    for _, r in p04.iterrows():
        f = perf.get(r["nombre_en_fuente"])
        out.append({
            "id": f"p04-{r['clave']}", "cola": "Varios Scopus ID", "prioridad": 3,
            "titulo": r["clave"],
            "contexto": ("Un mismo nombre completo con varios identificadores de Scopus: "
                         "perfil fragmentado en la fuente, u homonimia. IDs: "
                         + r["detalle"].replace("|", " · ")),
            "firmas": [f] if f else [], "cruces": None,
        })

    return sorted(out, key=lambda c: (c["prioridad"], c["titulo"]))


# ─────────────────────────────────────────────────────────────── plantilla

CSS = """
:root{--plano:#f1f5f6;--sup:#fff;--sup2:#eaf1f2;--tinta:#10222b;--tinta2:#4a5f68;
--tinta3:#5a6b71;--linea:#dbe6e8;--marca:#22577A;--accion:#1a6d78;--viva:#38A3A5;
--si:#2fa36b;--no:#cc3f5c;--duda:#d4a017;--radio:6px}
*{box-sizing:border-box}
body{margin:0;font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
background:var(--plano);color:var(--tinta)}
header{background:var(--marca);color:#fff;padding:1.1rem 0;border-bottom:2px solid var(--viva)}
.c{max-width:1100px;margin:0 auto;padding:0 1.5rem}
h1{margin:0;font-size:1.15rem;font-weight:650}
header p{margin:.3rem 0 0;font-size:.82rem;color:#c7f9cc}
.barra{position:sticky;top:0;z-index:10;background:var(--sup);border-bottom:1px solid var(--linea);
padding:.7rem 0;font-size:.85rem}
.barra .c{display:flex;gap:1rem;align-items:center;flex-wrap:wrap}
.avance{font-variant-numeric:tabular-nums}
.avance b{color:var(--marca)}
select,button{font:inherit;font-size:.85rem;border-radius:4px;border:1px solid #bccdd2;
background:var(--sup);color:var(--tinta);padding:.35rem .6rem;cursor:pointer}
button.pri{background:var(--marca);color:#fff;border-color:var(--marca);font-weight:600}
main{padding:1.5rem 0 4rem}
.caso{background:var(--sup);border:1px solid var(--linea);border-radius:var(--radio);
padding:1.1rem 1.25rem;margin-bottom:1rem}
.caso[data-decidido="1"]{opacity:.5}
.caso h2{margin:0 0 .2rem;font-size:1.02rem}
.cola{font-size:.68rem;text-transform:uppercase;letter-spacing:.08em;font-weight:700;
color:var(--tinta3);background:var(--sup2);border:1px solid var(--linea);
border-radius:999px;padding:.1rem .5rem;display:inline-block;margin-bottom:.4rem}
.ctx{font-size:.84rem;color:var(--tinta2);margin:.3rem 0 .9rem}
table{border-collapse:collapse;width:100%;font-size:.84rem;margin-bottom:.8rem}
th,td{text-align:left;padding:.4rem .55rem;border-bottom:1px solid var(--linea);vertical-align:top}
th{background:var(--sup2);font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;
color:var(--tinta2);font-weight:650}
td.n{text-align:right;font-variant-numeric:tabular-nums}
.mono{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.92em}
.senales{display:flex;flex-wrap:wrap;gap:.4rem;margin-bottom:.9rem}
.s{font-size:.78rem;border-radius:999px;padding:.15rem .6rem;border:1px solid}
.s.fuerte-no{background:#fdeaed;border-color:var(--no);color:#8a1f33}
.s.fuerte-si{background:#e8f6ef;border-color:var(--si);color:#155e3c}
.s.neutra{background:var(--sup2);border-color:var(--linea);color:var(--tinta2)}
.dec{display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;
border-top:1px solid var(--linea);padding-top:.8rem}
.dec button{border-width:1.5px}
.dec button[aria-pressed="true"][data-v="misma"]{background:var(--si);color:#fff;border-color:var(--si)}
.dec button[aria-pressed="true"][data-v="distintas"]{background:var(--no);color:#fff;border-color:var(--no)}
.dec button[aria-pressed="true"][data-v="pendiente"]{background:var(--duda);color:#fff;border-color:var(--duda)}
.dec input{flex:1;min-width:180px;font:inherit;font-size:.84rem;padding:.35rem .55rem;
border:1px solid #bccdd2;border-radius:4px;background:var(--sup);color:var(--tinta)}
.aviso{background:#fdf6e7;border:1px solid #c8901a55;border-left:3px solid #c8901a;
border-radius:4px;padding:.7rem .9rem;font-size:.85rem;color:#6a4a05;margin-bottom:1.2rem}
.oculto{display:none!important}
footer{border-top:1px solid var(--linea);padding:1.5rem 0;font-size:.8rem;color:var(--tinta2)}
"""

JS = """
const CASOS = __DATOS__;
const CLAVE = 'revision_identidad_v1';
let dec = {};
try { dec = JSON.parse(localStorage.getItem(CLAVE) || '{}'); } catch (e) { dec = {}; }

function guardar() {
  try { localStorage.setItem(CLAVE, JSON.stringify(dec)); } catch (e) {}
  pintarAvance();
}

function pintarAvance() {
  const n = Object.values(dec).filter(d => d && d.veredicto && d.veredicto !== 'pendiente').length;
  document.getElementById('avance').innerHTML =
    `<b>${n}</b> de ${CASOS.length} resueltos`;
  document.querySelectorAll('.caso').forEach(el => {
    const d = dec[el.dataset.id];
    el.dataset.decidido = (d && d.veredicto && d.veredicto !== 'pendiente') ? '1' : '0';
  });
  filtrar();
}

function filtrar() {
  const f = document.getElementById('filtro').value;
  document.querySelectorAll('.caso').forEach(el => {
    const d = dec[el.dataset.id];
    const resuelto = !!(d && d.veredicto && d.veredicto !== 'pendiente');
    el.classList.toggle('oculto',
      (f === 'pendientes' && resuelto) || (f === 'resueltos' && !resuelto));
  });
}

document.addEventListener('click', e => {
  const b = e.target.closest('.dec button[data-v]');
  if (!b) return;
  const id = b.closest('.caso').dataset.id;
  const v = b.dataset.v;
  const actual = dec[id] || {};
  dec[id] = { ...actual, veredicto: actual.veredicto === v ? null : v,
              fecha: new Date().toISOString().slice(0, 10) };
  b.closest('.dec').querySelectorAll('button[data-v]').forEach(o =>
    o.setAttribute('aria-pressed', String(dec[id].veredicto === o.dataset.v)));
  guardar();
});

document.addEventListener('input', e => {
  if (!e.target.matches('.dec input')) return;
  const id = e.target.closest('.caso').dataset.id;
  dec[id] = { ...(dec[id] || {}), nota: e.target.value };
  try { localStorage.setItem(CLAVE, JSON.stringify(dec)); } catch (err) {}
});

document.getElementById('filtro').addEventListener('change', filtrar);

document.getElementById('exportar').addEventListener('click', () => {
  const esc = v => `"${String(v ?? '').replace(/"/g, '""')}"`;
  const cab = [
    '# Decisiones de identidad de autor — revisión humana',
    '# Generado por internal/revision_identidad.html',
    `# Exportado: ${new Date().toISOString().slice(0, 10)}`,
    '# veredicto: misma = misma persona · distintas = personas distintas · pendiente = sin resolver',
  ].join('\\n');
  const cols = ['caso_id', 'cola', 'firmas', 'veredicto', 'nota', 'fecha'];
  const filas = CASOS.map(c => {
    const d = dec[c.id] || {};
    return [c.id, c.cola, c.firmas.map(f => f.nombre).join(' | '),
            d.veredicto || 'pendiente', d.nota || '', d.fecha || ''].map(esc).join(',');
  });
  const csv = [cab, cols.join(','), ...filas].join('\\n');
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob(['\\ufeff' + csv], { type: 'text/csv;charset=utf-8' }));
  a.download = 'identity_decisions.csv';
  a.click();
});

document.getElementById('limpiar').addEventListener('click', () => {
  if (!confirm('Se borran todas las decisiones guardadas en este navegador. ¿Continuar?')) return;
  dec = {}; guardar();
  document.querySelectorAll('.dec button[data-v]').forEach(b => b.setAttribute('aria-pressed', 'false'));
  document.querySelectorAll('.dec input').forEach(i => { i.value = ''; });
});

// Restaurar lo guardado
CASOS.forEach(c => {
  const d = dec[c.id]; if (!d) return;
  const el = document.querySelector(`.caso[data-id="${CSS.escape(c.id)}"]`);
  if (!el) return;
  el.querySelectorAll('.dec button[data-v]').forEach(b =>
    b.setAttribute('aria-pressed', String(d.veredicto === b.dataset.v)));
  const i = el.querySelector('.dec input'); if (i && d.nota) i.value = d.nota;
});
pintarAvance();
"""


def señales_html(cr: dict | None) -> str:
    if not cr:
        return ""
    s = []
    if cr["publicaciones_comunes"]:
        s.append(("fuerte-no", f"Firman juntas {cr['publicaciones_comunes']} publicación(es) "
                               "— casi seguro personas distintas"))
    else:
        s.append(("neutra", "Nunca firman la misma publicación"))
    if cr["mismo_orcid"]:
        s.append(("fuerte-si", "Mismo ORCID"))
    if cr["mismo_scopus"]:
        s.append(("fuerte-si", "Mismo Scopus Author ID"))
    if cr["coautores_comunes"]:
        s.append(("neutra", f"{cr['coautores_comunes']} coautor(es) en común"))
    else:
        s.append(("neutra", "Sin coautores en común"))
    s.append(("neutra", "Años solapados" if cr["anios_solapan"] else "Años sin solapar"))
    if cr["misma_unidad"]:
        s.append(("neutra", "Misma unidad académica"))
    return ('<div class="senales">'
            + "".join(f'<span class="s {k}">{html.escape(t)}</span>' for k, t in s)
            + "</div>")


def tabla_firmas(fs: list[dict]) -> str:
    if not fs:
        return '<p class="ctx">Sin perfil disponible para esta firma.</p>'
    filas = ""
    for f in fs:
        filas += (
            f'<tr><td><strong>{html.escape(f["nombre"])}</strong></td>'
            f'<td class="n">{f["n_pub"]}</td><td class="n">{html.escape(f["anios"])}</td>'
            f'<td>{html.escape(" · ".join(f["unidades"]) or "—")}</td>'
            f'<td class="mono">{html.escape(" ".join(f["scopus"]) or "—")}</td>'
            f'<td class="mono">{html.escape(f["orcid"] or "—")}'
            + (f' <span style="color:#5a6b71">({html.escape(f["orcid_confianza"])})</span>'
               if f["orcid"] and f["orcid_confianza"] else "")
            + "</td></tr>")
    return ('<table><thead><tr><th>Forma de firma</th><th>Pub.</th><th>Años</th>'
            '<th>Unidad académica</th><th>Scopus ID</th><th>ORCID</th></tr></thead>'
            f"<tbody>{filas}</tbody></table>")


def render(cs: list[dict], meta: dict) -> str:
    cuerpo = ""
    for c in cs:
        cuerpo += f"""
    <article class="caso" data-id="{html.escape(c['id'])}" data-decidido="0">
      <span class="cola">{html.escape(c['cola'])}</span>
      <h2>{html.escape(c['titulo'])}</h2>
      <p class="ctx">{html.escape(c['contexto'])}</p>
      {señales_html(c['cruces'])}
      {tabla_firmas(c['firmas'])}
      <div class="dec">
        <button type="button" data-v="misma" aria-pressed="false">Misma persona</button>
        <button type="button" data-v="distintas" aria-pressed="false">Personas distintas</button>
        <button type="button" data-v="pendiente" aria-pressed="false">Sigo sin saber</button>
        <input type="text" placeholder="Nota (opcional): en qué te basaste">
      </div>
    </article>"""

    datos = json.dumps([{"id": c["id"], "cola": c["cola"],
                         "firmas": [{"nombre": f["nombre"]} for f in c["firmas"]]}
                        for c in cs], ensure_ascii=False)

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Revisión de identidad de autor — capa interna</title>
<style>{CSS}</style>
</head>
<body>
<header><div class="c">
  <h1>Revisión de identidad de autor</h1>
  <p>Capa interna · {meta['casos']} casos · generado el {meta['fecha']}
     desde {meta['firmas']} formas de firma</p>
</div></header>

<div class="barra"><div class="c">
  <span class="avance" id="avance"></span>
  <select id="filtro" aria-label="Filtrar casos">
    <option value="todos">Todos los casos</option>
    <option value="pendientes">Sólo pendientes</option>
    <option value="resueltos">Sólo resueltos</option>
  </select>
  <button type="button" class="pri" id="exportar">Exportar decisiones (CSV)</button>
  <button type="button" id="limpiar">Borrar todo</button>
</div></div>

<main class="c">
  <div class="aviso">
    <strong>Esta página no decide nada por usted.</strong>
    Reúne la evidencia dispersa en cuatro archivos y la presenta junta; el
    veredicto lo pone usted. Las decisiones se guardan en este navegador
    mientras trabaja: <strong>expórtelas a CSV antes de cerrar</strong>, y
    guarde el archivo como <span class="mono">internal/identity_decisions.csv</span>.
    Nada de lo que marque aquí modifica el sitio público por sí solo.
  </div>
  <div class="aviso">
    <strong>Cómo leer las señales.</strong>
    «Firman juntas N publicaciones» es el descarte más limpio: nadie firma dos
    veces el mismo artículo, así que si dos formas de firma aparecen en el mismo
    trabajo son personas distintas. «Mismo ORCID» y «Mismo Scopus Author ID»
    apuntan en sentido contrario, pero recuerde que la asignación de ORCID es a
    su vez una hipótesis por apellido e inicial. El resto son indicios, no
    pruebas.
  </div>
  {cuerpo}
</main>

<footer class="c">
  Generado por <span class="mono">src/review/build_review.py</span>.
  Regenerable. No se despliega: el ensamblado del sitio sólo copia
  <span class="mono">web/</span> y <span class="mono">data/processed/</span>.
</footer>

<script>{JS.replace("__DATOS__", datos)}</script>
</body>
</html>
"""


def main() -> int:
    print("=" * 78)
    print("HERRAMIENTA DE REVISIÓN DE IDENTIDAD DE AUTOR")
    print("=" * 78)

    d = cargar()
    perf = perfiles(d["master"], d["log"], d["orcid"])
    cs = casos(d, perf)
    if not cs:
        print("  No hay casos que revisar. No se escribe nada.")
        return 0

    salida = INTERNAL / "revision_identidad.html"
    salida.write_text(render(cs, {
        "casos": len(cs), "fecha": date.today().isoformat(), "firmas": len(perf),
    }), encoding="utf-8")

    por_cola: dict[str, int] = defaultdict(int)
    for c in cs:
        por_cola[c["cola"]] += 1
    descartables = sum(1 for c in cs
                       if c["cruces"] and c["cruces"]["publicaciones_comunes"])

    for cola, n in sorted(por_cola.items(), key=lambda x: -x[1]):
        print(f"  {n:>4}  {cola}")
    print(f"\n  casos totales                 : {len(cs)}")
    print(f"  descartables por coautoría    : {descartables} "
          "(firman juntas, luego son personas distintas)")
    print(f"\n  OK · {salida.relative_to(ROOT)}")
    print("       Ábralo en el navegador. Exporte a internal/identity_decisions.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
