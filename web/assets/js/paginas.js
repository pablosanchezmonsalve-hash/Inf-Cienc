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
const RENDER = {
  'P-02': s => c.barrasV(s.datos, { etiquetaX: 'anio', etiquetaY: 'n' }),
  'P-03': s => c.barrasH(s.datos),
  'P-05': s => c.barrasH(s.datos),
  'P-07': s => c.barrasH(s.datos, { maxEtiqueta: 42 }),
  'I-01': s => c.barrasV(s.datos, { etiquetaX: 'anio', etiquetaY: 'n' }),
  'I-04': s => c.barrasV(s.datos.map(d => ({ anio: d.anio, n: d.valor })),
    { etiquetaX: 'anio', etiquetaY: 'n', referencia: 1 }),
  'I-05': s => c.barrasH(s.datos),
  'R-01': s => c.barrasH(s.datos),
  'A-01': s => c.barrasH(s.datos),
  'C-01': s => c.anillo(s.datos),
  'C-03': s => c.barrasH(s.datos),
  'C-04': s => c.barrasH(s.datos, { maxEtiqueta: 40 }),
  'C-06': s => c.barrasH(s.datos),
  'T-05': s => c.barrasH(s.datos, { maxEtiqueta: 40 }),
  'T-01': s => c.barrasH(s.datos, { maxEtiqueta: 40 }),
  'T-04': s => c.barrasH(s.datos, { maxEtiqueta: 40 }),
};

const EXTRA = {
  'I-04': s => `<p class="nota">Publicaciones aún sin citas por año: ` +
    s.sin_citas_pct.map(x => `${x.anio}: <strong>${x.pct} %</strong>`).join(' · ') + `</p>`,
  'C-06': s => `<p class="nota">Media ${s.media} · <strong>mediana ${s.mediana}</strong>.
    La distribución es asimétrica: la mediana describe mejor el caso típico.</p>`,
  'P-05': s => `<p class="nota">Se muestran las 20 fuentes con más publicaciones,
    de ${c.nf.format(s.total_fuentes)} distintas.</p>`,
  'T-04': s => `<p class="nota"><strong>${c.nf.format(s.con_ods)}</strong> publicaciones
    tienen al menos un ODS asignado. Se reporta como recuento, no como
    distribución porcentual del total.</p>`,
};

async function modulos() {
  const cont = document.getElementById('modulos');
  const codigos = cont.dataset.indicadores.split(',').map(s => s.trim());
  const series = await c.cargar('series.json');

  cont.innerHTML = codigos.map(cod => {
    const s = series[cod];
    if (!s) return '';
    const grafico = (RENDER[cod] || (x => c.barrasH(x.datos)))(s);
    const extra = EXTRA[cod] ? EXTRA[cod](s) : '';
    return `<section class="modulo">
      <header><h2>${c.escapar(s.nombre)}</h2><span class="codigo">${cod}</span></header>
      ${s.nota && s.nota.destacada ? c.nota(s.nota) : ''}
      ${grafico}
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
      <td>${c.celda(p.anio)}</td>
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

  function pintar() {
    let f = lista.filter(a => (!soloInterpretables || a.interpretable));
    if (q) {
      const n = q.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
      f = f.filter(a => a.nombre.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().includes(n));
    }
    f.sort((x, y) => (asc ? 1 : -1) * ((x[orden] ?? 0) - (y[orden] ?? 0)) ||
      x.nombre.localeCompare(y.nombre));

    document.getElementById('resumen').innerHTML =
      `<strong>${c.nf.format(f.length)}</strong> de ${c.nf.format(parametros.total_firmas)} formas de firma` +
      (soloInterpretables ? ` · mostrando sólo n ≥ ${parametros.n_minimo_interpretable}` : '');

    document.getElementById('tabla-cuerpo').innerHTML = f.length ? f.map(a => `<tr>
      <td><a href="autor.html?id=${encodeURIComponent(a.id)}">${c.escapar(a.nombre)}</a>
        ${a.identidad_no_consolidada ? ' <span class="nota">identidad no consolidada</span>' : ''}</td>
      <td>${c.escapar(a.unidades.join(' · '))}</td>
      <td class="num">${c.celda(a.n_publicaciones)}</td>
      <td class="num">${c.celda(a.citas)}</td>
      <td class="num">${c.celda(a.citas_por_publicacion, 2)}</td>
      <td class="num">${c.celda(a.publicaciones_top10)}</td></tr>`).join('')
      : `<tr><td colspan="6"><div class="vacio">Ningún autor coincide.</div></td></tr>`;
  }

  document.getElementById('solo-interpretables').addEventListener('change', e => {
    soloInterpretables = e.target.checked; pintar();
  });
  document.getElementById('buscar-autor').addEventListener('input',
    c.debounce(e => { q = e.target.value; pintar(); }, 250));
  document.querySelectorAll('th[data-orden]').forEach(th => {
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
        // La confianza viaja visible: un ORCID emparejado por apellido e
        // inicial es una hipótesis verificable, no un dato de la fuente.
        + (a.orcid_confianza === 'media'
          ? ` <span class="nota">correspondencia probable</span>` : '')
      : `<span class="sin-dato-txt">${c.escapar(a.orcid_estado)}</span>`}</div>`;

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
      Con menos de ${a.meta.denominadores ? 5 : 5} publicaciones en la ventana, los indicadores
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
      ${c.barrasV(a.evolucion, { etiquetaX: 'anio', etiquetaY: 'n' })}
      <p class="nota">Tres años de ventana: se presenta como barras, no como línea de tendencia.</p>
    </section>

    <section class="modulo">
      <header><h2>Publicaciones (${a.publicaciones.length})</h2></header>
      <div class="tabla-envoltura"><table>
        <thead><tr><th>Año</th><th>Título</th><th>Fuente</th><th>Tipo</th><th class="num">Citas</th></tr></thead>
        <tbody>${a.publicaciones.map(p => `<tr>
          <td>${c.celda(p.anio)}</td>
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
    if (PAGINAS[pagina]) await PAGINAS[pagina]();
  } catch (e) {
    c.mostrarError(document.getElementById('contenido') || document.body, e);
  }
});
