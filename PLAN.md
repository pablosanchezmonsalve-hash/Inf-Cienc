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
| T-02 | Validar institucionalmente el vocabulario de unidades académicas y la jerarquía escuela→facultad | 2 | Sin catálogo oficial |
| T-03 | Revisión humana de las 123 variantes de nombre encoladas | 2 | Regla P-03 |
| T-04 | Revisión humana de los 20 nombres con múltiples Scopus ID | 2 | Regla P-04 |
| T-05 | Decidir tratamiento del duplicado probable Article/Letter | 2 | Regla P-01 |
| T-06 | Reexportar Scopus con fecha de corte declarada | 2 | Ambigüedad de trazabilidad |
| ~~T-07~~ | ~~Excluir `Molecular Sequence Numbers` del dataset procesado~~ | — | **Cerrado en Fase 3**: no se materializa en `publications_universe.csv` |
| ~~T-08~~ | ~~Elegir stack de despliegue estático~~ | — | **Cerrado**: HTML/CSS/JS sin dependencias + build en Python |
| ~~T-09~~ | ~~Excluir `internal/` del bundle público~~ | — | **Cerrado**: `06_assemble_site.py` lo excluye y lo verifica |
| T-10 | Red de coautoría autor–autor derivada de `Autoria` | V2 | Diferido: depende de T-03 |
| ~~T-11~~ | ~~Confirmar alcance de publicación de fichas de autor~~ | — | **Cerrado**: confirmado por el usuario (589 firmas, ranking n>=5) |
| ~~T-12~~ | ~~Verificación automática de barrera pública/interna~~ | — | **Cerrado**: `05_verify_public_layer.py`, compuerta con código de salida |
| T-13 | Confirmar semántica del percentil de citación con documentación SciVal | V2 | Determinada empíricamente, no documentalmente |
| T-14 | Revisión humana de los 17 grupos de firmas que comparten ORCID | V2 | `internal/identity_candidates.csv`; 11 no los detecta el apellido |
| T-15 | Resolver el conflicto de `Castro-Sepúlveda M.`, con dos ORCID | V2 | `internal/orcid_conflicts.csv` |

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
