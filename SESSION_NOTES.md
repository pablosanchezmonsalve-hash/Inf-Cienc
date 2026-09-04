# SESSION_NOTES.md
# Bitácora de sesiones

---

## Sesión 2026-07-31 — Fase 1

**Estado inicial:** repositorio con 7 archivos de datos sueltos, un commit,
sin código, sin estructura, sin documentos de gobernanza.
`PLAN.md` y `SESSION_NOTES.md` no existían pese a estar exigidos por
`CLAUDE.md`. Sin Claude-Mem disponible: esta sesión es el punto de origen.

### Decisiones tomadas

| # | Decisión | Fundamento |
|---|---|---|
| D-01 | `EID` es PK de Publicación; `DOI` clave secundaria | 100 % cobertura, 0 duplicados; 19 registros sin DOI |
| D-02 | Doble método de detección institucional con reconciliación obligatoria | Un solo método no es auditable |
| D-03 | Prohibido el matching por subcadena; patrón con límite de palabra | 15 falsos positivos medidos con `inis` |
| D-04 | `Autoria` es entidad puente de primera clase | La afiliación varía entre publicaciones |
| D-05 | Los `.RData` son referencia, nunca fuente de indicadores | Proceso generador no trazable |
| D-06 | SciVal = métricas y temática; Scopus = autoría y afiliación | Cada fuente aporta lo que la otra no tiene |
| D-07 | ORCID se modela vacío y declarado, no se omite | Exigido por `PROJECT_SPEC.md` |
| D-08 | Duplicados probables y ambigüedades se encolan, no se resuelven | Restricción de `CLAUDE.md` |
| D-09 | `No determinada` es categoría de primera clase | No inventar datos |
| D-10 | Todo indicador declara fuente, corte, ventana, n y método | Trazabilidad |
| D-11 | Métricas de revista en entidad separada de métricas de documento | No confundir revista con artículo |
| D-12 | «h-index en ventana», nunca «h-index» | No es el h-index de carrera |
| D-13 | ID institucional y reglas en configuración, no en código | Replicabilidad |
| D-14 | Salidas de conciliación son capa interna por defecto | `<data_governance>` |
| D-15 | Los 396 investigadores son set de validación, no fuente de verdad | Confirmado por el usuario |

**Decisiones de alcance validadas por el usuario:** ventana 2023–2025; universo
= unión (823) con banderas de disponibilidad.

### Archivos creados

```
CLAUDE.md, PROJECT_SPEC.md          versionados desde los uploads
PLAN.md, SESSION_NOTES.md           gobernanza que faltaba
README.md, requirements.txt, .gitignore
prompts/PROMPT_{COMPACTO,FASE_1,FASE_2,FASE_3}.md
config/{institution,matching_rules,sources}.yml
src/audit/{common,01_inventory,02_reconcile_sources,
           03_affiliation_variants,04_author_population,
           05_validation_rules,run_all}.py
docs/{AUDIT_REPORT,DATA_MODEL,METHODOLOGY,LIMITATIONS,VALIDATION_REPORT}.md
internal/{ambiguities_authors,ambiguities_publications,matching_log}.csv
data/raw/                           los 7 archivos originales, movidos con git mv
data/interim/                       11 salidas regenerables
```

Ningún archivo de datos original fue modificado.

### Supuestos descartados durante la sesión

| Supuesto inicial | Qué pasó |
|---|---|
| «18 DOI duplicados en el CSV» | **Falso.** Artefacto de contar 19 DOI ausentes como repetidos. El recuento real es 0 |
| «La cobertura de unidad académica es 70,1 %» | **Falso.** La extracción tomaba la facultad de otra institución en casos de doble afiliación. Real: 63,8 % |
| «El patrón peligroso es `finis`» | **Impreciso.** El peligroso es la subcadena `inis` (15 falsos positivos); `finis` da 0 |
| «El patrón `\bfinis\s+terrae\b` es suficiente» | **Insuficiente.** Perdía `Universidad Finis-Terrae` con guion. Corregido a `[\s\-]+` |
| «La brecha 585/440/396 indica fallas del trabajo manual» | **Falso.** El trabajo manual era correcto; la brecha es de ventana temporal (143 autores sólo en 2023) y de variantes de firma |
| «Conviene quedarse con la intersección de 811 publicaciones» | **Descartado.** Las 7 exclusivas de Scopus son humanidades y ciencias sociales; excluirlas agravaba el sesgo de cobertura |

### Ambigüedades abiertas

- 249 casos de un Scopus ID con varios nombres (P-05).
- 123 variantes de nombre del mismo apellido base (P-03).
- 20 nombres con varios Scopus ID (P-04).
- 24 autores con más de una unidad académica (I-06).
- 8 publicaciones con bloques autor/afiliación desalineados.
- 1 duplicado probable Article/Letter (P-01).
- 12 publicaciones presentes en una sola fuente (X-01).
- El export de Scopus no declara fecha de corte.
- El vocabulario de unidades no está validado institucionalmente.

### Verificación

29 reglas ejecutadas: 28 pasan, 1 falla no bloqueante (`E-06`, columna
`Molecular Sequence Numbers` vacía — hallazgo real, debe excluirse en Fase 2).
Cero fallas bloqueantes.

Auditoría reproducible completa: `python3 src/audit/run_all.py`.

### Próximo paso recomendado

Iniciar Fase 2 (`prompts/PROMPT_FASE_2.md`): catálogo de indicadores y
selección V1. Sin bloqueos. Los pendientes T-01 a T-10 están en `PLAN.md`.

---

## Sesión 2026-07-31 — Fase 2

**Estado inicial:** Fase 1 aprobada y en `main` de la rama de trabajo. Universo
canónico de 823 publicaciones, 589 formas de firma, 29 reglas de validación sin
fallas bloqueantes.

### Decisiones tomadas

| # | Decisión | Fundamento |
|---|---|---|
| D-16 | Cada indicador declara su propio denominador (823 / 818 / 816) | Las banderas de disponibilidad de Fase 1 no permiten un total único |
| D-17 | Dos niveles de advertencia: nota contextual (19) y advertencia destacada (5) | Marcar todo por igual equivale a no marcar nada |
| D-18 | `AU-04` (FWCI por autor) se descarta, no se aproxima | El FWCI de un autor no es el promedio de sus publicaciones; calcularlo sería inventar la métrica |
| D-19 | La ficha de autor muestra «top 10 % de citación» en lugar de FWCI | Es normalizado por campo y sí está disponible por publicación |
| D-20 | Web estática con preagregación total en build | Corpus pequeño y de actualización esporádica; garantiza que lo publicado sea idéntico a lo auditado |
| D-21 | Fichas de autor como archivos individuales, no bundle único | Evita descargar ~3 MB para ver una ficha |
| D-22 | `src/build/` no lee de `data/raw/`; sólo de `data/interim/` validado | Barrera de calidad: sin validación no hay build |
| D-23 | La barrera pública/interna se verifica automáticamente post-build | No puede depender de que nadie se equivoque al escribir el build |
| D-24 | «Sin dato declarado» nunca se representa como 0 ni se excluye del 100 % | Consecuencia directa de D-09 (no imputar) |
| D-25 | Sin flechas de tendencia en los KPIs | Con 3 años y sin histórico previo, implicaría una tendencia que los datos no sostienen |
| D-26 | El FWCI se muestra con media y mediana juntas | Sólo la media (0,87) ocultaría que la mediana es 0,41 |
| D-27 | Los filtros incluyen «No determinada» y «Sin dato» como opciones reales | La ausencia de dato es información, no ruido a esconder |
| D-28 | Mapa coroplético y nube de palabras descartados | 23 países sobre ~200 exagera visualmente; la nube no tiene lectura cuantitativa |
| D-29 | Ranking de autores por defecto filtrado a n >= 5, sin excluir a nadie del catálogo | Calidad en la vista principal sin exclusión arbitraria |

### Archivos creados o modificados

```
src/analysis/indicator_feasibility.py    verificación reproducible de 40 indicadores
config/indicators.yml                    catálogo parametrizado
docs/INDICATORS.md                       catálogo + selección V1
docs/ARCHITECTURE.md                     pipeline, artefactos, despliegue, rendimiento
docs/UX_UI.md                            navegación, KPIs, módulos, filtros, estados
docs/LAYERS.md                           capa pública e interna
docs/AUTHOR_PROFILE.md                   ficha pública de autor
docs/GLOSSARY.md                         glosario y tooltips
data/interim/indicator_feasibility.csv   evidencia medida
PLAN.md, SESSION_NOTES.md                actualizados
```

### Hallazgos

- **Semántica del percentil de citación determinada empíricamente.** El campo
  `Outputs in Top Citation Percentiles, per percentile` no declara qué
  representa. Correlación −0,66 con citas; las 3 más citadas tienen percentil
  1–3 y las no citadas 56–78. Conclusión: es el percentil de la publicación,
  menor = mejor. Habilita `I-05`. Queda como pendiente T-13 confirmarlo contra
  la documentación oficial de SciVal.
- **FWCI mediano 0,41 frente a media 0,87.** Distribución fuertemente
  asimétrica. Mostrar sólo la media daría una imagen más uniforme que la real.
- **El 46 % de las publicaciones de 2025 aún no tiene citas.** El FWCI del año
  más reciente no es comparable con el de 2023.
- **497 de 589 firmas tienen h-index en ventana <= 1.** El indicador casi no
  discrimina en una ventana de 3 años.
- **Colaboración es el bloque más robusto:** cobertura 100 % de las
  publicaciones con métrica. 51,2 % internacional.

### Supuestos descartados durante la sesión

| Supuesto | Qué pasó |
|---|---|
| «21 indicadores en V1, 5 con advertencia» | **Impreciso.** El recuento real sobre `config/indicators.yml` es 27 publicados (26 calculables + 1 placeholder), 19 con nota contextual y 5 con advertencia destacada. Corregido en `docs/INDICATORS.md` |
| «El percentil de citación es ambiguo y no usable» | **Descartado.** Es determinable empíricamente y habilita un indicador normalizado por campo, el único disponible a nivel de publicación |

### Ambigüedades abiertas

Las nueve heredadas de Fase 1 siguen abiertas. Se suman:

- Alcance de publicación de fichas de autor: 589 o subconjunto (T-11).
- Stack de despliegue no decidido (T-08).
- Semántica del percentil verificada empíricamente pero no documentalmente (T-13).

### Próximo paso recomendado

Iniciar Fase 3 (`prompts/PROMPT_FASE_3.md`). Requiere antes la decisión T-11
(alcance de fichas) y T-08 (stack). Ningún bloqueo técnico.

---

## Sesión 2026-07-31 — Fase 3

**Estado inicial:** Fases 1 y 2 aprobadas. Universo de 823 publicaciones, 589
formas de firma, catálogo de 40 indicadores con 27 seleccionados para V1.
Faltaban las decisiones T-08 (stack) y T-11 (alcance de fichas).

### Decisiones tomadas

| # | Decisión | Fundamento |
|---|---|---|
| D-30 | Stack: HTML/CSS/JS sin dependencias + build en Python | Cero dependencias en el navegador; el sitio debe poder servirse en red cerrada. Sin toolchain que mantener |
| D-31 | Gráficos como SVG generados en el propio JS | Evita cargar una librería desde un CDN, cosa que el proyecto no puede permitirse |
| D-32 | El sitio se sirve desde `dist/`, no desde `web/` | Sin los datos ensamblados, `web/` no debe aparentar estar completo |
| D-33 | Tres compuertas con código de salida, no avisos | La separación de capas no puede depender de que nadie se equivoque |
| D-34 | Los atributos de publicación se materializan en `data/interim/` | Permite que `src/build/` no lea nunca de `data/raw/` (respeta D-22) |
| D-35 | Identificadores de autor únicos por firma, con sufijo de desambiguación | Dos variantes distintas nunca comparten archivo (ver hallazgo) |
| D-36 | `load_authorship()` proyecta sólo columnas publicables en la lectura | Los campos internos no pueden filtrarse por descuido más adelante |
| D-37 | Los denominadores se actualizan a mano en `config/indicators.yml` | Cambiar el denominador de todo lo publicado es una decisión, no un efecto secundario |
| D-38 | Toda exportación CSV arrastra la procedencia en su cabecera | Un CSV suelto sin fecha de corte deja de ser interpretable |
| D-39 | Licencia MIT para el software, separada de los datos | Permite adoptar el software sin heredar restricciones de Elsevier |
| D-40 | T-11 se implementa como supuesto parametrizado, no se bloquea | Publicar las 589 con ranking por defecto n >= 5; cambiarlo no requiere código |

### Archivos creados o modificados

```
Makefile, LICENSE, .gitignore, README.md          reescritos o nuevos
config/publication.yml                            alcance de publicación
src/audit/02_reconcile_sources.py                 enriquecido (38 columnas)
src/audit/04_author_population.py                 columna de validación parametrizada
config/sources.yml                                columna_autor declarada
src/build/{common_build,01_publications,02_indicators,
           03_authors,04_glossary,05_verify_public_layer,
           06_assemble_site,build_all}.py         pipeline de build
web/{9 páginas}.html, web/assets/{css,js,favicon} interfaz
docs/{DEPLOYMENT,UPDATING,REPLICATION,DATA_LICENSE,
      V2_BACKLOG,BUILD_VERIFICATION}.md           documentación de Fase 3
PLAN.md, SESSION_NOTES.md                         actualizados
```

### Hallazgos

- **Colisión de identificadores de autor.** La normalización del slug quita
  acentos y guiones, de modo que `Orellana-Donoso M.` y `Orellana Donoso M.`
  producían el mismo archivo: **589 firmas generaban sólo 552 fichas** y 37
  quedaban sobrescritas. Era exactamente el colapso automático de variantes que
  prohíbe D-08, ocurriendo por un detalle de nomenclatura de archivos.
  Corregido con `unique_slugs()`: 68 firmas reciben un sufijo derivado del
  nombre exacto, estable entre builds. Las tres variantes de `Orellana-Donoso`
  ahora coexisten.
- **`/favicon.ico` devolvía 404** en la portada. Chromium lo pide a nivel de
  navegador, por lo que el listener de red de la página no lo captura y sólo
  aparecía como error de consola. Resuelto con un favicon SVG local.
- **El único resto institucional en el código** era el nombre de una columna del
  Excel de validación. Movido a `config/sources.yml`:
  `grep -ri "finis" src/ web/` devuelve 0.

### Verificación

Ejecutada en navegador real (Chromium vía Playwright):

- Las 9 páginas cargan **sin un solo error de consola**.
- Filtros: OR dentro de un filtro (2023 + 2024 = 504), AND entre filtros
  (+ Article = 379), recuentos por faceta correctos.
- Persistencia en URL sobrevive a la recarga.
- Búsqueda insensible a acentos («nutricion» encuentra 6).
- Tooltip accesible por foco de teclado, no sólo por puntero.
- Exportación CSV incluye la fecha de corte en la cabecera.
- Ficha de una variante desambiguada resuelve al autor correcto.
- `05_verify_public_layer`: 596 artefactos revisados, **0 fallas**.
- `06_assemble_site`: `data/raw/` e `internal/` ausentes de `dist/`, verificado.

### Supuestos descartados durante la sesión

| Supuesto | Qué pasó |
|---|---|
| «`slugify()` basta para identificar fichas de autor» | **Falso.** Colapsaba variantes distintas: 37 fichas se perdían. Requirió `unique_slugs()` |
| «El 404 de la portada era un artefacto del test» | **Falso.** Era `/favicon.ico`, reproducible. Corregido |
| «No queda ninguna cadena institucional en el código» | **Impreciso.** Quedaba una, en `04_author_population.py`. Parametrizada |

### Ambigüedades abiertas

Las heredadas de Fases 1 y 2 siguen abiertas. Se suman:

- T-11 sin confirmar: se implementó el supuesto D-40.
- Licencia de datos derivados (CC BY 4.0) propuesta, sin validación jurídica.
- Alcance de publicación de métricas de Elsevier sin verificar.
- Branding institucional (`color_primario`, `logo_path`) son placeholders.
- Sin pruebas automatizadas del sitio en el repositorio (V2-17).

### Próximo paso recomendado

V1 completa. Lo de mayor rendimiento para V2 es **V2-01: enriquecer ORCID desde
Crossref por DOI** (cobertura 97,7 %): sin identificador persistente, las 589
firmas no pueden consolidarse y tres indicadores siguen bloqueados. Ver
`docs/V2_BACKLOG.md`.

### Confirmaciones del usuario (cierre de sesión)

| Decisión | Estado |
|---|---|
| T-11 · alcance de fichas de autor | **Confirmado**: se publican las 589 firmas, ranking por defecto n >= 5 |
| Licencia del software | **Confirmada**: MIT |
| Licencia de datos derivados | **Confirmada**: CC BY 4.0 |

La aprobación de licencias fija la intención del proyecto. **No sustituye** la
verificación con la unidad que administra la suscripción a Elsevier sobre qué
métricas derivadas pueden publicarse abiertamente: eso es un hecho externo, no
una decisión del proyecto, y sigue abierto.

---

## Sesión 2026-08-01 — Post-V1: ORCID, despliegue y estado

**Estado inicial:** V1 completa y las tres fases cerradas. El sitio existía sólo
en `dist/` local. `T-01` (enriquecimiento de ORCID) seguía abierto y bloqueaba
la consolidación de identidad de autor.

### Decisiones tomadas

| # | Decisión | Fundamento |
|---|---|---|
| D-41 | El resultado del enriquecimiento vive en `data/enriched/`, versionado | `data/interim/` está en `.gitignore` por ser regenerable; esto no lo es: consultar 804 DOI a un servicio externo no es reproducible a voluntad |
| D-42 | `rdata` pasa a dependencia opcional con degradación declarada | No hay ruedas para Python 3.14 y los `.RData` son fuentes de referencia (D-05). Una dependencia dura habría bloqueado la instalación por un archivo que no alimenta ningún indicador |
| D-43 | El respaldo por apellido sólo se aplica si Crossref no declara nombre de pila | Sin esa condición el respaldo asigna el ORCID de una persona a la firma de otra (ver supuestos descartados) |
| D-44 | Compartir ORCID **no** fusiona firmas: se encola en `internal/identity_candidates.csv` | La asignación firma→ORCID es a su vez una hipótesis. Encadenar dos hipótesis no produce un hecho (extiende D-08) |
| D-45 | La jerarquía escuela→facultad se declara con estado `confirmada` o `inferida` | Permite publicar la agregación por facultad sin afirmar como oficial lo que se dedujo de las afiliaciones |
| D-46 | `STATE.md` es una vista derivada generada, fuera del orden de precedencia | Un resumen mantenido a mano envejece y no se puede auditar. Si contradice a `config/` o `PLAN.md`, manda la fuente |
| D-47 | La activación de GitHub Pages queda como paso manual documentado | El `GITHUB_TOKEN` del workflow puede publicar pero no crear el sitio. Se documenta en vez de dejar un `enablement: true` que falla |

### Archivos creados o modificados

```
src/enrich/orcid_crossref.py                enriquecimiento desde Crossref (nuevo)
src/state/snapshot.py                       generador de STATE.md y DECISIONS.md (nuevo)
STATE.md, docs/DECISIONS.md                 generados
data/enriched/authors_orcid.csv             174 firmas con ORCID
internal/identity_candidates.csv            17 grupos que comparten ORCID
internal/orcid_conflicts.csv                1 conflicto
.github/workflows/deploy.yml                build y publicación en Pages (nuevo)
docs/{ORCID_GUIDE,DEPLOYMENT}.md            guía de ejecución y paso manual de Pages
config/matching_rules.yml                   jerarquía escuela→facultad; patrón con guion
src/build/03_authors.py                     lee ORCID de data/enriched/
src/build/02_indicators.py                  P-07 agrega por facultad, con detalle_escuelas
src/build/common_build.py                   unique_slugs()
requirements.txt, CLAUDE.md, README.md,
Makefile (objetivo `estado`)                actualizados
```

### Hallazgos

- **Enriquecimiento ejecutado por el usuario** sobre 804 DOI (97,7 % del
  universo), **0 errores de red**: **174 de 589 firmas (29,5 %)** reciben ORCID,
  54 con confianza alta y 120 con confianza media, sobre **153 ORCID distintos**.
- **17 grupos de firmas comparten ORCID** (21 firmas colapsables). **11 de ellos
  son invisibles para la heurística de apellido** que alimenta la cola `P-03`:
  el caso claro es `Gubbins V.` / `Foxley V.G.`, que no comparten apellido. El
  identificador persistente aporta evidencia que la comparación de cadenas no
  puede producir.
- **Cota superior de 568 personas distintas** para 589 firmas, si se confirmaran
  las 21 colapsables. Es una cota, no un recuento.
- **El patrón blando de detección institucional no cubría el guion**:
  `Universidad Finis-Terrae` quedaba fuera. Corregido a `\bfinis[\s\-]+terrae\b`.
- **Sitio publicado**: `.github/workflows/deploy.yml`, ejecución #11 en verde
  sobre `8f05a51`, en
  https://pablosanchezmonsalve-hash.github.io/Inf-Cienc/
- **El costo de retomar el proyecto se midió**: leer `PLAN.md`,
  `SESSION_NOTES.md` y `docs/` por adelantado son ~3.700 líneas / 155 KB, de las
  que la mayoría es referencia puntual. `STATE.md` lo reduce a ~110 líneas con un
  mapa de qué abrir para cada pregunta.

### Supuestos descartados durante la sesión

| Supuesto | Qué pasó |
|---|---|
| «`authors_orcid.csv` es una salida intermedia» | **Falso.** `.gitignore` impedía versionarlo y el resultado de 804 consultas externas se habría perdido al limpiar. Movido a `data/enriched/` |
| «El respaldo por apellido es seguro cuando no hay coincidencia exacta» | **Falso.** Asignaba el ORCID de `Diaz, Marcela` a la firma `Diaz F.`. Restringido a los casos en que Crossref no declara nombre de pila |
| «`enablement: true` crea el sitio de Pages desde el workflow» | **Falso.** `Resource not accessible by integration`: el token publica, no crea. Documentado como paso manual |
| «`rdata` se instala en cualquier Python 3.11+» | **Falso.** No hay ruedas para 3.14. Dependencia marcada como opcional |
| «La proporción alta/media se invertiría en la corrida completa» | **Falso.** La muestra de 20 DOI ya anticipaba el resultado: 54 alta / 120 media |
| «Claude-Mem está disponible en esta sesión» | **Falso.** No hay binario, plugin ni servidor MCP. La memoria del proyecto es `SESSION_NOTES.md` + `STATE.md`, versionada y legible por cualquiera |

### Ambigüedades abiertas

Las heredadas siguen abiertas. Se suman o se precisan:

- **415 firmas (70,5 %) sin ORCID.** El techo real es la cobertura de ORCID en
  los registros de Crossref, no el método.
- **`Castro-Sepúlveda M.` aparece con dos ORCID** (`0000-0001-7673-7269` y
  `0000-0002-2270-299X`). Encolado, no resuelto.
- **17 grupos de firmas con ORCID compartido** esperando confirmación humana.
- **Los 13 nombres de unidad académica siguen sin catálogo oficial**, y tres de
  las cuatro jerarquías escuela→facultad son `inferida`. Sólo Kinesiología →
  Facultad de Medicina está confirmada por el usuario. El sitio de la
  universidad no es alcanzable desde este entorno: la validación requiere una
  fuente institucional.

### Próximo paso recomendado

Revisión humana de las colas de identidad, que es lo único que puede convertir
174 asignaciones y 17 grupos en una tabla maestra de autores consolidada
(`T-03`, `T-04`, `T-14`). Nada de eso es automatizable sin violar `D-08`.

---

## Sesión 2026-08-01 — Auditoría general y rediseño de la interfaz

**Estado inicial:** V1 desplegada. Encargo: auditar todo el trabajo hecho,
aplicar las correcciones que no requirieran decisión del usuario, y rediseñar la
interfaz buscando una experiencia moderna con una paleta atractiva.

### Decisiones tomadas

| # | Decisión | Fundamento |
|---|---|---|
| D-48 | La compuerta de capas recorre los artefactos completos, sin muestrear | Revisaba los primeros 200 elementos de cada lista y la más larga tiene 823: el 76 % no se miraba. Una compuerta que muestrea no es una compuerta |
| D-49 | Toda serie se calcula sobre el denominador que declara | `A-01` y `R-01` se calculaban sobre 823 y declaraban 816: el gráfico contradecía su propia nota en pantalla |
| D-50 | La multivaluación se declara en config y el front la rotula junto al gráfico | Un gráfico cuyas barras no suman el total tiene que decirlo donde se lee, no sólo en la nota metodológica |
| D-51 | Las advertencias de LECTURA viven en el front, separadas de las de cálculo | Describen un sesgo que induce el gráfico concreto; dejan de aplicar si cambia la forma. `config/indicators.yml` describe el cálculo, que no cambia con el dibujo |
| D-52 | El color codifica una de tres cosas y se declara cuál: serie, ordinal o serie única | Cuatro tonos para Q1–Q4 afirmaban que son categorías sin relación, cuando son posiciones de una escala |
| D-53 | Si el nombre de la categoría ya es un color, el color no codifica | `A-01` dibujaba «Green» de naranja. Se mantiene en una sola serie |
| D-54 | Las dependencias se acotan por rango mayor | El workflow reconstruye y publica solo: con `>=` a secas, un cambio en pandas republica cifras distintas sin aviso |
| D-55 | Modo oscuro con paleta re-escalonada y revalidada, no invertida | Invertir una paleta validada no produce una paleta validada |

### Archivos creados o modificados

```
web/assets/css/app.css                    sistema de diseño completo (reescrito)
web/assets/js/core.js                     motor de gráficos, tooltip, tema
web/assets/js/paginas.js                  escalas, advertencias, ORCID, panorama
web/*.html (9)                            arranque de tema sin destello
web/index.html                            sección «Panorama»
web/autores.html                          columna ORCID, umbral parametrizado
src/build/02_indicators.py                denominadores y multivaluación
src/build/03_authors.py                   ORCID en el listado; umbral en la ficha
src/build/05_verify_public_layer.py       fin del muestreo
src/audit/run_all.py                      código de salida distinto de cero
src/audit/common.py                       hojas por clave lógica, no por nombre
src/audit/04_author_population.py         ventana de validación desde config
config/{indicators,sources}.yml           multivaluado A-01; hojas y ventana
requirements.txt, .github/workflows/      rangos acotados; denylist completa
docs/{LAYERS,UX_UI}.md, internal/README   excepciones y alcance declarados
```

### Hallazgos de la auditoría

- **La capa interna está publicada.** `internal/README.md` dice «NO PUBLICAR» y
  el directorio está versionado en un repositorio público, junto a 33 MB de
  exportaciones brutas de Elsevier. Las tres compuertas cubren `dist/`; ninguna
  cubre el repositorio. **Declarado, no resuelto**: es una decisión del usuario.
- **`A-01` se contradecía en pantalla**: el gráfico mostraba 233 sin dato y su
  propia nota destacada decía 226. Dos denominadores distintos, 823 y 816.
- **`R-01` arrastraba el mismo descuadre**: 61 frente a los 54 de su nota.
- **Etiquetas cortadas por el lado equivocado**: la columna de etiquetas era fija
  en 210 px y los nombres largos se salían del lienzo por la izquierda.
- **`No determinada` se pintaba como un dato medido.** 437 pares, la segunda
  barra más larga de `P-07`, con el mismo azul que las facultades reales.
- **Los años se imprimían «2.025»**: `Intl.NumberFormat('es-CL')` aplicado a algo
  que es una etiqueta, no una cantidad.
- **Un ternario muerto** (`a.meta.denominadores ? 5 : 5`) y el umbral escrito a
  mano en `autores.html`, pese a estar parametrizado en config.
- **Los nombres de hoja del Excel institucional vivían en `common.py`**, no en
  config: la corrección de la sesión anterior parametrizó la columna y dejó el
  nombre de la hoja. La afirmación del README se había validado contra la cadena
  «finis», que nunca aparece en un nombre de hoja.
- **El ORCID no aparecía en el listado de autores**, sólo dentro de cada ficha.
- **`run_all.py` nunca salía con código distinto de cero**: el paso de CI llamado
  «Auditoría y validación» quedaba verde con reglas bloqueantes rotas.

### Verificación

- Reconstrucción limpia desde `data/raw/`: artefactos **byte a byte idénticos**.
- Recorrido exhaustivo de los 596 artefactos, sin el muestreo: **0 fugas**.
- `unique_slugs`: 589 firmas → 589 identificadores, 0 colisiones residuales.
- Paleta validada con la herramienta de `dataviz` contra las superficies reales:
  claro (`#ffffff`) pasa las cinco comprobaciones con aviso de contraste; oscuro
  (`#12151c`) las pasa todas.
- **32 combinaciones** (8 páginas × 2 temas × 2 anchos) en Chromium: sin errores
  de consola y sin desborde horizontal.
- Tooltip verificado con puntero y con foco de teclado.
- Escapado HTML confirmado sobre un título real con `c.2302A>G`.

### Supuestos descartados durante la sesión

| Supuesto | Qué pasó |
|---|---|
| «Emitir el color como atributo `fill` basta» | **Falso.** Una regla CSS gana al atributo de presentación: `.barra { fill }` pintaba «Sin dato declarado» del color de una serie medida. Detectado en captura, no en revisión de código |
| «Un lienzo SVG único sirve para cualquier contenedor» | **Falso.** Un lienzo de 680 dentro de una columna de 330 reduce el texto a la mitad. El ancho se declara según el contexto |
| «Colorear cada barra distingue mejor» | **Falso** en dos casos: en una escala ordenada afirma que no hay orden, y en categorías que se llaman como colores produce «Green» en naranja |
| «`grep -ri finis src/ web/` = 0 prueba que no hay literales institucionales» | **Insuficiente.** Quedaban `Publicaciones_UFT_detalle`, `Investigadores` y un `>= 2024` |
| «Las compuertas del build protegen la capa interna» | **Parcial.** Protegen `dist/`. El repositorio público no lo cubre ninguna |

### Ambigüedades abiertas

Las heredadas siguen abiertas. Se suman:

- **`internal/` y `data/raw/` publicados**: pendiente de decisión del usuario.
  Borrarlos ahora no los saca del historial de git.
- **`P-07` expone defectos de extracción** que hoy son visibles en el sitio:
  `Facultad de MedicinaEscuela de Medicina` y `Faculty of MedicineUniver-sidad`
  son cadenas concatenadas sin separador, y `Facultad de Ingeniería` aparece dos
  veces. Es dato, no presentación: no se corrige en silencio. Alimenta `T-02`.
- La estimación del ancho de texto en SVG es aproximada: no hay forma de medir
  una cadena que aún no está en el documento.

### Próximo paso recomendado

Decidir sobre `internal/` y `data/raw/` en el repositorio público, que es lo
único de la auditoría que quedó sin aplicar. Después, `T-02`: las cadenas
concatenadas de unidad académica ya son visibles para cualquier visitante.

---

## Sesión 2026-08-01 — Sistema visual sobre la paleta institucional

**Estado inicial:** interfaz auditada y corregida en la sesión anterior, con
identidad azul marino y cian. Encargo: reanclar el sistema visual en la paleta
`#22577A · #38A3A5 · #57CC99 · #80ED99 · #C7F9CC`, refinar tipografía y
jerarquía, y profundizar la interacción de gráficos y tablas.

### Decisiones tomadas

| # | Decisión | Fundamento |
|---|---|---|
| D-56 | La paleta entregada se usa para identidad, superficies y rampa ordinal, **no para series de datos** | Medida como categórica falla tres de cinco comprobaciones. `#80ED99` vs `#57CC99` dan ΔE 10,3 en visión **normal**, bajo el piso de 15 |
| D-57 | Paleta categórica de seis ranuras que abre con el azul-teal de la referencia | Conserva el espíritu y separa de verdad: peor par CVD ΔE 8,7 claro / 8,0 oscuro |
| D-58 | El **orden** de las ranuras es mecanismo de seguridad, no estética | Violeta va entre naranja y verde porque ese par caía en la banda de aviso. Reordenar lo arregla sin cambiar un solo color |
| D-59 | Seis series, no ocho | Una séptima obligaría a meter un tono en la franja que ya ocupan otros. Más allá, se agrupa en «Otras» |
| D-60 | Tipografía: pila del sistema con jerarquía por peso, tamaño e interletrado | El proyecto prohíbe CDN y autoalojar añadiría binarios y peso por una mejora que no cambia ninguna lectura analítica |
| D-61 | Cifras tabulares sólo donde se alinean en columna | En un KPI suelto las proporcionales se leen mejor; forzar la tabulación sólo separa dígitos |
| D-62 | La separación entre superficies la hace el filete, no la elevación | Radios de 6 px y sombra mínima. Una interfaz analítica no flota |
| D-63 | Resaltar es atenuar el resto | Señalar sin apagar las demás no dirige la mirada: sólo añade un borde que hay que buscar |
| D-64 | La cuota sobre el total sólo aparece donde las barras son partes de un total | En umbrales encajados, multivaluados y rankings recortados, un porcentaje afirmaría algo falso |

### Archivos creados o modificados

```
web/assets/css/app.css        sistema completo reescrito sobre la paleta nueva
web/assets/js/core.js         SERIES a seis; resaltado por atenuación; cuota en
                              el tooltip; reposicionamiento cuando no cabe
web/assets/js/paginas.js      cuotaValida por indicador; columna ordenada
docs/UX_UI.md                 §12 reescrito: paleta medida, tipografía,
                              espacio, interacción, responsive
```

### Hallazgos

- **La paleta pedida es excelente como identidad y pésima como paleta de
  datos**, y la causa es estructural: sus cinco tonos viven en la franja
  cian-verde, que es donde la deuteranopía y la protanopía colapsan diferencias.
  No es cuestión de afinar, ninguna paleta de datos honesta sale de ahí.
- **Es, en cambio, una rampa ordinal natural.** Los cuartiles `R-01` usan ahora
  una rampa de un tono anclada en `#38A3A5`: el orden se ve en el color mismo.
- **`#38A3A5` da 3,02:1 sobre blanco**: vale para rellenos y bordes, no para
  texto de enlace. Los enlaces usan `#1a6d78` (6,0:1).
- **`#57CC99` rinde 2,00:1 sobre blanco y 8,15:1 sobre la superficie oscura.**
  El mismo color es inservible en un modo y el color de acción natural en el
  otro: la prueba más clara de que el modo oscuro no puede ser una inversión.
- **La afordancia de ordenamiento sólo aparecía al pasar el puntero**, y la
  columna ordenada no se distinguía en las 51 filas visibles.

### Verificación

- Paleta categórica revalidada contra las superficies reales: **cinco
  comprobaciones en verde** en claro (`#ffffff`) y oscuro (`#12222a`).
- Rampa ordinal: cuatro comprobaciones en verde en ambos modos.
- Contrastes de texto calculados uno a uno antes de fijar los tokens.
- **32 combinaciones** (8 páginas × 2 temas × 2 anchos): sin errores de consola
  ni desborde horizontal.
- Interacción comprobada en Chromium: atenuación al 34 %, una sola marca activa,
  aislamiento entre gráficos de la misma página, foco por teclado con tooltip,
  cierre con `Escape`, y 51 celdas marcadas al reordenar por otra columna.

### Supuestos descartados durante la sesión

| Supuesto | Qué pasó |
|---|---|
| «Una paleta bonita de cinco tonos sirve para series» | **Falso, y medible.** Dos de sus verdes son indistinguibles incluso con visión normal |
| «Basta oscurecer los tonos claros de la paleta para usarla en datos» | **Insuficiente.** El problema es el rango de tono, no la luminosidad: al separarlos deja de ser esa paleta |
| «El modo oscuro se obtiene invirtiendo el claro» | **Falso.** `#57CC99` pasa de 2,00:1 a 8,15:1 según la superficie |
| «El resalte por contorno basta para explorar» | **Insuficiente.** Sin atenuar el resto, el contorno hay que buscarlo |

### Ambigüedades abiertas

Las heredadas siguen abiertas, incluida `T-16`. Se suma:

- El aviso de contraste de `#d4a017` (2,38:1 sobre blanco) se resuelve con
  relieve —etiqueta de valor y tabla equivalente, que el sitio ya tiene—, pero
  es un piso, no un margen: si en el futuro un gráfico prescinde de la etiqueta
  de valor, ese color deja de ser legal.

### Próximo paso recomendado

Sin cambios: `T-16` sigue siendo lo único que requiere decisión del usuario.

---

## Sesión 2026-08-01 — Segunda auditoría: accesibilidad medida

**Estado inicial:** V1 desplegada en producción (`3cff716`, corrida #12 en
verde). Encargo: volver a auditar el total del trabajo. Esta vez el objeto de la
auditoría incluía lo escrito en las dos sesiones anteriores.

### Decisiones tomadas

| # | Decisión | Fundamento |
|---|---|---|
| D-65 | Todo texto de interfaz alcanza 4,5:1 contra el peor fondo en que aparece | `--tinta-3` se definió como «sólo texto no esencial» y acto seguido se usó para las marcas de eje, que son la escala del gráfico |
| D-66 | La etiqueta de la línea de referencia tiene tinta propia, distinta del trazo | El ámbar del trazo da 2,81:1 como texto: sirve para una línea, no para leer «promedio mundial» |
| D-67 | Toda cabecera ordenable es enfocable y se activa con `Enter` o `Espacio` | Un `<th>` no es un control operable por defecto: la tabla no se podía ordenar sin ratón |
| D-68 | El `aria-label` de un gráfico nombra el indicador, no la forma | Cinco «gráfico de barras horizontales» seguidos no orientan a nadie |
| D-69 | Un comentario que afirma una garantía debe corresponder a código que la implementa | El CSS prometía «leyenda siempre presente con dos o más series» y no había ninguna |

### Archivos creados o modificados

```
web/assets/css/app.css        --tinta-3 legible; --aviso-tinta-grafico nuevo;
                              foco visible en cabecera ordenable; se retira el
                              esqueleto de carga que no usaba ninguna página
web/assets/js/core.js         etiqueta accesible por indicador en las tres
                              formas de gráfico; se retiran leyenda() y
                              esqueleto(), muertas
web/assets/js/paginas.js      activación por teclado de las cabeceras; título
                              propagado a los 17 gráficos
web/autores.html              tabindex en las cuatro cabeceras ordenables
README.md                     peso real por página, medido en navegador
docs/UX_UI.md                 teclado en tablas, etiquetado de gráficos y el
                              criterio real sobre leyendas
PLAN.md                       T-18
```

### Hallazgos

- **La tabla de autores no se podía ordenar sin ratón.** Verificado tabulando:
  25 pulsaciones de `Tab` desde el buscador y la cabecera nunca recibía foco.
  Fallo de WCAG 2.1.1, y agravado porque `docs/UX_UI.md` describía la afordancia
  de ordenamiento sin que la función existiera por teclado.
- **Cuatro contrastes bajo el mínimo AA**, medidos en el navegador sobre lo
  pintado: etiqueta de referencia 2,81:1, código de indicador 3,27:1 claro y
  4,22:1 oscuro, marcas de eje 3,74:1, migas 3,41:1. Los dos primeros llevan
  información: el promedio mundial del FWCI y la escala del gráfico.
- **Los cinco gráficos se anunciaban igual**, con `aria-label` genérico.
- **`leyenda()` y `esqueleto()` muertas**, y el CSS afirmaba una regla de
  leyendas que ningún código implementaba.
- **El README decía «carga de la portada ~25 KB»; son 107 KB.** La cifra era
  correcta hasta que la sección «Panorama» hizo que la portada cargara
  `series.json`, y el rediseño engordó CSS y JS. Deriva causada por el propio
  trabajo de la sesión anterior.
- **`publicaciones.html` transfiere 808 KB**, 699 de ellos `publications.json`.
  Nadie lo había medido. Anotado como `T-18`.

### Verificación

- Los cuatro contrastes vuelven a medirse tras el arreglo: 5,56 · 5,48 · 5,07 ·
  4,86 en claro, y 5,84 · 7,26 · 6,52 · 5,05 en oscuro. Todos sobre 4,5.
- Cabecera ordenable alcanzable con `Tab` y operable con `Enter`: sí.
- Los cinco gráficos anuncian su indicador y su número de categorías.
- 32 combinaciones de página × tema × ancho sin errores ni desborde.
- Reconstrucción limpia byte a byte idéntica; las tres compuertas en verde.

### Supuestos descartados durante la sesión

| Supuesto | Qué pasó |
|---|---|
| «El texto SVG se mide con `color`» | **Falso.** Se colorea con `fill`, y mi primera medición dio 16,33:1 donde había 3,74:1. Los cuatro fallos sólo aparecieron al corregir el método |
| «Documentar una afordancia equivale a haberla implementado» | **Falso.** Escribí que la ordenación se ve antes del hover sin comprobar que funcionara sin ratón |
| «Marcar `--tinta-3` como “no esencial” evita usarlo donde importa» | **Falso.** Lo usé para las marcas de eje en la misma hoja donde lo etiqueté así |
| «Una cifra de rendimiento del README sigue siendo válida tras un rediseño» | **Falso.** Pasó de 25 a 107 KB por cambios que hice yo |

### Ambigüedades abiertas

Las heredadas siguen abiertas, `T-16` incluida. Se suma `T-18`. Nada nuevo que
requiera decisión.

### Próximo paso recomendado

`T-16` sigue siendo lo único que depende del usuario.

---

## Sesión 2026-08-03 — Pendientes: cierre de T-17 y T-18, herramienta de revisión

**Estado inicial:** V1 desplegada, doce pendientes abiertos. Encargo: abarcarlos.
El usuario confirmó tres cosas: quiere explicación comprensible antes de decidir
`T-16`, revisará él mismo el duplicado de `T-05`, y sí a la herramienta de
revisión de identidad.

### Decisiones tomadas

| # | Decisión | Fundamento |
|---|---|---|
| D-70 | Los artefactos de codificación de la fuente se reparan; las concatenaciones se corrigen con una tabla declarada en config | Reponer la letra base de `ı`+acento es canonicalizar, no inventar. Deducir una regla general de tres concatenaciones rompería nombres legítimos: son hechos sobre este conjunto, no una regla |
| D-71 | `T-18` se cierra sin cambios, con la medición | 699 KB comprimen a 146 KB; la página entera transfiere 181 KB. La cifra que motivó el pendiente era sin comprimir |
| D-72 | La revisión humana se desbloquea con herramienta, no resolviéndola | `D-08` prohíbe resolver; no prohíbe reunir la evidencia. La herramienta no decide ni propone respuesta por defecto |
| D-73 | La coautoría directa es el descarte de identidad más limpio | Nadie firma dos veces el mismo artículo: si dos firmas comparten publicación, son personas distintas |

### Archivos creados o modificados

```
src/review/build_review.py         herramienta de revisión (nuevo)
internal/revision_identidad.html   generada, 89 casos
src/audit/common.py                reparar_texto_fuente() + correcciones
config/matching_rules.yml          correcciones_declaradas, 3 entradas justificadas
Makefile                           objetivo `revision`
internal/README.md                 la herramienta y cómo usarla
README.md                          peso por página, ahora comprimido y sin comprimir
PLAN.md                            T-17 y T-18 cerrados; T-03/04/14/15 desbloqueados
```

### Hallazgos

- **`Facultad de Ingenierı́a` no era un duplicado de datos sino de codificación**:
  usa `ı` (U+0131, i sin punto) más acento combinante en vez de `í`. Comprobado
  que **NFC no lo arregla**: ese par no tiene composición canónica. Separaba 1
  par de los otros 49.
- **Las tres cadenas concatenadas están así en el origen**, no las produce el
  extractor: la afiliación de Scopus dice literalmente
  `Facultad de MedicinaEscuela de Medicina`.
- Tras la reparación, **26 → 22 unidades distintas**. Verificado que el cambio
  toca exactamente los 4 pares rotos y ninguno más; la cobertura de unidad
  académica queda igual (63,8 %, 437 `No determinada`), porque esos 4 pares ya
  tenían unidad, sólo que rota.
- **`T-18` no era un problema.** Medido: `publications.json` comprime al 20 % y
  `authors.json` al 8 %. Restructurar habría sido trabajo contra una cifra mal
  leída.
- **Ninguno de los 127 pares de firmas candidatas comparte publicación.** El
  descarte más limpio no aplica en ningún caso. Verificado con control positivo
  —un par que sí co-firma da 1— para descartar que el cálculo estuviera roto.
- Los dos registros de `T-05` tienen **DOI distintos** (`…07451-7` y `…07630-6`),
  misma revista y mismos 7 autores: compatible con carta al editor sobre el
  propio artículo. Entregado al usuario para que lo verifique en Scopus.

### Verificación

- Herramienta probada en navegador: 89 casos, veredicto, nota, filtro,
  persistencia tras recarga y exportación a CSV de 93 líneas. Sin errores.
- Comprobado que no entra en `dist/` ni queda referenciada.
- 32 combinaciones de página × tema × ancho sin errores ni desborde.
- Las tres compuertas en verde; 29 reglas, 0 bloqueantes fallando.

### Supuestos descartados durante la sesión

| Supuesto | Qué pasó |
|---|---|
| «`Facultad de Ingenierı́a` es un problema de datos» | **Falso.** Es de codificación, y la normalización Unicode estándar no lo resuelve |
| «Las concatenaciones son un fallo del extractor» | **Falso.** Están así en la afiliación de origen |
| «699 KB en una petición es un problema de rendimiento» | **Falso.** Son 146 KB comprimidos. Medir antes de restructurar |
| «0 pares que comparten publicación sugiere que el cálculo falla» | **Falso.** El control positivo da 1: el cálculo funciona y el 0 es real |

### Ambigüedades abiertas

- **`T-16`**: pendiente de decisión, con explicación entregada al usuario.
- **`T-05`**: el usuario lo verifica en Scopus.
- **`T-02`, `T-06`, `T-13`**: dependen de fuentes externas (catálogo oficial de
  la universidad, reexportación de Scopus, documentación de SciVal).
- **`T-03`, `T-04`, `T-14`, `T-15`**: desbloqueados, esperando la revisión.
- **`T-10`** sigue dependiendo de `T-03`.

### Próximo paso recomendado

Que el usuario ejecute `make revision` y trabaje los 89 casos. Los 18 con
evidencia de ORCID son los más rápidos y los de mayor rendimiento.

---

## Sesión 2026-08-03 (cont.) — T-05 cerrado, T-02/T-06/T-13 desbloqueados

**Estado inicial:** el usuario verificó el duplicado de `T-05` contra ambos DOI
y pidió seguir con lo pendiente.

### Decisiones tomadas

| # | Decisión | Fundamento |
|---|---|---|
| D-74 | Las resoluciones humanas viven en `config/resoluciones_humanas.yml` | Una resolución es un hecho verificado, no una regla. En el código sería invisible; aquí es dato versionado, con su evidencia al lado |
| D-75 | Resolver una ambigüedad no la borra: baja de severidad y queda como revisada | Una afirmación verificada y una no verificada no pueden verse igual ni contarse en la misma cifra |
| D-76 | `T-05` se cierra como **no es duplicado**: ambos siguen en el universo | Verificado por el usuario contra los dos DOI. El de 2025 es una carta al editor sobre el artículo de 2024: mismo título, documentos distintos |
| D-77 | Lo que depende de una fuente externa se deja *pedido*, no sólo anotado | `T-02` y `T-06` no son trabajo de código, pero dejar la pregunta hecha con la evidencia delante sí lo es |

### Archivos creados o modificados

```
config/resoluciones_humanas.yml       nuevo · resoluciones verificadas
src/audit/common.py                   resolucion_duplicado()
src/audit/02_reconcile_sources.py     lee la resolución; baja severidad
src/audit/05_validation_rules.py      P-01 cuenta revisados y pendientes aparte
src/review/build_unit_validation.py   nuevo · hoja de validación para T-02
internal/validacion_unidades.md       generada
docs/METHODOLOGY.md                   §7 bis · evidencia del percentil (T-13)
docs/UPDATING_REQUEST.md              nuevo · qué pedir en la próxima carga (T-06)
Makefile, PLAN.md                     objetivo `revision` amplía; estados
```

### Hallazgos

- **`T-05` no era un duplicado.** DOI `…07451-7` (Article, 2024) es la
  investigación; DOI `…07630-6` (Letter, 2025) es una carta al editor sobre sus
  aspectos metodológicos. Mismo título, dos documentos. El universo sigue en
  823 y ningún denominador cambia.
- **La evidencia de `T-13` es concluyente.** Las 5 publicaciones más citadas
  (115, 77, 52, 46, 45 citas) están en percentil 1, 2, 3, 4 y 2; **todas** las
  no citadas están en 78, el máximo del rango. Correlación −0,66 con citas y
  −0,58 con FWCI. Menor percentil = mejor posición, sin ambigüedad razonable.
  Falta sólo el respaldo documental de Elsevier.
- **`T-06` importa menos de lo que su enunciado sugiere.** Lo que no declara
  fecha de corte es la exportación de Scopus, que aporta cobertura; las citas
  —lo que más se mueve— vienen de SciVal, que sí la declara. Queda registrado
  con esa proporción, no como un agujero de trazabilidad general.
- **La hoja de `T-02` deja el pendiente a una lectura de distancia**: 21
  unidades con sus recuentos, sus variantes reconocidas, las 4 jerarquías
  separadas entre confirmada e inferidas, y una afiliación real por unidad.

### Verificación

- `P-01` reporta ahora «1 grupo · 1 revisado · 0 pendientes» y las dos filas
  bajan a severidad informativa, conservando la traza.
- Universo intacto en 823; las tres compuertas en verde.
- Comprobado que `resoluciones_humanas.yml`, `validacion_unidades.md` y
  `revision_identidad.html` no aparecen ni se referencian en `dist/`.

### Supuestos descartados durante la sesión

| Supuesto | Qué pasó |
|---|---|
| «Resolver una ambigüedad es quitarla de la cola» | **Falso como diseño.** La coincidencia de título es real y se sigue declarando; lo que cambia es que consta como revisada |
| «`T-06` es un agujero de trazabilidad general» | **Impreciso.** Afecta la cobertura, no las citas: SciVal sí declara su corte |
| «Lo bloqueado por terceros no admite trabajo» | **Falso.** No se puede responder por ellos, pero sí dejar la pregunta hecha con la evidencia delante |

### Ambigüedades abiertas

- **`T-16`**: única decisión que sigue dependiendo del usuario.
- `T-02`, `T-06`, `T-13`: esperando respuesta externa, ya pedida.
- `T-03`, `T-04`, `T-14`, `T-15`: esperando la revisión con `make revision`.
- `T-10`: depende de `T-03`.

### Próximo paso recomendado

Enviar `internal/validacion_unidades.md` a quien administre el catálogo de
unidades, y `docs/UPDATING_REQUEST.md` a quien haga la exportación de Scopus.
Ambas cosas pueden salir hoy y desbloquean dos pendientes.

---

## Sesión 2026-08-03 (cont. 2) — T-16 cerrado

**Estado inicial:** `T-16` era el único pendiente que dependía de una decisión
del usuario. Preguntó qué problema le generaría a él en particular, y observó
que difícilmente alguien tendría el enlace.

### Decisiones tomadas

| # | Decisión | Fundamento |
|---|---|---|
| D-78 | `internal/` y `data/raw/` **se mantienen** en el repositorio público | El riesgo es bajo y documentar la incertidumbre es lo que hace auditable al proyecto. Purgar el historial es desproporcionado para esta exposición |
| D-79 | La documentación pasa a declarar la exposición, no a negarla | El defecto real no era de seguridad sino de coherencia: `internal/README.md` decía «NO PUBLICAR» y estaba publicado |
| D-80 | Se declaran las tres condiciones que obligarían a revisar D-78 | Una decisión sin criterio de revisión se convierte en inercia |

### Archivos modificados

```
internal/README.md    reescrito: qué significa «interna» aquí, con el
                      razonamiento y las condiciones de revisión
docs/LAYERS.md        §5 pasa de «limitación abierta» a alcance declarado
README.md             «interna» = fuera del sitio, no secreta
PLAN.md               T-16 cerrado
```

### Hallazgos

- **La premisa «nadie tiene el enlace» no se sostiene** para un repositorio
  público: el buscador de GitHub indexa su contenido, Google indexa las páginas
  de GitHub, y el sitio publicado sale del mismo repositorio. Lo que sí es
  cierto es que hoy la probabilidad de que alguien lo busque es baja: la
  exposición no depende de guardar un secreto, sino de que a nadie se le ocurra
  mirar.
- **El riesgo personal está mal ordenado si se pone la privacidad primero.** El
  único con consecuencia práctica es Elsevier, y sería un aviso de retirada
  dirigido a la cuenta del propietario, no a la universidad. Las colas de
  identidad, en cambio, hacen que el proyecto se vea más riguroso, no menos.
- **Lo único que sí era un defecto era la contradicción**: un archivo que
  declara «NO PUBLICAR» dentro de un repositorio público rompe la premisa sobre
  la que se construyó todo lo demás, que es decir exactamente lo que se hace.

### Supuestos descartados durante la sesión

| Supuesto | Qué pasó |
|---|---|
| «La opción correcta es purgar el historial» | **Desproporcionado.** Revisado el riesgo real, la opción correcta es declarar la exposición y fijar cuándo revisarla |
| «Publicar las colas de identidad daña la credibilidad del proyecto» | **Al revés.** Documentar dudas en vez de esconderlas es lo que lo hace auditable |

### Ambigüedades abiertas

Ninguna que dependa del usuario. Queda abierta con Elsevier la redistribución de
`data/raw/`, que no es una decisión de este proyecto.

### Próximo paso recomendado

Sin cambios: enviar las dos hojas de validación y trabajar `make revision`.

---

## Sesión 2026-08-03 (cont. 3) — API de ORCID

**Estado inicial:** el usuario pidió implementar la API de ORCID. Antes de
escribir nada se comprobó qué permite y qué es alcanzable.

### Decisiones tomadas

| # | Decisión | Fundamento |
|---|---|---|
| D-81 | El conector **verifica** asignaciones existentes; no las crea ni las reescribe | `authors_orcid.csv` guarda de dónde vino cada dato. Machacarlo borraría la procedencia; la verificación va en un archivo aparte |
| D-82 | Las credenciales se leen del entorno y de ningún otro sitio | El repositorio es público: una credencial en un archivo versionado queda expuesta en el mismo commit |
| D-83 | `no_verificable` y `sin_coincidencia` son categorías distintas | La primera es ausencia de evidencia; la segunda, evidencia en contra. Fundirlas convertiría un registro vacío en una acusación |
| D-84 | La autoprueba sin red es obligatoria y corre en CI | El entorno de integración no alcanza la API: sin autoprueba, la lógica se rompería en silencio |

### Archivos creados o modificados

```
src/enrich/orcid_api.py          conector de verificación (nuevo)
docs/ORCID_API_GUIDE.md          guía de ejecución (nuevo)
src/review/build_review.py       columna «Verificado» y señal nueva
.github/workflows/deploy.yml     autoprueba en CI
Makefile                         objetivo `verificar-orcid`
.gitignore, README.md, PLAN.md   caché, índice, T-19
```

### Hallazgos

- **El entorno bloquea `pub.orcid.org` y también `api.crossref.org`.** Sólo pasa
  una lista corta (`api.github.com`, registros de paquetes). Eso confirma que el
  enriquecimiento original nunca pudo correr aquí: lo ejecutó el usuario en su
  máquina, como registra la sesión del 2026-08-01.
- **La API pública de ORCID exige token desde hace años**, pero es gratuito y no
  depende de suscripción institucional: se obtiene registrando un cliente en
  Developer Tools.
- **La verificación no sube la cobertura.** Comprueba las 174 asignaciones
  existentes; no busca ORCID nuevos. Ampliar por búsqueda de afiliación es un
  paso distinto, anotado como `T-19`.
- Muchos ORCID existen **sin obras declaradas**, así que `no_verificable` será
  un resultado frecuente y esperable, no un error.

### Verificación

- Autoprueba de **9 casos** con registros de mentira: todos pasan. Cubre
  extracción de DOI, normalización a minúsculas, registro vacío, obras sin DOI,
  los cuatro veredictos, y que una afiliación de otra institución no se cuente
  como propia.
- Sin credenciales, el script se detiene con instrucciones y no falla a medias.
- La herramienta de revisión se probó con un fixture de verificación construido
  sobre firmas reales de los 89 casos: los seis estados renderizan, y sin el
  archivo la columna muestra «—» en vez de un falso negativo.
- Las tres compuertas en verde; el fixture se retiró antes de commitear.

### Supuestos descartados durante la sesión

| Supuesto | Qué pasó |
|---|---|
| «La API pública de ORCID se consulta sin credenciales» | **Falso.** Exige token, aunque sea gratuito |
| «Un fixture con las primeras firmas del CSV sirve para probar la herramienta» | **Falso.** Esas firmas no están entre los 89 casos; hubo que construirlo con firmas que sí aparecen |
| «Verificar una publicación verifica una identidad» | **Falso.** Confirma que ese artículo es del titular; que dos firmas sean la misma persona sigue siendo conclusión humana |

### Ambigüedades abiertas

- **El contrato de la API no está verificado en vivo** desde este repositorio.
  Los nombres de campo vienen de la documentación. Declarado en la guía §6: si
  la primera ejecución con `--limit 10` falla al leer la respuesta, es ahí donde
  hay que mirar.

### Próximo paso recomendado

Obtener las credenciales gratuitas y ejecutar `--limit 10`. Con eso se confirma
el contrato de la API antes de gastar 174 peticiones.

### Corrección posterior · la guía era el problema

Al intentar ejecutarlo, el usuario copió tres veces el bloque de código de la
guía **incluidas las comillas de cierre de Markdown**, y PowerShell lo trató
como texto literal sin ejecutar nada. No fue un error suyo: la guía entregaba
seis comandos encadenados dentro de un bloque cercado, y en el archivo `.md`
esas comillas se ven como parte del contenido.

| # | Decisión | Fundamento |
|---|---|---|
| D-85 | La ejecución en Windows se hace con un asistente, no copiando comandos | Una instrucción que se puede copiar mal se copiará mal. El script comprueba cada paso y dice qué falló |
| D-86 | El Client Secret se pide oculto y en el momento, nunca por variable de entorno pegada | Pegarlo en una consola lo deja en el historial; en un archivo, en el repositorio. `Read-Host -AsSecureString` no deja rastro |
| D-87 | El `.ps1` se guarda con BOM UTF-8 | PowerShell 5.1 lee un script sin BOM como ANSI y corrompe los acentos |

`scripts/verificar-orcid.ps1` verifica Python, instala dependencias si faltan,
corre la autoprueba **antes** de pedir credenciales —si la lógica está rota, el
problema no son las credenciales—, ejecuta la auditoría si hace falta, y empieza
por 10 peticiones antes de ofrecer las 174.

Comprobado: llaves y paréntesis equilibrados, sin comillas impares, todo el
no-ASCII confinado a comentarios, BOM presente, y el directorio `scripts/` fuera
de `dist/`.

---

## Sesión 2026-08-03 (cont. 4) — Ejecución sin instalar nada

**Estado inicial:** el usuario intentó ejecutar el conector de ORCID. Dos
obstáculos, ninguno suyo.

### Decisiones tomadas

| # | Decisión | Fundamento |
|---|---|---|
| D-88 | Detectar un intérprete es ejecutarlo, no comprobar que el comando exista | Windows instala alias de `python` y `python3` que apuntan a la Microsoft Store y no son Python. `Get-Command` los da por buenos |
| D-89 | La verificación de ORCID puede correr en GitHub Actions, no sólo en local | El proyecto ya ejecuta Python allí. Un equipo administrado por la institución puede tener bloqueada la instalación, y eso no debería impedir el trabajo |
| D-90 | En esa vía las credenciales van a los secretos del repositorio | Cifradas y no legibles ni desde la propia interfaz. Mejor que una consola o un archivo local, no sólo más cómodo |

### Archivos creados o modificados

```
.github/workflows/verificar-orcid.yml   ejecución manual en GitHub (nuevo)
scripts/verificar-orcid.ps1             detección real del intérprete
docs/ORCID_API_GUIDE.md                 §3 con las tres vías
```

### Hallazgos

- **`Get-Command python` da un falso positivo en Windows.** Existe un alias de
  ejecución que responde con un mensaje de error en vez de ser Python. El fallo
  aparecía tres líneas más abajo, dentro de un `Write-Host`, donde ya no se
  entendía de qué venía.
- **Python puede estar instalado fuera del `PATH`.** El script busca ahora las
  rutas donde el instalador oficial lo deja por defecto antes de rendirse.
- **La instalación puede estar bloqueada por la administración del equipo**, y
  ese caso no se resuelve mejorando el mensaje de error. La vía por GitHub
  Actions lo elimina: el trabajo corre donde el usuario sí tiene control.

### Verificación

- YAML válido; 10 pasos en el orden correcto.
- La autoprueba sin red va **antes** de comprobar credenciales y de gastar
  peticiones: si la lógica está rota, el problema no son las credenciales.
- El artefacto se sube con `if: always()`, así que un fallo al guardar en el
  repositorio no pierde el resultado de las consultas.
- El `.ps1`: llaves y paréntesis equilibrados, sin comillas impares, no-ASCII
  sólo en comentarios, BOM UTF-8 presente.

### Supuestos descartados durante la sesión

| Supuesto | Qué pasó |
|---|---|
| «Si `Get-Command python` responde, hay Python» | **Falso.** Es un atajo a la Store que no ejecuta nada |
| «Una guía con los comandos correctos basta» | **Insuficiente.** Se copiaron tres veces con las comillas de Markdown incluidas. Una instrucción que se puede copiar mal se copiará mal |
| «Ejecutar en local es el único camino» | **Falso.** El pipeline ya corre en GitHub; la verificación también puede |

### Ambigüedades abiertas

El contrato de la API de ORCID sigue sin verificarse en vivo. La vía por GitHub
Actions es ahora la más probable para comprobarlo, porque no depende de que el
equipo del usuario permita instalar nada.

### Próximo paso recomendado

Guardar los dos secretos en el repositorio y lanzar el workflow con límite 10.

### Resultado de esa ejecución · el contrato queda verificado

El usuario guardó los secretos y lanzó el workflow con límite 10. Resultado:
**10 de 10 confirmadas**.

| # | Decisión | Fundamento |
|---|---|---|
| D-91 | El contrato de la API de ORCID pasa de supuesto a verificado | 10 de 10 confirmadas prueba que el conector lee bien la respuesta. Era la única incógnita real que quedaba |
| D-92 | Las acciones de los workflows se suben a las que usan Node 24 | GitHub avisa de que `checkout@v4`, `setup-python@v5` y `upload-artifact@v4` corren forzadas sobre Node 24. Un aviso que se repite en cada ejecución acaba tapando uno que sí importa |

Dos lecturas del resultado, y conviene no confundirlas:

- **Se confirma el conector.** Sabe encontrar la lista de obras dentro de la
  respuesta de ORCID. Eso era lo que no se había podido probar desde aquí.
- **Se confirman 10 asignaciones.** Para esas firmas, al menos un DOI atribuido
  aparece en las obras que el propio titular declara. Deja de ser una deducción
  por apellido e inicial.

Lo que **no** se puede concluir: que las 174 vayan a confirmarse. Las 10
primeras son las de mayor respaldo del archivo, así que el sesgo juega a favor.
La cifra real sale de la ejecución completa.

`docs/ORCID_API_GUIDE.md` §6 pasa de declarar el contrato como no verificado a
declararlo verificado, con la fecha y la evidencia.

---

## Cierre · la verificación de ORCID, de extremo a extremo

La ejecución completa corrió sobre las 174 asignaciones. Antes hubo que
arreglar dos fallos del workflow que la ejecución #4 dejó a la vista: terminó
en «success» a los 6 segundos, que para 174 firmas es imposible.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-93 | «Todas» necesita un valor explícito (`0`), no el campo vacío | Un campo vacío hace que GitHub sustituya el `default`. Pedir «sin límite» dejando el hueco en blanco devolvía 10 sin avisar |
| D-94 | Los archivos se añaden al índice uno por uno, comprobando que existan | `git add A B` falla entero si `B` no existe. `orcid_hallazgos.csv` sólo se genera si hay dudosas; sin él, tampoco se guardaba `A` |
| D-95 | El veredicto de ORCID se publica en la ficha de autor | Un ORCID de Crossref es una hipótesis por apellido e inicial. Publicarlo sin su evidencia lo convierte en un hecho sobre una persona con nombre y apellido, contra `<non_negotiable_rules>` |
| D-96 | En el listado se marca sólo la excepción, no la norma | 153 de 174 están confirmadas. Etiquetarlas todas es ruido; la información es la minoría que se sale |
| D-97 | `sin_coincidencia` se publica como «sin confirmar», nunca como «incorrecta» | La evidencia dice que no respalda la asignación, no que la desmienta. La segunda frase es una acusación que los datos no sostienen |
| D-98 | `--cifra` se separa de `--marca` | `--marca` cambia de oficio entre temas: tinta en claro, superficie en oscuro. Un token no puede hacer las dos cosas |

### Resultado

| Veredicto | Firmas | |
|---|---:|---|
| confirmada | 153 | 87,9 % |
| no_verificable | 17 | 9,8 % |
| sin_coincidencia | 4 | 2,3 % |
| sin_registro | 0 | — |

La confianza declarada por el emparejador resulta ser un predictor real:
94,4 % de confirmación cuando decía «alta», 85,0 % cuando decía «media».

Las cuatro sin confirmar: tres son apellidos frecuentes con inicial única que
no declaran afiliación UFT. `Díaz F.` arrastra además tres Scopus Author ID y
la marca de identidad no consolidada — dos señales independientes coincidiendo.
Quedan en `internal/orcid_hallazgos.csv`, sin resolver.

### Supuestos descartados

| Supuesto | Qué pasó |
|---|---|
| «Las 10 primeras eran las de mayor respaldo, el sesgo juega a favor» (escrito en el cierre anterior) | **Falso, y al revés.** `head(10)` toma el orden alfabético del archivo, no un ranking: 9 de esas 10 eran de confianza «media», frente a 69 % en el total. La muestra era algo más débil que la media, y aun así dio 10/10 |
| «El workflow terminó en success, luego hizo su trabajo» | **Falso.** Terminó en success habiendo verificado 10 y sin guardar nada. Un `success` sólo dice que ningún paso devolvió error |
| «La paleta está revalidada, luego los colores del sitio están bien» | **Insuficiente.** El fallo de las cifras en modo oscuro no está en la paleta: los dos valores son correctos por separado y sólo el uso los enfrenta |
| «Mi medición de contraste es de fiar» | **No lo era.** El primer barrido dio 64 fallos y 62 eran del instrumento: no componía fondos translúcidos, leía `color(srgb 0.21 …)` como enteros y daba por transparente la cabecera en degradado |

### Archivos modificados

`.github/workflows/verificar-orcid.yml`, `src/build/03_authors.py`,
`web/assets/js/paginas.js`, `web/assets/css/app.css`,
`docs/AUTHOR_PROFILE.md`, `docs/UX_UI.md`.
Generados por la ejecución: `data/enriched/orcid_verificacion.csv`,
`internal/orcid_hallazgos.csv`.

### Ambigüedades abiertas

Las cuatro asignaciones sin confirmar. La evidencia disponible no distingue
entre «es otra persona con la misma firma abreviada» y «es la misma persona con
el registro de ORCID incompleto». `De la Fuente M.` es el caso más favorable a
la segunda lectura: declara afiliación UFT y sólo tres obras con DOI.

### Próximo paso recomendado

Resolver esas cuatro en `make revision`, junto con los 89 casos de identidad
que ya esperaban. Es la misma clase de decisión y la misma herramienta.

---

## Cierre · ampliación de cobertura de ORCID y auditoría

Se pidió llevar la cobertura de ORCID al 100 % de los autores. Se llegó al
37,7 %, se agotaron las vías legítimas y se documentó por qué el 100 % no es
alcanzable sin inventar datos.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-99 | `orcid_api.py` fusiona en vez de sobrescribir | Escribir sin mirar convertía cualquier ejecución parcial en pérdida de datos, y era el camino por defecto del workflow |
| D-100 | Tres vías de cobertura, una sola regla de emparejamiento, importada | Dos copias de una regla que la documentación presenta como una sola divergen en cuanto alguien corrige una |
| D-101 | La búsqueda por afiliación NO publica | Ancla la asignación sólo en el nombre. Sin publicación compartida, dos homónimos de la misma universidad son indistinguibles |
| D-102 | Un desacuerdo entre Crossref y el registro se encola, no se resuelve | Uno de los dos está equivocado y cuál no se decide mirando nombres |
| D-103 | Las asignaciones halladas por `doi-self` dicen «declarado por el titular», no «verificado» | Su veredicto `confirmada` es circular: se las encontró justamente por declarar el DOI |
| D-104 | Los recuentos agregados se cuentan por etiqueta, no por veredicto | Contar por veredicto inflaría las verificaciones independientes con comprobaciones circulares |
| D-105 | La clase visual viaja aparte del veredicto | Un mismo veredicto merece dos tratamientos según de dónde venga la asignación |

### Resultado

Cobertura **174 → 222 de 589** (29,5 % → 37,7 %). Por etiqueta: 153 verificado,
48 declarado por el titular, 17 no verificable, 4 sin confirmar.

Entre las firmas con diez o más publicaciones la cobertura llega al **93,3 %**.
419 de 589 firmas tienen una sola publicación, y ahí la cobertura es del 26,3 %.

La herramienta de revisión pasa de 89 a **110 casos**.

### Supuestos descartados

| Supuesto | Qué pasó |
|---|---|
| «Un `--limit` pequeño es una prueba inofensiva» | **Falso.** Sobrescribía el archivo completo. El default del workflow era 10, así que el camino por defecto destruía 164 filas |
| «Si el veredicto dice `confirmada`, está verificado» | **Falso para las 48 nuevas.** Se las encontró por declarar el DOI, así que el veredicto repetía la primera comprobación en vez de añadir una segunda |
| «Ampliar cobertura es acercarse al objetivo» | **Sólo si la evidencia acompaña.** Un ORCID equivocado en la ficha de una persona real es peor que un hueco declarado: el hueco se ve, el error no |
| «Generar la cola es entregar el trabajo» | **No.** 20 candidatos y 2 desacuerdos quedaban en CSV que nadie abre hasta que entraron en `make revision` |

### Archivos creados

`src/enrich/orcid_expand.py`, `src/enrich/orcid_afiliacion.py`,
`docs/ORCID_COVERAGE.md`, `.github/workflows/ampliar-orcid.yml`.

### Ambigüedades abiertas

- Las 4 asignaciones sin confirmar. `De la Fuente M.` gana evidencia a favor: el
  titular declara la universidad y una segunda variante de firma apunta al mismo
  ORCID. Sigue sin resolverse porque los DOI no coinciden.
- Los 2 desacuerdos entre fuentes (`Castro M.`, `Elorrieta V.`).
- Los 20 candidatos por afiliación, de los que 18 son coincidencia 1-a-1.
- `Giordanino E.` y `Giordanino E.F.`: mismo ORCID por afiliación y mismo Scopus
  Author ID. Es la fusión de variantes mejor respaldada del proyecto, y aun así
  la decide una persona.

### Próximo paso recomendado

Abrir `make revision` y resolver los 110 casos. Cada decisión que confirme un
candidato por afiliación sube la cobertura publicable sin relajar el criterio,
que es la única vía que queda para acercarse más al 100 %.

---

## Cierre · aplicación de la revisión humana de identidad

El propietario revisó los 110 casos y exportó `internal/identity_decisions.csv`:
52 resueltos, 58 pendientes. Se aplicaron.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-106 | Las decisiones se aplican por un script con autoprueba, no a mano | Una fusión mal transcrita no se distingue de una decidida |
| D-107 | Un conjunto de decisiones contradictorio detiene la aplicación | Aplicar una contradicción deja el resultado sin significado y sin aviso |
| D-108 | La forma canónica se elige por frecuencia, con la tilde del apellido por delante | Ordenar por longitud desempataba alfabéticamente, y en español eso publica la variante sin tilde |
| D-109 | La tilde de la INICIAL no decide | Que el nombre de pila lleve tilde no se deduce de la fuente |
| D-110 | Las fichas de la corrida anterior se borran antes de escribir | Al consolidar cambian los slugs y quedaban huérfanas con datos viejos |
| D-111 | Cada ficha fusionada declara qué firmas la componen, y el buscador las encuentra por cualquiera | Sin eso, quien llegue desde Scopus con «Giglio A.» no encuentra sus publicaciones |
| D-112 | Entre varias variantes con ORCID gana la evidencia más fuerte, no la última fila | La etiqueta dependía del orden de ordenación del archivo |
| D-113 | Los candidatos por afiliación confirmados se publican con `fuente = revisión humana` | Lo que les faltaba era el juicio de una persona, y es lo que aporta el archivo |

### Resultado

**589 → 556 entidades publicadas**: 526 formas de firma sin revisar más 30
personas en las que se fusionaron 63 variantes.

**Cobertura de ORCID 216 de 556 (38,8 %)**: 139 verificado, 43 declarado por el
titular, 15 confirmado por revisión, 16 no verificable, 3 sin confirmar.

### Hallazgos

- **Las 22 personas consolidadas que traían ORCID desde más de una variante
  coinciden todas en el mismo identificador.** Dos vías independientes llegando
  al mismo sitio: es corroboración de que las fusiones son correctas.
- **La consolidación resolvió una de las 4 asignaciones sin confirmar.**
  `Diaz F.` declaraba 3 DOI coincidentes y `Díaz F.` ninguno: la marca era un
  artefacto de tener una persona partida en dos firmas. Quedan 3.

### Supuestos descartados

| Supuesto | Qué pasó |
|---|---|
| «Ordenar por longitud elige la mejor forma canónica» | **Falso.** A igualdad de longitud el desempate alfabético publicaba `Núnez-Lisboa M.` teniendo `Núñez-Lisboa M.` |
| «`make sitio` deja el sitio consistente» | **Falso.** No borraba las fichas previas: 610 archivos para 556 firmas, 54 con datos de antes de la revisión |
| «Las cifras del sitio se actualizan solas» | **Falso.** La nota del KPI decía 589 junto a un 556, y la advertencia afirmaba que sin ORCID no es posible consolidar justo después de consolidar 30 grupos |
| «Indexar por nombre canónico basta» | **Insuficiente.** Ganaba la última fila del CSV: qué evidencia se enseñaba dependía del orden del archivo |

### Ambigüedades abiertas

58 casos pendientes, entre ellos los 20 de «Varios Scopus ID», el grupo
`De la Fuente` —que mezcla `de la Cruz P.S.`, claramente otra persona— y los
2 desacuerdos entre fuentes. Sobre `Elorrieta V.`: la decisión «personas
distintas» dice que los dos identificadores no son la misma persona, pero no
cuál corresponde a la firma UFT. La pregunta estaba mal planteada por la
herramienta y hay que rehacerla.

### Próximo paso recomendado

Rehacer en la herramienta la pregunta de los desacuerdos: no «misma o distinta
persona» sino «cuál de los dos identificadores es el correcto».

---

## Cierre · rediseño de interfaz, identidad roja y pre-renderizado

Tres encargos en una sesión: cambiar la identidad cromática a rojo, rehacer la
interfaz tomando como referencia portales bibliométricos reales de educación
superior, y pre-renderizar el sitio.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-114 | La identidad pasa a roja, diseñada por medición, y NO se declara oficial de la UFT | `finis.cl` y los directorios de marca responden 403. Un hex inventado presentado como institucional es exactamente lo que `<non_negotiable_rules>` prohíbe |
| D-115 | Cambiar el color del dato es seguro porque el sitio usa un solo color de dato | Medido antes de tocar nada. Si hubiera una paleta categórica en uso, el cambio habría obligado a revalidar el conjunto entero |
| D-116 | La superficie oscura pasa de pizarra fría a pizarra cálida | Un rojo sobre fondo azulado se lee sucio: el fondo tira del tono al magenta |
| D-117 | Cada token se declara UNA vez con `light-dark()` | La paleta oscura estaba escrita tres veces y las tres copias podían separarse sin que nada avisara |
| D-118 | `--boton-tinta` se separa del blanco literal | El botón primario llevaba `#fff` fijo: 7,67:1 en claro y 2,84:1 en oscuro. Es el mismo fallo que obligó a crear `--cifra`, con otra cara |
| D-119 | La segunda ranura categórica SÍ está en uso y ahora está validada como par | La documentación afirmaba que ningún módulo pedía `escala: 'serie'`. Era falso: `anillo()` la pide siempre |
| D-120 | La tabla equivalente deja de estar detrás de un desplegable y pasa a ser la segunda vista | La figura resume; la tabla es la que se cita. Es el patrón del Leiden Ranking: misma serie, varias representaciones, elige el lector |
| D-121 | Sin JavaScript se muestran LAS DOS vistas, no ninguna | La tabla es la vía equivalente al gráfico, no un extra. El conmutador sólo existe bajo la clase `js`: un control que no conmuta nada es una promesa falsa |
| D-122 | Índice lateral fijo con scroll-spy en las páginas de sección | Patrón del panel de entidades de SciVal. En una página de cinco indicadores largos, poder ver qué hay y saltar es la diferencia entre consultar y leer en orden |
| D-123 | El titular de portada lleva TRES indicadores y esos tres BAJAN de la rejilla | Un indicador repetido a cuatro centímetros de sí mismo no gana énfasis, lo pierde |
| D-124 | El titular arrastra el denominador y la referencia de cada cifra | Un 0,87 de FWCI sin el «1 = promedio mundial» al lado no es un titular, es un número suelto |
| D-125 | La cabecera es fija sólo a partir de 900 px | En un teléfono ocupa tres filas: fijarla se comía un tercio de la pantalla en cada desplazamiento |
| D-126 | El marcado se construye en `vista.js`, sin tocar el DOM | Es la condición para que el navegador y el build produzcan lo mismo. Sin eso, pre-renderizar significa mantener dos versiones del marcado |
| D-127 | El pre-renderizado NO alcanza a `publicaciones.html` ni `autor.html` | Dependen del estado del usuario. No hay estado inicial único que sirva, y emitir uno arbitrario sería inventar una vista |
| D-128 | Node es requisito blando del build, con aviso en voz alta | Sin Node el sitio se ensambla y funciona igual mientras haya JavaScript. Abortar sería desproporcionado; callarlo dejaría un sitio peor sin que nadie lo notara |
| D-129 | El lienzo de un gráfico de barras verticales se ajusta al número de categorías | Tres años estirados a lo ancho de una tarjeta se leen como «poco dato», que es una impresión y no una medición |

### Referencias consultadas

Portales de análisis bibliométrico de instituciones de educación superior, para
tomar patrones con razón detrás y no apariencias. Detalle y qué se descartó, en
`docs/UX_UI.md` §13.

- CWTS Leiden Ranking (ediciones Tradicional y Abierta): vistas lista / gráfico
  / mapa sobre la misma serie; intervalos de estabilidad al 95 % por
  bootstrapping; sección «Responsible use» de primer nivel.
- SciVal, módulo *Overview*: panel de entidades fijo a la izquierda; el resumen
  agrupado en *Overall Research Performance*, *Research Topics* y *Performance
  Indicators*.
- Perfiles institucionales tipo Pure: resumen, línea de tiempo de producción,
  conceptos frecuentes y mapa de colaboración.
- Convenciones de tablero analítico: cifras tabulares alineadas a la derecha,
  rejilla recesiva, divulgación progresiva, «la figura resume, la tabla es la
  verdad».

### Resultado

| Medida | Antes | Después |
|---|---|---|
| LCP `index` (Slow 4G, mediana de 5) | 1.940 ms | **780 ms** |
| LCP `impacto` | 1.764 ms | **784 ms** |
| LCP `tematica` | 1.300 ms | **756 ms** |
| `impacto.html` sin JavaScript | 0 módulos, 99 caracteres | 5 módulos, 5 gráficos, 5 tablas, 2.847 caracteres |
| Contraste WCAG, 9 páginas × 2 temas | 0 fallos | **0 fallos** |
| Desborde horizontal en 430 px | — | **0 px** |
| CSS | 41,9 KB | 51,4 KB (15,2 KB gzip) |
| JavaScript | 61,0 KB | 72,1 KB (23,7 KB gzip) |

### Supuestos descartados

| Supuesto | Qué pasó |
|---|---|
| «Ningún módulo pide escala de serie» | **Falso.** `anillo()` la pide siempre. La segunda ranura llevaba dibujándose desde el principio, sin validar |
| «El pre-renderizado no mejoró el LCP» | **Falso, y el error era mío.** El primer `PerformanceObserver` resolvía en la primera entrada en vez de esperar a la última: medía un candidato temprano, no el LCP. Corregido, la mejora es de 43–59 % |
| «El rojo institucional se puede averiguar» | **No en esta sesión.** 403 en `finis.cl` y en los directorios de marca. Queda como token pendiente de sustituir |

### Ambigüedades abiertas

El hex oficial de la Universidad Finis Terrae sigue sin verificar. Todo el
sistema cromático cuelga de `--marca` y sus derivados, así que sustituirlo es
cambiar cuatro tokens y volver a correr el barrido de contraste; pero mientras
no se verifique, el rojo publicado es **un rojo diseñado**, no *el* rojo de la
institución, y así está declarado en la hoja de estilo y en `docs/UX_UI.md`.

El presupuesto de JavaScript (60 KB en bruto) queda **excedido en 12,1 KB**. No
se resolvió: se declara. El 28 % del archivo es comentario en prosa, que este
proyecto trata como parte del entregable, y con el sitio pre-renderizado el
JavaScript ya no está en la ruta crítica de pintado. Si se quiere respetar el
techo literal, la decisión a tomar es si se minifica en el build —lo que separa
lo que se lee en el repositorio de lo que se sirve— o si se sube el techo.

### Próximo paso recomendado

Pedir a la institución el valor oficial de su rojo y sustituir los cuatro tokens
de marca.

Del encargo original de interfaz queda pendiente **menos de lo que se anotó en
una primera versión de esta nota**. La auditoría posterior comprobó, ejerciendo
la interfaz en un navegador, que dos de los cuatro «pendientes» ya estaban
implementados y funcionando:

- **Estado en la URL**: sí existe. `leerURL()` y `history.replaceState` en
  `paginas.js`; el filtro sobrevive a la recarga y la URL es compartible.
- **Exportación**: sí existe. Botón «Exportar CSV» que exporta *lo filtrado*, no
  el universo, con BOM UTF-8 y la fecha de build en el nombre del archivo.

Queda de verdad: **panel conceptual por sección** —un texto que explique qué
pregunta responde cada eje antes de los indicadores— y **catálogo de
indicadores** —una vista que liste los 20 indicadores con su definición, fuente,
denominador y estado de factibilidad, hoy repartidos entre `metodologia.html` y
los sellos—.

---

## Cierre · sistema de diseño generado para Claude Design

Se abrió el PR #26 con el rediseño y se construyó el paquete de sistema de
diseño para sincronizar con `claude.ai/design`.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-130 | El sistema de diseño se GENERA desde la hoja, los constructores y los datos reales | Documentado a mano, empieza siendo verdad y deja de serlo en la primera corrección que nadie replica en la ficha |
| D-131 | Las razones de contraste de las fichas se calculan al generar, no se copian | Una tabla copiada se desactualiza en silencio; un cálculo no |
| D-132 | Los componentes se enseñan con datos reales del informe, no de relleno | Un componente de bibliometría ilustrado con cifras inventadas contradice las reglas del proyecto incluso en una ficha de diseño |
| D-133 | Cada ficha muestra los dos temas mediante `color-scheme` en contenedores hermanos | `light-dark()` resuelve según el elemento donde se sustituye la variable, no según la raíz. Permite comparar sin duplicar la paleta |
| D-134 | El cuerpo de una ficha se evalúa una vez POR PANEL | Inyectar la misma cadena en los dos duplicaba los `id` del SVG, y los patrones de trama se referencian por id |
| D-135 | Cada regla se ilustra con el indicador que de verdad la cumple | La ficha de codificación usaba P-07 para enseñar la trama, y P-07 no es multivaluado. Ponérsela habría sido afirmar algo falso sobre el indicador |
| D-136 | `design-system/` no se versiona | Salida derivada, igual que `dist/`. Cada regeneración sería un diff de un megabyte de HTML generado |

### Resultado

16 fichas —3 de fundamentos, 9 de componentes, 4 de gráficos—, verificadas en
navegador: 0 excepciones, 0 fichas con problema, los dos paneles de tema
resuelven a fondos distintos en las 16, y 0 identificadores duplicados tras la
corrección.

### Ambigüedad abierta

La sincronización **no se pudo ejecutar desde esta sesión**: `DesignSync` exige
autorización de sistema de diseño y `/design-login` necesita una terminal
interactiva, que un contenedor remoto no tiene. El paquete queda listo; falta
conectarlo desde Claude Design («Send to Claude Code Web») o desde Claude Code
en una máquina local. El skill `/design-sync` tampoco está habilitado en la
cuenta.

### Próximo paso recomendado

Fusionar el PR #26 para que el rediseño se publique —hoy el sitio en línea sigue
sirviendo la versión anterior— y conectar Claude Design por cualquiera de las
dos vías para empujar el paquete.

---

## Cierre · la verificación deja de ser efímera, y encuentra un fallo real

Las comprobaciones del rediseño vivían en el scratchpad de la sesión, que se
borra al terminar. Se trasladaron a `src/verify/` y `src/design/`, con dos
comandos nuevos: `make verificar` y `python3 src/design/validar_paleta.py`.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-137 | La batería de verificación vive en el repositorio, no en un directorio temporal | Una verificación que hay que reescribir en cada sesión no se corre; y una reescrita de memoria no es la misma. La versión anterior del barrido medía la ficha de autor con el parámetro equivocado y llevaba semanas dando «0 fallos» sobre una página vacía |
| D-138 | `run_all.mjs` levanta y baja su propio servidor | Una comprobación que exige recordar arrancar algo a mano acaba no corriéndose |
| D-139 | La resolución de Playwright y de Chromium se centraliza en `navegador.mjs` | Seis guiones llevaban incrustada la ruta del navegador del contenedor: ciertas aquí, falsas en cualquier otra máquina. La verificación no era replicable, que es justo lo que el proyecto exige de todo lo demás |
| D-140 | El validador de paleta LEE los tokens de `app.css`, no los repite | Una tabla copiada es una fotografía; el instrumento se puede volver a correr. El día que llegue el rojo institucional oficial es cambiar cuatro valores y un comando |
| D-141 | `--aviso-borde` en oscuro sube de `#c8901a` a `#f0b429` | Ver abajo |
| D-142 | `rendimiento.mjs` queda fuera de la batería | Cinco corridas por página contra dos servidores tarda minutos. Se corre a mano cuando se toca algo que pueda afectarlo |

### El fallo que encontró en su primera ejecución

`--aviso-borde` en tema oscuro era `#c8901a`, **un resto de la paleta teal que
sobrevivió al cambio de identidad sin que nadie lo mirara**. Contra un dato teal
la separación sobraba; contra un dato rojo caía a **ΔE 17,9**, bajo el piso de
20 que este mismo proyecto declara.

Peor: la cifra publicada en `docs/UX_UI.md` y en la hoja decía 21,2 y estaba
medida contra `#d9a520` —que era `--aviso-tinta-grafico` de la paleta anterior y
**ya no existe en la hoja**—. La documentación afirmaba que el sistema cumplía
midiendo contra un color que no se dibuja.

Corregido a `#f0b429`: ΔE 24,1, contraste 9,94:1 sobre la tarjeta y 8,53:1 sobre
el fondo de aviso. Las cifras de la documentación se rehicieron contra el par
que de verdad se dibuja junto —`--serie-1` contra `--aviso-borde`, barra de dato
contra línea de referencia—: 25,1 en claro y 24,1 en oscuro.

### Supuestos descartados

| Supuesto | Qué pasó |
|---|---|
| «El ámbar no hizo falta moverlo al cambiar el rojo» | **Falso.** Sí hacía falta, y no se movió. La medición que lo justificaba usaba un color de la paleta anterior |
| «Las cifras de la documentación reflejan la hoja» | **No necesariamente.** Una tabla escrita a mano y una hoja de estilo se separan sin que nada avise. Por eso ahora hay un instrumento |

### Próximo paso recomendado

Fusionar el PR #26. Después, en una sesión nueva partiendo de `STATE.md`:
conectar Claude Design, o abordar los dos pendientes reales de interfaz —panel
conceptual por sección y catálogo de indicadores—.

---

## Cierre · cuatro fichas publicadas que no son personas

`STATE.md` publicaba las cifras de autor sobre la base anterior a la
consolidación —589 formas de firma y 240 con ORCID— mientras el sitio servía 556
entidades y 216. Se corrigió el generador para que cada cifra declare su base.
Al declararlas apareció una tercera: «pares autor × publicación» eran filas del
log, y tres de ellas eran la misma firma repetida en una publicación. Esa firma
era `School of Psychology`, y tirando de ahí salieron otras tres.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-143 | Cada cifra de `STATE.md` declara su base, y las de autor publican las dos | Ninguna era falsa; lo falso era presentarlas sin decir cuál era cuál. La que llegaba al punto de entrada del proyecto era justo la que el sitio no usa |
| D-144 | La base consolidada se LEE de `data/processed/authors.json`, no se recalcula | Recalcularla sería una segunda implementación de la consolidación, y dos implementaciones divergen sin avisar. Si no coinciden, es que el build no se ha corrido, y eso se ve en la fecha |
| D-145 | Las firmas sin forma de persona se detectan con tres señales que NO pesan igual | Dos son invariantes de la fuente —posición fuera de rango, firma repetida en un trabajo— y no admiten lectura benévola. La tercera, no llevar inicial, es heurística de forma: aquí aísla los mismos cuatro casos, pero en otra institución marcaría a un autor mononímico, que es una persona real |
| D-146 | La regla se numera `E-09`, no `P-06` | `P-06` ya es el indicador al que esta regla afecta. Dos cosas distintas con el mismo código se confunden justo donde más importa no confundirlas |
| D-147 | El descarte se aplica en `src/build/`, nunca sobre `internal/matching_log.csv` | `I-01` es bloqueante y se calcula sobre el log. Las cuatro firmas son la ÚNICA detección de su publicación: quitarlas del log dejaría a esas publicaciones sin ninguna y abortaría la auditoría entera |
| D-148 | `P-06` sigue publicando 556 y declara que 552 tienen forma de persona | Declarar que una firma no es una persona es una decisión de identidad, y `D-08` la reserva a la revisión humana. Publicar 552 por decisión del pipeline sería resolverla por él |
| D-149 | La cola «Firma sin forma de persona» trae su propio vocabulario de veredicto | «Misma persona / personas distintas» no significa nada sobre una firma sola. Un botón que no significa nada se pulsa igual |
| D-150 | La nota de `P-06` vive en `common_build.py`, no en cada consumidor | Ya había divergido: la portada servía el texto construido con las cifras del momento y la página de autores el estático de `config/indicators.yml`. Dos notas para un indicador es una de más |

### Lo que apareció al declarar las bases

`School of Psychology` ocupaba tres posiciones de la misma publicación. Buscando
la clase entera aparecieron `and Senior Lecturer` —posición 9 de 7 autores—,
`Metabolism` y `Movement Sciences (NUTRIM)`. Las cuatro tienen ficha pública y en
las cuatro publicaciones donde aparecen **son la única detección UFT**: esas
publicaciones se quedan sin autoría UFT nombrada.

Los dos invariantes atrapan dos de las cuatro. La señal de forma —ninguna
inicial con punto— aísla las cuatro y sólo esas cuatro sobre 589 firmas.

### Supuestos descartados

| Supuesto | Qué pasó |
|---|---|
| «Los invariantes estructurales bastan para detectar la clase» | **Falso.** Atrapan 2 de 4. `Metabolism` está en la posición 3 de 6 y `Movement Sciences (NUTRIM)` en la 8 de 14: la fuente no se contradice, simplemente el nombre no es un nombre |
| «Basta con encolarlas» | **No.** Sin veredicto propio ni camino de aplicación, la herramienta habría recogido un botón que `apply_decisions.py` ignoraba en silencio. Peor que no ofrecerlo |
| «Excluirlas es quitarlas del log» | **Falso, y rompía el build.** `I-01` habría pasado de 0 a 4 fallos bloqueantes |

### Ambigüedades abiertas

- Las cuatro firmas siguen publicadas y con ficha. El descarte lo decide una
  persona en `make revision`; el ensayo del bucle completo se hizo y se
  revirtió.
- Cinco publicaciones sólo-SciVal ya salen hoy con la celda de autoría en
  blanco (discrepancia `X-01`, sin lista de autores en Scopus). Tras un descarte
  se les sumarían estas cuatro. Un lector no distingue «sin autoría UFT
  nombrada» de «no se muestra»: falta rotularlo, y es decisión de interfaz.
- `docs/ORCID_COVERAGE.md` sigue en la base previa a la revisión (222/589).

### Próximo paso recomendado

Abrir `make revision` y resolver los cuatro casos de la cola nueva. Después, el
catálogo de indicadores.

---

## Cierre · el review encontró que el arreglo anterior no cerraba

Se pasó `/code-review` al PR #27 antes de fusionarlo. Salieron 15 hallazgos, y
los graves no eran de estilo: tres publicaban cifras equivocadas y uno rompía
una regla no negociable de `CLAUDE.md`.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-151 | «Sí es una persona» se registra igual que «no es una persona» | La auditoría vuelve a marcar la firma en cada corrida —se calcula sobre el log, que no se toca—, así que sin registrar la confirmación el veredicto no tenía ningún efecto y la única salida que el sistema ofrecía era declarar inexistente a la firma |
| D-152 | Lo publicado dice «probables», no «no son personas» | Dos de las cuatro sólo disparan la señal heurística, sobre la que el propio código escribe que sola no basta. Publicarlo como hecho es convertir hipótesis en hecho, que `<non_negotiable_rules>` prohíbe |
| D-153 | La segunda lectura desde `internal/` se declara en el docstring y en `docs/LAYERS.md` | `05_verify_public_layer.py` comprueba nombres de campo en las salidas, no de dónde se leyó cada dato. Una lectura nueva no la detecta nada automático: o es una decisión escrita o es una fuga esperando |
| D-154 | Las publicaciones afectadas se cuentan por columna estructurada, no buscando un literal en la prosa | La regla contaba con `str.contains("ÚNICA detección")` sobre una frase escrita para humanos. Reescribir la frase —que es justo lo que pedía `D-152`— habría puesto la cifra a cero y publicado un «0» tranquilizador sobre el hecho que la regla existe para sacar a la luz |
| D-155 | El YAML generado se entrecomilla con `yaml.safe_dump`, no con `repr()` de Python | `repr()` acierta casi siempre y falla con una nota que lleve las dos comillas. `DESCARTADAS` se evalúa al importar `common_build`: un archivo mal escrito no da un error localizado, mata todos los objetivos del build a la vez |
| D-156 | «Única detección UFT» se evalúa publicación a publicación | Sobre la unión, una firma que acompañara a alguien en cualquier trabajo silenciaba el aviso para todos los demás |

### Los tres que publicaban cifras falsas

| Dónde | Qué habría publicado |
|---|---|
| `snapshot.py` | Restaba las marcadas a un total que ya las excluía: **548 donde son 552** |
| `03_authors.py` | La advertencia dejaba de cuadrar al descartar: decía «de las 589, 63 se fusionaron… las 522 restantes», y 589 − 63 = 526 |
| `build_review.py` | El HTML comprometido traía la redacción anterior a la corrección de concordancia: la cola y la pantalla del revisor no decían lo mismo |

### Supuestos descartados

| Supuesto | Qué pasó |
|---|---|
| «El ensayo de punta a punta validó el bucle» | **No.** Comprobé `kpis.json` tras el descarte, pero no la advertencia de `authors.json`, y nunca corrí `make estado` con firmas descartadas. Los tres fallos vivían justo ahí |
| «Añadir el botón basta para que el veredicto exista» | **Falso.** Sin camino de aplicación, «sí es una persona» era decorativo |

### Ambigüedades abiertas

Quedan sin arreglar, declarados y verificados, cuatro hallazgos latentes: el
filtro de redundancia de bases sí se corrigió, pero siguen abiertos los casos
`E-09` sin perfil asociado (se avisa, no se bloquea) y la ausencia de una
comprobación automática de que ninguna lectura nueva desde `internal/` entre sin
declararse.

### Próximo paso recomendado

Fusionar el PR #27. Después, validación de PR en CI.

---

## Cierre · la compuerta deja de correr sólo después de fusionar

`deploy.yml` disparaba en `push` a `main` y en `workflow_dispatch`, y nada más.
Ningún pull request se validaba antes de entrar: el primero que rompiera una
regla bloqueante lo habría hecho sobre la rama publicada. El PR #27, sin ir más
lejos, se fusionó con la única garantía de dos verificaciones a mano.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-157 | El job de construcción y verificación corre también en `pull_request`; sólo la publicación queda atada a `main` | Verificar después de fusionar es enterarse tarde. La compuerta es la misma; lo que cambia es cuándo actúa |
| D-158 | Las corridas de pull request se cancelan entre sí por rama; los despliegues se serializan y nunca se cancelan | De tres empujones seguidos a una rama sólo interesa el veredicto del último. Interrumpir una publicación a medias, en cambio, deja el sitio en un estado que nadie eligió |
| D-159 | Los permisos de escritura sobre Pages bajan de la cabecera a cada job | Estaban arriba, así que las corridas de validación —que no publican nada— cargaban con permiso para publicar |
| D-160 | La versión de Playwright se fija en el workflow, no en un `package.json` | El sitio no tiene dependencias de JavaScript y no va a tenerlas por una herramienta de prueba. Se fija la misma que se usa en local: una batería que corre contra otro navegador no comprueba lo mismo |
| D-161 | CI invoca `src/verify/run_all.mjs` directamente, no `make verificar` | El objetivo depende de `sitio` y reconstruiría todo desde la auditoría. En CI `dist/` ya está construido, y es ese `dist/` el que hay que verificar, no otro levantado a su lado |
| D-162 | La autoprueba de `apply_decisions` entra en CI | Es la lógica que decide qué firmas se fusionan como una persona y cuáles dejan de contarse por no serlo. Tenía 20 casos y no la ejercía nada automático |

### Lo que ahora corre en cada pull request

Pipeline completo, las cinco autopruebas, la comprobación de contenido sin
JavaScript, la barrera pública/interna y la batería de `src/verify/` —contraste
WCAG, estructura, consola, flujos, responsive e higiene—. La secuencia entera se
ensayó en local, en el mismo orden que el workflow, antes de escribirla.

### Ambigüedades abiertas

- `make rendimiento` sigue fuera de CI por `D-142`: cinco corridas por página
  contra dos servidores tarda minutos. Queda declarado, no resuelto.
- Nada comprueba que el workflow siga cubriendo lo que dice cubrir. Si mañana
  alguien añade un guion a `src/verify/`, entra solo —`run_all.mjs` los
  enumera—, pero una autoprueba nueva en otro módulo hay que acordarse de
  añadirla aquí.

### Próximo paso recomendado

Abrir el PR y comprobar que el disparador nuevo se ejecuta sobre él: es la
primera vez que este repositorio valida un pull request antes de fusionarlo, y
esa corrida es la prueba de que el cambio funciona.

---

## Cierre · lo que salió de revisar el PR de CI

Tres cosas que se decidieron durante la revisión del PR #28, después de que el
cierre anterior estuviera escrito. Se registran aparte porque `docs/DECISIONS.md`
se genera desde estas tablas: lo que no está aquí no existe para ninguna sesión
que arranque por `STATE.md`.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-163 | `id-token: write` sale del job `construir`; `pages: write` se queda | El primero no lo usaba nadie ahí: lo pide `deploy-pages`, que vive en `desplegar` y ya lo tiene. El segundo lo pide `configure-pages`, que sí vive en `construir`, y mover ese paso era imposible: `upload-pages-artifact` sube `dist/`, que sólo existe en ese job. Habría que pasar el sitio entero entre jobs para ahorrar un permiso que ninguna corrida de PR ejerce |
| D-164 | `setup-node` sube de `@v4` a `@v5` | Era la única de las siete acciones fuera de su major vigente, y la había fijado esta misma línea de trabajo al añadir Node para el pre-renderizado mientras el resto ya estaba al día por `D-92` |
| D-165 | La mitad restante del aviso de deprecación de Node es deuda de GitHub, no del proyecto | Medido, no supuesto: tras subir `setup-node@v5`, la corrida del 2026-08-14 nombra sólo `actions/upload-artifact@v5`, y **ése es su major vigente — no hay a dónde subir**. Queda escrito con esa frase para que dentro de unos meses nadie lo trate como deuda propia y se ponga a buscar una versión que no existe |

### Supuestos descartados

| Supuesto | Qué pasó |
|---|---|
| «Mover `upload-pages-artifact` a `desplegar` cierra el permiso» | **Falso.** El diagnóstico valía; el remedio no era aplicable. Comprobar que un remedio se puede aplicar es parte de proponerlo, no un paso posterior |
| «`upload-artifact@v5` no puede estar señalada, es el major vigente» | **Lo estaba.** El registro lo decía y bastaba con mirarlo. Un extrañamiento no es una comprobación |
| «El registro puede ir montado en la siguiente funcionalidad» | **No.** `docs/DECISIONS.md` se deriva de estas tablas: mientras el párrafo espera, las decisiones no existen para el camino de entrada que el propio proyecto manda usar |

### Estado que deja

`V2-17` cerrado: el próximo pull request ya no se fusiona a ciegas. La compuerta
—pipeline, cinco autopruebas, contenido sin JavaScript, barrera pública/interna y
la batería de `src/verify/`— corre antes de fusionar y no sólo después.

### Próximo paso recomendado

El catálogo de indicadores.

---

## Cierre · el catálogo de indicadores, y lo que despertó al publicarlo

El sitio publicaba 27 indicadores y no decía nada de los otros 13. Para un
lector, «no está» tiene tres lecturas incompatibles —no se midió, se midió y
salió mal, no se puede medir sin inventar el dato— y el criterio vivía sólo en
`docs/`, que no es el sitio.

Ahora hay una página, `indicadores.html`, con los cuarenta: definición, fuente,
denominador, cobertura medida y estado, y el motivo de cada uno de los trece que
no se publican.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-166 | El catálogo se construye en `02_indicators.py`, desde `config/indicators.yml` | Es el mismo archivo del que salen los KPI y las series. Un catálogo mantenido aparte diría lo que alguien recordó, no lo que el sitio publica: la única garantía de que «publicado» signifique publicado es que las dos cosas se lean del mismo sitio |
| D-167 | El estado tiene cuatro valores y no dos | «No publicado» tapa la diferencia entre diferido —calculable y verificado—, no calculable —la fuente no lo entrega— y fuera de alcance —decisión, no carencia—. Son tres cosas distintas y la tercera no se arregla con más datos |
| D-168 | Los estados no introducen colores nuevos | Reutilizan el par `--aviso-tinta` sobre `--aviso-fondo`, que ya está medido. Un verde y un rojo nuevos habrían metido dos colores sin validar en un sistema que se valida entero |
| D-169 | El catálogo se pre-renderiza | Es justo el contenido que alguien va a citar o archivar. Una página que exige JavaScript para decir qué se publica y qué no vale poco archivada |
| D-170 | `estructura.mjs` falla si una página de `dist/` no está en su lista de rutas | La lista es a mano porque la ficha de autor no dice nada sin `?id=`. Pero una lista a mano deja de cubrirlo todo en cuanto alguien añade una página, y el barrido sigue diciendo «0 problemas» sobre lo que no miró |
| D-171 | Las publicaciones sin autoría UFT nombrada se rotulan | Una celda en blanco no distingue «no hay» de «no se muestra». La publicación es institucional —la afiliación la trajo— pero ninguna firma con nombre la sostiene, y eso se dice |

### Lo que despertó al publicarlo

`config/indicators.yml` tenía cuatro campos —`estado`, `razon`, `que_falta`,
`mostrar_como`— que **no leía nadie**: metadatos dormidos. El catálogo los
publica, y tres estaban caducados. De inofensivos pasaban a falsedades
publicadas:

| Dónde | Decía | Dice |
|---|---|---|
| `AU-05` | ORCID «no existe en ninguna de las fuentes actuales», pendiente de `T-01` | `T-01` se cerró el 2026-08-01 y el sitio publica 216 de 556. Ya no es placeholder |
| `AU-03` | «497 de 589 firmas tienen h ≤ 1» | Base previa a la consolidación. Medido de nuevo: **466 de las 556 entidades publicadas** |
| `C-05` | «heredaría 123 variantes de nombre sin resolver» | 123 son filas de auditoría, y 20 de los 51 grupos ya se resolvieron. Quedan **31** |

Y la fuente de `AU-05` caía en el genérico «Scopus · SciVal» del mapa de
procedencia. ORCID no está en ninguna de las dos: se declara
`Crossref · registro de ORCID`.

### El verde que no miraba

La batería dio «sin fallos» sobre una página que **nunca abrió**:
`contraste.mjs` y `estructura.mjs` llevaban la lista de páginas escrita a mano y
`indicadores.html` no estaba en ella. Es el mismo fallo del barrido que pedía la
ficha de autor con `?firma=` cuando la página lee `?id=`.

Se añadió la página a las dos listas y, sobre todo, la guarda de `D-170`.
Comprobada en negativo: con un HTML de más en `dist/`, la estructura falla y dice
cuál nadie comprueba.

### Supuestos descartados

| Supuesto | Qué pasó |
|---|---|
| «Un campo de configuración que nadie lee es inofensivo» | **Hasta que alguien lo lee.** Tres de cuatro estaban caducados, y el error llevaba semanas siendo invisible porque nada lo mostraba |
| «La batería cubre el sitio» | **Cubría la lista.** Que no es lo mismo, y la diferencia no se ve desde el verde |

### Ambigüedades abiertas

- La cabecera `<head>` de `indicadores.html` se creó copiando la de metodología:
  `V2-16` pasa de manejable a incómodo con diez páginas.
- `docs/ORCID_COVERAGE.md` sigue en la base previa a la revisión (222/589).

### Próximo paso recomendado

Panel conceptual por sección, o resolver las cuatro firmas de `E-09` en
`make revision`.

---

## Cierre · el catálogo publicaba un repr de Python

La revisión del PR #29 encontró que la cobertura de `P-02` salía en la página
pública y en `catalogo.json` como
`823/823 · {2023: np.int64(228), 2024: np.int64(276), 2025: np.int64(319)}`.

`dict()` sobre una Series de pandas conserva los tipos de numpy, y su repr acaba
impreso tal cual. El defecto era anterior a este trabajo, pero mientras esa
cadena vivió en una nota interna de factibilidad fue fea; el catálogo es lo que
la asciende a página pública. El commit que la publica es el que debe publicarla
limpia.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-172 | La cobertura de `P-02` se formatea como texto, no se vuelca el diccionario | Esa columna la lee una persona, no un intérprete. Un volcado arrastra el tipo de dato de quien lo produjo |
| D-173 | `05_verify_public_layer.py` falla si un texto publicable contiene repr del intérprete | Un barrido a mano encuentra lo que ya está, no lo que alguien añada mañana. La compuerta que ya recorre todos los artefactos es el sitio donde eso se vigila |
| D-174 | `contraste.mjs` gana la misma guarda de cobertura que `estructura.mjs` | Una verificación que no mira todo dice «0 fallos» sobre lo que no miró. Aplicado al propio instrumento, no sólo al producto |
| D-175 | La fuente se afirma sólo de los indicadores que se calculan | Los cuatro no calculables no lo son por lo mismo: a `X-01` y `AU-04` la fuente no les entrega el dato, pero a `X-03` le falla la cobertura y a `X-04` la ventana. Una etiqueta única para los cuatro sería falsa en la mitad |

### El patrón, por tercera vez en dos sesiones

La primera versión de la guarda de `D-173` incluía `nan\b` y marcó **«Poznan
Studies in Contemporary Linguistics»** y **«se asignan al documento»**. Un patrón
que responde a otra pregunta devuelve resultados con la misma cara que uno que
acierta. Corregido: cada alternativa lleva puntuación o mayúscula que no aparece
en prosa, y el `nan` suelto se caza comparando la cadena entera.

Es el mismo tropiezo que el `grep` ampliado con «consecuencia|resolucion» sobre
un título de pediatría, y que el `git branch -r` que respondía con exactitud a
una pregunta distinta de la que se creía hacer. Aquí falló en voz alta —cuatro
falsos positivos en la compuerta— en vez de en silencio, que es la diferencia
entre una guarda y un adorno.

Quien revisó llegó al catálogo buscando `data-codigo="…"`, que no existe: la
página emite `data-e`. Estuvo a punto de reportar «la página no marca los
indicadores». El mismo silencio, del otro lado.

### Verificación

Las dos guardas comprobadas en negativo: con un HTML de más en `dist/`,
`contraste` y `estructura` fallan y dicen cuál nadie comprueba. Barrera de capas
0 fallas, batería completa sin fallos, y `np.int64` ausente de `dist/` y de
`data/processed/`.

### Próximo paso recomendado

Panel conceptual por sección, o resolver las cuatro firmas de `E-09`.

---

## Cierre · la guarda cazaba la mitad de lo que decía cazar

La revisión del PR #29 encontró que `REPR_DE_INTERPRETE` cerraba la mitad `np.*`
de la forma «valor interpolado en un texto» y dejaba abierta la mitad
`nan`/`None`, que sólo se cazaba comparando la cadena entera. Ese razonamiento
vale para `str(elemento)`, no para la interpolación en f-string — que es
exactamente cómo se rompió `P-02`. `«308/823 (nan %)»` pasaba.

### Decisión

| # | Decisión | Fundamento |
|---|---|---|
| D-176 | `nan`, `None` y `NaT` se cazan con frontera de letra unicode, no comparando la cadena entera | «Poznan» lleva `z` delante, «asignan» lleva `g`, «Nanotecnología» lleva `o` detrás: los tres quedan fuera por la frontera, no por la puntuación. Medido: 18 casos sintéticos sin discrepancias y **0 marcas sobre las 34.736 cadenas de los 564 artefactos publicados** |

### Coste residual, declarado — y no estaba donde yo lo puse

Lo escribí como un riesgo de títulos en inglés («None of the above: …»). La
revisión lo movió al sitio correcto: la frontera es de LETRA, el guión no la
cruza, y eso apunta a los **identificadores de autor** antes que a los títulos.
Son slugs con guión —`abara-j-f`— y `Nan` es un nombre de pila corriente en la
fuente china: una firma «Nan Y.» daría el id `nan-y`, que la guarda marcaría, y
abortaría el build por una persona real.

Comprobado sobre el patrón: `nan-y` marca, `abara-j-f` no. Hoy no ocurre —0
apariciones como token suelto en los 556 id de autor y en las 34.736 cadenas
publicadas—, y cuando ocurra lo que hay que afinar es la frontera, incluyendo el
guión. Queda escrito así en el propio archivo.

El arreglo del guión no entra aquí por decisión de quien revisó: va en el PR en
que se vuelva a tocar la guarda.

También queda escrito allí el alcance: la compuerta recorre
`data/processed/**/*.json`, no `dist/*.html`. El catálogo está cubierto porque su
JSON está aguas arriba de la página, pero un constructor que formatee un valor
directo al HTML se la saltaría.

### Dos cifras mías que estaban mal

- Dije **563 artefactos**; son **564**. La compuerta lo imprime en cada corrida y
  yo lo copié de una ejecución anterior al catálogo. La herramienta acertaba; la
  cifra se torció al pasarla a prosa. Es la regla de la base declarada aplicada a
  un número que ni siquiera había que calcular: había que leerlo.

### Un rojo falso, que se lee igual de bien que un verde falso

Quien revisó comprobó las guardas de cobertura corriendo `contraste.mjs` y
`estructura.mjs` sueltos, y obtuvo `exit=1` de los dos. Casi lo dio por
confirmado. El `1` era `ERR_CONNECTION_REFUSED` —el servidor lo levanta
`run_all.mjs`, no los módulos— y `estructura` ni había llegado a mirar `dist/`.

Es el cuarto caso del mismo patrón en dos sesiones, y el primero por el lado
contrario: **un rojo por el motivo equivocado confirma lo que uno quería creer**,
igual que un verde por el motivo equivocado. Rehecho con `run_all.mjs`, donde sí
pasa.

### Próximo paso recomendado

Panel conceptual por sección, o resolver las cuatro firmas de `E-09`.

---

## Cierre · el panel conceptual por sección

Cada sección presenta indicadores distintos y cada una invita a una lectura
equivocada concreta: producción se lee como rendimiento, impacto como calidad,
colaboración como influencia, y la clasificación temática como el tema real del
artículo. Un lector que llega sin saber qué pregunta responde la sección no
tiene forma de saber cuál **no** responde.

Las cuatro secciones abren ahora con un panel que declara tres cosas antes de
mostrar ningún gráfico: qué responde, qué no responde y sobre qué base.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-177 | El texto de los paneles vive en `docs/EJES.md`, no en `vista.js` | Son afirmaciones metodológicas y se revisan como documento. Es el mismo criterio del glosario: la fuente de verdad es el Markdown, para que lo que lee el usuario sea literalmente el documento revisado y no una copia divergente |
| D-178 | Las tres partes son obligatorias y su ausencia **aborta el build** | Un panel sin el «no responde» es justo el que no hacía falta escribir: sin esa parte el resto es un subtítulo. Y una sección sin el aviso es la que más lo necesitaba |
| D-179 | El panel ocupa el ancho completo y va delante del índice | En la rejilla de dos columnas caería en la del índice. El aviso de qué no responde una sección no es material de barra lateral, y decirlo después de los gráficos es decirlo tarde |
| D-180 | El texto es institucionalmente neutro | Describe la metodología, no a esta universidad: otra institución lo reutiliza sin tocarlo. `V2-14` —los textos de `docs/` citan cifras de esta institución— no crece con esto |

### Lo que dicen los cuatro

Las cuatro confusiones que `CLAUDE.md` enumera en su marco metodológico, cada
una en la sección donde de verdad se produce:

| Eje | Lo que no responde |
|---|---|
| Producción | Qué tan bueno es lo publicado. Volumen es actividad indexada, y comparar unidades mide también la cobertura desigual de Scopus |
| Impacto | Ni calidad ni mérito. Citar no es aprobar; tampoco es visibilidad; y el cuartil describe a la revista, no al artículo |
| Colaboración | Ni la calidad de la colaboración ni quién la lideró. «Más países» no es «mejor» |
| Temática | De qué trata cada artículo: la clasificación asigna la categoría de la revista. Y la prominencia describe al campo, no a quien publica en él |

### Verificación

Los cuatro paneles se pre-renderizan y salen delante del índice en las cuatro
páginas. La guarda comprobada en negativo: quitando el «no responde» de
colaboración, el build aborta nombrando el eje y la parte que falta. Batería
completa sin fallos —contraste incluido, sobre el par `--accion` /
`--superficie-2`, que ya estaba medido— y el validador de paleta sigue dando
sistema cromático válido.

### Ambigüedades abiertas

- El panel usa `--accion` para destacar «No responde». Es un par ya validado,
  pero si algún día llega el rojo institucional oficial hay que volver a medirlo
  como todo lo demás.

### Próximo paso recomendado

Resolver las cuatro firmas de `E-09` en `make revision`, que sigue siendo lo
único que bloquea que `P-06` baje a 552.

---

## Cierre · el panel se equivocó en lo que el panel promete

La revisión del PR encontró que el panel de producción decía «Las publicaciones
del universo» y explicaba sólo el caso de la unidad académica. Pero la sección
trae cuatro indicadores sobre **tres** bases: `P-02` y `P-03` sobre las 823 del
universo, `P-07` sobre los 818 con autoría detallada, y `P-05` —ranking de
fuentes— sobre las **816 con métricas**, que el panel no nombraba.

Un lector que mirara el ranking habría contado 823 donde son 816, en la frase
que existe para impedirle contar mal. Es pequeño en magnitud y exacto en tipo.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-181 | Cada eje declara en `EJES.md` los denominadores que su sección usa, y el build falla si no coinciden con los de `data-indicadores` | Los dos lados ya eran legibles por máquina: la página declara sus códigos y `config/indicators.yml` el denominador de cada uno. Sólo faltaba que el eje declarara los suyos. Sin esto, la lista escrita a mano deja de cubrirlo todo en cuanto alguien añade un indicador y el panel sigue diciendo su base vieja |
| D-182 | La guarda exige **igualdad**, no inclusión | Un denominador declarado que ninguna página usa es una declaración que envejeció, y esa es la otra mitad del problema |
| D-183 | `denominadores` no se publica en `ejes.json` | Es instrumental: sirve a la guarda, no al lector. Publicarlo metería en el artefacto un dato que la página no usa |

### La segunda, que hoy no se ve

Temática declaraba «con área temática asignada», pero `T-04` —Objetivos de
Desarrollo Sostenible— corre sobre `con_metricas`. Las dos valen 816 hoy, así
que ningún lector se confunde: **la igualdad es coincidencia, no definición**. El
panel lo dice ahora, y si algún día divergen la guarda lo caza antes de que el
texto envejezca en silencio.

### Comprobado en negativo, dos veces

| Escenario | Qué hace el build |
|---|---|
| Se quita `con_metricas` del panel de producción —el fallo original— | Aborta: «el eje 'produccion' declara […] y su página usa […] · faltan ['con_metricas']» |
| Se añade `P-07` a colaboración sin tocar su panel | Aborta nombrando `con_autoria_detallada` como el que falta |

El segundo es el que importa: es el caso futuro, no el pasado.

### Nota de método, la cuarta de la ronda

Quien revisó buscó `id="eje"` para localizar el panel y obtuvo «no» en las cuatro
páginas —el marcado es `<section class="panel-eje">` dentro de `#modulos`—. Estuvo
a punto de reportar que el panel no estaba. Lo cazó porque en el mismo barrido
«No responde» aparecía una vez por página y **las dos cosas no podían ser verdad
a la vez**.

Es la contrapartida exacta del rojo falso de la ronda anterior: un falso negativo
se lee igual de bien que un hallazgo. Lo que lo desmontó no fue mirar más, sino
tener dos medidas que se contradecían.

### Próximo paso recomendado

Resolver las cuatro firmas de `E-09` en `make revision`.

---

## Cierre · una errata de un carácter borraba un gráfico sin dejar rastro

La revisión encontró dos agujeros en la guarda de los paneles. El segundo no era
de este trabajo, pero se ve desde aquí porque es el primer sitio donde
`data-indicadores` se lee contra el catálogo.

### Lo que se midió antes de arreglarlo

Sustituyendo `A-01` por `Z-99` en el `data-indicadores` de impacto:

```
make sitio                        exit=0
menciones de «Z-99» en la salida  0
módulos en dist/impacto.html      5 → 4
A-01 en dist/impacto.html         ausente
```

Auditoría, barrera de capas, guarda nueva y batería del navegador: todo verde. Un
carácter mal escrito retira un indicador publicado del informe y **nada lo dice**.
De todo lo hallado en esta revisión es lo único que degrada lo publicado sin
dejar rastro; el resto eran cifras mal contadas o guardas que miraban de menos.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-184 | Un código de `data-indicadores` que no esté en `config/indicators.yml` aborta el build | No hay nada que interpretar: un código desconocido no es una decisión de diseño, es un error de escritura. `paginaModulos` lo descarta en silencio y la página sale con un gráfico menos |
| D-185 | Un eje declarado en `EJES.md` sin página que lo use aborta el build | El bucle recorría páginas, así que cazaba «página sin panel» y no su simétrico. Y el eje huérfano pesa más que el denominador huérfano: éste no llegaba al artefacto, aquél se serializa a `ejes.json` y se publica |
| D-186 | El denominador se cuenta sólo de los indicadores publicados, y eso endurece la guarda | Al retirar uno con `publicar: false`, su base deja de usarse y el panel pasa a declarar una que ya nadie tiene: el build se detiene. Es deliberado — si el ranking de fuentes deja de mostrarse, la frase del panel que lo explica deja de ser verdad |

### Un comentario mío que decía lo contrario de lo que hacía el código

Escribí que filtrar por `publicar` evitaba que ejercer la vía de replicabilidad
rompiera el build. **Es al revés**: el filtro hace que `publicar: false` detenga
el build, porque el panel queda declarando una base sin uso. Lo descubrí
probándolo, no releyéndolo.

El comportamiento es el correcto y se conserva; lo que estaba mal era la
explicación. La promesa de `config/indicators.yml` —desactivar un indicador «sin
tocar el código del build»— sigue en pie: `EJES.md` no es código, es el documento
que describe la sección, y si un gráfico desaparece su frase hay que reescribirla.

### Cuatro escenarios, cuatro mensajes distintos

| Escenario | Qué dice el build |
|---|---|
| `Z-99` por `A-01` en impacto | códigos que no existen en `config/indicators.yml`: `['Z-99']` |
| Eje `financiamiento` sin página | ejes que ninguna página usa: `['financiamiento']` |
| Quitar `con_metricas` del panel de producción | faltan `['con_metricas']` |
| Añadir `P-07` a colaboración | faltan `['con_autoria_detallada']` |

### La forma única, que merece nombre

Cinco hallazgos de esta revisión son el mismo defecto: **una lista escrita a mano
que deja de cubrir, y un verde que sigue diciendo «bien» sobre lo que no miró.**

`RUTAS` en `estructura.mjs` · `PAGINAS` en `contraste.mjs` · el barrido de `np.`
que sólo veía lo que ya estaba · el panel que declaraba dos bases de tres ·
`data-indicadores` contra el catálogo.

Cinco sitios, una sola forma. En los cinco el arreglo fue el mismo: que el
instrumento compare su lista contra la realidad y falle nombrando la diferencia.

### Próximo paso recomendado

Resolver las cuatro firmas de `E-09` en `make revision`.

---

## Cierre · la última base sin declarar

`docs/ORCID_COVERAGE.md` seguía publicando **222 de 589 (37,7 %)**: la base
previa a la consolidación, en un documento de capa pública cuyo tema es
precisamente esa cifra. Era la última instancia viva del defecto que ocupó toda
la ronda — se corrigieron `STATE.md`, `INDICATORS.md`, `LIMITATIONS.md`, el
catálogo, los cuatro paneles y `V2_BACKLOG.md`, y quedó éste.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-187 | Las cifras del documento se rehacen sobre la base publicada, y la cabecera declara cuál es | Un documento sobre cobertura que publica una base que ya no existe no es sólo inexacto: enseña a leer mal la cifra que explica |
| D-188 | La tabla de las tres vías conserva sus cifras de entonces, declaradas como históricas | Así se recorrió el camino y así queda. Reescribirla con cifras de hoy borraría el proceso; lo que hacía falta era decir sobre qué base estaba medida |
| D-189 | La cifra de `T-19` en `PLAN.md` se corrige; el pendiente sigue abierto | Cerrar o reescribir un `T-xx` es decisión del propietario. Corregir una cifra caducada dentro de él no lo es: el techo citado, 29,5 %, era de antes de la ampliación y de la revisión |

### Todo remedido, no arrastrado

| Qué | Decía | Dice |
|---|---|---|
| Cobertura | 222 de 589 · 37,7 % | **216 de 556 · 38,8 %** (y 240 sobre firmas sin consolidar) |
| Etiquetas | 153 / 48 / 17 / 4 | **139 / 43 / 16 / 15 / 3** — la de «confirmado por revisión» no existía |
| Una sola publicación | 419 firmas · 71,1 % · 26,3 % de cobertura | **387 entidades · 69,6 % · 27,1 %** |
| Diez o más | 15 firmas · 93,3 % | **18 entidades · 94,4 %** |
| Sin ninguna publicación con DOI | 10 | **10** — no cambió |

La forma de la distribución no cambió; las cifras sí. Fusionar variantes junta
las publicaciones de una persona, así que hay menos entidades de una sola
publicación y más de diez o más — y eso está dicho en el documento, porque la
diferencia entre las dos tablas es un dato sobre la consolidación, no ruido.

### Dos cosas que aparecieron al remedirlo

- **§2 bis contaba cuatro etiquetas y hoy son cinco.** «Confirmado por revisión»
  la trajo la revisión humana de identidad y es la única que no depende de una
  fuente automática. La tabla vieja no cuadraba con las 216.
- **§4 daba la consolidación por pendiente entera.** Ya no lo está: 63 formas son
  30 personas, y quedan 31 grupos, 20 perfiles fragmentados y las 4 firmas de
  `E-09`. El argumento —que «100 % de los autores» no está bien definido mientras
  no se sepa cuántos hay— se sostiene igual, y ahora dice además que esa cifra
  sólo baja según se resuelve la cola.

### Lo que se comprobó y NO estaba mal

§5 afirma que una ficha sin ORCID muestra «No disponible en las fuentes
actuales». Se verificó contra una ficha real: el campo `orcid_estado` dice
exactamente eso. Es la misma cadena que estaba caducada en `AU-05` de
`config/indicators.yml`, y aquí sí es cierta — describe la ficha, no el
indicador.

### Próximo paso recomendado

`V2-08`: procedimiento público de corrección de fichas de autor, requisito
escrito de `DATA_LICENSE.md` §4.

---

## Cierre · el procedimiento de corrección, y una comprobación que no comprobaba lo que creí

`DATA_LICENSE.md` §4 dejaba escrito un pendiente: definir cómo una persona puede
pedir la corrección de su ficha. Era `V2-08`, y llevaba abierto desde la Fase 3.

Al leerlo resultó **menos bloqueado de lo que parecía**: el propio documento ya
determinaba el camino principal —corregir el perfil en Scopus, y la plataforma
lo refleja en la siguiente carga porque se reconstruye entera—. Lo que faltaba
era declararlo donde el lector lo encuentra.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-190 | El procedimiento se publica en el sitio y `DATA_LICENSE.md` apunta a él en vez de repetirlo | Dos redacciones de un mismo compromiso divergen, y la que el público lee es la del sitio. Una sola, en un sitio |
| D-191 | Distingue lo que se corrige en la fuente de lo que sólo se corrige aquí | No son el mismo trámite. Nombre, afiliación e identificador vienen de Scopus; aparecer dos veces, una ficha que no es persona, un ORCID mal atribuido o una unidad mal deducida los introduce esta plataforma al procesar, y no hay perfil de Scopus que los arregle |
| D-192 | Declara además **qué no se cambia a petición** | Afirmar una identidad, enlazar firmas sin revisión, o alterar una posición en un listado. No por rigidez: cambiarlas publicaría afirmaciones que los datos no sostienen. Un procedimiento que no dice qué no concede promete de más |
| D-193 | El canal de contacto queda como hueco declarado, no improvisado | Es decisión de la institución. Inventar un canal sería peor que no tenerlo: haría creer que hay alguien escuchando |
| D-194 | El enlace va en la página de autores, no sólo en metodología | Es la página donde alguien se encuentra a sí mismo mal representado, y es el momento en que necesita saber qué puede hacer |

La sección es **HTML estático**: un lector sin JavaScript ve el procedimiento
entero. El glosario y la procedencia de esa misma página sí dependen de JS, pero
eso es anterior y queda declarado, no tocado.

### La sexta lista, y una prueba negativa que era falsa

El enlace nuevo es de **página cruzada** —`metodologia.html#correcciones`— y la
comprobación de enlaces internos corta el `href` en el `#`: daba por bueno el
ancla con sólo existir el archivo. Un ancla rota no falla; deja al lector arriba
de la página preguntándose dónde estaba lo prometido, que cuesta más detectar que
un 404 precisamente porque no rompe nada.

Se añadió la comprobación de anclas de página cruzada a `estructura.mjs`. **Pero
la primera prueba negativa fue inválida**: rompí un ancla de la MISMA página, y
la cazó una comprobación que ya existía —`a[href^="#"]`, en el barrido del
navegador— cuyo mensaje ni siquiera era el mío. Di por confirmado el instrumento
nuevo con el rojo del viejo.

Rehecha sobre un ancla de página cruzada, sale el mensaje correcto. Y de paso
quedó claro que el check nuevo no duplica al viejo: uno mira dentro de la página
en el DOM renderizado, el otro entre páginas en el HTML estático.

| Comprobación | Qué cubre | Qué no |
|---|---|---|
| `a[href^="#"]` en el navegador | Anclas de la misma página, incluidas las que pinta JS | Enlaces a otra página |
| La nueva, sobre el HTML | Anclas de página cruzada en los 30 enlaces estáticos | Enlaces que pinta JS |

**El enlace que añadí no lo cubre ninguna de las dos**, porque es de página
cruzada Y lo pinta JavaScript. Se verificó a mano en el navegador: aparece,
lleva a `metodologia.html#correcciones`, la sección existe y el título se ve.

### Supuesto descartado

| Supuesto | Qué pasó |
|---|---|
| «Nadie comprobaba las anclas» | **Falso.** Había una comprobación desde antes; leí un bloque del archivo y no el archivo. Validé mi suposición contra un fragmento |

### Próximo paso recomendado

`V2-16`: la cabecera `<head>` repetida en diez páginas.

---

## Cierre · los perfiles de ORCID pendientes, y la cola que nunca menguaba

El encargo era una interfaz para identificar y validar los perfiles de ORCID
pendientes, verificables a mano, más un apartado informativo de las plataformas
ya integradas y una propuesta de nuevas.

Antes de construir nada se midió qué superficie de validación **ya existía**,
porque una segunda herramienta fragmentaría el registro de decisiones que `D-08`
centraliza. La medición encontró dos cosas distintas:

**Lo que sí estaba cubierto.** Cuatro colas de `make revision` ya preguntaban a
quién asignar un ORCID: 17 grupos que comparten identificador, 1 conflicto, 2
desacuerdos entre fuentes y 20 candidatos por afiliación.

**Lo que no lo estaba, y es peor.** Las asignaciones **ya publicadas** cuya
evidencia no las respalda no tenían cola ninguna: 17 formas de firma cuyo
titular no declara ninguna obra con DOI contra la que contrastar, 4 cuyas obras
declaradas no coinciden con ninguna de las atribuidas, y 6 firmas con cinco o
más publicaciones y ningún identificador —una de ellas con 16—. Un ORCID mal
atribuido publicado en una ficha con nombre y apellido le adjudica a alguien la
obra de otro, y no había forma de resolverlo.

**Y una tercera cosa, que no se buscaba.** La herramienta reconstruía la cola
desde la auditoría en cada corrida y **no leía lo ya decidido**: de 114 casos,
52 estaban resueltos desde el 5 de agosto y los volvía a preguntar como si nadie
los hubiera mirado. Una cola de pendientes que incluye lo resuelto no es una
cola de pendientes; es la misma clase de defecto que este repositorio lleva seis
instrumentos corrigiendo, sólo que del revés: no una lista que deja de cubrir,
sino una que nunca mengua.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-195 | La validación de ORCID **extiende `make revision`**; no se construye una segunda herramienta | `D-08` centraliza las decisiones de identidad en una cola y un archivo. Dos herramientas serían dos registros, dos exportaciones y dos caminos de aplicación que podrían contradecirse sin que nadie lo notara |
| D-196 | `build_review.py` **lee `internal/identity_decisions.csv`** y siembra cada caso con lo que ya se decidió | El navegador guarda el avance, pero en una máquina y hasta que alguien limpie el navegador. El registro que perdura está en el repositorio, y era el único que la herramienta no consultaba |
| D-197 | Lo decidido **no se borra de la página**: se marca y el filtro por defecto lo oculta | La exportación reescribe el archivo entero. Si los casos resueltos desaparecieran del HTML, exportar produciría un CSV sin ellos y la siguiente aplicación deshaaría 30 consolidaciones |
| D-198 | Tres colas nuevas y no una sola de «ORCID pendiente» | «El titular no declara obras» y «declara obras y ninguna coincide» no son el mismo caso: el segundo es sospechoso y el primero sólo no contrastable. Mezclar 4 casos urgentes con 17 rutinarios entierra los urgentes |
| D-199 | El umbral para «vale la pena buscarlo a mano» es `n_minimo_interpretable`, el que ya existe | Inventar un segundo umbral obligaría a justificar por qué difiere del primero. Con 5 publicaciones hay obra suficiente para reconocer a alguien; con una, la búsqueda devuelve homónimos indistinguibles |
| D-200 | El vocabulario de veredictos vive en **un solo módulo** (`src/review/decisiones.py`) y quien aplica **falla ante un veredicto que no conoce** | Estaba en cuatro sitios: los botones, los veredictos por caso, el `isin([...])` del aplicador y la cabecera del CSV. Un veredicto que la página ofrecía y el aplicador no conocía se leía, se contaba como leído y no hacía nada |
| D-201 | Un ORCID tecleado a mano se valida con su **dígito de control** (ISO 7064 MOD 11-2) y uno inválido **detiene** la aplicación | La errata de un carácter produce un identificador que existe y es de otra persona. Es justo el error que se comete al copiar, y el único que un dígito de control detecta con certeza |
| D-202 | Una asignación retirada **no se borra** de `data/enriched/authors_orcid.csv`: se declara en `config/orcid_revisado.yml` y el build la filtra | Ese archivo lo regeneran los conectores. Un borrado se deshace solo en la siguiente corrida de `orcid_crossref.py`, sin aviso. Y borrar la fila perdería de dónde vino el dato |
| D-203 | La comprobación humana **no pisa a «verificado»**: va al final de la cadena de etiquetas | «Verificado» significa que dos fuentes independientes coinciden. Sustituirlo por el juicio de una persona sería cambiar evidencia fuerte por débil y presentarlo como mejora |
| D-204 | «Se buscó y no se encontró» se registra como dato propio | `D-09`: ausencia de dato y resultado negativo no pueden verse igual. Sin esto, una firma buscada sin éxito es indistinguible de una que nadie ha mirado, y se volvería a buscar |
| D-205 | El apartado de plataformas se **publica en el sitio**; las propuestas de integración se quedan en `docs/` | Qué se consulta hoy es procedencia, y es publicable. Qué podría consultarse es un plan: publicarlo como sección del informe presentaría una intención como un hecho |
| D-206 | Un corpus nuevo —SciELO, OpenAlex— entraría como **corpus paralelo declarado**, nunca sumado al universo | Indexan con criterios distintos. La suma produce una cifra que nadie puede reconciliar, y `D-16` exige que cada indicador declare su denominador |
| D-207 | Google Académico se declara **no viable** y queda escrito en `V2_BACKLOG.md` §6 | No tiene API pública, sus condiciones prohíben la recuperación automatizada y sus datos no son reproducibles: sin fecha de corte, sin criterio de indexación declarado, sin identificador estable. Escribirlo evita que se reabra cada vez que alguien pregunte |

### Un campo publicado que era falso

`orcid_estado` decía «Recuperado desde Crossref» para **toda** asignación. De
las 216 publicadas, 43 vinieron del registro de ORCID y 15 de una revisión
humana: **58 fichas afirmaban una procedencia que no era la suya**. Ahora se
deriva de la fuente, y distingue tres ausencias que no son la misma —nadie ha
mirado, alguien miró y no encontró, no hay fuente que lo aporte—.

No lo detectó ninguna comprobación. Salió de leer el campo mientras se añadía
uno nuevo al lado.

### Ensayo del bucle completo

Con un CSV de prueba: confirmar dos asignaciones, retirar una, teclear un ORCID
encontrado a mano y registrar una búsqueda sin resultado. `apply_decisions.py`
generó `config/orcid_revisado.yml`, el build lo consumió y el desglose cerró:
216 → 216 (−1 retirada, +1 encontrada), «sin confirmar» 3 → 2, «no verificable»
16 → 15, y dos etiquetas nuevas con un caso cada una. La batería de verificación
del sitio pasó sin fallos. Después se restauró el estado real: **ninguna de esas
decisiones es real y ninguna quedó aplicada**.

### Dos defectos menores que aparecieron de paso

| Defecto | Efecto |
|---|---|
| `pd.read_csv(comment='#')` en el lector de decisiones | Truncaba la línea en la primera almohadilla **estuviera donde estuviera**: una nota como «cotejado con el registro #2» perdía la mitad, en silencio. Ahora los comentarios se recortan por posición, sólo al principio del archivo |
| El desglose de etiquetas de ORCID se imprimía desde una lista escrita a mano | Una etiqueta nueva se habría omitido y el desglose habría dejado de sumar el total sin decir por qué. Ahora avisa de las que no tienen glosa |

### Lo que sigue sin ser mío

Las 89 decisiones pendientes de `make revision` —incluidas las 27 colas nuevas
de ORCID y las 4 firmas de `E-09`— las toma una persona. La herramienta reúne la
evidencia, enlaza al registro del titular y enseña las publicaciones que hay que
comparar; el veredicto no lo pone.

### Próximo paso recomendado

Abrir `internal/revision_identidad.html`, filtrar por «Sólo ORCID» y resolver
las 4 de «ORCID sin confirmar»: son las únicas que el sitio publica hoy con la
marca de que nadie las ha respaldado.

---

## Cierre · el asistente que faltaba para la parte que sí requiere una persona

Al recomendar «siéntese a revisar los 16 casos urgentes» salió a la luz que la
vía para hacerlo era copiar cinco comandos a mano. La decisión `D-85` ya había
descartado eso: *«una instrucción que se puede copiar mal se copiará mal»*.
Había asistente para la verificación de ORCID y no para la revisión, que es
justo donde una persona decide sobre personas reales.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-208 | `scripts/revisar-identidad.ps1`: la revisión de identidad tiene asistente en Windows, como ya lo tenía la verificación de ORCID | `D-85`. La secuencia son siete pasos en el orden justo —autoprueba, auditoría, generar, abrir, recoger el CSV descargado, aplicar, reconstruir— y el error no se ve donde ocurre sino tres pasos después |
| D-209 | El asistente muestra `--dry-run` y **exige confirmación** antes de escribir | Aplicar sin ver antes qué se va a aplicar es lo que convierte una errata en un dato publicado sobre una persona |
| D-210 | Respalda el CSV anterior en `internal/.respaldos/` antes de sustituirlo | La exportación reescribe el archivo entero. El respaldo no se versiona; el archivo bueno sí |
| D-211 | El asistente **no decide nada**: abre, recoge y aplica | `D-08`. Un asistente que propusiera un veredicto por defecto lo convertiría en el veredicto |

### Cómo se verificó, y qué no se pudo verificar

No hay Windows en el contenedor. Lo que sí se comprobó, instalando PowerShell
7.4.6 en Linux:

| Comprobación | Resultado |
|---|---|
| Sintaxis, con el parser de PowerShell | 1.199 tokens, 0 errores. También se pasó el asistente existente, que sale limpio |
| BOM UTF-8 (`D-87`) | Presente |
| Cero acentos en las cadenas que se muestran (la consola de PS 5.1 los rompe) | 0, igual que el asistente existente |
| `foreach` sobre un array de arrays no se aplana | 2 iteraciones, no 4 |
| `$LASTEXITCODE` sobrevive a un `\| Select-Object` | 7, correcto |
| `ErrorActionPreference = 'Stop'` no aborta con un comando nativo que falla | Sigue vivo; los `if ($LASTEXITCODE -ne 0)` son la guarda real |
| Cada comando de Python que invoca | `--test`, `--dry-run`, `build_review`, `build_unit_validation` y la cadena de reconstrucción, todos corridos |

**Lo que NO se verificó, y hay que decirlo:** el script no se ha ejecutado en
Windows. La detección del intérprete, la ruta de Descargas y `Start-Process` se
copiaron del asistente que sí funciona allí, pero copiar de algo que funciona no
es haberlo probado. Se corrigió de paso un `@()` que faltaba: sin él, un único
archivo encontrado llega como escalar y `.Count` no significa lo mismo en
PowerShell 5.1 que en 7.

### Próximo paso recomendado

Ejecutar el asistente y resolver los 16 casos urgentes: 4 «ORCID sin
confirmar», 4 de `E-09`, 1 conflicto, 1 desacuerdo y 6 «Firma sin ORCID».

---

## Cierre · V2-20, el conector de ROR, y una consulta que este entorno no puede hacer

`config/institution.yml` lleva desde la Fase 1 con dos identificadores en
`null` y el motivo escrito al lado: «placeholder: no verificado». ROR los tiene
los dos —`ror_id` e `isni`— y trae además algo que vale más: **los nombres bajo
los que la institución está registrada**.

Eso es lo que convierte esto en algo más que rellenar dos campos. La detección
institucional blanda es **un patrón escrito a mano**,
`\bfinis[\s\-]+terrae\b`. Contrastarlo contra un vocabulario público dice si se
deja fuera alguna forma con la que la institución se firma de verdad. En el
ensayo con datos de prueba, el acrónimo es exactamente lo que el patrón no
captura: una cadena de afiliación que llegara sólo como «UFT, Santiago, Chile»
hoy no se detectaría.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-212 | El conector **no escribe `config/institution.yml`**: imprime la línea exacta y la pega una persona | Ese archivo es el contrato de replicabilidad —lo que otra institución edita para reutilizar la plataforma— y un identificador de organización es una afirmación sobre esa organización |
| D-213 | Los candidatos se filtran con `matches_institution_soft`, la regla del propio proyecto, no con parecido de cadena | Si ROR y el corpus se filtraran con reglas distintas, el contraste posterior no compararía lo que dice comparar. Y la regla `I-05` prohíbe el matching por subcadena |
| D-214 | Si más de una organización coincide, **se encola**; no se desempata | Elegir la primera es elegir por orden de respuesta de una API, que no significa nada |
| D-215 | Se admiten las dos formas conocidas de respuesta y, ante una desconocida, **se guarda la cruda y se detiene** | `CLAUDE.md` prohíbe suponer endpoints no confirmados. Adivinar la forma produce un error tres capas más abajo, donde ya no se entiende de qué venía |
| D-216 | El contraste **declara** las formas que el patrón no captura; no amplía el patrón | Cada patrón nuevo puede traer falsos positivos, y este proyecto ya tiene 16 verificados. Ampliarlo es una decisión |
| D-217 | Crossref, ORCID y ROR se declaran en `config/sources.yml` | Estaban implementadas y sin declarar. La cabecera de ese archivo exige que todo indicador publicado se pueda rastrear hasta una entrada suya, y el ORCID **se publica en las fichas de autor**: era una brecha de trazabilidad real, no una formalidad |

### Lo que este entorno no pudo hacer, y hay que decirlo

**La consulta no se ha ejecutado.** El contenedor donde se escribió el conector
no alcanza `api.ror.org`: la política de red lo deniega con un 403 en el CONNECT.
Se comprobó contra el estado del proxy, no se supuso.

Consecuencia práctica: **el contrato de la API no está verificado desde este
repositorio**. Por eso el conector no da por hecha una forma de respuesta —admite
la de `v2` y la de `v1`, y detecta cuál llegó— y ante una desconocida guarda la
respuesta cruda y se detiene diciendo dónde está. Es el mismo camino que ya usa
el asistente de ORCID: probar corto, y hacer que el fallo sea legible para que
una sola corrida baste para corregir.

### Lo que sí se verificó

| Comprobación | Resultado |
|---|---|
| `--test`, 12 casos: extracción de las dos formas, forma desconocida, orden determinista, filtrado de candidatos, contraste | Todos OK. Corre también en CI, junto a las otras cuatro autopruebas de conector |
| Ensayo de los cuatro caminos de `main()` con respuestas guardadas | Un candidato → propone y escribe; dos → encola y sale con 1; cero → declara y sale con 1; contrato raro → guarda la cruda y se detiene |
| Que el ensayo no dejara nada inventado en disco | `data/enriched/ror_institucion.json`, `internal/ror_candidatos.csv` y la caché, borrados. Ningún identificador falso versionado |
| `make auditoria` y `make sitio` tras tocar `config/sources.yml` | Sin cambios; nada enumera `fuentes` a ciegas |

### Próximo paso recomendado

Ejecutar la consulta desde la máquina del proyecto —`py src\enrich\ror_institucion.py`—
y pegar en `config/institution.yml` las dos líneas que imprime. Si el contraste
declara alguna forma no capturada, esa es una decisión aparte: ampliar el patrón
de detección puede traer falsos positivos.

---

## Cierre · V2-19 OpenAlex, y una afirmación mía que era falsa

El encargo era el conector de OpenAlex, que el propio backlog presentaba como
«una **segunda fuente independiente** de ORCID». Al escribirlo quedó claro que
esa frase —que había escrito yo el día anterior— **es falsa**.

**OpenAlex ingiere Crossref.** Un ORCID que devuelve puede ser literalmente el
que Crossref depositó. Que las dos coincidan no confirma nada que no
supiéramos: es la misma evidencia contada dos veces.

Importa porque este proyecto **publica** esa distinción. Cada ficha de autor
dice si su ORCID está «verificado» —dos fuentes independientes— o «declarado
por el titular» —una sola—, y `03_authors.py` ya evita exactamente este error
con las asignaciones que salen del propio registro de ORCID: llamarlas
«verificado» sugeriría dos fuentes cuando la fuente es una. Contar una
coincidencia con OpenAlex como verificación habría inflado el recuento de
comprobaciones independientes con comprobaciones circulares.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-218 | OpenAlex **no cuenta como fuente independiente**. Sus concordancias se cuentan aparte y **nunca** suben una asignación a «verificado» | Ingiere Crossref. La independencia tiene que ser real, no aguas abajo de la misma fuente |
| D-219 | Lo que sí aporta y por eso se implementa: **ORCID donde no había** y **contraste de la detección institucional por ROR** | Lo primero es cobertura nueva venga de donde venga; lo segundo compara un patrón escrito a mano contra una desambiguación externa |
| D-220 | El emparejamiento **se importa** de `orcid_crossref.py`, no se reescribe | Dos reglas para «¿qué autor de esta publicación es esta firma?» bastaría con tocar una para que las asignaciones dejaran de ser comparables |
| D-221 | El `author.id` de OpenAlex **no** se usa para fusionar firmas | Es una desambiguación por agrupamiento, y fusionar por ella es justo la «consolidación automática por similitud» que `V2_BACKLOG` §6 descarta |
| D-222 | El contraste institucional corre **en una sola dirección**, y se declara por qué | La contraria —producción que OpenAlex atribuye y nosotros no— es inalcanzable: sólo se consultan los DOI del universo, y el universo ya está filtrado por la institución. Anotado como `V2-26` en vez de dejar código que no puede encontrarla |
| D-223 | Las citas de OpenAlex **no** se contrastan aquí | Añadiría indicadores, y eso es una decisión con su propio denominador (`D-16`), no una consecuencia de tener el dato a mano |

### Un hallazgo de paso: una bandera que los datos desmentían

`config/matching_rules.yml` declaraba `ejecutado_contra_api: false` para el
conector de Crossref, con un comentario explicando que la red del entorno lo
impedía. Pero `data/enriched/authors_orcid.csv` tiene **174 asignaciones con
fuente `Crossref`**, y `T-01` se cerró el 2026-08-01 con esa corrida. La bandera
llevaba semanas afirmando lo contrario de lo que el archivo de datos probaba.

Corregida, y separada de lo que sí sigue siendo cierto: **el entorno de
desarrollo no tiene salida a `api.crossref.org`, `api.openalex.org` ni
`pub.orcid.org`** —comprobado hoy contra los tres— y por eso todo conector se
escribe con `--test` sin red y se ejecuta desde una máquina con salida.

### Verificación

| Comprobación | Resultado |
|---|---|
| `--test`, 11 casos | Partición del nombre, autor sin ORCID, recogida de ROR, contrato desconocido, que la forma extraída alimenta al `emparejar` importado, apellido compuesto que **falla** en vez de asignar de más, y las tres ramas del contraste. Corre en CI |
| Ensayo completo de `main()`, **sin red**, sembrando la caché con respuestas de prueba sobre 400 DOI reales | 1 asignación nueva · 1 concordante, contada aparte y no como verificación · 1 desacuerdo encolado · 1 publicación en el contraste institucional |
| Que el ensayo no dejara nada inventado | `authors_orcid.csv` restaurado y comparado byte a byte; caché, artefactos internos y la ficha ROR de prueba, borrados |
| `make auditoria` tras tocar `config/` | Sin cambios |

**El apellido compuesto merece una nota.** OpenAlex da el nombre entero en
`display_name` y hay que partirlo; «Ana Arenas Massa» se parte como apellido
«Massa» y entonces **no coincide** con la firma «Arenas-Massa A.». El caso está
en la autoprueba y el resultado esperado es que **no se asigne nada**: perder
una asignación es el fallo correcto, y atribuirle a alguien el ORCID de otro
sería el incorrecto.

### Próximo paso recomendado

Ejecutar `make ror` primero —el contraste institucional lo necesita— y después
`make openalex`. Los dos desde una máquina con salida a internet.

---

## Sesión 2026-08-20 — Rediseño de la interfaz

**Estado inicial:** el sitio funcionaba y era metodológicamente sólido, pero el
usuario lo describió como «austero, técnico, poco moderno, poco dinámico, con
UX mediocre». Se pidió un replanteo completo, con libertad para cambiar la
paleta.

### Decisiones tomadas

| # | Decisión | Fundamento |
|---|---|---|
| D-375 | La BANDA es la unidad de composición de las páginas narrativas | Una banda sostiene una afirmación; un indicador diferido metido entre los publicados se lee como uno más |
| D-376 | Las cuatro superficies de consulta NO llevan bandas | Filtro y paginación: quien llega ahí viene a buscar, no a que le cuenten. Convertirlas en narrativa arreglaba la estética y rompía la función |
| D-377 | `.banda-contraste` redefine los tokens en su ámbito | Evita una segunda hoja de estilo para «lo que va sobre fondo oscuro»; lo que cae dentro se adapta solo |
| D-378 | La forma del gráfico la elige la RELACIÓN del dato | Contrastado contra el Visual Vocabulary del FT. `I-05` era correctitud, no estética |
| D-379 | La equivalencia ortográfica de firmas NO viola `D-08` | Es equivalencia de cadena, no juicio de identidad: la misma firma con otros diacríticos |
| D-380 | La vista de la red vive en `internal/` mientras `C-05` esté diferido | Una persona partida en dos nodos hace que la figura afirme que dos investigadores no colaboran |
| D-381 | La paleta institucional es **Ink Black · Deep Ocean · Jungle Teal · Peach Glow · Racing Red** (`071e22 · 1d7874 · 679289 · f4c095 · ee2e31`) | La fijó el usuario. Estuvo aplicada, se sustituyó por un índigo de alto contraste **sin consultarle** y se perdió. Validada: dato 5,14:1 / 5,79:1, ΔE 21,8 / 23,4 frente a la advertencia, daltonismo 30,1 / 22,5. Es más ajustada que el índigo en la separación del ámbar pero cumple |
| D-382 | Una elección cromática del usuario se registra como DECISIÓN, no como preferencia | `DECISIONS.md` tenía anotado cómo se declaran los tokens y cómo los valida el instrumento, pero no QUÉ colores eligió el usuario. Al no estar registrada, nada la sostuvo cuando el rediseño cambió de rumbo. El hueco no era de código: era de memoria |

### Correcciones sobre el propio trabajo

Quedan anotadas porque el motivo es la parte útil:

- El déficit de `I-04` se pintaba con `--sin-dato`. Ese gris significa
  **ausencia** (`D-09`) y un FWCI bajo el promedio es un valor **medido**.
- El segundo suelo de banda era `--superficie-2`, que contra el papel mide
  ΔE 0,18 y 1,00:1: **el mismo color**. La alternancia sólo funcionaba en
  oscuro.
- Se amplió el área táctil con un pseudo-elemento superpuesto; se veía correcto
  en la hoja y **no recibía el evento** al comprobarlo por hit-test. El área
  existía en el CSS y no en la pantalla.
- La pista de teclado, superpuesta, **tapaba la primera barra y su valor**.
- La exención de «identidad no consolidada» se aplicó también a las
  consolidaciones ortográficas y **apagó una advertencia real** en
  `De la Fuente López M.`.

### Un instrumento que estaba ciego

`validar_paleta.py` leía la hoja entera y se quedaba con la última aparición de
cada token, así que `.banda-contraste` pisaba `:root` y declaraba **12 fallos
inexistentes**. Al arreglarlo y medir esa banda como ámbito propio, encontró
**4 fallos reales**: no redefinía la rampa ordinal ni la tinta del botón, y en
tema claro caían sobre suelo oscuro con `--ord-1` en 1,06:1.

Un instrumento que da falsos positivos se deja de mirar, y entonces tampoco
atrapa los verdaderos.

### Archivos creados

`src/build/grafo_coautoria.py` · `src/review/equivalencia_ortografica.py` ·
`src/review/vista_red.py` · `internal/red_coautoria.html`

### Supuestos descartados

- Que el paquete de diseño del prototipo podía copiarse al repositorio real:
  era una instantánea reducida y vencida, con otro color de marca. Se portó
  sólo el delta.
- Que «1207 pares autor × publicación» eran pares. Son **apariciones**, y el
  exceso lo causa una sola firma: `School of Psychology`, un fragmento de
  cadena de afiliación que la regla `E-09` ya detecta.

### Ambigüedades abiertas

33 casos de identidad que exigen juicio humano o el registro ORCID externo.
`C-05` sigue diferido por `T-03`. La regla `E-06` sigue fallando (no
bloqueante): una columna de cobertura nula en el universo activo.

### Próximo paso recomendado

Resolver `T-03` con `make revision`, apoyándose en `make red`: la vista marca
los nodos que comparten apellido y la matriz muestra si comparten vecinos.
Resueltas esas variantes, publicar `C-05` es cambiar `publicar: false` a `true`
— el grafo, las tres formas y la navegación por teclado ya están construidos.
## Cierre · V2-16 y V2-26: la cabecera repetida, y la brecha que por fin se puede medir

Dos pendientes que no dependían de nadie más.

### V2-16 · Diez copias de dieciséis líneas

El `<head>` estaba copiado en las diez páginas: idéntico salvo el título y la
descripción. Su propia entrada del backlog decía cuándo tocaba arreglarlo —«con
una más, plantilla»— y la página del catálogo ya se había creado copiando la de
metodología, que es exactamente cómo diez copias se vuelven once y una se queda
atrás.

Ahora cada página declara sólo lo suyo:

```html
<head data-titulo="Producción — Informe Cienciométrico"
      data-descripcion="Volumen de publicaciones por año, tipo documental…"></head>
```

y `06_assemble_site.py` expande `web/_cabecera.html` al ensamblar. **140 líneas
duplicadas pasaron a 20.**

Con tres comprobaciones que abortan el build, y ninguna es decorativa: una
página sin marcador se quedaría sin hoja de estilo y sin el guion de tema; una
expansión rota produciría un sitio **sin CSS que pasaría todas las demás
comprobaciones**, porque el HTML seguiría siendo válido, sólo ilegible; y la
plantilla viajando a `dist/` sería una página huérfana. La primera se probó en
negativo: quitando el marcador de `tematica.html`, el build aborta nombrándola.

### V2-26 · La pregunta que el proyecto no podía responder

`LIMITATIONS.md` declara que el corpus describe producción **indexada en
Scopus** y que esa base castiga a humanidades, ciencias sociales y a la
publicación en español. Es una advertencia honesta y era **sólo cualitativa**:
nadie podía decir de qué tamaño es la brecha.

No se podía porque todo lo que el pipeline mira sale del universo, y el universo
ya está filtrado por la institución. `V2-19` tropezó con eso ayer: su contraste
sólo corre en una dirección. Esta consulta va al revés —le pregunta a OpenAlex
**quién publica desde esta institución**— y compara esa lista contra el universo.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-224 | La cabecera común vive en `web/_cabecera.html` y se expande en el ensamblado, no en el navegador | Hacerlo en cliente costaría una petición y un repintado en la ruta crítica, justo lo que el pre-renderizado vino a evitar |
| D-225 | Una expansión que deje la página sin hoja de estilo **aborta el build** | Es el único fallo de esta clase que pasaría inadvertido: el HTML seguiría siendo válido y todas las comprobaciones seguirían en verde |
| D-226 | La brecha de cobertura es una **cola de revisión**, nunca un ajuste del corpus | `D-206`. Scopus y OpenAlex indexan con criterios distintos; sumarlos produce una cifra que nadie puede reconciliar |
| D-227 | Una obra **sin DOI** no se afirma como faltante | Sin DOI no se puede saber si es la misma que el universo ya tiene por otro identificador. Contarla sería inventar brecha |
| D-228 | La consulta exige el **ROR**, no el nombre | Buscar por nombre es matching por cadena suelta —regla `I-05`— y aquí traería la producción de cualquier homónimo |
| D-229 | Los DOI se normalizan antes de comparar | Scopus exporta `10.x/y` y OpenAlex `https://doi.org/10.X/Y`. Comparar en crudo daría el 100 % de brecha: un resultado espectacular y falso. Está en la autoprueba |

### Verificación

| Comprobación | Resultado |
|---|---|
| `--test` de `openalex_cobertura.py`, 9 casos | Normalización de DOI, cursor, contrato desconocido, las tres clases de hallazgo, y el caso de la brecha inflada. Corre en CI |
| Ensayo con una respuesta guardada, contra el universo real | 6 obras: 3 ya dentro —con el DOI en MAYÚSCULAS a propósito, para probar la normalización—, 1 con DOI ausente, 1 sin DOI, 1 fuera de ventana. Cada una con su motivo |
| Guarda del ROR ausente | Se detiene y explica por qué no busca por nombre |
| `make sitio` + batería completa tras V2-16 | Sin fallos. `dist/produccion.html` reconstruido byte a byte con su cabecera |

### Próximo paso recomendado

Sigue siendo suyo: `make ror` desbloquea `make openalex` **y** `make cobertura`,
que son las dos consultas que hoy no pueden correr.

---

## Cierre · Claude-Mem no existe, y la constitución existía dos veces

El encargo era «aplica Claude-Mem al proyecto». No se puede: **no está en este
entorno**, comprobado por cuatro vías —sin binario, sin paquete npm global, sin
servidor MCP y sin plugin ni skill—. La única capacidad de memoria disponible
importa exportaciones de otro asistente, que es otra cosa.

Y no era un hallazgo nuevo: `SESSION_NOTES.md` ya lo tenía en su tabla de
supuestos descartados desde una sesión anterior. Lo que había era una
**contradicción**: `CLAUDE.md` —el archivo de mayor precedencia después de una
decisión del usuario— afirmaba «Este proyecto usa Claude-Mem» mientras el propio
repositorio documentaba lo contrario.

### Lo que apareció al buscarlo, y era peor

**`CLAUDE (1).md` estaba versionado en la raíz: una segunda constitución, y
divergente.** Una copia de descarga que se commiteó. No era idéntica: describía
el arranque de sesión **anterior** —«revisa la memoria, luego PLAN.md, luego
SESSION_NOTES»—, que es exactamente el comportamiento que la versión vigente
sustituyó por «lee STATE.md primero», porque leer todo por adelantado son ~3.700
líneas y consume el contexto que hace falta para trabajar. Le faltaban además
los dos párrafos que declaran que `STATE.md` es una vista derivada y no fuente
de autoridad.

El archivo de mayor autoridad del proyecto existía en dos versiones, y la
equivocada ordenaba justo lo que la vigente vino a corregir.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-230 | La memoria del proyecto se declara por lo que **es**: `STATE.md`, `SESSION_NOTES.md` y `docs/DECISIONS.md`, versionadas | Afirmar una capacidad ausente hace que cada sesión empiece buscando algo que no está. Y lo versionado es mejor para lo que aquí importa: se audita, se replica y sobrevive a cambiar de asistente |
| D-231 | Se elimina `CLAUDE (1).md` | Dos constituciones divergentes son peor que ninguna: la precedencia deja de significar nada si no se sabe cuál manda |
| D-232 | La memoria sale del orden de precedencia; queda en seis niveles | El sexto remitía a una memoria inexistente |
| D-233 | Los cinco `PROMPT_*.md` viven sólo en `prompts/` | Estaban duplicados en la raíz. Idénticos —desorden, no ambigüedad—, pero la raíz es donde se busca la constitución y conviene que sólo esté ella |

### Lo que sigue abierto

`make estado` **no corre solo al cerrar**. Hoy encontré `STATE.md` apuntando a
un commit anterior a seis: el punto de entrada de cada sesión, seis commits
viejo. Automatizarlo —un hook de cierre, o un paso más en `make sitio`— es el
trabajo con más rendimiento para la continuidad, más que cualquier memoria
propietaria.

### Próximo paso recomendado

Sin cambios: las 13 verificaciones urgentes, y los tres conectores escritos sin
ejecutar.

---

## Cierre · La fusión con el explorador, y el sello que había desaparecido

Dos trabajos encadenados: reconciliar esta rama con un `main` que había avanzado
25 commits, y arreglar lo que esa reconciliación dejó al descubierto.

### La fusión

`main` traía el rediseño en bandas aplicado al sitio, el motor único de
filtrado, las cuatro secciones explorables y el presupuesto de peso como
compuerta. Ocho archivos en conflicto; sólo cuatro eran trabajo de verdad.

**Las cuatro páginas de sección.** `V2-16` les había sustituido el `<head>` por
el marcador `data-titulo`/`data-descripcion`, y `main` les cambió el cuerpo y el
`data-pagina` de «modulos» a «seccion». Se resolvieron tomando la versión de
`main` **entera** y sustituyendo su `<head>` por el marcador — seguro porque se
comprobó antes de tocar nada que `main` no modificó el `<head>` en ninguna de
las diez páginas: es byte a byte la plantilla.

**Lo derivado no se fusiona, se deriva.** `STATE.md`, `docs/DECISIONS.md` y
`revision_identidad.html` se regeneraron después de resolver. `SESSION_NOTES.md`
conserva los dos bloques: es un diario de sólo añadir.

### El hallazgo: la procedencia había desaparecido de los indicadores

CI falló con «dist/impacto.html no trae los sellos de procedencia». Antes de
tocar nada se construyó `origin/main` puro en un worktree aparte: **cero sellos
en todas las páginas**. El fallo era anterior a esta rama.

No es que la procedencia se hubiera perdido entera. El explorador conservó el
denominador por cifra —cita `D-16` al construirlas— pero movió fuente y fecha
de corte a **una sola vez por página**, en la barra de vigencia. Medido sobre
`dist/impacto.html`: 3 denominadores por cifra, **una** aparición de la fecha de
corte, **cero** sellos. Con JavaScript y sin él.

Y quedó código vivo que nadie llamaba: `vista.js:173` seguía invocando
`c.sello(...)` desde `modulo()`, que las páginas de sección ya no usan.

**La compuerta de `deploy.yml` fue la única de las seis verificaciones que lo
notó.** Contraste, estructura, flujos, responsive, higiene y peso pasan en verde
con los sellos ausentes. Una comprobación de cadena literal escrita a mano
—justo el patrón que este repositorio desconfía— hizo aquí exactamente su
trabajo.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-234 | El sello vuelve **a cada indicador**, no sólo a la barra de página | El N no es global —823 en producción, 816 en impacto— y para una página que se imprime y se archiva, una hoja suelta no lleva la barra de vigencia encima |
| D-235 | `fuente` y `corte` vienen de `series.json`; `N` y cobertura se **recalculan sobre el recorte** | Son cosas distintas: las dos primeras son propiedades de la fuente y no cambian al filtrar. Repetir el N del total mientras alguien mira un recorte es el error que la propia cabecera de `vista_explorador.js` describía |
| D-236 | Un campo sin extractor **no afirma cobertura**: se calla | Ver el fallo de abajo. Un sello que miente es peor que ningún sello |
| D-237 | `cobertura_minima_sin_advertencia` viaja a `meta.json` | El explorador lo necesita para decidir cuándo un sello pasa a ser advertencia, y antes sólo lo conocía el build. Dos umbrales para una misma regla acaban diciendo cosas distintas |
| D-238 | El mapa de procedencias lo arma **una función** que comparten pre-render y navegador | El sello escrito en el build y el que se repinta al filtrar no pueden divergir |

### Un fallo mío, encontrado antes de empujar

La primera versión contaba la cobertura con el extractor del campo y, **cuando
no había extractor, devolvía el total**. Los tres cortes numéricos —citas, FWCI
y percentil— se dibujan sin extractor, así que `I-01` publicaba «100,0 % · 823
con dato» cuando las citas sólo existen en **816**.

Lo encontré mirando la salida, no una prueba: el sello decía 100 % en un
indicador cuyo denominador este proyecto lleva meses declarando como 816.

Corregido: los tres numéricos cuentan cuántas publicaciones traen ese número, y
un campo desconocido no afirma nada. La cobertura ahora varía como debe — 100 %,
99,1 %, 97,2 %, 92,6 % y 37,7 % en unidad académica, que dispara la advertencia.

### Ambigüedad que queda abierta

El sello de `P-07` declara **310 de 823 publicaciones**; el build calculaba ese
indicador sobre **1.207 pares autor × publicación** (63,8 %). Son dos cortes del
mismo indicador y cada superficie declara el suyo, que es lo correcto — pero
quien compare las dos cifras sin leer la base las verá contradictorias. Sin
resolver.

### Próximo paso recomendado

Fusionar el PR #37, que quedó en verde. Después, sin cambios: las 13
verificaciones urgentes y los tres conectores escritos sin ejecutar.

---

## Cierre · V2-20 ejecutado: la institución tiene identificador

`make ror` no corre en el entorno de desarrollo —el proxy deniega
`api.ror.org`, confirmado con la corrida real— así que el usuario ejecutó la
consulta en su máquina y trajo la respuesta. El conector la procesó con
`--json`, que es justo el camino que se dejó previsto para esto.

**Cerrados dos placeholders que llevaban abiertos desde la Fase 1:**

    ror_id: "0225snd59"
    isni:   "0000 0004 5934 6911"

El filtro de candidatos hizo su trabajo: de las organizaciones devueltas
descartó Lincoln, Interglobal, Anáhuac, Maimónides e Icesi —todas empiezan por
«Universidad»— porque ninguna responde al patrón institucional. Quedó una, en
Chile y activa.

### El contraste, y por qué NO se amplía el patrón

ROR registra cuatro nombres. El patrón `\bfinis[\s\-]+terrae\b` captura dos y
se le escapan **«UFT»** y **«Finis»**. Parecía un hueco de detección, así que
se midió sobre las 1.207 cadenas de afiliación del log:

| | |
|---|---|
| Con «UFT» y **sin** «Finis Terrae» | **0** |
| Con «UFT» **y** «Finis Terrae» | 3 — ya detectadas |
| Con «Finis» y sin «Finis Terrae» | 2, y son cadenas **truncadas** por el export; ya están en el log |

**El hueco es teórico, no real.** Añadir `\buft\b` no ganaría ninguna detección
medible y metería un patrón de tres letras en un corpus donde la regla `I-05`
existe justamente porque el matching laxo ya produjo 16 falsos positivos
verificados. Se deja el patrón como está, con la medición escrita.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-239 | `ror_id` e `isni` pasan de placeholder a valor verificado | Una sola organización candidata, activa, en Chile, y el ISNI lo declara su propia ficha de ROR |
| D-240 | **No se amplía** el patrón de detección con «UFT» ni «Finis» | Medido: 0 cadenas de 1.207 lo necesitarían. Un patrón nuevo sin ganancia medible sólo añade superficie de falso positivo |

### Qué desbloquea

`make openalex` y `make cobertura`, que preguntan por institución y hasta ahora
se detenían por falta de identificador. Siguen sin ejecutarse por la misma
razón de red: van desde la máquina del usuario.

### Próximo paso recomendado

`make openalex` y `make cobertura` en local. Y las 13 verificaciones urgentes,
que no dependen de ninguna red.

---

## Cierre · Dónde cae cada cola de los conectores nuevos

Antes de ejecutar `make openalex` y `make cobertura` había un hueco comprobado:
`build_review.py` lee seis archivos de `internal/` y **ninguno de los tres que
esos conectores emiten**. Las colas habrían caído en disco sin que nada las
mostrara.

### La decisión: no todas van al mismo sitio

Las tres son «cosas pendientes», pero no son la misma clase de pregunta, y
meterlas juntas habría roto lo que sostiene la herramienta de revisión.

**`openalex_desacuerdos` sí es identidad.** «OpenAlex atribuye a esta firma otro
ORCID» se responde con el vocabulario que ya existe —«el ORCID es correcto» /
«no es de esta persona»— y **tiene camino de aplicación**: `apply_decisions.py`
lo escribe en `config/orcid_revisado.yml` y el build lo consume. Entra como cola
de `make revision`, con prioridad 1, porque el sitio publica hoy uno de los dos
identificadores y si es el equivocado le está atribuyendo a alguien la obra de
otra persona.

**`openalex_deteccion` y `openalex_cobertura` NO.** «¿Esta publicación es de la
institución?» y «¿esta obra debería estar en el universo?» no se responden con
un veredicto de identidad, y sobre todo **no tienen camino de aplicación**:
cambiar el universo es una decisión de alcance, no algo que un script aplique.

Meterlas en la herramienta habría obligado a inventar veredictos sin efecto. Un
botón que no hace nada se pulsa igual, y entonces el registro de decisiones
afirma que algo se resolvió cuando no cambió nada. Van a un **informe**:
`internal/hallazgos_corpus.md`.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-241 | `openalex_desacuerdos` entra como cola de `make revision`, prioridad 1 | Es identidad, tiene vocabulario y tiene camino de aplicación. Y el sitio publica hoy uno de los dos ORCID |
| D-242 | `openalex_deteccion` y `openalex_cobertura` van a un informe, **no** a la herramienta | No tienen camino de aplicación. Un veredicto que no hace nada corrompe el registro de decisiones, que es lo que `D-08` protege |
| D-243 | El informe lista **25 casos por grupo** y declara cuántos quedan | La brecha puede traer miles de filas: una lista de miles no se lee, y una que se corta sin decir cuánto queda miente por omisión |
| D-244 | La brecha separa **las que tienen DOI y están en ventana** del resto | Sólo de ésas se puede afirmar que el universo no las tiene. Contar las demás inflaría la brecha con casos que no se pueden sostener |

### Verificación

Probado con fixtures que reproducen las columnas exactas que escriben los dos
conectores: la cola nueva aparece en `make revision` con su caso, y el informe
resume las dos colas de corpus con su desglose por motivo, año y tipo. Después
se borraron los fixtures y se comprobó lo contrario: **sin datos, la cola nueva
desaparece de la herramienta y el informe dice que no hay nada que escribir**,
en vez de emitir un archivo vacío que parecería un resultado.

### Próximo paso recomendado

Ejecutar `make openalex` y `make cobertura` en la máquina del proyecto. Al
volver, `make revision` ya tiene dónde poner cada cosa.

---

## Cierre · La ventana, declarada donde no se puede no verla

El informe cubre **2023–2025** y estamos en agosto de 2026: ocho meses de
producción que no están y que nada advertía. El rango aparecía en la línea de
identidad de la portada y en la barra de vigencia, pero **un rango no dice lo
que un lector necesita saber**. Alguien que abra esto en 2026 puede leerlo como
el estado actual de la producción institucional, y esa lectura no la corrige
ver «2023–2025» escrito al lado.

Ahora la portada lo dice:

> La ventana de este informe termina en **2025**: lo publicado después **no está
> aquí**. La fija la carga de datos, no la fecha en que usted lo lee.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-245 | La advertencia va **visible**, no dentro del desplegable «Qué mide este informe y qué no» | Una advertencia detrás de un clic es una advertencia que nadie lee. El desplegable sirve para matizar; esto es una condición de lectura |
| D-246 | Va en la familia **ámbar** del aviso metodológico | Está fuera de la familia visual del dato a propósito, y sus tokens ya están medidos |
| D-247 | El año sale de `meta.ventana.fin`, no escrito a mano | Una ventana que se mueva y una advertencia que siga diciendo 2025 sería peor que no advertir |
| D-248 | Sólo en la portada | Es donde se enmarca el informe. La barra de vigencia ya lleva el rango en las diez páginas, y repetir el párrafo entero en todas lo convertiría en ruido que se deja de ver |

### Lo que esto NO resuelve

Sigue siendo un parche honesto sobre un problema de datos: el corpus está
desactualizado, y declararlo no lo actualiza. La vía de fondo es la API de
Scopus y SciVal —el usuario tiene credenciales— y sigue esperando cuatro
respuestas: desde qué red correría, si la suscripción incluye SciVal, qué
límite de peticiones, y si migrar la ventana actual o extenderla a 2026.

### Próximo paso recomendado

Sin cambios: terminar `make openalex` y `make cobertura`, y decidir sobre la API
de Elsevier.

---

## Cierre · T-06 tiene conector, y una pregunta que no era la que parecía

El usuario pidió avanzar T-06 ("reexportar Scopus con la fecha de corte").
Antes de escribir nada, tres de las cuatro preguntas que quedaron pendientes en
el cierre anterior se resolvieron en la conversación: API Key confirmada,
todas las APIs de la suscripción aprobadas, sin restricción de IP. La cuarta
—si extender la ventana a 2026— **sigue sin decidirse**, y el límite de
consulta (quota) tampoco se conocía. Ninguna de las dos se asumió.

### El hallazgo que reencuadra T-06

`docs/UPDATING_REQUEST.md` y la sección 3.7 de `FUENTES_Y_APIS.md` (antes de
esta sesión) daban por sentado que la API "tiene" una fecha de corte que el
export manual no tiene. **Es impreciso.** La Scopus Search API no expone un
campo de actualización propio —a diferencia de SciVal, que sí lo declara—.
Lo que la API aporta de verdad es trazabilidad: consulta literal e instante
de ejecución capturados por código en vez de transcritos a mano, que es
exactamente el mínimo que `docs/UPDATING_REQUEST.md` §3 ya aceptaba ("si la
exportación no la incluye, basta con anotarla aparte junto con la consulta
usada"). Sin este ajuste, el script habría prometido un dato que la fuente no
entrega.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-249 | El conector declara el **instante de ejecución**, no una "fecha de corte de Scopus" que la API no expone | Prometer un campo que la fuente no tiene sería inventar un dato, prohibido por `CLAUDE.md` |
| D-250 | El límite de consulta no se asume: se lee de las cabeceras `X-RateLimit-*` de cada respuesta y se reporta | El usuario no lo conocía y la documentación general de Elsevier no sustituye una medición propia |
| D-251 | Si el recuento de la API difiere del universo publicado (823), se declara como hallazgo y no se aplica al corpus | Una base bibliográfica crece hacia atrás; una diferencia puede ser indexación nueva, no un error. Aplicarla sola confundiría hallazgo con corrección (mismo principio que `D-08`) |
| D-252 | El conector usa la ventana que hoy declara `config/institution.yml` (2023-2025), no una ventana extendida | Extender a 2026 es la cuarta pregunta del cierre anterior, todavía sin decidir. Bundlearla aquí la habría convertido en un hecho sin que nadie la decidiera |
| D-253 | Credenciales solo por variable de entorno (`SCOPUS_API_KEY`, `SCOPUS_INSTTOKEN`); nunca en el repositorio ni pedidas por chat | Mismo patrón que `docs/ORCID_API_GUIDE.md`; una API key es un secreto, no un dato de proyecto |

### Archivos creados o modificados

```
src/enrich/scopus_api.py       nuevo · conector Scopus Search API, --test sin red
config/sources.yml             nueva entrada scopus_api, ejecutada: false
docs/FUENTES_Y_APIS.md         §3.7 pasa de propuesta a implementada; fecha de
                                 actualización del documento
Makefile                       nuevo objetivo `scopus` (py src\enrich\scopus_api.py en Windows)
PLAN.md                        T-06: de "petición redactada" a "conector implementado"
```

### Verificación

`python3 src/enrich/scopus_api.py --test` — 7 casos, todos OK: construcción de
la consulta contra el valor exacto documentado en `UPDATING_REQUEST.md`
(`AF-ID(60105368) AND PUBYEAR > 2022 AND PUBYEAR < 2026`), extracción del
recuento, detección de tres formas de respuesta inválida sin adivinar, y
lectura de cabeceras de límite con y sin las cabeceras presentes. Sin red:
este entorno probablemente no alcanza `api.elsevier.com`, igual que le pasó a
`ror_institucion.py` con `api.ror.org`, así que la consulta real queda para
que el usuario la corra en su máquina con `SCOPUS_API_KEY`.

### Supuestos descartados durante la sesión

| Supuesto | Qué pasó |
|---|---|
| «La API de Scopus declara una fecha de corte que el export manual no tiene» | **Falso.** No tiene ese campo. Lo que aporta es instante de ejecución y consulta capturados por código, no una fecha declarada por la fuente |
| «Con la API Key ya se puede escribir el conector sin más preguntas» | **Parcial.** Alcanzó para las tres primeras; el límite de consulta seguía sin confirmarse y no se asumió — se lee de la respuesta |
| «T-06 y la decisión de extender la ventana a 2026 son la misma pregunta» | **Falso.** T-06 es trazabilidad de una consulta; la ventana es alcance del corpus. El conector usa 2023-2025 sin decidir la segunda |

### Ambigüedades abiertas

- **Límite de consulta**: se sabrá en la primera corrida real, no antes.
- **Ventana 2023-2025 vs. extender a 2026**: sigue abierta, sin tocar por esta sesión.
- `T-02`, `T-13`: como en el cierre anterior.
- `T-03`, `T-04`, `T-14`, `T-15`: esperando `make revision` (84 pendientes).
- `T-10`: depende de `T-03`.

### Próximo paso recomendado

Que el usuario ejecute `make scopus` (o `py src\enrich\scopus_api.py` en
Windows) con `SCOPUS_API_KEY` definida. El script imprime el bloque listo para
pegar en `config/sources.yml` y declara como hallazgo, no como corrección
automática, si el recuento difiere de 823. Con eso vuelto, T-06 se cierra a
mano con la evidencia delante — igual que `T-02` está esperando el envío de
`internal/validacion_unidades.md`.

---

## Cierre · El asistente de PowerShell, y dos fallos que sólo se ven corriendo

El usuario corrió `scripts\consultar-scopus.ps1` de verdad en su máquina.
Antes, ni siquiera llegó a clonar el repositorio (`git pull` desde
`C:\Users\Pablo`, fuera de cualquier carpeta de proyecto): la primera vez en
ese equipo, así que el paso a paso empezó por `git clone --branch
claude/state-review-next-steps-wzzq0h`. Con el repositorio ya local, el script
llegó hasta la consulta real y Scopus respondió **400 sin cuerpo**.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-254 | El conector manda un `User-Agent` descriptivo, no el que pone Python por defecto | `Python-urllib/3.x` lo bloquean sin cuerpo algunos WAF delante de APIs de Elsevier (Akamai es común ahí); eso se ve exactamente como el 400 vacío que reportó el usuario, indistinguible de un error real de la API sin este cambio |
| D-255 | El error de la API ahora imprime `Content-Type`, `Server` y un diagnóstico explícito cuando el cuerpo llega vacío, con las tres causas más probables en orden | Un `sys.exit` con un cuerpo vacío no dice nada; la próxima corrida del usuario tiene que traer evidencia suficiente para diagnosticar sin una segunda vuelta |
| D-256 | `scripts/consultar-scopus.ps1` lleva BOM UTF-8, igual que los otros dos `.ps1` del proyecto | Sin BOM, PowerShell 5.1 (la consola por defecto en Windows) lee el archivo con la página de códigos del sistema en vez de UTF-8, y las tildes salen como `Â¿`, `Ã©`. Los otros dos scripts ya lo tenían; éste se escribió sin él por descuido |

### Archivos creados o modificados

```
src/enrich/scopus_api.py   consultar(): User-Agent explícito, diagnóstico de error ampliado
scripts/consultar-scopus.ps1   BOM UTF-8 añadido (mismo contenido)
```

### Verificación

`--test` sigue con los 7 casos OK tras el cambio (no toca la lógica de
construcción de consulta ni de extracción de respuesta, sólo la llamada de red
y el mensaje de error). El fallo real —400 con cuerpo vacío— no se pudo
reproducir desde ningún entorno de este proyecto: ni este contenedor ni la
máquina donde se escribió el conector alcanzan `api.elsevier.com` (mismo
límite ya declarado para ROR y OpenAlex). El diagnóstico es la mejor hipótesis
disponible sin poder observar la petición real, no una causa confirmada.

### Supuestos descartados durante la sesión

| Supuesto | Qué pasó |
|---|---|
| «Si `e.read()` no lanza excepción, el cuerpo trae el error de Scopus» | **Falso en este caso.** El cuerpo llegó vacío — consistente con un WAF rechazando la petición antes de la aplicación, no con un error documentado de la API |
| «Los tres scripts de `scripts/` se generaron con el mismo procedimiento» | **Falso.** Los dos anteriores tienen BOM UTF-8; el nuevo no lo tenía. No se había comprobado la codificación de bytes de un `.ps1` nuevo hasta que el usuario vio las tildes rotas |

### Ambigüedades abiertas

- **Si el `User-Agent` era la causa real del 400**, sigue sin confirmarse: es la explicación más probable dado un 400 sin cuerpo contra una API de Elsevier, no una certeza. Si persiste tras este cambio, el nuevo mensaje de error trae `Content-Type` y `Server` para descartar un proxy corporativo.
- El resto, igual que el cierre anterior: límite de consulta, ventana 2023-2025 vs. 2026, `T-02`–`T-15` pendientes de `make revision`.

### Próximo paso recomendado

Que el usuario vuelva a correr `scripts\consultar-scopus.ps1` con estos
cambios. Si el 400 persiste, el mensaje ahora trae `Content-Type` y `Server`
de la respuesta — pedir que copie eso completo en vez de sólo el código de
estado, porque distingue un rechazo de proxy/antivirus de un rechazo real de
Elsevier.

---

## Cierre · No era la red: era pegar en un prompt oculto

El usuario siguió depurando en su máquina, con `curl.exe -v` directo —
herramienta que este proyecto no tenía instrumentada para diagnóstico y que
resultó decisiva: aisló cada capa una por una.

### La secuencia de hallazgos

1. **`curl` con la clave escrita a mano en el comando: 200 OK, total 818.**
   Coincide exacto con `scopus_export.n_registros_leido`. Esto solo probó que
   la API, la consulta y la red funcionan — no que el script funcione.
2. **`curl` con la clave en `$env:SCOPUS_API_KEY` tras un `Read-Host` en OTRA
   ventana: 401, sin cabecera `X-ELS-APIKey` en la petición.** La variable de
   entorno no viajó entre ventanas de PowerShell — eso es esperado, no un bug;
   confirmó que había que probar todo en una sola sesión.
3. **El usuario pegó su clave real donde iba la etiqueta del prompt** (`Read-Host
   "[CLAVE]" ` en vez de `Read-Host "API Key de Scopus"`), exponiéndola en el
   chat dos veces. Se le pidió rotarla en el portal de Elsevier de inmediato.
4. **Con la sintaxis corregida y la clave nueva: `Longitud capturada: 1`.**
   El prompt oculto (`-AsSecureString`) capturó un solo carácter basura en vez
   de los 32 de la clave pegada. **Esto era la causa real desde el principio**,
   no el `User-Agent` (D-254) ni la red: pegar dentro de un `Read-Host
   -AsSecureString` falla silenciosamente en algunas consolas de Windows.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-257 | `scripts/consultar-scopus.ps1` pide la API Key en texto VISIBLE, no oculto | Oculto pero roto es peor que visible y funcional. Nadie más ve la ventana del usuario, y una respuesta a `Read-Host` no queda en el historial de comandos de todas formas |
| D-258 | El script valida que la clave capturada tenga al menos 20 caracteres antes de consultar | Una clave de Elsevier tiene 32; un prompt que capturó 1 carácter por un pegado fallido debe detenerse ahí, no gastar una consulta contra la API con una clave que se sabe incompleta |
| D-259 | La API Key que el usuario expuso en el chat se trata como comprometida; se le pidió rotarla en dev.elsevier.com | Aunque la conversación es privada, quedó registrada fuera del control del usuario. `CLAUDE.md` no cubre credenciales de terceros explícitamente, pero el mismo principio de `<data_governance>` — no tratar lo interno como publicable por descuido — aplica a secretos |

### Archivos creados o modificados

```
scripts/consultar-scopus.ps1   API Key/insttoken en texto visible, valida longitud >= 20
```

### Verificación

No hay autoprueba para esta parte: es interacción de PowerShell con la
consola de Windows, que no se puede probar desde Linux ni desde una consola
sin TTY interactivo. La verificación real es que el usuario vuelva a correr
el script y el `curl` manual con clave visible confirme una captura de 32
caracteres.

### Supuestos descartados durante la sesión

| Supuesto | Qué pasó |
|---|---|
| «El `User-Agent` por defecto de Python causaba el 400» (D-254) | **No confirmado, y ahora improbable.** La cadena completa de fallos apunta a que ninguna consulta real llegó con una clave completa hasta ahora; el 400 original probablemente tenía la misma causa que el de esta vuelta: una clave truncada, no el User-Agent. D-254 se mantiene como buena práctica defensiva, no se revierte, pero deja de presentarse como la explicación encontrada |
| «Si el problema persiste tras cambiar el User-Agent, es la red» | **Descartado por la secuencia de curls.** La red, la consulta y la API funcionan perfecto; la única variable que fallaba era la captura de la clave en el prompt oculto |
| «Pegar en un prompt de PowerShell siempre captura el texto completo» | **Falso**, al menos en la consola de este usuario: un `Read-Host -AsSecureString` con pegado (Ctrl+V) capturó 1 carácter en vez de 32, sin ningún error visible |

### Ambigüedades abiertas

- **Si el `User-Agent` (D-254) hacía falta o no**, sigue sin poder probarse por separado: para cuando se corrija la captura de la clave, ya está también en el conector. No se revierte porque no hace daño, pero no se puede reclamar como la causa que se creía.
- El mismo patrón (`-AsSecureString` + pegado) está en `scripts/verificar-orcid.ps1` y `revisar-identidad.ps1`, sin corregir — no se tocó porque no fue lo que se pidió, pero es un hallazgo transferible si el usuario reporta el mismo síntoma ahí.
- El resto, igual que los cierres anteriores: límite de consulta ya resuelto (20.000/semana, confirmado por las cabeceras del `curl`), ventana 2023-2025 vs. 2026, `T-02`–`T-15` pendientes de `make revision`.

### Próximo paso recomendado

Que el usuario corra `scripts\consultar-scopus.ps1` de nuevo, de punta a
punta, con su clave rotada. Con la captura de clave arreglada y ya probado
que la consulta real da 818 (coincide con `scopus_export`), debería
funcionar en un solo intento. Si funciona, el bloque que imprime al final va
a `config/sources.yml` a mano, y T-06 queda cerrado con evidencia delante.

---

## Cierre · El script corrió de punta a punta — y un error metodológico que casi se cuela

El usuario corrió `scripts\consultar-scopus.ps1` completo, sin volver a
pedirle nada raro: capturó la clave en texto visible (32 caracteres),
consultó, y confirmó `total_resultados: 818`, coincide con
`scopus_export.n_registros_leido`. `data/enriched/scopus_api_consulta.json`
quedó en su máquina.

### El error, encontrado antes de subirlo

Al pegar el bloque que imprime el script en `config/sources.yml`, la primera
edición puso `fecha_corte: "2026-08-26"` en la entrada `scopus_export` — la
MISMA entrada que declara el CSV descargado el 2026-07-31. Eso contradice
directamente `docs/UPDATING_REQUEST.md` §5, que es explícito: la carga
vigente **debe seguir sin fecha de corte**, a propósito, y lo que este
mecanismo aporta es **para la próxima carga**, no aplicable
retroactivamente. Ponerle una fecha de corte a un export que no la declaró
habría sido inventar trazabilidad que la fuente no dio — exactamente lo que
`CLAUDE.md` prohíbe. Se corrigió antes de comitear: `fecha_corte` queda
`null`, como estaba, y el hallazgo entra en un campo nuevo y separado,
`verificacion_api`, con su propia semántica declarada (confirmación de
cobertura en una fecha, no fecha de corte del export).

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-260 | `scopus_export.fecha_corte` sigue `null`; la confirmación de la API entra en `verificacion_api`, un campo aparte | Fusionarlos habría declarado una fecha de corte que el export nunca tuvo. `docs/UPDATING_REQUEST.md` §5 ya fija esta frontera; el error fue no releerla antes de escribir |
| D-261 | T-06 **no se cierra** con esta corrida | Cierra cuando exista una reexportación NUEVA con fecha de corte propia. Lo de hoy es evidencia de que la cobertura no cambió desde el 31 de julio — valiosa, pero no es lo que T-06 pide |
| D-262 | La edición de `config/sources.yml` la hizo el asistente, no el usuario a mano | Son tres campos en un archivo sensible a la indentación (YAML), con los valores exactos ya confirmados en la terminal del usuario — el riesgo de un error de tipeo en Notepad superaba el de que el asistente transcribiera mal un dato que ya tenía completo y verificado |

### Archivos creados o modificados

```
config/sources.yml   scopus_export.verificacion_api (nuevo); fecha_corte se mantiene null
PLAN.md               T-06: de "falta ejecutar" a "conector probado, T-06 sigue abierto"
```

### Verificación

`python3 src/audit/run_all.py` completo tras el cambio: 29/30 reglas pasan,
0 bloqueantes (mismo resultado que antes de tocar `sources.yml`).
`docs/VALIDATION_REPORT.md` sin diff contra la versión ya comiteada — el
campo nuevo no afecta ninguna regla de auditoría. YAML validado con
`yaml.safe_load` antes de comitear.

### Supuestos descartados durante la sesión

| Supuesto | Qué pasó |
|---|---|
| «El bloque que imprime el script se puede pegar tal cual» | **Falso en este caso.** El bloque impreso (pensado para una reexportación NUEVA) no distingue esa situación de "verificar la vigente" — pegarlo literalmente en `scopus_export` habría fusionado dos hechos distintos. El script sigue correcto: es responsabilidad de quien pega, no un bug del conector |

### Ambigüedades abiertas

- Igual que el cierre anterior — límite de consulta resuelto (20.000/semana), rotación de la API Key expuesta pendiente de confirmar que el usuario la hizo, ventana 2023-2025 vs. 2026, `T-02`–`T-15` pendientes de `make revision`.
- **Nueva**: si vale la pena que `docs/UPDATING_REQUEST.md` mencione explícitamente que ahora existe un conector (`scopus_api.py`) para la próxima reexportación, en vez de asumir sólo el procedimiento manual. No se tocó esta sesión.

### Próximo paso recomendado

Confirmar con el usuario que rotó la API Key expuesta en el chat. Después,
sin pendiente inmediato de T-06 — queda documentado y a la espera de una
reexportación real. Retomar `T-02`–`T-15` vía `make revision` sigue siendo
el trabajo de mayor rendimiento disponible.

---

## Cierre · `make revision`: 84 decisiones aplicadas, y un casi-desastre de sobrescritura evitado a tiempo

El usuario revisó los 84 casos pendientes en `internal/revision_identidad.html`
por su cuenta (no vía `scripts\revisar-identidad.ps1`, cuyo flujo no se probó
en esta sesión) y subió el CSV exportado directamente al chat.

### Lo que casi se rompe

`apply_decisions.py` **regenera `config/identidades_consolidadas.yml` entero**
desde `internal/identity_decisions.csv` en cada corrida — no lo actualiza
incrementalmente. El archivo comiteado tenía **38 grupos** (la consolidación
histórica de «85 formas → 38 personas» que documenta `D-08`). Sobrescribir
`internal/identity_decisions.csv` con el CSV que subió el usuario y aplicar
sin más redujo eso a **16 grupos**: población de autores subiendo de 538 a
568 en el build, en la dirección contraria a lo que consolidar debería hacer.

**La causa:** `internal/revision_identidad.html` sólo pinta la cola VIVA de
ambigüedades (las que la auditoría sigue detectando). Un caso ya resuelto dos
semanas atrás, cuya consolidación hace que la ambigüedad que lo originó ya no
vuelva a aparecer, **desaparece del formulario** — no porque se haya revocado,
sino porque ya no hay nada que preguntar. `build_review.py` ya avisaba de
esto exactamente («25 decisión(es) del CSV sin caso vivo que las reciba»),
pero el aviso se leyó como informativo y no como lo que era: una advertencia
de que exportar y sobrescribir perdería esas 25-30 filas.

Se detectó ANTES de comitear, comparando `git diff --stat` de
`config/identidades_consolidadas.yml` contra lo que ya estaba en `HEAD` — el
recuento de grupos (38→16) fue la señal. Se revirtió con `git checkout --`
sobre los cuatro artefactos generados y sobre el CSV, sin haber tocado el
remoto en ningún momento.

### La corrección

Fusión por `caso_id`: unión del CSV viejo (respaldado en
`internal/.respaldos/` antes de sobrescribir, como ya hacía el flujo con
`scripts\verificar-orcid.ps1` para credenciales) y el nuevo, con el nuevo
ganando en los 80 casos que aparecen en ambos. Verificado que **ninguna** de
esas 80 coincidencias era una contradicción real: las 53 diferencias de
veredicto eran todas `pendiente → decidido`, nunca `misma → distintas` ni al
revés. Resultado: 141 filas (111 nuevas + 30 huérfanas preservadas), 37
grupos consolidados (84 formas de firma) — cercano a los 38 originales, con
la diferencia esperable de las decisiones genuinamente nuevas de hoy.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-263 | `internal/identity_decisions.csv` se FUSIONA por `caso_id`, nunca se reemplaza, al incorporar un CSV exportado de la herramienta | La herramienta sólo exporta la cola viva; un reemplazo directo pierde toda decisión cuyo caso ya no genera ambigüedad activa. Esto no estaba documentado en ningún lado y debería estarlo |
| D-264 | El respaldo va ANTES de sobrescribir cualquier CSV de decisiones, sin excepción, incluso en una sesión de un solo turno | Fue lo que hizo posible detectar y revertir esto sin pérdida: sin el respaldo en `internal/.respaldos/`, las 30 filas huérfanas habrían desaparecido sin rastro |
| D-265 | Antes de comitear un `apply_decisions.py`, se compara el recuento de grupos/personas contra `HEAD` | Es la señal más barata y más legible de una regresión de consolidación: un número que debería bajar y sube (o baja demasiado) es más fiable que leer 141 filas de CSV a ojo |
| D-266 | `scripts/revisar-identidad.ps1` deja de hacer `Copy-Item -Force` sobre el CSV vigente; llama a `merge_decisions.py` | Tenía EXACTAMENTE el mismo bug que se acaba de encontrar y revertir a mano — es el camino que `docs/OPERACION.md` recomienda como «la vía cómoda», así que corregirlo ahí importaba tanto como la fusión de esta sesión, no menos |
| D-267 | La fusión vive en `src/review/merge_decisions.py`, con `--test` propio, no como lógica suelta dentro del `.ps1` | PowerShell no es donde se valida lógica en este proyecto — los cuatro conectores y `apply_decisions.py` ya la ponen en Python con autoprueba; el `.ps1` sólo orquesta |

### Archivos creados o modificados

```
internal/identity_decisions.csv          fusionado (141 filas), no reemplazado
internal/.respaldos/identity_decisions_20260826T043050_pre_pablo.csv   nuevo · respaldo previo
config/identidades_consolidadas.yml      37 grupos (era 38; +6 nuevos, -7 al reagruparse con hoy)
config/firmas_e09_resueltas.yml          4 descartadas (Metabolism, Movement Sciences (NUTRIM),
                                           School of Psychology, and Senior Lecturer)
config/orcid_revisado.yml                13 confirmadas · 8 retiradas · 6 sin registro
data/enriched/authors_orcid.csv          +2 asignaciones
docs/BUILD_VERIFICATION.md               regenerado (538 fichas, era 542)
STATE.md                                 regenerado
src/review/merge_decisions.py            nuevo · fusión por caso_id, con --test
scripts/revisar-identidad.ps1            Copy-Item -Force reemplazado por merge_decisions.py;
                                           su autoprueba se suma al Paso 1
```

### Verificación

`apply_decisions.py --test`: 28 casos OK antes de tocar nada real.
`apply_decisions.py --dry-run` corrido DOS VECES: una contra el CSV
reemplazado (mostró el problema first-hand: 16 grupos) y otra contra el
fusionado (37 grupos, 0 contradicciones, 0 errores). Pipeline completo
(`run_all.py` → `indicator_feasibility.py` → `build_all.py`) reconstruido
tras la fusión: 29/30 reglas, 0 bloqueantes, 0 fallas de barrera
pública/interna. Población de autores 538 — coherente con una consolidación
adicional sobre 542, en la dirección correcta.

### Supuestos descartados durante la sesión

| Supuesto | Qué pasó |
|---|---|
| «Un CSV exportado por la herramienta de revisión es un reemplazo seguro del anterior» | **Falso.** Es un reemplazo seguro sólo de la cola VIVA. La consolidación histórica vive en filas cuyo caso ya no está vivo, y hay que fusionarlas a mano |
| «Si `apply_decisions.py --dry-run` no da error, el resultado es correcto» | **Verdad a medias, y peligrosa.** El script valida CONTRADICCIONES dentro del CSV que se le da, no pérdida de información respecto de un CSV anterior que ya no ve. Detectarlo exigió comparar contra `git diff`, no confiar solo en la salida del programa |

### Ambigüedades abiertas

- Igual que antes: rotación de la API Key, ventana 2023-2025 vs. 2026, `T-13` (percentil SciVal), `T-10` (red de coautoría, sigue esperando `T-03` completo).
- Quedan **5 pendientes** de las 141 filas fusionadas (casos genuinamente sin decidir, no perdidos).
- `scripts/verificar-orcid.ps1` sigue con el prompt oculto (`-AsSecureString`) que ya falló en `consultar-scopus.ps1`. No se tocó: es hallazgo transferible, no lo que se pidió esta sesión.

### Próximo paso recomendado

Ya corregido `scripts\revisar-identidad.ps1` (confirmado: tenía el mismo bug,
`Copy-Item -Force`, y ahora usa `merge_decisions.py --test`-eado). Subir todo
lo de esta sesión. Sin pendiente inmediato de identidad — la próxima ronda de
`make revision` puede usar el asistente con confianza.

---

## Cierre · Cuatro pendientes cerrados por consecuencia, y una referencia que nadie recordaba

El usuario pidió seguir con «las 13 verificaciones urgentes» mencionadas al
abrir la sesión. `build_review.py` recién regenerado mostraba **0 pendientes
de 111 casos** — la cola completa, no sólo lo que el usuario decidió hoy. Se
le preguntó qué eran esas 13; respondió que no lo sabe. No se inventó una
referencia: se cerró la pregunta con lo que sí se puede verificar.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-268 | `T-03`, `T-04`, `T-14`, `T-15` se cierran en `PLAN.md` | Sus colas respectivas («Variantes de nombre», «Varios Scopus ID», «ORCID compartido», «ORCID en conflicto») están en 0 pendientes tras la fusión y aplicación de hoy. Cerrarlos es consecuencia de un hecho verificable (`build_review.py`), no una decisión nueva |
| D-269 | `T-10` se declara desbloqueado, no cerrado | Dependía de `T-03`, que ya cerró. Pero `T-10` en sí —publicar la red de coautoría— sigue siendo una decisión de alcance aparte, no automática |

### Archivos creados o modificados

```
PLAN.md    T-03, T-04, T-14, T-15 cerrados; T-10 actualizado (desbloqueado, no cerrado)
STATE.md   regenerado — pendientes abiertos: 9 → 5
```

### Verificación

`build_review.py` recién corrido: 0 pendientes en las cuatro colas
correspondientes, de 111 casos totales. `python3 src/state/snapshot.py`
confirma la baja de 9 a 5 pendientes abiertos.

### Ambigüedades abiertas

- Qué eran las «13 verificaciones urgentes» sigue sin saberse. No bloquea nada: la cola real está en 0.
- Las de siempre: rotación de API Key, ventana 2023-2025 vs. 2026, `T-02`, `T-06`, `T-13`, `T-19`.
- Si vale la pena decidir ahora sobre `T-10` (publicar la red de coautoría) ya que su bloqueo se levantó.

### Próximo paso recomendado

Preguntarle al usuario cuál de los 5 pendientes reales quiere atacar:
`T-02` (enviar la hoja de unidades académicas — no es trabajo de código),
`T-06` (esperando una reexportación real de Scopus), `T-10` (decidir si
publicar la red de coautoría, ya desbloqueada), `T-13` (falta respaldo
documental de Elsevier) o `T-19` (ampliar cobertura ORCID por afiliación).

---

## Cierre · T-19: el mismo pendiente, un bug ya conocido, corregido antes de que muerda dos veces

El usuario eligió `T-19`. `src/enrich/orcid_afiliacion.py` ya existía y pasa
`--test`; lo que faltaba era un camino para Windows. Usa las mismas
credenciales (`ORCID_CLIENT_ID`/`ORCID_CLIENT_SECRET`) que
`scripts\verificar-orcid.ps1` — y ese script todavía tenía el prompt oculto
(`-AsSecureString`) que ya falló en vivo esta sesión con `consultar-scopus.ps1`
(D-257). Construir un asistente nuevo con el patrón corregido mientras el
existente seguía con el patrón roto habría sido dejar la misma trampa activa
para la próxima vez que alguien la use.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-270 | `scripts/ampliar-orcid-afiliacion.ps1`, nuevo, sigue el patrón de `consultar-scopus.ps1`: credenciales en texto visible, con validación de longitud mínima | Mismo bug de pegado ya diagnosticado (D-257); construir tooling nueva con el patrón roto habría sido repetir un error ya identificado |
| D-271 | `scripts/verificar-orcid.ps1` deja el prompt oculto por el mismo motivo, aunque no era lo pedido esta sesión | Comparte credenciales con la herramienta nueva de T-19: dejarlo roto mientras se corrige todo lo demás alrededor no tenía sentido, y ya estaba señalado como «hallazgo transferible» sin corregir desde `D-259` |
| D-272 | `orcid_afiliacion.py` no cachea en disco, a diferencia de los otros cuatro conectores | El registro de ORCID cambia con el tiempo y ese es el punto de volver a correrlo; cachear escondería justamente lo que T-19 busca encontrar. Se documentó la asimetría en `docs/OPERACION.md` en vez de dejarla implícita |

### Archivos creados o modificados

```
scripts/ampliar-orcid-afiliacion.ps1   nuevo · asistente de Windows para T-19
scripts/verificar-orcid.ps1            credenciales en texto visible (mismo fix que D-257)
Makefile                               nuevo objetivo `orcid-afiliacion`
docs/OPERACION.md                      Paso 5: orcid_afiliacion.py añadido; corregido
                                         «los tres» → «los cuatro/cinco» (arrastraba un error
                                         desde que se añadió scopus_api.py sin actualizar el conteo)
```

### Verificación

`orcid_afiliacion.py --test`: 9 casos, todos OK (verificado antes de construir
el asistente). El asistente en sí no se pudo probar de punta a punta: exige
una consola de Windows interactiva y credenciales de ORCID que no están en
este entorno — mismo límite que ya aplica a todos los `.ps1` de este
proyecto.

### Supuestos descartados durante la sesión

| Supuesto | Qué pasó |
|---|---|
| «`docs/OPERACION.md` decía "los tres" y era correcto» | **Falso.** Ya eran cuatro conectores documentados ahí (se añadió `scopus_api.py` en una sesión anterior sin actualizar el conteo). Corregido al pasar por el mismo párrafo |

### Ambigüedades abiertas

- Si el usuario tiene ya credenciales de ORCID (`ORCID_CLIENT_ID`/`SECRET`) — no se le preguntó todavía; las necesita para correr `ampliar-orcid-afiliacion.ps1`.
- Las de siempre: rotación de la API Key de Scopus, ventana 2023-2025 vs. 2026, `T-02`, `T-06`, `T-10`, `T-13`.

### Próximo paso recomendado

Que el usuario confirme si tiene credenciales de ORCID y corra
`scripts\ampliar-orcid-afiliacion.ps1` en su máquina. El resultado (candidatos
nuevos, si los hay) se revisa después con `scripts\revisar-identidad.ps1`,
que ya fusiona correctamente (`D-266`).

---

## Cierre · T-19 corrido, un stash con el bug ya conocido descartado, y 0 candidatos que sí tienen explicación

El usuario tenía credenciales de ORCID y corrió
`scripts\ampliar-orcid-afiliacion.ps1` sin fricción — funcionó a la primera.
Antes de llegar ahí, `git pull` en su máquina chocó con cambios locales sin
comitear en los mismos archivos que esta sesión ya había corregido
(`config/identidades_consolidadas.yml` y compañía). El usuario confirmó no
haber corrido nada. Se investigó con `git stash show --stat` y
`git show "stash@{0}:..."`: el stash contenía **16 grupos** de consolidación
— el mismo estado dañado ya diagnosticado y revertido antes en esta sesión
(`D-263`), no trabajo nuevo del usuario. Se descartó con `git stash drop`
después de confirmarlo, no antes. Sigue sin explicación firme de cómo llegó
ahí sin que el usuario ejecutara nada — candidato más probable: alguna
sincronización o herramienta local tocó el archivo, no algo que el usuario
hiciera a propósito.

Ya con el repositorio sincronizado, la consulta real de T-19 dio **0
candidatos nuevos** de 347 firmas cruzadas contra 630 titulares. Antes de
aceptarlo como resultado válido se verificó que no fuera consecuencia de
un error de aplicación: de los 18 candidatos que este método ya había
encontrado en rondas anteriores, 16 estaban decididos desde el 2026-08-05 y
ya estaban en `data/enriched/authors_orcid.csv` desde antes de esta sesión
— por eso `apply_decisions.py` sólo contó «2 asignaciones nuevas» al
aplicar el CSV de hoy, no 18: los otros 16 no eran nuevos, sólo se leían de
nuevo. Confirmado con `grep` directo sobre `authors_orcid.csv`: las cinco
firmas verificadas al azar están, con la fuente correcta. El 0 de hoy es un
resultado real: agotadas las coincidencias de nombre+inicial entre las
firmas restantes sin ORCID y el registro público.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-273 | Un stash con contenido sospechoso se inspecciona (`git stash show --stat`, `git show stash@{0}:archivo`) ANTES de descartarlo, nunca después | Es lo que permitió confirmar que no había trabajo del usuario que perder, en vez de asumirlo |
| D-274 | Un resultado de «0» en un conector no se reporta sin verificar que no sea consecuencia de una aplicación incompleta | La diferencia entre «0 candidatos porque ya no quedan» y «0 candidatos porque algo falló aplicando lo anterior» sólo se distingue verificando el archivo de salida real, no leyendo el resumen impreso por el script |

### Verificación

`git show "stash@{0}:config/identidades_consolidadas.yml" \| grep -c canonica` → 16, confirmando el estado dañado antes de dropear. `grep` de 5 firmas «Candidato por afiliación» contra `authors_orcid.csv`: las 5 presentes con fuente «Revisión humana (candidato por afiliación confirmado)». Fechas de las 18 decisiones cruzadas contra el CSV original: 16 con fecha 2026-08-05, 2 con fecha 2026-08-26 — coincide exacto con «asignaciones nuevas: 2» del `apply_decisions.py` de hoy.

### Archivos creados o modificados

```
PLAN.md   T-19 actualizado: corrida del 2026-08-26, 0 candidatos nuevos, con la explicación
```

### Ambigüedades abiertas

- Sigue sin saberse cómo llegaron cambios locales sin comitear a la máquina del usuario sin que corriera nada. No bloqueó nada esta vez porque se detectó y descartó a tiempo.
- Las de siempre: rotación de la API Key de Scopus, ventana 2023-2025 vs. 2026, `T-02`, `T-06`, `T-10`, `T-13`.

### Próximo paso recomendado

T-19 queda en su techo actual para este método (afiliación declarada);
reintentar más adelante cuando el registro de ORCID tenga gente nueva.
Preguntar al usuario cuál de los pendientes restantes (`T-02`, `T-06`,
`T-10`, `T-13`) quiere atacar, o si prefiere cerrar la sesión aquí.

---

## Cierre · Auditoría de la sesión: dos errores reales encontrados, ~200 líneas de duplicación eliminadas

El usuario pidió una auditoría completa del trabajo de la sesión: errores,
mejoras, reducción de extensión, y evaluación de APIs. Revisión ejecutada
directamente (sin sub-agente, para no depender de presupuesto de API que ya
había fallado una vez esta sesión), con verificación real —no sólo lectura—
usando un intérprete de PowerShell descargado para la ocasión.

### Errores encontrados y corregidos

1. **`consultar-scopus.ps1` con dos mensajes obsoletos**: el comentario de
   cabecera seguía diciendo «pide la API Key de forma oculta» después de
   que el cuerpo del script cambiara a texto visible (D-257); y el mensaje
   final seguía diciendo «coincide con el universo publicado (823)» después
   de que `scopus_api.py` cambiara la base de comparación a 818
   (commit `4fd12e9`, esta misma sesión). Ninguno afectaba la lógica, pero
   ambos habrían confundido a quien los leyera.
2. **Asimetría de robustez**: el `insttoken` opcional de `consultar-scopus.ps1`
   no tenía la misma validación de longitud mínima que la API Key —un
   pegado fallido ahí habría mandado un insttoken de 1 carácter a la API
   sin ningún aviso.

### Mejora ejecutada: módulo compartido para los cuatro asistentes de PowerShell

Los cuatro `.ps1` repetían textualmente las mismas ~80 líneas (detección de
Python evitando el atajo de la Microsoft Store, instalación de dependencias,
las cuatro funciones de mensaje). Nuevo `scripts/_comun.ps1`, con
`Titulo`/`Ok`/`Aviso`/`Malo`, `Entrar-Raiz`, `Buscar-Python`,
`Asegurar-Dependencias` y `Pedir-Credencial` (esta última generaliza la
validación de longitud mínima que ya existía repetida para API Key,
Client ID/Secret e insttoken). Cada script pasa a dot-sourcing (`. "$PSScriptRoot\_comun.ps1"`)
en vez de redefinir todo.

**Medido**: los 4 scripts sumaban ~825 líneas con duplicación; ahora suman
517 + 144 del módulo compartido = 661 — una reducción neta de ~200 líneas
(~24 %), y una corrección futura de la detección de Python ya sólo exige
tocar un archivo, no cuatro (que es exactamente el modo en que el error del
"823" sobrevivió sin corregirse: se arregló en un lugar y no en el otro que
decía lo mismo).

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-275 | Los asistentes de PowerShell comparten lógica vía `scripts/_comun.ps1` con dot-sourcing, no copia-y-pega | La duplicación ya causó un bug real esta sesión (mensaje "823" corregido en un lugar, no en el otro). Un módulo compartido lo hace estructuralmente imposible la próxima vez |
| D-276 | Las funciones compartidas devuelven valores con `return`, nunca usan `$script:` para comunicarse con quien las llama | `$script:` dentro de una función definida en un archivo dot-sourced resuelve contra el archivo donde se DEFINIÓ la función, no contra quien la llama — es ambiguo entre versiones de PowerShell y no vale la pena arriesgarlo |
| D-277 | La revisión de seguridad y esta auditoría se hicieron sin sub-agente cuando el sub-agente previo falló por límite de cuenta | Reintentar el mismo tipo de llamada que ya falló por presupuesto no es una estrategia; hacer el trabajo directamente sí lo es |

### Archivos creados o modificados

```
scripts/_comun.ps1                     nuevo · funciones compartidas
scripts/consultar-scopus.ps1           usa el módulo; corregidos los 2 mensajes obsoletos;
                                         insttoken ahora valida longitud
scripts/ampliar-orcid-afiliacion.ps1   usa el módulo
scripts/verificar-orcid.ps1            usa el módulo
scripts/revisar-identidad.ps1          usa el módulo
src/enrich/scopus_api.py               texto de ayuda de --count aclarado
```

### Verificación

No se pudo ejecutar PowerShell en ninguna sesión anterior de este proyecto
(el contenedor no lo traía). Se descargó el binario oficial de PowerShell
7.4.6 para Linux sólo para esta verificación. Confirmado con el parser real
del lenguaje (`[System.Management.Automation.Language.Parser]::ParseFile`)
que los 5 archivos no tienen errores de sintaxis. Más importante: se
ejecutaron los 4 scripts de punta a punta hasta el paso de credenciales
(con un Python real en el PATH, con pandas/PyYAML instalados) y los cuatro
llegaron correctamente a "Dependencias listas" y a la autoprueba —
confirmando que el mecanismo de dot-sourcing y paso de valores por `return`
funciona de verdad entre archivos, no sólo que compila. `Pedir-Credencial`
se probó aislada con un caso válido y uno corto: el corto se detiene con el
mensaje correcto y código de salida 1, como el original.

La invocación real de Python dentro de cada script (`& $py src\enrich\...`)
falló en este contenedor Linux porque Python no interpreta rutas con `\`
como separador — comportamiento correcto y sin cambios en Windows real (ya
confirmado en vivo por el usuario varias veces esta sesión con las mismas
líneas), y no es código que este commit haya tocado.

### Supuestos descartados durante la sesión

| Supuesto | Qué pasó |
|---|---|
| «Sin PowerShell instalado, esta clase de refactorización no se puede verificar, sólo leer con cuidado» | **Falso.** El binario de PowerShell para Linux se descarga en segundos y permite parsear y ejecutar de verdad, no sólo inspeccionar visualmente |

### Ambigüedades abiertas · pendiente de información del usuario

- **SciVal API**: el usuario dijo antes que tenía «todas las APIs aprobadas» al hablar de Scopus y SciVal juntos. Si eso incluye SciVal específicamente (no sólo Scopus), se podría construir un conector análogo a `scopus_api.py` para desbloquear `T-13` (semántica del percentil) y `X-01` (autocitación, `V2_BACKLOG.md`). No se construye sin confirmar primero: `docs/FUENTES_Y_APIS.md` §3.8 ya declara esto como bloqueante sin confirmar, y adivinar el contrato de una API nueva viola `CLAUDE.md`.
- El resto de las integraciones propuestas en `FUENTES_Y_APIS.md` §3 (Unpaywall, SciELO, Altmetric, DataCite, OpenAIRE, Semantic Scholar, Europe PMC, Wikidata) siguen exactamente como estaban: evaluadas, ninguna confirmada, nada nuevo que integrar sin más información del usuario.

### Próximo paso recomendado

Preguntar al usuario si su acceso API incluye SciVal específicamente. Si sí,
construir el conector análogo a `scopus_api.py` desbloquea dos pendientes de
una vez (`T-13`, `X-01`). Si no, no hay más integración de API accionable
hoy sin nueva información.

---

## Cierre · SciVal API probada por curl directo: sin entitlement, no se construye el conector

El usuario dijo tener «todas las APIs aprobadas», lo que sugería acceso a
SciVal además de Scopus. A diferencia de la Scopus Search API —muy
documentada, alta confianza al escribir el conector sin poder probarlo—, la
API de SciVal es un producto de Elsevier mucho menos público, y la
confianza en su endpoint exacto no alcanzaba para escribir código de red
sin más: hacerlo habría sido exactamente el tipo de suposición que
`CLAUDE.md` prohíbe. Se le preguntó al usuario por el endpoint documentado
en su portal; no supo encontrarlo. En vez de mandarlo a una búsqueda sin
garantía de éxito, se probó empíricamente con `curl` —la misma táctica que
ya había funcionado para diagnosticar Scopus— contra la ruta más probable
según el conocimiento disponible.

### El resultado, y por qué es información real y no un callejón sin salida

`GET analytics/scival/publication/metrics?metricTypes=OutputsInTopCitationPercentiles`
respondió **403 `ENTITLEMENTS_ERROR`**, no 404. La distinción es la señal:
un 404 diría "esa ruta no existe"; un 403 de entitlements dice "esa ruta
existe, la reconozco, y esta clave no está autorizada". Confirma dos cosas
a la vez: que la ruta probada es plausible como punto de partida futuro, y
que el supuesto "todas las APIs aprobadas" del usuario cubre los productos
de Scopus pero no se extiende a SciVal, que Elsevier licencia aparte —
exactamente lo que `V2_BACKLOG.md` §V2-23 ya declaraba como bloqueante
antes de esta sesión.

**No se escribió `src/enrich/scival_api.py`.** Sin poder confirmar el
contrato completo (headers adicionales, forma exacta de la respuesta,
parámetros válidos) contra una entitlement real, construir el conector
habría sido escribir código no verificable — ni siquiera con el patrón
defensivo de `ror_institucion.py`, porque ahí al menos la lógica de
extracción se podía probar con fixtures fieles a una API bien documentada.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-278 | No se construye el conector de SciVal sin entitlement confirmada, aunque el endpoint probado parezca válido | Un 403 de entitlements no es lo mismo que un contrato verificado: sólo dice que la ruta existe, no cómo luce una respuesta exitosa. Escribir el parseo sin eso sería adivinar la forma del JSON |
| D-279 | El endpoint probado (`analytics/scival/publication/metrics`) se deja documentado en `V2_BACKLOG.md` y `FUENTES_Y_APIS.md` como punto de partida | Si la entitlement se concede más adelante, no hay que redescubrir la ruta desde cero |
| D-280 | Se corrigió la afirmación «todas las APIs de la suscripción aprobadas» en `FUENTES_Y_APIS.md` §3.7 para aclarar que aplica a Scopus, no a SciVal | Quedaba escrita como un hecho general sin el matiz que esta prueba reveló; dejarla así habría sido una afirmación más amplia de lo que se verificó |

### Archivos creados o modificados

```
docs/V2_BACKLOG.md       V2-23 actualizado con el resultado del curl (403 ENTITLEMENTS_ERROR)
docs/FUENTES_Y_APIS.md   §3.7 corregida (matiz Scopus vs SciVal); §3.8 con el resultado probado;
                          fecha de actualización del documento
```

### Verificación

`curl -v` directo del usuario contra `api.elsevier.com` con su API Key real
de Scopus, ruta y parámetros propuestos por Claude. Respuesta HTTP completa
revisada: código 403, `X-ELS-Status: ENTITLEMENTS_ERROR`, sin
`X-RateLimit-*` relevante para este caso. No se pudo verificar más allá de
esto sin la entitlement.

### Supuestos descartados durante la sesión

| Supuesto | Qué pasó |
|---|---|
| «Todas las APIs de la suscripción aprobadas» incluye SciVal | **Falso, probado directamente.** Cubre Scopus; SciVal es una licencia aparte que Elsevier no concedió a esta clave |
| «Si el usuario no encuentra el endpoint en el portal, hay que seguir buscando ahí» | **Innecesario.** Una prueba empírica directa con `curl` fue más rápida y más concluyente que una búsqueda de navegación en un portal que ninguno de los dos podía ver con certeza |

### Ambigüedades abiertas

- Otra vez: el usuario pegó su API Key real (`e6b398...`) en el chat, la misma de antes — sigue sin rotarla pese a haberlo pedido dos veces ya. No se puede forzar; sólo recordarlo.
- Si vale la pena que el usuario gestione la entitlement de SciVal con Elsevier/la biblioteca de la UFT — queda como su decisión, no de esta sesión.
- Las de siempre: ventana 2023-2025 vs. 2026, `T-02`, `T-06`, `T-10`.

### Próximo paso recomendado

Sin acción de código pendiente sobre SciVal. Si el usuario gestiona la
entitlement con Elsevier, retomar con el endpoint ya documentado en
`V2_BACKLOG.md` §V2-23. Recordar la rotación de la API Key una vez más, sin
insistir más allá de eso.

---

## Cierre · T-13 cerrado sin acceso a la API: confirmación documental en vez de empírica

El usuario pidió seguir con los pendientes. Sin entitlement de SciVal (cierre
anterior), `T-13` parecía atado a esa API — pero `T-13` no pedía "consultar
la API de SciVal", pedía "confirmar la semántica del percentil contra
documentación oficial de Elsevier". Son cosas distintas: la documentación
pública de Elsevier no requiere entitlement, sólo requiere encontrarla.

### El camino

1. **El nombre exacto de columna** ya vivía en el propio código del
   proyecto: `grep` sobre `src/audit/02_reconcile_sources.py` y
   `src/analysis/indicator_feasibility.py` confirmó
   `"Outputs in Top Citation Percentiles, per percentile"` como el
   encabezado real leído del export, no una paráfrasis.
2. Búsqueda de esa cadena exacta vía `WebSearch`/`WebFetch`. Varios dominios
   de Elsevier (`service.elsevier.com`, `elsevier.libguides.com`,
   `manchester-uk.libanswers.com`) devolvieron `EGRESS_BLOCKED` en
   `WebFetch` — política de red del entorno, no error transitorio. Por
   `/root/.ccr/README.md`, un 403/407 de política no se reintenta: se buscó
   la misma información por otra vía en vez de insistir contra el bloqueo.
3. Un tercero independiente, [cu-library/scival-export-tools](https://github.com/cu-library/scival-export-tools)
   (herramienta de GitHub que procesa exports reales de SciVal, subcomando
   "Per Researcher"), confirmó que el nombre de columna es real y se usa en
   la práctica — no sólo lo que trae el archivo de este proyecto.
4. `WebSearch` sí devolvió el resumen del SciVal Support Center de Elsevier
   (`a_id/28193`) para la métrica "Outputs in Top Citation Percentiles":
   las publicaciones globales de Scopus se ordenan de mayor a menor citación
   (o FWCI si es field-weighted) y se dividen en 100 percentiles; el campo
   indica en cuál de los umbrales de top 1 %/5 %/10 %/25 % más citadas cae
   cada publicación.

### Por qué esto cierra T-13 sin ser razonamiento circular

La semántica «top X %» de Elsevier no deja ambigüedad sobre la dirección:
top 1 % sólo puede ser la posición más alta, nunca la más baja. Que las 5
publicaciones más citadas del corpus (evidencia empírica del 2026-08-03)
caigan en los valores 1-4 y las no citadas en el máximo observado (78) es
exactamente el patrón que esa semántica predice de forma independiente —
la documentación no se derivó de los datos propios, así que confirmarla
contra ellos es una prueba real, no un espejo. Se documentó también la
salvedad honesta: no se encontró una tabla literal «valor = 1 → top 1 %»
fila por fila para esta columna de exportación específica (distinta de la
métrica agregada del mismo nombre, que cuenta publicaciones en vez de
etiquetar cada una); la confirmación es sobre la metodología del campo, no
una cita textual del mapeo exacto.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-281 | `T-13` se cierra con evidencia documental pública, sin necesitar la API de SciVal | El pendiente pedía documentación oficial, no una consulta autenticada; la documentación de soporte de Elsevier es pública |
| D-282 | Se acepta la confirmación de nombre de columna de una herramienta de terceros (`cu-library/scival-export-tools`) como evidencia válida, no como sustituto de la fuente primaria | Es independiente del dataset del proyecto y demuestra que el nombre de columna se usa en exports reales, reduciendo el riesgo de que sea un artefacto propio |
| D-283 | Se documenta explícitamente la salvedad de que no hay cita textual del mapeo valor→porcentaje línea por línea | Afirmar más certeza de la que existe violaría `CLAUDE.md`; la salvedad queda en `docs/METHODOLOGY.md` §7 bis para quien audite después |
| D-284 | `X-01` (autocitación) sigue bloqueado por la falta de entitlement de SciVal; `T-13` ya no depende de esa API | Son pendientes distintos que compartían el mismo bloqueo aparente; separarlos evita que uno quede preso del otro innecesariamente |

### Archivos creados o modificados

```
docs/METHODOLOGY.md      §7 bis reestructurada: "evidencia empírica" + "confirmación documental",
                          citas a Elsevier (a_id/28193) y a cu-library/scival-export-tools, salvedad honesta
PLAN.md                  T-13 tachado y cerrado (2026-08-26), con el razonamiento resumido
docs/V2_BACKLOG.md       tabla de pendientes (línea ~102) T-13 cerrado; fila V2-23 (API SciVal) actualizada:
                          ya no depende de T-13, sólo de X-01
docs/FUENTES_Y_APIS.md   §3.8 "Qué desbloquearía" corregido: T-13 retirado de la lista de pendientes
                          que dependen de la API de SciVal
```

### Verificación

`grep -n -B2 -A8 "I-05" config/indicators.yml` confirmó que la definición
del indicador ya tenía `advertencia: null` — no necesitaba una salvedad
nueva, porque la confiabilidad ya estaba declarada como alta desde antes.
`grep -rln "T-13\|determinad. empíricamente" --include="*.md" --include="*.yml" .`
localizó todas las referencias restantes antes de dar el cierre por
completo: `STATE.md` (se regenera, no se edita a mano), `PLAN.md`,
`docs/METHODOLOGY.md`, `docs/FUENTES_Y_APIS.md`, `docs/V2_BACKLOG.md` — las
cinco revisadas y consistentes entre sí.

### Supuestos descartados durante la sesión

| Supuesto | Qué pasó |
|---|---|
| «T-13 sólo se puede cerrar con acceso a la API de SciVal» | **Falso.** El pendiente pedía documentación oficial, y la documentación de soporte de Elsevier es pública; no necesita entitlement ni autenticación |
| «Un `EGRESS_BLOCKED` en `WebFetch` es un fallo a reintentar» | Es una política de red explícita del entorno (`/root/.ccr/README.md`), no un error transitorio — se buscó la misma información por `WebSearch` en vez de insistir |

### Ambigüedades abiertas

- La salvedad de `docs/METHODOLOGY.md` §7 bis sigue abierta a propósito: si
  en algún momento aparece la tabla oficial línea por línea del mapeo
  valor→porcentaje, reemplaza esa salvedad por una cita directa.
- Las de siempre, sin cambios: `T-02` (falta enviar la hoja de validación de
  unidades a la UFT), `T-06` (espera una reexportación nueva de Scopus con
  fecha de corte propia), `T-10` (decisión de Pablo sobre publicar la red de
  coautoría), API Key de Scopus sin rotar tras tres exposiciones en el chat.

### Próximo paso recomendado

Pendientes activos tras este cierre: `T-02`, `T-06`, `T-10`, `T-19` (en su
techo por ahora). De estos, `T-02` y `T-10` son los únicos que no dependen
de un evento externo (reexportación futura, o candidatos nuevos en el
registro de ORCID) — son los que tienen sentido preguntarle al usuario cuál
retomar primero.

---

## Cierre · T-10: C-05 (red de coautoría) publicada, reactiva a los filtros

El usuario pidió revisar la red antes de decidir. Se le mandó una captura del
visor interno (`internal/red_coautoria.html`, regenerado con la consolidación
del día) y las cifras actuales (538 personas, 616 aristas, 267 componentes,
41 la mayor, 293 comunidades Louvain, 196 sin coautoría). Al revisar, salió
un hallazgo que **no** dependía de una decisión del usuario: el bloqueo
técnico original de `C-05` —heredaría variantes de nombre sin resolver— ya
no existía, porque `T-03` cerró en el cierre anterior de esta misma sesión.
Se corrigieron tres referencias que seguían dando por abierto un pendiente ya
cerrado (`config/indicators.yml`, `docs/V2_BACKLOG.md`,
`src/review/vista_red.py`) — commit `95416a3`, antes de tocar la decisión de
fondo.

Después, pedido explícito: **"Ok. Publícalo."** Antes de escribir código se
preguntó dos veces, porque cada respuesta cambiaba el trabajo de forma real:

1. **¿Con comunidades Louvain visibles, o sólo componentes?** El usuario
   eligió comunidades visibles — la opción que exige declarar con más cuidado
   que una comunidad detectada no es un grupo de investigación real.
2. **¿Reactivo a los filtros de la página (año, unidad…), o estático?**
   Aquí el hallazgo fue de arquitectura: el resto de `colaboracion.html`
   recalcula sus indicadores EN VIVO en el navegador a partir de
   `publications.json`, así que hacer C-05 reactivo exigía reimplementar en
   JavaScript la construcción del grafo y Louvain — el mismo algoritmo que
   hasta hoy sólo vivía, probado, en `grafo_coautoria.py`. Se explicó el
   riesgo (una segunda implementación que puede divergir de la que ya se
   auditó) y la alternativa (módulo estático, sin ese riesgo). El usuario
   eligió **reactivo**, sabiendo el costo.

### Cómo se resolvió el riesgo de divergencia, en vez de aceptarlo sin más

Se escribió `web/assets/js/grafo.js`: un puerto función por función de
`construir()`, `componentes()` y `comunidades()` de `grafo_coautoria.py`,
mismo orden de iteración y mismo criterio de desempate en Louvain. No se
declaró "fiel" de palabra: se verificó. Un script Node cargó el mismo
`publications.json`/`authors.json` que vería el navegador, corrió el puerto
JS sobre el corpus completo sin filtrar, y comparó nodo por nodo, arista por
arista, partición por partición contra `data/interim/coauthorship_graph.json`
(la salida canónica de Python). Coincidencia exacta: mismos 538 nodos, 616
aristas con el mismo peso y peso fraccional, misma partición de componentes,
misma partición de comunidades. Ahí, y sólo ahí, se consideró seguro dejar
que el JS recalculara en producción.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-285 | `C-05` se publica con comunidades Louvain visibles, declaradas explícitamente como heurística del algoritmo y no como veredicto sobre grupos de investigación reales | Elección del usuario tras ver el riesgo de malinterpretación explicado; la alternativa (sólo componentes) eliminaba el riesgo pero también la información |
| D-286 | `C-05` se publica reactivo a los filtros de `colaboracion.html`, igual que el resto de los indicadores de esa página | Elección del usuario, sabiendo que exigía reimplementar la construcción del grafo y Louvain en JavaScript — la alternativa (estático) era más simple pero rompía la consistencia de UX con el resto de la sección |
| D-287 | El puerto JS (`grafo.js`) no se declara fiel de palabra: se verifica programáticamente contra la salida canónica de Python sobre el corpus completo (nodos, aristas, pesos, ambas particiones) antes de dejarlo correr en producción | Es la única forma de cerrar honestamente el riesgo de divergencia que motivó la pregunta al usuario — una afirmación sin verificar habría sido exactamente el tipo de promesa sin evidencia que `CLAUDE.md` prohíbe |
| D-288 | `01_publications.py` excluye las firmas E-09 encoladas de `autores_uft`, cerrando una brecha que existía desde antes de esta sesión (sólo `grafo_coautoria.py`, capa interna, las excluía) | Publicar C-05 hace que un fragmento de afiliación colado como autor deje de ser un error cosmético en una tabla y pase a dibujar colaboraciones falsas en un grafo público; la ventana para que esto ocurra en una futura ronda de revisión se cierra ahora, aunque hoy sea un no-op |
| D-289 | La ficha de autor deja de decir "diferido a V2" en Coautoría y muestra la lista real de coautores internos de esa persona | La afirmación anterior se volvió falsa en cuanto `C-05` se publicó; dejarla habría sido una contradicción activa entre dos páginas del mismo sitio |

### Qué se construyó

- **`web/assets/js/grafo.js`** (nuevo): el puerto verificado arriba.
- **`web/assets/js/vista_explorador.js`**: `corteRed()` — el módulo de C-05
  dentro del explorador reactivo. Construye el grafo del recorte vigente,
  recorta el DIBUJO a componentes de 5+ personas (mismo criterio que
  `internal/red_coautoria.html`, para no repetir el error ya resuelto ahí de
  un anillo con cientos de grupos ilegible), pero la tabla de aristas y las
  cifras de arriba cubren a todos. Cuatro vistas —Nodos, Matriz, Arcos,
  Tabla— reutilizando el conmutador genérico `.vistas button[data-vista]`
  que ya engancha `paginas.js`: no hizo falta escucha nueva. Maneja el caso
  de un recorte tan angosto que ninguna componente llegue a 5 (sin
  `Math.min`/`Math.max` sobre arreglos vacíos rotos en silencio).
- **`web/assets/js/core.js`**: comentario de cabecera de `red()` actualizado
  (decía "C-05 NO se publica").
- **`config/indicators.yml`**: `C-05.publicar: true`, advertencia reescrita
  para el estado publicado (antes describía el diferimiento).
- **`src/build/02_indicators.py`**: exporta `C-05` a `series.json`
  reutilizando `grafo_coautoria.construir/componentes/comunidades`
  directamente (mismo código, no una tercera cuenta) para el resumen y el
  sello de procedencia (`n=538`, `cubiertas=342`, `unidad="personas"` —
  necesitaba una sobrescritura explícita, igual que ya hacía `P-07`, porque
  C-05 no tiene `denominador` en publicaciones).
- **`src/build/01_publications.py`**: `autores_uft` ahora excluye las firmas
  E-09 encoladas (fragmentos de cadena de afiliación) antes de que lleguen al
  público — antes sólo `grafo_coautoria.py` (capa interna) las excluía. Hoy
  es un no-op (0 encoladas), pero sin esto una futura ronda de revisión
  podría dejar un fragmento firmando como coautor en el sitio en vivo.
- **`src/build/prerender.mjs`**: pasa el mismo mapa persona→unidad al
  prerenderizado que arma `paginas.js` en el navegador, para que no diverjan.
- **`web/assets/js/paginas.js`** (ficha de autor): la sección "Coautoría",
  que decía "diferido a V2" desde julio, ahora lista la coautoría interna
  real de esa persona —cruzando sus EID contra `autores_uft` de cada
  publicación—, con enlace a la ficha de cada coautor.
- **`docs/GLOSSARY.md`**: entrada nueva, "Componente y comunidad (red de
  coautoría)", con el ejemplo de dos triángulos unidos por un vínculo débil
  —una componente, dos comunidades— para que un lector sin trasfondo técnico
  entienda la distinción sin tener que leer código.

### Verificación

Suite de paridad JS-vs-Python (arriba) · `python3 src/build/build_all.py`
completo (auditoría, factibilidad, 4 builds, compuerta de capas: 0 fallas) ·
`python3 src/verify/higiene.py`: sin fallos, y confirma que `data-indicadores`
de `colaboracion.html` referencia un `C-05` que existe en `series.json` y en
el HTML prerenderizado · navegador real (Playwright + Chromium headless):
las cuatro vistas cambian correctamente, filtrar por año 2024 recalcula el
grafo completo (grupos y cifras nuevas, no las del corpus total), el tooltip
muestra nombre + unidad + grado, sin errores de consola, tema oscuro
correcto.

### Archivos creados o modificados

```
web/assets/js/grafo.js              nuevo · puerto verificado de grafo_coautoria.py
web/assets/js/vista_explorador.js   corteRed(), tablaRed(), C-05 en SECCIONES.colaboracion
web/assets/js/paginas.js            unidadPorPersona cargado una vez; ficha de autor con coautoría real
web/assets/js/core.js               comentario de cabecera de red() actualizado
config/indicators.yml               C-05 publicar: true
src/build/01_publications.py        autores_uft excluye E-09 encoladas
src/build/02_indicators.py          C-05 en series.json (resumen + procedencia)
src/build/prerender.mjs             mismo mapa unidadPorPersona que el navegador
src/build/build_all.py              comentario de cabecera actualizado
src/build/grafo_coautoria.py        docstring y campo "capa" actualizados
src/build/common_build.py           FUENTE_POR_INDICADOR incluye C-05
src/review/vista_red.py             docstring y aviso: ya no es "antes de publicar", es la herramienta de revisión
src/analysis/indicator_feasibility.py  registro de C-05 corregido (decía "Diferido hasta T-03")
Makefile                            comentario de `make red` actualizado
docs/GLOSSARY.md                    nueva entrada "Componente y comunidad"
docs/AUTHOR_PROFILE.md              sección Coautoría actualizada
docs/ORCID_GUIDE.md                 referencia a C-05 actualizada
docs/INDICATORS.md                  fila C-05 y nota de "Excluidos de V1"
docs/V2_BACKLOG.md                  C-05 sale de "Indicadores diferidos"
PLAN.md                             T-10 cerrado
```

### Supuestos descartados durante la sesión

| Supuesto | Qué pasó |
|---|---|
| «"Publícalo" es un simple `publicar: true`» | **Falso.** La arquitectura del explorador (recalcular en vivo desde `publications.json`) obligaba a elegir entre reimplementar Louvain en JS o quedarse estático — una decisión de ingeniería real, no una formalidad |
| «Reimplementar un algoritmo en un segundo lenguaje es aceptar divergencia» | Se pudo VERIFICAR la fidelidad exacta contra el Python canónico en vez de sólo declararla — el riesgo señalado se cerró con evidencia, no con cuidado narrativo |

### Ambigüedades abiertas

- El tamaño de `colaboracion.html` subió a ~403 KB (36,6 KB comprimido): las
  cuatro vistas de C-05 se prerenderizan todas a la vez, para que la página
  funcione sin JavaScript. Aceptable por ahora (T-18 ya estableció que el
  peso comprimido es la cifra que importa), pero si crece más vale la pena
  revisar.
- Las de siempre, sin cambios: `T-02`, `T-06`, API Key de Scopus sin rotar.

### Próximo paso recomendado

`T-10` cerrado. Pendientes activos: `T-02` (enviar la hoja de validación de
unidades a la UFT), `T-06` (espera una reexportación real de Scopus), `T-19`
(en su techo). Regenerar `STATE.md`/`docs/DECISIONS.md`, confirmar
`git status`, commit y push.

---

## Cierre · T-02: hoja de validación refrescada, envío queda en manos del usuario

El usuario pidió seguir con `T-02`. `internal/validacion_unidades.md` estaba
fechado el 2026-08-19 —antes de la consolidación de identidad de esta
sesión—, así que se regeneró con `src/review/build_unit_validation.py` para
confirmar que las cifras seguían vigentes antes de darlo por listo. Sin
cambios sustantivos: 21 unidades detectadas, 4 jerarquías escuela→facultad
(3 inferidas), cobertura 63,8 % — sólo cambió la fecha del encabezado y el
orden interno de tres unidades con 1 par cada una (empate, sin significado).

Se le preguntó al usuario qué necesitaba para el paso de envío —redactar un
correo, dejar el documento listo, o nada porque él ya se encarga—. Eligió
gestionar el envío por su cuenta ("Realizaré el trabajo manual"): no
correspondía inventarle un destinatario ni redactar en su nombre una
comunicación institucional sin que él lo pidiera.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-290 | No se redacta ni se envía ninguna comunicación a la UFT sin pedido explícito del usuario | Enviar una solicitud institucional es una acción externa y consecuente que sólo le corresponde decidir a él; adivinar un destinatario dentro de la UFT habría sido inventar un dato que `CLAUDE.md` prohíbe |
| D-291 | La hoja de validación se regenera antes de considerarla "lista para enviar", aunque el contenido no cambie | Una hoja fechada antes de la consolidación de identidad de hoy podía estar describiendo datos ya superados; confirmar que no cambió es parte de declarar el documento vigente, no un paso opcional |

### Archivos creados o modificados

```
internal/validacion_unidades.md   regenerado: fecha 2026-08-26, cifras confirmadas sin cambios
```

### Verificación

`python3 src/review/build_unit_validation.py` y `git diff` del resultado:
sólo la fecha del encabezado y un empate de orden entre tres unidades de 1
par cambiaron: unidades detectadas (21), jerarquías (4, 3 inferidas) y
cobertura (63,8 %) idénticas a la versión del 2026-08-19.

### Ambigüedades abiertas

- El envío efectivo a la UFT queda fuera de esta sesión: lo gestiona el
  usuario por su cuenta, sin fecha declarada.
- Las de siempre, sin cambios: `T-06`, `T-19` en su techo, API Key de Scopus
  sin rotar.

### Próximo paso recomendado

Ninguna acción de código pendiente sobre `T-02`. Cuando el usuario tenga
respuesta de la UFT, las correcciones entran en `config/matching_rules.yml`
según ya documenta la propia hoja. Mientras tanto, quedan `T-06` y `T-19`
como los únicos pendientes activos, ambos a la espera de un evento externo.

---

## Cierre · T-02: herramienta interactiva de validación de unidades

El usuario aclaró el pedido anterior: no quería que se redactara un correo,
sino que él mismo hará la identificación con su propio conocimiento
institucional, y pidió "establecer un medio" para hacerlo. Un documento
Markdown con casillas `☐ sí ☐ no` para marcar a mano no es un medio — es
una lectura. Se construyó el mismo patrón que ya existe para la revisión de
identidad de autor (`build_review.py` → `revision_identidad.html` → CSV →
`apply_decisions.py`), aplicado a T-02 en vez de inventar uno nuevo.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-292 | Se reutiliza el patrón HTML interactivo + CSV exportado + script de aplicación ya establecido para la revisión de identidad, en vez de diseñar un mecanismo nuevo para T-02 | Dos herramientas de revisión con dos interacciones distintas para el mismo tipo de tarea (marcar sí/no con evidencia delante) habría sido inconsistencia sin motivo — el patrón ya está probado, incluida la entrega dual del CSV (archivo local vs. capacidad `downloads` del anfitrión) |
| D-293 | `config/matching_rules.yml` se edita con reemplazos de texto anclados a un patrón exacto, nunca con `yaml.dump()` | El archivo tiene más comentarios de justificación que líneas de dato; volcarlo de nuevo los borraría todos. Mismo criterio que ya usa `apply_decisions.py` para sus propios archivos de salida |
| D-294 | El resultado de cada edición se valida con `yaml.safe_load()` ANTES de escribirse, nunca después | Un YAML roto detectado después de sobrescribir ya rompió el build; validar antes permite abortar sin haber tocado el archivo |
| D-295 | `vocabulario_validado_por_institucion` sólo pasa a `true` cuando TODAS las filas del CSV tienen respuesta, nunca con una validación parcial | Declarar el vocabulario validado con preguntas todavía sin contestar sería publicar una confianza que nadie dio — el mismo principio que ya rige el resto del proyecto sobre no afirmar más certeza de la que existe |
| D-296 | Al corregir el nombre de una unidad, el nombre detectado se conserva SIEMPRE como variante reconocida — nunca se borra | La afiliación cruda seguirá llegando escrita igual en cualquier reexportación futura; borrar el reconocimiento haría que esa unidad volviera a aparecer sin resolver |

### Qué se construyó

- **`src/review/build_unit_validation.py`**: además del `.md` que ya
  generaba, ahora también escribe `internal/validacion_unidades.html` — 21
  unidades + 4 jerarquías, cada una con su evidencia (afiliación real) y
  botones Sí/No, corrección de texto libre cuando corresponde, contador de
  avance, exportación a CSV. Si ya existe un CSV de una corrida anterior
  (`internal/unit_validation_decisions.csv`), sus respuestas se precargan —
  se puede responder por partes sin perder lo ya marcado.
- **`src/review/apply_unit_validation.py`** (nuevo): lee el CSV exportado y
  edita `config/matching_rules.yml` con tres operaciones posibles por
  unidad — confirmar (no toca nada), agregar como variante de una entrada
  que ya existe, o renombrar una entrada propia conservando sus variantes y
  actualizando cualquier referencia cruzada en la jerarquía — y dos por
  jerarquía: confirmar (`inferida` → `confirmada`) o corregir la facultad.
  `--test` corre 10 comprobaciones sobre un YAML sintético (sin tocar el
  archivo real); `--dry-run` muestra los cambios sin escribirlos. Deja
  respaldo en `internal/.respaldos/` antes de escribir.
- **`scripts/validar-unidades.ps1`** (nuevo): asistente para Windows, mismo
  patrón en cinco pasos que `revisar-identidad.ps1` — autoprueba, preparar
  datos, generar la página, recoger el CSV de Descargas, aplicar en seco y
  luego de verdad, reconstruir el sitio.
- **`Makefile`**: nuevo objetivo `validar-unidades`.

### Verificación

`apply_unit_validation.py --test`: 10/10. Además, tres corridas manuales
contra una COPIA de `config/matching_rules.yml` (nunca el archivo real)
cubriendo los tres casos de unidad (confirmar, variante de entrada
existente, renombrar entrada propia con referencia cruzada en jerarquía) y
los dos de jerarquía, más el caso de validación parcial (el flag global
debe quedar en `false` si falta una fila por responder) — en los tres casos
el `diff` contra el original fue exactamente el cambio esperado y nada más,
y el resultado siguió siendo YAML válido. Herramienta HTML probada en
navegador real (Playwright/Chromium): marcar sí/no, mostrar/ocultar el
campo de corrección, contador de avance, y exportación de CSV con las
columnas y valores correctos — sin errores de consola. Sintaxis de
`validar-unidades.ps1` verificada con el parser de PowerShell.

### Archivos creados o modificados

```
src/review/build_unit_validation.py    genera también internal/validacion_unidades.html
src/review/apply_unit_validation.py    nuevo · aplica el CSV a config/matching_rules.yml
scripts/validar-unidades.ps1           nuevo · asistente Windows en 5 pasos
Makefile                               nuevo objetivo validar-unidades
internal/validacion_unidades.html      generado
```

### Ambigüedades abiertas

- Ninguna corrección real se aplicó todavía: el usuario hará la
  identificación con su propio conocimiento institucional cuando tenga
  tiempo. La herramienta queda lista y probada, no usada.
- Las de siempre, sin cambios: `T-06`, `T-19` en su techo.

### Próximo paso recomendado

Ninguna acción de código pendiente. Cuando el usuario responda la hoja
(`internal/validacion_unidades.html`, o `scripts\validar-unidades.ps1` en
Windows), aplicar con `apply_unit_validation.py`, reconstruir el sitio, y
cerrar `T-02` formalmente en `PLAN.md`.

---

## Cierre · T-02: primera ronda de respuestas aplicada, un caso pausado por cruce institucional

El usuario subió `internal/unit_validation_decisions.csv` (25 filas: 21
unidades + 4 jerarquías) exportado de la herramienta. Antes de aplicar en
seco, la revisión con `--dry-run` encontró DOS fallas reales en
`apply_unit_validation.py` (escrito la sesión anterior, nunca probado
contra respuestas reales) y UNA que no era del código: un dato mal
extraído que el CSV, sin querer, habría confirmado.

### Los dos defectos del script, encontrados por el propio dry-run

1. **Colisión de variante.** La fila `School of Medicine UFT-CLC` →
   `Escuela de Medicina` habría creado una clave de vocabulario NUEVA
   llamada «Escuela de Medicina» — pero ese texto ya vivía como VARIANTE
   dentro de la entrada «Facultad de Medicina». El resultado habría dejado
   el mismo nombre registrado dos veces, con matching ambiguo entre las dos
   entradas. Se agregó `entrada_por_variante()`: antes de crear una clave
   nueva, busca si el nombre corregido ya vive como variante de OTRA
   entrada, y si es así, agrega ahí en vez de duplicar.
2. **El propio arreglo escondía un segundo bug.** «Facultad de
   Comunicaciones y Humanidades» → «Facultad de Humanidades y
   Comunicaciones» es un renombrado real, pero el nombre nuevo YA estaba
   listado como variante — de la MISMA entrada que se está corrigiendo. La
   primera versión del arreglo #1 trataba eso igual que el caso de una
   entrada ajena y no hacía el renombrado. Se corrigió comparando la
   entrada encontrada contra `nombre`: sólo se desvía a "agregar en otra
   entrada" cuando la entrada encontrada NO es la que se está corrigiendo.
   El autotest subió de 10 a 21 comprobaciones para cubrir ambos casos por
   separado — el segundo bug es la clase de error que sólo aparece
   probando el arreglo del primero contra un caso real, y por eso no lo
   había atrapado el autotest original.

### El caso que no era un bug de código

La fila `Facultad de Odontología y Ciencias de la Rehabilitación` → `no` →
`Facultad de Medicina y Salud` parecía una corrección más. La afiliación
completa detrás de esa fila es: *"Universidad San Sebastián, Facultad de
Odontología y Ciencias de la Rehabilitación, Carrera de Fonoaudiología,
Santiago, Chile, Universidad Finis Terrae, Facultad de Educación,
Psicología y Familia, Santiago, Chile"* (autor Allende-Valenzuela T.,
`internal/matching_log.csv`). Es una cadena con DOS instituciones: la
unidad "Facultad de Odontología y Ciencias de la Rehabilitación" pertenece
a la Universidad San Sebastián, no a la UFT — el extractor se quedó con el
fragmento equivocado. La unidad UFT real de ese par es "Facultad de
Educación, Psicología y Familia" (ya renombrada a "Facultad de Educación y
Ciencias Sociales" en esta misma ronda).

Aplicar la respuesta tal como venía habría fusionado un dato mal extraído
dentro de "Facultad de Medicina y Salud" — dos errores en vez de uno, y
esta vez permanente en `config/matching_rules.yml`. No es un error del
usuario: la herramienta le mostró la cadena completa como evidencia, pero
enmarcada como "¿es correcto el nombre de esta unidad?", no como "¿pertenece
esta afiliación completa a la UFT?" — la pregunta que hacía falta hacer no
era la que se hizo. Se pausó esa fila (`correcto: pendiente`, con nota) y
se excluyó de esta aplicación; el resto (24 de 25 filas) se aplicó.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-297 | La corrección de «Facultad de Odontología y Ciencias de la Rehabilitación» NO se aplica esta ronda | El texto detectado pertenece a otra institución (Universidad San Sebastián) mezclada en la misma cadena de afiliación; fusionarlo en «Facultad de Medicina y Salud» habría publicado un dato con una causa raíz distinta a la que la corrección resolvía |
| D-298 | El resto de las 24 respuestas (11 cambios reales + 8 avisos de "sin corrección utilizable" + 5 sin cambio por ser idénticas) se aplica sin esperar la fila pausada | Retener 24 respuestas claras por una fila ambigua habría sido bloquear trabajo listo por un caso que necesita una conversación aparte |
| D-299 | `apply_unit_validation.py` gana `entrada_por_variante()`, con el autotest ampliado a 21 comprobaciones | Los dos defectos sólo se manifestaban con datos reales de producción, no con el fixture sintético original; ampliar el fixture para cubrir ambos casos deja el próximo lote (la fila pausada, cuando se resuelva, u otra ronda futura) protegido contra la misma clase de error |

### Qué se aplicó

`config/matching_rules.yml`: 4 jerarquías confirmadas (`inferida` →
`confirmada`, 3 con facultad corregida a «Facultad de Medicina y Salud», 1 a
«Facultad de Educación y Ciencias Sociales»); 4 unidades renombradas
(Medicina → Medicina y Salud, Educación/Psicología/Familia → Educación y
Ciencias Sociales, Comunicaciones y Humanidades → orden invertido,
Arquitectura y Diseño → +Estudios Creativos); 3 variantes agregadas a
entradas existentes; 1 entrada nueva (Escuela de Ingeniería Civil
Industrial). `vocabulario_validado_por_institucion` sigue en `false`: aún
quedan la fila pausada y varias unidades marcadas «no» sin corrección
utilizable (ver abajo).

### Verificación

`--test`: 21/21. `--dry-run` corrido DOS veces contra el CSV real antes de
aplicar (una por cada defecto encontrado y corregido). Tras aplicar:
`yaml.safe_load()` sobre el resultado, auditoría completa
(`src/audit/run_all.py`, 0 fallas bloqueantes), build completo
(`build_all.py`, compuerta de capas: 0 fallas), higiene del sitio sin
fallos, y confirmación manual de que `series.json` (`P-07`) agrega la
producción bajo los nombres nuevos correctamente (Facultad de Medicina y
Salud: 577 pares) y que la fila pausada sigue apareciendo sin fusionar
(Facultad de Odontología y Ciencias de la Rehabilitación: 1, sin tocar).

### Archivos creados o modificados

```
src/review/apply_unit_validation.py   entrada_por_variante(); autotest 10 → 21 comprobaciones
config/matching_rules.yml             4 jerarquías confirmadas, 4 unidades renombradas, 4 variantes/entradas nuevas
internal/unit_validation_decisions.csv   subido por el usuario; 1 fila pausada a mano antes de aplicar
internal/matching_log.csv             regenerado por la auditoría con los nombres corregidos
internal/ambiguities_authors.csv      regenerado; una ambigüedad I-06 falsa se resolvió sola al unificar nombres
internal/validacion_unidades.md/.html  regeneradas: 18 unidades restantes, 0 jerarquías inferidas
internal/.respaldos/matching_rules_20260826T175621.yml   respaldo automático antes de escribir
```

### Ambigüedades abiertas · pendiente de respuesta del usuario

- **La fila pausada**: ¿la unidad real de ese par es «Facultad de
  Educación y Ciencias Sociales» (lo que dice la propia cadena de
  afiliación), o hay algo que Claude no está viendo? Propuesta: agregar una
  entrada a `correcciones_declaradas` para ese texto exacto, no una fusión
  de vocabulario.
- **Facultad de Odontología** (sola, sin la coletilla "y Ciencias de la
  Rehabilitación"): la nota decía "actualmente pertenece a la Facultad de
  Medicina y Salud" pero el campo de corrección quedó vacío. ¿Se confirma
  esa fusión?
- **Escuela de Nutrición y Dietética** (fila de unidad, no de jerarquía):
  «no» sin corrección ni nota. ¿Qué falta corregir ahí?
- **School of Civil Engineering / School of Engineering**: el usuario
  señaló que son ambiguos entre varias escuelas de ingeniería civil
  (Industrial, Informática y Telecomunicaciones, IA y Realidad Virtual,
  Biomédica) y no completó cuál. Sin resolver.
- **Escuela de Ingeniería Civil Industrial** (entrada nueva creada esta
  ronda): no quedó vinculada a ninguna facultad en `jerarquia` — hoy se
  reporta por sí sola. ¿Se agrega el vínculo a «Facultad de Ingeniería»,
  igual que las otras escuelas?
- Las de siempre, sin cambios: `T-06`, `T-19` en su techo.

### Próximo paso recomendado

Preguntarle al usuario las cinco ambigüedades de arriba. Con esas
respuestas, `T-02` puede cerrarse por completo: aplicar la fila pausada
(probablemente como corrección declarada, no como fusión de vocabulario),
decidir Odontología y Nutrición, y — si corresponde — agregar la jerarquía
de Ingeniería Civil Industrial. Sólo entonces
`vocabulario_validado_por_institucion` puede pasar a `true`.

---

## Cierre · T-02: la fila pausada se resuelve — corrección declarada, no fusión de vocabulario

El usuario revisó la fila pausada junto con Claude, tal como pidió («No,
revisémoslo juntos primero»). Ante la pregunta de si un mismo autor podía
tener dos afiliaciones, señaló su postura metodológica — no puede — y pidió
el Scopus Author ID o el ORCID para verificar por su cuenta. Se le entregó
el Scopus Author ID (59321456000) y los datos de las dos publicaciones del
par; el usuario aportó después el ORCID que encontró
(`0009-0009-2334-0562`). Claude intentó una corroboración independiente por
web: `WebFetch` a `orcid.org`, `pub.orcid.org`, `repositorio.uft.cl`,
`doi.org` y `www.researchgate.net` devolvió `EGRESS_BLOCKED` en los cinco
casos (política del proxy de salida, no reintentada); `WebSearch` sí
respondió, con resultados sintetizados y con fuente. Con esa evidencia más
la suya propia, el usuario confirmó: **"Es una autora afiliada a la
institución. Aplica la opción número 1"** — la propuesta original de Claude
(corrección declarada sobre el texto exacto mal extraído, no una fusión de
vocabulario).

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-300 | Se agrega una 4ª entrada a `correcciones_declaradas` (`config/matching_rules.yml`), clave `"Facultad de Odontología y Ciencias de la Rehabilitación"` → `"Facultad de Educación, Psicología y Familia"` — NO una fusión de vocabulario | Las tres entradas previas de `correcciones_declaradas` arreglan artefactos de concatenación (texto pegado, guion de corte de línea); ésta es distinta — arregla una extracción que tomó la facultad de OTRA institución — pero el mecanismo es el correcto para ambos casos: intercepta antes de que el texto llegue a `vocabulario`, así que "Facultad de Odontología y Ciencias de la Rehabilitación" nunca se registra como si fuera una unidad UFT |
| D-301 | La fila 21 de `internal/unit_validation_decisions.csv` se marca `correcto: si` (no se deja en `pendiente`, ni se completa como `no` + corrección) | `no` + corrección habría hecho que una futura corrida de `apply_unit_validation.py` tratara el texto detectado como una entrada de vocabulario a fusionar — exactamente el error que la corrección declarada evita; `si` documenta que la fila queda resuelta por otra vía sin arriesgar ese efecto secundario en el CSV |

### Verificación

`yaml.safe_load()` sobre el archivo modificado antes de considerar el
cambio hecho. Auditoría completa (`src/audit/run_all.py`): 0 fallas
bloqueantes, `internal/matching_log.csv` regenerado confirma que el par
(eid `2-s2.0-85203525781`) ahora resuelve a «Facultad de Educación y
Ciencias Sociales». `data/interim/indicator_feasibility.py` y
`src/build/build_all.py` completos, compuerta de capas: 0 fallas.
`src/build/06_assemble_site.py`: 10 páginas, capa interna no incluida.
`src/verify/higiene.py`: sin fallos. Confirmación manual en
`data/processed/series.json` (`P-07`): «Facultad de Educación y Ciencias
Sociales» sube de 54 a 55 pares; «Facultad de Odontología y Ciencias de la
Rehabilitación» ya no aparece como unidad propia (sólo queda «Facultad de
Odontología», la unidad UFT real, sin tocar). `apply_unit_validation.py
--test`: 21/21. `--dry-run` tras el cambio del CSV: 0 filas pendientes, la
fila ya no aparece ni en cambios ni en avisos.

### Archivos creados o modificados

```
config/matching_rules.yml                 4ª entrada en correcciones_declaradas
internal/unit_validation_decisions.csv    fila 21: pendiente -> si, nota reescrita
internal/matching_log.csv                 regenerado por la auditoría con el par corregido
data/processed/series.json                 P-07: Educación y Ciencias Sociales 54 -> 55
dist/                                       reconstruido completo
```

### Ambigüedades abiertas · pendiente de respuesta del usuario

- **Facultad de Odontología** (sola, sin la coletilla "y Ciencias de la
  Rehabilitación"): la nota decía "actualmente pertenece a la Facultad de
  Medicina y Salud" pero el campo de corrección quedó vacío. ¿Se confirma
  esa fusión?
- **Escuela de Nutrición y Dietética** (fila de unidad, no de jerarquía):
  «no» sin corrección ni nota. ¿Qué falta corregir ahí?
- **School of Civil Engineering / School of Engineering**: el usuario
  señaló que son ambiguos entre varias escuelas de ingeniería civil
  (Industrial, Informática y Telecomunicaciones, IA y Realidad Virtual,
  Biomédica) y no completó cuál. Sin resolver.
- **Escuela de Ingeniería Civil Industrial** (entrada nueva creada la ronda
  anterior): no quedó vinculada a ninguna facultad en `jerarquia` — hoy se
  reporta por sí sola. ¿Se agrega el vínculo a «Facultad de Ingeniería»,
  igual que las otras escuelas?
- Las de siempre, sin cambios: `T-06`, `T-19` en su techo.

### Próximo paso recomendado

Preguntarle al usuario las cuatro ambigüedades restantes de arriba. Con
esas respuestas, `T-02` puede cerrarse por completo y
`vocabulario_validado_por_institucion` puede pasar a `true`.

---

## Cierre · T-02 completo: las cuatro ambigüedades resueltas, `vocabulario_validado_por_institucion: true`

El usuario respondió las cuatro ambigüedades pendientes en un solo mensaje:
(1) confirma la fusión de «Facultad de Odontología» en «Facultad de
Medicina y Salud»; (2) «Escuela de Nutrición y Dietética» se llama
efectivamente así — el nombre no necesita corrección, sólo la jerarquía
(ya confirmada en la ronda anterior); (3) «School of Civil Engineering» /
«School of Engineering» son ambiguos entre varias escuelas de ingeniería
civil y no hay forma de precisar cuál — sólo se sabe que pertenecen a la
Facultad de Ingeniería; (4) confirma el vínculo de jerarquía de «Escuela de
Ingeniería Civil Industrial» a «Facultad de Ingeniería».

Antes de tocar `config/matching_rules.yml`, se probó la fusión de
Odontología contra el script real (no contra el fixture sintético primero)
para ver qué haría, siguiendo la misma disciplina que ya había atrapado dos
bugs en la ronda anterior. Atrapó un tercero.

### El tercer defecto de `apply_unit_validation.py`

«Facultad de Odontología» → «Facultad de Medicina y Salud» es un caso que
ninguno de los dos bugs anteriores cubría: AMBOS nombres ya eran entradas
propias de vocabulario, cada una con sus propias variantes (Odontología
traía «Faculty of Dentistry», «Escuela de Odontología», «School of
Dentistry»). El código existente sólo sabía agregar `nombre` como una
variante suelta del destino — dejaba la entrada vieja de Odontología
intacta, con sus propias variantes huérfanas. El resultado habría quedado
con «Facultad de Odontología» registrada DOS VECES (clave propia Y
variante ajena), y «Faculty of Dentistry» / «Escuela de Odontología» /
«School of Dentistry» habrían seguido resolviendo a la entrada vieja en
vez de a la fusionada — contradiciendo la propia fusión que se estaba
aplicando. Verificado ejecutando `aplicar_unidad()` directamente contra el
archivo real antes de escribir nada.

Se corrigió `aplicar_unidad()`: cuando el nombre a corregir ES TAMBIÉN una
entrada propia (no sólo el destino), se trasladan TODAS sus variantes al
destino y se borra la entrada vieja completa, en vez de agregar sólo el
nombre suelto. Se agregó un caso de prueba nuevo al fixture (variantes
sintéticas de Odontología fusionándose en una entrada existente) — el
autotest subió de 21 a 24 comprobaciones.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-302 | `aplicar_unidad()` gana una rama para fusionar DOS entradas de vocabulario ya existentes (trasladando todas las variantes de la vieja, borrando la entrada vieja), en vez de sólo agregar el nombre corregido como variante suelta | El caso real (Odontología → Medicina y Salud) habría dejado el texto registrado dos veces y sus otras variantes sin fusionar — un defecto que sólo se manifestó al probar contra el archivo real, como los dos anteriores |
| D-303 | «School of Civil Engineering» y «School of Engineering» se registran como variantes de «Facultad de Ingeniería» (nivel de facultad), no de ninguna escuela específica | El usuario confirmó que no hay forma de precisar a cuál de las cuatro escuelas de ingeniería civil corresponden — atribuir al nivel de facultad es el dato más fino que la evidencia sostiene, no una invención (`CLAUDE.md`: no inventar datos ni relaciones) |
| D-304 | «Escuela de Ingeniería Civil Industrial» → «Facultad de Ingeniería» se agrega directo a `jerarquia`, a mano, sin pasar por el CSV | Es una entrada nueva de la ronda anterior que nunca tuvo fila en la hoja de validación (el generador sólo crea filas para jerarquías `inferida` existentes al momento de generarla); el usuario la confirmó directamente en el chat |
| D-305 | Con las 25 filas del CSV respondidas y ambas jerarquías nuevas confirmadas, `vocabulario_validado_por_institucion` pasa de `false` a `true` | Es la primera vez que el vocabulario completo de unidades académicas queda validado por el responsable institucional — condición que el propio archivo declara como requisito para publicar comparaciones entre unidades |

### Qué se aplicó

`config/matching_rules.yml`: jerarquía nueva («Escuela de Ingeniería Civil
Industrial» → «Facultad de Ingeniería», `confirmada`, agregada a mano);
vocabulario — «Facultad de Odontología» fusionada en «Facultad de Medicina
y Salud» (4 variantes trasladadas, entrada vieja eliminada), «School of
Civil Engineering» y «School of Engineering» agregadas como variantes de
«Facultad de Ingeniería»; `vocabulario_validado_por_institucion: false` →
`true`. `src/review/apply_unit_validation.py`: nueva rama de fusión en
`aplicar_unidad()`, autotest 21 → 24 comprobaciones.

### Verificación

`--test`: 24/24. `--dry-run` corrido contra el CSV real antes de aplicar;
además, la rama de fusión se probó por separado contra el archivo real
(`aplicar_unidad()` invocada directamente) ANTES de escribir el fixture de
prueba, para confirmar el bug antes de darlo por corregido. Tras aplicar:
`yaml.safe_load()` sobre el resultado; auditoría completa (0 fallas
bloqueantes); `build_all.py` completo (compuerta de capas: 0 fallas);
`06_assemble_site.py` (10 páginas, capa interna no incluida); higiene sin
fallos; confirmación manual en `series.json` (`P-07`): «Facultad de
Odontología» ya no aparece como fila propia, «Facultad de Medicina y
Salud» sube a 610 pares, «Facultad de Ingeniería» queda en 53.

### Archivos creados o modificados

```
src/review/apply_unit_validation.py       rama de fusión en aplicar_unidad(); autotest 21 -> 24
config/matching_rules.yml                 1 jerarquía nueva, 1 fusión de vocabulario, 2 variantes nuevas, flag validado: true
internal/unit_validation_decisions.csv    4 filas resueltas (Odontología, Nutrición, School of Civil/Engineering)
internal/matching_log.csv                 regenerado con los nombres fusionados
data/processed/series.json                P-07: Odontología fusionada, Medicina y Salud 55 -> 610, Ingeniería 53
dist/                                     reconstruido completo
```

### Ambigüedades abiertas

- Ninguna de `T-02`. El vocabulario de unidades académicas queda
  completamente validado por el responsable institucional.
- Las de siempre, sin cambios: `T-06`, `T-19` en su techo.

### Próximo paso recomendado

Cerrar `T-02` formalmente en `PLAN.md` (si el archivo lo rastrea como
pendiente abierto) y seguir con el resto de los `T` pendientes.

## Cierre · T-19: cron mensual en el workflow de GitHub Actions; T-06 confirmado sin ruta de automatización

El usuario pidió avanzar `T-06` y `T-19`. Ambos ya estaban en su techo del día
(commits `5c9a292`, `37d893c`, `8377f91`, ya en el historial de esta rama).
Preguntó después si pueden generarse actualizaciones automáticas en vez de
reimportar a mano.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-306 | `T-06` no gana automatización: consultar la API de Scopus con más frecuencia no produce la fecha de corte que el pendiente pide | La propia documentación de `scopus_api.py` declara que la Scopus Search API no expone un campo «actualizado al» — sólo captura instante de consulta + cadena de búsqueda. La fecha de corte sólo existe en la cabecera de un export manual desde la interfaz web (`docs/UPDATING_REQUEST.md`); automatizar la consulta repetiría el mismo hallazgo sin acercarse al cierre |
| D-307 | `.github/workflows/ampliar-orcid.yml` gana un disparador `schedule` mensual (`cron: '0 6 1 * *'`), además del `workflow_dispatch` que ya tenía | El registro de ORCID sí cambia con el tiempo (a diferencia de la API de Scopus); una corrida mensual automática cubre `T-19` sin gastar cuota de más ni depender de que alguien se acuerde de lanzarlo a mano |
| D-308 | Los tres pasos condicionados a `inputs.verificar`, `inputs.afiliacion` e `inputs.commitear` cambian a `github.event_name != 'workflow_dispatch' || inputs.X` | El contexto `inputs` sólo existe en disparos `workflow_dispatch`; en un disparo `schedule` llega vacío, y esos tres `if:` se habrían evaluado como falsos — la corrida mensual habría consultado ORCID pero nunca verificado, buscado candidatos por afiliación ni comiteado el resultado. Se encontró antes de que corriera en producción, no después |

### Qué se aplicó

`.github/workflows/ampliar-orcid.yml`: trigger `schedule` mensual agregado;
comentario «CÓMO SE LANZA» actualizado; los tres `if:` de pasos condicionales
corregidos para no depender de `inputs` fuera de un disparo manual.
`docs/OPERACION.md`: nota sobre el disparo automático en la sección de T-19.
`PLAN.md`: fila de `T-19` anota la automatización agregada hoy. `T-06` no
cambia: sigue igual en su techo, ahora con la razón de por qué más
automatización no lo mueve documentada aquí.

### Verificación

YAML parseado con `pyyaml` (`py -3 -c "import yaml; yaml.safe_load(...)"`):
válido, dos triggers (`workflow_dispatch`, `schedule`), cron
`[{'cron': '0 6 1 * *'}]`. No se pudo correr el workflow real en GitHub
Actions desde esta sesión — el cambio queda sin commitear/pushear a la
espera de que el usuario lo confirme.

### Archivos creados o modificados

```
.github/workflows/ampliar-orcid.yml   trigger schedule mensual + fix de los 3 if: dependientes de inputs
docs/OPERACION.md                     nota sobre el disparo automático mensual (T-19)
PLAN.md                               T-19: anota la automatización; T-06 sin cambio de estado
SESSION_NOTES.md                      este cierre
```

### Ambigüedades abiertas

- Las de siempre, sin cambios: `T-06`, `T-19` en su techo (T-19 ahora con
  corrida automática mensual además del techo del método).

### Próximo paso recomendado

Confirmar con el usuario si comitea y pushea el cambio del workflow (acción
visible en GitHub, no autoaplicada sin permiso). Si se aprueba, verificar la
primera corrida programada el 1 del mes próximo, o lanzarla a mano una vez
desde Actions para confirmar que el fix de los `if:` funciona antes de
esperar al cron.

## Cierre · SciVal Partner API: hallazgo del usuario, registrado sin probarlo

El usuario preguntó por la integración de la API de SciVal —tema abierto
tras `dda939f` (403 `ENTITLEMENTS_ERROR` contra `api.elsevier.com`)— y trajo
un enlace propio: `https://partnerapi.scival.com/`.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-309 | `partnerapi.scival.com` se documenta en `docs/FUENTES_Y_APIS.md` §3.8 como hallazgo sin confirmar, no como ruta de acceso disponible | La página consultada solo describe autenticación (firma HMAC-SHA256, credenciales «modelo Pure»), sin proceso de registro ni elegibilidad. Pure es el CRIS propio de Elsevier — la forma de las credenciales sugiere API de integración para partners/proveedores de software, distinta del autoservicio institucional que ya se probó y rebotó. `CLAUDE.md` prohíbe suponer disponibilidad de API sin confirmar, así que no se intentó construir nada contra ella |
| D-310 | La pregunta sobre esta API se agrega al mismo pedido pendiente de la entitlement estándar de SciVal (gestor de cuenta Elsevier / biblioteca UFT), en vez de abrir un pendiente `T-xx` nuevo | Es la misma persona, la misma gestión, y todavía no hay nada que ejecutar en el repositorio — abrir un pendiente de código para una pregunta de licenciamiento habría sido prematuro |

### Qué se aplicó

`docs/FUENTES_Y_APIS.md` §3.8: nuevo párrafo documentando el hallazgo, con
la pregunta redactada para el gestor de cuenta Elsevier. Ningún código
nuevo — no hay credenciales que probar todavía.

### Verificación

Ninguna aplicable: es un hallazgo de documentación, no una consulta a red
ni un cambio de comportamiento del pipeline.

### Archivos creados o modificados

```
docs/FUENTES_Y_APIS.md   §3.8: hallazgo de partnerapi.scival.com + pregunta para el gestor de cuenta
SESSION_NOTES.md         este cierre
```

### Ambigüedades abiertas

Si la UFT tiene o puede obtener acceso a `partnerapi.scival.com` — sin
respuesta del gestor de cuenta Elsevier, sigue sin confirmar en cualquier
dirección.

### Próximo paso recomendado

Enviar la pregunta combinada (entitlement estándar + Partner API) al gestor
de cuenta Elsevier o a la biblioteca UFT. Hasta tener respuesta, no hay
ruta de código que avanzar en la integración de SciVal.

## Cierre · Reprueba de SciVal con acceso admin (mismo resultado), y EBSCO registrado como propuesta

Con credenciales de administrador de Elsevier, el usuario repitió la prueba
de `analytics/scival/publication/metrics` por `curl` directo: sigue
`403 ENTITLEMENTS_ERROR`. Confirma que el acceso admin a la cuenta no
habilita por sí solo la entitlement de SciVal API — es una activación
comercial separada, no autogestionable. No se documentó de nuevo por
instrucción del usuario: el resultado es idéntico al ya registrado y no
aporta información nueva.

**Incidente de seguridad:** la API Key quedó escrita en texto plano en el
chat al pegar el comando `curl`. Se le recomendó al usuario rotarla —mismo
tipo de incidente que ya ocurrió antes en este proyecto (`1821b98`).

Después, el usuario mencionó tener acceso admin de EBSCO y preguntó si
serviría para EBSCO como fuente nueva (no para destrabar SciVal — son
proveedores distintos). Investigado por web: EDS (EBSCO Discovery Service)
es una capa de búsqueda/descubrimiento, no una plataforma bibliométrica —
no tiene FWCI ni percentil de citación. Su API también está bloqueada por
entitlement (hay que contactar a ventas de EBSCO), con un esquema de
autenticación distinto (usuario/contraseña → AuthToken + SessionToken vía
`developer.ebsco.com`). Registrado como propuesta en `docs/FUENTES_Y_APIS.md`
§3.12, en el mismo rol que OpenAlex: cruce de cobertura, nunca fusionado
con el universo publicado.

### Archivos creados o modificados

```
docs/FUENTES_Y_APIS.md   §3.12 nueva: EBSCO Discovery Service, propuesta sin confirmar
SESSION_NOTES.md         este cierre
```

### Ambigüedades abiertas

Qué producto EBSCO tiene contratado exactamente la UFT (EDS completo,
bases individuales, o ambos) y si esa suscripción incluye acceso API —
sin confirmar.

### Próximo paso recomendado

Nada de código pendiente en ninguna de las dos vías: SciVal espera
activación comercial de Elsevier; EBSCO espera que el usuario confirme con
su representante de ventas qué acceso tiene y active la API si aplica.

## Cierre · OpenAlex ejecutado por primera vez: V2-19 y V2-26 cerrados

El usuario pidió trabajar con OpenAlex (`V2-19`, `V2-26`), la única
propuesta de la lista sin bloqueo de licencia: es una API pública, sin
clave. Ambos conectores ya estaban escritos desde el 2026-08-19 pero nunca
se habían corrido contra la red real (el entorno de desarrollo remoto no
alcanza `api.openalex.org`); esta máquina sí.

`orcid_openalex.py` reventó al final con `UnicodeEncodeError` en la primera
corrida: la consola de Windows usa `cp1252`, sin «→» ni «─». El archivo ya
se había escrito antes de imprimir esa línea —verificado comparando
`git status` contra el traceback—, así que no se perdió nada, pero
`openalex_cobertura.py` habría reventado igual al usarse. Corregido
reconfigurando `stdout` a UTF-8 al importar, sólo en `sys.platform ==
"win32"` (no toca el comportamiento en CI, que ya corre en UTF-8).

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-311 | Los dos scripts ganan la reconfiguración de `stdout` a UTF-8, guardada tras `sys.platform == "win32"` | El trabajo real (escritura de CSV) ya había terminado cuando reventaba el print; el fix es puramente de presentación, pero sin él cualquier corrida local en Windows termina en traceback y esconde el resumen final |
| D-312 | Las 68 publicaciones sin atribución OpenAlex y los 6 desacuerdos de ORCID quedan en `internal/` sin resolver | Mismo principio que siempre (`D-08`): una discrepancia se encola para revisión humana, nunca se decide sola |
| D-313 | Las 414 obras que OpenAlex atribuye a la UFT y el universo no tiene NO se promueven a producción confirmada | `D-206`: Scopus y OpenAlex indexan con criterios distintos. Es una cola de candidatos —desambiguación posiblemente errónea, tipo documental excluido, o fecha fuera de ventana—, nunca un ajuste automático del corpus |

### Qué se aplicó

`src/enrich/orcid_openalex.py` y `openalex_cobertura.py`: fix de encoding en
Windows. `data/enriched/authors_orcid.csv`: 80 asignaciones nuevas (242 →
322 formas de firma; 216 → 280 de 538 entidades publicadas). Cuatro colas
nuevas en `internal/`: `openalex_log.csv` (log completo de la corrida),
`openalex_deteccion.csv` (68 publicaciones sin atribución OpenAlex),
`openalex_desacuerdos.csv` (6 desacuerdos de ORCID), `openalex_cobertura.csv`
(414 obras atribuidas por OpenAlex fuera del universo). `docs/V2_BACKLOG.md`:
V2-19 y V2-26 cerrados con resultado real. `docs/FUENTES_Y_APIS.md` §3.1 y
§2.3 actualizados con las cifras de la corrida.

### Verificación

Auditoría completa (29/30, 0 bloqueantes). `build_all.py` y
`06_assemble_site.py` sin fallas, compuerta pública/interna en 0.
`node src/verify/run_all.mjs dist` → 0 fallos en las 6 categorías, corrido
ANTES de commitear (no después, como en el cierre anterior).

### Archivos creados o modificados

```
src/enrich/orcid_openalex.py        fix de encoding Windows (stdout UTF-8)
src/enrich/openalex_cobertura.py    fix de encoding Windows (stdout UTF-8)
data/enriched/authors_orcid.csv     242 -> 322 asignaciones (80 nuevas de OpenAlex)
internal/openalex_log.csv           nuevo · log completo de la corrida de enriquecimiento
internal/openalex_deteccion.csv     nuevo · 68 publicaciones sin atribución OpenAlex, cola de revisión
internal/openalex_desacuerdos.csv   nuevo · 6 desacuerdos de ORCID, cola de revisión
internal/openalex_cobertura.csv     nuevo · 414 obras atribuidas por OpenAlex fuera del universo
docs/V2_BACKLOG.md                  V2-19 y V2-26 cerrados con resultado real
docs/FUENTES_Y_APIS.md              §3.1 y §2.3 actualizados
```

### Ambigüedades abiertas

Las cuatro colas nuevas en `internal/` quedan sin revisión humana — nadie
las ha mirado todavía. `docs/ORCID_COVERAGE.md` sigue con las cifras
previas a esta corrida (556 entidades / 38,8 %); no se reescribió su prosa
metodológica completa por alcance, sólo `FUENTES_Y_APIS.md` y
`V2_BACKLOG.md`, que son los que declaran el resultado crudo.

### Próximo paso recomendado

Revisar las cuatro colas nuevas de `internal/` con `scripts/revisar-identidad.ps1`
u otra herramienta equivalente, y decidir si `docs/ORCID_COVERAGE.md` merece
una actualización completa de sus cifras y su argumento del techo del 100 %.

## Cierre · Herramienta de revisión para la brecha de cobertura OpenAlex

El usuario planteó una hipótesis: si Scopus/SciVal son productos Elsevier,
es razonable que subestimen la producción real de la UFT, y OpenAlex podría
estar viendo lo que ese entorno no ve. Antes de aceptarla como hecho, se
desglosaron los 414 hallazgos de `V2-26`: 310 son `article` (no sólo
diferencia de tipo documental), pero el 71,5 % no tiene ninguna cita y el
40 % es de 2025 — consistente tanto con producción real muy reciente como
con falsos positivos de desambiguación de OpenAlex. Conclusión: la
hipótesis está bien respaldada, pero no verificada — exactamente la
distinción que `CLAUDE.md` exige.

El usuario pidió trabajar con los registros. Antes de revisar nada,
`openalex_cobertura.py` ganó `autores_de_la_institucion()`: identifica qué
autor y qué institución declarada (tal como la escribe OpenAlex) disparó
cada hallazgo — sin esto, revisar exigía abrir cada DOI a mano. Reutiliza
el caché en disco de la corrida anterior, sin volver a consultar la red.
Encontró un patrón de paso: «Franco Fernando Yanine» / «Fernando Yanine»
en el top-20 por citación son casi con certeza la misma persona — una
variante de nombre en autores que **no están en el universo Scopus en
absoluto**, un caso que ninguna herramienta existente cubre.

Se construyó `internal/revision_cobertura_openalex.html` (mismo patrón que
`build_unit_validation.py`/`build_review.py`): 414 casos ordenados por
citación, con autor, institución declarada, DOI, año, tipo y tres
veredictos (UFT real / error de OpenAlex / tipo excluido a propósito).
`apply_openalex_review.py` aplica lo exportado a la columna `resolucion`
de `openalex_cobertura.csv`. Verificado con Playwright real (no sólo
`--test`): 414 ítems renderizan, marcar un veredicto actualiza el
contador, la búsqueda filtra, 0 errores JS.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-314 | `apply_openalex_review.py` sólo actualiza `internal/openalex_cobertura.csv`; nunca escribe en `data/interim/publications_universe.csv` ni en ningún artefacto publicable | `D-206`: Scopus y OpenAlex indexan con criterios distintos. Confirmar que una obra es «producción real UFT» no la convierte en parte del corpus — ampliar el universo es una decisión de alcance aparte, explícita, posterior. Este tooling deja constancia de la revisión, no ejecuta la decisión de alcance |
| D-315 | El asistente de PowerShell (`revisar-cobertura-openalex.ps1`) NO reconstruye el sitio al final, a diferencia de `validar-unidades.ps1` | Nada del build depende de esta revisión —a diferencia de la validación de unidades, que si cierra alimenta `config/matching_rules.yml`—, así que agregar el paso sería trabajo sin efecto |
| D-316 | Tres veredictos (uft / error / tipo), no dos | «No está en Scopus» tiene una tercera lectura real y frecuente: un tipo documental (preprint, editorial) que este proyecto excluye a propósito, que no es lo mismo que «Scopus lo perdió» ni que «OpenAlex se equivocó» |

### Qué se aplicó

`src/enrich/openalex_cobertura.py`: nueva función `autores_de_la_institucion()`,
columnas `autor_uft`/`institucion_declarada` en la salida, con deduplicación
de nombres repetidos. `src/review/build_openalex_review.py` (nuevo):
genera la herramienta interactiva. `src/review/apply_openalex_review.py`
(nuevo): aplica las decisiones exportadas. `scripts/revisar-cobertura-openalex.ps1`
(nuevo): asistente de Windows, mismo patrón que `revisar-identidad.ps1`.
`Makefile`: objetivo `revisar-cobertura-openalex`. `docs/OPERACION.md`:
instrucciones de uso.

### Verificación

`--test` en ambos scripts nuevos (3 casos en el conector, 6 en el aplicador,
incluida idempotencia de reaplicar las mismas decisiones). Smoke test con
Playwright real contra el HTML generado: 414 ítems, marcar veredicto
actualiza el contador y el estado `aria-pressed`, búsqueda filtra
correctamente, 0 errores de consola. No se ejecutó el flujo completo de
exportar→aplicar con datos reales — el usuario todavía no ha revisado
ningún caso.

### Archivos creados o modificados

```
src/enrich/openalex_cobertura.py              autores_de_la_institucion(); columnas autor_uft/institucion_declarada
internal/openalex_cobertura.csv               regenerado con las dos columnas nuevas (desde caché, sin red)
src/review/build_openalex_review.py           nuevo · genera la herramienta interactiva
src/review/apply_openalex_review.py           nuevo · aplica las decisiones exportadas
internal/revision_cobertura_openalex.html     nuevo · 414 casos, generado
scripts/revisar-cobertura-openalex.ps1        nuevo · asistente de Windows
Makefile                                      objetivo revisar-cobertura-openalex
docs/OPERACION.md                             instrucciones de uso
SESSION_NOTES.md                              este cierre
```

### Ambigüedades abiertas

Los 414 casos siguen sin revisar — la herramienta está lista, pero nadie ha
marcado ningún veredicto todavía. El patrón de variante de nombre
("Franco Fernando Yanine" / "Fernando Yanine") tampoco tiene un lugar
donde declararse: no es una decisión de identidad del corpus interno
(`identity_decisions.csv`, que trabaja sobre firmas YA en el universo),
porque estos autores no están en Scopus en absoluto.

### Próximo paso recomendado

Abrir `internal/revision_cobertura_openalex.html` (o correr
`scripts/revisar-cobertura-openalex.ps1`) y empezar por el top de
citación, que ya se revisó informalmente en el chat de esta sesión: los
primeros ~20 casos ya tienen una lectura hecha, sólo falta marcarla en la
herramienta y exportar.

---

## Sesión 2026-08-26/27 — Higiene de codificación Windows y evidencia Crossref para V2-26

**Por qué se abre sesión aparte:** los cierres anteriores (OpenAlex, T-19,
la herramienta de cobertura) quedaron anidados bajo el encabezado de la
sesión del 20 de agosto («Rediseño de la interfaz») porque nadie abrió uno
nuevo ese día. `docs/DECISIONS.md` heredó la etiqueta: le atribuye a
«Rediseño de la interfaz» decisiones que no tienen nada que ver con la
interfaz. Esta entrada no corrige esa cola retroactivamente —es
arqueología de sesiones pasadas, tarea aparte—, pero al menos el trabajo
de hoy queda bajo su propio título.

**Punto de partida:** un crash de codificación en Windows
(`apply_decisions.py`/`merge_decisions.py`, `→` sobre consola cp1252) ya
corregido en la sesión anterior. El usuario pidió llevar esa corrección a
fondo («dele durísimo»), y luego evidencia adicional para acelerar la
revisión de los 414 casos de `V2-26` sin decidirlos por nadie.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-317 | El criterio real del guard de codificación win32 es «todo entry point que imprime datos que no controla» (stdout de un subproceso, contenido de un CSV, nombres que trae una API externa), no una lista literal de caracteres sospechosos | Un scan carácter-por-carácter contra `cp1252` mostró que 18 de los 31 scripts corregidos no tenían ningún carácter fuera de rango *antes* del cambio: se protegen por lo que podrían imprimir, no por lo que imprimen hoy. Quedaba sin escribir en ningún lado |
| D-318 | `subprocess.run(...)` usa `encoding="utf-8", errors="replace"` explícito, nunca `text=True` a secas | `text=True` decodifica con `locale.getpreferredencoding()` (cp1252 en Windows) y **no** respeta `PYTHONIOENCODING`. Con `node` y `git` emitiendo UTF-8, eso producía mojibake silencioso —no un crash— en `06_assemble_site.py` y `snapshot.py`. Único patrón en todo el repo: 2 call sites, ambos corregidos |
| D-319 | La evidencia de Crossref en la revisión de cobertura OpenAlex se muestra en un recuadro aparte, nunca se fusiona con el veredicto de OpenAlex | `D-08`: es una segunda fuente para leer, no un segundo voto que promedie con el primero. Si algún día decidieran cosas distintas, fusionarlas ocultaría el desacuerdo en vez de mostrarlo |
| D-320 | El guard de codificación de una biblioteca pura (`equivalencia_ortografica.py`, importada por otros tres scripts) vive dentro de `if __name__ == "__main__":`, no a nivel de módulo | Mutar `sys.stdout` como efecto secundario de un `import` es invisible para quien importa y rompe bajo `pythonw.exe` o cualquier captura que sustituya stdout (`redirect_stdout`): el módulo se vuelve inimportable, no sólo silencioso. Hallazgo de la revisión independiente, no propio |
| D-321 | Verificar un guard de codificación exige correr con `PYTHONIOENCODING` retirado | El harness de desarrollo la fija (`utf-8:surrogateescape`); la consola real de un usuario de Windows no. «Corrí el pipeline completo sin errores» con esa variable puesta no demuestra que el guard funcione ni que hiciera falta — sólo que el harness ya lo resolvía por su cuenta |

### Qué se aplicó

Tres commits. **`7d0e02a`**: el guard `sys.stdout.reconfigure(encoding="utf-8",
errors="replace")` tras `if sys.platform == "win32":` se generalizó de 2 a 31
scripts (todo punto de entrada directo bajo `src/`), más el fix de
`subprocess.run` en `06_assemble_site.py`/`snapshot.py` (D-318).
**`9557ca6`**: `src/enrich/openalex_cobertura_crossref.py` (nuevo) consulta
Crossref por DOI para los 414 casos de `openalex_cobertura.csv`, reutilizando
el patrón de caché y *polite pool* de `orcid_crossref.py` (V2-01); emparejamiento
por apellido con tres niveles de certeza (`unico`/`ambiguo`/`sin_match`, nunca
elige entre ambiguos). `build_openalex_review.py` incorpora el resultado sola,
en un recuadro `.xref` (D-319), si el CSV existe. Nuevo objetivo de Makefile
`cobertura-crossref`. **`88da8db`**: aplica los 10 hallazgos (5 MEDIUM, 5 LOW)
de una revisión independiente sobre `7d0e02a` — guard añadido a
`src/audit/run_all.py` (único `__main__` que había quedado sin él, correcto
hoy sólo por accidente de orden de import); `[Console]::OutputEncoding` fijado
una vez en `scripts/_comun.ps1` (la ruta real del usuario Windows seguía
mojibake-able, aun con el guard de Python bien puesto — PowerShell decodifica
con su propia codificación); comentario del guard corregido en 32 archivos
(citaba `—` y `·`, que sí están en cp1252); reordenamiento del guard antes de
los imports locales en 11 archivos y `import sys` agrupado con la stdlib;
`equivalencia_ortografica.py` corregido (D-320); `run_all.mjs` con
`setEncoding('utf8')` explícito en la captura del subproceso de `higiene.py`;
`i18n.logOutputEncoding=UTF-8` fijado en la llamada a `git` de `snapshot.py`.

### Verificación

`py_compile` sobre los 34 archivos Python tocados, `node --check` sobre
`run_all.mjs`, 11 suites `--test` al 100 % (incluidas las nuevas 6/6 de
`openalex_cobertura_crossref.py`), y el pipeline completo real de punta a
punta tres veces (una por commit): auditoría, factibilidad, build, sitio,
las tres herramientas de revisión, red de coautoría, estado — mismos
resultados en las tres corridas (29/30 reglas, 0 bloqueantes, 414 casos
OpenAlex, 59 con evidencia Crossref). El conector Crossref se corrió contra
los 385 casos con DOI reales: 0 errores de red.

Lo que **no** se hizo, y queda como hueco: no hay verificación con
Playwright real del HTML de revisión con el recuadro `.xref` nuevo —sólo
inspección del marcado generado por regex—, a diferencia de la sesión
anterior que sí abrió el HTML con un navegador real antes de darlo por
bueno. Tampoco se relanzó la revisión independiente sobre `9557ca6` ni
sobre `88da8db`: sólo existe para `7d0e02a`.

### Archivos creados o modificados

```
src/enrich/openalex_cobertura_crossref.py     nuevo · evidencia Crossref por DOI (V2-26 bis)
internal/openalex_cobertura_crossref.csv      nuevo · 385 casos consultados, 59 con afiliación
src/review/build_openalex_review.py           incorpora el recuadro .xref si el CSV existe
internal/revision_cobertura_openalex.html     regenerado con la evidencia incrustada
Makefile                                      objetivo cobertura-crossref
scripts/_comun.ps1                            [Console]::OutputEncoding = UTF8
src/verify/run_all.mjs                        setEncoding('utf8') en el subproceso de higiene.py
31 scripts bajo src/ (commit 7d0e02a)         guard win32 generalizado
11 de esos 31 (commit 88da8db)                guard reordenado, comentario corregido, import sys agrupado
src/audit/run_all.py                          guard propio añadido
src/state/snapshot.py                         encoding="utf-8" explícito + i18n.logOutputEncoding
SESSION_NOTES.md                              este cierre
```

### Ambigüedades abiertas

Sigue sin cambiar: los 414 casos de `V2-26` continúan sin revisión humana
(la ambigüedad ya estaba abierta desde el cierre anterior). Nueva: el
recuadro de evidencia Crossref no se verificó en un navegador real, sólo
por inspección de marcado — no se sabe con certeza que se vea bien en los
59 casos que sí traen afiliación hasta que alguien lo abra. La cola
histórica de `SESSION_NOTES.md` mal anidada bajo «Rediseño de la interfaz»
(desde algún punto de la sesión del 20 de agosto hasta el cierre anterior
a este) sigue sin corregirse.

### Próximo paso recomendado

Abrir `internal/revision_cobertura_openalex.html` en un navegador real y
confirmar visualmente que el recuadro verde de evidencia Crossref se ve
como se espera en un par de los 59 casos con afiliación, antes de empezar
la revisión de los 414. Si se quiere cerrar el hueco de bitácora del todo,
alguien tendría que releer la sesión del 20 de agosto en adelante y decidir
dónde insertar el `## Sesión 2026-08-26` que faltó ese día.

---

## Sesión 2026-08-27 (cont.) — Bento Grid, treemap y mapa de calor (EN CURSO)

**Encabezado propio a propósito**: es un tema distinto (rediseño de
interfaz) del de la entrada anterior (higiene de codificación) — la misma
lección de la entrada anterior, aplicada de inmediato en vez de esperar a
que se repita el hueco.

**Pedido del usuario**: actuar como ingeniero principal + diseñador UI
sénior, en bucle autónomo, para llevar la plataforma a una interfaz
"premium" (Bento Grid, treemap, mapa de calor de temáticas), sin romper
`make sitio` ni la arquitectura de cero dependencias externas.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-322 | Se le planteó al usuario, ANTES de tocar color, que "adoptar de forma autónoma" una paleta nueva chocaba con `D-381`/`D-382` (la paleta la fija el usuario; hay un incidente registrado de un cambio sin consultar que se perdió) | Autorizó una paleta nueva CON la condición de verla medida antes de aplicarla — condición que sigue pendiente de cerrarse, ver Ambigüedades |
| D-323 | El treemap colorea las facultades por PROFUNDIDAD (rampa ordinal `--ord-1..4`, ya validada) más gris de "sin dato", no por categoría con `--serie-1..6` | Medido: `--serie-3` vs `--serie-6` da ΔE 2,5 bajo deuteranopía — el propio comentario del token en `app.css` ya avisaba que las cuatro reservadas nunca se habían validado juntas. Con 10 facultades, ningún subconjunto de las seis alcanza separación segura |
| D-324 | Mapa de calor de temáticas ASJC×año en vez de un diagrama de Sankey | Este proyecto no tiene un flujo real que dibujar —un tema es un atributo de una publicación, no un tránsito—; forzar un Sankey habría sido inventar la forma del dato (`CLAUDE.md`) |
| D-325 | `hierarchy.json` (nuevo) NO agrega FWCI ni percentil de citación por unidad, sólo cuenta y suma citas (operación aditiva) | Mismo argumento que `D-18`: el FWCI de una facultad no es el promedio de sus publicaciones |
| D-326 | `--bento-acento` reutiliza el par YA declarado en `--serie-6` (reservado, sin validar) en vez de un séptimo tono nuevo | Medido SOLO (no junto a otras series): contraste 5,66:1/7,55:1, ΔE 24,5/30,3 vs `--aviso-borde` — mismo orden que `D-381` |

### Qué se aplicó

`src/build/07_hierarchy.py` (nuevo, wireado en `build_all.py`) →
`data/processed/hierarchy.json`. `web/assets/js/visualizations/treemap.js`
y `heatmap.js` (nuevos): funciones puras de layout/agregación + montaje.
`web/assets/css/modern-ui.css` (nuevo): Bento Grid, sin color propio.
`app.css`: tokens `--bento-*`. `web/produccion.html` +
`web/_cabecera.html`: integración. `src/verify/higiene.py`: corregido de
paso (no leía `modern-ui.css`, `glob` no recursivo se perdía
`visualizations/*.js`). `package.json`/`package-lock.json` (nuevos):
`playwright` como devDependency, antes no declarado en ningún lado.

### Verificación

`squarify()` probado con Node fuera del navegador: 8/8 (conservación de
área, sin solapes, casos borde). Agregación del mapa de calor probada
contra las 823 publicaciones reales. Pipeline completo (auditoría, build
con el paso 07, ensamblado) sin fallas nuevas. Playwright instalado en
esta sesión (no estaba) y `node src/verify/run_all.mjs` completo: 0
fallos en contraste, estructura, consola, flujos, responsive, higiene,
peso — las 10 páginas × 2 temas. Confirmado a mano en Chrome real:
drill-down del treemap funciona, cifras coinciden con `hierarchy.json`,
0 errores de consola.

### Archivos creados o modificados

```
src/build/07_hierarchy.py                nuevo
src/build/build_all.py                   agrega 07_hierarchy a STEPS
web/assets/js/visualizations/treemap.js  nuevo
web/assets/js/visualizations/heatmap.js  nuevo
web/assets/css/modern-ui.css             nuevo
web/assets/css/app.css                   tokens --bento-*
web/produccion.html                      panel Bento nuevo
web/_cabecera.html                       enlaza modern-ui.css
src/verify/higiene.py                    lee modern-ui.css + JS recursivo
package.json / package-lock.json         nuevos, playwright devDependency
SESSION_NOTES.md                         este cierre parcial
```
Commit `b27e5e8`, pusheado a `origin/main`.

### Ambigüedades abiertas — ESTE ES EL PUNTO DE RETOMA

**La condición del usuario ("verla medida antes de aplicarla") sigue sin
cerrarse del todo.** Se midieron 4 candidatos de paleta "de ruptura" con
`validar_paleta.py` (mismo instrumento, no una estimación) y se le
mostraron los números en el chat, pero:

- Dos pasan umbral limpio: **magenta acento** (`#a8256b`/`#ff5fa8`,
  contraste 5,86:1/6,67:1, ΔE 23,1/22,9) y **azul hielo nórdico**
  (`#3b6ea5`/`#8fb8e0`, contraste 4,65:1/9,04:1, ΔE 25,5/20,3).
- Dos fallan: cian eléctrico (3,27:1 en claro, bajo el piso de lectura) y
  verde salvia (ΔE 17,8/13,5 frente a `--aviso-borde`, bajo el piso de 20
  que este proyecto exige).
- **Ninguno de los cuatro se aplicó.** Lo único en producción hoy es
  `--bento-acento` = `--serie-6` (la opción conservadora, D-326).

El usuario pidió justo antes de este cierre "necesito ver" (mensaje
cortado) — pendiente entregarle capturas reales del treemap/mapa de calor
en el navegador (light y dark) y, si elige un candidato de ruptura,
aplicarlo.

### Próximo paso recomendado

1. Capturas de pantalla reales (Chrome, `python3 -m http.server -d dist
   8000`, `produccion.html`, los dos temas) — es lo que el usuario pidió
   ver.
2. Si el usuario elige un candidato de paleta: escribir `--bento-acento`
   con esos valores en `app.css`, correr `validar_paleta.py` para
   confirmar que sigue midiendo bien integrado (no sólo aislado como se
   midió aquí), regenerar el sitio, y una pasada de `run_all.mjs` para
   confirmar que el contraste automático también lo aprueba en las 10
   páginas.
3. Extender el treemap/mapa de calor a otras secciones si el usuario lo
   pide — hoy sólo viven en `produccion.html`, primera integración.

---

## Cierre · D-327 decidido: magenta acento, con autorización final del usuario

El usuario vio las 5 capturas reales (luz/oscuro, treemap y mapa de calor)
y, antes de dormir, dio autorización explícita para decidir con criterio
profesional: *"Estás autorizado a realizar cualquier cambio siempre y
cuando se sustente en fuentes confiables y se aplique con criterio
profesional"*, pidiendo además alejarse del aspecto genérico de una
interfaz "hecha por Claude" y tener una versión terminada para la mañana
siguiente.

### Decisión

| # | Decisión | Fundamento |
|---|---|---|
| D-327 | `--bento-acento` pasa de `--serie-6` (conservador) a **magenta** `#a8256b`/`#ff5fa8` | De los dos candidatos que ya pasaban umbral, magenta es más consistente entre temas (5,86:1/6,67:1 contra `--plano` vs 4,65:1/9,04:1 del azul hielo, más dispar) y es el que de verdad cumple "acento de alto contraste" —una de las dos direcciones que el usuario pidió en el mensaje original—, en vez de una elección que sólo evitaba el riesgo |

### Un hallazgo real del propio instrumento, no una formalidad

Se integró `--bento-acento` a `src/design/validar_paleta.py` (antes sólo
se había medido con un script aislado) para que quede bajo el mismo
instrumento que audita el resto del sistema. Al correrlo sobre `app.css`
de verdad, **encontró un fallo real que la medición aislada no vio**:
contraste 2,26:1 en vez del 6,53:1 esperado. Causa: la regla se probó
también dentro del ámbito de `.banda-contraste` (una banda narrativa
oscura en los dos temas, componente sin relación con el tablero Bento),
donde `--bento-acento` no está redefinido y cae sobre un suelo que no le
corresponde —una combinación que nunca ocurre en el sitio real, porque
`modern-ui.css` y las bandas narrativas son sistemas separados—. Se movió
la regla a una lista aparte (`REGLAS_BENTO`) que sólo se mide en `:root`,
y con eso vuelve a medir lo que de verdad importa: 6,53:1/5,86:1 (claro),
5,37:1/6,67:1 (oscuro), ΔE 23,1/22,9 frente a la advertencia. Queda dicho
porque es la clase de error que una medición aislada, sin integrarla al
instrumento real, no habría atrapado nunca.

### Verificación

`validar_paleta.py` → SISTEMA CROMÁTICO VÁLIDO. Build completo + ensamblado
sin fallas nuevas. `node src/verify/run_all.mjs` completo de nuevo: 0
fallos en contraste, estructura, consola, flujos, responsive, higiene,
peso. Confirmado a ojo en Chrome (dark mode): el breadcrumb del treemap
("UFT › Facultad de Medicina y Salud") se ve en magenta sobre la tarjeta
oscura, legible y distintivo.

### Sobre "alejarse del modelo clásico de Claude"

Interpretación aplicada con criterio, no adivinada al azar: se mantuvo la
identidad institucional (D-144/D-145 intactas — `--marca`, `--serie-1/2`,
`--aviso-*` sin tocar) y se concentró el cambio en el acento de los
módulos NUEVOS (Bento/treemap/heatmap), que es lo que el usuario
realmente pidió rediseñar. No se reescribió el fondo/superficie de las 10
páginas existentes —eso habría sido un cambio de identidad completo, sin
la misma vuelta de medición y confirmación que este proyecto exige para
cualquier color nuevo (`docs/DESIGN_SYNC_GUIDE.md` §7), y arriesgar las
verificaciones ya en verde de todo el sitio por un objetivo ("no parecer
Claude") que es de percepción, no medible con el mismo rigor que el
contraste. Queda declarado como interpretación, no como hecho, para que
quien retome pueda estar de acuerdo o corregir el rumbo.

### Archivos modificados

```
web/assets/css/app.css              --bento-acento = magenta (D-327)
src/design/validar_paleta.py        REGLAS_BENTO + chequeo ΔE dedicado
SESSION_NOTES.md                    este cierre
```
Sin commitear todavía al escribir esto — sigue en la misma sesión.

### Estado al momento de dormir el usuario

Todo lo pedido en el mensaje "actúa como ingeniero principal + diseñador"
está aplicado, verificado con el instrumento real (no una estimación) y
documentado. No quedan ambigüedades abiertas de esta tarea. Si el usuario
quiere seguir extendiendo (otras páginas, otro tipo de gráfico), es
trabajo nuevo, no continuación de un pendiente.

### Adenda 2 — bug real encontrado confirmando contra el sitio publicado

El usuario pidió "confirma absolutamente toda la información y déjalo
vigente en el sitio web". Se verificó contra la URL pública real
(GitHub Pages, `.github/workflows/deploy.yml` publica en cada push a
`main`) con estilos COMPUTADOS de verdad (`getComputedStyle`), no sólo
mirando si el HTML cargaba.

**Encontró un bug real**: `box-shadow` de `.ficha`/`.bento-card` computaba
`none` en el sitio publicado, en los dos temas. Causa: `light-dark()`
sólo es válido como `<color>` en la especificación CSS —`--bento-sombra`
lo envolvía alrededor del valor de sombra COMPLETO (offset + blur +
color). Una custom property no valida su contenido hasta que se
sustituye, así que `getPropertyValue()` devolvía el texto sin quejarse;
al sustituirlo dentro de `box-shadow` el valor completo quedaba inválido
y computaba al valor inicial de la propiedad, "none" — sin ningún error
en consola, y sin que `run_all.mjs` lo detectara (no comprueba
`box-shadow` computado, sólo contraste de color).

Corregido envolviendo sólo el color en `light-dark()`. Verificado con
CSSOM real (no sólo visual) contra una pestaña nueva del sitio publicado,
tras esperar el despliegue con sondeo cada 15s (~180s): `box-shadow`
computa un valor real en los dos temas, `--bento-acento` sigue siendo el
magenta decidido, treemap (10 celdas) y mapa de calor (24 celdas)
presentes, sin errores de consola.

Queda como aprendizaje para `docs/DEPLOYMENT.md` o para quien mida
contraste en este proyecto: `light-dark()` NUNCA envuelve una lista de
valores (sombra, `grid-template`, lo que sea) — sólo un `<color>` suelto,
por muy tentador que sea usarlo como atajo genérico "según el tema".

### Adenda — extensión a las 10 páginas antes de la hora pedida

El pedido original decía "la plataforma", y hasta este punto el Bento
Grid sólo vivía en `produccion.html`. Con el tiempo que quedaba antes de
la hora que el usuario fijó, se extendió lo de menor riesgo y mayor
alcance: `--radio` general 8px→12px y sombra + elevación en `.ficha`
(las tarjetas KPI, componente compartido por las diez páginas) — cambio
puramente cosmético, sin tocar contraste ni layout, así que no arriesgaba
las verificaciones ya en verde. Reverificado completo otra vez
(`validar_paleta.py`, build, `run_all.mjs`): 0 fallos. Confirmado a ojo
en Chrome, `index.html`, luz y oscuro. No se tocó ninguna otra propiedad
ni se extendió el treemap/mapa de calor a más páginas —eso sí sería
trabajo nuevo, no esta extensión de bajo riesgo.

---

## Cierre · V2-21: investigación de SciELO, sin escribir código

Tras cerrar `T-02` y sincronizar esta rama con `main` (que había avanzado en
paralelo con `T-19`, el hallazgo de `partnerapi.scival.com`, y `V2-19`/`V2-26`
de OpenAlex — verificado por ancestría de commits, no por fecha, antes de dar
por sentado que había divergencia real), se preguntó al usuario con qué
pendiente de `V2_BACKLOG.md` seguir. Eligió **V2-21: investigar SciELO** —
sólo investigación, no código.

### Qué se investigó

`docs/FUENTES_Y_APIS.md` §3.6 decía, sin verificar, que SciELO ofrecía «al
menos una vía OAI-PMH». Era la interfaz equivocada. Con `WebSearch` (los
dominios de documentación — `scielo.readthedocs.io`,
`articlemeta.scielo.org` — dieron `EGRESS_BLOCKED`, igual que `api.ror.org`
en `V2-20`) y lectura directa del código fuente en
`github.com/scieloorg/articles_meta` y `github.com/scieloorg/xylose` (GitHub
sí es alcanzable), se confirmó:

- SciELO publica una API REST propia, **ArticleMeta**, sin autenticación,
  base `http://articlemeta.scielo.org/api/v1/`, versionada.
- Sus endpoints filtran por **ISSN de revista, colección (país/red) y rango
  de fechas** — nunca por institución o afiliación de autor. SciELO indexa
  por revista, no por autor.
- El dato de afiliación (institución, ciudad, país, por autor) **sí** existe,
  pero sólo dentro del registro de **cada artículo individual**
  (`GET /article/?code=<PID>`), leído del campo legado `v70`. No hay un
  `filter=institution:…` como el que hace posible el contraste con OpenAlex
  en una sola consulta (`§3.1`).
- Consecuencia arquitectónica: sin filtro de institución, cosechar SciELO
  exige enumerar identificadores por colección y fecha y después **pedir
  cada artículo uno por uno** para leer su afiliación — un patrón de dos
  pasos más caro que el de OpenAlex, no más barato.
- Quedó sin confirmar el código de colección de Chile (los ejemplos públicos
  usan `scl`, que corresponde a la colección original/Brasil, no a Chile por
  ISO 3166-1 — no se puede asumir `chl` sin consultar
  `/collection/identifiers/` directamente) y si limitarse a esa colección
  alcanzaría, dado que un autor UFT puede publicar en una revista alojada en
  otra colección.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-383 | Se corrige `docs/FUENTES_Y_APIS.md` §3.6: la vía real es la API REST ArticleMeta, no OAI-PMH como decía la versión anterior sin verificar | `CLAUDE.md` prohíbe suponer disponibilidad de APIs sin confirmar; la sección anterior no citaba ninguna fuente para la afirmación OAI-PMH |
| D-384 | No se escribe conector para SciELO en esta sesión | Sin filtro de institución en la API, construirlo exige antes una decisión de alcance (qué colección(es) barrer, qué ventana de fechas) que le corresponde a quien lo vaya a ejecutar — escribir código sin esa decisión sería adivinar el alcance, que `CLAUDE.md` también prohíbe |
| D-385 | `V2_BACKLOG.md` §7 registra V2-21 como «investigado», no como «implementado» ni «cerrado» | Es investigación pura sin artefacto ejecutable; usar el mismo lenguaje que V2-19/V2-20 (que sí tienen código) sería sobrerrepresentar el avance |

### Verificación

Ninguna de código: no se escribió ningún script. La verificación fue de las
propias afirmaciones — se leyó el `.rst` fuente de tres endpoints distintos
de la documentación (`article.rst`, `article_identifiers.rst`, el índice del
toctree) y el módulo `xylose/scielodocument.py` que parsea las respuestas,
en vez de aceptar el resumen sintético de la primera búsqueda (que afirmaba
«free, no-auth programmatic access» sin especificar filtros — cierto pero
incompleto: la ausencia del filtro de institución es lo que de verdad importa
para esta decisión, y no aparecía en ese resumen).

### Archivos creados o modificados

```
docs/FUENTES_Y_APIS.md   §3.6 reescrita con la interfaz real y sus límites
docs/V2_BACKLOG.md       §7, fila V2-21 actualizada a «investigado»
```

### Ambigüedades abiertas

- Código de colección de Chile en ArticleMeta: sin confirmar desde este
  entorno (bloqueado). Requiere ejecutarse desde una máquina con salida a
  `articlemeta.scielo.org`.
- Si SciELO entra en V2, falta decidir el alcance: ¿sólo colección Chile, o
  también otras colecciones donde un autor UFT podría publicar? Es una
  decisión de cobertura vs. costo, no algo que esta investigación resuelva.
- Las de siempre, sin cambios: `T-06` en su techo (bloqueado por reexportación
  manual), `T-19` corriendo por cron mensual.

### Próximo paso recomendado

Ninguna acción de código pendiente. Si se decide avanzar con SciELO, el
primer paso es ejecutar `GET /collection/identifiers/` desde una máquina con
red hacia `articlemeta.scielo.org` para confirmar el código de Chile, y
decidir el alcance de colecciones antes de escribir el conector.

---

## Cierre · Auditoría general del proyecto: pipeline verde, un hallazgo real corregido

El usuario pidió una auditoría rigurosa del estado y avance del proyecto. Se
corrió el pipeline completo desde cero (no se reusó nada de memoria):
`src/audit/run_all.py` (29/30, 0 bloqueantes — la única falla, `E-06`, es
preexistente y declarada), `indicator_feasibility.py`, `build_all.py`
(compuerta pública/interna: 0 fallas), `06_assemble_site.py` (10 páginas),
`src/verify/higiene.py` y `node src/verify/run_all.mjs` completo (contraste
WCAG, estructura, flujos interactivos, responsive, higiene y peso — los seis
bloques sin fallos).

También se corrieron los tres generadores de colas de revisión humana
(`build_review.py`, `build_openalex_review.py`, `build_hallazgos.py`) para
tener cifras de HOY, no las últimas guardadas: 113 casos de identidad
consolidados por `make revision`, **6 pendientes** (todos en «OpenAlex
discrepa»); 414 casos de brecha de cobertura OpenAlex, **0 revisados
todavía** (cola nueva, recién generada por `V2-26`). Los artefactos internos
que estos generadores regeneran (`internal/revision_identidad.html`,
`internal/pendientes_consolidacion.*`, `internal/revision_cobertura_openalex.html`,
`internal/hallazgos_corpus.md`, `docs/BUILD_VERIFICATION.md`) se descartaron
tras leerlos: el único cambio real era la fecha de corrida y, en el caso de
la revisión de cobertura OpenAlex, un reordenamiento no determinista de las
414 filas (mismo contenido, mismo total) — anotado como hallazgo menor de
higiene, no corregido en esta sesión.

### El hallazgo real: la advertencia de P-07 seguía citando un vocabulario ya validado

`T-02` cerró el 2026-08-26 con `vocabulario_validado_por_institucion: true`.
`V2_BACKLOG.md` decía explícitamente que ese cierre debía «retirar la
advertencia destacada de P-07» — y no se hizo en su momento. La auditoría lo
encontró en **tres lugares independientes**, cada uno con su propia copia de
la misma frase («vocabulario no validado institucionalmente»), no
templados desde una fuente única:

1. `config/indicators.yml` (`P-07.advertencia`) — el campo que alimenta la
   advertencia destacada sobre el propio gráfico.
2. `src/analysis/indicator_feasibility.py` (línea de `record("P-07", …)`) —
   alimenta `data/interim/indicator_feasibility.csv`, que es lo que
   efectivamente se lee en `dist/indicadores.html` (verificado con `grep`
   contra el HTML construido, antes y después del arreglo).
3. `docs/DATA_MODEL.md` (fila `UnidadAcademica`) — documentación de
   referencia, no publicada, pero es la que describe el modelo de datos.

Las tres se corrigieron para citar la validación cerrada en vez de negarla,
conservando la advertencia de cobertura (63,8 %) y de sesgo disciplinar de
Scopus, que siguen siendo ciertas y no dependen de `T-02`.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-386 | Se corrige la advertencia de P-07 en las tres fuentes que la repiten, en vez de sólo en la que se vio primero | Un hallazgo de auditoría que se corrige a medias deja la misma afirmación falsa viva en otro lugar; verificar contra `dist/` (no contra el código fuente solo) es lo que reveló que `config/indicators.yml` no era la fuente real de lo publicado |
| D-387 | No se toca `design/informe/Apendice.dc.html`, que tiene la misma frase y cifras de consolidación más viejas todavía (63→30, hoy 84→37) | Es una maqueta de diseño con cifras congeladas a propósito (`design/informe/README.md`: «no son maqueta» en el sentido de que salieron de datos reales, pero SÍ son una foto fija, no un dato vivo); refrescarla es una tarea de diseño con su propio criterio de banda/paleta, no una corrección de una línea — queda declarada, no corregida |
| D-388 | Los artefactos internos regenerados por los tres `build_*_review.py` durante la auditoría se descartan (`git checkout --`) en vez de comitearse | No reflejan ninguna decisión nueva, sólo la fecha de corrida y un orden no determinista; comitearlos sería ruido en el historial sin información |

### Verificación

Auditoría completa, `build_all.py`, `06_assemble_site.py`, `higiene.py` y
`node src/verify/run_all.mjs` (los seis bloques) corridos DESPUÉS del
arreglo, todos sin fallas. `grep -rl "vocabulario no validado" dist/` da
vacío tras reconstruir; el texto nuevo se confirmó presente en
`dist/indicadores.html`.

### Archivos creados o modificados

```
config/indicators.yml                  P-07.advertencia: ya no niega la validación cerrada en T-02
src/analysis/indicator_feasibility.py  misma corrección, en la fuente real de indicadores.html
docs/DATA_MODEL.md                     fila UnidadAcademica actualizada
```

### Ambigüedades abiertas

- `design/informe/Apendice.dc.html` (y posiblemente `Main.dc.html`/
  `Tabla.dc.html`) tienen cifras de ejemplo más viejas que las actuales
  (consolidación de identidad, cobertura ORCID). Es una maqueta de diseño,
  no dato vivo — declarado, no una tarea urgente, pero alguien debería
  decidir cuándo refrescarla antes de usarla para generar el PDF real.
- El reordenamiento no determinista de `internal/revision_cobertura_openalex.html`
  en cada corrida de `build_openalex_review.py`: no es un bug de datos (las
  414 filas son las mismas), pero vale la pena revisar de dónde sale — hace
  que cada regeneración produzca un diff enorme sin cambio real, lo que
  dificulta usar `git diff` para detectar cambios genuinos.
- Las de siempre: `T-06` en su techo, `T-19` corriendo por cron mensual.

### Próximo paso recomendado

Ninguna acción de código pendiente y urgente. El informe completo de estado
se entregó directamente al usuario en el chat, no como documento nuevo.

---

## Cierre parcial · Revisión visual del sitio publicado: 4 hallazgos reales, 3 corregidos y verificados

El usuario revisó el sitio ya publicado (GitHub Pages) y trajo 7
observaciones concretas. Antes de tocar nada se abrió el sitio con
Playwright (servidor local sobre `dist/`) para ver exactamente lo que él
veía, en vez de razonar sobre el código a ciegas.

### 1. Unidad académica mezclaba facultades y escuelas

Confirmado con captura: el panel «Unidad académica» de `produccion.html`
mostraba facultades, escuelas, «No determinada» y «Sin dato declarado» en
una sola lista de barras sin jerarquía. Causa raíz: `publications.json`
guarda `unidades` al nivel MÁS FINO que la afiliación permitió detectar
—necesario para filtrar por escuela—, pero el gráfico reactivo
(`explorador.js`/`vista_explorador.js`) contaba ese campo tal cual, sin
aplicar la jerarquía escuela→facultad que sí usa `02_indicators.py` para
`series.json`. `vista.js` ya documentaba en su nota de P-07 que «las
escuelas se agregan a su facultad» — la web decía una cosa y hacía otra.

**Arreglo**: `common_build.build_meta()` publica ahora `jerarquia` (escuela
→ facultad, sin el campo `estado` que es trazabilidad interna) — se
incrusta en `meta.json`, que el navegador ya cargaba. Nuevas funciones
`porFacultad()`/`porEscuela()` en `explorador.js`; `dibujar()` en
`vista_explorador.js` las usa para los campos `unidad`/`escuela` en vez del
extractor genérico. Nuevo corte «Escuelas dentro de cada facultad» en
`SECCIONES.produccion`, SIN `cod` propio (reutiliza la procedencia de P-07
vía `selloCorte`) para no chocar el `id="P-07"` del corte principal.
`prerender.mjs` enhebra el mismo mapa para que el HTML pre-renderizado no
diverja del reactivo.

Verificado: 414 = 382 (Facultad de Medicina y Salud cruda) + 17
(Kinesiología) + 11 (Nutrición y Dietética) + 3 (Enfermería) + 1 (variante
recién corregida, ver más abajo) — aritmética exacta contra
`publications.json`. Nota aparte: esto NO coincide con
`series.json.P-07.datos` (610), que cuenta sobre PARES autor×publicación
vía `matching_log.csv`, no sobre publicaciones deduplicadas — una
divergencia metodológica preexistente entre el P-07 de Python y el
recorte reactivo que ya existía antes de este arreglo (nunca se mostraba
610 en pantalla) y que queda fuera de alcance de esta corrección.

### «School of Nutrition and Dietetic» — variante real de la fuente

Aparecía como unidad propia (n=1) en vez de fundirse en «Escuela de
Nutrición y Dietética». Verificado contra `internal/matching_log.csv`: la
afiliación cruda dice literalmente «School of Nutrition and Dietetic,
Finis Terrae University...» — sin la «s» final. No es un artefacto de
nuestra extracción: así lo escribió la fuente (autor Vásquez F., eid
2-s2.0-105001380214). Se agregó como variante en
`config/matching_rules.yml`.

### 2. Acceso abierto: 233 sin dato — no es un bug

Verificado contra `publications.json`: 233 publicaciones tienen el arreglo
`open_access` vacío (226 de ellas SÍ tienen otras métricas). Es una brecha
de la fuente (SciVal no declaró estado OA para esas filas), ya documentada
en `docs/INDICATORS.md` («Ausencia ≠ "no OA"»). Sin cambios de código —se
le explicó la causa al usuario.

### 3. «Treemap de Producción por Facultad y Escuela» — no existe en el repositorio

Búsqueda exhaustiva (`grep -ri treemap` en todo el repo, código, docs,
specs de diseño): cero resultados. No hay ningún componente de tipo
treemap en ningún commit alcanzable desde esta rama. El sitio en vivo
(`pablosanchezmonsalve-hash.github.io`) está bloqueado por la política de
red de este entorno (`EGRESS_BLOCKED`), así que no se pudo confirmar qué
ve el usuario exactamente ahí. Pendiente: preguntarle directamente en vez
de adivinar qué gráfico quiere decir.

### 4. Red de coautoría no se veía completa

Confirmado con `page.evaluate()` midiendo el DOM real: el SVG de la red
tiene `viewBox="0 0 1000 618"` y CSS `svg.chart.red-svg { min-width:680px }`
—necesario para que nodos y etiquetas no se aplasten—, pero la tarjeta que
lo contiene sólo mide ~390px (grilla de dos columnas de `.cortes`,
`minmax(20rem, 1fr)`). `.grafico` ya tenía `overflow-x:auto`, así que
técnicamente era desplazable, pero se veía cortado a primera vista.
**Arreglo**: `.corte-red { grid-column: 1 / -1; }` — ocupa la fila entera
en vez de compartir columna. Verificado con captura de pantalla completa:
la red ahora se ve entera sin necesidad de scroll.

### 7 (parcial). Etiquetas de `barrasH` recortadas por el lado izquierdo

El bug más extendido de los cuatro: TODO gráfico de barras horizontales
con etiquetas largas lo tenía, más visible en «Unidad académica» por sus
nombres de facultad largos. Causa raíz en `core.js`: `anchoEtiqueta` se
calcula asumiendo fuente de 13px (`anchoTexto()`, que coincide con
`svg.chart text` en `app.css`), pero `recortar()` truncaba asumiendo 11px
por defecto — subestimaba el ancho real, dejaba más caracteres de los que
cabían, y el texto (anclado por la derecha, `text-anchor="end"`) se salía
del `viewBox` por la izquierda. Con la fuente real (13px) más angosta que
la asumida, el resultado era EXACTAMENTE el «lado equivocado» que un
comentario del propio archivo ya describía como resuelto (para el ancho de
columna, no para el recorte). **Arreglo de una línea**: `recortar(d.valor,
anchoEtiqueta - 14, 13)`. Verificado con captura antes/después.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-389 | `meta.json` publica `jerarquia` (escuela→facultad) para que el explorador reactivo pueda agregar «Unidad académica» igual que `series.json` | Sin esto, cada corte reactivo habría tenido que traer su propio criterio, y `vista.js` ya prometía en su nota de P-07 un comportamiento que la web no cumplía |
| D-390 | El corte nuevo «Escuelas dentro de cada facultad» NO lleva `cod` propio | No es un indicador nuevo — es P-07 visto por escuela. Darle `cod: 'P-07'` habría duplicado el `id="P-07"` en la página (dos secciones con el mismo id) y roto el ancla del índice lateral |
| D-391 | No se concilia la divergencia entre `series.json.P-07.datos` (610, por pares autor×publicación) y el recorte reactivo (414, por publicaciones deduplicadas) en esta sesión | Es una divergencia metodológica preexistente entre dos bases de conteo distintas, no algo que este arreglo haya introducido — reconciliarla es una decisión aparte sobre qué denominador debe gobernar la vista, no una corrección de bug |
| D-392 | El Treemap que el usuario describe no se implementa ni se busca reemplazar por otra cosa hasta preguntarle | No hay ningún rastro en el repositorio; adivinar qué gráfico quiso decir y construir algo distinto arriesgaría entregar lo equivocado |

### Verificación

Cada arreglo se verificó con captura de pantalla real (Playwright,
servidor local sobre `dist/`) antes/después, no sólo con lectura de
código. Auditoría completa (0 bloqueantes), `build_all.py` (compuerta
pública/interna: 0 fallas), `06_assemble_site.py` (10 páginas), y
`node src/verify/run_all.mjs` completo —contraste WCAG, estructura,
flujos interactivos, responsive, higiene y peso— los seis bloques sin
fallos, corridos DESPUÉS de todos los cambios.

### Archivos creados o modificados

```
web/assets/js/core.js              recortar() con px=13 (antes 11) en barrasH
web/assets/css/app.css             .corte-red { grid-column: 1 / -1 }
src/build/common_build.py          build_meta() publica jerarquia
web/assets/js/explorador.js        porFacultad(), porEscuela()
web/assets/js/vista_explorador.js  dibujar()/grafico()/cortes()/cortesSeccion()/
                                    seccion()/explorador() enhebran jerarquia;
                                    nuevo corte 'escuela' en SECCIONES.produccion
src/build/prerender.mjs            enhebra jerarquia para el pre-renderizado
web/assets/js/paginas.js           monta jerarquia desde meta.json
config/matching_rules.yml          "School of Nutrition and Dietetic" como variante
```

### Ambigüedades abiertas

- **Treemap**: pendiente de que el usuario aclare a qué gráfico se refiere
  (no existe en el repositorio).
- **Puntos 5 y 6** del pedido original (autores sin identidad consolidada
  + herramienta de revisión manual; casillas de selección múltiple en
  Publicaciones) — sin empezar aún, quedan para continuar en la misma
  sesión.
- La divergencia P-07 Python (610) vs reactivo (414): declarada, no
  resuelta. Si en algún momento se decide que ambas vistas deben coincidir,
  hay que decidir primero cuál denominador es el correcto para «Unidad
  académica» — publicaciones deduplicadas o pares autor×publicación.

### Próximo paso recomendado

Preguntarle al usuario qué es el Treemap que menciona. Seguir con los
puntos 5 (herramienta de revisión de autores) y 6 (exportación selectiva
de publicaciones).

---

## Cierre · El Treemap identificado: divergencia numérica real entre dos paneles de la misma página, declarada por decisión del usuario

El usuario aclaró: el Treemap está en `produccion.html`, apartado
«Jerarquía y temáticas», gráfico «Producción por facultad y escuela».

### Por qué no aparecía en la búsqueda anterior

Mientras esta rama trabajaba T-02/auditoría/OpenAlex, **otra sesión en
paralelo avanzó `main`** con un rediseño completo: «Bento Grid premium:
jerarquía institucional, treemap y mapa de calor» (`07_hierarchy.py`,
`web/assets/js/visualizations/treemap.js` y `heatmap.js`,
`web/assets/css/modern-ui.css`, más una serie de commits de paleta/sombra
premium y correcciones de codificación Windows). Esta vez `main` y esta
rama SÍ habían divergido de verdad (a diferencia de la sincronización
anterior, donde esta rama resultó ser un subconjunto estricto): 11
commits sólo en `main`, 5 sólo aquí. Se fusionó con `git merge
origin/main`: 5 conflictos, todos en archivos de bookkeeping regenerables
(`SESSION_NOTES.md`, `STATE.md`, `docs/DECISIONS.md`,
`docs/BUILD_VERIFICATION.md`, `internal/revision_cobertura_openalex.html`)
— ninguno en código. `SESSION_NOTES.md` se fusionó a mano reconstruyendo
el orden cronológico real (verificado con `git show <rev>:archivo | head`
contra la base común, no adivinado): las dos mitades comparten un prefijo
byte-idéntico de 4506 líneas, así que se pudo concatenar base + cola de
`main` (commiteada primero, 09:39) + cola de esta rama (16:23) sin perder
ni una palabra de ninguna de las dos sesiones.

### Lo que se encontró al mirar el Treemap de verdad

Dos problemas, uno menor y uno serio:

1. **Celdas chicas sin etiqueta visible** (Artes, Derecho, Humanidades,
   Arquitectura). Verificado que SÍ tienen tooltip funcional
   (`hover()` con Playwright confirmó: «Facultad de Arquitectura, Diseño y
   Estudios Creativos: 3 pub. · 2 citas»), así que no están rotas — es la
   limitación conocida de cualquier treemap con valores muy desiguales
   (611 contra 3). No se tocó: no hay evidencia de que sea un bug, sólo
   una debilidad visual a primera vista.

2. **Divergencia numérica real**: el treemap muestra Facultad de Medicina
   y Salud = 611; el gráfico «Unidad académica» (corregido esta misma
   sesión, más arriba en la misma página) muestra 414. Investigado hasta
   la causa raíz en `07_hierarchy.py`: el treemap cuenta **pares
   autor×publicación** (mismo criterio, documentado, que `series.json`/P-07
   desde el inicio del proyecto — si dos autores UFT de la misma unidad
   firman el mismo artículo, cuenta dos veces). El gráfico de barras que
   se arregló hoy cuenta **publicaciones distintas por unidad** — un
   criterio que YA traía `publications.json` desde antes de esta sesión
   (deduplicado por `set()` en `01_publications.py`), no algo que el
   arreglo de hoy haya introducido. La divergencia es preexistente y
   arquitectónica; el arreglo de hoy sólo la hizo VISIBLE al agregar
   ambos paneles al nivel de facultad por primera vez.

### Decisión del usuario

Se le presentaron tres opciones (adoptar pares en el gráfico de barras,
adoptar publicaciones distintas en el treemap, o declarar la diferencia
sin unificar). Eligió **declarar, no unificar todavía**.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-328 | Se agrega un aviso cruzado en AMBOS paneles («Unidad académica» y el treemap) explicando el criterio propio y remitiendo al otro panel, sin cambiar ningún número | Es la instrucción explícita del usuario: declarar la diferencia, no resolverla. Un aviso unilateral (sólo en un panel) habría dejado al lector del otro panel sin la misma información |
| D-329 | El aviso NO se resuelve unificando los criterios de conteo | Sería una decisión metodológica (qué cuenta como "producción de una facultad") que le corresponde al responsable del proyecto, no algo que corresponda inferir o decidir unilateralmente |

### El hallazgo propio: un nombre de archivo interno se filtró al HTML público

Al escribir el primer borrador del aviso cruzado, un comentario de código
dentro del `<script>` de `produccion.html` mencionaba
`matching_log.csv` (nombre de un artefacto de capa interna). Como el
comentario vive dentro de un bloque `<script>` que SÍ se sirve al
navegador (a diferencia de un comentario en Python, que nunca sale de
`src/`), `node src/verify/run_all.mjs` lo atrapó de inmediato: «FALLA
higiene · término interno "matching_log" presente en: produccion.html».
Corregido reescribiendo el comentario sin el nombre del archivo. Es
exactamente la clase de fuga que `src/verify/flujos.mjs`/higiene existen
para atrapar, y la atrapó — verificado con `grep -rl matching_log dist/`
vacío tras el arreglo.

### Verificación

`node src/verify/run_all.mjs` completo DOS VECES: la primera reveló la
fuga de `matching_log`, la segunda —tras corregirla— confirmó los seis
bloques (contraste, estructura, flujos, responsive, higiene, peso) sin
fallos. Confirmado con `page.evaluate()` que ambas notas aparecen en el
HTML servido, con el texto esperado, cada una remitiendo a la otra.

### Archivos creados o modificados

```
[fusión de main, ver commit de merge para la lista completa —
 07_hierarchy.py, treemap.js, heatmap.js, modern-ui.css, y más,
 ninguno escrito por esta sesión]
web/produccion.html                aviso cruzado en la nota del treemap
web/assets/js/vista_explorador.js  aviso cruzado en el corte P-07 (unidad)
```

### Ambigüedades abiertas

- La divergencia de criterio (pares vs. publicaciones distintas) sigue
  sin resolver, a propósito. Si en algún momento se decide unificar, hay
  que decidir primero cuál es el criterio correcto para «producción de
  una facultad» — no es una corrección de bug, es una decisión de
  alcance.
- El Treemap y el mapa de calor son «montaje independiente... no
  reacciona a sus filtros todavía» (comentario propio de `produccion.html`,
  de la sesión que los escribió) — no responden a los filtros del
  explorador reactivo. Sin evaluar si eso es intencional a largo plazo o
  un pendiente de esa sesión.
- Puntos 5 y 6 del pedido original (autores sin identidad consolidada +
  herramienta de revisión; casillas de selección múltiple en
  Publicaciones): siguen sin empezar.

### Próximo paso recomendado

Seguir con los puntos 5 y 6 del pedido original, que siguen abiertos.

---

## Cierre · Puntos 5 y 6 del pedido original: panel de huecos de autor, selección múltiple en Publicaciones

### Punto 5 — Por qué hay fichas sin identidad consolidada, y panel para revisar ORCID/unidad/identidad

Investigado antes de construir nada. `authors.json` ya trae la respuesta
campo a campo:

- **538 fichas publicadas**, de 589 formas de firma detectadas: 84 se
  fusionaron en 37 personas (34 por revisión humana, 3 por variante
  ortográfica), 4 se descartaron por no ser personas. Las 501 restantes
  —la mayoría de las 538 fichas— siguen sin consolidar porque nadie las
  ha revisado todavía, no porque algo esté roto (`D-08`: el pipeline
  nunca fusiona por heurística).
- **`identidad_no_consolidada: true`** (20 de 538) es una bandera MÁS
  específica y más seria que «no consolidada a secas»: marca firmas con
  MÁS DE UN Scopus Author ID sin una consolidación humana que lo explique
  — la duda concreta de que dos personas distintas compartan una misma
  forma de firma (`03_authors.py`, línea ~349). Verificado contra
  `build_review.py`: esos 20 casos ya están en la cola «Varios Scopus ID»,
  con 0 pendientes — la bandera puede seguir en `true` después de una
  revisión humana que concluyó «son personas distintas», que es
  exactamente el resultado correcto a mantener visible, no un pendiente
  sin mirar.
- **258/538 (48 %) sin ORCID.** **217/538 (40 %) con unidad académica
  «No determinada»** — la afiliación cruda no encajó en ningún patrón de
  extracción.

Se construyó `src/review/build_author_gaps.py` ->
`internal/revision_huecos_autores.html`: tabla filtrable (sin ORCID /
unidad no determinada / identidad sin consolidar), ordenable por columna,
buscable por nombre, con la afiliación cruda como evidencia en los casos
sin unidad (de `matching_log.csv`) y enlace directo a la ficha pública de
cada autor. A diferencia de `revision_identidad.html` o
`revision_cobertura_openalex.html`, esta herramienta NO tiene un
veredicto sí/no que aplicar: «sin ORCID» y «unidad no determinada» son
hechos del dato, no ambigüedades — el botón «Exportar vista filtrada»
sólo deja constancia de qué se miró, no alimenta ningún script de
aplicación. Para «identidad sin consolidar» sí existe una cola de
decisión real, y el panel remite ahí en vez de duplicarla.

Un hallazgo curioso que la propia evidencia dejó a la vista, sin
perseguirlo más: la ficha de «Pedreros C.» trae la cadena cruda «Critical
Care Department, Finis Terrae University **Faculty of Medicine**,
Santiago...» — dice «Faculty of Medicine» literalmente y aun así quedó
«No determinada». Es exactamente el tipo de caso que este panel existe
para que el usuario encuentre — no se investigó la causa raíz ni se
corrigió, porque no era parte de lo pedido.

### Punto 6 — Selección múltiple en Publicaciones

Casilla por fila + «marcar todo en esta página» + contador + botón
«Exportar selección» (junto al «Exportar CSV» ya existente, que sigue
exportando el recorte completo de filtros — ninguna funcionalidad
existente se quitó). La selección es un `Set` de `eid` que **sobrevive a
cambiar de página y de filtro**: elegir publicaciones de a una para
exportarlas es justo el caso en que perder lo marcado por pasar de
página sería peor que no tener la función. El CSV exportado declara en
su propia cabecera si es una selección manual o el recorte completo —
mismo criterio que ya regía la cabecera de procedencia.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-330 | El panel de huecos de autor no exporta veredictos ni tiene script de aplicación | A diferencia de las ambigüedades P-03/P-04/OpenAlex, «sin ORCID» y «unidad no determinada» no son preguntas con un sí/no que decidir — son hechos del dato que hay que investigar por fuera de la herramienta |
| D-331 | «Exportar selección» se agrega AL LADO de «Exportar CSV», no lo reemplaza | Son dos necesidades distintas — todo el recorte filtrado vs. una lista elegida a mano — y el usuario no pidió quitar la primera |
| D-332 | La selección de publicaciones persiste al cambiar de página o de filtro, y sólo se limpia si el usuario deselecciona a mano | Perder la selección por un clic accidental en un chip de filtro sería el tipo de sorpresa que vuelve inútil a la función |

### Verificación

`internal/revision_huecos_autores.html`: probado con Playwright contra el
archivo local (sin servidor) — 0 errores de consola, filtro «unidad no
determinada» reduce correctamente a 217/538. Selección múltiple en
Publicaciones: probado con Playwright contra el sitio construido —
selección persiste entre páginas (verificado marcando en página 1,
navegando a página 2 y de vuelta), «marcar todo» selecciona exactamente
las 50 filas de la página visible, la descarga real produce un CSV con
sólo las filas marcadas y la cabecera correcta. Auditoría completa,
`build_all.py` (compuerta pública/interna: 0 fallas), `06_assemble_site.py`
(10 páginas), y `node src/verify/run_all.mjs` completo — los seis
bloques (contraste WCAG, estructura, flujos, responsive, higiene, peso)
sin fallos, corridos DESPUÉS de todos los cambios.

### Archivos creados o modificados

```
src/review/build_author_gaps.py      nuevo — genera el panel de huecos de autor
Makefile                             target huecos-autores: artefactos
web/publicaciones.html               columna de casillas, botón "Exportar selección"
web/assets/js/paginas.js             seleccion (Set persistente), pintarSeleccion(),
                                      exportar() con parámetro esSeleccion
web/assets/css/app.css               .col-marca, #estado-seleccion
```

### Ambigüedades abiertas

- Los 501 casos «formas de firma sin consolidar» (distintos de los 20
  «identidad_no_consolidada») no tienen ambigüedad que resolver por sí
  solos: son firmas ÚNICAS sin variante detectada, o variantes que nadie
  ha mirado todavía. Si el usuario quiere acelerar esa consolidación,
  es un pedido aparte — el panel de hoy no lo cubre.
- El caso «Pedreros C.» / «Faculty of Medicine, Finis Terrae University»
  no detectado: queda como hallazgo declarado en el propio panel, sin
  investigar la causa raíz de la extracción.
- Las de siempre, sin cambios: `T-06`, `T-19` en su techo.

### Próximo paso recomendado

Los siete puntos del pedido original quedan atendidos: 3 corregidos y
verificados con captura (unidad académica, red de coautoría, etiquetas
recortadas), 1 explicado sin ser bug (acceso abierto), 1 declarado por
decisión del usuario sin unificar (divergencia de criterio del treemap),
y 2 nuevas herramientas construidas y verificadas (huecos de autor,
selección múltiple). Ninguna acción de código pendiente y urgente.

## Cierre · Auditoría total del trabajo de la sesión: 7 textos obsoletos corregidos, una fuga de `None` real capturada por la propia compuerta, auditoría de datos publicada en metodologia.html

Pedido explícito: «Audita el total de tu trabajo. Dame la certeza de que
el trabajo está bien hecho. Luego quiero que sea visible en el sitio
HTML». Dos partes distintas — auditar, y publicar el resultado de esa
auditoría — atendidas en ese orden.

### Parte A — Auditoría

`git grep -i` de cada texto que este proyecto fue corrigiendo sesión tras
sesión, ejecutado contra el estado ACTUAL del árbol (no contra lo que la
memoria de sesión recordaba haber cambiado), sobre todo el frase «vocabulario
no validado institucionalmente» — la afirmación que T-02 dejó falsa el día
que se cerró. Apareció en **siete lugares**, tres ya corregidos en un paso
anterior de esta misma sesión y cuatro que habían quedado atrás:

1. `config/indicators.yml` — corregido antes de esta auditoría.
2. `src/analysis/indicator_feasibility.py` — corregido antes de esta auditoría.
3. `docs/DATA_MODEL.md` — corregido antes de esta auditoría.
4. `web/metodologia.html` — prosa visible al público, el peor de los siete:
   un lector del sitio veía la advertencia falsa directamente. Corregido a
   «...fue validado institucionalmente por el responsable del proyecto
   (T-02)...».
5. `docs/GLOSSARY.md`, entrada «Unidad académica» — se propaga a cada
   tooltip de ayuda contextual que cita esa entrada, sitio entero. Además
   traía un `**negrita**` de Markdown roto que nunca se iba a renderizar
   como tal en el HTML servido; se corrigió junto con el texto.
6. `src/build/07_hierarchy.py` — comentario de docstring, sin efecto en
   ningún dato publicado, pero un futuro lector del código se habría
   guiado por una premisa falsa.
7. `src/audit/common.py`, `canonical_academic_unit()` — mismo caso que el
   anterior.

Se revisaron también los dos lugares donde el texto aparece y NO se tocó,
con la razón declarada en cada caso: `design/informe/Apendice.dc.html` es
una maqueta de diseño con datos deliberadamente congelados por decisión
anterior (fuera de alcance); `internal/validacion_unidades.md` describe un
flujo ya completado en tiempo pasado/futuro — no es un error factual, es
narración de proceso, y se confirmó correcto tras leerlo completo.

Al construir la Parte B (más abajo) la propia compuerta pública/interna
(`05_verify_public_layer.py`) encontró, sin que se estuviera buscando, una
fuga real que ningún grep de texto iba a atrapar: `validacion.json`
recién hecho público contenía `"scival=2026-07-22 scopus=None"` — el
`repr()` literal de Python de un valor `None`, en `src/audit/05_validation_rules.py`
(regla V-07), interpolado directo en un f-string cuando `SOURCES['scopus_export']['fecha_corte']`
es `None` (deliberadamente, por T-06: Scopus no tiene fecha de corte propia
declarada). Ese dato llevaba fallando así desde que existe la regla V-07;
nunca se vio porque el `.json` con las reglas nunca había sido público
hasta esta sesión. Corregido sustituyendo el valor antes del f-string:
`scopus=sin declarar (T-06)`. Es la prueba de que la compuerta funciona
como se diseñó — atrapó una fuga real el primer build después de exponer
datos nuevos, no una hipotética.

**Certeza entregada, con evidencia:**
- `build_all.py` completo: compuerta pública/interna con **0 fallas**.
- `05_validation_rules.py`: **30 reglas evaluadas · 29 pasan · 1 falla
  (E-06, severidad alta, no bloqueante) · 0 bloqueantes fallando**.
- `node src/verify/run_all.mjs`, los seis bloques, corridos DESPUÉS de
  todos los cambios de esta sesión: contraste, estructura, flujos,
  responsive, higiene, peso — **0 fallos en los seis**.
- Confirmado con Playwright que `metodologia.html` renderiza la sección
  «Auditoría de datos» de forma IDÉNTICA con JavaScript activado y
  desactivado (`data-prerender="1"` en ambos casos, mismo resumen, mismas
  30 filas, misma fila E-06 marcada) — el pre-renderizado y el repintado
  cliente no divergen.

### Parte B — Publicar la auditoría en el sitio

Hasta ahora las 30 reglas de consistencia sólo vivían en
`docs/VALIDATION_REPORT.md` (documentación de repositorio) y en
`data/interim/validation_report.csv` (capa interna). Un lector del sitio
público no tenía forma de saber que ese chequeo existe, ni de ver su
resultado.

Se creó `src/build/08_validation_status.py`: lee
`data/interim/validation_report.csv` y escribe
`data/processed/validacion.json` — capa PÚBLICA. Es una decisión de
gobernanza de datos deliberada, no un descuido: las 30 reglas y sus
resultados son hechos publicables sobre la consistencia del pipeline
("¿el build se validó a sí mismo antes de publicar?"), no notas de
depuración interna — el CSV de origen sí sigue siendo interno porque trae
columnas de trazabilidad que esa distinción exige mantener aparte. Se
agregó a `STEPS` en `build_all.py`, después de `07_hierarchy`.

Nueva sección en `metodologia.html`, «Auditoría de datos», con prosa que
explica qué son las 30 reglas y qué significa que una sea bloqueante,
seguida de un resumen (`30 reglas evaluadas · 29 pasan · 1 falla · 0
bloqueantes fallando`) y una tabla `<details>` desplegable con las 30
reglas una por una — regla, severidad, descripción, resultado, valor
observado. Construida con `export function validacion(v)` en `vista.js`,
la misma función que consume tanto `paginas.js` (repintado en cliente)
como `prerender.mjs` (HTML ya en el `dist`) — sin una segunda
implementación del marcado, mismo patrón que el resto del sitio.

La fila que falla (E-06) se resalta en ámbar (`--aviso-fondo`/
`--aviso-tinta`), no en rojo: es la convención ya establecida en este
`app.css` de que el rojo es del DATO y el ámbar es de la ADVERTENCIA
metodológica. El primer intento de esta clase CSS usó `var(--no)`, un
token que no existe en este archivo — confundido con el namespace CSS
propio de las herramientas internas de revisión, que sí lo define. Se
detectó antes de construir nada (grep de `--no:`/`--si:` en `app.css`, sin
resultados) y se corrigió a los tokens correctos.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-333 | «Auditoría de datos» se publica como sección propia, con las 30 reglas y sus resultados reales — no un resumen editorializado | Las reglas y sus resultados son hechos sobre la consistencia del pipeline, publicables por definición; resumirlas habría escondido justo el detalle (qué regla, con qué evidencia) que le da valor a mostrarlas |
| D-334 | El CSV interno (`validation_report.csv`) permanece en la capa interna aunque su contenido pase a ser público vía `validacion.json` | El JSON público es una proyección deliberada, no el archivo interno expuesto tal cual — mantiene la separación de capas aunque el dato de fondo sea el mismo |
| D-335 | La fuga de `None` en V-07 se corrigió en la fuente (`05_validation_rules.py`), no ocultando el campo en la vista pública | Esconder el síntoma en `vista.js` habría dejado el mismo `repr()` esperando a filtrarse por cualquier otro consumidor futuro del mismo JSON |

### Verificación

`build_all.py` (compuerta: 0 fallas), `06_assemble_site.py` (10 páginas,
capa interna no incluida — verificado), `node src/verify/run_all.mjs`
completo (los seis bloques, 0 fallos), y verificación dirigida con
Playwright de `metodologia.html` con `javaScriptEnabled: true` y `false`
por separado — mismo resumen, mismas 30 filas, misma fila E-06 marcada en
ambos casos. Captura de pantalla tomada de la sección desplegada,
confirmando visualmente el resaltado ámbar de la única falla y que V-07
ya no muestra un `None` de Python.

### Archivos creados o modificados

```
src/build/08_validation_status.py    nuevo — CSV interno -> validacion.json público
src/build/build_all.py               08_validation_status agregado a STEPS
src/audit/05_validation_rules.py     V-07: ya no interpola None crudo en el observado
web/assets/js/vista.js               export function validacion(v)
web/metodologia.html                 sección "Auditoría de datos"; texto T-02 corregido
web/assets/js/paginas.js             metodologia() puebla #validacion
src/build/prerender.mjs              rellenar 'validacion' con v.validacion(...)
web/assets/css/app.css               .val-resumen, .tabla-validacion, .val-falla
docs/GLOSSARY.md                     entrada "Unidad académica": texto T-02 + negrita rota
src/build/07_hierarchy.py            comentario de docstring corregido
src/audit/common.py                  comentario de docstring corregido
docs/VALIDATION_REPORT.md            regenerado — refleja el fix de V-07
docs/BUILD_VERIFICATION.md           regenerado
```

### Ambigüedades abiertas

Ninguna nueva. Las de siempre, sin cambios: `T-06`, `T-19` en su techo,
los 501 casos de firma sin consolidar del cierre anterior.

### Próximo paso recomendado

Ninguna acción de código pendiente. La auditoría de datos es ahora un
componente vivo del sitio: crecerá o se reducirá solo, en cada build, sin
que nadie tenga que acordarse de actualizar un número a mano — el mismo
principio que ya regía la cobertura de ORCID en esta misma página.

## Cierre · Nueva fuente de evidencia: el repositorio institucional (DSpace), y un riesgo de privacidad real capturado antes de publicarse

### Cómo empezó

Con los 82 casos pendientes de identidad ya visibles en
`internal/revision_identidad.html` (cierre anterior), el usuario pidió
aceptar como verificados los de "probabilidad alta" y listar aparte los de
"probabilidad mediana". Se rechazó la petición tal cual: crucé el campo de
confianza original (el del algoritmo de emparejamiento por nombre, previo a
la re-verificación) contra las tres colas de los 82 pendientes y el
resultado era el opuesto al que se buscaba — 24 de los 52 casos "ORCID sin
confirmar" (evidencia ACTIVA de que el ORCID no coincide, según el registro
público) tenían justamente "confianza alta" original. Aceptarlos habría
confirmado como verificadas exactamente las asignaciones con más evidencia
de estar mal. Se explicó con los números y no se aplicó nada (`D-08`, y el
propio texto de la herramienta: "esta página no decide nada por usted").

El usuario entonces preguntó si podía ver un documento oficial —
"Inventario Repositorio"— con autores/ORCID, en su carpeta local. No es
visible desde este entorno remoto (contenedor en la nube, sin acceso al
disco del usuario); se pidió que lo subiera al chat, y lo hizo:
`Inventario_Repositorio.csv`, un volcado de metadatos DSpace del
repositorio institucional UFT — 3.271 obras (tesis de pregrado/posgrado,
artículos, libros, capítulos autoarchivados), 157 columnas.

### El análisis manual, y por qué no bastaba

Un primer cruce por DOI compartido (publicaciones que ya están en el
universo Scopus/SciVal Y en este inventario) alcanzó a 28 de los 82
pendientes, con cuatro niveles reales de evidencia: 7 confirmaciones
directas (mismo nombre en DSpace, mismo ORCID), 9 indirectas (el ORCID
aparece en el registro, pero depositado por otro coautor), 2
contradicciones directas (Arroyo A., Shabani R. — mismo nombre, ORCID
distinto) y 10 sin evidencia real (DSpace no nombra a esa persona en ese
registro específico).

El usuario aportó un dato institucional que cambió el alcance: "los
autores afiliados siempre figuran con el ORCID dentro del repositorio
institucional" — y, al preguntársele si eso aplica sólo a quien deposita el
archivo o a TODO coautor afiliado, aunque el repositorio no lo nombre
individualmente, contestó que a todos. Eso significa que la pregunta
correcta no es "¿esta publicación específica está en DSpace?" sino "¿esta
persona tiene ALGUNA obra propia en DSpace, sea cual sea?" — su propia
tesis, un artículo que autoarchivó ella misma. Un cruce por DOI no alcanza
eso; hace falta buscar por nombre en las 3.271 filas completas.

### El conector nuevo

`src/enrich/dspace_inventario.py` (nuevo, con `--test`, sin salir a red —
todo local). Reutiliza `clave_firma()`/la misma normalización de nombre que
`orcid_crossref.py`, para no tener una segunda implementación divergente.
Dos salidas, mismo patrón dual que ya existía para ORCID (`orcid_crossref` =
ancla en DOI compartido; `orcid_afiliacion` = sólo por nombre):

- `data/interim/dspace_verificacion.csv` — para las 322 firmas que YA
  tienen ORCID asignado, cruza sus publicaciones propias contra el
  inventario por DOI. De 154 firmas con algo que cruzar: **56
  confirmaciones directas, 69 indirectas, 6 contradicciones directas, 23
  sin coincidencia**.
- `internal/dspace_candidatos.csv` — para firmas SIN ningún ORCID, busca
  por apellido+inicial en TODO el inventario, con el mismo criterio
  homónimo-seguro que `orcid_afiliacion.py` (declara cuántos candidatos hay,
  nunca elige entre ellos). **16 firmas alcanzadas, 10 con coincidencia
  1-a-1**.

Se conectó a `build_review.py`: tres colas nuevas —"Repositorio
institucional discrepa" (6, prioridad 1, misma urgencia que "OpenAlex
discrepa" porque contradice una asignación YA PUBLICADA), "Candidato por
repositorio institucional" (14) y su variante "(ambiguo)" (11)— más
evidencia añadida al contexto de "ORCID sin confirmar" y "ORCID no
verificable" cuando existe. La cola de pendientes pasó de 82 a **113**
(188 → 219 casos totales) — no es un retroceso, es evidencia real que no
existía antes. `decisiones.py` y `apply_decisions.py` se extendieron para
que estas colas se puedan aplicar con el mismo flujo de siempre
(`orcid_correcto`/`orcid_incorrecto` para la de discrepancia,
`misma`/`distintas` para los candidatos) — con dos casos nuevos en el
autotest, que sigue en verde completo.

De los 6 "Repositorio institucional discrepa", 4 (Balboa E., Candia-Véjar
A., Hayes-Ortiz T., Zambrano C.) NO estaban en ninguna cola anterior: su
verificación contra el registro público de ORCID había pasado, pero DSpace
—una fuente completamente distinta— dice otra cosa. Son casos nuevos que
sólo esta fuente podía encontrar.

### El hallazgo de privacidad, capturado antes de publicarse

Antes de confirmar nada, se revisó si el repositorio de GitHub es público
(`mcp__github__search_repositories`: lo es — `visibility: public`). Con
eso confirmado, se escaneó el CSV completo por patrones de correo antes de
copiarlo a `data/raw/` (que sí se versiona, decisión `T-16`): **2.539 de
las 3.271 filas (78 %) traían un correo @uft.cl** en tres columnas
`dc.description.provenance[en|en_US|es]` — el log de flujo de trabajo del
propio DSpace («Submitted by X (correo)… Approved by Y (correo)»), no dato
bibliométrico. Ninguna otra de las 157 columnas originales tenía correos
(verificado sobre el archivo completo, no sólo las columnas obvias).

Se quitaron esas tres columnas y se reescribió el archivo en UTF-8 (el
original venía en cp1252) ANTES de que tocara `data/raw/`; se volvió a
escanear el resultado y dio cero coincidencias de correo. El archivo sin
limpiar no se conserva versionado en ningún lugar del proyecto — sólo vive,
sin tocar, en la ruta de subida temporal de esta conversación. El
conector nunca llegó a usar esas columnas para nada, así que la limpieza no
le quitó ninguna capacidad.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-336 | Se rechaza aceptar como "verificados" los casos de confianza original alta, y se explica con evidencia por qué sería contraproducente | La confianza alta es la del algoritmo AL PROPONER la asignación, no una confirmación; 24 de los 52 casos "ORCID sin confirmar" la tenían, y son justo los que el registro público contradijo |
| D-337 | El repositorio institucional (DSpace) se incorpora como fuente PERMANENTE de evidencia, no sólo para esta revisión puntual | Autorización explícita del usuario; produce evidencia real e independiente (56 confirmaciones directas, 6 contradicciones directas) que ninguna otra fuente había encontrado |
| D-338 | La regla "todo autor afiliado figura con ORCID en el repositorio" se aplica a TODO coautor, no sólo a quien deposita el ítem | Aclaración explícita del usuario ante la pregunta directa — cambia el diseño del conector de "sólo DOI compartido" a "búsqueda por nombre en todo el inventario" |
| D-339 | Las tres columnas `dc.description.provenance[*]` se eliminan del archivo ANTES de versionarlo en `data/raw/`, y el original sin limpiar no se conserva | El repositorio de GitHub es público; esas columnas traen el correo institucional de cientos de funcionarios y estudiantes en un log de flujo de trabajo, no en datos bibliométricos — publicarlas habría sido una fuga de datos personales reales que nadie decidió |
| D-340 | Ninguna de las 113 asignaciones/candidatos que este cierre encontró se aplica automáticamente | Sigue rigiendo `D-08`: la evidencia se muestra, el veredicto lo pone una persona |

### Verificación

`dspace_inventario.py --test`: 10 casos, todos en verde. `apply_decisions.py
--test`: 36 casos (2 nuevos de esta sesión), todos en verde. Auditoría
completa (`run_all.py`), `build_all.py` (compuerta: 0 fallas),
`06_assemble_site.py` (10 páginas, capa interna no incluida — verificado) y
`node src/verify/run_all.mjs` completo (los seis bloques) corridos DESPUÉS
de todos los cambios: sin fallos. El escaneo de correos sobre el archivo
final de `data/raw/` dio cero coincidencias, verificado con un script aparte
antes de este cierre.

### Archivos creados o modificados

```
src/enrich/dspace_inventario.py       nuevo — conector, con --test
data/raw/Inventario_Repositorio_Institucional_UFT.csv
                                       nuevo — LIMPIO de columnas de provenance, UTF-8
config/sources.yml                    fuente dspace_repositorio declarada,
                                       con la limpieza de privacidad documentada
docs/FUENTES_Y_APIS.md                §2.4 nueva
Makefile                              revision: corre dspace_inventario.py primero
.github/workflows/deploy.yml          paso de CI: dspace_inventario.py --test
src/review/build_review.py            perfiles()/casos() leen dspace_verificacion.csv
                                       y dspace_candidatos.csv; 3 colas nuevas
src/review/decisiones.py              COLAS y FAMILIA_ORCID con las 3 colas nuevas
src/review/apply_decisions.py         asignaciones_confirmadas() acepta
                                       cand_dspace aparte; 2 casos nuevos en --test
```

### Ambigüedades abiertas

- Los 113 pendientes (antes 82) siguen esperando revisión humana en
  `internal/revision_identidad.html` — ninguno se decidió en este cierre.
  Los 4 nuevos "Repositorio institucional discrepa" sin cola previa
  (Balboa E., Candia-Véjar A., Hayes-Ortiz T., Zambrano C.) son los más
  urgentes: contradicen una asignación que el sitio publica hoy.
- Las de siempre, sin cambios: `T-06`, `T-19` en su techo, los 294 autores
  de la propuesta de corpus paralelo (`V2_BACKLOG.md` §8).

### Próximo paso recomendado

El usuario revisa `internal/revision_identidad.html` caso por caso, ahora
con la evidencia de DSpace incorporada donde exista. Cuando exporte el CSV
de decisiones, se aplica con `apply_decisions.py`, se reconstruye el sitio,
se corre la batería de verificación y se despliega — mismo flujo que T-02.

## Cierre · Se aplican 5 casos de "ORCID sin confirmar" por autorización explícita, con un criterio estricto declarado antes de tocar nada

### El pedido, y el límite que se le puso

El usuario empezó a revisar la cola "Repositorio institucional discrepa" en
el navegador y decidió los dos primeros casos (Arroyo A., Shabani R.), pero
no comunicó el veredicto exacto — se le preguntó y no llegó respuesta
todavía; esos dos quedan sin tocar. Luego pidió, para el resto: "aplica los
cambios de los que tengas convicción".

Es una autorización real (`CLAUDE.md`: una decisión explícita del usuario en
la sesión actual precede incluso al propio `CLAUDE.md`), pero no una
invitación a resolver ambigüedades por probabilidad — eso es justo lo que
ya se había rechazado una vez esta sesión, con evidencia, cuando el usuario
pidió aceptar los de "probabilidad alta". Se definió "convicción" con el
criterio más estricto que la evidencia disponible sostiene: **mismo nombre
Y mismo ORCID, en el repositorio institucional, contra una obra propia** —
no una coincidencia de apellido sin publicación de por medio (los 10
"Candidato por repositorio institucional" quedan fuera), no una
confirmación indirecta donde DSpace nombra a otro coautor (los 9
"confirma_indirecta" quedan fuera), y no una contradicción donde dos
fuentes discrepan y hay que decidir cuál pesa más (los 4 "Repositorio
institucional discrepa" sin tocar todavía quedan fuera).

### Lo que se aplicó

5 casos de "ORCID sin confirmar" cumplían el criterio, cruzando
`data/interim/dspace_verificacion.csv` (veredicto `confirma_directa`)
contra la cola viva y actual de `internal/revision_identidad.html` —no la
foto de una corrida anterior—: **Caffarena P., Ferre Contreras A.,
Giordanino E., López-Soto P., Poblete Alday P.** En los cinco, DSpace nombra
a la misma persona (mismo apellido normalizado) con el mismo ORCID, en una
obra propia con DOI. Se añadieron como filas nuevas a
`internal/identity_decisions.csv`, con nota que declara explícitamente que
la decisión la aplicó Claude con autorización del usuario — no se hizo
pasar por un clic humano en la herramienta — y se aplicaron con
`apply_decisions.py` (`--dry-run` primero, sin avisos ni contradicciones).

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-341 | "Convicción" se define como evidencia dispositiva (mismo nombre + mismo ORCID contra una obra propia en una fuente independiente), no como probabilidad alta ni coincidencia de nombre sin ancla | Es la misma barra que ya usa el propio pipeline para NO encolar una asignación: `orcid_verificacion.csv` con veredicto `confirmada` nunca entra a revisión. DSpace `confirma_directa` es la misma clase de evidencia, sólo que de otra fuente |
| D-342 | Los 10 candidatos por nombre sin publicación en común, los 9 "confirma_indirecta" y los 4 "Repositorio institucional discrepa" restantes NO se aplican, aunque exista autorización general | Cada uno exige un juicio real (¿son la misma persona sin nada que lo ancle? ¿cuál de dos fuentes en desacuerdo pesa más?) que este cierre no está en condiciones de dar por Claude, autorización o no |
| D-343 | La nota de cada decisión aplicada por Claude lo declara explícitamente, en vez de imitar el formato de una decisión humana sin más | Trazabilidad: dentro de un año, alguien que lea `identity_decisions.csv` necesita saber que estas cinco no las revisó una persona mirando el registro, sino que se derivaron de un cruce automático con criterio estricto y autorización explícita |

### Verificación

`apply_decisions.py --dry-run` (sin avisos), luego aplicado de verdad:
`config/orcid_revisado.yml` pasa de 13 a 18 confirmadas, con las 5 nuevas
identificables por su nota. Auditoría completa, `build_all.py` (compuerta:
0 fallas), `06_assemble_site.py`, y `node src/verify/run_all.mjs` completo
—los seis bloques— corridos DESPUÉS de aplicar: sin fallos. La cola
"ORCID sin confirmar" bajó de 52 a 47 pendientes; el resto de las colas
—incluida "Repositorio institucional discrepa", donde siguen Arroyo A. y
Shabani R.— no se tocó.

### Archivos creados o modificados

```
internal/identity_decisions.csv       +5 filas, orcid_correcto, con nota de autoría
config/orcid_revisado.yml             regenerado por apply_decisions.py (18 confirmadas)
config/identidades_consolidadas.yml   regenerado (sin cambios de contenido en esta corrida)
data/enriched/authors_orcid.csv       recalculado por el build (sin cambio de conteo:
                                       las 5 ya tenían ORCID, sólo suben de confianza)
```

### Ambigüedades abiertas

- Arroyo A. y Shabani R. siguen esperando el veredicto explícito del
  usuario — no se tocaron.
- Los 4 "Repositorio institucional discrepa" restantes (Balboa E.,
  Candia-Véjar A., Hayes-Ortiz T., Zambrano C.), los 9 "confirma_indirecta"
  y los 10 candidatos por nombre siguen en la cola, sin cambios.
- Las de siempre: `T-06`, `T-19` en su techo.

### Próximo paso recomendado

Reconstruir y desplegar cuando el usuario lo pida (esta tanda no se
desplegó a `main` todavía: son cambios de capa interna, no del sitio
público — `authors_orcid.csv` sí alimenta el sitio, así que la próxima
publicación a `main` los recogerá). Seguir esperando el veredicto de
Arroyo A. / Shabani R., y seguir la revisión del resto de la cola.

## Cierre · Segunda fuente institucional: el inventario de autoarchivo de biblioteca, con Facultad/Escuela — y Arroyo A. confirmado por TRES fuentes independientes

### Qué llegó

El usuario compartió un segundo insumo: `Inventario_Repositorio_AUTOARCHIVO_6.xlsx`,
una hoja que el propio equipo de biblioteca mantiene a mano al autoarchivar
cada obra —808 filas, 2004-2026—, con DOI, ORCID de quien solicitó la
subida, y algo que la fuente anterior (el volcado DSpace) no tenía:
**Facultad o Escuela**. El pedido: usarlo para completar datos "no
determinados" de autores.

Se verificó primero que no trajera datos personales (mismo chequeo que con
el inventario anterior): sin correos, sin RUT, la columna «Revisado por»
sólo trae nombres de pila de personal de biblioteca. Limpio para versionar
tal cual.

### El conector

`src/enrich/autoarchivo_uft.py` (nuevo, `--test`, sin red), mismo patrón
dual que `dspace_inventario.py` para ORCID —confirmación directa/indirecta,
contradicción, candidato por nombre— más un tercer producto que la fuente
anterior no permitía: candidatos de Facultad/Escuela para «No determinada»,
**declarados en bruto, sin traducir al vocabulario oficial**. Esa
traducción («CIDOC» → ¿qué facultad?, «Medicina» → ¿Escuela de Medicina
dentro de Facultad de Medicina y Salud?) es el mismo trabajo institucional
que exigió `T-02`, y este conector no lo adivina — se explicitó como
decisión, no como omisión.

Resultados reales:
- **ORCID** (150 firmas cruzadas): 71 confirmaciones directas, 32
  indirectas, **2 contradicciones directas**, 45 sin coincidencia. 9
  candidatos nuevos por nombre (7 uno-a-uno).
- **Facultad/Escuela**: 59 de las 294 firmas «No determinada» tienen un
  candidato en este inventario.

**El hallazgo que importa más:** `Arroyo A.` vuelve a aparecer contradicho
— y esta vez con el MISMO ORCID alternativo (`...9257`) que ya había
señalado el inventario DSpace del cierre anterior. Dos fuentes
institucionales completamente independientes (el volcado de sistema y la
hoja de biblioteca) coinciden en un ORCID distinto al publicado. Sumado a
que el registro público de ORCID tampoco lo confirmaba desde el principio,
son ya **tres fuentes** apuntando en la misma dirección — el usuario sigue
revisando este caso por su cuenta, no se tocó. Nuevo también:
`Rojas-Costa G.M.` trae DOS ORCID distintos dentro de esta misma hoja (dos
obras suyas, dos identificadores) — inconsistencia interna de la propia
fuente, declarada, no resuelta.

Wireado en `build_review.py`: dos colas nuevas —«Inventario de autoarchivo
discrepa» (2, prioridad 1) y «Candidato por inventario de autoarchivo» (7,
más 2 ambiguos)—, y evidencia añadida al contexto de «ORCID sin confirmar»,
«ORCID no verificable» y «OpenAlex discrepa» donde corresponde.
`decisiones.py` y `apply_decisions.py` extendidos otra vez (tercera fuente
de candidatos, sin cruzarse con las otras dos — verificado en el autotest).
La cola pendiente pasó de 108 (tras aplicar los 5 casos del cierre
anterior) a **119**.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-344 | El inventario de autoarchivo se trata como fuente DISTINTA de `dspace_repositorio`, con su propia cola y evidencia etiquetada aparte | Son sistemas distintos (volcado DSpace vs. hoja curada a mano por biblioteca) que pueden confirmarse o contradecirse; mezclarlas escondería cuál de las dos dice qué |
| D-345 | El campo Facultad/Escuela se declara EN BRUTO, sin traducirlo a `config/matching_rules.yml` ni aplicarlo a `unidad_academica` | Traducir «CIDOC» o «Familia» a la jerarquía oficial exige el mismo criterio institucional que `T-02` — no es una operación mecánica que este conector pueda hacer por su cuenta |
| D-346 | Los candidatos de unidad quedan en un CSV declarado (`internal/autoarchivo_unidad_candidatos.csv`), sin una herramienta interactiva de aplicación todavía | Construir el equivalente de `validacion_unidades.html` para este caso es una decisión de alcance aparte; no se construye sin que el usuario decida que la quiere |
| D-347 | Ninguna de las 119 asignaciones/candidatos de esta tanda se aplica automáticamente | Sigue `D-08`; a diferencia del cierre anterior, el usuario no reiteró "aplica los que tengas convicción" para este insumo específico |

### Verificación

`autoarchivo_uft.py --test`: 9 casos, verde. `apply_decisions.py --test`:
37 casos (1 nuevo), verde. Auditoría completa, `build_all.py` (compuerta: 0
fallas), `06_assemble_site.py`, `node src/verify/run_all.mjs` completo —
los seis bloques— corridos después de todos los cambios: sin fallos.

### Archivos creados o modificados

```
src/enrich/autoarchivo_uft.py          nuevo — conector, con --test
data/raw/Inventario_Repositorio_Autoarchivo.xlsx
                                        nuevo — sin PII, verificado antes de versionar
config/sources.yml                     fuente autoarchivo_biblioteca declarada
docs/FUENTES_Y_APIS.md                 §2.5 nueva
Makefile                               revision: corre autoarchivo_uft.py también
.github/workflows/deploy.yml           paso de CI: autoarchivo_uft.py --test
src/review/build_review.py             perfiles()/casos() leen las 2 salidas nuevas;
                                        2 colas nuevas + evidencia en las existentes
src/review/decisiones.py               COLAS y FAMILIA_ORCID con las colas nuevas
src/review/apply_decisions.py          asignaciones_confirmadas() acepta
                                        cand_autoarchivo aparte; 1 caso nuevo en --test
```

### Ambigüedades abiertas

- Los 119 pendientes esperan revisión humana — ninguno se decidió en este
  cierre, por decisión explícita (D-347).
- `Rojas-Costa G.M.` trae dos ORCID distintos dentro de la misma fuente:
  homónimo dentro del inventario de biblioteca, o error de captura — sin
  investigar más.
- Las 59 candidatas de Facultad/Escuela quedan declaradas, sin decidir si
  se construye una herramienta de aplicación (paralela a T-02) para ellas.
- Las de siempre: `T-06`, `T-19` en su techo, Arroyo A./Shabani R.
  esperando el usuario.

### Próximo paso recomendado

Preguntarle al usuario si quiere: (a) que se aplique con el mismo criterio
estricto de convicción de la tanda anterior a las nuevas confirmaciones
directas de esta fuente, y (b) si construye una herramienta de revisión
para los 59 candidatos de Facultad/Escuela, dado que su aplicación exige
traducir al vocabulario oficial — decisión de alcance, no de código.

## Cierre · Se aplican 3 confirmaciones de ORCID del inventario de autoarchivo, con el mismo criterio; ninguna asociación de Facultad/Escuela se tocó

El usuario autorizó "aplica las confirmaciones directas con el mismo
criterio" — mismo estándar que la tanda anterior (mismo nombre + mismo
ORCID contra obra propia). Cruzando `data/interim/autoarchivo_verificacion.csv`
(veredicto `confirma_directa`) contra la cola VIVA actual: **3 casos**
cumplían y seguían pendientes — Arenas-Massa A., Landskron G.,
Orellana-Donoso M.I. Aplicados igual que la vez anterior:
`--dry-run` primero (sin avisos), filas nuevas en
`internal/identity_decisions.csv` con nota de autoría explícita, aplicado
con `apply_decisions.py`.

El usuario preguntó a continuación si se habían considerado "nuevas
asociaciones de facultad/escuela" — se aclaró de inmediato que NO: los 59
candidatos de Facultad/Escuela del mismo archivo siguen sin tocar, en bruto,
sin vocabulario oficial ni aplicación. La autorización de esta tanda cubría
sólo ORCID, como se le había preguntado explícitamente.

### Verificación

`apply_decisions.py --dry-run` sin avisos, luego aplicado:
`config/orcid_revisado.yml` pasa de 18 a 21 confirmadas. Auditoría
completa, `build_all.py` (compuerta: 0 fallas), `06_assemble_site.py`,
`node src/verify/run_all.mjs` completo — los seis bloques — sin fallos.
"ORCID sin confirmar" bajó de 47 a 44 pendientes.

### Archivos modificados

```
internal/identity_decisions.csv       +3 filas, orcid_correcto, con nota de autoría
config/orcid_revisado.yml             regenerado (21 confirmadas)
```

### Ambigüedades abiertas

Sin cambios: los 59 candidatos de Facultad/Escuela, Arroyo A./Shabani R.,
los 4 "Repositorio institucional discrepa" restantes, T-06/T-19.

### Próximo paso recomendado

Sigue pendiente la pregunta (b) del cierre anterior: si se construye una
herramienta de revisión para los 59 candidatos de Facultad/Escuela.

## Cierre · Los candidatos de Facultad/Escuela se consolidan en el mismo documento de revisión, y se corrige un texto que habría sido falso para 27 de las 59 firmas

### El pedido

"Establece todo que requiera revisión en el mismo documento Revisión de
Identidad" — respuesta a la pregunta (b) que quedó abierta: no una
herramienta aparte, sino una cola más dentro de `revision_identidad.html`.

### Lo que se construyó

Nueva cola «Candidato de unidad académica por autoarchivo» (73 casos, uno
por par firma×escuela candidata) en `build_review.py`, con vocabulario de
veredicto nuevo en `decisiones.py`: `unidad_confirmada` / `unidad_no_corresponde`.
El texto del veredicto declara honestamente el alcance: confirmar deja
constancia en `identity_decisions.csv` de que la unidad es correcta para
esa persona; APLICARLA al pipeline público —traducir el valor en bruto al
vocabulario oficial, que deje de figurar «No determinada»— sigue siendo un
paso aparte, sin construir todavía (exige el mismo criterio institucional
de T-02, y no hay decisiones reales que aplicar hasta que el usuario
revise). `apply_decisions.py --test` sigue en verde: el guardián de
veredictos desconocidos y de cola equivocada reconoce el vocabulario nuevo
sin que haga falta tocar la lógica de aplicación todavía.

Antes de dar esto por terminado, se comprobó si el vocabulario ya validado
en `config/matching_rules.yml` (T-02) reconocía alguna de las 73 cadenas en
bruto («Medicina», «CIDOC», etc.) — **0 de 73**, salvo 3 casos donde la
cadena YA es un nombre de Facultad canónico completo. Confirma lo que ya
se había declarado: el vocabulario de T-02 se construyó desde afiliaciones
Scopus, no desde esta nomenclatura abreviada de biblioteca: son alfabetos
distintos y no hay atajo.

### El error que se encontró y corrigió antes de terminar

Al revisar el primer caso generado (`Allende-Valenzuela T.` → CIPEF), el
texto decía "Hoy esta firma figura con unidad académica «No determinada»
en el sitio público" — **falso para esta firma**: tiene otra publicación
con «Facultad de Educación y Ciencias Sociales» ya determinada. «No
determinada» es un atributo de cada PAR autor×publicación, no de la firma
completa, y el texto lo trataba como si fuera lo segundo. Se comprobó el
alcance real: **27 de las 59 firmas candidatas (46 %) ya tienen unidad
determinada en alguna de sus otras publicaciones** — no son casos "sin
ningún dato", son casos con un hueco puntual. Se corrigió la frase para
distinguir los dos casos: cuando hay una unidad ya determinada, el texto la
muestra y pide comparar; cuando no hay ninguna, mantiene la frase original.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-348 | Los 73 casos de unidad se integran como cola de `build_review.py`, no como herramienta aparte | Instrucción explícita del usuario: todo lo que requiera revisión, en el mismo documento |
| D-349 | El veredicto `unidad_confirmada` registra el hecho en `identity_decisions.csv` pero NO aplica nada al pipeline todavía | Aplicar exige traducir al vocabulario oficial (criterio T-02) y no hay decisiones reales que aplicar aún; declarar la acción como "hecha" cuando no lo está habría sido falso |
| D-350 | El texto de cada caso distingue «sin ninguna unidad determinada» de «con unidad determinada en otra publicación, hueco puntual aquí» | Afirmar en blanco que la firma "no tiene unidad" cuando SÍ la tiene en otra publicación (27 de 59 casos) habría sido una afirmación falsa sobre el propio dato |

### Verificación

`apply_decisions.py --test`: sin cambios de lógica, sigue en verde
(guardianes de vocabulario reconocen las 2 nuevas entradas). Auditoría
completa, `build_all.py` (compuerta: 0 fallas), `06_assemble_site.py`,
`node src/verify/run_all.mjs` completo — sin fallos. Cola nueva verificada
manualmente contra el HTML generado: botones correctos
(`unidad_confirmada`/`unidad_no_corresponde`/`pendiente`), texto de
contexto correcto en un caso de cada tipo (unidad ya determinada en otra
publicación vs. ninguna).

### Archivos modificados

```
src/review/decisiones.py     unidad_confirmada/unidad_no_corresponde en
                              VOCABULARIO y COLAS
src/review/build_review.py   d["autoarchivo_unidad"] cargado; nueva cola
                              generada con el texto corregido
docs/FUENTES_Y_APIS.md       §2.5 actualizada: ya no "queda pendiente"
```

### Ambigüedades abiertas

- Las 73 candidaturas de unidad siguen sin decidir — el usuario las revisa
  en el mismo documento que el resto.
- El mecanismo de APLICACIÓN al pipeline sigue sin construir: cuando el
  usuario tenga decisiones reales que exportar, hace falta un script nuevo
  (análogo a `apply_unit_validation.py` pero para overrides por firma, no
  por variante de vocabulario) — no se construyó a ciegas sin decisiones
  que aplicar.
- Las de siempre: Arroyo A./Shabani R., los 4 "Repositorio institucional
  discrepa" restantes, T-06/T-19.

### Próximo paso recomendado

Esperar a que el usuario revise (puede ser por partes) y exporte
decisiones. Cuando haya `unidad_confirmada` reales que aplicar, construir
el script de aplicación correspondiente — recién ahí, no antes.

## Cierre: fusión del export perdido, saga Arroyo A./Castro M., y tres bugs de reasignación de ORCID en una sola corrida

### Contexto

El usuario exportó `identity_decisions_3.csv` (303 filas) desde
`revision_identidad.html` tras revisar una tanda de casos. Antes de
aplicarlo, la comprobación de rutina («¿bajó el número de grupos
consolidados?») encontró algo que no cuadraba: 37 → 12. Eso no es una
tanda de revisión, es pérdida de datos.

### El bug de exportación del navegador (hallado antes de aplicar nada)

La función `entregar()` de `revision_identidad.html` exporta el array
`CASOS` embebido en la página — que sólo contiene los casos que **siguen
vivos** en la corrida que generó ese HTML. Un caso ya resuelto en un ciclo
anterior (sin caso vivo pendiente) simplemente no está en `CASOS`, así que
un export fresco desde una versión más vieja de la página no lo trae: no
lo marca como "sin cambios", lo omite. Si ese export se usara para
*reemplazar* `identity_decisions.csv` en vez de fusionarlo, esas
decisiones desaparecerían.

Se comprobó el alcance exacto contra el historial (`git show
cb2ab6c~1:internal/identity_decisions.csv`): **72 filas** afectadas — 30
que desaparecían del todo y 42 que volvían a "pendiente" pese a estar
decididas. Se escribió un script de fusión (no se aplicó el export a
ciegas) que: toma el export nuevo como base, y para cada fila del CSV
anterior ausente en el nuevo, la reincorpora tal cual. Resultado: 349
filas de datos, sin pérdida.

Esto es un bug de la herramienta, no del usuario ni de sus datos — pero
significa que **todo export parcial futuro debe fusionarse contra el
historial, nunca reemplazar sin comparar**. Queda anotado para si se
retoma `revision_identidad.html` más adelante (no se corrigió la causa
raíz en el JS esta vez: el mitigante — fusionar contra git antes de
aplicar — es suficiente mientras la revisión se haga en esta modalidad).

### El caso Arroyo A.: contradicción de identidad resuelta con evidencia cruzada, no por conveniencia

`ver-Arroyo A.` (revisión anterior) decía `orcid_correcto` para el ORCID
hoy publicado. Los dos conectores nuevos —DSpace y autoarchivo—
discrepaban: `dspacedesac-Arroyo A.` y `aadesac-Arroyo A.` decían
`orcid_incorrecto` para esa misma firma. Dos fuentes institucionales
independientes contra una revisión humana anterior: no se desempata por
mayoría, se investiga.

Se revisó con el usuario, caso por caso:
- El perfil del ORCID hoy publicado tiene 140 obras y no declara afiliación
  UFT — no hay nada ahí que lo respalde por sí solo.
- Cruce por DOI (`internal/matching_log.csv` +
  `data/interim/publications_universe.csv`): 3 de las 4 publicaciones de
  Arroyo A. en el corpus coinciden EXACTAMENTE por DOI con lo que DSpace y
  autoarchivo citan bajo un ORCID distinto — no es coincidencia de nombre,
  es la misma obra.
- El usuario encontró de forma independiente, directamente en el sitio de
  ORCID (fuera del alcance de este entorno: `orcid.org` está bloqueado por
  egress aquí), el Scopus Author ID `55159442300` en ese perfil alternativo
  — y ese Scopus ID coincide con el que trae `authors_master_draft.csv`
  para esta firma.

Con evidencia convergente por dos vías independientes (DOI exacto +
Scopus ID confirmado por el usuario en la fuente), decisión del usuario:
«Sí, corrígelo y asígnalo». Aplicado: `ver-Arroyo A.` pasa a
`orcid_incorrecto` (con nota del porqué) y se agrega
`arroyoasignado-Arroyo A.` con `orcid_encontrado` →
`0000-0002-6248-9257`.

### El caso Castro M.: la fusión histórica se mantiene

Una fusión histórica («Castro M.» = «Castro-Sepúlveda M.») parecía
contradecir una lectura nueva de que «Castro M.» agrupa a dos personas
distintas (Magdalena y Mauricio). Se mostró el conflicto al usuario, quien
confirmó: «la fusión histórica era Mauricio, sigue siendo correcta» — sin
cambios al CSV, la duda quedó resuelta por confirmación directa del
titular de la decisión original.

### Tres bugs de pipeline, una sola causa raíz

Aplicar la decisión de Arroyo A. — retirar un ORCID Y asignar el correcto
para la misma firma, en la misma corrida de `apply_decisions.py` — expuso
tres fallas encadenadas, todas por la misma razón: código que calcula «el
estado vigente» una vez al principio de la corrida, sin contar con que esa
misma corrida va a modificar ese estado.

1. `veredictos_orcid()`: `vigente` se leía de `authors_orcid.csv` en disco
   ANTES de procesar las decisiones, así que `orcid_encontrado` veía la
   firma «ya asignada» con el valor que la misma corrida estaba retirando,
   y se negaba a asignar el reemplazo. Corregido con
   `vigente_para_nuevo` (excluye las firmas retiradas en esta corrida).
2. El filtro/concat final de `nuevas` contra `vig` en `main()`: descartaba
   la asignación nueva por estar la firma ya en `vig` (el CSV crudo, que
   todavía trae la fila vieja). Corregido con `vig_efectiva`/`reemplazadas`.
3. `src/build/03_authors.py`: el filtro `ORCID_RETIRADO` excluía TODAS las
   filas de una firma por nombre, no sólo la fila con el ORCID retirado
   específico — así que la fila nueva y correcta también se descartaba.
   Corregido comparando el valor retirado, no sólo el nombre.

Cada uno se encontró verificando la salida real
(`data/enriched/authors_orcid.csv` → `data/processed/authors.json`) tras
cada paso, no asumiendo que el fix anterior bastaba. El principio "no se
borra, se anota" (los ORCID retirados quedan en el CSV, filtrados en el
build) es precisamente lo que hace este escenario sutil: las filas vieja y
nueva conviven, y hay que reemplazar la vieja sin duplicar ni perder la
nueva.

Se agregaron dos casos nuevos a `apply_decisions.py --test`: «retirar y
reemplazar la misma firma en una sola corrida» y «confirmar no abre hueco
para un reemplazo» — ambos en verde.

**Verificación de la etiqueta final** (no se dio por buena sin trazarla):
en `03_authors.py`, la cadena que elige la etiqueta pública comprueba
`fuente_orcid == FUENTE_BUSQUEDA` ANTES que cualquier rama de
`comprobado_a_mano`/`veredicto`. `apply_decisions.py` marca
`orcid_encontrado` con `"fuente": FUENTE_BUSQUEDA` (misma constante
textual). Se confirmó que la ficha de Arroyo A. muestra
`"orcid_veredicto_etiqueta": "encontrado por revisión"` precisamente por
esa rama — no es una etiqueta vieja que sobrevivió por casualidad.

### Estado final tras aplicar la tanda completa

`internal/identity_decisions.csv`: 349 filas de datos (303 del export +
72 restauradas − reconciliación de duplicados + la fila de Arroyo A.).
Pipeline reconstruido de punta a punta:
`dspace_inventario.py` → `autoarchivo_uft.py` → `build_review.py` →
`build_all.py` → `06_assemble_site.py` → `node src/verify/run_all.mjs`.

- `build_review.py`: 301 casos totales · 163 ya decididos · **138
  pendientes** (33 decisiones del CSV ya no tienen caso vivo — son casos
  resueltos, no un problema).
- `build_all.py`: compuerta pública/interna 0 fallas · auditoría 29/30
  reglas pasan (la única falla, E-06 sobre una columna de Scopus vacía,
  es preexistente y no bloqueante, ajena a este trabajo).
- `node src/verify/run_all.mjs`: contraste, estructura, flujos,
  responsive, higiene, peso — los 6, sin fallos.
- `apply_decisions.py --test`: 38/38 casos OK.

Se reportó al usuario, pero **no se aplicó**, un análisis exploratorio de
cuántos casos pendientes se resolverían si se confiara en el acuerdo entre
las dos fuentes institucionales (DSpace + autoarchivo) para el ORCID de
una firma — queda a la espera de autorización explícita, igual que el
resto de los pendientes de esta cola.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-351 | Un export parcial de `revision_identidad.html` se fusiona contra el historial de git antes de aplicarse, nunca reemplaza el CSV directamente | La función `entregar()` sólo exporta casos vivos; un reemplazo directo pierde silenciosamente las decisiones ya resueltas (72 filas en este caso) |
| D-352 | La contradicción de Arroyo A. se resuelve a favor del ORCID `0000-0002-6248-9257`, retirando el previamente publicado | Evidencia convergente por dos vías independientes: coincidencia exacta de DOI en 3/4 publicaciones contra DSpace/autoarchivo, y Scopus Author ID confirmado por el usuario directamente en el registro ORCID |
| D-353 | La fusión histórica «Castro M. = Castro-Sepúlveda M. (Mauricio)» se mantiene sin cambios | Confirmación directa del usuario, autor de la decisión original, ante el conflicto mostrado |
| D-354 | `veredictos_orcid()`, el filtro final de `nuevas`/`vig`, y el filtro `ORCID_RETIRADO` de `03_authors.py` deben calcular «vigente» contando con los retiros de la MISMA corrida, no sólo el estado en disco al inicio | Sin esto, retirar-y-reemplazar el ORCID de una firma en un solo ciclo de revisión (D-08 lo exige explícitamente) falla silenciosamente: la firma queda sin ORCID nuevo asignado |
| D-355 | El análisis de acuerdo cross-fuente (DSpace × autoarchivo) para ORCID se reporta pero no se aplica sin autorización explícita | Sigue D-08/D-347: ningún hallazgo propio se convierte en aplicación sin que el usuario lo autorice para ese insumo específico |

### Verificación

`apply_decisions.py --test` (38/38), `build_all.py` (compuerta 0 fallas),
`node src/verify/run_all.mjs` (6/6 sin fallos), y verificación manual de
la cadena de etiquetado de veredicto ORCID en `03_authors.py` trazada
línea por línea contra la salida real en `authors.json` — no se dio por
buena la etiqueta sin confirmar la rama exacta que la produce.

### Archivos modificados

```
internal/identity_decisions.csv   fusión de 72 filas históricas + fila de
                                   Arroyo A. + corrección de ver-Arroyo A.
src/review/apply_decisions.py     vigente_para_nuevo / vig_efectiva
                                   (retirar-y-reemplazar en una corrida) +
                                   2 casos de prueba nuevos
src/build/03_authors.py           ORCID_RETIRADO compara valor, no sólo
                                   nombre de firma
config/identidades_consolidadas.yml,
config/orcid_revisado.yml,
data/enriched/authors_orcid.csv   regenerados por la corrida completa
```

### Ambigüedades abiertas

- 138 pendientes en la cola de revisión, sin cambios de alcance frente al
  cierre anterior.
- El acuerdo cross-fuente DSpace × autoarchivo para ORCID fue analizado y
  reportado, no aplicado — pendiente de autorización explícita.
- El bug de exportación parcial en `revision_identidad.html` (`entregar()`
  sólo exporta `CASOS` vivo) no se corrigió en el JS; se mitigó por fusión
  manual contra git. Si la herramienta se retoma, vale la pena corregirlo
  en la fuente.
- Las de siempre: Shabani R., T-06/T-19, el mecanismo de aplicación para
  `unidad_confirmada` (D-349, sigue sin construir).

### Próximo paso recomendado

Reportar al usuario el cierre completo de esta tanda (349 filas, 138
pendientes, las dos resoluciones de identidad, los tres bugs corregidos)
y reenviar `internal/revision_identidad.html` regenerado. Quedar a la
espera de la siguiente tanda de revisión o de autorización sobre el
análisis cross-fuente reportado.

## Cierre: se aplica el acuerdo cross-fuente DSpace × autoarchivo, con dos criterios distintos y un hallazgo honesto sobre su efecto real

### Contexto

El usuario autorizó («Autorizo») el análisis pendiente del cierre
anterior: aplicar las firmas donde el repositorio institucional (DSpace)
y el inventario de autoarchivo de biblioteca coinciden de forma
independiente sobre el ORCID de una firma. Antes de aplicar nada, se
recalculó el análisis desde cero (no se reutilizó ninguna cifra de antes
del corte de contexto) y se distinguieron dos preguntas distintas que la
frase original mezclaba:

**Criterio A — confirmar una asignación YA vigente.** 98 firmas tienen
ORCID asignado y ambas fuentes lo corroboran (`confirma_directa` o
`confirma_indirecta`, ninguna `contradice_directa`); 18 ya tenían
decisión registrada, quedaron **80** sin decidir.

**Criterio B — asignar ORCID a una firma que hoy NO tiene ninguno.** De
los candidatos por nombre sin publicación en común (`dspace_candidatos.csv`
/ `autoarchivo_candidatos.csv`), **5 cadenas de firma** (`Díaz-Galaz L.`,
`Letelier Widow G.`, `Salas-Guzmán N.`, `Morales Sepúlveda J.P.` y su
variante `Morales-Sepulveda J.P.`) tienen un único candidato en cada
fuente y ambas proponen el MISMO ORCID.

### El bug que casi corrompe el CSV, encontrado antes de escribir nada

El primer intento de leer `identity_decisions.csv` usó
`pd.read_csv(..., comment='#')` para saltar la cabecera de comentarios.
Es exactamente el bug que `src/review/decisiones.py::leer()` ya documenta
en su docstring: `comment='#'` trunca la línea en la primera almohadilla
ESTÉ DONDE ESTÉ, y varias notas de este mismo proyecto contienen una
(«evidencia cruzada... Scopus ID: 55159442300 ¿Calza?» no tiene, pero
otras sí). El síntoma se notó de inmediato: tras escribir el archivo con
ese lector, el conteo de filas no cuadraba (esperadas 429, escritas 414).
Se revirtió con `git checkout` antes de aplicar nada más, y se rehízo
todo el cálculo con `decisiones.leer()` — el lector correcto del propio
proyecto — confirmando que las cifras (80 y las 10 filas de Criterio B)
no habían cambiado, pero por verificación, no por suposición.

### Aplicado

- **Criterio A** (80 firmas): una fila nueva por firma, cola «ORCID sin
  confirmar», veredicto `orcid_correcto`, con nota que cita el veredicto
  y el número de publicaciones cruzadas de cada fuente.
- **Criterio B** (5 cadenas, 10 filas): se actualizaron in-situ las filas
  YA EXISTENTES y pendientes de `identity_decisions.csv` (los casos
  `dspacecand-`/`aacand-` que `build_review.py` ya había generado para
  estas firmas) de `pendiente` a `misma`, en vez de crear filas nuevas —
  son exactamente los casos que la cola de revisión ya tenía abiertos
  para esta pregunta.
- `apply_decisions.py --dry-run` antes de aplicar: 0 errores, 0
  contradicciones. Aplicado en real: 138 ORCID confirmados, 26
  asignaciones nuevas (candidatos de Criterio B + los ya represados de
  «Candidato por afiliación» de tandas anteriores), cobertura 322 → 329.

### El hallazgo honesto: el Criterio A no cambia nada visible en el sitio — y eso es correcto, no un defecto

Antes de reportar el resultado, se comprobó el efecto real en
`data/processed/authors.json` en vez de asumir que «confirmar» sube la
confianza. No la sube: de las 67 firmas del Criterio A localizables por
nombre exacto (13 quedaron fusionadas a otra forma canónica), **las 67
muestran la misma etiqueta que tenían antes** («verificado» o «declarado
por el titular»), **ninguna** pasó a «comprobado por revisión». La razón
está declarada en el propio código (`03_authors.py`, cadena de selección
de veredicto): cuando el titular ya declara en su propio registro de
ORCID una publicación que coincide con el corpus, esa es evidencia más
fuerte que el juicio de una persona sobre una fuente externa, y el código
decide EXPLÍCITAMENTE no dejar que la comprobación humana la reemplace
("sustituirlo por el juicio de una persona sería cambiar evidencia más
fuerte por más débil y presentarlo como una mejora"). Las 80 firmas del
Criterio A ya tenían esa evidencia más fuerte (veredicto `confirmada` por
coincidencia de DOI contra el propio registro ORCID del titular); el
cruce con DSpace/autoarchivo llega después y no pisa nada.

Esto significa que el Criterio A **no resuelve ningún caso pendiente**
(se comprobó: 0 de las 80 firmas coincide con las 9 pendientes actuales
de «ORCID sin confirmar», ni con ninguna otra cola pendiente) **ni cambia
la etiqueta pública**. Su valor es distinto y real: deja constancia
permanente en `config/orcid_revisado.yml` de que una persona, con dos
fuentes institucionales independientes, revisó y no encontró contradicción
en estas 80 asignaciones — trazabilidad para una auditoría futura, no una
mejora visible hoy.

El Criterio B sí tiene efecto visible y sí resuelve pendientes: las 5
firmas pasan de no tener ORCID a tenerlo (`confirmado por revisión`,
confianza alta, `FUENTE_REVISION`), y despejan **10 filas** de la cola
(2 colas × 5 firmas: `Candidato por repositorio institucional` bajó de
14→11, `Candidato por inventario de autoarchivo` de 7→4, y las dos colas
«(ambiguo)» de Morales Sepúlveda J.P. quedaron resueltas).

### Estado final

`build_review.py`: 290 casos totales · 162 ya decididos · **128
pendientes** (bajó de 138; -10 por el Criterio B, el Criterio A no toca
pendientes como se explicó arriba). `build_all.py` compuerta 0 fallas.
`node src/verify/run_all.mjs`: 6/6 sin fallos.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-356 | `identity_decisions.csv` se lee SIEMPRE con `decisiones.leer()`, nunca con `pd.read_csv(comment='#')` a mano | El propio proyecto ya documentó y corrigió este bug (docstring de `leer()`); reintroducirlo en un script ad-hoc truncó silenciosamente 15 filas antes de escribir nada — se detectó por el conteo, no por revisión de contenido |
| D-357 | Las 80 confirmaciones del Criterio A (acuerdo cross-fuente sobre una asignación YA vigente) se aplican como registro de auditoría, no como mejora de confianza o resolución de pendientes | Verificado contra la salida real: la cadena de veredicto en `03_authors.py` da prioridad, por diseño, a la evidencia de que el propio titular declara la publicación en su registro ORCID; una confirmación cruzada externa no la reemplaza. Afirmar que esto «resuelve casos» o «sube confianza» habría sido una afirmación falsa sobre el propio dato |
| D-358 | Las 10 filas de Criterio B (5 firmas × 2 fuentes) se aplican actualizando in-situ los casos `pendiente` ya existentes en `identity_decisions.csv`, no creando filas nuevas | Son exactamente las preguntas que la cola de revisión ya tenía abiertas para esas firmas; crear filas paralelas habría duplicado el caso sin necesidad |

### Verificación

`apply_decisions.py --dry-run` (0 errores) antes de aplicar en real;
`build_all.py` (compuerta 0 fallas, misma falla preexistente no
bloqueante de siempre); `node src/verify/run_all.mjs` (6/6); y
verificación manual contra `authors.json` de que el efecto reportado al
usuario (0 cambios visibles en Criterio A, 5 asignaciones nuevas visibles
en Criterio B) es el que realmente ocurre, no el que se esperaba antes de
comprobar.

### Archivos modificados

```
internal/identity_decisions.csv    +80 filas (Criterio A) · 10 filas
                                    pendiente→misma (Criterio B)
config/orcid_revisado.yml,
config/identidades_consolidadas.yml,
data/enriched/authors_orcid.csv    regenerados por apply_decisions.py
internal/dspace_candidatos.csv,
internal/autoarchivo_candidatos.csv regenerados (candidatos resueltos
                                    ya no aparecen)
```

### Ambigüedades abiertas

- 128 pendientes en la cola (bajó de 138).
- Las de siempre: Shabani R., T-06/T-19, el mecanismo de aplicación para
  `unidad_confirmada` (D-349, sigue sin construir).

### Próximo paso recomendado

Reportar al usuario el resultado con el encuadre correcto: el Criterio A
fortalece trazabilidad sin cambiar lo visible; el Criterio B resolvió 10
filas de cola reales. Reenviar `internal/revision_identidad.html`
regenerado. Esperar la siguiente tanda de revisión del usuario.

## Cierre: la cola de Facultad/Escuela mezclaba tres categorías distintas — se añade contexto, no vocabulario

### Contexto

El usuario abrió la cola «Candidato de unidad académica por autoarchivo»
(73 casos) y no logró entender el criterio: «Parece que no está claro el
funcionamiento de Escuelas/Facultades». Pidió recuperar información real
de facultades y carreras de la Universidad Finis Terrae para aclararlo.

### El hallazgo: no es un vocabulario incompleto, son tres preguntas distintas disfrazadas de una

Los 26 valores en bruto del inventario de autoarchivo no son todos
«escuelas»:
1. Facultades y Escuelas reales (la mayoría).
2. **Centros de investigación** (`CIDOC`, `CIPEF`) — viven dentro de una
   facultad pero no son unidades de docencia.
3. **Unidades transversales** (`Formación General`) — la Dirección de
   Filosofía y Formación General depende directamente de la
   Vicerrectoría Académica, PARALELA a las 8 facultades, no subordinada
   a ninguna.

Preguntarle al revisor «¿es correcto asignar esta escuela?» sobre un
centro de investigación o una unidad transversal es la pregunta
equivocada — de ahí la confusión reportada.

### finis.cl está bloqueado en este entorno — confirmado en dos capas, no una vez

`WebFetch` a `finis.cl` devolvió `EGRESS_BLOCKED`. Antes de reportarlo
como límite del entorno, se probó también `curl` directo contra el mismo
dominio a través del proxy configurado: `CONNECT tunnel failed, response
403` — confirma que es una denegación de política de red de la
organización para este sandbox, en dos vías independientes, no un fallo
puntual de una herramienta. Toda la información de facultades/escuelas
viene de `WebSearch` (fragmentos, no la página completa) y se etiquetó
así explícitamente en el código y en lo reportado al usuario.

### La corrección del usuario que evitó un error real

Basado en `WebSearch`, se propuso que el nombre canónico vigente era
«Facultad de Educación, Psicología y Familia» (no «Facultad de Educación
y Ciencias Sociales», que usa hoy `config/matching_rules.yml`). Se pidió
al usuario confirmarlo DIRECTAMENTE en finis.cl antes de tocar nada — y
confirmó lo contrario: el nombre vigente es «Facultad de Educación y
Ciencias Sociales», el que el proyecto ya usaba. La búsqueda web llevaba
a una página desactualizada o a un nombre alternativo, no al oficial
vigente. **No se tocó el nombre canónico.** Esto confirma por qué D-345
y el propio código insisten en no traducir automáticamente estos valores
al vocabulario oficial sin verificación humana directa: una fuente
externa indirecta, aunque razonable, puede estar equivocada.

### Lo que se aplicó

No se tocó `config/matching_rules.yml` (el nombre canónico de facultad
queda como estaba, confirmado correcto). Se agregó
`REFERENCIA_UNIDADES_AUTOARCHIVO` en `src/review/build_review.py`: un
diccionario de CONTEXTO (no de traducción) que añade una frase aclaratoria
al caso cuando el valor en bruto es uno de los 11 identificados como no
autoexplicativos (`CIDOC`, `CIPEF`, `Formación General`, `Escuela de
Filosofía`, `Periodismo`, `Literatura`, `Publicidad`, `Ingeniería
comercial`, `Ingenieria civil informática`, `Educación básica`,
`Educación parvularia`). Cada entrada declara su fuente y si está
verificada o no contra finis.cl directamente. El valor en bruto sigue
viajando sin traducir (D-345 no cambia): esto sólo ayuda a quien revisa a
entender qué es cada cosa antes de decidir, no decide por él.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-359 | El nombre canónico «Facultad de Educación y Ciencias Sociales» se mantiene sin cambios | Confirmado directamente por el usuario en finis.cl, contradiciendo la propuesta basada en `WebSearch` — la fuente indirecta estaba equivocada |
| D-360 | Se agrega contexto aclaratorio a la cola de unidad académica (centros de investigación vs. escuelas vs. unidades transversales), sin traducir el valor en bruto al vocabulario oficial | El problema reportado era de comprensión del caso, no de vocabulario faltante; D-345 ya reserva la traducción oficial para cuando exista decisión institucional validada |

### Verificación

`build_review.py` (mismos 128 pendientes, sin cambio de conteo — es sólo
texto de contexto), `build_all.py` (compuerta 0 fallas), `node
src/verify/run_all.mjs` (6/6). Se comprobó manualmente que la nota
aparece correctamente en `internal/pendientes_consolidacion.md` para
casos de CIDOC, CIPEF y Formación General.

### Ambigüedades abiertas

- Las notas de `REFERENCIA_UNIDADES_AUTOARCHIVO` para 8 de los 11 valores
  siguen sin verificación directa contra finis.cl (sólo `WebSearch`) — el
  propio texto lo declara. Si el usuario las revisa y encuentra un error
  como el de la Facultad de Educación, corregir el diccionario es
  inmediato.
- Sigue sin existir el mecanismo de aplicación para `unidad_confirmada`
  (D-349).

### Próximo paso recomendado

El usuario revisa la cola con el contexto nuevo. Si encuentra que alguna
nota está mal, se corrige puntualmente — no requiere reabrir todo el
diseño.

---

## Nota de fusión (2026-09-02)

Lo que sigue de aquí en adelante, hasta la próxima nota de fusión, es el
registro de una **sesión paralela** que trabajó directamente sobre `main`
mientras esta rama (`claude/state-review-next-steps-wzzq0h`) avanzaba por
separado. Se fusionó por decisión explícita del usuario tras comparar
ambas ramas: sólo hubo una contradicción real de identidad (Arroyo A.,
resuelta a favor de la evidencia cruzada de esta rama) y cero conflictos
de consolidación de identidad — el resto es trabajo complementario, sin
solaparse. Detalle completo en la entrada de cierre correspondiente más
abajo, después de todo este bloque.

## Cierre · Revisión humana de identidad exportada hoy, encontrada y aplicada

El usuario pidió revisar si había datos actualizados que afectaran el
trabajo ya hecho antes de seguir. `git fetch` confirmó que `main` no había
divergido (0 commits de diferencia en ambos sentidos) — nada nuevo por
ese lado. Pero en `Descargas` apareció `identity_decisions (2).csv`,
exportado **hoy** desde `internal/revision_identidad.html`: 188 filas
contra las 141 ya comiteadas, con 43 casos existentes cambiados de
veredicto además de 82 casos nuevos (52 seguían pendientes, 30 ya
decididos). Trabajo de revisión humana real, sin aplicar.

Aplicado siguiendo el flujo ya establecido, sin atajos: `merge_decisions.py`
(fusiona, no sobrescribe — 141 vigentes + 188 nuevas → 223, con 35 casos
huérfanos preservados que ya no están en la cola viva pero siguen
decididos), luego `apply_decisions.py --dry-run` para revisar antes de
escribir nada, y sólo después `apply_decisions.py` de verdad.

### Resultado de la aplicación

34 grupos de identidad consolidados (77 formas de firma, incluida
`Henriquez-Olguin C.` / `Henríquez-Olguín C.` — el mismo autor que ya
había aparecido en el top de citación de la revisión de cobertura
OpenAlex de esta sesión, ahora del lado del corpus interno). 4 firmas
descartadas por fragmento. 37 asignaciones de ORCID confirmadas, **14
retiradas** —asignaciones que la revisión humana encontró incorrectas, no
sólo confirmaciones—. Cobertura de ORCID: 322 → 308 asignaciones que el
build usará; baja porque se corrigen errores, no porque se pierda
cobertura real.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-393 | Se buscó activamente en `Descargas` una exportación de revisión sin aplicar en vez de asumir que "revisar datos actualizados" sólo significaba `git fetch` | El pedido explícito de la sesión anterior fue *"revisa cualquier dato actualizado que pueda afectar el trabajo realizado"* — el trabajo de identidad consolidada afecta directamente `authors.json`/`hierarchy.json`, que son insumo del treemap recién hecho reactivo esta misma sesión |
| D-394 | Los 14 retiros de ORCID se aplicaron sin pedir confirmación caso por caso | Ya venían de una decisión humana explícita en la exportación (`orcid_incorrecto`), no de una heurística nueva — `apply_decisions.py` sólo traduce un veredicto ya dado a los artefactos que el build consume |

### Verificación

Auditoría completa (0 bloqueantes). `build_all.py` (compuerta: 0 fallas,
542 fichas de autor, subió de 538 por la reconsolidación). `06_assemble_site.py`
(10 páginas). `node src/verify/run_all.mjs` completo — 6 bloques, 0 fallos —
corrido DESPUÉS de aplicar y reconstruir.

### Archivos creados o modificados

```
internal/identity_decisions.csv        141 -> 223 filas (fusión, no reemplazo)
config/identidades_consolidadas.yml    34 grupos nuevos/actualizados (77 formas de firma)
config/firmas_e09_resueltas.yml        4 descartadas
config/orcid_revisado.yml              37 confirmadas, 14 retiradas, 6 sin registro
docs/BUILD_VERIFICATION.md             regenerado (542 fichas de autor)
```

### Ambigüedades abiertas

Las de siempre, sin cambios: `T-06`, `T-19` en su techo. Quedan 100
decisiones pendientes en `internal/identity_decisions.csv` (de 223) para
una próxima ronda de revisión.

### Próximo paso recomendado

Ninguna acción de código pendiente. Si aparece otra exportación de
`revisar-identidad.ps1`/`revision_identidad.html` en Descargas, el mismo
flujo (`merge_decisions.py` → `apply_decisions.py --dry-run` →
`apply_decisions.py` → reconstruir → verificar) se repite igual.

---

## Cierre · Auditoría de 7 frentes y corrección de consistencia documental (2026-09-01)

El usuario pidió auditar el repositorio a fondo ("completa, ahora") con una
metodología de 7 frentes y evidencia, e incorporar habilidades de experto según
lo requiriera el desafío. Se reconstruyó el pipeline desde cero y se verificó
contra la **verdad ejecutable**, no contra lo que la memoria de sesión
recordaba. Frentes B (pipeline), C (capas), D (replicabilidad), E (metodología)
y F (repo/CI) quedaron en verde. Los hallazgos reales fueron de **consistencia
documental** — cifras que quedaron atrás de la última consolidación.

### Hallazgos de cifras obsoletas y su corrección

La consolidación de identidad del 2026-09-01 llevó la base publicada de 556 a
**542 entidades** y la cobertura de ORCID de 216/556 a **277/542 (51,1 %)**.
Varios documentos y una advertencia servida seguían citando la base vieja:

1. **`config/sources.yml`**: `ror_api`/`scopus_api`/`openalex_api` decían
   `ejecutada: false` cuando los artefactos enriquecidos existen
   (`ror_institucion.json`, `scopus_api_consulta.json`, `authors_orcid.csv`).
   El flag era un metadato que dejó de sincronizarse con la evidencia.
   Corregido a `true` con `fecha_ejecucion` real (ror 2026-08-25; scopus y
   openalex 2026-08-26), alineado con las fechas de los artefactos y de
   T-06/V2-19/V2-26.
2. **`docs/ORCID_COVERAGE.md`**: §2-bis y §3 reescritos sobre la base 277/542,
   con las etiquetas reales de las fichas (`verificado` 155, `declarado por el
   titular` 41, `confirmado por revisión` 17, `comprobado a mano` 22, `no
   verificable` 20, `sin confirmar` 22) y la distribución por rango de
   publicaciones (1 pub 38,9 % → 10+ 100 %). El aviso de base y el §4 dejaron
   de citar 556/216; contextos cronológicos que nombran 556 quedan como
   historia. **69,2 %** (no 69,6) de las entidades tienen una sola publicación.
3. **`STATE.md`**: regenerado con `snapshot.py` (no a mano). Sigue declarando
   «113 casos / 6 pendientes», que es la cuenta de la última corrida de `make
   revision` (puertas como `openalex_*` no se cuentan ahí); la tabla de colas
   sí refleja las 10 colas reales. No se reconcilió la diferencia entre esa
   lista de 113 y el ~450 total de PENDIENTE_REVISION_HUMANA en `internal/`
   porque es la definición de ese campo —ver mejora abajo.
4. **`docs/INDICATORS.md`** (P-06) y **`docs/V2_BACKLOG.md`** (V2-01 y el
   párrafo de la vía Crossref) y **`docs/AUTHOR_PROFILE.md`**: actualizados a
   base 542/277 (322 asignaciones sobre firmas sin consolidar). P-06 conserva
   una nota al pie que distingue la decisión histórica de la base vigente.
5. **`config/indicators.yml` `AU-03.advertencia`** — el único hallazgo que era
   una **figura servida**: decía «466 de las 556 entidades tienen h≤1» (84 %),
   cifra que no se puede re-derivar: hoy el h-index sólo se computa para las
   **50 entidades interpretables** (n≥5) y de ellas sólo **4 tienen h≤1**. La
   advertencia citaba una visión del indicador (h computado para todas) que
   contradice al built real (`03_authors.py`: sólo muestra h cuando la muestra
   es legible). Reescribí la advertencia para describir lo que el sitio
   realmente hace, anclado en los 50/542 reales, en vez de inventar un 466
   equivalente.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-395 | Los flags `ejecutada: false` de las 3 APIs en `sources.yml` se cambian a `true` con fecha de ejecución, en vez de borrar el campo | El campo ya existía para las 3; dejarlo en `false` engañaría a una próxima sesión a reconsultar APIs o creer inexistentes los artefactos enriquecidos. `crossref_api`/`orcid_api` se dejan sin flag (así están hoy) |
| D-396 | La advertencia de AU-03 no se «porta» a 542 multiplicando 466, se reescribe para describir el gate real (`n≥5`, 50 de 542) | `CLAUDE.md` prohíbe inventar cifras. El 466/556 (84 %) implica computar h para todas las entidades, lo que contradice `03_authors.py` («sólo cuando la muestra lo hace mínimamente legible»). La frase honesta y derivable es la del gate |
| D-397 | `config/indicators.yml` (AU-03) es la fuente de lo publicado; el número de `indicator_feasibility.py` (497 de 589) es la nota interna de la factibilidad y se deja | La factibilidad describe la decisión del analista de no publicar por falta de discriminación sobre firmas sin consolidar; cambiarlo exigiría re-correr el análisis con criterio nuevo, no una doc-fix |

### Mejora detectada, no aplicada

`STATE.md` «113 casos / 6 pendientes» (transición de `make revision`) y el
~450 pendientes de `internal/*` son dos cuentas que un futuro lector puede
confundir. `snapshot.py` podría aclarar que la línea de 113 se refiere a las
cuatro colas de identidad que `make revision` consolida, distinguiéndolas del
total de PENDIENTE_REVISION_HUMANA de `openalex_cobertura`/`orcid_hallazgos`.
Queda como mejora de la vista derivada, no un error de datos.

### Verificación

Reconstruido de punta a punta DESPUÉS de los cambios: `src/audit/run_all.py`
(0 bloqueantes), `build_all.py` (compuerta 0 fallas, 542 fichas),
`06_assemble_site.py` (10 páginas), y la advertencia servida confirmada en
`dist/data/catalogo.json` (`AU-03` con el texto nuevo y `n≥5, 50 de las 542`).
`grep "466 de las 556" dist/` y `data/processed/` → vacío. YAML de
`sources.yml`/`indicators.yml` válido.

### Notas de entorno (no de repo)

- **pandas**: esta máquina tiene **3.0.5** instalado, fuera del pin
  `pandas>=2.0,<3.0` de `requirements.txt`. El build corrió bien en 3.0.5,
  pero `make instalar` con `requirements.txt` instalará una versión menor. No
  rompe, es una diferencia de ambiente entre máquinas.
- **Playwright/Chromium**: `node src/verify/run_all.mjs` exige el navegador ya
  descargado (`npx playwright install chromium`); el Makefile `verificar` lo
  asume instalado y CI lo descarga. Una falla de browser NO es una falla de
  verificación del sitio. El `package.json` queda como dev-dependency, sitio
  sin dependencias runtime.

### Archivos creados o modificados

```
config/sources.yml               flags ejecutada + fecha_ejecucion (ror/scopus/openalex)
config/indicators.yml            AU-03.advertencia reescrita (gate real, no 466/556)
docs/ORCID_COVERAGE.md           277/542 + etiquetas reales + distribución por rango
docs/INDICATORS.md               P-06 nota de consolidación 2026-09-01
docs/V2_BACKLOG.md               V2-01 y vía Crossref a 277/542
docs/AUTHOR_PROFILE.md           ORCID 277/542 (51,1 %)
STATE.md                         regenerado con snapshot.py (no a mano)
docs/VALIDATION_REPORT.md        regenerado por auditoría
SESSION_NOTES.md                 este cierre
```

### Ambigüedades abiertas

Ninguna nueva. Las de siempre: `T-06` en su techo, `T-19` corriendo por cron
mensual, y las colas humanas de `internal/` sin revisar (414 cobertura, 56
`orcid_hallazgos`). El STATE sigue declarando 113/6 por definición de `make
revision` — mejora propuesta arriba, no aplicada.

### Próximo paso recomendado

Ninguna acción de código pendiente. Si se quiere, aplicar la mejora de
`snapshot.py` para distinguir las dos cuentas de pendientes (identidad vs.
cobertura), y decidir si `.gitignore`/`requirements.txt` deben tolerar pandas
3.x alguna vez.

---

## Cierre · V2-27: recuperación y almacenamiento de las publicaciones del sitio de la Facultad de Medicina

El usuario compartió `https://facultadmedicina.finis.cl/investigacion-y-postgrado/publicaciones/`
y pidió «recuperar la información» y almacenarla, tras pedir primero el método.

### El método investigado

El sitio es **WordPress**. La API REST (`/wp-json`) está abierta, pero **no hay
un custom post type de publicaciones** (el endpoint `/publicacion` da 404; los
`types` listan sólo los estándar de WordPress). Todo el contenido vive como
HTML incrustado en el `content` de **la página** `publicaciones`
(id 10009) — la respuesta de
`/wp-json/wp/v2/pages?slug=publicaciones&_fields=content` pesó ~950 KB e incluye
los 609 registros completos. Conclusión de la investigación de la vía: **la API
REST de la página es la fuente correcta**, en una sola respuesta, sin paginar.

### Qué se construyó

`src/enrich/facultad_medicina_publicaciones.py`: baja la página vía `wp-json`,
parsea cada `<div class="sima-pub-item">` (badge índice, badge año, `<h4>`
título, `<dl>` con Primer autor / Autor/a correspondencia / Autor/a UFT, enlace
"Ver DOI"), deduce la sección del `<h2>` previo, normaliza el DOI a minúsculas
y lo cruza contra `data/interim/publications_universe.csv`. Modos: `--test`
(parsa una muestra local guardada, sin red), `--sin-red` (usa la muestra) y el
modo por defecto (consulta la red).

### Resultado de la corrida real

- **609 registros** → 347 con DOI → **279 en el universo Scopus**.
- Por sección: Medicina 554 (por año), Nutrición y Dietética 34, Libros 11,
  Enfermería 10.
- Medicina por año: 2025=136, 2024=114, 2023=75, 2021=66, 2020=29, 2019=32,
  2018=26, 2017=23, 2016=20, 2015=15, 2022=9, 2014=6, 2013=3 — coincide
  exactamente con los encabezados de la página.
- Libros y buena parte de Enfermería/Nutrición **no traen DOI** (listados
  textuales/obras editoriales), por eso el cruce sólo aplica casi en su
  totalidad al bloque de Medicina (278 de 343 con DOI en universo).
- **60 DOIs están repetidos** dentro de la página (el sitio lista varias
  publicaciones dos veces, p. ej. Pharmacogenomics como #026 y #027) — observación
  de calidad de la fuente, no un bug del parser; los registros se guardan crudos
  y quien consuma decide deduplicar.

### Almacenamiento (por capa)

```
data/enriched/facultad_medicina_publicaciones.json   registros estructurados (capa de datos externos)
internal/facultad_medicina_cruce.csv                 cruce contra el universo markado (capa interna)
src/enrich/facultad_medicina_publicaciones.py        extractor
```

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-398 | El resultado se guarda como **referencia de contraste**, no como entrada de un corpus | `D-314`: confirmar que una obra es producción real UFT no la convierte en parte del universo — ampliarlo es una decisión de alcance aparte. Este cruce sólo clasifica en-universo / fuera, igual que la revisión de cobertura OpenAlex |
| D-399 | `data/enriched/` (JSON) + `internal/` (CSV de cruce) en vez de `data/processed/` | No es un artefacto del pipeline (`STEPS` no lo consume): es fuente externa ingerida para contraste. El JSON estructurado va con los otros enriquecimientos externos (`authors_orcid.csv`, `scopus_api_consulta.json`); el CSV de cruce, a la capa interna |
| D-400 | No se deduplica en el extractor; se guardan los 609 registros crudos | El sitio lista duplicados; borrarlos en el extractor ocultaría un dato de la fuente y forzaría una decisión (cuál queda) que no le toca a la ingesta decidir |

### Verificación

`--test` con la muestra local: 609 registros, campos correctos en un registro
conocido por DOI, secciones Enfermería/Libros/Nutrición detectadas (sin red).
Corrida real de red: misma cuenta 609/347/279. `pd.read_csv` del cruce línea a
línea: coincide el `eid_scopus` con el universo.

### Ambigüedades abiertas

- Los 60 DOIs duplicados de la fuente: sin decidir cuál queda (D-400).
- Los 68 registros con DOI que **no** están en el universo (347 − 279) son
  candidatos a revisión de cobertura (producción real UFT fuera de Scopus o
  error del listado) — podría enriquecerse igual que `V2-26` si se decide
  mirarlos: es producción propia de la Facultad declarada por sí misma.
- Las de siempre: `T-06`, `T-19`.

### Próximo paso recomendado

Decidir si los 68 con DOI fuera del universo merecen la misma herramienta de
revisión que OpenAlex (cruzar contra Crossref por DOI, listado para una persona),
o si el cruce ya aporta suficiente para el contraste que se buscaba.

---

## Sesión 2026-09-01 (tarde) — Cierre de tramo

Continuación de la sesión anterior y de V2-27. Retomé con un contexto
reconstruido y verifiqué primero `git status` y el estado del pipeline
(sin trabajo colgando).

### Cierre · V2-27 (publicaciones de la Facultad de Medicina)

**Arreglo del `--test` roto.** El extractor tenía un modo `--sin-red`/`--test`
que dependía de un archivo temporal `_sample.html` (raíz del repo) que había
borrado en la limpieza. Refactoricé `facultad_medicina_publicaciones.py`:

- Quite la dependencia de `SAMPLE` (archivo en disco) y el flag `--sin-red`.
- Incrusté un **fixture mínimo inline** (`FIXTURE`) que reproduce el marcado
  real (badges, `<h4>`, `<dl>`, "Ver DOI") para que `--test` sea hermético y
  sin red, acorde a la convención del proyecto.
- Corregí el mapeo de sección: los encabezados de grupo por año
  (`"2025: 136 publicaciones"`) ahora se resuelven a **Escuela de Medicina**
  vía `_seccion_de_encabezado`, no a su etiqueta literal. Re-verificado la
  corrida real: **609/347/279** sin cambios de conteo; secciones correctas
  (Medicina 554, Nutrición 34, Libros 11, Enfermería 10).

**Respuesta al usuario** sobre método y facultades:
- Método: no fue scrape del HTML renderizado, sino la **API REST de WordPress**
  (`/wp-json/wp/v2/pages?slug=publicaciones`). Verifiqué que **no hay** custom
  post type de publicaciones (`/publicacion` → 404); todo vive en el `content`
  de la página (id 10009).
- Facultades: es solo la **Facultad de Medicina y Salud**, con **escuelas**
  dentro (Medicina, Enfermería, Nutrición y Dietética, y Libros). El resto de
  facultades de la UFT no está en esta página.

### Cierre · V2-28 (desglose de los 68 "fuera del universo")

Ante la pregunta de "cómo serviría esta información", propuse el contraste de
cobertura y generé `internal/facultad_medicina_fuera_universo.md`.

**Hallazgo sobre nombres.** Al intentar cruzar "Autor/a UFT" con la identidad
consolidada (`authors.json`) salió que los **formatos no coinciden**: la Facultad
usa `Sócrates Aedo`; el proyecto usa la forma invertida de Scopus `Aedo S.`.
Un solape de tokens da falsos negativos (no fiabilidad). Decisión **D-344**:
no afirmar correspondencia; mostrar el campo tal cual lo declara la Facultad.
Un emparejamiento real requiere el normalizador de `matching_rules.yml`
(maquinaria V2-19), tarea aparte.

**Solo 16 de 68** registros fuera de universo declaran "Autor/a UFT" — la
Facultad no rellena ese campo en todas las entradas.

**Decisiones del reporte (D-345, D-346):**
- Preferí **tabla plana** ordenada por año (decisión explícita del usuario,
  no agrupar por subtítulos; tenía ofrecida la opción de agrupar por año).
- Los 34 dentro de ventana (2023-2025) son los candidatos plausibles de
  cobertura; 31 fuera de ventana; 3 sin año. Se marcó columna "Fuera de ventana".

### Works / commits de este tramo

| Commit | Contenido |
|---|---|
| `08ca769` (antes) | 6 fixes de auditoría documental (bases 542/277, flags de API, AU-03). Push a `origin/main`. |
| `e0eb798` | V2-27: extractor + JSON (609) + CSV cruce + cierre de sesión en SESSION_NOTES. Push. |
| `e89e58a` | V2-28: desglose de 68 DOIs fuera de universo. Push `e0eb798..e89e58a`. |

### Pendientes (sin bloqueo)

- **Los 68 DOIs fuera del universo quedan como insumo documentado** (`internal/
  facultad_medicina_fuera_universo.md`), **no** se incorporen a una cola de
  revisión nueva. Decisión del usuario **D-347**: ya existe la vía de revisión
  de cobertura (`internal/revision_cobertura_openalex.html`, V2-26) y la de
  identidad (`internal/revision_identidad.html`); el desglose de la Facultad no
  entra en ninguna como entrada nueva — es referencia de contraste.
- **`AGENTS.md` sin trackear** (intencional, igual que antes): no forma parte de
  estos fixes. Decidir si entra al repo o se queda fuera.
- **Emparejamiento "Autor/a UFT" con la identidad** (D-344): normalizador real
  de `matching_rules.yml`, tarea aparte.
- **Nota de entorno**: pandas 3.0.5 fuera del pin `pandas>=2.0,<3.0`; prerrequisito
  `npx playwright install chromium`. Ya consignado en sesión previa.
- Las de siempre: `T-06`, `T-19`.
- El `git push` muestra "RemoteException"/"NativeCommandError" en PowerShell por
  canal stderr de git: es esperado, no un error.

### Próximo paso recomendado

Decidir con el usuario si `AGENTS.md` se versiona. El contraste de la Facultad
quedó cerrado como insumo documentado (D-347).

## Cierre: fusión de `origin/main` (sesión paralela) y un bug real de idempotencia expuesto al fusionar

### Contexto

El usuario preguntó por `internal/facultad_medicina_fuera_universo.md`, un
archivo que no estaba en esta rama. Se encontró en `origin/main`: una
sesión paralela había trabajado directamente ahí mientras esta rama
avanzaba por separado — incluyendo su propia tanda de identidad (34
grupos consolidados, 14 ORCID retirados) y el cruce de la Facultad de
Medicina. El usuario pidió revisar el solapamiento real antes de seguir,
y luego autorizó la fusión.

### El análisis de solapamiento (antes de tocar nada)

Comparación fila por fila de `internal/identity_decisions.csv` entre las
dos ramas contra su ancestro común (`git merge-base`):
- 125 firmas con alguna decisión en ambas ramas.
- **1 sola contradicción real de ORCID**: `Arroyo A.` — `main` decía
  `orcid_correcto` (probablemente de una tanda temprana, antes de que
  existieran los conectores DSpace/autoarchivo que expusieron el
  problema); esta rama decía `orcid_incorrecto` con reasignación, con la
  evidencia cruzada construida junto al usuario. El usuario autorizó
  mantener la resolución de esta rama.
- **0 conflictos** de consolidación de identidad (`misma`/`distintas`):
  37 pares donde ambas ramas coinciden de forma independiente, ninguno
  donde una diga "misma" y la otra "distintas".
- El resto del solapamiento es progreso, no contradicción: la misma cola,
  con esta rama más avanzada en la mayoría de los casos compartidos.

`git merge-tree --write-tree` confirmó 7 archivos con conflicto textual,
pero 6 son generados (`STATE.md`, `docs/DECISIONS.md`,
`docs/BUILD_VERIFICATION.md`, `config/orcid_revisado.yml`,
`config/identidades_consolidadas.yml`) — se resuelven regenerándolos, no
fusionándolos a mano. Sólo `SESSION_NOTES.md` (narrativo) e
`internal/identity_decisions.csv` (el propio Arroyo A.) necesitaban
juicio real.

### La fusión

`internal/identity_decisions.csv`: unión de las filas de ambas ramas por
`caso_id`; donde el mismo `caso_id` difiere, gana la fila NO pendiente
(progreso), y `ver-Arroyo A.` se resolvió explícitamente a favor de esta
rama por instrucción del usuario. 419 filas resultantes.

`SESSION_NOTES.md`: las dos ramas comparten exactamente las primeras 5554
líneas con su ancestro común (verificado por diff, no asumido) — empalme
lineal limpio: base + lo añadido por esta rama + lo añadido por `main`,
con una nota explícita marcando dónde empieza el contenido de la sesión
paralela, para que quede claro su origen a quien lea esto después.

Los cinco archivos generados se resolvieron trivialmente (`--ours`, ya
que su contenido real llega de re-ejecutar los scripts) y luego se
regeneraron de verdad: `apply_decisions.py`, `dspace_inventario.py`,
`autoarchivo_uft.py`, `build_review.py`, `build_all.py`,
`src/state/snapshot.py`.

### El bug real que expuso la fusión: `apply_decisions.py` no era idempotente

Al reconstruir tras la fusión, `Arroyo A.` apareció con `orcid: null` en
`authors.json` — la ficha entera sin ORCID, no el valor viejo ni el
nuevo. Se rastreó hasta `config/orcid_revisado.yml`: la entrada
`retiradas` para Arroyo A. tenía **el ORCID nuevo y correcto**
(`0000-0002-6248-9257`) marcado como el que se retira, no el original
mal asociado. `03_authors.py` filtraba correctamente esa fila —tal como
está diseñado— pero la fila que filtraba era la única correcta que
quedaba.

Causa raíz: `veredictos_orcid()` calcula "vigente" leyendo
`data/enriched/authors_orcid.csv` en disco AL INICIO de cada corrida.
Esta rama ya había aplicado con éxito la retirada-y-reemplazo de Arroyo
A. en una corrida anterior (antes de la fusión), así que el disco ya
tenía el ORCID NUEVO como vigente. `identity_decisions.csv` sigue
trayendo la fila `orcid_incorrecto` original — nunca se borra, es
historial — así que al volver a correr `apply_decisions.py` (esta vez
disparado por la fusión, que reconstruye todo desde cero) el código leyó
"lo vigente hoy" (el reemplazo correcto) y lo marcó como "lo que hay que
retirar", pensando que seguía siendo el error original. Es la cuarta
variación de la misma familia de bug de esta sesión (retirar-y-reemplazar
en una sola corrida, ya corregido dos veces antes) — pero esta vez no
era dentro de una corrida, era ENTRE corridas: reaplicar la misma
decisión después de que ya había surtido efecto.

Corregido en `veredictos_orcid()`: antes de marcar una firma como
retirada, se comprueba si el valor "vigente" ya coincide con lo que la
MISMA tanda de decisiones está proponiendo como reemplazo
(`orcid_encontrado`) — si coincide, el retiro ya está aplicado y no se
repite; se registra un aviso, no un error. Caso de prueba nuevo en
`apply_decisions.py --test` que reproduce exactamente el escenario de
fusión (VIG ya con el valor de reemplazo).

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-361 | La rama se fusiona con `origin/main`; `Arroyo A.` se resuelve a favor de la evidencia cruzada de esta rama | Única contradicción real de identidad entre las dos ramas; decisión explícita del usuario tras ver el análisis de solapamiento |
| D-362 | `veredictos_orcid()` no retira una asignación cuando "lo vigente" ya coincide con el reemplazo que la misma tanda propone | Sin esto, reaplicar una decisión de retirar-y-reemplazar YA aplicada en una corrida anterior borra el reemplazo correcto pensando que sigue siendo el error original — encontrado al fusionar dos ramas que habían aplicado la misma decisión por separado |

### Verificación

`apply_decisions.py --test` (40/40, incluye el caso nuevo),
`dspace_inventario.py --test`, `autoarchivo_uft.py --test`,
`build_all.py` (compuerta 0 fallas), `node src/verify/run_all.mjs`
(6/6). Se comprobó manualmente en `authors.json` que Arroyo A. quedó con
`orcid: "0000-0002-6248-9257"`, confianza alta, etiqueta "encontrado por
revisión" — y que ninguna otra firma quedó con `orcid: null` de forma
espuria (se revisaron las 264 fichas sin ORCID: todas legítimamente sin
asignación, ninguna filtrada por error).

### Archivos modificados

```
internal/identity_decisions.csv     fusión de ambas ramas, 419 filas
SESSION_NOTES.md                    empalme lineal + nota de fusión
src/review/apply_decisions.py       fix de idempotencia + 1 caso de prueba
config/orcid_revisado.yml,
config/identidades_consolidadas.yml,
data/enriched/authors_orcid.csv     regenerados tras la fusión
+ todo lo que main aportó: AGENTS.md, facultad_medicina_*,
  src/enrich/facultad_medicina_publicaciones.py, fixes de auditoría
```

### Ambigüedades abiertas

- Las de siempre, más lo que main dejó pendiente: decidir si `AGENTS.md`
  se versiona (ya resuelto en un commit posterior de main, «sí»), y el
  emparejamiento "Autor/a UFT" de la Facultad de Medicina con la
  identidad consolidada (D-344, tarea aparte).

### Próximo paso recomendado

Push de la fusión. Reportar al usuario el resultado, incluyendo el bug
de idempotencia encontrado y corregido — no estaba buscándolo, lo
expuso la propia fusión.

## Cierre: auditoría de todo lo vinculado a revisiones pendientes

### Contexto

El usuario pidió auditar todo el trabajo vinculado con revisiones
pendientes — no un punto específico, un barrido completo. Se revisó
integridad de datos, consistencia del pipeline, y se buscaron
activamente patrones de bug ya conocidos de esta sesión en el resto del
código, en vez de asumir que estaban contenidos a donde ya se habían
corregido.

### Hallazgo 1 (corregido): el bug de `comment='#'` seguía vivo en 4 archivos hermanos

`decisiones.py::leer()` documenta el bug de `pd.read_csv(comment='#')`
(trunca en la primera almohadilla esté donde esté) y lo corrigió — pero
sólo para `identity_decisions.csv`. El mismo patrón exacto seguía sin
corregir en `build_openalex_review.py`, `apply_unit_validation.py`,
`apply_openalex_review.py` y `build_unit_validation.py`, los cuatro
leyendo decisiones de revisión humana de otras colas (validación de
unidades, cobertura OpenAlex). `internal/unit_validation_decisions.csv`
no tiene almohadillas fuera de su cabecera hoy —no es una corrupción
activa—, pero la vulnerabilidad era real para la próxima nota que
mencione "ítem #3". Corregido con el mismo patrón (saltar cabecera por
posición, no por `comment=`) en los cuatro archivos.

### Hallazgo 2 (encontrado, NO corregido — necesita decisión de diseño): la cola "Varios Scopus ID" no tiene efecto en el pipeline

Al auditar `identity_decisions.csv`, 20 filas —y sólo esas 20, las 20
de la cola "Varios Scopus ID" (P-04)— tienen la columna `firmas` VACÍA.
Se investigó por qué: `build_review.py` busca la ficha con
`perf.get(r["nombre_en_fuente"])`, pero para esta cola
`nombre_en_fuente` viene en formato "Apellido, Nombre completo" (p.
ej. "Castillo, Oscar"), mientras que `perf` está indexado por la firma
corta que usa el resto del proyecto ("Castillo O."). La búsqueda falla
siempre, para las 20 filas, tengan o no ficha real.

Pero incluso corrigiendo esa búsqueda, el problema de fondo seguiría: el
mecanismo que consume veredictos "misma"/"distintas"
(`grupos_de_identidad()`) necesita DOS firmas por fila para fusionar un
par — `itertools.pairwise([un_solo_elemento])` no produce nada. Esta
cola sólo puede aportar UNA firma por fila (el nombre completo con
varios Scopus Author ID es una sola persona-candidata, no dos firmas
distintas a comparar), así que el veredicto "misma"/"distintas" nunca
tuvo, estructuralmente, manera de fusionar ni separar nada — no importa
si la búsqueda de ficha funciona o no.

Se verificó el alcance real: de los 20 casos, **10 corresponden a
personas que SÍ están en la población UFT** (`en_poblacion_uft: True`
en `internal/ambiguities_authors.csv`) — alguien, en una revisión
anterior, miró la evidencia (¿coautoría en común? ¿los dos IDs firman la
misma publicación?) y marcó "misma" o "distintas" pensando que eso
registraba una decisión con efecto, y no lo tuvo — nunca lo tuvo, para
ningún caso de esta cola, desde que se creó.

**No se corrigió.** Arreglar la búsqueda de ficha es trivial, pero no
alcanza: haría falta decidir qué debería HACER un veredicto "distintas"
aquí — ¿partir la ficha en dos identidades? ¿marcar uno de los dos
Scopus Author ID como sospechoso? Eso es una decisión de diseño sobre el
modelo de datos, no un bug de una línea. Se documenta como hallazgo para
que el usuario decida el rumbo antes de tocar nada.

### Hallazgo 3 (encontrado, no corregido — fuera de alcance): `build_openalex_review.py` no corre contra el CSV actual

Al probar el fix del Hallazgo 1, `build_openalex_review.py` lanzó
`KeyError: 'nota'`: `internal/openalex_cobertura_decisiones.csv` sólo
tiene las columnas `openalex_id,veredicto` — sin `nota` — y el código
asume que existe. Es un bug preexistente, no causado por el fix (el
código viejo con `comment='#'` habría fallado exactamente igual: la
columna no existe en el archivo, sin importar cómo se lea). Pertenece a
la vía de cobertura OpenAlex (V2-26), un área distinta de las 128
revisiones de identidad de esta sesión, y aparentemente inactiva desde
hace tiempo. No se tocó: no hay contexto suficiente para saber si el
CSV está desactualizado o si el código lo está.

### Verificado limpio

- `identity_decisions.csv`: 419 filas, 0 `caso_id` duplicados, 0
  veredictos desconocidos, 0 veredictos fuera de su cola, 0 filas
  PENDIENTES con firmas vacías (el problema del Hallazgo 2 está
  contenido a filas YA decididas de una sola cola).
- `apply_decisions.py --test` (40/40), `dspace_inventario.py --test`,
  `autoarchivo_uft.py --test`: todos en verde.
- Estado de git: limpio, sin pushes paralelos, rama al día con origin.
- `apply_unit_validation.py --dry-run` corre limpio con el fix del
  Hallazgo 1 aplicado; confirma independientemente (desde una validación
  de 2026-08-26, anterior a la confusión de hoy) que "Facultad de
  Educación, Psicología y Familia" corrige A "Facultad de Educación y
  Ciencias Sociales" — el mismo sentido que confirmó el usuario
  directamente en finis.cl.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-363 | El fix de lectura segura de CSV (saltar cabecera por posición, no por `comment=`) se replica en los 4 archivos hermanos que compartían el mismo patrón sin corregir | Mismo bug ya documentado y corregido una vez en `decisiones.py`; dejarlo sin corregir en 4 sitios más es dejar la misma vulnerabilidad de corrupción silenciosa a la espera de una nota con almohadilla |
| D-364 | La cola "Varios Scopus ID" (P-04) NO se corrige todavía: se documenta como hallazgo que necesita una decisión de diseño del usuario, no un fix mecánico | Corregir sólo la búsqueda de ficha no resolvería el problema real (el mecanismo de fusión necesita 2 firmas por fila, esta cola sólo puede dar 1); decidir qué debe hacer un veredicto aquí es una decisión sobre el modelo de datos, reservada al usuario |

### Verificación

`apply_decisions.py --test` (40/40), `dspace_inventario.py --test`,
`autoarchivo_uft.py --test` en verde tras los cambios. Sintaxis validada
en los 4 archivos corregidos (`ast.parse`); `apply_unit_validation.py
--dry-run` y `build_unit_validation.py` corridos de verdad, sin errores.
`build_openalex_review.py`/`apply_openalex_review.py` probados: el
primero falla por el Hallazgo 3 (preexistente, documentado, no
corregido), el segundo corre limpio.

### Archivos modificados

```
src/review/build_openalex_review.py,
src/review/apply_unit_validation.py,
src/review/apply_openalex_review.py,
src/review/build_unit_validation.py    fix de lectura segura de CSV
internal/validacion_unidades.md,
internal/validacion_unidades.html      regenerados (fecha), sin cambio
                                        de contenido sustantivo
```

### Ambigüedades abiertas

- **Hallazgo 2 sin resolver**: 20 veredictos "misma"/"distintas" de la
  cola "Varios Scopus ID" son y siempre fueron inertes. Necesita
  decisión del usuario sobre qué debería hacer un veredicto ahí antes de
  tocar el código.
- **Hallazgo 3 sin resolver**: `build_openalex_review.py` no corre
  contra el CSV de decisiones actual. Fuera de alcance de esta
  auditoría (área V2-26, no las 128 revisiones de identidad).
- Las de siempre.

### Próximo paso recomendado

Reportar los tres hallazgos al usuario con su severidad real (uno
corregido, uno esperando decisión de diseño, uno fuera de alcance
documentado). No proponer una solución para el Hallazgo 2 sin que el
usuario decida primero qué debe significar "distintas" para un nombre
con varios Scopus Author ID.

## Cierre: revisión caso por caso del Hallazgo 2 (9 de 10 confirmados, 1 revertido a pendiente) y corrección del bug de búsqueda

### Contexto

El usuario pidió ver los 10 casos reales del Hallazgo 2 (población UFT)
antes de decidir nada, y luego pidió revisarlos caso por caso antes de
decidir — no aceptar el patrón "misma" uniforme con confianza ciega.

### La revisión

Para cada uno de los 10, se cruzó el/los Scopus Author ID contra el
export crudo de Scopus (`Authors with affiliations`, que trae la
afiliación ESPECÍFICA de esa persona en cada publicación, no la de todos
los coautores) y se comparó: misma unidad académica exacta, mismo tema
de investigación, entre los identificadores en conflicto.

**9 de 10 — evidencia fuerte y consistente**: Castillo Oscar, De la
Fuente López Marjorie, Gutiérrez Juan, Hartmann Schatloff Dan, Moreno
Sergio, Quezada Mauricio, Rojas Dario, Rojas-Costa Gonzalo M., Torres
Keila. En cada uno, ambos (o los varios) identificadores firman desde la
MISMA unidad académica exacta Y sobre el MISMO tema de investigación —
coincidencia por homonimia en ambos ejes a la vez es poco plausible.

**1 de 10 — dispersión temática real**: Moya, Patricia. Un mismo
identificador (57767862900) firma tanto "atención de urgencia por
ideación suicida" (Salud Pública) como "determinantes de caries en
preescolares" (Odontología) — mucho más dispersión que los otros 9. No
se confirmó junto con el resto.

**Verificación cruzada, no buscada a propósito**: al aplicar, "Castillo
O." y "Hartmann Schatloff D." resultaron ya fusionados en el sitio con
"Castillo-Valenzuela O." y "Hartmann D." respectivamente, vía una
consolidación de variantes de nombre (P-03) decidida por separado. La
unidad académica de esa ficha fusionada ("Escuela de Nutrición y
Dietética, Facultad de Medicina y Salud" para Castillo) coincide
exactamente con la afiliación que ya se había verificado para el caso
P-04 — dos decisiones tomadas por caminos completamente distintos
(consolidación de nombre vs. revisión de Scopus Author ID) llegan a la
misma conclusión. No prueba nada por sí sola, pero es la clase de
coincidencia que refuerza en vez de contradecir.

### Aplicado

Se corrigió PRIMERO el bug de búsqueda de ficha que el Hallazgo 2 ya
había identificado (`nombre_en_fuente` en formato "Apellido, Nombre" vs.
`perf` indexado por firma corta "Apellido N."): se agregó
`_firma_corta_p04()` en `build_review.py`, copia deliberada y declarada
de `_firma_corta()`/`id_by_short` de `04_author_population.py` (no
importable directo: el módulo empieza con dígito). Verificado contra el
HTML regenerado: las 10 firmas UFT ahora se vinculan a su ficha real; las
10 que no están en la población siguen —correctamente— sin firma.

Luego se actualizó `identity_decisions.csv`: los 9 casos confirmados
recibieron la firma correcta y una nota con la evidencia específica
revisada (afiliación + tema, no una frase genérica); Moya, Patricia se
revirtió de "misma" a "pendiente" con nota explicando la dispersión
temática que la deja fuera de este lote.

### Lo que esto NO cambió, dicho con la misma honestidad que el hallazgo original

Confirmado con `apply_decisions.py --dry-run`/real: "grupos consolidados"
se mantuvo en 37 antes y después — los 9 "misma" no fusionaron ni
separaron nada, exactamente como predijo el Hallazgo 2 (el mecanismo de
fusión necesita 2 firmas por fila para formar un par; esta cola sólo
puede dar 1). Lo que SÍ cambió: el registro ahora es preciso —firma
correctamente vinculada, evidencia específica en vez de una nota vacía—,
y la cola de pendientes subió de 128 a 129 (Moya, Patricia vuelve a
estar genuinamente abierta, no falsamente resuelta).

No se tocó el diseño del mecanismo de fusión (seguía siendo la pregunta
sin responder del Hallazgo 2: qué debería hacer "distintas" aquí). Eso
sigue pendiente de una decisión del usuario, no se resolvió con este
cierre.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-365 | Se confirma "misma" para 9 de los 10 casos P-04 de la población UFT, con evidencia de afiliación+tema específica por caso | Revisión caso por caso solicitada explícitamente por el usuario, no un patrón aceptado en bloque |
| D-366 | Moya, Patricia NO se confirma junto con el resto; se revierte a pendiente | Un mismo Scopus Author ID cubre dos temas de investigación bastante distintos — más dispersión que los otros 9, no alcanza el mismo nivel de evidencia |
| D-367 | Se corrige la búsqueda de ficha de la cola P-04 (`_firma_corta_p04`) antes de aplicar las confirmaciones | Sin esto, la ficha real seguiría sin vincularse aunque el veredicto estuviera bien registrado — el Hallazgo 2 ya lo había identificado como bug de código, no de diseño |

### Verificación

`apply_decisions.py --test` (40/40), `build_all.py` (compuerta 0
fallas, 538 fichas — sin cambio, como se predijo), `node
src/verify/run_all.mjs` (6/6). Verificado manualmente que las 10 firmas
UFT ahora aparecen en `CASOS` del HTML regenerado, y que las 9
confirmadas + la revertida quedan correctamente reflejadas en
`identity_decisions.csv` tras una relectura limpia.

### Archivos modificados

```
src/review/build_review.py        _firma_corta_p04() + fix de búsqueda
internal/identity_decisions.csv   9 filas confirmadas con evidencia,
                                   1 revertida a pendiente
config/orcid_revisado.yml,
config/identidades_consolidadas.yml,
data/enriched/authors_orcid.csv   regenerados (sin cambio sustantivo
                                   por este cierre específico)
```

### Ambigüedades abiertas

- El diseño del mecanismo de fusión para P-04 sigue sin resolver
  (Hallazgo 2 original): qué debe hacer "distintas" aquí es una
  decisión de modelo de datos, no tocada.
- Moya, Patricia queda pendiente de revisión adicional.
- Las de siempre.

### Próximo paso recomendado

Reportar al usuario: 9 confirmados con evidencia caso por caso, 1
diferido con motivo claro, el bug de búsqueda corregido, y la aclaración
honesta de que el mecanismo de fusión real sigue sin existir — esto deja
el registro correcto, no la pregunta de diseño resuelta.

## Cierre: "Producción ampliada" — corpus paralelo declarado por las Facultades, fuera de Scopus

### Cómo empezó

El usuario preguntó si los datos de la Facultad de Medicina (§2.6,
`facultad_medicina_publicaciones.py`) podían alimentar los gráficos del
sitio. Se explicó por qué no directamente —esos datos no tienen métricas
SciVal, no pasaron por el criterio de indexación de Scopus, mezclarlos
presentaría calidad y comparabilidad distintas como si fueran la misma
medición— y se ofreció la alternativa correcta: una nota de cobertura, o
un corpus paralelo declarado aparte. El usuario contestó con su objetivo
real: "ampliar la cobertura de la plataforma, no limitarnos a Scopus".
Se le preguntó explícitamente (`AskUserQuestion`) dónde debía vivir ese
dato y si el mecanismo debía ser general o sólo para Medicina — eligió
sección aparte y mecanismo general para cualquier Facultad.

### El diseño (plan mode)

Dado el alcance (pipeline de build, configuración de indicadores, y el
sitio), se usó `EnterPlanMode`: dos agentes Explore en paralelo (uno
sobre convenciones de build/config, otro sobre convenciones de sitio/JS)
más un agente Plan para converger en un diseño concreto, y verificación
manual de los hallazgos más consecuentes antes de escribir el plan final
(varios: el conteo real de duplicados/universo en el JSON existente, que
`eid_scopus`/`anio_scopus` no siempre están presentes como claves, la
convención exacta de `config/sources.yml`/`indicators.yml`, y — el
hallazgo más importante— que `common_build.procedencia()` siempre usa la
fecha de corte de SciVal como "Corte", que habría sido engañosa para un
indicador que no tiene nada que ver con SciVal).

### Lo aplicado

**Esquema común, no una fuente hardcodeada**: todo conector de
"producción declarada" escribe un JSON con un campo `facultad` (nombre
CANÓNICO, el mismo que usa la jerarquía de `matching_rules.yml`) — sin
eso, agrupar por facultad exige nombrar la Facultad en el código Python.
`facultad_medicina_publicaciones.py` ganó ese campo (constante
`FACULTAD`, un `assert` nuevo en `--test`); como no se pudo re-ejecutar
el scraper (egress bloqueado en este entorno, igual que con
`orcid.org`/`finis.cl` en sesiones anteriores), se parchearon los 609
registros existentes en `data/enriched/` e `internal/` in situ, sin
inventar ningún dato nuevo.

**`config/sources.yml`** ganó la entrada que faltaba (el encabezado del
archivo ya exigía que "todo indicador publicado debe poder rastrearse
hasta una entrada de este archivo" — un hueco real, no nuevo de este
cierre) con la bandera `corpus_paralelo_declarado: true`: es lo que
`09_produccion_declarada.py` usa para DESCUBRIR fuentes de este tipo sin
nombrar "Medicina" en `src/build/` — una segunda Facultad que sume su
propio listado más adelante sólo necesita su propia entrada con esa
bandera, nada en el build cambia.

**`src/build/09_produccion_declarada.py`** (nuevo, agregado a `STEPS`):
deduplica por (facultad, DOI) — la fuente trae duplicados a propósito
(`D-400` original: "el sitio lista duplicados; borrarlos en el extractor
ocultaría un dato de la fuente"), así que la deduplicación se hace aquí,
en el consumidor, no en la ingesta. Separa lo ya indexado en Scopus (pura
divulgación) de lo nuevo, y dentro de lo nuevo separa por la ventana
2023-2025: lo de fuera de ventana o sin año NUNCA se oculta, va a una
nota de transparencia aparte. No corre `sys.exit()` si no hay fuentes
declaradas — este dato es opcional por diseño, a diferencia de la
auditoría.

**`config/indicators.yml`** ganó `PD-01` con `solo_recuento: true` (mismo
campo que ya usa T-04 para ODS) y categoría nueva `declarado`.
Deliberadamente AUSENTE de `kpis_portada` — eso es lo que mantiene el
dato fuera de los gráficos existentes. `common_build.procedencia()` ganó
un parámetro `corte` opcional para no mostrar la fecha de corte de
SciVal en un indicador que no tiene relación con SciVal.

**`web/produccion-ampliada.html`** (nuevo): cifras clave, tabla Facultad
× año, nota de transparencia compuesta en runtime desde los datos reales
(nunca cifras escritas a mano), advertencia reutilizando `.nota-destacada`
y el sello de procedencia reutilizando `sello()` — con una frase propia
aclarando que "Cobertura" aquí significa algo distinto (% dentro de la
ventana temporal, no % de datos poblados) que en el resto del sitio.
Registrada en los tres puntos que hacían falta (`prerender.mjs`,
`paginas.js`, nav en `core.js`) y en los dos archivos de verificación que
fallan adrede si una página en `dist/` no está en su lista
(`estructura.mjs`, `contraste.mjs`).

### Verificación

`facultad_medicina_publicaciones.py --test`, `build_all.py` (compuerta 0
fallas), `06_assemble_site.py` (11 páginas, sin avisos de cabecera ni de
contenedor vacío), `node run_all.mjs` (6/6, incluido contraste WCAG de
los componentes reutilizados con datos reales). Verificación manual con
Playwright: nav en el lugar correcto con `aria-current` bien puesto,
contenido presente con JavaScript DESACTIVADO (contenido
pre-renderizado, no sólo cliente), capturas de pantalla en tema claro y
oscuro. Regresión: `kpis.json` sigue con los mismos 6 códigos de
siempre — PD-01 no tocó ningún gráfico existente.

Números reales de esta corrida: 609 registros leídos, 63 duplicados
colapsados, 221 ya en el universo Scopus, 325 fuera de él — de esos, 83
dentro de la ventana 2023-2025 (la cifra publicada), 222 fuera de
ventana y 20 sin año (declarados en la nota de transparencia, no
ocultados).

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-368 | Los datos de la Facultad de Medicina NO se mezclan en los gráficos Scopus/SciVal existentes | No tienen métricas SciVal ni pasaron por el criterio de indexación de Scopus — mezclarlos presentaría calidad y comparabilidad distintas como si fueran la misma medición |
| D-369 | Se construye un mecanismo GENERAL de "producción declarada" (esquema común + bandera en `sources.yml`), no una integración hardcodeada a Medicina | El usuario lo pidió explícitamente; una segunda Facultad que sume su propio listado no debe requerir tocar `src/build/` |
| D-370 | La deduplicación por DOI ocurre en `09_produccion_declarada.py` (el consumidor), no en el conector de Medicina | La decisión original de no deduplicar en la ingesta (`D-400` de la sesión V2-27: "borrarlos en el extractor ocultaría un dato de la fuente") sigue vigente; alguien tenía que deduplicar antes de publicar un recuento, y ese alguien es quien construye el indicador, no quien ingiere |
| D-371 | PD-01 se excluye deliberadamente de `kpis_portada` y de la ventana ya usada por el resto de indicadores para su fecha de "Corte" | Es lo que mantiene este dato fuera de los gráficos Scopus/SciVal existentes y evita publicar una fecha de corte (la de SciVal) que no tiene relación con este indicador |
| D-372 | Lo fuera de la ventana 2023-2025 o sin año declarado NUNCA se oculta: va a una nota de transparencia aparte, con cifras reales | Ocultarlo habría sido tan engañoso como mezclarlo en un gráfico Scopus — la ventana temporal del proyecto no es motivo para dejar de contar un dato declarado |

### Archivos modificados

```
src/enrich/facultad_medicina_publicaciones.py   campo 'facultad'
data/enriched/facultad_medicina_publicaciones.json,
internal/facultad_medicina_cruce.csv            parcheados con 'facultad'
config/sources.yml                              nueva entrada
src/build/09_produccion_declarada.py            nuevo
src/build/build_all.py                          STEPS += 1
src/build/common_build.py                       procedencia(corte=...), FUENTE_POR_INDICADOR
config/indicators.yml                           PD-01
src/build/02_indicators.py                      CATEGORIAS += declarado
web/produccion-ampliada.html                    nuevo
web/assets/js/vista.js                          produccionDeclarada()
web/assets/js/paginas.js                        dispatch + función
web/assets/js/core.js                           nav
src/build/prerender.mjs                         rama nueva
src/verify/estructura.mjs, contraste.mjs        registro de página
docs/FUENTES_Y_APIS.md                          §2.6 nueva
docs/DATA_MODEL.md                              nota de corpus paralelo
docs/V2_BACKLOG.md                              nota distinguiendo de §8
```

### Ambigüedades abiertas

- El mecanismo es general, pero sólo tiene UNA fuente real hoy
  (Medicina). No se construyó ninguna abstracción especulativa más allá
  de la bandera en `sources.yml` y el esquema documentado — si aparece
  una segunda Facultad, se sabrá si el esquema alcanza o hace falta
  ajustarlo.
- No se reejecutó el scraper de Medicina (egress bloqueado): los datos
  parcheados son los mismos 609 registros de la corrida del 2026-09-01,
  con el campo `facultad` agregado. Una corrida real, cuando se pueda,
  reflejaría el sitio actualizado.
- Las de siempre: Moya Patricia pendiente, el mecanismo de fusión de
  "Varios Scopus ID" sin resolver, T-06/T-19.

### Próximo paso recomendado

Reportar al usuario que la sección está publicada, con los números
reales y la explicación de por qué no toca ningún gráfico existente.
Confirmar que el push está limpio (sin pushes paralelos) antes de subir.

## Cierre: metodología para datos fuera de Scopus — jerarquía de niveles de evidencia (documentación, sin indicador nuevo)

### Contexto

Con `PD-01` ya publicado, el usuario preguntó cómo aportaban a esa misma
sección los datos de cobertura OpenAlex/Crossref que ya existían en
`internal/openalex_cobertura.csv` (`V2-26`). La respuesta —que son una
evidencia distinta, no una extensión de `PD-01`— llevó a la pregunta
explícita del usuario: "Me gustaría pensar en una metodología para
implementar todo lo que esté fuera de scopus". Tras exponer la idea central
en conversación (dos niveles de evidencia, incompatibles entre sí, que no
deben mezclarse aunque ambos compartan la etiqueta "fuera de Scopus") y
ofrecer formalizarla, el usuario pidió explícitamente: "Genera un doc".

### Qué se hizo

Nuevo `docs/METODOLOGIA_FUERA_DE_SCOPUS.md`: formaliza la distinción entre
**Nivel D** (declarado por la institución, sin verificación individual por
obra — `PD-01`/Facultad de Medicina, 609 registros, 83 en ventana) y
**Nivel V** (verificado obra por obra mediante criterio explícito —
la cola OpenAlex + Crossref, 414 candidatos, 20 confirmados vía revisión
humana, 394 pendientes; no publicada como indicador). Cinco reglas:
clasificar antes de construir, esquema compartido por nivel (nunca por
fuente ni entre niveles distintos), evidencia cruzada refuerza el mismo
registro en vez de duplicarlo, cada nivel con su propio indicador, y el
denominador del universo Scopus/SciVal no se toca en ningún nivel. Incluye
un checklist operativo de 5 preguntas para clasificar cualquier fuente
futura sin tener que rederivar el razonamiento desde cero.

No se propuso ni se construyó ningún indicador nuevo (ningún `PD-02`):
el propio documento declara en su §4 qué NO resuelve, y ampliar el alcance
publicado sigue siendo, por `D-16`/`D-206`, una decisión aparte que le
corresponde al usuario. Es un documento de clasificación, no una
implementación.

Verificado antes de escribir, no asumido: se leyó `docs/METHODOLOGY.md`
completo (gobierna el corpus canónico, no toca esta pregunta — no hay
duplicación) y se confirmaron con `python3` las cifras reales citadas
(`data/processed/produccion_declarada.json`, `internal/openalex_cobertura.csv`,
`internal/openalex_cobertura_decisiones.csv`) en vez de repetirlas de
memoria de la sesión anterior. Se agregaron referencias cruzadas de una
línea desde `docs/FUENTES_Y_APIS.md` §2.6, `docs/V2_BACKLOG.md` §8 y
`docs/DATA_MODEL.md` (todas ya mencionaban el mecanismo; ahora apuntan
también al marco general), y una entrada nueva en el mapa de lectura de
`src/state/snapshot.py` (`MAPA_LECTURA`) para que `STATE.md` la exponga.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-373 | Toda fuente fuera de Scopus se clasifica en Nivel D (declarado) o Nivel V (verificado obra por obra) antes de construir cualquier mecanismo para ella | `PD-01` y la cola OpenAlex/Crossref ya son dos fuentes reales con esa etiqueta compartida y evidencia incompatible; sin una regla explícita, una tercera fuente futura podría mezclarlas bajo el mismo indicador |
| D-374 | El documento de metodología no autoriza ni construye ningún indicador nuevo para la cola OpenAlex/Crossref | Ampliar el alcance publicado sigue siendo, por `D-16`/`D-206`, una decisión de alcance aparte y explícita que le corresponde al usuario — pensar la metodología no es autorizar su siguiente aplicación |

### Archivos modificados

```
docs/METODOLOGIA_FUERA_DE_SCOPUS.md   nuevo
docs/FUENTES_Y_APIS.md                referencia cruzada en §2.6
docs/V2_BACKLOG.md                    referencia cruzada en el blockquote de §8
docs/DATA_MODEL.md                    referencia cruzada en «Corpus paralelo declarado»
src/state/snapshot.py                 MAPA_LECTURA += 1 entrada
```

### Ambigüedades abiertas

- Ninguna nueva. Las de siempre: Moya Patricia pendiente, el mecanismo de
  fusión de "Varios Scopus ID" sin resolver (Hallazgo 2), 129 pendientes
  de identidad, T-06/T-19.

### Próximo paso recomendado

Ninguna acción de código pendiente de este cierre. Si el usuario decide
avanzar con un indicador Nivel V para la cola OpenAlex/Crossref, ese sería
un nuevo ciclo de diseño (EnterPlanMode), apoyado en el checklist de este
documento — no una continuación automática de este cierre.

## Cierre: auditoría integral del repositorio — inconsistencias, errores de datos, accesibilidad y correctitud metodológica de gráficos

### Contexto

El usuario pidió una auditoría rigurosa y detallada de todo el repositorio
—inconsistencias, errores, información desactualizada— con corrección
directa y sin consultas, seguida de una auditoría específica de interfaz,
gráficos, visualización e interacción. Se lanzaron 5 agentes en paralelo
(pipeline backend/config, documentación, integridad de
SESSION_NOTES/DECISIONS/STATE, frontend y registro de páginas, gráficos y
accesibilidad), cada uno con instrucción explícita de verificar contra el
repositorio real (ejecutar código, correr las herramientas del propio
proyecto) y no reportar nada sin evidencia. Se revisaron y aplicaron los
hallazgos de los 5, con verificación propia antes de cada corrección — en
al menos tres casos (ver «Errores propios» abajo) esa verificación evitó
aplicar un hallazgo tal como venía reportado.

### Qué se corrigió

**Integridad de datos (prioridad más alta, tabla maestra de autores).**
`config/orcid_revisado.yml` tenía a «Dreyse J.» a la vez en `confirmadas`
(ORCID `0000-0002-8201-5956`, respaldado por `authors_orcid.csv` vía
OpenAlex, confianza alta) y en `sin_registro` (nota vacía). Causa raíz:
`veredictos_orcid()` en `apply_decisions.py` sólo comprobaba
`confirmadas ∩ retiradas`, nunca `confirmadas ∩ sin_registro` ni
`retiradas ∩ sin_registro`. Hoy no afectaba lo publicado por una
casualidad de orden en `estado_orcid()` (03_authors.py), pero una futura
regeneración de `authors_orcid.csv` sin esa fila concreta habría publicado
«buscado y no encontrado» sobre una persona con ORCID confirmado por
revisión humana. Se agregó el guardián que falta (evidencia siempre le
gana a ausencia de evidencia, sin importar el orden temporal de los
veredictos) y se corrió `apply_decisions.py` de verdad: el único cambio
real fue eliminar la entrada contradictoria de `sin_registro` (327→327
asignaciones, sin backlog oculto — verificado con `git diff`).

**Bug de regex en `snapshot.py` — 55 % de `docs/DECISIONS.md` mal
atribuido.** `extraer_decisiones()` no toleraba un paréntesis entre la
fecha y el guion largo de un encabezado `## Sesión` (`(cont.)`,
`(EN CURSO)`, `(tarde)`): 6 de 16 encabezados no matcheaban, y la sesión
anterior quedaba pegada. Medido antes/después: "cierre de T-17 y T-18"
pasó de aparecer en 154 filas (de las que sólo 4 eran suyas) a 4; "Bento
Grid..." pasó de 0 apariciones a 57. Se agregó también detección de IDs
`D-NNN` repetidos (aviso a stderr, no bloqueante) y el mismo patrón seguro
de lectura de CSV (saltar líneas `#` por posición) que ya tenían otros 5
archivos, aplicado ahora a `colas_internas()`, que había quedado fuera de
ese barrido anterior.

**26 IDs de decisión duplicados, renumerados.** `SESSION_NOTES.md` tenía
26 números `D-NNN` reutilizados en sesiones distintas con contenido no
relacionado (`D-138`–`D-145`, `D-317`–`D-326`, `D-336`–`D-343`) — el
propio `D-341`/`D-343` que motivó la sospecha inicial. Causa: numeración
manual sin verificar el máximo ya usado al abrir cada sesión nueva, no un
bug de generación. Se conservó el ID de la primera aparición cronológica
de cada uno; la segunda aparición se renumeró a `D-375`–`D-400`
(secuencial, sin reabrir ninguna decisión: el texto no cambió, sólo su
identificador). Se buscaron y corrigieron las referencias en prosa que
dependían del número viejo apuntando al contenido correcto: 3 para
`D-343`→`D-400` (SESSION_NOTES.md, en el cierre de Medicina y en `D-370`),
2 para `D-144`/`D-145`→`D-381`/`D-382` (cierre de paleta), y 6 más para
`D-341`→`D-398` y `D-343`→`D-400` fuera de `SESSION_NOTES.md`
(`apply_decisions.py`, `web/assets/js/vista.js`, `config/sources.yml`,
`config/indicators.yml`, `docs/FUENTES_Y_APIS.md`, `docs/DATA_MODEL.md`,
`docs/METODOLOGIA_FUERA_DE_SCOPUS.md`) — verificadas una por una leyendo
el contexto real, no asumidas por proximidad numérica. `docs/DECISIONS.md`
pasó de 400 filas con 374 IDs únicos a 400 filas con 400 IDs únicos.

**Documentación: números desactualizados en 10 documentos.** Cluster de
cifras de autores/ORCID que llevaba dos consolidaciones sin propagarse
(556→542→538 entidades; 74/77/84 formas fusionadas en 30/34/37 personas) en
`README.md`, `docs/AUTHOR_PROFILE.md`, `docs/V2_BACKLOG.md`,
`docs/ORCID_COVERAGE.md`, `docs/INDICATORS.md`, `docs/DATA_LICENSE.md`,
`docs/DEPLOYMENT.md`, `docs/FUENTES_Y_APIS.md` — reconciliados contra
`STATE.md` (538 entidades, 274 con ORCID, 84 formas → 37 personas). Se
corrigió también, en `docs/LIMITATIONS.md`, la sección "cuatro firmas que
probablemente no son personas": ya se habían resuelto (las cuatro
confirmadas como fragmentos vía `E-09`, descartadas en
`firmas_e09_resueltas.yml`) y el documento seguía describiéndolas como
pendientes con la cifra vieja (556→552 hipotético). `docs/ARCHITECTURE.md`
decía "diseño aprobado, sin implementar" y marcaba `src/build/`,
`data/processed/` y `web/` como pendientes de Fase 3, y ROR/OpenAlex como
"consulta sin ejecutar" — los tres ya ejecutados y con fecha real en
`config/sources.yml` desde el 2026-08-25/26; reescrito para describir lo
implementado. `docs/LIMITATIONS.md` también afirmaba que el vocabulario de
unidades académicas «no está validado institucionalmente», contradiciendo
`config/matching_rules.yml` (`vocabulario_validado_por_institucion: true`,
`T-02` cerrado 2026-08-26). Además: 41/29 indicadores (no 40/28, con
`PD-01` agregado al catálogo de `docs/INDICATORS.md`, que no lo tenía),
400 decisiones (no 353), ruta `internal/matching_reconciliation.csv`
corregida a `data/interim/` (`docs/LIMITATIONS.md`), 11 páginas (no 10) en
`README.md`/`_cabecera.html`/`06_assemble_site.py`/`run_all.mjs`, y
`docs/METODOLOGIA_FUERA_DE_SCOPUS.md`, `docs/FUENTES_Y_APIS.md` y
`docs/OPERACION.md` agregados al índice de `README.md`, que no los tenía.

**Violación metodológica en la portada — barras multivaluadas sin trama.**
`vista_explorador.js`'s `grafico()` (el explorador de la portada, distinto
de `dibujar()` que usan las secciones) dibujaba "Áreas QS" y "Unidades
académicas" —ambos multivaluados: una publicación puede aportar a varias
barras— sin la trama rayada que marca esa condición en el resto del
sitio, y sin el aviso de P-07. Verificado en `dist/index.html`: cero
`rect.trama` en esos dos cortes antes del fix. Es la primera pantalla del
sitio; un lector podía leer las barras como si sumaran el total, que es
exactamente lo que `docs/METHODOLOGY.md` §6 prohíbe. Corregido pasando
`trama: MULTIVALUADO.has(clave)` y reutilizando (no reescribiendo) el
aviso de P-07 ya declarado en `SECCIONES.produccion`.

**`explorador.js` — dos bugs reales en cortes reactivos (R-01, C-06), no
sólo el gráfico de la portada.** `CAMPOS.cuartil` devolvía `[]` para
publicaciones sin `sjr_percentil`, así que el gráfico "parte de un
100 %" (R-01, `proporcional()`) se redibujaba, en cuanto se tocaba
cualquier filtro, como si el 100 % del recorte tuviera cuartil — mientras
el sello de cobertura, un párrafo más abajo, seguía mostrando el
porcentaje real. `02_indicators.py` sí declara un quinto valor, "Sin dato
declarado" (61 de 823), para exactamente este caso; `explorador.js` no lo
tenía. Se agregó el mismo bucket, y se corrigió `cobertura()` para
seguir excluyéndolo del cálculo de cobertura (igual que Python excluye
"Sin dato declarado" al sumar la cobertura de R-01) — confirmado con
Playwright: tras un clic de filtro, el gráfico reactivo pasa a mostrar
14,9 %/14,5 %/21,5 %/39,5 %/9,6 % (cinco segmentos, el quinto es "sin
dato"), no cuatro. Aparte, y más grave: los tramos de C-06 (autores por
publicación) en `explorador.js` (`TRAMOS_AUTORES`) usaban fronteras
DISTINTAS a las de `02_indicators.py` (JS: 1,2,3,4–5,6–10,11–20,21 o más;
Python: 1,2–3,4–6,7–10,11–20,21+) — no una etiqueta distinta, un binning
distinto: el mismo valor podía caer en un tramo diferente según cuál de
las dos versiones se estuviera mirando. Se igualaron los tramos JS a los
de Python.

**Accesibilidad de teclado — tres hallazgos reales, dos independientes.**
(1) La red de coautoría (C-05): `role="button"` en cada nodo sin
`tabindex`, `pasoTecladoRed()` escrito y nunca llamado, ningún
`addEventListener` sobre `[data-red-nodo]`. Se implementó con tabulación
giratoria (un solo punto de entrada, capado a los 90 nodos de mayor grado
que ya calculaba `disponerRed()`) y resaltado de nodo+coautores por clase
CSS —`data-vecinos`/`data-a`/`data-b` embebidos en el SVG en el
renderizado, sin necesitar volver a pedir datos ni re-renderizar—, en vez
de reproducir la ruta de re-render completo que `pasoTecladoRed()` (ya
eliminada, dependía de `D.nav`) hubiera exigido. Verificado con
Playwright: clic fija/suelta el foco, `Tab` aterriza en el nodo con
`tabindex=0`, flecha mueve el foco del navegador, `Intro` fija, `Escape`
suelta — sin errores de consola. (2) `heatmap.js`/`treemap.js` daban
`tabindex="0"` a CADA celda (hasta 24+9 paradas de Tab en
`produccion.html`), reintroduciendo el problema que las barras ya
habían resuelto (`docs/UX_UI.md` §10.1); se aplicó el mismo patrón
giratorio, generalizando el selector de `tecladoGraficos()` en
`paginas.js` en vez de duplicar el mecanismo. (3) `rect.acum-pista` (el
riel de fondo de `acumulada()`, I-05) medía 1,21:1 en claro y 1,08:1 en
oscuro contra `--superficie` —muy por debajo del piso 3:1 de WCAG
1.4.11—, y `contraste.mjs` nunca lo detectaba porque su selector de
"objetos gráficos" no lo cubría. Se cambió el token a `--tinta-3`
(6,18:1/5,75:1, medido, ya validado y en uso en el mismo componente) y se
amplió el selector de `contraste.mjs` para que este tipo de falla no
vuelva a pasar sin medirse.

**Código muerto real, verificado por alcanzabilidad, no por grep de
texto.** ~440 líneas: la arquitectura completa "modulos" —`RENDER`,
`modulo()`, `rail()`, `panelEje()`, `moduloDiferido()`, `paginaModulos()`,
`banda()`, `cierre()`, `hero()`, `kpis()`, `kpisRestantes`, `panorama()`
en `vista.js`; `modulos()` en `paginas.js`; la rama `tipo === 'modulos'`
en `prerender.mjs`— quedó inalcanzable desde que ninguna página lleva
`data-pagina="modulos"`, superada por la arquitectura "sección"/explorador
reactivo. `anillo()` en `core.js` (su único llamador vivo era
`RENDER['C-01']`, también muerto: C-01 se dibuja hoy como `barrasH`) y
`pasoTecladoRed()` (superada por el mecanismo de foco por CSS descrito
arriba) también se eliminaron. `docs/UX_UI.md` §12.4 todavía citaba
"Anillo de `C-01`" como ejemplo de la escala `'serie'`, que ahora no tiene
ningún gráfico publicado que la use — corregido para decirlo así, sin
inventar un ejemplo que no existe.

**Herramientas de verificación con defectos propios.**
`src/verify/higiene.py`: la detección de clases entre comillas no
toleraba un espacio inicial (`' chip-on'`, `' ordenada'`), dando dos
falsos positivos de "clase sin usar"; `EFIMEROS` tenía `'limpiar2'`
(id real: `limpiar-recorte`) y le faltaba `'q'` (creado dinámicamente,
buscado por `getElementById` en `paginas.js`), dando un falso positivo de
"id ausente" en cada corrida. `src/verify/responsive.mjs` cubría sólo
`index`/`impacto` sin guarda de cobertura — se amplió a las 11 páginas
(mismo patrón que `contraste.mjs`/`estructura.mjs`) y ENCONTRÓ un
desborde horizontal real: `publicaciones.html` desbordaba 303px en móvil
(430px) porque `.explorador-panel` (un ítem de grid) no tenía
`min-width: 0`, así que un chip de filtro con etiqueta larga ("Facultad
de Arquitectura, Diseño y Estudios Creativos") empujaba el panel entero a
su ancho de contenido (717px) — el clásico atrapa-desborde de
`min-width: auto` en CSS Grid. Corregido en `app.css`. `responsive.mjs`
tampoco fallaba nunca (nunca llamaba `process.exit(1)`); ahora sí.

### Errores propios, corregidos antes de aplicar

- Un agente reportó `data-indicadores` como marcado vestigial de la
  arquitectura "modulos" muerta y se quitó de 4 páginas de sección; el
  build se rompió (`04_glossary.py`'s `verificar_denominadores()` lo lee
  directamente del HTML para comprobar que el panel de `EJES.md` declara
  el denominador correcto — un uso real, en Python, que el grep de JS del
  agente no podía ver). Revertido antes de comitear; verificado con
  `python3 src/build/build_all.py` completo.
- Al medir el contraste del riel de I-05, `opacity: .55` sobre
  `--tinta-3` parecía visualmente más sutil pero medía 2,38:1/2,73:1 —
  vuelve a incumplir el piso. Se descartó antes de comitear; el fix final
  usa el color sólido, medido.
- La primera corrección de `.explorador-panel` mantuvo
  `min-width: auto` implícito en el propio `.explorador`; el desborde
  seguía. Se agregó `min-width: 0` en el nivel correcto (el ítem de grid,
  no el contenedor) tras diagnosticar con Playwright cuál elemento
  concreto excedía el viewport.

### Verificación

Cada corrección de código se verificó ejecutando la herramienta real que
la mide, no por inspección: `python3 src/audit/run_all.py` (30 reglas, 0
bloqueantes), `python3 src/review/apply_decisions.py --test` (batería
completa, incluidos los casos nuevos), `python3 src/build/build_all.py` +
`06_assemble_site.py` (11 páginas, sin avisos), `node
src/verify/run_all.mjs` completo — **contraste, estructura, flujos,
responsive, higiene, peso: 6/6 en verde**, incluida la cobertura ampliada
de `contraste.mjs`/`responsive.mjs` que antes no medía estos casos.
Verificación manual con Playwright, sin asumir nada del código: captura de
los 4 elementos con `getBoundingClientRect()` que causaban el desborde de
`publicaciones.html`; secuencia completa clic→Tab→flecha→Intro→Escape
sobre C-05 con verificación de clases DOM en cada paso; lectura de los
textos reales del SVG de R-01 tras un filtro de cliente.
`python3 src/state/snapshot.py`: 400 decisiones indexadas, 400 IDs únicos
(antes 374), sin avisos de duplicado.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-401 | `veredictos_orcid()` descarta siempre `sin_registro` cuando la misma firma tiene un veredicto `confirmadas`/`retiradas` con evidencia, sin importar el orden temporal en que se registraron | «No encontrado» es ausencia de evidencia, no una afirmación sobre un ORCID concreto — no pesa lo mismo que un veredicto con evidencia dispositiva (`D-341` original, ORCID) |
| D-402 | El regex de `## Sesión` en `snapshot.py` tolera un paréntesis opcional entre la fecha y el guion largo | 6 de 16 encabezados reales no matcheaban y mal-atribuían la "Fase" de hasta el 55 % de las filas de `docs/DECISIONS.md` a la sesión anterior |
| D-403 | Los 26 IDs `D-NNN` duplicados se resuelven conservando la primera aparición cronológica y renumerando sólo la segunda (`D-375`–`D-400`), sin tocar el texto de ninguna decisión | Es un error de numeración manual, no una decisión que reabrir (`CLAUDE.md`); el ID es una etiqueta, no el contenido |
| D-404 | La arquitectura "modulos" (`RENDER`, `modulo()`, `paginaModulos()`, `hero()`, `kpis()`, `panorama()`, `anillo()`, ~440 líneas) se elimina en vez de mantenerse | Verificado inalcanzable por trazado real desde los puntos de entrada (`data-pagina`, `tipo` de `prerender.mjs`), no por conteo textual — cero páginas la usan desde que la arquitectura de explorador reactivo la sustituyó |
| D-405 | El foco de C-05 (clic/teclado, resaltar nodo+coautores) se implementa con clases CSS sobre el SVG ya renderizado, no re-renderizando `svgRedNodos()` con `foco` | Evita necesitar `D` (el layout completo) en el navegador después del renderizado inicial; los datos para resaltar (`data-vecinos`, `data-a`/`data-b`) ya estaban disponibles en el SVG sin ese costo |
| D-406 | `data-indicadores` se conserva en `produccion.html`/`impacto.html`/`colaboracion.html`/`tematica.html` pese a que ningún JS de cliente lo lee ya | `04_glossary.py`'s `verificar_denominadores()` lo lee directamente del HTML como cruce de cobertura de `EJES.md` — quitarlo rompe el build (`BUILD ABORTADO`), confirmado al revertir |
| D-407 | Los tramos de "autores por publicación" en `explorador.js` se igualan a los de `02_indicators.py`, en vez de mantener un esquema propio para la vista reactiva | Eran fronteras de bin distintas para el mismo indicador (C-06): el gráfico cambiaba de agrupación al tocar cualquier filtro, no sólo de rótulo |
| D-408 | `CAMPOS.cuartil` en `explorador.js` devuelve `['Sin dato declarado']` en vez de `[]`, y `cobertura()` excluye ese valor explícitamente al contar cobertura | Mismo criterio que `02_indicators.py` (R-01): el gráfico "parte de un 100 %" necesita el bucket para no mentir sobre el reparto; el sello de cobertura necesita excluirlo para no mentir sobre cuánto dato hay |
| D-409 | El riel de fondo de `acumulada()` (I-05) usa `--tinta-3` en vez de `--red` | `--red` medía 1,21:1/1,08:1 contra `--superficie`, bajo el piso 3:1 de WCAG 1.4.11; `--tinta-3` (6,18:1/5,75:1, medido) es un token ya validado en el mismo componente |

### Archivos modificados

```
config/orcid_revisado.yml             elimina entrada contradictoria (Dreyse J.)
config/sources.yml, config/indicators.yml   referencia D-341→D-398 corregida
src/review/apply_decisions.py         guardián sin_registro∩(confirmadas∪retiradas)
src/state/snapshot.py                 regex de sesión, detección de ID duplicado, CSV seguro
SESSION_NOTES.md                      26 IDs renumerados + referencias en prosa corregidas
STATE.md, docs/DECISIONS.md           regenerados
README.md, PLAN.md                    cifras, índice de documentación, fecha de actualización
docs/ARCHITECTURE.md                  reescrito: estado implementado, no diseño pendiente
docs/LIMITATIONS.md                   ORCID recuperado, vocabulario validado, E-09 resuelto, ruta corregida
docs/AUTHOR_PROFILE.md, docs/V2_BACKLOG.md, docs/ORCID_COVERAGE.md,
docs/INDICATORS.md, docs/DATA_LICENSE.md, docs/DEPLOYMENT.md,
docs/FUENTES_Y_APIS.md                538/274, tramos de fusión, PD-01 en catálogo
docs/METHODOLOGY.md                   fecha de actualización
docs/UX_UI.md                         ejemplo de escala 'serie' corregido
web/assets/js/vista.js                −434 líneas (arquitectura modulos muerta)
web/assets/js/core.js                 −anillo(), −pasoTecladoRed(), +data-vecinos/data-a/data-b/data-nav en red()
web/assets/js/paginas.js              +alternarFocoRed/soltarFocoRed, tecladoGraficos() generalizado, −modulos()
web/assets/js/vista_explorador.js     grafico()/cortes() con trama+aviso, PAGINAS sin modulos
web/assets/js/explorador.js           TRAMOS_AUTORES, CAMPOS.cuartil, cobertura(), docstring reubicado
web/assets/js/visualizations/heatmap.js, treemap.js   tabindex giratorio
web/assets/css/app.css                --acum-pista, min-width:0 en .explorador-panel/.explorador-resultado
src/build/prerender.mjs               rama 'modulos' eliminada, carga de ejes.json sin uso eliminada
src/build/06_assemble_site.py         "once páginas"
src/verify/higiene.py                 EFIMEROS, regex de clases con espacio inicial
src/verify/responsive.mjs             reescrito: 11 páginas, guarda de cobertura, falla de verdad
src/verify/contraste.mjs, run_all.mjs rect.acum-pista, "11 páginas"
web/_cabecera.html, web/produccion.html, web/impacto.html,
web/colaboracion.html, web/tematica.html   "once páginas" / data-indicadores conservado
```

### Supuestos descartados

- Que `data-indicadores` en las páginas de sección era marcado
  vestigial de la arquitectura muerta: es una fuente de datos real para
  `04_glossary.py`, verificado al romper el build.
- Que reducir la opacidad de `--tinta-3` en el riel de I-05 bastaba para
  quedar "suficientemente sutil": medido, no alcanza 3:1 por debajo de
  ~70 % de mezcla, y a esa mezcla ya no es más sutil que el color sólido.
- Que las 4 firmas de `E-09` seguían pendientes de revisión (como decían
  varios documentos): ya estaban resueltas y descartadas.

### Ambigüedades abiertas

- Ninguna nueva de esta auditoría. Las de siempre: Moya Patricia
  pendiente, la fusión de "Varios Scopus ID" sin resolver (Hallazgo 2 de
  la auditoría anterior), 129 pendientes de identidad, T-06/T-19.
- Nota para una sesión futura, no una ambigüedad de esta: `ejes.json`
  (`04_glossary.py`, `docs/EJES.md`) ya no lo consume ningún JS de
  cliente —la arquitectura de secciones reactivas (`vista_explorador.js`)
  reescribió su propio texto "qué responde/no responde" en
  `SECCIONES`, en vez de leer el artefacto—, así que hay dos copias de la
  misma prosa metodológica que pueden divergir sin que nada lo note (ya
  divergieron parcialmente, verificado). No se tocó: es una decisión de
  arquitectura (¿leer `ejes.json` desde el cliente, o retirar el paso de
  build?), no un bug de una línea.

### Próximo paso recomendado

Ninguna acción de código pendiente de este cierre — las 17 correcciones
de esta auditoría están aplicadas, verificadas con las herramientas reales
del proyecto y listas para revisión antes de comitear. Confirmar que no
hay push paralelo a la rama antes de subir (patrón ya establecido en
sesiones anteriores). Cuando el usuario retome: la nota sobre
`ejes.json`/`SECCIONES` duplicados (arriba) es la única pieza no resuelta
que vale la pena decidir explícitamente, no ejecutar sin más contexto.

### Barrido adicional (continuación del mismo cierre)

Tras comitear lo anterior, una segunda pasada dirigida a áreas que los 5
agentes no habían recorrido —`design/`, `package.json`, `scripts/*.ps1`, y
un grep de las cifras "556"/"542" en todo el repo, no sólo en `docs/`—
encontró un hallazgo real más: `config/indicators.yml` (AU-03, h-index)
declaraba «50 de las 542 entidades publicadas» en su `advertencia` — un
número vivo, no histórico, que no se había corregido junto con el resto
del cluster porque este campo específico no lo lee ningún paso del build
(`grep -rn "AU-03" src/build/*.py` no devuelve nada: el texto real que ve
el lector vive duplicado en `paginas.js`/`docs/GLOSSARY.md`, hallazgo ya
documentado). Corregido a 538 de todas formas: es la fuente que un lector
directo de `config/indicators.yml` vería, aunque el build no la sirva hoy.

Las demás apariciones de "556"/"542" fuera de `docs/` resultaron ser
citas históricas deliberadas (comentarios en `common_build.py`,
`03_authors.py`, `05_verify_public_layer.py`, `paginas.js`,
`src/state/snapshot.py` que documentan un bug pasado como ejemplo, no una
cifra vigente) o la maqueta de diseño ya declarada como congelada a
propósito (`design/informe/`, decisión de una sesión anterior: "refrescarla
es una tarea de diseño... no una corrección de una línea"). No se tocaron.
`scripts/*.ps1` y `package.json` no mostraron ningún problema: todos los
`.py` que los scripts de PowerShell invocan existen, y `package.json`
declara playwright como única dependencia, correctamente marcada
`devDependencies` (README.md ya declara 0 dependencias en runtime).

`python3 src/build/build_all.py` + `06_assemble_site.py` + `node
src/verify/run_all.mjs`: limpio de nuevo tras este ajuste.

## Cierre: ejes.json deja de duplicarse — SECCIONES lee la fuente en vez de llevar su propia copia

### Contexto

El cierre anterior dejó declarada, sin tocar, la duplicación entre
`docs/EJES.md`/`ejes.json` (generado y verificado por `04_glossary.py`
contra los denominadores reales de cada indicador) y el texto
`pregunta`/`noResponde` que `vista_explorador.js`'s `SECCIONES` llevaba
copiado a mano — ya divergido en al menos un caso confirmado (producción).
El usuario, consultado explícitamente entre las dos direcciones posibles
(hacer que `SECCIONES` lea `ejes.json`, o retirar el paso de build que ya
no consumía nadie), eligió la primera: una sola fuente.

### Qué se hizo

`cabeceraSeccion(clave, titulo, eje)` (`vista_explorador.js`) gana un
tercer parámetro —la entrada de `ejes.json` para esa clave— y usa
`eje.responde`/`eje.no_responde` en vez de `SECCIONES[clave].pregunta`/
`.noResponde`, que se retiraron de las cuatro entradas de `SECCIONES`
(producción, impacto, colaboración, temática). Sin `eje` (archivo no
cargado, o clave sin panel) el bloque se omite, igual que antes.

Dos llamadores, mismo criterio en los dos:
- `src/build/prerender.mjs` vuelve a cargar `ejes.json` (se había retirado
  en el cierre anterior porque su único consumidor, la rama `modulos`
  muerta, ya no existía) y pasa `ejes[clave]`.
- `web/assets/js/paginas.js` lo pide con `c.cargar('ejes.json')` en la
  única rama donde `cabeceraSeccion` corre en el navegador (páginas sin
  pre-renderizar — hoy ninguna de las cuatro de sección cae ahí en
  producción, pero el camino queda correcto si alguna vez lo hace).

Verificado leyendo el HTML construido, no asumido: `dist/produccion.html`
pasó de mostrar el texto corto ("El volumen no mide calidad ni esfuerzo:
cuenta documentos indexados.") al texto completo de `docs/EJES.md` ("Qué
tan bueno es lo publicado. El volumen es una medida de actividad
indexada... la comparación entre ellas mide entonces la cobertura de la
base tanto como la actividad de las personas."). `04_glossary.py`'s
`verificar_denominadores()` sigue pasando sin cambios: no dependía de
`cabeceraSeccion`, sólo del atributo `data-indicadores` en el HTML.

### Verificación

`python3 src/build/build_all.py` + `06_assemble_site.py` (11 páginas, sin
avisos) + `node src/verify/run_all.mjs` (6/6 en verde, incluidos
`flujos.mjs` con 0 excepciones JS en todo el recorrido).

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-410 | `cabeceraSeccion()` lee el panel «responde/no responde» de `ejes.json`, y `SECCIONES` deja de llevar su propia copia | Las dos copias ya habían divergido (verificado); consultado explícitamente con el usuario entre esta opción y retirar `ejes.json`, eligió una sola fuente |

### Archivos modificados

```
web/assets/js/vista_explorador.js   cabeceraSeccion(clave, titulo, eje); SECCIONES sin pregunta/noResponde
src/build/prerender.mjs             vuelve a cargar ejes.json, lo pasa a cabeceraSeccion
web/assets/js/paginas.js            pide ejes.json en la rama sin pre-renderizar
```

### Próximo paso recomendado

Ninguno de código. Sigue pendiente, por elección explícita del usuario:
revisión caso por caso de los 129 pendientes de identidad
(`internal/revision_identidad.html`) — empieza en el próximo cierre de
esta misma sesión.

## Cierre: revisión caso por caso de los 128 pendientes de identidad — 46 confirmados con evidencia, 82 declarados sin evidencia suficiente, y un bug real de asignación descubierto en el camino

### Contexto

Con la autorización explícita del usuario ("los 129 pendientes completos"),
se revisó toda la cola de `internal/revision_identidad.html` con el mismo
rigor de evidencia que el repaso P-04 de una sesión anterior — nunca por
impresión, siempre contra el dato real. El caso «Varios Scopus ID» (Moya,
Patricia) ya estaba resuelto y diferido con razón documentada en un cierre
previo; no se reabrió (128 casos, no 129).

La cola NO es mayormente sobre fusionar identidades: agrupada por «cola»,
son en realidad seis mecanismos de evidencia distintos, cada uno con su
propio veredicto y su propio umbral:

| Cola | N | Pregunta que responde |
|---|---|---|
| Candidato de unidad académica por autoarchivo | 73 | ¿Es correcta la escuela que el autoarchivo declara para esta firma? |
| ORCID no verificable | 22 | Un ORCID ya publicado, sin nada contra qué contrastarlo — ¿se confirma o se retira? |
| Candidato por repositorio institucional | 11 | ¿Se asigna este ORCID nuevo, propuesto por coincidencia de nombre en DSpace? |
| Candidato por repositorio institucional (ambiguo) | 9 | Igual, pero el mismo ORCID lo reclaman 2+ firmas distintas |
| ORCID sin confirmar | 9 | Un ORCID ya publicado, cuyo titular no declara ninguna obra coincidente — ¿se confirma o se retira? |
| Candidato por inventario de autoarchivo | 4 | Igual que DSpace, otra fuente |

No se extrajo esto de la página HTML (el JSON incrustado en
`revision_identidad.html` sólo trae id/cola/firmas/previa, sin el
`contexto` rico): se llamó directamente a `build_review.cargar()` +
`perfiles()` + `casos()` desde Python, la misma función que genera la
página, para tener el mismo dato exacto con su evidencia completa
(`orcid_veredicto`, `dspace_veredicto`/`evidencia`,
`autoarchivo_veredicto`/`evidencia`, obras reales con DOI).

### Criterio aplicado, por cola

**Unidad académica por autoarchivo (73 → 44 confirmados).** El campo
declarado viaja en bruto (`D-345`, no se traduce al vocabulario oficial de
`config/matching_rules.yml`), y el propio vocabulario de veredictos deja
explícito que confirmar sólo registra la declaración —aplicarla al
pipeline sigue siendo un paso aparte, no automático—. Con ese umbral más
bajo (registrar lo que la propia firma autoarchivó de sí misma, no fusionar
identidades ni retirar nada publicado), se confirmaron las 44 firmas con
una sola escuela declarada (sin ambigüedad) que además no contradicen
ninguna unidad ya determinada por otra vía. Quedan pendientes 29: 24 con
**dos o más escuelas distintas** declaradas para la misma firma
(`build_review.py` ya lo advierte: "puede ser más de una persona... o
alguien que cambió de unidad — no se elige entre ellas"), y 5 que declaran
un **centro de investigación o unidad transversal**, no una escuela de
docencia (CIDOC ×3, Formación General ×2) — `REFERENCIA_UNIDADES_AUTOARCHIVO`,
ya escrita en una sesión anterior, deja explícito que esto es fuente
externa sin verificar contra finis.cl directamente; confirmar "es su
escuela" cuando la pregunta ni siquiera aplica (un centro no es una
escuela) habría sido una respuesta falsa a la pregunta correcta, así que
quedan declarados, no forzados a un sí o un no que no les corresponde.

**ORCID sin confirmar + ORCID no verificable (31 → 0 confirmados, 0
retirados).** Verificado sistemáticamente: de los 31, 22 no tienen ningún
cruce con DSpace ni autoarchivo (evidencia nula), 6 tienen
`sin_coincidencia` de ambas fuentes (ninguna corrobora, ninguna contradice)
y 3 tienen `confirma_indirecta` de DSpace — que significa que el registro
incluye ESE ORCID en una publicación, pero **a nombre de otro coautor**, no
de esta firma: no es evidencia dispositiva sobre esta persona (`D-341`), es
evidencia sobre alguien más en la misma publicación. Ninguno de los 31 pasa
el umbral que el proyecto ya fijó (evidencia dispositiva: mismo nombre +
mismo ORCID contra una obra propia en una fuente independiente). Los 31
quedan pendientes, sin excepción — no por falta de tiempo, sino porque la
evidencia automática disponible hoy genuinamente no alcanza para decidir
en ningún sentido.

**Candidatos nuevos de ORCID — DSpace + autoarchivo (24 → 1 firma
confirmada, con evidencia cruzada de dos fuentes independientes).** Mismo
Criterio B ya autorizado y aplicado el 2026-09-01 a un lote anterior: sólo
se confirma cuando el MISMO ORCID lo proponen, cada una por su cuenta, DOS
fuentes institucionales distintas (DSpace Y autoarchivo) para la misma
firma, sin ninguna otra alternativa declarada en ninguna de las dos. Sólo
«Olive F.» lo cumple (ORCID `0009-0000-0892-6746`, propuesto de forma
independiente por ambas fuentes). Las 22 filas restantes no se confirman:
o son de una sola fuente sin corroboración cruzada, o —peor, y esto es lo
que reveló el bug de abajo— el mismo ORCID lo reclaman varias firmas
distintas («0000-0002-0533-4531» lo piden a la vez Olive F., Pedreros C. y
Vergara K.: "el nombre no basta para elegir", literal en el propio código).

### Bug real encontrado y corregido: `asignaciones_confirmadas()` podía aplicar el ORCID equivocado

Al aplicar la confirmación de «Olive F.», el ORCID que terminó en
`data/enriched/authors_orcid.csv` fue **`0009-0005-8141-8912`** — no el
`0009-0000-0892-6746` confirmado con evidencia cruzada. Verificado antes de
seguir, no asumido: `internal/dspace_candidatos.csv` tiene TRES filas
distintas para «Olive F.» (tres ORCID candidatos distintos, uno de ellos
además reclamado por otras dos firmas). `asignaciones_confirmadas()`
construía `{nombre_en_fuente: orcid}` con un diccionario simple a partir de
esas filas — con tres filas para el mismo nombre, el diccionario se queda
con la ÚLTIMA, sin importar cuál de los tres `caso_id` fue el que la
revisión realmente confirmó. El bug es real y anterior a esta sesión (no
lo introdujo la revisión de hoy); simplemente nunca se había dado el caso
de confirmar una firma con más de un candidato de ORCID hasta ahora.

Alcance verificado, no supuesto: se comprobó CADA firma con veredicto
`misma` en las colas de candidatos (las de esta sesión y las de sesiones
anteriores) contra sus archivos de candidatos fuente — sólo «Olive F.»
tiene más de un candidato de ORCID distinto. Ninguna otra asignación ya
publicada está afectada.

Corregido: `_orcid_del_caso()` (nueva) extrae el ORCID directamente del
propio `caso_id` confirmado (que ya lo lleva literal:
`dspacecand-{nombre}-{orcid}`), y `asignaciones_confirmadas()` verifica
que ese par (nombre, ORCID) exista de verdad entre los candidatos antes de
aplicarlo — en vez de buscar sólo por nombre y quedarse con lo que sea que
haya quedado último en el archivo. Se agregó un caso de prueba nuevo que
reproduce exactamente este escenario (una firma con dos candidatos
distintos, sólo uno confirmado) para que no vuelva a pasar en silencio.
`python3 src/review/apply_decisions.py --test`: TODOS LOS CASOS OK. Se
re-aplicó después del fix: `authors_orcid.csv` ahora tiene el ORCID
correcto para «Olive F.», verificado línea por línea.

### Verificación

`python3 src/audit/run_all.py` (30 reglas, 0 bloqueantes) +
`src/build/build_all.py` + `06_assemble_site.py` (11 páginas, sin avisos)
+ `node src/verify/run_all.mjs` (6/6 en verde) tras aplicar. Las 44
`unidad_confirmada` no cambian nada publicado hoy (el paso de aplicación al
pipeline sigue sin construirse, como ya declaraba el propio vocabulario de
veredictos) — quedan registradas para cuando ese paso exista.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-411 | 44 candidatos de unidad académica por autoarchivo se confirman (`unidad_confirmada`) cuando declaran una sola escuela sin contradecir ninguna unidad ya determinada; los que declaran un centro de investigación o unidad transversal (CIDOC, CIPEF, Formación General) quedan pendientes en vez de forzar sí/no a una pregunta que no les aplica | El propio vocabulario de veredictos fija un umbral bajo para esta cola (registra la declaración, no la aplica al pipeline); confirmar una afiliación a un centro como si fuera una escuela sería una respuesta falsa a la pregunta correcta |
| D-412 | Los 31 casos de ORCID sin confirmar/no verificable quedan pendientes sin excepción, sin confirmar ni retirar ninguno | Ninguno tiene evidencia dispositiva de DSpace/autoarchivo (0 `confirma_directa`, 3 `confirma_indirecta` que corroboran a OTRO coautor, no a esta firma); el umbral de convicción ya fijado por `D-341` no se relaja para completar la cola |
| D-413 | Sólo «Olive F.» se confirma entre los 24 candidatos nuevos de DSpace/autoarchivo, por acuerdo cruzado de dos fuentes independientes (mismo Criterio B del 2026-09-01) | Es el único caso del lote con el mismo ORCID propuesto de forma independiente por ambas fuentes sin alternativa declarada; los demás son de una sola fuente o tienen el mismo ORCID reclamado por varias firmas |
| D-414 | `asignaciones_confirmadas()` toma el ORCID del `caso_id` confirmado, no de una búsqueda por nombre en el archivo de candidatos | Bug real descubierto al aplicar «Olive F.»: con tres candidatos de ORCID distintos para la misma firma, la búsqueda por nombre aplicaba el último del archivo, no el confirmado — un ORCID equivocado publicado con la etiqueta de revisión humana |

### Archivos modificados

```
internal/identity_decisions.csv       46 filas: 44 unidad_confirmada + 2 misma (Olive F.)
src/review/apply_decisions.py         _orcid_del_caso(), asignaciones_confirmadas() por par (nombre,orcid), +1 caso de prueba
config/identidades_consolidadas.yml, config/firmas_e09_resueltas.yml,
config/orcid_revisado.yml             regenerados (fecha_de_aplicacion 2026-09-02)
data/enriched/authors_orcid.csv       +1 (Olive F., ORCID correcto tras el fix)
docs/BUILD_VERIFICATION.md            regenerado (tamaño de artefactos)
STATE.md, docs/DECISIONS.md           regenerados
```

### Supuestos descartados

- Que «confirma_indirecta» de DSpace/autoarchivo era evidencia suficiente
  para confirmar un ORCID: significa que el registro incluye ese ORCID a
  nombre de OTRO coautor, no de la firma en revisión — no es evidencia
  sobre esta persona.
- Que un solo candidato de nombre (sin corroboración cruzada) bastaba para
  asignar un ORCID nuevo: el propio código ya lo advierte ("el nombre no
  basta para elegir") y el criterio ya autorizado exige dos fuentes
  independientes de acuerdo.
- Que aplicar `asignaciones_confirmadas()` sobre una firma con múltiples
  candidatos aplicaría el correcto: verificado que no era así (bug real,
  corregido).

### Ambigüedades abiertas

- Las de siempre, sin cambios: la fusión de "Varios Scopus ID" (Moya,
  Patricia) sigue diferida; el mecanismo de qué debe hacer un veredicto
  "distintas" en esa cola sigue sin resolver (Hallazgo 2 de una auditoría
  anterior).
- Nueva: 82 casos quedan genuinamente sin evidencia suficiente (29 de
  unidad académica, 31 de verificación de ORCID, 22 de candidatos nuevos
  sin corroboración cruzada) — no son pendientes por falta de revisión,
  son pendientes porque se revisaron y la evidencia automática disponible
  hoy no alcanza. Subir esta cobertura exigiría más fuentes (más
  repositorios, más autoarchivo) o una revisión manual publicación por
  publicación fuera del alcance de esta sesión.
- «Moya P.» (candidato de unidad académica, Odontología) podría o no ser
  la misma persona que «Moya, Patricia» (Varios Scopus ID, aún diferida) —
  no se investigó esa conexión: son preguntas distintas (unidad vs.
  identidad) y mezclarlas sin evidencia sería exactamente el error que
  este proceso evita. Queda anotado para quien retome el caso de identidad.

### Próximo paso recomendado

Ninguna acción de código pendiente. La cola de identidad queda en el mismo
estado honesto que el resto del proyecto ya practica: lo que se pudo
confirmar con evidencia real, confirmado; lo que no, declarado pendiente
con la razón exacta por la que sigue sin decidirse — no forzado para
vaciar la cola.

---

## Cierre: `PD-02` — la cola OpenAlex confirmada (Nivel V) se publica como segundo indicador de "producción fuera de Scopus"

### Contexto

El usuario pidió agregar el listado de otra Facultad al mecanismo de
`produccion-ampliada.html`. Antes de tocar código se preguntó, vía
`AskUserQuestion`, cuál Facultad y de dónde saldría su fuente real (otro
sitio con la misma API de WordPress, o un archivo) — `CLAUDE.md` prohíbe
suponer disponibilidad de una fuente sin confirmarla. El usuario descartó
la pregunta y, en su lugar, dio una instrucción distinta: **"Integra todo
el contenido recuperado desde API's en un nuevo apartado que indique la
producción total fuera de scopus"**.

Investigado qué contenido "recuperado desde APIs" podía significar
razonablemente producción fuera de Scopus:

- `facultad_medicina_publicaciones` (wp-json) — ya integrado como `PD-01`.
- `internal/openalex_cobertura.csv` (`openalex_api`, V2-26) — 414
  candidatos que OpenAlex atribuye a la institución y el universo no
  tiene, de los cuales **20 ya pasaron por revisión humana y quedaron
  `CONFIRMADO_PRODUCCION_UFT`** (`internal/revision_cobertura_openalex.html`,
  `apply_openalex_review.py`) y **394 siguen `PENDIENTE_REVISION_HUMANA`**.
  El resto de las fuentes API del proyecto (Crossref, ORCID, ROR, Scopus
  API) no son listados de producción: son verificación de identidad o de
  fecha de corte, ninguna aporta obras nuevas.

Esto es exactamente el escenario que `docs/METODOLOGIA_FUERA_DE_SCOPUS.md`
había dejado planteado el 2026-09-02 más temprano en esta misma sesión (con
otro nombre de trabajo): esa cola es **Nivel V** (verificado obra por
obra), distinto de `PD-01` (**Nivel D**, declarado), y §4 de ese documento
decía explícitamente que publicarla como indicador "es una decisión de
alcance aparte, explícita y posterior, que le corresponde al usuario" —
tentativamente nombrada ahí mismo `PD-02`. La instrucción del usuario ES
esa autorización explícita.

### Qué se construyó

`src/build/09_produccion_declarada.py` (ya existente para `PD-01`) se
extendió para leer también `internal/openalex_cobertura.csv`, filtrar
`resolucion == CONFIRMADO_PRODUCCION_UFT`, aplicar la misma ventana
temporal 2023-2025, y agregar por año (nunca por Facultad: esta evidencia
es por autor, no una declaración editorial de una unidad, así que no entra
al mecanismo `corpus_paralelo_declarado` de `PD-01`). Nuevo indicador
`PD-02` en `config/indicators.yml`, categoría `declarado` (compartida con
`PD-01`), `solo_recuento: true`, ausente de `kpis_portada` por el mismo
motivo que `PD-01`.

**Verificado antes de sumar cifras, no asumido:** 3 de los 20 DOI
confirmados por OpenAlex ya estaban en el listado que Medicina declara en
su propio sitio (`10.1097/gme.0000000000002620`,
`10.1007/s12565-025-00855-0`, `10.35366/112734`) — los tres, dentro de la
ventana 2023-2025 de `PD-01`. Sumar `PD-01` + `PD-02` sin deduplicar habría
contado esas tres obras dos veces. El total combinado
(`total_fuera_de_scopus`, publicado al inicio de `produccion-ampliada.html`)
une por DOI normalizado y resta la intersección: **83 + 20 − 3 = 100**. No
es un tercer indicador con entrada propia en `sources.yml` — es aritmética
declarada sobre `PD-01` y `PD-02`, documentada como tal para que nadie la
repita mal.

Los 394 casos `PENDIENTE_REVISION_HUMANA` se publican como cifra de
transparencia en la propia sección de `PD-02` ("Pendientes de revisión"),
con el mismo principio que ya rige `PD-01` para fuera-de-ventana/sin-año:
nunca se cuentan como producción confirmada, nunca se ocultan.

`vista.js::produccionDeclarada()` se reestructuró en tres bloques: total
combinado (arriba), subsección "Declarada por las Facultades" (`PD-01`,
sin cambios de contenido, sólo de encabezado), subsección nueva
"Confirmada por revisión de cobertura OpenAlex (V2-26)" (`PD-02`, con su
propia tabla año → N y su propio sello de procedencia). Ningún otro punto
de integración del sitio cambió: `produccion-ampliada.html`,
`prerender.mjs`, `paginas.js`, `core.js`, `estructura.mjs`, `contraste.mjs`
ya estaban registrados desde la implementación de `PD-01` y siguen
sirviendo sin modificación — sólo consumen un JSON con más campos.

### Verificación

`python3 src/audit/run_all.py` (29/30, la única falla es `E-06`
preexistente y no relacionada) + `src/build/build_all.py` (build 09
imprime ambos bloques y el total: "100 (83 PD-01 + 20 PD-02 - 3 en ambas)")
+ `06_assemble_site.py` (`produccion-ampliada.html` 10.9 KB, sin avisos) +
`node src/verify/run_all.mjs` (6/6 en verde). Captura de pantalla con
Playwright en tema claro y oscuro: las cuatro cifras de `PD-02`
(evaluados/confirmadas/en ventana/pendientes) y el total combinado se ven
correctamente, sin errores de consola. `indicadores.html` lista `PD-02`
bajo "Producción declarada (fuera de Scopus)" con fuente "OpenAlex,
confirmado por revisión humana (no Scopus)" — no "Scopus · SciVal".

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-415 | La cola de revisión de cobertura OpenAlex (V2-26) se publica como indicador propio `PD-02`, sólo para los casos con veredicto `CONFIRMADO_PRODUCCION_UFT` | Autorización explícita del usuario en esta sesión, exactamente la condición que `docs/METODOLOGIA_FUERA_DE_SCOPUS.md` §4 y `docs/V2_BACKLOG.md` §8 dejaban pendiente; los 394 casos sin revisar NUNCA se cuentan como confirmados |
| D-416 | `PD-02` se agrega sólo por año, nunca por Facultad, y no entra al mecanismo `corpus_paralelo_declarado` de `PD-01` | Es evidencia por autor (OpenAlex + revisión humana), no una declaración editorial de una unidad académica — forzarla a la forma Facultad × año de `PD-01` habría inventado una relación que la fuente no tiene |
| D-417 | El total combinado "producción fuera de Scopus" es la unión por DOI de `PD-01` y `PD-02`, sin entrada propia en `config/sources.yml` | Verificado que 3 DOI aparecen en ambas fuentes; sumarlas sin deduplicar habría contado la misma obra dos veces. Es aritmética sobre dos indicadores ya sourceados, no un tercer indicador |
| D-418 | Los casos `PENDIENTE_REVISION_HUMANA` de la cola OpenAlex se publican como cifra de transparencia junto a `PD-02`, nunca como producción confirmada ni ocultos | Mismo principio ya aplicado a fuera-de-ventana/sin-año en `PD-01`: ocultar cuánto falta por revisar sería tan engañoso como inflar el recuento con lo no confirmado |

### Archivos modificados

```
config/indicators.yml                 PD-02 (categoría declarado, solo_recuento)
src/build/common_build.py             FUENTE_POR_INDICADOR["PD-02"]
src/build/09_produccion_declarada.py  lee internal/openalex_cobertura.csv,
                                       agrega PD-02 por año, calcula total_fuera_de_scopus
web/assets/js/vista.js                produccionDeclarada(): tres bloques (total, PD-01, PD-02)
docs/FUENTES_Y_APIS.md                §2.7 nueva; §3.1 actualizada
docs/DATA_MODEL.md                    "Corpus paralelo declarado" describe PD-01 y PD-02
docs/METODOLOGIA_FUERA_DE_SCOPUS.md   Nivel V marcado como publicado (PD-02), no hipotético
docs/V2_BACKLOG.md                    §8 marcada implementada; fila V2-26 actualizada
STATE.md, docs/DECISIONS.md           regenerados
```

### Supuestos descartados

- Que "todo el contenido recuperado desde APIs" incluía fuentes como
  Crossref, ORCID o ROR: revisadas todas las entradas de `sources.yml` con
  `tipo: api` — ninguna otra es un listado de producción; son verificación
  de identidad, de fecha de corte, o de identidad institucional.
- Que los 394 casos `PENDIENTE_REVISION_HUMANA` podían aproximarse o
  estimarse como producción probable para dar una cifra "más completa":
  se descartó explícitamente — publicar un candidato no revisado como
  producción confirmada sería inventar el dato que `CLAUDE.md` prohíbe.
- Que bastaba con sumar `PD-01` y `PD-02` sin verificar solapamiento: se
  comprobó el cruce de DOI antes de publicar el total y se encontraron 3
  casos reales que habrían duplicado el recuento.

### Ambigüedades abiertas

- Los 394 casos pendientes de revisión de V2-26 no se resolvieron en esta
  sesión — `PD-02` crecerá cuando avance esa revisión (correr de nuevo
  `apply_openalex_review.py` y luego `09_produccion_declarada.py`).
- La evidencia de Crossref (`V2-26 bis`, `internal/openalex_cobertura_crossref.csv`)
  sigue sin usarse como refuerzo automático de ninguna confirmación — apoya
  la revisión humana, no decide por nadie (`docs/V2_BACKLOG.md` §8).
- Sigue sin construirse un tercer Nivel (o una regla explícita) para una
  fuente que no encaje limpiamente en D o V, si aparece — el checklist de
  `docs/METODOLOGIA_FUERA_DE_SCOPUS.md` §3 ya lo anticipa como posibilidad.

### Próximo paso recomendado

Ninguna acción de código pendiente. Si en el futuro se agrega el listado
propio de otra Facultad (la pregunta original que esta sesión no llegó a
responder porque el usuario redirigió el pedido), el mecanismo
`corpus_paralelo_declarado` de `PD-01` ya está listo para recibirla sin
tocar `src/build/`: sólo hace falta un conector que siga el esquema
documentado en `facultad_medicina_publicaciones.py` y su entrada en
`config/sources.yml`.

---

## Cierre: `PD-03` — el repositorio institucional cubre todas las Facultades, con la unidad en bruto por fila

### Contexto

La pregunta original que el cierre anterior dejó abierta ("agreguemos el
listado de otra Facultad") volvió: **"dale, avancemos con el listado de
otra Facultad"**. Se preguntó, vía `AskUserQuestion`, cuál Facultad y de
dónde saldría su fuente (otro sitio con la misma API de WordPress, o un
archivo) — con el aviso explícito de que el acceso a
`facultadmedicina.finis.cl` desde este entorno seguía bloqueado (probado
con `curl`, `CONNECT tunnel failed, response 403`, mismo hallazgo que la
sesión que corrió ese conector por primera vez). El usuario contestó, en
texto libre, algo distinto de las opciones ofrecidas: **"Todas. Utiliza el
repositorio institucional"** y **"Documentación repositorio institucional"**.

### Investigación antes de escribir código

"Repositorio institucional" nombra, literalmente, la fuente
`dspace_repositorio` de `config/sources.yml`. Verificado (no asumido) antes
de diseñar nada:

- El volcado DSpace (`data/raw/Inventario_Repositorio_Institucional_UFT.csv`,
  3.271 filas, 154 columnas) **no tiene Facultad usable**: `collection` es
  un handle opaco (`20.500.12254/2311`, sin nombre en ningún lado del
  export) y `dc.uft.carrera` está vacía en 3.267 de 3.271 filas. Mezcla
  además tesis (464 filas) con producción académica real —a diferencia de
  la hoja de autoarchivo, que sólo trae artículo/capítulo/libro/ponencia.
- `autoarchivo_biblioteca` (`data/raw/Inventario_Repositorio_Autoarchivo.xlsx`,
  hoja AUTOARCHIVOS, 808 filas) **sí sirve**: trae DOI (806/808), año
  (808/808), título y la Facultad o Escuela que biblioteca asignó a cada
  obra, fila por fila, para toda la institución — pero ese campo de
  Facultad/Escuela viene declarado EN BRUTO, exactamente como
  `config/sources.yml` ya advertía desde antes de esta sesión.

De los 35 valores distintos que trae ese campo, la mayoría no tiene una
relación escuela→Facultad validada institucionalmente hoy:
`config/matching_rules.yml` sólo confirma 5 escuelas en su `jerarquia`
(Kinesiología, Nutrición y Dietética, Enfermería, Ciencias de la Familia,
Ingeniería Civil Industrial), más las que su `vocabulario` (regla I-07,
validado el 2026-08-26) resuelve directo a nivel de Facultad (Medicina,
Odontología, Psicología, Derecho, Arquitectura, Historia). Forzar el resto
—CIDOC, CIPEF, Formación General, Periodismo, Literatura, Filosofía,
Publicidad, Ingeniería comercial, Ingeniería civil informática, Diseño,
Arte, y otro puñado más chico— a una Facultad adivinada habría sido
inventar una relación institucional, exactamente lo que `CLAUDE.md`
prohíbe. `REFERENCIA_UNIDADES_AUTOARCHIVO` (`src/review/build_review.py`,
de una sesión anterior) ya marcaba casi todos esos casos "fuente externa,
sin verificar en finis.cl directamente" — sólo dos ("Educación básica",
"Educación parvularia") están confirmados ahí DIRECTAMENTE contra finis.cl.

### Qué se construyó

Nuevo conector `src/enrich/autoarchivo_produccion.py`: por cada fila,
`unidad_declarada` (la cadena en bruto, siempre) y `facultad` (sólo si la
relación está validada, si no cadena vacía — nunca inferida). La resolución
reutiliza EXACTAMENTE `common.canonical_academic_unit()` +
`common.facultad_de()` de `src/audit/common.py` — las mismas dos funciones
que ya usa `P-07` en producción, no una copia nueva — más un puñado de
alias explícitos y documentados uno por uno: dos truncados de escuelas ya
confirmadas ("Nutrición"→Nutrición y Dietética, "Familia"→Ciencias de la
Familia) y los dos ÚNICOS casos de `REFERENCIA_UNIDADES_AUTOARCHIVO`
confirmados contra finis.cl. El DOI de esta hoja es texto libre (decenas de
valores tipo "artículo sin doi"/"libro no tiene doi" en la misma columna,
no un campo estructurado): se validó por forma (`10\.\d{4,9}/\S+`), no sólo
por "no vacío" — de otro modo esas frases se habrían contado como DOI
reales.

`src/build/09_produccion_declarada.py` gana un tercer bloque, `PD-03`, que
NO reutiliza el mecanismo `corpus_paralelo_declarado` de `PD-01` (que exige
Facultad siempre canónica): lee `autoarchivo_produccion.json` directo,
deduplica por `(facultad o unidad_declarada, DOI)`, separa
`en_universo_scopus`/ventana igual que `PD-01`, y agrega por Facultad × año
SÓLO entre las filas con Facultad validada. Las filas sin Facultad validada
(57 en ventana) se cuentan aparte, por unidad declarada, en su propia
tabla de transparencia — nunca ocultas, nunca forzadas.

**Verificado antes de publicar el total, no asumido:** hay solapamiento
real entre las tres fuentes, no sólo entre pares — Medicina aparece
declarada en su propio sitio (`PD-01`) Y autoarchivada por sus propios
autores (`PD-03`), y algunas confirmaciones de V2-26 (`PD-02`) también
están autoarchivadas. El total combinado (`total_fuera_de_scopus`) pasó de
unir 2 fuentes por DOI a unir 3, restando 19 apariciones repetidas entre
ellas antes de sumar: **209** = 83 (`PD-01`) + 20 (`PD-02`) + 125 (`PD-03`)
− 19.

`vista.js::produccionDeclarada()` gana una tercera subsección
("Autoarchivada en el repositorio institucional"), con dos tablas: Facultad
× año (sólo unidades validadas) y unidad declarada × N (sin Facultad
validada) — la segunda tabla es la parte más importante de este cierre
metodológicamente: dice explícitamente, con cifras reales, cuánto de este
corpus NO se pudo agregar por Facultad y por qué, en vez de forzarlo o
callarlo. `PD-03` en `config/indicators.yml` (categoría `declarado`,
`solo_recuento: true`).

### Verificación

`python3 src/enrich/autoarchivo_produccion.py --test` (11 casos, incluye
el mapeo válido/no-válido y la validación de forma del DOI) +
`python3 src/audit/run_all.py` (29/30, misma falla preexistente E-06,
no relacionada) + `build_all.py` (build 09 imprime los tres bloques y el
total: "209 (83 PD-01 + 20 PD-02 + 125 PD-03 - 19 repetidas entre fuentes)")
+ `06_assemble_site.py` (`produccion-ampliada.html` 16.2 KB, sin avisos) +
`node run_all.mjs` (6/6). Captura Playwright en claro/oscuro: las tres
secciones se ven completas, con la tabla de unidades sin mapeo visible y
cero errores de consola. `indicadores.html` lista `PD-03` bajo "Producción
declarada (fuera de Scopus)" con fuente "Repositorio institucional,
autoarchivo (no Scopus)".

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-419 | El volcado DSpace (`dspace_repositorio`) no se usa para `PD-03`; se usa `autoarchivo_biblioteca` en su lugar | Verificado que DSpace no tiene Facultad usable (`collection` es un handle opaco, `dc.uft.carrera` vacía en 99,9% de las filas) y mezcla tesis con producción académica; autoarchivo trae Facultad/Escuela, DOI, año y título por fila, y sólo producción académica |
| D-420 | La resolución de Facultad para `PD-03` reutiliza `common.canonical_academic_unit()`/`facultad_de()` (las mismas funciones de `P-07`) más un alias explícito de 5 casos ya validados en sesiones anteriores; el resto de las ~35 unidades en bruto NO se mapea | Cualquier mapeo nuevo, no reutilizado de una fuente ya validada institucionalmente, habría sido inventar una relación escuela→Facultad — la misma regla que `REFERENCIA_UNIDADES_AUTOARCHIVO` ya aplicaba distinguiendo "confirmado contra finis.cl" de "fuente externa sin verificar" |
| D-421 | Las publicaciones autoarchivadas sin Facultad validada (57 en ventana) se publican por unidad declarada en bruto, en su propia tabla, nunca forzadas a una Facultad ni ocultas | Mismo principio que "fuera de ventana"/"pendientes de revisión" en `PD-01`/`PD-02`: un límite de cobertura se declara, no se disimula agregando de más o quedándose callado |
| D-422 | El total combinado de la página pasa de unión por DOI de 2 fuentes a unión de 3 (`PD-01`+`PD-02`+`PD-03`) | Verificado antes de publicar: hay solapamiento real entre las tres, no sólo entre pares (Medicina declarada Y autoarchivada); sumar sin deduplicar habría contado la misma obra hasta tres veces |

### Archivos modificados

```
src/enrich/autoarchivo_produccion.py   nuevo — conector, mapeo validado, --test
src/build/09_produccion_declarada.py   bloque PD-03, _deduplicar() generalizado
                                        con clave_unidad, total de 3 fuentes
config/indicators.yml                  PD-03 (categoría declarado, solo_recuento)
src/build/common_build.py              FUENTE_POR_INDICADOR["PD-03"]
config/sources.yml                     autoarchivo_biblioteca: conector/aporta/salida
                                        actualizados con el nuevo uso
web/assets/js/vista.js                 produccionDeclarada(): subsección PD-03,
                                        total combinado a 3 fuentes
docs/FUENTES_Y_APIS.md                 §2.8 nueva
docs/DATA_MODEL.md                     "Corpus paralelo declarado" describe las 3
docs/METODOLOGIA_FUERA_DE_SCOPUS.md    matiz de granularidad parcial dentro de
                                        Nivel D; Regla 2/4 actualizadas
docs/V2_BACKLOG.md                     §8 ampliada con la segunda ronda
data/enriched/autoarchivo_produccion.json  nuevo — salida real del conector
STATE.md, docs/DECISIONS.md            regenerados
```

### Supuestos descartados

- Que el volcado DSpace serviría para esto sin más trabajo: verificado que
  no tiene Facultad usable antes de intentar construir nada sobre él.
- Que agrupar los ~35 valores en bruto por parecido de nombre ("Psicología"
  suena a Educación, "Arquitectura" suena a Arquitectura y Diseño") bastaba
  para publicarlos como Facultad: descartado — sólo cuenta lo que YA está
  validado en otro archivo del proyecto (jerarquia, vocabulario I-07,
  finis.cl confirmado), nada nuevo se validó en esta sesión por primera vez.
- Que "Arte" (5 filas) era lo mismo que "Facultad de Artes Visuales" del
  vocabulario: descartado por no ser una variante exacta — queda sin
  mapear, igual que "Diseño".
- Que el total combinado sólo necesitaba deduplicar PD-01 contra PD-02 (ya
  hecho en el cierre anterior): descartado al verificar que PD-03 también
  solapa con ambas — la unión se generalizó a las tres fuentes, no se
  agregó PD-03 como una suma directa.

### Ambigüedades abiertas

- Las 57 publicaciones sin Facultad validada (y las 199 de todo el
  historial de la hoja, dentro y fuera de ventana) quedan sin resolver:
  traducir "CIDOC"/"Periodismo"/"Arquitectura"/etc. a la jerarquía oficial
  sigue siendo el mismo trabajo institucional que exigió `T-02`, y esta
  sesión no lo hizo por su cuenta — sólo reutilizó lo que ya estaba
  confirmado.
- La pregunta que el cierre "Producción ampliada" original planteaba —el
  listado propio de OTRA Facultad en su propio sitio, como `PD-01`— sigue
  sin responder: `facultadmedicina.finis.cl` fue el único caso probado, y
  el acceso de red a `finis.cl` sigue bloqueado desde este entorno. El
  mecanismo `corpus_paralelo_declarado` sigue listo para recibirla cuando
  exista.

### Próximo paso recomendado

Ninguna acción de código pendiente. Si se quiere aumentar la cobertura de
`PD-03` por Facultad, el paso siguiente es institucional, no técnico:
alguien con autoridad para confirmarlo debe decidir a qué Facultad
pertenecen las ~30 unidades que hoy quedan sin mapeo (empezando por las de
mayor volumen: Ingeniería civil informática, Ingeniería comercial,
Formación General, CIDOC, Periodismo, CIPEF, Diseño) y agregar esa
confirmación a `config/matching_rules.yml` — este conector la recogería
sin cambios de código, igual que ya recoge las que sí están validadas.

---

## Cierre: Crossref para financiamiento — la fuente complementaria que `X-03` ya pedía, implementada y probada, sin poder ejecutarse aquí

### Contexto

**"Integra API Crossref."** El proyecto ya usa Crossref para dos preguntas
(ORCID declarado por el editor; evidencia de afiliación para la cola
OpenAlex, V2-26 bis) — no era obvio qué dato NUEVO pedía el usuario. Se
preguntó, vía `AskUserQuestion`, entre las tres ampliaciones que
`docs/FUENTES_Y_APIS.md` §3.4 ya dejaba planteadas sin construir
(financiamiento, acceso abierto contrastado, referencias/citación interna)
— el usuario delegó la elección: **"No estoy seguro/a — elegí vos"**.

### Por qué financiamiento, y no las otras dos

Investigado antes de elegir, no por preferencia:

- **Acceso abierto**: Crossref no tiene un campo limpio de "acceso
  abierto" (sólo URLs de licencia que exigen heurística) —
  `docs/FUENTES_Y_APIS.md` §3.5 ya identificaba Unpaywall como la
  herramienta correcta para esa pregunta específica. Elegirla habría sido
  duplicar un trabajo que el proyecto ya tiene mejor resuelto en otro
  lado.
- **Referencias**: la de mayor alcance técnico (una estructura de grafo
  nueva, comparable a C-05) — demasiado grande para "elegí vos" sin
  confirmar el diseño con el usuario primero.
- **Financiamiento**: al revisar `config/indicators.yml` se encontró que
  **ya existe** `X-03` ("Indicadores de financiamiento"), sin publicar,
  con razón explícita — "Cobertura 37,4 %: insuficiente para reportar sin
  sesgo" — y `que_falta` diciendo, literalmente, "Fuente complementaria de
  financiamiento". Verificado: esa cobertura sale de `Funding
  Details`/`Funding Texts`, campos reales del export nativo de Scopus (306
  de 818 filas), que **ningún paso del pipeline extraía** — no llegan a
  `publications_universe.csv` (confirmado antes de escribir código). Elegir
  esta opción no es inventar una pregunta nueva: es construir exactamente
  la pieza que el proyecto ya había identificado como faltante, con su
  propio umbral de decisión ya declarado.

### Qué se construyó

Nuevo conector `src/enrich/crossref_financiamiento.py`, mismo patrón de
caché/errores que `openalex_cobertura_crossref.py` (que sí corrió, en una
sesión con acceso de red real). Por cada publicación con DOI: extrae por
fin `Funding Details` del export de Scopus (texto libre, separado por
`;`), y consulta Crossref para traer `message.funder` (nombre +
identificador del Crossref Funder Registry + números de proyecto). Las dos
cadenas se reportan una al lado de la otra, **sin fusionarlas**: decidir
que "CONICYT" y su sucesora "ANID" son la misma entidad es el mismo tipo de
normalización de vocabulario institucional que
`unidad_academica.vocabulario` no hace sin validación, y este conector
sigue el mismo principio.

**No pudo ejecutarse de verdad.** Antes de darlo por bloqueado, se
comprobó: `curl` directo a `api.crossref.org` devuelve `CONNECT tunnel
failed, response 403`, y `curl "$HTTPS_PROXY/__agentproxy/status"`
confirma que es el gateway del proxy rechazando la conexión por política
("policy denial"), no un error transitorio ni un problema de configuración
local que se pudiera corregir desde la sesión. Correr el conector de
verdad (`--limit 3`) reprodujo el mismo 403 tres veces y, correctamente,
**no escribió ningún archivo** ("Sin resultados") en vez de dejar una
salida vacía o a medias.

`config/sources.yml` gana `crossref_financiamiento_api`, con
`ejecutada: false` explícito (primer caso de esta bandera en el archivo;
hasta ahora las tres fuentes API que alguna vez estuvieron sin ejecutar ya
corrieron). `config/indicators.yml` -> `X-03` **no cambia su
`publicar`/`estado`** — seguiría siendo inventar un resultado publicar algo
sin la cifra real de cobertura combinada —; sólo su `que_falta` se
actualiza para decir que la fuente complementaria ya está implementada y
probada, pendiente de una corrida real.

### Verificación

`python3 src/enrich/crossref_financiamiento.py --test`: 11/11
comprobaciones (parseo de `Funding Details`, extracción de `funder` de
Crossref, casos sin financiamiento en ninguna fuente, casos donde sólo una
de las dos declara financiamiento, normalización de DOI). Corrida real
intentada y documentada como bloqueada (ver arriba). `python3
src/audit/run_all.py`/`build_all.py`/`06_assemble_site.py`/`node
run_all.mjs`: sin cambios de comportamiento — ningún paso del build
consume todavía `data/enriched/crossref_financiamiento.csv` (no existe:
la corrida real no produjo salida), así que el sitio publicado no cambia
con este cierre.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-423 | De las tres ampliaciones de Crossref propuestas (financiamiento, acceso abierto, referencias), se implementa financiamiento | Es la única que resuelve una brecha YA documentada (`X-03`, `que_falta: "Fuente complementaria de financiamiento"`) en vez de proponer un indicador nuevo sin precedente; acceso abierto duplicaría el rol ya asignado a Unpaywall (§3.5) y referencias excede el alcance de una elección delegada sin diseño previo |
| D-424 | `crossref_financiamiento.py` reporta el financiador de Scopus y el de Crossref como dos cadenas separadas, sin fusionarlas | Normalizar nombres de financiador entre fuentes (p. ej. CONICYT/ANID, la misma entidad renombrada) es el mismo trabajo de vocabulario institucional que `unidad_academica.vocabulario` exige validar antes de aplicar — no una decisión que tome un conector por su cuenta |
| D-425 | `X-03` permanece sin publicar (`publicar: false` sin cambios); sólo se actualiza `que_falta` | La fuente complementaria está implementada pero no ejecutada (red bloqueada, confirmado con `curl` y el estado del proxy) — no hay cifra real de cobertura combinada, y publicar sin ella sería inventar un resultado, exactamente lo que `CLAUDE.md` prohíbe |

### Archivos modificados

```
src/enrich/crossref_financiamiento.py   nuevo — conector, --test (11 casos)
config/sources.yml                      crossref_financiamiento_api (ejecutada: false)
config/indicators.yml                   X-03.que_falta actualizado (sin cambiar publicar/estado)
docs/FUENTES_Y_APIS.md                  §3.4 y tabla de plataformas actualizadas
STATE.md, docs/DECISIONS.md             regenerados
```

### Supuestos descartados

- Que "Integra API Crossref" pedía ampliar alguno de los conectores
  Crossref ya existentes (ORCID, evidencia V2-26 bis): investigado y
  descartado — ninguno de los dos trae financiamiento, y el usuario
  delegó explícitamente la elección de QUÉ dato nuevo traer.
- Que bastaba con el campo `Funding Details` de Scopus, ya en el export,
  para levantar `X-03` sin tocar Crossref: descartado porque el pedido
  explícito era integrar Crossref, y porque la razón documentada de
  `X-03` (cobertura insuficiente) pide una fuente COMPLEMENTARIA, no sólo
  extraer lo que ya había.
- Que al no poder ejecutar la consulta convenía igual estimar o simular
  una cobertura combinada para poder publicar `X-03`: descartado sin
  ambigüedad — sería inventar el dato que este proyecto existe para no
  inventar.

### Ambigüedades abiertas

- La cobertura combinada real (Scopus + Crossref) sigue sin medirse. Hasta
  que alguien corra `crossref_financiamiento.py` desde una máquina con
  acceso a `api.crossref.org`, no hay forma de saber si `X-03` cruza el
  umbral que hoy lo bloquea — ni de si publicar financiamiento por
  proyecto/financiador es, además, una decisión de alcance que alguien
  deba tomar aparte, incluso con cobertura suficiente.
- Igual que con `facultadmedicina.finis.cl` y `dspace`/`autoarchivo`, el
  patrón se repite: este entorno de ejecución no tiene salida a la mayoría
  de los dominios externos reales del proyecto. Cualquier integración de
  API nueva debería anticiparse a esto desde el diseño (caché,
  `--limit`/`--test`, abortar sin escribir nada a medias), como ya lo hace
  ésta.

### Próximo paso recomendado

Ninguna acción de código pendiente. El paso siguiente es de infraestructura,
no de diseño: correr `python3 src/enrich/crossref_financiamiento.py` desde
una máquina con acceso real a `api.crossref.org`, revisar la "cobertura
combinada" que imprime al final, y decidir con esa cifra real si `X-03`
cruza el umbral para publicarse — y si publicarlo, además, requiere su
propia decisión de alcance sobre qué mostrar (financiador, número de
proyecto, o sólo el booleano "tiene financiamiento declarado").

---

## Cierre: bug real encontrado al mostrar `indicadores.html` — el índice lateral flotaba sobre el contenido en escritorio

### Contexto

Pedido: "Regenera indicadores.html y mostrame que quedó bien" (confirmar
visualmente `PD-01`/`PD-02`/`PD-03`/`X-03` tras los cierres anteriores).
Al capturar la página con Playwright en ≥1040px de ancho apareció un
defecto real, sin relación con el contenido agregado hoy: el índice "En
esta página" (`<nav class="rail">`) queda fijo (`position: sticky`) y
**flota semitransparente sobre las secciones** a medida que se hace
scroll, en vez de vivir en una columna al costado — visible en la captura
que se le mostró al usuario antes de preguntar si corregirlo. Confirmado
"sí, arreglalo".

### Diagnóstico

`web/assets/css/app.css` ya declara una clase `.disposicion`
(`display: grid; grid-template-columns: var(--rail) minmax(0, 1fr)` a
≥1040px) diseñada exactamente para envolver `[.rail, contenido]` en dos
columnas — pero **ningún código de armado de página la aplicaba**:
`vista.js::catalogo()` (el índice de `indicadores.html`) devolvía
`<nav class="rail">` y las secciones como hermanos sueltos, sin ningún
contenedor. Sin una columna que lo acote, `.rail` (`position: sticky`) se
vuelve un bloque de ancho completo que se pega a `top: 7.4rem` y tapa lo
que sigue debajo.

Verificado ANTES de asumir el mismo bug en otras páginas: el índice "En
esta sección" de `vista_explorador.js` (producción/impacto/colaboración/
áreas temáticas) NO tiene este problema — vive dentro de
`.explorador-panel`, que ya es su propia columna fija de 17rem con
`position: sticky` + `overflow-y: auto` acotado (`app.css` línea ~1572,
mecanismo previo y distinto de `.disposicion`). Confirmado con una captura
de `produccion.html` en el mismo punto de scroll: sin overlap. El bug
estaba aislado a `catalogo()`, la única función que emitía `.rail` sin
ningún contenedor de grid.

### Corrección

`vista.js::catalogo()`: el `<nav class="rail">` y las secciones ahora se
envuelven en `<div class="disposicion">`. Verificado antes de aplicar que
ningún selector de JS asume la profundidad del DOM anterior: `paginas.js`
(scroll-spy) y `src/verify/flujos.mjs` usan `.rail a` (descendiente, no hijo
directo) y `document.getElementById(id)` para las secciones observadas —
ninguno se rompe con un contenedor extra.

### Verificación

`06_assemble_site.py` + `node run_all.mjs` (6/6, incluido `flujos.mjs` que
ejercita el scroll-spy de este mismo rail con un clic real y comprueba que
marca exactamente un enlace activo). Captura Playwright en claro y oscuro,
mismo punto de scroll que mostró el bug: el índice ahora vive en su propia
columna angosta a la izquierda, sin superponerse a ninguna sección, en los
dos temas. Captura en 390px (breakpoint móvil, `.disposicion` sigue
`display: block` ahí): sin cambios respecto de antes — la fila de pastillas
horizontal de siempre.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-426 | `catalogo()` envuelve `.rail` y las secciones en `.disposicion`; el resto del sitio no se toca | `.disposicion` ya existía en `app.css` sin usarse en ningún lado — era la pieza que faltaba, no una clase nueva que inventar. Verificado que `vista_explorador.js` no tiene el mismo bug (columna propia ya correcta) antes de asumir un alcance mayor |

### Archivos modificados

```
web/assets/js/vista.js   catalogo(): .rail + secciones envueltos en .disposicion
```

### Ambigüedades abiertas

Ninguna nueva.

### Próximo paso recomendado

Ninguna acción de código pendiente.

---

## Cierre: Scopus Author Search — evidencia de identidad que el detector automático no podía ver

### Contexto

El usuario bajó de Scopus/SciVal un documento nuevo: **Scopus Author
Search por afiliación "Universidad Finis Terrae"** (812 perfiles de autor,
entregado hoy). Antes de decir para qué servía, se leyó el archivo real —
no se especuló sobre su estructura. Confirmado con el usuario: búsqueda
por afiliación institucional, sin ventana de años. Pidió avanzar con dos
cosas: (1) registrar la fuente y construir lo necesario para aprovecharla,
(2) cruzar el ORCID que trae contra lo que el proyecto ya tiene asignado.

### El hallazgo que justificó construir algo, no sólo archivar el CSV

Antes de escribir código se verificó, caso por caso, si esta fuente
aportaba algo que el proyecto no pudiera ya calcular solo. La regla `P-04`
(`04_author_population.py`) ya detecta "un nombre con más de un Scopus
Author ID" — pero SÓLO cuando ambos identificadores aparecen, dentro del
corpus de 823 publicaciones, bajo la misma cadena de nombre exacta.
Verificado con casos reales:

- **"Esis Villarroel, Ivette S."**: Scopus Author Search lista dos
  perfiles — uno con 1 documento (el que sí está en el corpus, Facultad de
  Derecho) y otro con **14 documentos y ORCID propio**, que no aparece en
  el corpus en ninguna forma. Un segundo perfil completo, invisible al
  detector automático porque ninguna de esas 14 publicaciones cae dentro
  del corpus 2023-2025.
- **"Caffarena, Paula"**: sus dos identificadores SÍ están ambos en el
  corpus — pero uno bajo "Caffarena, Paula" y el otro bajo "Barcenilla,
  Paula Caffarena" (apellidos en otro orden). El detector agrupa por
  cadena de nombre exacta, así que nunca los conectó.
- **"Cabello, José Miguel"**: mismo patrón que Esis Villarroel — un
  identificador con 4 documentos ausente del corpus.

Los otros 4 nombres repetidos en la fuente (Moya Patricia, Hartmann
Schatloff Dan, Quezada Mauricio, Torres Keila) ya estaban en
`internal/ambiguities_authors.csv` — la fuente los confirma de forma
independiente, no aporta dato nuevo ahí.

### Qué se construyó

`data/raw/Scopus_Author_Search_UFT.csv` (el archivo, versionado) y
`config/sources.yml` → `scopus_author_search` (entregado 2026-09-02, sin
ventana temporal declarada — se documenta explícitamente para no
confundir el "N° de documentos" de cada perfil, que es el que ve Scopus
Author Search, con el número de publicaciones de ese autor dentro del
corpus del proyecto).

Nuevo conector `src/enrich/scopus_author_search.py`, capa interna, nunca
decide (D-08). Reutiliza la misma extracción que `04_author_population.py`
(`scopus_id_map()`, regex `r"(.+?)\s+\((\d+)\)$"` sobre `Author full
names`) y la misma conversión "Apellido, Nombre" → "Apellido N." que
`_firma_corta()`/`_firma_corta_p04` — copiadas, no importadas: el módulo
de origen empieza con un dígito y no es importable, mismo motivo ya
documentado en `build_review.py` para la misma función. Produce:

- `internal/scopus_author_search_multiples_id.csv`: 7 candidatos con 2+
  Scopus Author ID (4 ya conocidos, 3 nuevos), cada uno con el detalle de
  qué dice Scopus de cada identificador, si está en el corpus, con
  cuántas publicaciones, y bajo qué otro nombre si corresponde.
- `internal/scopus_author_search_orcid.csv`: contraste de los 50 ORCID que
  trae la fuente contra `data/enriched/authors_orcid.csv` — **26
  coinciden, 0 contradicen, 1 es nuevo** (firma UFT ya conocida, sin ORCID
  asignado: "Bastías, Jaime"), **23** son firmas que Scopus asocia a la
  afiliación pero que la población UFT del proyecto no reconoce (fuera de
  ventana, u homonimia — no se investigó más sin evidencia adicional).

### Verificación

`python3 src/enrich/scopus_author_search.py --test`: 14/14 comprobaciones
(extracción de Scopus Author ID, mapa inverso ID→nombres, conteo de
publicaciones por ID, agrupación de candidatos con 2+ ID, detección de
nombre bajo otra grafía, marca de "ya conocido", y las cuatro resoluciones
del contraste de ORCID: coincide/contradice/nuevo/sin_firma_uft). Corrida
real: cifras iguales a las verificadas a mano antes de escribir el
conector (7 candidatos, 3 nuevos; 50 ORCID evaluados, 0 contradicciones).
`python3 src/audit/run_all.py`: sin cambios (29/30, misma falla
preexistente E-06). Este cierre no toca ningún build step ni artefacto
publicado — es capa interna, igual que `dspace_inventario.py`/
`autoarchivo_uft.py`.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-427 | Se construye un conector nuevo en vez de sólo archivar el CSV | Verificado antes de decidir: el detector automático `P-04` estructuralmente no puede ver fragmentación cuando un identificador no tiene publicaciones en el corpus, ni conectar identificadores bajo grafías distintas del mismo nombre — esta fuente sí, porque Scopus ya agrupó por identificador antes de exportar (3 casos reales, no hipotéticos, encontrados así) |
| D-428 | Los candidatos de "múltiples Scopus ID" y el contraste de ORCID se publican como cola de revisión interna, nunca como resolución automática | Mismo principio D-08 que ya rige DSpace, autoarchivo y Crossref: "puede ser perfil fragmentado o puede ser homonimia" no lo decide una máquina |
| D-429 | El "N° de documentos" de Scopus Author Search se declara explícitamente distinto del recuento de publicaciones del corpus, en todo lugar donde aparecen juntos | La fuente no tiene ventana temporal ni filtro de afiliación por publicación individual — mezclar los dos números sin decirlo habría sido presentar cosas no comparables como si lo fueran, exactamente lo que este proyecto evita |

### Archivos modificados

```
data/raw/Scopus_Author_Search_UFT.csv       nuevo — archivo entregado por el usuario
src/enrich/scopus_author_search.py          nuevo — conector, --test (14 casos)
internal/scopus_author_search_multiples_id.csv   nuevo — salida real
internal/scopus_author_search_orcid.csv          nuevo — salida real
config/sources.yml                          scopus_author_search
docs/FUENTES_Y_APIS.md                      §2.9 nueva
STATE.md, docs/DECISIONS.md                 regenerados
```

### Supuestos descartados

- Que el "N° de documentos" de cada perfil correspondía al corpus del
  proyecto: descartado explícitamente — es el conteo de Scopus Author
  Search, sobre todo el perfil, sin ventana ni afiliación-por-publicación.
- Que un nombre repetido en la fuente con dos Scopus Author ID era
  automáticamente la misma persona: se mantiene el mismo principio que
  `P-04` — homonimia y perfil fragmentado quedan igual de abiertos, la
  fuente no decide entre ellos.

### Ambigüedades abiertas

- Los 3 candidatos nuevos (Esis Villarroel, Caffarena, Cabello) quedan sin
  resolver — evidencia para revisión humana, no una fusión de identidad.
- Las 23 firmas "sin_firma_uft_en_el_proyecto" no se investigaron: podrían
  ser autores reales fuera de la ventana 2023-2025, homónimos, o casos que
  la extracción del proyecto no capturó por otra razón — no se asumió
  ninguna de las tres sin evidencia adicional.

### Próximo paso recomendado

Ninguna acción de código pendiente. Si se quiere, alguien puede revisar
`internal/scopus_author_search_multiples_id.csv` caso por caso y aplicar
una decisión (mismo mecanismo que la cola de identidad existente) para
los 3 candidatos nuevos.

## Cierre: aplicación de decisiones y listado — Scopus Author Search (2026-09-02, continuación)

### Contexto

Mismo día, continuación del cierre anterior. El usuario autorizó revisar
los 3 candidatos nuevos de "múltiples Scopus ID" y pidió aplicar la
decisión resultante y entregar un listado HTML del resto de los casos.

### Qué se hizo

**Revisión de los 3 candidatos** (cruce contra `authors_orcid.csv`,
`openalex_cobertura.csv`, `orcid_ampliacion_log.csv` y el corpus real):
- **Esis Villarroel, Ivette S.** → confirmada como una sola persona. Dos
  fuentes independientes (Crossref, ya en el proyecto; Scopus Author
  Search, nuevo) coinciden en el mismo ORCID `0000-0002-2379-8380` para
  los dos Scopus Author ID de la fuente, y `openalex_cobertura.csv` aporta
  3 publicaciones más de la misma persona (todas de Derecho, fuera del
  universo Scopus) que corroboran. Cumple el umbral de evidencia
  dispositiva que este proyecto exige (mismo nombre + mismo ORCID contra
  el trabajo propio de la persona, corroborado por fuente independiente).
- **Caffarena, Paula** → NO confirmada, queda pendiente. El proyecto ya
  tenía ORCID distintos asignados a las dos firmas (`0000-0002-2609-6413`
  vs. `0000-0001-9550-3695`) — si fueran la misma persona se esperaría el
  mismo ORCID. Hay coincidencia temática (historia social/sanitaria
  chilena) pero coincidencia temática sola no alcanza el umbral —mismo
  criterio ya aplicado a "Moya, Patricia" en una sesión anterior—, y en
  este caso hay evidencia que más bien argumenta EN CONTRA de la fusión.
- **Cabello, José Miguel** → NO confirmada, queda pendiente. Sin ORCID en
  ninguna fuente para verificar ninguno de los dos perfiles; sólo
  coherencia temática (Medicine/urología), insuficiente por sí sola.

**Mecanismo de aplicación** (D-430): se construyó
`src/review/apply_scopus_author_decisions.py`, calcado del patrón ya
existente de `apply_openalex_review.py` (lee un CSV pequeño de veredictos
humanos, actualiza `resolucion`/`nota_resolucion` por nombre, idempotente,
`--test`/`--dry-run`/real). Las 3 decisiones de arriba quedaron escritas
en `internal/scopus_author_search_decisiones.csv` con su razonamiento
completo, y se aplicaron sobre `internal/scopus_author_search_multiples_id.csv`
(verificado con `--dry-run` antes de escribir de verdad).

**Listado HTML** (`internal/scopus_author_search_listado.html`): cubre lo
que la revisión de los 3 candidatos no cubrió — los 2 casos que quedaron
pendientes (con su razonamiento completo), los 4 casos ya conocidos por el
proyecto (sin dato nuevo, sólo confirmación), y las 24 filas del contraste
de ORCID que no fueron "coincide" (1 nueva asignación posible — Bastías,
Jaime — y 23 sin firma UFT reconocida en el proyecto).

**Hallazgo al armar el listado, no automático** (D-431): revisando las 23
filas "sin_firma_uft_en_el_proyecto" a mano, "Fernández Abara, Joaquín
Fernández" (ORCID `0000-0001-8190-2361`) es casi seguro la misma persona
que "Abara J.F.", que el proyecto ya tiene con el ORCID idéntico
(`data/enriched/authors_orcid.csv`, vía OpenAlex). El cruce automático de
`contraste_orcid()` no lo detectó porque compara por firma corta exacta
y este documento escribe el apellido compuesto completo ("Fernández
Abara") mientras el corpus del proyecto lo abrevia distinto ("Abara") —
un límite real del cruce por apellido+inicial cuando hay apellidos
compuestos, no una fuente nueva de identidad. Se dejó marcado en el
listado HTML en vez de corregirlo en el código: corregir el cruce para
apellidos compuestos en general es un cambio de alcance mayor (afecta
`contraste_orcid()` y potencialmente otros cruces por firma del proyecto)
que no se investigó a fondo para las otras 22 filas — no se generalizó
un arreglo a partir de un solo caso verificado a mano.

### Verificación

`scopus_author_search.py --test` (14/14) y
`apply_scopus_author_decisions.py --test` (5/5) sin cambios. `--dry-run`
antes de aplicar de verdad: confirmó exactamente 3 cambios, los
esperados. `src/audit/run_all.py` y `src/build/build_all.py` completos
sin fallas nuevas; `git diff --stat -- data/processed/` vacío — este
cierre tampoco toca la capa pública.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-430 | Se aplican las 3 decisiones vía un mecanismo dedicado (`apply_scopus_author_decisions.py`), no editando el CSV de la cola a mano | Mismo patrón que `apply_openalex_review.py`: la decisión queda registrada con su razonamiento en un archivo separado, versionado, reaplicable — no se pierde si se regenera la cola |
| D-431 | El hallazgo "Fernández Abara" / "Abara J.F." se deja como nota marcada en el listado, no como corrección de código | Es un solo caso verificado a mano; generalizar el cruce por apellido compuesto a las otras 22 filas sin evidencia equivalente habría sido inventar una regla no probada |

### Archivos modificados

```
src/enrich/scopus_author_search.py               resolucion/nota_resolucion en candidatos_multiples_id
src/review/apply_scopus_author_decisions.py       nuevo
internal/scopus_author_search_decisiones.csv      nuevo — 3 decisiones con razonamiento
internal/scopus_author_search_multiples_id.csv    actualizado — 1 confirmada, 6 pendientes
internal/scopus_author_search_listado.html        nuevo — listado de lectura, capa interna
STATE.md, docs/DECISIONS.md                       regenerados
```

### Supuestos descartados

- Que el hallazgo "Fernández Abara"/"Abara J.F." justificaba revisar las
  otras 22 filas "sin_firma_uft_en_el_proyecto" en busca de coincidencias
  similares: descartado por alcance — un caso verificado a mano no es
  base para asumir que las demás tienen el mismo patrón.

### Ambigüedades abiertas

- Caffarena y Cabello siguen pendientes — evidencia insuficiente, no
  evidencia en contra (salvo Caffarena, donde hay un argumento activo
  en contra de la fusión).
- Las 23 filas "sin_firma_uft_en_el_proyecto" siguen sin investigar caso
  por caso, salvo la excepción marcada (Fernández Abara).
- El límite de `contraste_orcid()` con apellidos compuestos queda
  documentado pero no corregido.

### Próximo paso recomendado

Si se quiere avanzar el hallazgo D-431, confirmar "Fernández Abara" =
"Abara J.F." con una fuente adicional (Crossref u OpenAlex por DOI) antes
de fusionar. Si se quiere generalizar la detección de apellidos
compuestos en `contraste_orcid()`, primero revisar las otras 22 filas a
mano para ver cuántas comparten el patrón — no vale la pena generalizar
el código para un caso.

## Cierre: confirmación de "Fernández Abara" y ajuste de confianza (2026-09-03)

### Contexto

El usuario pidió confirmar el hallazgo D-431 contra Crossref u OpenAlex
por DOI, tal como quedó recomendado en el cierre anterior.

### Qué se hizo

La consulta en vivo a Crossref y OpenAlex está bloqueada por política de
red en este entorno (verificado: ambas devuelven 403 en el proxy de
salida — `curl` a `api.crossref.org` y `api.openalex.org`, mismo bloqueo
ya conocido de `crossref_financiamiento.py`). No se simuló ninguna
respuesta.

En su lugar, se rastreó el DOI de la publicación de "Abara J.F." en el
propio corpus (EID `2-s2.0-105034655965`, DOI
`10.38178/07183089/1211230605`) y se encontró que el campo "Author full
names" de ese registro ya trae **el mismo Scopus Author ID**
(57190811072) que Scopus Author Search asigna a "Fernández Abara,
Joaquín Fernández" — es Scopus, en dos productos distintos, resolviendo
el mismo perfil. Sumado a que `authors_orcid.csv` ya tenía asignado a
"Abara J.F." el mismo ORCID (`0000-0001-8190-2361`) **vía OpenAlex**, una
fuente independiente de Scopus Author Search, y a que el correo de
correspondencia del artículo es `jfernandez@uft.cl`, quedan tres señales
independientes convergiendo — el mismo umbral que confirmó a Esis
Villarroel. No se necesitó la llamada en vivo porque la corroboración ya
estaba en datos que el proyecto había producido en una sesión anterior.

Con la confirmación, se actualizaron las dos cosas que el usuario pidió:
- `internal/scopus_author_search_listado.html`: la nota pasó de "hallazgo
  sin confirmar" a "confirmado", con las tres señales listadas.
- `data/enriched/authors_orcid.csv`: `confianza` de "Abara J.F." subida de
  "media" a "alta" — mismo criterio que ya usan otras filas "alta" con
  respaldo humano o cruzado. `fuente` se dejó igual ("OpenAlex"): ese
  campo dice de dónde salió el ORCID, no cuánta corroboración tiene
  después; la corroboración es lo que ya dice `confianza`.

### Verificación

`python3 src/build/build_all.py`: build 05 sigue en 0 fallas. Como
`data/processed/` está en `.gitignore` (confirmado con
`git check-ignore`), un `git diff` ahí siempre da vacío — no es
verificación válida de impacto público; se verificó directamente sobre
el JSON generado: `data/processed/authors.json` y
`data/processed/author/abara-j-f.json` muestran `"orcid_confianza":"alta"`
para Abara J.F., como se esperaba.

Al verificar el efecto real en el sitio se encontró un bug preexistente,
sin relación con este cambio: la tabla de `autores.html`
(`web/assets/js/paginas.js`, función `autores()`) muestra en el tooltip
del ORCID el texto fijo "ORCID recuperado desde Crossref · confianza
X" para **toda** fila con ORCID, sin importar la fuente real — 154 de
~328 filas con ORCID tienen una fuente distinta de Crossref (79
OpenAlex, 48 ORCID declarado por el titular, 27 revisión humana), así
que el tooltip les atribuye mal el origen. La ficha individual de cada
autor sí usa el texto correcto (`orcid_estado`, calculado en
`03_authors.py`); sólo la tabla del directorio tiene el texto fijo. No se
corrigió aquí — no formaba parte de lo pedido y toca un componente
compartido por las 538 fichas — se dejó como sugerencia de tarea aparte
(`task_596c1939`).

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-432 | Se confirma "Fernández Abara, Joaquín Fernández" = "Abara J.F." sin la llamada en vivo a Crossref/OpenAlex que se había recomendado | Ya existía corroboración independiente suficiente en datos que el proyecto ya tenía (OpenAlex, de una sesión anterior) — repetir la consulta no habría cambiado la conclusión, y la red está bloqueada de todas formas |
| D-433 | El bug del tooltip fijo en `autores.html` se reporta como tarea aparte en vez de corregirse en este cambio | Fuera del alcance de lo pedido (confirmar un hallazgo y actualizar dos archivos puntuales); corregirlo toca un componente compartido por las 538 fichas del directorio, no sólo la de Abara |

### Archivos modificados

```
internal/scopus_author_search_listado.html   nota actualizada a "confirmado"
data/enriched/authors_orcid.csv              Abara J.F.: confianza media → alta
STATE.md, docs/DECISIONS.md                  regenerados
```

### Supuestos descartados

- Que hacía falta reintentar la consulta a Crossref/OpenAlex antes de dar
  el hallazgo por confirmado: descartado — la corroboración por ORCID ya
  existía en `authors_orcid.csv` desde una fuente independiente
  (OpenAlex), y repetirla no habría añadido evidencia nueva.

### Ambigüedades abiertas

Ninguna nueva. El bug del tooltip queda documentado como tarea aparte,
no como ambigüedad de este cierre.

### Próximo paso recomendado

Ninguna acción de código pendiente en esta línea de trabajo. El bug del
tooltip de `autores.html` queda disponible como tarea aparte
(`task_596c1939`) si se quiere corregir.

## Cierre: las otras 22 filas del contraste de ORCID (2026-09-03, mismo día)

### Contexto

El usuario pidió revisar si las 22 filas restantes de "sin_firma_uft_en_el_
proyecto" (después de confirmar "Fernández Abara") compartían el mismo
patrón de apellido compuesto. Se revisaron con el mismo método —Auth-ID
exacto de Scopus Author Search en el corpus, por posición de autor, contra
el ORCID ya asignado a la firma resultante— y el usuario autorizó aplicar
el mismo tratamiento a lo que se encontrara.

### Qué se encontró

Un primer cruce por Auth-ID sin discriminar posición de autor dio
resultados ruidosos en publicaciones con varios coautores UFT (el mismo
EID mapeaba a firmas equivocadas). Se corrigió cruzando por
`(eid, posicion_autor)` contra `matching_log.csv`, que sí distingue cada
coautor dentro de un mismo EID.

Con el cruce correcto: **11 de las 22 comparten el mismo patrón** —mismo
Auth-ID presente en el corpus del proyecto en la posición correcta, mismo
ORCID ya asignado a la firma resultante, desde una fuente independiente de
Scopus Author Search—: Andrade→Kobayashi M.A., Ayala Munita→Ayala M.,
Amarouch García→Amarouch García I./García I.A. (dos firmas, ver abajo),
Bustos Arriagada→Bustos-Arriagada E., Díaz→Diaz F./Díaz F., Letelier
Widow→Letelier Widow G., Mardones Falcone→Mardones-Falcone G.,
Phillips→Letelier J.P., Santibañez→Santibáñez D., Simón→Simón L.,
Zambrano-Matamala→Zambrano C. Las variantes del patrón: apellido compuesto
truncado (igual que Fernández Abara), espacio vs. guion, tilde presente o
ausente, e inicial de más en el nombre de pila.

**11 de las 22 no muestran ninguna señal** —ni el Auth-ID aparece en el
corpus bajo ninguna posición, ni su ORCID coincide con ninguna firma ya
asignada—: Barros, Bolt, Bugueño, Cortés, Fortuny, Fuentes Anabalón,
Lehmann, Letelier (Rene F.), Opitz, Saldías, Sanhueza. Quedan igual que
estaban — sin evidencia para decidir nada.

**Dos hallazgos al margen, no resueltos:**
- "Amarouch García, Ismael Amarouch" confirmó el mismo Auth-ID bajo *dos*
  firmas del proyecto sin consolidar entre sí ("Amarouch García I." y
  "García I.A.", más una tercera, "Amarouch I.", sin ORCID) — inconsistencia
  interna previa a este documento, no introducida por él.
- "Fortuny, Esteban Fortuny" no encaja en el patrón de apellido compuesto,
  pero su ORCID coincide exacto con "Fortuny E." ya asignado en el
  proyecto, bajo un Auth-ID **distinto** (59254638800 en el corpus vs.
  57203373183 en Scopus Author Search) — es fragmentación de perfil
  Scopus (el mismo fenómeno de "Varios Scopus ID" ya revisado para
  Moya/Hartmann/Quezada/Torres), no el patrón de esta revisión.

### Qué se aplicó

`internal/scopus_author_search_listado.html`: las 11 filas confirmadas se
marcan igual que Fernández Abara, con el emparejamiento y el motivo
específico; los dos hallazgos al margen quedan anotados sin resolver.

`data/enriched/authors_orcid.csv`: confianza subida de "media" a "alta"
para las 6 firmas que estaban en "media" — Amarouch García I., García
I.A., Ayala M., Mardones-Falcone G., Letelier J.P., Zambrano C. Las otras
cinco firmas confirmadas ya estaban en "alta" por otra vía, sin cambio.

### Verificación

`python3 src/build/build_all.py`: build 05 en 0 fallas. Verificado
directamente sobre `data/processed/authors.json` (no vía `git diff`, que
siempre da vacío en `data/processed/` por estar en `.gitignore`): las 6
firmas bumpeadas muestran `"orcid_confianza":"alta"` en la salida real.
`python3 src/audit/run_all.py`: sin cambios, misma falla preexistente E-06.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-434 | El cruce se hace por `(eid, posicion_autor)`, no por Auth-ID solo | Un Auth-ID que aparece en un EID con varios coautores UFT puede emparejarse con la firma equivocada si no se usa la posición — se detectó y corrigió antes de reportar resultados |
| D-435 | Las 11 confirmaciones se aplican en un solo lote, con el mismo criterio ya usado para Fernández Abara | Cada una cumple el mismo umbral (Auth-ID exacto + ORCID idéntico desde fuente independiente); tratarlas una por una no habría cambiado el criterio, sólo el ritmo |
| D-436 | Los dos hallazgos al margen (Amarouch con dos firmas sin consolidar, Fortuny con Auth-ID fragmentado) se documentan sin resolver | Ninguno de los dos es el patrón de esta revisión (apellido compuesto); resolverlos ahora habría sido ampliar el alcance sin la misma evidencia ya reunida para los otros casos |

### Archivos modificados

```
internal/scopus_author_search_listado.html   11 filas más marcadas confirmado + 2 notas al margen
data/enriched/authors_orcid.csv              6 firmas: confianza media → alta
STATE.md, docs/DECISIONS.md                  regenerados
```

### Supuestos descartados

- Que el primer cruce (por Auth-ID sin posición) era suficiente: descartado
  al ver resultados inconsistentes en EID con varios coautores UFT — se
  corrigió antes de reportar nada al usuario.

### Ambigüedades abiertas

- Los dos hallazgos al margen (Amarouch, Fortuny) quedan sin resolver —
  ver arriba.
- Las 11 firmas sin ninguna señal permanecen sin investigar caso por caso.

### Próximo paso recomendado

Si se quiere avanzar el hallazgo de Amarouch, consolidar sus tres firmas
("Amarouch García I.", "García I.A.", "Amarouch I.") bajo una sola, igual
que ya se hizo para Esis Villarroel. Si se quiere avanzar el de Fortuny,
tratarlo como un candidato más de "Varios Scopus ID" — mismo mecanismo que
Moya/Hartmann/Quezada/Torres.

## Cierre: consolidación de las tres firmas de Amarouch (2026-09-03, mismo día)

### Contexto

El usuario pidió consolidar el hallazgo de Amarouch del cierre anterior:
tres firmas del proyecto ("Amarouch García I.", "García I.A.", "Amarouch I.")
que Scopus Author Search confirmó como un solo Scopus Author ID
(57339772200), sin fusionar entre sí en la población del proyecto.

### Qué se hizo

A diferencia de las decisiones anteriores de esta línea de trabajo (que
sólo tocaban archivos internos de `scopus_author_search.py`), consolidar
firmas de verdad —que se fusionen en una sola ficha pública, con sus
publicaciones sumadas— tiene un mecanismo propio y único en el proyecto
(D-08: "el pipeline nunca lo hace por heurística"):
`internal/identity_decisions.csv` (decisión humana) →
`src/review/apply_decisions.py` (aplica) →
`config/identidades_consolidadas.yml` (lo que el build consume). Se usó
ese mecanismo, no uno nuevo: se agregó una fila
(`caso_id=sas-amarouch, cola=Variantes de nombre, veredicto=misma`) con
las tres firmas separadas por `|` y la evidencia completa en la nota, y
se corrió `apply_decisions.py`.

Antes de aplicar de verdad se verificó con `--dry-run` y con una
inspección directa de `grupos_de_identidad()` que las tres firmas forman
un solo grupo sin contradicciones y que la forma canónica resultante
("Amarouch García I.", por ser la más larga a igualdad de frecuencia y
diacríticos) es la esperada.

Al aplicar, el resumen impreso mostró "22 asignaciones nuevas" y "138
ORCID confirmados", números mucho mayores que lo que este único cambio
explicaría — el script recalcula TODO `identity_decisions.csv` en cada
corrida, no sólo la fila agregada. Se verificó con cuidado antes de
continuar: `git diff` sobre `data/enriched/authors_orcid.csv` después de
la corrida da vacío — el archivo se reescribió pero con contenido
byte-idéntico al ya commiteado. Es el comportamiento esperado, no un
efecto colateral: esas 22/138 cifras son el CÁLCULO COMPLETO recomputado
desde cero sobre decisiones que ya estaban aplicadas de sesiones
anteriores; sólo cambió lo que de verdad era nuevo (el grupo de
Amarouch). `config/firmas_e09_resueltas.yml` y `config/orcid_revisado.yml`
también se reescribieron con sólo la fecha cambiada, sin contenido nuevo.

### Verificación

`python3 src/review/apply_decisions.py --test`: 18/18 casos OK, sin
cambios. `--dry-run` antes de aplicar: previó exactamente el grupo
esperado (38 grupos, +1). `python3 src/build/build_all.py`: build 05 en
0 fallas; fichas de autor 538 → 536 (-2, exactamente lo esperado al
fusionar 3 firmas en 1). Verificado directo sobre
`data/processed/authors.json`: la ficha consolidada "Amarouch García I."
trae `n_publicaciones: 3` (1+1+1), ORCID `0000-0003-2444-8179` a
confianza alta, y `variantes_consolidadas` lista las tres firmas
originales. `python3 src/audit/run_all.py`: 29/30, misma falla
preexistente E-06.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-437 | La consolidación se aplica por `internal/identity_decisions.csv` + `apply_decisions.py`, no por un archivo nuevo | Es el único mecanismo del proyecto que fusiona firmas en la capa pública (D-08); usar otro habría creado una segunda vía para el mismo efecto |
| D-438 | Se verificó `git diff` sobre `authors_orcid.csv` antes de confiar en el resumen impreso por el script | El resumen ("22 nuevas", "138 confirmados") por sí solo sugería un efecto mucho mayor al esperado; sólo comparando el archivo resultante contra lo ya commiteado se confirmó que era recómputo idempotente, no un cambio real no solicitado |

### Archivos modificados

```
internal/identity_decisions.csv              +1 fila (sas-amarouch, misma)
config/identidades_consolidadas.yml           regenerado — 38 grupos (+1)
config/firmas_e09_resueltas.yml               regenerado — sólo fecha
config/orcid_revisado.yml                     regenerado — sólo fecha
internal/scopus_author_search_listado.html    nota de Amarouch actualizada a "resuelto"
STATE.md, docs/DECISIONS.md                   regenerados
```

### Supuestos descartados

- Que las 22/138 cifras del resumen indicaban un efecto no solicitado
  sobre `authors_orcid.csv`: descartado tras verificar `git diff` — el
  contenido resultante es idéntico al ya commiteado; el número refleja
  cómo se calcula el archivo, no cuánto cambió.

### Ambigüedades abiertas

Ninguna nueva. El hallazgo de Fortuny (Auth-ID fragmentado, mismo ORCID)
sigue pendiente, sin tocar.

### Próximo paso recomendado

Ninguna acción de código pendiente en esta línea de trabajo. Si se quiere
avanzar el hallazgo de Fortuny, tratarlo como un candidato más de "Varios
Scopus ID" — mismo mecanismo que Moya/Hartmann/Quezada/Torres.

## Cierre: Fortuny como candidato durable de "Varios Scopus ID" (2026-09-03, mismo día)

### Contexto

El usuario pidió tratar el hallazgo de Fortuny (del cierre anterior) como
un candidato más de la cola "Varios Scopus ID" — la misma que ya trae
Moya/Hartmann/Quezada/Torres/Esis Villarroel/Caffarena/Cabello.

### Por qué no bastaba con agregar una fila a mano

`internal/scopus_author_search_multiples_id.csv` lo regenera por completo
`scopus_author_search.py` en cada corrida (mismo patrón que
`ambiguities_authors.csv` — no es editable a mano, D-08 otra vez). El
detector que encontró a los otros 7 (`candidatos_multiples_id`) agrupa por
NOMBRE EXACTO dentro de la propia fuente Scopus Author Search — y el caso
de Fortuny no comparte nombre en ninguna fuente ("Fortuny, Esteban" en el
corpus vs. "Fortuny, Esteban Fortuny" en Scopus Author Search): sólo se
conecta por el ORCID. Una fila agregada a mano habría desaparecido en la
siguiente corrida del conector, sin aviso.

### Qué se hizo

Se agregó un segundo detector, `candidatos_fragmentacion_orcid()`, a
`src/enrich/scopus_author_search.py`: busca, para cada fila de Scopus
Author Search con ORCID, si ese ORCID ya está asignado en el proyecto a
una firma cuyo Auth-ID en el corpus —calculado por posición de autor vía
la función nueva `auth_ids_por_firma()`, mismo cuidado que el resto de
esta revisión (ver el cierre de "las otras 22 filas")— es DISTINTO al
Auth-ID que trae Scopus Author Search. Su salida usa las mismas columnas
que `candidatos_multiples_id()` para viajar en la misma cola y el mismo
mecanismo de decisión (`apply_scopus_author_decisions.py`, sin cambios).

Al conectar los dos detectores apareció una duplicación real: "Esis
Villarroel, Ivette S." —ya confirmada en un cierre anterior— quedó
detectada TAMBIÉN por el nuevo detector, porque ahora tiene ORCID
asignado y ese ORCID converge con su propio Auth-ID del corpus. Dos filas
con el mismo `nombre_scopus` habrían roto la unicidad de la que depende
`apply_scopus_author_decisions.py` (indexa por nombre; con dos filas
iguales sólo actualiza la última). Se corrigió pasándole al segundo
detector los nombres que el primero ya cubrió, para que no los repita —
no una excepción para Esis Villarroel, una regla general: cualquier
nombre que el primer detector ya explica no necesita una segunda fila.

Al volver a correr el conector, `scopus_author_search_multiples_id.csv`
se regeneró completo y perdió las decisiones ya aplicadas (Esis
Villarroel vuelta a "pendiente") — es el comportamiento esperado del
archivo (se regenera, no se edita), así que se volvió a correr
`apply_scopus_author_decisions.py` con el mismo
`scopus_author_search_decisiones.csv` de antes para restaurarlas.

### Verificación

`python3 src/enrich/scopus_author_search.py --test`: 21/21 (6 casos
nuevos: `auth_ids_por_firma` no mezcla coautores del mismo EID, detecta
el ORCID cruzado, no marca `ya_conocido_en_ambiguities`, no reporta sin
evidencia en tres formas distintas, no duplica un nombre que el otro
detector ya cubrió). Corrida real: 8 candidatos (7 de antes + Fortuny),
sin duplicados, Fortuny con `auth_ids` "57203373183 | 59254638800"
—exactamente lo encontrado a mano en el cierre anterior—.
`apply_scopus_author_decisions.py --dry-run` antes de reaplicar: previó
exactamente los 3 cambios esperados (Esis Villarroel restaurada,
Caffarena/Cabello re-anotadas). `python3 src/audit/run_all.py` y
`python3 src/build/build_all.py`: sin fallas nuevas, `git status` sobre
`data/enriched/` y `config/` vacío — este cierre tampoco toca la capa
pública.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-439 | Se agrega un detector nuevo al conector en vez de una fila a mano | El archivo de candidatos se regenera por completo en cada corrida; una fila a mano desaparecería sin aviso en la siguiente ejecución |
| D-440 | El detector nuevo excluye los nombres que el detector existente ya reportó | Sin la exclusión, un nombre con ORCID asignado y también con 2+ Auth-ID en la misma fuente (caso real: Esis Villarroel) se duplicaría, rompiendo la unicidad de `nombre_scopus` que usa `apply_scopus_author_decisions.py` para indexar |
| D-441 | El candidato Fortuny entra a la cola como PENDIENTE_REVISION_HUMANA, sin decisión aplicada | Consistente con cómo entraron los otros 7: la cola registra evidencia, decidir es un paso aparte que alguien autoriza explícitamente |

### Archivos modificados

```
src/enrich/scopus_author_search.py                +auth_ids_por_firma(), +candidatos_fragmentacion_orcid(), 7 casos de prueba nuevos
internal/scopus_author_search_multiples_id.csv     regenerado — 8 candidatos (Fortuny nuevo), decisiones previas reaplicadas
internal/scopus_author_search_listado.html         nota de Fortuny actualizada
STATE.md, docs/DECISIONS.md                        regenerados
```

### Supuestos descartados

- Que bastaba con una fila agregada a mano en `scopus_author_search_multiples_id.csv`:
  descartado — el archivo es 100% regenerado, no editable (mismo principio
  que `ambiguities_authors.csv`).
- Que la duplicación de Esis Villarroel al conectar los dos detectores era
  un caso aislado a ignorar: descartado — es la consecuencia esperada de
  tener dos detectores independientes sobre las mismas personas a medida
  que se les asignan ORCID; se corrigió con una regla general, no con una
  excepción puntual.

### Ambigüedades abiertas

Fortuny queda pendiente — evidencia a favor (ORCID declarado por el
titular, corroborado independientemente por Scopus Author Search, mismo
campo temático) pero sin decisión aplicada.

### Próximo paso recomendado

Si se quiere decidir el caso de Fortuny, el mismo mecanismo de los otros
7: una fila en `internal/scopus_author_search_decisiones.csv` +
`apply_scopus_author_decisions.py`.

---

## Fusión con `origin/main` (2026-09-03): narrativa de la rama paralela de UX/mapas/paleta

Lo que sigue es la parte de `SESSION_NOTES.md` en `origin/main` (commit
`8f6d2bf`) que no tenía equivalente en esta rama — un hilo de trabajo
paralelo sobre la cabecera del sitio, los mapas de producción y la paleta
de color, hecho en otra sesión el 2026-09-01. El resto del historial de
`origin/main` (identidad, DSpace, ORCID) ya estaba cubierto aquí, a veces
de forma más completa — se verificó sección por sección antes de fusionar
y no se perdió nada de ninguno de los dos lados. Ver el cierre "fusión de
`origin/main` (sesión paralela)..." para el detalle de esa verificación.

## Sesión 2026-09-01 (noche) - Interactividad de la parte superior

Contexto: el usuario declaró *"No me gusta la parte superior del sitio. Es poco
interactiva"* (cabecera + barra de vigencia). Se aplicó criterio UX de fuentes
confiables (USWDS, GOV.UK, RSS, NN/g): claridad > decoración, menos carga
cognitiva, accesibilidad WCAG 2.2, progressive enhancement, feedback de estado
visible. Objetivo: **usuario final del informe**.

### Hallazgo estructural clave
El header, la barra de vigencia y el pie **no son HTML por página**: los genera
la función _sin DOM_ `cromo(meta, paginaActual)` en `web/assets/js/core.js`,
compartida por los 10 HTML y usada por el pre-renderizador (Node) y por la
hidratación (navegador). Mejorar la parte superior es tocar **un solo
cuerpo de código** (core.js + app.css + paginas.js) que ya conoce
`paginaActual` y `meta` — no hay 10 copias que sincronizar.

### Mejoras implementadas (todas en `web/`, ninguna toca fuentes/de datos)
1. **Nav agrupado por sección + colapsable.** `NAV_GRUPOS` (Informe / Datos /
   Sobre este informe) con `navHtml()`. En banda ancha (≥900px) una sola fila sin
   rótulos; en móvil/tablet se pliega tras un botón hamburguesa `.nav-toggle`
   con `aria-expanded` y cierre al elegir sección. `overflow-x: auto`
   eliminado → adiós doble barra de scroll interna.
2. **Migas de posición en la barra.** `.v-migas` (Portada · {página}); en la
   portada se suprime el par redundante («Portada → Portada») con CSS por
   `data-pagina="portada"`. Clase propia para no chocar con el breadcrumb de
   contenido de secciones (`.migas`, línea 508). No se duplica el H1: cada
   página ya tiene uno propio (WCAG: no crear segundo H1 ni saltar niveles).
3. **Chips de vigencia interactivos.** `Fuente` / `Ventana` / `Citas al` pasan
   de texto plano a `<details class="v-chip">` nativo: despliegan un panel
   explicativo de una línea, accesible por teclado y por móvil, sin JS.
4. **Badge de recorte en vivo.** `.recorte-vivo` en la barra (slot oculto por
   defecto). `paginas.js: actualizarRecorteVivo()` lo enciende al filtrar y lo
   apaga al limpiar; vive en la barra de todas las páginas pero sólo se
   rellena desde el explorador. Verificado: «Recorte 319 de 823 publicaciones».
5. **Selector de año en la barra.** `.v-anio` (`<select id="recorte-anio">`),
   oculto salvo en páginas explorador, que `montarSelectorAnio()` rellena con
   los años reales del corpus y preselecciona el activo; al cambiar aplica el
   recorte (mismo filtro que tocar el chip de año).
6. **Mini-foco en portada.** Atajos de un toque `#minifoco` (Exploración
   rápida): «Publicaciones {último año}» y «Ver todo» cuando hay recorte.
   No duplican los filtros: son entradas rápidas que aplican el recorte vía el
   cierre `fijar` (único dueño de `sel` y del repintado).

Decisiones de integración:
- El `<select>` del año y el `#minifoco` son **elementos estables**: el escucha
  se engancha una vez (`.addEventListener`) y el contenido se redibuja con
  `redibujarSelectorAnio()`/`redibujarMiniFoco()` en cada `pintar()`, evitando
  manejadores acumulados.
- `actual()`/`cambiar()` devuelven el recorte vigente en cada momento, para que
  el handler nunca trabaje con un `sel` anticuado tras varios repintados.
- Progressive enhancement íntegro: sin JS el `<details>` y las migas se leen
  igual; el badge/select/mini-foco quedan `hidden`.
- Print: `.nav-toggle`, `.v-migas`, `.v-chip`, `.recorte-vivo`, `.v-anio`,
  `.minifoco` entran en la regla `@media print { display:none }`.

### Verificación
- `py src/build/06_assemble_site.py` → 10 páginas pre-renderizadas, capa interna
  no incluida (verificado), peso 3548 KB.
- `node src/verify/run_all.mjs dist` → **completa sin fallos** (contraste 0,
  estructura 0, flujos 0 excepciones JS, responsive 0px desborde, higiene sin
  fallos, peso dentro de techo).
- Sonda Playwright dirigida (servidor persistente Node, puerto 8852) confirmó
  en runtime: 3 grupos de nav, hamburguesa oculta en escritorio y `flex` +
  abre+`aria-expanded` en móvil 480px, miga «Portada» en índice, chip
  «Fuente Scopus · SciVal» con panel, `<select>` con 4 años poblado, mini-foco
  visible, badge oculto sin filtro y **badge «Recorte 319 de 823» tras pulsar
  el mini-foco**, botón «Ver todo» al haber recorte.
- Capturas regeneradas (PNG, raíz repo, viewport 1440, fullPage): `_cap_*.png`
  (9 páginas) + `_cap_index_recorte.png`. Ojo operativo: las capturas al
  principio salieron en blanco porque el servidor de captura apuntaba a la raíz
  del repo en vez de `dist/` (el `.html` no está en la raíz); se corrigió el
  `root` del servidor. Servidor persistente en script Node, no `Start-Job`.

### Pendientes (sin bloqueo)
- `_cap_autor.png` es de una corrida anterior (90 KB); la ficha autor no se
  volvió a capturar en esta pasada (no listada). Regenerarla si se quiere.
- Decidido con el usuario: se implementaron **ambas** mejoras restantes
  (selector de año + mini-foco). No queda ninguno de los 6 TODOs originales
  abierto; solo queda cerrar con commit.
- SESSION_NOTES del cierre de tramo previo (V2-28) ya documenta los 68 DOIs
  como insumo documentado (D-346/D-347).

### Próximo paso recomendado
Revisar con el usuario las capturas (`explorer _cap_*.png`), confirmar el
criterio visual, y hacer commit + push del refinement UX de la parte superior.

---
## Sesión 2026-09-01 (tarde) — Paleta H (vino + champán), cambio integral de identidad

### Decisión (usuario)
- Elegida la paleta **H · Vino/burdeos + champán** de la comparativa, y se pidió
  tomarla **íntegra** ("aunque cueste más tokens"): marca, dato y advertencia a
  la vez, no sólo la cabecera.
- Comparativa servida en vivo (http://localhost:8100/paletas.html, 8 candidatas,
  claro/oscuro) generada con la skill `brand-palette` (creada en
  `~/.claude/skills/brand-palette/`).

### Qué se cambió (solo `web/assets/css/app.css`, tokens + comentarios)
- **Marca/superficies/tinta → cálidas**: `--marca` vino `#2c0c12`, superficies
  hueso/champán en claro y vino profundo en oscuro, tinta champán, `--marca-tinta`
  champán `#f0ddca`, `--accion` vino `#8a2430`. Se re-tocó también el
  `.banda-contraste` y `.banda-enfasis` (son ámbitos oscuros que redefinen tokens).
- **Dato → bordeaux (cálido)**: `--serie-1` `#8a2430`/`--serie-2` `#c06070`,
  rampa ordinal `--ord-1..4` en bordeaux (claro sube, oscuro baja para legibilidad).
- **Advertencia → verde-moneda (frío)**: con el dato en bordeaux, el viejo ámbar
  (cálido) quedaba a ΔE 17,9 < 20; se movió a `--aviso-*` verde moneda
  (`#2e7d32`/`#5a9e5f`…), que separa el dato (ΔE 26,0 claro / 22,2 oscuro).
- Comentarios actualizados: se sustituyeron las tablas/afirmaciones viejas
  (teal, Deep Ocean, Peach, ámbar) que habían quedado como "fotografía" por la
  referencia al validador como juez; se conservó la identidad institucional como
  "rojo no oficial verificado".

### Verificación (evidencia)
- `py src/design/validar_paleta.py` → **SISTEMA CROMÁTICO VÁLIDO** (0 fallos.
  Incluye: contraste AA por token en claro/oscuro, ΔE dato↔advertencia ≥20,
  rampa ΔE ≥8 y monótona, par categórico bajo protanopía/deuteranopía/tritanopía).
- `py src/build/06_assemble_site.py` → build OK (10 páginas, capa interna no
  incluida).
- `node src/verify/run_all.mjs dist` → **VERIFICACIÓN COMPLETA · sin fallos**
  (contraste, estructura, flujos, responsive, higiene, peso).
- Sonda de color Playwright (`color.mjs`): cabecera vino `rgb(168,68,85)`,
  acentos champán `rgb(240,221,202)`, chip hueso `rgb(253,246,239)`, vigencia-
  guía vino `rgb(138,36,48)`. El dato bordeaux/verde-moneda los confirma la
  captura de impacto.

### Archivos tocados
- `web/assets/css/app.css` (tokens + comentarios; sin hardcodear hex en JS — el
  JS usa variables CSS, verificado por grep: 0 hex en `web/assets/js/`).
- `SESSION_NOTES.md` (esta entrada).

### Capturas regeneradas
- `_rev_portada.png` (254 KB) y `_rev_impacto.png` (356 KB) en raíz del repo
  (viewport 1440, fullPage, servidor `dist/`).

### Pendiente
- Commit + push de la paleta H (aún sin commitear sobre `23d102e`).
- Nota operativa: `dist/`, `data/processed/` son derivados no versionados; el
  servidor 8000 (PID 2440) sirve `dist/` ya reconstruido.

## Sesión 2026-09-01 (noche) - Fix visual del heatmap de Producción

### Síntoma
El usuario reportó "los gráficos y mapas" de Producción rotos visualmente tras
la paleta H. Causa raíz: en H, `--accion-viva` dejó de ser teal (color de dato
fuerte) y pasó a **champán claro** `#f0ddca`; el heatmap lo usaba como relleno
de magnitud → **champán sobre papel champán = invisible (1,16:1)**, además
diluido por `fill-opacity` (0,06–0,94).

### Cambio
- `web/assets/js/visualizations/heatmap.js` (línea 91): `fill="var(--accion-viva)"`
  → `fill="var(--serie-1)"` (bordeaux del dato). `es-clara`/texto intactos.
- Comentario de cabecera (líneas 14-18) actualizado para no citar el token viejo.

### Verificación
- Pixel-sampling del `.heatmap-svg` renderizado: celdas bordeaux (p. ej.
  `#91313b`, `#a5555d`, `#b06b71`) sobre papel champán; gradiente de intensidad
  legible. Treemap: etiquetas claras `#fdf6ef` confirmadas (contraste 4,99:1).
- Contraste del texto del heatmap: bordeaux claro→texto vino ok; bordeaux
  intenso→ texto claro (`es-clara`) ok. Umbral `es-clara` intacto.
- `py src/build/06_assemble_site.py` OK; `node src/verify/run_all.mjs dist` →
  **VERIFICACIÓN COMPLETA · sin fallos**.

### Capturas
- `_rev_produccion.png` regenerada (416 KB, fullPage, servidor `dist/`).

### Pendiente
- Commit (aún sin commitear) de `web/assets/js/visualizations/heatmap.js`.
- Nota: previewl del foco en la red (`core.js:830`, anillo `--accion-viva`
  champán) queda como acento; no es fallo WCAG y no se tocó.
- Confirmación visual del usuario sobre el heatmap corregido.

## Sesión 2026-09-01 (noche) - Mejoras de UX/comprensión en los mapas de Producción

### Cambios
- **Heatmap** (`web/assets/js/visualizations/heatmap.js`): umbral `es-clara` de
  `intensidad > 0.55` → `> 0.66`. Antes la cifra cambiaba a texto claro en la
  franja op 0,54 (contraste de luz sólo 2,84:1); con el nuevo cruce el texto
  oscuro cubre las celdas claras y el claro las oscuras, minimizando la banda
  donde ninguno llegaba a 4,5:1 (la rampa bordeaux-alpha pasa por un centro
  "embarrado" irreducible entre op 0,64-0,72; ambos colores ≥3,7:1 ahí).
- **Heatmap**: nueva **leyenda de escala** dentro del SVG (`renderLegend`):
  barra de 4 pastillas (op 0,06→0,94) con marcas 0 / mitad / máximo (real).
  Comparte la escala raíz cuadrada de las celdas.
- **Treemap** (`web/assets/js/visualizations/treemap.js`): nueva leyenda bajo
  las migas con las 4 pastillas `ord-*` + gris `--sin-dato`, y texto que aclara
  que el tono identifica la celda (no codifica magnitud) y que gris = sin datos.

### CSS (token-only, en `modern-ui.css`)
- `.heatmap-leyenda`, `.heatmap-ley-guia`, `.heatmap-ley-titulo`,
  `.heatmap-ley-marca`, `.treemap-leyenda`, `.treemap-ley-titulo`,
  `.treemap-ley-mostrar`, `.treemap-ley-sin`, `.treemap-ley-rotulo`.
  Sólo referencias a tokens de `app.css`; sin hex propios.

### Verificación
- `node src/verify/run_all.mjs dist` → **sin fallos** (responsivo, higiene,
  contraste, peso).
- Sonda DOM: leyenda del heatmap con marcas 0/17/34 (máx real 34), pastillas
  op 0,06→0,94; leyenda del treemap con 5 muestras; **desborde X = 0**.
- `_rev_produccion.png` regenerada (422 KB).

### Archivos tocados
`web/assets/js/visualizations/heatmap.js`, `treemap.js`, `web/assets/css/modern-ui.css`,
`SESSION_NOTES.md`.

### Pendiente
- Commit (aún sin commitear) de los 3 archivos de código + SESSION_NOTES.md.
- Confirmación visual del usuario de que tanto leyendas como el heatmap corregido
  se ven bien en claro y en oscuro.

## Cierre: fusión de `origin/main` (sesión paralela) y un bug real de idempotencia expuesto al fusionar

### Contexto

El usuario pidió revisar un listado de trabajo real en `origin/main`
(commit `8f6d2bf`) — conectores ORCID nuevos (DataCite, Europe PMC,
Zenodo, GitHub), una herramienta `informes/` con ejecución aislada, y la
identidad de Carlos Henríquez-Olguín consolidada. Verificado contra el
repositorio real (no se asumió el listado): existe, y esta rama
(`claude/state-review-next-steps-wzzq0h`) y `origin/main` habían
divergido — 22 commits propios, 12 de main, desde un ancestro común
(`61de666`), con 33 archivos tocados en ambos lados. El usuario pidió
resolver la divergencia antes de tocar cualquier otra cosa del listado.

### Cómo se resolvió cada archivo en conflicto

`git merge origin/main` marcó 10 archivos en conflicto real y auto-fusionó
el resto (incluidos `data/enriched/authors_orcid.csv`, `03_authors.py`,
`apply_decisions.py` y varios más — verificado con `git diff --quiet`
contra ambos lados antes de confiar en el auto-merge, no se asumió).

- **`internal/identity_decisions.csv`** (fuente de verdad, no
  regenerable): de 67 filas con contenido distinto entre ramas, 65 eran
  el mismo patrón — esta rama las tenía resueltas, main las tenía
  `pendiente` sin nota — y se resolvieron a favor de esta rama sin
  pérdida (main no aportaba nada ahí). Las 2 restantes exigieron leer la
  evidencia de cada lado, no un criterio mecánico:
  - **Henríquez-Olguín** (`p03-henriquezolguin`): esta rama la tenía
    `pendiente` sin tocar desde 2026-08-05; main la resolvió `misma` el
    2026-09-03 con evidencia real (ORCID y Scopus Author ID compartidos).
    Se tomó la de main.
  - **Moya, Patricia** (`p04-Moya, Patricia`): aquí el patrón se invertía
    — main la tenía `misma` desde 2026-08-26 SIN firmas ni nota (fila
    vacía), y esta rama la tenía `pendiente` desde 2026-09-02 con un
    análisis explícito de por qué NO se confirma (dispersión temática
    real entre las publicaciones de un mismo Auth-ID: atención de
    urgencia por ideación suicida vs. caries en preescolares). Se
    mantuvo el `pendiente` de esta rama — la evidencia posterior y más
    completa pesa más que un veredicto sin respaldo, sea de la rama que
    sea.
- **`config/identidades_consolidadas.yml`, `orcid_revisado.yml`,
  `firmas_e09_resueltas.yml`**: los tres se declaran "GENERADO... no
  editar a mano" — se descartó el contenido en conflicto y se
  regeneraron con `apply_decisions.py` sobre el `identity_decisions.csv`
  ya fusionado.
- **`internal/revision_identidad.html`, `pendientes_consolidacion.{html,md}`**:
  mismo criterio — regenerados con `build_review.py`, no fusionados a mano.
- **`SESSION_NOTES.md`**: comparar los 103 títulos de sección de esta
  rama contra los 86 de main mostró que sólo 4 eran exclusivos de main
  (un hilo de trabajo paralelo de UX/mapas/paleta, 2026-09-01) — el
  resto de las secciones de main YA estaban en esta rama, a veces con
  detalle que a la copia de main le faltaba (verificado con `diff` línea
  a línea en cada bloque de conflicto antes de resolver, no se asumió
  por la posición del marcador). Se conservó el contenido de esta rama
  completo y se agregaron al final las 4 secciones exclusivas de main,
  con una nota explicando la fusión.
- **`STATE.md`, `docs/DECISIONS.md`, `docs/BUILD_VERIFICATION.md`**:
  regenerados (`snapshot.py`, build), no fusionados.
- **`docs/FUENTES_Y_APIS.md`**: el merge automático de git dejó dos
  secciones "### 2.2" (la nueva de DataCite/EuropePMC/Zenodo choca con
  la ya existente de ORCID) — renombrada a "2.1 ter", siguiendo la
  convención "bis" que el propio documento ya usaba.

### El hallazgo de idempotencia

Al correr `apply_decisions.py` tras fusionar `identity_decisions.csv`, el
resumen impreso mostró "22 asignaciones nuevas, 138 confirmadas" — cifras
que ya se habían visto y verificado como recómputo idempotente en un
cierre anterior de esta misma rama (sesión de hoy). Se confirmó de nuevo
con `git diff --quiet` sobre `authors_orcid.csv`: sin cambios reales.

### Verificación

`git status` sin archivos sin trackear ni marcadores de conflicto
restantes. `grep` de `D-[0-9]+` en `SESSION_NOTES.md` fusionado: sin
números duplicados. `python3 src/audit/run_all.py`: 29/30, misma falla
preexistente E-06, sin fallas nuevas. `python3 src/build/build_all.py`:
0 fallas en la compuerta pública/interna; 536 fichas de autor, igual que
antes de fusionar (Henríquez-Olguín ya estaba consolidado por
equivalencia ortográfica en esta rama; el cambio es sólo su `origen`,
de "ortografica" a "humana" — no cambia el recuento). `git diff --quiet`
sobre `data/enriched/authors_orcid.csv`, `config/firmas_e09_resueltas.yml`
y los archivos `data/raw/Inventario_*` contra ambas ramas: contenido ya
resuelto por el auto-merge de git, sin pérdida verificada en ningún
sentido (ni de main hacia acá, ni de esta rama hacia main).
`python3 src/build/06_assemble_site.py`: 11 páginas, capa interna no
incluida. `node src/verify/run_all.mjs`: corrido en segundo plano —
pendiente confirmar el resultado antes de dar el cierre por completo.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-442 | Se prefiere "esta rama" sobre "main" en 65 de los 67 conflictos de `identity_decisions.csv` sin revisar caso por caso, y se revisan a mano únicamente los 2 donde ambos lados tenían un veredicto real | En 65 casos main sólo tenía la fila en blanco (`pendiente` sin nota): no hay decisión de main que perder. Revisar los 2 restantes uno por uno, en vez de aplicar "el más reciente gana" o "main gana" mecánicamente, es lo que expuso que Moya, Patricia necesitaba el criterio opuesto al de Henríquez-Olguín |
| D-443 | Se mantiene "pendiente" para Moya, Patricia pese a que main la tenía "misma" | El veredicto de main no traía evidencia (fila vacía); el de esta rama sí, y es evidencia EN CONTRA de la fusión (dispersión temática real entre las publicaciones del mismo Auth-ID) — aceptar "misma" solo porque main lo tenía habría publicado una fusión que la propia evidencia de esta rama contradice |
| D-444 | Los archivos "GENERADO... no editar a mano" (`identidades_consolidadas.yml`, `orcid_revisado.yml`, `firmas_e09_resueltas.yml`, `revision_identidad.html`, `pendientes_consolidacion.*`, `STATE.md`, `docs/DECISIONS.md`, `docs/BUILD_VERIFICATION.md`) se regeneran desde su fuente fusionada, nunca se resuelven a mano | Fusionar YAML o HTML generado a mano arriesga producir algo que ninguno de los dos scripts que lo leen (`common_build.py`, `03_authors.py`) reconocería como válido; regenerar desde la fuente ya fusionada es la única forma de garantizar que el resultado es exactamente lo que el pipeline produciría |
| D-445 | `SESSION_NOTES.md` se resuelve comparando títulos de sección completos entre ambas ramas, no aceptando el marcador de conflicto de git tal cual | Varios bloques de conflicto resultaron ser el MISMO contenido reposicionado por ediciones cercanas (mismo texto, distinto número de decisión) — aceptar el marcador de git sin verificar habría duplicado media docena de cierres ya presentes en esta rama |

### Archivos modificados

```
internal/identity_decisions.csv               fusionado — 2 casos revisados a mano, 65 automáticos
config/identidades_consolidadas.yml            regenerado
config/orcid_revisado.yml                      regenerado (sin cambio real)
internal/revision_identidad.html               regenerado
internal/pendientes_consolidacion.{html,md}    regenerado
SESSION_NOTES.md                               fusionado — 4 secciones de main agregadas al final
STATE.md, docs/DECISIONS.md                    regenerados
docs/BUILD_VERIFICATION.md                     regenerado (build)
docs/FUENTES_Y_APIS.md                         "2.2" duplicada -> "2.1 ter"
Makefile, .gitignore, web/*, data/enriched/authors_orcid.csv,
config/sources.yml, src/build/03_authors.py, src/review/*, etc.
                                                auto-fusionados por git,
                                                verificados sin pérdida
src/enrich/{datacite,europepmc,zenodo,github_orcid}.py,
informes/*, internal/zenodo_log.csv            nuevos, de main, sin cambios
```

### Supuestos descartados

- Que "el veredicto más reciente gana" o "main gana los conflictos
  reales" era un criterio seguro: descartado en el caso de Moya,
  Patricia — main era el veredicto MÁS ANTIGUO (2026-08-26) y sin
  ninguna evidencia, frente a uno más reciente (2026-09-02) y
  explícitamente razonado en esta rama.
- Que las cifras "22 nuevas / 138 confirmadas" de `apply_decisions.py`
  indicaban que el merge había introducido cambios reales en
  `authors_orcid.csv`: descartado con `git diff --quiet` — es el mismo
  recómputo idempotente ya verificado en un cierre anterior de hoy.

### Ambigüedades abiertas

Ninguna nueva sobre la fusión en sí. Los hallazgos de la revisión de
`origin/main` (bug de parseo en `europepmc.py`, dependencia `rich` no
declarada, el conector de red que no se ejecuta con `--test` en CI, el
token de GitHub documentado hacia un archivo versionado) siguen sin
corregir — el usuario pidió resolver la divergencia primero.

### Próximo paso recomendado

Confirmar el resultado de `node src/verify/run_all.mjs` (corriendo en
segundo plano al cerrar esta nota). Si sale limpio, comitear la fusión y
empujar. Después, decidir con el usuario cuál de los hallazgos de la
revisión de `origin/main` corregir primero.

## Cierre: corrige el parseo de iniciales dobles en europepmc.py

### Contexto

`node src/verify/run_all.mjs` terminó limpio (6/6) tras la fusión; se
comiteó y empujó. El usuario pidió corregir el primer hallazgo de la
revisión de `origin/main`: `extraer()` en `src/enrich/europepmc.py`
perdía el apellido entero cuando el bloque de iniciales tenía más de una
letra — verificado antes de tocar nada: `"Smith AB"` daba
`family="Smith AB", given=""` en vez de `family="Smith", given="AB"`,
porque el código sólo reconocía como inicial un token de UNA letra.

### Qué se corrigió

El criterio pasa de "¿es de una sola letra?" a "¿es el ÚLTIMO token, y
está TODO en mayúsculas?" — el apellido de la fuente nunca viene en
mayúsculas, así que ese token siempre es el bloque de iniciales,
independientemente de cuántas letras tenga. Se conserva una guarda para
un solo token (sin apellido separado): sin ella, `family` quedaría vacío.

Se verificó además, antes de dar la corrección por completa, que
`clave_crossref()` (`orcid_crossref.py`) sólo usa la PRIMERA letra de
`given` para emparejar — el mismo criterio "apellido + primera inicial"
de todo el proyecto — así que el bug real y con impacto era sólo en
`family`; `given` con más de una letra no cambiaba nada aguas abajo, pero
se corrige igual porque es lo que la fuente realmente declara.

### Verificación

`python3 src/enrich/europepmc.py --test`: 10/10 (4 casos nuevos: bloque
de dos iniciales se separa bien, un autor normal en la misma cadena no
se rompe, apellido con guion no se confunde con el bloque de iniciales,
un solo token no deja el apellido vacío). Verificado a mano, antes y
después: `emparejar(["Smith A.B."], ...)` no encontraba nada antes de la
corrección y encuentra `match: apellido+inicial` después. `python3
src/audit/run_all.py`: sin cambios, mismo resultado de siempre.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-446 | El criterio de "es inicial" pasa de "un token de una letra" a "el último token, todo en mayúsculas" | El apellido de Europe PMC nunca viene en mayúsculas; un bloque de dos o más iniciales ("AB") es indistinguible de un apellido corto sólo por longitud, pero sí por mayúsculas — es la señal que realmente distingue los dos casos en esta fuente |

### Archivos modificados

```
src/enrich/europepmc.py    extraer(): criterio de iniciales corregido, 4 casos de prueba nuevos
```

### Ambigüedades abiertas

Ninguna nueva. Siguen sin corregir los otros hallazgos de la revisión de
`origin/main`: la dependencia `rich` no declarada en
`informes/_consolidar_autores.py`, los 4 conectores ORCID sin `--test`
en CI, y el token de GitHub documentado hacia un archivo versionado
(`config/matching_rules.yml`).

### Próximo paso recomendado

Decidir con el usuario cuál de los hallazgos restantes corregir a
continuación.

## Cierre: quita la dependencia no declarada de `rich`

### Contexto

El usuario pidió corregir el segundo hallazgo de la revisión de
`origin/main`: `informes/_consolidar_autores.py` importaba `rich`
(`from rich import print`, `Console`, `Table`) sin que el paquete
estuviera en `requirements.txt` — reventaría con `ModuleNotFoundError`
en cualquier máquina que sólo siguiera el setup documentado.

### Por qué se quitó la dependencia en vez de declararla

`rich` sólo se usaba para el resumen final por consola (una tabla y dos
líneas de texto en color) — el trabajo real del script (leer las
fuentes, escribir `informe_autores.md` y `autores_consolidado.csv`) no
la necesitaba. Agregarla a `requirements.txt` habría sido la corrección
más corta, pero introduce una dependencia nueva al proyecto por un
`print` bonito, contra el criterio que el propio `requirements.txt` ya
declara (versiones acotadas, sólo lo estrictamente necesario, `rich` no
figura en ningún otro script de los ~40 que tiene `src/enrich/` y
`src/review/`). Se reemplazó por `print()` plano con el mismo formato
que usa el resto del proyecto (`f"  {etiqueta:32s}: {valor}"`).

### Verificación

Sintaxis verificada (`ast.parse`). Corrida real contra los datos vigentes
del repositorio: mismo resumen de siempre (589 formas de firma, 328 con
ORCID, 38 grupos de identidad), sin errores. `grep` de `import rich` /
`from rich` en todo el proyecto: cero coincidencias. `informe_autores.md`
y `autores_consolidado.csv` se regeneraron al probar el script —se
revirtieron antes de comitear: refrescarlos es una decisión aparte,
no lo que se pidió acá. `python3 src/audit/run_all.py`: sin cambios.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-447 | Se quita `rich` en vez de declararla en `requirements.txt` | Sólo formateaba el resumen de consola, no el trabajo real del script; el proyecto no usa `rich` en ningún otro lugar, y `requirements.txt` declara explícitamente el criterio de no agregar dependencias más allá de lo necesario |
| D-448 | No se comitean los `informe_autores.md`/`autores_consolidado.csv` regenerados al probar el arreglo | Refrescarlos con los datos vigentes del repositorio es útil pero es otra tarea, no la que se pidió; comitearlos de paso habría mezclado un cambio de código con 2000+ líneas de datos regenerados sin que nadie lo pidiera |

### Archivos modificados

```
informes/_consolidar_autores.py    quita rich, usa print() plano
```

### Ambigüedades abiertas

Ninguna nueva. Siguen sin corregir: los 4 conectores ORCID sin `--test`
en CI, y el token de GitHub documentado hacia un archivo versionado
(`config/matching_rules.yml`).

### Próximo paso recomendado

Decidir con el usuario cuál de los dos hallazgos restantes corregir a
continuación. Si en algún momento se quiere refrescar
`informe_autores.md`/`autores_consolidado.csv` con los datos vigentes,
basta con volver a correr `python3 informes/_consolidar_autores.py`.

## Cierre: los 4 conectores ORCID nuevos entran a CI

### Contexto

El usuario pidió corregir el tercer hallazgo de la revisión de
`origin/main`: `.github/workflows/deploy.yml` no ejercía `--test` para
`datacite.py`, `europepmc.py`, `zenodo.py` ni `github_orcid.py` —
rompía el patrón que el propio workflow sigue con todo lo demás en
`src/enrich/` (cada conector que decide qué ORCID se atribuye a quién
tiene su paso de `--test`, `orcid_afiliacion.py` incluido).

### Qué se hizo

Se agregaron los 4 pasos, en el mismo bloque donde ya están
`orcid_expand.py`/`orcid_afiliacion.py`/`dspace_inventario.py`/
`autoarchivo_uft.py`, justo antes del comentario que explica por qué
ROR no corre su consulta real en CI pero sí su lógica de extracción —
`github_orcid.py` sigue exactamente ese mismo patrón: inactivo sin
token, pero su función de extraer ORCID del bio se comprueba igual.

### Verificación

`python3 -c "import yaml; yaml.safe_load(...)"`: el YAML sigue siendo
válido. Los 4 `--test` corridos a mano, uno por uno: los cuatro pasan
limpio — son exactamente los mismos comandos que CI va a ejecutar, no
una aproximación. `python3 src/audit/run_all.py`: sin cambios.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-449 | Los 4 pasos nuevos se insertan junto a los otros conectores de identidad/ORCID, no al final del bloque | Mantiene el agrupamiento temático que el workflow ya tenía (ORCID/identidad primero, ROR y OpenAlex después) en vez de una lista sin orden aparente |

### Archivos modificados

```
.github/workflows/deploy.yml    4 pasos --test nuevos (DataCite, Europe PMC, Zenodo, GitHub)
```

### Ambigüedades abiertas

Ninguna nueva. Sigue sin corregir: el token de GitHub documentado hacia
un archivo versionado (`config/matching_rules.yml`).

### Próximo paso recomendado

Decidir con el usuario si corregir el hallazgo del token de GitHub.

## Cierre: el token de GitHub sale del archivo versionado

### Contexto

El usuario pidió corregir el último hallazgo de la revisión de
`origin/main`: `github_orcid.py` documentaba y leía el token desde
`config/matching_rules.yml` bajo `enriquecimiento_externo.github.token`
— un archivo del repositorio, versionado y sin ignorar. Quien siguiera
esa instrucción al pie de la letra habría comiteado una credencial real.

### Qué se hizo

Se cambió a variable de entorno (`GITHUB_ORCID_TOKEN`), mismo criterio
que ya siguen `orcid_api.py`/`orcid_expand.py` con sus propias
credenciales de ORCID — se agregó `credenciales()` como función propia,
calcada de la de `orcid_api.py`, con la diferencia de que la ausencia de
token no detiene el script (esta fuente es opcional por diseño, se
informa y termina en 0, no se aborta). El mensaje cuando falta el token
ahora trae la instrucción de exportarlo (bash y PowerShell), igual que
`orcid_api.py`. Verificado que `config/matching_rules.yml` no tenía
ningún valor real bajo esa clave (nunca se comiteó una credencial) — no
hubo nada que revocar, sólo la instrucción que apuntaba mal.

De paso, en la misma función que se estaba tocando, se corrigió un
artefacto de generación real encontrado en la revisión anterior:
caracteres chinos sueltos en medio de una oración en español
("... con 搜索 por ORCID en campos de perfil.") — visible sólo cuando el
script corre con token configurado, nunca ejercido hasta ahora porque
nadie tenía uno.

### Verificación

`python3 src/enrich/github_orcid.py --test`: 4/4, sin cambios (la lógica
de extracción de ORCID del bio no se tocó). Corrida real, las dos rutas:
sin `GITHUB_ORCID_TOKEN` en el entorno, imprime las instrucciones y
termina en 0; con uno (falso, de prueba), imprime "Token de GitHub:
configurado" y el texto ahora en español correcto, también termina en 0.
`grep` de "matching_rules" y del carácter chino en el archivo: cero
coincidencias en ambos casos. `python3 src/audit/run_all.py`: sin
cambios.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-450 | El token pasa a variable de entorno, no a `matching_rules.yml` con instrucciones de "no lo comitee" | Es el mismo criterio que ya rige las credenciales de ORCID en este proyecto: nunca en un archivo del repositorio, sin excepciones ni advertencias que dependan de que alguien las lea |
| D-451 | Se corrige el texto en chino de la misma función, en el mismo cierre | Es la misma línea de código que se estaba tocando por el hallazgo del token; separarlo en un cierre aparte habría sido más ceremonia que la corrección amerita |

### Archivos modificados

```
src/enrich/github_orcid.py    token vía GITHUB_ORCID_TOKEN, credenciales(), texto en chino corregido
```

### Ambigüedades abiertas

Ninguna. Los cuatro hallazgos de la revisión de `origin/main` quedan
todos corregidos.

### Próximo paso recomendado

Ninguna acción de código pendiente en esta línea de trabajo.

## Cierre de sesión: fusión a `main`, despliegue confirmado, sitio verificado en navegador

### Contexto

Con los cuatro hallazgos de la revisión de `origin/main` ya corregidos,
el usuario pidió fusionar esta rama a `main`, luego confirmar que el
despliegue terminara bien, y por último revisar que el sitio se viera
bien en un navegador real. Cierre de la sesión completa de hoy
(2026-09-03): Scopus Author Search, la fusión con el trabajo paralelo de
`origin/main`, los cuatro hallazgos de esa revisión, y esto.

### Qué se hizo

**Fusión a `main`**: `origin/main` no había avanzado desde que se trajo a
esta rama más temprano (seguía en `8f6d2bf`), así que fue un
fast-forward limpio — `main` pasó a `1150920`, el mismo commit que esta
rama, sin fusión nueva ni conflictos. Antes de empujar se corrieron
auditoría y build una vez más sobre el estado final; ambos en 0 fallas.
`git push origin main` sin objeciones — un solo push, sin force.

**Confirmación del despliegue** (`.github/workflows/deploy.yml`, run
#118, `33800447345`): se monitoreó por la API de GitHub Actions en vez
de asumir que un push exitoso implica un despliegue exitoso. Hubo un
susto real a mitad de camino: varias consultas seguidas mostraron el
paso "Verificar el sitio construido" en `in_progress` durante más de 10
minutos, contra un baseline de 1m16s de la corrida exitosa anterior —
suficiente para sospechar un cuelgue genuino, no sólo un runner lento, y
se le dijo así al usuario en vez de seguir esperando en silencio. La
siguiente consulta mostró que en realidad ya había terminado en 1m45s
—las consultas anteriores cayeron en una ventana de latencia de la propia
API, no un cuelgue real— y que el job `desplegar`
(`actions/deploy-pages@v4`) también había corrido y terminado limpio.
Los 4 pasos `--test` agregados hoy (DataCite, Europe PMC, Zenodo,
GitHub) corrieron en CI por primera vez y pasaron los cuatro. Duración
total del workflow: 3m20s, sin incidentes reales.

**Verificación visual en navegador**: la URL pública (`github.io`) está
bloqueada por la política de red de este entorno — confirmado con
`curl`, no asumido. En su lugar se reconstruyó `dist/` en local desde el
mismo commit exacto que quedó desplegado (`1150920`) — son los mismos
archivos que Pages sirve, sin modificar — y se recorrieron con
Playwright (Chromium preinstalado, `executablePath` explícito, sin
`playwright install`) las 10 páginas del sitio más una ficha de autor,
en tema claro y oscuro: 21 cargas, todas HTTP 200 con contenido real,
cero errores de consola y cero fallos de red. Inspección visual de
varias capturas: la portada, el directorio de autores (confirma
Henríquez-Olguín ya consolidado, "87 se fusionaron en 38 personas"), una
ficha de autor completa, la página de producción ampliada, y
`indicadores.html` —confirmando que el bug del índice lateral corregido
antes en esta sesión sigue arreglado—. Se enviaron cuatro capturas al
usuario.

### Verificación

Ya documentada arriba en cada bloque: auditoría y build en 0 fallas
antes del push; el propio workflow de CI como verificación independiente
(30 reglas de auditoría, 21 autopruebas de conectores incluidas las 4
nuevas, verificación de capa pública/interna, `src/verify/run_all.mjs`
completo); y la revisión con navegador real como una cuarta capa,
independiente de las tres anteriores, sobre los artefactos exactos que
quedaron públicos.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-452 | La fusión a `main` se hace por fast-forward, no por un merge commit nuevo | `main` no había avanzado desde que se trajo a esta rama; un fast-forward es la operación más simple que logra el mismo resultado, sin historia adicional que explicar |
| D-453 | Se le avisa al usuario que el despliegue parece colgado en vez de seguir monitoreando en silencio, aun cuando después resultó ser una falsa alarma | Diez minutos contra un minuto de baseline es una señal real, no ruido — la alternativa (esperar sin decir nada, posiblemente durante horas si de verdad estaba colgado) es peor que una alarma que termina siendo falsa |
| D-454 | La revisión visual se hace sobre `dist/` reconstruido en local, no sobre la URL pública | La URL pública está bloqueada por la política de red de este entorno (verificado con `curl`, no asumido); `dist/` reconstruido desde el mismo commit es exactamente lo que Pages sirve, sin modificar, así que la verificación es igual de válida |

### Archivos modificados

```
(ninguno — sesión de verificación, no de código)
```

### Supuestos descartados

- Que un push exitoso a `main` implica un despliegue exitoso: se verificó
  el workflow de principio a fin en vez de asumirlo.
- Que 10+ minutos de "in_progress" en un paso con baseline de 1m16s era
  sólo lentitud del runner: se trató como sospecha real de cuelgue y se
  le avisó al usuario, aunque la siguiente consulta mostró que ya había
  terminado.
- Que no poder abrir la URL pública era motivo para omitir la revisión
  visual: se reconstruyó el mismo artefacto en local en su lugar.

### Ambigüedades abiertas

Ninguna sobre este cierre. Quedan, de cierres anteriores, sin resolver:
los dos hallazgos "al margen" de Scopus Author Search (Fortuny como
candidato de Varios Scopus ID pendiente de decisión; el bug del tooltip
fijo en `autores.html`, `task_596c1939`, sin ejecutar).

### Próximo paso recomendado

Ninguna acción de código pendiente. El sitio está desplegado, verificado
por CI y por revisión visual directa, y `main`/esta rama están
sincronizadas. Sesión cerrada.

## Addendum: reconciliación con PR #39 al empujar el cierre a `main`

### Contexto

Al empujar el commit de cierre anterior (`6e866e0`) también a `main` —
siguiendo el mismo patrón de sincronización que el resto de la sesión—,
`git fetch origin main` mostró que `origin/main` ya no estaba en
`1150920`: había avanzado a `b6ea061`, un merge commit (PR #39,
`claude/pensive-tesla-81t44z`) que no se originó en esta sesión ni en
esta rama.

### Qué se hizo

Se inspeccionó el contenido antes de tocar nada, en vez de asumir
cualquier cosa sobre su origen o forzar un push. El diff (`git diff
1150920 origin/main`) mostró exactamente 2 archivos, ambos coherentes con
el hallazgo "al margen" que había quedado como sugerencia sin ejecutar
(`task_596c1939`, tooltip ORCID codificado a "Crossref" en la tabla de
autores):

- `src/build/03_authors.py`: agrega `"orcid_estado": estado_orcid(nombre,
  fuente_orcid)` al JSON publicado de un segundo bloque de autores (la
  función `estado_orcid` y su uso en el primer bloque ya existían).
- `web/assets/js/paginas.js`: el `title` del tooltip pasa de fijo
  `"ORCID recuperado desde Crossref · confianza ..."` a `` `ORCID:
  ${c.escapar(a.orcid_estado)} · confianza ...` ``, usando el campo nuevo.

Es exactamente el fix correcto para el bug reportado: alguien —no esta
sesión— tomó la sugerencia en algún momento y la resolvió por su cuenta,
en paralelo. Se verificó sintaxis de ambos archivos y que
`orcid_estado` esté referenciado correctamente antes de aceptar el
merge.

Como los archivos tocados por `origin/main` (`03_authors.py`,
`paginas.js`) no se solapan con los del cierre de esta rama
(`SESSION_NOTES.md`, `STATE.md`, `docs/DECISIONS.md`), el merge
(`git merge origin/main`, sin `--ff-only` porque las dos ramas habían
divergido de verdad) resolvió sin conflictos. Se empujó el resultado
(`c86075e`) a `origin/main`.

Se intentó retirar la sugerencia `task_596c1939` con `dismiss_task`; la
herramienta respondió que ya había sido iniciada por el usuario y por
tanto no admite retiro — confirma independientemente que el fix vino de
esa sugerencia siendo tomada, no de una coincidencia.

### Verificación

- `python3 -c "import ast; ast.parse(...)"` sobre `03_authors.py`: sin
  errores de sintaxis.
- Verificación de texto de que `paginas.js` referencia `orcid_estado`.
- `git diff --quiet` tras el merge: limpio, nada sin commitear.
- `git push origin main`: `b6ea061..c86075e main -> main`, sin rechazo.

No se corrió el pipeline de build completo para este addendum — el
cambio no es de esta sesión, ya llegó revisado y fusionado vía su propio
PR (#39), y el diff es mínimo y de sintaxis verificable. Si hiciera falta
una verificación de build end-to-end sobre este fix específico, queda
pendiente (ver "Próximo paso recomendado").

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-455 | Ante una `origin/main` que avanzó de forma inesperada, se inspecciona el diff completo antes de fusionar o empujar nada | Evita tanto perder trabajo ajeno (pisándolo) como aceptar a ciegas algo no verificado; en este caso el diff era pequeño y se pudo leer entero |
| D-456 | Se hace un merge commit normal (no fast-forward) entre esta rama y `origin/main`, en vez de forzar o descartar cualquiera de los dos lados | Las ramas habían divergido de verdad (cada una con commits que la otra no tenía) — un fast-forward ya no aplicaba, y los archivos no se solapaban, así que un merge commit es la operación mínima que conserva ambos lados |

### Archivos modificados

```
(ninguno de código nuevo en esta sesión — se fusionó c86075e, que trae
 src/build/03_authors.py y web/assets/js/paginas.js de PR #39)
SESSION_NOTES.md   (este addendum)
```

### Supuestos descartados

- Que `origin/main` seguiría en el mismo commit que la última vez que se
  revisó: se volvió a hacer `git fetch` justo antes de empujar, como
  indica la práctica ya establecida en esta sesión, y eso fue lo que
  reveló la divergencia.
- Que la divergencia ameritaba forzar el push de esta rama por encima:
  se leyó el contenido ajeno primero; resultó ser trabajo legítimo y se
  conservó vía merge.

### Ambigüedades abiertas

Del cierre anterior, sólo queda uno de los dos hallazgos "al margen": el
tooltip ORCID (`task_596c1939`) ya está resuelto por PR #39 y fusionado
a `main`. Sigue pendiente únicamente Fortuny como candidato de "Varios
Scopus ID" (en la cola, esperando revisión humana).

No se investigó quién ni cómo generó el PR #39 (otra sesión, otra
persona, u otra corrida) — no era necesario para reconciliar el estado
del repositorio, y esta nota no debe leerse como una atribución
verificada del autor del fix.

### Próximo paso recomendado

`main` y `claude/state-review-next-steps-wzzq0h` divergen ahora en un
commit: `main` tiene el merge `c86075e` (con el fix de PR #39) que esta
rama no tiene. Dado que esta rama ya cumplió su propósito (todo el
trabajo de identidad/conectores/CI de esta sesión ya está en `main`), no
se sincronizó ese último commit hacia acá — no hace falta para nada
pendiente en esta rama. Si una sesión futura retoma esta rama, conviene
traer `main` primero (`git merge origin/main` o similar) antes de seguir
trabajando, para no perder de vista el fix del tooltip.

Sitio, CI y ambas ramas en un estado consistente y verificado. Sesión
cerrada.

## Cierre: se resuelve el pendiente de Fortuny en la cola de "Varios Scopus ID"

### Contexto

El usuario pidió un balance de las revisiones de identidad. Al revisarlo
se detectó y corrigió una imprecisión propia: la cifra "Varios Scopus ID:
1 pendiente" que se había reportado como si fuera Fortuny en realidad
correspondía a "Moya, Patricia" — son dos colas distintas que comparten
nombre de categoría pero no de mecanismo. `internal/pendientes_consolidacion.md`
(los "290 casos / 83 pendientes") se genera sólo de
`internal/identity_decisions.csv`, y Fortuny nunca entró ahí: vive
exclusivamente en `internal/scopus_author_search_multiples_id.csv`, la
cola nueva que produce `candidatos_fragmentacion_orcid()`
(`src/enrich/scopus_author_search.py`, agregado el 2026-09-03). El
usuario pidió entonces cerrar ese pendiente puntual.

### Qué se hizo

Se siguió el mecanismo vigente de esa cola —no `identity_decisions.csv` +
`apply_decisions.py`, que es el canal usado para "Varios Scopus ID" en una
generación anterior de esta misma cola (los casos `p04-*`, ya resueltos en
su momento) pero no el que se usó esta sesión para los candidatos nuevos
("Esis Villarroel, Ivette S.", agregada el 2026-09-02, siguió el otro
canal—:

1. Se agregó una fila para "Fortuny, Esteban Fortuny" en
   `internal/scopus_author_search_decisiones.csv` con veredicto `misma` y
   la evidencia: el ORCID `0000-0002-0864-5669` que el proyecto ya tenía
   asignado a "Fortuny E." (declarado por el propio titular) coincide,
   confirmado de forma independiente, con el que Scopus Author Search
   asigna al perfil "Fortuny, Esteban Fortuny" (Auth-ID distinto, 3
   documentos, mismo campo Medicine/salud) — mismo patrón de convergencia
   de ORCID entre dos fuentes independientes ya usado para confirmar a
   Esis Villarroel en esta cola.
2. Se corrió `python3 src/review/apply_scopus_author_decisions.py
   --dry-run` (1 cambio, sólo Fortuny) y luego sin `--dry-run`: la columna
   `resolucion` de su fila en `scopus_author_search_multiples_id.csv` pasó
   de `PENDIENTE_REVISION_HUMANA` a `CONFIRMADO_MISMA_PERSONA`.
3. Se actualizó la nota (2) de `internal/scopus_author_search_listado.html`
   de "Entrado a la cola" (naranja) a "Resuelto" (verde), documentando el
   mecanismo de aplicación y dejando explícito que la confianza del ORCID
   en `data/enriched/authors_orcid.csv` NO se tocó (sigue en "media").
4. Se corrigió `docs/FUENTES_Y_APIS.md` §2.9: decía "7 nombres" en la cola
   cuando ya eran 8 desde que se agregó Fortuny (2026-09-03) y no mencionaba
   el segundo detector ni el estado de revisión. Ahora dice 8, describe
   `candidatos_fragmentacion_orcid()` y resume el estado real: 2
   confirmados, 6 pendientes.

Esta resolución no cambia ninguna firma del proyecto ni ninguna cifra
pública: "Fortuny E." ya era una única firma en el corpus; lo que se
confirmó es que el Auth-ID adicional que ve Scopus Author Search
corresponde a la misma persona, no a una homonimia. Es puramente capa
interna (evidencia de identidad, D-08).

### Verificación

- `apply_scopus_author_decisions.py --dry-run` mostró exactamente 1
  cambio (Fortuny) antes de aplicar — ninguno de los otros 6 pendientes se
  tocó.
- Tras aplicar, se releyó `scopus_author_search_multiples_id.csv` completo
  y se confirmó que sólo la fila de Fortuny cambió de `resolucion`.
- Se verificó que este conector no está encadenado en ningún pipeline
  automático (`Makefile`, `.github/workflows/`, `config/sources.yml` sólo
  lo referencia como conector manual) — la resolución no corre riesgo de
  perderse en la próxima corrida de CI, a diferencia del bug ya documentado
  antes en esta sesión (regenerar el conector a mano sí resetea la cola;
  correr `--test` en CI no).

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-457 | Fortuny se resuelve por `scopus_author_search_decisiones.csv` + `apply_scopus_author_decisions.py`, no por `identity_decisions.csv` | Es el mecanismo que esta sesión ya usó para el resto de los candidatos nuevos de esta misma cola (Esis Villarroel); usar el otro canal habría creado dos registros de la misma decisión en dos archivos, sin necesidad |
| D-458 | No se sube la confianza del ORCID de "Fortuny E." en `authors_orcid.csv` al resolver este pendiente | Sigue el precedente literal ya sentado para "Esis Villarroel" en esta misma cola esta sesión (tampoco se subió la suya); cambiar el criterio sólo para Fortuny sería inconsistente sin una razón declarada — se deja como ambigüedad abierta en vez de decidirlo por mi cuenta |

### Archivos modificados

```
internal/scopus_author_search_decisiones.csv    + fila Fortuny (misma)
internal/scopus_author_search_multiples_id.csv  resolucion actualizada
internal/scopus_author_search_listado.html      nota (2): pendiente → resuelto
docs/FUENTES_Y_APIS.md                          §2.9: 7→8 nombres, detector nuevo, estado real
SESSION_NOTES.md, STATE.md, docs/DECISIONS.md   este cierre
```

### Supuestos descartados

- Que el "Varios Scopus ID: 1 pendiente" reportado en la respuesta anterior
  era Fortuny: era Moya, Patricia. Se corrige explícitamente aquí en vez de
  dejar la afirmación anterior sin corregir.
- Que resolver este pendiente debía también subir la confianza del ORCID
  en `authors_orcid.csv` (por analogía con las 12 confirmaciones de
  apellido compuesto de antes en la sesión): se decidió NO hacerlo, para
  no romper la consistencia con "Esis Villarroel", que se resolvió sin ese
  paso.

### Ambigüedades abiertas

Si las confirmaciones de esta cola ("Varios Scopus ID") deberían subir la
confianza del ORCID en `authors_orcid.csv` cuando la evidencia es
convergencia de ORCID entre dos fuentes independientes — el mismo tipo de
evidencia que sí subió la confianza en la cola de apellido compuesto. Hoy
el comportamiento es inconsistente entre colas (una sube, la otra no) y
nadie lo ha decidido explícitamente; afecta también a "Esis Villarroel",
ya resuelta antes de este cierre.

Siguen pendientes, sin cambios en este cierre: los 6 casos restantes de
"Varios Scopus ID" (Cabello, Caffarena, Hartmann Schatloff, Moya Patricia,
Quezada, Torres) y los 83 casos de `internal/pendientes_consolidacion.md`.

### Próximo paso recomendado

Ninguna acción de código pendiente sobre Fortuny — cerrado. Si se quiere
seguir con la revisión de identidad, las colas más grandes siguen siendo
"Candidato de unidad académica por autoarchivo" (29) y "ORCID no
verificable" (22) en `internal/pendientes_consolidacion.md`, o cualquiera
de los 6 restantes en `scopus_author_search_multiples_id.csv`.

## Cierre: se resuelve el pendiente de Moya, Patricia en la cola de "Varios Scopus ID"

### Contexto

El usuario pidió seguir con "Moya, Patricia", el único caso que quedaba
`pendiente` en `internal/identity_decisions.csv` bajo la cola "Varios
Scopus ID" (`p04-Moya, Patricia`, decidido `pendiente` el 2026-09-02): el
Auth-ID 57767862900 firma tanto «atención de urgencia por ideación
suicida» (Salud Pública) como «determinantes de caries en preescolares»
(Facultad de Odontología) — dos temas que entonces parecían demasiado
distintos bajo un mismo identificador para cumplir el umbral de evidencia
dispositiva del proyecto, más que en los otros 9 casos revisados junto a
este en su momento.

### Qué se hizo

Se reunió evidencia local que no se había cruzado antes:

1. El ORCID de "Moya P." (`0000-0002-8442-2571`) ya estaba confirmado por
   otra vía, independiente de este caso: `ver-Moya P.`, cola "ORCID sin
   confirmar", 2026-09-01 — acuerdo entre repositorio institucional e
   inventario de autoarchivo, 3 publicaciones cruzadas cada uno.
2. Se buscó ese ORCID directamente en `data/raw/Inventario_Repositorio_
   Institucional_UFT.csv` (24 registros bajo "Moya, Patricia" o variantes
   cercanas). El campo `dc.contributor.orcid` —el campo limpio de un solo
   valor, no la lista mezclada de `dc.identifier.orcid`— lo declara
   directamente sobre "Atención de urgencia por ideación suicida en
   Chile": exactamente la publicación que generaba la duda, y coincide con
   el DOI y el Auth-ID (57767862900) del registro en el corpus Scopus.
3. Se cruzó `internal/matching_log.csv` para ver la afiliación declarada
   exacta de cada aparición de "Moya P." en el corpus: una de las dos
   publicaciones bajo 57767862900 (EID 2-s2.0-105024529012, que en
   realidad es la de bibliometría de ansiedad, firmada por Auth-ID
   60235456000 — se verificó el emparejamiento EID↔Auth-ID contra el
   export nativo de Scopus, no se asumió) declara "Salud Pública, Facultad
   de Odontología, Universidad Finís Terrae" — una unidad de salud pública
   **dentro** de la Facultad de Odontología. Esto reconcilia exactamente
   la tensión que dejó el caso pendiente: no son dos campos distintos, es
   un perfil de salud pública aplicada a la práctica odontológica.
4. El export nativo de Scopus (`Authors with affiliations`) confirmó lo
   mismo para el Auth-ID 60235456000: "Observatorio en Salud Pública Oral,
   Facultad de Odontología, Universidad Finís Terrae".
5. `data/raw/Scopus_Author_Search_UFT.csv` declara el mismo nombre
   completo exacto, "Moya, Patricia", para ambos Auth-ID, con área
   temática superpuesta ("Dentistry" en los dos; el 57767862900 agrega
   "Medicine").

Con esa evidencia se revirtió el veredicto:

- `internal/identity_decisions.csv`: caso `p04-Moya, Patricia` de
  `pendiente` a `misma`, nota reescrita con la evidencia nueva, fecha
  actualizada a 2026-09-03.
- `internal/scopus_author_search_decisiones.csv`: se agregó una fila
  equivalente para "Moya, Patricia" (`misma`), para no dejar las dos colas
  diciendo cosas distintas — la confusión de la respuesta anterior sobre
  cuál pendiente era cuál ya mostró el costo de no mantenerlas coherentes.
- Se aplicaron ambas: `apply_decisions.py` y
  `apply_scopus_author_decisions.py`.
- Se regeneró `internal/pendientes_consolidacion.{md,html}` y
  `internal/revision_identidad.html` con `src/review/build_review.py`
  (herramienta declarada "GENERADO, no editar a mano").
- Se actualizó `internal/scopus_author_search_listado.html` (fila de Moya
  en la tabla de "ya conocidos", más una nota nueva (3) con el detalle
  completo) y el conteo de `docs/FUENTES_Y_APIS.md` §2.9 (2→3
  confirmados, 6→5 pendientes).

### Verificación

- `apply_decisions.py --dry-run` antes de aplicar: sin avisos de
  contradicción, sin cambio en "grupos consolidados" (38, igual que
  antes) — confirma la hipótesis de que la firma "Moya P." es un grupo de
  una sola forma en `firmas_de()`, así que esta decisión no fusiona nada
  nuevo, sólo confirma que el segundo Auth-ID no es una persona distinta.
- Tras aplicar de verdad, `git diff` sobre `config/identidades_
  consolidadas.yml`, `config/orcid_revisado.yml`,
  `config/firmas_e09_resueltas.yml` y `data/enriched/authors_orcid.csv`
  salió vacío — verificado explícitamente, no asumido: esta decisión no
  cambia ningún artefacto que el build consuma, sólo la capa interna de
  evidencia.
- `apply_scopus_author_decisions.py --dry-run` mostró exactamente 1 cambio
  (Moya) antes de aplicar.
- `build_review.py` recalculó 290 casos, 208 decididos, 82 pendientes
  (antes: 207/83) — baja en 1, como corresponde.
- Se confirmó con un `grep` dirigido que la sección "Varios Scopus ID" de
  `pendientes_consolidacion.md` desapareció del todo (quedó en 0
  pendientes entre las dos colas combinadas).

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-459 | Se revierte el veredicto `pendiente` de `p04-Moya, Patricia` a `misma` | Evidencia nueva (ORCID declarado directamente sobre la publicación en disputa, en el repositorio institucional; unidad de salud pública dentro de la propia Facultad de Odontología en ambos Auth-ID) supera el umbral de evidencia dispositiva que dejó el caso pendiente el 2026-09-02; no es una decisión tomada por rutina ni por analogía con los otros casos, es evidencia directa sobre este caso específico |
| D-460 | Se mantienen sincronizadas `identity_decisions.csv` y `scopus_author_search_decisiones.csv` para el mismo caso, en vez de decidir sólo en una | La sesión anterior ya mostró el costo de que las dos colas divergieran silenciosamente (la confusión Fortuny/Moya en la respuesta al usuario); duplicar el registro es más barato que dejarlas incoherentes otra vez |

### Archivos modificados

```
internal/identity_decisions.csv                   p04-Moya: pendiente → misma
internal/scopus_author_search_decisiones.csv       + fila Moya (misma)
internal/scopus_author_search_multiples_id.csv     resolucion actualizada
internal/scopus_author_search_listado.html         fila Moya + nota (3)
internal/pendientes_consolidacion.md, .html        regenerados (build_review.py)
internal/revision_identidad.html                   regenerado (build_review.py)
docs/FUENTES_Y_APIS.md                             §2.9: 2→3 confirmados, 6→5 pendientes
SESSION_NOTES.md, STATE.md, docs/DECISIONS.md      este cierre
```

Sin cambios en `config/identidades_consolidadas.yml`, `config/orcid_
revisado.yml`, `config/firmas_e09_resueltas.yml` ni
`data/enriched/authors_orcid.csv` — verificado, no sólo esperado.

### Supuestos descartados

- Que la evidencia de "unidad exacta y mismo tema" (el criterio usado
  para Castillo/Hartmann/Quezada/Torres) era necesaria para este caso: se
  usó evidencia más directa y más fuerte (ORCID declarado sobre la
  publicación puntual en disputa, desde una fuente independiente), no la
  misma plantilla aplicada mecánicamente.
- Que revertir un veredicto `pendiente` anterior requería descartar la
  duda original como un error: no lo era — la dispersión temática
  observada en 2026-09-02 era real y razonable de cuestionar; lo que
  cambió es que apareció evidencia nueva, no que la duda original fuera
  infundada.

### Ambigüedades abiertas

Las mismas que dejó el cierre de Fortuny, sin cambios: si esta cola
("Varios Scopus ID") debería subir la confianza del ORCID en
`authors_orcid.csv` al confirmarse (no se hizo aquí tampoco, siguiendo el
mismo precedente que Esis Villarroel y Fortuny).

Siguen pendientes, sin tocar en este cierre: los 5 casos restantes de
"Varios Scopus ID" (Cabello, Caffarena, Hartmann Schatloff, Quezada,
Torres) y los 82 casos de `internal/pendientes_consolidacion.md`.

### Próximo paso recomendado

Ninguna acción de código pendiente sobre Moya — cerrado. De los 5 casos
restantes en esta cola, Hartmann Schatloff, Quezada y Torres ya tenían
`misma` en una generación anterior de `identity_decisions.csv` (2026-09-02,
antes del detector actual) pero siguen `PENDIENTE_REVISION_HUMANA` en
`scopus_author_search_multiples_id.csv` — la misma clase de
inconsistencia entre colas que se acaba de corregir para Moya, sin
resolver todavía para esos tres. Sería el siguiente candidato natural si
se sigue con esta cola.

## Cierre: fusión de firmas por convergencia de ORCID no consolidada ("Tier A")

### Contexto

El usuario preguntó cuántos autores afiliados tiene UFT 2023-2025 (589
formas / 536 entidades consolidadas), y a partir de ahí pidió un listado
de posibles autores fusionables para aprobar. En vez de limitarme a las
colas ya trabajadas esta sesión (Varios Scopus ID, Variantes de nombre
pendientes — 0 en la herramienta de revisión), se buscó una fuente nueva:
firmas que comparten el mismo ORCID en `data/enriched/authors_orcid.csv`
sin estar fusionadas en `config/identidades_consolidadas.yml`. El cruce
(agrupando por ORCID, descartando grupos ya totalmente consolidados, y
verificando cada uno contra `internal/matching_log.csv` para confirmar
apariciones reales en el corpus y coincidencia de unidad académica)
encontró 22 grupos. Se presentaron en tres niveles (Tier A: variante
ortográfica/de forma con evidencia adicional; Tier B: apellido compuesto
truncado sin verificar; Tier C: sin patrón claro) y el usuario pidió
aplicar el Tier A (8 grupos).

### Qué se hizo

Antes de escribir las 8 decisiones se revisó la fuerza real de cada una
—no sólo la similitud de cadena— y se detectaron dos problemas que
cambiaron el alcance de lo aplicado:

1. **2 de los 8 (Gómez G./Gómez G.G., Macho R.A.M./Macho R.M.) tenían
   evidencia más débil que el resto**: en ambos casos, las dos firmas del
   par comparten el mismo ORCID por la MISMA fuente no independiente
   (OpenAlex las dos — ver la advertencia ya documentada en
   `docs/FUENTES_Y_APIS.md` §3.1 sobre que OpenAlex ingiere Crossref y no
   cuenta como segunda fuente), sin ninguna unidad académica que corrobore
   en el corpus. Se comunicó esto al usuario antes de aplicar nada; quedan
   fuera de esta fusión.
2. **Al preparar las notas de los 6 restantes, se encontró que 3 ya tenían
   una fusión PARCIAL decidida previamente** que mis notas originales no
   reflejaban (afirmaban «nunca antes decidido»): `p03-nunezlisboa`
   (2026-08-26, 2 de 5 formas), `p03-moyanodavila` (2026-08-05) +
   `orcid-0000-0002-6357-3469` (2026-09-01, juntas cubrían 3 de 4 formas),
   `p03-martinezmardones` (2026-08-26, 2 de 4 formas). Se corrigieron las
   tres notas para decir exactamente qué ya estaba fusionado y qué se
   agregaba de nuevo, antes de aplicar — no se dejó una nota inexacta en
   un archivo de registro auditado.
3. **Al correr `apply_decisions.py --dry-run`, un chequeo cruzado contra
   `config/orcid_revisado.yml` (la lista `retiradas`, que registra qué
   ORCID el pipeline dejará de usar por decisiones previas de tipo
   `orcid_incorrecto`) encontró que 2 de los 6 grupos usaban como base
   exactamente un ORCID ya retirado**:
   - `Vasquez F.` tiene su ORCID (`0000-0003-1769-3969`, el mismo que
     comparte con `Vásquez F.`) marcado `orcid_incorrecto` por una
     decisión previa (`noverif-Vasquez F.`, cola "ORCID no verificable",
     2026-08-26). La fusión propuesta se apoyaba precisamente en ese
     ORCID compartido — con la base inválida, la evidencia desaparece.
     **Se retiró del todo, no se aplicó.**
   - El grupo Moyano/Dávila tiene el mismo problema en 2 de sus 4 formas:
     `Moyano Davila C.` y `Moyano Dávila C.` tienen su ORCID
     (`0000-0002-6357-3469`) marcado `orcid_incorrecto` (2026-08-26) —
     pero ese mismo ORCID YA estaba siendo usado por dos decisiones de
     fusión más recientes y todavía vigentes (`p03-moyanodavila`,
     2026-08-05, y `orcid-0000-0002-6357-3469`, cola "ORCID compartido",
     2026-09-01). Es una **contradicción preexistente en el propio
     historial de decisiones del proyecto**, de antes de esta sesión, que
     no se investigó a fondo (no hay nota en ninguna de las decisiones
     involucradas, ni rastro en `SESSION_NOTES.md` de por qué se marcó
     incorrecto ese ORCID). No se resolvió por mi cuenta: **se retiró mi
     adición** (la cuarta forma, `Dávila C.M.`, que habría profundizado la
     contradicción sin aportar nada a resolverla) **y se deja la
     contradicción existente declarada, sin tocar**, como ambigüedad
     abierta para que la resuelva una persona.

Con eso, se aplicaron finalmente **4 de los 8** grupos originales del
Tier A:

| Grupo | Formas fusionadas | Evidencia |
|---|---|---|
| `orcidconv-nunezlisboa` | 5 (2 ya fusionadas + 3 nuevas) | Mismo ORCID por dos linajes de fuente independientes (ORCID declarado + Crossref), misma unidad (Facultad de Medicina y Salud) en las 5 |
| `orcidconv-yanine` | 2 (nuevo grupo) | Mismo ORCID por dos linajes independientes (Crossref + ORCID declarado), ambas ya `orcid_correcto` confirmado por separado (2026-09-01), misma unidad (Facultad de Ingeniería) |
| `orcidconv-martinezmardones` | 4 (2 ya fusionadas + 2 nuevas) | Mismo ORCID, 3 de 4 ya `orcid_correcto` confirmadas por separado, misma unidad donde hay dato (Facultad de Medicina y Salud) |
| `orcidconv-busquets` | 2 (nuevo grupo) | Mismo ORCID; una de las dos ya tenía revisión humana previa (candidato por afiliación, confianza alta) |

### Verificación

- `apply_decisions.py --dry-run` corrido dos veces: una tras escribir las
  6 notas corregidas (sin avisos de contradicción sobre los grupos
  nuevos), otra tras retirar Vasquez y Moyano (39 grupos, 94 formas —
  antes 38/87).
- Se cruzaron programáticamente los 6 grupos candidatos contra las listas
  `confirmadas`/`retiradas`/`sin_registro` de `config/orcid_revisado.yml`
  antes de la corrida real, no después — así se encontró el problema de
  Vasquez/Moyano antes de escribir nada en `identidades_consolidadas.yml`.
- Tras aplicar de verdad: `git diff --stat` confirma que sólo cambió
  `config/identidades_consolidadas.yml` (los otros tres artefactos que
  genera `apply_decisions.py` — `orcid_revisado.yml`,
  `firmas_e09_resueltas.yml`, `authors_orcid.csv` — no cambiaron, porque
  estas 4 decisiones son puras fusiones de nombre, no tocan asignación de
  ORCID). Se inspeccionó el YAML resultante grupo por grupo: los 4 grupos
  nuevos/ampliados tienen exactamente las formas esperadas, ninguna con
  Vasquez ni con la cuarta forma de Moyano.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-461 | Se retira `orcidconv-vasquez` de la aplicación, pese a la instrucción de aplicar todo el Tier A | Su única evidencia (ORCID compartido) está construida sobre un ORCID que una decisión previa (2026-08-26) ya calificó de incorrecto para esa firma; aplicar hubiera fusionado dos personas con una base ya invalidada |
| D-462 | Se retira la adición de «Dávila C.M.» al grupo Moyano, pero NO se toca el grupo ya existente (3 formas) que comparte el mismo problema | El grupo ya existente es una decisión previa vigente, tomada por una persona en su momento; no me corresponde deshacerla por mi cuenta al notar la contradicción — se declara la contradicción, no se resuelve unilateralmente (regla del proyecto sobre ambigüedades) |
| D-463 | Se corrigen 3 notas antes de aplicar, en vez de dejarlas con la afirmación inexacta «nunca antes decidido» | Es un archivo de registro auditado (`internal/identity_decisions.csv`); una nota que dice algo falso sobre el estado previo del caso es un error de integridad de datos, no un detalle menor |

### Archivos modificados

```
internal/identity_decisions.csv       + 4 decisiones aplicadas (nunezlisboa, yanine, martinezmardones, busquets)
config/identidades_consolidadas.yml   38→39 grupos, 87→94 formas
SESSION_NOTES.md, STATE.md, docs/DECISIONS.md   este cierre
```

Nota: `config/orcid_revisado.yml`, `config/firmas_e09_resueltas.yml` y
`data/enriched/authors_orcid.csv` NO cambiaron (verificado con `git diff`),
pese a que `apply_decisions.py` los regenera en cada corrida — su
contenido resultante es idéntico al de antes de esta sesión de fusiones.

### Supuestos descartados

- Que las 8 firmas del Tier A tenían todas evidencia equivalente porque
  compartían un ORCID: no era cierto — 2 tenían fuente única no
  independiente sin corroboración (Gómez, Macho), y 2 más tenían el ORCID
  compartido directamente invalidado por una decisión previa (Vasquez, y
  parcialmente Moyano). Aplicar sin este chequeo habría escrito fusiones
  con una base de evidencia falsa en un archivo que el proyecto trata como
  registro auditado.
- Que la instrucción «Aplica Tier A» obligaba a aplicar las 8 tal como se
  presentaron: se interpretó como autorización sobre el TIPO de fusión
  (evidencia de ORCID + coherencia de forma/unidad), no como una orden de
  escribir decisiones concretas sin volver a mirar la evidencia una vez
  redactada — la instrucción no pudo prever el hallazgo de una
  contradicción con `orcid_revisado.yml`, que sólo apareció al preparar la
  aplicación real.

### Ambigüedades abiertas

**Nueva, importante:** el grupo Moyano (`Moyano C.` / `Moyano Davila C.` /
`Moyano Dávila C.`, ORCID `0000-0002-6357-3469`) tiene una contradicción
sin resolver en el propio historial del proyecto: una decisión de
2026-08-26 (`noverif-Moyano Davila C.`, `noverif-Moyano Dávila C.`, cola
"ORCID no verificable") calificó ese ORCID de incorrecto para esas dos
firmas, pero dos decisiones de fusión posteriores y vigentes
(`p03-moyanodavila`, 2026-08-05 — anterior en fecha pero no revocada; y
`orcid-0000-0002-6357-3469`, cola "ORCID compartido", 2026-09-01 —
posterior) siguen usando ese mismo ORCID como base para fusionar a estas
personas. Ninguna de las decisiones en conflicto tiene nota que explique
el porqué, y no hay rastro en `SESSION_NOTES.md`. No se investigó más ni
se resolvió — queda declarada para que una persona decida cuál veredicto
prevalece.

Siguen abiertos, sin tocar en este cierre: Tier B (13 grupos, patrón de
apellido compuesto truncado, sin la verificación de posición que sí se
hizo para casos anteriores como Fernández Abara); Tier C (Bilicic
D./Ubierna D.B.B., sin patrón claro); Gómez G./Gómez G.G. y Macho
R.A.M./Macho R.M. del propio Tier A, retirados por evidencia insuficiente
más que por contradicción.

**Cifra pública desactualizada:** la fila "Entidades de autor publicadas"
de `STATE.md` (536) viene de `data/processed/authors.json`
(`data/processed/` es artefacto de build, gitignored) y NO se recalculó
con esta fusión — `snapshot.py` no reconstruye el sitio, sólo lee lo que
ya existe. Con 94 formas / 39 grupos la cifra real tras un build sería
589 − 94 + 39 − 4 = **530**, no 536. La fila de texto ("87 formas... 38
personas" → "94 formas... 39 personas") sí se actualizó porque viene
directo de `identidades_consolidadas.yml`. No se corrió el pipeline de
build en este cierre — sigue pendiente.

### Próximo paso recomendado

Si se quiere que el recuento público (536→530) y las fichas de autor
reflejen estas 4 fusiones, hace falta correr el pipeline de build
(`python3 src/build/build_all.py` o `make sitio`) y, si se despliega,
repetir el ciclo de verificación ya establecido esta sesión (CI, revisión
visual). Como siguiente ronda de identidad: resolver la contradicción de
Moyano (ambigüedad abierta arriba) antes de decidir si agregar «Dávila
C.M.»; o pedir la verificación de posición del Tier B, el mismo método
que ya se usó para Fernández Abara/Amarouch/Fortuny, para elevarlo a un
nivel de evidencia aplicable.

## Cierre: `PD-04` — la cuarta fuente fuera de Scopus, Nivel V, sobre repositorios de datos y acceso abierto (2026-09-03)

### Contexto

El usuario pidió primero un resumen del trabajo de esa misma tarde
(conectores ORCID de DataCite/Europe PMC/Zenodo/GitHub, la herramienta
de `informes/`, consolidación de identidad) y después preguntó **"¿de
qué forma es posible incluir las publicaciones fuera de Scopus/SciVal?"**
Sobre la respuesta —el marco de `docs/METODOLOGIA_FUERA_DE_SCOPUS.md`,
que ya define dos niveles de evidencia y tres indicadores publicados—
autorizó explícitamente: **"avancemos con esa cuarta fuente de nivel V"**.

La oportunidad concreta: las tres fuentes que entraron esa misma tarde
sólo se consultaban **por DOI del universo**, para recuperar el ORCID de
sus autores. Esa dirección sólo puede mirar hacia adentro. Las mismas
tres APIs indexan datasets, software, preprints y materiales depositados
que ningún índice bibliográfico cubre bien — y nadie se lo había
preguntado.

### La restricción del entorno, comprobada antes de escribir nada

La política de red de este entorno bloquea `api.datacite.org`,
`www.ebi.ac.uk` y `zenodo.org`: 403 en el CONNECT del proxy, verificado
con `curl` sobre los tres hosts y contra `__agentproxy/status`, no
supuesto. Igual que `api.crossref.org` y `api.openalex.org`. Es el mismo
precedente de `crossref_financiamiento.py` (2026-09-02): se construye y
se prueba el mecanismo, la corrida real la hace el usuario desde otra
red. Se le dijo antes de empezar, no al entregar.

### Qué se construyó

- **`src/enrich/obras_externas.py`** — recupera obras de las tres
  fuentes por dos vías, criba contra `publications_universe.csv` y deja
  `internal/obras_externas_cobertura.csv` como cola de revisión.
- **`src/review/build_obras_externas_review.py`** — la herramienta de
  revisión, con cuatro veredictos.
- **`src/review/apply_obras_externas_review.py`** — aplica el CSV
  exportado sobre la columna `resolucion`.
- **`src/build/09_produccion_declarada.py`** — bloque de agregación de
  `PD-04` y su entrada en el total combinado.
- **`web/assets/js/vista.js`** — la cuarta sección de
  `produccion-ampliada.html`.
- **`config/sources.yml`** — las cuatro fuentes de esa tarde
  (DataCite, Europe PMC, Zenodo, GitHub), que **no estaban declaradas**;
  `config/indicators.yml` — `PD-04`; `Makefile` — dos objetivos;
  `.github/workflows/deploy.yml` — tres `--test` nuevos.

### Las decisiones que costaron pensar

**Por qué NO reutiliza la cola de `PD-02`, aunque sean el mismo nivel.**
La tentación era obvia: las dos son Nivel V, las dos terminan en
`CONFIRMADO_PRODUCCION_UFT`. Pero la cola de OpenAlex se identifica por
`openalex_id` —una obra, un identificador— y ésta necesita
`(fuente, id_fuente)`, porque la misma obra puede estar en los tres
repositorios y cada uno se decide por separado (la evidencia que aporta
cada uno es distinta). Además hay obras sin DOI, que con clave por DOI
se pisarían todas entre sí. Y el vocabulario de veredictos no coincide.
Forzar una sola cola habría exigido que la clave y los veredictos de
`PD-02` aceptaran casos que no son suyos — exactamente lo que `PD-03`
evitó al no meterse en el mecanismo de `PD-01`.

**Qué sí se comparte.** La INTERACCIÓN de la herramienta de revisión
—marcar, filtrar, guardar en el navegador, exportar el CSV— no tiene
contenido metodológico: es presentación. Copiar sus ~120 líneas de
JavaScript habría significado corregir cada bug de exportación dos veces
y descubrir la segunda copia tarde. Se parametrizó
`build_openalex_review.py` (clave de navegador, columnas de identidad,
nombre del CSV, cabecera de comentario) y el nuevo módulo la importa.
La salida de la herramienta de OpenAlex se verificó idéntica en
estructura tras el cambio.

**El cuarto veredicto, que ninguna otra cola necesita.** Zenodo acuña un
DOI por cada versión de un depósito, además del DOI de concepto;
DataCite indexa preprints cuya versión publicada sí está en Scopus. Son
DOI distintos para la misma obra, y la deduplicación por DOI —el único
mecanismo de deduplicación del proyecto— no puede colapsarlos. La obra
SÍ es de la institución, así que meterlo en "atribución errónea" habría
perdido la distinción y, con ella, la capacidad de saber si la cola está
llena de homónimos o de versiones repetidas: dos diagnósticos con
soluciones distintas.

**Las dos vías de recuperación, y por qué la débil se conserva.** La vía
por ORCID parte de un identificador de persona ya confirmado. La vía por
afiliación parte de una cadena de texto, que `I-05` prohíbe como base de
una atribución. No se descartó porque las 267 firmas sin ORCID son
invisibles a la vía fuerte por construcción; se conserva declarando que
no atribuye nada —sólo propone un candidato— y la advertencia del
homónimo va en la tarjeta del caso, no en una nota al pie que nadie
relaciona con lo que tiene delante.

**Los ORCID retirados no fundan búsquedas.** `config/orcid_revisado.yml`
lista 18 asignaciones que una persona declaró incorrectas para esa firma.
Usarlas para recuperar "obras de esa persona" habría reconstruido, del
lado de las obras, el error que esa decisión ya descartó del lado de los
autores. Se excluyen, y hay un caso de prueba que lo comprueba.

**Las plantillas de consulta salen de `config/sources.yml`.** El
guardarraíl técnico de `CLAUDE.md` pide que otra institución adapte el
sistema cambiando parámetros, no reescribiendo lógica. Las tres cadenas
de búsqueda viven en `consulta_obras`, con `{orcid}` y `{institucion}`
como únicos marcadores; hay un caso de prueba que verifica que ninguna
cadena de consulta esté escrita en el código.

**Reejecutar no borra revisiones.** La cola se reconstruye entera en cada
corrida, pero `resolucion` es trabajo humano. Se conserva emparejando por
`(fuente, id_fuente)`. `openalex_cobertura.py` NO hace esto: reejecutarlo
hoy pondría en `PENDIENTE` las 20 confirmaciones existentes. Se declara
como ambigüedad abierta, no se corrigió — es otro indicador y no estaba
en el encargo.

### Tres defectos reales encontrados de paso

1. **`build_openalex_review.py` no se podía ejecutar.** `_leer_previas()`
   exigía una columna `nota` que el `openalex_cobertura_decisiones.csv`
   versionado no tiene (sólo `openalex_id,veredicto`): `KeyError: 'nota'`.
   Verificado que es previo a esta sesión (`git stash` y reejecutar sobre
   el árbol limpio). Corregido con `.get("nota", "")`. Al regenerarlo, el
   HTML versionado resultó estar congelado desde el 2026-08-27: le
   faltaban los bloques de evidencia Crossref (V2-26 bis) y las 20
   decisiones ya tomadas. Ahora los trae.
2. **El sello de procedencia de `PD-04` mostraba la fecha de corte de
   SciVal.** `procedencia()` cae en ella por defecto, y su propio
   docstring advierte que eso es engañoso para un indicador que no viene
   de Scopus ni de SciVal. Se pasa la fecha de consulta de la propia cola.
3. **La columna «Fase» de `docs/DECISIONS.md` atribuía 346 de 465
   decisiones a la sesión equivocada.** `snapshot.py` sólo reconocía
   encabezados `## Sesión … — …` como frontera de sesión, y desde agosto
   casi todas las notas se titulan `## Cierre · …` (64), `## Cierre: …`
   (27) o `## Addendum: …` (1). La variable de sesión se quedaba clavada
   en el último encabezado que sí calzaba, así que las 15 decisiones más
   recientes —y las mías— aparecían bajo «Paleta H (vino + champán)», una
   sesión de diseño del 2026-09-01 sin ninguna relación. Es el MISMO
   defecto que la auditoría del 2026-09-02 ya corrigió una vez, sobre otro
   patrón de título (`(cont.)`), sin cubrir éste. Corregido reconociendo
   cualquier `## ` como frontera y limpiando prefijo y fecha del título;
   verificado fila por fila contra el encabezado real de cada nota.

### Verificación

- `--test` de los tres módulos nuevos: 29/29, 10/10 y 11/11.
- Agregación de `PD-04` ejercitada con una cola sintética de 7 filas que
  cubre los casos difíciles: mismo DOI en dos fuentes, obra sin DOI, fuera
  de ventana, pendiente, descartada por versión, y un DOI que `PD-02` ya
  cuenta. Resultado esperado y obtenido: 4 filas confirmadas en ventana →
  3 obras (1 corroborada, contada una vez); total combinado 209 → 211,
  con `duplicados_entre_fuentes` 19 → 20, porque una de las tres ya
  estaba en `PD-02`. **La cola sintética se borró antes de comitear**: es
  dato inventado y no puede quedar versionada (`CLAUDE.md`,
  `<non_negotiable_rules>`).
- Atribución de `DECISIONS.md` verificada tras el arreglo: se recompuso
  el mapa decisión → encabezado real leyendo `SESSION_NOTES.md` por
  separado, y se contrastó contra la columna generada. Las filas de
  Fase 1/2/3 no cambiaron.
- `src/audit/run_all.py`: 29/30, misma falla preexistente E-06, sin
  fallas nuevas. `src/build/build_all.py`: 0 fallas en la compuerta
  pública/interna, 536 fichas de autor, total fuera de Scopus 209 —
  idéntico al de antes del cambio, que es lo que debe ocurrir mientras la
  cola esté vacía.
- `node src/verify/run_all.mjs` con la sección renderizada: contraste,
  estructura, flujos, responsive, higiene y peso, sin fallos.
- `node --check` sobre `vista.js`; YAML de los tres archivos de
  configuración y del workflow, parseados.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-464 | `PD-04` es Nivel V con cola PROPIA, no una ampliación de la cola de `PD-02` | Clave de identidad distinta (`(fuente, id_fuente)` frente a `openalex_id`, porque la misma obra puede estar en los tres repositorios y decidirse por separado en cada uno), obras sin DOI que una clave por DOI pisaría entre sí, y un vocabulario de veredictos distinto. Forzar una sola cola habría metido en `PD-02` casos que no son suyos |
| D-465 | La INTERACCIÓN de la herramienta de revisión se comparte entre las dos colas; la cola, no | Marcar, filtrar y exportar no tiene contenido metodológico: es presentación. Dos copias del mismo JavaScript significan corregir cada bug de exportación dos veces. Mezclar las colas sí tendría contenido metodológico |
| D-466 | La revisión de `PD-04` tiene un cuarto veredicto, «otra versión de una obra ya contada» | Zenodo acuña un DOI por versión y DataCite indexa preprints de obras ya en Scopus: son DOI distintos para la misma obra y la deduplicación por DOI no los colapsa. La obra SÍ es de la institución, así que clasificarlo como atribución errónea perdería la distinción entre una cola llena de homónimos y una llena de versiones — dos problemas con soluciones distintas |
| D-467 | Se conserva la vía de recuperación por afiliación pese a ser matching por cadena suelta (`I-05`) | Las 267 firmas sin ORCID son invisibles a la vía por identificador, por construcción. `I-05` prohíbe la cadena suelta como base de una ATRIBUCIÓN; aquí no atribuye nada — propone un candidato que una persona confirma, y cada fila declara por qué vía llegó |
| D-468 | Los ORCID de `config/orcid_revisado.yml → retiradas` no fundan la recuperación de obras | Un ORCID que una persona ya declaró incorrecto para esa firma reconstruiría, del lado de las obras, el mismo error que esa decisión descartó del lado de los autores |
| D-469 | Las plantillas de consulta de las tres APIs viven en `config/sources.yml`, no en el código | Guardarraíl de replicabilidad de `CLAUDE.md`: otra institución cambia parámetros, no lógica. Y si una API renombra su campo de búsqueda, se corrige la configuración |
| D-470 | El conector conserva las resoluciones humanas al reejecutarse | La cola se reconstruye entera desde la API, pero `resolucion` es trabajo humano, no un dato recuperado: sobrescribirlo devolvería a cero cada revisión al refrescar la fuente |
| D-471 | Se publica el MECANISMO de `PD-04` con la cola vacía, y la sección lo declara en la página | La red de este entorno bloquea las tres APIs (403 verificado). Publicar un cero se leería como «no hay producción fuera de Scopus en repositorios», que es una afirmación que nadie ha comprobado; declarar que falta correr el conector es el estado real |
| D-473 | `snapshot.py` toma cualquier `## ` de `SESSION_NOTES.md` como frontera de sesión, no sólo `## Sesión … — …` | Desde agosto las notas se titulan `## Cierre …`; reconocer sólo el patrón viejo dejaba la sesión clavada y atribuía 346 de 465 decisiones a la sección equivocada. `DECISIONS.md` es el índice por el que el proyecto recupera el porqué de cada decisión: una columna de procedencia falsa lo vuelve inútil justo donde más se usa |
| D-472 | La numeración de decisiones salta de `D-456` a `D-464` | La rama `claude/state-review-next-steps-wzzq0h` ya usa hasta `D-463` sin haberse fusionado. Continuar en `D-457` habría creado ocho identificadores duplicados al fusionar, que es el bug que la auditoría del 2026-09-02 ya tuvo que corregir una vez (26 IDs duplicados) |

### Archivos modificados

```
src/enrich/obras_externas.py                    nuevo · conector de las tres fuentes
src/review/build_obras_externas_review.py       nuevo · herramienta de revisión
src/review/apply_obras_externas_review.py       nuevo · aplicador de decisiones
src/review/build_openalex_review.py             parametrizado (CSS/JS compartidos) + fix de `nota`
src/build/09_produccion_declarada.py            bloque PD-04 y total combinado
src/build/common_build.py                       fuente de procedencia de PD-04
web/assets/js/vista.js                          cuarta sección de produccion-ampliada
config/sources.yml                              4 fuentes declaradas + plantillas de consulta
config/indicators.yml                           PD-04
Makefile                                        obras-externas, revisar-obras-externas
.github/workflows/deploy.yml                    3 --test nuevos
docs/METODOLOGIA_FUERA_DE_SCOPUS.md             §0, §1, Reglas 2 y 4, checklist, §4
docs/FUENTES_Y_APIS.md                          §2.10 nueva; §2.1 ter actualizada
docs/DATA_MODEL.md, docs/V2_BACKLOG.md          PD-04 en el modelo y en el backlog
internal/revision_cobertura_openalex.html       regenerado (estaba congelado en agosto)
src/state/snapshot.py                           frontera de sesión: cualquier `## `, no sólo `## Sesión`
STATE.md, docs/DECISIONS.md                     regenerados (346 filas con la Fase corregida)
```

### Supuestos descartados

- Que las tres APIs se podrían consultar desde aquí: descartado con `curl`
  sobre los tres hosts, 403 en el CONNECT del proxy.
- Que `PD-04` podía entrar como una fuente más en la cola de `PD-02` por
  compartir nivel de evidencia: descartado al ver que la misma obra
  necesita decidirse por separado en cada repositorio.
- Que sumar las filas confirmadas de `PD-04` al total combinado era
  correcto: descartado — el indicador ya colapsa la corroboración entre
  sus tres fuentes, y sumar filas contaría dos veces lo que ya descontó.
- Que `build_openalex_review.py` estaba sano: no lo estaba, y el HTML
  versionado llevaba una semana sin poder regenerarse.

### Ambigüedades abiertas

- **`openalex_cobertura.py` pisa las resoluciones humanas al reejecutarse.**
  Escribe `resolucion="PENDIENTE_REVISION_HUMANA"` en todas las filas: una
  corrida nueva borraría las 20 confirmaciones de `PD-02`. El conector nuevo
  no tiene el problema (`D-470`). No se corrigió el de OpenAlex: es otro
  indicador, no estaba en el encargo, y merece su propia verificación.
- **Los contratos de BÚSQUEDA de las tres APIs no están verificados.** Los de
  recuperación por DOI sí se corrieron contra el corpus real desde otra red;
  el endpoint de búsqueda tiene otra forma de respuesta y está tomado de la
  documentación. El conector se detiene y guarda la respuesta cruda si no la
  reconoce, en vez de adivinar — pero la primera corrida real puede exigir
  ajustar una plantilla en `config/sources.yml`.
- **La rama `claude/state-review-next-steps-wzzq0h` tiene 3 commits sin
  fusionar** (Fortuny, Moya Patricia, y las 4 fusiones de firmas por
  convergencia de ORCID), con decisiones hasta `D-463`. No se fusionó aquí
  para no mezclar dos trabajos distintos en un mismo commit.

### Próximo paso recomendado

Correr `make obras-externas` desde una red que alcance las tres APIs. Si
alguna plantilla de `consulta_obras` no calza con el contrato real, el
conector se detiene y deja la respuesta cruda en
`data/cache/obras_externas/<fuente>/ultima_respuesta.json` — ese archivo dice
exactamente qué corregir. Con la cola llena: `make revisar-obras-externas`,
revisar caso por caso, aplicar y reconstruir.

## Fusión de `claude/state-review-next-steps-wzzq0h` (2026-09-03)

### Contexto

El usuario pidió fusionar la rama que quedaba sin integrar, señalada como
ambigüedad abierta en el cierre de `PD-04`. Traía tres commits desde el
ancestro común (`4d23df6`): los pendientes de Fortuny y de Moya, Patricia
en la cola de "Varios Scopus ID", y la fusión de 4 grupos de firmas por
convergencia de ORCID no consolidada ("Tier A").

### Por qué esta fusión fue mecánica, a diferencia de la del 2026-09-03 por la mañana

Aquélla tuvo 10 archivos en conflicto real y exigió leer la evidencia caso
por caso (`D-442`–`D-445`). Ésta no, y la diferencia es verificable, no una
impresión: los dos lados **sólo añadieron** al final de los mismos cuatro
archivos. Se comprobó comparando las primeras 10.048 líneas de cada versión
de `SESSION_NOTES.md` contra el ancestro: idénticas byte a byte en ambos
lados. Con eso, "conservar los dos" no es una elección entre versiones — es
la única resolución sin pérdida.

- **`SESSION_NOTES.md`**: se reconstruyó como ancestro + las 3 notas de la
  otra rama + la nota de `PD-04`, en orden cronológico (las suyas son de las
  20:39–22:25; la de `PD-04`, posterior). Verificado después: cero líneas
  únicas de cualquiera de los dos lados ausentes del resultado.
- **`STATE.md` y `docs/DECISIONS.md`**: regenerados con `snapshot.py`, nunca
  fusionados a mano (`D-444`). 473 decisiones indexadas.
- **`docs/FUENTES_Y_APIS.md`**: git lo auto-fusionó. Verificado que trae los
  dos cambios —el §2.9 actualizado a 8 nombres con varios Scopus ID (suyo) y
  el §2.10 de `PD-04` (mío)—; la única línea "perdida" es el "**7 nombres**"
  que su propio commit reemplaza por "**8 nombres**".
- **Identidad** (`identity_decisions.csv`, `identidades_consolidadas.yml`,
  `scopus_author_search_*`, `pendientes_consolidacion.*`,
  `revision_identidad.html`): entraron enteros desde su rama, sin conflicto —
  esta rama no tocó ninguno.

### Que la numeración de decisiones no chocara no fue suerte

`D-472` ya lo había previsto: el cierre de `PD-04` saltó de `D-456` a
`D-464` precisamente porque esta rama existía y llegaba hasta `D-463`. El
resultado fusionado es contiguo, `D-457`…`D-473`, sin un solo identificador
repetido — comprobado con `uniq -d` sobre las tablas de decisiones.

### Verificación

- Sin marcadores de conflicto en ningún archivo del árbol.
- `apply_decisions.py --dry-run`: **39 grupos consolidados, 94 formas de
  firma**, exactamente las cifras que la nota del "Tier A" declara tras
  aplicar. El estado de identidad fusionado es el que su rama produjo.
- **530 fichas de autor** (antes 536). Verificado por aritmética
  independiente de la salida del build, no aceptado porque el build lo
  imprimiera: 589 formas − (94 formas en grupo − 39 grupos) − 4 firmas
  descartadas = 530. Las 6 fichas que desaparecen son las formas que los 4
  grupos nuevos absorbieron.
- `src/audit/run_all.py`: 29/30, misma falla preexistente `E-06`, sin fallas
  nuevas. `src/build/build_all.py`: 0 fallas de capa. Total fuera de Scopus
  209, sin cambio — ninguna de las dos ramas tocaba esas fuentes.
- `--test` de los tres módulos de `PD-04` (29/29, 10/10, 11/11) y de
  `apply_decisions.py` y `apply_scopus_author_decisions.py` (5/5) tras
  fusionar.
- `node src/verify/run_all.mjs`: contraste, estructura, flujos, responsive,
  higiene y peso, sin fallos.

### Supuestos descartados

- Que esta fusión necesitaría el mismo trabajo de arbitraje que la de la
  mañana: descartado al comprobar que ambos lados sólo añadían, con el
  prefijo idéntico al ancestro.

### Ambigüedades abiertas

Ninguna nueva. Las tres del cierre de `PD-04` siguen: `openalex_cobertura.py`
pisa las resoluciones humanas al reejecutarse, los contratos de búsqueda de
las tres APIs siguen sin verificar contra la red, y `PD-04` sigue sin
corrida real. La tercera de esa lista —esta rama sin fusionar— queda cerrada
aquí.

### Próximo paso recomendado

Correr `make obras-externas` desde una red que alcance DataCite, Europe PMC
y Zenodo. Y decidir si esta rama se lleva a `main`.

## Fusión con `origin/main` (2026-09-03): la purga de seguridad D-SEC-01/D-SEC-02

### Contexto

El usuario pidió llevar esta rama a `main`. `main` había avanzado tres
commits mientras tanto, y no eran menores: la auditoría de seguridad del
2026-09-03 expulsó del árbol publicado `data/raw/` (exports de Elsevier, no
redistribuibles) e `internal/` (decisiones de identidad sobre personas
reales), invirtió la política de `.gitignore` —`data/processed/` pasa a
versionarse, `internal/` y `data/raw/` dejan de hacerlo— y reescribió CI
para ensamblar el sitio desde la capa pública versionada en vez de
reconstruirlo desde las fuentes sensibles (`docs/SEGURIDAD_PURGA.md`).

Esta rama modifica ocho ficheros de `internal/`. **Una fusión ingenua los
habría resucitado**, deshaciendo la purga sin que nadie lo notara en el
diff. Ése era el riesgo real de esta fusión, y por eso se leyó
`docs/SEGURIDAD_PURGA.md` antes de tocar nada.

### Cómo se resolvió

- **Los ocho conflictos `modify/delete` de `internal/`**: gana la supresión
  de `main`, sin excepción. Se sacaron del índice con `git rm --cached`, no
  con `git rm`: el fichero desaparece del control de versiones y **sigue en
  disco**, que es exactamente lo que la política nueva pide (la capa interna
  vive en la máquina de confianza, no en el repositorio).
- **`data/raw/` e `internal/` que la fusión borró del disco**: la fusión
  también los eliminó del árbol de trabajo, y sin ellos no se puede
  reconstruir nada. Se restauraron con
  `git restore --source=bf33fc0 --worktree`, que toca el disco y **no** el
  índice. Comprobado después: 10 ficheros en `data/raw/`, 37 en `internal/`,
  y en el índice sólo `internal/README.md`.
- **`.gitignore` e `internal/README.md`**: se toman tal cual de `main`.
- **`.github/workflows/deploy.yml`**: los dos lados añadían pasos en el
  mismo punto. Se conservan los dos, con los de `main` primero para no
  reordenar lo ya desplegado.
- **`data/processed/`**: `main` empezó a versionarla, pero con una copia
  generada antes de las consolidaciones de identidad de la tarde. Se
  regeneró entera desde la capa sensible restaurada —que es justamente el
  modelo que `D-SEC-02` describe: la reconstrucción completa es una
  operación local en la máquina que tiene las licencias— y se versionó el
  resultado.

### Tres defectos de `main` que esta fusión tuvo que arreglar para poder desplegar

1. **Faltaba `data/processed/produccion_declarada.json` en la capa pública.**
   `main` versionó doce artefactos y se dejó éste. Sin él, `cargar()` recibe
   un 404 y **la página de Producción ampliada entera se queda sin
   contenido**: es el único artefacto que consume. Ahora está versionado.
2. **Ese artefacto no pasaba la compuerta de CI de `main`.** Lleva un campo
   `herramienta_de_revision` con la ruta `internal/…`, y el paso «Verificar
   que no haya filtración en la capa pública» rechaza cualquier mención de
   `internal/` en `data/processed/`. Es plausible que sea la razón por la
   que `main` lo omitió, pero omitirlo rompe la página. Se quitó el campo:
   ninguna vista lo consumía, y la página nombra la herramienta en prosa,
   donde es una indicación de método y no un dato. El de `PD-02` tenía el
   mismo campo desde antes; también se fue.
3. **CI invocaba `src/enrich/wos_piloto.py --test`, un fichero que no existe
   en ninguna rama.** Ese paso falla y con él todo el despliegue: `main`
   estaba, en la práctica, sin poder publicar. Se retiró el paso —vuelve
   cuando exista el conector, no antes— tras comprobar uno por uno que los
   otros 19 pasos sí apuntan a ficheros presentes.

### Verificación

- Las tres compuertas de `main`, ejecutadas a mano aquí: `data/raw/` no
  versionado, `internal/` sólo con su README, y `data/processed/` sin
  material interno y con `meta.json`. Las tres pasan.
- Todos los pasos `--test` del workflow apuntan a ficheros que existen,
  comprobado por script sobre el YAML.
- Auditoría 29/30 (misma falla preexistente `E-06`), build sin fallas de
  capa, **530 fichas de autor**. `main` versionaba 542: las 12 de diferencia
  son variantes de firma que las consolidaciones de la tarde y del "Tier A"
  absorbieron (Amarouch, Busquets, Yanine, Núñez Lisboa, Martínez Mardones,
  Orellana Donoso, Ballesteros, García, Mardonez), más una ficha canónica
  nueva. La capa pública de `main` estaba generada antes de todo eso.
- Ensamblado del sitio desde la capa pública y batería de navegador
  completa —contraste, estructura, flujos, responsive, higiene y peso— sin
  fallos.
- `--test` de los tres módulos de `PD-04` y del conector de Scopus, en
  verde tras fusionar.

### Ambigüedades abiertas

- **`internal/README.md` se titula «fuera del sitio, dentro del
  repositorio»**, y desde `D-SEC-01` la capa interna ya no está en el
  repositorio. Es documentación de `main`, de la misma sesión que decidió la
  purga: se deja como está y se señala, en vez de reescribir por cuenta
  propia el texto de una decisión de seguridad ajena.
- **La purga de historial sigue pendiente.** `docs/SEGURIDAD_PURGA.md`
  advierte que expulsar las capas del árbol no borra los blobs viejos, y que
  hacerlo exige `git filter-repo`, un backup del remoto y la sesión
  autenticada del propietario. Esta rama es una de las que el documento
  nombra como portadoras de material sensible en su historial.
- Las tres de `PD-04` siguen: `openalex_cobertura.py` pisa resoluciones
  humanas al reejecutarse, los contratos de búsqueda de las tres APIs no
  están verificados contra la red, y `PD-04` no tiene corrida real.

### Próximo paso recomendado

Ejecutar la purga de historial de `docs/SEGURIDAD_PURGA.md` en la sesión
autenticada del propietario, con el backup previo que el propio documento
exige. Y correr `make obras-externas` desde una red que alcance DataCite,
Europe PMC y Zenodo.

## Cierre: el README de la capa interna, al día con D-SEC-01 (2026-09-03)

### Contexto

Quedaba señalado como ambigüedad abierta en la fusión con `main`:
`internal/README.md` se titulaba «fuera del sitio, **dentro del
repositorio**» cuando ese mismo archivo, más abajo, ya documentaba que
`D-SEC-01` había sacado el directorio del repositorio. El usuario pidió
actualizarlo.

### Qué estaba mal, además del título

Al revisarlo entero aparecieron tres problemas más, ninguno visible desde
el título:

1. **Una sección entera con la premisa invertida.** «Que estos archivos sean
   **accesibles** no los convierte en publicables» presupone que siguen
   siendo accesibles en el repositorio, y además repetía casi literalmente
   el párrafo que la precede. Se fundió con él en una sola regla.
2. **La tabla de contenido cubría 11 de los 36 archivos.** Faltaban las
   colas de OpenAlex, las de Scopus Author Search, las de validación de
   unidad, las de autoarchivo, el grafo de coautoría, las herramientas de
   revisión y las trazas de los conectores nuevos. Se reconstruyó agrupada
   por propósito y con una columna nueva: **qué comando genera cada
   archivo**, que es la pregunta práctica ahora que un clon nuevo trae el
   directorio vacío.
3. **Cifras vivas escritas a mano, ya falsas y contradictorias entre sí.**
   Decía «los 110 casos» en un párrafo y «los 127 pares» tres líneas más
   abajo; hoy la herramienta reporta 284 casos, 202 decididos y 82
   pendientes. Se quitaron en vez de actualizarse: ver `D-474`.

### Lo que se añadió

- **Un aviso al principio**: este README es lo único versionado del
  directorio, y un clon nuevo lo trae vacío. No es un error, es la
  política. Sin eso, el primer efecto de `D-SEC-01` sobre quien clone es
  desconcierto.
- **Una sección «Cómo se regenera»**: qué comandos reconstruyen qué, y la
  advertencia de que todo sale de `data/raw/`, que tampoco se versiona —
  hace falta una máquina con los exports bajo licencia institucional.
- **El estado real de `PD-04`**: sus tres archivos no existen en ningún
  disco todavía, porque el conector nunca se ha corrido de verdad. Se dice
  en el propio bloque de la tabla, no en una nota aparte.
- **El vocabulario de resolución de `PD-02`/`PD-04`**, que es distinto del
  de las colas de identidad y no estaba en ninguna parte de este archivo.
- **La advertencia de homónimo de la vía por afiliación de `PD-04`**, junto
  a la que ya existía para `orcid_candidatos_afiliacion.csv`: es el mismo
  límite metodológico (`I-05`) en dos sitios distintos, y tenerlas juntas
  evita que alguien resuelva una y no vea la otra.
- **Un puntero a `docs/SEGURIDAD_PURGA.md`**, porque la purga del historial
  sigue pendiente y este archivo es donde se va a mirar primero.

### Verificación

Comprobado por script sobre el texto, no a ojo:

- los 36 archivos del directorio están documentados; ninguno quedó fuera;
- los 11 objetivos `make` que cita existen en el `Makefile`;
- los 10 scripts que cita existen en `src/`;
- los únicos archivos citados que no están en disco son los tres de
  `PD-04`, y el propio README declara por qué;
- las dos compuertas de `D-SEC-01` siguen pasando: sólo `internal/README.md`
  versionado, `data/raw/` fuera del control de versiones.

Dos filas se corrigieron al verificar: la tabla atribuía a `make orcid-datos`
tres trazas (`zenodo_log.csv`, `datacite_log.csv`, `europepmc_log.csv`) y
sólo la primera existe — las otras dos están declaradas por sus conectores
pero la corrida del 2026-09-03 no produjo ninguna fila. Se dice así.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-474 | `internal/README.md` no fija cifras de las colas: remite a lo que imprime `make revision` y a `pendientes_consolidacion.md` | Las que tenía llevaban semanas siendo falsas y se contradecían entre sí («110 casos» y «127 pares» en el mismo apartado). Un recuento de una cola cambia con cada decisión que se toma; escribirlo a mano en un archivo que nadie regenera garantiza que envejezca mal sin que se note |

### Ambigüedades abiertas

Ninguna nueva. La purga del historial (`docs/SEGURIDAD_PURGA.md`) y las tres
de `PD-04` siguen abiertas; la del título de este README queda cerrada.

### Próximo paso recomendado

Correr `make obras-externas` desde una red que alcance DataCite, Europe PMC
y Zenodo, y ejecutar la purga de historial en la sesión autenticada del
propietario.

## Cierre: la plantilla de Zenodo no se pudo verificar, así que la corrida la resuelve (2026-09-03)

### Contexto

Antes de correr `make obras-externas` en su máquina, el usuario pidió
verificar la plantilla de búsqueda de Zenodo — la candidata más frágil de
las tres, porque Zenodo migró a InvenioRDM y el campo por el que se busca un
ORCID cambió de nombre.

**No se pudo verificar.** `zenodo.org` está bloqueado por la política de
egreso de la organización, comprobado con `curl` y también con `WebFetch`,
que sale por el mismo proxy y devuelve `EGRESS_BLOCKED`. Tampoco había
respuestas cacheadas: `data/cache/zenodo/` está vacío en este entorno.

### Qué se hizo en vez de adivinar

Convertir la pregunta abierta en algo que la primera corrida responda sola,
y protegerla del modo de fallo que de verdad importa.

**El parseo acepta las dos serializaciones.** Un autor de Zenodo llega como
`{name, orcid, affiliation}` (heredada) o como
`{person_or_org: {name, identifiers}, affiliations}` (InvenioRDM). El código
leía sólo la primera. Si el endpoint de búsqueda sirviera la segunda, cada
obra habría entrado a la cola **con el autor vacío y sin que nada fallara**
— la cola se llenaría de filas inútiles en silencio, que es justo lo que
este proyecto no admite. Ahora lee las dos y se detiene ante una tercera.

**La plantilla se declara por duplicado y se decide sondeando.**
`config/sources.yml` admite ahora una lista de candidatas por vía; Zenodo
declara la heredada primero —es la que la corrida del 2026-09-03 verificó en
el endpoint de recuperación por DOI— y la de InvenioRDM como alternativa. El
conector sondea al empezar, fija la que responda e imprime cuál usó.

**No se prueba la alternativa en cada consulta**, y esa decisión importa: la
mayoría de las 322 firmas no tiene ningún depósito en Zenodo, así que «cero
resultados» es la respuesta correcta y no un síntoma. Reintentar con la otra
plantilla cada vez habría duplicado ~322 peticiones sin ganar nada. Se
sondea una vez, con unos pocos identificadores.

**Si ninguna responde, se dice.** Con la red delante no se puede distinguir
«el campo de búsqueda cambió» de «esta institución no tiene depósitos aquí»,
y el conector no elige por su cuenta entre esas dos lecturas: usa la primera
y deja constancia.

### Lo que sí se sabe, y lo que sigue sin saberse

La corrida del 2026-09-03 sobre el corpus **sí verificó** la forma de la
respuesta del endpoint de recuperación por DOI: es la heredada. Eso es
evidencia real de que Zenodo sigue sirviendo esa serialización, y por eso va
primera. Pero la serialización y el índice de búsqueda son capas distintas:
que un registro se devuelva en forma heredada no prueba que `creators.orcid`
siga siendo un campo consultable. Esa parte sigue sin verificar, y ahora se
resuelve sola en la primera corrida en vez de fallar de forma callada.

### Verificación

`--test`: 35/35 en `obras_externas.py` (seis casos nuevos: las dos formas de
autor, la tercera forma que se detiene, las dos candidatas declaradas, y que
una fuente con una sola plantilla no gaste sondas), 10/10 y 11/11 en los
otros dos módulos. YAML de `sources.yml` parseado.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-475 | El parseo de un autor de Zenodo acepta la forma heredada y la de InvenioRDM, y se detiene ante una tercera | Leer sólo una habría producido una cola entera de filas con el autor vacío, sin error: un fallo silencioso sobre datos, que es peor que una parada ruidosa |
| D-476 | Una vía de consulta puede declarar varias plantillas candidatas en `sources.yml`, y el conector sondea cuál responde en vez de elegirse una a ciegas | El campo de búsqueda de Zenodo no se pudo verificar desde ningún entorno con red; publicar el cero que devolvería la plantilla equivocada habría sido presentar un fallo de integración como una medición |
| D-477 | El sondeo se hace una vez por fuente y vía, no en cada consulta vacía | La mayoría de las firmas no tiene depósitos: «cero resultados» es la respuesta correcta en el caso normal, y reintentar ahí duplicaría las peticiones sin aportar información |

### Ambigüedades abiertas

Las tres de `PD-04` siguen, con la primera ya acotada: los contratos de
búsqueda de DataCite y Europe PMC siguen sin verificar (y esas dos declaran
una sola plantilla), `openalex_cobertura.py` pisa resoluciones humanas al
reejecutarse, y `PD-04` no tiene corrida real. La purga de historial sigue
pendiente.

### Próximo paso recomendado

El usuario corre `make obras-externas` en su máquina. Lo primero que imprime
la sección de Zenodo es qué plantilla usó y por qué; eso cierra la pregunta.
---

## Sesión 2026-09-01 (noche) - Vuelta de tuerca: celdas neutras claras + bordeaux solo en el dato

### Contexto
El usuario confirmó que los mapas seguían mal pese a que el contraste WCAG
pasaba. Sintomas: treemap con celdas bordeaux-oscuro casi iguales, texto
ilegible, heatmap apagado/murky, leyendas chocando. Diagnóstico: la identidad
de marca (vino/champán) está bien para ACENTOS, pero llenar mapas densos de
bordeaux oscuro + texto sobre ellos es ilegible. El usuario eligió:
**"Celdas neutras claras + bordeaux solo en el dato"**.

### Cambios
- `web/assets/css/app.css`: nueva rampa `--mapa-1..5`
  (claro `#f7ebd6/#eed0b2/#e1b794/#cf9e7d/#b9836f` · oscuro
  `#1e0f12/#341d20/#4e2e2f/#6a403c/#88534b`), celdas cálidas claras. No toca
  `--ord-*` (siguen para la rampa ordinal) ni `--serie-1` (bordeaux, el dato).
- `src/design/validar_paleta.py`: nuevas reglas §1 `--mapa-* vs --tinta`
  (piso 4,5, ambos temas) en ámbito raíz SÓLO (viven en `bento-card`, no en
  bandas de contraste — mismo trato que `--bento-acento`); nuevo §3bis
  `CELDAS DE MAPA` ΔE ≥ 6,5 entre vecinas. Resultado: **SISTEMA VÁLIDO**.
- `web/assets/js/visualizations/treemap.js`: `RAMPA` pasa a `--mapa-1..5`;
  identidad por etiqueta, color sólo para separar vecinas.
- `web/assets/js/visualizations/heatmap.js`: las celdas usan `rellenoDeCelda(i)`
  sobre la rampa `--mapa-*`, y la franja de mayor intensidad (≥ UMBRAL_DATO 0,9)
  usa **`--serie-1` bordeaux** (el dato). Etiqueta `--tinta`; sobre la celda
  bordeaux, texto claro. Leyenda con 5 + bordeaux.
- `web/assets/css/modern-ui.css`: etiquetas del treemap pasan a `fill: --tinta`
  (oscura en claro, clara en oscuro) sin halo (ya no hace falta sobre celdas
  claras); `.heatmap-cifra.es-clara` usa `light-dark(#fdf6ef,#241014)` porque
  sobre el bordeaux la tinta tiene que invertir con el tema.

### Verificación
- `py src/design/validar_paleta.py` → **SISTEMA CROMÁTICO VÁLIDO**.
- `node src/verify/run_all.mjs dist` → **VERIFICACIÓN COMPLETA · sin fallos**.
- Pixel-check ambos temas: treemap claro ahora crema/clay + gris sin-dato
  (antes bordeaux oscuro); heatmap claro gradiente mapa-brand → bordeaux;
  labels `--tinta` (74,54,54 claro / 212,194,182 oscuro). Sin desborde X.

### Archivos tocados
`web/assets/css/app.css`, `src/design/validar_paleta.py`,
`web/assets/js/visualizations/treemap.js`, `heatmap.js`,
`web/assets/css/modern-ui.css`, `SESSION_NOTES.md`.

### Pendiente
- Commit (aún sin commitear) de estos 6 archivos.
- Nota: la celda gigante `--sin-dato` (gris) del treemap sigue siendo la mayor
  volumen real (gran "No determinada"); no es bug de paleta.
- Confirmación visual final del usuario (claro y oscuro).

## Sesión 2026-09-01 (noche, 2ª parte) - Grilla Bento a ancho completo

### Contexto
Tras el rediseño de celdas claras, el usuario sugirió que sobraban laterales y
que los mapas podrían crecer. Diagnóstico por medición (Playwright): los mapas
estaban atrapados en `.explorador-resultado` (872px) porque `.explorador` tiene
dos columnas (`17rem` panel + `minmax(0,1fr)`); la grilla era hija de la columna
derecha y el panel de filtros bloqueaba la izquierda. El usuario eligió "sacar la
grilla a ancho completo".

### Cambios
- `web/produccion.html`: el bloque "Jerarquía y temáticas" (`bento-grid`) se
  MOVIÓ fuera de `.explorador-resultado`; ahora es hijo directo de
  `.explorador`, con su `h2` de sección.
- `web/assets/css/modern-ui.css`: `.bento-grid > .bento-ancha` pasa de
  `span 2` a `1 / -1` (tarjeta ancha = fila completa); nueva regla
  `.explorador > .bento-grid { grid-column: 1 / -1 }` para que la grilla
  atraviese las dos columnas del explorador sin chocar con el panel sticky
  (vive en una fila superior distinta).

### Resultado medido
- Treemap/heatmap: **826px → 1130px** (+37%), aprovechando los laterales.
- Validator → **SISTEMA CROMÁTICO VÁLIDO**; verificar → sin fallos; desborde
  horizontal 0px. Leyendas del heatmap (0/17/34) reubicadas correctamente.
- Captura regenerada `_rev_produccion.png`.

### Archivos tocados
`web/produccion.html`, `web/assets/css/modern-ui.css`, `SESSION_NOTES.md`.

### Pendiente
- Commit (aún sin commitear) de los 8 archivos de esta serie (rediseño + grilla):
  `web/assets/css/app.css`, `src/design/validar_paleta.py`, `treemap.js`,
  `heatmap.js`, `modern-ui.css`, `web/produccion.html`, `SESSION_NOTES.md`.
- Confirmación visual final del usuario (claro y oscuro).

## Sesión 2026-09-01 (noche, 3ª parte) - "En oscuro se visualiza poco"

### Contexto
Al ver el ancho completo en oscuro, el usuario reportó que los mapas "se
visualizan poco". Medición: las celdas oscuras (1,05–3,15:1 contra el fondo
`--superficie` oscuro `#17080a`) desaparecían dentro de la tarjeta oscura.

### Causa raíz (dos problemas encadenados)
1. `--mapa-1..5` eran `light-dark(claro, OSSS)`: en oscuro se volvían vino
   oscuro y se fundían con la tarjeta oscura. El usuario pidió "celdas neutras
   claras", lo que en contexto significa un campo de datos claro en AMBOS temas.
2. BUG de especificidad: `app.css:1359` `svg.chart text { fill: var(--tinta-2) }`
   (0,1,1) **pisaba** `.treemap-etq { fill: var(--tinta) }` de `modern-ui.css`
   (0,1,0). El texto "legible" que veíamos eran `--tinta-2` (`#4a3636`/`#d4c2b6`),
   no la tinta del mapa.

### Cambios
- `app.css`: `--mapa-1..5` pasan a valores ÚNICOS claros (#f7ebd6…#b9836f), sin
  `light-dark`. Nuevos tokens: `--mapa-tinta: #241014` (texto sobre el campo,
  oscuro fijo en ambos temas) y `--mapa-dato: #8a2430` (bordeaux del dato,
  oscuro fijo — si fuera `--serie-1`, en oscuro se volvería rosa claro y se
  perdería contra las celdas claras).
- `modern-ui.css`: `.treemap-etq/.treemap-cifra/.heatmap-cifra` →
  `fill: var(--mapa-tinta)` y se re-encasillan como `svg.chart .treemap-etq`
  (0,2,1) para ganar al `svg.chart text` genérico; `.heatmap-cifra.es-clara` →
  `var(--marca-tinta)` (clara fija) sobre la celda de dato.
- `heatmap.js`: `CELDA_DATO` → `var(--mapa-dato)`; comentario actualizado.
- `validar_paleta.py`: `REGLAS_MAPA` miden el par real (`--mapa-N vs
  --mapa-tinta` piso 4,5) y la cifra del dato (`--mapa-dato vs --marca-tinta`).

### Resultado medido (ambos temas idénticos)
- Celdas `--mapa-1..5` claras (#f7ebd6…#b9836f); texto `--mapa-tinta`
  `rgb(36,16,20)`; dato `--mapa-dato` `#8a2430` con `--marca-tinta`.
- Oscuro: las celdas claras ahora RESALTAN sobre la tarjeta oscura → se leen.
- Validator → VÁLIDO · batería → sin fallos · overflow 0 · lienzo 1130px.
- Capturas: `_rev_produccion.png` (claro) y `_rev_produccion_oscuro.png`.

### Archivos tocados
`web/assets/css/app.css`, `web/assets/css/modern-ui.css`, `heatmap.js`,
`treemap.js`, `src/design/validar_paleta.py`, `SESSION_NOTES.md`.

### Pendiente
- Commit (aún sin commitear) de toda la serie (ahora ~10 archivos).
- Confirmación visual final del usuario en claro y, sobre todo, en OSCURO.

## Sesión 2026-09-01 (noche, 4ª parte) - El treemap vuelve a la familia BORDEAUX

### Contexto
Tras el arreglo de oscuro, el usuario notó que el treemap "la paleta de colores
es distinta a todo el resto del informe": las celdas pastel `--mapa-*`
(crema/arena/tostada) quedaban ajenas a la familia bordeaux (--serie-1/2,
--ord-1..4) que usa todo lo demás. El usuario eligió **"Rampa ordinal bordeaux"**.

### Cambios
- `treemap.js`: `RAMPA` vuelve a la ordinal bordeaux
  `['--ord-3','--ord-2','--ord-4','--ord-1']` (misma familia de los gráficos de
  cuartiles; `light-dark`, invierte con el tema).
- `modern-ui.css`:
  - `.treemap-etq/.treemap-cifra` → `fill: --superficie` (claro sobre bordeaux
    oscuro en claro; oscuro sobre bordeaux claro en oscuro) + HALO `--marca`
    (`paint-order: stroke`, 3px) para que se lea hasta sobre la celda más clara
    (`--ord-4`).
  - `.treemap-celda { stroke: --superficie; stroke-width: 2px }`: resquicio de
    la superficie entre celdas → el treemap se lee como MOSAICO y no se
    apelmaza (el defecto original de las celdas bordeaux "casi iguales").
- La leyenda ya iteraba `RAMPA` + `--sin-dato`, así que ahora muestra los 4
  tonos ordinales + gris sin cambios.

### Por qué no se repite el apelmazado ni la ilegibilidad originales
- La ordinal tiene ΔE ≥ 8,1 entre vecinas (validado §0) y ahora además las
  celdas tienen gutter de 2px que las separa visualmente.
- El texto usa `--superficie` + halo; la celda más clara (`--ord-4`) cae a
  ~3,3-3,6:1 crudo, que el halo remedia en la práctica (remedio aceptado en la
  opción elegida; no se mide como par estricto WCAG en el validador).

### Resultado medido
- Claro: celdas #a6505d (dominante) + #bf6977 + #5c1f29 + #8c3845 (todos
  presentes) + gris sin-dato; texto/gutters #fdf6ef.
- Oscuro: celdas #cf828e + #9d4a56 + #f8dde0 + #ebaab4 + gris; texto/gutters
  #17080a.
- Validator → VÁLIDO · batería → sin fallos · overflow 0 · lienzo 1130px.
- Capturas: `_rev_produccion.png` y `_rev_produccion_oscuro.png`.

### Nota
- El HEATMAP mantiene sus celdas claras `--mapa-*` con bordeaux `--mapa-dato`
  en el dato: el usuario no lo señaló (lo aprobó como "mucho mejor"). Queda la
  inconsistencia visual treemap-bordeaux vs heatmap-claro; si el usuario lo
  quiere unificado, sería el siguiente paso.

### Archivos tocados
`web/assets/js/visualizations/treemap.js`, `web/assets/css/modern-ui.css`,
`SESSION_NOTES.md`.

### Pendiente
- Commit (aún sin commitear) de toda la serie.
- Confirmación visual del treemap en claro y oscuro.

---

## Sesión 2026-09-03 - Revisión de visibilidad + mejora del informe descargable

### Contexto
El usuario pidió (1) revisar cada página y cada gráfico para asegurar que sean
visibles, y (2) usar los conocimientos/skills para mejorar la interfaz del
informe descargable (PDF), que debe ser accesible visualmente y agradable.

### Parte A - Visibilidad del sitio (auditoría estructural)
Auditoría Playwright sobre las 10 páginas (`index, impacto, produccion,
colaboracion, tematica, indicadores, autores, publicaciones, metodologia,
autor.html?id=...`) × temas claro/oscuro, por métricas DOM (sin ver imágenes):
- **Montaje** sin errores de consola ni `pageerror` en todas.
- **25 gráficos** con datos: 28 barras, 15 barras-de-déficit, 9 celdas de
  treemap, 24 celdas de heatmap, 4 segmentos de donut, 3 anillos acumulados,
  210 nodos de red de coautoría. **Ningún gráfico vacío/roto.**
- **Contraste**: 0 fallos WCAG AA (claro y oscuro) sobre ~10.000 nodos de texto
  (cabecera de gradiente bordeaux validada leyendo el `linear-gradient`).
- **Desbordes** horizontales: ninguno. **Fuentes < 11px**: ninguna.
- Recordatorio: el treemap es sólo de `produccion.html` (la portada es un
  explorador de BARRAS, no reproduce el treemap por diseño).

### Parte B - Informe descargable (impresión): defectos encontrados
El informe descargable es `window.print()` (el PDF = la página impresa, sin
segunda maquetación). Se encontraron tres defectos reales en `@media print`:
1. **El panel de filtros imprimía**: la regla ocultaba `.filtros` (clase
   antigua) pero el explorador usa `.explorador-panel`; el panel sticky caía a
   la izquierda de TODAS las páginas del PDF.
2. **El `.explorador` seguía en grid de 2 columnas** en papel → los gráficos
   quedaban encerrados en ~390px frente a un panel vacío en vez de usar el ancho
   de la hoja.
3. **`padding-bottom: 45vh`** (respaldo de pantalla para que el último corte
   suba hasta la cabecera; D-2a) añadía media página en blanco al final de cada
   sección impresa.

### Cambios (app.css)
- Lista `display:none` de impresión: añadidos `.explorador-panel`,
  `.filtros-explorador`, `.estado-recorte`, `#controles`, `.treemap-migas`,
  `.treemap-leyenda` (migas y leyenda de los mapas no hacen falta en papel,
  donde no hay drill-down).
- Nuevo bloque `@media print` AL FINAL del archivo (a propósito: estas reglas
  tienen la misma especificidad que las del explorador, líneas ~1737 y ~1948, y
  en la cascada manda la última; los `@media print` del medio del archivo quedan
  detrás de ellas en el orden de origen):
  - `.explorador { display: block }` → colapsa a una sola columna en papel.
  - `.explorador-resultado { padding-bottom: 0 }` → elimina el hueco de 45vh.
  - `.portada-cabecera { padding: 34mm 0 28mm; text-align: center }` + h1 a
    30pt con filete inferior → la primera hoja se lee como portada de informe,
    no como borde superior de una web. `break-inside: avoid`.
  - `.bento-card { break-inside: avoid }` → el treemap/heatmap no se parte a la
    mitad de la figura.

### Resultado medido (print emulado y PDF real)
- Panel de filtros `display:none`; explorador a `block`; `padding-bottom: 0`;
  resultado a ancho completo de hoja; sin desborde. PDFs de `index/produccion`
  regenerados sin error (333 KB / 495 KB).
- Secciones `impacto/colaboracion/tematica`: h1 + portada-sub presentes, gráficos
  montados (la red de coautoría de colaboración va a ancho completo, 711px).
- Validador paleta → VÁLIDO · batería `src/verify/run_all.mjs` → sin fallos
  (0 contraste, 0 estructura, 0 excepciones JS, 0 desborde, higiene OK, peso OK).

### Nota
- Los overrides de pantalla→papel viven al final de `app.css` con comentario
  explicando el porqué del orden de cascada; no hay que reintroducirlos en el
  `@media print` del medio o volverán a perder contra `.explorador` (más tarde
  en origen).

### Archivos tocados
`web/assets/css/app.css`, `SESSION_NOTES.md`; **sin commitear** (sigue pendiente
el commit de toda la serie).

### Pendiente
- Commit de toda la serie (~11 archivos) y push.
- Confirmación visual del treemap en claro y oscuro y del PDF del informe.

## Cierre: revisión del asistente de purga de historial (2026-09-03)

### Contexto

El usuario pidió correr la purga. No se corrió desde aquí, y no por falta
de autorización suya: el respaldo que `docs/SEGURIDAD_PURGA.md` exige como
paso previo obligatorio no se puede cumplir en un contenedor efímero —un
mirror que se recicla al cerrar la sesión no es un respaldo—, el script pide
la sesión autenticada del propietario con permiso de administración, el
force-push alcanza a las diez ramas remotas que el propio documento lista, y
el asistente es PowerShell sobre un contenedor Linux. Se explicó y el usuario
pidió, en su lugar, revisar el script línea por línea.

### Cómo se revisó

No de memoria. Se instaló `git-filter-repo` en un entorno aislado y se montó
un repositorio de laboratorio con dos ramas, una etiqueta, capa sensible
(`internal/` con README y con datos, `data/raw/`) y capa pública
(`data/processed/`), reproduciendo el flujo exacto del script: mirror →
clon de trabajo → filtro → force-push a un remoto local → verificación.

Tres cosas que se sospechaban rotas resultaron correctas, y conviene
dejarlo escrito para no volver a dudarlas:

- **Las ramas que sólo existen como referencias de seguimiento sí se
  empujan.** Era la duda principal: un `git clone` crea una sola rama local.
  Se comprobó que `filter-repo` convierte las remote-tracking en locales, de
  modo que `--all` alcanza a todas. En el laboratorio se reescribieron las
  dos ramas y la etiqueta.
- Las etiquetas sobreviven a la reescritura.
- `data/processed/` sobrevive al filtro.

### Los cuatro defectos encontrados, y sus arreglos

1. **Reejecutarlo destruía el único respaldo previo.** El paso 2 ofrecía
   sobrescribir el mirror existente. Una segunda corrida ocurre justo tras
   un fallo parcial —cuando el remoto ya puede estar reescrito—, así que
   aceptar reemplazaba el respaldo del historial original por uno del remoto
   ya purgado. Ahora el nombre lleva sello de tiempo, nunca se sobrescribe
   nada, y si hay respaldos anteriores el script los lista advirtiendo que
   **el bueno es el más antiguo**.
2. **`internal/README.md` se borraba del historial**, contra el alcance que
   declara la Sección 2 del propio documento. Verificado en el laboratorio.
   Se sustituyó `--invert-paths` por un `--filename-callback` que hace la
   excepción; probado, conserva el README y elimina todo lo demás.
3. **El force-push no era atómico.** El encabezado avisa de la protección de
   rama pero nada la comprueba: con `--all` a secas, si `main` está protegido
   el resto de ramas se reescribe y `main` no, dejando dos historiales
   incompatibles conviviendo en el remoto. Ahora va con `--atomic` y, si
   falla, el mensaje dice que no se escribió ninguna rama y por qué.
4. **La verificación sólo miraba lo que debía desaparecer.** Un filtro
   equivocado que además se llevara `data/processed/` habría pasado en
   silencio, y sin capa pública el despliegue no puede ensamblar el sitio.
   Se añadió la comprobación positiva, y la negativa ahora excluye el README
   para no dar falsa alarma con el filtro nuevo.

`docs/SEGURIDAD_PURGA.md` se actualizó para no contradecir al script: la
Sección 4 documenta el callback y por qué, con las comillas simples de Python
explicadas (PowerShell maltrata las dobles al pasar argumentos a un
ejecutable nativo), la Sección 6.4 deja de mandar recrear el README, y la
Sección 5 declara que el método alternativo con `filter-branch` sí lo borra.

### Verificación

La secuencia corregida entera, ejecutada de punta a punta en el laboratorio:
push atómico que reescribe las dos ramas y la etiqueta, verificación negativa
vacía, `data/processed/` e `internal/README.md` presentes en el árbol final, y
cero rastro sensible en el remoto resultante.

**Lo que NO se pudo comprobar**: no hay PowerShell en este entorno, así que la
sintaxis del script no se ejecutó. Lo verificado son los comandos `git` que
contiene, extraídos y corridos tal cual.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-478 | La purga no se ejecuta desde el entorno remoto, aunque el usuario lo pida | El respaldo obligatorio no es cumplible en un contenedor efímero, y es el único margen que hace recuperable un force-push irreversible sobre diez ramas. La operación se corre en la máquina del propietario, con su gestor de credenciales y el respaldo fuera del clon |
| D-479 | El filtro conserva `internal/README.md` mediante `--filename-callback` en vez de eliminarlo con `--invert-paths` | La Sección 2 del documento declara ese alcance; el método anterior lo contradecía y obligaba a un paso manual posterior. El callback admite la excepción y se verificó en laboratorio |
| D-480 | Cada corrida crea su propio respaldo fechado y ninguna sobrescribe uno anterior | Un respaldo se sobrescribe precisamente en el segundo intento, que es cuando el remoto ya puede estar reescrito: la copia del historial original se perdería en el momento en que hace falta |
| D-481 | El force-push va con `--atomic` | Sin él, la protección de rama sobre `main` deja el remoto a medio reescribir, con ramas en dos historiales incompatibles y sin señal clara de qué entró |

### Ambigüedades abiertas

- **La sintaxis PowerShell del script sigue sin ejecutarse.** No hay
  intérprete en este entorno. El primer arranque en la máquina del
  propietario es la primera prueba real; el script pide confirmación antes de
  cada paso destructivo, y el respaldo es el paso cero.
- Las de `PD-04` y la purga en sí siguen pendientes.

### Próximo paso recomendado

El usuario ejecuta el script en su máquina, tras el respaldo y con la
protección de rama de `main` desactivada.

## Cierre: se retira la atribución nominal de «Fuentes externas» (2026-09-04)

### Contexto

El usuario fusionó a `main` la rama `integracion-identidad`, que añadía una
página con **701 pares obra-autor y 344 personas nombradas**, procedentes de
Facultad de Medicina, DSpace y el inventario de autoarchivo. La capa pública
versionada incluía `data/processed/fuentes_externas.json` con esos nombres, y
CI ensambla el sitio exactamente desde ahí: estaba publicándose.

El propio commit lo declaraba: «Los autores no están verificados
individualmente… La afiliación a la UFT se asume por la fuente institucional,
no por verificación humana». Eso es una afirmación no verificada sobre
personas reales, que `docs/LAYERS.md` §3 clasifica como capa interna — el
día siguiente de que `D-SEC-01` sacara esa capa del repositorio por esa misma
razón.

El usuario pidió primero agotar los cruces disponibles y, a la vista del
resultado, retirar la parte nominal.

### Qué dieron los cruces, medido

Sobre las 344 personas que la fuente nombra:

| Vía | Confirma | Aporta nuevos |
|---|---|---|
| Firma ya en el corpus Scopus 2023-2025 | 110 | — |
| Directorio Scopus por afiliación (812 perfiles, sin ventana) | 98 | 22 |
| ORCID de la propia fuente = ORCID del proyecto, misma persona | 80 | 0 |
| **Verificadas por alguna vía local** | **132 (38 %)** | |

Y el hallazgo que zanjó la decisión: **152 nombres vienen acompañados de un
ORCID que el proyecto tiene asignado a OTRA persona**. No es ruido de
emparejamiento — en el inventario de autoarchivo la columna `ORCID` lleva con
frecuencia el identificador de un coautor, no el de quien figura en `Autor`.
Ejemplos verificados: la fuente empareja «Cruces, Pablo» con el ORCID de
«Díaz F.», y «Krause, Christina» con el de «Farsani D.». Publicar eso
atribuiría trabajos a personas equivocadas, con nombre y apellido.

**Dos errores propios durante la medición, corregidos antes de concluir.**
El primero: normalicé los nombres asumiendo «Nombre Apellido» cuando el
corpus usa «Apellido I.», y salió 0 % de coincidencia — un cero tan redondo
que era obviamente un bug, no un resultado. El segundo, más caro: llegué a
reportar al usuario un 76 % de cobertura porque partía el campo de autor sólo
por `;`, y estas fuentes usan además `||`; varias personas contaban como una.
Se retiró la cifra en cuanto la comprobación cruzada la contradijo. La
lección operativa: un número que sale redondo o demasiado bueno se comprueba
contra otra cosa antes de decirlo.

### Qué se hizo

La frontera se aplica en `src/build/10_fuentes_externas.py`, que era un
paso-a-través de `interim` a `processed`. Ahora:

- **Publica obras, no personas.** Que un DOI exista, esté fuera del universo
  Scopus y proceda de una fuente institucional declarada es una afirmación
  sobre un trabajo, del mismo nivel que `PD-01`/`PD-03`. Quién lo firma, no.
- **Colapsa las filas a obras**: 701 pares obra-autor son 436 obras. Contar
  las filas multiplicaba cada trabajo por su número de autores.
- **Cada obra guarda TODAS sus fuentes**, no la primera. Quedarse con una
  hacía que el autoarchivo apareciera aportando 46 obras cuando declara 302
  filas; corregido, aporta 238, y 193 obras las declara más de una fuente.
- **Declara lo que retiene**: `atribuciones_retenidas` (701) y
  `personas_nombradas_en_la_fuente` (344) viajan en el resumen, y la página
  sustituye la tabla de autores por una explicación de por qué no está.

`data/interim/fuentes_externas.json` conserva el detalle nominal íntegro —no
se versiona— para alimentar la cola de revisión cuando se monte.

### Verificación

- **Cero nombres de la fuente en las 12 páginas de `dist/`**, comprobado
  cruzando la lista de 344 contra el HTML ensamblado.
- El artefacto público no tiene clave `autores` ni campo de autor en ninguna
  de sus 436 entradas.
- Compuerta de CI de `main` sobre `data/processed/`: limpia.
- Auditoría 29/30, sin fallas nuevas. Build sin fallas de capa.
- **530 fichas de autor**: la fusión había reintroducido 16 fichas de firmas
  que la consolidación del 2026-09-03 había fusionado (el build local del
  usuario corrió con otro estado de identidad). La reconstrucción las retira.
- Batería de navegador completa, sin fallos. Encontró un error real de mi
  edición —`node --check` lo dio por bueno y el navegador no— al recortar el
  bloque de autores por un índice que casaba dentro de otro bloque. Corregido
  y reverificado.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-482 | La capa pública de «Fuentes externas» publica obras y NO la atribución obra-persona | Sólo 132 de 344 nombres se confirman con todas las vías locales, y 152 traen un ORCID asignado a otra persona: publicar la atribución adjudicaría trabajos a quien no los firmó. Una obra fuera del universo es una afirmación sobre un trabajo; quién la firma es una afirmación sobre una persona, y exige el mismo respaldo que el resto del proyecto pide |
| D-483 | El corte se aplica en el build (`10_fuentes_externas.py`), no en el conector | `data/interim/` no se versiona y puede conservar el detalle nominal íntegro para la cola de revisión futura; mutilarlo en el conector obligaría a recuperarlo de la fuente otra vez |
| D-484 | El artefacto declara cuántas atribuciones retiene y cuántas personas hay detrás | Una cifra ausente sin explicación no se distingue de un dato que no existe; el proyecto ya publica así sus pendientes en `PD-02` y `PD-04` |
| D-485 | Cada obra registra todas las fuentes que la declaran, y el desglose por fuente cuenta aportes | Quedarse con la primera fuente atribuía a DSpace los trabajos compartidos y hacía ilegible la contribución del autoarchivo |

### Ambigüedades abiertas

- **Crossref por DOI sigue sin correrse**, y es la vía más fuerte: preguntar a
  cada una de las 435 publicaciones qué afiliación declaró ella misma,
  evidencia primaria e independiente de la fuente institucional. La red de
  este entorno lo bloquea; queda para la máquina del usuario.
- **La cola de revisión de estas atribuciones no está montada.** El detalle
  vive en `interim/`; falta el conector que lo convierta en cola, su
  herramienta y su aplicador, siguiendo el patrón de `PD-04`.
- Las de `PD-04` y la purga de historial siguen igual.

### Próximo paso recomendado

Correr Crossref sobre los 435 DOI desde la máquina del usuario, y con eso
decidir cuánta de la atribución se puede confirmar automáticamente antes de
montar la cola para el resto.

## Cierre: la primera corrida real de PD-04, y dos fallos de diseño que expuso (2026-09-04)

### Contexto

El usuario corrió `obras_externas.py` en su máquina, la primera ejecución
real del conector contra las tres APIs. Resultado:

| Fuente | Obras recuperadas | Fuera del universo |
|---|---|---|
| DataCite | 169 | 168 |
| Europe PMC | 2.784 | 2.085 |
| Zenodo | — | HTTP 400 |

### El primer fallo: un 400 tiraba la corrida entera

`elegir_plantilla()` sólo pasaba a la plantilla siguiente cuando la primera
devolvía **cero resultados**. Zenodo no devuelve cero: devuelve **HTTP 400**,
porque no reconoce el nombre del campo. Ese error subía como excepción de red
y `main()` lo trataba como fatal, así que la corrida murió sin escribir la
cola — perdiendo también las 2.253 filas que DataCite y Europe PMC ya habían
recuperado.

Es un fallo de diseño mío, y el escenario que más probable era: monté todo el
mecanismo de plantillas candidatas precisamente porque no podía verificar el
contrato de Zenodo, y luego no contemplé la forma en que ese contrato falla.

Corregido en tres puntos:

- **Un 400 o 422 descarta esa plantilla y prueba la siguiente.** Otros
  códigos siguen propagándose: un 500 es la API caída, no una consulta mala,
  y confundirlos haría que un corte pasajero pareciera un campo renombrado.
- **Una vía que no se puede consultar se salta, no aborta.** Se anota en una
  lista de fallos y la corrida sigue con el resto.
- **La cola se escribe igual**, con lo recuperado, y el resumen final declara
  qué quedó sin consultar. Perder el trabajo de dos APIs porque una tercera
  rechaza su consulta no ayuda a nadie.

Se añadió además una **tercera plantilla candidata por vía** para Zenodo:
búsqueda de texto libre, sin nombre de campo. Menos precisa, pero no depende
de cómo se llame el campo hoy — y para una cola que revisa una persona, un
poco de ruido es preferible a no tener nada que revisar.

### El segundo hallazgo: el volumen

Europe PMC devolvió **2.085 obras fuera del universo**, frente a 168 de
DataCite. No es un error: consultar por ORCID trae toda la producción de esa
persona, también la que firmó en otras instituciones y la que cae fuera de la
ventana 2023-2025. Pero una cola de ~2.250 filas no es revisable caso por
caso por una persona, que es justo lo que `PD-04` exige antes de contar nada.

Queda sin resolver y es el problema serio del indicador. Opciones que habrá
que sopesar con el usuario: filtrar por ventana antes de encolar, exigir que
la obra declare la afiliación institucional, o priorizar la cola por
evidencia y revisar sólo el tramo alto. Ninguna es gratis: la primera
descarta producción real anterior a 2023, y la segunda devuelve el problema a
la afiliación declarada, que es justo lo que no siempre está.

### Verificación

`--test`: 41/41, con cuatro casos nuevos que cubren el camino del 400 —que
descarta la plantilla y prueba la siguiente, que devuelve -1 cuando ninguna
sirve, que un 500 sí se propaga, y que la candidata de texto libre no lleva
nombre de campo—. Los otros dos módulos, 10/10 y 11/11.

Una de esas comprobaciones falló al escribirla y el código tenía razón: yo
esperaba que el motivo dijera «rechaza» cuando la segunda plantilla funciona,
y lo que dice es con qué sonda respondió, que es más útil. Se corrigió la
expectativa, no el código.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-486 | Un HTTP 400/422 de una plantilla la descarta y pasa a la siguiente; otros códigos se propagan | Un 400 es la API diciendo que no entiende la consulta —una plantilla mala—; un 500 es la API caída. Tratarlos igual haría que un corte pasajero se leyera como un campo renombrado, y al revés |
| D-487 | Una fuente o vía que falla no aborta la corrida: se anota y la cola se escribe con lo recuperado | La corrida real perdió 2.253 filas ya recuperadas porque la tercera fuente rechazó su consulta. El trabajo hecho se conserva y el resumen declara qué falta |
| D-488 | Zenodo declara una tercera plantilla de texto libre, sin nombre de campo | Las dos primeras dependen de cómo se llame el campo, que es exactamente lo que no se pudo verificar y lo que resultó estar mal. Una búsqueda libre es menos precisa, pero alimenta una cola que revisa una persona, donde algo de ruido cuesta menos que no tener nada |

### Ambigüedades abiertas

- **El volumen de la cola de Europe PMC** (~2.085 filas). Sin resolver.
- **Qué plantilla de Zenodo funciona** sigue sin saberse: la primera está
  descartada por la corrida real, las otras dos no se han probado.
- Crossref sobre los 435 DOI de fuentes institucionales, y la cola de
  revisión de esas atribuciones, siguen pendientes.

### Próximo paso recomendado

Reejecutar el conector en la máquina del usuario. DataCite y Europe PMC se
releen de la caché en segundos; la corrida entra directa en Zenodo y la línea
de plantilla dirá cuál de las tres responde.

## Addendum: el 400 de Zenodo era el tamaño de página, no la plantilla (2026-09-04)

Con las tres plantillas candidatas ya en su sitio, la segunda corrida real
las rechazó **las tres** con HTTP 400, incluida la de texto libre. Eso
descartaba la hipótesis: si una búsqueda sin nombre de campo también falla,
el problema no es el campo.

Se consultó la API directamente y el cuerpo del error lo dijo en una línea:

> `Page size cannot be greater than 25. Please use authenticated requests to
> increase the limit to 100.`

`TAMANO_PAGINA` era una constante global de 100 compartida por las tres
fuentes. Zenodo limita a 25 sin autenticación y rechaza cualquier consulta
que pida más — con lo cual las tres plantillas fallaban por la misma razón,
que no era la suya.

**Y ese diagnóstico costó dos corridas de más porque el conector tiraba el
cuerpo del error.** `pedir()` dejaba subir el `HTTPError` sin leerlo, así que
el mensaje llegaba como «HTTP Error 400: BAD REQUEST» a secas, sin la frase
que explicaba todo. Corregido: ahora el cuerpo del 4xx se lee y se adjunta al
mensaje.

Dos correcciones, entonces:

- **Tamaño de página por fuente**, no global: Zenodo 25, las otras dos 100.
- **El cuerpo del error de la API se lee y se muestra**, que es donde estaba
  la respuesta desde el principio.

La plantilla original de Zenodo puede estar perfectamente bien; nunca llegó a
probarse, porque el tamaño se rechazaba antes. La próxima corrida lo dirá.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-489 | El tamaño de página se declara por fuente, no como constante única | Cada API pone su propio límite y Zenodo rechaza la petición entera si se excede. Una constante compartida hacía que el límite de una fuente rompiera esa fuente por completo, con un error que no nombraba la causa |
| D-490 | El cuerpo de un error 4xx se lee y se adjunta al mensaje | El diagnóstico estaba en la respuesta desde la primera corrida y se estaba descartando. Sin él, un error de tamaño se leyó dos veces como un error de sintaxis |

### Verificación

45/45 en el conector, con cuatro casos nuevos sobre el tamaño por fuente.
10/10 y 11/11 en los otros dos módulos.

## Addendum: la cola de PD-04, ordenada por lo que puede llegar a contarse (2026-09-04)

La primera corrida completa dejó **1.967 filas**, y de esas sólo **322 caen
en la ventana 2023-2025**. Como `build 09` únicamente cuenta lo que está en
ventana, revisar una obra de 2015 es trabajo que no puede traducirse en
cifra por mucho que se confirme.

La herramienta de revisión ordena ahora por ventana primero, después por
evidencia (corroborada entre fuentes, luego hallada por ORCID), y lo declara
en la cabecera: cuántas caen dentro y cuántas quedan detrás. Las de fuera
**no se descartan** —la ventana puede cambiar y son evidencia igual—, sólo
dejan de estorbar.

Es la diferencia entre una cola que nadie empieza y una del mismo orden que
la de OpenAlex (`PD-02`, 414), que el proyecto ya trata así.

### Lo que la corrida dejó establecido

| Fuente | Recuperadas | Fuera del universo |
|---|---|---|
| DataCite | 169 | 168 |
| Europe PMC | 2.784 | 2.085 |
| Zenodo | 36 | 30 |

La plantilla de Zenodo que funciona es **la primera candidata**, la
heredada: el campo nunca estuvo mal, el problema era el tamaño de página. La
vía por ORCID de Zenodo quedó sin consultar porque las tres candidatas
devolvieron vacío en las sondas — que con la red delante no distingue «campo
equivocado» de «esas ocho personas no tienen depósitos». Como la plantilla
hermana de afiliación sí responde, lo segundo es lo probable; queda
declarado, no resuelto.

### Decisiones

| # | Decisión | Fundamento |
|---|---|---|
| D-491 | La cola de revisión se ordena por ventana temporal antes que por evidencia | Sólo lo que cae en 2023-2025 puede contarse; en la corrida real eso separa 322 filas de 1.967. Ordenar por evidencia primero enterraba las revisables bajo mil setecientas que no pueden traducirse en cifra |
| D-492 | Las filas fuera de ventana se conservan en la cola, detrás | La ventana es un parámetro de configuración, no una verdad del dato: si cambia, esas filas vuelven a ser relevantes. Y siguen siendo evidencia de producción institucional aunque hoy no se cuenten |

### Ambigüedades abiertas

- **Las 322 en ventana siguen sin revisar.** Es el trabajo humano que PD-04
  exige y que nadie ha empezado.
- Si la vía por ORCID de Zenodo funciona, sin resolver: las sondas se toman
  de las ocho primeras firmas por orden alfabético, no de las más
  productivas. Sondear por número de publicaciones lo despejaría.
- Crossref sobre los 435 DOI de fuentes institucionales, y la cola de
  atribución nominal de «Fuentes externas», siguen pendientes.
