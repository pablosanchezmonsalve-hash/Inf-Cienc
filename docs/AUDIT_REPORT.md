# Reporte de auditoría — Fase 1

**Capa:** pública · **Fecha:** 2026-07-31 · **Reproducible con:** `python3 src/audit/run_all.py`

Todas las cifras de este documento son salida de los scripts de `src/audit/`.
Ninguna fue transcrita a mano.

---

## 1. Objetivo

Auditar los archivos disponibles, construir el modelo lógico preliminar, diseñar
la tabla maestra de autores UFT y establecer reglas de validación verificables.

## 2. Decisiones de alcance

Validadas con el responsable del proyecto el 2026-07-31:

| Decisión | Valor | Consecuencia |
|---|---|---|
| Ventana temporal | **2023–2025** | 823 publicaciones en vez de 591; 589 autores en vez de 446 |
| Universo de publicaciones | **Unión con banderas de disponibilidad** | Se conservan las 12 publicaciones presentes en una sola fuente |
| Lista de 396 investigadores | **Set de validación**, no fuente de verdad | La tabla maestra se construye desde las fuentes primarias |
| Catálogo de unidades / ORCID | No disponibles institucionalmente | Vocabulario inferido; ORCID como pendiente vía Crossref |

## 3. Inventario de archivos

| Archivo | Tipo | Filas × Cols | Rol | Observaciones |
|---|---|---|---|---|
| `export_1667ea7a-….csv` | CSV Scopus | 818 × 45 | **primaria** | Autoría y afiliación. Sin fecha de corte declarada. Sin ORCID |
| `Publications_at_Universidad_Finis_Terrae_2023_-_2025.xlsx` | XLSX SciVal | 816 × 70 | **primaria** | Métricas y áreas temáticas. Cabecera en fila 20. Corte 2026-07-22 |
| `Scopus_Normalizado.RData` | bibliometrixDB | 818 × 65 | referencia | 6 columnas residuales de join |
| `Scival_Normalizado.RData` | bibliometrixDB | 818 × 59 | referencia | **No contiene métricas SciVal** pese al nombre |
| `Unificado_Normalizado.RData` | bibliometrixDB | 818 × 65 | referencia | Difiere del anterior en 7 columnas |
| `2026_Reporte-UFT.xlsx` | XLSX, 8 hojas | — | validación | Trabajo manual previo, 2024–2025. Fórmulas vivas |
| `Informe 2024-2025.xlsx` | XLSX | 217 × 13 | documental | Fórmulas rotas (libro externo ausente) |

Inventario completo de columnas: `data/interim/inventory_columns.csv`.

## 4. Universo canónico

**823 publicaciones**

| Año | Publicaciones |
|---|---|
| 2023 | 228 |
| 2024 | 276 |
| 2025 | 319 |

| Tipo documental | n |
|---|---|
| Article | 595 |
| Review | 133 |
| Book chapter | 24 |
| Letter | 24 |
| Conference paper | 18 |
| Editorial | 8 |
| Otros | 21 |

**Banderas de disponibilidad:**

| Bandera | n | Uso |
|---|---|---|
| Con métricas (FWCI, citas SciVal) | 816 | Denominador de indicadores de impacto |
| Con autoría detallada | 818 | Denominador de rankings de autor |
| Con clasificación temática | 816 | Denominador de vistas temáticas |

## 5. Reconciliación entre fuentes

| Verificación | Resultado |
|---|---|
| EID en ambas fuentes | 811 |
| Sólo en Scopus | 7 (sin FWCI ni área temática) |
| Sólo en SciVal | 5 (sin detalle de autoría) |
| Discrepancia de año | **0** |
| Discrepancia de DOI | **0** |
| EID duplicados | **0** |
| DOI duplicados | **0** |
| Duplicados probables por título | **1 grupo**, encolado sin resolver |
| Citas: Scopus vs SciVal | 3.909 vs 3.935 · Δ +26 (+0,67 %) en 88 publicaciones |

## 6. Detección institucional

Dos métodos independientes, reconciliados entre sí.

| Método | Criterio | Publicaciones detectadas |
|---|---|---|
| **Duro** (I-02) | `Scopus Affiliation ID = 60105368` | 811 |
| **Blando** (I-03) | patrón `\bfinis[\s\-]+terrae\b` | 818 |

| Reconciliación (I-04) | Resultado |
|---|---|
| Sólo por método duro | **0** |
| Sólo por método blando | 7 — exactamente las 7 publicaciones ausentes de SciVal |
| Sin ninguna detección | **0** |

Los dos métodos **no se contradicen en ningún caso**. Las 7 divergencias tienen
explicación estructural completa.

**421 cadenas literales distintas** de afiliación institucional, en 858
apariciones.

### Falsos positivos medidos, no supuestos

| Patrón | Cadenas de falso positivo |
|---|---|
| `inis` (subcadena suelta) | **15** — «Ministerio de Salud», «Faculty of Economics and Business», «Department of Medicine and Geriatrics»… |
| `finis` (sin exigir «terrae») | 0 |
| `\bfinis[\s\-]+terrae\b` (en uso) | 0 |

El separador admite guion porque la variante `Universidad Finis-Terrae` existe
en los datos y se perdía con un patrón que exigiera espacio.

## 7. Unidad académica

Inferida por parsing, restringida a la ventana de texto que precede a la
institución foco.

- Cobertura: **63,8 %** de las 1.207 apariciones firma × publicación (filas
  del log; los pares distintos son 1.205).
- **437 pares** como `No determinada`, sin imputar.
- 13 unidades canónicas; **11 variantes** fuera del vocabulario, conservadas.

| Unidad | Pares |
|---|---|
| Facultad de Medicina | 527 |
| *No determinada* | 437 |
| Facultad de Educación, Psicología y Familia | 50 |
| Facultad de Ingeniería | 49 |
| Facultad de Odontología | 34 |
| Facultad de Economía y Negocios | 28 |
| Escuela de Nutrición y Dietética | 24 |
| Escuela de Kinesiología | 22 |
| Facultad de Derecho | 6 |
| Facultad de Artes | 6 |
| Facultad de Comunicaciones y Humanidades | 4 |
| Facultad de Arquitectura y Diseño | 3 |
| Escuela de Enfermería | 3 |
| Escuela de Ciencias de la Familia | 2 |

Ver `docs/LIMITATIONS.md` §4 sobre por qué esta tabla **no** mide productividad
relativa entre unidades.

## 8. Población de autores: la brecha resuelta

La discrepancia entre 585/440/396 detectada al inicio queda explicada.

| Población | n | Ventana |
|---|---|---|
| Extracción automática | **589** | 2023–2025 |
| Extracción automática | **446** | 2024–2025 |
| Excel, hoja detalle | 440 | 2024–2025 |
| Excel, hoja ranking | 396 | 2024–2025 |

**Descomposición:**

1. **589 → 446**: 143 autores aparecen únicamente en 2023, año que el trabajo
   manual nunca cubrió. No era un error, era alcance.
2. **446 → 440**: 6 autores adicionales que la extracción automática encuentra
   y el trabajo manual no registró.
3. **440 → 396**: deduplicación parcial de variantes de nombre. Los 396 del
   ranking están **íntegramente contenidos** en los 440 del detalle.

**Validación cruzada:** la extracción automática reproduce **los 396 nombres del
ranking y los 440 del detalle sin excepción** (0 entradas de tipo
`V-manual_no_reproducido`). El trabajo manual previo era correcto; el problema
no era la detección institucional sino el colapso de variantes de firma.

### Borrador de tabla maestra

**589 autores** en `data/interim/authors_master_draft.csv`.

| Atributo | Cobertura |
|---|---|
| Scopus Author ID resuelto | 575 / 589 |
| ORCID | **0** — no existe en las fuentes |
| Unidad académica identificada | 353 / 589 |
| Validados contra el ranking manual | 396 |
| Con menos de 5 publicaciones | 538 |

## 9. Ambigüedades encoladas

Registradas en `internal/`, **ninguna resuelta automáticamente**.

| Tipo | n | Regla |
|---|---|---|
| Un Scopus ID con varios nombres | 249 | P-05 |
| Variantes de nombre del mismo apellido | 123 | P-03 |
| Autor con varias unidades académicas | 24 | I-06 |
| Un nombre con varios Scopus ID | 20 | P-04 |
| Publicaciones en una sola fuente | 12 | X-01 |
| Bloques autor/afiliación desalineados | 8 | parsing |
| Duplicado probable por título | 1 grupo | P-01 |

## 10. Validación

**29 reglas ejecutadas · 28 pasan · 1 falla · 0 fallas bloqueantes.**

La única falla es `E-06`: la columna `Molecular Sequence Numbers` tiene 0 % de
cobertura. Es un hallazgo real y debe excluirse del dataset procesado en Fase 2.

Reporte completo: `docs/VALIDATION_REPORT.md`.

## 11. Corrección aplicada durante la auditoría

La primera versión de la extracción de unidad académica reportaba 70,1 % de
cobertura. Al verificar la salida se detectó que, en bloques con doble
afiliación, tomaba la facultad de **otra** institución: 30 pares autor ×
publicación se atribuían a `Faculty of Medicine and Nursing`, que pertenece a
la Universidad del País Vasco.

Corregido restringiendo la búsqueda a la ventana de texto que precede a la
institución foco. La cobertura real es **63,8 %**, no 70,1 %. La cifra bajó
porque la anterior incluía atribuciones falsas.

## 12. Estado de la fase

| Entregable exigido | Estado |
|---|---|
| Inventario de archivos | ✅ |
| Inventario de columnas reales | ✅ |
| Modelo lógico preliminar | ✅ `docs/DATA_MODEL.md` |
| Reglas de validación | ✅ 29 reglas ejecutables |
| Ambigüedades críticas identificadas | ✅ `internal/` |
| Tabla maestra de autores (diseño + borrador) | ✅ 589 autores |

**Fase 1 cerrada.**
