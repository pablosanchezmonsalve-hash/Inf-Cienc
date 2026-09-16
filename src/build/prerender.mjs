/* prerender.mjs — escribe el HTML del sitio en el build, no en el navegador.

   PROBLEMA QUE RESUELVE
   Hasta ahora `impacto.html` pesaba 1,3 KB y su cuerpo era `<div id="modulos">`
   vacío. Todo —cabecera, KPI, gráficos, tablas, sellos— aparecía después de que
   el navegador descargara dos módulos de JavaScript, resolviera un `fetch` y
   dibujara veinte SVG. Consecuencias medibles:

     · sin JavaScript el sitio no mostraba NADA. Ni el titular. Para un informe
       institucional que aspira a ser citable y archivable, eso es un defecto,
       no una limitación aceptable;
     · el LCP dependía de la cadena crítica más larga posible: HTML → módulo →
       fetch → parseo → dibujo;
     · un archivador web (o un buscador que no ejecute el módulo) guardaba una
       página en blanco.

   CÓMO
   Los constructores de marcado viven en web/assets/js/vista.js y no tocan el
   DOM. Este script los importa BAJO NODE, les pasa los mismos artefactos JSON
   que consumiría el navegador, y sustituye el contenido de los contenedores
   vacíos en dist/*.html.

   No hay una segunda implementación del marcado. Es el mismo código: por eso el
   HTML pre-renderizado no puede divergir del que produce el navegador.

   HIDRATACIÓN
   Cada contenedor rellenado se marca con `data-prerender="1"`. paginas.js lo
   consulta y, si está, se salta el repintado y sólo engancha los
   comportamientos. Repintar destruiría un LCP que ya ocurrió.

   Uso:  node src/build/prerender.mjs <dist>
*/

import { readFile, writeFile, readdir, stat } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const dist = resolve(process.argv[2] || 'dist');

const leerJSON = async (n) => JSON.parse(await readFile(join(dist, 'data', n), 'utf8'));
const mod = (n) => import(pathToFileURL(join(dist, 'assets', 'js', n)).href);

/** Rellena `<tag id="…" …></tag>` conservando los atributos que ya tenía.

   Se sustituye por posición del contenedor, no por un parser de HTML completo:
   los contenedores son elementos vacíos con id conocido, y meter una
   dependencia de parseo para eso sería pagar un árbol entero por un hueco.
   Si el contenedor no existe o no está vacío, se deja como está y se avisa: un
   pre-renderizado silencioso que no hizo nada es peor que uno que falla. */
function rellenar(html, id, contenido, aviso) {
  const re = new RegExp(`(<([a-z]+)([^>]*\\bid="${id}"[^>]*)>)\\s*(</\\2>)`, 'i');
  const m = html.match(re);
  if (!m) { aviso.push(id); return html; }
  return html.replace(re, `${m[1].replace('>', ' data-prerender="1">')}\n${contenido}\n${m[4]}`);
}

/* ── Inventario de la página «Descarga de datos» ──────────────────────────
   Qué se lista y cómo se cuenta cada archivo se declara aquí, junto a la
   lectura de los bytes reales: registros y tamaños no se escriben a mano. Un
   archivo de dist/data que no esté ni en CONJUNTOS ni en NO_LISTADOS, o uno
   declarado que falte, aborta el build: una página que dice listar lo que el
   sitio sirve no puede quedarse atrás en silencio. */
const PROC_ELSEVIER = (m) => `${m.fuentes.join(' · ')} · citas al ${m.fecha_corte_citas}`;
const CONJUNTOS = [
  { archivo: 'publications.json', unidad: 'publicaciones',
    describe: 'Una fila por publicación del universo, con sus metadatos y sus métricas.',
    registros: (j) => j.publicaciones.length, procedencia: (j, m) => PROC_ELSEVIER(m) },
  { archivo: 'authors.json', unidad: 'formas de firma',
    describe: 'Una entrada por forma de firma de la institución, con sus recuentos.',
    registros: (j) => j.autores.length, procedencia: (j, m) => PROC_ELSEVIER(m),
    nota: (j) => `Formas de firma, no personas. Sólo ${j.parametros.firmas_interpretables} de `
      + `${j.parametros.total_firmas} tienen al menos ${j.parametros.n_minimo_interpretable} publicaciones; `
      + 'por debajo, sus cifras no son interpretables ni comparables entre personas (DORA, Manifiesto de Leiden).' },
  { archivo: 'author/', dir: true, unidad: 'fichas',
    describe: 'Una ficha por forma de firma: lo mismo que muestra la página de cada autor.',
    procedencia: (j, m) => PROC_ELSEVIER(m), nota: () => 'Con las mismas salvedades que authors.json.' },
  { archivo: 'series.json', unidad: 'indicadores',
    describe: 'La serie de cada indicador publicado, calculada sobre el universo completo.',
    registros: (j) => Object.keys(j).filter((k) => k !== 'meta').length, procedencia: (j, m) => PROC_ELSEVIER(m) },
  { archivo: 'kpis.json', unidad: 'cifras',
    describe: 'Las cifras de cabecera del universo, con su denominador y su nota.',
    registros: (j) => j.kpis.length, procedencia: (j, m) => PROC_ELSEVIER(m) },
  { archivo: 'catalogo.json', unidad: 'indicadores',
    describe: 'Todos los indicadores evaluados, publicados o no, con la razón de los que no.',
    registros: (j) => j.indicadores.length, procedencia: (j, m) => PROC_ELSEVIER(m) },
  { archivo: 'facets.json', unidad: 'dimensiones',
    describe: 'Los valores de cada dimensión de filtro, con su recuento sobre el universo.',
    registros: (j) => Object.keys(j).filter((k) => k !== 'meta').length, procedencia: (j, m) => PROC_ELSEVIER(m) },
  { archivo: 'hierarchy.json', unidad: 'unidades',
    describe: 'Producción y citas por facultad y escuela.',
    registros: (j) => { const n = (x) => 1 + (x.hijos || []).reduce((a, h) => a + n(h), 0); return n(j.raiz) - 1; },
    // Sin fecha: el sello de este archivo hereda por defecto el corte de SciVal,
    // y sus citas son las del export de Scopus, que no declara fecha de corte.
    procedencia: (j) => `${j.procedencia.fuente} · citas del export de Scopus, que no declara fecha de corte`,
    // Las dos advertencias del propio archivo, no prosa aparte: cuenta pares y
    // suma citas de Scopus sobre ellos, así que no es un total institucional.
    nota: (j) => `${j.metodologia.n_publicaciones} ${j.metodologia.citas_totales}` },
  { archivo: 'validacion.json', unidad: 'reglas',
    describe: 'Las reglas de la auditoría de datos y el resultado de cada una.',
    registros: (j) => j.reglas.length, procedencia: (j, m) => `Auditoría del build del ${m.fecha_build}` },
  { archivo: 'glossary.json', unidad: 'entradas',
    describe: 'Las definiciones del glosario.',
    registros: (j) => j.entradas.length, procedencia: (j, m) => `Documentación del proyecto · build del ${m.fecha_build}` },
  { archivo: 'produccion_declarada.json', unidad: 'obras en la ventana, sin repetir entre fuentes',
    describe: 'Producción de la institución fuera de Scopus, declarada por las facultades o recuperada de repositorios y fuentes abiertas.',
    registros: (j) => j.total_fuera_de_scopus.en_ventana,
    procedencia: (j) => [j.procedencia, j.openalex_cobertura?.procedencia, j.autoarchivo_produccion?.procedencia,
      j.obras_externas?.procedencia].filter(Boolean).map((p) => p.fuente).join(' · ') },
  { archivo: 'fuentes_externas.json', unidad: 'obras',
    describe: 'Inventario de obras de fuentes institucionales que no están en el universo de Scopus.',
    registros: (j) => j.publicaciones.length,
    procedencia: (j) => `${(j.meta.fuentes || []).join(' · ')} · generado el ${j.meta.fecha_generacion}` },
  { archivo: 'meta.json', unidad: 'bloque',
    describe: 'La procedencia del build: fuentes, ventana, fechas y denominadores.',
    registros: () => 1, procedencia: (j) => `Build del ${j.fecha_build}` },
];
const NO_LISTADOS = [
  { archivo: 'ejes.json', motivo: 'textos de los paneles de sección' },
  { archivo: 'lecturas.json', motivo: 'textos «Qué muestra» de las figuras' },
  { archivo: 'informe.json', motivo: 'manifiesto del informe en PDF' },
];

async function inventarioDatos(meta) {
  const dir = join(dist, 'data');
  const nombres = (await readdir(dir, { withFileTypes: true }))
    .map((e) => (e.isDirectory() ? `${e.name}/` : e.name));
  const declarados = new Set([...CONJUNTOS, ...NO_LISTADOS].map((x) => x.archivo));
  const problemas = nombres.filter((n) => !declarados.has(n)).map((n) => `${n} sin clasificar`);
  const filas = [];
  for (const cj of CONJUNTOS) {
    if (!nombres.includes(cj.archivo)) { problemas.push(`${cj.archivo} declarado y ausente`); continue; }
    if (cj.dir) {
      const archivos = await readdir(join(dir, cj.archivo));
      let bytes = 0;
      for (const a of archivos) bytes += (await stat(join(dir, cj.archivo, a))).size;
      filas.push({ archivo: `data/${cj.archivo}`, ruta: null, describe: cj.describe, unidad: cj.unidad,
        registros: archivos.length, bytes, procedencia: cj.procedencia(null, meta), nota: cj.nota ? cj.nota(null) : null });
      continue;
    }
    const texto = await readFile(join(dir, cj.archivo), 'utf8');
    const j = JSON.parse(texto);
    const registros = cj.registros(j);
    if (!Number.isFinite(registros)) problemas.push(`${cj.archivo}: el recuento no es un número`);
    filas.push({ archivo: `data/${cj.archivo}`, ruta: `data/${cj.archivo}`, describe: cj.describe, unidad: cj.unidad,
      registros, bytes: Buffer.byteLength(texto, 'utf8'), procedencia: cj.procedencia(j, meta),
      nota: cj.nota ? cj.nota(j) : null });
  }
  return { filas, problemas };
}

async function main() {
  const c = await mod('core.js');
  const v = await mod('vista.js');
  const vx = await mod('vista_explorador.js');
  const hm = await mod('visualizations/heatmap.js');
  const tm = await mod('visualizations/treemap.js');

  const meta = await leerJSON('meta.json');
  const series = await leerJSON('series.json');
  // El mismo mapa que arma el navegador, con la misma función: el sello
  // pre-renderizado y el que se repinta al filtrar no pueden divergir.
  const proc = vx.procedencias(series, meta);
  const { kpis } = await leerJSON('kpis.json');
  const { ejes } = await leerJSON('ejes.json');
  const { publicaciones } = await leerJSON('publications.json');
  const catalogo = await leerJSON('catalogo.json');
  // Sólo lo usa C-05 (red de coautoría); el mismo mapa que arma el navegador
  // en paginas.js, para que el prerenderizado no divergan en qué unidad
  // muestra cada nodo.
  const autoresJson = await leerJSON('authors.json');
  const unidadPorPersona = new Map(
    autoresJson.autores.map(a => [a.nombre, (a.unidades || [])[0]]));
  const umbral = autoresJson.parametros?.n_minimo_interpretable;
  // Los textos que explican cada gráfico en el papel. Mismo origen que en el
  // navegador: el documento revisado y el catálogo, no cadenas escritas aquí.
  const { lecturas } = await leerJSON('lecturas.json');
  const catalogoJson = await leerJSON('catalogo.json');
  const textos = {
    lecturas,
    advertencias: Object.fromEntries(
      catalogoJson.indicadores.filter(i => i.advertencia).map(i => [i.codigo, i.advertencia])),
  };
  // Escuela -> facultad (P-07): mismo mapa que `meta.json` le da al navegador
  // (`common_build.build_meta()`), para que el pre-renderizado no diverja en
  // qué unidad agrega el gráfico.
  const jerarquia = meta.jerarquia || {};

  const archivos = (await readdir(dist)).filter(f => f.endsWith('.html'));
  const faltantes = [];
  let total = 0;

  for (const archivo of archivos) {
    const ruta = join(dist, archivo);
    let html = await readFile(ruta, 'utf8');
    const antes = html.length;

    // El cromo va en todas las páginas. `tema` se emite como 'auto' porque en
    // el build no hay preferencia guardada; el navegador corrige el botón
    // activo en cuanto arranca, sin repintar nada.
    const cromo = c.cromo(meta, archivo, 'auto');
    const av = [];
    html = rellenar(html, 'cabecera', cromo.cabecera, av);
    html = rellenar(html, 'vigencia', cromo.vigencia, av);
    html = rellenar(html, 'pie', cromo.pie, av);
    if (av.length) faltantes.push(`${archivo}: ${av.join(', ')}`);

    // Contenido específico de cada tipo de página. Las páginas cuyo contenido
    // depende del estado del usuario —filtros de publicaciones, ficha de autor
    // elegida por parámetro— NO se pre-renderizan: no hay un estado inicial
    // único que sirva, y emitir uno arbitrario sería inventar una vista.
    const tipo = (html.match(/<body[^>]*data-pagina="([^"]+)"/) || [])[1];

    if (tipo === 'portada') {
      const a = [];
      // La portada es un explorador. Se deja escrito el estado SIN FILTRAR,
      // que es exactamente el informe completo: quien llegue sin JavaScript ve
      // las cifras y los gráficos del conjunto entero, y sólo pierde la
      // capacidad de recortarlo. Los `details` de los filtros se abren y se
      // leen igual sin guion.
      const vacio = vx.explorador(publicaciones, {}, proc, jerarquia, meta, umbral, textos);
      html = rellenar(html, 'titular', vx.cabecera(meta), a);
      html = rellenar(html, 'estado-recorte', vacio.estado, a);
      html = rellenar(html, 'controles', vacio.controles, a);
      html = rellenar(html, 'cifras', vacio.cifras, a);
      html = rellenar(html, 'cortes', vacio.cortes, a);
      html = rellenar(html, 'dinamica', vacio.dinamica, a);
      html = rellenar(html, 'mas-citadas', vacio.masCitadas, a);
      html = rellenar(html, 'lectura', v.lectura(kpis), a);
      html = rellenar(html, 'cierre', v.cierrePortada(), a);
      if (a.length) faltantes.push(`${archivo}: ${a.join(', ')}`);
    } else if (tipo === 'seccion') {
      // Mismo explorador que la portada, con los cortes del eje. Se deja
      // escrito el estado sin filtrar: el informe completo.
      const a = [];
      const clave = (html.match(/data-seccion="([^"]+)"/) || [])[1];
      const titulo = c.tituloDeSeccion((html.match(/<title>([^<]*)/) || [])[1], clave);
      const sec = vx.seccion(publicaciones, {}, clave, proc, unidadPorPersona, jerarquia, meta, umbral, textos);
      html = rellenar(html, 'titular', vx.cabeceraSeccion(clave, titulo, ejes[clave]), a);
      html = rellenar(html, 'estado-recorte', sec.estado, a);
      html = rellenar(html, 'controles', sec.controles, a);
      html = rellenar(html, 'cifras', sec.cifras, a);
      html = rellenar(html, 'cortes', sec.cortes, a);
      html = rellenar(html, 'diferidos', vx.diferidos(catalogo, clave), a);
      // El mapa de calor (Bento Grid) sólo existe en produccion.html — las
      // demás páginas de tipo "seccion" no tienen `#heatmap-contenedor`, y
      // `rellenar()` lo reportaría en `faltantes` si se intentara ahí.
      // El ancho es una estimación razonable para la primera pintura sin
      // guion: el `ResizeObserver` de `montarHeatmap()` la corrige apenas
      // el navegador mide el contenedor real.
      if (archivo === 'produccion.html') {
        const agregado = hm.agregarMatriz(publicaciones);
        html = rellenar(html, 'heatmap-contenedor',
          hm.renderHeatmap(agregado, { ancho: 760 }), a);

        // Treemap: primer nivel (facultades) del árbol sin filtrar —
        // construirArbol() es la misma función que el navegador usa en cada
        // recorte, verificada contra hierarchy.json sobre el corpus
        // completo. Sólo el nivel 1 se pre-renderiza (nadie puede hacer
        // drill-down sin JavaScript de todos modos); `montarTreemap()`
        // hidrata el resto al cargar el módulo.
        const arbol = tm.construirArbol(publicaciones, jerarquia, meta.institucion_corta);
        const anchoTM = 760, altoTM = Math.round(anchoTM * 0.55);
        const nodosTM = tm.squarify(tm.aPlano(arbol.hijos), { ancho: anchoTM, alto: altoTM });
        const conHijosTM = n => !!(n._origen && n._origen.hijos && n._origen.hijos.length);
        html = rellenar(html, 'treemap-contenedor',
          `<div class="treemap-lienzo"><div class="treemap-capa">${tm.renderTreemap(nodosTM,
            { ancho: anchoTM, alto: altoTM, nivel: 'Facultad', conHijos: conHijosTM })}</div></div>`,
          a);
      }
      if (a.length) faltantes.push(`${archivo}: ${a.join(', ')}`);
    } else if (tipo === 'catalogo') {
      // Se pre-renderiza porque es contenido de referencia: es justo la página
      // que alguien va a citar o archivar, y una que exige JavaScript para
      // decir qué se publica y qué no vale de poco archivada.
      const a = [];
      html = rellenar(html, 'catalogo',
        v.catalogo(await leerJSON('catalogo.json'), vx.seccionDeGrafico()), a);
      if (a.length) faltantes.push(`${archivo}: ${a.join(', ')}`);
    } else if (tipo === 'produccionAmpliada') {
      const a = [];
      html = rellenar(html, 'produccion-declarada',
        v.produccionDeclarada(await leerJSON('produccion_declarada.json')), a);
      if (a.length) faltantes.push(`${archivo}: ${a.join(', ')}`);
    } else if (tipo === 'metodologia') {
      // El glosario es el destino de todo enlace `#slug` a una definición,
      // desde el tooltip de ayuda contextual o desde otra página (p. ej.
      // «Cómo se lee esta red →» en colaboracion.html). Sin pre-renderizar,
      // esos enlaces aterrizaban en un contenedor vacío: el ancla no existía.
      const a = [];
      const { entradas } = await leerJSON('glossary.json');
      const val = await leerJSON('validacion.json');
      const notaP01 = (kpis.find((k) => k.codigo === 'P-01') || {}).nota;
      html = rellenar(html, 'glosario', v.glosario(entradas), a);
      html = rellenar(html, 'ficha-tecnica-datos', v.fichaTecnica(meta, val, notaP01 && notaP01.texto), a);
      html = rellenar(html, 'validacion', v.validacion(val), a);
      // Misma razón que unidadPorPersona más abajo: esta cifra crece sola
      // (T-19 corre por cron), y sin pre-renderizarla un lector sin
      // JavaScript vería el hueco vacío que "hoy hay X de Y" deja al medio
      // de la frase — peor que la cifra vieja que este mismo cambio corrigió.
      const { autores: autoresOrcid } = await leerJSON('authors.json');
      const conOrcid = autoresOrcid.filter(a2 => a2.orcid).length;
      html = rellenar(html, 'orcid-cobertura',
        `${c.nf.format(conOrcid)} de ${c.nf.format(autoresOrcid.length)} formas de firma con ORCID`, a);
      if (a.length) faltantes.push(`${archivo}: ${a.join(', ')}`);
    } else if (tipo === 'fuentesexternas') {
      const a = [];
      try {
        const fe = await leerJSON('fuentes_externas.json');
        const { meta: fm, resumen, publicaciones: fp } = fe;
        html = rellenar(html, 'aviso-fuentes',
          `<b>Sobre este listado</b> ${c.escapar(fm.advertencia)}`, a);
        // El mismo constructor que usa el navegador. Aquí había una copia que
        // pedía `resumen.total_autores`, que el artefacto no trae, y publicaba
        // «NaN · Autores UFT».
        html = rellenar(html, 'kpis-fuentes', v.kpisFuentesExternas(fm, resumen), a);
        // Primera página de la tabla (50 filas), suficiente para sin-JS.
        const pag = fp.slice(0, 50);
        const tablaHtml = pag.map(p => `<tr><td>${p.anio || ''}</td>`
          + `<td>${p.doi ? `<a href="https://doi.org/${c.escapar(p.doi)}" target="_blank" rel="noopener">${c.escapar(p.titulo)}</a>` : c.escapar(p.titulo)}<br><span class="nota">${c.escapar(p.autor_uft)}</span></td>`
          + `<td>${c.escapar(p.fuente)}</td><td>${c.escapar(p.tipo)}</td></tr>`).join('');
        html = rellenar(html, 'tabla-cuerpo', tablaHtml, a);
        // Aquí se rellenaba también una tabla de autores. La capa pública ya no
        // trae `autores` ni la página tiene ese contenedor: la línea lanzaba
        // una excepción que el `catch` de abajo tragaba, después de haber escrito
        // lo anterior y sin que el build lo dijera.
      } catch (e) {
        console.error(`  fuentes-externas.html: sin datos fuentes_externas.json (${e.message})`);
      }
      if (a.length) faltantes.push(`${archivo}: ${a.join(', ')}`);
    }

    if (tipo === 'datos') {
      const a = [];
      const { filas, problemas } = await inventarioDatos(meta);
      problemas.forEach((p) => faltantes.push(`${archivo}: inventario · ${p}`));
      const notaP01 = (kpis.find((k) => k.codigo === 'P-01') || {}).nota;
      html = rellenar(html, 'datos-csv', v.datosCsv(meta), a);
      html = rellenar(html, 'datos-condiciones', v.datosCondiciones(meta, notaP01 && notaP01.texto), a);
      html = rellenar(html, 'datos-inventario', v.datosInventario(filas, NO_LISTADOS), a);
      if (a.length) faltantes.push(`${archivo}: ${a.join(', ')}`);
    }

    if (html.length !== antes) { await writeFile(ruta, html, 'utf8'); total++; }
    const kb = (Buffer.byteLength(html, 'utf8') / 1024).toFixed(1);
    console.log(`  ${archivo.padEnd(22)} ${String(kb).padStart(7)} KB`
      + (html.length === antes ? '   (sin cambios)' : ''));
  }

  if (faltantes.length) {
    console.error('\nCONTENEDORES NO ENCONTRADOS O NO VACÍOS:');
    faltantes.forEach(f => console.error(`  · ${f}`));
    process.exit(1);
  }
  console.log(`\n  ${total} páginas pre-renderizadas`);
}

main().catch(e => { console.error(e); process.exit(1); });
