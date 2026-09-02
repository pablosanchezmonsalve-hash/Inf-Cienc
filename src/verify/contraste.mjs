/* Barrido de contraste sobre el sitio construido.

   Mide LO QUE SE PINTA, no lo que dicen los tokens: los colores se leen de
   getComputedStyle, así que light-dark() ya viene resuelto y el tema activo es
   el real. Tres cuidados que en una versión anterior de esta herramienta
   faltaban y produjeron 62 falsos positivos:

     1. COMPOSICIÓN ALFA. Un fondo rgba(...,.08) no es el fondo: hay que
        componerlo sobre lo que tenga debajo, ancestro a ancestro.
     2. DEGRADADOS. Si un ancestro pinta un gradiente, su background-color es
        transparente. Se extraen todas las paradas del gradiente y se mide
        contra la PEOR, no contra un fondo inventado.
     3. DECORACIÓN. aria-hidden, elementos sin caja y nodos sin texto visible
        no son texto y no tienen umbral que cumplir.

   Umbrales: WCAG 2.1 · 4,5:1 texto normal · 3,0:1 texto grande (≥24px, o
   ≥18,66px en negrita) y objetos gráficos (1.4.11). */

import { readdir } from 'node:fs/promises';
import { abrir } from './navegador.mjs';

const PORT = process.env.PUERTO || 8841;
const PAGINAS = ['index', 'produccion', 'impacto', 'colaboracion', 'tematica',
  'autores', 'publicaciones', 'indicadores', 'produccion-ampliada', 'metodologia', 'autor'];

const medir = () => {
  const lin = c => (c /= 255, c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4);
  const lum = ([r, g, b]) => .2126 * lin(r) + .7152 * lin(g) + .0722 * lin(b);
  const ct = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + .05) / (y + .05); };
  const parse = s => {
    const m = String(s).match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(/[\s,/]+/).filter(Boolean).map(Number);
    return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1];
  };
  const sobre = (f, b) => f.slice(0, 3).map((v, i) => v * f[3] + b[i] * (1 - f[3]));
  const paradas = img => [...String(img).matchAll(/rgba?\([^)]+\)/g)]
    .map(m => parse(m[0])).filter(Boolean);

  /* Fondo efectivo de un elemento: se compone hacia arriba hasta encontrar
     algo opaco. Devuelve una LISTA de fondos candidatos cuando hay gradiente,
     para poder medir contra el peor caso. */
  function fondos(el) {
    let capas = [];
    for (let n = el; n; n = n.parentElement) {
      const cs = getComputedStyle(n);
      if (cs.backgroundImage && cs.backgroundImage !== 'none') {
        const ps = paradas(cs.backgroundImage);
        if (ps.length) { capas.push(ps); continue; }
      }
      const bg = parse(cs.backgroundColor);
      if (bg && bg[3] > 0) { capas.push([bg]); if (bg[3] === 1) break; }
    }
    capas.push([[255, 255, 255, 1]]);
    // Producto cartesiano acotado: cada combinación de paradas compuesta.
    let combos = [[]];
    for (const capa of capas) {
      const sig = [];
      for (const c of combos) for (const p of capa) sig.push([...c, p]);
      combos = sig.slice(0, 24);
    }
    return combos.map(pila => {
      let base = pila[pila.length - 1].slice(0, 3);
      for (let i = pila.length - 2; i >= 0; i--) base = sobre(pila[i], base);
      return base;
    });
  }

  const fallos = [];
  document.querySelectorAll('*').forEach(el => {
    if (el.closest('[aria-hidden="true"]')) return;
    if (!el.getClientRects().length) return;
    const propio = [...el.childNodes]
      .filter(n => n.nodeType === 3 && n.textContent.trim())
      .map(n => n.textContent.trim()).join(' ');
    if (!propio) return;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.opacity === '0') return;
    const col = parse(cs.color);
    if (!col || col[3] === 0) return;
    const px = parseFloat(cs.fontSize);
    const peso = parseInt(cs.fontWeight, 10) || 400;
    const grande = px >= 24 || (px >= 18.66 && peso >= 700);
    const piso = grande ? 3 : 4.5;
    const cands = fondos(el);
    const r = Math.min(...cands.map(f => ct(sobre(col, f), f)));
    if (r < piso - 0.005) {
      fallos.push({
        sel: el.tagName.toLowerCase() + (el.className && typeof el.className === 'string'
          ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : ''),
        txt: propio.slice(0, 42), r: +r.toFixed(2), piso, px, peso,
      });
    }
  });

  /* Objetos gráficos: barras, líneas de referencia, puntos de leyenda. Piso 3:1
     contra la superficie sobre la que están dibujados (WCAG 1.4.11).
     `rect.acum-pista` (el riel de fondo de acumulada(), I-05) faltaba aquí:
     medía 1,21:1/1,08:1 sin que esta batería lo detectara nunca, porque su
     selector no lo cubría — el mismo hueco que dejó pasar el caso real. */
  const graf = [];
  document.querySelectorAll('svg.chart rect.barra, svg.chart circle, svg.chart rect.acum-pista').forEach(el => {
    if (!el.getClientRects().length) return;
    const f = parse(getComputedStyle(el).fill) || parse(el.getAttribute('fill'));
    const trazo = parse(getComputedStyle(el).stroke);
    const pintura = f && f[3] > 0 ? f : trazo;
    if (!pintura || pintura[3] === 0) return;
    const fondo = fondos(el.closest('svg'))[0];
    const r = ct(sobre(pintura, fondo), fondo);
    if (r < 2.995) graf.push({ sel: el.tagName, r: +r.toFixed(2), piso: 3 });
  });

  return { texto: fallos, graficos: graf };
};

/* GUARDA DE COBERTURA, igual que en estructura.mjs y por lo mismo: la lista de
   arriba está escrita a mano porque la ficha de autor no dice nada sin `?id=`,
   pero deja de cubrirlo todo en cuanto alguien añade una página, y este barrido
   seguiría diciendo «0 fallos de contraste» sobre la que no miró. Ya pasó con
   `indicadores.html`: la batería dio verde sobre una página que nunca abrió. */
const DIST = process.argv[2] || process.env.DIST || 'dist';
const enDisco = (await readdir(DIST)).filter(f => f.endsWith('.html'));
const cubiertas = new Set(PAGINAS.map(p => `${p}.html`));
const sinCubrir = enDisco.filter(f => !cubiertas.has(f));
if (sinCubrir.length) {
  console.log(`  ✗ páginas en ${DIST}/ que nadie comprueba: ${sinCubrir.join(', ')}`);
}

const b = await abrir();
let total = 0;
for (const tema of ['light', 'dark']) {
  const ctx = await b.newContext({ viewport: { width: 1360, height: 1000 }, colorScheme: tema });
  const pg = await ctx.newPage();
  for (const p of PAGINAS) {
    const url = `http://127.0.0.1:${PORT}/${p}.html`
      + (p === 'autor' ? '?id=giglio-jimenez-a' : '');
    await pg.goto(url, { waitUntil: 'networkidle' });
    await pg.waitForTimeout(600);
    const r = await pg.evaluate(medir);
    const n = r.texto.length + r.graficos.length;
    total += n;
    console.log(`  ${tema === 'dark' ? 'oscuro' : 'claro '} ${p.padEnd(14)} ${
      n === 0 ? 'sin fallos' : `${n} FALLO(S)`}`);
    r.texto.forEach(f => console.log(
      `      ${f.r}:1 (piso ${f.piso}) ${f.px}px/${f.peso}  ${f.sel}  «${f.txt}»`));
    r.graficos.forEach(f => console.log(`      ${f.r}:1 (piso 3) objeto gráfico ${f.sel}`));
  }
  await ctx.close();
}
await b.close();
console.log(`\n  TOTAL: ${total + sinCubrir.length} fallo(s) de contraste`);
process.exit(total + sinCubrir.length ? 1 : 0);
