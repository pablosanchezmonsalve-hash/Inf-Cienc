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
  // DESVIACIÓN, no magnitud: el FWCI se lee CONTRA el 1,00 mundial, así que el
  // 1,00 va en el eje y el déficit se lee sin aritmética mental (FT: Deviation).
  'I-04': s => c.desviacion(s.datos.map(d => ({ anio: d.anio, valor: d.valor })), {
    titulo: s.nombre, etiquetaX: 'anio', etiquetaY: 'valor', decimales: 2,
    referencia: 1, refEtiqueta: '1,00 — promedio mundial',
  }),
  // Los tramos son ACUMULADOS y anidados: las 3 del top 1 % están también en el
  // top 5, 10 y 25. Cuatro barras hermanas sugerían cuatro grupos disjuntos que
  // podrían sumarse —322, una cifra sin significado— (FT: Distribution).
  'I-05': s => c.acumulada(s.datos, { titulo: s.nombre, total: s.base_percentil }),
  // Q1–Q4 es una escala ORDENADA, no cuatro categorías sueltas: un solo tono en
  // cuatro pasos, del más oscuro (mejor posición) al más claro.
  'R-01': s => c.proporcional(s.datos, { titulo: s.nombre }),
  // Acceso abierto se queda en una sola serie a propósito: las categorías se
  // llaman Gold, Green y Bronze, y pintarlas con la paleta categórica dejaría
  // «Green» de color naranja. Cuando el nombre de la categoría ya es un color,
  // el color deja de estar disponible para codificar.
  'A-01': s => c.barrasH(s.datos, { titulo: s.nombre, trama: s.multivaluado }),
  'C-01': s => c.anillo(s.datos, { titulo: s.nombre }),
  'C-03': s => c.barrasH(s.datos, { titulo: s.nombre, trama: s.multivaluado }),
  'C-04': s => c.barrasH(s.datos, { titulo: s.nombre, trama: s.multivaluado }),
  // El tamaño del equipo es un continuo tramificado: ordenarlo por frecuencia
  // destruiría el eje, que es justo la información (FT: Distribution).
  'C-06': s => c.distribucion(s.datos, { titulo: s.nombre, etiquetaEje: 'autores por publicación' }),
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
        <h3>${c.escapar(s.nombre)}</h3>
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
        <h3>${c.escapar(r.nombre)}</h3>
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

  // Los diferidos se separan de los publicados porque van a bandas distintas:
  // lo que el informe NO sabe merece su propio suelo, no una tarjeta más en la
  // fila. Dentro de cada grupo se conserva el orden declarado en la página.
  const publicados = presentes.filter(cod => series[cod]);
  const diferidos = presentes.filter(cod => !series[cod]);

  const bandas = [];

  // 1 · APERTURA — qué responde la sección y qué NO responde. Va primero
  //     porque condiciona todo lo que viene después.
  bandas.push(banda('papel', panelEje(eje)));

  // 2 · TRABAJO — el índice y los módulos publicados. Es la banda de consulta:
  //     aquí la narrativa cede y manda la función de referencia.
  if (publicados.length) {
    bandas.push(banda('papel-2', `<h2 class="solo-lectores">Indicadores publicados</h2>
      <div class="disposicion">${
      rail(presentes, series, porCodigo)}<div class="modulos">${
      publicados.map(cod => modulo(cod, series[cod])).join('')}</div></div>`));
  }

  // 3 · AUSENCIA — sobre el suelo de contraste. Un indicador diferido metido
  //     entre los publicados se lee como uno más; aquí se lee como lo que es.
  if (diferidos.length) {
    bandas.push(banda('contraste', `
      <div class="banda-titulo">
        <p class="banda-gancho">Lo que esta sección todavía no puede mostrar</p>
        <h2>${diferidos.length === 1 ? 'Un indicador' : `${diferidos.length} indicadores`}
          de esta sección está${diferidos.length === 1 ? '' : 'n'} verificado${
          diferidos.length === 1 ? '' : 's'} pero no se publica${diferidos.length === 1 ? '' : 'n'}.</h2>
        <p>Se dice cuál y por qué. Un hueco se leería como que el fenómeno no existe.</p>
      </div>
      <div class="modulos">${diferidos.map(cod => moduloDiferido(cod, porCodigo[cod])).join('')}</div>`));
  }

  // 4 · CIERRE — sobre Peach, SÓLO tipografía y enlaces: sobre ese suelo el
  //     color del dato no despeja 4,5:1 y la marca de ausencia no despeja 3:1.
  bandas.push(banda('enfasis', cierre(eje)));

  return bandas.join('');
}

/** Envoltura de una banda: franja a sangre con su contenido en el contenedor. */
function banda(suelo, contenido) {
  return `<section class="banda banda-${suelo}"><div class="contenedor">${contenido}</div></section>`;
}

/** Banda de cierre: el denominador de la sección y la salida a las demás.

    Repite el denominador a propósito. Es la última cosa que se lee y la que
    más se cita de memoria: «823» y «816» no son la misma cifra medida dos
    veces, y decirlo una vez arriba no basta. */
function cierre(eje) {
  const salidas = c.PAGINAS
    .filter(([href]) => !['index.html', 'publicaciones.html', 'autores.html'].includes(href))
    .slice(0, 3);
  return `
    <div class="banda-titulo">
      <h2>Cada indicador declara su propio denominador.</h2>
      <p>${eje && eje.sobre_que ? c.escapar(eje.sobre_que)
        : 'Los denominadores del informe no son intercambiables.'}
        Ninguna sección los mezcla, y por eso dos cifras del mismo informe
        pueden medirse sobre conjuntos distintos sin contradecirse.</p>
    </div>
    <div class="banda-salidas">${salidas.map(([href, txt]) => `
      <a href="${href}"><strong>${c.escapar(txt)}</strong><span>Ver la sección →</span></a>`).join('')}
    </div>`;
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
            <h3>${c.escapar(series[cod].nombre)}</h3>
            <span class="codigo">${cod}</span>
          </div>
        </header>
        ${dibujar(series[cod])}
        <p class="nota"><a class="enlace-seguir" href="${destino}"
           aria-label="Ver la sección completa de ${c.escapar(series[cod].nombre)}"
           >Ver la sección completa →</a></p>
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

/** Banda de cierre de la portada: la salida a las secciones.

    Se genera en vez de escribirse en el HTML para que no pueda divergir de
    PAGINAS: si mañana se añade una sección, aparece aquí sola. Va sobre el
    suelo de énfasis, que sólo admite tipografía y enlaces. */
export function cierrePortada() {
  const salidas = c.PAGINAS.filter(([href]) =>
    ['produccion.html', 'impacto.html', 'colaboracion.html', 'tematica.html'].includes(href));
  return `
    <div class="banda-titulo">
      <h2>Cada indicador declara su propio denominador.</h2>
      <p>Las cifras de este informe no se miden todas sobre el mismo conjunto,
      y por eso dos de ellas pueden diferir sin contradecirse. Cada gráfico
      lleva pegada su fuente, su fecha de corte y sobre cuántos casos está
      medido.</p>
    </div>
    <div class="banda-salidas">${salidas.map(([href, txt]) => `
      <a href="${href}"><strong>${c.escapar(txt)}</strong><span>Ver la sección →</span></a>`).join('')}
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
      <tr id="${r.codigo}">
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

/** Producción ampliada: recuentos que una Facultad declara en su propio
    sitio, fuera del corpus indexado en Scopus. Es un corpus PARALELO
    declarado (D-206, D-341) — nunca aparece en los gráficos de
    producción/impacto del resto del sitio, y por eso vive en su propia
    página con su propio marcado, no reutilizando `RENDER`/`kpiCarta` de
    los indicadores Scopus/SciVal.

    El párrafo de transparencia (fuera de ventana / sin año) se compone
    aquí desde `datos.fuera_de_ventana_o_sin_anio` — nunca una cifra
    escrita a mano — porque ocultar esos registros habría sido tan
    engañoso como mezclarlos en un gráfico Scopus: la ventana temporal del
    proyecto no es motivo para que un dato declarado deje de contarse. */
export function produccionDeclarada(datos) {
  const { resumen, por_facultad_anio: filas, fuera_de_ventana_o_sin_anio: extra,
          ventana, procedencia: proc, nota, fuentes } = datos;

  if (!fuentes || !fuentes.length) {
    return `
    <p class="nota">Ninguna Facultad tiene, por ahora, un listado propio
    declarado en <code>config/sources.yml</code>. Esta sección aparece vacía
    a propósito: el dato es opcional, no un indicador que debiera existir.</p>`;
  }

  const kpi = (valor, etiqueta, secundario) => `
    <div class="kpi">
      <span class="valor">${c.nf.format(valor)}</span>
      <span class="etiqueta">${c.escapar(etiqueta)}</span>
      ${secundario ? `<span class="secundario">${c.escapar(secundario)}</span>` : ''}
    </div>`;

  const kpisHTML = [
    kpi(resumen.total_leido, 'Registros declarados',
      `por las Facultades participantes, ${resumen.duplicados_colapsados_por_doi} duplicados de la fuente ya colapsados`),
    kpi(resumen.en_universo_scopus, 'Ya en el universo Scopus',
      'divulgación: ya se cuentan en el resto del sitio, no se repiten aquí'),
    kpi(resumen.fuera_del_universo, 'Fuera del universo Scopus',
      'el conjunto que este corpus paralelo aporta de nuevo'),
    kpi(resumen.en_ventana, `En la ventana ${ventana.inicio}-${ventana.fin}`,
      'la cifra principal de la tabla de abajo'),
  ].join('');

  const filaTabla = (r) => `
    <tr><td>${c.escapar(r.facultad)}</td><td>${r.anio}</td>
      <td>${c.nf.format(r.n)}</td></tr>`;

  const tabla = filas.length ? `
    <div class="tabla-envoltura tabla-datos">
      <table>
        <thead><tr><th scope="col">Facultad</th><th scope="col">Año</th>
          <th scope="col">Publicaciones declaradas</th></tr></thead>
        <tbody>${filas.map(filaTabla).join('')}</tbody>
      </table>
    </div>` : `
    <p class="nota">Ninguna publicación declarada cae dentro de la ventana
    ${ventana.inicio}-${ventana.fin}. Ver la nota de transparencia abajo:
    no significa que no haya datos, sino que los que hay quedan fuera de
    esta ventana o sin año declarado.</p>`;

  const notaExtra = (extra || []).filter(e => e.fuera_de_ventana || e.sin_anio)
    .map(e => {
      const partes = [];
      if (e.fuera_de_ventana) partes.push(`${c.nf.format(e.fuera_de_ventana)} fuera de la ventana ${ventana.inicio}-${ventana.fin}`);
      if (e.sin_anio) partes.push(`${c.nf.format(e.sin_anio)} sin año declarado`);
      return `${c.escapar(e.facultad)}: ${partes.join(', ')}`;
    }).join('; ');

  return `
    <div class="kpis" data-n="4">${kpisHTML}</div>
    ${c.nota(nota)}
    <h2>Por Facultad y año, dentro de la ventana ${ventana.inicio}-${ventana.fin}</h2>
    ${tabla}
    ${notaExtra ? `<p class="nota">Registros declarados adicionales que
    quedan fuera de esta tabla, sin descartarse: ${notaExtra}.</p>` : ''}
    ${c.sello(proc)}
    <p class="nota">En esta página, «Cobertura» es el porcentaje de lo
    declarado que cae dentro de la ventana ${ventana.inicio}-${ventana.fin}
    — no el sentido habitual del sello en el resto del sitio (porcentaje de
    publicaciones con un dato poblado).</p>`;
}

/** La lista de procedencia de metodologia.html: fuentes, ventana temporal,
    fecha de corte de citas, export de origen y build. Vivía inline en
    paginas.js — se saca aquí por lo mismo que el resto del archivo: para que
    el prerenderizado no tenga una segunda copia del marcado. */
export function procedencia(meta) {
  return `
    <ul>
      <li>Fuentes: ${meta.fuentes.join(', ')}</li>
      <li>Ventana temporal: ${meta.ventana.inicio}–${meta.ventana.fin}</li>
      <li>Citas actualizadas al: <strong>${meta.fecha_corte_citas}</strong></li>
      <li>Export de origen: ${meta.fecha_export}</li>
      <li>Publicaciones: ${c.nf.format(meta.denominadores.universo_total)} ·
          con métricas: ${c.nf.format(meta.denominadores.con_metricas)} ·
          con autoría detallada: ${c.nf.format(meta.denominadores.con_autoria_detallada)}</li>
      <li>Build: ${meta.fecha_build}</li>
    </ul>`;
}

/** Estado de la auditoría de datos (V2-27): la misma tabla de 30 reglas que
    `docs/VALIDATION_REPORT.md`, publicada donde el sitio se ve. Antes vivía
    sólo en el repositorio — un informe que se declara riguroso y no deja
    ver su propia auditoría le pide al lector que confíe sin poder
    comprobar. El resumen va siempre visible; la tabla completa entra en
    `<details>` para no imponerse sobre el resto de la página. */
export function validacion(v) {
  const filas = v.reglas.map(r => `<tr class="${r.resultado === 'FALLA' ? 'val-falla' : ''}">
      <td class="mono">${c.escapar(r.regla)}</td>
      <td>${c.escapar(r.severidad)}</td>
      <td>${c.escapar(r.descripcion)}</td>
      <td>${r.resultado === 'FALLA' ? '<strong>FALLA</strong>' : 'Pasa'}</td>
      <td>${c.escapar(r.observado)}</td>
    </tr>`).join('');

  return `
    <p class="val-resumen">
      <strong>${c.nf.format(v.reglas_evaluadas)}</strong> reglas evaluadas ·
      <strong>${c.nf.format(v.pasan)}</strong> pasan ·
      <strong>${c.nf.format(v.fallan)}</strong> falla${v.fallan === 1 ? '' : 'n'} ·
      <strong>${c.nf.format(v.bloqueantes_fallando)}</strong> bloqueante${v.bloqueantes_fallando === 1 ? '' : 's'} fallando.
      Es la compuerta que el propio build no deja pasar si alguna regla bloqueante falla.
    </p>
    <details class="metodo">
      <summary>Ver las ${c.nf.format(v.reglas_evaluadas)} reglas, una por una</summary>
      <div class="metodo-cuerpo">
        <div class="tabla-envoltura"><table class="tabla-validacion">
          <thead><tr><th scope="col">Regla</th><th scope="col">Severidad</th>
            <th scope="col">Descripción</th><th scope="col">Resultado</th>
            <th scope="col">Observado</th></tr></thead>
          <tbody>${filas}</tbody>
        </table></div>
      </div>
    </details>`;
}

/** El glosario completo de metodologia.html, una sección por término con
    `id="{slug}"`. Es el destino de todo enlace `#slug` que apunte a una
    definición —desde el tooltip de ayuda contextual o desde otra página,
    como «Cómo se lee esta red →» en colaboracion.html— y por eso tiene que
    pre-renderizarse: sin JavaScript, esos enlaces aterrizaban en un
    contenedor vacío y el ancla no existía. */
export function glosario(entradas) {
  return entradas.map(e => `
    <section class="modulo" id="${e.slug}">
      <h2>${c.escapar(e.termino)}</h2>
      <p>${c.escapar(e.corto)}</p>
      ${e.extendido ? `<p class="nota">${c.escapar(e.extendido)}</p>` : ''}
    </section>`).join('');
}
