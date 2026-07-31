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
