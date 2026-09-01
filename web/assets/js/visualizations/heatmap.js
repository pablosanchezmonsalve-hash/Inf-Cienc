/* heatmap.js — Matriz de calor: temáticas ASJC más frecuentes por año.

   Se prefirió sobre un diagrama de Sankey por lo que dice `docs/DECISIONS.md`
   una y otra vez: no inventar la forma del dato. Este proyecto no tiene un
   flujo real que dibujar (una publicación no "fluye" de un año a un tema; el
   tema es un atributo, no un tránsito) — lo que sí existe es una frecuencia
   por año × categoría, y eso es exactamente lo que una matriz de calor
   representa sin forzar la lectura.

   Misma separación que `treemap.js`: `agregarMatriz()` reduce datos crudos a
   una matriz (pura), `renderHeatmap()` dibuja esa matriz en SVG (pura),
   `montarHeatmap()` es la única parte que toca el DOM.

   Escala de color: NO se introduce un tono nuevo. Se modula la opacidad de
   `--accion-viva` (el mismo token que ya usa el resto del sitio para "dato
   activo"), de modo que la intensidad se lee con el sistema cromático
   existente en los dos temas, sin depender de una paleta secuencial nueva
   que alguien tendría que validar aparte. */

import { esSinDato } from '../core.js';

const escapar = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const nf = new Intl.NumberFormat('es-CL');

/* ------------------------------------------------------------ agregación */

/** `publicaciones`: registros de `publicaciones.json` (`anio`, y un campo
    multivaluado como `asjc`). Devuelve `{anios, categorias, matriz, maximo}`:
    `matriz[categoria][anio]` es el recuento; `categorias` son las `topN` más
    frecuentes en todo el período, ordenadas de más a menos. */
export function agregarMatriz(publicaciones, { campo = 'asjc', topN = 8 } = {}) {
  const anios = [...new Set(publicaciones.map(p => p.anio).filter(a => a != null))].sort();
  const totalPorCategoria = new Map();
  for (const p of publicaciones) {
    for (const cat of (p[campo] || [])) {
      if (!cat || esSinDato(cat)) continue;
      totalPorCategoria.set(cat, (totalPorCategoria.get(cat) || 0) + 1);
    }
  }
  const categorias = [...totalPorCategoria.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, topN)
    .map(([cat]) => cat);
  const catSet = new Set(categorias);

  const matriz = new Map(categorias.map(c => [c, new Map(anios.map(a => [a, 0]))]));
  let maximo = 0;
  for (const p of publicaciones) {
    if (p.anio == null) continue;
    for (const cat of (p[campo] || [])) {
      if (!catSet.has(cat)) continue;
      const fila = matriz.get(cat);
      const n = (fila.get(p.anio) || 0) + 1;
      fila.set(p.anio, n);
      if (n > maximo) maximo = n;
    }
  }
  return { anios, categorias, matriz, maximo };
}

/* ------------------------------------------------------------------ render */

const MARGEN_IZQ = 210;  // ancho reservado para el nombre de categoría
const MARGEN_SUP = 28;   // alto reservado para el año

export function renderHeatmap({ anios, categorias, matriz, maximo }, { ancho, altoFila = 34 } = {}) {
  const alto = MARGEN_SUP + categorias.length * altoFila;
  const anchoCol = Math.max(28, (ancho - MARGEN_IZQ) / Math.max(1, anios.length));

  const cabeceraAnios = anios.map((a, i) => {
    const x = MARGEN_IZQ + i * anchoCol + anchoCol / 2;
    return `<text x="${x}" y="${MARGEN_SUP - 8}" class="heatmap-anio" text-anchor="middle">${a}</text>`;
  }).join('');

  const filas = categorias.map((cat, fi) => {
    const y = MARGEN_SUP + fi * altoFila;
    const etiqueta = `<text x="${MARGEN_IZQ - 12}" y="${y + altoFila / 2 + 4}" class="heatmap-etq"
        text-anchor="end">${escapar(cat.length > 28 ? cat.slice(0, 27) + '…' : cat)}</text>`;

    const celdas = anios.map((anio, ai) => {
      const n = matriz.get(cat).get(anio) || 0;
      const x = MARGEN_IZQ + ai * anchoCol;
      // Raíz cuadrada, no lineal: en bibliometría la frecuencia por celda
      // suele tener una cola larga, y una escala lineal deja casi todo el
      // mapa con opacidad casi cero salvo un par de celdas dominantes.
      const intensidad = maximo > 0 ? Math.sqrt(n / maximo) : 0;
      return `<g class="heatmap-celda" tabindex="0" role="gridcell"
          aria-label="${escapar(cat)}, ${anio}: ${nf.format(n)} publicaciones"
          data-tip="${escapar(cat)}" data-tip-v="${nf.format(n)} pub." data-tip-n="${anio}">
        <rect x="${x + 2}" y="${y + 3}" width="${anchoCol - 4}" height="${altoFila - 6}" rx="6"
          fill="var(--accion-viva)" fill-opacity="${(0.06 + intensidad * 0.88).toFixed(3)}"/>
        ${n > 0 && anchoCol >= 30 ? `<text x="${x + anchoCol / 2}" y="${y + altoFila / 2 + 4}"
          class="heatmap-cifra${intensidad > 0.55 ? ' es-clara' : ''}" text-anchor="middle">${n}</text>` : ''}
      </g>`;
    }).join('');

    return `<g class="heatmap-fila">${etiqueta}${celdas}</g>`;
  }).join('');

  return `<svg class="chart heatmap-svg" viewBox="0 0 ${ancho} ${alto}" role="img"
      aria-label="Frecuencia de temática ASJC por año">
    ${cabeceraAnios}${filas}
  </svg>`;
}

/* ------------------------------------------------------------------ montaje */

export function montarHeatmap(contenedor, publicaciones, opciones = {}) {
  // Un recorte del explorador vuelve a llamar a esta función sobre el MISMO
  // contenedor con una lista de publicaciones distinta. Sin desconectar el
  // observador de la corrida anterior, cada recorte deja un ResizeObserver
  // vivo de más — un ratón que abre y cierra filtros un rato acumula
  // decenas de observadores sobre el mismo nodo.
  contenedor._heatmapObserver?.disconnect();

  const agregado = agregarMatriz(publicaciones, opciones);

  function dibujar() {
    const ancho = Math.max(360, Math.round(contenedor.getBoundingClientRect().width));
    contenedor.innerHTML = agregado.categorias.length
      ? renderHeatmap(agregado, { ancho })
      : '<p class="heatmap-vacio">Sin datos de área temática suficientes para el mapa.</p>';
  }

  dibujar();
  let pendiente = null;
  const observador = new ResizeObserver(() => {
    clearTimeout(pendiente);
    pendiente = setTimeout(dibujar, 120);
  });
  observador.observe(contenedor);
  contenedor._heatmapObserver = observador;
}
