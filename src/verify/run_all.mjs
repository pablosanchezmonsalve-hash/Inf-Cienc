/* run_all.mjs — batería de verificación del sitio construido.

   POR QUÉ ESTO VIVE EN EL REPOSITORIO Y NO EN UN DIRECTORIO TEMPORAL

   Estas comprobaciones se escribieron durante el rediseño y vivían en el
   scratchpad de la sesión, que es efímero. Rehacerlas en cada sesión cuesta
   más que todo el trabajo que verifican, y —peor— una comprobación reescrita
   de memoria no es la misma comprobación: la versión anterior del barrido de
   contraste medía la ficha de autor con el parámetro equivocado y llevaba
   semanas dando «0 fallos» sobre una página vacía.

   Una verificación que no se puede volver a correr no es una verificación.
   Es una anécdota.

   QUÉ COMPRUEBA

     contraste     WCAG 2.1 · 9 páginas × 2 temas, con composición alfa,
                   paradas de degradado y exclusión de decoración
     estructura    consola, peticiones fallidas, id duplicados, ARIA que
                   apunta a nada, anclas y enlaces internos rotos
     flujos        conmutador de vista, scroll-spy, tema, tooltip, ayuda,
                   filtros, búsqueda, ordenación y ficha de autor
     responsive    desborde horizontal en 430 px y 860 px
     higiene       tokens y clases declarados vs usados, exportaciones sin
                   consumidor, id que el JS busca y no existen, y que la capa
                   interna no haya viajado
     peso          CSS, JavaScript y datos contra su techo, medidos con gzip
                   porque es como viajan

   `rendimiento.mjs` queda FUERA de la batería por diseño: mide LCP con cinco
   corridas por página contra dos servidores y tarda minutos. Se corre a mano
   cuando se toca algo que pueda afectarlo.

   Uso:  node src/verify/run_all.mjs [dist]
*/

import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';

const DIST = resolve(process.argv[2] || 'dist');
const PUERTO = process.env.PUERTO || 8841;

if (!existsSync(DIST)) {
  console.error(`No existe ${DIST}. Ejecute antes: make sitio`);
  process.exit(1);
}

/* El servidor lo levanta y lo baja esta misma batería: una comprobación que
   exige que alguien recuerde arrancar un servidor a mano acaba no corriéndose. */
const servidor = spawn('python3', ['-m', 'http.server', '-d', DIST, String(PUERTO)],
  { stdio: 'ignore' });
const bajar = () => { try { servidor.kill(); } catch { /* ya estaba muerto */ } };
process.on('exit', bajar);
process.on('SIGINT', () => { bajar(); process.exit(130); });

await new Promise((r) => setTimeout(r, 1200));

const PASOS = [
  ['contraste', 'node', ['src/verify/contraste.mjs']],
  ['estructura', 'node', ['src/verify/estructura.mjs']],
  ['flujos', 'node', ['src/verify/flujos.mjs']],
  ['responsive', 'node', ['src/verify/responsive.mjs']],
  ['higiene', 'python3', ['src/verify/higiene.py', DIST]],
  // Sólo lee archivos y los comprime: tarda menos de un segundo, así que
  // no hay razón para dejarlo fuera como a rendimiento.mjs.
  ['peso', 'node', ['src/verify/peso.mjs', DIST]],
];

const correr = (cmd, args) => new Promise((res) => {
  const p = spawn(cmd, args, { env: { ...process.env, PUERTO: String(PUERTO), DIST } });
  let salida = '';
  p.stdout.on('data', (d) => { salida += d; });
  p.stderr.on('data', (d) => { salida += d; });
  p.on('close', (codigo) => res({ codigo, salida }));
});

console.log('='.repeat(78));
console.log('VERIFICACIÓN DEL SITIO CONSTRUIDO');
console.log('='.repeat(78));

const fallidos = [];
for (const [nombre, cmd, args] of PASOS) {
  const t0 = Date.now();
  const { codigo, salida } = await correr(cmd, args);
  const seg = ((Date.now() - t0) / 1000).toFixed(0);
  const ok = codigo === 0;
  if (!ok) fallidos.push(nombre);
  console.log(`\n  ${ok ? 'OK   ' : 'FALLA'} ${nombre.padEnd(12)} ${seg.padStart(3)} s`);
  // En verde se resume; en rojo se enseña todo, que es cuando hace falta.
  const lineas = salida.trimEnd().split('\n');
  (ok ? lineas.slice(-2) : lineas).forEach((l) => console.log(`         ${l}`));
}

bajar();
console.log(`\n${'='.repeat(78)}`);
if (fallidos.length) {
  console.log(`VERIFICACIÓN FALLIDA · ${fallidos.join(', ')}`);
  process.exit(1);
}
console.log('VERIFICACIÓN COMPLETA · sin fallos');
