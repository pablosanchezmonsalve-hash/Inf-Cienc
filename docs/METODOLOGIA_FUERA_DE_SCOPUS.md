# Metodología para datos fuera de Scopus/SciVal

**Capa:** pública · **Estado:** vigente · **Última actualización:** 2026-09-02

Este documento fija cómo se clasifica, construye y publica cualquier fuente de
datos que no sea el corpus Scopus/SciVal. No reemplaza a `METHODOLOGY.md`
—ese gobierna el corpus canónico— ni a `D-206`/`D-341` —esos ya establecen
que un corpus nuevo se publica aparte, con denominador propio, nunca fusionado
al universo—. Responde la pregunta que esos textos dejan abierta: **cuando hay
más de una fuente fuera de Scopus, ¿cómo se relacionan entre sí?**

---

## 0. Por qué hace falta esto ahora

Hasta el 2026-09-01 "fuera de Scopus" tenía un solo caso real. Ya no: existen
dos fuentes con esa etiqueta y son **metodológicamente incompatibles** entre
sí, aunque las dos respeten `D-206`:

- `PD-01` (publicado): la Facultad de Medicina y Salud autodeclara su propio
  listado de publicaciones en su sitio. El proyecto no verifica cada título
  contra una fuente independiente antes de contarlo.
- La cola de revisión OpenAlex + Crossref (`V2-26`, **no publicada**): 414
  obras que OpenAlex atribuye a la UFT y que el universo Scopus no tiene;
  cada una pasa por un criterio explícito —DOI, tipo documental, apellido ya
  presente en el corpus, corroboración independiente de Crossref cuando
  existe— antes de que una persona la confirme una por una.

Si un tercer origen (SciELO, un segundo listado de otra Facultad, un
repositorio institucional) se agrega sin este marco, el riesgo concreto es
que alguien —humano o Claude, en una sesión futura sin este contexto—
termine sumando ambos tipos de evidencia bajo el mismo indicador, o
reinventando desde cero una distinción que ya se resolvió una vez. Este
documento existe para que eso no pase.

## 1. El eje que importa: nivel de evidencia por obra

No preguntar "¿está o no en Scopus?" — eso ya lo resuelve `D-206`. Preguntar:
**¿existe, para cada registro individual de esta fuente, un criterio
explícito y verificable de que esa obra específica pertenece al autor o
institución declarados?**

| | Nivel D — Declarado | Nivel V — Verificado obra por obra |
|---|---|---|
| **Qué certifica** | La fuente agrega/publica un conjunto; el proyecto no re-verifica cada título individualmente | Cada registro pasa un criterio explícito antes de contar |
| **Ejemplo real** | `PD-01` — Facultad de Medicina y Salud | Cola OpenAlex, `internal/openalex_cobertura.csv` (`V2-26`) |
| **Estado** | Publicado (`produccion-ampliada.html`) | Construida como herramienta de revisión; **no publicada** como indicador |
| **Mecanismo de "cuenta"** | `corpus_paralelo_declarado: true` en `config/sources.yml` + `09_produccion_declarada.py` | `internal/openalex_cobertura_decisiones.csv` (veredicto humano) → `apply_openalex_review.py` → `resolucion: CONFIRMADO_PRODUCCION_UFT` |
| **Cifras reales (2026-09-02)** | 609 leídos → 63 duplicados por DOI colapsados → 325 fuera del universo Scopus → 83 en ventana 2023-2025 (cifra publicada), 222 fuera de ventana + 20 sin año (nota de transparencia) | 414 candidatos → 20 confirmados (`CONFIRMADO_PRODUCCION_UFT`), 394 `PENDIENTE_REVISION_HUMANA` — ninguno se promueve solo (`D-313`) |
| **Corroboración cruzada** | Ninguna prevista: es la propia institución declarando | Crossref, cuando el DOI existe (`internal/openalex_cobertura_crossref.csv`) — refuerza, no reemplaza la revisión humana |

Mezclar estos dos niveles bajo un mismo número sería el mismo error que
`METHODOLOGY.md` §3 y §4 ya evitan dentro del corpus canónico —presentar
certidumbres distintas como si fueran la misma medición— aplicado ahora a lo
que queda fuera de él.

## 2. Las reglas

### Regla 1 — Clasificar antes de construir

Antes de escribir una línea de `src/build/`, responder por escrito en
`config/sources.yml` (campo `rol` o `nota`): ¿hay un criterio explícito,
documentado y verificable que confirme cada obra individual? Si no lo hay,
es Nivel D. Si lo hay, es Nivel V. Ninguna fuente nueva empieza a alimentar
nada sin esta clasificación escrita.

### Regla 2 — Esquema por nivel, no por fuente

Fuentes del **mismo** nivel comparten mecanismo; fuentes de niveles
**distintos** nunca lo comparten, aunque ambas digan "fuera de Scopus".

Ya construido para Nivel D: la bandera `corpus_paralelo_declarado: true` +
`09_produccion_declarada.py` descubren genéricamente cualquier fuente de
este nivel. Una segunda Facultad que publique su propio listado se integra
agregando su entrada a `sources.yml` con la misma bandera y un conector que
siga el esquema documentado en `facultad_medicina_publicaciones.py` —cero
cambios en `src/build/`. Una fuente Nivel V no puede enchufarse ahí: necesita
su propio mecanismo de cola y su propio criterio de "confirmado", porque el
nivel de evidencia por registro es cualitativamente distinto, no un dato más
en la misma tabla.

### Regla 3 — Evidencia cruzada refuerza, nunca duplica

Cuando dos fuentes independientes corroboran el **mismo** registro (mismo
DOI), eso es evidencia más fuerte para ese registro — nunca un segundo
registro. Ya construido: Crossref sobre un candidato OpenAlex
(`_bloque_crossref` en `src/review/build_openalex_review.py`) aparece como
apoyo adicional en la ficha de revisión de esa misma obra, no como una obra
nueva.

La deduplicación en sí vive en el consumidor, no en el conector: el conector
de Medicina no deduplica —conserva los 609 registros crudos tal como la
fuente los declara (`D-343`, sesión V2-27: "borrarlos en el extractor
ocultaría un dato de la fuente")—; es `09_produccion_declarada.py`, que sabe
que va a publicar un recuento, quien deduplica por `(facultad, DOI)` antes
de contar (`D-370`). Ingestar y contar son responsabilidades distintas; sólo
la segunda decide qué es un duplicado.

### Regla 4 — Cada nivel, su propio indicador

Nunca combinar Nivel D y Nivel V bajo una etiqueta compartida como "fuera de
Scopus", aunque los dos respeten `D-206`. `PD-01` (Nivel D, publicado) y la
cola OpenAlex + Crossref (Nivel V, no publicada) son la instancia concreta
de esta regla — ya declarada en `docs/V2_BACKLOG.md` §8. Si se autoriza
publicar el Nivel V algún día, es un indicador propio (tentativamente
`PD-02`), nunca una fila más dentro de `PD-01`.

### Regla 5 — El denominador del universo no se toca, en ningún nivel

Ya establecido por `D-16`/`D-206`, reafirmado aquí explícitamente: ningún
corpus paralelo, de ningún nivel, cambia el recuento de las 823
publicaciones del universo canónico ni ningún indicador que dependa de ese
denominador. `data/interim/publications_universe.csv` es de solo lectura
para todo lo que este documento describe.

## 3. Checklist para clasificar una fuente nueva

1. **¿Hay un criterio explícito y documentado que verifique cada obra
   individual antes de contarla?** No → Nivel D. Sí → Nivel V.
2. **¿Es la propia institución/facultad autodeclarando su producción?**
   Normalmente Nivel D.
3. **¿Es un índice o agregador externo (OpenAlex, Crossref, SciELO, un
   repositorio) que requiere corroborar la atribución institucional obra
   por obra?** Normalmente Nivel V.
4. **¿Puede integrarse agregando sólo una entrada a `sources.yml`, sin
   tocar `src/build/`?** Si la respuesta es no incluso dentro del mismo
   nivel, el mecanismo genérico de ese nivel está mal diseñado — corregirlo
   antes de escribir código específico de esta fuente.
5. **Si no encaja limpiamente en Nivel D ni en Nivel V**, eso es una señal
   real de que hace falta un tercer nivel, no una razón para forzarla en
   uno de los dos existentes. Actualizar este documento con el nuevo nivel
   antes de construir nada.

## 4. Qué NO resuelve este documento

- No autoriza construir un indicador para la cola OpenAlex + Crossref
  (`PD-02` u otro nombre). Ampliar lo que el sitio publica sigue siendo,
  por `D-206`/`D-16`, una decisión de alcance aparte, explícita y posterior,
  que le corresponde al usuario.
- No reabre `D-206`, `D-313`, `D-314` ni `D-341`.
- No cambia nada del corpus Scopus/SciVal ni de `METHODOLOGY.md`.
- Es un marco para clasificar y aislar fuentes nuevas — no reemplaza a
  `docs/DECISIONS.md` como registro de qué se decidió y cuándo.

---

## Referencias

- `docs/DECISIONS.md` — `D-16`, `D-206`, `D-226`, `D-313`, `D-314`, `D-341`,
  `D-343`, `D-370`.
- `docs/V2_BACKLOG.md` §8 — la propuesta, todavía sin autorizar, de publicar
  el Nivel V.
- `docs/DATA_MODEL.md` — «Corpus paralelo declarado (fuera de este modelo)».
- `docs/FUENTES_Y_APIS.md` §2.6 — la fuente Nivel D implementada.
- `config/sources.yml` → `facultad_medicina_publicaciones`,
  `corpus_paralelo_declarado`.
- `src/build/09_produccion_declarada.py` — mecanismo genérico de Nivel D.
- `src/review/build_openalex_review.py`, `src/review/apply_openalex_review.py`
  — mecanismo de cola de Nivel V (herramienta de revisión, sin indicador
  publicado todavía).
