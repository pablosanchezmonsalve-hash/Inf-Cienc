/* paginas.js — renderizadores por página.
   Se despacha según data-pagina en <body>. */

import * as c from './core.js';
import * as v from './vista.js';
import * as X from './explorador.js';
import * as VX from './vista_explorador.js';
import * as anim from './animar.js';
import { montarHeatmap } from './visualizations/heatmap.js';
import { montarTreemap, construirArbol } from './visualizations/treemap.js';

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
async function portada() { return montarExplorador(null); }

/* Las secciones son el mismo explorador con OTROS cortes. Se comparte la
   función entera en vez de duplicarla: filtros, estado, URL y navegación son
   idénticos, y lo único que cambia es qué se dibuja con el recorte. */
async function seccion() {
  const clave = document.getElementById('contenido')?.dataset.seccion;
  return montarExplorador(clave || null);
}

async function montarExplorador(claveSeccion) {
  const cabecera = document.getElementById('titular');
  const zonas = {
    estado: document.getElementById('estado-recorte'),
    controles: document.getElementById('controles'),
    cifras: document.getElementById('cifras'),
    cortes: document.getElementById('cortes'),
    // Sólo existen en produccion.html (Bento Grid). El resto de las
    // secciones no tiene estos contenedores y quedan en null — se
    // comprueban antes de usarlos, igual que zonas.diferidos.
    heatmap: document.getElementById('heatmap-contenedor'),
    treemap: document.getElementById('treemap-contenedor'),
  };
  if (!zonas.cifras) return;

  const { publicaciones } = await c.cargar('publications.json');

  // La procedencia de cada indicador. Se carga SIEMPRE, esté la página
  // pre-renderizada o no: al repintar un recorte los sellos se rehacen con él,
  // y sin este mapa saldrían sin fuente ni fecha.
  const metaBase = await c.cargar('meta.json');
  const proc = VX.procedencias(await c.cargar('series.json'), metaBase);
  // Escuela -> facultad (P-07): mismo criterio que agrega el build, para que
  // el gráfico reactivo no mezcle facultades y escuelas sueltas en una
  // misma lista de barras (ver `porFacultad()` en explorador.js).
  const jerarquia = metaBase.jerarquia || {};

  // Persona → unidad académica, sólo para C-05 (red de coautoría): una
  // publicación no trae la unidad por autor individual, así que el corte de
  // colaboración necesita esta tabla aparte. Se carga siempre —barato, un
  // Map de 538 entradas— para que funcione igual con o sin pre-renderizado.
  const unidadPorPersona = new Map(
    (await c.cargar('authors.json')).autores.map(a => [a.nombre, (a.unidades || [])[0]]));

  if (!yaPintado(zonas.cifras)) {
    const meta = await c.cargar('meta.json');
    if (cabecera) {
      cabecera.innerHTML = claveSeccion
        ? VX.cabeceraSeccion(claveSeccion, document.title.split('·')[0].trim(),
            (await c.cargar('ejes.json')).ejes[claveSeccion])
        : VX.cabecera(meta);
    }
    const lectura = document.getElementById('lectura');
    if (lectura) lectura.innerHTML = v.lectura((await c.cargar('kpis.json')).kpis);
    const cierre = document.getElementById('cierre');
    if (cierre) cierre.innerHTML = v.cierrePortada();

    // Los indicadores DIFERIDOS siguen apareciendo. Que un indicador esté
    // verificado y no se publique es información del informe: un hueco se
    // leería como que el fenómeno no existe. No responden al recorte —no se
    // calculan— y por eso van sobre su propio suelo, separados de lo que sí.
    const dif = document.getElementById('diferidos');
    if (dif && claveSeccion) {
      const catalogo = await c.cargar('catalogo.json');
      dif.innerHTML = VX.diferidos(catalogo, claveSeccion);
    }
  }

  let sel = X.leerURL();

  function pintar({ nuevaEntrada = false } = {}) {
    const partes = claveSeccion
      ? VX.seccion(publicaciones, sel, claveSeccion, proc, unidadPorPersona, jerarquia)
      : VX.explorador(publicaciones, sel, proc, jerarquia);
    // Se comparan los valores ANTES de reemplazar el marcado: la señal de
    // cambio sólo debe encenderse en las cifras que de verdad cambiaron.
    const antes = new Map([...zonas.cifras.querySelectorAll('[data-valor]')]
      .map(e => [e.dataset.valor, e.textContent]));

    zonas.estado.innerHTML = partes.estado;
    zonas.controles.innerHTML = partes.controles;
    zonas.cifras.innerHTML = partes.cifras;
    // Los cortes se repintan DENTRO de la transición: hay que medir la
    // geometría antes y después del cambio, y el orden sólo se garantiza si el
    // repintado ocurre en medio.
    anim.transicion(zonas.cortes, () => { zonas.cortes.innerHTML = partes.cortes; });

    // El mapa de calor de temáticas (Bento Grid) reacciona al mismo recorte
    // que el resto de la página: mismo criterio, un solo filtro. No lleva
    // pantalla de "sin datos" separada — montarHeatmap() ya la resuelve.
    if (zonas.heatmap) montarHeatmap(zonas.heatmap, X.recorte(publicaciones, sel));

    // El treemap cuenta pares autor×publicación (criterio de
    // 07_hierarchy.py, distinto del resto de la página) — construirArbol()
    // es el mismo cálculo portado a JS, verificado línea a línea contra
    // hierarchy.json sobre el corpus completo antes de usarse aquí (mismo
    // resultado, sin recorte). Se recalcula en TODO pintar(), incluida la
    // limpieza del recorte: si sólo se recalculara cuando hay filtro activo,
    // "Ver todo" habría dejado el treemap congelado en el último filtro.
    if (zonas.treemap) {
      montarTreemap(zonas.treemap,
        construirArbol(X.recorte(publicaciones, sel), jerarquia, metaBase.institucion_corta));
    }

    zonas.cifras.querySelectorAll('[data-valor]').forEach(e => {
      if (antes.size && antes.get(e.dataset.valor) !== e.textContent) e.classList.add('cambia');
    });
    X.escribirURL(sel, !nuevaEntrada);
    if (claveSeccion) scrollSpy(document.getElementById('contenido'));
  }

  // Un solo escucha delegado para los chips y para el botón de limpiar: los
  // controles se repintan enteros a cada cambio, así que enganchar escuchas a
  // cada botón los dejaría colgando del marcado anterior.
  document.addEventListener('click', e => {
    // C-05: fijar/soltar un nodo y resaltar sus coautores. Se resuelve sin
    // volver a pedir datos ni repintar `zonas.cortes` —a diferencia de un
    // filtro— porque no cambia el recorte, sólo qué se resalta.
    const nodoRed = e.target.closest('.nodo-red[data-red-nodo]');
    if (nodoRed) { alternarFocoRed(nodoRed); return; }
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

  // El conmutador Gráfico ⇄ Tabla se engancha al CONTENEDOR, no a cada corte:
  // los cortes se reemplazan enteros a cada recorte y los escuchas colgados de
  // ellos morirían con el marcado anterior.
  conmutadorVistas(zonas.cortes);
  anim.entradaAlVer(zonas.cortes);
  // El scroll-spy se re-engancha tras cada recorte: los cortes se reemplazan
  // y el observador anterior apuntaba a nodos que ya no están en el documento.
  if (claveSeccion) scrollSpy(document.getElementById('contenido'));

  // El recorte vive en la URL, así que el botón de volver del navegador tiene
  // que deshacer un filtro. Sin esto, volver saca al lector del sitio.
  addEventListener('popstate', () => { sel = X.leerURL(); pintar(); });

  if (!yaPintado(zonas.cifras) || X.hayRecorte(sel)) pintar();
}

/* Conmutador Gráfico ⇄ Tabla. Un solo escucha delegado para toda la página:
   con veinte módulos, veinte escuchas serían veinte veces el mismo código. */
function conmutadorVistas(raiz) {
  raiz.addEventListener('click', e => {
    const btn = e.target.closest('.vistas button');
    if (!btn) return;
    // `.corte` es el módulo del explorador. Sin esto el conmutador no
    // encontraba su contenedor y las secciones perdían la vista de tabla, que
    // es la vía equivalente al gráfico y no un extra.
    const modulo = btn.closest('.modulo, .corte');
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
  const zonas = {
    estado: document.getElementById('estado-recorte'),
    controles: document.getElementById('controles'),
  };
  let sel = X.leerURL();
  let pagina = 1;
  // Selección por casilla, independiente del recorte de filtros: sobrevive a
  // cambiar de página o de filtro, porque elegir publicaciones de a una para
  // exportarlas es justo el caso en que el lector NO quiere perder lo ya
  // marcado por tocar un chip sin querer. Sólo se limpia a mano.
  const seleccion = new Set();

  function pintar({ nuevaEntrada = false, soloTabla = false } = {}) {
    const res = X.recorte(pubs, sel);

    if (!soloTabla) {
      zonas.estado.innerHTML = VX.estado(res.length, pubs.length, sel);
      // El buscador se repinta con el resto, así que hay que devolverle el
      // foco y el cursor: si no, escribir una letra lo expulsa del campo.
      const antes = document.getElementById('q');
      const tenia = document.activeElement === antes;
      const pos = antes ? antes.selectionStart : null;
      zonas.controles.innerHTML = VX.controles(pubs, sel, { buscador: true });
      if (tenia) {
        const ahora = document.getElementById('q');
        ahora.focus();
        if (pos !== null) ahora.setSelectionRange(pos, pos);
      }
    }
    X.escribirURL(sel, !nuevaEntrada);

    const totalPag = Math.max(1, Math.ceil(res.length / POR_PAGINA));
    pagina = Math.min(pagina, totalPag);
    const pag = res.slice((pagina - 1) * POR_PAGINA, pagina * POR_PAGINA);
    const cuerpo = document.getElementById('tabla-cuerpo');

    if (!res.length) {
      cuerpo.innerHTML = `<tr><td colspan="7"><div class="vacio">
        <p>Ningún resultado con este recorte.</p></div></td></tr>`;
      document.getElementById('paginacion').innerHTML = '';
      pintarSeleccion();
      return;
    }
    cuerpo.innerHTML = pag.map(p => `<tr>
      <td class="col-marca"><label class="solo-lectores" for="marca-${c.escapar(p.eid)}">Seleccionar «${c.escapar(p.titulo)}»</label>
        <input type="checkbox" class="chk-fila" id="marca-${c.escapar(p.eid)}" data-eid="${c.escapar(p.eid)}" ${seleccion.has(p.eid) ? 'checked' : ''}></td>
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
    if (ant) ant.onclick = () => { pagina--; pintar({ soloTabla: true }); };
    if (sig) sig.onclick = () => { pagina++; pintar({ soloTabla: true }); };
    pintarSeleccion(pag);
  }

  /** Sincroniza la casilla «marcar todo» (indeterminada si sólo parte de la
      página está marcada) y el contador + estado del botón de exportar. */
  function pintarSeleccion(pag) {
    const todo = document.getElementById('marcar-todo');
    if (todo && pag) {
      const marcadas = pag.filter(p => seleccion.has(p.eid)).length;
      todo.checked = pag.length > 0 && marcadas === pag.length;
      todo.indeterminate = marcadas > 0 && marcadas < pag.length;
    }
    const n = seleccion.size;
    document.getElementById('estado-seleccion').textContent =
      n ? `${n} seleccionada${n === 1 ? '' : 's'}` : '';
    document.getElementById('exportar-seleccion').disabled = n === 0;
  }

  // Mismo escucha delegado que el explorador: los controles se repintan
  // enteros y los escuchas colgados de cada chip morirían con el marcado.
  document.addEventListener('click', e => {
    const chip = e.target.closest('.chip[data-dim]');
    if (chip) {
      const { dim, valor } = chip.dataset;
      const actual = sel[dim] || [];
      sel = { ...sel, [dim]: actual.includes(valor)
        ? actual.filter(x => x !== valor) : [...actual, valor] };
      pagina = 1; pintar({ nuevaEntrada: true });
      document.querySelector(
        `.chip[data-dim="${CSS.escape(dim)}"][data-valor="${CSS.escape(valor)}"]`)?.focus();
      return;
    }
    if (e.target.closest('#limpiar-recorte')) { sel = {}; pagina = 1; pintar({ nuevaEntrada: true }); }
    if (e.target.id === 'exportar') exportar(X.recorte(pubs, sel));
    if (e.target.id === 'exportar-seleccion') {
      exportar(pubs.filter(p => seleccion.has(p.eid)), { esSeleccion: true });
    }
  });

  document.addEventListener('input', c.debounce(e => {
    if (e.target.id !== 'q') return;
    sel = { ...sel, q: e.target.value || undefined };
    if (!sel.q) delete sel.q;
    pagina = 1; pintar();
  }, 250));

  // 'change', no 'click': una casilla también cambia con teclado (barra
  // espaciadora), y delegar en 'click' se la habría perdido.
  document.addEventListener('change', e => {
    if (e.target.id === 'marcar-todo') {
      const res = X.recorte(pubs, sel);
      const pag = res.slice((pagina - 1) * POR_PAGINA, pagina * POR_PAGINA);
      pag.forEach(p => e.target.checked ? seleccion.add(p.eid) : seleccion.delete(p.eid));
      pintar({ soloTabla: true });
      return;
    }
    const chk = e.target.closest('.chk-fila');
    if (chk) {
      chk.checked ? seleccion.add(chk.dataset.eid) : seleccion.delete(chk.dataset.eid);
      pintarSeleccion(X.recorte(pubs, sel).slice((pagina - 1) * POR_PAGINA, pagina * POR_PAGINA));
    }
  });

  addEventListener('popstate', () => { sel = X.leerURL(); pagina = 1; pintar(); });
  pintar();
}

/** La exportación arrastra la procedencia: un CSV sin fecha de corte deja de
    ser interpretable en cuanto sale del sitio. `esSeleccion` distingue en la
    propia cabecera si son las publicaciones marcadas a mano o todo el
    recorte de filtros — quien reabra el CSV meses después necesita saber
    cuál de las dos cosas está mirando, no sólo cuántas filas tiene. */
async function exportar(filas, { esSeleccion = false } = {}) {
  const meta = await c.cargar('meta.json');
  const cab = [
    `# ${meta.institucion} — ${meta.titulo_plataforma}`,
    `# Fuentes: ${meta.fuentes.join(', ')} | Ventana: ${meta.ventana.inicio}-${meta.ventana.fin}`,
    `# Citas actualizadas al ${meta.fecha_corte_citas} | Exportado desde el build ${meta.fecha_build}`,
    `# ${meta.advertencia_global}`,
    esSeleccion
      ? `# Selección manual: ${filas.length} ${filas.length === 1 ? 'publicación marcada' : 'publicaciones marcadas'} una por una, de ${meta.denominadores.universo_total} en total.`
      : `# Subconjunto exportado: ${filas.length} de ${meta.denominadores.universo_total} publicaciones`,
  ].join('\n');
  const cols = ['eid', 'anio', 'titulo', 'fuente', 'tipo', 'doi', 'citas', 'fwci', 'percentil_citacion', 'n_paises'];
  const esc = v => `"${String(v ?? '').replace(/"/g, '""')}"`;
  const csv = [cab, cols.join(','), ...filas.map(f => cols.map(k => esc(f[k])).join(','))].join('\n');
  const url = URL.createObjectURL(new Blob([`﻿${csv}`], { type: 'text/csv;charset=utf-8' }));
  const a = document.createElement('a');
  a.href = url;
  a.download = `publicaciones${esSeleccion ? '-seleccion' : ''}-${meta.fecha_build}.csv`;
  a.click();
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
  const idCrudo = new URLSearchParams(location.search).get('id');
  // Los identificadores que emite el propio build son slugs (letras, dígitos,
  // guion): `orellana-donoso-m`. Cualquier otra cosa en `?id=` no es un
  // identificador válido y se trata como ausente, no como ruta de `fetch`.
  const id = idCrudo && /^[a-z0-9-]{1,80}$/.test(idCrudo) ? idCrudo : null;
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

  // Coautoría interna de ESTA persona (C-05): quién más firma sus mismas
  // publicaciones. No hace falta el grafo entero para una ficha individual,
  // sólo cruzar sus propios EID contra `autores_uft` de cada publicación.
  const { publicaciones: todasPubs } = await c.cargar('publications.json');
  const idPorNombre = new Map((await c.cargar('authors.json')).autores.map(x => [x.nombre, x.id]));
  const misEid = new Set(a.publicaciones.map(p => p.eid));
  const pesoCoautor = new Map();
  for (const p of todasPubs) {
    if (!misEid.has(p.eid)) continue;
    for (const persona of (p.autores_uft || [])) {
      if (persona === a.nombre_en_fuente) continue;
      pesoCoautor.set(persona, (pesoCoautor.get(persona) || 0) + 1);
    }
  }
  const coautores = [...pesoCoautor.entries()]
    .sort((x, y) => y[1] - x[1] || x[0].localeCompare(y[0]));

  const i = a.indicadores;
  document.title = `${a.nombre_en_fuente} — Ficha de autor`;

  const idents = `
    <div><span>Nombre en fuente</span>${c.escapar(a.nombre_en_fuente)}</div>
    <div><span>Unidad académica</span>${c.escapar(a.unidades_academicas.join(' · '))}</div>
    <div><span>Scopus Author ID</span>${a.scopus_author_ids.length
      ? a.scopus_author_ids.map(s => `<a class="enlace-dato" href="https://www.scopus.com/authid/detail.uri?authorId=${encodeURIComponent(s)}"
          target="_blank" rel="noopener">${c.escapar(s)}</a>`).join(' · ')
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
      <header><h2>Coautoría interna (${coautores.length})</h2><span class="codigo">C-05</span></header>
      ${coautores.length ? `<div class="tabla-envoltura"><table>
        <thead><tr><th scope="col">Persona</th><th scope="col" class="num">Publicaciones compartidas</th></tr></thead>
        <tbody>${coautores.map(([nombre, n]) => {
          const otroId = idPorNombre.get(nombre);
          return `<tr><td>${otroId
            ? `<a href="autor.html?id=${encodeURIComponent(otroId)}">${c.escapar(nombre)}</a>`
            : c.escapar(nombre)}</td><td class="num">${n}</td></tr>`;
        }).join('')}</tbody></table></div>`
        : `<p class="vacio">Ninguna coautoría con otro autor UFT en esta ventana: sus
           publicaciones no comparten firma con otra persona detectada como afiliada a
           la institución. No significa que trabaje en solitario — puede coautorar con
           gente fuera de la UFT, que este corte no ve.</p>`}
      <p class="nota">Sólo cuenta coautoría <strong>interna</strong>: otra firma UFT en la
        misma publicación, dentro de esta ventana. <a href="colaboracion.html#C-05">Ver la
        red completa →</a></p>
    </section>`;
}

/* =========================================================== metodología */
async function metodologia() {
  const glosarioEl = document.getElementById('glosario');
  const procedenciaEl = document.getElementById('procedencia');
  const validacionEl = document.getElementById('validacion');
  if (yaPintado(glosarioEl) && yaPintado(procedenciaEl) && yaPintado(validacionEl)) return;
  const { entradas } = await c.cargar('glossary.json');
  const meta = await c.cargar('meta.json');
  glosarioEl.innerHTML = v.glosario(entradas);
  procedenciaEl.innerHTML = v.procedencia(meta);
  if (validacionEl) validacionEl.innerHTML = v.validacion(await c.cargar('validacion.json'));

  // La cifra de cobertura de ORCID crece sola (T-19 corre por cron mensual):
  // escribirla a mano en el HTML es exactamente cómo terminó diciendo
  // "216 de 556" cuando ya eran 280 de 538. Se calcula aquí, sobre el mismo
  // authors.json que sirve autores.html, para que nunca vuelva a desactualizarse.
  const orcidEl = document.getElementById('orcid-cobertura');
  if (orcidEl) {
    const { autores } = await c.cargar('authors.json');
    const total = autores.length;
    const conOrcid = autores.filter(a => a.orcid).length;
    orcidEl.textContent = `${c.nf.format(conOrcid)} de ${c.nf.format(total)} formas de firma con ORCID`;
  }
}

async function catalogo() {
  const cont = document.getElementById('catalogo');
  // Pre-renderizado: repintar destruiría un LCP que ya ocurrió, y el marcado
  // sería idéntico porque lo produce esta misma función.
  if (!yaPintado(cont)) cont.innerHTML = v.catalogo(await c.cargar('catalogo.json'));
}

async function produccionAmpliada() {
  const cont = document.getElementById('produccion-declarada');
  if (!yaPintado(cont)) cont.innerHTML = v.produccionDeclarada(await c.cargar('produccion_declarada.json'));
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
    // `g.nodo-red[tabindex]` generaliza la misma rotación a la red de
    // coautoría (C-05): sólo los nodos con `tabindex` ya puesto entran a la
    // tabulación (el tope de 90 por grado que fija `disponerRed()` en
    // core.js) — el resto del selector, y este bucle, no cambian.
    // `g.heatmap-celda`/`g.treemap-nodo` con `tabindex` reproducen el mismo
    // punto único de tabulación que ya tenían las barras: antes cada celda
    // llevaba `tabindex="0"` a mano (hasta 24 paradas en el mapa de calor de
    // producción.html), justo lo que este mecanismo existe para evitar.
    const marca = e.target.closest?.(
      'svg.chart g.marca, svg.chart g.nodo-red[tabindex], ' +
      'svg.chart g.heatmap-celda[tabindex], svg.chart g.treemap-nodo[tabindex]');
    if (marca) {
      const esRed = marca.classList.contains('nodo-red');
      const sel = esRed ? 'g.nodo-red[tabindex]'
        : marca.classList.contains('heatmap-celda') ? 'g.heatmap-celda[tabindex]'
        : marca.classList.contains('treemap-nodo') ? 'g.treemap-nodo[tabindex]'
        : 'g.marca';
      const marcas = [...marca.closest('svg.chart').querySelectorAll(sel)];
      const i = marcas.indexOf(marca);
      let j = null;
      // Las dos orientaciones responden a los cuatro cursores a propósito: el
      // lector no tiene por qué saber si la serie se dibujó en horizontal o en
      // vertical para poder recorrerla. La red da la vuelta al llegar a una
      // punta (mismo criterio que ya tenía `pasoTecladoRed`, ahora inline);
      // las barras se quedan en el extremo, comportamiento sin cambios.
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        j = esRed ? (i + 1) % marcas.length : Math.min(i + 1, marcas.length - 1);
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        j = esRed ? (i - 1 + marcas.length) % marcas.length : Math.max(i - 1, 0);
      }
      else if (e.key === 'Home') j = 0;
      else if (e.key === 'End') j = marcas.length - 1;
      else if (esRed && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); alternarFocoRed(marca); return; }
      else if (esRed && e.key === 'Escape') { e.preventDefault(); soltarFocoRed(marca.closest('svg.red-svg')); return; }
      else return;

      e.preventDefault();
      if (j === i) return;
      marca.setAttribute('tabindex', '-1');
      marcas[j].setAttribute('tabindex', '0');
      marcas[j].focus();
      return;
    }
  });
}

/** C-05: fija (o suelta, si ya estaba fijado) el nodo `g` y resalta sus
    coautores directos — mismo patrón visual que el filtro atenúa las barras
    inactivas (`svg.chart.hay-foco .marca`), aplicado al nodo y sus vecinos
    en vez de a una serie. Puramente de marcado: no vuelve a pedir datos ni
    repinta el SVG, sólo alterna clases ya previstas en `app.css`. */
function alternarFocoRed(g) {
  const svg = g.closest('svg.red-svg');
  if (!svg) return;
  if (g.classList.contains('en-foco')) { soltarFocoRed(svg); return; }
  soltarFocoRed(svg, { mantenerHayFoco: true });
  svg.classList.add('hay-foco');
  g.classList.add('en-foco');
  const vecinos = new Set((g.dataset.vecinos || '').split(',').filter(Boolean));
  const i = g.dataset.redNodo;
  svg.querySelectorAll('.nodo-red[data-red-nodo]').forEach(n => {
    if (vecinos.has(n.dataset.redNodo)) n.classList.add('en-foco');
  });
  svg.querySelectorAll('.vinculo').forEach(l => {
    if (l.dataset.a === i || l.dataset.b === i) l.classList.add('en-foco');
  });
}

function soltarFocoRed(svg, { mantenerHayFoco = false } = {}) {
  if (!svg) return;
  svg.querySelectorAll('.en-foco').forEach(el => el.classList.remove('en-foco'));
  if (!mantenerHayFoco) svg.classList.remove('hay-foco');
}

/* ============================================================== arranque */
const PAGINAS = { portada, seccion, publicaciones, autores, fichaAutor, metodologia, catalogo, produccionAmpliada };

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
