# Fuentes y plataformas: lo implementado y lo propuesto

**Actualizado:** 2026-08-19 · **Alcance:** de dónde sale cada dato hoy, y qué
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
| Crossref | REST, `api.crossref.org/works/{doi}` | Ninguna (`mailto` para el *polite pool*) | `src/enrich/orcid_crossref.py` | `data/enriched/authors_orcid.csv` |
| ORCID | Public API v3.0, `pub.orcid.org` | Token `client_credentials`, alcance `/read-public`, gratuito | `orcid_api.py`, `orcid_expand.py`, `orcid_afiliacion.py` | `data/enriched/orcid_verificacion.csv`, `internal/orcid_*.csv` |

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
  en la capa publicable**: deja 20 candidatos en `internal/` para revisión
  humana. 18 de ellos ya se confirmaron uno a uno.

### 2.3 Lo que aportó cada vía, medido

| Vía | Asignaciones vigentes |
|---|---|
| Crossref | 174 |
| Registro de ORCID (`doi-self`) | 48 |
| Revisión humana sobre candidatos por afiliación | 18 |
| **Total** | **240 formas de firma · 216 de 556 entidades publicadas** |

El detalle metodológico y el argumento de por qué el 100 % no es alcanzable
están en `docs/ORCID_COVERAGE.md`.

---

## 3. Propuestas de nuevas integraciones

Ordenadas por lo que desbloquean frente a lo que cuestan. **Ninguna está
probada desde este repositorio.** La columna «Hay que confirmar» no es una
formalidad: es lo que separa una propuesta de una promesa.

### 3.1 OpenAlex — la de mayor relación entre lo que aporta y lo que cuesta

- **Qué preguntaría:** por DOI, los autores con su ORCID, su institución
  desambiguada (con identificador ROR), el estado de acceso abierto y las citas
  contadas sobre un grafo abierto.
- **Qué desbloquearía:**
  - una **segunda fuente independiente de ORCID**, que es justo lo que hoy
    falta: hoy 43 asignaciones descansan sólo en lo que declara el titular;
  - un **contraste externo del recuento de citas**, que hoy sólo tiene a Scopus
    y SciVal, que no son independientes entre sí;
  - la desambiguación institucional por ROR, que permitiría cerrar el
    `ror_id: null` declarado en `config/institution.yml`.
- **Hay que confirmar:** política de uso del *polite pool*, límites de consulta,
  y —lo importante— si su desambiguación de autor es lo bastante buena para el
  tamaño de este corpus o si añadiría ruido que habría que encolar.
- **Riesgo metodológico:** su cobertura NO es la de Scopus. Mezclar recuentos de
  las dos sin declararlo produciría cifras que no se pueden reconciliar. Se
  integraría como **fuente de contraste**, con su propio denominador declarado
  (`D-16`), nunca fusionada con la principal.

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

- **Financiadores** (`funder`): `PROJECT_SPEC` no incluye financiamiento, pero
  el export de Scopus sí trae el campo y hoy no se explota.
- **Licencias y acceso abierto**: contrastaría el `open_access` de SciVal contra
  una fuente distinta.
- **Referencias**: habilitaría análisis de citación interna que hoy no existe.
- **Hay que confirmar:** nada técnico; sí una decisión de alcance, porque cada
  uno de estos añade indicadores nuevos al catálogo y eso es una decisión, no
  una consecuencia.

### 3.5 Unpaywall — acceso abierto verificado

- **Qué preguntaría:** por DOI, si existe una versión de acceso abierto y de qué
  tipo.
- **Qué desbloquearía:** hoy `open_access` viene de SciVal sin contraste. Es un
  indicador que se publica y que nadie ha verificado contra una segunda fuente.
- **Hay que confirmar:** condiciones de uso y si exige `mailto` como Crossref.

### 3.6 SciELO — la brecha de cobertura que este proyecto declara

- **Qué preguntaría:** producción de la institución indexada en SciELO y no en
  Scopus.
- **Qué desbloquearía:** es la propuesta con más valor **metodológico** de la
  lista. `docs/LIMITATIONS.md` declara que el corpus describe producción
  indexada en Scopus y que la cobertura de esa base no es uniforme entre
  disciplinas: castiga a humanidades, ciencias sociales y a la publicación en
  español. SciELO es exactamente donde está esa producción. Medir el tamaño de
  la brecha convertiría una advertencia cualitativa en una cifra.
- **Hay que confirmar (y es sustancial):** qué interfaz ofrece hoy SciELO para
  consulta programática y con qué estabilidad. Hay al menos una vía OAI-PMH,
  pero **no está verificada desde este repositorio** y no debe darse por hecha.
- **Riesgo metodológico:** dos corpus con criterios de indexación distintos no
  se suman. Entraría como **corpus paralelo declarado**, con su propia ficha en
  `config/sources.yml` y sus propios denominadores; jamás agregado al universo
  principal sin decisión explícita.

### 3.7 API de Scopus (Elsevier) — sustituir el export manual

- **Qué preguntaría:** lo mismo que hoy se exporta a mano, pero con fecha de
  corte declarada por la propia consulta.
- **Qué desbloquearía:** `V2-05` y la ambigüedad `A-05` —el export de Scopus no
  declara fecha de corte— dejarían de existir. La actualización pasaría de ser
  un procedimiento manual a un objetivo del `Makefile`.
- **Hay que confirmar (bloqueante):** clave de API institucional, si la
  suscripción de la universidad la habilita, si exige consulta desde IP
  institucional o *token* de institución, y qué límites de consulta impone. Nada
  de esto está confirmado hoy.
- **Restricción legal declarada:** el alcance de publicación de métricas de
  Elsevier sigue **sin verificación jurídica** (`V2_BACKLOG.md` §4). Recuperar
  más dato por API no cambia esa restricción; la hace más urgente.

### 3.8 API de SciVal (Elsevier) — cerrar `X-01`

- **Qué preguntaría:** métricas normalizadas con los parámetros que el export
  no permite fijar, en particular **autocitas**.
- **Qué desbloquearía:** `X-01` (tasa de autocitación) está bloqueado hoy porque
  el export no las trae (`V2-06`). También permitiría documentar la semántica
  del percentil de citación, que hoy está determinada **empíricamente** y no
  documentalmente (`T-13`).
- **Hay que confirmar (bloqueante):** las mismas credenciales que 3.7, y además
  que la suscripción incluya acceso programático a SciVal, que suele ser un
  producto aparte.

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
