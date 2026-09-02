/* vista.js — construcción de HTML, sin DOM.

   TODO lo que hay aquí es una función de datos a cadena. Ni una lectura de
   `document`, ni un `addEventListener`, ni un `localStorage`. Esa disciplina
   es la que permite que el mismo código corra en dos sitios:

     · en el BUILD, bajo Node (src/build/prerender.mjs), para dejar el HTML
       ya escrito en dist/*.html;
     · en el NAVEGADOR (paginas.js), cuando hay que repintar tras un filtro.

   Antes esta lógica vivía dentro de los renderizadores de página, mezclada con
   `innerHTML =`. Separarla no es una preferencia de estilo: es la condición
   para que el sitio tenga contenido sin JavaScript sin mantener dos versiones
   del mismo marcado, que es como esas dos versiones acaban divergiendo.

   La INTERACCIÓN —conmutador de vista, scroll-spy, tooltip, filtros— sigue
   viviendo en paginas.js. Aquí sólo se emite el marcado que esa interacción
   después manipula. */

import * as c from './core.js';

/* El FWCI mediano (0,41) frente a la media (0,87) es el dato que más fácilmente
   se malinterpreta: se explicita en portada, no sólo en el módulo. */
export function lectura(kpisLista) {
  const fwci = kpisLista.find(k => k.codigo === 'I-03');
  if (!fwci) return '';
  return `<div class="modulo modulo-lectura">
    <h2>Cómo leer estas cifras</h2>
    <p>El FWCI compara las citas recibidas con las esperadas para
    publicaciones del mismo campo, año y tipo: <strong>1,0 es el promedio
    mundial</strong>. Aquí la media es ${c.num(fwci.valor, 2)} y la mediana
    ${c.num(fwci.mediana, 2)}. La diferencia entre ambas indica una
    distribución asimétrica: unas pocas publicaciones muy citadas elevan el
    promedio.</p>
    ${c.nota(fwci.nota)}
    <p class="nota">Cada indicador declara sobre cuántas publicaciones se
    calcula. No todas las publicaciones tienen métricas: el denominador
    cambia según el indicador.</p>
  </div>`;
}

/** Banda de cierre de la portada: la salida a las secciones.

    Se genera en vez de escribirse en el HTML para que no pueda divergir de
    PAGINAS: si mañana se añade una sección, aparece aquí sola. Va sobre el
    suelo de énfasis, que sólo admite tipografía y enlaces. */
export function cierrePortada() {
  const salidas = c.PAGINAS.filter(([href]) =>
    ['produccion.html', 'impacto.html', 'colaboracion.html', 'tematica.html'].includes(href));
  return `
    <div class="banda-titulo">
      <h2>Cada indicador declara su propio denominador.</h2>
      <p>Las cifras de este informe no se miden todas sobre el mismo conjunto,
      y por eso dos de ellas pueden diferir sin contradecirse. Cada gráfico
      lleva pegada su fuente, su fecha de corte y sobre cuántos casos está
      medido.</p>
    </div>
    <div class="banda-salidas">${salidas.map(([href, txt]) => `
      <a href="${href}"><strong>${c.escapar(txt)}</strong><span>Ver la sección →</span></a>`).join('')}
    </div>`;
}

/* ------------------------------------------------------------ catálogo */

/** El catálogo completo de indicadores: los 40 evaluados, no los 27 que se
    publican.

    POR QUÉ EXISTE
    El sitio mostraba 27 indicadores y no decía nada de los otros 13. Para un
    lector, «no está» tiene al menos tres lecturas incompatibles: no se midió,
    se midió y salió mal, o no se puede medir sin inventar el dato. Publicar el
    criterio es lo que separa un informe de una selección de cifras favorables.

    Es una tabla y no tarjetas a propósito: cuarenta entradas que se comparan
    entre sí se leen en columnas. Y va sin JavaScript —se pre-renderiza— porque
    es justo el contenido que alguien va a querer citar o archivar. */
export function catalogo(cat) {
  const { indicadores, resumen, categorias, etiquetas_estado: est } = cat;

  const resumenHTML = Object.entries(est)
    .filter(([e]) => resumen[e])
    .map(([e, [etq, detalle]]) => `
      <div class="kpi">
        <span class="valor">${resumen[e]}</span>
        <span class="etiqueta">${c.escapar(etq)}</span>
        <span class="secundario">${c.escapar(detalle)}</span>
      </div>`).join('');

  const fila = (r) => {
    const den = r.denominador
      ? `${c.escapar(r.denominador)}<br><span class="nota">${c.nf.format(r.denominador_valor)}</span>`
      : '<span class="sin-dato-txt">No aplica</span>';
    // El porqué de no publicarse va en su propia fila y no en una celda: es
    // prosa, y meterla en una columna la haría ilegible en las cuarenta.
    const motivo = [r.razon, r.estado !== 'publicado' ? r.advertencia : null]
      .filter(Boolean).join(' ');
    const extra = (motivo || r.que_falta) ? `
      <tr class="cat-motivo">
        <td colspan="6">
          ${motivo ? `<strong>Por qué:</strong> ${c.escapar(motivo)}` : ''}
          ${r.que_falta ? `<br><strong>Qué falta:</strong> ${c.escapar(r.que_falta)}` : ''}
        </td>
      </tr>` : '';
    return `
      <tr id="${r.codigo}">
        <td><span class="codigo">${r.codigo}</span></td>
        <td>
          <strong>${c.escapar(r.nombre)}</strong>
          ${r.definicion ? `<br><span class="nota">${c.escapar(r.definicion)}</span>` : ''}
        </td>
        <td>${r.fuente ? c.escapar(r.fuente)
          : '<span class="sin-dato-txt">No se calcula</span>'}</td>
        <td>${den}</td>
        <td>${r.cobertura ? c.escapar(r.cobertura) : '—'}</td>
        <td><span class="estado" data-e="${r.estado}">${c.escapar(r.estado_etiqueta)}</span>
          ${r.confiabilidad ? `<br><span class="nota">confiabilidad ${c.escapar(r.confiabilidad)}</span>` : ''}
        </td>
      </tr>${extra}`;
  };

  const secciones = Object.entries(categorias).map(([clave, etiqueta]) => {
    const filas = indicadores.filter(r => r.categoria === clave);
    if (!filas.length) return '';
    return `
    <section class="modulo" id="cat-${clave}" tabindex="-1">
      <header><div class="modulo-id"><h2>${c.escapar(etiqueta)}</h2>
        <span class="codigo">${filas.length}</span></div></header>
      <div class="tabla-envoltura tabla-datos tabla-catalogo">
        <table>
          <thead><tr>
            <th scope="col">Cód.</th><th scope="col">Indicador y definición</th>
            <th scope="col">Fuente</th><th scope="col">Denominador</th>
            <th scope="col">Cobertura medida</th><th scope="col">Estado</th>
          </tr></thead>
          <tbody>${filas.map(fila).join('')}</tbody>
        </table>
      </div>
    </section>`;
  }).join('');

  const indice = Object.entries(categorias).map(([clave, etiqueta]) =>
    `<li><a href="#cat-${clave}"><span class="rail-txt">${c.escapar(etiqueta)}</span></a></li>`).join('');

  return `
    <div class="kpis" data-n="${Object.values(resumen).filter(Boolean).length}">${resumenHTML}</div>
    <p class="nota">Las coberturas están <strong>medidas sobre los datos</strong>,
    no estimadas: salen de <code>indicator_feasibility.csv</code>, que se
    regenera en cada build. Un indicador diferido está verificado como
    calculable; uno no calculable no lo está, y aproximarlo sería inventar la
    métrica.</p>
    <nav class="rail" aria-label="Categorías del catálogo">
      <p class="rail-titulo">En esta página</p><ol>${indice}</ol></nav>
    ${secciones}`;
}

/** Producción ampliada: recuentos que una Facultad declara en su propio
    sitio, fuera del corpus indexado en Scopus. Es un corpus PARALELO
    declarado (D-206, D-398) — nunca aparece en los gráficos de
    producción/impacto del resto del sitio, y por eso vive en su propia
    página con su propio marcado, no reutilizando `RENDER`/`kpiCarta` de
    los indicadores Scopus/SciVal.

    El párrafo de transparencia (fuera de ventana / sin año) se compone
    aquí desde `datos.fuera_de_ventana_o_sin_anio` — nunca una cifra
    escrita a mano — porque ocultar esos registros habría sido tan
    engañoso como mezclarlos en un gráfico Scopus: la ventana temporal del
    proyecto no es motivo para que un dato declarado deje de contarse. */
export function produccionDeclarada(datos) {
  const { resumen, por_facultad_anio: filas, fuera_de_ventana_o_sin_anio: extra,
          ventana, procedencia: proc, nota, fuentes } = datos;

  if (!fuentes || !fuentes.length) {
    return `
    <p class="nota">Ninguna Facultad tiene, por ahora, un listado propio
    declarado en <code>config/sources.yml</code>. Esta sección aparece vacía
    a propósito: el dato es opcional, no un indicador que debiera existir.</p>`;
  }

  const kpi = (valor, etiqueta, secundario) => `
    <div class="kpi">
      <span class="valor">${c.nf.format(valor)}</span>
      <span class="etiqueta">${c.escapar(etiqueta)}</span>
      ${secundario ? `<span class="secundario">${c.escapar(secundario)}</span>` : ''}
    </div>`;

  const kpisHTML = [
    kpi(resumen.total_leido, 'Registros declarados',
      `por las Facultades participantes, ${resumen.duplicados_colapsados_por_doi} duplicados de la fuente ya colapsados`),
    kpi(resumen.en_universo_scopus, 'Ya en el universo Scopus',
      'divulgación: ya se cuentan en el resto del sitio, no se repiten aquí'),
    kpi(resumen.fuera_del_universo, 'Fuera del universo Scopus',
      'el conjunto que este corpus paralelo aporta de nuevo'),
    kpi(resumen.en_ventana, `En la ventana ${ventana.inicio}-${ventana.fin}`,
      'la cifra principal de la tabla de abajo'),
  ].join('');

  const filaTabla = (r) => `
    <tr><td>${c.escapar(r.facultad)}</td><td>${r.anio}</td>
      <td>${c.nf.format(r.n)}</td></tr>`;

  const tabla = filas.length ? `
    <div class="tabla-envoltura tabla-datos">
      <table>
        <thead><tr><th scope="col">Facultad</th><th scope="col">Año</th>
          <th scope="col">Publicaciones declaradas</th></tr></thead>
        <tbody>${filas.map(filaTabla).join('')}</tbody>
      </table>
    </div>` : `
    <p class="nota">Ninguna publicación declarada cae dentro de la ventana
    ${ventana.inicio}-${ventana.fin}. Ver la nota de transparencia abajo:
    no significa que no haya datos, sino que los que hay quedan fuera de
    esta ventana o sin año declarado.</p>`;

  const notaExtra = (extra || []).filter(e => e.fuera_de_ventana || e.sin_anio)
    .map(e => {
      const partes = [];
      if (e.fuera_de_ventana) partes.push(`${c.nf.format(e.fuera_de_ventana)} fuera de la ventana ${ventana.inicio}-${ventana.fin}`);
      if (e.sin_anio) partes.push(`${c.nf.format(e.sin_anio)} sin año declarado`);
      return `${c.escapar(e.facultad)}: ${partes.join(', ')}`;
    }).join('; ');

  return `
    <div class="kpis" data-n="4">${kpisHTML}</div>
    ${c.nota(nota)}
    <h2>Por Facultad y año, dentro de la ventana ${ventana.inicio}-${ventana.fin}</h2>
    ${tabla}
    ${notaExtra ? `<p class="nota">Registros declarados adicionales que
    quedan fuera de esta tabla, sin descartarse: ${notaExtra}.</p>` : ''}
    ${c.sello(proc)}
    <p class="nota">En esta página, «Cobertura» es el porcentaje de lo
    declarado que cae dentro de la ventana ${ventana.inicio}-${ventana.fin}
    — no el sentido habitual del sello en el resto del sitio (porcentaje de
    publicaciones con un dato poblado).</p>`;
}

/** La lista de procedencia de metodologia.html: fuentes, ventana temporal,
    fecha de corte de citas, export de origen y build. Vivía inline en
    paginas.js — se saca aquí por lo mismo que el resto del archivo: para que
    el prerenderizado no tenga una segunda copia del marcado. */
export function procedencia(meta) {
  return `
    <ul>
      <li>Fuentes: ${meta.fuentes.join(', ')}</li>
      <li>Ventana temporal: ${meta.ventana.inicio}–${meta.ventana.fin}</li>
      <li>Citas actualizadas al: <strong>${meta.fecha_corte_citas}</strong></li>
      <li>Export de origen: ${meta.fecha_export}</li>
      <li>Publicaciones: ${c.nf.format(meta.denominadores.universo_total)} ·
          con métricas: ${c.nf.format(meta.denominadores.con_metricas)} ·
          con autoría detallada: ${c.nf.format(meta.denominadores.con_autoria_detallada)}</li>
      <li>Build: ${meta.fecha_build}</li>
    </ul>`;
}

/** Estado de la auditoría de datos (V2-27): la misma tabla de 30 reglas que
    `docs/VALIDATION_REPORT.md`, publicada donde el sitio se ve. Antes vivía
    sólo en el repositorio — un informe que se declara riguroso y no deja
    ver su propia auditoría le pide al lector que confíe sin poder
    comprobar. El resumen va siempre visible; la tabla completa entra en
    `<details>` para no imponerse sobre el resto de la página. */
export function validacion(v) {
  const filas = v.reglas.map(r => `<tr class="${r.resultado === 'FALLA' ? 'val-falla' : ''}">
      <td class="mono">${c.escapar(r.regla)}</td>
      <td>${c.escapar(r.severidad)}</td>
      <td>${c.escapar(r.descripcion)}</td>
      <td>${r.resultado === 'FALLA' ? '<strong>FALLA</strong>' : 'Pasa'}</td>
      <td>${c.escapar(r.observado)}</td>
    </tr>`).join('');

  return `
    <p class="val-resumen">
      <strong>${c.nf.format(v.reglas_evaluadas)}</strong> reglas evaluadas ·
      <strong>${c.nf.format(v.pasan)}</strong> pasan ·
      <strong>${c.nf.format(v.fallan)}</strong> falla${v.fallan === 1 ? '' : 'n'} ·
      <strong>${c.nf.format(v.bloqueantes_fallando)}</strong> bloqueante${v.bloqueantes_fallando === 1 ? '' : 's'} fallando.
      Es la compuerta que el propio build no deja pasar si alguna regla bloqueante falla.
    </p>
    <details class="metodo">
      <summary>Ver las ${c.nf.format(v.reglas_evaluadas)} reglas, una por una</summary>
      <div class="metodo-cuerpo">
        <div class="tabla-envoltura"><table class="tabla-validacion">
          <thead><tr><th scope="col">Regla</th><th scope="col">Severidad</th>
            <th scope="col">Descripción</th><th scope="col">Resultado</th>
            <th scope="col">Observado</th></tr></thead>
          <tbody>${filas}</tbody>
        </table></div>
      </div>
    </details>`;
}

/** El glosario completo de metodologia.html, una sección por término con
    `id="{slug}"`. Es el destino de todo enlace `#slug` que apunte a una
    definición —desde el tooltip de ayuda contextual o desde otra página,
    como «Cómo se lee esta red →» en colaboracion.html— y por eso tiene que
    pre-renderizarse: sin JavaScript, esos enlaces aterrizaban en un
    contenedor vacío y el ancla no existía. */
export function glosario(entradas) {
  return entradas.map(e => `
    <section class="modulo" id="${e.slug}">
      <h2>${c.escapar(e.termino)}</h2>
      <p>${c.escapar(e.corto)}</p>
      ${e.extendido ? `<p class="nota">${c.escapar(e.extendido)}</p>` : ''}
    </section>`).join('');
}
