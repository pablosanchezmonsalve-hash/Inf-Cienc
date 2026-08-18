# Cobertura de ORCID: hasta dónde llega y por qué no llega al 100 %

**Capa:** pública · **Pendientes que ataca:** `T-19` y la pregunta de cuánta
cobertura es alcanzable

> **Las cifras van sobre la base publicada: 556 entidades de autor**, que son las
> 589 formas de firma de la fuente con 63 ya fusionadas en 30 personas por
> revisión humana. Este documento se escribió antes de esa revisión y durante un
> tiempo siguió publicando 222 de 589 —una base que ya no existía— mientras el
> sitio servía otra. Corregido el 2026-08-18; si vuelve a divergir, manda
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
por afiliación. **Sobre la base que hoy publica el sitio la cobertura es de 216
de 556 entidades (38,8 %)**, y son 240 asignaciones si se cuentan sobre las
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

Sobre las **216 entidades con ORCID** de la base publicada:

| Etiqueta en la ficha | Entidades |
|---|---:|
| `verificado` — dos fuentes independientes coinciden | 139 |
| `declarado por el titular` — una sola fuente, el titular | 43 |
| `no verificable` — sin obras con DOI que contrastar | 16 |
| `confirmado por revisión` — una persona lo comprobó en `make revision` | 15 |
| `sin confirmar` — pendiente de revisión humana | 3 |

La cuarta etiqueta no existía cuando se escribió este documento: la trajo la
revisión humana de identidad, y es la única que no depende de una fuente
automática.

---

## 3. Por qué el corpus limita la cobertura

La cobertura sube con el número de publicaciones de la firma, y el corpus está
dominado por firmas de una sola publicación:

| Publicaciones de la entidad | Entidades | Con ORCID | Cobertura |
|---|---:|---:|---:|
| 1 | 387 | 105 | 27,1 % |
| 2 | 74 | 38 | 51,4 % |
| 3–4 | 46 | 31 | 67,4 % |
| 5–9 | 31 | 25 | 80,6 % |
| 10 o más | 18 | 17 | **94,4 %** |

**69,6 % de las entidades tienen una sola publicación.** Una entidad con una
publicación tiene exactamente una oportunidad de ser encontrada: si su ORCID no
aparece en ese único DOI, no hay una segunda vía por la que pueda aparecer.
Entre quienes tienen diez o más, la cobertura es del 94,4 %: **entre los autores
con obra sostenida en la ventana, la cobertura casi está completa**, y lo que
falta se concentra en la cola de entidades con una sola publicación.

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

Para que las 556 tuvieran ORCID harían falta las cuatro cosas a la vez:

1. que las 556 personas **tengan** un ORCID —es voluntario y no todas lo crean—;
2. que su registro sea **público** —puede configurarse como privado—;
3. que alguna fuente **conecte** ese ORCID con alguna de sus publicaciones de
   este corpus, o que la persona declare la universidad;
4. que el nombre permita distinguirla de sus homónimos.

Las cuatro se cumplen para una parte de los autores y no para el resto. Escribir
556 asignaciones exigiría inventar las que faltan, que es lo primero que prohíben
las reglas del proyecto: *«No inventes datos, columnas, métricas, relaciones ni
resultados»*.

**Y 556 entidades tampoco son 556 personas.** Una revisión humana ya fusionó 63
formas de firma en 30 personas, pero quedan 31 grupos de variantes y 20 perfiles
fragmentados sin resolver (`T-03`, `T-04`), y cuatro firmas que probablemente no
sean personas sino fragmentos de cadena de afiliación (`E-09`). Una cobertura del
«100 % de los autores» ni siquiera está bien definida mientras no se sepa cuántos
autores hay — y esa cifra sólo baja según se resuelve la cola, nunca sube.

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
