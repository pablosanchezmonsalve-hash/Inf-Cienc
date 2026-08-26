# PLAN.md
# Plan maestro por fases

**Última actualización:** 2026-07-31 (Fase 3 — V1 completa)

Orden de precedencia ante conflicto (definido en `CLAUDE.md`):
decisión validada en sesión → `CLAUDE.md` → `PROJECT_SPEC.md` → `PLAN.md` →
`SESSION_NOTES.md` → memoria recuperada → inferencia.

---

## Estado general

| Fase | Nombre | Estado |
|---|---|---|
| 1 | Fundamentos, auditoría de datos y validación | ✅ **Completada** (2026-07-31) |
| 2 | Indicadores, arquitectura y UX/UI | ✅ **Completada** (2026-07-31) |
| 3 | Implementación, despliegue, documentación y replicabilidad | ✅ **Completada** (2026-07-31) |

---

## Fase 1 — Completada

**Definition of done** (`prompts/PROMPT_FASE_1.md`):

- [x] Inventario de archivos → `docs/AUDIT_REPORT.md` §3, `data/interim/inventory_files.csv`
- [x] Inventario de columnas reales → `data/interim/inventory_columns.csv`
- [x] Modelo lógico preliminar → `docs/DATA_MODEL.md`
- [x] Reglas de validación → `src/audit/05_validation_rules.py`, `docs/VALIDATION_REPORT.md`
- [x] Ambigüedades críticas identificadas → `internal/`
- [x] Tabla maestra de autores: diseño y borrador → `data/interim/authors_master_draft.csv`

**Decisiones de alcance validadas con el usuario:**

| Decisión | Valor |
|---|---|
| Ventana temporal | 2023–2025 |
| Universo de publicaciones | Unión (823) con banderas de disponibilidad |
| Lista de 396 investigadores | Set de validación, no fuente de verdad |
| Catálogo oficial de unidades | No existe → vocabulario inferido, pendiente de validación |
| ORCID | No existe en las fuentes → recuperable vía Crossref / repositorio UFT |

**Resultados clave:** 823 publicaciones · 589 formas de firma detectadas ·
1.207 pares autor × publicación · 29 reglas de validación, 0 fallas bloqueantes.

---

## Fase 2 — Completada

**Definition of done** (`prompts/PROMPT_FASE_2.md`):

- [x] Catálogo de indicadores → `docs/INDICATORS.md` §1, `data/interim/indicator_feasibility.csv`
- [x] Selección V1 → `docs/INDICATORS.md` §2, `config/indicators.yml`
- [x] Arquitectura técnica → `docs/ARCHITECTURE.md`
- [x] Arquitectura UX/UI → `docs/UX_UI.md`
- [x] Definición de capas → `docs/LAYERS.md`
- [x] Ficha pública de autor → `docs/AUTHOR_PROFILE.md`
- [x] Filtros, glosario y tooltips → `docs/UX_UI.md` §6, `docs/GLOSSARY.md`

**Resultados:** 40 indicadores evaluados contra los datos reales · 27
publicados en V1 (26 calculables + 1 placeholder) · 8 diferidos a V2 · 5 no
calculables declarados · 6 KPIs de portada.

**Hallazgo relevante:** la semántica del campo de percentil de citación no
estaba declarada en el export y se determinó empíricamente (correlación −0,66
con citas). Habilita el indicador `I-05` (top 10 %).

**Decisiones que quedaron abiertas para Fase 3:** stack de despliegue (T-08) y
alcance de publicación de fichas de autor (T-11).

---

## Fase 3 — Completada

**Definition of done** (`prompts/PROMPT_FASE_3.md`):

- [x] Estructura del proyecto → `README.md`, `Makefile`
- [x] Entregable funcional base → `src/build/`, `web/`, `dist/` (9 páginas, 589 fichas)
- [x] Documentación de despliegue → `docs/DEPLOYMENT.md`
- [x] Documentación de actualización → `docs/UPDATING.md`
- [x] Estrategia de replicabilidad → `docs/REPLICATION.md`
- [x] Propuesta de licencia → `LICENSE` (MIT) + `docs/DATA_LICENSE.md`
- [x] Pendientes V2 → `docs/V2_BACKLOG.md`

**Resultados:** sitio estático de 9 páginas y 589 fichas de autor · ~1,9 MB ·
cero dependencias externas en el navegador · tres compuertas automáticas en el
pipeline · verificado en navegador real sin errores de consola.

**T-11 confirmado por el usuario** (sesión 2026-07-31): se publican las 589
firmas con el ranking filtrado por defecto a n >= 5, parametrizado en
`config/publication.yml`. Licencias aprobadas: MIT para el software, CC BY 4.0
para los datos derivados.

---

## Pendientes transversales

| # | Pendiente | Fase objetivo | Origen |
|---|---|---|---|
| ~~T-01~~ | ~~Enriquecer ORCID desde Crossref por DOI (cobertura 97,7 %)~~ | — | **Cerrado (2026-08-01)**: 174 de 589 firmas, 0 errores de red |
| ~~T-02~~ | ~~Validar institucionalmente el vocabulario de unidades académicas y la jerarquía escuela→facultad~~ | — | **Cerrado (2026-08-26)**: `vocabulario_validado_por_institucion: true` en `config/matching_rules.yml`. 25 respuestas del responsable del proyecto aplicadas (herramienta interactiva + CSV), más 1 corrección de extracción declarada (afiliación cruzada) y 2 jerarquías confirmadas a mano |
| ~~T-03~~ | ~~Revisión humana de las variantes de nombre encoladas (28 grupos, 27 pendientes)~~ | — | **Cerrado (2026-08-26)**: 0 pendientes en la cola «Variantes de nombre» tras aplicar las decisiones del usuario, fusionadas con las de la ronda anterior (`D-263`). Desbloquea `T-10` |
| ~~T-04~~ | ~~Revisión humana de los 20 nombres con múltiples Scopus ID, de los que 10 afectan al informe~~ | — | **Cerrado (2026-08-26)**: 0 pendientes en la cola «Varios Scopus ID» |
| ~~T-05~~ | ~~Decidir tratamiento del duplicado probable Article/Letter~~ | — | **Cerrado (2026-08-03)**: verificado por el usuario contra ambos DOI. Son dos documentos distintos con el mismo título; universo intacto en 823 |
| T-06 | Reexportar Scopus con fecha de corte declarada | 2 | **Conector probado de punta a punta** (2026-08-26): `src/enrich/scopus_api.py` consultó la API real y confirmó 818, coincide con `scopus_export.n_registros_leido`. Queda en `verificacion_api` dentro de `config/sources.yml` — NO es la fecha de corte del export vigente, que sigue `null` a propósito (`docs/UPDATING_REQUEST.md` §5). T-06 se cierra cuando exista una reexportación NUEVA con su propia fecha de corte declarada por la fuente |
| ~~T-07~~ | ~~Excluir `Molecular Sequence Numbers` del dataset procesado~~ | — | **Cerrado en Fase 3**: no se materializa en `publications_universe.csv` |
| ~~T-08~~ | ~~Elegir stack de despliegue estático~~ | — | **Cerrado**: HTML/CSS/JS sin dependencias + build en Python |
| ~~T-09~~ | ~~Excluir `internal/` del bundle público~~ | — | **Cerrado**: `06_assemble_site.py` lo excluye y lo verifica |
| ~~T-10~~ | ~~Red de coautoría autor–autor derivada de `Autoria`~~ | — | **Cerrado (2026-08-26)**: `C-05` se publicó en `colaboracion.html`, con comunidades Louvain visibles y declaradas como heurística (no como componente objetiva). Reactivo a los filtros: `web/assets/js/grafo.js` reimplementa `construir()`/`componentes()`/`comunidades()` en JS, verificado línea a línea contra `grafo_coautoria.py` sobre el corpus completo (mismos nodos, aristas, pesos y las dos particiones). La ficha de autor muestra la coautoría real de cada persona en vez de la nota de diferido |
| ~~T-11~~ | ~~Confirmar alcance de publicación de fichas de autor~~ | — | **Cerrado**: confirmado por el usuario (589 firmas, ranking n>=5) |
| ~~T-12~~ | ~~Verificación automática de barrera pública/interna~~ | — | **Cerrado**: `05_verify_public_layer.py`, compuerta con código de salida |
| ~~T-13~~ | ~~Confirmar semántica del percentil de citación con documentación SciVal~~ | — | **Cerrado (2026-08-26)**: `docs/METHODOLOGY.md` §7 bis. Nombre de columna real confirmado por una herramienta de terceros que procesa exports de SciVal; metodología «top X%» documentada por Elsevier en su SciVal Support Center coincide con el patrón empírico (5 más citadas en percentil 1-4, no citadas en 78). No se confirmó el mapeo valor-a-porcentaje línea por línea, pero la dirección del campo ya no depende sólo de medición propia |
| ~~T-14~~ | ~~Revisión humana de los grupos de firmas que comparten ORCID (10 casos, 2 pendientes)~~ | — | **Cerrado (2026-08-26)**: 0 pendientes en la cola «ORCID compartido». Evidencia reforzable con `make verificar-orcid` si se quiere confirmar contra el registro público |
| ~~T-15~~ | ~~Resolver el conflicto de `Castro-Sepúlveda M.`, con dos ORCID~~ | — | **Cerrado (2026-08-26)**: decidido «misma» en la revisión humana. `make verificar-orcid` puede confirmar cuál de los dos ORCID declara las publicaciones, si se quiere evidencia adicional |
| ~~T-16~~ | ~~Decidir si `internal/` y `data/raw/` siguen versionados en el repositorio público~~ | — | **Cerrado (2026-08-03)**: se mantienen, y `internal/README.md` pasa a declararlo con su razonamiento y las condiciones que obligarían a revisarlo |
| ~~T-17~~ | ~~Corregir las cadenas de unidad académica concatenadas sin separador~~ | — | **Cerrado (2026-08-03)**: reparación de codificación + 3 correcciones declaradas en config. 26 → 22 unidades distintas |
| ~~T-18~~ | ~~Trocear o paginar `publications.json`~~ | — | **Cerrado sin cambios (2026-08-03)**: 699 KB comprimen a 146 KB. La página entera transfiere 181 KB. La cifra que lo motivó era sin comprimir |

| T-19 | Ampliar cobertura de ORCID buscando por afiliación en el registro | V2 | **Corrido de nuevo el 2026-08-26** con `scripts\ampliar-orcid-afiliacion.ps1`: 630 titulares que declaran la institución, 347 firmas sin ORCID cruzadas, **0 candidatos nuevos**. No es un fallo: los 18 candidatos que este método había encontrado en rondas previas ya están todos confirmados y excluidos de la búsqueda (16 desde el 2026-08-05, 2 más el 2026-08-26). Lo que queda sin ORCID no comparte nombre+inicial con ningún titular que declare la institución — el techo de este método específico está alcanzado por ahora. Reintentar tiene sentido más adelante, cuando el registro de ORCID tenga más gente nueva. **Automatizado (2026-08-26)**: `.github/workflows/ampliar-orcid.yml` gana un disparo `schedule` mensual (día 1, 06:00 UTC), además del manual — no hace falta acordarse de correrlo |

---

## Estado de la V1

Los diez puntos obligatorios de `PROJECT_SPEC.md` `<v1_scope_required>`:

| # | Requisito | Entregable |
|---|---|---|
| 1 | Auditoría de datos y modelo lógico | `docs/AUDIT_REPORT.md`, `docs/DATA_MODEL.md` |
| 2 | Tabla maestra de autores | `data/interim/authors_master_draft.csv` (589) |
| 3 | Catálogo de indicadores | `docs/INDICATORS.md` (40) |
| 4 | Selección priorizada V1 | `config/indicators.yml` (27) |
| 5 | Arquitectura técnica base | `docs/ARCHITECTURE.md`, `src/build/` |
| 6 | Diseño UX/UI del dashboard | `docs/UX_UI.md`, `web/` |
| 7 | Capa pública e interna | `docs/LAYERS.md` + verificación automática |
| 8 | Ficha pública de autor | `docs/AUTHOR_PROFILE.md`, 589 fichas |
| 9 | Tooltips o glosario | `docs/GLOSSARY.md`, 14 entradas |
| 10 | Entregable técnico y documentación | `dist/`, 17 documentos |

De `<v1_scope_desirable>`: implementados persistencia de filtros en URL,
exportación de subconjuntos con procedencia, carga diferida por módulo y
breadcrumbs. No implementados: navegación facetada avanzada más allá de la
actual, y conectores a APIs (registrados como V2-01).
