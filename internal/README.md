# Capa interna — fuera del sitio y fuera del repositorio

Este directorio contiene material de conciliación y depuración: cómo se llegó a
los resultados, no los resultados. Conforme a `CLAUDE.md`, `<data_governance>`:

> Nunca publiques por defecto información que haya sido usada solo para
> depuración o conciliación interna.

**Este archivo es lo único que queda versionado del directorio.** Todo lo demás
vive sólo en el disco de la máquina de trabajo. Si acaba de clonar el
repositorio, `internal/` contiene este README y nada más: eso no es un error,
es la política vigente. La sección «Cómo se regenera» explica qué correr.

## Qué significa «interna» aquí, exactamente

**Excluido del sitio.** Desde la Fase 3 (T-09 cerrado),
`src/build/06_assemble_site.py` no copia este directorio a `dist/` y lo
verifica; el workflow de despliegue lo comprueba otra vez antes de publicar.
Nada de lo que hay aquí ha llegado nunca a
https://pablosanchezmonsalve-hash.github.io/Inf-Cienc/

**Excluido del repositorio (D-SEC-01).** La auditoría de seguridad de
2026-09-03 cerró la exposición que quedaba en el REPOSITORIO: `internal/` y
`data/raw/` dejan de versionarse por completo. Antes se mantenían versionadas
(desde `T-16`, 2026-08-03) con la transparencia como argumento; eso las hacía
accesibles a cualquiera que pudiera leer el repositorio, y el repositorio estaba
público. El razonamiento que sostuvo `T-16` —y los gatillos que lo
condicionaban— queda aquí como registro, aunque ya no es la postura vigente:

- Los **nombres de los autores ya son públicos**: están en Scopus. Pero este
  directorio no guarda sólo nombres: guarda **dudas y decisiones de identidad
  sobre personas reales** (`identity_decisions.csv`, `ambiguities_*.csv`,
  `matching_log.csv`, `orcid_*`), que `docs/LAYERS.md` §3 clasifica como
  «nunca se exponen por defecto». La transparencia no obliga a publicar
  afirmaciones no verificadas sobre una persona.
- Las **exportaciones originales de Elsevier** (`data/raw/`) son «no
  redistribuibles» por la licencia institucional. Versionarlas en un
  repositorio accesible las redistribuía igual que el sitio, con menos
  control.

**Postura vigente (D-SEC-01):** ambos directorios viven sólo en el disco de
trabajo local y en los artefactos de CI (que sí los conservan como registros
descargables de cada ejecución). No se citan desde el repositorio.

**Reglas que se preservan, sin excepción.** Que una corrida de CI genere estos
archivos no los convierte en publicables: los workflows los suben como
artefactos y **no** los commitean de vuelta. Que estén en su disco tampoco: no
se citan, no se enlazan desde el sitio, no se presentan como resultado y no
sustituyen a nada de `docs/`. Lo que puede difundirse es el **recuento
agregado** de ambigüedades y su explicación metodológica, nunca el detalle
nominal.

> La purga del historial sigue pendiente al 2026-09-03: expulsar estas capas
> del árbol no borra los blobs de los commits antiguos. El procedimiento, el
> respaldo previo obligatorio y el estado de cada rama están en
> `docs/SEGURIDAD_PURGA.md`, y requieren la sesión autenticada del propietario.

## Cómo se regenera

Todo esto se reconstruye desde `data/raw/`, que tampoco se versiona: hace falta
una máquina que tenga los exports bajo la licencia institucional. No hay forma
de regenerarlo desde el repositorio solo, y ése es el punto.

```bash
make auditoria             # las colas de ambigüedad y matching_log.csv
make revision              # las herramientas de revisión de identidad
make validar-unidades      # la validación de unidad académica
```

Los conectores de red (`make openalex`, `make cobertura`, `make orcid-datos`,
`make obras-externas`, …) escriben sus propias trazas aquí; cada uno las
declara en su docstring y en `config/sources.yml`.

## Contenido

Ninguno de estos archivos se versiona. La columna «Se genera con» dice qué lo
produce; lo que no tiene comando salió de una sesión puntual y no se regenera
solo.

### Trazabilidad y colas de ambigüedad

| Archivo | Qué es | Se genera con |
|---|---|---|
| `matching_log.csv` | Trazabilidad de cada par autor × publicación: cadena de afiliación cruda, método de detección, confianza | `make auditoria` |
| `ambiguities_authors.csv` | Cola de revisión humana de identidad de autor (reglas P-03, P-04, P-05, I-06) | `make auditoria` |
| `ambiguities_publications.csv` | Cola de revisión de publicaciones (reglas X-01, X-02, X-03, P-01) | `make auditoria` |
| `hallazgos_corpus.md` | Hallazgos del corpus en forma de lectura | `src/review/build_hallazgos.py` |

### Identidad de autor

| Archivo | Qué es | Se genera con |
|---|---|---|
| `identity_candidates.csv` | Firmas distintas que comparten ORCID: candidatas a ser la misma persona, sin confirmar (D-44) | `make auditoria` |
| `revision_identidad.html` | **Herramienta de revisión.** Generada, no editable a mano. Cruza todas las colas y presenta cada caso con su evidencia junta | `make revision` |
| `identity_decisions.csv` | Decisiones que una persona ha tomado en esa herramienta, exportadas desde el navegador. **Fuente de verdad, no regenerable** | exportación humana |
| `pendientes_consolidacion.{md,html}` | La misma cola en forma de lista, un enlace por caso | `make revision` |
| `revision_huecos_autores.html` | Qué fichas publicadas carecen de ORCID, de unidad determinada, o tienen identidad sin consolidar | `src/review/build_author_gaps.py` |
| `red_coautoria.html` | Vista interna del grafo de coautoría | `src/review/vista_red.py` |

### ORCID

| Archivo | Qué es | Se genera con |
|---|---|---|
| `orcid_conflicts.csv` | Firmas a las que Crossref atribuye más de un ORCID (V2-01) | `make auditoria` |
| `orcid_hallazgos.csv` | Asignaciones que el registro de ORCID no confirma (V2-01) | `src/enrich/orcid_api.py` |
| `orcid_ampliacion_log.csv` | Traza de cada hallazgo de `orcid_expand.py`: firma, ORCID, publicación y tipo de coincidencia | `src/enrich/orcid_expand.py` |
| `orcid_desacuerdos.csv` | Crossref y el registro atribuyen ORCID distintos a la misma firma (V2-03) | `src/enrich/orcid_expand.py` |
| `orcid_candidatos_afiliacion.csv` | Titulares que declaran la universidad y coinciden en nombre con una firma sin ORCID (V2-04). **Candidatos, no asignaciones** | `make orcid-afiliacion` |
| `zenodo_log.csv` | Traza de cada hallazgo de ORCID en Zenodo. `datacite.py` y `europepmc.py` declaran una traza equivalente, que en la corrida del 2026-09-03 no llegó a producir ninguna fila | `make orcid-datos` |

### Fuentes institucionales

| Archivo | Qué es | Se genera con |
|---|---|---|
| `dspace_candidatos.csv` | Candidatos de ORCID desde el repositorio institucional | `src/enrich/dspace_inventario.py` |
| `autoarchivo_candidatos.csv` | Candidatos de ORCID desde el inventario de autoarchivo | `src/enrich/autoarchivo_uft.py` |
| `autoarchivo_unidad_candidatos.csv` | Candidatos de unidad académica desde ese mismo inventario | `src/enrich/autoarchivo_uft.py` |
| `unit_validation_decisions.csv`, `validacion_unidades.{md,html}` | Validación humana de unidad académica (T-02) | `make validar-unidades` |
| `facultad_medicina_cruce.csv` | Cruce por DOI del listado propio de la Facultad contra el universo (PD-01) | `src/enrich/facultad_medicina_publicaciones.py` |
| `facultad_medicina_fuera_universo.md` | Desglose de los 68 DOIs de ese listado que el universo no tiene (V2-27) | sesión puntual |

### Producción fuera de Scopus

| Archivo | Qué es | Se genera con |
|---|---|---|
| `openalex_log.csv`, `openalex_deteccion.csv`, `openalex_desacuerdos.csv` | Traza del contraste con OpenAlex (V2-19) | `make openalex` |
| `openalex_cobertura.csv` | La cola de `PD-02`: obras que OpenAlex atribuye a la institución y el universo no tiene (V2-26) | `make cobertura` |
| `openalex_cobertura_crossref.csv` | Evidencia independiente de Crossref sobre esa misma cola (V2-26 bis) | `make cobertura-crossref` |
| `openalex_cobertura_decisiones.csv` | Veredicto humano sobre esa cola | exportación humana |
| `revision_cobertura_openalex.html` | Herramienta de revisión de la cola de `PD-02` | `make revisar-cobertura-openalex` |
| `obras_externas_cobertura.csv` | La cola de `PD-04`: obras en DataCite, Europe PMC y Zenodo fuera del universo | `make obras-externas` |
| `revision_obras_externas.html` | Herramienta de revisión de esa cola | `make revisar-obras-externas` |
| `obras_externas_decisiones.csv` | Veredicto humano sobre esa cola | exportación humana |
| `obras_externas_depuradas.csv` | Filas que la regla de título repetido sacó de la cola, con la fila que las sustituye | `make revisar-obras-externas` |

> Los tres archivos de `PD-04` **todavía no existen en ningún disco**: la
> política de red del entorno donde se construyó el conector bloquea las tres
> APIs, así que nunca se ha corrido de verdad. El mecanismo está probado con
> `--test`; la cola se llena la primera vez que `make obras-externas` corra
> desde una red que las alcance.

### Scopus Author Search

| Archivo | Qué es | Se genera con |
|---|---|---|
| `scopus_author_search_multiples_id.csv` | Nombres con más de un Scopus Author ID que el detector automático no ve | `src/enrich/scopus_author_search.py` |
| `scopus_author_search_orcid.csv` | Contraste del ORCID que Scopus declara en el perfil del autor | `src/enrich/scopus_author_search.py` |
| `scopus_author_search_decisiones.csv` | Veredicto humano sobre esa cola | exportación humana |
| `scopus_author_search_listado.html` | Listado de casos para revisar | sesión puntual |

`.respaldos/` guarda la copia del CSV de decisiones anterior a cada aplicación
de `apply_*.py`. Es una red de seguridad local, no un registro.

## Cómo revisar la identidad de autor

```bash
make revision                       # regenera internal/revision_identidad.html
```

Ábralo en el navegador. Reúne todos los casos vivos —variantes de nombre,
nombres con varios Scopus ID, firmas que comparten ORCID, conflictos y
desacuerdos de ORCID, candidatos por afiliación, por repositorio institucional
y por autoarchivo— y para cada uno muestra publicaciones, años, unidades,
identificadores y tres señales cruzadas que ningún archivo tenía por separado:

- **si dos firmas aparecen en la misma publicación, son personas distintas**:
  nadie firma dos veces el mismo artículo. Es el descarte más limpio que
  existe, y el propio comando imprime a cuántos pares aplica hoy —dato que por
  sí solo no prueba identidad, pero elimina la vía rápida de descarte;
- coautores en común;
- solapamiento de años y de unidad académica.

El recuento de casos, cuáles quedan pendientes y en qué cola están los imprime
`make revision` en cada corrida, y `internal/pendientes_consolidacion.md` los
lista uno por uno. Aquí no se fijan esas cifras a propósito: cambian con cada
decisión que se toma, y un número escrito a mano en este archivo llevaría
semanas siendo falso antes de que alguien lo notara.

Las decisiones se guardan en el navegador mientras trabaja y se exportan a
`identity_decisions.csv`. **La herramienta no decide nada ni propone respuesta
por defecto**: sólo reúne la evidencia.

## Regla de uso

Ninguna entrada de estas colas se resuelve automáticamente. El campo
`resolucion` indica el tratamiento:

- `PENDIENTE_REVISION_HUMANA` — requiere decisión de una persona.
- `NO_RESOLVER_AUTOMATICAMENTE` — prohibido el colapso o la fusión por
  heurística.
- `DECLARAR_NO_RESOLVER` — se publica como ambigüedad declarada.
- `REVISAR_NORMALIZACION_DE_NOMBRE` — revisar la regla, no el dato.

Las colas de producción fuera de Scopus (`PD-02`, `PD-04`) usan su propio
vocabulario, documentado en `docs/METODOLOGIA_FUERA_DE_SCOPUS.md`: sólo
`CONFIRMADO_PRODUCCION_UFT` se cuenta, y los descartes se conservan en vez de
borrarse porque distinguir un homónimo de una versión repetida de la misma obra
son dos diagnósticos con soluciones distintas.

## Los candidatos por afiliación no son asignaciones

`orcid_candidatos_afiliacion.csv` sale de preguntarle a ORCID quién declara la
universidad, y cruzar esos nombres con las firmas que aún no tienen ORCID. A
diferencia de las otras dos vías, **no hay ninguna publicación compartida que
ancle la coincidencia**: sólo el nombre y la institución. Dos personas
apellidadas Díaz con inicial F. en la misma universidad son indistinguibles por
este método.

Por eso `src/enrich/orcid_afiliacion.py` no escribe nunca en
`data/enriched/authors_orcid.csv` y nada de esto llega al sitio. Cada fila trae
`titulares_que_coinciden_con_la_firma` y `firmas_que_coinciden_con_el_titular`
para que quien revise vea de un vistazo si el caso es un 1-a-1 o un 1-a-3.

La misma advertencia vale para la vía por afiliación de `PD-04`: recupera obras
por la cadena institucional declarada en el registro, que es matching por cadena
suelta (`I-05`). No atribuye nada — propone un candidato que una persona
confirma, y la herramienta lo advierte en la tarjeta de cada caso.

Lo que puede publicarse es el **recuento agregado** de ambigüedades y su
explicación metodológica, no el detalle nominal de la cola.
