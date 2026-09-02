# Pendientes para V2

**Fase:** 3 · Cerrada la V1 · **Reconciliado con el repositorio:** 2026-08-19

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
| **V2-01** | Subir la cobertura de ORCID desde el 51,1 % actual (277 de 542), confirmando candidatos por afiliación | Identidad persistente; campo exigido por `PROJECT_SPEC` | T-01 (cerrado), T-19 |
| **V2-02** | ~~Resolver los grupos de variantes de nombre que siguen pendientes~~ | `C-05` red de coautoría; recuento real de personas | T-03 (cerrado, 2026-08-26) |
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
  dejaron en **322 asignaciones sobre 589 formas de firma sin consolidar**, que
  son **277 de 542 entidades publicadas (51,1 %)**. El 100 % no es alcanzable
  sin inventar datos: el argumento está en `docs/ORCID_COVERAGE.md` §5.
- **La consolidación no esperó al ORCID.** De los 110 casos que `make revision`
  puso delante de una persona —repartidos en cuatro colas—, 52 se resolvieron:
  51 «misma persona» y 1 «personas distintas». Su cierre transitivo dejó **63
  formas de firma convertidas en 30 personas**
  (`config/identidades_consolidadas.yml`); una consolidación posterior
  (2026-09-01) llevó la base publicada a **542 entidades**. El camino fue humano
  y caso por caso, que es justo lo que `D-08` exige y lo que este párrafo daba
  por imposible.

No confundir dos recuentos que coinciden en el número: la cola de variantes de
nombre tiene **51 grupos** (`T-03`, 123 filas en `internal/ambiguities_authors.csv`),
y **51** es también el total de veredictos «misma» sumando las cuatro colas. Son
conjuntos distintos.

Queda `T-19`: cada candidato por afiliación que una persona confirme sube la
cobertura sin relajar el criterio de evidencia (`D-101`).

**Lo que cambió el 2026-08-19.** `make revision` sólo encolaba asignaciones *por
hacer*. Las **ya publicadas cuya evidencia no las respalda** no tenían cola: 21
formas de firma con ORCID que el registro no puede contrastar —17 cuyo titular
no declara obras con DOI, 4 cuyas obras declaradas no coinciden con ninguna
atribuida—, más 6 firmas con cinco o más publicaciones y ningún identificador.
Ahora tienen tres colas propias, con enlace al registro del titular y la lista
de publicaciones que hay que comparar. Y la herramienta **lee lo ya decidido**:
antes volvía a preguntar los 52 casos resueltos en cada corrida.

---

## 2. Indicadores diferidos

Ya evaluados en Fase 2 y verificados como calculables. Están en
`config/indicators.yml` con `publicar: false`.

`C-05` (red de coautoría) salió de esta tabla el 2026-08-26: se publicó
(`T-10`), con comunidades Louvain visibles y declaradas como heurística. Ver
`PLAN.md` y `docs/GLOSSARY.md`.

| Código | Indicador | Bloqueo |
|---|---|---|
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
| **V2-08** | ~~Procedimiento público de corrección de fichas de autor~~ · **publicado (2026-08-18)** en `metodologia.html#correcciones`, enlazado desde la página de autores. Distingue lo que se corrige en Scopus de lo que sólo se corrige aquí, y declara qué no se cambia a petición. **Queda un hueco declarado:** la vía institucional de contacto, que es decisión de la institución | Requisito de `DATA_LICENSE.md` §4 |
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
| ~~T-13~~ | ~~Confirmar la semántica del percentil de citación con documentación de SciVal~~ | **Cerrado (2026-08-26)**: empírica (correlación −0,66) y ahora también documental — `docs/METHODOLOGY.md` §7 bis |
| — | Licencia de datos derivados (CC BY 4.0) | Propuesta en `DATA_LICENSE.md`, sin validar |
| — | Alcance de publicación de métricas de Elsevier | Sin verificación jurídica |
| — | Branding institucional definitivo | `color_primario` y `logo_path` son placeholders |

---

## 5. Deuda técnica conocida

| # | Deuda | Impacto |
|---|---|---|
| **V2-14** | Los textos de `docs/` citan cifras de esta institución | Un despliegue replicado debe revisarlos a mano (`REPLICATION.md` §4) |
| **V2-15** | Los denominadores de `config/indicators.yml` se actualizan a mano | Deliberado: cambiarlos es una decisión. Podría automatizarse con confirmación explícita |
| ~~**V2-16**~~ | ~~Las páginas HTML repiten la estructura del `<head>`~~ | **Cerrado (2026-08-19).** `web/_cabecera.html` es la única copia; cada página declara sólo `data-titulo` y `data-descripcion`, y `06_assemble_site.py` la expande al ensamblar. Tres comprobaciones abortan el build: una página sin marcador, una expansión que deje la página sin hoja de estilo, y la plantilla viajando a `dist/`. 140 líneas duplicadas pasaron a 20 |
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
- **Google Académico.** No tiene API pública —no es que sea de pago: no
  existe—, sus condiciones prohíben la recuperación automatizada, y sus datos no
  son reproducibles ni auditables: sin fecha de corte, sin criterio de indexación
  declarado y sin identificador estable de autor. Incompatible con las tres
  primeras prioridades del proyecto. Queda escrito para que no se reabra.
- **Fusionar corpus de fuentes distintas en un solo universo.** Scopus, OpenAlex
  y SciELO indexan con criterios distintos; sumarlos produce una cifra que nadie
  puede reconciliar.

---

## 7. Plataformas evaluadas para integración

Evaluadas el 2026-08-19; el análisis completo —qué preguntaría cada una, qué
riesgo metodológico trae y qué reglas tendría que cumplir el conector— está en
`docs/FUENTES_Y_APIS.md`.

**Ninguna se ha probado desde este repositorio.** La columna «qué falta
confirmar» no es una formalidad: es lo que separa una propuesta de una promesa,
y `CLAUDE.md` prohíbe suponer disponibilidad de APIs o credenciales.

| # | Integración | Desbloquea | Qué falta confirmar |
|---|---|---|---|
| ~~**V2-19**~~ | OpenAlex · **ejecutado (2026-08-26)**, `src/enrich/orcid_openalex.py` | ORCID donde no había: **80 asignaciones nuevas**, cobertura 242 → 322. Contraste institucional por ROR: **68 publicaciones** que este proyecto atribuye a la UFT y OpenAlex no (cola en `internal/openalex_deteccion.csv`), **6 desacuerdos** de ORCID encolados (`internal/openalex_desacuerdos.csv`), ninguno resuelto automáticamente (`D-08`) | Cerrado. Recordatorio vigente: OpenAlex no es fuente independiente de verificación —ingiere Crossref—, así que sus 212 concordancias no suben ninguna asignación a «verificado» |
| ~~**V2-26**~~ | OpenAlex **por institución** · **ejecutado (2026-08-26)**, `src/enrich/openalex_cobertura.py` | Mide la brecha de cobertura que `LIMITATIONS.md` sólo advertía en prosa: OpenAlex atribuye **1.112 obras** a la UFT por ROR, de las cuales **698 ya están en el universo** y **414 no** (385 con DOI ausente del universo, 29 sin DOI en OpenAlex). Cola de revisión en `internal/openalex_cobertura.csv`, **nunca un ajuste del corpus** (`D-206`): Scopus y OpenAlex indexan con criterios distintos | Cerrado. Las 414 son candidatas a revisión humana, no producción confirmada perdida — pueden ser desambiguación errónea de OpenAlex, tipo documental excluido a propósito, o fecha fuera de ventana |
| ~~**V2-20**~~ | ROR · **conector escrito (2026-08-19)**, `src/enrich/ror_institucion.py` | Cierra `ror_id` e `isni`, y contrasta el patrón de detección institucional contra los nombres que ROR registra | **Falta ejecutar la consulta.** El entorno de desarrollo no alcanza `api.ror.org`; se corre desde la máquina del proyecto y se pega el resultado en `config/institution.yml`. La lógica está verificada con 12 casos en CI |
| **V2-21** | SciELO | Mide la brecha de cobertura que hoy sólo se advierte en prosa: humanidades, ciencias sociales y publicación en español | **Investigado el 2026-08-26** (`docs/FUENTES_Y_APIS.md` §3.6): la interfaz real es la API REST ArticleMeta, sin autenticación, pero **no filtra por institución** — sólo por ISSN, colección y fecha. El dato de afiliación existe por artículo, pero exige cosechar identificadores y volver a pedir cada uno individualmente: más trabajo que `V2-19`/`V2-26`, no menos. Queda sin confirmar el código de colección de Chile y si limitarse a esa colección alcanza — `scielo.readthedocs.io` y `articlemeta.scielo.org` bloqueados desde este entorno, igual que `api.ror.org` en `V2-20`. Sin código escrito: es una decisión de alcance |
| **V2-22** | API de Scopus | `V2-05` y la ambigüedad `A-05`: fecha de corte declarada por la propia consulta, y actualización como objetivo del `Makefile` | Clave institucional, si la suscripción la habilita, y si exige IP institucional. **Bloqueante** |
| **V2-23** | API de SciVal | `X-01` autocitas (`V2-06`). `T-13` ya **no** depende de esto: se cerró por documentación (`docs/METHODOLOGY.md` §7 bis, 2026-08-26) | **Probado el 2026-08-26**: `GET analytics/scival/publication/metrics` con la API Key de Scopus del usuario responde `403 ENTITLEMENTS_ERROR — Not entitled to the resource specified`. No es un 404 (ruta inexistente): el gateway de Elsevier reconoce el recurso y niega el acceso, lo que sugiere que la ruta es válida y el bloqueo es puramente de licencia. La suscripción de Scopus **no** incluye acceso programático a SciVal, confirmando el supuesto original. **Sigue bloqueante para X-01**: pedir la entitlement al gestor de cuenta de Elsevier de la UFT o a la biblioteca; si se concede, `analytics/scival/publication/metrics?metricTypes=OutputsInTopCitationPercentiles` es el punto de partida ya probado |
| **V2-24** | Unpaywall | Contraste de acceso abierto, que hoy se publica desde SciVal sin segunda fuente | Condiciones de uso |
| **V2-25** | Altmetric | Un eje de atención que hoy no existe; la mención en política pública tiene valor real para un informe institucional | Condiciones de acceso para una web pública institucional. Riesgo alto de leerse como impacto: entraría con panel conceptual propio o no entraría |

Más abajo, en una línea cada una: DataCite, OpenAIRE, Semantic Scholar,
Europe PMC y Wikidata. Dimensions y Lens.org quedan fuera por requerir acuerdo.

---

## 8. Corpus paralelo declarado — producción institucional fuera de Scopus/SciVal (propuesta, 2026-08-27)

**No confundir con §6 arriba:** eso descarta *fusionar* corpus de fuentes
distintas en un solo universo. Esto es lo que `D-206` ya deja abierto en su
propio texto — *"Un corpus nuevo —SciELO, OpenAlex— entraría como **corpus
paralelo declarado**, nunca sumado al universo"* — y que hasta ahora nadie
había propuesto ejecutar.

**La necesidad, con evidencia acumulada:**

- OpenAlex atribuye **1.112 obras** a la UFT por ROR. **698** ya están en el
  universo Scopus/SciVal; **414 no** (`V2-26`).
- De esas 414, la revisión humana ya confirmó **20** como producción real UFT
  (DOI + tipo documental citable + autor con apellido ya presente en el
  corpus + ≥3 citas en OpenAlex), aplicadas en `internal/openalex_cobertura.csv`
  con veredicto `CONFIRMADO_PRODUCCION_UFT`.
- La evidencia independiente de Crossref (`V2-26 bis`) confirma afiliación UFT
  en **56 autores más** (sobre las 365 filas pendientes con DOI), sin haber
  sido revisados todavía uno por uno.
- Es decir: hay una base creciente y verificable de producción institucional
  real que **Scopus y SciVal, por diseño, nunca van a indexar** (criterios de
  indexación distintos, no un error de carga) — el informe hoy no la muestra
  en ninguna parte.

**Lo que esto NO es:** no propone tocar las 823 publicaciones del universo
canónico, ni su cifra, ni ningún indicador que dependa de ese denominador
(`D-16`). Sumar produciría exactamente la cifra irreconciliable que §6 arriba y
`D-206` prohíben.

**Lo que sí propondría, si se autoriza diseñarlo:**

- Una sección o página aparte —"Producción institucional detectada fuera de
  Scopus/SciVal" o equivalente—, con su propio denominador declarado
  (`D-16`), que muestre los casos con veredicto `CONFIRMADO_PRODUCCION_UFT`
  de `internal/openalex_cobertura.csv` a medida que la revisión avanza.
  Nunca mezclada con `P-01`/`P-03` ni con ningún indicador del universo
  primario.
- Etiquetado explícito de la fuente y el método de verificación en cada obra
  (OpenAlex + Crossref, revisión humana, fecha), para que nadie la lea como
  Scopus.
- Seguir la revisión humana de los 294 autores restantes sin evidencia fuerte
  todavía (`internal/openalex_cobertura.csv`, `internal/openalex_cobertura_crossref.csv`)
  antes de fijar un tamaño definitivo de este corpus paralelo.

**Qué falta confirmar:** esto es una propuesta de alcance, no una decisión
tomada — `D-206` exige que ampliar lo que el informe cubre sea "una decisión
de alcance aparte, posterior y explícita". Falta que el usuario autorice
diseñarla e implementarla, y decidir dónde vive en la navegación del sitio.

> **Distinto de esto:** `produccion-ampliada.html` (implementado
> 2026-09-02) publica un corpus paralelo declarado de otra naturaleza —
> agregados Facultad × año que una Facultad autodeclara en su propio
> sitio, sin verificación individual obra por obra — bajo el mismo
> principio `D-206`. No sustituye esta propuesta de individual
> `CONFIRMADO_PRODUCCION_UFT` (evidencia OpenAlex + Crossref + revisión
> humana caso por caso), que sigue abierta. Ver
> `src/build/09_produccion_declarada.py` y `docs/FUENTES_Y_APIS.md` §2.6.
>
> El marco general para relacionar estos dos tipos de evidencia —y
> clasificar cualquier fuente futura de la misma familia— está en
> `docs/METODOLOGIA_FUERA_DE_SCOPUS.md`: `produccion-ampliada.html` es
> Nivel D (declarado), esta propuesta sería Nivel V (verificado obra por
> obra) si se autoriza construirla.
