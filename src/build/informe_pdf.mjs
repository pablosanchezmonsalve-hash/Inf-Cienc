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
import { readFile, stat, writeFile } from 'node:fs/promises';
import { join, extname, resolve } from 'node:path';
import { abrir, pdfEtiquetado } from '../verify/navegador.mjs';
import * as vx from '../../web/assets/js/vista_explorador.js';

const dist = resolve(process.argv[2] || 'dist');
const salida = resolve(process.argv[3] || 'dist/informe-cienciometrico.pdf');

/* El recorte, normalizado con la misma clase que usa el navegador para leerlo
   de la URL: así una cadena escrita a mano con un `?` delante, con espacios o
   con el orden cambiado produce exactamente la misma consulta que un clic en
   el explorador. */
const recorte = new URLSearchParams((process.argv[4] || '').replace(/^\?/, ''));
const consulta = recorte.toString();

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
  const { buffer, etiquetado, motivo } = await pdfEtiquetado(pag, { format: 'A4', printBackground: true });
  partes.push({ seccion, buffer, etiquetado });
  console.log(`  ${seccion.padEnd(14)} ${(buffer.length / 1024).toFixed(0)} KB`
    + (etiquetado ? '' : `  ⚠ sin etiquetar${motivo ? `: ${motivo}` : ''}`));
}

await nav.close();
s.close();

/* Se emite una parte por sección en vez de un PDF único porque unir PDF exige
   una dependencia de manipulación que este proyecto no tiene, y añadirla por
   esto sería pagar un árbol entero por un grapado. Se declara en vez de
   fingir un informe de una pieza. */
for (const { seccion, buffer } of partes) {
  await writeFile(`${base}-${seccion}.pdf`, buffer);
}
const etiquetadas = partes.filter((p) => p.etiquetado).length;
console.log(`\n  ${partes.length} secciones · ${base}-*.pdf`);
console.log('  Texto seleccionable y buscable: el navegador embebe las tipografías.');
console.log(`  Etiquetado para lectores de pantalla: ${etiquetadas} de ${partes.length}.`);
console.log(`  Declara en la hoja 1: ${consulta ? 'el recorte aplicado' : 'que es el informe completo'}.`);
