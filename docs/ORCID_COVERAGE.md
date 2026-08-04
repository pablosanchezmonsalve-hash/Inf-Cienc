# Cobertura de ORCID: hasta dónde llega y por qué no llega al 100 %

**Capa:** pública · **Pendientes que ataca:** `T-19` y la pregunta de cuánta
cobertura es alcanzable

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

**Cobertura: 174 → 222 de 589 (29,5 % → 37,7 %)**, un 27,6 % más de firmas
identificadas. La ejecución completa consultó los 804 DOI del corpus y encoló
2 desacuerdos entre Crossref y el registro, sin resolverlos.

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

| Etiqueta en la ficha | Firmas |
|---|---:|
| `verificado` — dos fuentes independientes coinciden | 153 |
| `declarado por el titular` — una sola fuente, el titular | 48 |
| `no verificable` — sin obras con DOI que contrastar | 17 |
| `sin confirmar` — pendiente de revisión humana | 4 |

---

## 3. Por qué el corpus limita la cobertura

La cobertura sube con el número de publicaciones de la firma, y el corpus está
dominado por firmas de una sola publicación:

| Publicaciones de la firma | Firmas | Con ORCID | Cobertura |
|---|---:|---:|---:|
| 1 | 419 | 110 | 26,3 % |
| 2 | 74 | 38 | 51,4 % |
| 3–4 | 45 | 30 | 66,7 % |
| 5–9 | 36 | 30 | 83,3 % |
| 10 o más | 15 | 14 | **93,3 %** |

**71,1 % de las formas de firma tienen una sola publicación.** Una firma con
una publicación tiene exactamente una oportunidad de ser encontrada: si su ORCID
no aparece en ese único DOI, no hay una segunda vía por la que pueda aparecer.
Entre quienes tienen diez o más, la cobertura ya es del 93,3 %: **entre los
autores con obra sostenida en la ventana, la cobertura casi está completa**, y
lo que falta se concentra en la cola de firmas con una sola publicación.

A esto se añade un límite estructural: **10 formas de firma no tienen ninguna
publicación con DOI**. Ninguna vía basada en DOI puede alcanzarlas, ni la de
Crossref ni la del registro. Para ellas sólo queda la búsqueda por afiliación,
que no publica.

---

## 4. Lo que el 100 % exigiría

Para que las 589 tuvieran ORCID harían falta las cuatro cosas a la vez:

1. que las 589 personas **tengan** un ORCID —es voluntario y no todas lo crean—;
2. que su registro sea **público** —puede configurarse como privado—;
3. que alguna fuente **conecte** ese ORCID con alguna de sus publicaciones de
   este corpus, o que la persona declare la universidad;
4. que el nombre permita distinguirla de sus homónimos.

Las cuatro se cumplen para una parte de los autores y no para el resto. Escribir
589 asignaciones exigiría inventar las que faltan, que es lo primero que prohíben
las reglas del proyecto: *«No inventes datos, columnas, métricas, relaciones ni
resultados»*.

**589 formas de firma tampoco son 589 personas.** Son variantes de nombre, y
consolidarlas es un pendiente abierto de revisión humana (`T-03`, `T-04`). Una
cobertura del «100 % de los autores» ni siquiera está bien definida mientras no
se sepa cuántos autores hay.

---

## 5. Qué es lo correcto en vez de un porcentaje

El indicador `AU-05` se publica **con su denominador y su veredicto a la vista**,
no como una cifra a maximizar. Cada ORCID del sitio dice qué evidencia lo
respalda: `verificado`, `no verificable` o `sin confirmar`. Una firma sin ORCID
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
