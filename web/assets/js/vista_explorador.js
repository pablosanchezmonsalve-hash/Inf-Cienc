/* vista_explorador.js — el marcado del explorador. Sin DOM, como vista.js.

   Todo lo de aquí es una función de datos a cadena, para que el mismo código
   produzca el HTML en el BUILD (portada sin filtrar, legible sin JavaScript) y
   en el NAVEGADOR (al cambiar el recorte). Una segunda implementación para el
   repintado es la forma segura de que las dos versiones acaben divergiendo. */

import * as c from './core.js';
import * as X from './explorador.js';

/* ────────────────────────────────────────────────────────────── cabecera */

/** Cabecera compacta. La anterior ocupaba media pantalla con el título en tres
    líneas, un párrafo de cuatro y TRES cifras que el tablero repite justo
    debajo. En un explorador eso es ruido dos veces: gasta la pantalla que le
    toca al dato y enseña una cifra del total mientras el lector mira un
    recorte, que es la manera de que se lea la que no es.

    Queda el nombre, la procedencia —que no es decorativa: dice de dónde salen
    las cifras— y la explicación detrás de un control. */
export function cabecera(meta) {
  const v = meta.ventana || {};
  return `<div class="portada-id">
    <h1>Informe cienciométrico</h1>
    <p class="portada-sub">${c.escapar(meta.institucion || 'Universidad Finis Terrae')}
      · Scopus y SciVal · ${c.escapar(String(v.inicio ?? ''))}–${c.escapar(String(v.fin ?? ''))}</p>
  </div>
  <details class="metodo portada-metodo">
    <summary>Qué mide este informe y qué no</summary>
    <div class="metodo-cuerpo">
      <p>Producción, impacto, colaboración y estructura temática de la actividad
      científica indexada en <b>Scopus</b>, con las métricas normalizadas de
      <b>SciVal</b>. No mide la actividad académica total: sólo lo que esas dos
      fuentes recogen.</p>
      <p>Cada cifra declara <b>sobre cuántas publicaciones se calcula</b>, y esa
      base cambia según el indicador: no todas las publicaciones tienen
      métricas. Por eso dos cifras de esta página pueden no cuadrar entre sí sin
      que ninguna esté mal.</p>
    </div>
  </details>`;
}

/* ───────────────────────────────────────────────────────── cifras grandes */

/* El cuarto campo es el término del glosario. La ayuda contextual vivía en los
   KPI de la portada anterior y se habría perdido al sustituirlos: aquí es más
   necesaria todavía, porque una cifra recalculada sobre un recorte se
   malinterpreta con más facilidad que una del total. */
const FICHAS = [
  ['publicaciones', 'Publicaciones',        'publicaciones en el recorte', null],
  ['citas',         'Citas recibidas',      'sobre las que tienen métricas', 'Fecha de corte'],
  ['citas_por_pub', 'Citas por publicación', 'sobre las que tienen métricas', null],
  ['fwci_mediano',  'FWCI mediano',         '1,00 = promedio mundial', 'FWCI'],
  ['internacional', 'Colaboración internacional', 'sobre las que declaran país', 'Colaboración internacional'],
  ['autores',       'Autores UFT',          'formas de firma, no personas', 'Formas de firma'],
];

function fmt(f) {
  if (f.valor === null) return '—';
  const v = c.num(f.valor, f.decimales || 0);
  // El sufijo va en su propio elemento y más pequeño. Pegado a la cifra a
  // tamaño completo, «61,6 %» se partía en dos líneas y el símbolo caía solo
  // debajo del número.
  return v + (f.sufijo ? `<span class="ficha-sufijo">${f.sufijo.trim()}</span>` : '');
}

/** La fila de cifras. Cada una lleva SU denominador pegado (D-16): son bases
    distintas y presentarlas juntas sin decirlo invita a dividir una por otra. */
export function cifras(res) {
  return `<div class="tablero">${FICHAS.map(([k, etq, base, termino]) => {
    const f = res[k];
    return `<article class="ficha" data-k="${k}">
      <p class="ficha-valor" data-valor="${k}">${fmt(f)}</p>
      <h3 class="ficha-etq">${c.escapar(etq)}${termino ? c.botonAyuda(termino) : ''}</h3>
      <p class="ficha-base"><b data-base="${k}">${c.nf.format(f.base)}</b> ${c.escapar(base)}</p>
    </article>`;
  }).join('')}</div>`;
}

/* ─────────────────────────────────────────────────────────── el recorte */

/** La frase que dice qué se está mirando. Es obligatoria, no decorativa:
    quien llega por un enlace con filtros tiene que saber que lo que ve es un
    subconjunto, o leerá las cifras como si fueran las del total. */
export function estado(n, total, sel) {
  const partes = X.describir(sel);
  const filtrado = partes.length > 0;
  return `<p class="recorte-estado" role="status">
    <span class="recorte-n">${c.nf.format(n)}</span>
    <span class="recorte-de">de ${c.nf.format(total)} publicaciones</span>
    ${filtrado
      ? `<span class="recorte-que">${partes.map(p =>
          `<span class="recorte-chip">${c.escapar(p)}</span>`).join('')}</span>
         <button type="button" class="boton boton-limpiar" id="limpiar-recorte">Ver todo</button>`
      : `<span class="recorte-que recorte-todo">sin filtros · el informe completo</span>`}
  </p>`;
}

/** Los controles. Un `details` por dimensión: sin JavaScript se abren y se
    leen igual, que es la razón de usarlo en vez de un panel montado por
    guion. La primera dimensión va abierta para que el mecanismo se vea. */
export function controles(pubs, sel) {
  return `<div class="filtros-explorador">${X.DIMENSIONES.map(([clave, etiqueta], i) => {
    const cuenta = X.facetas(pubs, sel, clave);
    const elegidos = sel[clave] || [];
    const opciones = [...cuenta.entries()]
      .sort(clave === 'anio' ? (a, b) => a[0].localeCompare(b[0]) : (a, b) => b[1] - a[1]);
    return `<details class="dim" ${i === 0 || elegidos.length ? 'open' : ''}>
      <summary><span class="dim-nombre">${c.escapar(etiqueta)}</span>${
        elegidos.length ? `<span class="dim-n">${elegidos.length}</span>` : ''}</summary>
      <div class="dim-ops">${opciones.map(([valor, n]) => {
        const act = elegidos.includes(valor);
        return `<button type="button" class="chip${act ? ' chip-on' : ''}"
          data-dim="${clave}" data-valor="${c.escapar(valor)}"
          aria-pressed="${act}">${c.escapar(valor)}<span class="chip-n">${c.nf.format(n)}</span></button>`;
      }).join('')}</div>
    </details>`;
  }).join('')}</div>`;
}

/* ────────────────────────────────────────────────────────────── gráficos */

/* Cuatro cortes que responden al recorte. Cada uno declara su forma según la
   RELACIÓN del dato, no por costumbre: el año es una secuencia y va en
   vertical; los rankings de categorías largas van en horizontal. */
export const CORTES = [
  ['anio',        'Producción por año',    'barrasV'],
  ['qs_area',     'Áreas QS',              'barrasH'],
  ['unidad',      'Unidades académicas',   'barrasH'],
  ['tipo',        'Tipos documentales',    'barrasH'],
];

export function grafico(pubs_sel, clave, titulo, forma) {
  const datos = X.porDimension(pubs_sel, clave, { tope: forma === 'barrasH' ? 10 : 0 });
  if (!datos.length) {
    return `<p class="vacio">Ninguna publicación en este recorte.</p>`;
  }
  return forma === 'barrasV'
    ? c.barrasV(datos.map(d => ({ anio: d.valor, n: d.n })),
        { titulo, etiquetaX: 'anio', etiquetaY: 'n' })
    : c.barrasH(datos, { titulo });
}

export function cortes(pubs_sel) {
  return CORTES.map(([clave, titulo, forma]) => `
    <section class="corte" data-corte="${clave}">
      <h3>${c.escapar(titulo)}</h3>
      <div class="grafico">${grafico(pubs_sel, clave, titulo, forma)}</div>
    </section>`).join('');
}

/* ─────────────────────────────────────────────────────── página completa */

/** Todo el cuerpo del explorador. La usa el pre-renderizado con el conjunto
    completo y el navegador con el recorte vigente. */
export function explorador(pubs, sel) {
  const sub = X.recorte(pubs, sel);
  return {
    estado: estado(sub.length, pubs.length, sel),
    controles: controles(pubs, sel),
    cifras: cifras(X.resumen(sub)),
    cortes: cortes(sub),
  };
}
