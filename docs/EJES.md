# Los ejes del informe: qué pregunta responde cada uno

**Capa:** pública · **Fase:** 3

Fuente del panel conceptual que abre cada sección del sitio. Se serializa a
`ejes.json` en el build (`src/build/04_glossary.py`).

**Por qué existe.** Las cuatro secciones del informe presentan indicadores
distintos, y cada una invita a una lectura equivocada concreta: producción se lee
como rendimiento, impacto como calidad, colaboración como influencia, y la
clasificación temática como el tema real de cada artículo. Un lector que llega a
una sección sin saber qué pregunta responde no tiene forma de saber cuál **no**
responde.

**Criterio de escritura.** Cada eje declara tres cosas, en este orden:

1. **Responde** — la pregunta que los indicadores de la sección contestan.
2. **No responde** — la lectura que la sección invita y que sería falsa. Es la
   parte que justifica el panel; sin ella esto sería un subtítulo.
3. **Sobre qué** — la base de cálculo, porque la misma sección puede mezclar
   denominadores (`D-16`).

El texto es **institucionalmente neutro**: describe la metodología, no a esta
universidad. Otra institución lo reutiliza sin tocarlo.

---

## produccion

**Título:** Qué se publicó, y qué no dice el volumen

**Responde:** Cuánto se publicó, en qué años, de qué tipo documental, en qué
fuentes y desde qué unidades académicas.

**No responde:** Qué tan bueno es lo publicado. El volumen es una medida de
actividad indexada, no de rendimiento ni de calidad. Dos unidades con la misma
cifra pueden estar en disciplinas que Scopus cubre de forma muy desigual, y la
comparación entre ellas mide entonces la cobertura de la base tanto como la
actividad de las personas.

**Sobre qué:** Las publicaciones del universo. La producción por unidad
académica se calcula sobre pares autor × publicación, no sobre publicaciones: un
trabajo firmado desde dos unidades cuenta en las dos, y por eso esas barras no
suman el total.

---

## impacto

**Título:** Qué recibió atención, y de qué tipo

**Responde:** Cuántas citas acumuló lo publicado, cómo se compara con lo esperado
para su campo y año, y qué proporción entra en los percentiles altos de citación.

**No responde:** Ni la calidad de un trabajo ni el mérito de quien lo firma.
Citar no es aprobar, y no citar no es desaprobar: hay campos que citan diez veces
más rápido que otros, y por eso las citas crudas no se comparan entre
disciplinas. Tampoco es visibilidad —cuánta gente lo vio— que es otra cosa y se
mide aparte. Y el cuartil o el percentil de una revista describen a la revista,
no al artículo que se publicó en ella.

**Sobre qué:** Las publicaciones con métricas normalizadas, que son menos que el
universo. Las de los años más recientes han tenido menos tiempo para acumular
citas: su impacto es provisional por construcción, no bajo.

---

## colaboracion

**Título:** Con quién se publicó, y qué mide eso

**Responde:** Qué proporción de la producción se firma con al menos una
institución de otro país, con qué países e instituciones, y con qué tamaño de
equipo.

**No responde:** Ni la calidad de la colaboración ni quién la lideró. Compartir
una publicación es la única evidencia que la fuente entrega, y de ahí no se
deduce el reparto del trabajo ni quién dirigió. «Más países» tampoco es «mejor»:
en algunos campos el equipo internacional grande es la norma metodológica y en
otros es excepcional, así que la cifra se lee dentro de su disciplina o no se
lee.

**Sobre qué:** Las publicaciones con métricas. Los países y las instituciones son
campos multivaluados: una publicación aparece en todos los que la firman, así que
esas barras no son partes de un total y no suman el 100 %.

---

## tematica

**Título:** De qué trata lo publicado, según la clasificación de la fuente

**Responde:** En qué áreas y categorías temáticas se concentra la producción,
según la clasificación que Scopus y SciVal aplican.

**No responde:** De qué trata cada artículo. La clasificación por área asigna la
categoría **de la revista**, no el tema del trabajo: un artículo de historia de
la medicina publicado en una revista clínica se clasifica como clínico. Las
categorías tampoco son excluyentes —una revista puede estar en varias— y por eso
no reparten el total. Y la prominencia de un tema describe la atención que el
campo recibe en el mundo, no el desempeño de quien publica en él.

**Sobre qué:** Las publicaciones con área temática asignada. Al ser
multivaluadas, la suma de las categorías supera el número de publicaciones.
