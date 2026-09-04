# Arquitectura técnica

**Capa:** técnica · **Estado:** implementada y en producción (V1 completa,
`STATE.md`); este documento describe lo construido, no un diseño pendiente

---

## 1. Principio rector

Web **estática**, sin backend obligatorio (`CLAUDE.md` `<technical_guardrails>`,
`PROJECT_SPEC` `<out_of_scope_for_v1>`). Todo el cálculo ocurre en el pipeline
de datos, offline. El navegador consume artefactos ya agregados y no recalcula
métricas.

Razón: el corpus es pequeño y de actualización esporádica (un export por
período). Preagregar en build elimina la necesidad de servidor, hace el
despliegue trivial y garantiza que la cifra publicada sea idéntica a la
auditada.

---

## 2. Pipeline de datos

```
data/raw/          →  src/audit/     →  data/interim/  →  src/build/  →  data/processed/  →  web/
(inmutable)           (auditoría)       (validado)        (build)        (artefactos)        (estático)
```

| Etapa | Responsabilidad | Estado |
|---|---|---|
| `data/raw/` | Exports originales. Nunca se modifican | ✅ implementado |
| `src/audit/` | Inventario, reconciliación, matching, validación | ✅ implementado |
| `data/interim/` | Universo, tabla maestra, log de matching, factibilidad | ✅ implementado |
| `src/build/` | Construcción de artefactos publicables (`01_publications.py`…`09_produccion_declarada.py`) | ✅ implementado |
| `data/processed/` | JSON preagregados que consume la web | ✅ implementado |
| `web/` | Sitio estático, 11 páginas | ✅ implementado y desplegado |

**Regla de barrera:** `src/build/` no lee de `data/raw/`. Sólo consume
`data/interim/`, que ya pasó las 30 reglas de validación. Si la validación
falla con severidad bloqueante, el build no debe ejecutarse.

---

## 3. Archivo maestro y artefactos

### Archivo maestro

`data/interim/publications_universe.csv` (823 filas) es la tabla canónica de
publicaciones, con las banderas `tiene_metricas`, `tiene_autoria_detallada` y
`tiene_area_tematica` que determinan el denominador de cada indicador.

`data/interim/authors_master_draft.csv` (589 filas) es el borrador inicial de
la tabla maestra de autores, una fila por forma de firma sin consolidar. El
plan original era promoverlo a `authors_master.csv` al cerrarse `T-03`/`T-04`
(ambos cerrados, 2026-08-26); en la práctica la consolidación tomó otra forma:
`config/identidades_consolidadas.yml` y `config/firmas_e09_resueltas.yml`
—generados por `src/review/apply_decisions.py` desde decisiones humanas en
`make revision`, nunca a mano (`D-08`)— son hoy el mecanismo real de
consolidación, y `data/processed/authors.json` (513 entidades) es el
artefacto final que sirve el sitio. `authors_master.csv` nunca se creó.

`internal/matching_log.csv` (1.207 filas) es la tabla de autoría — la entidad
puente del modelo. **Capa interna:** contiene las cadenas de afiliación crudas y
el método de detección.

### Artefactos publicables

Diseñados para carga diferida: la portada no descarga el corpus completo.
Tamaños medidos en `dist/`, no estimados (ver `README.md` §Rendimiento para el
detalle comprimido).

| Artefacto | Contenido |
|---|---|
| `kpis.json` | Los 6 KPIs de portada + fecha de corte |
| `series.json` | Series anuales preagregadas de todos los módulos |
| `publications.json` | 823 registros, campos de tabla y filtro |
| `authors.json` | 513 entidades de autor con agregados |
| `author/<id>.json` | Ficha individual con sus publicaciones, una por entidad (513 archivos) |
| `facets.json` | Valores de cada filtro con su recuento |
| `glossary.json` | Definiciones de métricas para tooltips |
| `meta.json` | Fuentes, cortes, ventana, versión del build |
| `hierarchy.json` | Jerarquía escuela→facultad para el explorador reactivo |
| `produccion_declarada.json` | Corpus paralelo declarado (`PD-01`), fuera del universo Scopus/SciVal — nunca se une a los anteriores (`D-206`, `D-398`) |

**Decisión:** las fichas de autor se generan como archivos individuales, no
como un único JSON con todas las entidades y sus publicaciones. Evita
descargar el corpus completo para ver una ficha.

---

## 4. Lógica de actualización

Un nuevo período de datos se incorpora así:

1. Depositar los nuevos exports en `data/raw/`.
2. Registrarlos en `config/sources.yml` con su fecha de corte y ventana.
3. `python3 src/audit/run_all.py` → revalida las 30 reglas.
4. Revisar las colas nuevas en `internal/` (ambigüedades no resueltas).
5. `python3 src/build/build_all.py` → regenera `data/processed/`.
6. Desplegar.

**Ningún paso requiere editar código.** La ventana temporal, el identificador
institucional y las reglas de matching viven en `config/`.

---

## 5. Despliegue

Sitio estático servible desde cualquier hosting de archivos. Sin base de datos,
sin proceso servidor, sin variables de entorno en runtime.

**`T-08` (cerrado):** se descartó todo generador de terceros (Astro, Eleventy,
Quarto, Observable Framework) a favor de **HTML/CSS/JS sin dependencias +
build en Python**, con pre-renderizado propio (`src/build/prerender.mjs`, vía
Node) para que cada página tenga contenido real sin JavaScript. Cumple los
requisitos que motivaron la decisión:

- Salida completamente estática, sin runtime de servidor.
- Generación de 513 páginas de autor en build (una por entidad publicada).
- Carga diferida por módulo.
- Sin dependencia de CDN externo en runtime (los datos son institucionales;
  `README.md` declara **0** dependencias externas en el navegador).

---

## 6. Integraciones externas

**Implementadas** (paso de enriquecimiento entre `interim` y `build`, por DOI):

| Integración | Script | Qué aporta | Ejecutada |
|---|---|---|---|
| Crossref | `src/enrich/orcid_crossref.py` | ORCID declarado por el editor | ✅ 2026-08-01 |
| ORCID Public API | `orcid_api.py`, `orcid_expand.py`, `orcid_afiliacion.py` | Verificación, ampliación y candidatos | ✅ |
| ROR | `src/enrich/ror_institucion.py` | Identidad de la institución y sus nombres registrados | ✅ 2026-08-25 |
| OpenAlex | `src/enrich/orcid_openalex.py` | ORCID donde no había y contraste de la detección por ROR. No es fuente independiente: ingiere Crossref | ✅ 2026-08-26 |
| OpenAlex por institución | `src/enrich/openalex_cobertura.py`, `openalex_cobertura_crossref.py` | La brecha de cobertura: producción que OpenAlex atribuye a la institución y el universo no tiene, con corroboración de Crossref | ✅ 2026-08-26 |
| Repositorio institucional (DSpace) | `src/enrich/dspace_inventario.py` | Confirmación cruzada de ORCID vía autoarchivo institucional | ✅ 2026-09-01 |
| Autoarchivo de biblioteca | `src/enrich/autoarchivo_uft.py` | Inventario curado por biblioteca UFT, cruce de identidad | ✅ 2026-09-01 |
| Listado propio de Facultad | `src/enrich/facultad_medicina_publicaciones.py` | Corpus paralelo declarado (`PD-01`), no verificado obra por obra — ver `docs/METODOLOGIA_FUERA_DE_SCOPUS.md` | ✅ 2026-09-01 |

Todas se declaran en `config/sources.yml` con su fecha de ejecución real
(`ejecutada: true`/`fecha_ejecucion`); ninguna corre en el build normal —cada
una se ejecuta aparte y versiona su salida, para que el sitio no dependa de
red disponible—. El detalle metodológico de cada vía está en
`docs/FUENTES_Y_APIS.md` §2.

Scopus y SciVal **no se consultan por API**: se leen de exports manuales
versionados en `data/raw/`. Confundir las dos cosas cambia lo que se puede
prometer sobre actualización y fecha de corte.

**Evaluadas y no implementadas:** SciELO, las API de Elsevier, Unpaywall y
Altmetric, entre otras. Qué preguntaría cada una, qué desbloquearía
y qué falta confirmar está en `docs/FUENTES_Y_APIS.md` §3; el orden de
prioridad, en `V2_BACKLOG.md` §7.

El contrato es `config/sources.yml`: cualquier fuente nueva se declara ahí con
su rol, fecha de corte y cobertura, y el pipeline la trata igual que a un
export manual. Las ocho reglas que un conector nuevo tiene que cumplir —modo
`--test` sin red, caché, fuente declarada por dato, ambigüedades encoladas y no
resueltas— están en `docs/FUENTES_Y_APIS.md` §4.

---

## 7. Rendimiento

| Regla | Aplicación |
|---|---|
| Preagregación | Todo indicador se calcula en build, nunca en el navegador |
| Carga diferida | Cada módulo pide su JSON al abrirse; la portada sólo `kpis.json` |
| Debounce en filtros | 250 ms en el buscador de texto; inmediato en facetas |
| Paginación | Tabla de publicaciones en páginas de 50; sin scroll infinito |
| Fichas individuales | Un archivo por autor, no un bundle monolítico |

El corpus (823 publicaciones, 513 entidades de autor) es lo bastante pequeño para filtrar
en cliente sobre `publications.json` sin índice invertido. Se registra que este
supuesto deja de valer alrededor de ~10.000 publicaciones, umbral a partir del
cual haría falta un índice precomputado.

---

## 8. Replicabilidad

Adaptar a otra institución no requiere tocar `src/`:

| Archivo | Qué cambia |
|---|---|
| `config/institution.yml` | Nombre, `scopus_affiliation_id`, ventana, branding |
| `config/matching_rules.yml` | Patrones de detección, vocabulario de unidades |
| `config/sources.yml` | Rutas, fechas de corte, roles |
| `config/indicators.yml` | Qué indicadores se publican y con qué advertencias |

Tres archivos más de `config/` **no se editan**: los genera
`src/review/apply_decisions.py` desde lo que una persona decidió en `make
revision` —`identidades_consolidadas.yml`, `firmas_e09_resueltas.yml` y
`orcid_revisado.yml`—. Un despliegue replicado empieza sin ellos, que es el
estado correcto: son decisiones sobre personas concretas de esta institución.

Separación software / datos institucionales: `src/`, `config/` y `web/` son
reutilizables; `data/` e `internal/` son propios de cada institución.
