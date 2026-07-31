# Definición de capa pública e interna

**Capa:** técnica · **Fase:** 2

Materializa `CLAUDE.md` `<data_governance>`:

> Nunca publiques por defecto información que haya sido usada solo para
> depuración o conciliación interna.

---

## 1. Criterio de asignación

Un dato es **público** si describe un resultado; es **interno** si describe
cómo se llegó a él.

Caso límite resuelto: los nombres de autor son públicos (están en Scopus), pero
**la cola de revisión que los agrupa como posibles duplicados es interna**. Lo
sensible no es el nombre: es la afirmación no verificada de que dos firmas son
la misma persona.

---

## 2. Asignación por artefacto

| Artefacto | Capa | Se publica | Razón |
|---|---|---|---|
| `data/processed/*.json` | **Pública** | Sí | Resultados agregados y validados |
| `docs/AUDIT_REPORT.md` | **Pública** | Sí | Cifras y método; sin detalle nominal de colas |
| `docs/METHODOLOGY.md` | **Pública** | Sí | Criterios de cálculo |
| `docs/LIMITATIONS.md` | **Pública** | Sí | **Obligatoria**: publicar sin límites es el error |
| `docs/INDICATORS.md` | **Pública** | Sí | Definiciones y fórmulas |
| `docs/GLOSSARY.md` | **Pública** | Sí | Alimenta los tooltips |
| `docs/VALIDATION_REPORT.md` | **Pública** | Sí | Verificabilidad (Leiden: permitir verificación) |
| `data/interim/publications_universe.csv` | Pública | Derivado | Base de los artefactos |
| `data/interim/authors_master_draft.csv` | Pública | Derivado | Tabla maestra publicable |
| `data/interim/indicator_feasibility.csv` | Pública | Derivado | Evidencia del catálogo |
| **`internal/matching_log.csv`** | **Interna** | **No** | Cadenas de afiliación crudas, método y confianza por par |
| **`internal/ambiguities_authors.csv`** | **Interna** | **No** | 412 entradas de identidad no resuelta |
| **`internal/ambiguities_publications.csv`** | **Interna** | **No** | Duplicados probables y discrepancias |
| **`data/interim/matching_reconciliation.csv`** | **Interna** | **No** | Casos de divergencia entre métodos |
| **`data/raw/*`** | **Interna** | **No** | Exports con licencia Elsevier (ver §5) |
| `config/*.yml` | Técnica | Código | Sin secretos; parametrización |

---

## 3. Qué nunca se expone por defecto

1. **Cadenas de afiliación crudas** por autor y publicación.
2. **Colas de revisión nominal**: qué firmas se sospecha que son la misma
   persona. Publicarlo afirmaría una identidad no verificada sobre personas
   reales.
3. **El método y la confianza de detección** por registro individual.
4. **Los exports originales** de Scopus y SciVal.
5. **Notas de conciliación** y logs de proceso.

## 4. Qué sí se publica sobre la capa interna

El **recuento agregado** y su explicación metodológica. Es la forma de ser
transparente sobre la incertidumbre sin exponer afirmaciones no verificadas
sobre personas:

> «589 formas de firma detectadas. 123 corresponden a apellidos con más de una
> variante de nombre y 20 a nombres con más de un Scopus Author ID; ambas
> situaciones están declaradas sin resolver. El número de personas distintas es
> menor que 589.»

Eso es público. La lista nominal que lo sustenta, no.

---

## 5. Datos de origen y licencia

Los exports de Scopus y SciVal están sujetos a los términos de Elsevier. La
plataforma publica **indicadores derivados y metadatos bibliográficos**
(título, autores, año, DOI, fuente), no los archivos de origen.

`data/raw/` permanece en el repositorio de trabajo pero **no forma parte del
bundle desplegado**. La decisión de licencia del software y el tratamiento
definitivo de los datos institucionales corresponde a Fase 3
(`PROMPT_FASE_3` §8).

---

## 6. Implementación de la barrera

Pendiente T-09, a ejecutar en Fase 3:

1. El build sólo lee de `data/interim/` y `config/`. **Nunca de `internal/`.**
2. Verificación automática post-build: fallar si algún artefacto de
   `data/processed/` contiene campos de la lista de §3
   (`afiliacion_declarada_raw`, `metodo_blando`, `confianza`, `resolucion`).
3. `internal/` y `data/raw/` excluidos explícitamente del directorio de
   despliegue.

La verificación automática es deliberada: la separación de capas no puede
depender de que nadie se equivoque al escribir un `build`.
