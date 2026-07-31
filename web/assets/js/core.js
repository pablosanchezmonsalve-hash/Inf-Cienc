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

export function escapar(s) {
  return String(s).replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
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

  document.getElementById('cabecera').innerHTML = `
    <div class="contenedor">
      <div class="marca">
        <strong>${escapar(meta.institucion)}</strong>
        <span>${escapar(meta.titulo_plataforma)}</span>
      </div>
      <nav class="nav" aria-label="Secciones">${nav}</nav>
    </div>`;

  document.getElementById('vigencia').innerHTML = `
    <div class="contenedor">
      Datos: <strong>${meta.fuentes.join(' · ')}</strong> ·
      Ventana <strong>${meta.ventana.inicio}–${meta.ventana.fin}</strong> ·
      Citas actualizadas al <strong>${meta.fecha_corte_citas}</strong> ·
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
const SIN_DATO = /sin dato/i;

/** Barras horizontales. Elegidas cuando las etiquetas son largas o muchas. */
export function barrasH(datos, { alto = 22, maxEtiqueta = 34 } = {}) {
  if (!datos.length) return '<p class="vacio">Sin datos</p>';
  const max = Math.max(...datos.map(d => d.n), 1);
  const anchoEtiqueta = 210, anchoValor = 52, ancho = 640;
  const total = datos.length * alto + 8;
  const filas = datos.map((d, i) => {
    const y = i * alto;
    const w = (ancho - anchoEtiqueta - anchoValor) * (d.n / max);
    const etq = d.valor.length > maxEtiqueta ? d.valor.slice(0, maxEtiqueta - 1) + '…' : d.valor;
    const clase = SIN_DATO.test(d.valor) ? 'barra sin-dato' : 'barra';
    return `<g><title>${escapar(d.valor)}: ${nf.format(d.n)}</title>
      <text x="${anchoEtiqueta - 8}" y="${y + alto / 2 + 4}" text-anchor="end">${escapar(etq)}</text>
      <rect class="${clase}" x="${anchoEtiqueta}" y="${y + 3}" width="${w}" height="${alto - 8}" rx="2"/>
      <text class="valor" x="${anchoEtiqueta + w + 6}" y="${y + alto / 2 + 4}">${nf.format(d.n)}</text>
    </g>`;
  }).join('');
  return `<div class="grafico"><svg class="chart" viewBox="0 0 ${ancho} ${total}"
    role="img" aria-label="Gráfico de barras">${filas}</svg></div>`;
}

/** Barras verticales. Para series anuales cortas: 3 años no son una línea. */
export function barrasV(datos, { etiquetaX = 'anio', etiquetaY = 'n', referencia = null } = {}) {
  if (!datos.length) return '<p class="vacio">Sin datos</p>';
  const ancho = 640, alto = 240, mIzq = 46, mAb = 34, mArr = 18;
  const vals = datos.map(d => d[etiquetaY]);
  const max = Math.max(...vals, referencia || 0) * 1.15 || 1;
  const bw = (ancho - mIzq - 16) / datos.length;
  const y = v => mArr + (alto - mArr - mAb) * (1 - v / max);

  const barras = datos.map((d, i) => {
    const x = mIzq + i * bw + bw * 0.18;
    const w = bw * 0.64;
    const yy = y(d[etiquetaY]);
    return `<g><title>${escapar(String(d[etiquetaX]))}: ${nf.format(d[etiquetaY])}</title>
      <rect class="barra" x="${x}" y="${yy}" width="${w}" height="${alto - mAb - yy}" rx="2"/>
      <text class="valor" x="${x + w / 2}" y="${yy - 5}" text-anchor="middle">${nf.format(d[etiquetaY])}</text>
      <text x="${x + w / 2}" y="${alto - mAb + 16}" text-anchor="middle">${escapar(String(d[etiquetaX]))}</text>
    </g>`;
  }).join('');

  const ref = referencia !== null ? `
    <line class="ref" x1="${mIzq}" x2="${ancho - 8}" y1="${y(referencia)}" y2="${y(referencia)}"/>
    <text x="${ancho - 10}" y="${y(referencia) - 5}" text-anchor="end">${referencia} (promedio mundial)</text>` : '';

  return `<div class="grafico"><svg class="chart" viewBox="0 0 ${ancho} ${alto}"
    role="img" aria-label="Gráfico de barras">
    <line class="eje" x1="${mIzq}" x2="${ancho - 8}" y1="${alto - mAb}" y2="${alto - mAb}"/>
    ${ref}${barras}</svg></div>`;
}

/** Anillo. Reservado a proporciones binarias, que es donde se lee bien. */
export function anillo(datos) {
  const total = datos.reduce((s, d) => s + d.n, 0) || 1;
  const r = 62, c = 2 * Math.PI * r;
  let offset = 0;
  const colores = ['var(--azul-claro)', 'var(--borde)', 'var(--sin-dato)'];
  const arcos = datos.map((d, i) => {
    const len = c * (d.n / total);
    const seg = `<circle r="${r}" cx="80" cy="80" fill="none" stroke="${colores[i % colores.length]}"
      stroke-width="26" stroke-dasharray="${len} ${c - len}" stroke-dashoffset="${-offset}"
      transform="rotate(-90 80 80)"><title>${escapar(d.valor)}: ${nf.format(d.n)}</title></circle>`;
    offset += len;
    return seg;
  }).join('');
  const leyenda = datos.map((d, i) =>
    `<div><span style="display:inline-block;width:.7rem;height:.7rem;background:${colores[i % colores.length]};border-radius:2px"></span>
     ${escapar(d.valor)}: <strong>${nf.format(d.n)}</strong> (${(100 * d.n / total).toFixed(1)} %)</div>`).join('');
  return `<div style="display:flex;gap:1.25rem;align-items:center;flex-wrap:wrap">
    <svg class="chart" viewBox="0 0 160 160" style="width:160px;flex:none" role="img"
      aria-label="Gráfico de anillo">${arcos}</svg>
    <div style="font-size:.86rem;display:grid;gap:.35rem">${leyenda}</div></div>`;
}

/** Tabla de datos equivalente: los gráficos no pueden ser la única vía. */
export function tablaEquivalente(datos, col = 'valor') {
  const filas = datos.map(d =>
    `<tr><td>${escapar(String(d[col] ?? d.anio))}</td><td class="num">${nf.format(d.n ?? d.valor)}</td></tr>`).join('');
  return `<details class="tabla-datos"><summary>Ver datos en tabla</summary>
    <table><thead><tr><th>Categoría</th><th class="num">n</th></tr></thead>
    <tbody>${filas}</tbody></table></details>`;
}

/* -------------------------------------------------------------- estados */
export function esqueleto(n = 4) {
  return Array.from({ length: n }, () => '<div class="esqueleto"></div>').join('');
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
