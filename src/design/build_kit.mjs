/* build_kit.mjs — genera el paquete de sistema de diseño para Claude Design.

   POR QUÉ SE GENERA Y NO SE ESCRIBE A MANO
   Un sistema de diseño documentado a mano empieza siendo verdad y deja de
   serlo en la primera corrección que alguien hace en `app.css` sin acordarse
   de la ficha. Aquí cada ficha se construye a partir de las fuentes reales:

     · la hoja de estilo desplegable, incrustada entera en cada ficha, de modo
       que la previsualización usa EXACTAMENTE los estilos que se sirven;
     · los constructores de gráfico de `core.js` y los de módulo de `vista.js`,
       ejecutados bajo Node, igual que hace el pre-renderizador;
     · los artefactos de datos reales de `data/processed/`, no datos de
       relleno. Un componente de bibliometría enseñado con cifras inventadas
       contradice `<non_negotiable_rules>` incluso en una ficha de diseño;
     · las razones de contraste, CALCULADAS aquí a partir de los tokens leídos
       de la hoja. No se copian de una tabla: una tabla copiada se desactualiza
       en silencio, un cálculo no.

   Cada ficha lleva en su primera línea el marcador `@dsCard`, que es lo que el
   panel de Claude Design usa para construir su índice.

   Uso:  node src/design/build_kit.mjs [salida]     (por defecto design-system/)
*/

import { readFile, writeFile, mkdir, rm, cp } from 'node:fs/promises';
import { join, resolve, dirname } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';

// `fileURLToPath` y no `new URL(...).pathname`: la ruta de la URL conserva la
// barra inicial y los caracteres codificados, y en Windows daba
// «C:\C:\…\CIENCIOMETR%C3%8DA»: el generador no arrancaba en ese equipo.
const RAIZ = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const SALIDA = resolve(process.argv[2] || join(RAIZ, 'design-system'));
const DATOS = join(RAIZ, 'data', 'processed');

const css = await readFile(join(RAIZ, 'web/assets/css/app.css'), 'utf8');
const mod = (n) => import(pathToFileURL(join(RAIZ, 'web/assets/js', n)).href);
const c = await mod('core.js');
const v = await mod('vista.js');
/* El explorador es hoy el dueño del marcado del sitio: la portada y las cuatro
   secciones se dibujan desde aquí. Hasta el 2026-09-16 este generador llamaba a
   `v.hero`, `v.rail`, `v.modulo`, `v.kpis`, `v.kpisRestantes` y `v.RENDER`, que
   `vista.js` dejó de exportar cuando el corte sustituyó al módulo — y con eso
   `make kit` llevaba tres semanas sin arrancar (`D-602`). */
const vx = await mod('vista_explorador.js');
const X = await mod('explorador.js');
const dato = async (n) => JSON.parse(await readFile(join(DATOS, n), 'utf8'));

const meta = await dato('meta.json');
const series = await dato('series.json');
const { kpis } = await dato('kpis.json');

/* Los mismos artefactos y con los mismos nombres que `src/build/prerender.mjs`:
   si el kit se alimentara distinto, enseñaría un componente que el sitio no
   sirve. Ésa es la única razón por la que esta sección existe. */
const { publicaciones } = await dato('publications.json');
const catalogo = await dato('catalogo.json');
const autoresJson = await dato('authors.json');
const { lecturas } = await dato('lecturas.json');
const proc = vx.procedencias(series, meta);
const jerarquia = meta.jerarquia || {};
const umbral = autoresJson.parametros?.n_minimo_interpretable;
const unidadPorPersona = new Map(
  autoresJson.autores.map((a) => [a.nombre, (a.unidades || [])[0]]));
const textos = {
  lecturas,
  advertencias: Object.fromEntries(
    catalogo.indicadores.filter((i) => i.advertencia).map((i) => [i.codigo, i.advertencia])),
};

/** El corte de un indicador, tal cual lo declara la sección que lo publica.
    Se busca en `SECCIONES` en vez de escribirlo aquí: la forma de cada gráfico
    la fija esa tabla (`D-378`), y una segunda copia divergiría. */
const corteDe = (cod) => {
  for (const s of Object.values(vx.SECCIONES)) {
    const x = (s.cortes || []).find((k) => k.cod === cod);
    if (x) return x;
  }
  throw new Error(`No hay corte declarado para ${cod} en SECCIONES`);
};
/** Ese corte, dibujado sobre el corpus entero y con el componente real. */
const corte = (cod) => vx.corteUno(publicaciones, corteDe(cod),
  { proc, jerarquia, unidadPorPersona, textos });

/** Sólo la FIGURA de ese corte, para las fichas del grupo «Gráficos», que
    documentan la forma y no el componente que la envuelve. Sale del mismo
    `dibujar()` que usa el sitio: antes estas fichas llamaban a `v.RENDER[cod]`
    sobre `series.json`, es decir a una serie ya calculada, y el sitio dejó de
    servirlas cuando el explorador pasó a derivarlas de las publicaciones. */
const figura = (cod) => {
  const r = vx.dibujar(publicaciones, corteDe(cod), jerarquia);
  if (!r) throw new Error(`${cod} no dibuja nada sobre el corpus entero`);
  return r.svg;
};

/* El valor vigente de un KPI, por código. Las fichas lo usan en vez de escribir
   la cifra: la de tipografía llevaba «823» y un FWCI de «0,87» congelados desde
   una carga anterior, y una ficha que promete datos reales enseñaba dos que ya
   no lo eran. */
const kpi = (codigo) => {
  const k = kpis.find((x) => x.codigo === codigo);
  if (!k) throw new Error(`No hay KPI ${codigo} en kpis.json`);
  return k.valor;
};

/* ─────────────────────────────────────────────── medición de contraste */
const lin = (x) => (x /= 255, x <= 0.04045 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4);
const rgb = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
const lum = (h) => { const [r, g, b] = rgb(h).map(lin); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
const ct = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
const ratio = (a, b) => ct(a, b).toFixed(2).replace('.', ',');

/* Distancia perceptual en OKLab, ×100. Es un PORTE literal de la que usa
   src/design/validar_paleta.py (`oklab()` y `delta_e()`), y tiene que dar el
   mismo número que ella: las fichas publican la misma medida que valida el
   sistema, así que dos matemáticas distintas serían dos verdades.

   Existe porque hasta el 2026-09-16 las separaciones ΔE de estas fichas eran
   prosa escrita a mano, y sobrevivieron a un cambio de paleta entero: el kit
   publicaba «la advertencia ámbar, ΔE 28,6» con la advertencia ya en verde
   moneda y la separación real en 26,0. Una cifra que no se calcula deja de ser
   cierta en silencio, que es lo que este archivo promete no hacer. */
const oklab = (h) => {
  const [r, g, b] = rgb(h).map(lin);
  const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
  const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
  const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
  return [0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
          1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
          0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s];
};
const dE = (a, b) => 100 * Math.hypot(...oklab(a).map((v, i) => v - oklab(b)[i]));
const deltaE = (a, b) => dE(a, b).toFixed(1).replace('.', ',');

/* Lee los tokens de la hoja: `--x: light-dark(#aaa, #bbb);`. La ficha de color
   se dibuja con estos valores, así que cambiar la hoja cambia la ficha.

   SÓLO del bloque `:root`. Recorrer la hoja entera y quedarse con la ÚLTIMA
   aparición de cada token era un error real: `.banda-contraste` redefine
   --superficie, --superficie-2, --plano, --linea, --linea-fuerte y --red en su
   propio ámbito, y esos valores pisaban los de :root. La ficha de color medía
   entonces la tinta de :root contra el suelo OSCURO de la banda y publicaba
   razones de contraste que no le pasan a ningún lector.

   Es el mismo fallo que src/design/validar_paleta.py documenta haber corregido
   en su `_bloque()`, en el otro archivo del sistema de diseño. Se corrigió allí
   y siguió vivo aquí porque este generador no arranca desde el 2026-08-26. */
const bloqueRaiz = (() => {
  const i = css.indexOf(':root');
  const a = css.indexOf('{', i);
  return css.slice(a + 1, css.indexOf('}', a));
})();
const TOKENS = {};
for (const m of bloqueRaiz.matchAll(/(--[a-z0-9-]+):\s*light-dark\(\s*(#[0-9a-f]{6})\s*,\s*(#[0-9a-f]{6})\s*\)/gi)) {
  TOKENS[m[1]] = { claro: m[2].toLowerCase(), oscuro: m[3].toLowerCase() };
}
if (!TOKENS['--superficie']) throw new Error('No se leyó ningún token light-dark() de :root en app.css');

/* Atajos para escribir una medida DENTRO de la prosa de una ficha, que es
   justo donde las cifras se congelaban: `sep('--serie-1','--aviso-borde','claro')`
   se lee casi como la frase que sustituye, y se recalcula al generar. */
const sep = (a, b, t) => deltaE(TOKENS[a][t], TOKENS[b][t]);
const cr = (a, b, t) => ratio(TOKENS[a][t], TOKENS[b][t]);
/* Separador de miles del proyecto: 1.342, no 1,342 ni 1342. */
const miles = (n) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, '.');

/* El fondo de una banda no es un token: vive en su propia regla, como
   `background: light-dark(#eff6ff, #00143d)`. Se lee de ahí en vez de
   deducirlo de un token que hoy coincida, porque esa coincidencia no la
   declara nadie y se rompería sola. */
function fondoDeRegla(selector) {
  const m = css.match(
    new RegExp(`\\${selector}\\s*\\{[^}]*background:\\s*light-dark\\(\\s*(#[0-9a-f]{6})\\s*,\\s*(#[0-9a-f]{6})\\s*\\)`, 'i'));
  if (!m) throw new Error(`No se encuentra el fondo light-dark() de ${selector} en app.css`);
  return { claro: m[1].toLowerCase(), oscuro: m[2].toLowerCase() };
}
const BANDA_ENFASIS = fondoDeRegla('.banda-enfasis');
/* Contraste de un token de :root sobre el fondo de una banda que NO redefine
   tokens: es lo que ve de verdad quien lee dentro de ella. */
const sobreBanda = (tok, banda, t) => ratio(TOKENS[tok][t], banda[t]);

/* ─────────────────────────────────────────────── armazón de cada ficha */

/** Una ficha del panel de diseño.

    La hoja va incrustada entera, no enlazada: cada ficha tiene que poder
    abrirse sola. `color-scheme` se declara en el panel y no en :root, que es
    lo que permite enseñar los dos temas uno al lado del otro — light-dark()
    resuelve según el color-scheme del elemento donde se sustituye la variable,
    no según el de la raíz. */
function ficha({ grupo, nombre, subtitulo, intro, cuerpo, dosTemas = true, ancho = 900 }) {
  /* `cuerpo` se evalúa UNA VEZ POR PANEL, no una vez por ficha. Inyectar la
     misma cadena en los dos paneles duplicaba los identificadores del SVG, y
     los patrones de trama se referencian por id: el panel oscuro terminaba
     apuntando al patrón del claro. Un `id` repetido en un documento es un
     error aunque a veces no se note. */
  const construir = typeof cuerpo === 'function' ? cuerpo : () => cuerpo;
  const panel = (tema) => `
    <section class="panel tema-${tema}">
      <p class="panel-etq">${tema === 'claro' ? 'Tema claro' : 'Tema oscuro'}</p>
      <div class="lienzo">${construir(tema)}</div>
    </section>`;
  return `<!-- @dsCard group="${grupo}" name="${nombre}" subtitle="${subtitulo}" width="${ancho}" -->
<!doctype html>
<html lang="es" class="js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${nombre} — Sistema de diseño</title>
<style>
${css}
</style>
<style>
/* Cromo de la ficha. No forma parte del sistema: sólo enmarca la muestra. */
  body { background: var(--plano); padding: 0; margin: 0; }
  .ficha { padding: var(--e5); max-width: ${ancho + 80}px; }
  .ficha > h1 { font-size: var(--t-xl); margin: 0 0 var(--e2); }
  .ficha > .intro { font-size: var(--t-m); max-width: 78ch; margin: 0 0 var(--e5); }
  .paneles { display: grid; gap: var(--e4); }
  @media (min-width: 940px) { .paneles.dos { grid-template-columns: 1fr 1fr; } }
  .panel { min-width: 0; }
  .tema-claro { color-scheme: light; }
  .tema-oscuro { color-scheme: dark; }
  .panel-etq {
    font: 700 var(--t-xs)/1 var(--f-ui); letter-spacing: .12em; text-transform: uppercase;
    color: var(--tinta-3); margin: 0 0 var(--e2);
  }
  .lienzo {
    background: var(--plano); color: var(--tinta);
    border: 1px solid var(--linea); border-radius: var(--radio);
    padding: var(--e4); overflow: hidden;
  }
  .lienzo > .modulo:last-child, .lienzo > .kpis { margin-bottom: 0; }
  .regla {
    font-size: var(--t-s); color: var(--tinta-2); line-height: 1.55;
    border-left: 2px solid var(--linea-fuerte); padding-left: var(--e3);
    margin: var(--e4) 0 0; max-width: 78ch;
  }
  .regla b { color: var(--tinta); }
  .muestras { display: grid; gap: var(--e3); grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); }
  .muestra { border: 1px solid var(--linea); border-radius: var(--radio-s);
    overflow: hidden; display: flex; flex-direction: column; }
  .muestra .pie { flex: 1; }
  .muestra .tinte { height: 54px; }
  .muestra .pie { padding: var(--e2) var(--e3); background: var(--superficie); }
  .muestra code { font: 600 var(--t-xs)/1.4 var(--f-mono); color: var(--tinta); display: block; }
  .muestra .hex { font: 400 var(--t-xs)/1.5 var(--f-mono); color: var(--tinta-3); }
  .muestra .medida { font-size: var(--t-xs); color: var(--tinta-2); margin-top: 2px; }
  .muestra .medida b { color: var(--tinta); font-variant-numeric: tabular-nums; }
</style>
</head>
<body>
<div class="ficha">
  <h1>${nombre}</h1>
  <p class="intro">${intro}</p>
  <div class="paneles ${dosTemas ? 'dos' : ''}">
    ${dosTemas ? panel('claro') + panel('oscuro') : panel('claro')}
  </div>
</div>
</body>
</html>
`;
}

/* ───────────────────────────────────────────────────────── fundamentos */

function muestrasColor(lista, fondoTok) {
  return `<div class="muestras">${lista.map(([tok, uso, piso]) => {
    const t = TOKENS[tok];
    if (!t) return '';
    const f = TOKENS[fondoTok];
    const rc = ct(t.claro, f.claro), ro = ct(t.oscuro, f.oscuro);
    const bien = piso === null || (rc >= piso && ro >= piso);
    return `<div class="muestra">
      <div class="tinte" style="background:var(${tok})"></div>
      <div class="pie">
        <code>${tok}</code>
        <span class="hex">${t.claro} · ${t.oscuro}</span>
        ${piso === null ? '' : `<div class="medida">sobre <code style="display:inline">${fondoTok}</code><br>
          <b>${ratio(t.claro, f.claro)}:1</b> · <b>${ratio(t.oscuro, f.oscuro)}:1</b>
          ${bien ? `(piso ${String(piso).replace('.', ',')} ✓)` : '(NO CUMPLE)'}</div>`}
      </div>
    </div>`;
  }).join('')}</div>`;
}

const CARDS = [];
const añadir = (ruta, contenido) => CARDS.push({ ruta, contenido });

añadir('fundamentos/color.html', ficha({
  grupo: 'Fundamentos', nombre: 'Color', ancho: 1000,
  subtitulo: 'Superficies, tinta, marca, dato y advertencia · medido en los dos temas',
  intro: `Cada color despeja un umbral comprobable. Las razones de contraste de esta
    ficha <strong>se calculan al generarla</strong> a partir de los tokens de la hoja de
    estilo: si un token cambia, la cifra cambia con él. La identidad es roja, pero
    <strong>no es el rojo institucional oficial de la Universidad Finis Terrae</strong>:
    no se pudo verificar y no se inventó.`,
  dosTemas: false,
  cuerpo: `
    <p class="panel-etq" style="margin-top:0">Superficies y tinta</p>
    ${muestrasColor([
      ['--plano', 'fondo de página', null],
      ['--superficie', 'tarjetas', null],
      ['--superficie-2', 'superficie alterna', null],
      ['--tinta', 'texto principal', 4.5],
      ['--tinta-2', 'texto secundario', 4.5],
    ], '--superficie')}
    ${muestrasColor([['--tinta-3', 'metadatos y ejes, sobre su PEOR fondo', 4.5]], '--superficie-2')}
    <p class="panel-etq" style="margin-top:var(--e5)">Marca y acción · nunca codifican un dato</p>
    ${muestrasColor([
      ['--marca', 'cabecera', null],
      ['--marca-tinta', 'texto sobre la cabecera', null],
      ['--cifra', 'cifra grande de KPI', 3],
      ['--accion', 'enlaces y controles', 4.5],
      ['--accion-viva', 'rellenos y filetes', null],
    ], '--superficie')}
    <p class="panel-etq" style="margin-top:var(--e5)">Dato · una sola serie en uso, más el par del anillo</p>
    ${muestrasColor([
      ['--serie-1', 'color de dato', 3],
      ['--serie-2', 'segunda ranura, anillo C-01', 3],
      ['--sin-dato', 'ausencia de dato', 3],
    ], '--superficie')}
    <p class="panel-etq" style="margin-top:var(--e5)">Rampa ordinal · Q1 a Q4, escala ORDENADA</p>
    ${muestrasColor([
      ['--ord-1', 'Q1', 3], ['--ord-2', 'Q2', 3], ['--ord-3', 'Q3', 3], ['--ord-4', 'Q4', 3],
    ], '--superficie')}
    <p class="panel-etq" style="margin-top:var(--e5)">Advertencia metodológica · esmeralda, fuera de la familia del dato</p>
    ${muestrasColor([
      ['--aviso-borde', 'línea de referencia', null],
      ['--aviso-tinta-grafico', 'etiqueta de referencia', 4.5],
    ], '--superficie')}
    <p class="regla"><b>Tres reglas que no se negocian.</b>
      La ausencia de dato siempre es gris, ignorando la escala pedida: un valor no
      medido no puede parecerse a uno medido. El color sigue a la entidad, nunca a
      su posición: al filtrar, un color ligado al rango saltaría de una entidad a
      otra. Y si el nombre de la categoría ya es un color —Gold, Green, Bronze— el
      color deja de estar disponible para codificar.</p>
    <p class="regla"><b>Separación dato ↔ advertencia.</b> El dato es azul marino y
      la advertencia esmeralda, la paleta de Stitch (D-678): familias opuestas.
      Medido en OKLab al generar esta ficha: ΔE
      <b>${sep('--serie-1', '--aviso-borde', 'claro')}</b> en claro y
      <b>${sep('--serie-1', '--aviso-borde', 'oscuro')}</b> en oscuro, sobre un piso
      de 20. Cuando un color no llegó al piso se movió el color, no el piso: con el
      dato en bordeaux, el ámbar caía a 17,9 y la advertencia pasó a verde.</p>
    <p class="regla"><b>Cuatro ranuras categóricas siguen reservadas y sin validar.</b>
      Nunca se han dibujado juntas. Quien las estrene debe revalidarlas para el
      número de ranuras que vaya a usar, no para seis.</p>`,
}));

añadir('fundamentos/tipografia.html', ficha({
  grupo: 'Fundamentos', nombre: 'Tipografía', ancho: 820,
  subtitulo: 'Dos registros: lectura y cifra · pila del sistema, sin fuente web',
  intro: `Pila del sistema, no fuente web: el proyecto prohíbe cargar nada desde un CDN.
    La jerarquía se construye con peso, tamaño, interletrado y cifras tabulares.
    Hay <strong>dos registros</strong>: el de lectura, que sube despacio, y el de cifra,
    que salta — una plataforma de indicadores tiene que dejar que el número gane la página.`,
  cuerpo: `
    <div style="display:grid;gap:var(--e4)">
      <div><span class="cifra-display">${miles(kpi('P-01'))}</span>
        <div class="cifra-etq">--t-display · titular<span>tabular-nums · interletrado −0,042em</span></div></div>
      <div><div class="valor" style="font:700 var(--t-cifra)/1.04 var(--f-cifra);color:var(--cifra);letter-spacing:-.028em">${String(kpi('I-03')).replace('.', ',')}</div>
        <div class="cifra-etq">--t-cifra · valor de KPI<span>el sufijo va en &lt;small&gt;, no dentro del número</span></div></div>
      <h1 style="margin:0">Áreas temáticas</h1>
      <h2 style="margin:0">Publicaciones en el top 10 % de citación</h2>
      <p style="margin:0">Prosa a 16 px. El FWCI compara las citas recibidas con las
        esperadas para publicaciones del mismo campo, año y tipo.</p>
      <p class="nota" style="margin:0">Nota contextual a 12,5 px, en tinta secundaria.</p>
      <p><span class="codigo">I-05</span> <span class="etiqueta-en-linea">etiqueta en línea</span></p>
    </div>
    <p class="regla"><b>Las cifras tabulares se reservan.</b> Van en tablas, ejes,
      titular y tooltips, donde hay columnas que alinear. En una etiqueta suelta las
      proporcionales se leen mejor y forzar la tabulación sólo separa los dígitos.</p>`,
}));

añadir('fundamentos/espacio-trazo.html', ficha({
  grupo: 'Fundamentos', nombre: 'Espacio y trazo', ancho: 820,
  subtitulo: 'Escala de 4 px · radios contenidos · sombra mínima',
  intro: `Escala de espacio de 4 px, sin valores sueltos fuera de ella. Radios
    contenidos y sombra mínima: <strong>la separación entre superficies la hace el
    filete, no la elevación</strong>. Una interfaz analítica no flota.`,
  cuerpo: `
    <div style="display:grid;gap:var(--e2)">
      ${['e1', 'e2', 'e3', 'e4', 'e5', 'e6', 'e7', 'e8'].map((e) => `
        <div style="display:flex;align-items:center;gap:var(--e3)">
          <code style="font:600 var(--t-xs)/1 var(--f-mono);color:var(--tinta-3);width:3rem">--${e}</code>
          <div style="height:12px;width:var(--${e});background:var(--accion-viva);border-radius:2px"></div>
        </div>`).join('')}
    </div>
    <div style="display:flex;gap:var(--e4);margin-top:var(--e5);flex-wrap:wrap">
      <div style="width:110px;height:66px;background:var(--superficie);border:1px solid var(--linea);border-radius:var(--radio);box-shadow:var(--sombra-1);display:grid;place-items:center;font-size:var(--t-xs);color:var(--tinta-3)">sombra-1</div>
      <div style="width:110px;height:66px;background:var(--superficie);border:1px solid var(--linea);border-radius:var(--radio);box-shadow:var(--sombra-2);display:grid;place-items:center;font-size:var(--t-xs);color:var(--tinta-3)">sombra-2</div>
      <div style="width:110px;height:66px;background:var(--superficie);border:1px solid var(--linea);border-radius:var(--radio);box-shadow:var(--sombra-3);display:grid;place-items:center;font-size:var(--t-xs);color:var(--tinta-3)">sombra-3</div>
    </div>`,
}));

/* ───────────────────────────────────────────────────────── componentes */

añadir('componentes/kpi.html', ficha({
  grupo: 'Componentes', nombre: 'Tablero de cifras', ancho: 1000,
  subtitulo: 'Seis fichas · cada una con su propio denominador y su lectura',
  intro: `Una cifra sin su denominador y su fecha de corte está incompleta: la
    advertencia metodológica <strong>es parte del componente</strong>, no una nota al
    pie. Son las seis del tablero real, calculadas aquí sobre el corpus entero con
    <code>X.resumen()</code> — la misma función que las recalcula en el navegador a
    cada recorte. Cada una declara su base, porque son bases distintas
    (<code>D-16</code>) y presentarlas juntas sin decirlo invita a dividir una por
    otra.`,
  cuerpo: () => vx.cifras(X.resumen(publicaciones), textos),
}));

añadir('componentes/titular.html', ficha({
  grupo: 'Componentes', nombre: 'Cabecera de portada', ancho: 1000,
  subtitulo: 'Sin cifras: nombre, procedencia y el método tras un control',
  intro: `La cabecera <strong>no lleva cifras</strong>, y es una decisión medida: la
    anterior gastaba media pantalla en un titular de tres líneas y tres cifras que el
    tablero repetía justo debajo. En un explorador eso es ruido dos veces — gasta la
    pantalla que le toca al dato y enseña una cifra del total mientras el lector mira
    un recorte. Queda el nombre, la procedencia —que dice de dónde salen las cifras—
    y la explicación detrás de un control.`,
  cuerpo: () => vx.cabecera(meta),
}));

añadir('componentes/modulo.html', ficha({
  grupo: 'Componentes', nombre: 'Corte', ancho: 1000,
  subtitulo: 'La unidad de la sección: figura, tabla equivalente, lectura y sello',
  intro: `El <strong>corte</strong> sustituyó al módulo cuando el sitio dejó de servir
    series ya calculadas: responde al recorte, se deriva de las publicaciones y trae
    su conmutador. El orden no es decorativo: primero lo que condiciona la lectura,
    después la figura, después el sello que dice de dónde sale y sobre cuántos casos.
    El sello al final se convertía en letra pequeña. Es el componente real, no una
    reconstrucción: sale de <code>vx.corteUno()</code>, la misma función que dibuja
    cada corte del sitio. Se enseña con <code>P-07</code> porque es el que trae las
    tres cosas a la vez: trama de multivaluado, advertencia propia y un sello que
    advierte por cobertura.`,
  cuerpo: () => corte('P-07'),
}));

añadir('componentes/vistas.html', ficha({
  grupo: 'Componentes', nombre: 'Conmutador Gráfico ⇄ Tabla', ancho: 1000,
  subtitulo: 'Dos representaciones de la misma serie · la tabla no es un extra',
  intro: `Patrón tomado de los portales del oficio: el Leiden Ranking presenta la misma
    tabla como lista, dispersión o mapa y deja elegir. Aquí las dos vistas son la figura
    y la tabla. <strong>Sin JavaScript se muestran las dos</strong> — la tabla es la vía
    equivalente al gráfico— y el control desaparece, porque un conmutador que no conmuta
    nada es una promesa falsa. Cuando el indicador trae valor esperado, la tabla gana
    las columnas que convierten un recuento en un juicio.

    Las dos vistas están <b>las dos en el DOM</b>, y lo que decide cuál se ve es
    <code>data-activa</code>. Por eso sin JavaScript se leen ambas: no hay nada que
    revelar, sólo un control que no llega a esconder la segunda.`,
  cuerpo: () => corte('I-05'),
}));

añadir('componentes/sello.html', ficha({
  grupo: 'Componentes', nombre: 'Sello de procedencia', ancho: 900,
  subtitulo: 'Fuente, fecha, N y cobertura · con sus variantes de export y de advertencia',
  intro: `Responde, sin que haya que buscarlo, a las cuatro preguntas que deciden si una
    cifra puede citarse. <strong>El N no es global</strong> —${miles(series['P-02'].procedencia.n)}
    en producción, ${miles(series['I-05'].procedencia.n)} en impacto,
    ${miles(series['P-07'].procedencia.n)} ${series['P-07'].procedencia.unidad} en P-07— y
    por eso viaja pegado al gráfico y no en el pie de la página. Esas tres cifras se leen
    de <code style="display:inline">series.json</code> al generar esta ficha: escritas a
    mano sobrevivían a la carga que las volvía falsas, que es justo lo que el sello
    existe para impedir. Por debajo del umbral de cobertura declarado en configuración,
    el sello cambia de registro y pasa a advertir. Lo decide el dato. La fecha es la que
    declara la fuente: el export de Scopus no declara corte, y el sello de
    <code style="display:inline">P-02</code>, el tercero, rotula la de su export.`,
  cuerpo: [c.sello(series['I-05'].procedencia), c.sello(series['T-04'].procedencia),
    c.sello(series['P-02'].procedencia)].join(''),
}));

añadir('componentes/notas.html', ficha({
  grupo: 'Componentes', nombre: 'Notas y advertencias', ancho: 900,
  subtitulo: 'Dos niveles por diseño · marcar todo igual equivale a no marcar nada',
  intro: `La advertencia destacada lleva fondo, filete e icono; la nota contextual es
    texto recesivo. Son <strong>dos niveles distintos a propósito</strong>. También hay
    advertencias que describen cómo se <em>lee el gráfico</em>, no cómo se calcula el
    indicador, y que sólo existen mientras el gráfico sea ése.`,
  cuerpo: `
    ${c.nota({ destacada: true, texto: series['T-04'].nota?.texto || 'Advertencia metodológica de ejemplo.' })}
    <div class="nota-destacada"><b>Cómo se lee este gráfico</b>
      Las barras cuentan las citas recibidas por las publicaciones de cada año, no la
      actividad citadora de ese año. <strong>La caída del último año no indica menor
      impacto.</strong></div>
    <p class="nota">Nota contextual: se muestran las 20 fuentes con más publicaciones,
      de 431 distintas.</p>
    <p class="leyenda-trama">Barras rayadas: no son partes de un total y no suman.</p>`,
}));

añadir('componentes/rail.html', ficha({
  grupo: 'Componentes', nombre: 'Índice lateral', ancho: 560,
  subtitulo: 'Scroll-spy · colapsa a pastillas bajo 1040 px',
  intro: `Tomado del panel de entidades que SciVal mantiene fijo a la izquierda. En una
    página de cinco indicadores largos, saber qué hay y poder saltar sin recorrerla
    entera es la diferencia entre consultar y resignarse a leer en orden. Sin JavaScript
    sigue siendo una lista de anclas útil.`,
  cuerpo: () => vx.indice('impacto'),
}));

añadir('componentes/controles.html', ficha({
  grupo: 'Componentes', nombre: 'Controles', ancho: 900,
  subtitulo: 'Botones, pastillas de filtro, chips, conmutador de tema',
  intro: `El botón primario <strong>no puede llevar tinta blanca fija</strong>: el mismo
    token de fondo es azul medio en tema claro y <em>azul claro</em> en oscuro,
    donde el blanco caería a <b>${ratio('#ffffff', TOKENS['--boton'].oscuro)}:1</b>. Con
    <code style="display:inline">--boton-tinta</code>, que cambia con el tema igual que su
    fondo, mide <b>${cr('--boton-tinta', '--boton', 'claro')}:1</b> en claro y
    <b>${cr('--boton-tinta', '--boton', 'oscuro')}:1</b> en oscuro.`,
  cuerpo: `
    <div style="display:flex;gap:var(--e3);flex-wrap:wrap;align-items:center">
      <button class="boton">Limpiar filtros</button>
      <button class="boton boton-primario">Exportar CSV</button>
      <button class="boton" disabled>Deshabilitado</button>
      <button class="ayuda" type="button" aria-label="Ayuda">?</button>
    </div>
    <div class="chips" style="margin-top:var(--e4)">
      <span class="chip">2024 <button aria-label="Quitar filtro">×</button></span>
      <span class="chip">Internacional <button aria-label="Quitar filtro">×</button></span>
    </div>
    <div class="grupo-filtro" style="margin-top:var(--e4)">
      <span class="etiqueta">Tipo documental</span>
      <div class="opciones">
        <label class="opcion"><input type="checkbox" checked> Article <span class="n">595</span></label>
        <label class="opcion"><input type="checkbox"> Review <span class="n">133</span></label>
        <label class="opcion desactivada"><input type="checkbox" disabled> Chapter <span class="n">0</span></label>
      </div>
    </div>
    <p class="regla"><b>Una faceta en 0 se deshabilita, no se oculta.</b> Su ausencia
      es información: esconderla haría creer que la categoría no existe.</p>`,
}));

añadir('componentes/estados.html', ficha({
  grupo: 'Componentes', nombre: 'Estados', ancho: 900,
  subtitulo: 'Vacío, error y ausencia de dato',
  intro: `<strong>Ausencia de dato y cero nunca se ven igual.</strong> «Sin dato
    declarado» es una afirmación distinta de «0», y confundirlas es el error que este
    proyecto persigue.`,
  cuerpo: `
    <div class="vacio"><p>Ningún resultado con estos filtros.</p>
      <button class="boton">Limpiar filtros</button></div>
    <div class="error" style="margin-top:var(--e4)"><p><strong>No se pudieron cargar los datos.</strong></p>
      <p>No se pudo cargar series.json (404)</p>
      <button class="boton">Reintentar</button></div>
    <div class="tabla-envoltura" style="margin-top:var(--e4)"><table>
      <thead><tr><th>Categoría</th><th class="num">n</th></tr></thead>
      <tbody>
        <tr><td>Facultad de Medicina</td><td class="num">356</td></tr>
        <tr><td class="sin-dato-txt">No determinada</td><td class="num">287</td></tr>
        <tr><td>Sin métricas</td><td class="num"><span class="sin-dato-txt">Sin dato declarado</span></td></tr>
      </tbody></table></div>`,
}));

añadir('componentes/bandas.html', ficha({
  grupo: 'Componentes', nombre: 'Banda', ancho: 1100,
  subtitulo: 'La unidad de composición de la portada, las secciones y metodología',
  intro: `Una banda sostiene UNA afirmación y va a sangre. Los suelos alternan para que
    dos bandas seguidas no se lean como una sola. <strong>No manda en todas partes</strong>:
    publicaciones, autores, la ficha y el catálogo son superficies de consulta con filtro
    y paginación —quien llega ahí viene a buscar, no a que le cuenten— y convertirlas en
    narrativa habría arreglado la estética rompiendo la función.`,
  cuerpo: () => `
    <p class="panel-etq" style="margin-top:0">Los cuatro suelos</p>
    <div class="banda banda-papel"><div style="padding:var(--e4)">
      <p class="banda-gancho">papel</p>
      <p style="margin:0">El suelo por defecto: el canvas de Stitch.</p></div></div>
    <div class="banda banda-papel-2"><div style="padding:var(--e4)">
      <p class="banda-gancho">papel-2</p>
      <p style="margin:0">El segundo suelo. Admite figuras, incluida la marca de
      ausencia, que es el piso que fija cuánto puede oscurecerse.</p></div></div>
    <div class="banda banda-contraste"><div style="padding:var(--e4)">
      <p class="banda-gancho">contraste</p>
      <p style="margin:0">Para lo que el informe NO puede afirmar: indicadores diferidos
      y advertencias metodológicas. Redefine sus tokens en su propio ámbito.</p></div></div>
    <div class="banda banda-enfasis"><div style="padding:var(--e4)">
      <p class="banda-gancho">énfasis</p>
      <p style="margin:0">El cierre. SÓLO titular y prosa.</p></div></div>

    <p class="regla" style="margin-top:var(--e5)">La banda de contraste <b>redefine los
      tokens en su ámbito</b> en vez de tener una segunda hoja de estilo para «lo que va
      sobre fondo oscuro». Módulos, gráficos, sellos y tablas que caen dentro se adaptan
      solos, sin que ninguno sepa que está sobre otro suelo. Al medirla como ámbito propio
      aparecieron cuatro tokens que no redefinía —la rampa ordinal y la tinta del botón—:
      como la banda es oscura en los DOS temas, en claro conservaban su valor claro y
      caían sobre suelo oscuro, con --ord-1 en 1,06:1.</p>

    <p class="regla">La banda de énfasis <b>no lleva figuras</b>: es el cierre, sólo
      tipografía y enlaces. La regla nació de una medida —con la paleta vino, la marca de
      ausencia caía bajo el piso de 3 sobre ese suelo— y se conserva como regla de
      composición. Hoy, sobre el azul claro del cierre, el dato mide
      <b>${sobreBanda('--serie-1', BANDA_ENFASIS, 'claro')}:1</b> y
      <code style="display:inline">--sin-dato</code>
      <b>${sobreBanda('--sin-dato', BANDA_ENFASIS, 'claro')}:1</b>: si una figura
      llegara ahí, habría que medirla antes, no suponer que cumple.</p>

    <p class="regla">El segundo papel <b>no puede oscurecerse más</b>, y el techo lo fija
      una medida, no el gusto: tiene que sostener la marca de ausencia con el dato
      azul marino encima. Hoy <code style="display:inline">--sin-dato</code> mide
      <b>${cr('--sin-dato', '--banda-papel-2', 'claro')}:1</b> sobre él, contra
      <b>${cr('--sin-dato', '--plano', 'claro')}:1</b> sobre el primer papel: un paso más
      de oscuridad y la ausencia se acerca al piso de 3.</p>

    <p class="regla">Los dos suelos de banda se separan poco por definición —son papel
      contra papel—: ΔE <b>${sep('--plano', '--banda-papel-2', 'claro')}</b> en claro y
      <b>${sep('--plano', '--banda-papel-2', 'oscuro')}</b> en oscuro, con un borde de
      <b>${cr('--plano', '--banda-papel-2', 'claro')}:1</b>. Es real pero no sostiene solo
      un corte de sección, así que en tema claro las bandas llevan una costura de 1px. En
      oscuro la separación es algo mayor y la costura se apaga.</p>`,
}));

/* ─────────────────────────────────────────────────────────── gráficos */

añadir('graficos/barras-horizontales.html', ficha({
  grupo: 'Gráficos', nombre: 'Barras horizontales', ancho: 1000,
  subtitulo: 'Etiquetas largas o muchas categorías · con trama y valor esperado',
  intro: `Se eligen cuando las etiquetas son largas o son muchas. La identidad no la
    lleva una leyenda sino la etiqueta de la propia barra y su valor visible al lado:
    <strong>el color nunca es el único canal</strong>. La columna de etiquetas se
    dimensiona con el contenido real y se acota a un tercio del lienzo.`,
  cuerpo: () => figura('P-03') + figura('T-05'),
}));

añadir('graficos/barras-verticales.html', ficha({
  grupo: 'Gráficos', nombre: 'Barras verticales', ancho: 1000,
  subtitulo: 'Series anuales cortas · rejilla recesiva y línea de referencia',
  intro: `Para series anuales cortas: tres años no son una línea. El lienzo
    <strong>se ajusta al número de categorías</strong> — tres barras estiradas a lo
    ancho de una tarjeta se leen como «poco dato», que es una impresión y no una
    medición. Un gráfico de citas por año de publicación induce a leer «el impacto
    está cayendo»: lo que cae es el tiempo disponible para acumular citas, y por eso
    el módulo lleva esa advertencia pegada.`,
  cuerpo: () => figura('I-01') + figura('P-02'),
}));

añadir('graficos/red.html', ficha({
  grupo: 'Gráficos', nombre: 'Red de coautoría', ancho: 1000,
  subtitulo: 'La única figura que no es una serie · comunidades declaradas como heurística',
  intro: `La única figura del sitio cuya unidad no es una categoría con un recuento,
    sino un par: quién firma con quién. Las comunidades se calculan con Louvain y se
    <strong>declaran como heurística</strong>, no como estructura real de equipos —
    un algoritmo de partición siempre devuelve particiones, incluso donde no las hay.
    En pantalla el lector elige entre nodos, matriz, arcos y la tabla de pares; en
    papel se imprime sólo la vista de nodos, porque la tabla convertía la sección en
    49 hojas.

    <b>Esta ficha sustituyó a la del «Anillo»</b>, que documentaba un componente
    inexistente: no hay ningún gráfico de anillo en el código —<code>proporcional()</code>
    dibuja una barra apilada— y <code>C-01</code> se dibuja hoy como barras
    horizontales de una sola serie.`,
  cuerpo: () => corte('C-05'),
}));

/* Cuatro formas que antes eran barrasH. La forma la elige la RELACIÓN que
   expresa el dato, contrastada contra el Visual Vocabulary del Financial
   Times; no la costumbre de la casa. */

añadir('graficos/desviacion.html', ficha({
  grupo: 'Gráficos', nombre: 'Desviación', ancho: 1000,
  subtitulo: 'Un valor que se lee CONTRA una referencia, no en magnitud absoluta',
  intro: `El FWCI no se lee por su tamaño sino por su distancia al 1,00 mundial. Con
    barras desde cero, esa distancia había que calcularla de cabeza. Aquí el
    <strong>1,00 es el eje</strong> y la desviación se ve sin aritmética.
    La dirección la lleva sólo la POSICIÓN respecto del eje: pintar el déficit de otro
    color habría gastado color en algo que la posición ya dice, y el gris del sitio
    significa ausencia de dato, no valor bajo.`,
  cuerpo: () => figura('I-04'),
}));

añadir('graficos/acumulada.html', ficha({
  grupo: 'Gráficos', nombre: 'Acumulada', ancho: 1000,
  subtitulo: 'Umbrales ANIDADOS, que no se suman',
  intro: `Los umbrales de percentil se contienen unos a otros: las publicaciones del
    top 1 % están también en el top 5, el 10 y el 25. Dibujarlos como cuatro barras
    hermanas sugería cuatro grupos disjuntos que se podían sumar —322, una cifra sin
    significado—. <strong>Era un problema de correctitud, no de estética.</strong>
    La forma anidada hace visible la contención y vuelve imposible la suma.`,
  cuerpo: () => figura('I-05'),
}));

añadir('graficos/distribucion.html', ficha({
  grupo: 'Gráficos', nombre: 'Distribución', ancho: 1000,
  subtitulo: 'Un continuo tramificado · el eje es la información',
  intro: `El número de autores por publicación es un continuo partido en tramos.
    Ordenarlo por frecuencia, como haría un ranking, <strong>destruye el eje</strong>,
    que es justo lo que hay que leer. La media y la mediana van juntas al pie porque
    la distribución es asimétrica y la media sola describe mal el caso típico.`,
  cuerpo: () => figura('C-06'),
}));

añadir('graficos/proporcional.html', ficha({
  grupo: 'Gráficos', nombre: 'Proporcional', ancho: 1000,
  subtitulo: 'Partes de un total conocido · rampa ordinal, no escala categórica',
  intro: `Los cuartiles reparten un total conocido, así que se dibujan repartiendo una
    barra y no como cuatro barras sueltas que obliguen a sumar de cabeza. Q1–Q4 es una
    escala <strong>ordenada</strong>: un solo tono en cuatro pasos, del más oscuro al
    más claro, con luminosidad monótona y ΔE mínimo de 11,4 entre escalones.`,
  cuerpo: () => figura('R-01'),
}));

añadir('graficos/codificacion.html', ficha({
  grupo: 'Gráficos', nombre: 'Codificación por naturaleza del dato', ancho: 1000,
  subtitulo: 'Trama de multivaluado, marca de esperado, gris de ausencia',
  intro: `Tres cosas que antes sólo existían en prosa y ahora tienen forma. Cada una se
    enseña con <strong>el indicador que de verdad la usa</strong>: una ficha de sistema de
    diseño que ilustra una regla con un ejemplo que no la cumple es peor que no tenerla.`,
  cuerpo: () => `
    <p class="panel-etq" style="margin-top:0">Trama diagonal · T-05, multivaluado</p>
    ${figura('T-05')}
    <p class="leyenda-trama">Barras rayadas: no son partes de un total y no suman.</p>
    <p class="regla">Las líneas van en el color de la superficie y <b>cortan</b> el
      relleno en vez de teñirlo. Por eso el rayado se lee igual en los dos temas, con
      cualquier daltonismo y sobre papel en blanco y negro.</p>

    <p class="panel-etq" style="margin-top:var(--e5)">Marca del valor esperado · I-05</p>
    ${figura('I-05')}
    <p class="regla">Un recuento sin escala no dice si es mucho o poco. El trazo verde de
      referencia marca lo que cabría esperar bajo el promedio mundial: por definición, el top
      <i>k</i> % de la distribución mundial contiene el <i>k</i> % de las publicaciones.
      Se lee de un vistazo que la institución queda <b>por debajo en el 1 %, el 5 % y el
      10 %, y por encima en el 25 %</b>.</p>

    <p class="panel-etq" style="margin-top:var(--e5)">Gris de ausencia · P-07</p>
    ${figura('P-07')}
    <p class="regla"><b>«No determinada» siempre es gris</b>, ignorando la escala pedida.
      Un valor no medido no puede parecerse a uno medido. Nótese que P-07
      <b>no</b> lleva trama: no es multivaluado, y ponérsela para que la ficha quedara
      más completa habría sido afirmar algo falso sobre el indicador.</p>`,
}));

/* ──────────────────────────────────────────────────────────── escritura */

const LEEME = `# Sistema de diseño — Informe Bibliométrico Institucional

**Generado**, no escrito a mano. Se reconstruye con \`make kit\`.

Cada ficha se construye a partir de las fuentes reales del proyecto:

- \`web/assets/css/app.css\`, incrustada entera en cada ficha, de modo que la
  previsualización usa exactamente los estilos que se sirven;
- los constructores de \`web/assets/js/core.js\` y \`web/assets/js/vista.js\`,
  ejecutados bajo Node — los mismos que usa el pre-renderizador del sitio;
- los artefactos de \`data/processed/\`. **Los componentes se enseñan con datos
  reales**: un componente de bibliometría ilustrado con cifras inventadas
  contradice las reglas del proyecto incluso en una ficha de diseño;
- las razones de contraste, **calculadas al generar** a partir de los tokens
  leídos de la hoja. No se copian de ninguna tabla.

Por eso el sistema de diseño no puede desactualizarse respecto del producto:
si divergen, es que no se ha vuelto a generar.

## Advertencia sobre la identidad

El rojo **no es el color institucional oficial de la Universidad Finis Terrae**.
No se pudo verificar y no se inventó. Está diseñado por medición. Cuando exista
el valor oficial se sustituyen cuatro tokens —\`--marca\`, \`--marca-honda\`,
\`--marca-alta\`, \`--marca-tinta\`— y se vuelve a correr el barrido de contraste.

## Fichas

| Grupo | Ficha |
|---|---|
${CARDS.map((c) => {
  const m = c.contenido.match(/group="([^"]+)" name="([^"]+)"/);
  return `| ${m[1]} | \`${c.ruta}\` — ${m[2]} |`;
}).join('\n')}

## Sincronizar con Claude Design

Este directorio es el paquete listo para empujar. Requiere autorización de
sistema de diseño, que **no se puede conceder desde una sesión remota sin
terminal interactiva**. Dos vías:

1. Desde Claude Design, «Send to Claude Code Web», que siembra el proyecto en el
   espacio de trabajo.
2. Claude Code en una máquina local, donde \`/design-login\` sí abre.

Hecho eso, la sincronización es incremental —componente a componente— y nunca
un reemplazo completo.
`;

await rm(SALIDA, { recursive: true, force: true });
for (const { ruta, contenido } of CARDS) {
  const destino = join(SALIDA, ruta);
  await mkdir(dirname(destino), { recursive: true });
  await writeFile(destino, contenido, 'utf8');
}
await writeFile(join(SALIDA, 'README.md'), LEEME, 'utf8');
// Las fichas copian app.css entera, y sus @font-face apuntan a ../fonts/: sin
// esta copia el kit se pintaba con la fuente del sistema y no enseñaba ni
// Inter, ni JetBrains Mono, ni Newsreader (D-678).
await cp(join(RAIZ, 'web/assets/fonts'), join(SALIDA, 'fonts'), { recursive: true });

console.log(`\n  Paquete de sistema de diseño en ${SALIDA.replace(RAIZ + '/', '')}/\n`);
let grupoActual = '';
for (const { ruta, contenido } of CARDS) {
  const m = contenido.match(/group="([^"]+)" name="([^"]+)"/);
  if (m[1] !== grupoActual) { grupoActual = m[1]; console.log(`  ${grupoActual}`); }
  const kb = (Buffer.byteLength(contenido, 'utf8') / 1024).toFixed(0);
  console.log(`    ${ruta.padEnd(42)} ${String(kb).padStart(4)} KB   ${m[2]}`);
}
console.log(`\n  ${CARDS.length} fichas · ${Object.keys(TOKENS).length} tokens leídos de la hoja`);
