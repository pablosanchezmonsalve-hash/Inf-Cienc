# Metodología para datos fuera de Scopus/SciVal

**Capa:** pública · **Estado:** vigente · **Última actualización:** 2026-09-02

Este documento fija cómo se clasifica, construye y publica cualquier fuente de
datos que no sea el corpus Scopus/SciVal. No reemplaza a `METHODOLOGY.md`
—ese gobierna el corpus canónico— ni a `D-206`/`D-398` —esos ya establecen
que un corpus nuevo se publica aparte, con denominador propio, nunca fusionado
al universo—. Responde la pregunta que esos textos dejan abierta: **cuando hay
más de una fuente fuera de Scopus, ¿cómo se relacionan entre sí?**

---

## 0. Por qué hace falta esto ahora

Hasta el 2026-09-01 "fuera de Scopus" tenía un solo caso real. Ya no: existen
tres fuentes con esa etiqueta, publicadas en el mismo día, y son
**metodológicamente incompatibles** entre sí, aunque las tres respeten
`D-206`:

- `PD-01` (publicado): la Facultad de Medicina y Salud autodeclara su propio
  listado de publicaciones en su sitio. El proyecto no verifica cada título
  contra una fuente independiente antes de contarlo.
- `PD-02` (publicado el 2026-09-02, con autorización explícita del usuario —
  ver §4): la cola de revisión OpenAlex + Crossref (`V2-26`); de las 414
  obras que OpenAlex atribuye a la UFT y que el universo Scopus no tiene,
  sólo las que una persona confirmó una por una —DOI, tipo documental,
  apellido ya presente en el corpus, corroboración independiente de Crossref
  cuando existe— se cuentan aquí. Las que siguen sin revisión (394) se
  publican como cifra de transparencia, nunca como producción confirmada.
- `PD-03` (publicado el 2026-09-02, misma autorización): la hoja de
  autoarchivo que biblioteca cura, para TODA la institución a la vez —no
  una sola Facultad como `PD-01`—. Mismo Nivel D que `PD-01` (biblioteca
  declara, el proyecto no reverifica obra por obra), pero con un límite
  propio: la Facultad/Escuela viene en bruto por fila, y sólo una parte de
  esas cadenas tiene una relación escuela→Facultad validada
  institucionalmente. Ver §1 (Regla 2, nota sobre granularidad parcial).

Si un cuarto origen (SciELO, un segundo listado de otra Facultad) se agrega
sin este marco, el riesgo concreto es que alguien —humano o Claude, en una
sesión futura sin este contexto— termine sumando distintos tipos de
evidencia bajo el mismo indicador, o reinventando desde cero una distinción
que ya se resolvió una vez. Este documento existe para que eso no pase.

## 1. El eje que importa: nivel de evidencia por obra

No preguntar "¿está o no en Scopus?" — eso ya lo resuelve `D-206`. Preguntar:
**¿existe, para cada registro individual de esta fuente, un criterio
explícito y verificable de que esa obra específica pertenece al autor o
institución declarados?**

| | Nivel D — Declarado | Nivel V — Verificado obra por obra |
|---|---|---|
| **Qué certifica** | La fuente agrega/publica un conjunto; el proyecto no re-verifica cada título individualmente | Cada registro pasa un criterio explícito antes de contar |
| **Ejemplo real** | `PD-01` — Facultad de Medicina y Salud; `PD-03` — autoarchivo institucional | `PD-02` — cola OpenAlex, `internal/openalex_cobertura.csv` (`V2-26`) |
| **Estado** | Publicado (`produccion-ampliada.html`) | Publicado (`produccion-ampliada.html`, `PD-02`, desde 2026-09-02) |
| **Mecanismo de "cuenta"** | `corpus_paralelo_declarado: true` en `config/sources.yml` + `09_produccion_declarada.py` (`PD-01`); lectura directa de `data/enriched/autoarchivo_produccion.json` en el mismo build, agregada sólo donde la Facultad está validada (`PD-03`) | `internal/openalex_cobertura_decisiones.csv` (veredicto humano) → `apply_openalex_review.py` → `resolucion: CONFIRMADO_PRODUCCION_UFT` → agregado por año en `09_produccion_declarada.py` |
| **Cifras reales (2026-09-02)** | `PD-01`: 609 leídos → 63 duplicados por DOI colapsados → 325 fuera del universo Scopus → 83 en ventana 2023-2025 (cifra publicada), 222 fuera de ventana + 20 sin año. `PD-03`: 808 leídos → 7 duplicados colapsados → 498 fuera del universo → 341 con Facultad validada (125 en ventana, cifra publicada) + 157 sin Facultad validada (57 en ventana, publicadas por unidad declarada, nunca forzadas) | 414 candidatos → 20 confirmados (`CONFIRMADO_PRODUCCION_UFT`), 394 `PENDIENTE_REVISION_HUMANA` — ninguno se promueve solo (`D-313`) |
| **Corroboración cruzada** | Ninguna prevista: es la propia institución declarando | Crossref, cuando el DOI existe (`internal/openalex_cobertura_crossref.csv`) — refuerza, no reemplaza la revisión humana |

Mezclar estos dos niveles bajo un mismo número sería el mismo error que
`METHODOLOGY.md` §3 y §4 ya evitan dentro del corpus canónico —presentar
certidumbres distintas como si fueran la misma medición— aplicado ahora a lo
que queda fuera de él.

**Matiz que `PD-03` agrega, dentro del mismo Nivel D**: "declarado" no
significa "siempre agregable a Facultad". `PD-01` viene de UNA Facultad que
declara su propio sitio — su granularidad (Facultad × año) nunca está en
duda. `PD-03` viene de biblioteca, para toda la institución, con la unidad
en bruto por fila — la granularidad SÍ varía según cuánto de esa cadena
esté validado. Esto no es un tercer nivel de evidencia (la pregunta de la
§1 sigue siendo la misma: nadie reverifica la obra, sólo la unidad
declarada), es un límite de COMPLETITUD dentro del mismo Nivel D, y se
resuelve igual que cualquier otro límite conocido en este proyecto: se
declara, nunca se oculta ni se fuerza (ver Regla 2 abajo).

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

Ya construido para Nivel D con Facultad SIEMPRE canónica: la bandera
`corpus_paralelo_declarado: true` + `09_produccion_declarada.py` descubren
genéricamente cualquier fuente de este tipo. Una segunda Facultad que
publique su propio listado se integra agregando su entrada a `sources.yml`
con la misma bandera y un conector que siga el esquema documentado en
`facultad_medicina_publicaciones.py` —cero cambios en `src/build/`.

`PD-03` es Nivel D pero NO tiene Facultad siempre canónica (ver el matiz de
§1), así que NO usa ese mismo mecanismo — forzar su esquema habría exigido
que `_leer_registros()`/`_deduplicar()` de `PD-01` aceptaran `facultad`
vacía, mezclando dos contratos distintos en una sola función. Vive como su
propio bloque en `09_produccion_declarada.py`, con su propia deduplicación
(por unidad-o-Facultad + DOI) y su propia partición (con Facultad validada
/ sin ella). Una tercera fuente de este tipo —otro inventario con unidad en
bruto— seguiría el mismo patrón que `PD-03`, no el de `PD-01`.

Una fuente Nivel V no puede enchufarse en ninguno de los dos: necesita su
propio mecanismo de cola y su propio criterio de "confirmado", porque el
nivel de evidencia por registro es cualitativamente distinto, no un dato
más en la misma tabla.

### Regla 3 — Evidencia cruzada refuerza, nunca duplica

Cuando dos fuentes independientes corroboran el **mismo** registro (mismo
DOI), eso es evidencia más fuerte para ese registro — nunca un segundo
registro. Ya construido: Crossref sobre un candidato OpenAlex
(`_bloque_crossref` en `src/review/build_openalex_review.py`) aparece como
apoyo adicional en la ficha de revisión de esa misma obra, no como una obra
nueva.

La deduplicación en sí vive en el consumidor, no en el conector: el conector
de Medicina no deduplica —conserva los 609 registros crudos tal como la
fuente los declara (`D-400`, sesión V2-27: "borrarlos en el extractor
ocultaría un dato de la fuente")—; es `09_produccion_declarada.py`, que sabe
que va a publicar un recuento, quien deduplica por `(facultad, DOI)` antes
de contar (`D-370`). Ingestar y contar son responsabilidades distintas; sólo
la segunda decide qué es un duplicado.

### Regla 4 — Cada nivel, su propio indicador

Nunca combinar Nivel D y Nivel V bajo una etiqueta compartida como "fuera de
Scopus", aunque las tres respeten `D-206`. `PD-01`/`PD-03` (Nivel D) y `PD-02`
(Nivel V, cola OpenAlex + Crossref) son la instancia concreta de esta regla —
ya declarada en `docs/V2_BACKLOG.md` §8. Publicados como tres indicadores
separados, cada uno con su propia sección en `produccion-ampliada.html`;
ninguno es una fila más dentro de otro — ni siquiera `PD-01` y `PD-03`,
que comparten nivel: son fuentes distintas (una Facultad declarando su
sitio; biblioteca curando autoarchivo institucional), con mecanismos de
"cuenta" distintos (ver Regla 2), y mezclarlas en una sola tabla ocultaría
esa diferencia. El único punto en que se tocan las tres es el total
combinado de la página (`total_fuera_de_scopus`), que es la unión por DOI
de las tres — aritmética declarada sobre los tres indicadores, no un cuarto
con fuente propia.

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

- **Actualización 2026-09-02**: el usuario autorizó explícitamente publicar
  el Nivel V como `PD-02` ("Integra todo el contenido recuperado desde
  APIs en un nuevo apartado que indique la producción total fuera de
  Scopus") — exactamente la decisión de alcance aparte, explícita y
  posterior que este documento exigía como condición. Implementado en
  `09_produccion_declarada.py` y `produccion-ampliada.html`; ver
  `docs/FUENTES_Y_APIS.md` §2.7. Esta sección se deja como registro de que
  la autorización fue explícita, no implícita ni asumida.
- **Segunda actualización, mismo día**: el usuario pidió, además, sumar
  "todas [las Facultades], usando el repositorio institucional" — otra
  decisión de alcance aparte y explícita, distinta de la anterior.
  Implementada como `PD-03` (autoarchivo institucional, Nivel D con el
  límite de granularidad de §1): sólo se agrega por Facultad donde esa
  relación está validada institucionalmente; el resto se publica por
  unidad declarada. Ver `docs/FUENTES_Y_APIS.md` §2.8.
- No reabre `D-206`, `D-313`, `D-314` ni `D-398`: ni `PD-02` ni `PD-03`
  tocan `publications_universe.csv` ni ningún indicador de citas/FWCI.
- No cambia nada del corpus Scopus/SciVal ni de `METHODOLOGY.md`.
- Es un marco para clasificar y aislar fuentes nuevas — no reemplaza a
  `docs/DECISIONS.md` como registro de qué se decidió y cuándo.

---

## Referencias

- `docs/DECISIONS.md` — `D-16`, `D-206`, `D-226`, `D-313`, `D-314`, `D-370`,
  `D-398`, `D-400`, y las decisiones de autorización de `PD-02`/`PD-03`
  (2026-09-02).
- `docs/V2_BACKLOG.md` §8 — la propuesta de publicar el Nivel V, autorizada
  y cerrada el 2026-09-02.
- `docs/DATA_MODEL.md` — «Corpus paralelo declarado (fuera de este modelo)».
- `docs/FUENTES_Y_APIS.md` §2.6 (Nivel D, `PD-01`), §2.7 (Nivel V, `PD-02`)
  y §2.8 (Nivel D con límite de granularidad, `PD-03`).
- `config/sources.yml` → `facultad_medicina_publicaciones`,
  `corpus_paralelo_declarado`, `openalex_api`, `autoarchivo_biblioteca`.
- `src/build/09_produccion_declarada.py` — mecanismo genérico de Nivel D
  (`PD-01`), agregación de Nivel V (`PD-02`), y bloque propio para Nivel D
  con granularidad parcial (`PD-03`), en un mismo build.
- `src/review/build_openalex_review.py`, `src/review/apply_openalex_review.py`
  — mecanismo de cola de Nivel V; su `resolucion: CONFIRMADO_PRODUCCION_UFT`
  alimenta `PD-02`.
- `src/enrich/autoarchivo_produccion.py` — reutiliza
  `common.canonical_academic_unit()`/`common.facultad_de()` (las mismas
  funciones que `P-07`) para resolver `PD-03` a Facultad sólo donde esa
  relación está validada.
