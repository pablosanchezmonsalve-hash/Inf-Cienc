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
     este sitio: el explorador manda publications.json entero al navegador. No
     es externo y por eso su procedencia dice otra cosa que la de los otros
     dos: es un techo propio, fijado con margen sobre lo medido, porque el
     corpus crece cada año y un techo que se rompe con el crecimiento normal
     obliga a subirlo cada vez, que es la forma de que deje de significar algo.

     Historial, con la regla que lo fijó cada vez —siempre 1,21x lo medido—:
       250 KB sobre 204,3 medidos  (carga de 2026-07)
       300 KB sobre 247,7 medidos  (2026-09-04)
       450 KB sobre 370,7 medidos  (2026-09-10, carga 2020-2025 · D-587)

     LA PRÓXIMA VEZ NO SE SUBE (D-589)
     Una tercera aplicación del 1,21x convierte el techo en una función del
     corpus: sube siempre y deja de restringir. Cuando este techo se vuelva a
     exceder, la respuesta es recodificar publications.json en columnas con
     diccionario de cadenas, que está medido y deja el grupo en 265,8 KB —105
     menos— con rehidratación idéntica byte a byte al texto original. No otro
     1,21x.

     QUÉ MIDE ESTA SUMA, Y QUÉ NO (D-591)
     Suma los quince artefactos raíz de dist/data/, y NINGUNA página los pide
     juntos: la más pesada pide 328,0 KB y la ficha de autor 316,0. Es una COTA
     SUPERIOR del peso de datos de cualquier página, no el peso de ninguna. Se
     deja así a propósito: derivar el peor caso exigiría mantener a mano la
     lista de qué pide cada página, y esa lista envejece en silencio. La
     afirmación deja de ser cierta si algún día una página carga a la vez
     publications.json y fuentes_externas.json.

   POR QUÉ EL TECHO DE DATOS PUEDE SER TAN ALTO
     Porque está FUERA de la ruta crítica de pintado y eso está medido: el
     contenido llega pre-renderizado en el HTML y el JSON se descarga después.
     Medido con rendimiento.mjs el 2026-09-10, sobre el corpus de 1.342
     publicaciones y en Slow 4G, el LCP es de 1.596 ms en la portada, 1.620 en
     impacto y 1.592 en temática, sobre un umbral de 2.500: un 36 % de margen.
     Con el corpus anterior, de 823, eran 1.424 ms; duplicar el número de
     publicaciones costó 172 ms. Recortar el conjunto tarda decenas de
     milisegundos sobre un umbral de 200. Si algún día ese margen se estrecha,
     lo dirá rendimiento.mjs, no este archivo: aquí se vigila el tamaño, allí
     el efecto. */

import { readdirSync, readFileSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { gzipSync } from 'node:zlib';

const DIST = resolve(process.argv[2] || 'dist');
const KB = 1024;

/* techo en KB comprimido, y de dónde sale */
const TECHOS = [
  ['CSS', 60, 'recomendación de presupuesto para móvil'],
  ['JavaScript', 150, 'recomendación de presupuesto para móvil'],
  ['Datos', 450, 'techo propio, 1,21x lo medido: el mismo criterio con que se fijaron 250 y 300'],
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
