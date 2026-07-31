# PLAN.md
# Plan maestro por fases

**Última actualización:** 2026-07-31 (Fase 2)

Orden de precedencia ante conflicto (definido en `CLAUDE.md`):
decisión validada en sesión → `CLAUDE.md` → `PROJECT_SPEC.md` → `PLAN.md` →
`SESSION_NOTES.md` → memoria recuperada → inferencia.

---

## Estado general

| Fase | Nombre | Estado |
|---|---|---|
| 1 | Fundamentos, auditoría de datos y validación | ✅ **Completada** (2026-07-31) |
| 2 | Indicadores, arquitectura y UX/UI | ✅ **Completada** (2026-07-31) |
| 3 | Implementación, despliegue, documentación y replicabilidad | ⏳ Pendiente |

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

## Fase 3 — Pendiente

**Bloqueos conocidos:** ninguno técnico. Requiere la decisión T-11 (alcance de
publicación de fichas) antes de generar las páginas de autor.

**Objetivo:** estructura del proyecto, entregable funcional, documentación de
despliegue, replicabilidad, licencia.

**Ya adelantado en Fase 1** (no repetir):
`config/institution.yml`, `config/matching_rules.yml`, `config/sources.yml`,
separación `data/raw` · `data/interim` · `src` · `docs` · `internal`.

---

## Pendientes transversales

| # | Pendiente | Fase objetivo | Origen |
|---|---|---|---|
| T-01 | Enriquecer ORCID desde Crossref por DOI (cobertura 97,7 %) | 2/3 | Confirmado por el usuario |
| T-02 | Validar institucionalmente el vocabulario de unidades académicas | 2 | Sin catálogo oficial |
| T-03 | Revisión humana de las 123 variantes de nombre encoladas | 2 | Regla P-03 |
| T-04 | Revisión humana de los 20 nombres con múltiples Scopus ID | 2 | Regla P-04 |
| T-05 | Decidir tratamiento del duplicado probable Article/Letter | 2 | Regla P-01 |
| T-06 | Reexportar Scopus con fecha de corte declarada | 2 | Ambigüedad de trazabilidad |
| T-07 | Excluir `Molecular Sequence Numbers` del dataset procesado | 2 | Regla E-06 |
| T-08 | Elegir stack de despliegue estático | 3 | No decidido |
| T-09 | Excluir `internal/` del bundle público en el build | 3 | `CLAUDE.md` |
| T-10 | Red de coautoría autor–autor derivada de `Autoria` | 3 | Diferido: depende de T-03 |
| T-11 | Decidir alcance de publicación de fichas de autor (589 vs. subconjunto) | 3 | `docs/AUTHOR_PROFILE.md` §5 |
| T-12 | Verificación automática de barrera pública/interna en el build | 3 | `docs/LAYERS.md` §6 |
| T-13 | Confirmar semántica del percentil de citación con documentación SciVal | 3 | Determinada empíricamente, no documentalmente |
