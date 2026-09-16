/* kit.mjs — compuerta del paquete de sistema de diseño.

   POR QUÉ ESTA COMPUERTA EXISTE

   `docs/UX_UI.md` §16.1 promete que el sistema de diseño «no puede
   desactualizarse respecto del producto: si divergen, es que no se ha vuelto a
   generar». La promesa era cierta y vacía: `src/design/build_kit.mjs` llevaba
   desde el 2026-08-26 sin arrancar —llamaba a seis funciones que `vista.js`
   dejó de exportar al llegar el explorador— y nada en el proyecto lo corría,
   así que nadie lo vio. Durante tres semanas el generador publicaba fichas que
   hablaban de Peach Glow y de una advertencia ámbar, con la paleta ya en vino
   y verde moneda (`D-599`, `D-600`, `D-602`).

   Un generador que nadie ejecuta se congela. Ésta es la diferencia entre que
   el kit esté al día y que lo parezca.

   QUÉ COMPRUEBA

     1. Que el generador CORRE. Es la regresión que costó tres semanas.
     2. Que cada ficha se pinta en los dos temas, con fondos distintos: es lo
        que prueba que `light-dark()` resuelve por contenedor y no por `:root`.
     3. Que ninguna ficha lanza excepciones en el navegador.
     4. Que la ficha de color mide contra los tokens de `:root` y no contra los
        que una banda redefine. El generador leía la hoja entera y se quedaba
        con la ÚLTIMA aparición de cada token, así que publicaba la tinta medida
        contra el suelo oscuro de `.banda-contraste` (`D-599`). Es un fallo que
        no se ve mirando la ficha: hay que comparar con la hoja.

   Uso:  node src/verify/kit.mjs
*/

import { abrir } from './navegador.mjs';
import { readdirSync, statSync, readFileSync, mkdirSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { spawn } from 'node:child_process';

const RAIZ = resolve(process.env.KIT || 'design-system');
const PUERTO = Number(process.env.PUERTO_KIT || 8843);
const fallos = [];

/* ── 1. El generador tiene que correr ─────────────────────────────────── */

const generar = () => new Promise((res) => {
  const p = spawn('node', ['src/design/build_kit.mjs', RAIZ], { stdio: ['ignore', 'pipe', 'pipe'] });
  let salida = '';
  p.stdout.on('data', (d) => { salida += d; });
  p.stderr.on('data', (d) => { salida += d; });
  p.on('close', (codigo) => res({ codigo, salida }));
});

console.log('='.repeat(78));
console.log('SISTEMA DE DISEÑO');
console.log('='.repeat(78));

const gen = await generar();
if (gen.codigo !== 0) {
  console.log('\n  FALLA  el generador no arranca\n');
  console.log(gen.salida.trimEnd().split('\n').map((l) => '         ' + l).join('\n'));
  console.log('\n' + '='.repeat(78));
  console.log('SISTEMA DE DISEÑO · el generador no corre');
  console.log('Las fichas que haya en ' + RAIZ + ' son de una corrida anterior y no');
  console.log('describen el producto. Ver docs/UX_UI.md §16.');
  console.log('='.repeat(78));
  process.exit(1);
}

const fichas = [];
(function walk(d, p = '') {
  for (const f of readdirSync(d)) {
    const full = join(d, f);
    if (statSync(full).isDirectory()) walk(full, p + f + '/');
    else if (f.endsWith('.html')) fichas.push(p + f);
  }
})(RAIZ);

if (!fichas.length) {
  console.log('  FALLA  el generador corrió pero no dejó ninguna ficha');
  process.exit(1);
}
console.log(`\n  OK     el generador corre · ${fichas.length} fichas`);

/* ── 2. La ficha de color mide contra :root ───────────────────────────── */

/* El token tal como lo declara :root, que es la paleta que ve un lector del
   sitio. Se lee del MISMO bloque que lee validar_paleta.py, a propósito. */
const css = readFileSync('web/assets/css/app.css', 'utf8');
const raiz = (() => {
  const i = css.indexOf(':root');
  const a = css.indexOf('{', i);
  return css.slice(a + 1, css.indexOf('}', a));
})();
const deRaiz = (tok) => {
  const m = raiz.match(new RegExp(`${tok}:\\s*light-dark\\(\\s*(#[0-9a-f]{6})\\s*,\\s*(#[0-9a-f]{6})\\s*\\)`, 'i'));
  return m ? [m[1].toLowerCase(), m[2].toLowerCase()] : null;
};
const colorHtml = readFileSync(join(RAIZ, 'fundamentos/color.html'), 'utf8');
for (const tok of ['--superficie', '--superficie-2', '--plano']) {
  const esperado = deRaiz(tok);
  if (!esperado) continue;
  // La ficha imprime «#claro · #oscuro» junto al nombre del token.
  const m = colorHtml.match(new RegExp(`<code>${tok}</code>\\s*<span class="hex">(#[0-9a-f]{6}) · (#[0-9a-f]{6})</span>`, 'i'));
  if (!m) { fallos.push(`la ficha de color no declara ${tok}`); continue; }
  if (m[1].toLowerCase() !== esperado[0] || m[2].toLowerCase() !== esperado[1]) {
    fallos.push(`${tok}: la ficha dice ${m[1]} · ${m[2]} y :root dice ${esperado[0]} · ${esperado[1]}`
      + ' — el generador está leyendo el valor que una banda redefine');
  }
}
console.log(`  ${fallos.length ? 'FALLA ' : 'OK    '} la ficha de color mide contra :root`);

/* ── 3. Cada ficha se pinta, en los dos temas, sin excepciones ─────────── */

const servidor = spawn('python3', ['-m', 'http.server', '-d', RAIZ, String(PUERTO)],
  { stdio: 'ignore' });
const bajar = () => { try { servidor.kill(); } catch { /* ya estaba muerto */ } };
process.on('exit', bajar);
await new Promise((r) => setTimeout(r, 1200));

const b = await abrir();
const pg = await (await b.newContext({ viewport: { width: 1100, height: 900 } })).newPage();
const errs = [];
pg.on('pageerror', (e) => errs.push(e.message));

console.log('');
for (const f of fichas.sort()) {
  await pg.goto(`http://127.0.0.1:${PUERTO}/${f}`, { waitUntil: 'networkidle' });
  await pg.waitForTimeout(200);
  const r = await pg.evaluate(() => {
    const c = document.querySelector('.tema-claro .lienzo');
    const o = document.querySelector('.tema-oscuro .lienzo');
    const bg = (el) => (el ? getComputedStyle(el).backgroundColor : null);
    const ficha = document.querySelector('.ficha');
    return {
      claro: bg(c), oscuro: bg(o),
      alto: ficha ? ficha.getBoundingClientRect().height : 0,
      svg: document.querySelectorAll('svg.chart').length,
      texto: (document.querySelector('.lienzo')?.innerText || '').trim().length,
    };
  });
  // Si el panel oscuro existe, su fondo TIENE que diferir del claro: eso prueba
  // que light-dark() resuelve por contenedor y no por :root.
  const distintos = !r.oscuro || r.claro !== r.oscuro;
  const ok = distintos && r.alto > 150 && r.texto > 10;
  if (!ok) {
    fallos.push(`${f}: ${!distintos ? 'los dos temas pintan igual'
      : r.alto <= 150 ? `alto ${Math.round(r.alto)}px` : 'sin texto'}`);
  }
  console.log(`  ${ok ? '·' : '✗'} ${f.padEnd(38)} alto ${String(Math.round(r.alto)).padStart(4)}px  svg ${r.svg}`);
}

if (errs.length) fallos.push(`${errs.length} excepción(es) de JavaScript: ${errs.join('; ')}`);

try {
  mkdirSync('.shots', { recursive: true });
  for (const [n, f] of [['color', 'fundamentos/color.html'],
    ['codificacion', 'graficos/codificacion.html'], ['vistas', 'componentes/vistas.html']]) {
    await pg.goto(`http://127.0.0.1:${PUERTO}/${f}`, { waitUntil: 'networkidle' });
    await pg.waitForTimeout(300);
    await pg.screenshot({ path: `.shots/KIT-${n}.png`, fullPage: false });
  }
} catch { /* las capturas son cortesía, no una comprobación */ }

await b.close();
bajar();

console.log(`\n  excepciones: ${errs.length}`);
console.log('\n' + '='.repeat(78));
if (fallos.length) {
  console.log(`SISTEMA DE DISEÑO · ${fallos.length} fallo(s)`);
  for (const f of fallos) console.log('  ✗ ' + f);
} else {
  console.log(`SISTEMA DE DISEÑO · ${fichas.length} fichas, generadas y comprobadas`);
}
console.log('='.repeat(78));
process.exit(fallos.length ? 1 : 0);
