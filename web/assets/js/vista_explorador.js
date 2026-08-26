/* vista_explorador.js — el marcado del explorador. Sin DOM, como vista.js.

   Todo lo de aquí es una función de datos a cadena, para que el mismo código
   produzca el HTML en el BUILD (portada sin filtrar, legible sin JavaScript) y
   en el NAVEGADOR (al cambiar el recorte). Una segunda implementación para el
   repintado es la forma segura de que las dos versiones acaben divergiendo. */

import * as c from './core.js';
import * as X from './explorador.js';
import * as G from './grafo.js';

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
    <p class="ventana-cierre">La ventana de este informe termina en
      <b>${c.escapar(String(v.fin ?? ''))}</b>: lo publicado después
      <b>no está aquí</b>. La fija la carga de datos, no la fecha en que usted lo lee.</p>
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
export function estado(n, total, sel, { enlaceLista = false } = {}) {
  const partes = X.describir(sel);
  const filtrado = partes.length > 0;
  // El puente entre el tablero y el listado: mirando un recorte, lo siguiente
  // que se quiere es ver QUÉ publicaciones lo componen. Sin este enlace había
  // que rehacer el mismo filtro a mano en la otra página.
  const q = X.consulta(sel);
  const aLista = enlaceLista
    ? `<a class="enlace-lista" href="publicaciones.html${q ? '?' + q : ''}">Ver las ${
        c.nf.format(n)} publicaciones →</a>` : '';
  return `<p class="recorte-estado" role="status">
    <span class="recorte-n">${c.nf.format(n)}</span>
    <span class="recorte-de">de ${c.nf.format(total)} publicaciones</span>
    ${filtrado
      ? `<span class="recorte-que">${partes.map(p =>
          `<span class="recorte-chip">${c.escapar(p)}</span>`).join('')}</span>
         <button type="button" class="boton boton-limpiar" id="limpiar-recorte">Ver todo</button>`
      : `<span class="recorte-que recorte-todo">sin filtros · el informe completo</span>`}
    ${aLista}
  </p>`;
}

/** Los controles. Un `details` por dimensión: sin JavaScript se abren y se
    leen igual, que es la razón de usarlo en vez de un panel montado por
    guion. La primera dimensión va abierta para que el mecanismo se vea. */
export function controles(pubs, sel, { buscador = false } = {}) {
  const busca = buscador ? `<div class="dim dim-busca">
    <label for="q">Buscar en título, fuente o autor</label>
    <input type="search" id="q" name="q" value="${c.escapar(sel.q || '')}"
      placeholder="Escriba para filtrar…" autocomplete="off">
  </div>` : '';
  return busca + `<div class="filtros-explorador">${X.DIMENSIONES.map(([clave, etiqueta], i) => {
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

/* Qué indicador dibuja cada corte de la portada. Los cortes de sección ya
   traen su `cod`; éstos no lo tenían porque nadie se lo había pedido, y el
   sello lo necesita para saber de qué fuente hablar. */
const COD_PORTADA = { anio: 'P-02', qs_area: 'T-05', unidad: 'P-07', tipo: 'P-03' };

/** El mapa de procedencias que consumen los sellos, desde los artefactos.

    Se construye UNA vez y lo comparten el pre-renderizado y el navegador, para
    que no haya dos formas de decidir de qué fuente viene un indicador. */
export function procedencias(series, meta) {
  const umbral = meta && meta.cobertura_minima_sin_advertencia;
  const m = {};
  for (const [cod, bloque] of Object.entries(series || {})) {
    const p = bloque && bloque.procedencia;
    if (p) m[cod] = { fuente: p.fuente, corte: p.corte, unidad: p.unidad, umbral };
  }
  return m;
}

/** Sello de procedencia de un corte, medido sobre el recorte que se mira.

    QUÉ ES INVARIANTE Y QUÉ NO
    `fuente` y `corte` son propiedades de la fuente y no cambian al filtrar:
    vienen de `series.json`, que las calcula el build. `N` y la cobertura SÍ
    cambian, y por eso se recalculan aquí sobre el subconjunto.

    Repetir el N del total mientras el lector mira un recorte es exactamente el
    error que la cabecera de este archivo describe: enseñar «una cifra del
    total mientras el lector mira un recorte, que es la manera de que se lea la
    que no es».

    Sin procedencia para ese código no se inventa una: se devuelve cadena
    vacía. Un sello con la fuente adivinada es peor que ningún sello. */
function selloCorte(sub, campo, cod, proc) {
  const p = proc && proc[cod];
  if (!p) return '';
  const { n, cubiertas, pct } = X.cobertura(sub, campo);
  return c.sello({
    fuente: p.fuente, corte: p.corte, unidad: p.unidad || 'publicaciones',
    n, cubiertas, cobertura: pct,
    insuficiente: pct !== null && p.umbral != null && pct < p.umbral * 100,
  });
}

export function cortes(pubs_sel, proc) {
  return CORTES.map(([clave, titulo, forma]) => `
    <section class="corte" data-corte="${clave}">
      <h3>${c.escapar(titulo)}</h3>
      <div class="grafico">${grafico(pubs_sel, clave, titulo, forma)}</div>
      ${selloCorte(pubs_sel, clave, COD_PORTADA[clave], proc)}
    </section>`).join('');
}

/* ─────────────────────────────────────────────────────── página completa */

/** Todo el cuerpo del explorador. La usa el pre-renderizado con el conjunto
    completo y el navegador con el recorte vigente. */
export function explorador(pubs, sel, proc) {
  const sub = X.recorte(pubs, sel);
  return {
    estado: estado(sub.length, pubs.length, sel, { enlaceLista: true }),
    controles: controles(pubs, sel),
    cifras: cifras(X.resumen(sub)),
    cortes: cortes(sub, proc),
  };
}

/* ═══════════════════════════════════════════ secciones ═══════════════════ */

/* Cada sección declara SUS cortes. La forma la fija la relación del dato, no
   la costumbre: una serie anual va en vertical, un ranking largo en
   horizontal, unos umbrales anidados en acumulada y un total repartido en
   proporcional. */
export const SECCIONES = {
  produccion: {
    pregunta: 'Cuánto se publicó, de qué tipo y desde qué unidad.',
    noResponde: 'El volumen no mide calidad ni esfuerzo: cuenta documentos indexados.',
    cortes: [
      { cod: 'P-02', campo: 'anio',   titulo: 'Publicaciones por año',        forma: 'barrasV' },
      { cod: 'P-03', campo: 'tipo',   titulo: 'Tipo documental',              forma: 'barrasH' },
      { cod: 'P-05', campo: 'fuente', titulo: 'Fuentes con más publicaciones', forma: 'barrasH', tope: 15 },
      { cod: 'P-07', campo: 'unidad', titulo: 'Unidad académica',             forma: 'barrasH' },
    ],
  },
  impacto: {
    pregunta: 'Cuántas citas recibió lo publicado y cómo se sitúa frente al mundo.',
    noResponde: 'Las citas miden atención recibida, no calidad ni utilidad social.',
    cortes: [
      { cod: 'I-01', campo: 'citas',  titulo: 'Citas por año de publicación', forma: 'suma-anio',
        aviso: 'Las barras cuentan las citas recibidas por lo publicado en cada año, no la actividad de ese año. Un año reciente tuvo menos tiempo para acumular citas.' },
      { cod: 'I-04', campo: 'fwci',   titulo: 'FWCI mediano por año',         forma: 'mediana-anio' },
      { cod: 'I-05', campo: 'percentil', titulo: 'Umbrales de percentil',     forma: 'acumulada' },
      { cod: 'R-01', campo: 'cuartil', titulo: 'Cuartil de la revista',       forma: 'proporcional' },
      { cod: 'A-01', campo: 'open_access', titulo: 'Vías de acceso abierto',  forma: 'barrasH' },
    ],
  },
  colaboracion: {
    pregunta: 'Con quién se publicó y en qué tamaño de equipo.',
    noResponde: 'Colaborar no es por sí mismo mejor: describe una forma de trabajo, no un logro.',
    cortes: [
      { cod: 'C-01', campo: 'colaboracion',   titulo: 'Nacional o internacional', forma: 'barrasH' },
      { cod: 'C-03', campo: 'paises',         titulo: 'Países colaboradores',     forma: 'barrasH', tope: 15 },
      { cod: 'C-04', campo: 'instituciones',  titulo: 'Instituciones colaboradoras', forma: 'barrasH', tope: 15 },
      { cod: 'C-06', campo: 'autores_tramo',  titulo: 'Autores por publicación',  forma: 'distribucion' },
      { cod: 'C-05', campo: 'coautoria',      titulo: 'Red de coautoría',         forma: 'red' },
    ],
  },
  tematica: {
    pregunta: 'En qué áreas y sobre qué objetivos se publicó.',
    noResponde: 'La categoría de la revista no es el tema exacto del artículo.',
    cortes: [
      { cod: 'T-05', campo: 'qs_area', titulo: 'Áreas QS',                    forma: 'barrasH' },
      { cod: 'T-01', campo: 'asjc',    titulo: 'Áreas temáticas ASJC',        forma: 'barrasH', tope: 20 },
      { cod: 'T-04', campo: 'ods',     titulo: 'Objetivos de Desarrollo Sostenible', forma: 'barrasH', tope: 17 },
    ],
  },
};

/* Los campos multivaluados: una publicación aparece en varias barras y la suma
   de las barras supera el número de publicaciones. Se marca con trama, que es
   el código visual que el sitio ya enseña. */
const MULTIVALUADO = new Set(['paises', 'instituciones', 'asjc', 'ods', 'qs_area', 'unidad', 'open_access']);

/* Devuelve el gráfico Y sus datos. La TABLA equivalente no es un extra: es la
   vía alternativa al gráfico para quien no puede leerlo, y se construye de los
   mismos números para que no pueda decir otra cosa. */
function dibujar(sub, corte) {
  const { campo, titulo, forma, tope } = corte;
  if (forma === 'suma-anio') {
    const d = X.sumaPorAnio(sub, campo);
    return d.length
      ? { svg: c.barrasV(d, { titulo, etiquetaX: 'anio', etiquetaY: 'n' }),
          datos: d.map(x => ({ valor: x.anio, n: x.n })) } : null;
  }
  if (forma === 'mediana-anio') {
    const d = X.medianaPorAnio(sub, campo).filter(x => x.valor !== null);
    return d.length
      ? { svg: c.desviacion(d, { titulo, etiquetaX: 'anio', etiquetaY: 'valor',
            decimales: 2, referencia: 1, refEtiqueta: '1,00 — promedio mundial' }),
          datos: d.map(x => ({ valor: x.anio, n: x.valor })) } : null;
  }
  if (forma === 'acumulada') {
    const { datos, base } = X.umbralesPercentil(sub);
    return base ? { svg: c.acumulada(datos, { titulo, total: base }), datos } : null;
  }
  const datos = X.porCampo(sub, campo, { tope: tope || 0 });
  if (!datos.length) return null;
  if (forma === 'proporcional') return { svg: c.proporcional(datos, { titulo }), datos };
  if (forma === 'distribucion') {
    return { svg: c.distribucion(datos, { titulo, etiquetaEje: 'autores por publicación' }), datos };
  }
  if (forma === 'barrasV') {
    return { svg: c.barrasV(datos.map(d => ({ anio: d.valor, n: d.n })),
      { titulo, etiquetaX: 'anio', etiquetaY: 'n' }), datos };
  }
  return { svg: c.barrasH(datos, { titulo, trama: MULTIVALUADO.has(campo) }), datos };
}

/** Gráfico y tabla, conmutables. Sin JavaScript se muestran los dos, que es lo
    correcto: la tabla es la vía equivalente, no un añadido. */
function conmutador(id) {
  return `<div class="vistas" role="group" aria-label="Forma de presentación">
    <button type="button" data-vista="grafico" aria-pressed="true"
      aria-controls="${id}-grafico">Gráfico</button>
    <button type="button" data-vista="tabla" aria-pressed="false"
      aria-controls="${id}-tabla">Tabla</button>
  </div>`;
}

/* ─────────────────────────────────────────────────── C-05, red de coautoría

   No pasa por `dibujar()`/`conmutador()`: la red no es un gráfico con una
   tabla equivalente, son TRES lecturas del mismo grafo (nodos, matriz,
   arcos) más una tabla de aristas como cuarta vía accesible. Reutiliza el
   mismo conmutador genérico de `.vistas button[data-vista]` que ya engancha
   `conmutadorVistas()` en paginas.js — no hace falta escucha nueva. */

/** El id del patrón de trama (D-09, ausencia de unidad) se pone en conflicto
    si dos SVG de esta misma sección lo declaran igual: el navegador resuelve
    `url(#id)` contra el documento entero, no por SVG. Los tres SVG de este
    corte —nodos, matriz, arcos— conviven en el DOM a la vez (se alternan con
    CSS, no con innerHTML), así que cada uno necesita su propio id. */
function svgConTramaUnica(svg, sufijo) {
  return svg.replace(/tramaSinDatoRed/g, `tramaSinDatoRed-${sufijo}`);
}

/** Tabla de aristas: la vía accesible para quien no puede leer el SVG. Cada
    fila es una coautoría real, con las dos formas de pesarla —igual que
    declara `docs/METHODOLOGY.md`, el recuento y el peso fraccional no
    responden la misma pregunta y no se elige uno por el lector. */
function tablaRed(aristas) {
  const filas = aristas.slice()
    .sort((e1, e2) => e2.peso - e1.peso || e1.a.localeCompare(e1.b) || e1.b.localeCompare(e2.b))
    .map(e => `<tr><td>${c.escapar(e.a)}</td><td>${c.escapar(e.b)}</td>
      <td class="num">${e.peso}</td><td class="num">${e.peso_fraccional.toFixed(2)}</td></tr>`).join('');
  return `<div class="tabla-envoltura tabla-datos"><table>
    <thead><tr><th scope="col">Persona</th><th scope="col">Coautor</th>
      <th scope="col" class="num">Publicaciones compartidas</th>
      <th scope="col" class="num">Peso fraccional</th></tr></thead>
    <tbody>${filas}</tbody></table></div>`;
}

/** El módulo completo de C-05. `unidadPorPersona`: Map nombre → unidad
    académica, de `authors.json` (no hay forma de derivarla de `sub` sola:
    una publicación no lleva la unidad por autor individual, sólo el conjunto
    de unidades de TODOS sus firmantes). */
function corteRed(sub, corte, unidadPorPersona, proc) {
  const id = corte.cod;
  const autoria = [];
  for (const p of sub) for (const persona of (p.autores_uft || [])) autoria.push([persona, p.eid]);

  const g = G.construirGrafo(autoria, new Set(), unidadPorPersona || new Map());
  if (!g.nodos.length) {
    return `<section class="corte" id="${id}" data-corte="${corte.campo}" tabindex="-1">
      <header class="corte-cab"><h3>${c.escapar(corte.titulo)}</h3></header>
      <p class="vacio">Ninguna publicación con autoría UFT detallada en este recorte.</p>
    </section>`;
  }
  const comp = G.componentes(g.nodos, g.aristas);
  const coms = G.comunidades(g.nodos, g.aristas);
  const nComp = new Set(comp.values()).size;
  const nComs = new Set(coms.values()).size;
  const nodosConArista = new Set();
  for (const e of g.aristas) { nodosConArista.add(e.a); nodosConArista.add(e.b); }
  const conectadas = nodosConArista.size;

  // El DIBUJO se recorta a las componentes de 5 personas o más — el mismo
  // criterio y el mismo motivo que `internal/red_coautoria.html`
  // (src/review/vista_red.py): con cientos de componentes de una pareja o un
  // trío, el anillo de grupos se vuelve ilegible. Se recorta el dibujo, no el
  // análisis — las cifras de arriba y la tabla de abajo cubren a TODAS.
  const MINIMO = 5;
  const tamComp = new Map();
  for (const c2 of comp.values()) tamComp.set(c2, (tamComp.get(c2) || 0) + 1);
  const visibles = g.nodos.filter(n => tamComp.get(comp.get(n)) >= MINIMO);
  const idxVis = new Map(visibles.map((n, i) => [n, i]));
  const nodos = visibles.map((n, i) => ({
    i, id: n, valor: n, n: g.publicacionesPorPersona.get(n) || 0,
    unidad: g.unidades.get(n), com: coms.get(n),
  }));
  const aristasIdx = g.aristas
    .filter(e => idxVis.has(e.a) && idxVis.has(e.b))
    .map(e => ({ a: idxVis.get(e.a), b: idxVis.get(e.b), n: e.peso }));

  // Un recorte angosto puede no dejar NINGUNA componente de 5+: el dibujo se
  // queda sin nada que mostrar, pero la tabla de aristas sigue cubriendo todo
  // lo que el recorte sí tiene. Un hueco sin avisar se leería como que no hay
  // coautoría en absoluto, que sería falso si `conectadas` es mayor que 0.
  const sinDibujo = !nodos.length;
  const D = sinDibujo ? null : c.disponerRed(nodos, aristasIdx);
  const vacioDibujo = `<p class="vacio">Ninguna componente de 5 personas o más en este
    recorte. La tabla, abajo, cubre las ${c.nf.format(conectadas)} personas con
    coautoría interna que sí tiene.</p>`;

  return `<section class="corte corte-red" id="${id}" data-corte="${corte.campo}" tabindex="-1">
    <header class="corte-cab">
      <h3>${c.escapar(corte.titulo)}</h3>
      <div class="vistas" role="group" aria-label="Forma de la red">
        <button type="button" data-vista="nodos" aria-pressed="${!sinDibujo}" aria-controls="${id}-nodos">Nodos</button>
        <button type="button" data-vista="matriz" aria-pressed="false" aria-controls="${id}-matriz">Matriz</button>
        <button type="button" data-vista="arcos" aria-pressed="false" aria-controls="${id}-arcos">Arcos</button>
        <button type="button" data-vista="tabla" aria-pressed="${sinDibujo}" aria-controls="${id}-tabla">Tabla</button>
      </div>
    </header>
    <p class="nota-destacada"><b>Dos particiones que no son lo mismo</b>
      La posición agrupa por <b>comunidad</b>, detectada por un algoritmo (Louvain) que
      maximiza densidad interna — una heurística razonable, no un veredicto sobre qué
      grupos de investigación existen. La <b>componente</b> —si hay un camino de
      coautoría entre dos personas— sí es un hecho objetivo del grafo, sin parámetros
      ni azar. <a href="metodologia.html#componente-y-comunidad-red-de-coautoria">Cómo se lee esta red →</a></p>
    <div class="vista" id="${id}-nodos" data-vista="nodos" data-activa="${!sinDibujo}">
      ${sinDibujo ? vacioDibujo : svgConTramaUnica(c.red(D, 'nodos'), id + '-nodos')}</div>
    <div class="vista" id="${id}-matriz" data-vista="matriz" data-activa="false">
      ${sinDibujo ? vacioDibujo : svgConTramaUnica(c.red(D, 'matriz'), id + '-matriz')}</div>
    <div class="vista" id="${id}-arcos" data-vista="arcos" data-activa="false">
      ${sinDibujo ? vacioDibujo : svgConTramaUnica(c.red(D, 'arcos'), id + '-arcos')}</div>
    <div class="vista" id="${id}-tabla" data-vista="tabla" data-activa="${sinDibujo}">${tablaRed(g.aristas)}</div>
    <p class="nota"><strong>${c.nf.format(g.nodos.length)}</strong> personas en el recorte ·
      <strong>${c.nf.format(conectadas)}</strong> con al menos una coautoría interna ·
      <strong>${c.nf.format(nComp)}</strong> componentes · <strong>${c.nf.format(nComs)}</strong>
      comunidades Louvain. Sólo se dibujan las componentes de 5 personas o más; la tabla
      cubre a todas.</p>
    ${selloCorte(sub, corte.campo, corte.cod, proc)}
  </section>`;
}

/** Los cortes de una sección, recalculados sobre el recorte vigente.
    `unidadPorPersona` sólo lo usa C-05 (red de coautoría); el resto de los
    cortes lo ignora. */
export function cortesSeccion(sub, clave, proc, unidadPorPersona) {
  const s = SECCIONES[clave];
  if (!s) return '';
  return s.cortes.map(corte => {
    if (corte.forma === 'red') return corteRed(sub, corte, unidadPorPersona, proc);
    const r = dibujar(sub, corte);
    const id = corte.cod || corte.campo;
    // El id es el CÓDIGO del indicador y no el campo: así la compuerta de
    // higiene puede comprobar que cada indicador declarado se dibuja de
    // verdad, y los enlaces del catálogo a #C-01 siguen llegando al gráfico.
    return `<section class="corte" id="${c.escapar(corte.cod || corte.campo)}"
      data-corte="${corte.campo}" tabindex="-1">
      <header class="corte-cab">
        <h3>${c.escapar(corte.titulo)}</h3>
        ${r ? conmutador(id) : ''}
      </header>
      ${r ? `<div class="vista" id="${id}-grafico" data-vista="grafico" data-activa="true">
        <div class="grafico">${r.svg}</div>
      </div>
      <div class="vista" id="${id}-tabla" data-vista="tabla" data-activa="false">
        ${c.tablaEquivalente(r.datos)}
      </div>`
      : '<p class="vacio">Ninguna publicación con este dato en el recorte.</p>'}
      ${MULTIVALUADO.has(corte.campo)
        ? '<p class="leyenda-trama">Barras rayadas: no son partes de un total y no suman.</p>' : ''}
      ${corte.aviso ? `<p class="nota">${c.escapar(corte.aviso)}</p>` : ''}
      ${selloCorte(sub, corte.campo, corte.cod, proc)}
    </section>`;
  }).join('');
}

/** Índice de los cortes de la sección.

    El panel lateral pasó de ser un índice de módulos a ser los controles del
    recorte, y con eso se habría perdido la navegación rápida entre gráficos.
    Vuelve debajo de los filtros: sigue siendo la forma de saltar a un
    indicador concreto sin buscarlo con la rueda. */
export function indice(clave) {
  const s = SECCIONES[clave];
  if (!s) return '';
  return `<nav class="rail" aria-label="Indicadores de la sección">
    <p class="rail-titulo">En esta sección</p>
    ${s.cortes.map(x => `<a href="#${c.escapar(x.cod || x.campo)}">
      <span class="rail-cod">${c.escapar(x.cod || '')}</span>
      <span class="rail-nom">${c.escapar(x.titulo)}</span></a>`).join('')}
  </nav>`;
}

/** La cabecera de una sección: qué responde y qué NO responde. */
export function cabeceraSeccion(clave, titulo) {
  const s = SECCIONES[clave];
  return `<div class="portada-id">
    <h1>${c.escapar(titulo)}</h1>
    <p class="portada-sub">${c.escapar(s ? s.pregunta : '')}</p>
  </div>
  ${s ? `<details class="metodo portada-metodo">
    <summary>Qué NO dice esta sección</summary>
    <div class="metodo-cuerpo"><p>${c.escapar(s.noResponde)}</p></div>
  </details>` : ''}`;
}

/** Todo el cuerpo de una sección. `unidadPorPersona` (Map, opcional) sólo lo
    necesita C-05; las demás secciones lo reciben y no lo usan. */
export function seccion(pubs, sel, clave, proc, unidadPorPersona) {
  const sub = X.recorte(pubs, sel);
  return {
    estado: estado(sub.length, pubs.length, sel, { enlaceLista: true }),
    controles: controles(pubs, sel) + indice(clave),
    cifras: cifras(X.resumen(sub)),
    cortes: cortesSeccion(sub, clave, proc, unidadPorPersona),
  };
}

/* ────────────────────────────────────────────── indicadores no publicados */

/** Los indicadores de la sección que existen y NO se publican.

    Aparecen a propósito: que uno esté verificado y diferido es información del
    informe, y un hueco se leería como que el fenómeno no existe. Van sobre el
    suelo de contraste porque NO responden al recorte —no se calculan aquí— y
    mezclarlos con lo que sí responde haría creer que el filtro los cambia. */
export function diferidos(catalogo, clave) {
  const filas = (catalogo.indicadores || []).filter(
    r => r.categoria === clave && r.estado !== 'publicado');
  if (!filas.length) return '';
  return `<section class="banda banda-contraste no-publicados">
    <div class="banda-titulo">
      <p class="banda-gancho">Lo que esta sección todavía no puede mostrar</p>
      <h2>${filas.length === 1 ? 'Un indicador' : `${filas.length} indicadores`}
        de esta sección está${filas.length === 1 ? '' : 'n'} verificado${
        filas.length === 1 ? '' : 's'} pero no se publica${filas.length === 1 ? '' : 'n'}.</h2>
      <p>No responden al recorte: no se calculan aquí. Se dice cuál y por qué.</p>
    </div>
    ${filas.map(r => `<article class="modulo modulo-diferido" id="${c.escapar(r.codigo)}">
      <header><div class="modulo-id">
        <h3>${c.escapar(r.nombre)}</h3><span class="codigo">${c.escapar(r.codigo)}</span>
      </div><span class="estado" data-e="${c.escapar(r.estado)}">${
        c.escapar(r.estado_etiqueta || r.estado)}</span></header>
      <p class="nota">${c.escapar(r.advertencia || r.definicion || '')}</p>
    </article>`).join('')}
  </section>`;
}
