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
| `D-74` | Las resoluciones humanas viven en `config/resoluciones_humanas.yml` | Una resolución es un hecho verificado, no una regla. En el código sería invisible; aquí es dato versionado, con su evidencia al lado | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-75` | Resolver una ambigüedad no la borra: baja de severidad y queda como revisada | Una afirmación verificada y una no verificada no pueden verse igual ni contarse en la misma cifra | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-76` | `T-05` se cierra como **no es duplicado**: ambos siguen en el universo | Verificado por el usuario contra los dos DOI. El de 2025 es una carta al editor sobre el artículo de 2024: mismo título, documentos distintos | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-77` | Lo que depende de una fuente externa se deja *pedido*, no sólo anotado | `T-02` y `T-06` no son trabajo de código, pero dejar la pregunta hecha con la evidencia delante sí lo es | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-78` | `internal/` y `data/raw/` **se mantienen** en el repositorio público | El riesgo es bajo y documentar la incertidumbre es lo que hace auditable al proyecto. Purgar el historial es desproporcionado para esta exposición | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-79` | La documentación pasa a declarar la exposición, no a negarla | El defecto real no era de seguridad sino de coherencia: `internal/README.md` decía «NO PUBLICAR» y estaba publicado | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-80` | Se declaran las tres condiciones que obligarían a revisar D-78 | Una decisión sin criterio de revisión se convierte en inercia | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-81` | El conector **verifica** asignaciones existentes; no las crea ni las reescribe | `authors_orcid.csv` guarda de dónde vino cada dato. Machacarlo borraría la procedencia; la verificación va en un archivo aparte | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-82` | Las credenciales se leen del entorno y de ningún otro sitio | El repositorio es público: una credencial en un archivo versionado queda expuesta en el mismo commit | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-83` | `no_verificable` y `sin_coincidencia` son categorías distintas | La primera es ausencia de evidencia; la segunda, evidencia en contra. Fundirlas convertiría un registro vacío en una acusación | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-84` | La autoprueba sin red es obligatoria y corre en CI | El entorno de integración no alcanza la API: sin autoprueba, la lógica se rompería en silencio | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-85` | La ejecución en Windows se hace con un asistente, no copiando comandos | Una instrucción que se puede copiar mal se copiará mal. El script comprueba cada paso y dice qué falló | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-86` | El Client Secret se pide oculto y en el momento, nunca por variable de entorno pegada | Pegarlo en una consola lo deja en el historial; en un archivo, en el repositorio. `Read-Host -AsSecureString` no deja rastro | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-87` | El `.ps1` se guarda con BOM UTF-8 | PowerShell 5.1 lee un script sin BOM como ANSI y corrompe los acentos | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-88` | Detectar un intérprete es ejecutarlo, no comprobar que el comando exista | Windows instala alias de `python` y `python3` que apuntan a la Microsoft Store y no son Python. `Get-Command` los da por buenos | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-89` | La verificación de ORCID puede correr en GitHub Actions, no sólo en local | El proyecto ya ejecuta Python allí. Un equipo administrado por la institución puede tener bloqueada la instalación, y eso no debería impedir el trabajo | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-90` | En esa vía las credenciales van a los secretos del repositorio | Cifradas y no legibles ni desde la propia interfaz. Mejor que una consola o un archivo local, no sólo más cómodo | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-91` | El contrato de la API de ORCID pasa de supuesto a verificado | 10 de 10 confirmadas prueba que el conector lee bien la respuesta. Era la única incógnita real que quedaba | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-92` | Las acciones de los workflows se suben a las que usan Node 24 | GitHub avisa de que `checkout@v4`, `setup-python@v5` y `upload-artifact@v4` corren forzadas sobre Node 24. Un aviso que se repite en cada ejecución acaba tapando uno que sí importa | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-93` | «Todas» necesita un valor explícito (`0`), no el campo vacío | Un campo vacío hace que GitHub sustituya el `default`. Pedir «sin límite» dejando el hueco en blanco devolvía 10 sin avisar | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-94` | Los archivos se añaden al índice uno por uno, comprobando que existan | `git add A B` falla entero si `B` no existe. `orcid_hallazgos.csv` sólo se genera si hay dudosas; sin él, tampoco se guardaba `A` | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-95` | El veredicto de ORCID se publica en la ficha de autor | Un ORCID de Crossref es una hipótesis por apellido e inicial. Publicarlo sin su evidencia lo convierte en un hecho sobre una persona con nombre y apellido, contra `<non_negotiable_rules>` | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-96` | En el listado se marca sólo la excepción, no la norma | 153 de 174 están confirmadas. Etiquetarlas todas es ruido; la información es la minoría que se sale | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-97` | `sin_coincidencia` se publica como «sin confirmar», nunca como «incorrecta» | La evidencia dice que no respalda la asignación, no que la desmienta. La segunda frase es una acusación que los datos no sostienen | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-98` | `--cifra` se separa de `--marca` | `--marca` cambia de oficio entre temas: tinta en claro, superficie en oscuro. Un token no puede hacer las dos cosas | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-99` | `orcid_api.py` fusiona en vez de sobrescribir | Escribir sin mirar convertía cualquier ejecución parcial en pérdida de datos, y era el camino por defecto del workflow | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-100` | Tres vías de cobertura, una sola regla de emparejamiento, importada | Dos copias de una regla que la documentación presenta como una sola divergen en cuanto alguien corrige una | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-101` | La búsqueda por afiliación NO publica | Ancla la asignación sólo en el nombre. Sin publicación compartida, dos homónimos de la misma universidad son indistinguibles | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-102` | Un desacuerdo entre Crossref y el registro se encola, no se resuelve | Uno de los dos está equivocado y cuál no se decide mirando nombres | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-103` | Las asignaciones halladas por `doi-self` dicen «declarado por el titular», no «verificado» | Su veredicto `confirmada` es circular: se las encontró justamente por declarar el DOI | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-104` | Los recuentos agregados se cuentan por etiqueta, no por veredicto | Contar por veredicto inflaría las verificaciones independientes con comprobaciones circulares | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-105` | La clase visual viaja aparte del veredicto | Un mismo veredicto merece dos tratamientos según de dónde venga la asignación | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-106` | Las decisiones se aplican por un script con autoprueba, no a mano | Una fusión mal transcrita no se distingue de una decidida | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-107` | Un conjunto de decisiones contradictorio detiene la aplicación | Aplicar una contradicción deja el resultado sin significado y sin aviso | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-108` | La forma canónica se elige por frecuencia, con la tilde del apellido por delante | Ordenar por longitud desempataba alfabéticamente, y en español eso publica la variante sin tilde | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-109` | La tilde de la INICIAL no decide | Que el nombre de pila lleve tilde no se deduce de la fuente | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-110` | Las fichas de la corrida anterior se borran antes de escribir | Al consolidar cambian los slugs y quedaban huérfanas con datos viejos | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-111` | Cada ficha fusionada declara qué firmas la componen, y el buscador las encuentra por cualquiera | Sin eso, quien llegue desde Scopus con «Giglio A.» no encuentra sus publicaciones | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-112` | Entre varias variantes con ORCID gana la evidencia más fuerte, no la última fila | La etiqueta dependía del orden de ordenación del archivo | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
| `D-113` | Los candidatos por afiliación confirmados se publican con `fuente = revisión humana` | Lo que les faltaba era el juicio de una persona, y es lo que aporta el archivo | Pendientes: cierre de T-17 y T-18, herramienta de revisión |
