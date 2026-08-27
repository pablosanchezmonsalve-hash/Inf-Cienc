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
| D-138 | La BANDA es la unidad de composición de las páginas narrativas | Una banda sostiene una afirmación; un indicador diferido metido entre los publicados se lee como uno más |
| D-139 | Las cuatro superficies de consulta NO llevan bandas | Filtro y paginación: quien llega ahí viene a buscar, no a que le cuenten. Convertirlas en narrativa arreglaba la estética y rompía la función |
| D-140 | `.banda-contraste` redefine los tokens en su ámbito | Evita una segunda hoja de estilo para «lo que va sobre fondo oscuro»; lo que cae dentro se adapta solo |
| D-141 | La forma del gráfico la elige la RELACIÓN del dato | Contrastado contra el Visual Vocabulary del FT. `I-05` era correctitud, no estética |
| D-142 | La equivalencia ortográfica de firmas NO viola `D-08` | Es equivalencia de cadena, no juicio de identidad: la misma firma con otros diacríticos |
| D-143 | La vista de la red vive en `internal/` mientras `C-05` esté diferido | Una persona partida en dos nodos hace que la figura afirme que dos investigadores no colaboran |
| D-144 | La paleta institucional es **Ink Black · Deep Ocean · Jungle Teal · Peach Glow · Racing Red** (`071e22 · 1d7874 · 679289 · f4c095 · ee2e31`) | La fijó el usuario. Estuvo aplicada, se sustituyó por un índigo de alto contraste **sin consultarle** y se perdió. Validada: dato 5,14:1 / 5,79:1, ΔE 21,8 / 23,4 frente a la advertencia, daltonismo 30,1 / 22,5. Es más ajustada que el índigo en la separación del ámbar pero cumple |
| D-145 | Una elección cromática del usuario se registra como DECISIÓN, no como preferencia | `DECISIONS.md` tenía anotado cómo se declaran los tokens y cómo los valida el instrumento, pero no QUÉ colores eligió el usuario. Al no estar registrada, nada la sostuvo cuando el rediseño cambió de rumbo. El hueco no era de código: era de memoria |

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
