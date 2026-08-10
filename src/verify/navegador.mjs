/* navegador.mjs — resolución de Playwright y del binario de Chromium.

   Los seis guiones de verificación llevaban incrustada la ruta del navegador
   (`/opt/pw-browsers/chromium`) y daban por hecho que `playwright` se resolvía
   como dependencia local. Las dos cosas son ciertas en el contenedor donde se
   escribieron y falsas en cualquier otro sitio, así que la verificación no era
   replicable — que es justo lo que este proyecto exige de todo lo demás.

   Aquí se resuelven las dos con una cadena de intentos, y si no hay navegador
   se dice qué instalar en vez de morir con un error de módulo. */

import { createRequire } from 'node:module';
import { existsSync } from 'node:fs';

const require = createRequire(import.meta.url);

/* `playwright` puede estar como dependencia del proyecto, global, o en la ruta
   que indique la variable PLAYWRIGHT. Un import de ESM no mira los módulos
   globales, así que se resuelve a mano y se importa por URL de archivo. */
const CANDIDATOS = [
  process.env.PLAYWRIGHT,
  'playwright',
  '/opt/node22/lib/node_modules/playwright',
  '/usr/lib/node_modules/playwright',
  '/usr/local/lib/node_modules/playwright',
].filter(Boolean);

let playwright = null;
for (const cand of CANDIDATOS) {
  try {
    playwright = await import(cand.startsWith('/')
      ? new URL(`file://${require.resolve(cand)}`).href : cand);
    break;
  } catch { /* siguiente candidato */ }
}

if (!playwright) {
  console.error('No se encontró Playwright. Instálelo con:\n  npm i -D playwright\n'
    + 'o indique su ruta en la variable PLAYWRIGHT.');
  process.exit(2);
}

/* Chromium: el que traiga Playwright por defecto, salvo que haya uno
   preinstalado. En este contenedor lo hay y descargar otro sería tirar 150 MB
   a la basura; en una máquina normal no lo hay y Playwright sabe encontrarlo. */
const RUTAS = [
  process.env.CHROMIUM,
  '/opt/pw-browsers/chromium',
].filter(Boolean).filter(existsSync);

/* Playwright es CommonJS. Importado con `import()` desde ESM, sus exportaciones
   pueden quedar colgando de `.default` en vez de nombradas, según cómo el
   analizador de CJS lea el módulo. Hay que mirar en los dos sitios. */
export const chromium = playwright.chromium ?? playwright.default?.chromium;

if (!chromium) {
  console.error('Playwright se cargó pero no expone `chromium`. Versión incompatible.');
  process.exit(2);
}

/** Opciones de lanzamiento. Se pasa `executablePath` sólo si de verdad existe:
    pasarlo apuntando a la nada rompe con un error mucho peor de leer. */
export const opciones = RUTAS.length ? { executablePath: RUTAS[0] } : {};

export const abrir = () => chromium.launch(opciones);
