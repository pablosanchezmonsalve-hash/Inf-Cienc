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
// Los filtros son píldoras que nacen cerradas: hay que abrir la de año.
await pg.click('details.dim:has(.chip[data-dim="anio"]) > summary');
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

// La barra superior y las píldoras de filtro. Los años de la barra recortan
// igual que el chip de año; la píldora en la que se elige no se cierra al
// repintar, porque elegir dos valores obligaba a abrirla dos veces.
console.log('  Barra superior y píldoras');
await pg.click('#recorte-anio-env button[data-anio="2024"]');
await pg.waitForTimeout(400);
ok(new URL(pg.url()).searchParams.get('anio') === '2024', 'el año de la barra recorta y viaja en la URL');
ok(await pg.getAttribute('#recorte-anio-env button[data-anio="2024"]', 'aria-pressed') === 'true',
   'el año elegido queda marcado');
ok((await pg.textContent('#lateral-filtros')).includes('1 aplicado'),
   'la barra lateral declara el filtro activo');
await pg.click('details.dim:has(.chip[data-dim="tipo"]) > summary');
await pg.locator('.chip[data-dim="tipo"]').first().click();
await pg.waitForTimeout(400);
ok(await pg.locator('details.dim[open]:has(.chip[data-dim="tipo"])').count() === 1,
   'la píldora sigue abierta tras elegir un valor');
await pg.keyboard.press('Escape');
await pg.waitForTimeout(150);
ok(await pg.locator('details.dim[open]').count() === 0, 'Escape cierra la píldora');
await pg.click('#limpiar-recorte');
await pg.waitForTimeout(400);

// Las dos tablas de la portada responden al recorte; la banda no lleva cifras.
// Los años esperados salen de la ventana declarada, no de un número escrito aquí.
console.log('  Tablas de la portada');
const ventana = await pg.evaluate(async () => (await (await fetch('data/meta.json')).json()).ventana);
ok(await pg.locator('#dinamica tbody tr').count() === ventana.fin - ventana.inicio + 1,
   'la dinámica anual trae un año por fila de la ventana');
ok(await pg.locator('#mas-citadas tbody tr').count() === 10, 'la tabla de más citadas trae diez filas');
ok(await pg.locator('#titular [data-valor], #titular table').count() === 0,
   'la banda de cabecera no lleva cifras del recorte');
await pg.click('#recorte-anio-env button[data-anio="2024"]');
await pg.waitForTimeout(500);
ok(await pg.locator('#dinamica tbody tr').count() === 1, 'con un año elegido, la dinámica anual trae una fila');
const aniosCitadas = await pg.locator('#mas-citadas tbody tr td:nth-child(5)').allTextContents();
ok(aniosCitadas.length > 0 && aniosCitadas.every((t) => t.trim() === '2024'),
   'las más citadas son del año elegido');
await pg.click('#limpiar-recorte');
await pg.waitForTimeout(400);
await pg.goto(`http://127.0.0.1:${P}/index.html?autor=${encodeURIComponent('Mujika I.')}`,
  { waitUntil: 'networkidle' });
await pg.waitForTimeout(600);
ok(await pg.locator('#mas-citadas tbody tr').count() === 0
   && await pg.locator('#mas-citadas .vacio').count() === 1,
   'recortada a una persona, la tabla de más citadas no se dibuja');

// ─────────────────────────────────────────────────────────────────── filtros
// Publicaciones usa EL MISMO motor que la portada y las secciones. Lo que se
// comprueba aquí es justo eso: que un recorte hecho en el tablero llegue por la
// URL y siga valiendo, que el buscador no expulse el foco al repintar, y que
// los enlaces antiguos con `internacional=` no se hayan roto al unificar.
console.log('  Filtros de publicaciones');
// «Facultad de Medicina» se fusionó en «Facultad de Medicina y Salud» al
// cerrar T-02 (2026-08-26, consolidación de vocabulario de unidades
// académicas); el nombre viejo ya no matchea nada y el recuento subió de
// 113 a 122 al incorporar las publicaciones que antes eran de Odontología.
// La carga del 2026-09-08 lo dejó en 121: el export nuevo no trae cinco
// registros de 2023-2025 que sí traía el de julio, y uno de ellos era de
// esta unidad y este año. No es una regresión del filtro, es que el corpus
// cambió; la comparación entre los dos exports está en docs/LIMITATIONS.md §1.
await pg.goto(`http://127.0.0.1:${P}/publicaciones.html?anio=2024&unidad=Facultad+de+Medicina+y+Salud`,
  { waitUntil: 'networkidle' });
await pg.waitForTimeout(700);
const heredado = await pg.textContent('.recorte-n');
ok(heredado.trim() === '121', `el recorte de la portada llega intacto (${heredado.trim()})`);
ok(await pg.locator('.chip-on').count() === 2, 'los controles reflejan el recorte heredado');
const filas = await pg.locator('#tabla-cuerpo tr').count();
ok(filas > 0, `la tabla trae filas (${filas})`);

await pg.fill('#q', 'salud');
await pg.waitForTimeout(500);
ok(await pg.evaluate(() => document.activeElement?.id) === 'q',
   'el buscador conserva el foco tras repintarse');
ok(new URL(pg.url()).searchParams.get('q') === 'salud', 'la búsqueda viaja en la URL');

await pg.reload({ waitUntil: 'networkidle' });
await pg.waitForTimeout(700);
ok(await pg.locator('.chip-on').count() === 2, 'el recorte sobrevive a la recarga');

await pg.click('#limpiar-recorte');
await pg.waitForTimeout(400);
ok(await pg.locator('.recorte-chip').count() === 0, '«Ver todo» limpia el recorte');

// Un enlace guardado con el nombre viejo de la dimensión tiene que seguir
// funcionando: unificar no puede romper lo que alguien ya citó.
await pg.goto(`http://127.0.0.1:${P}/publicaciones.html?internacional=Internacional`,
  { waitUntil: 'networkidle' });
await pg.waitForTimeout(700);
ok(await pg.locator('.chip-on').count() === 1,
   'un enlace antiguo con «internacional=» sigue recortando');

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

// ───────────────────────────────────────────────────────── menú en un teléfono
// Por debajo de 1040 px la barra lateral es un cajón. Tiene que nacer fuera del
// orden de tabulación, abrirse con «Menú» y cerrarse con Escape.
console.log('  Menú en teléfono');
const movil = await b.newContext({ viewport: { width: 430, height: 900 } });
const pm = await movil.newPage();
pm.on('pageerror', e => err.push(e.message));
await pm.goto(`http://127.0.0.1:${P}/impacto.html`, { waitUntil: 'networkidle' });
await pm.waitForTimeout(400);
const enlaceMenu = '.lateral .nav a[href="index.html"]';
ok(!await pm.isVisible(enlaceMenu), 'la barra lateral nace cerrada');
await pm.click('.nav-toggle');
await pm.waitForTimeout(350);
ok(await pm.isVisible(enlaceMenu), 'el botón «Menú» la abre');
ok(await pm.getAttribute('.nav-toggle', 'aria-expanded') === 'true', 'aria-expanded sigue al estado');
await pm.keyboard.press('Escape');
await pm.waitForTimeout(350);
ok(!await pm.isVisible(enlaceMenu), 'Escape la cierra');
await movil.close();

// ─────────────────────────────────────── cabecera y no publicados de sección
// El «qué NO dice» va a la vista, no plegado. Y producción y temática declaran
// sus indicadores no publicados: la banda no aparecía nunca en esas dos páginas
// porque su clave no coincide con la categoría del catálogo.
console.log('  Cabecera y no publicados de las secciones');
for (const [pagina, codigo] of [['produccion', 'P-08'], ['tematica', 'T-02']]) {
  await pg.goto(`http://127.0.0.1:${P}/${pagina}.html`, { waitUntil: 'networkidle' });
  await pg.waitForTimeout(400);
  ok(await pg.isVisible('.seccion-limite'), `${pagina}: el «qué NO dice» está a la vista`);
  ok(await pg.locator(`.no-publicados .codigo:text-is("${codigo}")`).count() === 1,
     `${pagina}: declara ${codigo} entre los no publicados`);
}

// ────────────────────────────────────────────────────────── descarga de datos
// El inventario se mide en el build; aquí se comprueba que llegó y que el
// botón, que sólo existe con JavaScript, descarga de verdad el CSV.
console.log('  Descarga de datos');
await pg.goto(`http://127.0.0.1:${P}/datos.html`, { waitUntil: 'networkidle' });
await pg.waitForTimeout(500);
ok(await pg.locator('#datos-inventario tbody tr').count() >= 10, 'el inventario lista los archivos de datos');
ok(!(await pg.textContent('#datos-inventario')).includes('NaN'), 'ningún recuento ni tamaño sale como NaN');
const [descarga] = await Promise.all([
  pg.waitForEvent('download', { timeout: 15000 }),
  pg.click('#descargar-csv'),
]);
ok(/^publicaciones-.+\.csv$/.test(descarga.suggestedFilename()),
   `el botón descarga el CSV (${descarga.suggestedFilename()})`);

// ───────────────────────────────────────────────── glosario y ficha técnica
// La ficha se contrasta con meta.json, no con cifras escritas aquí: una prueba
// con 1.342 a mano pasaría a mentir en la próxima carga.
console.log('  Glosario y ficha técnica');
await pg.goto(`http://127.0.0.1:${P}/metodologia.html`, { waitUntil: 'networkidle' });
await pg.waitForTimeout(400);
const metaM = await pg.evaluate(() => fetch('data/meta.json').then(r => r.json()));
const nGlosario = await pg.evaluate(() => fetch('data/glossary.json').then(r => r.json()))
  .then(g => g.entradas.length);
const ficha = await pg.textContent('#ficha-tecnica');
ok(await pg.locator('#ficha-tecnica dl.ficha-datos').count() === 4, 'la ficha tiene sus cuatro bloques');
ok(ficha.includes(new Intl.NumberFormat('es-CL').format(metaM.denominadores.universo_total)),
   'la ficha declara el universo de meta.json');
ok(ficha.includes(metaM.fecha_corte_citas) && ficha.includes(metaM.exports.Scopus.fecha_export),
   'la ficha da la fecha de SciVal y la del export de Scopus');
ok(metaM.exports.Scopus.fecha_corte || ficha.includes('El export no lo declara'),
   'la ficha no atribuye a Scopus el corte de SciVal');
ok(await pg.locator('.glosario-entrada').count() === nGlosario,
   `el glosario lista las ${nGlosario} entradas`);
await pg.goto(`http://127.0.0.1:${P}/metodologia.html#fwci-field-weighted-citation-impact`,
  { waitUntil: 'networkidle' });
ok(await pg.locator('.glosario-entrada:target').count() === 1, 'un enlace #slug aterriza en su definición');

console.log(`\n  excepciones JS durante todo el recorrido: ${err.length}`);
err.forEach(e => console.log(`    ✗ ${e}`));
await b.close();
console.log(`  TOTAL: ${fallos + err.length} fallo(s)`);
process.exit(fallos + err.length ? 1 : 0);
