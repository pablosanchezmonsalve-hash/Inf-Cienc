/* paginas.js — renderizadores por página.
   Se despacha según data-pagina en <body>. */

import * as c from './core.js';
import * as v from './vista.js';
import * as X from './explorador.js';
import * as VX from './vista_explorador.js';

/* ============================================================== portada */

/* El pre-renderizador ya dejó este HTML escrito en el archivo. Repintarlo
   destruiría un LCP que ya ocurrió y volvería a pagar el coste de dibujar
   veinte SVG. Si el marcado está, sólo se enganchan los comportamientos. */
const yaPintado = el => el && el.dataset.prerender === '1';

/* La portada es un EXPLORADOR: el lector elige un recorte y las cifras y los
   gráficos se recalculan sobre él, aquí, sin volver al servidor.

   El HTML llega pre-renderizado con el recorte VACÍO —el informe completo—, así
   que sin JavaScript se ve el informe entero. Esta función no reescribe nada
   hasta que alguien toca un filtro: engancha el comportamiento y se aparta. */
async function portada() {
  const cabecera = document.getElementById('titular');
  const zonas = {
    estado: document.getElementById('estado-recorte'),
    controles: document.getElementById('controles'),
    cifras: document.getElementById('cifras'),
    cortes: document.getElementById('cortes'),
  };
  if (!zonas.cifras) return;

  const { publicaciones } = await c.cargar('publications.json');

  if (!yaPintado(zonas.cifras)) {
    const meta = await c.cargar('meta.json');
    const { kpis } = await c.cargar('kpis.json');
    if (cabecera) cabecera.innerHTML = VX.cabecera(meta);
    document.getElementById('lectura').innerHTML = v.lectura(kpis);
    document.getElementById('cierre').innerHTML = v.cierrePortada();
  }

  let sel = X.leerURL();

  function pintar({ nuevaEntrada = false } = {}) {
    const partes = VX.explorador(publicaciones, sel);
    // Se comparan los valores ANTES de reemplazar el marcado: la señal de
    // cambio sólo debe encenderse en las cifras que de verdad cambiaron.
    const antes = new Map([...zonas.cifras.querySelectorAll('[data-valor]')]
      .map(e => [e.dataset.valor, e.textContent]));

    zonas.estado.innerHTML = partes.estado;
    zonas.controles.innerHTML = partes.controles;
    zonas.cifras.innerHTML = partes.cifras;
    zonas.cortes.innerHTML = partes.cortes;

    zonas.cifras.querySelectorAll('[data-valor]').forEach(e => {
      if (antes.size && antes.get(e.dataset.valor) !== e.textContent) e.classList.add('cambia');
    });
    X.escribirURL(sel, !nuevaEntrada);
  }

  // Un solo escucha delegado para los chips y para el botón de limpiar: los
  // controles se repintan enteros a cada cambio, así que enganchar escuchas a
  // cada botón los dejaría colgando del marcado anterior.
  document.addEventListener('click', e => {
    const chip = e.target.closest('.chip[data-dim]');
    if (chip) {
      const { dim, valor } = chip.dataset;
      const actual = sel[dim] || [];
      sel = { ...sel, [dim]: actual.includes(valor)
        ? actual.filter(x => x !== valor) : [...actual, valor] };
      pintar({ nuevaEntrada: true });
      // El foco se pierde al reemplazar el marcado; se devuelve al mismo
      // control para que se pueda seguir filtrando con el teclado.
      const vuelta = zonas.controles.querySelector(
        `.chip[data-dim="${CSS.escape(dim)}"][data-valor="${CSS.escape(valor)}"]`);
      if (vuelta) vuelta.focus();
      return;
    }
    if (e.target.closest('#limpiar-recorte')) {
      sel = {};
      pintar({ nuevaEntrada: true });
      zonas.estado.querySelector('.recorte-n')?.scrollIntoView({ block: 'nearest' });
    }
  });

  // El recorte vive en la URL, así que el botón de volver del navegador tiene
  // que deshacer un filtro. Sin esto, volver saca al lector del sitio.
  addEventListener('popstate', () => { sel = X.leerURL(); pintar(); });

  if (!yaPintado(zonas.cifras) || X.hayRecorte(sel)) pintar();
}

/* ============================================================== módulos */

async function modulos() {
  const cont = document.getElementById('modulos');
  if (!yaPintado(cont)) {
    const codigos = cont.dataset.indicadores.split(',').map(s => s.trim());
    const series = await c.cargar('series.json');
    // El eje se identifica por el archivo, igual que en el pre-renderizado, y
    // por el mismo motivo: es la clave de la sección y ya está en la URL.
    const clave = (location.pathname.split('/').pop() || '').replace(/\.html$/, '');
    const { ejes } = await c.cargar('ejes.json');
    // El catálogo se pide para que un indicador declarado en la página pero no
    // publicado se dibuje como diferido en vez de desaparecer.
    const catalogo = await c.cargar('catalogo.json');
    cont.innerHTML = v.paginaModulos(codigos, series, ejes[clave], catalogo);
  }
  conmutadorVistas(cont);
  scrollSpy(cont);
}

/* Conmutador Gráfico ⇄ Tabla. Un solo escucha delegado para toda la página:
   con veinte módulos, veinte escuchas serían veinte veces el mismo código. */
function conmutadorVistas(raiz) {
  raiz.addEventListener('click', e => {
    const btn = e.target.closest('.vistas button');
    if (!btn) return;
    const modulo = btn.closest('.modulo');
    modulo.querySelectorAll('.vistas button').forEach(b =>
      b.setAttribute('aria-pressed', String(b === btn)));
    modulo.querySelectorAll(':scope > .vista').forEach(p =>
      p.dataset.activa = String(p.dataset.vista === btn.dataset.vista));
  });
}

/* Scroll-spy del índice lateral: marca el indicador que se está mirando.

   Se toma el que esté más arriba entre los visibles, no el último que entró:
   al desplazarse hacia arriba, «el último que entró» es el de abajo y el
   índice señalaba el módulo equivocado. El margen superior descuenta la
   cabecera para que un módulo cuente como activo cuando su título es visible,
   no cuando su borde toca el borde de la ventana. */
function scrollSpy(raiz) {
  const enlaces = new Map();
  raiz.querySelectorAll('.rail a').forEach(a =>
    enlaces.set(a.getAttribute('href').slice(1), a));
  if (!enlaces.size || !('IntersectionObserver' in window)) return;

  const visibles = new Set();
  const marcar = () => {
    const orden = [...enlaces.keys()].filter(id => visibles.has(id));
    enlaces.forEach((a, id) => {
      const activo = id === orden[0];
      a.classList.toggle('activo', activo);
      if (activo) a.setAttribute('aria-current', 'true');
      else a.removeAttribute('aria-current');
    });
  };
  const obs = new IntersectionObserver(entradas => {
    entradas.forEach(en => en.isIntersecting
      ? visibles.add(en.target.id) : visibles.delete(en.target.id));
    marcar();
  }, { rootMargin: '-88px 0px -55% 0px' });
  enlaces.forEach((_, id) => {
    const el = document.getElementById(id);
    if (el) obs.observe(el);
  });
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
        ${p.autores_uft.length
          ? `<br><span class="nota">${c.escapar(p.autores_uft.join(' · '))}</span>`
          // Una celda en blanco no distingue «no hay» de «no se muestra», y
          // aquí sí hay algo que decir: la publicación es institucional —la
          // afiliación la trajo— pero ninguna firma con nombre la sostiene.
          : '<br><span class="sin-dato-txt">Sin autoría UFT nombrada</span>'}</td>
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

  // El enlace de corrección va AQUÍ y no sólo en metodología: ésta es la página
  // donde alguien se encuentra a sí mismo mal representado, y es el momento en
  // que necesita saber qué puede hacer. `DATA_LICENSE.md` §4 lo exige.
  document.getElementById('aviso-autores').innerHTML = `
    <div class="nota-destacada"><b>Sobre estas cifras</b>${c.escapar(data.advertencia_identidad)}
      <br><a href="metodologia.html#correcciones">¿Su ficha tiene un error? Cómo se corrige →</a></div>`;

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
  // Sin identificador la página quedaba en blanco: ni encabezado —la ficha es
  // la única del sitio sin h1 propio en el archivo, porque lo pone el JS— ni
  // salida hacia ningún lado. Un callejón sin salida se corrige con una puerta.
  if (!id) {
    cont.innerHTML = `<h1>Ficha de autor</h1>
      <div class="vacio">La dirección no trae identificador de autor, así que no
      hay ficha que mostrar.<br><a href="autores.html">Ir al directorio de autores →</a></div>`;
    return;
  }

  let a;
  try { a = await c.cargar(`author/${id}.json`); }
  catch (e) { c.mostrarError(cont, e); return; }

  const i = a.indicadores;
  document.title = `${a.nombre_en_fuente} — Ficha de autor`;

  const idents = `
    <div><span>Nombre en fuente</span>${c.escapar(a.nombre_en_fuente)}</div>
    <div><span>Unidad académica</span>${c.escapar(a.unidades_academicas.join(' · '))}</div>
    <div><span>Scopus Author ID</span>${a.scopus_author_ids.length
      ? a.scopus_author_ids.map(s => `<a class="enlace-dato" href="https://www.scopus.com/authid/detail.uri?authorId=${s}"
          target="_blank" rel="noopener">${s}</a>`).join(' · ')
      : '<span class="sin-dato-txt">No resuelto</span>'}</div>
    <div><span>ORCID</span>${a.orcid
      ? `<a class="enlace-dato" href="https://orcid.org/${c.escapar(a.orcid)}" target="_blank" rel="noopener">${c.escapar(a.orcid)}</a>`
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
        <thead><tr><th scope="col">Año</th><th scope="col">Título</th><th scope="col">Fuente</th><th scope="col">Tipo</th><th scope="col" class="num">Citas</th></tr></thead>
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

async function catalogo() {
  const cont = document.getElementById('catalogo');
  // Pre-renderizado: repintar destruiría un LCP que ya ocurrió, y el marcado
  // sería idéntico porque lo produce esta misma función.
  if (!yaPintado(cont)) cont.innerHTML = v.catalogo(await c.cargar('catalogo.json'));
}

/* ══════════════════════════════════════════ teclado dentro de un gráfico */

/* Cada barra era un punto de tabulación. Medido en Áreas temáticas: 41 de los
   70 puntos de la página eran barras, así que pasar del primer gráfico al
   enlace siguiente costaba veinte pulsaciones de Tab. Un gráfico no es una
   lista de veinte controles: es UN control con veinte posiciones.

   Patrón de composición de las prácticas ARIA: el gráfico es un solo punto de
   tabulación y por dentro se recorre con las flechas. El tabindex «rueda» —la
   marca enfocada vale 0 y las demás −1—, así que al volver con Tab se entra
   por donde se salió y no por el principio.

   Con esto el recorrido de la página baja de 70 puntos a 32, y explorar el
   gráfico se vuelve más rápido en vez de más lento. */
function tecladoGraficos() {
  document.addEventListener('keydown', e => {
    const marca = e.target.closest?.('svg.chart g.marca');
    if (!marca) return;
    const marcas = [...marca.closest('svg.chart').querySelectorAll('g.marca')];
    const i = marcas.indexOf(marca);
    let j = null;
    // Las dos orientaciones responden a los cuatro cursores a propósito: el
    // lector no tiene por qué saber si la serie se dibujó en horizontal o en
    // vertical para poder recorrerla.
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') j = Math.min(i + 1, marcas.length - 1);
    else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') j = Math.max(i - 1, 0);
    else if (e.key === 'Home') j = 0;
    else if (e.key === 'End') j = marcas.length - 1;
    else return;

    e.preventDefault();
    if (j === i) return;
    marca.setAttribute('tabindex', '-1');
    marcas[j].setAttribute('tabindex', '0');
    marcas[j].focus();
  });
}

/* ============================================================== arranque */
const PAGINAS = { portada, modulos, publicaciones, autores, fichaAutor, metodologia, catalogo };

document.addEventListener('DOMContentLoaded', async () => {
  const pagina = document.body.dataset.pagina;
  const archivo = location.pathname.split('/').pop() || 'index.html';
  try {
    await c.montarCabecera(archivo);
    await c.montarAyuda();
    c.montarTooltip();
    if (PAGINAS[pagina]) await PAGINAS[pagina]();
    // Delegado en document: vale para los gráficos pre-renderizados y para los
    // que se repintan después de un filtro, sin volver a enganchar nada.
    tecladoGraficos();
  } catch (e) {
    c.mostrarError(document.getElementById('contenido') || document.body, e);
  }
});
