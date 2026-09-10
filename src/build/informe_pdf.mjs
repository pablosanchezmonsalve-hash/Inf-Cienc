/* informe_pdf.mjs — el informe institucional en PDF, desde el sitio construido.

   POR QUÉ EXISTE, HABIENDO UN BOTÓN
   El botón de la interfaz resuelve el caso de quien está mirando una sección y
   quiere llevársela. No resuelve el otro: un PDF del informe COMPLETO, igual en
   cada carga, que se pueda archivar y citar. Ese no puede depender de que
   alguien abra un navegador y acierte con los ajustes del diálogo.

   UN SOLO ORIGEN
   No hay una segunda maquetación. Este guion abre las mismas páginas de
   `dist/`, con la misma hoja de estilo y el mismo bloque `@media print` que usa
   el botón, y le pide al navegador el PDF. Si el informe cambia, cambia en un
   sitio; si divergiera, sería porque alguien escribió una segunda definición,
   que es justo lo que aquí no hay.

   Es el mismo patrón que `prerender.mjs` con `vista.js`: un cuerpo de código,
   dos consumidores.

   EL INFORME A MEDIDA
   El tercer argumento es un recorte: la misma cadena de consulta que el
   explorador escribe en la URL (`anio=2024&tipo=Article`). Se le pasa a cada
   sección y las cifras, los gráficos y las tablas se recalculan sobre él, que
   es lo que el sitio ya hacía; aquí no se filtra nada por cuenta propia. La
   primera hoja declara el recorte, así que el PDF dice sobre qué está medido
   sin depender de cómo se llame el archivo.

   Si el recorte es de UNA persona (`autor=…`), la ficha de esa firma abre el
   informe: es lo único que declara su identidad, su ORCID con la evidencia de
   cada asignación y su unidad. Las advertencias que exige un informe personal
   —DORA y Leiden, y muestra reducida por debajo del umbral— las escribe el
   propio sitio sobre las cifras, así que viajan solas al papel.

   REQUISITO BLANDO
   Necesita Playwright y Chromium, que este proyecto ya usa para verificar el
   sitio. Sin ellos no corre y lo dice; el sitio se construye igual.

   SELECCIÓN DE GRÁFICOS
   `grafico=I-04|T-05` elige qué figuras se dibujan, de las dieciocho del
   informe y sin importar en qué sección viven. NO es un recorte: las cifras
   siguen siendo las del filtro de datos, y lo que se acota es qué se muestra.
   Las secciones que se quedan sin ninguna figura no se imprimen; la portada y
   el anexo metodológico sí, siempre.

   Uso:  node src/build/informe_pdf.mjs <dist> <salida.pdf> [recorte]
   Ej.:  node src/build/informe_pdf.mjs dist dist/informe.pdf "anio=2024&unidad=Medicina"
         node src/build/informe_pdf.mjs dist dist/informe.pdf "grafico=I-04|T-05"
*/

import { createServer } from 'node:http';
import { readFile, stat, writeFile, mkdir } from 'node:fs/promises';
import { join, extname, resolve, basename, dirname } from 'node:path';
import { abrir, pdfEtiquetado } from '../verify/navegador.mjs';
import * as vx from '../../web/assets/js/vista_explorador.js';

/* pdf.js sólo para LEER en qué hoja cayó cada gráfico, y así poder escribir el
   índice con números de hoja de verdad. Es la misma dependencia de desarrollo
   que ya usa `src/verify/impresion.mjs`; si falta, el informe se genera igual
   y sale sin índice, que es peor pero no es nada. */
let getDocument = null;
try {
  ({ getDocument } = await import('pdfjs-dist/legacy/build/pdf.mjs'));
} catch {
  console.log('  ⚠ sin pdfjs-dist: el informe sale sin índice. `npm i -D pdfjs-dist`');
}

const dist = resolve(process.argv[2] || 'dist');
const salida = resolve(process.argv[3] || 'dist/informe-cienciometrico.pdf');

/* El recorte, normalizado con la misma clase que usa el navegador para leerlo
   de la URL: así una cadena escrita a mano con un `?` delante, con espacios o
   con el orden cambiado produce exactamente la misma consulta que un clic en
   el explorador. */
const recorte = new URLSearchParams((process.argv[4] || '').replace(/^\?/, ''));
const consulta = recorte.toString();

/* Un `grafico=` suelto NO es un recorte: no filtra publicaciones, y la hoja
   dice «Sin filtros: el informe completo» junto a la línea de selección. El
   resumen de consola afirmaba «el recorte aplicado» en ese caso, que es justo
   lo contrario de lo que el PDF declara. La carátula usa la misma distinción
   para decidir si imprime las bases del universo. */
const filtra = [...recorte.keys()].some((k) => k !== 'grafico');

/* El nombre del archivo lleva el recorte, porque dos informes distintos no
   pueden llamarse igual en la carpeta de descargas de nadie. Es una etiqueta
   para encontrarlo, no la declaración: ésa va dentro, en la primera hoja, que
   es lo único que sobrevive a que alguien renombre el archivo. */
const etiqueta = [...recorte.entries()]
  .map(([k, v]) => `${k}-${v}`).join('_')
  .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
  .replace(/[^A-Za-z0-9_-]+/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '')
  .slice(0, 60);
const base = salida.replace(/\.pdf$/, etiqueta ? `-${etiqueta}` : '');

/* Las secciones del informe, en orden de lectura. NO incluye las superficies de
   consulta —publicaciones, autores, el catálogo—: son tablas con filtro y
   paginación, y volcarlas enteras produciría un anexo de cientos de páginas que
   nadie lee. Quien las quiera las exporta en CSV. */
const SECCIONES = ['index.html', 'produccion.html', 'impacto.html',
                   'colaboracion.html', 'tematica.html', 'metodologia.html'];

/* La excepción es la ficha, cuando el recorte es de UNA persona: entonces abre
   el informe. Es lo único que declara su identidad, su ORCID con la evidencia
   de cada asignación, su unidad y las variantes de firma que se fusionaron en
   ella; sin eso, las páginas siguientes son cifras de alguien sin decir de
   quién exactamente. El nombre se traduce a su identificador con `authors.json`
   —el mismo artefacto que sirve el sitio—, no con una regla de slug reescrita
   aquí, que sería una segunda forma de nombrar a las mismas personas. */
async function fichaDe(nombre) {
  if (!nombre) return null;
  const autores = JSON.parse(await readFile(join(dist, 'data/authors.json'), 'utf8')).autores;
  const a = autores.find((x) => x.nombre === nombre);
  if (!a) {
    console.log(`  ⚠ «${nombre}» no es una firma del corpus: el informe sale sin ficha.`);
    return null;
  }
  return `autor.html?id=${encodeURIComponent(a.id)}`;
}

const autores = recorte.getAll('autor');
const ficha = autores.length === 1 ? await fichaDe(autores[0]) : null;

/* Una selección de gráficos deja secciones sin ninguno. Se saltan: un informe
   de tres figuras no debe traer cuatro secciones, tres de ellas diciendo que
   no tienen nada que enseñar.

   La portada y el anexo metodológico se quedan siempre. La primera lleva las
   cifras y la declaración; el segundo es lo que hace interpretable cualquier
   figura, y un informe recortado a tres gráficos lo necesita más, no menos. */
const seleccion = (recorte.get('grafico') || '').split('|').filter(Boolean);
const conGrafico = new Set(Object.entries(vx.seccionDeGrafico())
  .filter(([cod]) => seleccion.includes(cod)).map(([, clave]) => clave));
const SIEMPRE = new Set(['index.html', 'metodologia.html']);

const TIPOS = { '.html': 'text/html; charset=utf-8', '.css': 'text/css',
                '.js': 'text/javascript', '.json': 'application/json',
                '.svg': 'image/svg+xml', '.woff2': 'font/woff2' };

const servir = (raiz) => new Promise((ok) => {
  const s = createServer(async (req, res) => {
    const ruta = join(raiz, decodeURIComponent(req.url.split('?')[0]));
    try {
      if ((await stat(ruta)).isDirectory()) throw new Error('dir');
      res.writeHead(200, { 'content-type': TIPOS[extname(ruta)] || 'application/octet-stream' });
      res.end(await readFile(ruta));
    } catch { res.writeHead(404).end('no'); }
  });
  s.listen(0, '127.0.0.1', () => ok({ s, puerto: s.address().port }));
});

/* Se lee una vez: lo necesitan la portada del informe y el manifiesto. */
const meta = JSON.parse(await readFile(join(dist, 'data/meta.json'), 'utf8'));

const { s, puerto } = await servir(dist);
const nav = await abrir();
const ctx = await nav.newContext();
const pag = await ctx.newPage();

if (consulta) console.log(`  recorte: ${consulta}\n`);

/* Cada parte es [ruta, nombre del archivo]. La ficha entra primero y con su
   propio nombre; el recorte se le añade con `&` porque su ruta ya trae el
   identificador, y hace falta para que su hoja declare el mismo recorte que
   las demás en vez de contradecirlas. */
const RUTAS = [
  ...(ficha ? [[ficha, 'ficha']] : []),
  ...SECCIONES
    .filter((s) => !seleccion.length || SIEMPRE.has(s) || conGrafico.has(s.replace(/\.html$/, '')))
    .map((s) => [s, s.replace(/\.html$/, '')]),
];
if (seleccion.length) {
  console.log(`  selección: ${seleccion.length} gráfico(s) · ${RUTAS.length} secciones\n`);
}

/* El folio. Un informe de más de cuarenta hojas sin numerar no se puede citar
   ni comentar: «mire la página 12» deja de significar algo, y una hoja suelta
   no dice de qué documento salió.

   Va aquí y no en la hoja de estilo porque Chromium no implementa los cuadros
   de margen de CSS Paged Media (`@bottom-center`), así que en el navegador no
   hay forma de escribirlo. Es la diferencia real entre las dos vías: el botón
   ofrece el folio del propio diálogo —con la dirección web y la fecha del
   navegador—, y este guion pone el del informe.

   La plantilla no hereda NADA de la hoja de estilo: se le escriben las fuentes
   y los tamaños, y `pageNumber`/`totalPages` los rellena Chromium. Los
   nombres de sección se traducen a la palabra que el lector ve en la portada,
   no al del archivo. */
const NOMBRE_SECCION = {
  index: 'Portada', produccion: 'Producción', impacto: 'Impacto',
  colaboracion: 'Colaboración', tematica: 'Áreas temáticas',
  metodologia: 'Metodología y limitaciones', ficha: 'Ficha del investigador',
};

const pieDeHoja = (seccion) => `
  <div style="width:100%;margin:0 14mm;font:8pt -apple-system,'Segoe UI',Roboto,sans-serif;
              color:#444;display:flex;justify-content:space-between;align-items:baseline;
              border-top:.5pt solid #bbb;padding-top:2mm;">
    <span>Informe bibliométrico · ${NOMBRE_SECCION[seccion] || seccion}</span>
    <span>Hoja <span class="pageNumber"></span> de <span class="totalPages"></span></span>
  </div>`;

/* El texto de UNA hoja, sin espacios, para comprobar qué acabó impreso en
   ella. Mismo cuidado con `Uint8Array.from` que en `hojasDe`: pdf.js desprende
   el ArrayBuffer que recibe, y pasarle una vista del mismo Buffer dejaría el
   PDF vacío al escribirlo. */
async function textoDeHoja(buffer, n) {
  const doc = await getDocument({ data: Uint8Array.from(buffer), verbosity: 0 }).promise;
  if (n > doc.numPages) return '';
  return (await (await doc.getPage(n)).getTextContent())
    .items.map((x) => x.str).join('').replace(/\s+/g, '');
}

const esc = (s) => String(s).replace(/[&<>"]/g, (c) =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

/* ── La portada del informe ─────────────────────────────────────────────────
   La hoja 1 traía el titular de la PÁGINA WEB: «Informe bibliométrico», la
   línea de procedencia en letra chica y el desplegable de método. Servía, pero
   se leía como el borde superior de un sitio, no como la carátula de un
   documento que alguien va a archivar, citar o mandar por correo.

   Qué añade que no estuviera ya en el papel:
     · el ALCANCE arriba y en grande — un informe recortado a una facultad se
       distinguía de otro sólo por una línea de 8 pt;
     · la fecha de EXPORTACIÓN de los datos, que no se imprimía en ninguna
       parte (la de corte de citas está en la banda, la de build en el pie);
     · la fecha en que se generó ESTE PDF, que tampoco;
     · las cuatro bases de cálculo juntas — el pie imprime tres.

   Va en el generador y no en la hoja de estilo por lo mismo que el índice: es
   el informe compuesto quien sabe que hay un documento, y no una página suelta
   que alguien mandó a imprimir. Su MAQUETA sí vive en `app.css`
   (`.portada-informe`), que sigue siendo el único sitio donde se decide cómo
   se ve el papel.

   El alcance NO se redacta aquí: se LEE de `#recorte-impreso`, el párrafo que
   la propia página escribe con el recorte ya aplicado (`fraseRecorte` en
   `core.js`). Una segunda redacción del mismo hecho es la forma de que las dos
   acaben diciendo cosas distintas, y en este caso una de ellas mentiría sobre
   qué publicaciones sostienen el informe. */
/* El rótulo por el que se reconoce la carátula en el PDF compuesto. Se declara
   aquí, junto a la maqueta que lo imprime, para que la autocomprobación y lo
   comprobado no puedan separarse: si alguien lo reescribe, lo reescribe en el
   único sitio donde está. */
const SELLO_CARATULA = 'Informe generado el';

const fila = (rotulo, valor) => valor
  ? `<p class="pi-fila"><span class="pi-rotulo">${esc(rotulo)}</span>
       <span class="pi-valor">${esc(valor)}</span></p>` : '';

function portadaHTML(meta, declara) {
  const v = meta.ventana || {};
  const d = meta.denominadores || {};
  const hoy = new Date().toISOString().slice(0, 10);
  /* Las cuatro bases son del UNIVERSO institucional, y sobre un recorte
     engañan: bajo «46 de 823 publicaciones» se leen como el suelo de este
     informe, que no lo son. La línea de alcance ya declara sobre cuántas
     descansa, y cada cifra declara la suya dentro. Recalcularlas para el
     recorte sería reimplementar en el generador un cálculo que el sitio ya
     hace, que es la clase de segunda definición que este proyecto evita. */
  const bases = filtra ? [] : [
    [d.universo_total, 'en el universo'],
    [d.con_metricas, 'con métricas normalizadas'],
    [d.con_autoria_detallada, 'con autoría detallada'],
    [d.con_area_tematica, 'con área temática'],
  ].filter(([n]) => n !== undefined && n !== null);
  return `<section class="portada-informe solo-papel" aria-label="Portada del informe">
    <p class="pi-institucion">${esc(meta.institucion || '')}</p>
    <h1 class="pi-titulo">${esc(meta.titulo_plataforma || 'Informe bibliométrico')}</h1>
    <p class="pi-alcance">${esc(declara.recorte)}</p>
    ${declara.seleccion ? `<p class="pi-seleccion">${esc(declara.seleccion)}</p>` : ''}
    <p class="pi-ventana">Publicaciones de ${esc(String(v.inicio ?? ''))} a ${esc(String(v.fin ?? ''))}</p>
    <div class="pi-datos">
      ${fila('Fuentes', (meta.fuentes || []).join(' · '))}
      ${fila('Exportación de los datos', meta.fecha_export)}
      ${fila('Citas actualizadas al', meta.fecha_corte_citas)}
      ${fila('Sitio construido el', meta.fecha_build)}
      ${fila(SELLO_CARATULA, hoy)}
    </div>
    ${bases.length ? `<div class="pi-bases">
      <p class="pi-bases-tit">Bases de cálculo</p>
      <p class="pi-bases-cifras">${bases.map(([n, q]) =>
        `<b>${esc(new Intl.NumberFormat('es-CL').format(n))}</b> ${esc(q)}`).join(' · ')}.</p>
      <p class="pi-bases-nota">Cada indicador declara la suya, y no es la misma para todos.</p>
    </div>` : ''}
  </section>`;
}

const partes = [];
for (const [ruta, seccion] of RUTAS) {
  const union = ruta.includes('?') ? '&' : '?';
  const url = `http://127.0.0.1:${puerto}/${ruta}${consulta ? union + consulta : ''}`;
  await pag.goto(url, { waitUntil: 'networkidle' });
  // Sin esto el PDF sale con los gráficos a medio dibujar en las páginas que
  // los pintan al hidratar: `networkidle` dice que la red calló, no que el
  // navegador terminó.
  await pag.waitForTimeout(400);
  // Etiquetado: el árbol de estructura —encabezados, listas, tablas, orden de
  // lectura— es lo que hace navegable el PDF con un lector de pantalla. Sin
  // pedirlo el documento sale sin marcar, comprobado sobre el archivo.
  const { buffer, etiquetado, motivo } = await pdfEtiquetado(pag, {
    format: 'A4', printBackground: true,
    displayHeaderFooter: true, headerTemplate: '<span></span>',
    footerTemplate: pieDeHoja(seccion),
  });
  partes.push({ seccion, buffer, etiquetado });
  console.log(`  ${seccion.padEnd(14)} ${(buffer.length / 1024).toFixed(0)} KB`
    + (etiquetado ? '' : `  ⚠ sin etiquetar${motivo ? `: ${motivo}` : ''}`));
}

/* ── El índice ──────────────────────────────────────────────────────────────
   Cuarenta y seis hojas repartidas en seis archivos no se recorren sin un
   índice: «mire el gráfico de tipos documentales» obliga a abrir los seis.

   Los números de hoja NO se estiman ni se cuentan bloques: se LEEN del PDF ya
   generado, buscando el título de cada gráfico página por página. Es la misma
   razón por la que la compuerta de impresión lee el PDF y no el DOM —el
   navegador miente sobre el papel—, y además resuelve gratis el caso de la
   selección de gráficos: lo que no se dibujó no aparece, sin una segunda regla
   que decida qué entra.

   El precio es que la portada se compone dos veces: una para que existan las
   demás y otra ya con el índice. Son unos segundos y ocurre sólo aquí.

   Va en el generador y no en la hoja de estilo por lo mismo que el folio: el
   botón del navegador no puede saber en qué hoja cae nada. Su MAQUETA sí vive
   en `app.css` (`.indice-informe`), que sigue siendo el único sitio donde se
   decide cómo se ve el papel. */
const TITULOS = Object.fromEntries(Object.entries(vx.SECCIONES).map(
  ([clave, s]) => [clave, s.cortes.map((c) => [c.cod || c.campo, c.titulo])]));

async function hojasDe(buffer, titulos) {
  // `Uint8Array.from` COPIA. pdf.js se queda con el ArrayBuffer que recibe y
  // lo desprende, así que pasarle una vista del mismo Buffer dejaría a
  // `writeFile` escribiendo un búfer vacío. Ya pasó una vez.
  const doc = await getDocument({ data: Uint8Array.from(buffer), verbosity: 0 }).promise;
  const donde = new Map();
  for (let i = 1; i <= doc.numPages; i++) {
    const texto = (await (await doc.getPage(i)).getTextContent())
      .items.map((x) => x.str).join('').replace(/\s+/g, '');
    for (const [cod, titulo] of titulos) {
      if (!donde.has(cod) && texto.includes(titulo.replace(/\s+/g, ''))) donde.set(cod, i);
    }
  }
  return { donde, hojas: doc.numPages };
}

const entradas = [];
for (const { seccion, buffer } of (getDocument ? partes : [])) {
  if (seccion === 'index') continue;   // la portada no se indexa a sí misma
  const { donde, hojas } = await hojasDe(buffer, TITULOS[seccion] || []);
  entradas.push({
    seccion, hojas, archivo: `${basename(base)}-${seccion}.pdf`,
    graficos: (TITULOS[seccion] || [])
      .filter(([cod]) => donde.has(cod))
      .map(([cod, titulo]) => ({ cod, titulo, hoja: donde.get(cod) })),
  });
}

const indiceHTML = `<nav class="indice-informe solo-papel" aria-label="Índice del informe">
  <h2>Índice</h2>
  <p class="indice-nota">El informe se entrega en ${partes.length} archivos, uno por
    sección; éste es el primero. Las hojas se cuentan dentro de cada archivo.</p>
  <ol>${entradas.map((e) => `
    <li>
      <p class="indice-sec"><b>${esc(NOMBRE_SECCION[e.seccion] || e.seccion)}</b>
        <span class="indice-hojas">${e.hojas} ${e.hojas === 1 ? 'hoja' : 'hojas'}</span></p>
      <p class="indice-archivo">${esc(e.archivo)}</p>
      ${e.graficos.length ? `<ul>${e.graficos.map((g) => `
        <li><span class="indice-cod">${esc(g.cod)}</span>
          <span class="indice-tit">${esc(g.titulo)}</span>
          <span class="indice-guia"></span>
          <span class="indice-hoja">hoja ${g.hoja}</span></li>`).join('')}</ul>` : ''}
    </li>`).join('')}
  </ol>
</nav>`;

const iPortada = partes.findIndex((p) => p.seccion === 'index');
if (iPortada >= 0 && entradas.length) {
  const union = 'index.html'.includes('?') ? '&' : '?';
  await pag.goto(`http://127.0.0.1:${puerto}/index.html${consulta ? union + consulta : ''}`,
    { waitUntil: 'networkidle' });
  await pag.waitForTimeout(400);
  /* El alcance se lee de la página YA CARGADA con el recorte: es el párrafo
     que `core.js` escribe, no una segunda redacción del mismo hecho. */
  const declara = await pag.evaluate(() => ({
    recorte: (document.getElementById('recorte-impreso')?.textContent || '').trim(),
    seleccion: (document.getElementById('seleccion-impresa')?.textContent || '').trim(),
  }));
  /* Los dos van ANTES del titular, y en este orden. El índice lleva
     `break-before: page`, así que puesto DESPUÉS del titular dejaba el
     desplegable de método solo en una hoja, entre la carátula y el índice: una
     hoja con cuatro líneas. Delante, la portada del documento queda
     carátula · índice · qué mide, que es el orden en que se lee. */
  /* No se devuelve si encontró el ancla: lo que vale es lo que quedó en la
     hoja, y eso se comprueba abajo leyendo el PDF. Un `return true` del DOM
     diría que se insertó el marcado, no que se imprimió. */
  await pag.evaluate(({ portada, indice }) => {
    const cab = document.querySelector('.portada-cabecera');
    if (!cab) return;
    cab.insertAdjacentHTML('beforebegin', portada + indice);
  }, { portada: portadaHTML(meta, declara), indice: indiceHTML });
  const { buffer, etiquetado } = await pdfEtiquetado(pag, {
    format: 'A4', printBackground: true,
    displayHeaderFooter: true, headerTemplate: '<span></span>',
    footerTemplate: pieDeHoja('index'),
  });
  partes[iPortada] = { seccion: 'index', buffer, etiquetado };

  /* Autocomprobación de la carátula. La inyección depende de encontrar
     `.portada-cabecera`: si esa clase se renombra en `index.html`, el
     `if (!cab) return` deja el informe SIN carátula y sin índice, y el guion
     terminaría anunciando las dos. Se comprueba sobre el PDF ya compuesto —no
     sobre el DOM— por la misma razón que todo lo demás del papel: lo que
     importa es lo que quedó en la hoja.
     Se busca `SELLO_CARATULA` y NO la línea de alcance: el alcance sale de
     `fraseRecorte`, que la banda de crédito también imprime, así que sin
     carátula la comprobación habría pasado igual. Medido: con el selector
     roto a propósito, la hoja 1 seguía trayendo esa frase. Una comprobación
     que no puede fallar no comprueba nada. */
  const hoja1 = await textoDeHoja(buffer, 1);
  const conCaratula = hoja1.includes(SELLO_CARATULA.replace(/\s+/g, ''));
  if (!conCaratula) {
    console.log('  ⚠ sin carátula ni índice: la inyección no encontró '
      + '`.portada-cabecera` en index.html. El informe sale igual, sin las dos.');
  }
  /* Autocomprobación: sin selección, TODOS los gráficos declarados de una
     sección tienen que aparecer en su PDF. Si uno no se encuentra es que su
     título cambió en `vista_explorador.js` y la búsqueda dejó de casar, y el
     índice se quedaría corto sin decirlo. Con selección no se comprueba: ahí
     faltan a propósito, y decidir cuáles exigir obligaría a reimplementar la
     regla de selección, que es la clase de segunda definición que este
     proyecto evita. */
  if (!seleccion.length) {
    for (const e of entradas) {
      const esperados = (TITULOS[e.seccion] || []).length;
      if (e.graficos.length < esperados) {
        const faltan = (TITULOS[e.seccion] || [])
          .filter(([cod]) => !e.graficos.some((g) => g.cod === cod))
          .map(([cod]) => cod).join(', ');
        console.log(`  ⚠ ${e.seccion}: ${e.graficos.length} de ${esperados} gráficos `
          + `localizados en el PDF. Sin hoja en el índice: ${faltan}.`);
      }
    }
  }

  const n = entradas.reduce((s, e) => s + e.graficos.length, 0);
  // El peso de la portada se anunció antes de tener índice: se corrige aquí en
  // vez de dejar en pantalla una cifra que ya no corresponde al archivo.
  if (conCaratula) {
    console.log(`\n  índice: ${entradas.length} secciones · ${n} gráficos, con su hoja`);
    console.log(`  index          ${(buffer.length / 1024).toFixed(0)} KB (con carátula e índice)`);
  }
}

await nav.close();
s.close();

/* Se emite una parte por sección en vez de un PDF único porque unir PDF exige
   una dependencia de manipulación que este proyecto no tiene, y añadirla por
   esto sería pagar un árbol entero por un grapado. Se declara en vez de
   fingir un informe de una pieza. */
await mkdir(dirname(base), { recursive: true });
for (const { seccion, buffer } of partes) {
  await writeFile(`${base}-${seccion}.pdf`, buffer);
}

/* ── El manifiesto, para que el sitio pueda ofrecer el informe ──────────────
   El sitio se ensambla ANTES de que este guion corra —necesita `dist/` para
   componer el PDF—, así que las páginas no pueden traer los enlaces escritos:
   no sabrían si los archivos existen ni cuántas hojas tienen. Se deja aquí un
   artefacto con lo que de verdad se generó, y la portada dibuja el bloque de
   descarga sólo si lo encuentra.

   Eso es lo que impide la versión que sí engaña: enlaces fijos en el HTML que
   apuntan a archivos que puede que no estén, o que están pero son de otra
   carga de datos. Sin manifiesto no hay bloque, y el manifiesto lo escribe la
   misma corrida que escribió los PDF.

   Sólo se escribe si la salida cae DENTRO de `dist/`: generar el informe en
   otra carpeta —una entrega, una prueba— no debe anunciar en el sitio unos
   archivos que no están junto a él. */
const dentroDeDist = base.startsWith(dist + '/');
if (dentroDeDist && getDocument) {
  const archivos = [];
  for (const { seccion, buffer } of partes) {
    const { hojas } = await hojasDe(buffer, []);
    archivos.push({
      seccion,
      nombre: NOMBRE_SECCION[seccion] || seccion,
      archivo: `${base}-${seccion}.pdf`.slice(dist.length + 1),
      hojas,
      kb: Math.round(buffer.length / 1024),
    });
  }
  await writeFile(join(dist, 'data/informe.json'), JSON.stringify({
    generado: new Date().toISOString().slice(0, 10),
    // La fecha de build del sitio con el que se compuso. Si alguien reconstruye
    // el sitio y no vuelve a generar el informe, las dos fechas dejan de
    // coincidir y la portada lo dice en vez de ofrecer un PDF de otra carga.
    build: meta.fecha_build,
    recorte: consulta,
    hojas: archivos.reduce((s, a) => s + a.hojas, 0),
    archivos,
  }, null, 1) + '\n', 'utf8');
  console.log(`  manifiesto: dist/data/informe.json · ${archivos.length} archivos`);
}
const etiquetadas = partes.filter((p) => p.etiquetado).length;
console.log(`\n  ${partes.length} secciones · ${base}-*.pdf`);
console.log('  Texto seleccionable y buscable: el navegador embebe las tipografías.');
console.log(`  Etiquetado para lectores de pantalla: ${etiquetadas} de ${partes.length}.`);
console.log(`  Declara en la hoja 1: ${[
  filtra ? 'el recorte aplicado' : 'que es el informe completo',
  seleccion.length ? 'y la selección de gráficos, sin cambiar las cifras' : '',
].filter(Boolean).join(' ')}.`);
