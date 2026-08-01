/* core.js — carga de datos, formato, gráficos y ayuda contextual.
   Sin dependencias externas. Los gráficos se dibujan como SVG inline: evita
   cargar una librería desde un CDN, cosa que el sitio no puede permitirse. */

/* Ruta relativa a la página. El sitio se sirve desde `dist/`, que ensambla
   src/build/06_assemble_site.py: las páginas quedan en la raíz y los
   artefactos bajo ./data/. Servir `web/` directamente no funciona a propósito:
   sin los datos ensamblados el sitio no debe aparentar estar completo. */
const RUTA_DATOS = 'data';

/* --------------------------------------------------------------- datos */
const cache = new Map();

export async function cargar(nombre) {
  if (cache.has(nombre)) return cache.get(nombre);
  const p = fetch(`${RUTA_DATOS}/${nombre}`).then(r => {
    if (!r.ok) throw new Error(`No se pudo cargar ${nombre} (${r.status})`);
    return r.json();
  });
  cache.set(nombre, p);
  return p;
}

/* -------------------------------------------------------------- formato */
export const nf = new Intl.NumberFormat('es-CL');

export function num(v, dec = 0) {
  if (v === null || v === undefined) return null;
  return new Intl.NumberFormat('es-CL', {
    minimumFractionDigits: dec, maximumFractionDigits: dec
  }).format(v);
}

/** Ausencia de dato y cero nunca se ven igual (decisión D-24). */
export function celda(v, dec = 0) {
  if (v === null || v === undefined || v === '')
    return '<span class="sin-dato-txt">Sin dato declarado</span>';
  return typeof v === 'number' ? num(v, dec) : escapar(v);
}

/** Un año es una etiqueta, no una cantidad: nunca lleva separador de millar.
    Con el formato numérico de es-CL, 2025 se imprimía «2.025». */
export function anio(v) {
  if (v === null || v === undefined || v === '')
    return '<span class="sin-dato-txt">Sin dato declarado</span>';
  return escapar(String(v));
}

export function escapar(s) {
  return String(s).replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

/* ---------------------------------------------------------------- tema */

/* Tres estados explícitos, no dos: «automático» sigue al sistema operativo y es
   el de partida. La elección se recuerda; sin elección, no se escribe nada y el
   sitio respeta la preferencia del sistema. */
const TEMAS = [
  ['auto', 'Auto', 'M12 3v1m0 16v1m9-9h-1M4 12H3m15.5-6.5-.7.7M6.2 17.8l-.7.7m12.6 0-.7-.7M6.2 6.2l-.7-.7M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z'],
  ['claro', 'Claro', 'M12 4v1m0 14v1m8-8h-1M5 12H4m13.7-5.7-.7.7M6.9 17.1l-.7.7m11.5 0-.7-.7M6.9 6.9l-.7-.7M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7z'],
  ['oscuro', 'Oscuro', 'M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5z'],
];

function aplicarTema(t) {
  if (t === 'auto') document.documentElement.removeAttribute('data-tema');
  else document.documentElement.setAttribute('data-tema', t);
  try { t === 'auto' ? localStorage.removeItem('tema') : localStorage.setItem('tema', t); } catch { /* modo privado */ }
  document.querySelectorAll('.tema button').forEach(b =>
    b.setAttribute('aria-pressed', String(b.dataset.tema === t)));
}

/* Se aplica antes de pintar para no mostrar un destello del tema equivocado. */
export function temaInicial() {
  try {
    const t = localStorage.getItem('tema');
    if (t) document.documentElement.setAttribute('data-tema', t);
    return t || 'auto';
  } catch { return 'auto'; }
}

/* ------------------------------------------------------------ cabecera */
export async function montarCabecera(paginaActual) {
  const meta = await cargar('meta.json');
  const paginas = [
    ['index.html', 'Portada'],
    ['produccion.html', 'Producción'],
    ['impacto.html', 'Impacto'],
    ['colaboracion.html', 'Colaboración'],
    ['tematica.html', 'Áreas temáticas'],
    ['autores.html', 'Autores'],
    ['publicaciones.html', 'Publicaciones'],
    ['metodologia.html', 'Metodología'],
  ];
  const nav = paginas.map(([href, txt]) =>
    `<a href="${href}"${href === paginaActual ? ' aria-current="page"' : ''}>${txt}</a>`).join('');

  const actual = temaInicial();
  const selectorTema = `<div class="tema" role="group" aria-label="Tema de color">${
    TEMAS.map(([id, txt, d]) => `<button type="button" data-tema="${id}"
      aria-pressed="${String(id === actual)}" title="Tema ${txt.toLowerCase()}">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="${d}" stroke-linecap="round" stroke-linejoin="round"/></svg>
      ${txt}</button>`).join('')}</div>`;

  document.getElementById('cabecera').innerHTML = `
    <div class="contenedor">
      <div class="marca-fila">
        <div class="marca">
          <strong>${escapar(meta.institucion)}</strong>
          <span>${escapar(meta.titulo_plataforma)}</span>
        </div>
        ${selectorTema}
      </div>
      <nav class="nav" aria-label="Secciones">${nav}</nav>
    </div>`;

  document.querySelectorAll('.tema button').forEach(b =>
    b.addEventListener('click', () => aplicarTema(b.dataset.tema)));

  document.getElementById('vigencia').innerHTML = `
    <div class="contenedor">
      <span>Datos: <strong>${meta.fuentes.join(' · ')}</strong></span>
      <span class="sep" aria-hidden="true">|</span>
      <span>Ventana <strong>${meta.ventana.inicio}–${meta.ventana.fin}</strong></span>
      <span class="sep" aria-hidden="true">|</span>
      <span>Citas al <strong>${meta.fecha_corte_citas}</strong></span>
      <span class="sep" aria-hidden="true">|</span>
      <a href="metodologia.html">Cómo leer estos indicadores</a>
    </div>`;

  const pie = document.getElementById('pie');
  if (pie) pie.innerHTML = `
    <div class="contenedor">
      <p>${escapar(meta.advertencia_global)}
      Ver <a href="metodologia.html">metodología y limitaciones</a>.</p>
      <p>Universo: ${nf.format(meta.denominadores.universo_total)} publicaciones ·
      ${nf.format(meta.denominadores.con_metricas)} con métricas ·
      ${nf.format(meta.denominadores.con_autoria_detallada)} con autoría detallada.
      Build ${meta.fecha_build}.</p>
    </div>`;
  return meta;
}

/* ---------------------------------------------------------------- notas */
export function nota(n) {
  if (!n) return '';
  if (n.destacada) {
    return `<p class="nota-destacada"><b>Advertencia metodológica</b>${escapar(n.texto)}</p>`;
  }
  return `<p class="nota">${escapar(n.texto)}</p>`;
}

/* --------------------------------------------------- ayuda contextual */
let glosario = null;

export async function montarAyuda() {
  if (!glosario) glosario = (await cargar('glossary.json')).entradas;
  const panel = document.createElement('div');
  panel.className = 'ayuda-panel';
  panel.hidden = true;
  panel.setAttribute('role', 'tooltip');
  document.body.appendChild(panel);

  const mostrar = (btn) => {
    const termino = btn.dataset.ayuda.toLowerCase();
    const e = glosario.find(g => g.slug.includes(termino) || g.termino.toLowerCase().includes(termino));
    if (!e) return;
    panel.innerHTML = `<strong>${escapar(e.termino)}</strong><br>${escapar(e.corto)}
      <br><a href="metodologia.html#${e.slug}">Ver definición completa</a>`;
    panel.hidden = false;
    const r = btn.getBoundingClientRect();
    panel.style.top = `${window.scrollY + r.bottom + 6}px`;
    panel.style.left = `${Math.max(8, Math.min(window.scrollX + r.left - 40,
      window.innerWidth - panel.offsetWidth - 12))}px`;
  };
  const ocultar = () => { panel.hidden = true; };

  // Accesible por foco y no sólo por hover: si sólo respondiera al puntero,
  // la ayuda no existiría por teclado ni en móvil.
  document.addEventListener('mouseover', e => {
    const b = e.target.closest('[data-ayuda]'); if (b) mostrar(b);
  });
  document.addEventListener('mouseout', e => {
    if (e.target.closest('[data-ayuda]')) ocultar();
  });
  document.addEventListener('focusin', e => {
    const b = e.target.closest('[data-ayuda]'); if (b) mostrar(b);
  });
  document.addEventListener('focusout', ocultar);
  document.addEventListener('keydown', e => { if (e.key === 'Escape') ocultar(); });
}

export function botonAyuda(termino) {
  return `<button class="ayuda" type="button" data-ayuda="${escapar(termino)}"
    aria-label="Qué significa ${escapar(termino)}">?</button>`;
}

/* ------------------------------------------------------------ gráficos */

/* Una categoría que representa AUSENCIA de dato nunca se pinta como una que
   representa una medición (decisión D-09). El nombre de esas categorías lo fija
   el build, así que la lista vive aquí y no se adivina por color. */
const SIN_DATO = /^(sin dato|no determinad|sin declarar|desconocid)/i;
export const esSinDato = v => SIN_DATO.test(String(v).trim());

/* Orden fijo de series. Nunca se cicla ni se reasigna según el ranking: el
   color sigue a la entidad, no a su posición.

   Son SEIS, no ocho: la paleta se validó a seis ranuras y añadir una séptima
   obligaría a meter un tono en la franja que ya ocupan otros. Más allá de seis
   entidades, lo correcto es agrupar en «Otras» o separar en varios gráficos,
   no generar un color nuevo. */
export const SERIES = Array.from({ length: 6 }, (_, i) => `var(--serie-${i + 1})`);

/* Rampa ordinal: un solo tono en cuatro pasos. Para escalas ORDENADAS
   (cuartiles, tramos). Cuatro tonos distintos afirmarían que Q1 y Q4 son
   categorías sin relación, cuando son posiciones de una misma escala. */
const ORDINAL = ['var(--ord-1)', 'var(--ord-2)', 'var(--ord-3)', 'var(--ord-4)'];

/** Color de una barra.

    `escala` distingue los tres casos que el color puede estar codificando:
      - null       una sola serie. El caso por defecto, y el correcto para un
                   ranking por volumen: colorear por posición haría que el color
                   siguiera al rank y repintara los supervivientes al filtrar.
      - 'serie'    entidades distintas sin orden entre sí.
      - 'ordinal'  posiciones de una escala ordenada.
    La ausencia de dato ignora las tres y siempre sale gris (decisión D-09). */
function colorDe(d, i, escala) {
  if (esSinDato(d.valor)) return 'var(--sin-dato)';
  if (escala === 'ordinal') return ORDINAL[Math.min(i, ORDINAL.length - 1)];
  if (escala === 'serie') return SERIES[i % SERIES.length];
  return 'var(--serie-1)';
}

/* Ancho aproximado de un texto a 11px en la fuente de sistema. No hay forma de
   medir dentro de una cadena SVG que aún no está en el documento, y el error de
   una estimación es preferible a que la etiqueta se salga del lienzo. */
const anchoTexto = (s, px = 11) => String(s).length * px * 0.58;

/** Recorta una etiqueta al ancho disponible, con puntos suspensivos. */
function recortar(txt, maxPx, px = 11) {
  const s = String(txt);
  if (anchoTexto(s, px) <= maxPx) return s;
  const maxCar = Math.max(4, Math.floor(maxPx / (px * 0.58)) - 1);
  return s.slice(0, maxCar).trimEnd() + '…';
}

let idGrafico = 0;

/** Barras horizontales. Elegidas cuando las etiquetas son largas o muchas. */
export function barrasH(datos, {
  alto = 26, escala = null, sufijo = '', ancho = 680, cuotaValida = false,
  titulo = '',
} = {}) {
  if (!datos.length) return '<p class="vacio">Sin datos para mostrar.</p>';
  const max = Math.max(...datos.map(d => d.n), 1);

  // El ancho del lienzo se declara según el contexto. El SVG se escala al
  // contenedor, así que un lienzo de 680 dentro de una columna de 330 reduce el
  // texto a la mitad y lo vuelve ilegible: en una tarjeta estrecha se pide un
  // lienzo estrecho, no un escalado.
  //
  // La columna de etiquetas se dimensiona con el contenido real y se acota a un
  // tercio del lienzo. Antes era fija en 210 px y los nombres largos se salían
  // del viewBox por la izquierda, apareciendo cortados por el lado equivocado.
  const anchoValor = 56;
  // En un lienzo estrecho la etiqueta puede ocupar una fracción mayor: si no,
  // no cabe ni una palabra y la barra gana un espacio que no necesita.
  const anchoEtiqueta = Math.min(
    Math.max(96, Math.ceil(Math.max(...datos.map(d => anchoTexto(d.valor)))) + 14),
    Math.round(ancho * (ancho < 420 ? 0.44 : 0.34)));
  const anchoPista = ancho - anchoEtiqueta - anchoValor;
  const total = datos.length * alto + 10;
  const id = `g${++idGrafico}`;

  /* Cuota sobre el total mostrado. Se omite cuando las barras no son partes de
     un total —multivaluados, umbrales encajados, rankings recortados—: ahí un
     porcentaje sería una afirmación falsa, no una ayuda. */
  const sumaBarras = datos.reduce((s, d) => s + d.n, 0);
  const cuota = d => (cuotaValida && sumaBarras
    ? `${(100 * d.n / sumaBarras).toFixed(1).replace('.', ',')} % de lo mostrado` : '');

  const filas = datos.map((d, i) => {
    const y = i * alto;
    const w = Math.max(2, anchoPista * (d.n / max));
    const etq = recortar(d.valor, anchoEtiqueta - 14);
    const cy = y + alto / 2;
    const nota = d.nota || cuota(d);
    return `<g class="marca" tabindex="0" role="listitem"
        aria-label="${escapar(d.valor)}: ${nf.format(d.n)}${sufijo}"
        data-tip="${escapar(d.valor)}" data-tip-v="${nf.format(d.n)}${sufijo}"
        ${nota ? `data-tip-n="${escapar(nota)}"` : ''}>
      <text x="${anchoEtiqueta - 10}" y="${cy + 3.5}" text-anchor="end">${escapar(etq)}</text>
      <rect class="barra" fill="${colorDe(d, i, escala)}" x="${anchoEtiqueta}" y="${y + 6}"
        width="${w}" height="${alto - 12}" rx="4"/>
      <text class="valor" x="${anchoEtiqueta + w + 7}" y="${cy + 3.5}">${nf.format(d.n)}${sufijo}</text>
    </g>`;
  }).join('');

  // La etiqueta accesible nombra el INDICADOR, no la forma del gráfico: cinco
  // «gráfico de barras horizontales» seguidos no le dicen nada a quien navega
  // con lector de pantalla.
  const etq = titulo ? `${titulo} — gráfico de barras, ${datos.length} categorías`
                     : `Gráfico de barras horizontales, ${datos.length} categorías`;
  return `<div class="grafico"><svg class="chart" id="${id}" viewBox="0 0 ${ancho} ${total}"
    role="list" aria-label="${escapar(etq)}">${filas}</svg></div>`;
}

/** Barras verticales. Para series anuales cortas: 3 años no son una línea. */
export function barrasV(datos, {
  etiquetaX = 'anio', etiquetaY = 'n', referencia = null,
  refEtiqueta = '', decimales = 0, ancho = 680, alto = 260, titulo = '',
} = {}) {
  if (!datos.length) return '<p class="vacio">Sin datos para mostrar.</p>';
  const mIzq = 52, mDer = 16, mAb = 38, mArr = 26;
  const vals = datos.map(d => d[etiquetaY]).filter(v => v !== null && v !== undefined);
  const max = Math.max(...vals, referencia || 0) * 1.18 || 1;
  const bw = (ancho - mIzq - mDer) / datos.length;
  const base = alto - mAb;
  const y = v => mArr + (base - mArr) * (1 - v / max);

  // Rejilla recesiva con tres marcas: da escala sin competir con las barras.
  const pasos = [0, max / 2, max];
  // El cero se rotula «0», no «0,0»: un decimal en el origen sugiere una
  // precisión que la marca de escala no tiene.
  const tick = v => (v === 0 ? '0' : num(v, max < 10 ? 1 : 0));
  const red = pasos.map(v => `
    <line class="red" x1="${mIzq}" x2="${ancho - mDer}" y1="${y(v)}" y2="${y(v)}"/>
    <text class="tick" x="${mIzq - 8}" y="${y(v) + 3.5}" text-anchor="end">${tick(v)}</text>`
  ).join('');

  // Barras finas: como mucho 56 px, y nunca más de la mitad del hueco.
  const w = Math.min(56, bw * 0.5);
  const barras = datos.map((d, i) => {
    const v = d[etiquetaY];
    const x = mIzq + i * bw + (bw - w) / 2;
    if (v === null || v === undefined) {
      return `<g class="marca" role="listitem" aria-label="${escapar(String(d[etiquetaX]))}: sin dato">
        <text class="tick" x="${x + w / 2}" y="${base - 8}" text-anchor="middle">sin dato</text>
        <text x="${x + w / 2}" y="${base + 18}" text-anchor="middle">${escapar(String(d[etiquetaX]))}</text>
      </g>`;
    }
    const yy = y(v);
    return `<g class="marca" tabindex="0" role="listitem"
        aria-label="${escapar(String(d[etiquetaX]))}: ${num(v, decimales)}"
        data-tip="${escapar(String(d[etiquetaX]))}" data-tip-v="${num(v, decimales)}"
        ${d.nota ? `data-tip-n="${escapar(d.nota)}"` : ''}>
      <rect class="barra" x="${x}" y="${yy}" width="${w}" height="${Math.max(2, base - yy)}" rx="4"/>
      <text class="valor" x="${x + w / 2}" y="${yy - 7}" text-anchor="middle">${num(v, decimales)}</text>
      <text x="${x + w / 2}" y="${base + 18}" text-anchor="middle">${escapar(String(d[etiquetaX]))}</text>
    </g>`;
  }).join('');

  // La etiqueta de referencia va sobre la línea y alineada a la derecha, pero
  // sin invadir la última barra: se sube un poco cuando queda muy arriba.
  const ref = referencia !== null ? `
    <line class="ref" x1="${mIzq}" x2="${ancho - mDer}" y1="${y(referencia)}" y2="${y(referencia)}"/>
    <text class="ref-etq" x="${ancho - mDer}" y="${Math.max(12, y(referencia) - 7)}"
      text-anchor="end">${escapar(refEtiqueta || String(referencia))}</text>` : '';

  const etq = titulo ? `${titulo} — gráfico de barras por año, ${datos.length} años`
                     : `Gráfico de barras verticales, ${datos.length} valores`;
  return `<div class="grafico"><svg class="chart" viewBox="0 0 ${ancho} ${alto}"
    role="list" aria-label="${escapar(etq)}">
    ${red}${ref}${barras}
    <line class="eje" x1="${mIzq}" x2="${ancho - mDer}" y1="${base}" y2="${base}"/>
  </svg></div>`;
}

/** Anillo. Reservado a proporciones binarias, que es donde se lee bien. */
export function anillo(datos, { titulo = '' } = {}) {
  const total = datos.reduce((s, d) => s + d.n, 0) || 1;
  const r = 58, grosor = 22, c = 2 * Math.PI * r;
  let offset = 0;
  const color = (d, i) => colorDe(d, i, 'serie');

  const arcos = datos.map((d, i) => {
    // Un hueco de 2 px de superficie entre segmentos: separa sin inventar color.
    const len = Math.max(0, c * (d.n / total) - 2);
    const seg = `<circle r="${r}" cx="72" cy="72" fill="none" stroke="${color(d, i)}"
      stroke-width="${grosor}" stroke-linecap="butt"
      stroke-dasharray="${len} ${c - len}" stroke-dashoffset="${-offset}"
      transform="rotate(-90 72 72)"><title>${escapar(d.valor)}: ${nf.format(d.n)}</title></circle>`;
    offset += c * (d.n / total);
    return seg;
  }).join('');

  const mayor = datos.reduce((a, b) => (b.n > a.n ? b : a), datos[0]);
  const centro = `
    <text x="72" y="68" text-anchor="middle" class="valor" style="font-size:20px">
      ${(100 * mayor.n / total).toFixed(1).replace('.', ',')} %</text>
    <text x="72" y="85" text-anchor="middle" style="font-size:10px">${escapar(recortar(mayor.valor, 92, 10))}</text>`;

  const leyenda = datos.map((d, i) =>
    `<div><span class="punto" style="background:${color(d, i)}"></span>${escapar(d.valor)}:
     <strong>${nf.format(d.n)}</strong> (${(100 * d.n / total).toFixed(1).replace('.', ',')} %)</div>`).join('');

  return `<div style="display:flex;gap:1.5rem;align-items:center;flex-wrap:wrap">
    <svg class="chart" viewBox="0 0 144 144" style="width:144px;flex:none" role="img"
      aria-label="${escapar(titulo ? titulo + ' — gráfico de anillo' : 'Gráfico de anillo')}"
      >${arcos}${centro}</svg>
    <div class="leyenda" style="display:grid;gap:.4rem">${leyenda}</div></div>`;
}

/* ------------------------------------------------------ tooltip común */

/* Un gráfico HTML es interactivo por naturaleza: `<title>` sólo aparece tras
   una pausa larga del puntero y no existe por teclado. Este panel responde a
   ambos. Se instala una vez por página y sirve a todas las marcas. */
export function montarTooltip() {
  const tip = document.createElement('div');
  tip.className = 'tip';
  tip.hidden = true;
  tip.setAttribute('role', 'tooltip');
  document.body.appendChild(tip);

  let activa = null;

  /* Resaltar es atenuar el resto. Señalar una barra sin apagar las demás no
     dirige la mirada: sólo añade un borde que hay que buscar. La atenuación se
     aplica en el SVG que contiene la marca, no en la página, para que dos
     gráficos de la misma pantalla no se interfieran. */
  const resaltar = (m) => {
    if (activa === m) return;
    apagar();
    activa = m;
    m.classList.add('activa');
    m.ownerSVGElement?.classList.add('hay-foco');
  };
  const apagar = () => {
    if (!activa) return;
    activa.classList.remove('activa');
    activa.ownerSVGElement?.classList.remove('hay-foco');
    activa = null;
  };

  const mostrar = (el, x, y) => {
    resaltar(el);
    tip.innerHTML = `<span class="tip-t">${el.dataset.tip}</span>
      <span class="tip-v">${el.dataset.tipV}</span>
      ${el.dataset.tipN ? `<span class="tip-n">${el.dataset.tipN}</span>` : ''}`;
    tip.hidden = false;
    const r = tip.getBoundingClientRect();
    // Se coloca arriba a la derecha del puntero, y salta abajo o a la izquierda
    // cuando no cabe: un tooltip recortado por el borde no informa de nada.
    const izq = Math.min(Math.max(8, x + 14), window.innerWidth - r.width - 10);
    const arr = y - r.height - 12 < 8 ? y + 20 : y - r.height - 12;
    tip.style.left = `${izq}px`;
    tip.style.top = `${arr}px`;
  };
  const ocultar = () => { tip.hidden = true; apagar(); };

  document.addEventListener('pointermove', e => {
    const m = e.target.closest?.('[data-tip]');
    if (m) mostrar(m, e.clientX, e.clientY); else ocultar();
  });
  document.addEventListener('pointerleave', ocultar);
  document.addEventListener('focusin', e => {
    const m = e.target.closest?.('[data-tip]');
    if (m) { const r = m.getBoundingClientRect(); mostrar(m, r.right, r.bottom); }
    else ocultar();
  });
  document.addEventListener('focusout', ocultar);
  document.addEventListener('keydown', e => { if (e.key === 'Escape') ocultar(); });
}

/** Tabla de datos equivalente: los gráficos no pueden ser la única vía. */
export function tablaEquivalente(datos, col = 'valor') {
  const filas = datos.map(d =>
    `<tr><td>${escapar(String(d[col] ?? d.anio))}</td><td class="num">${nf.format(d.n ?? d.valor)}</td></tr>`).join('');
  return `<details class="tabla-datos"><summary>Ver datos en tabla</summary>
    <table><thead><tr><th>Categoría</th><th class="num">n</th></tr></thead>
    <tbody>${filas}</tbody></table></details>`;
}

export function mostrarError(contenedor, err) {
  contenedor.innerHTML = `<div class="error"><p><strong>No se pudieron cargar los datos.</strong></p>
    <p>${escapar(err.message)}</p>
    <button class="boton" onclick="location.reload()">Reintentar</button></div>`;
}

export function debounce(fn, ms = 250) {
  let t;
  return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
}
