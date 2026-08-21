/* explorador.js — recálculo de indicadores en el navegador.

   QUÉ CAMBIA RESPECTO DEL SITIO ANTERIOR
     Antes el sitio servía indicadores YA CALCULADOS: el build dejaba
     `series.json` con las cifras del conjunto completo y la página las
     pintaba. Eso hacía un informe, no una plataforma: el lector veía las
     cifras que alguien decidió por él y no podía preguntar nada más.

     Aquí los indicadores se derivan de `publications.json` en el navegador,
     sobre el subconjunto que el lector elige. «Publicaciones de la Facultad de
     Medicina de 2024 con colaboración internacional» no es una vista
     preparada: es una pregunta que se responde al momento porque el dato de
     cada publicación viaja entero.

   POR QUÉ NO ROMPE LA GARANTÍA DE «SIN JAVASCRIPT»
     El HTML llega pre-renderizado con los valores del conjunto COMPLETO, que
     son los del informe. Este módulo no escribe nada hasta que el lector toca
     un filtro. Sin JavaScript se ve el informe entero; con JavaScript, además,
     se puede interrogar. Mejora progresiva, no dependencia.

   LO QUE NO HACE
     No recalcula el FWCI ni los percentiles: son métricas NORMALIZADAS que
     SciVal computa contra el mundo, y promediarlas sobre un subconjunto
     arbitrario daría un número con aspecto de FWCI que no lo es. Sobre un
     recorte se informa la MEDIANA de los valores que la fuente ya asignó a
     cada publicación, y se dice que es eso. Confundir «promedio de FWCI» con
     «FWCI del conjunto» es el error que el Leiden Manifesto pide no cometer. */

/* ─────────────────────────────────────────────────── el estado del recorte */

export const DIMENSIONES = [
  ['anio',          'Año',                p => [String(p.anio)]],
  ['qs_area',       'Área QS',            p => p.qs_area],
  ['unidad',        'Unidad académica',   p => p.unidades.length ? p.unidades : ['Sin dato declarado']],
  ['tipo',          'Tipo documental',    p => [p.tipo]],
  ['open_access',   'Acceso abierto',     p => p.open_access.length ? p.open_access : ['Sin dato declarado']],
  ['colaboracion',  'Colaboración',       p => [p.es_internacional === null ? 'Sin dato declarado'
                                                : p.es_internacional ? 'Internacional' : 'Nacional']],
];

const EXTRAE = Object.fromEntries(DIMENSIONES.map(([k, , f]) => [k, f]));

/** ¿Esta publicación entra en el recorte? `omitir` deja fuera una dimensión,
    que es como se cuentan las facetas de la propia dimensión sin que se
    anulen a sí mismas. */
export function pasa(p, sel, omitir = null) {
  for (const [clave] of DIMENSIONES) {
    if (clave === omitir) continue;
    const elegidos = sel[clave];
    if (!elegidos || !elegidos.length) continue;
    // OR dentro de una dimensión, AND entre dimensiones. Es lo que espera
    // cualquiera que haya usado un filtro, y hacerlo al revés convierte cada
    // clic adicional en menos resultados sin que se entienda por qué.
    if (!EXTRAE[clave](p).some(v => elegidos.includes(String(v)))) return false;
  }
  return true;
}

export const recorte = (pubs, sel) => pubs.filter(p => pasa(p, sel));

/* ──────────────────────────────────────────────────────── los indicadores */

const num = xs => xs.filter(v => typeof v === 'number' && !Number.isNaN(v));

export function mediana(xs) {
  const v = num(xs).slice().sort((a, b) => a - b);
  if (!v.length) return null;
  const m = v.length >> 1;
  return v.length % 2 ? v[m] : (v[m - 1] + v[m]) / 2;
}

/** Las cifras de cabecera del recorte.

    Cada una declara SU PROPIO DENOMINADOR, que es la decisión D-16 del
    proyecto: no todas las publicaciones tienen métricas, así que dividir
    siempre por el total daría porcentajes que no significan nada. */
export function resumen(sel_pubs) {
  const conMetricas = sel_pubs.filter(p => p.tiene_metricas);
  const conColab = sel_pubs.filter(p => p.es_internacional !== null);
  const inter = conColab.filter(p => p.es_internacional);
  const citas = conMetricas.reduce((a, p) => a + (p.citas || 0), 0);
  const fwci = num(conMetricas.map(p => p.fwci));

  return {
    publicaciones: { valor: sel_pubs.length, base: sel_pubs.length },
    citas:         { valor: citas, base: conMetricas.length },
    citas_por_pub: { valor: conMetricas.length ? citas / conMetricas.length : null,
                     base: conMetricas.length, decimales: 2 },
    // MEDIANA y no media: la distribución del FWCI es asimétrica —unas pocas
    // publicaciones muy citadas tiran del promedio— y sobre un recorte
    // pequeño la media miente más todavía.
    fwci_mediano:  { valor: mediana(fwci), base: fwci.length, decimales: 2 },
    internacional: { valor: conColab.length ? inter.length / conColab.length * 100 : null,
                     base: conColab.length, decimales: 1, sufijo: ' %' },
    autores:       { valor: new Set(sel_pubs.flatMap(p => p.autores_uft)).size,
                     base: sel_pubs.filter(p => p.tiene_autoria).length },
  };
}

/** Recuento por categoría de una dimensión, listo para dibujar. */
export function porDimension(sel_pubs, clave, { tope = 0, ordenar = true } = {}) {
  const cuenta = new Map();
  for (const p of sel_pubs) {
    for (const v of EXTRAE[clave](p)) {
      cuenta.set(String(v), (cuenta.get(String(v)) || 0) + 1);
    }
  }
  let filas = [...cuenta].map(([valor, n]) => ({ valor, n }));
  // El año es un EJE, no un ranking: ordenarlo por frecuencia destruye la
  // única lectura que tiene, que es la secuencia temporal.
  filas.sort(clave === 'anio' || !ordenar
    ? (a, b) => a.valor.localeCompare(b.valor)
    : (a, b) => b.n - a.n || a.valor.localeCompare(b.valor));
  return tope ? filas.slice(0, tope) : filas;
}

/** Recuentos por faceta para pintar los propios controles del filtro.

    Se calculan con las DEMÁS dimensiones aplicadas pero no la propia: si una
    faceta se contara a sí misma, al elegirla todas sus hermanas caerían a
    cero y el filtro dejaría de poder cambiarse sin limpiarlo antes. */
export function facetas(pubs, sel, clave) {
  const visibles = pubs.filter(p => pasa(p, sel, clave));
  const cuenta = new Map();
  for (const p of visibles) {
    for (const v of EXTRAE[clave](p)) cuenta.set(String(v), (cuenta.get(String(v)) || 0) + 1);
  }
  return cuenta;
}

/* ────────────────────────────────────────────────────── URL como estado */

/* El recorte vive en la barra de direcciones. Es lo que permite CITAR una
   vista concreta —«la Facultad de Medicina en 2024»— en un correo o en un
   informe, que es justo lo que un lector de datos institucionales necesita
   hacer y lo que un tablero sin URL no deja. También hace que el botón de
   volver funcione. */

export function leerURL(busqueda = location.search) {
  const q = new URLSearchParams(busqueda), sel = {};
  for (const [clave] of DIMENSIONES) {
    const v = q.get(clave);
    if (v) sel[clave] = v.split('|').filter(Boolean);
  }
  return sel;
}

export function escribirURL(sel, reemplazar = true) {
  const q = new URLSearchParams();
  for (const [clave] of DIMENSIONES) {
    if (sel[clave] && sel[clave].length) q.set(clave, sel[clave].join('|'));
  }
  const url = q.toString() ? `?${q}` : location.pathname;
  history[reemplazar ? 'replaceState' : 'pushState'](null, '', url);
}

export const hayRecorte = sel => DIMENSIONES.some(([c]) => sel[c] && sel[c].length);

/** Cómo se llama el recorte activo, en palabras. Un tablero que sólo muestra
    cifras filtradas sin decir por qué está filtrado produce lecturas falsas:
    quien llega por un enlace tiene que saber qué está mirando. */
export function describir(sel) {
  const partes = [];
  for (const [clave, etiqueta] of DIMENSIONES) {
    const v = sel[clave];
    if (v && v.length) partes.push(`${etiqueta}: ${v.join(' o ')}`);
  }
  return partes;
}
