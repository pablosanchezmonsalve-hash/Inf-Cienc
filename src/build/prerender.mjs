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

import { readFile, writeFile, readdir } from 'node:fs/promises';
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
  const unidadPorPersona = new Map(
    (await leerJSON('authors.json')).autores.map(a => [a.nombre, (a.unidades || [])[0]]));
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
      const vacio = vx.explorador(publicaciones, {}, proc, jerarquia);
      html = rellenar(html, 'titular', vx.cabecera(meta), a);
      html = rellenar(html, 'estado-recorte', vacio.estado, a);
      html = rellenar(html, 'controles', vacio.controles, a);
      html = rellenar(html, 'cifras', vacio.cifras, a);
      html = rellenar(html, 'cortes', vacio.cortes, a);
      html = rellenar(html, 'lectura', v.lectura(kpis), a);
      html = rellenar(html, 'cierre', v.cierrePortada(), a);
      if (a.length) faltantes.push(`${archivo}: ${a.join(', ')}`);
    } else if (tipo === 'seccion') {
      // Mismo explorador que la portada, con los cortes del eje. Se deja
      // escrito el estado sin filtrar: el informe completo.
      const a = [];
      const clave = (html.match(/data-seccion="([^"]+)"/) || [])[1];
      const titulo = (html.match(/<title>([^<·]+)/) || ['', clave])[1].trim();
      const sec = vx.seccion(publicaciones, {}, clave, proc, unidadPorPersona, jerarquia);
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
      html = rellenar(html, 'catalogo', v.catalogo(await leerJSON('catalogo.json')), a);
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
      html = rellenar(html, 'glosario', v.glosario(entradas), a);
      html = rellenar(html, 'procedencia', v.procedencia(meta), a);
      html = rellenar(html, 'validacion', v.validacion(await leerJSON('validacion.json')), a);
      // Misma razón que unidadPorPersona más abajo: esta cifra crece sola
      // (T-19 corre por cron), y sin pre-renderizarla un lector sin
      // JavaScript vería el hueco vacío que "hoy hay X de Y" deja al medio
      // de la frase — peor que la cifra vieja que este mismo cambio corrigió.
      const { autores: autoresOrcid } = await leerJSON('authors.json');
      const conOrcid = autoresOrcid.filter(a2 => a2.orcid).length;
      html = rellenar(html, 'orcid-cobertura',
        `${c.nf.format(conOrcid)} de ${c.nf.format(autoresOrcid.length)} formas de firma con ORCID`, a);
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
