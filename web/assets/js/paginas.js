/* paginas.js — renderizadores por página.
   Se despacha según data-pagina en <body>. */

import * as c from './core.js';

/* ================================================================= KPIs */
async function portada() {
  const cont = document.getElementById('kpis');
  const { kpis } = await c.cargar('kpis.json');

  const AYUDA = {
    'I-03': 'FWCI', 'C-01': 'Colaboración internacional',
    'P-06': 'Formas de firma', 'I-01': 'Fecha de corte',
  };

  // El recuento gobierna la repartición de la rejilla: seis tarjetas en una
  // rejilla automática dejaban cinco arriba y una huérfana abajo.
  cont.dataset.n = String(kpis.length);

  cont.innerHTML = kpis.map(k => {
    const ayuda = AYUDA[k.codigo] ? c.botonAyuda(AYUDA[k.codigo]) : '';
    const sec = k.mediana !== undefined
      ? `<div class="secundario">Mediana: <strong>${c.num(k.mediana, 2)}</strong> ·
         referencia ${k.referencia} = ${k.referencia_etiqueta}</div>` : '';
    // Los porcentajes llevan un decimal; los enteros, ninguno. Dos decimales en
    // un porcentaje sugieren una precisión que el dato no tiene.
    const dec = Number.isInteger(k.valor) ? 0 : (k.sufijo === '%' ? 1 : 2);
    // La unidad del valor ('formas de firma') va bajo la etiqueta, no dentro
    // del número: intercalada rompe la línea y estorba la lectura.
    const unidad = k.etiqueta_valor
      ? `<div class="secundario">${c.escapar(k.etiqueta_valor)}, no personas distintas</div>` : '';
    return `<article class="kpi">
      <div class="valor">${c.num(k.valor, dec)}${k.sufijo ? ' ' + k.sufijo : ''}</div>
      <div class="etiqueta">${c.escapar(k.nombre)}${ayuda}</div>
      <div class="denominador">sobre ${c.nf.format(k.denominador)} publicaciones</div>
      ${unidad}${sec}</article>`;
  }).join('');

  // Panorama: la portada no puede ser sólo seis cifras. Tres cortes que
  // responden «cuánto», «con quién» y «de qué», cada uno enlazado a su sección
  // para que la portada oriente en vez de agotar.
  const series = await c.cargar('series.json');
  // Lienzos estrechos: estas tarjetas viven en una rejilla de tres columnas.
  const panorama = [
    ['P-02', 'produccion.html', s => c.barrasV(s.datos,
      { titulo: s.nombre, etiquetaX: 'anio', etiquetaY: 'n', ancho: 330, alto: 210 })],
    ['C-01', 'colaboracion.html', s => c.anillo(s.datos, { titulo: s.nombre })],
    ['T-05', 'tematica.html', s => c.barrasH(s.datos.slice(0, 6),
      { titulo: s.nombre, alto: 25, ancho: 330 })],
  ].filter(([cod]) => series[cod]);

  document.getElementById('panorama').innerHTML = `
    <h2 class="titulo-seccion">Panorama</h2>
    <div class="rejilla">${panorama.map(([cod, destino, dibujar]) => `
      <section class="modulo">
        <header>
          <h2>${c.escapar(series[cod].nombre)}</h2>
          <span class="codigo">${cod}</span>
        </header>
        ${dibujar(series[cod])}
        <p class="nota"><a href="${destino}">Ver la sección completa →</a></p>
      </section>`).join('')}</div>`;

  // El FWCI mediano (0,41) frente a la media (0,87) es el dato que más
  // fácilmente se malinterpreta: se explicita en portada, no sólo en el módulo.
  const fwci = kpis.find(k => k.codigo === 'I-03');
  if (fwci) {
    document.getElementById('lectura').innerHTML = `
      <div class="modulo">
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
}

/* ============================================================== módulos */

/* El color por serie se reserva a los cortes CATEGÓRICOS —vías de acceso
   abierto, cuartiles, países— donde cada barra es una entidad distinta. Un
   ranking por volumen se queda en una sola serie: colorear por posición haría
   que el color siguiera al rank y no a la entidad, y repintaría los
   supervivientes en cuanto cambiara el recorte. */
/* `cuotaValida` habilita el «% de lo mostrado» en el tooltip. Se activa SÓLO
   donde las barras son realmente partes de un total: no en umbrales encajados
   (I-05), no en multivaluados (A-01, C-03, C-04, T-01, T-04, T-05) y no en
   rankings recortados (P-05), donde un porcentaje afirmaría algo falso. */
const RENDER = {
  'P-02': s => c.barrasV(s.datos, { titulo: s.nombre, etiquetaX: 'anio', etiquetaY: 'n' }),
  'P-03': s => c.barrasH(s.datos, { titulo: s.nombre, cuotaValida: true }),
  'P-05': s => c.barrasH(s.datos, { titulo: s.nombre }),
  'P-07': s => c.barrasH(s.datos, { titulo: s.nombre, cuotaValida: true }),
  'I-01': s => c.barrasV(s.datos, { titulo: s.nombre, etiquetaX: 'anio', etiquetaY: 'n' }),
  'I-04': s => c.barrasV(s.datos.map(d => ({ anio: d.anio, n: d.valor })), {
    titulo: s.nombre, etiquetaX: 'anio', etiquetaY: 'n', decimales: 2,
    referencia: 1, refEtiqueta: '1,00 — promedio mundial',
  }),
  'I-05': s => c.barrasH(s.datos, { titulo: s.nombre }),
  // Q1–Q4 es una escala ORDENADA, no cuatro categorías sueltas: un solo tono en
  // cuatro pasos, del más oscuro (mejor posición) al más claro.
  'R-01': s => c.barrasH(s.datos, { titulo: s.nombre, escala: 'ordinal', cuotaValida: true }),
  // Acceso abierto se queda en una sola serie a propósito: las categorías se
  // llaman Gold, Green y Bronze, y pintarlas con la paleta categórica dejaría
  // «Green» de color naranja. Cuando el nombre de la categoría ya es un color,
  // el color deja de estar disponible para codificar.
  'A-01': s => c.barrasH(s.datos, { titulo: s.nombre }),
  'C-01': s => c.anillo(s.datos, { titulo: s.nombre }),
  'C-03': s => c.barrasH(s.datos, { titulo: s.nombre }),
  'C-04': s => c.barrasH(s.datos, { titulo: s.nombre }),
  'C-06': s => c.barrasH(s.datos, { titulo: s.nombre, cuotaValida: true }),
  'T-05': s => c.barrasH(s.datos, { titulo: s.nombre }),
  'T-01': s => c.barrasH(s.datos, { titulo: s.nombre }),
  'T-04': s => c.barrasH(s.datos, { titulo: s.nombre }),
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
  // Varios indicadores ya lo dicen en su propia advertencia de config. Repetirlo
  // debajo no refuerza nada: dos avisos idénticos se leen como un descuido y
  // restan credibilidad al resto de las advertencias.
  if (/multivaluad|no sumable/i.test(s.nota?.texto || '')) return '';
  return `<p class="nota"><strong>Multivaluado:</strong> una publicación puede
    aparecer en varias barras, de modo que la suma de las barras supera el número
    de publicaciones. Las barras no son partes de un total.</p>`;
}

async function modulos() {
  const cont = document.getElementById('modulos');
  const codigos = cont.dataset.indicadores.split(',').map(s => s.trim());
  const series = await c.cargar('series.json');

  cont.innerHTML = codigos.map(cod => {
    const s = series[cod];
    if (!s) return '';
    const grafico = (RENDER[cod] || (x => c.barrasH(x.datos, { titulo: x.nombre })))(s);
    const extra = EXTRA[cod] ? EXTRA[cod](s) : '';
    return `<section class="modulo">
      <header><h2>${c.escapar(s.nombre)}</h2><span class="codigo">${cod}</span></header>
      ${s.nota && s.nota.destacada ? c.nota(s.nota) : ''}
      ${LECTURA[cod] || ''}
      ${grafico}
      ${avisoMultivaluado(s)}
      ${extra}
      ${s.nota && !s.nota.destacada ? c.nota(s.nota) : ''}
      ${c.tablaEquivalente(s.datos)}
    </section>`;
  }).join('');
}

/* ========================================================= publicaciones */
const POR_PAGINA = 50;

async function publicaciones() {
  const { publicaciones: pubs } = await c.cargar('publications.json');
  const facetas = await c.cargar('facets.json');
  const estado = leerURL();
  let pagina = 1;

  const FILTROS = [
    ['anio', 'Año', facetas.anio],
    ['tipo', 'Tipo documental', facetas.tipo],
    ['qs_area', 'Área QS', facetas.qs_area],
    ['unidad', 'Unidad académica', facetas.unidad],
    ['open_access', 'Acceso abierto', facetas.open_access],
    ['internacional', 'Colaboración', facetas.internacional],
  ];

  function coincide(p, omitir = null) {
    for (const [clave] of FILTROS) {
      if (clave === omitir) continue;
      const sel = estado[clave];
      if (!sel || !sel.length) continue;
      let vals;
      if (clave === 'anio') vals = [String(p.anio)];
      else if (clave === 'tipo') vals = [p.tipo];
      else if (clave === 'qs_area') vals = p.qs_area;
      else if (clave === 'unidad') vals = p.unidades.length ? p.unidades : ['Sin dato declarado'];
      else if (clave === 'open_access') vals = p.open_access.length ? p.open_access : ['Sin dato declarado'];
      else if (clave === 'internacional') vals = [p.es_internacional === null
        ? 'Sin dato declarado' : (p.es_internacional ? 'Internacional' : 'Nacional')];
      // OR dentro de un filtro, AND entre filtros.
      if (!vals.some(v => sel.includes(String(v)))) return false;
    }
    if (estado.q) {
      const q = estado.q.toLowerCase();
      const heno = `${p.titulo} ${p.fuente} ${p.autores_uft.join(' ')}`
        .normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
      if (!heno.includes(q.normalize('NFD').replace(/[\u0300-\u036f]/g, ''))) return false;
    }
    return true;
  }

  function pintarFiltros() {
    document.getElementById('filtros').innerHTML = FILTROS.map(([clave, etiqueta, opciones]) => {
      // Recuento calculado con los demás filtros activos: una faceta en 0 se
      // muestra deshabilitada, no se oculta (su ausencia es información).
      const visibles = publicacionesQue(clave);
      const items = opciones.map(o => {
        const n = contarFaceta(visibles, clave, o.valor);
        const sel = (estado[clave] || []).includes(String(o.valor));
        return `<label class="opcion ${n === 0 && !sel ? 'desactivada' : ''}">
          <input type="checkbox" value="${c.escapar(String(o.valor))}" data-filtro="${clave}"
            ${sel ? 'checked' : ''} ${n === 0 && !sel ? 'disabled' : ''}>
          ${c.escapar(String(o.valor))} <span class="n">${n}</span></label>`;
      }).join('');
      return `<div class="grupo-filtro"><span class="etiqueta">${etiqueta}</span>
        <div class="opciones">${items}</div></div>`;
    }).join('') + `
      <div class="grupo-filtro">
        <label for="q">Buscar en título, fuente o autor</label>
        <input type="search" id="q" value="${c.escapar(estado.q || '')}" placeholder="Escriba para filtrar…">
      </div>
      <button class="boton" id="limpiar">Limpiar filtros</button>
      <button class="boton boton-primario" id="exportar">Exportar CSV</button>`;
  }

  const publicacionesQue = (omitir) => pubs.filter(p => coincide(p, omitir));

  function contarFaceta(lista, clave, valor) {
    return lista.filter(p => {
      if (clave === 'anio') return String(p.anio) === String(valor);
      if (clave === 'tipo') return p.tipo === valor;
      if (clave === 'qs_area') return p.qs_area.includes(valor);
      if (clave === 'unidad') return valor === 'Sin dato declarado'
        ? !p.unidades.length : p.unidades.includes(valor);
      if (clave === 'open_access') return valor === 'Sin dato declarado'
        ? !p.open_access.length : p.open_access.includes(valor);
      if (clave === 'internacional') {
        if (valor === 'Sin dato declarado') return p.es_internacional === null;
        return p.es_internacional === (valor === 'Internacional');
      }
      return false;
    }).length;
  }

  function pintar() {
    const res = pubs.filter(p => coincide(p));
    const chips = Object.entries(estado).flatMap(([k, v]) =>
      k === 'q' ? (v ? [[k, v]] : []) : (v || []).map(x => [k, x]))
      .map(([k, v]) => `<span class="chip">${c.escapar(String(v))}
        <button data-quitar="${k}" data-valor="${c.escapar(String(v))}" aria-label="Quitar filtro">×</button></span>`).join('');
    document.getElementById('chips').innerHTML = chips;

    const totalPag = Math.max(1, Math.ceil(res.length / POR_PAGINA));
    pagina = Math.min(pagina, totalPag);
    const pag = res.slice((pagina - 1) * POR_PAGINA, pagina * POR_PAGINA);

    document.getElementById('resumen').innerHTML =
      `<strong>${c.nf.format(res.length)}</strong> de ${c.nf.format(pubs.length)} publicaciones` +
      (res.length !== pubs.length ? ' · filtros aplicados' : '');

    const cuerpo = document.getElementById('tabla-cuerpo');
    if (!res.length) {
      cuerpo.innerHTML = `<tr><td colspan="6"><div class="vacio">
        <p>Ningún resultado con estos filtros.</p>
        <button class="boton" id="limpiar2">Limpiar filtros</button></div></td></tr>`;
      document.getElementById('limpiar2').onclick = limpiar;
      document.getElementById('paginacion').innerHTML = '';
      return;
    }
    cuerpo.innerHTML = pag.map(p => `<tr>
      <td>${c.anio(p.anio)}</td>
      <td>${p.doi ? `<a href="https://doi.org/${c.escapar(p.doi)}" target="_blank" rel="noopener">${c.escapar(p.titulo)}</a>`
        : c.escapar(p.titulo)}
        ${p.autores_uft.length ? `<br><span class="nota">${c.escapar(p.autores_uft.join(' · '))}</span>` : ''}</td>
      <td>${c.celda(p.fuente)}</td>
      <td>${c.celda(p.tipo)}</td>
      <td class="num">${p.tiene_metricas ? c.celda(p.citas) : '<span class="sin-dato-txt">Sin métricas</span>'}</td>
      <td class="num">${p.tiene_metricas ? c.celda(p.fwci, 2) : '<span class="sin-dato-txt">Sin métricas</span>'}</td>
    </tr>`).join('');

    document.getElementById('paginacion').innerHTML = totalPag > 1 ? `
      <button class="boton" id="ant" ${pagina === 1 ? 'disabled' : ''}>Anterior</button>
      <span>Página ${pagina} de ${totalPag}</span>
      <button class="boton" id="sig" ${pagina === totalPag ? 'disabled' : ''}>Siguiente</button>` : '';
    const ant = document.getElementById('ant'), sig = document.getElementById('sig');
    if (ant) ant.onclick = () => { pagina--; pintar(); };
    if (sig) sig.onclick = () => { pagina++; pintar(); };
  }

  function leerURL() {
    const p = new URLSearchParams(location.search), e = {};
    for (const [k, v] of p) e[k] = k === 'q' ? v : v.split('|');
    return e;
  }
  function escribirURL() {
    const p = new URLSearchParams();
    for (const [k, v] of Object.entries(estado)) {
      if (k === 'q' && v) p.set(k, v);
      else if (Array.isArray(v) && v.length) p.set(k, v.join('|'));
    }
    history.replaceState(null, '', p.toString() ? `?${p}` : location.pathname);
  }
  function refrescar() { escribirURL(); pintarFiltros(); pintar(); }
  function limpiar() { for (const k of Object.keys(estado)) delete estado[k]; pagina = 1; refrescar(); }

  document.getElementById('filtros').addEventListener('change', e => {
    const cb = e.target.closest('[data-filtro]'); if (!cb) return;
    const k = cb.dataset.filtro;
    estado[k] = estado[k] || [];
    if (cb.checked) estado[k].push(cb.value);
    else estado[k] = estado[k].filter(v => v !== cb.value);
    if (!estado[k].length) delete estado[k];
    pagina = 1; refrescar();
  });
  document.getElementById('filtros').addEventListener('input', c.debounce(e => {
    if (e.target.id !== 'q') return;
    estado.q = e.target.value || undefined;
    if (!estado.q) delete estado.q;
    pagina = 1; escribirURL(); pintar();
  }, 250));
  document.getElementById('filtros').addEventListener('click', e => {
    if (e.target.id === 'limpiar') limpiar();
    if (e.target.id === 'exportar') exportar(pubs.filter(p => coincide(p)));
  });
  document.getElementById('chips').addEventListener('click', e => {
    const b = e.target.closest('[data-quitar]'); if (!b) return;
    const k = b.dataset.quitar;
    if (k === 'q') delete estado.q;
    else { estado[k] = (estado[k] || []).filter(v => v !== b.dataset.valor); if (!estado[k].length) delete estado[k]; }
    refrescar();
  });

  refrescar();
}

/** La exportación arrastra la procedencia: un CSV sin fecha de corte deja de
    ser interpretable en cuanto sale del sitio. */
async function exportar(filas) {
  const meta = await c.cargar('meta.json');
  const cab = [
    `# ${meta.institucion} — ${meta.titulo_plataforma}`,
    `# Fuentes: ${meta.fuentes.join(', ')} | Ventana: ${meta.ventana.inicio}-${meta.ventana.fin}`,
    `# Citas actualizadas al ${meta.fecha_corte_citas} | Exportado desde el build ${meta.fecha_build}`,
    `# ${meta.advertencia_global}`,
    `# Subconjunto exportado: ${filas.length} de ${meta.denominadores.universo_total} publicaciones`,
  ].join('\n');
  const cols = ['eid', 'anio', 'titulo', 'fuente', 'tipo', 'doi', 'citas', 'fwci', 'percentil_citacion', 'n_paises'];
  const esc = v => `"${String(v ?? '').replace(/"/g, '""')}"`;
  const csv = [cab, cols.join(','), ...filas.map(f => cols.map(k => esc(f[k])).join(','))].join('\n');
  const url = URL.createObjectURL(new Blob([`﻿${csv}`], { type: 'text/csv;charset=utf-8' }));
  const a = document.createElement('a');
  a.href = url; a.download = `publicaciones-${meta.fecha_build}.csv`; a.click();
  URL.revokeObjectURL(url);
}

/* ================================================================ autores */
async function autores() {
  const data = await c.cargar('authors.json');
  const { autores: lista, parametros } = data;
  let soloInterpretables = true, orden = 'n_publicaciones', asc = false, q = '';

  document.getElementById('aviso-autores').innerHTML = `
    <div class="nota-destacada"><b>Sobre estas cifras</b>${c.escapar(data.advertencia_identidad)}</div>`;

  // El umbral estaba escrito en el HTML. Viene de config/publication.yml.
  document.getElementById('etiqueta-umbral').textContent =
    `Mostrar sólo firmas con ${parametros.n_minimo_interpretable} o más publicaciones`;

  function pintar() {
    let f = lista.filter(a => (!soloInterpretables || a.interpretable));
    if (q) {
      const sinTildes = t => t.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
      const n = sinTildes(q);
      // Se busca también entre las variantes fusionadas: quien llega con
      // «Giglio A.» desde Scopus no encontraría nada si sólo se mirara el
      // nombre canónico, y la ficha que busca existe con otro título.
      f = f.filter(a => [a.nombre, ...(a.variantes_consolidadas || [])]
        .some(x => sinTildes(x).includes(n)));
    }
    f.sort((x, y) => (asc ? 1 : -1) * ((x[orden] ?? 0) - (y[orden] ?? 0)) ||
      x.nombre.localeCompare(y.nombre));

    // La columna por la que se ordena se marca en todo su alto, no sólo en la
    // cabecera: con 51 filas en pantalla, una flecha arriba del todo se pierde.
    const ord = k => (k === orden ? ' ordenada' : '');

    const conOrcid = f.filter(a => a.orcid).length;
    // Por etiqueta, no por veredicto: las asignaciones que salieron del propio
    // registro también vienen «confirmada», pero por construcción, y sumarlas
    // aquí presentaría como verificación independiente lo que no lo es.
    const verificados = f.filter(a => a.orcid_veredicto_etiqueta === 'verificado').length;
    document.getElementById('resumen').innerHTML =
      `<strong>${c.nf.format(f.length)}</strong> de ${c.nf.format(parametros.total_firmas)} formas de firma` +
      (soloInterpretables ? ` · mostrando sólo n ≥ ${parametros.n_minimo_interpretable}` : '') +
      ` · <strong>${c.nf.format(conOrcid)}</strong> con ORCID recuperado` +
      // Sólo si la verificación se ha ejecutado: sin ella el recuento sería 0
      // y un 0 aquí se leería como «ninguno se verificó», que es falso.
      (verificados ? ` · <strong>${c.nf.format(verificados)}</strong> verificado${
        verificados === 1 ? '' : 's'} contra el registro de ORCID` : '');

    document.getElementById('tabla-cuerpo').innerHTML = f.length ? f.map(a => `<tr>
      <td><a href="autor.html?id=${encodeURIComponent(a.id)}">${c.escapar(a.nombre)}</a>
        ${a.identidad_no_consolidada
          ? ' <span class="etiqueta-en-linea">identidad no consolidada</span>' : ''}</td>
      <td>${a.orcid
        ? `<a class="etiqueta-en-linea etiqueta-orcid" href="https://orcid.org/${c.escapar(a.orcid)}"
             target="_blank" rel="noopener"
             title="ORCID recuperado desde Crossref · confianza ${c.escapar(a.orcid_confianza || '')}"
             >${c.escapar(a.orcid)}</a>`
          // Se marca todo lo que NO sea una verificación independiente. Las
          // verificadas son la norma y etiquetarlas sería ruido; el resto dice
          // qué evidencia tiene, incluidas las que sólo declara el titular.
          // En texto, no en color: el color solo no comunica.
          + (a.orcid_veredicto_clase && a.orcid_veredicto_clase !== 'verificado'
            ? ` <span class="nota nota-orcid-${c.escapar(a.orcid_veredicto_clase)}"
                 >${c.escapar(a.orcid_veredicto_etiqueta)}</span>` : '')
        : '<span class="sin-dato-txt">No disponible</span>'}</td>
      <td>${c.escapar(a.unidades.join(' · '))}</td>
      <td class="num${ord('n_publicaciones')}">${c.celda(a.n_publicaciones)}</td>
      <td class="num${ord('citas')}">${c.celda(a.citas)}</td>
      <td class="num${ord('citas_por_publicacion')}">${c.celda(a.citas_por_publicacion, 2)}</td>
      <td class="num${ord('publicaciones_top10')}">${c.celda(a.publicaciones_top10)}</td></tr>`).join('')
      : `<tr><td colspan="7"><div class="vacio">Ningún autor coincide.</div></td></tr>`;
  }

  document.getElementById('solo-interpretables').addEventListener('change', e => {
    soloInterpretables = e.target.checked; pintar();
  });
  document.getElementById('buscar-autor').addEventListener('input',
    c.debounce(e => { q = e.target.value; pintar(); }, 250));
  document.querySelectorAll('th[data-orden]').forEach(th => {
    // Enter y Espacio, además del clic: sin esto la tabla no se podía ordenar
    // sin ratón, porque un <th> no es un control activable por defecto.
    th.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); th.click(); }
    });
    th.addEventListener('click', () => {
      const k = th.dataset.orden;
      asc = (orden === k) ? !asc : false;
      orden = k;
      document.querySelectorAll('th[data-orden]').forEach(o =>
        o.setAttribute('aria-sort', o === th ? (asc ? 'ascending' : 'descending') : 'none'));
      pintar();
    });
  });
  pintar();
}

/* ============================================================ ficha autor */
async function fichaAutor() {
  const id = new URLSearchParams(location.search).get('id');
  const cont = document.getElementById('ficha');
  if (!id) { cont.innerHTML = '<div class="vacio">Falta el identificador de autor.</div>'; return; }

  let a;
  try { a = await c.cargar(`author/${id}.json`); }
  catch (e) { c.mostrarError(cont, e); return; }

  const i = a.indicadores;
  document.title = `${a.nombre_en_fuente} — Ficha de autor`;

  const idents = `
    <div><span>Nombre en fuente</span>${c.escapar(a.nombre_en_fuente)}</div>
    <div><span>Unidad académica</span>${c.escapar(a.unidades_academicas.join(' · '))}</div>
    <div><span>Scopus Author ID</span>${a.scopus_author_ids.length
      ? a.scopus_author_ids.map(s => `<a href="https://www.scopus.com/authid/detail.uri?authorId=${s}"
          target="_blank" rel="noopener">${s}</a>`).join(' · ')
      : '<span class="sin-dato-txt">No resuelto</span>'}</div>
    <div><span>ORCID</span>${a.orcid
      ? `<a href="https://orcid.org/${c.escapar(a.orcid)}" target="_blank" rel="noopener">${c.escapar(a.orcid)}</a>`
        // Qué evidencia respalda este ORCID, en orden de fuerza. El veredicto
        // sale de contrastar la asignación contra el registro del propio
        // titular, así que cuando existe desplaza a la confianza, que sólo
        // dice lo que opina nuestra heurística de emparejamiento.
        + (a.orcid_veredicto_etiqueta
          ? ` <span class="nota nota-orcid-${c.escapar(a.orcid_veredicto_clase)}"
                 title="${c.escapar(a.orcid_veredicto_detalle || '')}"
               >${c.escapar(a.orcid_veredicto_etiqueta)}</span>`
          : a.orcid_confianza === 'media'
            ? ` <span class="nota">correspondencia probable</span>` : '')
      : `<span class="sin-dato-txt">${c.escapar(a.orcid_estado)}</span>`}</div>`
    // Sin esto, una ficha con 24 publicaciones repartidas entre tres formas de
    // firma no se puede rastrear hasta Scopus: quien busque «Giglio A.» no
    // sabría que sus publicaciones están aquí.
    + (a.variantes_consolidadas && a.variantes_consolidadas.length > 1
      ? `<div><span>Formas de firma fusionadas</span>${
          a.variantes_consolidadas.map(v => c.escapar(v)).join(' · ')}</div>`
      : '');

  const kpi = (v, etq, dec = 0, ayuda = null) => `<article class="kpi">
    <div class="valor">${v === null ? '<span class="sin-dato-txt" style="font-size:1rem">No disponible</span>' : c.num(v, dec)}</div>
    <div class="etiqueta">${etq}${ayuda ? c.botonAyuda(ayuda) : ''}</div></article>`;

  cont.innerHTML = `
    <p class="migas"><a href="autores.html">Autores</a> › ${c.escapar(a.nombre_en_fuente)}</p>
    <div class="ficha-cabecera">
      <h1>${c.escapar(a.nombre_en_fuente)}</h1>
      <div class="identificadores">${idents}</div>
    </div>

    <div class="nota-destacada"><b>Cómo leer esta ficha</b>
      Los indicadores describen la producción indexada en Scopus entre
      ${a.meta.ventana.inicio} y ${a.meta.ventana.fin}, con citas actualizadas al
      ${a.meta.fecha_corte_citas}. No representan la trayectoria completa de la persona.
      Las métricas individuales sobre ventanas cortas y pocas publicaciones no son
      comparables entre personas ni deben usarse para evaluar desempeño individual.
      Este informe adhiere a los principios de DORA y del Manifiesto de Leiden.</div>

    ${a.advertencia_muestra_reducida ? `<div class="nota-destacada"><b>Muestra reducida</b>
      Con menos de ${a.umbral_interpretable} publicaciones en la ventana, los indicadores
      de impacto no son interpretables individualmente. Se muestran por transparencia,
      no para comparación.</div>` : ''}

    ${a.identidad_no_consolidada ? `<div class="nota-destacada"><b>Identidad no consolidada</b>
      Esta firma está asociada a más de un identificador de autor en la fuente. La
      consolidación de identidades requiere validación institucional u ORCID, pendientes.</div>` : ''}

    <div class="kpis">
      ${kpi(i.n_publicaciones, 'Publicaciones')}
      ${kpi(i.citas_totales, 'Citas', 0, 'Fecha de corte')}
      ${kpi(i.citas_por_publicacion, 'Citas por publicación', 2)}
      ${kpi(i.h_index_ventana, 'h-index en ventana', 0, 'h-index en ventana')}
      ${kpi(i.publicaciones_top10, 'En el top 10 % de citación', 0, 'Percentil de citación')}
    </div>

    <p class="nota">El FWCI no se muestra a nivel de autor: no es el promedio de los
    FWCI de sus publicaciones y la fuente no lo entrega a nivel de persona.
    En su lugar se reporta la presencia en el top 10 % de citación, que sí está
    normalizado por campo. Ver <a href="metodologia.html">metodología</a>.</p>

    <section class="modulo">
      <header><h2>Evolución temporal</h2><span class="codigo">AU-06</span></header>
      ${c.barrasV(a.evolucion, { titulo: 'Publicaciones por año', etiquetaX: 'anio', etiquetaY: 'n' })}
      <p class="nota">Tres años de ventana: se presenta como barras, no como línea de tendencia.</p>
    </section>

    <section class="modulo">
      <header><h2>Publicaciones (${a.publicaciones.length})</h2></header>
      <div class="tabla-envoltura"><table>
        <thead><tr><th>Año</th><th>Título</th><th>Fuente</th><th>Tipo</th><th class="num">Citas</th></tr></thead>
        <tbody>${a.publicaciones.map(p => `<tr>
          <td>${c.anio(p.anio)}</td>
          <td>${p.doi ? `<a href="https://doi.org/${c.escapar(p.doi)}" target="_blank" rel="noopener">${c.escapar(p.titulo)}</a>` : c.escapar(p.titulo)}</td>
          <td>${c.celda(p.fuente)}</td>
          <td>${c.celda(p.tipo)}</td>
          <td class="num">${p.tiene_metricas ? c.celda(p.citas) : '<span class="sin-dato-txt">Sin métricas</span>'}</td>
        </tr>`).join('')}</tbody></table></div>
    </section>

    <section class="modulo">
      <header><h2>Coautoría</h2><span class="codigo">C-05</span></header>
      <p class="nota">La red de coautoría se difiere a una versión posterior: heredaría
      las variantes de nombre aún sin consolidar y mostraría a una misma persona como
      varios nodos distintos.</p>
    </section>`;
}

/* =========================================================== metodología */
async function metodologia() {
  const { entradas } = await c.cargar('glossary.json');
  const meta = await c.cargar('meta.json');
  document.getElementById('glosario').innerHTML = entradas.map(e => `
    <section class="modulo" id="${e.slug}">
      <h2>${c.escapar(e.termino)}</h2>
      <p>${c.escapar(e.corto)}</p>
      ${e.extendido ? `<p class="nota">${c.escapar(e.extendido)}</p>` : ''}
    </section>`).join('');
  document.getElementById('procedencia').innerHTML = `
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

/* ============================================================== arranque */
const PAGINAS = { portada, modulos, publicaciones, autores, fichaAutor, metodologia };

document.addEventListener('DOMContentLoaded', async () => {
  const pagina = document.body.dataset.pagina;
  const archivo = location.pathname.split('/').pop() || 'index.html';
  try {
    await c.montarCabecera(archivo);
    await c.montarAyuda();
    c.montarTooltip();
    if (PAGINAS[pagina]) await PAGINAS[pagina]();
  } catch (e) {
    c.mostrarError(document.getElementById('contenido') || document.body, e);
  }
});
