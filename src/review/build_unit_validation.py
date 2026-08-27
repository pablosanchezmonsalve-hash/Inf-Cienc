"""Genera la hoja de validación institucional de unidades académicas (T-02).

QUÉ RESUELVE
    El vocabulario de unidades académicas está INFERIDO de cómo aparecen
    escritas en las afiliaciones, no tomado de un catálogo oficial: no existe
    uno disponible para el proyecto. Mientras siga inferido, el indicador `P-07`
    lleva confiabilidad baja y su advertencia lo declara.

    Resolverlo no es trabajo de código: alguien con el conocimiento
    institucional tiene que confirmarlo. Lo que sí es trabajo de código es
    dejar la pregunta hecha, con la evidencia delante, para que responderla
    cueste una lectura y un clic, no una investigación.

QUÉ PRODUCE
    Dos vistas del mismo contenido:
      · `internal/validacion_unidades.md`   — documento de lectura y archivo.
      · `internal/validacion_unidades.html` — herramienta interactiva: marca
        sí/no por unidad y por jerarquía, exporta un CSV, que
        `apply_unit_validation.py` aplica a `config/matching_rules.yml`.
    Mismo patrón que `build_review.py`/`revision_identidad.html` para la
    identidad de autor: una sola fuente de verdad para la pregunta, dos
    formas de responderla.

QUÉ NO HACE
    No propone nombres oficiales ni corrige los detectados. Lo que aparece es lo
    que dicen los datos.

CAPA
    Interna: incluye afiliaciones crudas como evidencia. No entra en `dist/`.

Uso:
    python3 src/review/build_unit_validation.py

Salida:
    internal/validacion_unidades.md
    internal/validacion_unidades.html
"""

from __future__ import annotations

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


def es(n: int) -> str:
    """Miles con punto, como se escribe en español."""
    return f"{n:,}".replace(",", ".")


def pct(x: float) -> str:
    """Decimal con coma. El documento lo lee una persona, no una máquina."""
    return f"{x:.1f}".replace(".", ",")


CSS = """
:root{--plano:#f1f5f6;--sup:#fff;--sup2:#eaf1f2;--tinta:#10222b;--tinta2:#4a5f68;
--tinta3:#5a6b71;--linea:#dbe6e8;--marca:#22577A;--accion:#1a6d78;--viva:#38A3A5;
--si:#2fa36b;--no:#cc3f5c;--radio:6px}
*{box-sizing:border-box}
body{margin:0;font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
background:var(--plano);color:var(--tinta)}
header{background:var(--marca);color:#fff;padding:1.1rem 0;border-bottom:2px solid var(--viva)}
.c{max-width:900px;margin:0 auto;padding:0 1.5rem}
h1{margin:0;font-size:1.15rem;font-weight:650}
header p{margin:.3rem 0 0;font-size:.82rem;color:#c7f9cc}
.barra{position:sticky;top:0;z-index:10;background:var(--sup);border-bottom:1px solid var(--linea);
padding:.7rem 0;font-size:.85rem}
.barra .c{display:flex;gap:1rem;align-items:center;flex-wrap:wrap}
.avance{font-variant-numeric:tabular-nums}
.avance b{color:var(--marca)}
button{font:inherit;font-size:.85rem;border-radius:4px;border:1px solid #bccdd2;
background:var(--sup);color:var(--tinta);padding:.35rem .6rem;cursor:pointer}
button.pri{background:var(--marca);color:#fff;border-color:var(--marca);font-weight:600}
main{padding:1.5rem 0 4rem}
h2.seccion{font-size:1rem;border-bottom:2px solid var(--viva);padding-bottom:.3rem;margin:2rem 0 1rem}
.item{background:var(--sup);border:1px solid var(--linea);border-radius:var(--radio);
padding:1rem 1.2rem;margin-bottom:.8rem}
.item[data-decidido="1"]{opacity:.55}
.item h3{margin:0 0 .2rem;font-size:.98rem}
.n{font-size:.68rem;text-transform:uppercase;letter-spacing:.06em;font-weight:700;
color:var(--tinta3);background:var(--sup2);border:1px solid var(--linea);
border-radius:999px;padding:.1rem .5rem;display:inline-block;margin-bottom:.3rem}
.ctx{font-size:.83rem;color:var(--tinta2);margin:.2rem 0 .8rem}
.mono{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.88em}
.dec{display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;
border-top:1px solid var(--linea);padding-top:.7rem}
.dec button[data-v]{border-width:1.5px}
.dec button[aria-pressed="true"][data-v="si"]{background:var(--si);color:#fff;border-color:var(--si)}
.dec button[aria-pressed="true"][data-v="no"]{background:var(--no);color:#fff;border-color:var(--no)}
.dec input{flex:1;min-width:170px;font:inherit;font-size:.83rem;padding:.35rem .55rem;
border:1px solid #bccdd2;border-radius:4px;background:var(--sup);color:var(--tinta)}
.dec input.correccion{display:none}
.item[data-v="no"] .dec input.correccion{display:block}
.aviso{background:#fdf6e7;border:1px solid #c8901a55;border-left:3px solid #c8901a;
border-radius:4px;padding:.7rem .9rem;font-size:.85rem;color:#6a4a05;margin-bottom:1.2rem}
footer{border-top:1px solid var(--linea);padding:1.5rem 0;font-size:.8rem;color:var(--tinta2)}
"""

JS = """
const ITEMS = __DATOS__;
const CLAVE = 'validacion_unidades_v1';
let dec = {};
try { dec = JSON.parse(localStorage.getItem(CLAVE) || '{}'); } catch (e) { dec = {}; }

/* Lo ya decidido viene del CSV del repositorio (si existe uno de una corrida
   anterior); lo de este navegador es trabajo en curso. Manda el navegador
   sólo donde hay una entrada suya. */
ITEMS.forEach(it => { if (it.previa && !dec[it.id]) dec[it.id] = { ...it.previa }; });

function guardar() {
  try { localStorage.setItem(CLAVE, JSON.stringify(dec)); } catch (e) {}
  pintarAvance();
}

function pintarAvance() {
  const n = Object.values(dec).filter(d => d && d.correcto).length;
  document.getElementById('avance').innerHTML =
    `<b>${n}</b> de ${ITEMS.length} respondidos · <b>${ITEMS.length - n}</b> pendientes`;
  document.querySelectorAll('.item').forEach(el => {
    const d = dec[el.dataset.id];
    el.dataset.decidido = (d && d.correcto) ? '1' : '0';
    el.dataset.v = (d && d.correcto) || '';
  });
}

document.addEventListener('click', e => {
  const b = e.target.closest('.dec button[data-v]');
  if (!b) return;
  const item = b.closest('.item');
  const id = item.dataset.id;
  const v = b.dataset.v;
  const actual = dec[id] || {};
  dec[id] = { ...actual, correcto: actual.correcto === v ? null : v };
  item.querySelectorAll('.dec button[data-v]').forEach(o =>
    o.setAttribute('aria-pressed', String(dec[id].correcto === o.dataset.v)));
  guardar();
});

document.addEventListener('input', e => {
  const campo = e.target.closest('.dec input[data-campo]');
  if (!campo) return;
  const id = campo.closest('.item').dataset.id;
  const clave = campo.dataset.campo;
  dec[id] = { ...(dec[id] || {}), [clave]: campo.value };
  try { localStorage.setItem(CLAVE, JSON.stringify(dec)); } catch (err) {}
});

document.getElementById('exportar').addEventListener('click', () => {
  const esc = v => `"${String(v ?? '').replace(/"/g, '""')}"`;
  const cab = [
    '# Validación de unidades académicas — revisión humana',
    '# Generado por internal/validacion_unidades.html',
    `# Exportado: ${new Date().toISOString().slice(0, 10)}`,
    '# correcto: si = el nombre/jerarquía tal como aparece es correcto ·',
    '#           no = corregir con el valor de la columna "correccion"',
  ].join('\\n');
  const cols = ['id', 'tipo', 'nombre', 'correcto', 'correccion', 'nota'];
  const filas = ITEMS.map(it => {
    const d = dec[it.id] || {};
    return [it.id, it.tipo, it.nombre, d.correcto || 'pendiente',
            d.correccion || '', d.nota || ''].map(esc).join(',');
  });
  entregar('unit_validation_decisions', '\\ufeff' + [cab, cols.join(','), ...filas].join('\\n'));
});

/* Misma entrega de dos vías que revision_identidad.html: archivo local por
   <a download>, o la capacidad `downloads` del anfitrión si la página se
   sirve dentro de un marco que la anula en silencio. */
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
  if (!confirm('Se borra lo respondido en ESTE navegador. Lo ya registrado en '
    + 'el CSV del repositorio no se toca. ¿Continuar?')) return;
  dec = {};
  ITEMS.forEach(it => { if (it.previa) dec[it.id] = { ...it.previa }; });
  try { localStorage.setItem(CLAVE, JSON.stringify(dec)); } catch (e) {}
  location.reload();
});

pintarAvance();
"""


def _leer_previas(ruta: Path) -> dict[str, dict]:
    """Decisiones de una corrida anterior de esta misma herramienta, si existe."""
    if not ruta.exists():
        return {}
    df = pd.read_csv(ruta, dtype=str, comment="#").fillna("")
    return {r["id"]: {"correcto": r["correcto"], "correccion": r["correccion"], "nota": r["nota"]}
            for _, r in df.iterrows() if r.get("correcto") not in (None, "", "pendiente")}


def render_html(detectadas, etiqueta_sin_dato: str, vocab: dict, jer: dict,
                 log: pd.DataFrame, total: int, sin_dato: int) -> str:
    import html as htmlmod

    previas = _leer_previas(ROOT / "internal" / "unit_validation_decisions.csv")
    items: list[dict] = []
    cuerpo_unidades = ""
    for nombre, n in detectadas.items():
        if nombre == etiqueta_sin_dato:
            continue
        iid = f"u-{nombre}"
        fila = log[log["unidad_academica"] == nombre].iloc[0]
        cruda = str(fila.get("afiliacion_declarada_raw", ""))[:220]
        vs = ", ".join(f"`{v}`" for v in vocab.get(nombre, []))
        items.append({"id": iid, "tipo": "unidad", "nombre": nombre,
                       "previa": previas.get(iid)})
        cuerpo_unidades += f"""
    <article class="item" data-id="{htmlmod.escape(iid)}" data-decidido="0">
      <span class="n">{es(n)} pares</span>
      <h3>{htmlmod.escape(nombre)}</h3>
      <p class="ctx">Evidencia: <span class="mono">{htmlmod.escape(cruda)}</span>
        {f'<br>Variantes ya reconocidas: {vs}' if vs else ''}</p>
      <div class="dec">
        <button type="button" data-v="si" aria-pressed="false">Sí, es correcto</button>
        <button type="button" data-v="no" aria-pressed="false">No, corregir</button>
        <input type="text" class="correccion" data-campo="correccion" placeholder="Nombre oficial correcto">
        <input type="text" data-campo="nota" placeholder="Nota (opcional)">
      </div>
    </article>"""

    cuerpo_jerarquia = ""
    for escuela, e in jer.items():
        iid = f"j-{escuela}"
        estado = "confirmada" if e.get("estado") == "confirmada" else "inferida de los datos"
        items.append({"id": iid, "tipo": "jerarquia", "nombre": escuela,
                       "previa": previas.get(iid)})
        cuerpo_jerarquia += f"""
    <article class="item" data-id="{htmlmod.escape(iid)}" data-decidido="0">
      <span class="n">{htmlmod.escape(estado)}</span>
      <h3>{htmlmod.escape(escuela)} → {htmlmod.escape(e['facultad'])}</h3>
      <p class="ctx">¿Esta escuela suma su producción a esa facultad?</p>
      <div class="dec">
        <button type="button" data-v="si" aria-pressed="false">Sí, es correcto</button>
        <button type="button" data-v="no" aria-pressed="false">No, corregir</button>
        <input type="text" class="correccion" data-campo="correccion" placeholder="Facultad correcta">
        <input type="text" data-campo="nota" placeholder="Nota (opcional)">
      </div>
    </article>"""

    datos = json.dumps(items, ensure_ascii=False)
    hoy = date.today().isoformat()

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Validación de unidades académicas — capa interna</title>
<style>{CSS}</style>
</head>
<body>
<header><div class="c">
  <h1>Validación de unidades académicas</h1>
  <p>Capa interna · generado el {hoy} · {len(detectadas) - 1} unidades ·
     {len(jer)} jerarquías escuela→facultad</p>
</div></header>

<div class="barra"><div class="c">
  <span class="avance" id="avance"></span>
  <button type="button" class="pri" id="exportar">Exportar respuestas (CSV)</button>
  <button type="button" id="limpiar">Borrar todo</button>
</div></div>

<main class="c">
  <div class="aviso">
    <strong>Esta página no decide nada por sí sola.</strong>
    Marque sí/no por cada unidad y cada jerarquía; las respuestas se guardan
    en este navegador mientras trabaja. <strong>Expórtelas a CSV</strong> y
    guarde el archivo como
    <span class="mono">internal/unit_validation_decisions.csv</span>, luego
    corra <span class="mono">python3 src/review/apply_unit_validation.py</span>
    para aplicarlas a <span class="mono">config/matching_rules.yml</span>.
    Nada de lo que marque aquí modifica el sitio por sí solo.
  </div>

  <h2 class="seccion">1 · Unidades detectadas ({len(detectadas) - 1})</h2>
  <p class="ctx">Sobre {es(total)} apariciones firma × publicación de la ventana;
    {es(sin_dato)} ({pct(100 * sin_dato / total)} %) no permiten deducir unidad
    y quedan fuera de esta lista — no se imputan.</p>
  {cuerpo_unidades}

  <h2 class="seccion">2 · Jerarquía escuela → facultad ({len(jer)})</h2>
  <p class="ctx">Una jerarquía equivocada mueve publicaciones de una facultad a
    otra: es la parte más sensible de esta validación.</p>
  {cuerpo_jerarquia}
</main>
<footer><div class="c">
  Generado por <span class="mono">src/review/build_unit_validation.py</span>.
  Regenerable — no pierde respuestas ya exportadas a CSV.
</div></footer>
<script>{JS.replace("__DATOS__", datos)}</script>
</body>
</html>
"""


def main() -> int:
    log_path = ROOT / "internal" / "matching_log.csv"
    if not log_path.exists():
        sys.exit("Falta internal/matching_log.csv. Ejecute: python3 src/audit/run_all.py")

    log = pd.read_csv(log_path, dtype=str)
    etiqueta_sin_dato = c.MATCHING["unidad_academica"]["etiqueta_sin_dato"]
    u = log["unidad_academica"].fillna(etiqueta_sin_dato)
    detectadas = u.value_counts()
    total = len(log)
    sin_dato = int(detectadas.get(etiqueta_sin_dato, 0))

    vocab = c.MATCHING["unidad_academica"]["vocabulario"]
    jer = c.MATCHING["unidad_academica"].get("jerarquia", {})

    L = [
        "# Validación institucional de unidades académicas",
        "",
        f"**Generado** el {date.today().isoformat()} por "
        "`src/review/build_unit_validation.py`. Regenerable.",
        "",
        "## Qué se pide",
        "",
        "El informe bibliométrico agrupa la producción por unidad académica. "
        "Esos nombres **no vienen de un catálogo oficial**: están deducidos de "
        "cómo aparecen escritos en las afiliaciones de Scopus, porque no había "
        "un catálogo disponible al construir la plataforma.",
        "",
        "Mientras sigan sin validar, el indicador de producción por unidad se "
        "publica con confiabilidad baja y una advertencia que lo declara. "
        "Para retirar esa advertencia hacen falta tres cosas:",
        "",
        "1. **Confirmar o corregir** el nombre oficial de cada unidad listada.",
        "2. **Señalar las que no existen** o cambiaron de nombre en el período.",
        "3. **Confirmar a qué facultad pertenece cada escuela** (segunda tabla).",
        "",
        "No hace falta responder en ningún formato especial: basta con marcar "
        "sobre este documento.",
        "",
        "---",
        "",
        "## 1. Unidades detectadas",
        "",
        # «Apariciones» y no «pares»: `total` son filas del log, y una firma
        # puede ocupar varias posiciones de un mismo trabajo. Los pares
        # distintos son menos, y llamar igual a las dos cifras es el error
        # silencioso que este proyecto persigue.
        f"Sobre **{es(total)}** apariciones firma × publicación de la ventana "
        f"{c.INSTITUTION['ventana_temporal']['anio_inicio']}–"
        f"{c.INSTITUTION['ventana_temporal']['anio_fin']}. "
        f"**{es(sin_dato)}** ({pct(100 * sin_dato / total)} %) no permiten deducir "
        "unidad y se declaran como «"
        f"{etiqueta_sin_dato}»: no se imputan.",
        "",
        "| Unidad como aparece en el informe | Pares | ¿Nombre oficial correcto? | Corrección |",
        "|---|---:|---|---|",
    ]

    for nombre, n in detectadas.items():
        if nombre == etiqueta_sin_dato:
            continue
        L.append(f"| {nombre} | {es(n)} | ☐ sí  ☐ no | |")

    L += [
        "",
        "### Variantes de escritura que se agrupan bajo cada nombre",
        "",
        "El sistema reconoce estas formas y las lleva al nombre canónico. Si "
        "falta alguna variante que use la universidad, indíquela.",
        "",
        "| Nombre canónico | Variantes reconocidas |",
        "|---|---|",
    ]
    for canonico, variantes in vocab.items():
        vs = ", ".join(f"`{v}`" for v in variantes)
        L.append(f"| {canonico} | {vs} |")

    L += [
        "",
        "---",
        "",
        "## 2. Jerarquía escuela → facultad",
        "",
        "El informe suma la producción de cada escuela a su facultad. Una "
        "jerarquía equivocada mueve publicaciones de una facultad a otra, así "
        "que es la parte más sensible de esta validación.",
        "",
        "| Escuela | Se suma a | Estado actual | ¿Correcto? | Corrección |",
        "|---|---|---|---|---|",
    ]
    for escuela, e in jer.items():
        estado = ("**confirmada**" if e.get("estado") == "confirmada"
                  else "*inferida de los datos*")
        L.append(f"| {escuela} | {e['facultad']} | {estado} | ☐ sí  ☐ no | |")

    inferidas = [k for k, v in jer.items() if v.get("estado") != "confirmada"]
    L += [
        "",
        f"**{len(inferidas)} de {len(jer)} jerarquías están inferidas**, no "
        "confirmadas. Son las que más importa revisar.",
        "",
        "¿Falta alguna escuela o instituto que deba sumar a una facultad y no "
        "aparezca en esta tabla?",
        "",
        "---",
        "",
        "## 3. Evidencia: cómo aparece cada unidad en el origen",
        "",
        "Una afiliación real por unidad, tal como la entrega Scopus. Sirve para "
        "juzgar si el nombre deducido es razonable.",
        "",
    ]
    for nombre, n in detectadas.items():
        if nombre == etiqueta_sin_dato:
            continue
        fila = log[log["unidad_academica"] == nombre].iloc[0]
        cruda = str(fila.get("afiliacion_declarada_raw", ""))[:200]
        L += [f"**{nombre}** ({es(n)} pares)", "", f"> {cruda}", ""]

    L += [
        "---",
        "",
        "## Qué pasa cuando esto vuelva respondido",
        "",
        "Las correcciones entran en `config/matching_rules.yml` —vocabulario y "
        "jerarquía— y el estado de cada jerarquía pasa de `inferida` a "
        "`confirmada`. Con eso, el indicador de producción por unidad puede "
        "subir su confiabilidad y perder la advertencia sobre vocabulario no "
        "validado. **No requiere reescribir nada del sistema.**",
        "",
        "Lo que **no** cambia: la cobertura. "
        f"{es(sin_dato)} pares seguirán sin unidad deducible porque su afiliación "
        "no la menciona, y seguirán declarándose como «"
        f"{etiqueta_sin_dato}» en vez de imputarse.",
    ]

    salida = ROOT / "internal" / "validacion_unidades.md"
    salida.write_text("\n".join(L) + "\n", encoding="utf-8")

    salida_html = ROOT / "internal" / "validacion_unidades.html"
    salida_html.write_text(
        render_html(detectadas, etiqueta_sin_dato, vocab, jer, log, total, sin_dato),
        encoding="utf-8")

    print("=" * 78)
    print("HOJA DE VALIDACIÓN DE UNIDADES ACADÉMICAS")
    print("=" * 78)
    print(f"  unidades detectadas   : {len(detectadas) - 1}")
    print(f"  jerarquías declaradas : {len(jer)} ({len(inferidas)} inferidas)")
    print(f"  cobertura             : {pct(100 * (total - sin_dato) / total)} % "
          f"({es(sin_dato)} pares sin unidad deducible)")
    print(f"\n  OK · {salida.relative_to(ROOT)} (documento de lectura)")
    print(f"  OK · {salida_html.relative_to(ROOT)} (herramienta interactiva)")
    print("       Abra el .html, marque sí/no, exporte el CSV, y aplíquelo con")
    print("       python3 src/review/apply_unit_validation.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
