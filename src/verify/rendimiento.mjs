/* LCP con repeticiones y mediana. Una sola muestra en un contenedor compartido
   es ruido: la primera corrida publicada daba 776 ms y la siguiente 916 ms para
   la misma página. Se reporta la mediana de N corridas y el rango. */
import { abrir } from './navegador.mjs';
const N = 5;
const PAGINAS = ['index', 'impacto', 'tematica'];
const b = await abrir();

async function lcp(port, p) {
  const ctx = await b.newContext({ viewport: { width: 1360, height: 900 } });
  const pg = await ctx.newPage();
  const cdp = await ctx.newCDPSession(pg);
  await cdp.send('Network.emulateNetworkConditions', {
    offline: false, latency: 150,
    downloadThroughput: 1.6 * 1024 * 1024 / 8, uploadThroughput: 750 * 1024 / 8,
  });
  await pg.goto(`http://127.0.0.1:${port}/${p}.html`, { waitUntil: 'load' });
  const v = await pg.evaluate(() => new Promise(res => {
    let ult = -1;
    new PerformanceObserver(l => { ult = l.getEntries().at(-1).startTime; })
      .observe({ type: 'largest-contentful-paint', buffered: true });
    setTimeout(() => res(ult), 2500);
  }));
  await ctx.close();
  return v;
}

const mediana = a => { const s = [...a].sort((x, y) => x - y); return s[Math.floor(s.length / 2)]; };
const r = n => Math.round(n);

console.log(`  Slow 4G · mediana de ${N} corridas por celda\n`);
console.log('  página      sin pre-render        pre-renderizado       mejora');
for (const p of PAGINAS) {
  const sin = [], con = [];
  for (let i = 0; i < N; i++) { sin.push(await lcp(process.env.PUERTO_SIN || 8842, p)); con.push(await lcp(process.env.PUERTO || 8841, p)); }
  const ms = mediana(sin), mc = mediana(con);
  console.log(`  ${p.padEnd(11)} ${String(r(ms)).padStart(5)} ms [${r(Math.min(...sin))}–${r(Math.max(...sin))}]`
    + `   ${String(r(mc)).padStart(5)} ms [${r(Math.min(...con))}–${r(Math.max(...con))}]`
    + `   ${(100 * (ms - mc) / ms).toFixed(0).padStart(4)} %`);
}
await b.close();
