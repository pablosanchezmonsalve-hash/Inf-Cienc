# Fuentes y plataformas: lo implementado y lo propuesto

**Actualizado:** 2026-08-26 · **Alcance:** de dónde sale cada dato hoy, y qué
plataformas podrían aportar lo que hoy falta.

Este documento responde a dos preguntas que se confunden con facilidad:

1. ¿Qué plataformas consulta hoy la plataforma, y qué aporta cada una?
2. ¿Qué otras podrían integrarse, con qué requisitos y para desbloquear qué?

La segunda es una lista de **propuestas**. Ninguna de ellas se ha probado desde
este repositorio. `CLAUDE.md` prohíbe suponer disponibilidad de APIs,
credenciales o endpoints no confirmados, así que cada propuesta declara qué
tendría que confirmarse antes de escribir una línea de código.

---

## 1. Una distinción que hay que hacer primero

**Scopus y SciVal no se consultan por API en este proyecto.** Se leen de dos
archivos exportados a mano desde la interfaz web, versionados en `data/raw/` y
declarados en `config/sources.yml`. Llamarlos «integración con Scopus» sería
falso, y tiene consecuencias prácticas: no hay actualización automática, la
fecha de corte es la del export, y reproducir la carga exige volver a exportar
con los mismos filtros (`docs/UPDATING.md`).

Las dos plataformas que sí se consultan por API —Crossref y ORCID— entraron
por una carencia concreta: **ni Scopus ni SciVal entregan ORCID** en sus
exports, y sin identificador persistente no hay identidad de autor estable.

---

## 2. Lo implementado

| Plataforma | Acceso | Autenticación | Script | Salida |
|---|---|---|---|---|
| Scopus | Export CSV manual | — | `src/audit/common.py` (lectura) | `data/interim/` |
| SciVal | Export XLSX manual | — | `src/audit/common.py` (lectura) | `data/interim/` |
| Crossref | REST, `api.crossref.org/works/{doi}` | Ninguna (`mailto` para el *polite pool*) | `src/enrich/orcid_crossref.py`, `src/enrich/openalex_cobertura_crossref.py`, `src/enrich/crossref_financiamiento.py` (implementado, sin ejecutar — §3.4) | `data/enriched/authors_orcid.csv`, `internal/openalex_cobertura_crossref.csv`, `data/enriched/crossref_financiamiento.csv` |
| ORCID | Public API v3.0, `pub.orcid.org` | Token `client_credentials`, alcance `/read-public`, gratuito | `orcid_api.py`, `orcid_expand.py`, `orcid_afiliacion.py` | `data/enriched/orcid_verificacion.csv`, `internal/orcid_*.csv` |
| DataCite | REST, `api.datacite.org/dois/{doi}` | Ninguna | `src/enrich/datacite.py` | `data/enriched/authors_orcid.csv`, `internal/datacite_log.csv` |
| Europe PMC | REST, `ebi.ac.uk/europepmc/webservices/rest/search` | Ninguna | `src/enrich/europepmc.py` | `data/enriched/authors_orcid.csv`, `internal/europepmc_log.csv` |
| Zenodo | REST, `zenodo.org/api/records` | Ninguna | `src/enrich/zenodo.py` | `data/enriched/authors_orcid.csv`, `internal/zenodo_log.csv` |

### 2.1 ter DataCite, Europe PMC y Zenodo — fuentes de datos no tradicionales

Tres APIs públicas sin autenticación que aportan **outputs no tradicionales**
que ni Scopus ni OpenAlex indexan bien: `src/enrich/datacite.py` (datasets,
software), `src/enrich/europepmc.py` (acceso abierto biomédico) y
`src/enrich/zenodo.py` (preservación CERN, parte de OpenAIRE).

- **Añaden ORCID donde no había**, con el mismo emparejamiento por apellido e
  inicial que `orcid_crossref.py` (que se importa, no se reescribe — `D-08`).
- **Son fuentes independientes**: a diferencia de OpenAlex, no ingieren
  Crossref, así que una coincidencia con una asignación vigente cuenta como
  confirmación, no como comprobación circular.
- **Escriben** asignaciones nuevas en `data/enriched/authors_orcid.csv`
  (fusionando con lo previo) y dejan traza en `internal/`.
- **Caché en disco y pausa** entre consultas, igual que los demás conectores.

Desde el 2026-09-03 estas tres fuentes responden además una segunda pregunta,
en dirección contraria: no "¿qué ORCID tienen los autores de este DOI?" sino
"¿qué obras tienen estas personas que el universo no tiene?". Ese es el
conector de `PD-04` (§2.10) — otro endpoint, otra salida, misma fuente.

> GitHub (`src/enrich/github_orcid.py`) queda implementado pero **inactivo por
> defecto**: su REST API no permite buscar por ORCID en el bio de un perfil sin
> autenticación. Requiere un token en
> `enriquecimiento_externo.github.token` de `config/matching_rules.yml` y, aun
> así, la búsqueda amplia exige GraphQL. Se documenta pero no se ejecuta.

### 2.1 Crossref — de dónde salió el primer ORCID

`src/enrich/orcid_crossref.py` pregunta por cada DOI del universo qué ORCID
declaró el editor al depositar la publicación, y empareja esos titulares con
las firmas UFT detectadas en esa misma publicación por apellido e inicial.

- **Qué la hace viable:** el 97,7 % del corpus tiene DOI.
- **Qué NO resuelve:** sólo ve el ORCID que alguien escribió en el formulario
  de envío. Si el editor no lo transmitió, Crossref no lo tiene.
- **Límite metodológico declarado:** emparejar por apellido e inicial es una
  hipótesis, no un hecho. Cada asignación viaja con su nivel de confianza y con
  el número de publicaciones que la respaldan; los conflictos se encolan sin
  resolver (`D-08`).
- **Cortesía y caché:** una pausa de 0,12 s entre consultas y caché en disco,
  de modo que reejecutar no vuelve a golpear la API.
- **Aportó:** 174 asignaciones.

### 2.1 bis Crossref — evidencia para la brecha de cobertura OpenAlex (V2-26 bis)

`src/enrich/openalex_cobertura_crossref.py` pregunta al mismo endpoint algo
distinto: no busca un ORCID, trae la afiliación que la propia publicación
declaró al depositar, para los 414 casos de `internal/openalex_cobertura.csv`
(V2-26) donde OpenAlex atribuye la obra a la UFT y el universo no la tiene.

- **Qué resuelve:** hasta esta corrida, la única evidencia para decidir esos
  414 casos era la propia desambiguación de OpenAlex — una fuente opinando
  sobre sí misma. Crossref aporta una lectura independiente.
- **Qué NO hace:** no decide nada (`D-08`), no toca `openalex_cobertura.csv`
  ni su columna `resolucion`, y no promueve ningún caso al universo publicado
  (`D-206`). Empareja por apellido contra los autores que Crossref lista; no
  siempre encuentra una coincidencia única.
- **Corrida el 2026-08-27** contra los 385 casos con DOI: 0 errores de red,
  59 con afiliación recuperada.
- **Salida:** `internal/openalex_cobertura_crossref.csv` — capa interna, no
  entra en `dist/`.

### 2.2 ORCID — tres preguntas distintas al mismo registro

El registro público de ORCID se consulta con tres conectores que **no hacen lo
mismo**, y confundirlos sería confundir tres calidades de evidencia:

| Script | Pregunta que hace | Qué produce |
|---|---|---|
| `orcid_api.py` | ¿el titular de este ORCID declara ESTA publicación entre sus obras? | Veredicto por asignación |
| `orcid_expand.py` | ¿quién declara este DOI entre sus obras? (`doi-self`) | Asignaciones que Crossref no vio |
| `orcid_afiliacion.py` | ¿quién declara esta institución en su registro? (`affiliation-org-name`) | **Candidatos**, nunca asignaciones |

- **`orcid_api.py` — verificación.** Convierte una hipótesis en evidencia o en
  sospecha. De 222 asignaciones comprobadas: 201 confirmadas, 17 sin obras con
  DOI contra las que contrastar, 4 sin ninguna coincidencia. No reescribe
  `authors_orcid.csv`: emite un archivo aparte, para no borrar de dónde vino
  cada dato.
- **`orcid_expand.py` — ampliación.** Alcanza a quien incorporó la obra a su
  registro por vías que Crossref no refleja. Aportó 48 asignaciones. Su
  ambigüedad es peor detectable que la de Crossref —sólo devuelve a quien tiene
  registro— y por eso sus asignaciones se cruzan además contra las de Crossref.
- **`orcid_afiliacion.py` — candidatos.** Encuentra a quien declara la
  institución sin que haya publicación compartida que lo ancle. Dos homónimos de
  la misma universidad son indistinguibles por este método, así que **no escribe
  en la capa publicable**: deja candidatos en `internal/` para revisión humana
  (hoy, 20 pendientes). Las confirmaciones acumuladas por esta vía —25 a la
  fecha— se escriben en `authors_orcid.csv`, no en el archivo de candidatos: el
  conector lo regenera en cada corrida, así que no es el lugar donde persiste
  qué ya se revisó.

### 2.3 Lo que aportó cada vía, medido

| Vía | Asignaciones vigentes |
|---|---|
| Crossref | 174 |
| Registro de ORCID (`doi-self`) | 48 |
| OpenAlex (`doi-self`, vía autorías) | 79 |
| Revisión humana sobre candidatos por afiliación | 25 |
| Revisión humana (búsqueda manual en el registro) | 1 |
| **Total** | **327 formas de firma · 274 de 538 entidades publicadas** |

El detalle metodológico y el argumento de por qué el 100 % no es alcanzable
están en `docs/ORCID_COVERAGE.md`.

### 2.4 Repositorio institucional UFT (DSpace) — **entregado y ejecutado el 2026-09-01**

No es una API: es un export de metadatos DSpace (`data/raw/Inventario_Repositorio_Institucional_UFT.csv`,
3.271 filas) que el responsable del proyecto entregó directamente —tesis de
pregrado/posgrado y artículos/libros/capítulos autoarchivados por sus propios
autores. `src/enrich/dspace_inventario.py` no sale a red: lee ese archivo y lo
cruza contra el corpus propio.

Dos productos, no uno:

- **Contraste** (`data/interim/dspace_verificacion.csv`) para las 322 firmas
  que ya tienen ORCID asignado: busca sus publicaciones propias en el
  inventario por DOI compartido. De 154 firmas con algo que cruzar,
  **56 confirmaciones directas** (el propio nombre, con el mismo ORCID),
  **69 confirmaciones indirectas** (el ORCID aparece en la obra, depositada
  por otro coautor), **6 contradicciones directas** (el propio nombre, con un
  ORCID DISTINTO al publicado) y 23 sin coincidencia.
- **Candidatos por nombre** (`internal/dspace_candidatos.csv`) para firmas SIN
  ningún ORCID: busca por apellido+inicial en TODO el inventario —su propia
  tesis, un artículo suyo autoarchivado—, no sólo en publicaciones ya
  compartidas. 16 firmas alcanzadas, 10 con coincidencia 1-a-1.

Ninguno de los dos sube nada a `verificado` por sí solo: alimenta
`build_review.py` con dos colas nuevas —«Repositorio institucional discrepa» y
«Candidato por repositorio institucional»— para que una persona decida
(`D-08`), igual que las demás fuentes de esta sección. La premisa de que un
autor afiliado a la UFT declara su ORCID en el repositorio institucional la
declaró el responsable del proyecto en sesión; el conector no la verifica de
forma independiente, la aplica.

### 2.5 Inventario de autoarchivo — hoja curada por biblioteca UFT — **entregado y ejecutado el 2026-09-01**

Distinta de §2.4: no es el volcado de metadatos de DSpace, es una hoja de
cálculo (`data/raw/Inventario_Repositorio_Autoarchivo.xlsx`, 808 obras,
2004–2026) que el propio equipo de biblioteca mantiene a mano al
autoarchivar cada ítem — trae DOI, ORCID de quien solicitó la subida, y
**Facultad o Escuela**, un campo que DSpace no tiene. `src/enrich/autoarchivo_uft.py`,
mismo patrón que `dspace_inventario.py`: no sale a red, no traduce nada al
vocabulario oficial, no aplica nada por su cuenta.

**ORCID** (`data/interim/autoarchivo_verificacion.csv`,
`internal/autoarchivo_candidatos.csv`): de 150 firmas con algo que cruzar,
**71 confirmaciones directas, 32 indirectas, 2 contradicciones directas**
(`Arroyo A.` — con el MISMO ORCID alternativo que ya señalaba §2.4:
evidencia cruzada de dos fuentes independientes — y `Rojas-Costa G.M.`,
que además trae dos ORCID distintos dentro de esta misma hoja) y 45 sin
coincidencia. Candidatos por nombre para firmas sin ORCID: 9 (7 uno-a-uno).

**Facultad o Escuela** (`internal/autoarchivo_unidad_candidatos.csv`): de
las 294 firmas con unidad académica «No determinada», **59 tienen un
candidato** en este inventario (73 casos, algunas firmas con más de una
escuela candidata). El valor se declara TAL CUAL lo escribió biblioteca
(«Medicina», «CIDOC», «Familia»...), sin mapear a
`config/matching_rules.yml` — esa traducción es el mismo trabajo
institucional que exigió `T-02`. Desde el 2026-09-01 SÍ es una cola de
`build_review.py` («Candidato de unidad académica por autoarchivo»), a
pedido del usuario de reunir toda revisión pendiente en un solo documento:
confirmar un caso deja constancia en `identity_decisions.csv` de que la
unidad declarada es correcta para esa persona, pero APLICARLA al pipeline
público —traducirla al vocabulario oficial y que deje de figurar «No
determinada»— sigue siendo un paso aparte, todavía sin construir.

### 2.6 Facultad de Medicina y Salud — listado propio de publicaciones — **implementado el 2026-09-01, publicado el 2026-09-02**

Distinta de §2.4 y §2.5 en naturaleza, no sólo en fuente: no es un inventario
institucional para cruzar identidad de autor, es el listado de producción
que la propia Facultad publica en su sitio
(`https://facultadmedicina.finis.cl/investigacion-y-postgrado/publicaciones/`),
vía la API REST de WordPress. `src/enrich/facultad_medicina_publicaciones.py`
lo baja, lo estructura (facultad, sección, año, título, autores, DOI) y lo
cruza por DOI contra `data/interim/publications_universe.csv`. No sale a
red durante el build normal — se ejecuta aparte, y su salida se versiona
(`data/enriched/facultad_medicina_publicaciones.json`,
`internal/facultad_medicina_cruce.csv`).

**609 registros**, 347 con DOI (284 DOIs únicos: la fuente lista
duplicados, y el conector no los colapsa — "el sitio lista duplicados;
borrarlos en el extractor ocultaría un dato de la fuente", `D-400`), **279
ya en el universo Scopus**. El resto —lo que la Facultad declara y Scopus
no indexa— NO se suma a `publications_universe.csv` ni a ningún indicador
de citas/FWCI (D-206, D-398): eso mezclaría criterios de indexación
distintos con evidencia que SciVal nunca midió.

En cambio, alimenta un **corpus paralelo declarado**: el indicador `PD-01`
("Producción declarada por las Facultades, fuera de Scopus"), calculado por
`src/build/09_produccion_declarada.py`, publicado en su propia página
(`produccion-ampliada.html`) — sólo recuentos por Facultad × año, dentro de
la ventana 2023-2025, con nota explícita de cuántos registros adicionales
quedan fuera de ventana o sin año. El mecanismo es general, no hardcodeado
a Medicina: cualquier fuente que declare `corpus_paralelo_declarado: true`
en `config/sources.yml` con un JSON del mismo esquema (documentado en el
docstring del conector) se descubre sola.

`PD-01` es Nivel D (declarado, sin verificación individual por obra) según
`docs/METODOLOGIA_FUERA_DE_SCOPUS.md`. No confundir con `PD-02` (§2.7), que
es Nivel V: cada caso pasó por revisión humana antes de contarse.

### 2.7 OpenAlex — cobertura confirmada por revisión humana, fuera de Scopus (V2-26) — **publicado el 2026-09-02**

Segunda fuente de `produccion-ampliada.html`, de otra naturaleza que §2.6:
no es una Facultad declarando su propia lista editorial, es
`src/enrich/openalex_cobertura.py` preguntándole a OpenAlex quién publica
desde la institución (por ROR, `V2-20`) y comparando contra el universo
Scopus — la brecha que §3.1 mide. Cada caso de esa brecha (414) pasa por
revisión humana caso por caso en
`internal/revision_cobertura_openalex.html`
(`src/review/apply_openalex_review.py`) antes de contarse: sólo los que
quedan `CONFIRMADO_PRODUCCION_UFT` alimentan el indicador `PD-02`
("Producción institucional confirmada por revisión de cobertura OpenAlex,
fuera de Scopus"), calculado por el mismo `09_produccion_declarada.py` que
PD-01. Los que siguen `PENDIENTE_REVISION_HUMANA` (394 hoy) NUNCA se
cuentan como producción confirmada — se publican como cifra de
transparencia, no se ocultan ni se dan por buenos.

`PD-02` no trae `facultad` (es evidencia por autor, no una declaración
editorial de una unidad), así que no entra al mecanismo de
`corpus_paralelo_declarado` de §2.6: tiene su propia sección en
`produccion-ampliada.html`, agregada sólo por año. El total combinado que
la página encabeza (`total_fuera_de_scopus`) es la unión por DOI de PD-01 y
PD-02 — no un tercer indicador con fuente propia, sino aritmética sobre los
dos de arriba: 3 DOI de Medicina (§2.6) coinciden con confirmaciones de
V2-26, y se restan una sola vez para no contar la misma obra dos veces.

Como PD-01, `PD-02` NUNCA toca `publications_universe.csv` ni ningún
indicador de citas/FWCI (D-206, D-398): "confirmado" aquí significa que un
humano concluyó que la obra es producción real UFT fuera del corpus
indexado, no que entra al corpus.

### 2.8 Autoarchivo institucional — producción por unidad declarada (PD-03) — **publicado el 2026-09-02**

Tercera fuente de `produccion-ampliada.html`, de otra naturaleza que §2.6 y
§2.7: el usuario pidió sumar "todas [las Facultades], usando el
repositorio institucional". El volcado DSpace (§2.4) no sirve para eso —su
columna `collection` es un handle opaco, sin nombre de Facultad en ningún
lado del export, verificado antes de descartarlo—, pero la hoja
AUTOARCHIVOS que biblioteca cura (§2.5,
`data/raw/Inventario_Repositorio_Autoarchivo.xlsx`) sí: 808 obras
autoarchivadas por sus propios autores (artículo, capítulo, libro,
ponencia — nunca tesis), cada una con DOI, año, título y la Facultad o
Escuela que biblioteca le asignó, fila por fila, para toda la institución
de una vez.

El obstáculo real: ese campo de Facultad/Escuela viene EN BRUTO (§2.5 ya lo
advertía). De los 35 valores distintos que trae, la mayoría no tiene una
relación escuela→Facultad validada institucionalmente hoy —
`config/matching_rules.yml` sólo confirma 5 escuelas en su `jerarquia`, más
las que su `vocabulario` (regla I-07) resuelve directo a nivel de Facultad—.
Nuevo conector `src/enrich/autoarchivo_produccion.py` reutiliza EXACTAMENTE
esas dos funciones de producción (`canonical_academic_unit()` +
`facultad_de()`, las mismas que ya usa `P-07`), más un puñado de alias
explícitos y documentados uno por uno (dos, "Educación básica"/"Educación
parvularia", tomados de `REFERENCIA_UNIDADES_AUTOARCHIVO` porque el usuario
los confirmó DIRECTAMENTE contra finis.cl — el resto de esa referencia
sigue marcada "sin verificar" y NO se usa aquí). Cada registro trae
`unidad_declarada` (siempre) y `facultad` (sólo si está validada) por
separado — nunca se fuerza la segunda a partir de la primera.

**Resultado (2026-09-02):** 808 leídos, 7 duplicados colapsados por DOI,
498 fuera del universo Scopus. De esas, 341 con Facultad validada (125 en
la ventana 2023-2025 — la cifra que entra a `PD-03`) y 157 sin Facultad
validada (57 en ventana), publicadas por unidad declarada en vez de
adivinar a qué Facultad pertenecen — nunca ocultas.

**Solapamiento real con §2.6 y §2.7, verificado antes de publicar el
total:** Medicina aparece declarada en su propio sitio (PD-01) Y
autoarchivada por sus autores (PD-03) — y algunas de las confirmaciones de
V2-26 (PD-02) también están autoarchivadas. El total combinado de
`produccion-ampliada.html` une las tres por DOI antes de sumar, exactamente
por esto.

`PD-03` es Nivel D para las filas con Facultad validada (declarado por
biblioteca, no verificado obra por obra) según
`docs/METODOLOGIA_FUERA_DE_SCOPUS.md` — mismo nivel que `PD-01`, fuente
distinta.

### 2.9 Scopus Author Search — directorio de autores por afiliación — **entregado y ejecutado el 2026-09-02**

Distinta en naturaleza de todo lo demás que este proyecto usa de Scopus:
no es un export de publicaciones (`scopus_export`, 823 filas, ventana
2023-2025), es el directorio de AUTORES que Scopus Author Search asocia a
la afiliación "Universidad Finis Terrae" — 812 perfiles (nombre, Scopus
Author ID, N° de documentos según Scopus, área temática, ORCID cuando
existe), sin ventana temporal ni filtro de año (confirmado con el usuario:
"búsqueda por afiliación", nada más). Capa interna, nunca publicable
directamente (D-08): alimenta dos colas de revisión, nunca decide.

**Por qué hacía falta, y qué no puede ver el detector automático del
proyecto.** `P-04` (`src/audit/04_author_population.py`) ya detecta
"nombre con más de un Scopus Author ID" — pero sólo cuando los dos
identificadores aparecen, DENTRO del corpus de 823 publicaciones, bajo la
misma cadena de nombre exacta. No puede ver un identificador cuyas
publicaciones caen fuera del corpus (otra ventana, otro tipo documental),
ni conectar dos identificadores que aparecen bajo grafías distintas del
mismo nombre. Scopus Author Search sí los ve, porque ya agrupó por
identificador antes de exportar.

`src/enrich/scopus_author_search.py` (nuevo) cruza los 812 perfiles contra
el corpus y contra `internal/ambiguities_authors.csv`, y produce:

- `internal/scopus_author_search_multiples_id.csv` — **8 nombres** con 2+
  Scopus Author ID. 4 ya estaban conocidos (Moya Patricia, Hartmann
  Schatloff Dan, Quezada Mauricio, Torres Keila — esta fuente los confirma
  de forma independiente). **3 son nuevos, no detectables por `P-04` antes
  de esta fuente**: "Esis Villarroel, Ivette S." (un segundo perfil con 14
  documentos y ORCID propio, invisible al detector porque ninguna de esas
  14 publicaciones está en el corpus), "Cabello, José Miguel" (mismo
  patrón), "Caffarena, Paula" (sus dos identificadores SÍ están en el
  corpus, pero uno aparece bajo "Barcenilla, Paula Caffarena" — apellidos
  en otro orden, cadena distinta). Cada candidato lleva el detalle
  necesario para revisar sin volver a buscar nada: qué dice SciVal de cada
  identificador, si aparece en el corpus y con cuántas publicaciones, y
  bajo qué otro nombre si corresponde.

  Un **8º candidato**, "Fortuny, Esteban Fortuny", lo ve un segundo
  detector (`candidatos_fragmentacion_orcid()`, agregado 2026-09-03): dos
  identificadores que no comparten nombre en NINGUNA fuente, sólo el
  mismo ORCID (el declarado por el titular para "Fortuny E." en el corpus,
  y el que Scopus Author Search asigna a su propio perfil de 3
  documentos). El primer detector agrupa por nombre exacto dentro de esta
  misma fuente y no puede ver esto.

  Revisión humana al 2026-09-03: **3 confirmados** ("Esis Villarroel,
  Ivette S.", "Fortuny, Esteban Fortuny", "Moya, Patricia" — convergencia
  de ORCID entre dos o más fuentes independientes en los tres casos; el de
  Moya revierte un veredicto `pendiente` del 2026-09-02, también reflejado
  en `internal/identity_decisions.csv`), **5 pendientes** (Cabello,
  Caffarena, Hartmann Schatloff, Quezada, Torres — sin evidencia suficiente
  todavía, o con evidencia en contra en el caso de Caffarena). Decisiones
  en `internal/scopus_author_search_decisiones.csv`, aplicadas con
  `apply_scopus_author_decisions.py`.
- `internal/scopus_author_search_orcid.csv` — contraste del ORCID que
  Scopus declara en el perfil del autor (tercera fuente independiente,
  además de Crossref y el registro público de ORCID) contra
  `data/enriched/authors_orcid.csv`. De 50 filas con ORCID: **26
  coinciden** con lo ya asignado (corroboración), **0 contradicen**, **1
  es nuevo** (firma ya reconocida como UFT, sin ORCID asignado todavía:
  "Bastías, Jaime"), **23** corresponden a firmas que Scopus asocia a la
  afiliación pero que la población UFT del proyecto no reconoce como tal
  (fuera de la ventana 2023-2025, u homonimia — no se investiga más sin
  evidencia adicional).

Ninguna de las dos salidas escribe en `data/enriched/authors_orcid.csv` ni
en ninguna ficha publicada. Un ORCID que contradijera al ya asignado se
reportaría como conflicto, igual que hace `orcid_crossref.py` — no ocurrió
en esta corrida, pero el conector está probado para ese caso (`--test`).

---

### 2.10 DataCite, Europe PMC y Zenodo — obras fuera del universo (PD-04) — **mecanismo publicado el 2026-09-03**

Cuarta fuente de `produccion-ampliada.html`. El usuario preguntó de qué forma
es posible incluir publicaciones fuera de Scopus/SciVal y, sobre la respuesta,
autorizó explícitamente avanzar con "esa cuarta fuente de nivel V".

**La pregunta que ninguna fuente del proyecto hacía.** §2.7 (`PD-02`) ya
pregunta qué le atribuye a la institución un índice bibliográfico grande que
el universo no tiene. Queda otra: **qué produjeron estas personas que ningún
índice bibliográfico indexa bien** — datasets, software, preprints, pósters,
materiales depositados. Las tres fuentes de §2.1 ter sí los ven. Hasta hoy se
les consultaba sólo **por DOI del universo**, para recuperar el ORCID de sus
autores: eso únicamente puede mirar hacia adentro. `src/enrich/obras_externas.py`
invierte la dirección.

**Cómo busca, y por qué de dos maneras.**

- **Por ORCID** (`via = orcid`): un identificador de persona. Usa sólo los
  ORCID vigentes de `data/enriched/authors_orcid.csv`, **descontando los que
  `config/orcid_revisado.yml` marca como `retiradas`** — un ORCID que una
  persona ya declaró incorrecto para esa firma no puede fundar la
  recuperación de obras suyas. Es la vía fuerte.
- **Por afiliación** (`via = afiliacion`): la cadena institucional declarada
  en el registro. Es matching por cadena suelta, que `I-05` prohíbe como base
  de una atribución — por eso aquí **no atribuye nada**: sólo propone un
  candidato que una persona confirma. Se conserva porque recupera obras de
  las 267 firmas sin ORCID, que la vía fuerte no puede ver por construcción.

Cada fila declara por cuál de las dos llegó, y la herramienta de revisión
advierte del homónimo en la tarjeta del caso, no en una nota al pie.

**Las plantillas de búsqueda están en `config/sources.yml`**, campo
`consulta_obras`, con `{orcid}` y `{institucion}` como únicos marcadores —
no en el código. Otra institución que replique la plataforma cambia
`config/institution.yml` y esas plantillas; si una API renombra su campo de
búsqueda, se corrige la configuración.

Una vía puede declarar **varias plantillas candidatas**, y Zenodo lo hace:
migró a InvenioRDM y el campo por el que se busca un ORCID cambió de nombre,
sin que se haya podido comprobar cuál sirve hoy —todas las salidas a
`zenodo.org` están bloqueadas desde este entorno—. El conector **sondea** las
candidatas al empezar, con unos pocos identificadores, fija la que responda
para el resto de la corrida e imprime cuál usó. No prueba la alternativa en
cada consulta: la mayoría de las firmas no tiene ningún depósito, y ahí
«cero resultados» es la respuesta correcta, no un síntoma. Si ninguna
responde, lo dice: con la red delante no se puede distinguir «el campo
cambió» de «no hay depósitos», y el conector no elige por su cuenta entre
las dos lecturas.

Por la misma migración, el **parseo** acepta las dos serializaciones de un
autor —la heredada (`name`/`orcid`/`affiliation`) y la de InvenioRDM
(`person_or_org.identifiers`)— y se detiene ante una tercera. Leer sólo una
habría devuelto un autor vacío por obra si la búsqueda sirviera la otra: la
cola se llenaría de filas sin autor sin que nada fallara.

**El cuarto veredicto.** Zenodo acuña un DOI por cada versión de un depósito,
además del DOI de concepto; DataCite indexa preprints cuya versión publicada
sí está en Scopus. Son DOI distintos para la misma obra, y la deduplicación
por DOI —el único mecanismo de deduplicación del proyecto— no los colapsa. La
obra SÍ es de la institución, así que "atribución errónea" perdería la
distinción. La revisión tiene por eso un veredicto propio, `version`, y su
recuento se publica: saber si la cola está llena de homónimos o de versiones
repetidas son dos diagnósticos con soluciones distintas.

**Corroboración entre las tres.** El mismo DOI en dos repositorios es una
obra corroborada dos veces, no dos obras (Regla 3 de
`docs/METODOLOGIA_FUERA_DE_SCOPUS.md`). La cola conserva las dos filas —quien
revisa necesita ver las dos— y el recuento cuenta una. La tabla "qué aportó
cada repositorio" cuenta APORTES, no obras, y la página lo dice donde se
lee, para que la diferencia no parezca un error de cuadratura.

**Reejecutar no borra revisiones.** La cola se reconstruye entera en cada
corrida, pero `resolucion` es trabajo humano, no un dato de la API: se
conserva emparejando por `(fuente, id_fuente)`.

**Estado (2026-09-03): mecanismo publicado, cifra ausente.** La política de
red del entorno de desarrollo bloquea `api.datacite.org`, `www.ebi.ac.uk` y
`zenodo.org` — 403 en el CONNECT del proxy, comprobado. El conector, la cola,
la herramienta de revisión, el aplicador, el agregado y la sección del sitio
están construidos y probados con `--test` en CI; la cola nace vacía y la
sección lo declara en la página en vez de mostrar un cero que se leería como
un resultado. **Los contratos de búsqueda de las tres APIs están tomados de
su documentación y NO verificados contra la red desde este repositorio**: el
conector comprueba la forma de cada respuesta y, si no la reconoce, guarda la
respuesta cruda y se detiene, en vez de adivinar.

Para llenarla, desde una red que alcance las tres APIs:

```
make obras-externas            # construye internal/obras_externas_cobertura.csv
make revisar-obras-externas    # genera internal/revision_obras_externas.html
# marcar caso por caso, exportar el CSV a internal/obras_externas_decisiones.csv
python3 src/review/apply_obras_externas_review.py --dry-run
python3 src/review/apply_obras_externas_review.py
python3 src/build/build_all.py
```

**Lo que no hace:** no toca `data/interim/publications_universe.csv` ni
ningún indicador de citas o FWCI. Confirmar una obra la vuelve contable como
`PD-04`, en su propia sección, con su propio denominador y sin impacto —
SciVal no mide nada de esto (`D-206`, `D-398`, Regla 5).

## 3. Propuestas de nuevas integraciones

Ordenadas por lo que desbloquean frente a lo que cuestan. **Ninguna está
probada desde este repositorio.** La columna «Hay que confirmar» no es una
formalidad: es lo que separa una propuesta de una promesa.

### 3.1 OpenAlex — **ejecutado el 2026-08-26**

`src/enrich/orcid_openalex.py`.

> **Corrección.** La versión anterior de esta sección presentaba a OpenAlex como
> «una segunda fuente independiente de ORCID». **Era falso.** OpenAlex ingiere
> Crossref entre sus fuentes: un ORCID que devuelve puede ser literalmente el
> que Crossref depositó, y que las dos coincidan no confirma nada que no
> supiéramos — es la misma evidencia contada dos veces.
>
> Importa porque este proyecto **publica** la diferencia entre «verificado» —dos
> fuentes independientes— y «declarado por el titular» —una sola— en cada ficha
> de autor. Contar una coincidencia con OpenAlex como verificación habría
> inflado el recuento de comprobaciones independientes con comprobaciones
> circulares. El conector las cuenta aparte y **nunca sube una asignación a
> «verificado»**.

- **Qué aporta, sin discusión:**
  1. **ORCID donde no había ninguno.** 349 formas de firma no tienen
     identificador por ninguna de las tres vías actuales; cualquiera que
     OpenAlex traiga es cobertura nueva, venga de donde venga.
  2. **Contraste de la detección institucional por ROR.** Las publicaciones que
     este proyecto atribuye a la institución y OpenAlex no, son un hallazgo: o
     su desambiguación falló, o el patrón blando detectó de más.
- **Lo que este conector no alcanza** —la producción que OpenAlex atribuye a la
  institución y este proyecto no— lo cubre `src/enrich/openalex_cobertura.py`
  (`V2-26`), que pregunta **por institución** (`filter=institutions.ror:…`) y
  compara contra el universo. Es la primera vez que la brecha de cobertura que
  `LIMITATIONS.md` advierte en prosa se puede **medir**. Su resultado es una cola
  de revisión en `internal/`, nunca un ajuste del corpus: Scopus y OpenAlex
  indexan con criterios distintos y sumarlos no significa nada (`D-206`). Desde
  el 2026-09-02, los casos que esa revisión CONFIRMA (no los pendientes) se
  publican como recuento en `PD-02` (§2.7) — nunca al universo, pero ya no sólo
  en la capa interna.
- **Dependencia declarada:** el contraste necesita el ROR de la institución
  (`V2-20`). Sin él esa mitad no corre, y se dice; no se sustituye por una
  comparación de nombres, que la regla `I-05` prohíbe.
- **Contraste de citas:** no se implementa aquí. Añadiría indicadores, y eso es
  una decisión con su propio denominador (`D-16`), no una consecuencia.
- **Riesgo metodológico que sigue vigente:** su cobertura NO es la de Scopus.
  Mezclar recuentos produciría cifras que nadie puede reconciliar. Entra como
  fuente de contraste, nunca fusionada (`D-206`).
- **Resultado de la consulta (2026-08-26):** 804 de 823 publicaciones tienen
  DOI y se consultaron. **80 asignaciones de ORCID nuevas** (cobertura de
  242 → 322 formas de firma). **68 publicaciones** que este proyecto atribuye
  a la UFT y OpenAlex no —cola en `internal/openalex_deteccion.csv`, sin
  resolver automáticamente—. **6 desacuerdos** de ORCID encolados en
  `internal/openalex_desacuerdos.csv` (`D-08`). `openalex_cobertura.py`
  (`V2-26`) corrió también: OpenAlex atribuye 1.112 obras a la UFT por ROR,
  698 ya en el universo, **414 no** (385 con DOI ausente, 29 sin DOI en
  OpenAlex) — cola en `internal/openalex_cobertura.csv`, nunca un ajuste
  del corpus.
- **Hallazgo de entorno, no de datos:** ambos scripts revientan al final en
  Windows por un `UnicodeEncodeError` — la consola usa `cp1252`, que no
  tiene «→» ni «─». El trabajo (escritura de archivos) ya había terminado
  cuando revienta el `print`, así que no perdía datos, pero sí ensuciaba la
  salida. Corregido reconfigurando `stdout` a UTF-8 al importar, sólo en
  Windows (`sys.platform == "win32"`).

### 3.2 ROR — **implementado el 2026-08-19; falta ejecutar la consulta**

`src/enrich/ror_institucion.py`. Es la única entrada de esta sección que ya
tiene código, y por eso conviene leer bien qué significa «falta ejecutar».

- **Qué pregunta:** el identificador ROR de la institución, su ISNI, y los
  nombres bajo los que está registrada.
- **Qué cierra:** los dos placeholders de `config/institution.yml` —`ror_id` e
  `isni`, ambos `null` con el motivo escrito al lado— y, sobre todo, contrasta
  el patrón de detección institucional de `config/matching_rules.yml` contra un
  vocabulario público, que es una de las reglas de `<author_master_rule>`.
- **Lo que el contraste puede encontrar:** una forma registrada que el patrón
  `\bfinis[\s\-]+terrae\b` no reconoce —un acrónimo, por ejemplo— y que, si
  llegara sola en una cadena de afiliación, no se detectaría. El conector lo
  **declara**; ampliar el patrón es una decisión, porque la regla `I-05` prohíbe
  el matching por subcadena y hay 16 falsos positivos verificados.
- **Lo que NO hace:** no escribe `config/institution.yml` —es el contrato de
  replicabilidad, y un identificador de organización es una afirmación sobre
  ella—, no elige entre candidatos si más de una organización coincide, y no
  toca el patrón de detección.

**El contrato de la API no está verificado desde este repositorio.** El entorno
donde se escribió el conector no alcanza `api.ror.org`: la política de red del
contenedor deniega la conexión. En consecuencia el conector admite las dos
formas de respuesta conocidas —`v2` con `names[]`, `v1` con `name`/`aliases`/
`acronyms`— y, si no encaja ninguna, guarda la respuesta cruda y se detiene
diciéndolo, en vez de adivinar. La lógica de extracción y de contraste sí está
verificada: 12 casos en `--test`, que corre también en CI.

```
python3 src/enrich/ror_institucion.py --test     lógica, sin red
python3 src/enrich/ror_institucion.py            la consulta
py src\enrich\ror_institucion.py                lo mismo, en Windows
```

### 3.3 ORCID — ampliar lo ya implementado

No es una integración nueva: es usar más del conector que ya existe.

- **Empleos y educación del titular** (`/employments`): hoy la afiliación se usa
  para generar candidatos, pero no se explota la **fecha** del empleo declarado.
  Un titular que declara la institución en un período que no solapa con las
  publicaciones atribuidas es un candidato más débil, y hoy se le trata igual
  que a uno que sí solapa.
- **Hay que confirmar:** nada. Las credenciales ya están documentadas en
  `docs/ORCID_API_GUIDE.md` y el conector ya las usa.

### 3.4 Crossref — ampliar lo ya implementado

- **Financiadores** (`funder`) — **implementado y probado el 2026-09-02;
  falta ejecutar la consulta.** `PROJECT_SPEC` no incluye financiamiento,
  pero el export de Scopus sí trae el campo (`Funding Details`/`Funding
  Texts`, 306 de 818 filas, 37,4 %) y hasta ahora ningún paso del pipeline
  lo extraía —no llega a `publications_universe.csv`, verificado antes de
  escribir código—. Es, literalmente, la "fuente complementaria de
  financiamiento" que `config/indicators.yml` -> `X-03` declara que falta
  para poder evaluar si ese indicador cruza el umbral de cobertura que hoy
  lo mantiene sin publicar. Nuevo conector
  `src/enrich/crossref_financiamiento.py`: extrae por fin el campo de
  Scopus, y consulta Crossref por DOI para traer el `funder` que el editor
  registró ahí directamente (con el identificador del Crossref Funder
  Registry cuando existe) — una fuente distinta, no una segunda copia del
  mismo dato. Reporta las dos cadenas de financiador una al lado de la
  otra, sin fusionarlas (normalizar nombres de financiador entre fuentes es
  el mismo trabajo de vocabulario institucional que
  `unidad_academica.vocabulario`, no algo que este conector decida por su
  cuenta). Probado con `--test` (11 casos); la consulta real no pudo
  correr desde este entorno — `api.crossref.org` devuelve `CONNECT tunnel
  failed, response 403` (política del gateway de red, confirmado con
  `curl` y con el estado del proxy, no un error transitorio). Ver
  `config/sources.yml` -> `crossref_financiamiento_api`
  (`ejecutada: false`).
- **Licencias y acceso abierto**: contrastaría el `open_access` de SciVal contra
  una fuente distinta. Nota: Crossref no tiene un campo limpio de "acceso
  abierto" (sólo URLs de licencia, que exigen heurística para clasificar);
  §3.5 (Unpaywall) es la herramienta que este proyecto ya identificó para
  esa pregunta específica — no se duplicó ese trabajo aquí.
- **Referencias**: habilitaría análisis de citación interna que hoy no existe.
  Es la más grande de las tres en alcance (necesitaría una estructura de
  grafo nueva, comparable a la de C-05) — sin empezar.
- **Hay que confirmar:** nada técnico para financiadores (ya implementado);
  para las otras dos, publicarlas sigue siendo una decisión de alcance,
  porque cada una añade un indicador nuevo al catálogo.

### 3.5 Unpaywall — acceso abierto verificado

- **Qué preguntaría:** por DOI, si existe una versión de acceso abierto y de qué
  tipo.
- **Qué desbloquearía:** hoy `open_access` viene de SciVal sin contraste. Es un
  indicador que se publica y que nadie ha verificado contra una segunda fuente.
- **Hay que confirmar:** condiciones de uso y si exige `mailto` como Crossref.

### 3.6 SciELO — investigado el 2026-08-26 (V2-21); la interfaz real no admite consulta por institución

- **Qué preguntaría:** producción de la institución indexada en SciELO y no en
  Scopus.
- **Qué desbloquearía:** es la propuesta con más valor **metodológico** de la
  lista. `docs/LIMITATIONS.md` declara que el corpus describe producción
  indexada en Scopus y que la cobertura de esa base no es uniforme entre
  disciplinas: castiga a humanidades, ciencias sociales y a la publicación en
  español. SciELO es exactamente donde está esa producción. Medir el tamaño de
  la brecha convertiría una advertencia cualitativa en una cifra.

**Corrección sobre la versión anterior de esta sección.** Decía que había «al
menos una vía OAI-PMH», sin verificar. Es la interfaz equivocada: SciELO
publica una **API REST propia**, ArticleMeta
(`docs.scielo.org`/`scielo.readthedocs.io`, código en
[`github.com/scieloorg/articles_meta`](https://github.com/scieloorg/articles_meta)),
sin autenticación, base `http://articlemeta.scielo.org/api/v1/`. Confirmado
leyendo el código y la documentación fuente en GitHub — `scielo.readthedocs.io`
y `articlemeta.scielo.org` mismos están bloqueados por la política de red de
este entorno, igual que `api.ror.org` en `V2-20`.

- **La API existe, pero no busca por institución.** Los endpoints
  documentados (`/article/`, `/article/identifiers/`, y sus equivalentes para
  `collection`/`journal`/`issue`) sólo filtran por **ISSN de revista**,
  **colección** (código de tres letras por país/red) y **rango de fechas**
  (`from`/`until`, paginado con `limit`/`offset`, máximo 1000 por página). No
  existe un parámetro equivalente al `filter=institutions.ror:…` que hace
  posible el contraste con OpenAlex (`§3.1`). SciELO indexa por **revista**,
  no por afiliación de autor.
- **El dato SÍ está, pero sólo por artículo individual.** El endpoint de
  artículo (`GET /api/v1/article/?code=<PID>`) devuelve, por cada autor, su
  afiliación completa (institución, ciudad, país; campo `v70` del formato
  legado, expuesto por la librería
  [`xylose`](https://github.com/scieloorg/xylose) como `affiliations` /
  `normalized_affiliations`) — la misma clase de dato que
  `deteccion_institucional.metodo_blando` ya sabe reconocer. Pero **no hay
  forma de pedir "los artículos cuya afiliación contenga Finis Terrae"**: hay
  que enumerar identificadores por colección y rango de fechas, y **volver a
  pedir cada artículo uno por uno** para leer su afiliación. Es un patrón de
  cosecha de dos pasos, más caro que el de OpenAlex (que resuelve la
  institución en una sola consulta) y del mismo orden que construir el propio
  `metodo_blando` sobre un export ajeno.
- **Sin confirmar, y no es menor:** el código de colección de Chile. Los
  ejemplos públicos que aparecieron en la búsqueda usan `scl` (que en la
  práctica documentada de SciELO corresponde a la colección original/Brasil,
  no a un código ISO 3166-1), así que **no se puede asumir "chl" ni ningún
  otro candidato sin consultar `GET /api/v1/collection/identifiers/`
  directamente** — bloqueado desde aquí, requiere ejecutarse desde una máquina
  con salida a `articlemeta.scielo.org`, igual que `V2-20` con `api.ror.org`.
  Tampoco está resuelto si limitarse a la colección de Chile bastaría: un
  autor UFT puede publicar en una revista alojada en otra colección (Brasil,
  España, red regional), y la API filtra por colección de la **revista**, no
  por afiliación del autor — el propio filtro que faltaría.
- **Riesgo metodológico:** dos corpus con criterios de indexación distintos no
  se suman. Entraría como **corpus paralelo declarado**, con su propia ficha en
  `config/sources.yml` y sus propios denominadores; jamás agregado al universo
  principal sin decisión explícita (mismo principio que `D-206` ya aplica a
  OpenAlex).
- **Conclusión de esta investigación:** la interfaz existe, es estable (API
  versionada, sin autenticación) y el dato de afiliación está disponible por
  artículo — pero construir el conector es más trabajo que `V2-19`/`V2-26`
  (OpenAlex), no menos: sin filtro de institución, cosechar la producción
  potencialmente relevante exige primero decidir qué colección(es) barrer y
  luego una llamada HTTP por artículo candidato. No se escribió código: es
  una decisión de alcance (cuántas colecciones, qué ventana de fechas) que le
  corresponde a quien la vaya a ejecutar, no a esta investigación.

### 3.7 API de Scopus (Elsevier) — **implementado el 2026-08-25; falta ejecutar la consulta**

`src/enrich/scopus_api.py` (T-06).

- **Qué pregunta:** la misma cadena que hoy se exporta a mano —`AF-ID(...) AND
  PUBYEAR > ... AND PUBYEAR < ...`, tomada de `config/institution.yml`—, pero
  capturando el instante exacto de ejecución en vez de depender de que alguien
  transcriba el "Data last updated" de la interfaz web.
- **Corrección respecto de la versión anterior de esta sección:** no es cierto
  que la API "tenga" una fecha de corte que el export manual no tiene. La
  Scopus Search API no expone un campo de actualización propio, a diferencia
  de SciVal. Lo que sí resuelve es la trazabilidad: consulta literal e
  instante de ejecución quedan capturados por código, no copiados a mano — que
  es exactamente lo que `docs/UPDATING_REQUEST.md` §3 pide como mínimo
  aceptable cuando la fuente no declara su propio corte.
- **Qué NO hace:** no reemplaza `scopus_export` ni el universo publicado (823,
  `D-16`). Si el recuento que devuelve difiere del vigente, lo declara como
  hallazgo — nunca lo aplica solo. Promover un nuevo export a fuente primaria
  sigue siendo una decisión humana posterior.
- **Confirmado por el usuario, sesión 2026-08-25:** tiene API Key, sin
  restricción de IP institucional. «Todas las APIs de la suscripción
  aprobadas» resultó cierto para los productos de Scopus, pero no se
  extiende a SciVal — probado por separado, ver §3.8.
- **Sigue sin confirmar:** el límite de consulta (quota). El conector no lo
  asume: lee y reporta las cabeceras `X-RateLimit-*` de la propia respuesta en
  cada corrida, así que la primera ejecución responde la pregunta en vez de
  que el código adivine un número de la documentación general de Elsevier.
- **Restricción legal declarada:** el alcance de publicación de métricas de
  Elsevier sigue **sin verificación jurídica** (`V2_BACKLOG.md` §4). Recuperar
  más dato por API no cambia esa restricción; la hace más urgente.
- **El contrato de la API no está verificado desde este repositorio.** Igual
  que ROR y OpenAlex, este entorno probablemente no alcanza
  `api.elsevier.com`; ejecutar desde la máquina del usuario.

```
python3 src/enrich/scopus_api.py --test     lógica, sin red
python3 src/enrich/scopus_api.py            la consulta (exige SCOPUS_API_KEY)
py src\enrich\scopus_api.py                 lo mismo, en Windows
```

### 3.8 API de SciVal (Elsevier) — cerrar `X-01`, **probada y sin entitlement**

- **Qué preguntaría:** métricas normalizadas con los parámetros que el export
  no permite fijar, en particular **autocitas**.
- **Qué desbloquearía:** `X-01` (tasa de autocitación) está bloqueado hoy porque
  el export no las trae (`V2-06`). `T-13` (semántica del percentil) ya **no**
  depende de esto: se cerró por documentación pública de Elsevier, sin
  necesitar la API (`docs/METHODOLOGY.md` §7 bis, 2026-08-26).
- **Probado el 2026-08-26.** `curl` directo contra
  `GET analytics/scival/publication/metrics?metricTypes=OutputsInTopCitationPercentiles`
  con la API Key de Scopus del usuario (la misma de §3.7, que sí funciona
  para Scopus) respondió `403 ENTITLEMENTS_ERROR — Not entitled to the
  resource specified`. La distinción con un 404 importa: el gateway
  reconoció el recurso y lo rechazó por licencia, no porque la ruta no
  exista. Esto corrige la nota de §3.7 de que «todas las APIs de la
  suscripción están aprobadas» — aparentemente eso cubre los productos de
  Scopus, no SciVal, que Elsevier vende y licencia por separado.
- **Sigue bloqueante:** pedir la entitlement de SciVal API al gestor de
  cuenta Elsevier de la UFT o a la biblioteca. Si se concede, el endpoint de
  arriba es el punto de partida ya probado — no hay que redescubrirlo.
- **`partnerapi.scival.com` NO es el mismo producto** (hallazgo del usuario,
  2026-08-26). Es un gateway distinto de `api.elsevier.com`: autenticación
  por firma HMAC-SHA256 sobre cada petición, no la API Key simple de arriba.
  La documentación pública menciona credenciales «cliente/clave privada
  (modelo Pure)» — Pure es el CRIS propio de Elsevier — lo que sugiere una
  API de integración para **partners/proveedores de software** que conectan
  SciVal en nombre de una institución, no un canal de autoservicio para que
  la institución consulte sus propios datos directamente. No se encontró
  documentación de proceso de registro, elegibilidad ni contacto en la
  página consultada: **sin confirmar, no se asume que la UFT pueda o no
  usarla** (`CLAUDE.md`, no suponer disponibilidad de APIs sin confirmar).
  Antes de invertir tiempo evaluándola, la pregunta para el gestor de cuenta
  Elsevier (junto con la de la entitlement estándar, arriba) es:

  > Además de la entitlement de SciVal API en el Developer Portal, he visto
  > que existe `partnerapi.scival.com`, con autenticación por firma HMAC y
  > un modelo de credenciales que menciona "Pure". ¿Es una vía de acceso
  > disponible para la UFT como institución, o es exclusiva de proveedores
  > de software con un acuerdo de partner separado con Elsevier? Si está
  > disponible, ¿qué se necesita para solicitarla?

### 3.9 Altmetric — atención, que no es impacto

- **Qué preguntaría:** por DOI, menciones en prensa, políticas públicas, redes y
  documentos de patente.
- **Qué desbloquearía:** una dimensión que hoy no existe en el catálogo. La
  mención en un documento de política pública es un dato de valor real para un
  informe institucional.
- **Hay que confirmar:** condiciones de acceso y si el uso previsto —una web
  pública institucional— entra en ellas. **No se debe suponer que sí.**
- **Riesgo metodológico, el más alto de la lista:** una métrica de atención se
  lee como si fuera impacto, y no lo es. El `<methodological_frame>` de este
  proyecto separa explícitamente productividad, impacto y visibilidad. Si entra,
  entra en un eje propio, con un panel conceptual que diga qué NO responde
  (`docs/EJES.md`), o no entra.

### 3.10 Google Académico — **no viable, y conviene decir por qué**

- **No existe API pública.** No es que sea de pago o que exija convenio: no
  existe.
- Sus condiciones de servicio **prohíben la recuperación automatizada**, y las
  bibliotecas de terceros que la ofrecen funcionan eludiendo esa prohibición.
- Sus datos no son reproducibles ni auditables: no hay fecha de corte, ni
  criterio de indexación declarado, ni identificador estable de autor.
- **Veredicto:** incompatible con los tres primeros valores de este proyecto
  —correctitud metodológica, integridad y trazabilidad—. No se propone, y se
  deja escrito para que no se reabra sin motivo.

### 3.11 Otras, en una línea

| Plataforma | Qué aportaría | Estado |
|---|---|---|
| DataCite | DOI de datasets, tesis y software: producción que Scopus no indexa | Propuesta; no confirmada |
| OpenAIRE | Agregador europeo, útil para contrastar acceso abierto y financiación | Propuesta; no confirmada |
| Semantic Scholar | Grafo de citación abierto; segunda fuente de contraste | Propuesta; no confirmada |
| Europe PMC / PubMed | Cobertura biomédica fina, útil por el peso de Medicina en el corpus | Propuesta; no confirmada |
| Wikidata | Reconciliación de identificadores entre registros | Propuesta; no confirmada |
| Dimensions, Lens.org | Corpus alternativos amplios | Requieren acuerdo; fuera de alcance hoy |

### 3.12 EBSCO Discovery Service — cruce de cobertura, no fuente de métricas

- **Qué es, y qué NO es.** EDS es una capa de búsqueda/descubrimiento sobre
  las bases de datos que agrega EBSCO — el mismo tipo de producto que un
  portal de biblioteca usa para buscar en varias fuentes a la vez. **No es**
  una plataforma de analítica bibliométrica: no expone FWCI, percentil de
  citación normalizado por campo, ni los indicadores curados que este
  proyecto ya consume de SciVal.
- **Qué preguntaría:** publicaciones institucionales indexadas por las bases
  que agrega EBSCO, como segunda fuente de contraste de cobertura.
- **Dónde encajaría:** el mismo rol que ya cumple OpenAlex (`§3.1`) —
  contrastar qué ve una fuente que Scopus no indexó, o viceversa — **nunca
  fusionado** con el universo publicado ni con sus denominadores (`D-16`,
  `D-206`). Nunca sustituiría a Scopus/SciVal como fuente de métricas.
- **Acceso: bloqueado por entitlement, igual que SciVal.** Hace falta ser
  cliente de EDS y **contactar a un representante de ventas de EBSCO para
  habilitar el acceso a la API** — no es autogestionable desde un panel de
  administración. Autenticación por usuario/contraseña contra
  `developer.ebsco.com`, con `AuthToken` + `SessionToken` por sesión, distinta
  del esquema de API Key único que usa Elsevier.
- **Hay que confirmar antes de escribir código:** qué producto EBSCO tiene
  contratado la UFT exactamente (EDS, bases individuales, o ambos), y si esa
  suscripción incluye acceso a la API o sólo a la interfaz web.

---

## 4. Lo que cualquier conector nuevo tiene que cumplir

No son buenas prácticas genéricas: son las reglas que los cuatro conectores
existentes ya cumplen, y por las que un quinto se aceptará o no.

1. **Modo `--test` sin red.** La lógica de emparejamiento se verifica sin salir
   a internet, o no se puede verificar.
2. **Caché en disco.** Reejecutar no vuelve a golpear la API.
3. **`--limit` para probar corto.** Nadie depura contra 823 consultas.
4. **Fuente declarada por dato.** Cada asignación dice de dónde vino, y ese
   campo llega hasta la ficha pública.
5. **Las ambigüedades se encolan, no se resuelven.** `D-08`: la identidad la
   decide una persona. Un conector que fusione firmas por similitud se rechaza.
6. **Capa pública y capa interna separadas.** Lo que sirve para depurar vive en
   `internal/` y no viaja al sitio; la compuerta de
   `src/build/05_verify_public_layer.py` lo comprueba.
7. **Entrada propia en `config/sources.yml`**, con su rol y lo que aporta.
8. **Denominador propio si añade indicadores.** `D-16`: cada indicador declara
   sobre cuántas publicaciones se calcula. Un corpus nuevo no comparte
   denominador con el existente.

---

## 5. Qué NO se propone, y por qué

- **Fusionar corpus de fuentes distintas en un solo universo.** Scopus, OpenAlex
  y SciELO indexan con criterios distintos: sumarlos produce una cifra que no
  significa nada y que nadie puede reconciliar.
- **Recuperación automatizada de plataformas que la prohíben.** Ver 3.10.
- **Métricas de persona que la fuente no entrega a nivel de persona.** Ya está
  registrado para FWCI en `V2_BACKLOG.md` §6, y aplica igual a cualquier
  plataforma nueva.
