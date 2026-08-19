/* vista.js — construcción de HTML, sin DOM.

   TODO lo que hay aquí es una función de datos a cadena. Ni una lectura de
   `document`, ni un `addEventListener`, ni un `localStorage`. Esa disciplina
   es la que permite que el mismo código corra en dos sitios:

     · en el BUILD, bajo Node (src/build/07_prerender.mjs), para dejar el HTML
       ya escrito en dist/*.html;
     · en el NAVEGADOR (paginas.js), cuando hay que repintar tras un filtro.

   Antes esta lógica vivía dentro de los renderizadores de página, mezclada con
   `innerHTML =`. Separarla no es una preferencia de estilo: es la condición
   para que el sitio tenga contenido sin JavaScript sin mantener dos versiones
   del mismo marcado, que es como esas dos versiones acaban divergiendo.

   La INTERACCIÓN —conmutador de vista, scroll-spy, tooltip, filtros— sigue
   viviendo en paginas.js. Aquí sólo se emite el marcado que esa interacción
   después manipula. */

import * as c from './core.js';

/* ═══════════════════════════════════════════════════════ gráficos por código */

/* El color por serie se reserva a los cortes CATEGÓRICOS —vías de acceso
   abierto, cuartiles, países— donde cada barra es una entidad distinta. Un
   ranking por volumen se queda en una sola serie: colorear por posición haría
   que el color siguiera al rank y no a la entidad, y repintaría los
   supervivientes en cuanto cambiara el recorte. */
/* `cuotaValida` habilita el «% de lo mostrado» en el tooltip. Se activa SÓLO
   donde las barras son realmente partes de un total: no en umbrales encajados
   (I-05), no en multivaluados (A-01, C-03, C-04, T-01, T-04, T-05) y no en
   rankings recortados (P-05), donde un porcentaje afirmaría algo falso. */
export const RENDER = {
  'P-02': s => c.barrasV(s.datos, { titulo: s.nombre, etiquetaX: 'anio', etiquetaY: 'n' }),
  'P-03': s => c.barrasH(s.datos, { titulo: s.nombre, cuotaValida: true, trama: s.multivaluado }),
  'P-05': s => c.barrasH(s.datos, { titulo: s.nombre, trama: s.multivaluado }),
  'P-07': s => c.barrasH(s.datos, { titulo: s.nombre, cuotaValida: true, trama: s.multivaluado }),
  'I-01': s => c.barrasV(s.datos, { titulo: s.nombre, etiquetaX: 'anio', etiquetaY: 'n' }),
  'I-04': s => c.barrasV(s.datos.map(d => ({ anio: d.anio, n: d.valor })), {
    titulo: s.nombre, etiquetaX: 'anio', etiquetaY: 'n', decimales: 2,
    referencia: 1, refEtiqueta: '1,00 — promedio mundial',
  }),
  'I-05': s => c.barrasH(s.datos, { titulo: s.nombre, trama: s.multivaluado,
    // El trazo dice qué cabría esperar bajo el promedio mundial. Sin él, «75
    // en el top 10 %» es un número sin escala: nadie sabe si son muchos.
    refEtiqueta: `Lo esperable bajo el promedio mundial: el top k % contiene el k % `
      + `de las ${c.nf.format(s.base_percentil)} publicaciones con percentil.` }),
  // Q1–Q4 es una escala ORDENADA, no cuatro categorías sueltas: un solo tono en
  // cuatro pasos, del más oscuro (mejor posición) al más claro.
  'R-01': s => c.barrasH(s.datos, { titulo: s.nombre, escala: 'ordinal', cuotaValida: true, trama: s.multivaluado }),
  // Acceso abierto se queda en una sola serie a propósito: las categorías se
  // llaman Gold, Green y Bronze, y pintarlas con la paleta categórica dejaría
  // «Green» de color naranja. Cuando el nombre de la categoría ya es un color,
  // el color deja de estar disponible para codificar.
  'A-01': s => c.barrasH(s.datos, { titulo: s.nombre, trama: s.multivaluado }),
  'C-01': s => c.anillo(s.datos, { titulo: s.nombre }),
  'C-03': s => c.barrasH(s.datos, { titulo: s.nombre, trama: s.multivaluado }),
  'C-04': s => c.barrasH(s.datos, { titulo: s.nombre, trama: s.multivaluado }),
  'C-06': s => c.barrasH(s.datos, { titulo: s.nombre, cuotaValida: true, trama: s.multivaluado }),
  'T-05': s => c.barrasH(s.datos, { titulo: s.nombre, trama: s.multivaluado }),
  'T-01': s => c.barrasH(s.datos, { titulo: s.nombre, trama: s.multivaluado }),
  'T-04': s => c.barrasH(s.datos, { titulo: s.nombre, trama: s.multivaluado }),
};

/* Advertencias que nacen de CÓMO se dibuja el indicador, no de cómo se calcula.
   Por eso viven aquí y no en config/indicators.yml: describen una lectura que
   el gráfico induce, y sólo existen mientras el gráfico sea ése. */
const LECTURA = {
  // Un gráfico de citas por año de publicación invita a leer «el impacto está
  // cayendo». Lo que cae es el tiempo disponible para acumular citas.
  'I-01': `<div class="nota-destacada"><b>Cómo se lee este gráfico</b>
    Las barras cuentan las citas recibidas por las publicaciones de cada año, no
    la actividad citadora de ese año. Un año reciente ha tenido menos tiempo para
    acumular citas, así que <strong>la caída del último año no indica menor
    impacto</strong>. Para comparar años use el FWCI, que está normalizado por
    campo, año y tipo documental.</div>`,
  // Cuatro barras crecientes parecen cuatro categorías; son cuatro umbrales
  // encajados uno dentro del otro.
  'I-05': `<p class="nota">Los umbrales son <strong>acumulativos y encajados</strong>:
    las publicaciones del top 1 % también están contadas en el top 5 %, el 10 %
    y el 25 %. Las barras no son categorías excluyentes y no se suman.</p>`,
};

const EXTRA = {
  'I-04': s => `<p class="nota">Publicaciones aún sin citas por año: ` +
    s.sin_citas_pct.map(x => `${x.anio}: <strong>${x.pct === null ? 'sin dato' : x.pct + ' %'}</strong>`)
      .join(' · ') + `</p>`,
  'C-06': s => `<p class="nota">Media ${s.media} · <strong>mediana ${s.mediana}</strong>.
    La distribución es asimétrica: la mediana describe mejor el caso típico.</p>`,
  'P-05': s => `<p class="nota">Se muestran las 20 fuentes con más publicaciones,
    de ${c.nf.format(s.total_fuentes)} distintas.</p>`,
  'A-01': s => `<p class="nota"><strong>${c.nf.format(s.con_varias_etiquetas)}</strong>
    publicaciones tienen más de una vía de acceso abierto declarada —típicamente
    Gold en la revista y Green en un repositorio—, así que aparecen en más de una
    barra.</p>`,
  'T-04': s => `<p class="nota"><strong>${c.nf.format(s.con_ods)}</strong> publicaciones
    tienen al menos un ODS asignado. Se reporta como recuento, no como
    distribución porcentual del total.</p>`,
  'P-07': () => `<p class="nota">Las escuelas se agregan a su facultad según la
    jerarquía declarada en configuración. Las unidades sin jerarquía declarada
    aparecen tal como figuran en la afiliación.</p>`,
};

/* Un gráfico cuyas barras no suman el total tiene que decirlo junto al gráfico,
   no sólo en la nota metodológica. La bandera la publica el build desde
   config/indicators.yml. */
function avisoMultivaluado(s) {
  if (!s.multivaluado) return '';
  // La LEYENDA va siempre: es la que enseña el código visual. Un lector la
  // aprende una vez —«rayado = las barras no suman»— y la reconoce en los seis
  // módulos multivaluados del sitio sin volver a leer nada.
  const leyenda = `<p class="leyenda-trama">Barras rayadas: no son partes de un
    total y no suman.</p>`;
  // El texto largo, en cambio, se omite si la advertencia del indicador ya lo
  // dice. Dos avisos idénticos se leen como un descuido y restan credibilidad
  // al resto de las advertencias.
  if (/multivaluad|no sumable/i.test(s.nota?.texto || '')) return leyenda;
  return leyenda + `<p class="nota"><strong>Multivaluado:</strong> una publicación
    puede aparecer en varias barras, de modo que la suma de las barras supera el
    número de publicaciones. Las barras no son partes de un total.</p>`;
}

/* ══════════════════════════════════════════════════════════════ módulos */

/** Conmutador Gráfico ⇄ Tabla de un módulo.

    El patrón viene de los portales del oficio: el Leiden Ranking presenta la
    misma tabla como lista, dispersión o mapa y deja elegir, en vez de decidir
    por el lector cuál es la representación buena. Aquí las dos vistas son el
    gráfico y la tabla, y la tabla dejó de estar detrás de un «Ver datos».

    El control se oculta cuando no hay JavaScript —no haría nada— y en ese caso
    las dos vistas se muestran a la vez, que es el comportamiento correcto: la
    tabla es la vía equivalente al gráfico, no un extra. Lo decide una sola
    clase en <html> escrita antes de pintar. */
function conmutador(id) {
  return `<div class="vistas" role="group" aria-label="Forma de presentación">
    <button type="button" data-vista="grafico" aria-pressed="true"
      aria-controls="${id}-grafico">Gráfico</button>
    <button type="button" data-vista="tabla" aria-pressed="false"
      aria-controls="${id}-tabla">Tabla</button>
  </div>`;
}

/** Un módulo de indicador completo.

    El orden no es decorativo. Primero lo que condiciona la lectura —la
    advertencia metodológica y la nota de lectura del gráfico—, después la
    figura, después el sello que dice de dónde sale y sobre cuántos casos, y al
    final las notas de detalle. Poner el sello al final lo convertía en letra
    pequeña; puesto justo bajo la figura, se lee con ella. */
export function modulo(cod, s) {
  const dibujar = RENDER[cod] || (x => c.barrasH(x.datos, { titulo: x.nombre }));
  return `<section class="modulo" id="${cod}" tabindex="-1">
    <header>
      <div class="modulo-id">
        <h2>${c.escapar(s.nombre)}</h2>
        <span class="codigo">${cod}</span>
      </div>
      ${conmutador(cod)}
    </header>
    ${s.nota && s.nota.destacada ? c.nota(s.nota) : ''}
    ${LECTURA[cod] || ''}
    <div class="vista" id="${cod}-grafico" data-vista="grafico" data-activa="true">
      ${dibujar(s)}
    </div>
    <div class="vista" id="${cod}-tabla" data-vista="tabla" data-activa="false">
      ${c.tablaEquivalente(s.datos)}
    </div>
    ${c.sello(s.procedencia)}
    ${avisoMultivaluado(s)}
    ${EXTRA[cod] ? EXTRA[cod](s) : ''}
    ${s.nota && !s.nota.destacada ? c.nota(s.nota) : ''}
  </section>`;
}

/** Índice lateral de la página.

    Copiado en intención del panel de entidades que SciVal mantiene fijo a la
    izquierda: en una página de cinco indicadores largos, saber qué hay y poder
    saltar sin recorrer la página entera es la diferencia entre consultar y
    resignarse a leer en orden. El indicador activo se marca por scroll-spy
    desde paginas.js; sin JavaScript sigue siendo una lista de anclas útil. */
export function rail(codigos, series, porCodigo = {}) {
  // Un indicador diferido sigue en el índice: si desapareciera de aquí, la
  // página diría que no existe, que es justo lo que el módulo evita decir.
  const items = codigos.map(cod => {
    const s = series[cod] || porCodigo[cod];
    if (!s) return '';
    const dif = !series[cod];
    return `<li><a href="#${cod}"${dif ? ' class="rail-diferido"' : ''}>
      <span class="rail-cod">${cod}</span>
      <span class="rail-txt">${c.escapar(s.nombre)}</span>
      ${dif ? '<span class="rail-marca">diferido</span>' : ''}</a></li>`;
  }).join('');
  return `<nav class="rail" aria-label="Indicadores de esta página">
    <p class="rail-titulo">En esta página</p>
    <ol>${items}</ol>
  </nav>`;
}

/** El panel conceptual que abre una sección.

    Cada sección invita a una lectura equivocada concreta —producción se lee como
    rendimiento, impacto como calidad, colaboración como influencia, la
    clasificación temática como el tema real del artículo— y un lector que llega
    sin saber qué pregunta responde la sección no tiene forma de saber cuál NO
    responde. Decirlo después de los gráficos es decirlo tarde: va delante.

    El texto viene de `docs/EJES.md` a través de `ejes.json`. No se escribe aquí:
    es una afirmación metodológica y se revisa como documento. */
export function panelEje(eje) {
  if (!eje) return '';
  return `<section class="panel-eje" aria-label="Qué responde esta sección">
    <h2>${c.escapar(eje.titulo)}</h2>
    <dl>
      <dt>Responde</dt><dd>${c.escapar(eje.responde)}</dd>
      <dt>No responde</dt><dd>${c.escapar(eje.no_responde)}</dd>
      <dt>Sobre qué</dt><dd>${c.escapar(eje.sobre_que)}</dd>
    </dl>
  </section>`;
}

/** Módulo de un indicador que NO se publica.

    Un indicador diferido que simplemente no aparece se lee como que el
    fenómeno no existe: en colaboración, un hueco donde iría la red de
    coautoría dice «no hay coautoría interna», que es una afirmación distinta
    y falsa. Es la misma regla que `D-09` aplica a la celda —ausencia de dato
    y cero nunca se ven igual— llevada al módulo completo.

    No inventa texto: el motivo sale de `catalogo.json`, que a su vez lo toma
    de `config/indicators.yml`. Se combinan `razon` y `advertencia` con el
    mismo criterio que la tabla del catálogo, para que las dos vistas del
    mismo hecho no puedan divergir. */
export function moduloDiferido(cod, r) {
  const motivo = [r.razon, r.advertencia].filter(Boolean).join(' ');
  return `<section class="modulo modulo-diferido" id="${cod}" tabindex="-1">
    <header>
      <div class="modulo-id">
        <h2>${c.escapar(r.nombre)}</h2>
        <span class="codigo">${cod}</span>
      </div>
      <span class="estado" data-e="${r.estado}">${c.escapar(r.estado_etiqueta)}</span>
    </header>
    <p class="diferido-detalle">${c.escapar(r.estado_detalle)}</p>
    ${motivo ? `<p class="nota-destacada"><b>Por qué no se publica</b>${c.escapar(motivo)}</p>` : ''}
    ${r.que_falta ? `<p class="nota"><strong>Qué falta:</strong> ${c.escapar(r.que_falta)}</p>` : ''}
    <p class="nota">Este módulo no muestra un gráfico vacío ni un cero: el dato
      todavía no se ha construido, que no es lo mismo que valer cero. Ver el
      <a href="indicadores.html#${cod}">catálogo de indicadores</a>.</p>
  </section>`;
}

/** Los módulos de una página de sección, con su panel y su índice.

    `catalogo` es opcional: sin él la página se comporta como antes. Con él,
    los códigos declarados en la página que no tienen serie porque no se
    publican se dibujan como módulo diferido en lugar de desaparecer. */
export function paginaModulos(codigos, series, eje, catalogo = null) {
  const porCodigo = {};
  if (catalogo) for (const r of catalogo.indicadores) porCodigo[r.codigo] = r;

  // Se conserva el orden declarado en la página: el diferido ocupa el lugar
  // que le corresponde en la secuencia, no se relega al final.
  const presentes = codigos.filter(cod =>
    series[cod] || (porCodigo[cod] && porCodigo[cod].estado !== 'publicado'));

  const bloques = presentes.map(cod => series[cod]
    ? modulo(cod, series[cod])
    : moduloDiferido(cod, porCodigo[cod])).join('');

  return panelEje(eje) + rail(presentes, series, porCodigo)
    + `<div class="modulos">${bloques}</div>`;
}

/* ══════════════════════════════════════════════════════════════ portada */

const AYUDA_KPI = {
  'I-03': 'FWCI', 'C-01': 'Colaboración internacional',
  'P-06': 'Formas de firma', 'I-01': 'Fecha de corte',
};

/* Los tres indicadores que abren el informe. No es una preferencia estética:
   son los tres ejes que el proyecto declara —cuánto se produce, con qué impacto
   normalizado, y con quién se colabora—. El resto de los KPI baja a la rejilla.

   La alternativa era repetir: el titular mostraba 823 publicaciones y la
   rejilla, cuatro centímetros más abajo, volvía a mostrar 823 publicaciones. Un
   indicador dicho dos veces en la misma pantalla no gana énfasis, lo pierde. */
const TITULARES = ['P-01', 'I-03', 'C-01'];

/** Titular de portada: los tres indicadores de cabecera a tamaño display.

    Las plataformas del oficio abren con la magnitud y el índice normalizado, no
    con un índice de contenidos: hay que saber de qué tamaño es el objeto antes
    de que un desglose signifique algo. Son TRES y no seis porque un titular con
    seis cifras no tiene titular.

    Cada cifra arrastra SU denominador y, si lo tiene, su referencia. Un 0,87 de
    FWCI sin el «1,0 = promedio mundial» al lado no es un titular: es un número
    suelto, que es justo lo que este proyecto no publica. */
export function hero(meta, lista) {
  const cifras = TITULARES.map(cod => lista.find(k => k.codigo === cod)).filter(Boolean);

  return `<section class="hero">
    <div class="hero-texto">
      <div>
        <p class="hero-kicker">${c.escapar(meta.institucion)}</p>
        <h1>${c.escapar(meta.titulo_plataforma)}</h1>
      </div>
      <p class="intro">Producción, impacto, colaboración y estructura temática de la
      actividad científica institucional indexada en <strong>Scopus</strong>, con las
      métricas normalizadas de <strong>SciVal</strong>. Cada indicador declara en su
      sello qué fuente lo sostiene, a qué fecha y sobre cuántos casos se calcula.</p>
    </div>
    <dl class="hero-cifras">${cifras.map(k => {
      const dec = Number.isInteger(k.valor) ? 0 : (k.sufijo === '%' ? 1 : 2);
      const ref = k.referencia !== undefined
        ? `${k.referencia} = ${c.escapar(k.referencia_etiqueta)}`
        : `sobre ${c.nf.format(k.denominador)} publicaciones`;
      return `
      <div>
        <dt class="cifra-display">${c.num(k.valor, dec)}${
          k.sufijo ? `<span class="suf">${c.escapar(k.sufijo)}</span>` : ''}</dt>
        <dd class="cifra-etq">${c.escapar(k.nombre)}<span>${ref}</span></dd>
      </div>`;
    }).join('')}</dl>
  </section>`;
}

/** Los KPI que NO subieron al titular. Se filtran aquí y no en la página para
    que el corte esté declarado en un solo sitio. */
export const kpisRestantes = lista => lista.filter(k => !TITULARES.includes(k.codigo));

/** Rejilla de tarjetas KPI. */
export function kpis(lista) {
  return lista.map(k => {
    const ayuda = AYUDA_KPI[k.codigo] ? c.botonAyuda(AYUDA_KPI[k.codigo]) : '';
    const sec = k.mediana !== undefined
      ? `<div class="secundario">Mediana: <strong>${c.num(k.mediana, 2)}</strong> ·
         referencia ${k.referencia} = ${k.referencia_etiqueta}</div>` : '';
    // Los porcentajes llevan un decimal; los enteros, ninguno. Dos decimales en
    // un porcentaje sugieren una precisión que el dato no tiene.
    const dec = Number.isInteger(k.valor) ? 0 : (k.sufijo === '%' ? 1 : 2);
    // La unidad del valor ('formas de firma') va bajo la etiqueta, no dentro
    // del número: intercalada rompe la línea y estorba la lectura.
    const unidad = k.etiqueta_valor
      ? `<div class="secundario">${c.escapar(k.etiqueta_valor)}</div>` : '';
    // La advertencia del indicador se pinta en la tarjeta, no sólo en el
    // artefacto: el puente entre las 589 formas de firma de la fuente y las 556
    // que publica el sitio se calculaba y no llegaba a ninguna pantalla.
    const aviso = k.nota && k.nota.texto
      ? `<div class="kpi-nota">${c.escapar(k.nota.texto)}</div>` : '';
    return `<article class="kpi">
      <div class="valor">${c.num(k.valor, dec)}${k.sufijo ? `<small>${k.sufijo}</small>` : ''}</div>
      <div class="etiqueta">${c.escapar(k.nombre)}${ayuda}</div>
      <div class="denominador">sobre ${c.nf.format(k.denominador)} publicaciones</div>
      ${unidad}${sec}${aviso}</article>`;
  }).join('');
}

/* Panorama: la portada no puede ser sólo un puñado de cifras. Tres cortes que
   responden «cuánto», «con quién» y «de qué», cada uno enlazado a su sección
   para que la portada oriente en vez de agotar. */
const PANORAMA = [
  ['P-02', 'produccion.html', s => c.barrasV(s.datos,
    { titulo: s.nombre, etiquetaX: 'anio', etiquetaY: 'n', ancho: 330, alto: 210 })],
  ['C-01', 'colaboracion.html', s => c.anillo(s.datos, { titulo: s.nombre })],
  ['T-05', 'tematica.html', s => c.barrasH(s.datos.slice(0, 6),
    { titulo: s.nombre, alto: 25, ancho: 330, trama: s.multivaluado })],
];

export function panorama(series) {
  const bloques = PANORAMA.filter(([cod]) => series[cod]);
  if (!bloques.length) return '';
  return `<h2 class="titulo-seccion">Panorama</h2>
    <div class="rejilla">${bloques.map(([cod, destino, dibujar]) => `
      <section class="modulo modulo-compacto">
        <header>
          <div class="modulo-id">
            <h2>${c.escapar(series[cod].nombre)}</h2>
            <span class="codigo">${cod}</span>
          </div>
        </header>
        ${dibujar(series[cod])}
        <p class="nota"><a class="enlace-seguir" href="${destino}">Ver la sección completa →</a></p>
      </section>`).join('')}</div>`;
}

/* El FWCI mediano (0,41) frente a la media (0,87) es el dato que más fácilmente
   se malinterpreta: se explicita en portada, no sólo en el módulo. */
export function lectura(kpisLista) {
  const fwci = kpisLista.find(k => k.codigo === 'I-03');
  if (!fwci) return '';
  return `<div class="modulo modulo-lectura">
    <h2>Cómo leer estas cifras</h2>
    <p>El FWCI compara las citas recibidas con las esperadas para
    publicaciones del mismo campo, año y tipo: <strong>1,0 es el promedio
    mundial</strong>. Aquí la media es ${c.num(fwci.valor, 2)} y la mediana
    ${c.num(fwci.mediana, 2)}. La diferencia entre ambas indica una
    distribución asimétrica: unas pocas publicaciones muy citadas elevan el
    promedio.</p>
    ${c.nota(fwci.nota)}
    <p class="nota">Cada indicador declara sobre cuántas publicaciones se
    calcula. No todas las publicaciones tienen métricas: el denominador
    cambia según el indicador.</p>
  </div>`;
}

/* ------------------------------------------------------------ catálogo */

/** El catálogo completo de indicadores: los 40 evaluados, no los 27 que se
    publican.

    POR QUÉ EXISTE
    El sitio mostraba 27 indicadores y no decía nada de los otros 13. Para un
    lector, «no está» tiene al menos tres lecturas incompatibles: no se midió,
    se midió y salió mal, o no se puede medir sin inventar el dato. Publicar el
    criterio es lo que separa un informe de una selección de cifras favorables.

    Es una tabla y no tarjetas a propósito: cuarenta entradas que se comparan
    entre sí se leen en columnas. Y va sin JavaScript —se pre-renderiza— porque
    es justo el contenido que alguien va a querer citar o archivar. */
export function catalogo(cat) {
  const { indicadores, resumen, categorias, etiquetas_estado: est } = cat;

  const resumenHTML = Object.entries(est)
    .filter(([e]) => resumen[e])
    .map(([e, [etq, detalle]]) => `
      <div class="kpi">
        <span class="valor">${resumen[e]}</span>
        <span class="etiqueta">${c.escapar(etq)}</span>
        <span class="secundario">${c.escapar(detalle)}</span>
      </div>`).join('');

  const fila = (r) => {
    const den = r.denominador
      ? `${c.escapar(r.denominador)}<br><span class="nota">${c.nf.format(r.denominador_valor)}</span>`
      : '<span class="sin-dato-txt">No aplica</span>';
    // El porqué de no publicarse va en su propia fila y no en una celda: es
    // prosa, y meterla en una columna la haría ilegible en las cuarenta.
    const motivo = [r.razon, r.estado !== 'publicado' ? r.advertencia : null]
      .filter(Boolean).join(' ');
    const extra = (motivo || r.que_falta) ? `
      <tr class="cat-motivo">
        <td colspan="6">
          ${motivo ? `<strong>Por qué:</strong> ${c.escapar(motivo)}` : ''}
          ${r.que_falta ? `<br><strong>Qué falta:</strong> ${c.escapar(r.que_falta)}` : ''}
        </td>
      </tr>` : '';
    return `
      <tr>
        <td><span class="codigo">${r.codigo}</span></td>
        <td>
          <strong>${c.escapar(r.nombre)}</strong>
          ${r.definicion ? `<br><span class="nota">${c.escapar(r.definicion)}</span>` : ''}
        </td>
        <td>${r.fuente ? c.escapar(r.fuente)
          : '<span class="sin-dato-txt">No se calcula</span>'}</td>
        <td>${den}</td>
        <td>${r.cobertura ? c.escapar(r.cobertura) : '—'}</td>
        <td><span class="estado" data-e="${r.estado}">${c.escapar(r.estado_etiqueta)}</span>
          ${r.confiabilidad ? `<br><span class="nota">confiabilidad ${c.escapar(r.confiabilidad)}</span>` : ''}
        </td>
      </tr>${extra}`;
  };

  const secciones = Object.entries(categorias).map(([clave, etiqueta]) => {
    const filas = indicadores.filter(r => r.categoria === clave);
    if (!filas.length) return '';
    return `
    <section class="modulo" id="cat-${clave}" tabindex="-1">
      <header><div class="modulo-id"><h2>${c.escapar(etiqueta)}</h2>
        <span class="codigo">${filas.length}</span></div></header>
      <div class="tabla-envoltura tabla-datos tabla-catalogo">
        <table>
          <thead><tr>
            <th scope="col">Cód.</th><th scope="col">Indicador y definición</th>
            <th scope="col">Fuente</th><th scope="col">Denominador</th>
            <th scope="col">Cobertura medida</th><th scope="col">Estado</th>
          </tr></thead>
          <tbody>${filas.map(fila).join('')}</tbody>
        </table>
      </div>
    </section>`;
  }).join('');

  const indice = Object.entries(categorias).map(([clave, etiqueta]) =>
    `<li><a href="#cat-${clave}"><span class="rail-txt">${c.escapar(etiqueta)}</span></a></li>`).join('');

  return `
    <div class="kpis" data-n="${Object.values(resumen).filter(Boolean).length}">${resumenHTML}</div>
    <p class="nota">Las coberturas están <strong>medidas sobre los datos</strong>,
    no estimadas: salen de <code>indicator_feasibility.csv</code>, que se
    regenera en cada build. Un indicador diferido está verificado como
    calculable; uno no calculable no lo está, y aproximarlo sería inventar la
    métrica.</p>
    <nav class="rail" aria-label="Categorías del catálogo">
      <p class="rail-titulo">En esta página</p><ol>${indice}</ol></nav>
    ${secciones}`;
}
