# Pendientes para V2

**Fase:** 3 · Cerrada la V1

Ordenados por lo que desbloquean. Los pendientes `T-xx` vienen de fases
anteriores y siguen abiertos.

---

## 1. Calidad de datos — habilitan indicadores hoy bloqueados

| # | Pendiente | Desbloquea | Origen |
|---|---|---|---|
| **V2-01** | Enriquecer ORCID desde Crossref por DOI (cobertura 97,7 %) | Identidad persistente; consolidación de variantes; campo exigido por `PROJECT_SPEC` | T-01 |
| **V2-02** | Revisión humana de las 123 variantes de nombre | `C-05` red de coautoría; recuento real de personas | T-03 |
| **V2-03** | Revisión humana de los 20 identificadores fragmentados | `C-07` liderazgo autoral | T-04 |
| **V2-04** | Validar institucionalmente el vocabulario de unidades | Retirar la advertencia destacada de `P-07` | T-02 |
| **V2-05** | Reexportar Scopus con fecha de corte declarada | Cierra la única brecha de trazabilidad que queda | T-06 |
| **V2-06** | Reexportar SciVal con autocitas | `X-01` tasa de autocitación | Fase 2 |
| **V2-07** | Decidir el duplicado probable Article/Letter | Cierra la última ambigüedad de publicaciones | T-05 |

**V2-01 es el de mayor rendimiento.** Sin ORCID, las 589 firmas no pueden
consolidarse y tres indicadores quedan bloqueados. Es la única vía identificada
que no depende de trabajo manual.

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
| **T-11** | Alcance de publicación de fichas de autor | **Supuesto vigente:** se publican las 589, ranking por defecto n ≥ 5 (`config/publication.yml`). Sin confirmar |
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
| **V2-17** | Sin pruebas automatizadas del sitio | Existe una verificación manual con Playwright; no está en el repositorio |
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
