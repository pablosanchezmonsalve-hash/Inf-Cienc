"""Genera la herramienta interactiva para revisar la brecha de cobertura de OpenAlex (V2-26).

QUÉ RESUELVE
    `internal/openalex_cobertura.csv` (`openalex_cobertura.py`) deja 414 obras
    que OpenAlex atribuye a la UFT y el universo (Scopus) no tiene. Es una cola
    de revisión, no un ajuste del corpus (`D-206`): decidir CADA caso exige
    criterio humano, porque «no está en Scopus» admite lecturas incompatibles
    —producción real fuera de Scopus, atribución errónea de la desambiguación
    de OpenAlex, o un tipo documental que este proyecto excluye a propósito.

    Es la misma clase de tarea que la validación de unidades académicas o la
    revisión de identidad: la pregunta ya tiene la evidencia delante —autor,
    institución tal como la declara OpenAlex, DOI, año, tipo, citas— y
    responderla debe costar una lectura y un clic, no abrir cada DOI a mano.

QUÉ NO HACE
    No decide nada por sí sola, y no toca `data/interim/publications_universe.csv`
    bajo ninguna circunstancia: aunque se marque «confirmado UFT», la obra NO
    entra al universo. Ampliar el corpus es una decisión de alcance aparte,
    posterior y explícita — nunca la consecuencia automática de esta revisión.
    Lo único que esta herramienta cambia es la columna `resolucion` de
    `internal/openalex_cobertura.csv`: dejar constancia de que alguien miró el
    caso, y qué concluyó.

QUÉ PRODUCE
    `internal/revision_cobertura_openalex.html` — herramienta interactiva,
    mismo patrón que `build_unit_validation.py`/`build_review.py`: marca por
    caso, exporta un CSV, `apply_openalex_review.py` lo aplica.

CAPA
    Interna: no entra en `dist/`.

Uso:
    python3 src/review/build_openalex_review.py

Salida:
    internal/revision_cobertura_openalex.html
"""

from __future__ import annotations

import html as htmlmod
import io
import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

if sys.platform == "win32":
    # La consola de Windows usa cp1252 por defecto: revienta cualquier print()
    # con caracteres como "→"/"✗"/"⚠". Mismo patrón que src/enrich/orcid_openalex.py.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(ROOT / "src" / "audit"))

import common as c  # noqa: E402

FUENTE = ROOT / "internal" / "openalex_cobertura.csv"
DECISIONES = ROOT / "internal" / "openalex_cobertura_decisiones.csv"
CROSSREF = ROOT / "internal" / "openalex_cobertura_crossref.csv"
SALIDA = ROOT / "internal" / "revision_cobertura_openalex.html"


def _json_para_script(obj) -> str:
    """JSON seguro para incrustar en <script>: json.dumps no escapa '</',
    así que un título o afiliación con "</script>" cerraría el bloque antes
    de tiempo y el resto se interpretaría como HTML."""
    return (
        json.dumps(obj, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )

CSS = """
:root{--plano:#f1f5f6;--sup:#fff;--sup2:#eaf1f2;--tinta:#10222b;--tinta2:#4a5f68;
--tinta3:#5a6b71;--linea:#dbe6e8;--marca:#22577A;--accion:#1a6d78;--viva:#38A3A5;
--si:#2fa36b;--no:#cc3f5c;--tipo:#c8901a;--radio:6px}
*{box-sizing:border-box}
body{margin:0;font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
background:var(--plano);color:var(--tinta)}
header{background:var(--marca);color:#fff;padding:1.1rem 0;border-bottom:2px solid var(--viva)}
.c{max-width:960px;margin:0 auto;padding:0 1.5rem}
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
main{padding:1.5rem 0 4rem}
.aviso{background:#fdf6e7;border:1px solid #c8901a55;border-left:3px solid #c8901a;
border-radius:4px;padding:.7rem .9rem;font-size:.85rem;color:#6a4a05;margin:1rem 0 1.4rem}
.item{background:var(--sup);border:1px solid var(--linea);border-radius:var(--radio);
padding:1rem 1.2rem;margin-bottom:.8rem}
.item[data-decidido="1"]{opacity:.5}
.item h3{margin:0 0 .2rem;font-size:.95rem;line-height:1.35}
.meta{display:flex;gap:.5rem;flex-wrap:wrap;margin-bottom:.4rem}
.n{font-size:.68rem;text-transform:uppercase;letter-spacing:.06em;font-weight:700;
color:var(--tinta3);background:var(--sup2);border:1px solid var(--linea);
border-radius:999px;padding:.1rem .5rem;display:inline-block}
.ctx{font-size:.83rem;color:var(--tinta2);margin:.2rem 0 .8rem}
.ctx b{color:var(--tinta)}
.mono{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.88em}
.xref{font-size:.83rem;border-left:3px solid var(--linea);padding:.35rem .7rem;
margin:.5rem 0 .8rem;color:var(--tinta2)}
.xref.hay-afiliacion{border-left-color:var(--si);background:#f0faf4}
.xref b{color:var(--tinta)}
.xref .etq{font-size:.68rem;text-transform:uppercase;letter-spacing:.04em;
color:var(--tinta3);font-weight:700}
.dec{display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;
border-top:1px solid var(--linea);padding-top:.7rem}
.dec button[data-v]{border-width:1.5px}
.dec button[aria-pressed="true"][data-v="uft"]{background:var(--si);color:#fff;border-color:var(--si)}
.dec button[aria-pressed="true"][data-v="error"]{background:var(--no);color:#fff;border-color:var(--no)}
.dec button[aria-pressed="true"][data-v="tipo"]{background:var(--tipo);color:#fff;border-color:var(--tipo)}
.dec input{flex:1;min-width:170px;font:inherit;font-size:.83rem;padding:.35rem .55rem;
border:1px solid #bccdd2;border-radius:4px;background:var(--sup);color:var(--tinta)}
footer{border-top:1px solid var(--linea);padding:1.5rem 0;font-size:.8rem;color:var(--tinta2)}
"""

JS = """
const ITEMS = __DATOS__;
const CLAVE = 'revision_cobertura_openalex_v1';
let dec = {};
try { dec = JSON.parse(localStorage.getItem(CLAVE) || '{}'); } catch (e) { dec = {}; }

ITEMS.forEach(it => { if (it.previa && !dec[it.id]) dec[it.id] = { ...it.previa }; });

function guardar() {
  try { localStorage.setItem(CLAVE, JSON.stringify(dec)); } catch (e) {}
  pintarAvance();
}

function pintarAvance() {
  const n = Object.values(dec).filter(d => d && d.veredicto).length;
  document.getElementById('avance').innerHTML =
    `<b>${n}</b> de ${ITEMS.length} revisados · <b>${ITEMS.length - n}</b> pendientes`;
  document.querySelectorAll('.item').forEach(el => {
    const d = dec[el.dataset.id];
    el.dataset.decidido = (d && d.veredicto) ? '1' : '0';
  });
  aplicarFiltro();
}

document.addEventListener('click', e => {
  const b = e.target.closest('.dec button[data-v]');
  if (!b) return;
  const item = b.closest('.item');
  const id = item.dataset.id;
  const v = b.dataset.v;
  const actual = dec[id] || {};
  dec[id] = { ...actual, veredicto: actual.veredicto === v ? null : v };
  item.querySelectorAll('.dec button[data-v]').forEach(o =>
    o.setAttribute('aria-pressed', String(dec[id].veredicto === o.dataset.v)));
  guardar();
});

document.addEventListener('input', e => {
  const campo = e.target.closest('.dec input[data-campo]');
  if (campo) {
    const id = campo.closest('.item').dataset.id;
    dec[id] = { ...(dec[id] || {}), [campo.dataset.campo]: campo.value };
    try { localStorage.setItem(CLAVE, JSON.stringify(dec)); } catch (err) {}
    return;
  }
  if (e.target.id === 'buscar') aplicarFiltro();
});

document.getElementById('filtro-estado').addEventListener('change', aplicarFiltro);

function aplicarFiltro() {
  const q = (document.getElementById('buscar').value || '').toLowerCase();
  const solo = document.getElementById('filtro-estado').value;
  document.querySelectorAll('.item').forEach(el => {
    const texto = el.dataset.buscar;
    const decidido = el.dataset.decidido === '1';
    let visible = texto.includes(q);
    if (solo === 'pendientes' && decidido) visible = false;
    if (solo === 'revisados' && !decidido) visible = false;
    el.style.display = visible ? '' : 'none';
  });
}

document.getElementById('exportar').addEventListener('click', () => {
  const esc = v => `"${String(v ?? '').replace(/"/g, '""')}"`;
  const cab = [
    '# Revisión de la brecha de cobertura OpenAlex (V2-26) — decisión humana',
    '# Generado por internal/revision_cobertura_openalex.html',
    `# Exportado: ${new Date().toISOString().slice(0, 10)}`,
    '# veredicto: uft = producción real de la UFT fuera de Scopus ·',
    '#            error = atribución errónea de OpenAlex (no es UFT) ·',
    '#            tipo = tipo documental que este proyecto excluye a propósito',
    '# ESTO NO MODIFICA EL UNIVERSO PUBLICADO. Sólo deja constancia de la revisión.',
  ].join('\\n');
  const cols = ['openalex_id', 'doi', 'veredicto', 'nota'];
  const filas = ITEMS.map(it => {
    const d = dec[it.id] || {};
    return [it.id, it.doi, d.veredicto || 'pendiente', d.nota || ''].map(esc).join(',');
  });
  entregar('openalex_cobertura_decisiones', '\\ufeff' + [cab, cols.join(','), ...filas].join('\\n'));
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
    alert('No se pudo entregar el archivo: ' + (e && e.message ? e.message : e)
      + '\\n\\nSus respuestas NO se han perdido: siguen guardadas en este navegador.');
    return;
  }
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
  a.download = nombre + '.csv';
  a.click();
}

document.getElementById('limpiar').addEventListener('click', () => {
  if (!confirm('Se borra lo revisado en ESTE navegador. Lo ya registrado en '
    + 'el CSV del repositorio no se toca. ¿Continuar?')) return;
  dec = {};
  ITEMS.forEach(it => { if (it.previa) dec[it.id] = { ...it.previa }; });
  try { localStorage.setItem(CLAVE, JSON.stringify(dec)); } catch (e) {}
  location.reload();
});

pintarAvance();
"""


def _leer_previas(ruta: Path) -> dict[str, dict]:
    """Decisiones de una corrida anterior de esta misma herramienta, si existe.

    Se salta la cabecera de comentario por POSICIÓN, no con
    `pd.read_csv(comment='#')`: eso trunca en la primera almohadilla ESTÉ
    DONDE ESTÉ, y una nota como «ítem #3» perdería la mitad en silencio
    (mismo bug que ya se corrigió en decisiones.py::leer()).
    """
    if not ruta.exists():
        return {}
    lineas = ruta.read_text(encoding="utf-8-sig").splitlines()
    i = 0
    while i < len(lineas) and lineas[i].startswith("#"):
        i += 1
    df = pd.read_csv(io.StringIO("\n".join(lineas[i:])), dtype=str).fillna("")
    return {r["openalex_id"]: {"veredicto": r["veredicto"], "nota": r["nota"]}
            for _, r in df.iterrows() if r.get("veredicto") not in (None, "", "pendiente")}


def _leer_crossref(ruta: Path) -> dict[str, dict]:
    """Evidencia de `openalex_cobertura_crossref.py`, si ya se corrió (V2-26 bis).

    Es evidencia adicional para leer, no una segunda opinión que se combine
    con la de OpenAlex: se muestra tal cual, sin fusionar veredictos.
    """
    if not ruta.exists():
        return {}
    df = pd.read_csv(ruta, dtype=str).fillna("")
    return {r["openalex_id"]: r.to_dict() for _, r in df.iterrows()}


def _bloque_crossref(xref: dict | None) -> str:
    """Caja de evidencia independiente de OpenAlex, o vacío si no se ha corrido
    `openalex_cobertura_crossref.py` o Crossref no tenía el DOI."""
    if not xref or xref.get("crossref_encontrado") not in ("True", True):
        return ""
    tipo = str(xref.get("crossref_tipo") or "")
    anio = str(xref.get("crossref_anio") or "")
    certeza = str(xref.get("crossref_certeza_autor") or "")
    autor = str(xref.get("crossref_autor") or "")
    afiliacion = str(xref.get("crossref_afiliacion") or "")

    etiqueta_certeza = {
        "unico": "autor identificado sin ambigüedad",
        "ambiguo": "varios autores comparten apellido — no se eligió entre ellos",
        "sin_match": "ningún autor de Crossref comparte apellido con el declarado",
    }.get(certeza, certeza)

    if afiliacion:
        cuerpo = (f'Crossref declara para <b>{htmlmod.escape(autor)}</b>: '
                  f'<b>{htmlmod.escape(afiliacion)}</b>')
    elif autor:
        cuerpo = (f'Crossref identifica a <b>{htmlmod.escape(autor)}</b> '
                  f'({htmlmod.escape(etiqueta_certeza)}), sin afiliación declarada')
    else:
        cuerpo = f'Crossref: {htmlmod.escape(etiqueta_certeza)}'

    return f"""
      <p class="xref{' hay-afiliacion' if afiliacion else ''}">
        <span class="etq">Evidencia independiente (Crossref{f', {htmlmod.escape(tipo)}' if tipo else ''}{f', {htmlmod.escape(anio)}' if anio else ''})</span><br>
        {cuerpo}
      </p>"""


def render_html(filas: pd.DataFrame) -> str:
    previas = _leer_previas(DECISIONES)
    crossref = _leer_crossref(CROSSREF)
    items: list[dict] = []
    cuerpo = ""
    for _, r in filas.iterrows():
        oid = str(r["openalex_id"])
        doi = str(r.get("doi") or "")
        titulo = str(r.get("titulo") or "(sin título)")
        anio = r.get("anio")
        anio = "" if pd.isna(anio) else str(int(anio))
        tipo = str(r.get("tipo") or "")
        citas = r.get("citas_openalex")
        citas = 0 if pd.isna(citas) else int(citas)
        autor = str(r.get("autor_uft") or "(no identificado)")
        institucion = str(r.get("institucion_declarada") or "")
        motivo = str(r.get("motivo") or "")

        items.append({"id": oid, "doi": doi, "previa": previas.get(oid)})

        doi_html = (f'<a href="https://doi.org/{htmlmod.escape(doi)}" target="_blank" '
                    f'rel="noopener">{htmlmod.escape(doi)}</a>' if doi
                    else '<em>sin DOI</em>')
        buscar = htmlmod.escape(f"{titulo} {autor} {doi} {tipo}".lower())

        cuerpo += f"""
    <article class="item" data-id="{htmlmod.escape(oid)}" data-decidido="0"
             data-buscar="{buscar}">
      <div class="meta">
        <span class="n">{citas} cita{'s' if citas != 1 else ''}</span>
        <span class="n">{htmlmod.escape(anio)}</span>
        <span class="n">{htmlmod.escape(tipo)}</span>
      </div>
      <h3>{htmlmod.escape(titulo)}</h3>
      <p class="ctx">
        Autor UFT según OpenAlex: <b>{htmlmod.escape(autor)}</b>
        {f' · declara: <b>{htmlmod.escape(institucion)}</b>' if institucion else ''}
        <br>DOI: <span class="mono">{doi_html}</span>
        <br><span class="mono">{htmlmod.escape(motivo)}</span>
      </p>{_bloque_crossref(crossref.get(oid))}
      <div class="dec">
        <button type="button" data-v="uft" aria-pressed="false">Sí, es UFT</button>
        <button type="button" data-v="error" aria-pressed="false">No, error de OpenAlex</button>
        <button type="button" data-v="tipo" aria-pressed="false">Tipo excluido a propósito</button>
        <input type="text" data-campo="nota" placeholder="Nota (opcional)">
      </div>
    </article>"""

    datos = _json_para_script(items)
    hoy = date.today().isoformat()
    n = len(filas)

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Revisión de cobertura OpenAlex (V2-26) — capa interna</title>
<style>{CSS}</style>
</head>
<body>
<header><div class="c">
  <h1>Brecha de cobertura: producción que OpenAlex ve y Scopus no</h1>
  <p>Capa interna · generado el {hoy} · {n} obras</p>
</div></header>

<div class="barra"><div class="c">
  <span class="avance" id="avance"></span>
  <input type="text" class="buscar" id="buscar" placeholder="Buscar título, autor, DOI…">
  <select id="filtro-estado">
    <option value="todos">Todos</option>
    <option value="pendientes">Sólo pendientes</option>
    <option value="revisados">Sólo revisados</option>
  </select>
  <button type="button" class="pri" id="exportar">Exportar decisiones (CSV)</button>
  <button type="button" id="limpiar">Borrar todo</button>
</div></div>

<main class="c">
  <div class="aviso">
    <strong>Esto NO modifica el universo publicado.</strong> Marcar «Sí, es UFT»
    no agrega la obra al corpus — ampliar el universo es una decisión de
    alcance aparte, explícita, nunca la consecuencia automática de esta
    revisión (<span class="mono">D-206</span>). Lo único que cambia es la
    columna <span class="mono">resolucion</span> de
    <span class="mono">internal/openalex_cobertura.csv</span>: deja
    constancia de que alguien miró el caso. Ordenado por citación —los más
    citados son los más fáciles de verificar primero. Donde aparece un
    recuadro verde «Evidencia independiente (Crossref)», es la afiliación que
    la propia publicación declaró —dato primario, no otra desambiguación de
    OpenAlex— y suele bastar para decidir sin abrir el DOI.
  </div>
  {cuerpo}
</main>
<footer><div class="c">
  Generado por <span class="mono">src/review/build_openalex_review.py</span>
  a partir de <span class="mono">internal/openalex_cobertura.csv</span>.
  Regenerable — no pierde respuestas ya exportadas a CSV. Exporte y aplique con
  <span class="mono">python3 src/review/apply_openalex_review.py</span>.
</div></footer>
<script>{JS.replace("__DATOS__", datos)}</script>
</body>
</html>
"""


def main() -> int:
    if not FUENTE.exists():
        sys.exit(f"Falta {FUENTE.relative_to(ROOT)}. Ejecute: "
                  "python3 src/enrich/openalex_cobertura.py")
    df = pd.read_csv(FUENTE, dtype=str)
    for col in ("anio", "citas_openalex"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.sort_values("citas_openalex", ascending=False, na_position="last")

    SALIDA.write_text(render_html(df), encoding="utf-8")

    pendientes = len(df) - len(_leer_previas(DECISIONES))
    con_evidencia_crossref = sum(
        1 for x in _leer_crossref(CROSSREF).values()
        if x.get("crossref_afiliacion")
    )
    print("=" * 78)
    print("REVISIÓN DE COBERTURA OPENALEX (V2-26)")
    print("=" * 78)
    print(f"  obras a revisar          : {len(df)}")
    print(f"  ya revisadas             : {len(df) - pendientes}")
    print(f"  pendientes               : {pendientes}")
    if CROSSREF.exists():
        print(f"  con evidencia Crossref   : {con_evidencia_crossref}")
    else:
        print("  evidencia Crossref       : no corrida — "
              "python3 src/enrich/openalex_cobertura_crossref.py")
    print(f"\n  OK · {SALIDA.relative_to(ROOT)}")
    print("       Abra el .html, marque cada caso, exporte el CSV, y aplíquelo con")
    print("       python3 src/review/apply_openalex_review.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
