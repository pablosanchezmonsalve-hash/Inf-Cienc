# Cobertura de ORCID: hasta dónde llega y por qué no llega al 100 %

**Capa:** pública · **Pendientes que ataca:** `T-19` y la pregunta de cuánta
cobertura es alcanzable

> **Las cifras van sobre la base publicada: 542 entidades de autor**, que son las
> 589 formas de firma de la fuente con las variantes ya fusionadas por revisión
> humana (77 formas en 34 personas en la consolidación vigente; la última
> revisión de identidad del 2026-09-01 llevó la base publicada a 542). Este
> documento se escribió sobre la base anterior (556) y se actualizó el
> 2026-09-01 a la base que sirve el sitio; si vuelve a divergir, manda
> `STATE.md`, que se deriva del repositorio.

---

## 1. La pregunta

Se pidió llevar la cobertura de ORCID **al 100 % de los autores**. Este
documento responde qué se hizo para acercarse, hasta dónde se llegó y por qué el
100 % no es una meta alcanzable sino un número que sólo podría escribirse
inventando datos.

La conclusión, por delante: **el techo no lo pone el método, lo pone la
realidad de los datos**. ORCID es voluntario, y un identificador que su titular
no ha creado no puede encontrarse por ninguna vía.

---

## 2. Tres vías, tres clases de evidencia

Las tres comparten la **misma regla de emparejamiento** —apellido normalizado
más inicial, coincidencia inequívoca— que vive en `orcid_crossref.py` y que las
otras dos **importan** en vez de reimplementar.

| Vía | Qué pregunta | Qué ancla la asignación | Publica | Firmas |
|---|---|---|---|---:|
| `orcid_crossref.py` | ¿Qué ORCID transmitió el editor con este DOI? | Publicación compartida | Sí | 174 |
| `orcid_expand.py` | ¿Quién declara este DOI entre sus obras? | Publicación compartida | Sí | **+48** |
| `orcid_afiliacion.py` | ¿Quién declara esta universidad en su registro? | **Sólo el nombre** | **No** | 0 |

Las cifras de la columna son **de aquella ejecución, sobre las 589 formas de
firma sin consolidar**: así se recorrió el camino, y así queda. La ejecución
completa consultó los 804 DOI del corpus y encoló 2 desacuerdos entre Crossref y
el registro, sin resolverlos.

Después vino la revisión humana, que consolidó variantes y confirmó candidatos
por afiliación. **Sobre la base que hoy publica el sitio la cobertura es de 277
de 542 entidades (51,1 %)**, y son 322 asignaciones si se cuentan sobre las
formas de firma sin consolidar. Las dos cifras son ciertas y miden poblaciones
distintas; citar una donde corresponde la otra es el error que este proyecto
persigue.

La tercera es distinta y por eso no publica. Las dos primeras exigen que la
firma y el titular coincidan en nombre **y** aparezcan en el mismo artículo. La
tercera sólo tiene el nombre: dos personas apellidadas Díaz con inicial F. en la
misma universidad son indistinguibles por ese método, y lo seguirían siendo
aunque el registro de ORCID fuese perfecto.

Resolverlas automáticamente sería exactamente lo que prohíbe `CLAUDE.md` en
`<author_master_rule>`: «declarar ambigüedades de afiliación en vez de
resolverlas arbitrariamente». Por eso `orcid_afiliacion.py` escribe en
`internal/orcid_candidatos_afiliacion.csv` y **nunca** en `authors_orcid.csv`.
Cada candidato lleva a la vista cuántos titulares coinciden con la firma y
cuántas firmas coinciden con el titular, porque un 1-a-1 y un 1-a-3 no piden el
mismo trabajo a quien revisa.

---

## 2 bis. Por qué las 48 nuevas no dicen «verificado»

`orcid_api.py` pregunta: *¿el titular declara alguno de los DOI atribuidos a
esta firma?* Para una asignación hallada por `orcid_expand.py` la respuesta es
**sí por construcción**: se la encontró justamente por declarar ese DOI. El
veredicto no aporta ahí una segunda comprobación, repite la primera.

Las 48 salen `confirmada` en el CSV —el veredicto es correcto— pero en la ficha
se etiquetan **«declarado por el titular»**, no «verificado». Llamarlas
verificadas sugeriría que dos fuentes independientes coinciden, y la fuente es
una sola: el propio titular.

Los recuentos agregados se cuentan por esa etiqueta y no por el veredicto, para
que el número de verificaciones independientes no se infle con comprobaciones
circulares:

Sobre las **277 entidades con ORCID** de la base publicada:

| Etiqueta en la ficha | Entidades |
|---|---:|
| `verificado` — dos fuentes independientes coinciden | 155 |
| `declarado por el titular` — una sola fuente, el titular | 41 |
| `confirmado por revisión` — una persona lo comprobó en `make revision` | 17 |
| `comprobado a mano` — verificado manualmente en el registro | 22 |
| `no verificable` — sin obras con DOI que contrastar | 20 |
| `sin confirmar` — pendiente de revisión humana | 22 |

La cuarta etiqueta no existía cuando se escribió este documento: la trajo la
revisión humana de identidad, y es la única que no depende de una fuente
automática. Las dos últimas (`comprobado a mano` y `sin confirmar`) llegaron
con las listas de revisión del 2026-08-19 y se mantienen al consolidar la
identidad; `sin confirmar` queda para las que aún esperan una persona.

---

## 3. Por qué el corpus limita la cobertura

La cobertura sube con el número de publicaciones de la firma, y el corpus está
dominado por firmas de una sola publicación:

| Publicaciones de la entidad | Entidades | Con ORCID | Cobertura |
|---|---:|---:|---:|
| 1 | 375 | 146 | 38,9 % |
| 2 | 74 | 50 | 67,6 % |
| 3–4 | 43 | 35 | 81,4 % |
| 5–9 | 31 | 27 | 87,1 % |
| 10 o más | 19 | 19 | **100 %** |

**69,2 % de las entidades tienen una sola publicación.** Una entidad con una
publicación tiene exactamente una oportunidad de ser encontrada: si su ORCID no
aparece en ese único DOI, no hay una segunda vía por la que pueda aparecer.
Entre quienes tienen diez o más, la cobertura es del **100 %**: **entre los autores
con obra sostenida en la ventana, la cobertura está completa**, y lo que falta
se concentra en la cola de entidades con una sola publicación.

La forma de la distribución no cambió con la consolidación —sigue dominada por
la cola de una publicación— pero las cifras sí: fusionar variantes junta las
publicaciones de una misma persona, y por eso hay menos entidades de una sola
publicación y más de diez o más.

A esto se añade un límite estructural: **10 entidades no tienen ninguna
publicación con DOI**. Ninguna vía basada en DOI puede alcanzarlas, ni la de
Crossref ni la del registro. Para ellas sólo queda la búsqueda por afiliación,
que no publica.

---

## 4. Lo que el 100 % exigiría

Para que las 542 tuvieran ORCID harían falta las cuatro cosas a la vez:

1. que las 542 personas **tengan** un ORCID —es voluntario y no todas lo crean—;
2. que su registro sea **público** —puede configurarse como privado—;
3. que alguna fuente **conecte** ese ORCID con alguna de sus publicaciones de
   este corpus, o que la persona declare la universidad;
4. que el nombre permita distinguirla de sus homónimos.

Las cuatro se cumplen para una parte de los autores y no para el resto. Escribir
542 asignaciones exigiría inventar las que faltan, que es lo primero que prohíben
las reglas del proyecto: *«No inventes datos, columnas, métricas, relaciones ni
resultados»*.

**Y 542 entidades tampoco son 542 personas.** Una revisión humana ya fusionó
variantes (77 formas en 34 personas en la consolidación vigente), pero quedan
grupos de variantes y perfiles fragmentados sin resolver (`T-03`, `T-04`), y
cuatro firmas que probablemente no sean personas sino fragmentos de cadena de
afiliación (`E-09`). Una cobertura del «100 % de los autores» ni siquiera está
bien definida mientras no se sepa cuántos autores hay — y esa cifra sólo baja
según se resuelve la cola, nunca sube.

---

## 5. Qué es lo correcto en vez de un porcentaje

El indicador `AU-05` se publica **con su denominador y su veredicto a la vista**,
no como una cifra a maximizar. Cada ORCID del sitio dice qué evidencia lo
respalda: `verificado`, `declarado por el titular`, `confirmado por revisión`,
`no verificable` o `sin confirmar`. Una firma sin ORCID
muestra «No disponible en las fuentes actuales», declarado y no escondido
(decisión `D-07`).

Subir la cobertura es deseable; subirla a costa de la certeza, no. Un ORCID
equivocado en la ficha de una persona real es peor que un hueco declarado,
porque el hueco es visible y el error no.

---

## 6. Cómo se ejecuta

```bash
# 1. Crossref: lo que transmitió el editor
python3 src/enrich/orcid_crossref.py

# 2. Registro de ORCID: quién declara cada DOI
python3 src/enrich/orcid_expand.py

# 3. Verificación de todo lo anterior contra el registro del titular
python3 src/enrich/orcid_api.py

# 4. Candidatos por afiliación — NO publica, sólo encola para revisión
python3 src/enrich/orcid_afiliacion.py
```

Los pasos 2 y 3 corren juntos en el workflow **«Ampliar la cobertura de ORCID»**,
que no requiere instalar nada en local. Los cuatro admiten `--test`, que
comprueba la lógica sin red y sin credenciales.

Las credenciales salen del entorno o de los secretos del repositorio, nunca de
un archivo versionado.

---

## 7. Dónde se validan a mano los pendientes

Las cuatro vías automáticas se detienen donde empieza el juicio. Lo que queda
—asignaciones que el registro no puede contrastar, firmas sin identificador,
candidatos sin publicación que los ancle— se revisa en **`make revision`**, que
las presenta con la evidencia junta y con enlace al registro del titular:

| Cola | Qué pregunta |
|---|---|
| ORCID sin confirmar | El titular declara obras y ninguna coincide con las atribuidas. La ficha lo publica hoy con esa marca |
| ORCID no verificable | El titular no declara ninguna obra con DOI: no hay contra qué contrastar |
| Firma sin ORCID | Ninguna vía lo encontró, y la firma tiene obra suficiente para buscarla a mano |
| ORCID compartido · en conflicto · fuentes en desacuerdo | A quién corresponde un identificador que aparece más de una vez, o dos veces distinto |
| Candidato por afiliación | El titular declara la institución y coincide el nombre, sin publicación compartida que lo respalde |

Cada veredicto se exporta a `internal/identity_decisions.csv` y se aplica con
`src/review/apply_decisions.py`. Retirar una asignación **no borra** su fila de
`data/enriched/authors_orcid.csv`: se declara en `config/orcid_revisado.yml` y
el build la filtra, porque los conectores regeneran ese archivo y un borrado se
desharía solo en la siguiente corrida.

Un identificador tecleado a mano se comprueba con su dígito de control antes de
aplicarse: la errata de un carácter produce un ORCID que existe y es de otra
persona.

**Cómo se corre.** En Linux o macOS, `make revision`. En Windows —donde `make`
no existe— hay asistente:

```
scripts\revisar-identidad.ps1     clic derecho -> «Ejecutar con PowerShell»
```

Genera la página, la abre, y cuando usted vuelve con el CSV exportado lo recoge
de la carpeta de descargas, respalda el anterior, muestra en seco qué se
aplicaría, y sólo después de su confirmación aplica y reconstruye el sitio y el
estado. Volver a correrlo no pierde nada: las decisiones ya tomadas se siembran
desde `internal/identity_decisions.csv`.
