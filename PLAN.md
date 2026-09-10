# PLAN.md
# Plan maestro por fases

**Última actualización:** 2026-08-26 (Fase 3 — V1 completa)

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
| T-06 | Reexportar Scopus con fecha de corte declarada | 2 | **Sigue abierto tras la reexportación del 2026-09-08** (`D-580`). La reexportación existe y trae la ventana 2020-2025 con 1342 registros, pero el CSV nativo de Scopus **no trae filas de metadatos y no declara fecha de corte**: comprobado sobre `data/raw/Scopus_Sept.csv`, cuya primera línea ya es la cabecera de columnas. El 2026-08-30 que sí se declara es de SciVal y no se traslada (`D-260`, `D-261`, `docs/UPDATING_REQUEST.md` §5), así que `scopus_export.fecha_corte` sigue `null`. Se cierra cuando la fuente entregue un export que la declare, o cuando se documente que este formato nunca lo hará y se sustituya el requisito por la verificación por API de `T-20` |
| T-20 | Reejecutar la verificación por API de Scopus con la ventana 2020-2025 | 2 | **Abierto el 2026-09-09**. La verificación anterior (`scopus_export.verificacion_api`) consultaba `AF-ID(60105368) AND PUBYEAR > 2022 AND PUBYEAR < 2026` y afirmaba 818 resultados coincidentes: describe el export reemplazado y su ventana. Se retiró en vez de reescribirla a ojo, porque declararla vigente sin volver a consultar sería afirmar algo no comprobado. Reejecutar `src/enrich/scopus_api.py` con `PUBYEAR > 2019` y volver a declarar el bloque con el conteo que devuelva |
| T-21 | Recuperar ORCID para las 299 formas de firma que trajo la ventana 2020-2025 | 2 | **Abierto el 2026-09-09**. Las 328 firmas con ORCID siguen todas en el corpus nuevo. Sin identificador quedan 560 formas, pero sólo **299** son las que añadió la ampliación y nunca se consultaron: las otras 261 ya estaban en el corpus 2023-2025 y se consultaron sin resultado, que es un hueco distinto y más duro. La cobertura cae de 55,7 % a 36,9 % por dilución del denominador, no por dato perdido. Los conectores (`src/enrich/orcid_*.py`, `crossref_*`, DSpace, autoarchivo) salen a red y no se corrieron en esta carga. Hasta entonces, toda cifra de cobertura de ORCID describe el corpus 2023-2025 medido contra un universo 2020-2025, y así se declara en `docs/LIMITATIONS.md` |
| T-22 | Validar las 11 variantes de unidad académica que trajo la ventana 2020-2025 | 2 | **Abierto el 2026-09-09**. `data/interim/academic_unit_vocabulary.csv` marca 11 formas fuera del vocabulario controlado, con 17 pares autor × publicación afectados: cuatro son la forma inglesa de facultades ya conocidas (`School of Physiotherapy`, `Faculty of Humanities and Communications`, `School of Business and Economics`, `School of Family Studies`), una es un duplicado ortográfico (`Escuela de Post grado` frente a `Escuela de Postgrado`), otra es un error de codificación de la fuente (`Facultad de Ingenierĺa`, con `ĺ` en lugar de `í`), una es una cadena compuesta (`Facultad de Medicina y Facultad de Odontología`) y tres son escuelas que no aparecían antes (`Escuela de Educación Parvularia`, `Escuela de Historia – CIDOC`, `Escuela de Literatura`). Ninguna se resuelve por heurística (`D-08`): la equivalencia entre una forma inglesa y una facultad, o entre dos grafías de postgrado, es una afirmación institucional. La cola está generada en `internal/validacion_unidades.html`; se aplica con `python3 src/review/apply_unit_validation.py`. Es el mismo procedimiento con que se cerró `T-02` |
| ~~T-23~~ | ~~Resolver el presupuesto de peso de datos, excedido por la carga 2020-2025~~ | — | **Cerrado (2026-09-10)**: el techo de datos sube de 300 a 450 KB (`D-587`), aplicando la misma regla con que se fijó las dos veces anteriores, 1,21x lo medido. La evidencia se midió sobre ESTE corpus y no sobre el anterior (`D-588`): LCP de 1.596 ms en la portada bajo Slow 4G contra un umbral de 2.500, un 36 % de margen; con las 823 publicaciones de julio eran 1.424, así que duplicar el corpus costó 172 ms. Aligerar no era alternativa y está medido: quitar los tres campos que nada consume ahorra 41,3 KB comprimidos de los 70,7 que harían falta, porque son campos de altísima repetición que gzip ya colapsaba; la palanca queda declarada agotada (`D-590`). El próximo exceso NO se resuelve subiendo el techo otra vez sino recodificando `publications.json` en columnas, ya medido en 265,8 KB con rehidratación idéntica byte a byte (`D-589`). `node src/verify/run_all.mjs dist` pasa entera, exit 0 |
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
