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
