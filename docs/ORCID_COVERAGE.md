# Cobertura de ORCID: hasta dónde llega y por qué no llega al 100 %

**Capa:** pública · **Pendientes que ataca:** `T-19` y la pregunta de cuánta
cobertura es alcanzable

> **Las cifras van sobre la base publicada: 513 entidades de autor**, que son las
> 589 formas de firma de la fuente con las variantes ya fusionadas por revisión
> humana (123 formas en 51 personas en la consolidación vigente) y 4 formas
> descartadas por la regla `E-09` (fragmentos de cadena de afiliación, no
> personas — ver `docs/LIMITATIONS.md` §7). Este documento se escribió sobre
> la base de 556, se actualizó el 2026-09-01 a 542, el 2026-09-02 a 538, el
> 2026-09-03 a 530, y de nuevo el 2026-09-04 a la base que sirve el sitio hoy;
> si vuelve a divergir, manda `STATE.md`, que se deriva del repositorio.

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
por afiliación. **Sobre la base que hoy publica el sitio la cobertura es de 252
de 513 entidades (49,1 %)**, y son 328 asignaciones si se cuentan sobre las
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

Sobre las **252 entidades con ORCID** de la base publicada:

| Etiqueta en la ficha | Entidades |
|---|---:|
| `verificado` — dos fuentes independientes coinciden | 147 |
| `declarado por el titular` — una sola fuente, el titular | 36 |
| `comprobado por revisión` — una persona abrió el registro del titular y respaldó una asignación que la vía automática no pudo resolver | 24 |
| `confirmado por revisión` — una persona lo comprobó en `make revision` | 18 |
| `no verificable` — sin obras con DOI que contrastar | 18 |
| `sin confirmar` — pendiente de revisión humana | 8 |
| `encontrado por revisión` — ninguna vía automática halló identificador; una persona lo buscó y lo encontró en el registro de ORCID | 1 |

La cuarta etiqueta (`comprobado por revisión`, antes documentada como
«comprobado a mano») no existía cuando se escribió este documento: la trajo
la revisión humana de identidad, y es la única que no depende de una fuente
automática. `encontrado por revisión` es la más reciente —una sola asignación
por búsqueda manual pura, sin ninguna publicación compartida que la ancle
(`src/build/03_authors.py`, `VEREDICTO_DE_BUSQUEDA`). `sin confirmar` queda
para las que aún esperan una persona.

---

## 3. Por qué el corpus limita la cobertura

La cobertura sube con el número de publicaciones de la firma, y el corpus está
dominado por firmas de una sola publicación:

| Publicaciones de la entidad | Entidades | Con ORCID | Cobertura |
|---|---:|---:|---:|
| 1 | 342 | 117 | 34,2 % |
| 2 | 71 | 46 | 64,8 % |
| 3–4 | 48 | 40 | 83,3 % |
| 5–9 | 33 | 30 | 90,9 % |
| 10 o más | 19 | 19 | **100 %** |

**66,7 % de las entidades tienen una sola publicación.** Una entidad con una
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

Para que las 513 tuvieran ORCID harían falta las cuatro cosas a la vez:

1. que las 513 personas **tengan** un ORCID —es voluntario y no todas lo crean—;
2. que su registro sea **público** —puede configurarse como privado—;
3. que alguna fuente **conecte** ese ORCID con alguna de sus publicaciones de
   este corpus, o que la persona declare la universidad;
4. que el nombre permita distinguirla de sus homónimos.

Las cuatro se cumplen para una parte de los autores y no para el resto. Escribir
513 asignaciones exigiría inventar las que faltan, que es lo primero que prohíben
las reglas del proyecto: *«No inventes datos, columnas, métricas, relaciones ni
resultados»*.

**Y 513 entidades tampoco son 513 personas.** Una revisión humana ya fusionó
variantes (123 formas en 51 personas en la consolidación vigente) y descartó
cuatro firmas que resultaron ser fragmentos de cadena de afiliación, no
personas (`E-09`, ya resuelto — ver `docs/LIMITATIONS.md` §7), pero quedan
grupos de variantes y perfiles fragmentados sin resolver (`T-03`, `T-04`). Una
cobertura del «100 % de los autores» ni siquiera está bien definida mientras
no se sepa cuántos autores hay — y esa cifra sólo baja según se resuelve la
cola, nunca sube.

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
