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
incluida la decisión de que el contexto metodológico extenso se pliegue tras un
control en vez de ocupar la pantalla que le toca al dato. La excepción es lo que
cada sección NO responde, que va a la vista (§4 bis).

---

## 2. Navegación general

```
Informe
├── Portada            → banda, tablero, cortes, dinámica anual, más citadas
├── Producción         → volumen, años, tipos, fuentes, unidades
├── Impacto            → citas, FWCI, percentiles, cuartiles de revista
├── Colaboración       → países, instituciones, tamaño de equipo, red
└── Áreas temáticas    → QS (entrada) → ASJC (detalle)
Datos
├── Autores            → listado → ficha individual
├── Publicaciones      → tabla completa filtrable
├── Fuentes externas   → obras fuera de Scopus (→ Producción ampliada)
└── Descarga de datos  → CSV de publicaciones e inventario de archivos
Sobre este informe
├── Indicadores        → catálogo, publicados o no
└── Metodología        → auditoría, fuentes, límites, glosario y ficha técnica
```

La navegación es una **barra lateral fija** con los tres grupos rotulados e
iconos, como la pantalla «Inicio» del diseño de Stitch (`D-611`). Lleva además
la marca, la ventana, los filtros activos, el tema y el enlace a la
documentación. Por debajo de 1040 px es un cajón que abre «Menú»: fija se come
la pantalla de un teléfono. Sobre el contenido, una **barra superior** con el
buscador global —un formulario GET a `publicaciones.html?q=`, que funciona sin
JavaScript (`D-618`)—, los años y «Descargar informe».

Profundidad máxima 3 niveles. Migas desde el nivel 2. `Metodología` está en la
barra lateral de todas las páginas, no enterrada en el pie.

---

## 3. Encabezado institucional

| Elemento | Contenido | Propósito |
|---|---|---|
| Identidad | Sigla y nombre institucional (desde `config/institution.yml`) | Atribución, arriba de la barra lateral |
| Título | «Informe Bibliométrico Institucional» | Contexto, bajo el nombre |
| Ventana | «Ventana Scopus · SciVal · 2020–2025 · citas al 2026-08-30» | Bajo la marca, en la barra lateral |
| **Barra de vigencia** | Migas, fuente, ventana y fecha de corte, cada una con su explicación desplegable | **Persistente en todas las páginas** |

La barra de vigencia es una decisión deliberada: es la única forma de que una
captura de pantalla del dashboard siga siendo interpretable fuera de contexto.
En papel imprime además el crédito completo y el recorte aplicado.

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

Medido sobre la carga anterior: 823 → 113 publicaciones al pedir Medicina
2024, con las seis cifras y los cuatro gráficos recalculados, y esas mismas 113
en la tabla al seguir el enlace.

### 4.2 Qué NO recalcula, y por qué

**Sobre un recorte el FWCI se informa por su mediana, no por su promedio.** El
promedio de los FWCI de las publicaciones de un conjunto *es* el FWCI de ese
conjunto según SciVal (*Research Metrics Guidebook*, 2019, §5.5.2), así que
calcularlo no inventa nada. Lo descarta su inestabilidad: la propia guía
advierte que con pocas publicaciones una o dos muy citadas lo inflan. Se informa
la **mediana** de los valores que la fuente ya asignó a cada publicación, y se
dice que es eso (`D-668`).

Los percentiles no se promedian: SciVal los agrega contando cuántas
publicaciones del conjunto entran en cada umbral (§5.5.3).

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

En la portada van en **rejilla bento**: las dos primeras a media fila y las
otras cuatro a un cuarto, sin reordenar el marcado (`D-633`). La jerarquía la da
el tamaño. Las secciones las conservan en fila.

Bajo el tablero y los cortes, la portada suma dos tablas que también responden
al recorte: **Dinámica anual** —año, publicaciones, % del recorte y citas, sin
media por año (`D-634`)— y **Publicaciones más citadas** (`I-07`), las diez con
más citas, sin autores ni cuartil (`D-637`). Esta última no se dibuja con recorte
a una persona (`D-638`). `coherencia.mjs` compara la tabla anual con P-02 e I-01.

Al recalcularse, la cifra que **cambió** parpadea una vez. Sin esa señal, un
filtro que mueve poco parece no haber hecho nada. Bajo
`prefers-reduced-motion` no ocurre.

El glosario contextual cuelga de las fichas. Vivía en los KPI de la portada
anterior y se habría perdido al sustituirlos; aquí hace más falta todavía,
porque **una cifra recalculada sobre un recorte se malinterpreta con más
facilidad que una del total**.

### 4.4 Los controles

Una **píldora `<details>` por dimensión**, en una tarjeta sobre el resultado,
con chips dentro. La elección del elemento no es estética: **un `details` se
abre y se lee sin JavaScript**, que es lo que permite que la garantía de la §14
siga en pie con un panel de filtros en la página.

Los filtros vivían en una columna a la izquierda del dato. Con la barra lateral
de navegación eran dos columnas de interfaz, y el dato quedaba en unos 740 px:
el explorador pasó a una columna (`D-613`). Se pierde ver causa y efecto lado a
lado; lo compensan los años en la barra superior, como grupo de botones con los
tres más recientes y «Todos» (`D-616`), y el bloque de filtros activos en la
barra lateral, siempre a la vista. Las píldoras nacen cerradas, su lista se
despliega a lo ancho de la tarjeta y la abierta sobrevive al repintado
(`D-614`).

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

Va **a la vista**, en una tarjeta junto al título: el título y lo que la
sección responde a un lado, y al otro «Qué NO dice esta sección», en la familia
de la advertencia metodológica (`D-641`). Es la estructura editorial del
«Dossier» de Stitch. Iba plegado tras un control, y una advertencia detrás de un
clic es una advertencia que casi nadie lee. Del Dossier se tomó la forma de su
tarjeta, no su texto (`D-642`).

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
| `P-02` Publicaciones por año | Barras verticales | Se eligió cuando la ventana tenía 3 puntos; desde 2020–2025 son 6 y esa razón ya no la sostiene |
| `P-03` Tipo documental | Barras horizontales | 10 categorías muy desbalanceadas |
| `P-05` Fuentes | Barras horizontales, top 15 | 713 fuentes: hay que recortar y decirlo |
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
| `T-05` / `T-01` / `T-04` | Barras horizontales | 271 ASJC: top 20 + acceso al resto |

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

El índice de cortes no tiene ya columna lateral donde fijarse: es **una fila de
píldoras en la tarjeta de filtros**, con su ancla y su scroll-spy (`D-615`).
Los cortes van como tarjetas de dos en dos, cada una con su código junto al
título, para ligarla con su fila del catálogo (`D-643`).

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
| Año | `anio` | 6 valores |
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

No se implementa búsqueda semántica ni ranking por relevancia: con 1.342
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

Si la publicación carece de métricas, la sección de impacto muestra «Sin
métricas disponibles: esta publicación no está en el export de SciVal», no un
cero ni un guion. El tratamiento sigue implementado y en esta carga no lo usa
ninguna publicación: las 1.342 del universo están todas en el export de SciVal.

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

Implementado en `web/assets/css/app.css`, hoja única, con el diseño del proyecto
de Stitch (`D-678`). Sin dependencias externas: fuentes e iconos se alojan en el
sitio, y ninguna hoja ni script se carga desde un CDN.

### 12.1 Paleta: la de Stitch, con el dato en una sola familia

La paleta vigente es la del proyecto de Stitch **«Institutional Scientific
Productivity Dashboard»**, aplicada **lo más fiel posible** por decisión del
usuario el 2026-09-17 (`D-678`). Revisa `D-610`, que había tomado de Stitch sólo
la estructura y conservaba la paleta vino y champán (`D-596`). Los valores base
son los de su configuración: `primary-container` `#00205b`, `secondary`
`#1c5fa8`, `accent-cobalt` `#2563eb`, `canvas-ground` `#f8fafc`,
`text-primary` `#0a0e14` y el «benchmark» esmeralda `#059669`.

| | Claro | Oscuro |
|---|---|---|
| Suelo · `--plano` | `#f8fafc` | `#0a1128` azul noche |
| Tarjeta · `--superficie` | `#ffffff` | `#111a33` |
| Tinta · `--tinta` | `#0a0e14` | `#e6ecf6` |
| Dato · `--serie-1` | `#00205b` azul marino | `#b2c5ff` |
| Marca · `--marca` | `#00205b` | `#00143d` |
| Botón · `--boton` | `#1c5fa8` | `#b2c5ff` |
| Advertencia · `--aviso-borde` | `#059669` esmeralda | `#34d399` |

**Stitch no define tema oscuro** —ninguna de sus pantallas tiene una sola clase
`dark:`—. El oscuro se **deriva** de su `inverse-surface`, `inverse-primary` y
`surface-dark`, y se mide igual que el claro.

**Tres valores de Stitch se movieron un paso**, porque no despejaban su umbral:

- el gris de ausencia (`missing-data` `#64748b`) medía 4,34:1 sobre la
  superficie secundaria y pasa a `#5e6e84`;
- el cuarto cuartil (`quartile-q4` `#60a5fa`) no llegaba a 3:1 como objeto
  gráfico sobre blanco y pasa a `#3b82f6`;
- el acento del tablero en oscuro quedaba a ΔE 18,2 del verde de advertencia,
  bajo el piso de 20, y pasa a `#a5b4fc`.

Tampoco es el color institucional oficial de la Universidad Finis Terrae, que
no se pudo verificar: son tokens, y el día que exista el hex oficial se cambian.

> **Genealogía.** Identidad roja → paleta institucional fijada por el usuario
> (`D-381`) → un índigo aplicado sin consultarle, registrado como incidente →
> vino y champán (`D-596`) → Stitch (`D-678`). Esta sección llegó a describir el
> índigo dos semanas después de retirado: una paleta entera correcta el día que
> se escribió y falsa desde el cambio siguiente.

#### Las razones de contraste, medidas

Las **calcula** `python3 src/design/validar_paleta.py` a partir de los tokens
que lee de la hoja. Esta tabla es la foto de una corrida —veredicto
`SISTEMA CROMÁTICO VÁLIDO`—, no una fuente: si discrepan, manda el validador.

| Token | Fondo | Claro | Oscuro | Piso |
|---|---|---|---|---|
| `--tinta` | `--superficie` | 19,34 | 14,51 | 4,5 |
| `--tinta-2` | `--superficie` | 10,35 | 10,55 | 4,5 |
| `--tinta-3` | `--superficie-2` | 5,58 | 6,95 | 4,5 |
| `--cifra` | `--superficie` | 15,47 | 13,76 | 3,0 |
| `--accion` | `--superficie` | 15,47 | 10,11 | 4,5 |
| `--serie-1` | `--superficie` | 15,47 | 10,11 | 3,0 |
| `--serie-2` | `--superficie` | 5,17 | 4,68 | 3,0 |
| `--sin-dato` | `--superficie` | 5,20 | 5,83 | 3,0 |
| `--ord-4` | `--superficie` | 3,68 | 4,68 | 3,0 |
| `--bento-acento` | `--plano` | 4,94 | 9,37 | 4,5 |
| `--boton-tinta` | `--boton` | 6,46 | 10,56 | 4,5 |
| `--marca-tinta` | `--marca` | 15,47 | 17,99 | 4,5 |
| `--aviso-tinta` | `--aviso-fondo` | 7,29 | 11,53 | 4,5 |

#### Las cuatro condiciones que el contraste solo no cubre

**Separación dato ↔ advertencia:** ΔE OKLab **37,5** en claro y
**20,4** en oscuro, sobre un piso de 20. El dato es azul marino y la
advertencia esmeralda: familias opuestas.

**Rampa ordinal Q1–Q4:** los cuartiles de Stitch en un solo tono, paso mínimo
ΔE **8,2** y **10,2** sobre un piso de 8, con
luminosidad monótona.

**Par categórico bajo daltonismo** (anillo `C-01`): peor caso ΔE
**29,1** en claro y **21,4** en oscuro, sobre un piso de 8.

**Celdas de mapa** (`--mapa-1..5`): paso mínimo entre vecinas ΔE
**7,7**, sobre un piso de 6. Son fijas y no invierten con el tema:
un mapa es una hoja de datos.

#### El validador estaba midiendo otra paleta

`validar_paleta.py` leía la hoja entera y se quedaba con la **última** aparición
de cada token. Desde que `.banda-contraste` redefine `--superficie`,
`--superficie-2` y `--plano` en su ámbito, esos valores pisaban los de `:root` y
el validador declaraba **12 fallos inexistentes**. Ahora lee sólo `:root`, y la
banda se mide como ámbito propio. Así aparecieron cuatro fallos reales: la banda
había olvidado redefinir la rampa ordinal y la tinta del botón, y `--ord-1`
llegó a medir 1,06:1.

### 12.2 Tipografía

**Tres familias de Stitch, alojadas en el sitio** (`D-678`):

| Familia | Papel | Dónde |
|---|---|---|
| **Inter** | interfaz y lectura | todo el texto |
| **JetBrains Mono** | rótulos «mono-seal», sellos, códigos | cabeceras de tabla, sellos, grupos de navegación, vigencia |
| **Newsreader** | serif editorial del Dossier | títulos de las secciones y de la metodología |

Se sirven desde `web/assets/fonts/` —Fontsource 5.3.0, subconjuntos latin y
latin-ext, licencia OFL, con sus licencias al lado—. **Nada se carga de un CDN**
(`D-30`): en la red cerrada de la institución una fuente de Google no llegaría y
el sitio se vería con otra letra. Con la cursiva y el griego de Inter pesan unos
350 KB. Usan `font-display: swap`: el texto se pinta con la fuente del sistema y
cambia a Inter al llegar, sin bloquear.

> **Las fuentes no se precargan, y está medido.** La primera versión precargaba
> Inter y JetBrains Mono en `_cabecera.html`. En *Slow 4G* el LCP de la portada
> subió de 1.708 a 2.224 ms: los 88 KB de la precarga competían con el HTML y
> la hoja por el mismo ancho de banda. Cambiar `swap` por `optional` no movía
> nada (2.180 ms); quitar la precarga, sí (1.796 ms). El precio visible es que el
> texto cambia de letra un instante al llegar la fuente.

La portada, los listados y la descarga de datos son superficies de **consulta** y
van en Inter, como en Stitch. La serif sólo entra donde el sitio se **lee**.

La escala es la de Stitch, en `rem`:

| Token | Valor | Nombre en Stitch |
|---|---|---|
| `--t-xs` | 13 px | caption-xs |
| `--t-s` | 15 px | body-table |
| `--t-m` | 16 px | controles |
| `--t-base` | 17 px | body-base |
| `--t-l` | 20 px | title-md |
| `--t-xl` | 24 px | title-lg |
| `--t-2xl` | 1,75–2,25 rem | headline-xl |
| `--t-cifra` | 2,5–3,5 rem | display-kpi |

**Todo en `rem`, nunca en `px`.** WCAG 1.4.4 exige que el texto llegue al 200 %
sin perder contenido ni función, y eso sólo se cumple si la escala entera cuelga
del tamaño raíz que el lector puede cambiar en su navegador. Los rótulos
«mono-seal» son la excepción visual que no lo es: 12 px escritos como `.75rem`.

Las cifras usan `tabular-nums`. En un explorador el número cambia a cada filtro,
y con cifras proporcionales el bloque entero salta a cada pulsación.

> **El texto dentro del SVG no heredaba la escala.** Son píxeles fijos en la
> hoja, así que se quedó a 11 px mientras el resto subía. Se movió a 13 — y con
> él el medidor de ancho de etiqueta de `core.js`, porque si esos dos números se
> separan las etiquetas se recortan donde no toca.

**Iconos.** Material Symbols Outlined, los mismos símbolos que usa Stitch para
cada destino. Sus trazos oficiales (Apache 2.0) están copiados en `core.js`: la
fuente de iconos se sirve desde un CDN.

### 12.3 Espacio y trazo

Escala de espacio de 4 px, de `--e1` (4 px) a `--e8` (72 px). Sin valores
sueltos fuera de la escala.

Radios de Stitch: `--radio-s` 4 px en códigos y sellos, `--radio-m` 8 px
(`rounded-lg`) en navegación, campos y botones, y `--radio` 12 px (`rounded-xl`)
en tarjetas. Las tarjetas KPI llevan la franja cobalto de 4 px de Stitch, y la
barra lateral y la superior se separan del contenido con una sombra suave, no
con un filete. La banda de la portada es el degradado azul marino del Cockpit.

### 12.4 Reglas de color en gráficos

El color codifica **una** de tres cosas, y cuál se declara en la llamada:

| `escala` | Cuándo | Ejemplo |
|---|---|---|
| (por defecto) | Una sola serie | Rankings por volumen: `P-03`, `P-05`, `C-03` |
| `'serie'` | Entidades distintas sin orden entre sí | Sin gráfico publicado que la use hoy — `C-01` se dibuja como barras horizontales de una sola serie (§5). Queda declarada en `colorDe()`/`SERIES` (core.js) para el próximo gráfico categórico que la necesite |
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
anidados —las 11 publicaciones del top 1 % están también en el top 5, 10 y 25— y
cuatro barras hermanas sugerían cuatro grupos disjuntos que podían sumarse. La
suma daba 524, una cifra sin significado.

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

El modo oscuro es una paleta **derivada y revalidada contra su propia
superficie**, no una inversión: Stitch no trae tema oscuro, y invertir una
paleta validada no produce una paleta validada.

- **Claro:** suelo `#f8fafc`, tarjetas blancas, tinta `#0a0e14`.
- **Oscuro:** suelo azul noche `#0a1128`, tarjetas `#111a33`, tinta `#e6ecf6`.

En los dos temas la tarjeta se levanta sobre el suelo, y no al revés: la
jerarquía de superficies es la misma y sólo cambia de registro.

El dato **cambia de valor pero no de familia**: azul marino `#00205b` en claro y
azul claro `#b2c5ff` en oscuro. Un lector que alterna de tema no debería tener
que reaprender qué significa el color.

El selector de la barra lateral tiene tres estados —automático, claro,
oscuro—; el automático sigue al sistema operativo. La elección se recuerda y se
aplica antes de pintar, para que la página no aparezca un instante con el tema
equivocado.

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

`T-04` no estaba marcado como multivaluado y lo es: 638 asignaciones sobre las
521 publicaciones que tienen algún ODS.

**Marca del valor esperado.** `I-05` mostraba cuatro recuentos —11, 53, 115 y
345— sin nada contra qué compararlos. Ahora cada umbral lleva el trazo de lo que
cabría esperar bajo el promedio mundial: por definición, el top *k* % de la
distribución mundial contiene el *k* % de las publicaciones. Se lee de un
vistazo que la institución queda **por debajo en el 1 %, el 5 % y el 10 %, y
por encima en el 25 %**. Usa el mismo verde de referencia que la línea de `I-04`
(`--aviso-tinta-grafico`), porque ambas dicen lo mismo y aprenderlo una vez debe
servir en todo el sitio. Era ámbar hasta la paleta H, que movió toda la familia
de la advertencia a verde moneda por la separación medida frente al dato
bordeaux (§12.1).

Cuando lo esperable cae a la derecha de la barra, la cifra se corre más allá de
la marca: es el caso que más importa leer y taparlo lo volvería ilegible justo
ahí.

**Sello de procedencia.** Franja monoespaciada bajo cada gráfico con fuente,
fecha, N y cobertura. La fecha es el corte que declara el export de la fuente;
el de Scopus no declara ninguno (`T-06`) y su sello rotula «Export» con la
fecha del export, no el corte de SciVal (`D-669`). El N **no es global**: 1.342 en producción y 1.342 en
impacto —que en esta carga coinciden, y no tienen por qué—, pero 1.962
apariciones firma × publicación en `P-07`. Publicar un denominador genérico
sería el error que este proyecto persigue.

Por debajo del umbral de cobertura declarado en `config/indicators.yml` el sello
cambia de registro y advierte. Dispara solo en `A-01` (70,3 %) y `T-04` (38,8 %).

`P-07` obligó a corregir su denominador: se calcula sobre pares autor ×
publicación, no sobre publicaciones, y con el denominador de config el sello
daba 94,1 % donde la auditoría mide 64,2 %.

### 12.7 Responsive

Tres cortes. Bajo **1040 px** la barra lateral de navegación deja de ser fija y
pasa a un cajón que abre «Menú», fuera del orden de tabulación mientras está
cerrado. El índice de cortes no cambia: ya es una fila de píldoras (§5.1). Bajo
**900 px** la barra superior **deja de ser fija** (`D-125`): en un teléfono
ocupa varias filas y fijarla se comía un tercio de la pantalla en cada
desplazamiento, que es peor que perder la referencia. Bajo
**640 px** baja el tamaño base, se compacta el espaciado, el conmutador de tema
pierde sus rótulos y conserva los iconos, y el titular abandona la rejilla
compartida de filas, que en una sola columna sólo abría un hueco.

Comprobado: **0 px de desborde horizontal** en 430 px y 860 px de ancho.

Hoja de impresión: oculta cabecera, filtros, paginación e índice de cortes, evita
que los módulos se partan entre páginas y **despliega las dos vistas de cada
módulo** —la figura y la tabla—, porque en papel no hay conmutador. Los enlaces
externos imprimen su URL.

### 12.7 bis El informe descargable

Se descarga por dos vías y **una sola maquetación**. El botón «Descargar
informe», en la barra de vigencia, es `window.print()`: el navegador ya pagina,
embebe tipografías y produce texto seleccionable, y una librería de PDF costaría
entre 300 KB y 1 MB para, o rasterizar el texto, o obligar a reescribir el
informe en su API de maquetación. La otra vía es `make informe`
(`src/build/informe_pdf.mjs`), que abre las mismas páginas de `dist/` con la
misma hoja y pide el PDF al navegador; existe porque el botón resuelve a quien
mira una sección y no un informe completo, idéntico en cada carga y archivable.
Deja fuera las superficies de consulta —publicaciones, autores, ficha,
catálogo—: son tablas paginadas y volcarlas produciría un anexo de cientos de
páginas. Quien las quiera las exporta en CSV.

La hoja **declara sobre qué está medida**, porque un PDF archivado no tiene el
sitio al lado. La primera hoja abre con dos líneas que en pantalla no existen:
la de crédito —institución, fuentes, ventana y fecha de corte de las citas— y la
del recorte, que dice qué filtros están aplicados y sobre cuántas publicaciones,
o que no hay ninguno y es el informe completo. El pie añade el universo y sus
tres denominadores (`D-16`). El bloque de recorte de la pantalla no se imprime:
trae controles que en una hoja no llevan a ninguna parte.

**El informe por persona.** `autor` es una dimensión de filtro más, con los
nombres canónicos que el corpus ya trae. No se dibuja como las demás: 829
pastillas no son un filtro, así que el panel enseña las firmas elegidas y un
campo con autocompletado, y la entrada natural es el enlace de cada ficha.
Cuando el recorte es de una persona, sobre las cifras aparecen las salvaguardas
—la advertencia de lectura que adhiere a DORA y al Manifiesto de Leiden, y la
de muestra reducida por debajo del umbral—, con la misma redacción que la
ficha y no una copia. Se ofrece a las 829 entidades, no sólo a las 68 que
superan el umbral: `docs/INFORME_POR_INVESTIGADOR.md` explica por qué.

Dos cortes cambian de significado sobre una sola persona y se tratan distinto.
La **red de coautoría se apaga** y declara por qué: recortada a una firma es una
estrella, no una estructura de colaboración, y con quién coautoró está en su
ficha. La **mediana por año se queda con un aviso** que dice sobre cuántas
publicaciones se calcula: es una cifra correcta sobre pocos valores, y ocultarla
dejaría un hueco que se leería como ausencia de dato.

### Elegir gráficos, independiente de la sección

Los dieciocho gráficos del informe viven repartidos en cuatro secciones, y desde
una sección sólo se ven los suyos. El **catálogo de indicadores** es la única
página donde están todos juntos, así que es donde se eligen: una casilla por
gráfico, y una barra que dice cuántos van y ofrece dos salidas, el informe en
pantalla y la orden para el PDF.

La selección viaja como `grafico=I-04|T-05` **junto al recorte y con la misma
gramática**, así que se comparte, se cita y se descarga igual. Cada sección
dibuja sólo los suyos que estén elegidos, y la que se queda sin ninguno lo dice
en vez de aparecer vacía. En el PDF, las secciones sin figuras elegidas no se
imprimen; la portada y el anexo metodológico sí, siempre.

**No es un recorte, y la hoja lo distingue.** Un filtro cambia *qué
publicaciones se cuentan*; una selección cambia *qué figuras se muestran*. Por
eso `grafico` no es una dimensión —no filtra datos, no tiene facetas y no
aparece en la frase del recorte— y se declara en su propia línea: «Selección: 2
de los 17 gráficos del informe. Las cifras no cambian». Sin esa distinción, una
hoja con dos figuras se leería como un informe medido sobre una submuestra que
no existe.

La vista de escuelas no se elige aparte: es la misma `P-07` un nivel más abajo,
así que viene con ella. Tiene lectura propia porque son dos figuras, pero no es
otro indicador.

**El informe a medida.** `make informe RECORTE="anio=2024&tipo=Article"` toma la
misma consulta que el explorador escribe en la URL —se copia de la barra de
direcciones— y la pasa a cada sección: las cifras, los gráficos y las tablas se
recalculan sobre ese recorte, que es lo que el sitio ya hacía en pantalla. El
recorte va en el nombre del archivo y, sobre todo, declarado en la hoja 1. El
anexo metodológico también lo declara, sin cifras: no cuenta publicaciones,
pero es parte del informe que alguien pidió y una hoja suelta que se llame
«informe completo» contradiría a las demás del mismo PDF. Si el recorte es de
una persona (`RECORTE="autor=Firma"`), su ficha abre el informe: es lo único
que declara identidad, ORCID con la evidencia de cada asignación y unidad.

### El bloque de gráfico en papel

Cada gráfico del informe descargado es **una unidad de lectura de cinco partes**,
y las cinco caben en la misma hoja:

| | Parte | De dónde sale |
|---|---|---|
| 1 | Título del corte | `vista_explorador.js`, tabla `SECCIONES` |
| 2 | La figura | el mismo SVG de la pantalla, con tope de 90 mm de alto |
| 3 | La tabla equivalente | la figura en cifras, con su encabezado repetido si se parte |
| 4 | **Qué muestra** y **Cuidado** | `docs/LECTURAS.md` y la advertencia del catálogo |
| 5 | El sello | fuente, fecha de corte o de export, N y cobertura **del recorte** |

**Qué muestra** es la pieza que faltaba, y va en los dos medios. La línea dice
qué cuenta cada barra, cada punto o cada segmento, y sobre qué. Vive en
`docs/LECTURAS.md`, se serializa a `lecturas.json` y **el build se detiene** si
una figura se queda sin ella o si sobra una que ninguna figura usa.

Nació `solo-papel`, con este argumento: en pantalla la ayuda contextual, el
glosario y el panel de la sección están a un clic, y en el PDF no hay nada. El
argumento era cierto y la conclusión estaba mal. «A un clic» es la parte que
falla: quien no entiende un gráfico no siempre sabe que no lo entiende, y menos
aún qué término buscar. La ayuda escondida sirve a quien ya sospecha; la frase
junto a la figura sirve a quien la mira por primera vez, que es el caso normal
de alguien que llega a un tablero bibliométrico desde su propia disciplina. El
resultado práctico era que el sitio, la superficie que casi todo el mundo usa,
era la única donde el gráfico no se explicaba.

Un texto, dos presentaciones: pie de figura en pantalla, bloque compacto en
papel. La hoja de estilo resuelve la diferencia y `docs/LECTURAS.md` sigue
siendo el único sitio donde se escribe.

**Las seis cifras del tablero también la llevan.** La ficha ya declaraba su
denominador —sobre cuántas publicaciones está medida— y cuatro de las seis
tenían botón de glosario. Faltaba lo otro: qué ES la cifra. «Citas por
publicación 4,82» es el caso que lo justifica: sin una frase al lado, un
promedio que unas pocas publicaciones muy citadas levantan para todas se lee
como la publicación típica. La línea va bajo el denominador, separada por un
filete, en cuerpo pequeño: acompaña a la cifra, no compite con ella. Medido
después: el LCP de la portada no se movió y en papel las seis fichas siguen
cabiendo en una hoja.

**La compuerta cubre TODA figura y TODA cifra, no sólo los cortes.** El treemap y el mapa de
calor de producción se montan aparte, desde `paginas.js`, y quedaban fuera: el
mapa llevaba su explicación escrita a mano en el HTML y el treemap tenía un
párrafo de explicación **vacío** que nadie rellenaba —la figura más difícil de
leer del sitio, sin una frase que dijera qué mide un rectángulo, y sin nada que
lo denunciara—. Ahora la compuerta lee las figuras bento del marcado de las
páginas (`id="…-contenedor"`) en vez de una lista escrita a mano, así que
cualquiera que se añada entra sola.

**Cuidado** es la advertencia que el catálogo ya publica para ese indicador, y
sólo se muestra si el corte no trae un aviso propio: dos textos sobre lo mismo
se leen como dos advertencias distintas.

**Que quepan no fue gratis.** Con el interlineado de pantalla, las 21 filas de
«Áreas temáticas» ocupaban una hoja entera y empujaban fuera de la página la
explicación y el sello del gráfico al que pertenecen. En papel la tabla baja a
8 pt con 1,5 pt de aire por celda, el sello pierde su marco de tarjeta y la
figura tiene tope de alto. Medido a ancho de A4: **ningún bloque supera una
hoja** en las cuatro secciones ni en la portada.

**La red de coautoría imprime una sola vista.** En pantalla el lector elige
entre nodos, matriz, arcos y la tabla de pares; en papel se desplegaban las
cuatro, y la tabla —una fila por par de firmas que coautoró— convertía la
sección de colaboración en 49 hojas. Se imprime la vista de nodos, y la hoja
declara qué se quedó en el sitio. Es el mismo criterio por el que el informe no
vuelca publicaciones ni autores.

**Qué llega al papel y qué no.** Los desplegables se imprimen abiertos: un
`<details>` cerrado imprime su resumen y nada más, y eso vaciaba el panel «Qué
NO dice esta sección» —el título de la advertencia sin la advertencia—. El
conmutador Gráfico ⇄ Tabla no se imprime, porque en papel las dos vistas se
despliegan y el control no conmuta nada. Todo esto lo comprueba
`src/verify/impresion.mjs` **sobre el texto del PDF**, no sobre el DOM: con el
medio `print` emulado, el cuerpo de un desplegable cerrado devuelve una caja de
109 px de alto y aun así no aparece en el documento.

**Accesibilidad del documento.** `make informe` pide el PDF etiquetado, con
árbol de estructura para lectores de pantalla. El botón del navegador depende
de los ajustes de quien imprime, que el sitio no controla.

**La carátula.** La hoja 1 traía el titular de la página web: «Informe
bibliométrico», la procedencia en letra chica y el desplegable de método.
Servía, pero se leía como el borde superior de un sitio, no como la carátula de
un documento que alguien va a archivar, citar o mandar por correo. Ahora la
hoja 1 es una carátula: institución, título, **alcance**, ventana, y una tabla
de procedencia con las cuatro fechas que definen la carga.

Lo que añade y no estaba en el papel: el alcance arriba y en grande —un informe
recortado a una facultad se distinguía de otro sólo por una línea de 8 pt—, la
fecha de **exportación** de los datos, que no se imprimía en ninguna parte, y
la fecha en que se generó **ese** PDF, que tampoco.

El alcance no se redacta en el generador: se **lee** del párrafo que la propia
página escribe con el recorte ya aplicado (`fraseRecorte`, en `core.js`). Una
segunda redacción del mismo hecho acaba divergiendo, y aquí una de las dos
mentiría sobre qué publicaciones sostienen el informe.

Las cuatro bases de cálculo —universo, con métricas, con autoría, con área—
sólo se imprimen en el informe **completo**. Sobre un recorte engañan: bajo
«46 de 823 publicaciones» se leerían como el suelo de ese informe, que no lo
son. Ahí la línea de alcance ya dice sobre cuántas descansa, y cada cifra
declara la suya dentro.

Con carátula se apagan, sólo en ese archivo, el titular de la página y la barra
de crédito: dicen lo mismo, más corto y una hoja después. Las demás secciones
la conservan, porque una hoja suelta tiene que seguir diciendo de qué informe
salió. El aviso de ventana —«lo publicado después no está aquí»— **no** se
apaga: la carátula da los años, no la advertencia.

El orden de la portada es carátula · índice · qué mide. Puesto el índice
después del titular, su `break-before: page` dejaba el desplegable de método
solo en una hoja con cuatro líneas.

**El folio y el índice.** El PDF que genera `make informe` numera sus hojas
—«Informe bibliométrico · Producción» a la izquierda, «Hoja 3 de 8» a la
derecha— y abre con un índice: cada sección con su archivo y su número de
hojas, y bajo ella cada gráfico con su código, su título y la hoja en la que
cae. Los números de hoja **se leen del PDF ya compuesto**, buscando el título
de cada figura página por página, por la misma razón por la que la compuerta de
impresión lee el PDF y no el DOM: el navegador miente sobre el papel. Eso
resuelve gratis la selección de gráficos —lo que no se dibujó no aparece— y
permite una autocomprobación: sin selección, un gráfico declarado que no
aparezca en su PDF significa que su título cambió y la búsqueda dejó de casar,
y el generador lo dice por su código.

Las dos cosas viven en el generador porque Chromium no implementa los cuadros
de margen de CSS Paged Media y el botón del navegador no puede saber en qué
hoja cae nada; su maqueta sí está en `app.css` (`.indice-informe`), que sigue
siendo el único sitio donde se decide cómo se ve el papel. El precio es que la
portada se compone dos veces: una para que existan las demás secciones y otra
ya con el índice.

**El sitio lo ofrece hecho.** El despliegue compone el informe dentro del
`dist/` que publica —después de verificarlo, con el Chromium que la batería ya
instaló— y la portada muestra un bloque con los seis archivos y sus hojas. Los
PDF no se versionan: son un derivado del sitio y comitearlos habría metido
megabytes de binarios por carga de datos, además del hueco de siempre —datos
nuevos, informe viejo, un PDF que contradice a sus propias páginas—.

El bloque se dibuja SÓLO si existe `data/informe.json`, el manifiesto que deja
la corrida que compuso los PDF. Enlaces escritos a mano en el HTML habrían
apuntado a archivos que pueden no estar. El ensamblado deja el manifiesto vacío,
así que la ausencia del informe es un bloque que no aparece y no un 404 en la
consola de cada visita. Y si el informe se compuso con datos más viejos que los
del sitio, el bloque lo declara en vez de callarlo.

**Límite conocido:** las líneas de procedencia van en la primera hoja, no en
cada una. Chromium no implementa los cuadros de margen de CSS Paged Media, así
que un encabezado repetido tendría que inyectarse desde `informe_pdf.mjs` y
dejaría de valer para el botón del navegador.

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
| **Panel de entidades fijo a la izquierda** | SciVal, módulo *Overview* | En una página de cinco indicadores largos hay que poder ver qué hay y saltar sin recorrerla entera | **Barra lateral fija** con la navegación agrupada; el índice de cortes, en píldoras con scroll-spy (§5.1) |
| **Agrupar indicadores en bloques con nombre** | SciVal agrupa en *Overall Research Performance*, *Research Topics*, *Performance Indicators* | Una lista plana de indicadores no tiene jerarquía | Páginas por eje (Producción, Impacto, Colaboración, Temática) y, en portada, *Indicadores de cabecera* / *Panorama* |
| **Abrir con la magnitud, no con el índice** | Perfil institucional de los portales de investigación | Hay que saber de qué tamaño es el objeto antes de que un desglose signifique algo | **Tablero de seis fichas en bento** justo bajo la banda, recalculado con el recorte (§4.3). La banda no lleva cifras (§13.1) |
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

**Una banda «Cockpit» sin cifras** (`D-631`). Toma la estructura de la pantalla
«Cockpit» de Stitch sobre la paleta invertida de `.banda-contraste`, ya medida:
título, institución, el aviso de ventana de citación y un recuadro «No cambia
con el recorte» con fuentes, ventana y fecha de corte.

Una cabecera anterior gastaba media pantalla en tres cifras que el tablero
repetía justo debajo. En un explorador eso es ruido dos veces: gasta la pantalla
que le toca al dato y enseña una cifra del total mientras el lector mira un
recorte, que es la manera de que se lea la que no es. Por eso tampoco va el
universo (`D-632`): la línea de estado lo dice justo debajo. Las cifras están
donde deben, en el tablero, y cambian con el recorte.

En papel la banda se imprime en tinta sobre blanco, y reinicia también los
tokens de aviso, acción y cifra: la advertencia de ventana, que vive dentro,
habría salido verde claro sobre blanco (`D-640`).

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
| `index` | 3.636 ms [3.608–3.656] | **1.796 ms** [1.764–1.812] | −51 % |
| `impacto` | 3.624 ms [3.600–3.644] | **1.804 ms** [1.760–1.812] | −50 % |
| `tematica` | 3.652 ms [3.624–3.660] | **1.800 ms** [1.772–1.852] | −51 % |

Medido el 2026-09-17 con el diseño de Stitch y sus fuentes alojadas. Las cifras
absolutas cambian de una máquina a otra —la primera medición publicada dio
780 ms de portada, la del 2026-09-16 1.708— porque el entorno donde se mide no
es el mismo y su carga varía; lo comparable es la columna de mejora y la
relación entre páginas, que se miden en la misma corrida.

> **Una medición no vale si comparte máquina.** La del 2026-09-17 se repitió
> tres veces: con dos revisores usando el navegador en paralelo, la portada dio
> 2.136 ms, y en Windows un servidor de una corrida anterior seguía escuchando
> en el mismo puerto. Sólo cuenta la corrida con los puertos libres y sin otra
> carga.

**El bloque de descarga del informe casi duplicó el LCP de la portada, y por eso
está donde está.** Puesto bajo el titular, medía 3.156 ms contra 1.420 ms, y el
elemento de mayor pintado era su propio párrafo. La causa es estructural y no se
arregla optimizando: el bloque **no puede pre-renderizarse**, porque su
manifiesto no existe cuando se escribe la página, así que siempre pinta tarde,
después del guion y de dos peticiones. Arriba y grande, eso lo convierte en el
elemento que define el LCP; abajo del pliegue no es candidato. Medido con el
mismo sitio servido dos veces, la única diferencia el manifiesto lleno o vacío.

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
| Auditoría de datos | 30 reglas | 27 pasan · 3 fallan, **0 bloqueantes fallando** |
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
| CSS | 39,9 KB | 60 KB | 67 % |
| JavaScript | 82,7 KB | 150 KB | 55 % |
| Datos | 370,8 KB | 450 KB | 82 % |

El techo de datos **subió de 300 a 450 KB** con la carga 2020–2025 (`D-587`).
No es un techo externo, y su propia procedencia lo dice: CSS y JavaScript citan
una recomendación de presupuesto para móvil; datos dice «techo propio». La regla
con que se fijó las dos veces anteriores es **1,21 veces lo medido** —250 sobre
204,3 y 300 sobre 247,7—, y aplicarla a los 370,8 de hoy da 450. Se aplicó la
regla, no se derogó.

**La próxima vez no se sube** (`D-589`). Una tercera aplicación del 1,21x
convierte el techo en una función del corpus: sube siempre y deja de restringir.
La salida ya está medida y no cuesta ningún dato: recodificar
`publications.json` en columnas con diccionario de cadenas deja el grupo en
**265,8 KB** —105 menos— y la rehidratación devuelve el texto original byte a
byte.

**Qué mide esa suma** (`D-591`): los quince artefactos raíz de `dist/data/`, que
ninguna página pide juntos. La página más pesada pide 328,0 KB y la ficha de
autor 316,0. Es una **cota superior** del peso de datos de cualquier página, no
el peso de ninguna. Las 829 fichas de autor quedan fuera a propósito: suman
995,8 KB entre todas, pero la mayor pesa 6,5 KB y ninguna página carga más de
una.

#### Por qué el techo de datos puede ser tan alto

Porque el peso está **fuera de la ruta crítica de pintado**, y eso está medido,
no supuesto. El contenido llega pre-renderizado en el HTML y el JSON se descarga
después:

| Medición | Resultado | Umbral |
|---|---|---|
| LCP en *Slow 4G*, portada | **1.796 ms** | 2.500 ms (Core Web Vitals) |
| LCP en *Slow 4G*, impacto | 1.804 ms | 2.500 ms |
| LCP en *Slow 4G*, temática | 1.800 ms | 2.500 ms |
| Latencia al recortar el conjunto | **21–37 ms** | 200 ms (INP) |

Las tres cifras de LCP son del 2026-09-17, con el diseño de Stitch y sus fuentes
(§14.1); el margen sobre el umbral es del 28 %. La latencia, del 2026-09-10 sobre
el corpus de **1.342 publicaciones**, no sobre el anterior: subir un techo
citando una medición vieja es el defecto que `peso.mjs` existe para impedir
(`D-588`). Con las 823 de julio el LCP era de 1.424 ms, y **duplicar el corpus
costó 172 ms**; el diseño de Stitch, con sus fuentes, unos 90 ms más medidos en
la misma máquina. El peso de los datos es el precio de la arquitectura —cualquier pregunta
se responde sin volver al servidor— y está comprado con margen.

#### La decisión de no recortar el dataset

**Cinco** campos de `publications.json` —`editorial`, `idioma`, `topic`,
`tipo_fuente`, `n_instituciones`— no los consume nada: ni el explorador, ni el
generador del informe en PDF, ni el CSV que descarga el usuario, ni los otros
catorce artefactos, ni las 829 fichas de autor.

> **Corrección del 2026-09-10.** Este documento listaba seis e incluía
> `n_paises`. Es falso: `n_paises` es la décima columna del CSV que descarga el
> usuario (`web/assets/js/paginas.js:634`). Quien hubiera accionado la palanca
> fiándose de esta lista habría roto la descarga pública en silencio.

**No se quitan**, por tres razones. Las dos primeras ya estaban:

- `publications.json` no es sólo el combustible del explorador: es el **dataset
  publicable** del informe. Quien lo descargue esperando los campos del corpus
  no debería encontrarse un recorte hecho para que una página cargue antes.
- El orden de prioridades del proyecto pone **integridad de datos (2) por
  encima de rendimiento (5)**.

La tercera es la que cierra el asunto, y es una medición, no un argumento:

- **La palanca no llega.** Quitar los tres campos sin ningún consumo deja el
  grupo en **329,4 KB** comprimidos, un 110 % del techo; ampliarlo a los cinco,
  en **325,3 KB**, un 108 %. La compuerta sigue en rojo y el despliegue sigue
  detenido. Los 47 KB que este documento anotaba eran una estimación sobre el
  peso **en bruto**: medido tras comprimir, el recorte de los tres vale 41,3 KB
  de los 70,7 que harían falta. Son campos de altísima repetición —`Journal`
  1.342 veces, editoriales y topics repetidos— y **gzip ya colapsaba casi todo
  ese peso**: 167 KB en bruto valen 41,3 comprimidos.

Recortar el dataset publicable **y seguir excediendo el techo** es el peor de
los dos mundos: se pierde dato y no se desbloquea nada. La palanca queda
**declarada agotada**, con su cifra, para que nadie vuelva a anotarla como
disponible. Lo que sí resuelve el exceso está en la sección siguiente.

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
—1.429 KB, 1.342 registros con sus 29 campos— y a cambio cualquier pregunta se
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
