# Pendientes para V2

**Fase:** 3 · Cerrada la V1 · **Reconciliado con el repositorio:** 2026-08-11

Ordenados por lo que desbloquean. Los pendientes `T-xx` vienen de fases
anteriores; los que ya se cerraron lo declaran, con lo que quedó abierto en su
lugar.

> Este archivo se mantiene **a mano** y por eso envejece: entre el cierre de la
> V1 y esta reconciliación, tres entradas describían un estado que el
> repositorio ya había superado. Las cifras de autor que aparecen aquí van
> siempre con su base —firmas sin consolidar o entidades publicadas—, por la
> misma razón que en `STATE.md`: sin base declarada, dos cifras verdaderas
> parecen contradecirse.

---

## 1. Calidad de datos — habilitan indicadores hoy bloqueados

| # | Pendiente | Desbloquea | Origen |
|---|---|---|---|
| **V2-01** | Subir la cobertura de ORCID desde el 38,8 % actual, confirmando candidatos por afiliación | Identidad persistente; campo exigido por `PROJECT_SPEC` | T-01 (cerrado), T-19 |
| **V2-02** | Resolver los 31 grupos de variantes de nombre que siguen pendientes | `C-05` red de coautoría; recuento real de personas | T-03 |
| **V2-03** | Revisión humana de los 20 identificadores fragmentados | `C-07` liderazgo autoral | T-04 |
| **V2-04** | Validar institucionalmente el vocabulario de unidades | Retirar la advertencia destacada de `P-07` | T-02 |
| **V2-05** | Reexportar Scopus con fecha de corte declarada | Cierra la única brecha de trazabilidad que queda | T-06 |
| **V2-06** | Reexportar SciVal con autocitas | `X-01` tasa de autocitación | Fase 2 |
| **V2-07** | Decidir el duplicado probable Article/Letter | Cierra la última ambigüedad de publicaciones | T-05 |

**Lo que cambió desde que se escribió este bloque.** Decía que sin ORCID las 589
firmas no podían consolidarse y que era la única vía sin trabajo manual. Las dos
afirmaciones caducaron:

- **La vía Crossref ya se recorrió.** `T-01` se cerró el 2026-08-01 con 174
  firmas, y la ampliación desde el registro más las decisiones humanas la
  dejaron en **240 asignaciones sobre 589 formas de firma sin consolidar**, que
  son **216 de 556 entidades publicadas (38,8 %)**. El 100 % no es alcanzable
  sin inventar datos: el argumento está en `docs/ORCID_COVERAGE.md` §5 —sus
  cifras de portada son anteriores a la revisión humana, el razonamiento no—.
- **La consolidación no esperó al ORCID.** De los 110 casos que `make revision`
  puso delante de una persona —repartidos en cuatro colas—, 52 se resolvieron:
  51 «misma persona» y 1 «personas distintas». Su cierre transitivo dejó **63
  formas de firma convertidas en 30 personas**
  (`config/identidades_consolidadas.yml`). El camino fue humano y caso por caso,
  que es justo lo que `D-08` exige y lo que este párrafo daba por imposible.

No confundir dos recuentos que coinciden en el número: la cola de variantes de
nombre tiene **51 grupos** (`T-03`, 123 filas en `internal/ambiguities_authors.csv`),
y **51** es también el total de veredictos «misma» sumando las cuatro colas. Son
conjuntos distintos.

Queda `T-19`: cada candidato por afiliación que una persona confirme sube la
cobertura sin relajar el criterio de evidencia (`D-101`).

---

## 2. Indicadores diferidos

Ya evaluados en Fase 2 y verificados como calculables. Están en
`config/indicators.yml` con `publicar: false`: activarlos no requiere código,
salvo el renderizador de la red.

| Código | Indicador | Bloqueo |
|---|---|---|
| `C-05` | Red de coautoría | V2-02 |
| `C-07` | Liderazgo autoral | V2-03 |
| `T-02` | Topics de SciVal | Ninguno; 632 topics son demasiados para vista principal |
| `T-03` | Prominencia temática | Ninguno; alto riesgo de malinterpretación |
| `I-06` | Visualizaciones | Ninguno; decidir si aporta sin confundirse con impacto |
| `R-02`, `R-03` | CiteScore y SNIP | Ninguno; redundantes con `R-01` |
| `P-08` | Idioma | Ninguno; bajo valor analítico |

---

## 3. Funcionalidad

| # | Pendiente | Nota |
|---|---|---|
| **V2-08** | Procedimiento público de corrección de fichas de autor | Requisito de `DATA_LICENSE.md` §4 |
| **V2-09** | Comparación entre períodos | Necesita al menos dos cargas con corte distinto |
| **V2-10** | Interfaz en inglés | Hoy sólo español |
| **V2-11** | Exportación desde más vistas | Hoy sólo desde publicaciones |
| **V2-12** | Página de detalle por publicación | Hoy el detalle vive en la tabla y la ficha de autor |
| **V2-13** | Índice precomputado para filtrado | Sólo si el corpus supera ~10.000 publicaciones |

---

## 4. Decisiones institucionales pendientes

| # | Decisión | Estado |
|---|---|---|
| **T-11** | Alcance de publicación de fichas de autor | **Supuesto vigente:** se publican las **556 entidades** —las 589 formas de firma de la fuente, con 63 ya fusionadas en 30 personas—, ranking por defecto n ≥ 5 (`config/publication.yml`). Sin confirmar |
| **T-13** | Confirmar la semántica del percentil de citación con documentación de SciVal | Determinada empíricamente (correlación −0,66), no documentalmente |
| — | Licencia de datos derivados (CC BY 4.0) | Propuesta en `DATA_LICENSE.md`, sin validar |
| — | Alcance de publicación de métricas de Elsevier | Sin verificación jurídica |
| — | Branding institucional definitivo | `color_primario` y `logo_path` son placeholders |

---

## 5. Deuda técnica conocida

| # | Deuda | Impacto |
|---|---|---|
| **V2-14** | Los textos de `docs/` citan cifras de esta institución | Un despliegue replicado debe revisarlos a mano (`REPLICATION.md` §4) |
| **V2-15** | Los denominadores de `config/indicators.yml` se actualizan a mano | Deliberado: cambiarlos es una decisión. Podría automatizarse con confirmación explícita |
| **V2-16** | Las páginas HTML repiten la estructura del `<head>` | Con 9 páginas es manejable; con más conviene una plantilla |
| ~~**V2-17**~~ | ~~La batería de verificación del sitio no corre en CI~~ | **Cerrado (2026-08-14).** `deploy.yml` ejecuta `src/verify/run_all.mjs` y la autoprueba de `apply_decisions`, y el job de verificación corre también en `pull_request`: antes la compuerta sólo actuaba al empujar a `main`, o sea después de fusionar. Queda una brecha declarada aparte: `make rendimiento` sigue fuera por tardar minutos (`D-142`) |
| **V2-18** | `Molecular Sequence Numbers` sigue apareciendo en la auditoría | Excluida del dataset procesado; la regla `E-06` la reporta como hallazgo (T-07 cerrado en el build, no en la auditoría) |

---

## 6. Lo que NO debería entrar en V2

Registrado para evitar que se reabra sin motivo:

- **FWCI por autor.** No es el promedio de los FWCI de sus publicaciones y la
  fuente no lo entrega a nivel de persona. Calcularlo sería inventar la métrica.
- **Benchmarking interinstitucional.** Fuera de alcance por `PROJECT_SPEC`.
- **Mapa coroplético de colaboración.** 23 países sobre ~200 produce un mapa
  casi vacío que exagera visualmente la dispersión.
- **Nube de palabras.** Sin lectura cuantitativa defendible.
- **Consolidación automática de variantes de nombre por similitud.** Fusionaría
  homónimos. Requiere ORCID o validación humana.
