# Arquitectura UX/UI del dashboard

**Capa:** pública · **Fase:** 2 · **Estado:** implementado en `web/`

Referencia estructural: `dataciencia.anid.gob.cl`. Conceptual, no copia de
diseño.

---

## 1. Principio rector

Cada elemento visual debe responder una pregunta analítica. Ningún gráfico
decorativo. Si un dato no sostiene una lectura, no se grafica: se tabula o se
omite.

Corolario operativo: **la advertencia metodológica es parte del componente**, no
una nota al pie. Una cifra sin su denominador y su fecha de corte está
incompleta.

Segundo corolario, más reciente: **el lector pregunta, el sitio responde**. Un
informe entrega las cifras que alguien decidió por él; una plataforma le deja
recortar el conjunto y ver qué pasa. Todo lo que sigue está subordinado a eso —
incluida la decisión de que el contexto metodológico se pliegue tras un control
en vez de ocupar la pantalla que le toca al dato.

---

## 2. Navegación general

```
Portada
├── Producción      → volumen, años, tipos, fuentes
├── Impacto         → citas, FWCI, top percentiles, cuartiles de revista
├── Colaboración    → países, instituciones, tamaño de equipo
├── Áreas temáticas → QS (entrada) → ASJC (detalle)
├── Autores         → ranking → ficha individual
├── Publicaciones   → tabla completa filtrable
└── Metodología     → glosario, límites, fuentes
```

Profundidad máxima 3 niveles. Breadcrumbs desde el nivel 2.
`Metodología` es accesible desde cualquier página, no enterrada en el pie.

---

## 3. Encabezado institucional

| Elemento | Contenido | Propósito |
|---|---|---|
| Identidad | Logo y nombre institucional (desde `config/institution.yml`) | Atribución |
| Título | «Informe Cienciométrico Institucional» | Contexto |
| **Barra de vigencia** | «Datos: Scopus/SciVal · Ventana 2023–2025 · Corte 22-07-2026» | **Persistente en todas las páginas** |

La barra de vigencia es una decisión deliberada: es la única forma de que una
captura de pantalla del dashboard siga siendo interpretable fuera de contexto.

---

## 4. El explorador

**La decisión que ordena todo lo demás.** El sitio dejó de servir indicadores ya
calculados y pasó a derivarlos en el navegador sobre el subconjunto que el
lector elige.

Antes el build dejaba `series.json` con las cifras del conjunto completo y la
página las pintaba. Eso hacía un **informe**: el lector veía las cifras que
alguien decidió por él y no podía preguntar nada más. Ahora *«las publicaciones
de la Facultad de Medicina de 2024 con colaboración internacional»* no es una
vista preparada — es una pregunta que se responde al momento, porque el dato de
cada publicación viaja entero en `publications.json`.

Tres superficies comparten un solo motor
([`explorador.js`](../web/assets/js/explorador.js)): la portada, las cuatro
secciones y el listado de publicaciones.

### 4.1 El recorte vive en la URL

`?anio=2024&unidad=Facultad+de+Medicina` es el estado completo. De ahí salen
tres propiedades que un tablero sin URL no tiene:

- una vista concreta se puede **citar** en un correo o en un informe;
- el **botón de volver** del navegador deshace un filtro;
- el recorte **viaja entre páginas**: se hace en el tablero y el listado lo
  hereda.

Medido: 823 → 113 publicaciones al pedir Medicina 2024, con las seis cifras y
los cuatro gráficos recalculados, y esas mismas 113 en la tabla al seguir el
enlace.

### 4.2 Qué NO recalcula, y por qué

**El FWCI y los percentiles no se promedian sobre un recorte.** Son métricas
*normalizadas* que SciVal computa contra el mundo; promediarlas sobre un
subconjunto arbitrario daría un número con aspecto de FWCI que no lo es. Sobre
un recorte se informa la **mediana** de los valores que la fuente ya asignó a
cada publicación, y se dice que es eso.

Confundir «promedio de FWCI» con «FWCI del conjunto» es exactamente el error que
el Leiden Manifesto pide no cometer, y la tentación aparece justo aquí: el dato
está disponible y sumar es fácil.

La mediana, además, no es una preferencia: la distribución del FWCI es
asimétrica —unas pocas publicaciones muy citadas tiran del promedio— y sobre el
recorte de una facultad la media miente más todavía.

### 4.3 El tablero de cifras

Seis fichas, siempre las mismas, que se recalculan enteras a cada recorte. Cada
una lleva **su propio denominador pegado** (`D-16`): son bases distintas, y
presentarlas juntas sin decirlo invita a dividir una por otra.

| Cifra | Base declarada |
|---|---|
| Publicaciones | las del recorte |
| Citas recibidas | las que tienen métricas |
| Citas por publicación | las que tienen métricas |
| FWCI mediano | las que tienen FWCI |
| Colaboración internacional | las que declaran país |
| Autores UFT | las que tienen autoría nombrada |

Al recalcularse, la cifra que **cambió** parpadea una vez. Sin esa señal, un
filtro que mueve poco parece no haber hecho nada. Bajo
`prefers-reduced-motion` no ocurre.

El glosario contextual cuelga de las fichas. Vivía en los KPI de la portada
anterior y se habría perdido al sustituirlos; aquí hace más falta todavía,
porque **una cifra recalculada sobre un recorte se malinterpreta con más
facilidad que una del total**.

### 4.4 Los controles

Un `<details>` por dimensión, con chips dentro. La elección del elemento no es
estética: **un `details` se abre y se lee sin JavaScript**, que es lo que
permite que la garantía de la §14 siga en pie con un panel de filtros en la
página.

Los recuentos de cada faceta se calculan con las **demás** dimensiones
aplicadas pero no la propia. Si una faceta se contara a sí misma, al elegirla
todas sus hermanas caerían a cero y el filtro dejaría de poder cambiarse sin
limpiarlo antes.

### 4.5 Un solo motor, y qué costó unificarlo

Publicaciones tenía su propio sistema de filtros, anterior al explorador: dos
implementaciones del mismo concepto, con **claves distintas para la misma
dimensión** —`internacional` en una, `colaboracion` en la otra— y dos lectores
de URL que no se entendían.

> **Unificar no puede romper lo que alguien ya citó.** La dimensión se unifica
> bajo `colaboracion`, pero el nombre viejo se sigue leyendo: un enlace guardado
> o pegado en un correo sigue recortando. Está cubierto por la batería, no sólo
> por el código.

Dos cosas que hubo que añadir al motor:

- **Búsqueda de texto insensible a acentos.** Buscar «Nunez» encuentra «Núñez»:
  en un corpus con nombres en español, exigir la tilde convierte el buscador en
  un examen de ortografía. Medido: 5 resultados con y sin ella.
- **`consulta(sel)`**, que serializa el recorte. Se calcula del *recorte* y no
  de `location.search` por dos razones: es la verdad —la URL puede ir un paso
  por detrás— y `location` no existe bajo Node, donde corre el pre-renderizado.
  El build abortó al primer intento justamente por eso.

> **Un detalle que habría hecho inusable el buscador.** Los controles se
> repintan enteros a cada pulsación, así que el campo de texto se reemplaza
> mientras se escribe: la primera letra expulsaba el foco. Se devuelven el foco
> y la posición del cursor. Es la clase de fallo que sólo aparece usándolo, y
> por eso quedó cubierto por la batería.

---

## 4 bis. Panel conceptual de sección

Cada sección abre declarando **qué responde y qué NO responde**. El «no
responde» es la parte que justifica el panel; sin ella esto sería un subtítulo.

| Sección | Qué NO dice |
|---|---|
| Producción | El volumen no mide calidad ni esfuerzo: cuenta documentos indexados. |
| Impacto | Las citas miden atención recibida, no calidad ni utilidad social. |
| Colaboración | Colaborar no es por sí mismo mejor: describe una forma de trabajo, no un logro. |
| Áreas temáticas | La categoría de la revista no es el tema exacto del artículo. |

Va **plegado** tras un control, como el resto del contexto metodológico (§12.8):
la pantalla la manda el dato, y la advertencia sigue a un clic para quien la
necesite.

---

## 4 ter. La banda, y dónde quedó

La banda fue durante un tiempo la unidad de composición de las páginas
narrativas. **Ya no lo es**: el explorador la sustituyó en la portada y en las
cuatro secciones, porque un tablero que se interroga no se compone como un
texto que se lee de arriba abajo.

Sobrevive donde su trabajo sigue siendo necesario: **el suelo de contraste de
los indicadores diferidos**.

Que un indicador esté verificado y no se publique es información del informe —
un hueco se leería como que el fenómeno no existe. Y como esos indicadores **no
responden al recorte** (no se calculan en el navegador), mezclarlos con los
cortes que sí responden haría creer que el filtro los cambia. Su propio suelo es
lo que dice, sin escribirlo, que son otra cosa.

`.banda-contraste` sigue redefiniendo los tokens **en su propio ámbito**, que es
lo que permite que módulos, sellos y tablas que caen dentro se adapten solos sin
una segunda hoja de estilo para «lo que va sobre fondo oscuro».

---

## 5. Los cortes

Un **corte** es la unidad de la sección: un gráfico que responde al recorte, con
su conmutador Gráfico ⇄ Tabla y su advertencia si la tiene. Sustituye al
«módulo» de la versión anterior, que dibujaba una serie ya calculada.

Catorce de los quince indicadores del sitio se derivan de `publications.json`,
así que son cortes de pleno derecho. La forma la elige **la relación del dato**
(§12.4), no la costumbre.

| Corte | Forma | Por qué esa forma |
|---|---|---|
| `P-02` Publicaciones por año | Barras verticales | 3 puntos no son una serie temporal |
| `P-03` Tipo documental | Barras horizontales | 10 categorías muy desbalanceadas |
| `P-05` Fuentes | Barras horizontales, top 15 | 495 fuentes: hay que recortar y decirlo |
| `P-07` Unidad académica | Barras horizontales | Cobertura parcial: la advertencia es obligatoria |
| `I-01` Citas por año | Barras verticales | Con advertencia de ventana de citación |
| `I-04` FWCI mediano por año | Desviación contra 1,00 | Se lee CONTRA el mundo, no en magnitud |
| `I-05` Umbrales de percentil | Acumulada | Tramos **anidados**: no se suman |
| `R-01` Cuartil de revista | Proporcional | Reparten un total conocido |
| `A-01` Vías de acceso abierto | Barras horizontales | Multivaluado |
| `C-01` Nacional o internacional | Barras horizontales | Proporción con «sin dato» visible |
| `C-03` Países | Barras horizontales, top 15 | Mapa descartado: 23 países sobre ~200 |
| `C-04` Instituciones | Barras horizontales, top 15 | Nombres largos |
| `C-06` Autores por publicación | Distribución | Continuo tramificado: el eje ES el dato |
| `T-05` / `T-01` / `T-04` | Barras horizontales | 249 ASJC: top 20 + acceso al resto |

> **C-04 era el único que no se podía derivar.** «Instituciones colaboradoras»
> salía de una columna que no viajaba por publicación: `publications.json` traía
> el recuento pero no los nombres. Se añadió la lista. Sin eso, la sección de
> colaboración habría tenido un gráfico que **ignora el filtro sin decirlo**,
> que es peor que no tenerlo.

**Descartado:** mapa coroplético de colaboración (23 países sobre ~200 → mapa
mayoritariamente vacío que exagera visualmente la dispersión), nube de palabras
(sin lectura cuantitativa), gráfico de torta para ASJC (multivaluado: los
porcentajes no suman 100 %).

### 5.1 El índice de la sección

El panel lateral pasó de ser un índice de módulos a ser los controles del
recorte, y con eso se habría perdido la navegación rápida entre gráficos.
Vuelve **debajo de los filtros**, con su scroll-spy.

> **El ancla al último corte no movía nada.** Medido: el corte se quedaba a
> 351 px del borde con un `scroll-margin` correcto de 120. No era el margen —
> la página se acababa antes y no había recorrido que gastar. Con espacio al
> final, el último sube hasta la cabecera como los demás.

---

## 6. Filtros

Los filtros son **el motor del explorador**, no un accesorio de una página. Su
comportamiento y su modelo de estado están en la §4; aquí quedan sólo las
dimensiones y las reglas que las gobiernan.

| Dimensión | Origen | Notas |
|---|---|---|
| Año | `anio` | 3 valores |
| Área QS | `qs_area` | 5 valores · multivaluado |
| Unidad académica | `unidades` | incluye «Sin dato declarado» como opción real |
| Tipo documental | `tipo` | 10 valores |
| Acceso abierto | `open_access` | multivaluado · incluye «Sin dato declarado» |
| Colaboración | derivado de `es_internacional` | Internacional / Nacional / Sin dato |
| Texto libre | título, fuente, autores UFT | debounce 250 ms · insensible a acentos |

### Reglas de comportamiento

1. **AND entre dimensiones, OR dentro de una dimensión.** Es lo que espera
   cualquiera que haya usado un filtro; al revés, cada clic adicional daría
   menos resultados sin que se entienda por qué.
2. **«Sin dato declarado» es una opción de filtro, no un hueco.** Poder pedir
   *«las publicaciones cuya unidad no se determinó»* es parte de auditar la
   cobertura, y esconderlas las volvería invisibles justo para quien las busca.
3. **Los recuentos de una faceta se calculan sin aplicarse a sí misma.** Si no,
   al elegir un valor todos sus hermanos caerían a cero.
4. **Una faceta en 0 se muestra deshabilitada, no se oculta.** Su ausencia es
   información.
5. **El recorte es el estado de la aplicación** y vive en la URL (§4.1).

## 7. Buscador

Campo único sobre título, fuente y autor. Debounce 250 ms. Coincidencia por
subcadena insensible a acentos y caso — la misma normalización que el matching
institucional, reutilizada.

No se implementa búsqueda semántica ni ranking por relevancia: con 823
registros, la coincidencia literal es suficiente y verificable.

---

## 8. Detalle documental

Al abrir una publicación:

| Sección | Campos |
|---|---|
| Cabecera | Título, año, tipo, fuente, DOI (enlace) |
| Autoría | Autores UFT destacados; total de autores; posición |
| Impacto | Citas, FWCI, percentil de citación · **con fecha de corte** |
| Fuente | SJR, CiteScore, SNIP y percentiles · **etiquetados «de la revista»** |
| Temática | ASJC, Topic, ODS si existe |
| Colaboración | Países, instituciones |
| Trazabilidad | EID, banderas de disponibilidad |

Si la publicación carece de métricas (7 casos), la sección de impacto muestra
«Sin métricas disponibles: esta publicación no está en el export de SciVal», no
un cero ni un guion.

---

## 9. Estados de carga, vacío y error

| Estado | Tratamiento |
|---|---|
| Cargando | Esqueleto con la forma del contenido, no spinner genérico |
| Vacío por filtro | «Ningún resultado con estos filtros» + botón limpiar + recuento de cuáles descartan más |
| Dato ausente | «Sin dato declarado», **nunca 0 ni «—» ambiguo** |
| Indicador no calculable | Tarjeta con la razón y qué falta (ej. ORCID) |
| Error de carga | Mensaje con el artefacto que falló y opción de reintentar |

**Regla dura:** ausencia de dato y valor cero nunca se representan igual. Un
autor sin ORCID y un autor con 0 citas son casos distintos y deben verse
distintos.

---

## 10. Accesibilidad

- Contraste mínimo AA en texto y elementos de gráfico.
- El color nunca es el único portador de información: los estados llevan
  etiqueta o patrón.
- Tablas con encabezados asociados y orden operable por teclado.
- Tooltips accesibles por foco, no sólo por hover — de lo contrario la ayuda
  contextual no existe en móvil ni por teclado.
- Gráficos con tabla de datos equivalente accesible.

---


### 10.1 Lo que la auditoría encontró y se corrigió

Medido sobre las 10 páginas a 360 px de ancho:

**Objetivos de puntero (WCAG 2.2 · SC 2.5.8).** Siete controles bajo el mínimo
de 24×24: el botón de ayuda a 17×17, las etiquetas ORCID y el enlace de vigencia
a 20 de alto, el de seguimiento a 15 y la casilla de filtro a **13×13**. Los
enlaces dentro de un párrafo se dejan como están —la norma los exceptúa y
agrandarlos rompería el interlineado de la prosa—. El botón de ayuda separa área
y dibujo: el botón es el objetivo de 24×24 y el círculo lo pinta `::before`.

> Una primera versión amplió el área con un pseudo-elemento superpuesto. Se veía
> correcta en la hoja y **al comprobarla por hit-test real no recibía el
> evento**: el área existía en el CSS y no en la pantalla. Se reemplazó por
> padding con margen negativo, que agranda la caja real —medible— sin mover la
> maquetación.

**Esquema de encabezados.** Todo el sitio era `h2`, así que la banda y los
módulos que contiene competían al mismo nivel: quien navega por encabezados no
tenía forma de saber que los módulos cuelgan de algo. Ahora `h1` página → `h2`
banda → `h3` módulo. El catálogo **no** usa bandas, así que sus secciones se
quedan en `h2`: bajarlas habría creado el salto `h1`→`h3` que se corregía.

**Teclado dentro de un gráfico.** Cada barra era un punto de tabulación: en
Áreas temáticas, **41 de los 70 puntos de la página eran barras**, así que pasar
del primer gráfico al enlace siguiente costaba veinte pulsaciones de Tab. Un
gráfico no es una lista de veinte controles: es *un* control con veinte
posiciones. Con el patrón de composición de las prácticas ARIA —un punto de
tabulación y flechas por dentro, con `Inicio` y `Fin` en los extremos— la página
baja de **70 puntos a 32**. El `tabindex` rueda, así que al volver con Tab se
entra por donde se salió.

La pista del atajo aparece al entrar el foco y va **debajo** del gráfico: probada
encima, tapaba la primera barra y su valor.

**Otros:** los tres «Ver la sección completa» de la portada eran indistintos
fuera de contexto (SC 2.4.4) y ahora nombran su sección en `aria-label`;
cabeceras de tabla sin `scope` en tres tablas (SC 1.3.1); y `autor.html` sin
parámetro quedaba en blanco, sin encabezado ni salida.


## 11. Responsive

Prioridad de contenido en pantallas estrechas: KPIs → módulo actual → filtros
en panel desplegable. Las tablas anchas scrollean horizontalmente dentro de su
contenedor; la página nunca scrollea en horizontal.

---

## 12. Sistema visual

Implementado en `web/assets/css/app.css`, hoja única. Sin dependencias externas:
ninguna fuente, hoja ni script se carga desde un CDN.

### 12.1 Paleta: alto contraste, y el dato en una sola familia

La dirección es **científico moderno de alto contraste**: papel blanco puro o
suelo casi negro, cifras enormes, y el color reservado al dato. Sustituye a una
paleta cálida (Ink Black · Deep Ocean · Peach Glow) que a su vez había
sustituido a una identidad roja.

El motivo del cambio es legible en las cifras: la tinta pasa a **19,34:1** en
claro y **16,58:1** en oscuro. Un informe que se lee en una sala de reuniones,
en un proyector o con presbicia no puede permitirse menos.

El dato es **azul índigo**: `#2b44d9` en claro, `#7c93ff` en oscuro. Se eligió
por medición y no por gusto — ver más abajo la separación frente al ámbar de
advertencia.

| Token | Fondo | Claro | Oscuro | Piso |
|---|---|---|---|---|
| `--tinta` | `--superficie` | **19,34** | **16,58** | 4,5 (WCAG 1.4.3) |
| `--tinta-2` | `--superficie` | 9,00 | 9,95 | 4,5 |
| `--tinta-3` | `--superficie-2` | 5,22 | 6,07 | 4,5 |
| `--cifra` | `--superficie` | 19,34 | 16,58 | 3,0 (texto grande) |
| `--accion` | `--superficie` | 8,55 | 7,61 | 4,5 |
| `--serie-1` | `--superficie` | 7,16 | 6,40 | 3,0 (WCAG 1.4.11) |
| `--sin-dato` | `--superficie` | 3,42 | 3,78 | 3,0 |
| `--ord-1` … `--ord-4` | `--superficie` | 14,91 … 3,21 | 14,07 … 3,34 | 3,0 |
| `--marca-tinta` | `--marca` | 15,14 | 15,14 | 4,5 |
| `--aviso-tinta` | `--aviso-fondo` | 7,84 | 10,43 | 4,5 |

**La cifra no lleva color.** `--cifra` es tinta pura en los dos temas, a
19,34:1. En un tablero donde el número es lo que se viene a ver, teñirlo lo
convierte en decoración y le quita contraste; el color queda libre para lo único
que codifica algo, que es el dato de los gráficos.

#### Las tres condiciones que el contraste solo no cubre

**Separación dato ↔ advertencia:** ΔE OKLab **36,0** en claro y **33,3** en
oscuro, sobre un piso de 20. Es holgura, y viene de que las dos familias
—índigo y ámbar— están lejos en el círculo. La paleta cálida anterior vivía al
borde de este piso y una de sus versiones llegó a incumplirlo.

**Rampa ordinal Q1–Q4:** paso mínimo ΔE **11,8** y **11,2**, sobre un piso de 8,
con luminosidad monótona. Un solo tono en cuatro pasos: cuatro tonos distintos
habrían afirmado que Q1 y Q4 no tienen relación entre sí, cuando son posiciones
de una misma escala.

**Par categórico bajo daltonismo:** peor caso ΔE **37,9** en claro y **22,0** en
oscuro. El par se separa por **luminosidad** —índigo contra casi negro— y eso
ninguna dicromacia lo colapsa.

#### Dos correcciones que impuso la medición

> **`--ord-4` no llegaba a 3:1.** El cuarto escalón de la rampa quedaba en
> 1,94:1 sobre blanco. No bastaba con oscurecerlo: al hacerlo se comía la
> separación con `--ord-3`. La rampa entera se rebalanceó con la matemática del
> validador hasta que los cuatro escalones cumplieran a la vez el piso de
> contraste y el de ΔE.
>
> **La marca de ausencia se quedaba corta.** `--sin-dato` medía 2,56:1 sobre
> blanco y 2,95 sobre el segundo suelo. Un gris que no se ve es peor que no
> marcar la ausencia, porque la deja pasar por dato.

#### El validador estaba midiendo otra paleta

`validar_paleta.py` leía la hoja entera y se quedaba con la **última** aparición
de cada token. Desde que `.banda-contraste` redefine `--superficie`,
`--superficie-2` y `--plano` en su ámbito, esos valores pisaban los de `:root`:
el validador comparaba tinta clara contra suelo oscuro y declaraba **12 fallos
inexistentes**. Ahora lee sólo el bloque `:root`.

No es cosmético. Un instrumento que da falsos positivos se deja de mirar, y
entonces tampoco atrapa los verdaderos — que era el caso:

> Al medir la banda de contraste **como ámbito propio**, aparecieron cuatro
> fallos reales. La banda redefine `--serie-1`, `--serie-2` y `--sin-dato` pero
> se había olvidado de la rampa ordinal y de la tinta del botón. Como la banda
> es oscura en los **dos** temas, en claro esos tokens conservaban su valor
> claro y caían sobre un suelo oscuro: `--ord-1` medía **1,06:1**, o sea
> invisible.

### 12.2 Tipografía

**La escala subió entera.** La anterior arrancaba en 11 px y ponía las notas a
12,5 y las tablas a 14: por debajo de los 16 px que las guías de accesibilidad
dan como suelo de lectura cómoda, y el primer texto que deja de leerse cuando la
vista cambia con la edad.

| Token | Valor | Uso |
|---|---|---|
| `--t-xs` | 13 px | códigos, micro-etiquetas |
| `--t-s` | 15 px | notas, pie |
| `--t-m` | 16 px | tablas, controles |
| `--t-base` | 17 px | prosa |
| `--t-l` | 20 px | — |
| `--t-xl` | 24 px | título de módulo |
| `--t-2xl` | 2–3,25 rem | h1 |
| `--t-cifra` | 2,75–4,5 rem | valor de ficha |
| `--t-display` | 3,5–7 rem | cifra de titular |

**Todo en `rem`, nunca en `px`.** WCAG 1.4.4 exige que el texto llegue al 200 %
sin perder contenido ni función, y eso sólo se cumple si la escala entera cuelga
del tamaño raíz que el lector puede cambiar en su navegador.

Las cifras usan `tabular-nums`. En un explorador el número cambia a cada filtro,
y con cifras proporcionales el bloque entero salta a cada pulsación.

> **El texto dentro del SVG no heredaba la escala.** Son píxeles fijos en la
> hoja, así que se quedó a 11 px mientras el resto subía. Se movió a 13 — y con
> él el medidor de ancho de etiqueta de `core.js`, porque si esos dos números se
> separan las etiquetas se recortan donde no toca.

### 12.3 Espacio y trazo

Escala de espacio de 4 px, de `--e1` (4 px) a `--e7` (48 px). Sin valores
sueltos fuera de la escala.

Radios contenidos (8 px) y **sombra mínima**: la separación entre superficies la
hace el filete, no la elevación. Una interfaz analítica no flota. Por la misma
razón la cabecera es color plano de marca con un descenso sutil, sin degradados
de color ni resplandores.

### 12.4 Reglas de color en gráficos

El color codifica **una** de tres cosas, y cuál se declara en la llamada:

| `escala` | Cuándo | Ejemplo |
|---|---|---|
| (por defecto) | Una sola serie | Rankings por volumen: `P-03`, `P-05`, `C-03` |
| `'serie'` | Entidades distintas sin orden entre sí | Anillo de `C-01` |
| `'ordinal'` | Posiciones de una escala ordenada | Cuartiles de revista, `R-01` |

Tres reglas que no se negocian:

1. **La ausencia de dato siempre es gris**, ignorando la escala pedida
   (decisión `D-09`). Un valor no medido no puede parecerse a uno medido.
2. **El color sigue a la entidad, nunca a su posición.** Un ranking por volumen
   no se colorea por rank: al filtrar, el color saltaría de una entidad a otra.
3. **Si el nombre de la categoría ya es un color, el color deja de estar
   disponible para codificar.** Por eso `A-01` (Gold, Green, Bronze) se dibuja
   en una sola serie: la paleta categórica dejaría «Green» de color naranja.

#### La forma la elige la relación del dato, no la costumbre

El sitio dibujaba **11 de sus 16 indicadores con `barrasH`**. No era una
preferencia: era la forma por defecto aplicándose a relaciones de datos
distintas. Contrastado contra el
[Visual Vocabulary del Financial Times](https://github.com/Financial-Times/chart-doctor),
que clasifica los gráficos por la RELACIÓN que expresan, cuatro estaban en la
categoría equivocada:

| | Relación | Forma |
|---|---|---|
| `I-04` | FWCI contra el 1,00 mundial | `desviacion()` |
| `I-05` | umbrales de percentil, **anidados** | `acumulada()` |
| `C-06` | autores por publicación, continuo tramificado | `distribucion()` |
| `R-01` | cuartiles Q1–Q4 de un total conocido | `proporcional()` |

`I-05` era un problema de **correctitud**, no de estética: los tramos son
anidados —las 3 publicaciones del top 1 % están también en el top 5, 10 y 25— y
cuatro barras hermanas sugerían cuatro grupos disjuntos que podían sumarse. La
suma daba 322, una cifra sin significado.

> **Corrección sobre una primera versión.** El déficit de `I-04` se pintaba con
> `--sin-dato`. Ese gris significa **ausencia** de dato (`D-09`) y un FWCI bajo
> el promedio es un valor **medido**. Ahora la dirección la lleva sólo la
> posición respecto del eje, que no gasta color ni inventa semántica.

### 12.5 Interacción

**Gráficos.** Señalar una marca **atenúa las demás** al 34 % y contornea la
activa. Resaltar sin apagar el resto no dirige la mirada: sólo añade un borde
que hay que buscar. La atenuación se aplica al SVG que contiene la marca, así
que dos gráficos en la misma pantalla no se interfieren.

Cada marca es **enfocable por teclado** y muestra el mismo tooltip que con el
puntero. `Escape` lo cierra. El `aria-label` del gráfico nombra **el indicador**,
no la forma: cinco «gráfico de barras horizontales» seguidos no orientan a quien
navega con lector de pantalla.

En las barras la identidad no la lleva una leyenda sino la etiqueta de la propia
barra y su valor visible al lado. Es relieve suficiente y evita repetir junto al
gráfico lo que ya está escrito en la marca; sólo el anillo lleva leyenda, porque
sus segmentos no admiten etiqueta interior. El tooltip salta abajo o a la izquierda cuando no
cabe: uno recortado por el borde no informa de nada.

El tooltip añade la **cuota sobre el total mostrado**, pero sólo donde las
barras son realmente partes de un total. En umbrales encajados (`I-05`),
multivaluados (`A-01`, `C-03`, `C-04`, `T-01`, `T-04`, `T-05`) y rankings
recortados (`P-05`) se omite: ahí un porcentaje afirmaría algo falso.

**Tablas.** La fila activa lleva fondo teñido **y** un filete de acción a la
izquierda; el fondo solo es demasiado tenue en pantallas de bajo contraste. La
regla responde a `:hover` y a `:focus-within`, de modo que existe navegando con
teclado. Las cabeceras ordenables son **enfocables y se activan con `Enter` o
`Espacio`**: un `<th>` no es un control operable por defecto, y sin eso la tabla
no se podía ordenar sin ratón. Las cabeceras ordenables muestran su afordancia (`↕`) **antes** de
pasar el puntero, y la columna por la que se ordena se marca **en todo su alto**:
con 51 filas en pantalla, una flecha arriba del todo se pierde.

### 12.6 Modo claro y oscuro

El modo oscuro es una paleta **elegida y revalidada contra su propia
superficie**, no una inversión. Invertir una paleta validada no produce una
paleta validada.

- **Claro:** papel blanco puro (`#ffffff`), tinta casi negra (`#0a0e14`).
- **Oscuro:** suelo `#070a0f`, tarjetas levantadas sobre él en `#111721`.

El color del dato **cambia de valor pero no de familia**: índigo en los dos
temas, `#2b44d9` sobre blanco y `#7c93ff` sobre el suelo oscuro. Que la familia
no cambie importa — un lector que alterna de tema no debería tener que reaprender
qué significa el color.

El selector de la cabecera tiene tres estados —automático, claro, oscuro—; el
automático sigue al sistema operativo. La elección se recuerda y se aplica antes
de pintar, para que la página no aparezca un instante con el tema equivocado.

### 12.6 bis Codificación por naturaleza del dato

Tres cosas que antes sólo existían en prosa y ahora tienen forma.

**Trama diagonal = las barras no suman.** Seis indicadores son multivaluados
—`T-01`, `T-04`, `T-05`, `A-01`, `C-03`, `C-04`—: una publicación aparece en
varias barras y la suma supera el total. Hasta ahora se advertía en una nota al
pie y el gráfico se dibujaba igual que uno cuyas barras sí suman. Ahora van
rayadas, con una leyenda que usa **el mismo patrón** que el gráfico (7 px de
período, 2,4 px de trazo): si la muestra no coincidiera con lo dibujado dejaría
de enseñar el código y sería un adorno parecido.

Las líneas van en el color de la superficie y **cortan** el relleno en vez de
teñirlo. Por eso el rayado se lee igual en los dos temas, con cualquier
daltonismo y sobre papel en blanco y negro — comprobado con un filtro de escala
de grises sobre el módulo entero.

`T-04` no estaba marcado como multivaluado y lo es: 391 asignaciones sobre las
310 publicaciones que tienen algún ODS.

**Marca del valor esperado.** `I-05` mostraba cuatro recuentos —3, 34, 75, 210—
sin nada contra qué compararlos. Ahora cada umbral lleva el trazo de lo que
cabría esperar bajo el promedio mundial: por definición, el top *k* % de la
distribución mundial contiene el *k* % de las publicaciones. Se lee de un
vistazo que la institución queda **por debajo en el 1 %, el 5 % y el 10 %, y
por encima en el 25 %**. Usa el mismo ámbar que la línea de `I-04`, porque
ambas dicen lo mismo y aprenderlo una vez debe servir en todo el sitio.

Cuando lo esperable cae a la derecha de la barra, la cifra se corre más allá de
la marca: es el caso que más importa leer y taparlo lo volvería ilegible justo
ahí.

**Sello de procedencia.** Franja monoespaciada bajo cada gráfico con fuente,
corte, N y cobertura. El N **no es global**: 823 en producción, 816 en impacto,
1.207 apariciones firma × publicación en `P-07`. Publicar un denominador genérico
sería el error que este proyecto persigue.

Por debajo del umbral de cobertura declarado en `config/indicators.yml` el sello
cambia de registro y advierte. Dispara solo en `A-01` (72,3 %) y `T-04` (38 %).

`P-07` obligó a corregir su denominador: se calcula sobre pares autor ×
publicación, no sobre publicaciones, y con el denominador de config el sello
daba 94,1 % donde la auditoría mide 63,8 %.

### 12.7 Responsive

Tres cortes. Bajo **1040 px** el índice lateral deja de ser una columna fija y
pasa a una fila de pastillas desplazable sobre el contenido —no se oculta: es la
única vista general de la página—. Bajo **900 px** la cabecera **deja de ser
fija**: en un teléfono ocupa tres filas y fijarla se comía un tercio de la
pantalla en cada desplazamiento, que es peor que perder la referencia. Bajo
**640 px** baja el tamaño base, se compacta el espaciado, el conmutador de tema
pierde sus rótulos y conserva los iconos, y el titular abandona la rejilla
compartida de filas, que en una sola columna sólo abría un hueco.

Comprobado: **0 px de desborde horizontal** en 430 px y 860 px de ancho.

Hoja de impresión: oculta cabecera, filtros, paginación e índice lateral, evita
que los módulos se partan entre páginas y **despliega las dos vistas de cada
módulo** —la figura y la tabla—, porque en papel no hay conmutador. Los enlaces
externos imprimen su URL.

### 12.8 Advertencias de lectura

Además de la nota metodológica de cada indicador —que describe cómo se
*calcula*—, hay advertencias que describen cómo se *lee el gráfico*, y que sólo
existen mientras el gráfico sea ése. Viven en `paginas.js`, no en config:

- `I-01` **Citas por año**: las barras cuentan citas recibidas por las
  publicaciones de cada año. Un año reciente ha tenido menos tiempo para
  acumular citas, así que la caída del último año no indica menor impacto.
- `I-05` **Top de citación**: los umbrales son acumulativos y encajados; el top
  1 % también está contado en el 5 %, el 10 % y el 25 %.
- Cualquier indicador con `multivaluado: true` en `config/indicators.yml`
  declara junto al gráfico que las barras no son partes de un total.

---

## 13. Modelo de interfaz: qué se tomó de los portales del oficio

El rediseño no partió del gusto. Se revisaron plataformas que publican análisis
bibliométrico de instituciones de educación superior y se tomaron **patrones con
una razón detrás**, no apariencias.

| Patrón observado | Dónde | Qué resuelve | Cómo se implementó aquí |
|---|---|---|---|
| **Una serie, varias representaciones, y el lector elige** | CWTS Leiden Ranking: lista, dispersión y mapa sobre los mismos datos | La figura resume; la tabla es la que se cita. Decidir por el lector cuál es «la buena» le quita una de las dos | Conmutador **Gráfico ⇄ Tabla** en la cabecera de cada módulo |
| **La incertidumbre se muestra, no se esconde** | Leiden publica intervalos de estabilidad al 95 % junto a cada indicador | Un indicador puntual sugiere una precisión que el dato no tiene | Marca del **valor esperado** en `I-05`, línea de promedio mundial en `I-04`, y **sello de procedencia** con N y cobertura en todos |
| **Uso responsable como sección de primer nivel** | Leiden dedica una sección entera a cómo *no* usar el ranking | Publicar el número sin las condiciones de lectura es publicar media cosa | `Metodología` en la navegación principal, advertencias dentro del componente y notas de lectura por gráfico |
| **Panel de entidades fijo a la izquierda** | SciVal, módulo *Overview* | En una página de cinco indicadores largos hay que poder ver qué hay y saltar sin recorrerla entera | **Índice lateral fijo** con scroll-spy, colapsable a pastillas |
| **Agrupar indicadores en bloques con nombre** | SciVal agrupa en *Overall Research Performance*, *Research Topics*, *Performance Indicators* | Una lista plana de indicadores no tiene jerarquía | Páginas por eje (Producción, Impacto, Colaboración, Temática) y, en portada, *Indicadores de cabecera* / *Panorama* |
| **Abrir con la magnitud, no con el índice** | Perfil institucional de los portales de investigación | Hay que saber de qué tamaño es el objeto antes de que un desglose signifique algo | **Titular con tres cifras a tamaño display**: volumen, impacto normalizado y colaboración |
| **Cifras tabulares, alineadas a la derecha, rejilla recesiva** | Convención de tableros analíticos | Las columnas se comparan de un vistazo | `tabular-nums` en tablas, ejes y titular; `--red` y `--eje` como cromo recesivo |

Lo que **no** se copió, y por qué:

- **Mapa geográfico.** Leiden lo usa para comparar 1.500 universidades. Aquí hay
  una institución: un mapa de colaboración por país sería un adorno con dos
  docenas de puntos.
- **Dispersión de dos indicadores.** Tiene sentido para comparar entidades entre
  sí. Con una sola institución no hay nube que dibujar.
- **Nube de conceptos tipo *fingerprint*.** Requiere minería de texto sobre los
  documentos completos, que este proyecto no tiene, y produce una figura que se
  interpreta como si midiera algo. No se emula con datos que no la sostienen.

### 13.1 Cabecera de portada

**Sin cifras.** La cabecera anterior gastaba media pantalla en un título de tres
líneas, un párrafo de cuatro y tres cifras que el tablero repetía justo debajo.
En un explorador eso es ruido dos veces: gasta la pantalla que le toca al dato y
enseña una cifra del total mientras el lector mira un recorte, que es la manera
de que se lea la que no es.

Queda el nombre, la procedencia —que no es decorativa: dice de dónde salen las
cifras— y la explicación **detrás de un control**. Las cifras están donde deben,
en el tablero, y cambian con el recorte.

### 13.2 Conmutador Gráfico ⇄ Tabla

La tabla equivalente dejó de estar detrás de un `<details>` «Ver datos» y pasó a
ser la segunda vista, al mismo nivel que la figura. Cuando el indicador trae
valor esperado, la tabla gana columnas **Observado · Esperado · Diferencia**,
que es lo que convierte un recuento en un juicio.

**Sin JavaScript se muestran las dos vistas.** Es lo correcto: la tabla es la
vía equivalente al gráfico, no un extra. Lo decide una clase `js` escrita en
`<html>` antes de pintar; el conmutador sólo existe bajo esa clase, porque un
control que no conmuta nada es una promesa falsa.

---

## 14. Pre-renderizado

Hasta ahora `impacto.html` pesaba **1,3 KB** y su cuerpo era `<div id="modulos">`
vacío. Todo —cabecera, KPI, gráficos, tablas, sellos— aparecía después de
descargar dos módulos de JavaScript, resolver un `fetch` y dibujar veinte SVG.

Ahora `src/build/prerender.mjs` ejecuta **los mismos constructores de marcado**
bajo Node durante el build y deja el HTML escrito en `dist/*.html`.

**No hay una segunda implementación del marcado.** Los constructores viven en
`web/assets/js/vista.js` y no tocan el DOM: ni una lectura de `document`, ni un
`addEventListener`, ni un `localStorage`. Esa disciplina es la condición para
que el navegador y el build produzcan lo mismo. La interacción —conmutador,
scroll-spy, tooltip, filtros— sigue en `paginas.js`.

Cada contenedor rellenado se marca con `data-prerender="1"`; `paginas.js` lo
consulta y se salta el repintado, porque repintar destruiría un LCP que ya
ocurrió.

### 14.1 Qué se ganó, medido

Perfil *Slow 4G* (1,6 Mbps · 150 ms de latencia), Chromium. **Mediana de cinco
corridas por celda, con el rango observado**: una sola muestra en un contenedor
compartido es ruido —la primera medición publicada dio 776 ms y la siguiente
916 ms para la misma página—, así que la cifra suelta no era defendible.

| Página | LCP sin pre-render | LCP pre-renderizado | Mejora |
|---|---|---|---|
| `index` | 1.940 ms [1.904–1.956] | **780 ms** [772–796] | −60 % |
| `impacto` | 1.764 ms [1.748–1.808] | **784 ms** [780–812] | −56 % |
| `tematica` | 1.300 ms [1.296–1.320] | **756 ms** [752–764] | −42 % |

Con JavaScript **desactivado**, lo que queda en la página:

| Página | Antes | Después |
|---|---|---|
| `index` | 0 módulos · 0 gráficos · 23 caracteres | 3 módulos · 3 gráficos · 1.833 caracteres |
| `impacto` | 0 · 0 · 99 caracteres | 5 módulos · 5 gráficos · 5 tablas · 2.847 caracteres |
| `tematica` | 0 · 0 · 130 caracteres | 3 módulos · 3 gráficos · 3 tablas · 3.117 caracteres |

El coste es HTML más pesado (de 1,3 KB a 25–37 KB por página de sección) y está
pagado con creces: el sitio es citable, archivable e indexable sin ejecutar nada.

### 14.2 Qué NO se pre-renderiza

`publicaciones.html` y `autor.html` dependen del estado del usuario —filtros
aplicados, autor elegido por parámetro—. No hay un estado inicial único que
sirva, y emitir uno arbitrario sería inventar una vista.

Node es un requisito **blando**: si no está, el sitio se ensambla igual y
funciona igual mientras haya JavaScript en el cliente. Lo que se pierde se avisa
en voz alta durante el build, en vez de degradarse en silencio.

---

## 15. Verificación

Todo lo anterior está comprobado sobre el sitio construido, no sobre la hoja de
estilos:

| Comprobación | Alcance | Resultado |
|---|---|---|
| Contraste WCAG 2.1 (1.4.3 y 1.4.11) | 10 páginas × 2 temas, con composición alfa, paradas de degradado y exclusión de decoración | **0 fallos** |
| Sistema cromático | 36 pares, separación dato↔advertencia, rampa ordinal y par categórico bajo daltonismo, en `:root` y en cada ámbito de banda | **válido** |
| Estructura y consola | 10 páginas | **0 problemas** |
| Flujos interactivos | recorte, recálculo, URL, botón de volver, «Ver todo», conmutador, índice, glosario, buscador, enlaces antiguos | **0 fallos**, 0 excepciones de JavaScript |
| Desborde horizontal | 430 px y 860 px | **0 px** |
| Sitio sin JavaScript | `index`, `impacto`, `produccion`, `colaboracion`, `tematica` | cifras, gráficos, tablas y sellos presentes |
| Auditoría de datos | 30 reglas | 29 pasan, **0 bloqueantes fallando** |
| Barrera pública/interna | artefactos de `dist/` | **0 fallas** |

Tres de esas comprobaciones **se reformularon, no se debilitaron**, cuando la
interfaz cambió: la que buscaba el botón de ayuda en los KPI de la portada, la
que ligaba `EJES.md` con `id="modulos"`, y la de los filtros de publicaciones.
En los tres casos el flujo seguía existiendo con otra forma, y bajar la
comprobación habría dejado sin cubrir justo lo que se acababa de reescribir.

### 15.1 El presupuesto de peso, rehecho contra la evidencia

Los techos anteriores —CSS 55 KB, JavaScript 60 KB— estaban **excedidos desde
hacía dos rediseños sin que nada avisara**, porque vivían en una frase de este
documento. Se rehicieron con tres cambios, todos justificados por medición:

**1. Se miden con gzip, que es como viaja el contenido.** Los anteriores estaban
en bruto y se comparaban contra recomendaciones expresadas en comprimido, así
que declaraban excedido lo que no lo estaba. GitHub Pages, donde esto se
publica, sirve comprimido.

**2. Los techos son externos.** Se adopta la recomendación de presupuesto para
móvil de uso corriente: JavaScript < 150 KB y CSS < 60 KB con gzip. No los fija
quien tiene que cumplirlos.

**3. Se añade el techo que faltaba, el de DATOS**, que es lo que de verdad pesa
en este sitio: el explorador manda `publications.json` entero al navegador.

| | Comprimido | Techo | Uso |
|---|---|---|---|
| CSS | 22,4 KB | 60 KB | 37 % |
| JavaScript | 51,4 KB | 150 KB | 34 % |
| Datos | 204,3 KB | 250 KB | **82 %** |

#### Por qué el techo de datos puede ser tan alto

Porque el peso está **fuera de la ruta crítica de pintado**, y eso está medido,
no supuesto. El contenido llega pre-renderizado en el HTML y el JSON se descarga
después:

| Medición | Resultado | Umbral |
|---|---|---|
| LCP en *Slow 4G* | **916 ms** | 2.500 ms (Core Web Vitals) |
| Latencia al recortar el conjunto | **21–37 ms** | 200 ms (INP) |

Los dos con holgura de más del doble. El peso de los datos es el precio de la
arquitectura —cualquier pregunta se responde sin volver al servidor— y está
comprado con margen.

#### La decisión de no recortar el dataset

Seis campos de `publications.json` —`editorial`, `idioma`, `topic`,
`tipo_fuente`, `n_paises`, `n_instituciones`— **no los consume el explorador**.
Quitarlos ahorraría 28 KB comprimidos, un 17 %.

**No se quitan**, por dos razones:

- `publications.json` no es sólo el combustible del explorador: es el **dataset
  publicable** del informe. Quien lo descargue esperando los campos del corpus
  no debería encontrarse un recorte hecho para que una página cargue antes.
- El orden de prioridades del proyecto pone **integridad de datos (2) por
  encima de rendimiento (5)**, y aquí no hay conflicto real: el techo está en el
  82 % y el efecto medido está a menos de la mitad del umbral.

Queda **anotado como la palanca disponible** para cuando el techo apriete. Con
el corpus creciendo cada año, ese momento llegará; lo dirá la batería, no una
frase de este documento.

#### Y ahora es una compuerta, no una nota

[`src/verify/peso.mjs`](../src/verify/peso.mjs) corre **dentro de la batería**:
sólo lee archivos y los comprime, así que tarda menos de un segundo. Un
presupuesto escrito en prosa envejece en silencio — que es exactamente lo que
había pasado.

Subir un techo sigue siendo posible, pero es una **decisión** y no un arreglo: el
propio verificador lo dice al fallar, y obliga a declarar contra qué evidencia se
sube.

---|---|---|---|
| CSS | 75 KB | **22 KB** | 55 KB · **excedido** |
| JavaScript | 151 KB | **47 KB** | 60 KB · **excedido** |

Los dos techos se fijaron para un sitio que servía indicadores ya calculados.
El explorador cambió el trato: **`publications.json` viaja entero al navegador**
—699 KB, 823 registros con sus 28 campos— y a cambio cualquier pregunta se
responde sin volver al servidor. Un sitio que sólo pintaba series no necesitaba
ese peso; uno que se interroga, sí.

Cuatro cosas relevantes para juzgarlo, ninguna de las cuales lo resuelve:

- El **30 %** del JavaScript es comentario en prosa, que este proyecto trata
  como parte del entregable y no como sobra.
- El JavaScript es `type="module"`, o sea diferido, y con el sitio
  pre-renderizado **no está en la ruta crítica de pintado**: el contenido ya
  está en el HTML cuando llega.
- Con gzip, que es como viaja, son 47 y 22 KB.
- El coste real no es el código sino los datos, y ése es el precio de la
  arquitectura, no un descuido de implementación.

Queda **declarado como excedido, no como resuelto**. Los techos hay que
rehacerlos contra la arquitectura nueva en vez de arrastrar los de la anterior,
que medían otra cosa.

---

## 16. Sistema de diseño para Claude Design

`make kit` genera en `design-system/` un paquete de 16 fichas listo para
sincronizar con un proyecto de sistema de diseño en `claude.ai/design`.

### 16.1 Por qué se genera y no se escribe

Un sistema de diseño documentado a mano empieza siendo verdad y deja de serlo en
la primera corrección que alguien hace en `app.css` sin acordarse de la ficha.
Aquí cada ficha se construye desde las fuentes reales:

- **la hoja de estilo desplegable**, incrustada entera en cada ficha, de modo que
  la previsualización usa exactamente los estilos que se sirven;
- **los constructores de `core.js` y `vista.js`**, ejecutados bajo Node — los
  mismos que usa el pre-renderizador del sitio;
- **los artefactos de `data/processed/`**. Los componentes se enseñan con datos
  reales: un componente de bibliometría ilustrado con cifras inventadas
  contradice `<non_negotiable_rules>` incluso en una ficha de diseño;
- **las razones de contraste, calculadas al generar** a partir de los tokens
  leídos de la hoja. No se copian de ninguna tabla: una tabla copiada se
  desactualiza en silencio, un cálculo no.

El sistema de diseño no puede desactualizarse respecto del producto. Si
divergen, es que no se ha vuelto a generar.

### 16.2 Las fichas

| Grupo | Fichas |
|---|---|
| Fundamentos | Color · Tipografía · Espacio y trazo |
| Componentes | KPI · Titular de portada · Módulo · Conmutador Gráfico ⇄ Tabla · Sello de procedencia · Notas y advertencias · Índice lateral · Controles · Estados |
| Gráficos | Barras horizontales · Barras verticales · Anillo · Codificación por naturaleza del dato |

Cada ficha muestra **los dos temas uno al lado del otro**. El mecanismo: la
paleta usa `light-dark()`, que resuelve según el `color-scheme` del elemento
donde se sustituye la variable —no según el de la raíz—, así que basta declarar
`color-scheme: light` y `color-scheme: dark` en dos contenedores hermanos.
Comprobado en las 16 fichas: los fondos de los dos paneles difieren siempre.

### 16.3 Dos defectos que la verificación encontró

**Identificadores duplicados.** El generador construía el cuerpo una vez y lo
inyectaba en los dos paneles. Los patrones de trama se referencian por `id`, así
que el panel oscuro terminaba apuntando al patrón del claro. Se corrigió
evaluando el cuerpo **una vez por panel**.

**Una ficha que ilustraba una regla con un ejemplo que no la cumple.** La ficha
de codificación prometía trama, valor esperado y gris de ausencia, y usaba
`P-07` para las tres. Pero `P-07` **no es multivaluado** —comprobado en
`series.json`— y por tanto no lleva trama. Ahora cada afirmación trae el
indicador que de verdad la demuestra: `T-05` para la trama, `I-05` para el valor
esperado, `P-07` para el gris. Ponerle trama a `P-07` para que la ficha quedara
completa habría sido afirmar algo falso sobre el indicador.

### 16.4 Sincronización

**Procedimiento completo en [`DESIGN_SYNC_GUIDE.md`](DESIGN_SYNC_GUIDE.md)** —
requisitos, las dos vías de autorización, el protocolo `list → finalize_plan →
write`, la comprobación de capas antes de publicar, y qué hacer cuando un cambio
viene de Claude Design hacia el repositorio, que es el caso delicado.

El paquete requiere autorización de sistema de diseño, que **no se puede
conceder desde una sesión remota sin terminal interactiva**. Dos vías:

1. desde Claude Design, «Send to Claude Code Web», que siembra el proyecto en el
   espacio de trabajo;
2. Claude Code en una máquina local, donde `/design-login` sí abre.

Hecho eso, la sincronización es **incremental, componente a componente**, nunca
un reemplazo completo.

`design-system/` no se versiona, por la misma razón que `dist/`: es una salida
derivada, y cada regeneración produciría un diff de un megabyte de HTML
generado. Se reconstruye con `make kit`.
