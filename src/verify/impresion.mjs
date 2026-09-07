/* impresion.mjs — el informe DESCARGADO, comprobado sobre el PDF de verdad.

   POR QUÉ HACE FALTA UNA COMPROBACIÓN APARTE
   El resto de la batería mira la pantalla. El informe que la gente archiva y
   cita no es la pantalla: es lo que sale del botón «Descargar informe» y de
   `make informe`, y ahí manda `@media print`, que nadie estaba mirando. Tres
   defectos reales vivían ahí sin que nada los viera:

     · la barra de vigencia se imprimía vacía —fuente, ventana y fecha de corte
       de las citas viven en `<details>` que la impresión oculta—, de modo que
       la hoja archivada no decía de dónde salían sus cifras;
     · el bloque del recorte se imprimía entero, con su botón «Ver todo», porque
       la regla que debía ocultarlo apuntaba a una clase inexistente;
     · el panel «Qué NO dice esta sección» imprimía su título y no su cuerpo, al
       ser un desplegable cerrado: un titular de advertencia sin la advertencia.

   Los tres son del mismo tipo: una regla de impresión que no casa con el
   marcado. Ninguno rompe nada en pantalla y ninguno se ve al revisar el código.

   POR QUÉ LEE EL PDF Y NO EL DOM
   Porque el DOM miente sobre el papel. Con el medio `print` emulado, el cuerpo
   de un `<details>` cerrado devuelve una caja de 109 px de alto y aun así no
   aparece en el PDF: medido en esta misma sesión, y es lo que hizo falsa la
   primera lectura del defecto. Aquí se genera el PDF y se lee su texto, que es
   el artefacto que la gente descarga.

   Uso:  node src/verify/impresion.mjs        (con el servidor de run_all.mjs)
*/

import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { abrir, pdfEtiquetado } from './navegador.mjs';

const PORT = process.env.PUERTO || 8841;
const DIST = process.argv[2] || process.env.DIST || 'dist';

/* pdf.js sólo para leer el texto del PDF. Es dependencia de desarrollo, como
   Playwright: nada de esto viaja al sitio. */
let getDocument;
try {
  ({ getDocument } = await import('pdfjs-dist/legacy/build/pdf.mjs'));
} catch {
  console.error('No se encontró pdfjs-dist. Instálelo con:\n  npm i -D pdfjs-dist');
  process.exit(2);
}

const meta = JSON.parse(await readFile(join(DIST, 'data/meta.json'), 'utf8'));
const { ejes } = JSON.parse(await readFile(join(DIST, 'data/ejes.json'), 'utf8'));

/* Una firma por debajo del umbral de interpretabilidad, tomada del artefacto y
   no escrita aquí: 480 de las 530 lo están, así que el caso normal de un
   informe personal es éste, y es el que tiene que llevar las dos advertencias.
   Se elige la primera por orden alfabético para que la comprobación sea la
   misma en cada corrida. */
const { autores } = JSON.parse(await readFile(join(DIST, 'data/authors.json'), 'utf8'));
const escasa = autores.filter((a) => !a.interpretable)
  .sort((a, b) => a.nombre.localeCompare(b.nombre))[0];

/* Y la firma más prolífica, para el corte que se apaga: sobre ella la red de
   coautoría sí se dibujaría, así que si volviera a dibujarse esta comprobación
   lo vería. Elegirla al azar podría dar con alguien de una publicación, cuya
   red estaría vacía por otra razón y dejaría la compuerta pasando en falso. */
const prolifica = [...autores].sort(
  (a, b) => b.n_publicaciones - a.n_publicaciones || a.nombre.localeCompare(b.nombre))[0];

/* Se compara sin espacios: pdf.js parte el texto en fragmentos por tipografía y
   por salto de línea, así que «Citas actualizadas al» puede llegar en tres
   trozos. Lo que se comprueba es que el contenido esté, no cómo quedó
   troceado. */
const pelado = (s) => s.replace(/\s+/g, '');
const tiene = (heno, aguja) => pelado(heno).includes(pelado(aguja));

/* Controles de pantalla que en una hoja no llevan a ninguna parte. Cada uno
   entró en esta lista después de aparecer en un PDF real.

   Van ANCLADOS —con su flecha, o pegados al texto que los sigue— porque la
   comparación ignora los espacios y un trozo suelto caza donde no debe: «Ver
   las» encontraba «Ver la sección →», que son las tarjetas de la portada y sí
   deben imprimirse, y «Ver las 30 reglas, una por una», que es el título de
   una lista que el informe sí lleva. Una compuerta que falla en verde es tan
   mala como la que no mira nada. */
const CONTROLES = ['GráficoTabla', 'Ver todo', 'publicaciones →',
                   'Saltar al contenido', 'Cómo leer estos indicadores →',
                   'Descargar informe'];

const CASOS = [
  {
    nombre: 'portada sin recorte',
    ruta: 'index.html',
    exige: ['Sin filtros: el informe completo'],
    prohibe: ['Recorte aplicado'],
  },
  {
    nombre: 'sección con recorte',
    ruta: 'produccion.html?anio=2024&tipo=Article',
    // El cuerpo del panel metodológico, tomado del artefacto y no copiado: si
    // alguien reescribe el eje, esta comprobación sigue midiendo lo mismo.
    exige: ['Recorte aplicado', 'Año: 2024', 'Tipo documental: Article',
            ejes.produccion.no_responde.slice(0, 80)],
    prohibe: ['Sin filtros'],
  },
  {
    /* Un informe personal es el caso en que el papel más se puede leer mal: un
       PDF con el nombre de alguien y cifras de impacto circula sin el sitio al
       lado. Las dos advertencias que lo hacen legible tienen que estar EN la
       hoja, no en la web que se quedó atrás.

       Los rótulos en negrita van en versalitas por CSS —«MUESTRA REDUCIDA» en
       el PDF—, así que se busca el cuerpo de cada advertencia y no su título. */
    nombre: 'informe recortado a una persona',
    ruta: `index.html?autor=${encodeURIComponent(escasa.nombre)}`,
    exige: ['Recorte aplicado', `Autor: ${escasa.nombre}`,
            'principios de DORA y del Manifiesto de Leiden',
            'no son interpretables individualmente'],
    prohibe: ['Sin filtros'],
  },
  {
    /* El corte que cambia de significado sobre una persona. La red recortada a
       una firma es una estrella, no una estructura de colaboración, así que se
       apaga y se declara; que el informe personal no la lleve es parte de lo
       que hace legible ese PDF. */
    nombre: 'la red de coautoría no se dibuja para una persona',
    ruta: `colaboracion.html?autor=${encodeURIComponent(prolifica.nombre)}`,
    exige: ['No se dibuja en un informe recortado a una persona',
            `Autor: ${prolifica.nombre}`],
    prohibe: ['personas en el recorte'],
  },
  {
    nombre: 'anexo dentro de un informe filtrado',
    ruta: 'metodologia.html?anio=2024',
    // Sin explorador que cuente, pero el anexo es parte del informe que alguien
    // pidió: una hoja suelta que se declare «informe completo» contradice a las
    // demás del mismo PDF.
    exige: ['Recorte aplicado', 'Año: 2024'],
    prohibe: ['Sin filtros'],
  },
];

const nav = await abrir();
const pag = await (await nav.newContext()).newPage();
let fallos = 0;
const anotar = (m) => { fallos++; console.log(`      ✗ ${m}`); };

for (const caso of CASOS) {
  await pag.goto(`http://127.0.0.1:${PORT}/${caso.ruta}`, { waitUntil: 'networkidle' });
  await pag.waitForTimeout(400);
  // Por la misma vía que `informe_pdf.mjs`: comprobar un PDF distinto del que
  // se publica sería comprobar otra cosa.
  const { buffer, etiquetado, motivo } = await pdfEtiquetado(pag, { format: 'A4', printBackground: true });

  const doc = await getDocument({ data: new Uint8Array(buffer), useSystemFonts: true,
                                  verbosity: 0 }).promise;
  let texto = '';
  for (let i = 1; i <= doc.numPages; i++) {
    texto += (await (await doc.getPage(i)).getTextContent()).items.map((t) => t.str).join('');
  }

  console.log(`  ${caso.nombre.padEnd(38)} ${doc.numPages} hojas · ${(buffer.length / 1024).toFixed(0)} KB`);

  // La procedencia, desde el artefacto: institución, fuentes, ventana y corte.
  const credito = [meta.institucion, `Fuentes:${meta.fuentes.join('·')}`,
                   `Ventana${meta.ventana.inicio}`, meta.fecha_corte_citas];
  credito.forEach((c) => { if (!tiene(texto, c)) anotar(`${caso.nombre}: falta en el crédito «${c}»`); });

  caso.exige.forEach((e) => {
    if (!tiene(texto, e)) anotar(`${caso.nombre}: no imprime «${e.slice(0, 60)}…»`);
  });
  caso.prohibe.forEach((p) => {
    if (tiene(texto, p)) anotar(`${caso.nombre}: imprime «${p}» y no debería`);
  });
  CONTROLES.forEach((ctl) => {
    if (tiene(texto, ctl)) anotar(`${caso.nombre}: imprime el control «${ctl}»`);
  });

  /* Etiquetado: sin árbol de estructura, un lector de pantalla recita el PDF
     en vez de navegarlo. Si la versión instalada de Playwright no sabe pedirlo
     no es un defecto del informe y no se cuenta como fallo, pero se dice: una
     comprobación que no pudo hacerse no es una comprobación que pasó. */
  if (!etiquetado) {
    if (motivo) console.log(`      · etiquetado no comprobado — ${motivo}`);
    else anotar(`${caso.nombre}: el PDF no está etiquetado`);
  }
}

await nav.close();

console.log(`\n  TOTAL: ${fallos} fallo(s) de impresión`);
process.exit(fallos ? 1 : 0);
