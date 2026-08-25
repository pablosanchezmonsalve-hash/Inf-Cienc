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

import { readFile, writeFile, mkdir, rm } from 'node:fs/promises';
import { join, resolve, dirname } from 'node:path';
import { pathToFileURL } from 'node:url';

const RAIZ = resolve(dirname(new URL(import.meta.url).pathname), '../..');
const SALIDA = resolve(process.argv[2] || join(RAIZ, 'design-system'));
const DATOS = join(RAIZ, 'data', 'processed');

const css = await readFile(join(RAIZ, 'web/assets/css/app.css'), 'utf8');
const mod = (n) => import(pathToFileURL(join(RAIZ, 'web/assets/js', n)).href);
const c = await mod('core.js');
const v = await mod('vista.js');
const dato = async (n) => JSON.parse(await readFile(join(DATOS, n), 'utf8'));

const meta = await dato('meta.json');
const series = await dato('series.json');
const { kpis } = await dato('kpis.json');

/* ─────────────────────────────────────────────── medición de contraste */
const lin = (x) => (x /= 255, x <= 0.04045 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4);
const rgb = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
const lum = (h) => { const [r, g, b] = rgb(h).map(lin); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
const ct = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
const ratio = (a, b) => ct(a, b).toFixed(2).replace('.', ',');

/* Lee los tokens de la hoja: `--x: light-dark(#aaa, #bbb);`. La ficha de color
   se dibuja con estos valores, así que cambiar la hoja cambia la ficha. */
const TOKENS = {};
for (const m of css.matchAll(/(--[a-z0-9-]+):\s*light-dark\(\s*(#[0-9a-f]{6})\s*,\s*(#[0-9a-f]{6})\s*\)/gi)) {
  TOKENS[m[1]] = { claro: m[2].toLowerCase(), oscuro: m[3].toLowerCase() };
}

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
    <p class="panel-etq" style="margin-top:var(--e5)">Advertencia metodológica · ámbar, fuera de la familia del dato</p>
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
    <p class="regla"><b>Separación dato ↔ advertencia.</b> El dato es rojo y la
      advertencia ámbar. Medido en OKLab: ΔE 28,6 en claro y 21,2 en oscuro, sobre
      un piso de 20. Es la razón por la que el ámbar no se movió al cambiar el rojo.</p>
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
      <div><span class="cifra-display">823</span>
        <div class="cifra-etq">--t-display · titular<span>tabular-nums · interletrado −0,042em</span></div></div>
      <div><div class="valor" style="font:700 var(--t-cifra)/1.04 var(--f-cifra);color:var(--cifra);letter-spacing:-.028em">0,87</div>
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
  grupo: 'Componentes', nombre: 'Tarjeta de indicador (KPI)', ancho: 1000,
  subtitulo: 'Cifra, denominador, unidad y advertencia · datos reales',
  intro: `Un KPI sin su denominador y su fecha de corte está incompleto: la advertencia
    metodológica <strong>es parte del componente</strong>, no una nota al pie. Estas
    tarjetas se dibujan con los indicadores reales del informe.`,
  cuerpo: `<div class="kpis" data-n="3">${v.kpis(v.kpisRestantes(kpis))}</div>
    <p class="regla"><b>Los porcentajes llevan un decimal; los enteros, ninguno.</b>
      Dos decimales en un porcentaje sugieren una precisión que el dato no tiene.
      La unidad del valor va bajo la etiqueta, nunca intercalada en el número.</p>`,
}));

añadir('componentes/titular.html', ficha({
  grupo: 'Componentes', nombre: 'Titular de portada', ancho: 1000,
  subtitulo: 'Tres cifras a tamaño display, con denominador y referencia',
  intro: `Abrir con la magnitud, no con el índice. Son <strong>tres y no seis</strong>:
    un titular con seis cifras no tiene titular. Cada una arrastra su denominador y,
    si la tiene, su referencia — un 0,87 de FWCI sin el «1 = promedio mundial» al lado
    no es un titular, es un número suelto.`,
  cuerpo: v.hero(meta, kpis),
}));

añadir('componentes/modulo.html', ficha({
  grupo: 'Componentes', nombre: 'Módulo de indicador', ancho: 1000,
  subtitulo: 'Cabecera, conmutador de vista, figura, sello y notas',
  intro: `El orden no es decorativo: primero lo que condiciona la lectura —advertencia
    metodológica y nota de lectura del gráfico—, después la figura, después el sello
    que dice de dónde sale y sobre cuántos casos, y al final el detalle. El sello al
    final se convertía en letra pequeña.`,
  cuerpo: () => v.modulo('I-05', series['I-05']),
}));

añadir('componentes/vistas.html', ficha({
  grupo: 'Componentes', nombre: 'Conmutador Gráfico ⇄ Tabla', ancho: 1000,
  subtitulo: 'Dos representaciones de la misma serie · la tabla no es un extra',
  intro: `Patrón tomado de los portales del oficio: el Leiden Ranking presenta la misma
    tabla como lista, dispersión o mapa y deja elegir. Aquí las dos vistas son la figura
    y la tabla. <strong>Sin JavaScript se muestran las dos</strong> — la tabla es la vía
    equivalente al gráfico— y el control desaparece, porque un conmutador que no conmuta
    nada es una promesa falsa. Cuando el indicador trae valor esperado, la tabla gana
    las columnas que convierten un recuento en un juicio.`,
  cuerpo: `<div class="modulo">
      <header>
        <div class="modulo-id"><h2>${c.escapar(series['I-05'].nombre)}</h2><span class="codigo">I-05</span></div>
        <div class="vistas" role="group" aria-label="Forma de presentación">
          <button type="button" data-vista="grafico" aria-pressed="false">Gráfico</button>
          <button type="button" data-vista="tabla" aria-pressed="true">Tabla</button>
        </div>
      </header>
      ${c.tablaEquivalente(series['I-05'].datos)}
    </div>`,
}));

añadir('componentes/sello.html', ficha({
  grupo: 'Componentes', nombre: 'Sello de procedencia', ancho: 900,
  subtitulo: 'Fuente, corte, N y cobertura · con su variante de advertencia',
  intro: `Responde, sin que haya que buscarlo, a las cuatro preguntas que deciden si una
    cifra puede citarse. <strong>El N no es global</strong> —823 en producción, 816 en
    impacto, 1.207 pares autor × publicación en P-07— y por eso viaja pegado al gráfico
    y no en el pie de la página. Por debajo del umbral de cobertura declarado en
    configuración, el sello cambia de registro y pasa a advertir. Lo decide el dato.`,
  cuerpo: [c.sello(series['I-05'].procedencia), c.sello(series['T-04'].procedencia)].join(''),
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
  cuerpo: v.rail(['I-01', 'I-04', 'I-05', 'R-01', 'A-01'].filter((k) => series[k]), series)
    .replace('<li><a href="#I-04"', '<li><a class="activo" href="#I-04"'),
}));

añadir('componentes/controles.html', ficha({
  grupo: 'Componentes', nombre: 'Controles', ancho: 900,
  subtitulo: 'Botones, pastillas de filtro, chips, conmutador de tema',
  intro: `El botón primario <strong>no puede llevar tinta blanca fija</strong>: el mismo
    token de fondo es un rojo hondo en tema claro y un rosa en oscuro, donde el blanco
    caería a 2,84:1. La tinta del botón es un token que cambia con el tema, igual que
    su fondo.`,
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
      <p style="margin:0">El suelo por defecto. Papel teñido con Peach al 6–10 %.</p></div></div>
    <div class="banda banda-papel-2"><div style="padding:var(--e4)">
      <p class="banda-gancho">papel-2</p>
      <p style="margin:0">El segundo suelo, FRÍO. Admite figuras, incluida la marca de
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

    <p class="regla">La banda de énfasis <b>no lleva figuras</b>. Medido: sobre Peach Glow
      el color del dato cae a 3,21:1 y la marca de ausencia a 2,35:1. Por eso el cierre es
      sólo tipografía y enlaces, y la regla queda escrita junto al componente.</p>

    <p class="regla">El segundo papel es frío y no un peach más oscuro por la misma razón:
      oscurecer el papel hacia el peach rompe la marca de ausencia —cae bajo 3:1 pasado
      #dbe3df— y lo acercaba al cierre. #e1e7e4 es el límite útil, con la ausencia en
      3,10:1. Su borde contra el papel mide 1,10:1, que es real pero no sostiene solo un
      corte de sección, así que en tema claro las bandas de papel llevan una costura de
      1px; en oscuro los dos suelos ya se separan ΔE 11,75 y la costura sobra.</p>`,
}));

/* ─────────────────────────────────────────────────────────── gráficos */

añadir('graficos/barras-horizontales.html', ficha({
  grupo: 'Gráficos', nombre: 'Barras horizontales', ancho: 1000,
  subtitulo: 'Etiquetas largas o muchas categorías · con trama y valor esperado',
  intro: `Se eligen cuando las etiquetas son largas o son muchas. La identidad no la
    lleva una leyenda sino la etiqueta de la propia barra y su valor visible al lado:
    <strong>el color nunca es el único canal</strong>. La columna de etiquetas se
    dimensiona con el contenido real y se acota a un tercio del lienzo.`,
  cuerpo: () => v.RENDER['P-03'](series['P-03']) + v.RENDER['T-05'](series['T-05']),
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
  cuerpo: () => v.RENDER['I-01'](series['I-01']) + v.RENDER['P-02'](series['P-02']),
}));

añadir('graficos/anillo.html', ficha({
  grupo: 'Gráficos', nombre: 'Anillo', ancho: 700,
  subtitulo: 'Reservado a proporciones binarias · el único que lleva leyenda',
  intro: `Reservado a proporciones binarias, que es donde se lee bien. Es el único
    gráfico con leyenda, porque sus segmentos no admiten etiqueta interior — y el único
    que gasta la escala categórica: usa las dos primeras ranuras, medidas como par
    incluso bajo deuteranopía (ΔE 12,2, sobre un piso de 8).`,
  cuerpo: () => v.RENDER['C-01'](series['C-01']),
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
  cuerpo: () => v.RENDER['I-04'](series['I-04']),
}));

añadir('graficos/acumulada.html', ficha({
  grupo: 'Gráficos', nombre: 'Acumulada', ancho: 1000,
  subtitulo: 'Umbrales ANIDADOS, que no se suman',
  intro: `Los umbrales de percentil se contienen unos a otros: las publicaciones del
    top 1 % están también en el top 5, el 10 y el 25. Dibujarlos como cuatro barras
    hermanas sugería cuatro grupos disjuntos que se podían sumar —322, una cifra sin
    significado—. <strong>Era un problema de correctitud, no de estética.</strong>
    La forma anidada hace visible la contención y vuelve imposible la suma.`,
  cuerpo: () => v.RENDER['I-05'](series['I-05']),
}));

añadir('graficos/distribucion.html', ficha({
  grupo: 'Gráficos', nombre: 'Distribución', ancho: 1000,
  subtitulo: 'Un continuo tramificado · el eje es la información',
  intro: `El número de autores por publicación es un continuo partido en tramos.
    Ordenarlo por frecuencia, como haría un ranking, <strong>destruye el eje</strong>,
    que es justo lo que hay que leer. La media y la mediana van juntas al pie porque
    la distribución es asimétrica y la media sola describe mal el caso típico.`,
  cuerpo: () => v.RENDER['C-06'](series['C-06']),
}));

añadir('graficos/proporcional.html', ficha({
  grupo: 'Gráficos', nombre: 'Proporcional', ancho: 1000,
  subtitulo: 'Partes de un total conocido · rampa ordinal, no escala categórica',
  intro: `Los cuartiles reparten un total conocido, así que se dibujan repartiendo una
    barra y no como cuatro barras sueltas que obliguen a sumar de cabeza. Q1–Q4 es una
    escala <strong>ordenada</strong>: un solo tono en cuatro pasos, del más oscuro al
    más claro, con luminosidad monótona y ΔE mínimo de 11,4 entre escalones.`,
  cuerpo: () => v.RENDER['R-01'](series['R-01']),
}));

añadir('graficos/codificacion.html', ficha({
  grupo: 'Gráficos', nombre: 'Codificación por naturaleza del dato', ancho: 1000,
  subtitulo: 'Trama de multivaluado, marca de esperado, gris de ausencia',
  intro: `Tres cosas que antes sólo existían en prosa y ahora tienen forma. Cada una se
    enseña con <strong>el indicador que de verdad la usa</strong>: una ficha de sistema de
    diseño que ilustra una regla con un ejemplo que no la cumple es peor que no tenerla.`,
  cuerpo: () => `
    <p class="panel-etq" style="margin-top:0">Trama diagonal · T-05, multivaluado</p>
    ${v.RENDER['T-05'](series['T-05'])}
    <p class="leyenda-trama">Barras rayadas: no son partes de un total y no suman.</p>
    <p class="regla">Las líneas van en el color de la superficie y <b>cortan</b> el
      relleno en vez de teñirlo. Por eso el rayado se lee igual en los dos temas, con
      cualquier daltonismo y sobre papel en blanco y negro.</p>

    <p class="panel-etq" style="margin-top:var(--e5)">Marca del valor esperado · I-05</p>
    ${v.RENDER['I-05'](series['I-05'])}
    <p class="regla">Un recuento sin escala no dice si es mucho o poco. El trazo ámbar
      marca lo que cabría esperar bajo el promedio mundial: por definición, el top
      <i>k</i> % de la distribución mundial contiene el <i>k</i> % de las publicaciones.
      Se lee de un vistazo que la institución queda <b>por debajo en el 1 %, el 5 % y el
      10 %, y por encima en el 25 %</b>.</p>

    <p class="panel-etq" style="margin-top:var(--e5)">Gris de ausencia · P-07</p>
    ${v.RENDER['P-07'](series['P-07'])}
    <p class="regla"><b>«No determinada» siempre es gris</b>, ignorando la escala pedida.
      Un valor no medido no puede parecerse a uno medido. Nótese que P-07
      <b>no</b> lleva trama: no es multivaluado, y ponérsela para que la ficha quedara
      más completa habría sido afirmar algo falso sobre el indicador.</p>`,
}));

/* ──────────────────────────────────────────────────────────── escritura */

const LEEME = `# Sistema de diseño — Informe Cienciométrico Institucional

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

console.log(`\n  Paquete de sistema de diseño en ${SALIDA.replace(RAIZ + '/', '')}/\n`);
let grupoActual = '';
for (const { ruta, contenido } of CARDS) {
  const m = contenido.match(/group="([^"]+)" name="([^"]+)"/);
  if (m[1] !== grupoActual) { grupoActual = m[1]; console.log(`  ${grupoActual}`); }
  const kb = (Buffer.byteLength(contenido, 'utf8') / 1024).toFixed(0);
  console.log(`    ${ruta.padEnd(42)} ${String(kb).padStart(4)} KB   ${m[2]}`);
}
console.log(`\n  ${CARDS.length} fichas · ${Object.keys(TOKENS).length} tokens leídos de la hoja`);
