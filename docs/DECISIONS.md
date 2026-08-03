# Índice de decisiones

**Generado** por `src/state/snapshot.py` desde las tablas de `SESSION_NOTES.md`. No editar a mano.

Una decisión registrada aquí **no se reabre sin una razón nueva** (`CLAUDE.md`, `<memory_and_continuity>`).

| # | Decisión | Fundamento | Fase |
|---|---|---|---|
| `D-01` | `EID` es PK de Publicación; `DOI` clave secundaria | 100 % cobertura, 0 duplicados; 19 registros sin DOI | Fase 1 |
| `D-02` | Doble método de detección institucional con reconciliación obligatoria | Un solo método no es auditable | Fase 1 |
| `D-03` | Prohibido el matching por subcadena; patrón con límite de palabra | 15 falsos positivos medidos con `inis` | Fase 1 |
| `D-04` | `Autoria` es entidad puente de primera clase | La afiliación varía entre publicaciones | Fase 1 |
| `D-05` | Los `.RData` son referencia, nunca fuente de indicadores | Proceso generador no trazable | Fase 1 |
| `D-06` | SciVal = métricas y temática; Scopus = autoría y afiliación | Cada fuente aporta lo que la otra no tiene | Fase 1 |
| `D-07` | ORCID se modela vacío y declarado, no se omite | Exigido por `PROJECT_SPEC.md` | Fase 1 |
| `D-08` | Duplicados probables y ambigüedades se encolan, no se resuelven | Restricción de `CLAUDE.md` | Fase 1 |
| `D-09` | `No determinada` es categoría de primera clase | No inventar datos | Fase 1 |
| `D-10` | Todo indicador declara fuente, corte, ventana, n y método | Trazabilidad | Fase 1 |
| `D-11` | Métricas de revista en entidad separada de métricas de documento | No confundir revista con artículo | Fase 1 |
| `D-12` | «h-index en ventana», nunca «h-index» | No es el h-index de carrera | Fase 1 |
| `D-13` | ID institucional y reglas en configuración, no en código | Replicabilidad | Fase 1 |
| `D-14` | Salidas de conciliación son capa interna por defecto | `<data_governance>` | Fase 1 |
| `D-15` | Los 396 investigadores son set de validación, no fuente de verdad | Confirmado por el usuario | Fase 1 |
| `D-16` | Cada indicador declara su propio denominador (823 / 818 / 816) | Las banderas de disponibilidad de Fase 1 no permiten un total único | Fase 2 |
| `D-17` | Dos niveles de advertencia: nota contextual (19) y advertencia destacada (5) | Marcar todo por igual equivale a no marcar nada | Fase 2 |
| `D-18` | `AU-04` (FWCI por autor) se descarta, no se aproxima | El FWCI de un autor no es el promedio de sus publicaciones; calcularlo sería inventar la métrica | Fase 2 |
| `D-19` | La ficha de autor muestra «top 10 % de citación» en lugar de FWCI | Es normalizado por campo y sí está disponible por publicación | Fase 2 |
| `D-20` | Web estática con preagregación total en build | Corpus pequeño y de actualización esporádica; garantiza que lo publicado sea idéntico a lo auditado | Fase 2 |
| `D-21` | Fichas de autor como archivos individuales, no bundle único | Evita descargar ~3 MB para ver una ficha | Fase 2 |
| `D-22` | `src/build/` no lee de `data/raw/`; sólo de `data/interim/` validado | Barrera de calidad: sin validación no hay build | Fase 2 |
| `D-23` | La barrera pública/interna se verifica automáticamente post-build | No puede depender de que nadie se equivoque al escribir el build | Fase 2 |
| `D-24` | «Sin dato declarado» nunca se representa como 0 ni se excluye del 100 % | Consecuencia directa de D-09 (no imputar) | Fase 2 |
| `D-25` | Sin flechas de tendencia en los KPIs | Con 3 años y sin histórico previo, implicaría una tendencia que los datos no sostienen | Fase 2 |
| `D-26` | El FWCI se muestra con media y mediana juntas | Sólo la media (0,87) ocultaría que la mediana es 0,41 | Fase 2 |
| `D-27` | Los filtros incluyen «No determinada» y «Sin dato» como opciones reales | La ausencia de dato es información, no ruido a esconder | Fase 2 |
| `D-28` | Mapa coroplético y nube de palabras descartados | 23 países sobre ~200 exagera visualmente; la nube no tiene lectura cuantitativa | Fase 2 |
| `D-29` | Ranking de autores por defecto filtrado a n >= 5, sin excluir a nadie del catálogo | Calidad en la vista principal sin exclusión arbitraria | Fase 2 |
| `D-30` | Stack: HTML/CSS/JS sin dependencias + build en Python | Cero dependencias en el navegador; el sitio debe poder servirse en red cerrada. Sin toolchain que mantener | Fase 3 |
| `D-31` | Gráficos como SVG generados en el propio JS | Evita cargar una librería desde un CDN, cosa que el proyecto no puede permitirse | Fase 3 |
| `D-32` | El sitio se sirve desde `dist/`, no desde `web/` | Sin los datos ensamblados, `web/` no debe aparentar estar completo | Fase 3 |
| `D-33` | Tres compuertas con código de salida, no avisos | La separación de capas no puede depender de que nadie se equivoque | Fase 3 |
| `D-34` | Los atributos de publicación se materializan en `data/interim/` | Permite que `src/build/` no lea nunca de `data/raw/` (respeta D-22) | Fase 3 |
| `D-35` | Identificadores de autor únicos por firma, con sufijo de desambiguación | Dos variantes distintas nunca comparten archivo (ver hallazgo) | Fase 3 |
| `D-36` | `load_authorship()` proyecta sólo columnas publicables en la lectura | Los campos internos no pueden filtrarse por descuido más adelante | Fase 3 |
| `D-37` | Los denominadores se actualizan a mano en `config/indicators.yml` | Cambiar el denominador de todo lo publicado es una decisión, no un efecto secundario | Fase 3 |
| `D-38` | Toda exportación CSV arrastra la procedencia en su cabecera | Un CSV suelto sin fecha de corte deja de ser interpretable | Fase 3 |
| `D-39` | Licencia MIT para el software, separada de los datos | Permite adoptar el software sin heredar restricciones de Elsevier | Fase 3 |
| `D-40` | T-11 se implementa como supuesto parametrizado, no se bloquea | Publicar las 589 con ranking por defecto n >= 5; cambiarlo no requiere código | Fase 3 |
| `D-41` | El resultado del enriquecimiento vive en `data/enriched/`, versionado | `data/interim/` está en `.gitignore` por ser regenerable; esto no lo es: consultar 804 DOI a un servicio externo no es reproducible a voluntad | Post-V1: ORCID, despliegue y estado |
| `D-42` | `rdata` pasa a dependencia opcional con degradación declarada | No hay ruedas para Python 3.14 y los `.RData` son fuentes de referencia (D-05). Una dependencia dura habría bloqueado la instalación por un archivo que no alimenta ningún indicador | Post-V1: ORCID, despliegue y estado |
| `D-43` | El respaldo por apellido sólo se aplica si Crossref no declara nombre de pila | Sin esa condición el respaldo asigna el ORCID de una persona a la firma de otra (ver supuestos descartados) | Post-V1: ORCID, despliegue y estado |
| `D-44` | Compartir ORCID **no** fusiona firmas: se encola en `internal/identity_candidates.csv` | La asignación firma→ORCID es a su vez una hipótesis. Encadenar dos hipótesis no produce un hecho (extiende D-08) | Post-V1: ORCID, despliegue y estado |
| `D-45` | La jerarquía escuela→facultad se declara con estado `confirmada` o `inferida` | Permite publicar la agregación por facultad sin afirmar como oficial lo que se dedujo de las afiliaciones | Post-V1: ORCID, despliegue y estado |
| `D-46` | `STATE.md` es una vista derivada generada, fuera del orden de precedencia | Un resumen mantenido a mano envejece y no se puede auditar. Si contradice a `config/` o `PLAN.md`, manda la fuente | Post-V1: ORCID, despliegue y estado |
| `D-47` | La activación de GitHub Pages queda como paso manual documentado | El `GITHUB_TOKEN` del workflow puede publicar pero no crear el sitio. Se documenta en vez de dejar un `enablement: true` que falla | Post-V1: ORCID, despliegue y estado |
| `D-48` | La compuerta de capas recorre los artefactos completos, sin muestrear | Revisaba los primeros 200 elementos de cada lista y la más larga tiene 823: el 76 % no se miraba. Una compuerta que muestrea no es una compuerta | Auditoría general y rediseño de la interfaz |
| `D-49` | Toda serie se calcula sobre el denominador que declara | `A-01` y `R-01` se calculaban sobre 823 y declaraban 816: el gráfico contradecía su propia nota en pantalla | Auditoría general y rediseño de la interfaz |
| `D-50` | La multivaluación se declara en config y el front la rotula junto al gráfico | Un gráfico cuyas barras no suman el total tiene que decirlo donde se lee, no sólo en la nota metodológica | Auditoría general y rediseño de la interfaz |
| `D-51` | Las advertencias de LECTURA viven en el front, separadas de las de cálculo | Describen un sesgo que induce el gráfico concreto; dejan de aplicar si cambia la forma. `config/indicators.yml` describe el cálculo, que no cambia con el dibujo | Auditoría general y rediseño de la interfaz |
| `D-52` | El color codifica una de tres cosas y se declara cuál: serie, ordinal o serie única | Cuatro tonos para Q1–Q4 afirmaban que son categorías sin relación, cuando son posiciones de una escala | Auditoría general y rediseño de la interfaz |
| `D-53` | Si el nombre de la categoría ya es un color, el color no codifica | `A-01` dibujaba «Green» de naranja. Se mantiene en una sola serie | Auditoría general y rediseño de la interfaz |
| `D-54` | Las dependencias se acotan por rango mayor | El workflow reconstruye y publica solo: con `>=` a secas, un cambio en pandas republica cifras distintas sin aviso | Auditoría general y rediseño de la interfaz |
| `D-55` | Modo oscuro con paleta re-escalonada y revalidada, no invertida | Invertir una paleta validada no produce una paleta validada | Auditoría general y rediseño de la interfaz |
| `D-56` | La paleta entregada se usa para identidad, superficies y rampa ordinal, **no para series de datos** | Medida como categórica falla tres de cinco comprobaciones. `#80ED99` vs `#57CC99` dan ΔE 10,3 en visión **normal**, bajo el piso de 15 | Sistema visual sobre la paleta institucional |
| `D-57` | Paleta categórica de seis ranuras que abre con el azul-teal de la referencia | Conserva el espíritu y separa de verdad: peor par CVD ΔE 8,7 claro / 8,0 oscuro | Sistema visual sobre la paleta institucional |
| `D-58` | El **orden** de las ranuras es mecanismo de seguridad, no estética | Violeta va entre naranja y verde porque ese par caía en la banda de aviso. Reordenar lo arregla sin cambiar un solo color | Sistema visual sobre la paleta institucional |
| `D-59` | Seis series, no ocho | Una séptima obligaría a meter un tono en la franja que ya ocupan otros. Más allá, se agrupa en «Otras» | Sistema visual sobre la paleta institucional |
| `D-60` | Tipografía: pila del sistema con jerarquía por peso, tamaño e interletrado | El proyecto prohíbe CDN y autoalojar añadiría binarios y peso por una mejora que no cambia ninguna lectura analítica | Sistema visual sobre la paleta institucional |
| `D-61` | Cifras tabulares sólo donde se alinean en columna | En un KPI suelto las proporcionales se leen mejor; forzar la tabulación sólo separa dígitos | Sistema visual sobre la paleta institucional |
| `D-62` | La separación entre superficies la hace el filete, no la elevación | Radios de 6 px y sombra mínima. Una interfaz analítica no flota | Sistema visual sobre la paleta institucional |
| `D-63` | Resaltar es atenuar el resto | Señalar sin apagar las demás no dirige la mirada: sólo añade un borde que hay que buscar | Sistema visual sobre la paleta institucional |
| `D-64` | La cuota sobre el total sólo aparece donde las barras son partes de un total | En umbrales encajados, multivaluados y rankings recortados, un porcentaje afirmaría algo falso | Sistema visual sobre la paleta institucional |
| `D-65` | Todo texto de interfaz alcanza 4,5:1 contra el peor fondo en que aparece | `--tinta-3` se definió como «sólo texto no esencial» y acto seguido se usó para las marcas de eje, que son la escala del gráfico | Segunda auditoría: accesibilidad medida |
| `D-66` | La etiqueta de la línea de referencia tiene tinta propia, distinta del trazo | El ámbar del trazo da 2,81:1 como texto: sirve para una línea, no para leer «promedio mundial» | Segunda auditoría: accesibilidad medida |
| `D-67` | Toda cabecera ordenable es enfocable y se activa con `Enter` o `Espacio` | Un `<th>` no es un control operable por defecto: la tabla no se podía ordenar sin ratón | Segunda auditoría: accesibilidad medida |
| `D-68` | El `aria-label` de un gráfico nombra el indicador, no la forma | Cinco «gráfico de barras horizontales» seguidos no orientan a nadie | Segunda auditoría: accesibilidad medida |
| `D-69` | Un comentario que afirma una garantía debe corresponder a código que la implementa | El CSS prometía «leyenda siempre presente con dos o más series» y no había ninguna | Segunda auditoría: accesibilidad medida |
| `D-70` | Los artefactos de codificación de la fuente se reparan; las concatenaciones se corrigen con una tabla declarada en config | Reponer la letra base de `ı`+acento es canonicalizar, no inventar. Deducir una regla general de tres concatenaciones rompería nombres legítimos: son hechos sobre este conjunto, no una regla | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-71` | `T-18` se cierra sin cambios, con la medición | 699 KB comprimen a 146 KB; la página entera transfiere 181 KB. La cifra que motivó el pendiente era sin comprimir | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-72` | La revisión humana se desbloquea con herramienta, no resolviéndola | `D-08` prohíbe resolver; no prohíbe reunir la evidencia. La herramienta no decide ni propone respuesta por defecto | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-73` | La coautoría directa es el descarte de identidad más limpio | Nadie firma dos veces el mismo artículo: si dos firmas comparten publicación, son personas distintas | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
