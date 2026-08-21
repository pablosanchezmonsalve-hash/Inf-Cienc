/* Presupuesto de peso, medido y comprobado.

   POR QUÉ ESTO ES UNA COMPUERTA Y NO UNA NOTA
     Los techos anteriores vivían en una frase de docs/UX_UI.md y estaban
     excedidos desde hacía dos rediseños sin que nada avisara. Un presupuesto
     escrito en prosa envejece en silencio; uno que corre con la batería, no.

   LOS TECHOS SE MIDEN CON GZIP, QUE ES COMO VIAJA
     Los anteriores estaban en bruto y comparaban contra recomendaciones que
     están expresadas en comprimido, así que declaraban excedido lo que no lo
     estaba. GitHub Pages —donde esto se publica— sirve comprimido.

   DE DÓNDE SALEN LAS CIFRAS
     La recomendación de presupuesto para móvil de uso corriente sitúa el
     JavaScript por debajo de 150 KB y el CSS por debajo de 60 KB, ambos con
     gzip. Se adoptan tal cual: son externas, comprobables y no las fija quien
     tiene que cumplirlas.

     El tercer techo, el de DATOS, no existía y es el que de verdad pesa en
     este sitio: el explorador manda publications.json entero al navegador. Se
     fija en 250 KB con margen deliberado sobre los ~172 KB actuales, porque el
     corpus crece cada año y un techo que se rompe con el crecimiento normal
     obliga a subirlo cada vez, que es la forma de que deje de significar algo.

   POR QUÉ EL TECHO DE DATOS PUEDE SER TAN ALTO
     Porque está FUERA de la ruta crítica de pintado y eso está medido: el
     contenido llega pre-renderizado en el HTML y el JSON se descarga después.
     Con Slow 4G el LCP queda en torno a 900 ms sobre un umbral de 2.500, y
     recortar el conjunto tarda decenas de milisegundos sobre un umbral de 200.
     Si algún día ese margen se estrecha, lo dirá rendimiento.mjs, no este
     archivo: aquí se vigila el tamaño, allí el efecto. */

import { readdirSync, readFileSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { gzipSync } from 'node:zlib';

const DIST = resolve(process.argv[2] || 'dist');
const KB = 1024;

/* techo en KB comprimido, y de dónde sale */
const TECHOS = [
  ['CSS', 60, 'recomendación de presupuesto para móvil'],
  ['JavaScript', 150, 'recomendación de presupuesto para móvil'],
  ['Datos', 250, 'margen sobre lo medido; el corpus crece cada año'],
];

function pesar(archivos) {
  let bruto = 0, comprimido = 0;
  for (const f of archivos) {
    const b = readFileSync(f);
    bruto += b.length;
    comprimido += gzipSync(b, { level: 9 }).length;
  }
  return { bruto, comprimido };
}

const listar = (dir, ext) => existsSync(dir)
  ? readdirSync(dir).filter(f => f.endsWith(ext)).map(f => join(dir, f)) : [];

const grupos = {
  CSS: listar(join(DIST, 'assets/css'), '.css'),
  JavaScript: listar(join(DIST, 'assets/js'), '.js'),
  // Sólo los artefactos que la portada y las secciones cargan de entrada. Las
  // fichas de autor son cientos de archivos que se piden de uno en uno, así
  // que sumarlas mediría algo que nadie descarga.
  Datos: listar(join(DIST, 'data'), '.json'),
};

console.log('='.repeat(78));
console.log('PRESUPUESTO DE PESO');
console.log('='.repeat(78));
console.log('  Los techos son de contenido COMPRIMIDO, que es como viaja.\n');

let fallos = 0;
for (const [nombre, techo, fuente] of TECHOS) {
  const archivos = grupos[nombre] || [];
  const { bruto, comprimido } = pesar(archivos);
  const kb = comprimido / KB;
  const ok = kb <= techo;
  if (!ok) fallos++;
  const pct = Math.round(kb / techo * 100);
  console.log(`  ${ok ? 'OK   ' : 'FALLA'} ${nombre.padEnd(11)} ` +
    `${kb.toFixed(1).padStart(6)} KB de ${String(techo).padStart(3)} KB  ` +
    `(${String(pct).padStart(3)} %)  · ${(bruto / KB).toFixed(0)} KB en bruto · ` +
    `${archivos.length} archivo(s)`);
  console.log(`         techo: ${fuente}`);
}

console.log('\n' + '='.repeat(78));
if (fallos) {
  console.log(`${fallos} PRESUPUESTO(S) EXCEDIDO(S)`);
  console.log('Subir el techo es una decisión, no un arreglo: si se sube, hay que');
  console.log('decir contra qué evidencia. Ver src/verify/rendimiento.mjs.');
} else {
  console.log('PRESUPUESTO DE PESO · dentro de los techos');
}
console.log('='.repeat(78));
process.exit(fallos ? 1 : 0);
