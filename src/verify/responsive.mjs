const PUERTO = process.env.PUERTO || 8841;
import { abrir } from './navegador.mjs';
const b = await abrir();
for (const [w,h,etq] of [[430,900,'movil'],[860,1000,'tableta']]) {
  const ctx = await b.newContext({ viewport:{width:w,height:h}, deviceScaleFactor:2 });
  const pg = await ctx.newPage();
  for (const p of ['index','impacto']) {
    await pg.goto(`http://127.0.0.1:${PUERTO}/${p}.html`, {waitUntil:'networkidle'});
    await pg.waitForTimeout(600);
    // ¿desborda horizontalmente?
    const desborde = await pg.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    console.log(`${etq} ${p}: desborde horizontal ${desborde}px`);
    await pg.screenshot({path:`.shots/R-${p}-${etq}.png`});
  }
  await ctx.close();
}
await b.close();
