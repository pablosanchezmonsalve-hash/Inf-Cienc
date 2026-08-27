"""Genera el panel de revisión de huecos en las fichas de autor (T-02x / V2-01).

QUÉ RESUELVE
    El usuario pidió entender por qué `autores.html` publica fichas con
    identidad sin consolidar, y revisar manualmente cuántas fichas carecen
    de ORCID o de unidad académica determinada. Las tres preguntas ya
    tienen respuesta en `data/processed/authors.json` (campo por campo,
    ficha por ficha) — lo que faltaba era una vista que las junte y deje
    filtrar, ordenar y buscar sin tener que leer JSON a mano.

QUÉ NO HACE
    No decide nada ni exporta un CSV de veredictos: a diferencia de
    `revision_identidad.html` o `revision_cobertura_openalex.html`, aquí no
    hay una pregunta cerrada («¿es la misma persona?», «¿es de la UFT?»)
    que un botón sí/no pueda resolver. Falta ORCID o falta unidad
    determinada son HECHOS del dato, no ambigüedades a resolver con un
    clic — la acción sobre cada caso (buscar el ORCID a mano, reconocer una
    afiliación nueva) vive en otra parte:
      · identidad sin consolidar  -> `internal/revision_identidad.html`
        (cola «Varios Scopus ID»), donde SÍ hay un veredicto que registrar.
      · unidad no determinada     -> si la cadena cruda revela una unidad
        reconocible, es un caso para `config/matching_rules.yml`
        (`correcciones_declaradas` o `vocabulario`), igual que T-02.
    Este panel sólo deja ver, filtrar y exportar la lista para investigar.

CAPA
    Interna: incluye afiliaciones crudas como evidencia (`matching_log.csv`).
    No entra en `dist/`.

Uso:
    python3 src/review/build_author_gaps.py

Salida:
    internal/revision_huecos_autores.html
"""

from __future__ import annotations

import html as htmlmod
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

if sys.platform == "win32":
    # La consola de Windows usa cp1252 por defecto: revienta cualquier print()
    # con caracteres como "→"/"✗"/"⚠". Mismo patrón que src/enrich/orcid_openalex.py.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AUTHORS = ROOT / "data" / "processed" / "authors.json"
MATCHING_LOG = ROOT / "internal" / "matching_log.csv"
SALIDA = ROOT / "internal" / "revision_huecos_autores.html"


def es(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _evidencia_no_determinada(log: pd.DataFrame) -> dict[str, list[str]]:
    """Nombre en la fuente -> hasta 2 cadenas de afiliación distintas que la
    auditoría no pudo clasificar. Es la evidencia que un humano necesita
    para reconocer una unidad que el patrón de extracción no reconoce."""
    filas = log[log["unidad_academica"] == "No determinada"]
    out: dict[str, list[str]] = defaultdict(list)
    for nombre, afil in zip(filas["nombre_en_fuente"], filas["afiliacion_declarada_raw"]):
        if not isinstance(afil, str) or not afil.strip():
            continue
        lista = out[nombre]
        if afil not in lista and len(lista) < 2:
            lista.append(afil)
    return out


CSS = """
:root{--plano:#f1f5f6;--sup:#fff;--sup2:#eaf1f2;--tinta:#10222b;--tinta2:#4a5f68;
--tinta3:#5a6b71;--linea:#dbe6e8;--marca:#22577A;--accion:#1a6d78;--viva:#38A3A5;
--si:#2fa36b;--no:#cc3f5c;--tipo:#c8901a;--radio:6px}
*{box-sizing:border-box}
body{margin:0;font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
background:var(--plano);color:var(--tinta)}
header{background:var(--marca);color:#fff;padding:1.1rem 0;border-bottom:2px solid var(--viva)}
.c{max-width:1180px;margin:0 auto;padding:0 1.5rem}
h1{margin:0;font-size:1.15rem;font-weight:650}
header p{margin:.3rem 0 0;font-size:.82rem;color:#c7f9cc}
.barra{position:sticky;top:0;z-index:10;background:var(--sup);border-bottom:1px solid var(--linea);
padding:.7rem 0;font-size:.85rem}
.barra .c{display:flex;gap:1rem;align-items:center;flex-wrap:wrap}
.avance{font-variant-numeric:tabular-nums}
.avance b{color:var(--marca)}
select,input.buscar{font:inherit;font-size:.83rem;padding:.3rem .5rem;border:1px solid #bccdd2;
border-radius:4px;background:var(--sup);color:var(--tinta)}
button{font:inherit;font-size:.85rem;border-radius:4px;border:1px solid #bccdd2;
background:var(--sup);color:var(--tinta);padding:.35rem .6rem;cursor:pointer}
button.pri{background:var(--marca);color:#fff;border-color:var(--marca);font-weight:600}
button.filtro{border-radius:999px}
button.filtro[aria-pressed="true"]{background:var(--accion);color:#fff;border-color:var(--accion)}
main{padding:1.5rem 0 4rem}
.resumen{display:flex;gap:.8rem;flex-wrap:wrap;margin-bottom:1.2rem}
.resumen .tarjeta{background:var(--sup);border:1px solid var(--linea);border-radius:var(--radio);
padding:.7rem 1rem;flex:1;min-width:170px}
.resumen .tarjeta b{display:block;font-size:1.4rem;color:var(--marca);font-variant-numeric:tabular-nums}
.resumen .tarjeta span{font-size:.78rem;color:var(--tinta2)}
.aviso{background:#fdf6e7;border:1px solid #c8901a55;border-left:3px solid #c8901a;
border-radius:4px;padding:.7rem .9rem;font-size:.85rem;color:#6a4a05;margin:0 0 1.2rem}
table{width:100%;border-collapse:collapse;background:var(--sup);border:1px solid var(--linea);
border-radius:var(--radio);overflow:hidden;font-size:.87rem}
thead th{background:var(--sup2);text-align:left;padding:.5rem .7rem;font-size:.72rem;
text-transform:uppercase;letter-spacing:.04em;color:var(--tinta2);cursor:pointer;
border-bottom:1px solid var(--linea);white-space:nowrap}
thead th:hover{color:var(--tinta)}
thead th.activa{color:var(--marca)}
tbody td{padding:.5rem .7rem;border-bottom:1px solid var(--linea);vertical-align:top}
tbody tr:last-child td{border-bottom:none}
tbody tr:hover{background:var(--sup2)}
.n{font-variant-numeric:tabular-nums}
.hueco{color:var(--no);font-weight:600}
.hueco-suave{color:#916b00}
.si{color:var(--si)}
.pill{display:inline-block;font-size:.68rem;font-weight:700;text-transform:uppercase;
letter-spacing:.03em;padding:.1rem .5rem;border-radius:999px;border:1px solid transparent}
.pill.no-orcid{background:#fbe4e8;color:var(--no);border-color:#f3c1cb}
.pill.no-det{background:#fdf1da;color:var(--tipo);border-color:#f5dca3}
.pill.no-cons{background:#eae0f7;color:#6a3fb0;border-color:#d9c6f2}
.evidencia{font-size:.78rem;color:var(--tinta3);font-family:ui-monospace,Menlo,Consolas,monospace;
margin:.2rem 0 0;max-width:34rem}
.evidencia div{white-space:normal}
footer{border-top:1px solid var(--linea);padding:1.5rem 0;font-size:.8rem;color:var(--tinta2)}
footer a{color:var(--accion)}
.vacio{padding:2rem;text-align:center;color:var(--tinta3)}
"""

JS = """
const ITEMS = __DATOS__;
let orden = { col: 'n_publicaciones', dir: -1 };
let filtros = new Set();

function pintar() {
  const q = (document.getElementById('buscar').value || '').toLowerCase();
  let filas = ITEMS.filter(it => {
    if (q && !it.nombre.toLowerCase().includes(q)) return false;
    if (filtros.has('orcid') && it.orcid) return false;
    if (filtros.has('unidad') && !it.sin_unidad) return false;
    if (filtros.has('identidad') && !it.identidad_no_consolidada) return false;
    return true;
  });
  filas.sort((a, b) => {
    const va = a[orden.col], vb = b[orden.col];
    if (va == null && vb == null) return 0;
    if (va == null) return 1;
    if (vb == null) return -1;
    if (typeof va === 'string') return orden.dir * va.localeCompare(vb);
    return orden.dir * (va - vb);
  });

  document.getElementById('avance').innerHTML =
    `<b>${filas.length}</b> de ${ITEMS.length} fichas`;

  const cuerpo = filas.map(it => {
    const pills = [];
    if (!it.orcid) pills.push('<span class="pill no-orcid">Sin ORCID</span>');
    if (it.sin_unidad) pills.push('<span class="pill no-det">Unidad no determinada</span>');
    if (it.identidad_no_consolidada) pills.push('<span class="pill no-cons">Identidad sin consolidar</span>');
    const evid = (it.evidencia && it.evidencia.length)
      ? `<p class="evidencia">${it.evidencia.map(e => `<div>&ldquo;${e}&rdquo;</div>`).join('')}</p>` : '';
    return `<tr>
      <td><a href="autor.html?id=${encodeURIComponent(it.id)}" target="_blank" rel="noopener">${it.nombre}</a>
        ${pills.join(' ')}${evid}</td>
      <td class="n">${it.n_publicaciones}</td>
      <td>${it.unidad}</td>
      <td>${it.orcid ? `<span class="si">${it.orcid}</span>` : '<span class="hueco">&mdash;</span>'}</td>
      <td>${it.identidad_no_consolidada ? '<span class="hueco-suave">sin consolidar</span>' : 'consolidada'}</td>
    </tr>`;
  }).join('');

  document.getElementById('cuerpo').innerHTML = cuerpo ||
    '<tr><td colspan="5" class="vacio">Ninguna ficha coincide con este filtro.</td></tr>';

  document.querySelectorAll('thead th[data-col]').forEach(th => {
    th.classList.toggle('activa', th.dataset.col === orden.col);
    th.textContent = th.dataset.etq + (th.dataset.col === orden.col ? (orden.dir === 1 ? ' \\u2191' : ' \\u2193') : '');
  });
}

document.querySelectorAll('thead th[data-col]').forEach(th => {
  th.addEventListener('click', () => {
    if (orden.col === th.dataset.col) orden.dir *= -1;
    else { orden.col = th.dataset.col; orden.dir = th.dataset.col === 'nombre' ? 1 : -1; }
    pintar();
  });
});

document.querySelectorAll('button.filtro').forEach(b => {
  b.addEventListener('click', () => {
    const f = b.dataset.f;
    if (filtros.has(f)) filtros.delete(f); else filtros.add(f);
    b.setAttribute('aria-pressed', filtros.has(f) ? 'true' : 'false');
    pintar();
  });
});

document.getElementById('buscar').addEventListener('input', pintar);

document.getElementById('exportar').addEventListener('click', () => {
  const esc = v => `"${String(v ?? '').replace(/"/g, '""')}"`;
  const cab = [
    '# Fichas de autor con huecos de dato — vista filtrada, exportada para revisión manual',
    '# Generado por internal/revision_huecos_autores.html',
    `# Exportado: ${new Date().toISOString().slice(0, 10)}`,
    '# Este archivo no se aplica con ningún script: es sólo la lista visible al exportar,',
    '# para llevar registro de qué se investigó fuera de esta herramienta.',
  ].join('\\n');
  const cols = ['id', 'nombre', 'n_publicaciones', 'unidad', 'orcid', 'identidad_no_consolidada'];
  const q = (document.getElementById('buscar').value || '').toLowerCase();
  const filas = ITEMS.filter(it => {
    if (q && !it.nombre.toLowerCase().includes(q)) return false;
    if (filtros.has('orcid') && it.orcid) return false;
    if (filtros.has('unidad') && !it.sin_unidad) return false;
    if (filtros.has('identidad') && !it.identidad_no_consolidada) return false;
    return true;
  }).map(it => [it.id, it.nombre, it.n_publicaciones, it.unidad, it.orcid || '',
    it.identidad_no_consolidada ? 'si' : 'no'].map(esc).join(','));
  entregar('huecos_autores', '\\ufeff' + [cab, cols.join(','), ...filas].join('\\n'));
});

async function entregar(nombre, csv) {
  try {
    const d = await window.claude?.use?.('downloads');
    if (d) {
      try {
        await d.save({ filename: nombre + '.csv', data: csv });
      } catch (e) {
        if (e && e.code === 'declined') return;
        if (e && e.code === 'extension_not_enabled') {
          await d.save({ filename: nombre + '.txt', data: csv });
        } else { throw e; }
      }
      return;
    }
  } catch (e) {
    alert('No se pudo entregar el archivo: ' + (e && e.message ? e.message : e));
    return;
  }
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
  a.download = nombre + '.csv';
  a.click();
}

pintar();
"""


def render_html(autores: list[dict], evidencia: dict[str, list[str]]) -> str:
    items = []
    for a in autores:
        sin_unidad = a["unidades"] == ["No determinada"]
        ev = evidencia.get(a["nombre"], []) if sin_unidad else []
        items.append({
            "id": a["id"], "nombre": a["nombre"],
            "n_publicaciones": a["n_publicaciones"],
            "unidad": a["unidades"][0] if a["unidades"] else "Sin dato declarado",
            "sin_unidad": sin_unidad,
            "orcid": a.get("orcid"),
            "identidad_no_consolidada": bool(a.get("identidad_no_consolidada")),
            "evidencia": [htmlmod.escape(e) for e in ev],
        })

    total = len(autores)
    sin_orcid = sum(1 for a in autores if not a.get("orcid"))
    sin_unidad = sum(1 for a in autores if a["unidades"] == ["No determinada"])
    no_cons = sum(1 for a in autores if a.get("identidad_no_consolidada"))
    datos = json.dumps(items, ensure_ascii=False)
    hoy = date.today().isoformat()

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Huecos en fichas de autor — capa interna</title>
<style>{CSS}</style>
</head>
<body>
<header><div class="c">
  <h1>Fichas de autor: ORCID, unidad académica e identidad sin consolidar</h1>
  <p>Capa interna · generado el {hoy} · {es(total)} fichas publicadas</p>
</div></header>

<div class="barra"><div class="c">
  <span class="avance" id="avance"></span>
  <button type="button" class="filtro" data-f="orcid" aria-pressed="false">Sin ORCID</button>
  <button type="button" class="filtro" data-f="unidad" aria-pressed="false">Unidad no determinada</button>
  <button type="button" class="filtro" data-f="identidad" aria-pressed="false">Identidad sin consolidar</button>
  <input type="text" class="buscar" id="buscar" placeholder="Buscar por nombre…">
  <button type="button" class="pri" id="exportar">Exportar vista filtrada (CSV)</button>
</div></div>

<main class="c">
  <div class="resumen">
    <div class="tarjeta"><b>{es(total)}</b><span>fichas publicadas</span></div>
    <div class="tarjeta"><b>{es(sin_orcid)}</b><span>sin ORCID ({100*sin_orcid/total:.0f} %)</span></div>
    <div class="tarjeta"><b>{es(sin_unidad)}</b><span>unidad académica «No determinada» ({100*sin_unidad/total:.0f} %)</span></div>
    <div class="tarjeta"><b>{es(no_cons)}</b><span>identidad sin consolidar ({100*no_cons/total:.0f} %)</span></div>
  </div>

  <div class="aviso">
    <strong>Esta vista no decide ni aplica nada.</strong> «Sin ORCID» y
    «unidad no determinada» son hechos del dato, no ambigüedades con un
    veredicto sí/no — investigar cada caso es trabajo manual (buscar el
    registro de ORCID, reconocer una afiliación que el patrón de extracción
    no cubre). «Identidad sin consolidar» SÍ tiene una cola de decisión
    propia: <a href="revision_identidad.html">revision_identidad.html</a>,
    cola «Varios Scopus ID» — ese caso puede significar que dos personas
    distintas comparten una misma forma de firma. Exportar aquí sólo deja
    constancia de qué se miró, no aplica ningún cambio a
    <span class="evidencia" style="display:inline">config/matching_rules.yml</span>
    ni a ningún otro artefacto.
  </div>

  <table>
    <thead><tr>
      <th data-col="nombre" data-etq="Nombre">Nombre</th>
      <th data-col="n_publicaciones" data-etq="Publicaciones">Publicaciones</th>
      <th data-col="unidad" data-etq="Unidad académica">Unidad académica</th>
      <th data-col="orcid" data-etq="ORCID">ORCID</th>
      <th data-col="identidad_no_consolidada" data-etq="Identidad">Identidad</th>
    </tr></thead>
    <tbody id="cuerpo"></tbody>
  </table>
</main>
<footer><div class="c">
  Generado por <span class="evidencia" style="display:inline">src/review/build_author_gaps.py</span>
  a partir de <span class="evidencia" style="display:inline">data/processed/authors.json</span> y
  <span class="evidencia" style="display:inline">internal/matching_log.csv</span> (evidencia de
  afiliación cruda, sólo para los casos sin unidad determinada). Regenerable —
  no guarda estado propio entre corridas.
</div></footer>
<script>{JS.replace("__DATOS__", datos)}</script>
</body>
</html>
"""


def main() -> int:
    if not AUTHORS.exists():
        sys.exit(f"Falta {AUTHORS.relative_to(ROOT)}. Ejecute: python3 src/build/03_authors.py")
    if not MATCHING_LOG.exists():
        sys.exit(f"Falta {MATCHING_LOG.relative_to(ROOT)}. Ejecute: python3 src/audit/run_all.py")

    autores = json.loads(AUTHORS.read_text(encoding="utf-8"))["autores"]
    log = pd.read_csv(MATCHING_LOG, dtype=str)
    evidencia = _evidencia_no_determinada(log)

    SALIDA.write_text(render_html(autores, evidencia), encoding="utf-8")

    total = len(autores)
    sin_orcid = sum(1 for a in autores if not a.get("orcid"))
    sin_unidad = sum(1 for a in autores if a["unidades"] == ["No determinada"])
    no_cons = sum(1 for a in autores if a.get("identidad_no_consolidada"))

    print("=" * 78)
    print("REVISIÓN DE HUECOS EN FICHAS DE AUTOR")
    print("=" * 78)
    print(f"  fichas totales          : {total}")
    print(f"  sin ORCID               : {sin_orcid} ({100*sin_orcid/total:.1f} %)")
    print(f"  unidad no determinada   : {sin_unidad} ({100*sin_unidad/total:.1f} %)")
    print(f"  identidad sin consolidar: {no_cons} ({100*no_cons/total:.1f} %)")
    print(f"\n  OK · {SALIDA.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
