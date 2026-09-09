# Lecturas: qué muestra cada gráfico

**Capa:** pública · **Fase:** 3

Fuente de la línea **«Qué muestra»** que acompaña a cada figura del sitio, en
pantalla y en el informe descargado. Se serializa a `lecturas.json` en el build
(`src/build/04_glossary.py`), igual que el glosario y los paneles de eje.

**Por qué existe.** Quien mira un gráfico bibliométrico desde su propia
disciplina no siempre sabe qué cuenta una barra, y muchas veces ni siquiera
sabe que no lo sabe. La ayuda contextual y el glosario sirven a quien ya
sospecha; la frase junto a la figura sirve a quien la ve por primera vez.

Nació sólo para el papel, con el argumento de que en pantalla la ayuda está a
un clic. El argumento era cierto y la conclusión estaba mal: el resultado fue
que el sitio, la superficie que casi todo el mundo usa, era la única donde el
gráfico no se explicaba. Desde el 2026-09-09 se ve en los dos medios, con el
mismo texto y distinta presentación —pie de figura en pantalla, bloque compacto
en papel—.

**Alcance: TODA figura.** Los dieciocho cortes del explorador y las dos figuras
bento de producción, el treemap y el mapa de calor. Estas dos estaban fuera:
el mapa llevaba su explicación escrita a mano en el HTML y el treemap tenía un
párrafo vacío que nadie rellenaba. La compuerta las cubre leyendo el marcado de
las páginas (`id="…-contenedor"`), así que una figura bento nueva entra sola.

**Qué es y qué no es cada línea.** La lectura describe la **figura**: qué
representa una barra, un punto o un segmento, y sobre qué se cuenta. No es la
advertencia metodológica —eso ya lo declara `config/indicators.yml` y se imprime
debajo— ni la definición del indicador, que vive en `docs/INDICATORS.md`. Son
tres cosas distintas y el papel las lleva en este orden:

1. **Qué muestra** — esta lectura.
2. **Cuidado** — la advertencia del catálogo, cuando la hay.
3. **El sello** — fuente, fecha de corte, N y cobertura del recorte.

**Criterio de escritura.** Una o dos frases. Se nombra la unidad que se cuenta
—publicaciones, pares, firmas— porque es donde nacen los malentendidos, y se
dice cuando una publicación puede contarse en más de una barra. Nada de
adjetivos de valor: el gráfico muestra, no califica.

**Clave.** El código del indicador, o el campo cuando el corte no tiene código
propio (`escuela` es `P-07` visto por escuela y no un indicador nuevo).

---

## P-02 — Producción anual

**Muestra:** Cada barra cuenta las publicaciones cuyo año de publicación cae en
ese año. Mide actividad indexada en la ventana, no producción total.

---

## P-03 — Tipo documental

**Muestra:** Cada barra cuenta las publicaciones de un tipo documental según lo
clasifica la fuente: artículo, revisión, capítulo de libro, carta y demás.

---

## P-05 — Fuentes con más publicaciones

**Muestra:** Cada barra es una revista o fuente, y su largo cuenta cuántas
publicaciones del recorte aparecieron en ella. Se dibujan las quince con más.

---

## P-07 — Unidad académica

**Muestra:** Cada barra cuenta publicaciones distintas atribuidas a una
facultad. Una publicación firmada desde dos facultades cuenta en las dos, así
que las barras suman más que el total del recorte.

---

## escuela — Escuelas dentro de cada facultad

**Muestra:** El mismo recuento de `P-07` un nivel más abajo: cada barra es una
escuela, y sólo aparecen las publicaciones cuya afiliación nombra la escuela y
no sólo la facultad.

---

## I-01 — Citas por año de publicación

**Muestra:** Cada barra suma las citas que han recibido las publicaciones de ese
año, contadas hasta la fecha de corte. No son las citas emitidas ese año.

---

## I-04 — FWCI mediano por año

**Muestra:** Cada punto es la mediana del FWCI de las publicaciones de ese año.
El FWCI compara las citas recibidas con las esperadas para el mismo campo, año y
tipo de documento: 1,00 es el promedio mundial.

---

## I-05 — Umbrales de percentil

**Muestra:** Cuántas publicaciones del recorte entran en cada umbral de las más
citadas de su campo. Los umbrales están encajados: lo que está en el top 1 %
también se cuenta en el 5 %, en el 10 % y en el 25 %.

---

## R-01 — Cuartil de la revista

**Muestra:** Reparte las publicaciones del recorte según el cuartil de la revista
en que salieron, medido por su percentil SJR. Cada publicación cae en un solo
cuartil.

---

## A-01 — Vías de acceso abierto

**Muestra:** Cada barra cuenta las publicaciones que la fuente marca con esa vía
de acceso abierto —dorada, verde, híbrida o de bronce—. Una publicación puede
llevar varias a la vez.

---

## C-01 — Nacional o internacional

**Muestra:** Reparte las publicaciones del recorte según participe o no al menos
una institución de otro país en la firma. No mide cuánta colaboración hubo, sólo
si la hubo.

---

## C-03 — Países colaboradores

**Muestra:** Cada barra es un país y cuenta las publicaciones firmadas con al
menos una institución de ahí. Una publicación con tres países cuenta en los
tres. Se dibujan los quince con más.

---

## C-04 — Instituciones colaboradoras

**Muestra:** Cada barra es una institución que aparece en la firma de alguna
publicación del recorte, y cuenta cuántas comparte. Se dibujan las quince con
más.

---

## C-06 — Autores por publicación

**Muestra:** Cada barra cuenta publicaciones según cuántas personas las firman,
agrupadas en tramos. Cuenta **todos** los autores del trabajo, no sólo los de la
institución.

---

## C-05 — Red de coautoría

**Muestra:** Cada punto es una firma de la institución y cada línea une a dos que
comparten al menos una publicación; el grosor de la línea es cuántas comparten.
Se dibujan los grupos de cinco personas o más, y las cifras y la tabla cubren a
todas.

---

## T-05 — Áreas QS

**Muestra:** Cada barra cuenta las publicaciones de un área QS, que son las cinco
grandes agrupaciones de la clasificación. Una publicación puede estar en varias.

---

## T-01 — Áreas temáticas ASJC

**Muestra:** Cada barra es una categoría temática de la revista en que se publicó
y cuenta sus publicaciones. Se dibujan las veinte con más.

---

## T-04 — Objetivos de Desarrollo Sostenible

**Muestra:** Cada barra cuenta las publicaciones que la fuente asocia a ese
Objetivo de Desarrollo Sostenible. Es un recuento, no un reparto del total: la
mayoría de las publicaciones no tiene ninguno asignado.

---

## treemap — Producción por facultad y escuela

**Muestra:** Cada rectángulo es una unidad, y su área es cuántos pares
autor×publicación le corresponden: una publicación firmada por dos personas de
la misma facultad cuenta dos veces aquí. Las barras de «Unidad académica»
cuentan publicaciones distintas, así que sus totales no coinciden con éste y
ninguno de los dos está mal. Pulsando una facultad se abren sus escuelas.

---

## heatmap — Temáticas ASJC más frecuentes por año

**Muestra:** Cada celda cuenta las publicaciones de una temática en un año. Se
dibujan las ocho temáticas con más publicaciones del período, no todas. La
intensidad del color es la raíz cuadrada del recuento, para que un año con un
pico no aplane el resto del mapa: compare celdas por su cifra, no por su tono.
