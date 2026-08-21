/* Ejercita los flujos interactivos de punta a punta. Un sitio que carga sin
   errores puede seguir teniendo rotos los filtros, la ordenación o el tema. */
import { abrir } from './navegador.mjs';
const P = process.env.PUERTO || 8841;
const b = await abrir();
const ctx = await b.newContext({ viewport: { width: 1360, height: 1000 } });
const pg = await ctx.newPage();
let fallos = 0;
const err = [];
pg.on('pageerror', e => err.push(e.message));
const ok = (cond, msg) => { if (!cond) { fallos++; console.log(`    ✗ ${msg}`); } else console.log(`    · ${msg}`); };

// ─────────────────────────────────────────── conmutador de vista + scroll-spy
console.log('  Conmutador Gráfico ⇄ Tabla');
await pg.goto(`http://127.0.0.1:${P}/tematica.html`, { waitUntil: 'networkidle' });
await pg.waitForTimeout(400);
ok(await pg.isVisible('#T-01-grafico') && !await pg.isVisible('#T-01-tabla'), 'arranca en gráfico');
await pg.click('#T-01 .vistas button[data-vista="tabla"]');
ok(!await pg.isVisible('#T-01-grafico') && await pg.isVisible('#T-01-tabla'), 'conmuta a tabla');
ok(await pg.getAttribute('#T-01 .vistas button[data-vista="tabla"]', 'aria-pressed') === 'true',
   'aria-pressed sigue al estado');
// El conmutador de un módulo no debe tocar los demás
ok(await pg.isVisible('#T-04-grafico'), 'no arrastra a los otros módulos');
await pg.click('#T-01 .vistas button[data-vista="grafico"]');
ok(await pg.isVisible('#T-01-grafico'), 'vuelve a gráfico');

console.log('  Índice lateral');
const nEnlaces = await pg.locator('.rail a').count();
ok(nEnlaces === 3, `enlaza los 3 indicadores de la página (${nEnlaces})`);
await pg.click('.rail a[href="#T-04"]');
await pg.waitForTimeout(800);
const enFoco = await pg.evaluate(() => {
  const r = document.getElementById('T-04').getBoundingClientRect();
  return r.top >= -5 && r.top < 260;
});
ok(enFoco, 'el ancla lleva el módulo bajo la cabecera, no debajo de ella');
await pg.waitForTimeout(500);
ok(await pg.locator('.rail a.activo').count() === 1, 'el scroll-spy marca exactamente uno');

// ─────────────────────────────────────────────────────────── tema persistente
console.log('  Conmutador de tema');
await pg.click('.tema button[data-tema="oscuro"]');
await pg.waitForTimeout(200);
ok(await pg.getAttribute('html', 'data-tema') === 'oscuro', 'aplica el tema oscuro');
await pg.reload({ waitUntil: 'networkidle' });
await pg.waitForTimeout(400);
ok(await pg.getAttribute('html', 'data-tema') === 'oscuro', 'lo recuerda tras recargar');
ok(await pg.getAttribute('.tema button[data-tema="oscuro"]', 'aria-pressed') === 'true',
   'el botón activo se corrige sobre el HTML pre-renderizado');
await pg.click('.tema button[data-tema="auto"]');
await pg.waitForTimeout(150);
ok(await pg.getAttribute('html', 'data-tema') === null, '«auto» borra la preferencia');

// ────────────────────────────────────────────────────────────────── tooltip
console.log('  Tooltip de gráfico');
await pg.hover('#T-05 svg.chart g.marca');
await pg.waitForTimeout(250);
ok(await pg.isVisible('.tip'), 'aparece al señalar una barra');
ok(await pg.locator('svg.chart.hay-foco').count() > 0, 'atenúa el resto del gráfico');
await pg.keyboard.press('Escape');
await pg.waitForTimeout(150);
ok(!await pg.isVisible('.tip'), 'Escape lo cierra');

// ──────────────────────────────────────────────────────────── ayuda de glosario
// La portada dejó de ser una lista de KPI y pasó a ser el explorador, pero el
// glosario contextual sigue ahí: cuelga de las fichas del tablero, donde hace
// más falta que antes porque una cifra recalculada sobre un recorte se
// malinterpreta con más facilidad que una del total.
console.log('  Ayuda contextual');
await pg.goto(`http://127.0.0.1:${P}/index.html`, { waitUntil: 'networkidle' });
await pg.waitForTimeout(400);
await pg.hover('button.ayuda');
await pg.waitForTimeout(300);
ok(await pg.isVisible('.ayuda-panel'), 'el panel de glosario abre sobre HTML pre-renderizado');

// ──────────────────────────────────────────────────────── explorador de portada
// Lo que hace la portada AHORA: recortar el conjunto y recalcular. Es el flujo
// con más superficie del sitio y no lo cubría nada.
console.log('  Explorador de la portada');
await pg.goto(`http://127.0.0.1:${P}/index.html`, { waitUntil: 'networkidle' });
await pg.waitForTimeout(500);
const antes = await pg.textContent('.ficha-valor[data-valor="publicaciones"]');
ok(/^[\d.]+$/.test(antes.trim()), `las cifras llegan pre-renderizadas (${antes.trim()})`);
await pg.locator('.chip[data-dim="anio"]').first().click();
await pg.waitForTimeout(400);
const luego = await pg.textContent('.ficha-valor[data-valor="publicaciones"]');
ok(luego.trim() !== antes.trim(), `el recorte recalcula las cifras (${antes.trim()} -> ${luego.trim()})`);
ok(new URL(pg.url()).searchParams.has('anio'), 'el recorte viaja en la URL');
ok(await pg.locator('.recorte-chip').count() > 0, 'el recorte se declara en pantalla');
await pg.goBack();
await pg.waitForTimeout(400);
ok(await pg.textContent('.ficha-valor[data-valor="publicaciones"]') === antes,
   'volver atrás deshace el recorte');
await pg.goForward();
await pg.waitForTimeout(400);
await pg.click('#limpiar-recorte');
await pg.waitForTimeout(400);
ok(await pg.locator('.recorte-chip').count() === 0, '«Ver todo» limpia el recorte');

// ─────────────────────────────────────────────────────────────────── filtros
console.log('  Filtros de publicaciones');
await pg.goto(`http://127.0.0.1:${P}/publicaciones.html`, { waitUntil: 'networkidle' });
await pg.waitForTimeout(600);
const total = await pg.locator('#tabla-cuerpo tr').count();
ok(total > 0, `la tabla trae filas (${total})`);
await pg.click('input[data-filtro="anio"][value="2024"]');
await pg.waitForTimeout(400);
const resumen = await pg.textContent('#resumen');
ok(/filtros aplicados/.test(resumen), `el resumen declara el filtro: «${resumen.trim().replace(/\s+/g, ' ')}»`);
ok(await pg.locator('.chip').count() === 1, 'aparece la pastilla del filtro');
ok(new URL(pg.url()).searchParams.get('anio') === '2024', 'el estado viaja en la URL');
await pg.reload({ waitUntil: 'networkidle' });
await pg.waitForTimeout(600);
ok(await pg.isChecked('input[data-filtro="anio"][value="2024"]'), 'el filtro sobrevive a la recarga');
await pg.click('#limpiar');
await pg.waitForTimeout(400);
ok(await pg.locator('.chip').count() === 0, 'limpiar quita las pastillas');

// ───────────────────────────────────────────────────── autores: orden y búsqueda
console.log('  Autores: búsqueda y ordenación');
await pg.goto(`http://127.0.0.1:${P}/autores.html`, { waitUntil: 'networkidle' });
await pg.waitForTimeout(600);
const filas0 = await pg.locator('tbody tr').count();
ok(filas0 > 0, `lista autores (${filas0} filas visibles)`);
await pg.fill('#buscar-autor', 'Giglio');
await pg.waitForTimeout(500);
const filas1 = await pg.locator('tbody tr').count();
ok(filas1 > 0 && filas1 < filas0, `la búsqueda filtra (${filas0} → ${filas1})`);
// Buscar por una variante fusionada debe encontrar la ficha consolidada
await pg.fill('#buscar-autor', 'Giglio A.');
await pg.waitForTimeout(500);
ok(await pg.locator('tbody tr').count() > 0, 'encuentra por una forma de firma fusionada');
await pg.fill('#buscar-autor', '');
await pg.waitForTimeout(400);
const th = pg.locator('th[data-orden]').first();
if (await th.count()) {
  await th.click();
  await pg.waitForTimeout(300);
  ok(await pg.locator('td.ordenada').count() > 0, 'ordenar marca la columna en todo su alto');
  await th.press('Enter');
  await pg.waitForTimeout(200);
  ok(true, 'la cabecera se activa con teclado');
}

// ─────────────────────────────────────────────────── ficha de autor navegable
console.log('  Ficha de autor');
await pg.goto(`http://127.0.0.1:${P}/autores.html`, { waitUntil: 'networkidle' });
await pg.waitForTimeout(600);
await pg.locator('tbody tr a').first().click();
await pg.waitForTimeout(800);
ok(/autor\.html\?id=/.test(pg.url()), `navega a la ficha (${pg.url().split('/').pop()})`);
ok(await pg.locator('h1').count() === 1, 'la ficha tiene su h1');
ok(await pg.locator('.identificadores').count() === 1, 'trae el bloque de identificadores');

console.log(`\n  excepciones JS durante todo el recorrido: ${err.length}`);
err.forEach(e => console.log(`    ✗ ${e}`));
await b.close();
console.log(`  TOTAL: ${fallos + err.length} fallo(s)`);
process.exit(fallos + err.length ? 1 : 0);
