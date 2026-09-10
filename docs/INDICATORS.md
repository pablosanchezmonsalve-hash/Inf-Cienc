# Catálogo de indicadores y selección V1

**Capa:** pública · **Fase:** 2 · **Fecha:** 2026-07-31
**Evidencia:** `data/interim/indicator_feasibility.csv`, generado por
`python3 src/analysis/indicator_feasibility.py`

La columna «Disponible» y las coberturas son **medidas sobre los datos**, no
estimadas. Ningún indicador entró al catálogo sin verificación.

Base: 1.342 publicaciones (2020–2025) · 1.342 con métricas · 1.342 con autoría
detallada · 888 formas de firma · 1.962 apariciones firma × publicación
(1.960 pares distintos: una firma se repite en tres posiciones de un mismo
trabajo).

---

## 1. Catálogo completo

### 1.1 Descriptivos y de desempeño

| Cód. | Indicador | Definición | Lógica | Campos requeridos | Disp. | Confiab. | V1 | Nota metodológica |
|---|---|---|---|---|---|---|---|---|
| `P-01` | Publicaciones totales | Recuento de publicaciones únicas | `count(distinct eid)` | `eid` | **sí** 1.342/1.342 | alta | ✅ | Denominador institucional base |
| `P-02` | Producción anual | Publicaciones por año | `group by anio` | `eid`, `anio` | **sí** 131/199/194/227/273/318 | alta | ✅ | Serie de 6 puntos; no sostiene tendencia de largo plazo |
| `P-03` | Tipo documental | Distribución por tipo | `group by tipo` | `tipo_documental` | **sí** 100 % | alta | ✅ | Permite excluir tipos no citables del impacto |
| `P-04` | Fuentes distintas | Revistas y otras fuentes | `count(distinct Source ID)` | `Source ID` | **sí** 713 | alta | ✅ | `Source ID` mejor clave que ISSN |
| `P-05` | Ranking de fuentes | Fuentes por volumen | `group by fuente, order desc` | `Scopus Source title` | **sí** | alta | ✅ | Volumen ≠ calidad. No ordenar por métrica de revista |
| `P-06` | Autores UFT distintos | Formas de firma detectadas | `count(distinct autor)` | tabla maestra | **parcial** 829 publicadas de 888 en la fuente[^p06] | media | ✅ | **No son personas.** 888 en la fuente → 833 tras fusionar 94 variantes en 39 personas por revisión humana → **829 publicadas** tras descartar 4 fragmentos de afiliación (regla `E-09`, ya resuelto, ver `docs/LIMITATIONS.md` §7). Quedan 50 grupos de variantes y 29 perfiles fragmentados sin revisar |

[^p06]: Este recuento describe la decisión de la revisión histórica del 2026-07-31. Consolidaciones posteriores de identidad (94 formas en 39 personas, más 4 descartadas por `E-09`) bajaron la base publicada a **829 entidades**, y el sitio sirve esa. Ver `STATE.md`. La nota metodológica («no son personas») no cambia.
| `P-07` | Producción por unidad académica | Pares por unidad | `group by unidad` | `unidad_academica` | **parcial** 64,2 % | **baja** | ⚠️ | Cobertura parcial + sesgo de cobertura Scopus. Advertencia obligatoria |
| `P-08` | Distribución por idioma | Idioma del documento | `group by idioma` | `Language` | **sí** 100 % | alta | V2 | Bajo valor analítico inmediato |
| `A-01` | Acceso abierto | Publicaciones con estado OA | `count(OA not null)` | `Open Access` | **parcial** 70,3 % | media | ⚠️ | **Ausencia ≠ «no OA»**. Reportar como «n con estado declarado» |

### 1.2 Impacto

| Cód. | Indicador | Definición | Lógica | Campos requeridos | Disp. | Confiab. | V1 | Nota metodológica |
|---|---|---|---|---|---|---|---|---|
| `I-01` | Citas totales | Citas acumuladas al corte | `sum(Citations)` | `Citations` | **sí** 14.245 | alta | ✅ | Fuente única SciVal, corte 2026-08-30 |
| `I-02` | Citas por publicación | Media de citas | `sum(citas)/1342` | `Citations` | **sí** 10,61 | alta | ✅ | Denominador 1.342: universo y publicaciones con métrica coinciden. Declararlo junto al valor |
| `I-03` | FWCI institucional | Impacto normalizado por campo, año y tipo | agregado sobre el conjunto | `FWCI` | **sí** media 1,14 · **mediana 0,48** | media | ✅ | **Nunca promedio de FWCI individuales.** Distribución muy asimétrica: mostrar media y mediana |
| `I-04` | FWCI por año | Serie anual de FWCI | `group by anio` | `FWCI`, `anio` | **parcial** 0,83/1,04/0,77 | **baja** | ⚠️ | **42 % de las publicaciones de 2025 aún sin citas.** El año reciente no es comparable |
| `I-05` | Top 10 % de citación | Publicaciones en el decil superior | `count(percentil <= 10)` | `Outputs in Top Citation Percentiles` | **sí** 115/1.342 (8,6 %) | alta | ✅ | Semántica verificada empíricamente (§3) |
| `I-06` | Visualizaciones | Views en Scopus | `sum(Views)` | `Views` | **sí** 100 % | media | V2 | **Visibilidad, no impacto.** Módulo separado |
| `R-01` | Publicaciones en revistas Q1 | Percentil SJR ≤ 25 | `count(sjr_pct <= 25)` | `SJR percentile` | **parcial** 578/1.223 | media | ✅ | **Métrica de la revista, no del artículo** |
| `R-02` | Percentil CiteScore | Posición de la fuente | `CiteScore percentile` | idem | **sí** 92,5 % | media | V2 | Redundante con `R-01`; elegir uno principal |
| `R-03` | SNIP de la fuente | Impacto normalizado de la fuente | `SNIP` | idem | **sí** 94,3 % | media | V2 | Tercera métrica de revista; redundante para V1 |

### 1.3 Colaboración

| Cód. | Indicador | Definición | Lógica | Campos requeridos | Disp. | Confiab. | V1 | Nota metodológica |
|---|---|---|---|---|---|---|---|---|
| `C-01` | Colaboración internacional | Publicaciones con más de un país | `count(n_paises > 1)` | `Number of Countries` | **sí** 668/1.342 (49,8 %) | alta | ✅ | Indicador robusto: cobertura 100 % |
| `C-02` | Sin colaboración institucional | Una sola institución | `count(n_inst == 1)` | `Number of Institutions` | **sí** 213 (15,9 %) | alta | ✅ | Complemento de `C-01` |
| `C-03` | Países colaboradores | Ranking de países | `explode(Country/Region)` | `Country/Region` | **sí** 100 % | alta | ✅ | Multivaluado: **no sumable** |
| `C-04` | Instituciones colaboradoras | Ranking de instituciones | `explode(Institution IDs)` | `Institution IDs` | **sí** 100 % | alta | ✅ | SciVal advierte truncamiento en nombres: usar IDs |
| `C-06` | Autores por publicación | Tamaño de equipo | `Number of Authors` | idem | **sí** media 7,3 · mediana 5 | alta | ✅ | Asimétrica: **preferir mediana** |
| `C-05` | Red de coautoría | Grafo autor–autor | derivado de `Autoria` | tabla maestra | **sí** | media | V2 | **Publicado el 2026-08-26 (T-10)**, tras cerrarse T-03: ya no hereda nodos duplicados. Se muestra la componente (hecho objetivo) y la comunidad Louvain (heurística), declaradas por separado — ver `docs/GLOSSARY.md` |
| `C-07` | Liderazgo autoral | Primer/último/correspondencia | cruce por Scopus Author ID | roles SciVal | **parcial** 90,4 % | media | V2 | Depende de resolver los 29 perfiles fragmentados (T-04) |

### 1.4 Conceptuales y temáticos

| Cód. | Indicador | Definición | Lógica | Campos requeridos | Disp. | Confiab. | V1 | Nota metodológica |
|---|---|---|---|---|---|---|---|---|
| `T-05` | Áreas QS | 5 grandes áreas | `explode(QS area)` | `QS Subject area` | **sí** 98,1 % | media | ✅ | Vista de entrada antes de bajar a ASJC |
| `T-01` | Áreas ASJC | 271 categorías temáticas | `explode(ASJC field name)` | `ASJC field name` | **sí** 100 % · 2.973 asignaciones | media | ✅ | **Clasifica la revista, no el artículo.** Multivaluado: no sumar a 100 % |
| `T-02` | Topics de SciVal | Clúster de co-citación del documento | `Topic name` | idem | **sí** 97,8 % · 932 topics | media | V2 | Demasiado disperso para vista principal; útil en ficha de publicación |
| `T-03` | Prominencia temática | Atención del campo | `Topic Prominence Percentile` | idem | **sí** 97,8 % | **baja** | V2 | **Mide el campo, no el desempeño UFT.** Alto riesgo de malinterpretación |
| `T-04` | ODS | Objetivos de Desarrollo Sostenible | `explode(SDG)` | `SDG 2025` | **parcial** 38,8 % | **baja** | ⚠️ | Publicable **sólo** como recuento, nunca como distribución del total |

### 1.5 Nivel autor

| Cód. | Indicador | Definición | Lógica | Campos requeridos | Disp. | Confiab. | V1 | Nota metodológica |
|---|---|---|---|---|---|---|---|---|
| `AU-01` | Publicaciones por autor | Conteo completo | `count(distinct eid) by autor` | `Autoria` | **sí** | media | ✅ | Suma por autor (1.960) > total (1.342). No es total institucional |
| `AU-02` | Citas por autor | Citas atribuidas | `sum(citas) by autor` | `Autoria` + `Citations` | **sí** | media | ✅ | Atribución completa: una publicación aporta sus citas a cada autor UFT |
| `AU-06` | Evolución temporal del autor | Publicaciones por año | `group by autor, anio` | `Autoria` | **sí** | media | ✅ | 6 puntos: **barras, no línea de tendencia** |
| `AU-03` | h-index en ventana | h sobre 2020–2025 | h clásico sobre el subconjunto | `Autoria` + `Citations` | **parcial** | **baja** | ⚠️ | **675 de las 829 entidades tienen h ≤ 1 (81 %): sobre el conjunto no discrimina**[^au03]. Entre las 68 fichas donde sí se publica (n ≥ 5) la mediana es 4, el máximo 20 y sólo 5 quedan en h ≤ 1. Sólo en ficha, siempre etiquetado |
| `AU-05` | ORCID | Identificador persistente | emparejamiento por apellido+inicial | Crossref + registro de ORCID | **parcial** 328/888 firmas · 268/829 entidades | media | ✅ | Ya no es placeholder: se publicó al cerrarse `T-01` (2026-08-01); revisiones de identidad posteriores consolidaron más grupos y retiraron asignaciones erróneas. Cada asignación viaja con su veredicto; sin ORCID se muestra «no disponible», no se oculta |
| `AU-04` | FWCI por autor | Impacto normalizado del autor | — | — | **no** | no aplicable | ❌ | **Descartado.** El FWCI de un autor no es el promedio de sus publicaciones y SciVal no lo entrega a nivel autor. Calcularlo sería inventar la métrica |

[^au03]: Recalculado el 2026-09-09 con la **misma** función `h_index()` de `src/build/03_authors.py`, aplicada a las `publicaciones` de las 829 fichas: reproduce sin una sola discrepancia los 68 valores que el sitio publica, así que no es otra métrica sino la misma sobre toda la base. El reparto es 221 entidades con h = 0, 454 con h = 1, 75 con h = 2 y 79 con h ≥ 3. Que se calcule para el análisis no cambia lo que se publica: la ficha sigue mostrando h sólo con n ≥ 5 (`D-396`). La cifra anterior —729 de 888— la produce `src/analysis/indicator_feasibility.py` sobre **formas de firma sin consolidar**, que es otra población; se conserva ahí como nota interna de factibilidad (`D-397`) y sólo cambia si se re-corre ese análisis.

### 1.6 Declarado — fuera del corpus Scopus/SciVal

| Cód. | Indicador | Definición | Lógica | Campos requeridos | Disp. | Confiab. | V1 | Nota metodológica |
|---|---|---|---|---|---|---|---|---|
| `PD-01` | Producción declarada por las Facultades, fuera de Scopus | Recuento Facultad × año, sólo `solo_recuento` | `09_produccion_declarada.py` | `config/sources.yml` → `corpus_paralelo_declarado: true` | **sí**, cuando alguna Facultad lo declara | **baja** | ✅ | **No es un índice bibliográfico.** No aplica los criterios de cobertura de Scopus y SciVal no lo mide (sin citas, FWCI ni impacto). Nunca se suma al universo del resto del sitio (`D-206`, `D-398`). Publicado aparte en `produccion-ampliada.html`. Ver `docs/METODOLOGIA_FUERA_DE_SCOPUS.md` |

### 1.7 No calculables — placeholders metodológicos declarados

| Cód. | Indicador | Por qué no | Qué falta |
|---|---|---|---|
| `X-01` | Autocitas | El export declara `Self-citations: -` | Reexportar SciVal con la opción activada |
| `X-02` | Benchmarking interinstitucional | Sin datos de instituciones comparables | Fuera de alcance V1 por `PROJECT_SPEC` |
| `X-03` | Financiamiento | Cobertura 37,4 % | Fuente complementaria |
| `X-04` | Tendencia de largo plazo | Ventana 2020–2025 | Datos previos a 2020 |

---


## 2. Selección priorizada V1

Criterio de inclusión: **cobertura ≥ 90 %**, semántica verificada, y aporte
analítico no redundante. Los indicadores con cobertura menor entran sólo si son
exigidos por `PROJECT_SPEC.md` y llevan advertencia visible.

### Núcleo — 6 KPIs de portada

| # | KPI | Valor actual | Denominador declarado |
|---|---|---|---|
| 1 | Publicaciones totales | **1.342** | 2020–2025 |
| 2 | Citas totales | **14.245** | 1.342 con métrica, corte 2026-08-30 |
| 3 | Citas por publicación | **10,61** | 1.342 |
| 4 | FWCI institucional | **1,14** (mediana 0,48) | 1.342 |
| 5 | Colaboración internacional | **49,8 %** | 1.342 |
| 6 | Autores UFT | **829 firmas** | 2020–2025 |

### Módulos analíticos V1

| Módulo | Indicadores | Justificación |
|---|---|---|
| Producción | `P-02`, `P-03`, `P-04`, `P-05` | Base descriptiva, cobertura total |
| Impacto | `I-01`, `I-02`, `I-03`, `I-05`, `R-01` | Impacto bruto, normalizado y posición de fuente |
| Colaboración | `C-01`, `C-02`, `C-03`, `C-04`, `C-06` | El bloque más robusto: cobertura 100 % |
| Temático | `T-05`, `T-01` | QS como entrada, ASJC como detalle |
| Autores | `P-06`, `AU-01`, `AU-02`, `AU-06` | Ranking y fichas |
| Con advertencia destacada | `P-07`, `I-04`, `A-01`, `T-04`, `AU-03` | Exigidos por spec, cobertura o interpretación limitada |

**Excluidos de V1:** `P-08`, `I-06`, `R-02`, `R-03`, `C-05`, `C-07`, `T-02`,
`T-03` (8 indicadores redundantes o dependientes de pendientes abiertos) y
`AU-04`, `X-01` a `X-04` (5 no calculables o fuera de alcance).
`C-05` se publicó después, el 2026-08-26 (`T-10`), cuando se cerró el
pendiente que lo bloqueaba (`T-03`); esta lista describe la decisión de
Fase 2 tal como se tomó, no el estado actual del sitio.

### Recuento

| | n |
|---|---|
| Indicadores evaluados | **44** |
| Publicados | **32** |
| ├ calculables | 32 |
| └ placeholder declarado | 0 |
| Diferidos a V2 | 7 |
| No calculables o fuera de alcance | 5 |

`AU-05` (ORCID) dejó de ser placeholder al cerrarse `T-01` y se publica, y
`C-05` (red de coautoría) se publicó con `T-10` (2026-08-26); por eso el total es
32. De los publicados, **25 llevan nota metodológica** y **9 de ellas son
advertencia destacada** — banda visible junto al módulo, no ocultable: `P-07`,
`A-01`, `I-04`, `T-04`, `AU-03` y los cuatro indicadores de producción
declarada, `PD-01` a `PD-04`.

Los dos niveles son distintos por diseño: la nota contextual explica cómo leer
un indicador correcto; la advertencia destacada señala que el indicador tiene
cobertura o interpretabilidad limitada y podría inducir a error si se lee sin
ella. La parametrización está en `config/indicators.yml`
(`advertencia` vs. `advertencia_destacada`).

---

## 3. Verificación de semántica: el percentil de citación

El campo `Outputs in Top Citation Percentiles, per percentile` no declara en su
nombre qué representa. Se determinó empíricamente antes de usarlo:

| Evidencia | Resultado |
|---|---|
| Correlación con citas | **−0,66** |
| Correlación con FWCI | −0,58 |
| Publicaciones sin citas (n=260) | percentil 56–78 |
| Publicaciones con >50 citas (n=3) | percentil 1–3 |

**Conclusión:** el valor es el percentil de citación de la publicación, donde
**menor = mejor**. Permite calcular `I-05` (top 10 % = percentil ≤ 10).

Distribución resultante: top 1 % → 11 publicaciones · top 5 % → 53 · top 10 % →
115 (8,6 %) · top 25 % → 345 (25,7 %).

Un corpus sin sesgo tendría ~10 % en el top 10 %. El 8,6 % observado es
consistente con el FWCI mediano de 0,48: **la UFT está cerca del promedio
mundial en la cola alta, y por debajo en la mediana.** Ese contraste es un
resultado real y debe presentarse, no suavizarse.

---

## 4. Reglas de cálculo transversales

1. **Denominador explícito.** Todo indicador declara sobre cuántas
   publicaciones se calcula. En esta carga los cuatro denominadores coinciden
   en 1.342, porque ninguna publicación queda fuera de las banderas de
   disponibilidad; declararlo sigue siendo obligatorio, no opcional.
2. **FWCI agregado sobre el conjunto**, nunca como media de FWCI individuales.
3. **Multivaluados no suman al total.** ASJC, QS, ODS, países e instituciones
   producen más asignaciones que publicaciones. Prohibido presentarlos como
   partición porcentual.
4. **Conteo completo declarado.** Los agregados por autor no son sumables a
   nivel institucional.
5. **Mediana junto a media** cuando la distribución es asimétrica (`I-03`,
   `C-06`).
6. **n < 5 marca el indicador como no interpretable** en vistas individuales
   (761 de las 829 entidades publicadas).
7. **Fecha de corte visible** en todo indicador de impacto: 2026-08-30.
