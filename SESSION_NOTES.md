# SESSION_NOTES.md
# Bitácora de sesiones

---

## Sesión 2026-07-31 — Fase 1

**Estado inicial:** repositorio con 7 archivos de datos sueltos, un commit,
sin código, sin estructura, sin documentos de gobernanza.
`PLAN.md` y `SESSION_NOTES.md` no existían pese a estar exigidos por
`CLAUDE.md`. Sin Claude-Mem disponible: esta sesión es el punto de origen.

### Decisiones tomadas

| # | Decisión | Fundamento |
|---|---|---|
| D-01 | `EID` es PK de Publicación; `DOI` clave secundaria | 100 % cobertura, 0 duplicados; 19 registros sin DOI |
| D-02 | Doble método de detección institucional con reconciliación obligatoria | Un solo método no es auditable |
| D-03 | Prohibido el matching por subcadena; patrón con límite de palabra | 15 falsos positivos medidos con `inis` |
| D-04 | `Autoria` es entidad puente de primera clase | La afiliación varía entre publicaciones |
| D-05 | Los `.RData` son referencia, nunca fuente de indicadores | Proceso generador no trazable |
| D-06 | SciVal = métricas y temática; Scopus = autoría y afiliación | Cada fuente aporta lo que la otra no tiene |
| D-07 | ORCID se modela vacío y declarado, no se omite | Exigido por `PROJECT_SPEC.md` |
| D-08 | Duplicados probables y ambigüedades se encolan, no se resuelven | Restricción de `CLAUDE.md` |
| D-09 | `No determinada` es categoría de primera clase | No inventar datos |
| D-10 | Todo indicador declara fuente, corte, ventana, n y método | Trazabilidad |
| D-11 | Métricas de revista en entidad separada de métricas de documento | No confundir revista con artículo |
| D-12 | «h-index en ventana», nunca «h-index» | No es el h-index de carrera |
| D-13 | ID institucional y reglas en configuración, no en código | Replicabilidad |
| D-14 | Salidas de conciliación son capa interna por defecto | `<data_governance>` |
| D-15 | Los 396 investigadores son set de validación, no fuente de verdad | Confirmado por el usuario |

**Decisiones de alcance validadas por el usuario:** ventana 2023–2025; universo
= unión (823) con banderas de disponibilidad.

### Archivos creados

```
CLAUDE.md, PROJECT_SPEC.md          versionados desde los uploads
PLAN.md, SESSION_NOTES.md           gobernanza que faltaba
README.md, requirements.txt, .gitignore
prompts/PROMPT_{COMPACTO,FASE_1,FASE_2,FASE_3}.md
config/{institution,matching_rules,sources}.yml
src/audit/{common,01_inventory,02_reconcile_sources,
           03_affiliation_variants,04_author_population,
           05_validation_rules,run_all}.py
docs/{AUDIT_REPORT,DATA_MODEL,METHODOLOGY,LIMITATIONS,VALIDATION_REPORT}.md
internal/{ambiguities_authors,ambiguities_publications,matching_log}.csv
data/raw/                           los 7 archivos originales, movidos con git mv
data/interim/                       11 salidas regenerables
```

Ningún archivo de datos original fue modificado.

### Supuestos descartados durante la sesión

| Supuesto inicial | Qué pasó |
|---|---|
| «18 DOI duplicados en el CSV» | **Falso.** Artefacto de contar 19 DOI ausentes como repetidos. El recuento real es 0 |
| «La cobertura de unidad académica es 70,1 %» | **Falso.** La extracción tomaba la facultad de otra institución en casos de doble afiliación. Real: 63,8 % |
| «El patrón peligroso es `finis`» | **Impreciso.** El peligroso es la subcadena `inis` (15 falsos positivos); `finis` da 0 |
| «El patrón `\bfinis\s+terrae\b` es suficiente» | **Insuficiente.** Perdía `Universidad Finis-Terrae` con guion. Corregido a `[\s\-]+` |
| «La brecha 585/440/396 indica fallas del trabajo manual» | **Falso.** El trabajo manual era correcto; la brecha es de ventana temporal (143 autores sólo en 2023) y de variantes de firma |
| «Conviene quedarse con la intersección de 811 publicaciones» | **Descartado.** Las 7 exclusivas de Scopus son humanidades y ciencias sociales; excluirlas agravaba el sesgo de cobertura |

### Ambigüedades abiertas

- 249 casos de un Scopus ID con varios nombres (P-05).
- 123 variantes de nombre del mismo apellido base (P-03).
- 20 nombres con varios Scopus ID (P-04).
- 24 autores con más de una unidad académica (I-06).
- 8 publicaciones con bloques autor/afiliación desalineados.
- 1 duplicado probable Article/Letter (P-01).
- 12 publicaciones presentes en una sola fuente (X-01).
- El export de Scopus no declara fecha de corte.
- El vocabulario de unidades no está validado institucionalmente.

### Verificación

29 reglas ejecutadas: 28 pasan, 1 falla no bloqueante (`E-06`, columna
`Molecular Sequence Numbers` vacía — hallazgo real, debe excluirse en Fase 2).
Cero fallas bloqueantes.

Auditoría reproducible completa: `python3 src/audit/run_all.py`.

### Próximo paso recomendado

Iniciar Fase 2 (`prompts/PROMPT_FASE_2.md`): catálogo de indicadores y
selección V1. Sin bloqueos. Los pendientes T-01 a T-10 están en `PLAN.md`.
