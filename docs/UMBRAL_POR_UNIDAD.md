# Umbral de interpretabilidad para el informe de una unidad

**Capa:** pública · **Fase:** 3 · **Estado:** **propuesta, pendiente de decisión** (2026-09-09)

Un informe recortado a la Facultad de Ingeniería sale con 46 publicaciones y
presenta su mediana de FWCI y su porcentaje en el top 10 % con la misma cara que
el informe institucional, que descansa sobre 823. El proyecto ya resolvió esto
para las personas —una banda de «muestra reducida» por debajo de cinco
publicaciones— y para las unidades no existe nada.

Este documento mide cuánto se mueven esos indicadores según el tamaño del
conjunto y propone un umbral. No lo aplica: la decisión es del responsable,
porque fijar el número tiene consecuencias sobre qué se dice de cada facultad.

---

## 1. Cómo se midió

No con una convención estadística traída de fuera, sino con la perturbación
mínima que de verdad ocurre: **una publicación más o una menos en el recorte**.

Para cada unidad se recalculó el indicador quitando una publicación, para las n
posibles, y se anotó el rango resultante. Es un jackknife, y responde a la
pregunta que importa: si el próximo export de Scopus trae una publicación más de
esta facultad, ¿cuánto cambia la cifra que el informe presenta como suya?

---

## 2. Lo que se midió

| Unidad | n | FWCI mediano | Se mueve | Top 10 % | Se mueve |
|---|---:|---:|---:|---:|---:|
| Medicina y Salud | 382 | 0,52 | 0,015 | 11,5 % | 0,3 pp |
| Educación y Ciencias Sociales | 47 | 0,83 | 0,040 | 6,4 % | 2,2 pp |
| Ingeniería | 46 | 0,52 | 0,030 | 21,7 % | 2,2 pp |
| Economía y Negocios | 17 | 0,36 | 0,055 | 5,9 % | 6,2 pp |
| Escuela de Kinesiología | 17 | 0,41 | 0,035 | 5,9 % | 6,2 pp |
| Escuela de Nutrición y Dietética | 12 | 0,62 | 0,090 | 25,0 % | 9,1 pp |
| Artes | 6 | 0,08 | 0,160 | 0,0 % | 0,0 pp |
| Derecho | 5 | 0,06 | 0,085 | 0,0 % | 0,0 pp |
| Humanidades y Comunicaciones | 4 | 0,07 | 0,150 | 0,0 % | 0,0 pp |
| Escuela de Enfermería | 3 | 0,67 | 0,505 | 33,3 % | 50,0 pp |
| Arquitectura, Diseño y Estudios Creativos | 3 | 0,00 | 0,360 | 0,0 % | 0,0 pp |
| Escuela de Ciencias de la Familia | 2 | 1,52 | 0,510 | 0,0 % | 0,0 pp |
| Escuela de Ingeniería Civil Industrial | 1 | 0,70 | — | 0,0 % | — |

«Se mueve» es la diferencia entre el valor máximo y el mínimo al quitar una
publicación cualquiera.

### El top 10 % es el indicador frágil, y su fragilidad es aritmética

Una publicación vale exactamente `100/n` puntos porcentuales. No hay nada que
estimar:

| n | Lo que vale una publicación |
|---:|---:|
| 5 | 20,0 pp |
| 10 | 10,0 pp |
| 20 | 5,0 pp |
| 30 | 3,3 pp |
| 50 | 2,0 pp |
| 100 | 1,0 pp |

El valor de referencia del indicador es 10 % —por construcción, en un conjunto
sin sesgo una de cada diez publicaciones cae en el top 10 % de su campo—. Con
n = 17, una sola publicación vale 6,2 puntos sobre una cifra cuyo orden de
magnitud es 10: la unidad puede pasar de 5,9 % a 0 % o a 12 % por un trabajo.
Eso no es una medición, es un lanzamiento de moneda con aspecto de porcentaje.

### Los ceros no son ceros

Cuatro unidades muestran «0,0 % que no se mueve». No significa estabilidad:
significa que ninguna de sus publicaciones está en el top 10 % y que quitar una
no lo cambia. Con n = 4, que la siguiente publicación entre al top 10 % llevaría
la cifra a 25 %. La inmovilidad del jackknife engaña donde el conjunto es
demasiado pequeño para tener variedad.

---

## 3. La propuesta

### 3.1 El umbral: 20 publicaciones

Y con una propiedad que lo hace robusto: **hoy da exactamente el mismo resultado
que 25 o que 30**, porque la distribución de unidades tiene un hueco entre 17 y
46. No hay ninguna unidad en ese tramo, así que el número exacto no se está
eligiendo sobre el filo.

| Umbral | Unidades marcadas | Publicaciones afectadas |
|---:|---:|---|
| 5 (el de personas) | 5 de 13 | 13 · 2 % del universo |
| 10 | 7 de 13 | 24 · 3 % |
| **20** | **10 de 13** | **68 · 8 %** |
| 25 | 10 de 13 | 68 · 8 % |
| 30 | 10 de 13 | 68 · 8 % |
| 50 | 12 de 13 | 161 · 20 % |

Con 20 quedan sin marcar Medicina y Salud (382), Educación y Ciencias Sociales
(47) e Ingeniería (46). Con 50 se marcaría también a las dos últimas, y una
facultad con 46 publicaciones y un movimiento de 2,2 pp no está en la misma
situación que una con 12 y 9,1 pp.

**El umbral de personas, 5, no sirve aquí.** Marcaría cuatro unidades y dejaría
pasar a Economía y Negocios y a Kinesiología con sus 6,2 puntos de vaivén. Que
el número sea distinto no es incoherencia: el de personas responde además a un
argumento que no es estadístico —DORA y el Manifiesto de Leiden sobre evaluar
individuos— y por eso puede permitirse ser más bajo y más tajante.

### 3.2 La banda dice el número, no sólo la etiqueta

Ésta es la parte que importa más que el umbral. En lugar de un rótulo genérico,
la banda declara **la sensibilidad medida**, que se calcula sin juicio:

> **Muestra reducida.** Los indicadores de impacto de esta unidad se calculan
> sobre 17 publicaciones. Una publicación más o menos mueve el top 10 % en 6,2
> puntos porcentuales. Compare con cautela entre unidades de tamaño muy
> distinto.

Así el umbral sólo decide **cuándo** aparece la banda; **qué dice** lo fija la
aritmética. Si mañana alguien discute el 20, la cifra que el lector ve sigue
siendo correcta.

### 3.3 Alcanza al impacto, no al informe entero

Una facultad con seis publicaciones publicó seis publicaciones: eso no está en
duda y la sección de producción es válida entera. Lo que la banda califica son
los indicadores normalizados —FWCI mediano, top 10 %, cuartil de revista— que
son los que dependen del tamaño.

Marcar el informe completo como «no interpretable» sería apagar de más, y este
proyecto ya decidió una vez que apagar de más también engaña (la mediana por año
en el informe personal, `D-…`).

### 3.4 Dónde va

Sobre las cifras, igual que la banda de las personas, y con la misma redacción
única: en la portada del recorte y en cada sección, en pantalla y en papel. No
se escribe una segunda advertencia.

---

## 4. Lo que NO se propone

- **No se oculta ninguna unidad.** Todas tienen informe; lo que cambia es lo que
  el informe declara sobre sí mismo. Excluir a una facultad de su propio informe
  es una decisión sobre esa facultad tomada en silencio.
- **No se reutiliza la redacción de personas.** «No son interpretables
  individualmente» apela a DORA y al Manifiesto de Leiden, que hablan de evaluar
  personas. Una facultad no es una persona y copiar la frase importaría un
  argumento que aquí no aplica.
- **No se toca el umbral de personas.** Está decidido y su fundamento es otro.
- **No se propone un ranking de unidades.** Ni con banda ni sin ella. La
  cobertura desigual de Scopus entre disciplinas ya hace que comparar Medicina
  con Derecho mida indexación tanto como actividad, y eso el glosario lo dice.

---

## 5. Lo que hay que decidir

1. **El número.** Se propone 20. Cualquier valor entre 18 y 45 produce hoy el
   mismo resultado.
2. **Si la banda alcanza también a las escuelas** o sólo a las facultades. Se
   propone que sí: la aritmética no distingue, y tres de las escuelas están por
   debajo de 20.
3. **Si el umbral vive en `config/indicators.yml`** junto al de personas, con
   nombre propio (`n_minimo_interpretable_unidad`). Se propone que sí, para que
   se pueda cambiar sin tocar código y para que una institución que replique el
   sistema lo ajuste a su tamaño.

---

## 6. Cómo reproducir la medición

El guion del jackknife no se versiona porque es de un solo uso, pero la
medición se rehace sobre `dist/data/publications.json` agrupando por
`unidades`, recalculando la mediana de `fwci` y el porcentaje de
`percentil_citacion <= 10` al quitar cada publicación, y anotando el rango. Los
valores de la tabla del §2 salieron de la carga con fecha de build 2026-09-09.
