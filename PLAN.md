# PLAN.md
# Plan maestro por fases

**Última actualización:** 2026-07-31

Orden de precedencia ante conflicto (definido en `CLAUDE.md`):
decisión validada en sesión → `CLAUDE.md` → `PROJECT_SPEC.md` → `PLAN.md` →
`SESSION_NOTES.md` → memoria recuperada → inferencia.

---

## Estado general

| Fase | Nombre | Estado |
|---|---|---|
| 1 | Fundamentos, auditoría de datos y validación | ✅ **Completada** (2026-07-31) |
| 2 | Indicadores, arquitectura y UX/UI | ⏳ Pendiente |
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

## Fase 2 — Pendiente

**Objetivo:** catálogo de indicadores, selección V1, arquitectura técnica,
arquitectura UX/UI, definición de capas, ficha pública de autor.

**Entradas de Fase 1 que la condicionan:**

- El denominador de cada indicador se deriva de las banderas de disponibilidad
  (816 / 818 / 823), no de un total único.
- Las métricas normalizadas sólo son publicables a nivel individual con n,
  ventana y advertencia: 538 de 589 autores tienen n < 5.
- La comparación entre unidades académicas requiere advertencia de cobertura
  (63,8 %) y de sesgo disciplinar.
- ORCID entra al catálogo como placeholder declarado.

**Bloqueos conocidos:** ninguno. La Fase 2 puede iniciarse.

---

## Fase 3 — Pendiente

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
| T-10 | Red de coautoría autor–autor derivada de `Autoria` | 2/3 | Diferido |
