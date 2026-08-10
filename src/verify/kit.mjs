import { abrir } from './navegador.mjs';
import { readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
const RAIZ = process.env.KIT || 'design-system';
const fichas = [];
(function walk(d, p = '') {
  for (const f of readdirSync(d)) {
    const full = join(d, f);
    if (statSync(full).isDirectory()) walk(full, p + f + '/');
    else if (f.endsWith('.html')) fichas.push(p + f);
  }
})(RAIZ);

const b = await abrir();
const pg = await (await b.newContext({ viewport: { width: 1100, height: 900 } })).newPage();
let mal = 0;
const errs = [];
pg.on('pageerror', e => errs.push(e.message));
for (const f of fichas.sort()) {
  await pg.goto(`http://127.0.0.1:8843/${f}`, { waitUntil: 'networkidle' });
  await pg.waitForTimeout(200);
  const r = await pg.evaluate(() => {
    const c = document.querySelector('.tema-claro .lienzo');
    const o = document.querySelector('.tema-oscuro .lienzo');
    const bg = el => el ? getComputedStyle(el).backgroundColor : null;
    return {
      claro: bg(c), oscuro: bg(o),
      alto: document.querySelector('.ficha').getBoundingClientRect().height,
      svg: document.querySelectorAll('svg.chart').length,
      texto: document.querySelector('.lienzo').innerText.trim().length,
    };
  });
  // Si el panel oscuro existe, su fondo TIENE que diferir del claro: eso prueba
  // que light-dark() resuelve por contenedor y no por :root.
  const distintos = !r.oscuro || r.claro !== r.oscuro;
  const ok = distintos && r.alto > 150 && r.texto > 10;
  if (!ok) mal++;
  console.log(`  ${ok ? '·' : '✗'} ${f.padEnd(36)} alto ${String(Math.round(r.alto)).padStart(4)}px  svg ${r.svg}  ${r.claro} / ${r.oscuro ?? '—'}`);
}
console.log(`\n  excepciones: ${errs.length}${errs.length ? ' → ' + errs.join('; ') : ''}`);
console.log(`  fichas con problema: ${mal} de ${fichas.length}`);
await pg.goto('http://127.0.0.1:8843/fundamentos/color.html', { waitUntil: 'networkidle' });
await pg.waitForTimeout(300);
await pg.screenshot({ path: '.shots/KIT-color.png', fullPage: false });
await pg.goto('http://127.0.0.1:8843/graficos/codificacion.html', { waitUntil: 'networkidle' });
await pg.waitForTimeout(300);
await pg.screenshot({ path: '.shots/KIT-codificacion.png', fullPage: false });
await pg.goto('http://127.0.0.1:8843/componentes/vistas.html', { waitUntil: 'networkidle' });
await pg.waitForTimeout(300);
await pg.screenshot({ path: '.shots/KIT-vistas.png', fullPage: false });
await b.close();
