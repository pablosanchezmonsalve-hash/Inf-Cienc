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
una nota al pie. Un KPI sin su denominador y su fecha de corte está incompleto.

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

## 4. Panel de KPIs

Seis tarjetas, orden fijo. Cada una: valor, etiqueta, denominador, icono de
información con tooltip.

| KPI | Valor | Denominador visible | Tooltip |
|---|---|---|---|
| Publicaciones | 823 | 2023–2025 | Qué cuenta y qué no |
| Citas | 3.935 | 816 con métrica | Fuente y corte |
| Citas/publicación | 4,82 | 816 | Tipos incluidos |
| FWCI | 0,87 · mediana 0,41 | 816 | **Qué significa 1,0** |
| Colab. internacional | 51,2 % | 816 | Definición (>1 país) |
| Autores UFT | 589 | firmas, no personas | **Por qué firmas** |

**Decisiones de diseño:**

- El FWCI muestra **media y mediana juntas**. Mostrar sólo la media (0,87)
  ocultaría que la mediana es 0,41 y sugeriría un desempeño más uniforme del
  real.
- «589 firmas» en vez de «589 investigadores». La etiqueta honesta es más larga
  y peor de leer; se prefiere igual.
- Ningún KPI usa flecha de tendencia: con 3 años y sin datos previos, una
  flecha implicaría una tendencia que los datos no sostienen.

---

## 5. Módulos analíticos

| Módulo | Visualización | Pregunta que responde | Por qué esa forma |
|---|---|---|---|
| **Producción anual** | Barras verticales, 3 barras | ¿Cuánto se publica por año? | Barras y no línea: 3 puntos no son una serie temporal |
| **Tipo documental** | Barras horizontales ordenadas | ¿Qué se publica? | 10 categorías muy desbalanceadas (595 vs 2); barras horizontales legibles |
| **Ranking de fuentes** | Tabla ordenable, top 20 + «ver todas» | ¿Dónde se publica? | 495 fuentes: tabla, no gráfico |
| **Citas** | Barras por año + total | ¿Cuánto se cita? | Con advertencia de ventana de citación |
| **FWCI** | Indicador + histograma de distribución | ¿Cuál es el impacto normalizado? | El histograma es lo que revela la asimetría; el número solo la esconde |
| **Top percentiles** | Barras: top 1/5/10/25 % | ¿Cuánta producción destacada? | 4 categorías anidadas, comparación directa |
| **Cuartil de revista** | Barras apiladas Q1–Q4 + «sin dato» | ¿En qué revistas se publica? | **«Sin dato» visible**, no excluido del 100 % |
| **Colaboración internacional** | Anillo + valor | ¿Cuánta colaboración externa? | Proporción binaria: el anillo funciona |
| **Países colaboradores** | Barras horizontales top 15 | ¿Con quién se colabora? | Mapa descartado: 23 países, un mapa mundial sería casi vacío |
| **Instituciones** | Tabla ordenable | ¿Con qué instituciones? | Nombres largos; tabla legible |
| **Tamaño de equipo** | Histograma | ¿Cuántos autores por publicación? | Media 7 / mediana 5: la distribución es el dato |
| **Áreas QS** | Barras, 5 categorías | ¿En qué grandes áreas? | Vista de entrada |
| **Áreas ASJC** | Barras horizontales top 20 | ¿En qué disciplinas? | 249 categorías: top 20 + acceso al resto |
| **Unidades académicas** | Barras + **banda de advertencia** | ¿Cómo se distribuye internamente? | Cobertura 63,8 % y sesgo disciplinar: la advertencia es obligatoria |
| **Ranking de autores** | Tabla ordenable y paginada | ¿Quién publica más? | 589 filas |

**Descartado:** mapa coroplético de colaboración (23 países sobre ~200 → mapa
mayoritariamente vacío que exagera visualmente la dispersión), nube de palabras
(sin lectura cuantitativa), gráfico de torta para ASJC (multivaluado: los
porcentajes no suman 100 %).

---

## 6. Filtros

| Filtro | Tipo | Origen | Notas |
|---|---|---|---|
| Año | Botones múltiples | `anio` | 3 valores |
| Tipo documental | Multi-select | `tipo_documental` | 10 valores |
| Área QS | Multi-select | QS area | 5 valores |
| Área ASJC | Buscador + multi-select | ASJC | 249 valores: requiere búsqueda |
| Unidad académica | Multi-select | `unidad_academica` | Incluye «No determinada» como opción real |
| Acceso abierto | Multi-select | `Open Access` | Incluye «Sin dato declarado» |
| Colaboración internacional | Toggle | derivado | Sí/No |
| Autor | Autocompletado | tabla maestra | 589 entradas |
| Texto libre | Input con debounce 250 ms | título, fuente | — |

### Reglas de comportamiento

1. **AND entre filtros, OR dentro de un filtro.** Convención estándar; se
   documenta en la interfaz.
2. **Recuento en cada faceta**, calculado sobre los demás filtros activos.
3. **Facetas con 0 resultados se muestran deshabilitadas**, no se ocultan: su
   ausencia es información.
4. **`No determinada` y `Sin dato declarado` son opciones seleccionables.**
   Consecuencia directa de la decisión D-09: no imputar.
5. **Persistencia en URL** (query string). Es `<v1_scope_desirable>` y su coste
   es bajo; permite compartir una vista filtrada.
6. **Los filtros que reducen el denominador lo declaran.** Al filtrar por área
   temática, el conteo base pasa de 823 a 816: la interfaz lo indica en vez de
   dejar que el usuario note una inconsistencia.
7. **Chips de filtros activos** siempre visibles, con opción de limpiar.

---

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

## 11. Responsive

Prioridad de contenido en pantallas estrechas: KPIs → módulo actual → filtros
en panel desplegable. Las tablas anchas scrollean horizontalmente dentro de su
contenedor; la página nunca scrollea en horizontal.

---

## 12. Sistema visual

Implementado en `web/assets/css/app.css`, hoja única. Sin dependencias externas:
ninguna fuente, hoja ni script se carga desde un CDN.

### 12.1 Paleta: de dónde sale cada color

**La identidad es roja.** El sistema anterior era teal-azul (`#22577A` ·
`#38A3A5` · …); se sustituyó por decisión del proyecto. Lo que hizo el cambio
viable sin reabrir todo el diseño es un hecho medido: **el sitio usa un solo
color de dato**, así que cambiarlo no obliga a revalidar un conjunto categórico.

**El rojo no es el rojo institucional oficial de la UFT.** No se pudo verificar
su valor exacto —`finis.cl` y los directorios de marca respondieron 403— y ante
la duda **no se inventó**. Los tonos están *diseñados por medición*. El día que
exista el hex oficial se cambia `--marca` y sus derivados: son tokens, no
literales repartidos por la hoja.

Cada token despeja un umbral comprobable, medido en los **dos** temas:

| Token | Fondo | Claro | Oscuro | Piso |
|---|---|---|---|---|
| `--tinta` | `--superficie` | 18,54 | 15,57 | 4,5 (WCAG 1.4.3) |
| `--tinta-2` | `--superficie` | 8,28 | 8,47 | 4,5 |
| `--tinta-3` | `--superficie-2` | 5,73 | 5,64 | 4,5 |
| `--cifra` | `--superficie` | 9,10 | 8,16 | 3,0 (texto grande) |
| `--accion` | `--superficie` | 7,67 | 7,88 | 4,5 |
| `--accion` | `--superficie-2` | 6,71 | 7,26 | 4,5 |
| `--serie-1` | `--superficie` | 7,67 | 5,48 | 3,0 (WCAG 1.4.11) |
| `--sin-dato` | `--superficie` | 3,90 | 3,71 | 3,0 |
| `--ord-1` … `--ord-4` | `--superficie` | 14,80 … 3,53 | 12,33 … 3,17 | 3,0 |
| `--marca-tinta` | `--marca` | 8,26 | 10,29 | 4,5 |
| blanco | `--marca` | 10,88 | 17,73 | 4,5 |
| `--aviso-tinta` | `--aviso-fondo` | 8,74 | 11,75 | 4,5 |

Dos condiciones que el contraste solo no cubre:

**Separación dato ↔ advertencia.** El dato es rojo y la advertencia metodológica
es ámbar: dos familias cálidas contiguas podrían confundirse. Medido en OKLab
entre `--serie-1` y `--aviso-borde` —el par que de verdad se dibuja junto, barra
de dato contra línea de referencia—: ΔE **25,1** en claro y **24,1** en oscuro,
sobre un piso de 20.

> **Corrección.** Una versión anterior publicaba 28,6 y 21,2. Estaban medidas
> contra `#d9a520`, que era `--aviso-tinta-grafico` de la paleta teal anterior y
> ya no existe en la hoja. Con el valor real, el tema oscuro daba **17,9 y no
> cumplía**: `--aviso-borde` en oscuro era `#c8901a`, un resto de la paleta teal
> que sobrevivió al cambio de identidad sin que nadie lo mirara. Contra un dato
> teal la separación sobraba; contra un dato rojo, no. Lo encontró
> [`src/design/validar_paleta.py`](../src/design/validar_paleta.py), que lee los
> tokens de la hoja en vez de creerse una tabla. Corregido a `#f0b429`.

**Rampa ordinal (Q1–Q4).** Un solo tono en cuatro pasos con luminosidad
monótona; paso mínimo ΔE **10,5** y **11,3**, sobre un piso de 8. Cuatro tonos
distintos habrían afirmado que Q1 y Q4 no tienen relación entre sí, cuando son
posiciones de una misma escala.

**Superficie oscura cálida.** El tema oscuro pasó de pizarra fría (`#12222a`) a
pizarra cálida (`#171214`). Un rojo sobre fondo azulado se lee sucio: el fondo
tira del tono hacia el magenta.

#### Series categóricas: qué se dibuja de verdad

De las seis ranuras declaradas, **el sitio dibuja dos**: el anillo de `C-01`
pide escala categórica y gasta `--serie-1` y `--serie-2`. Todo lo demás cae en
`--serie-1` sola o en la rampa ordinal.

> Corrección. Una versión anterior de esta documentación afirmaba que «ningún
> módulo pide `escala: 'serie'`» y que el sitio usaba una sola ranura. Era
> **falso**: `anillo()` pide siempre escala de serie, así que la segunda ranura
> llevaba dibujándose desde el principio. Queda anotado porque una paleta
> declarada sin usar y una paleta en uso sin validar son problemas distintos, y
> sólo el segundo es urgente.

El par en uso **sí** está validado, y como par, que es como se dibuja:

| Medida | Claro | Oscuro | Piso |
|---|---|---|---|
| Contraste `--serie-1` / `--serie-2` | 7,67 y 5,77 | 5,48 y 7,50 | 3,0 |
| ΔE visión normal | 25,9 | 26,6 | — |
| ΔE protanopía | 17,5 | 17,9 | 8 |
| **ΔE deuteranopía** | **12,2** | **12,1** | **8** ← peor caso |
| ΔE tritanopía | 32,4 | 33,1 | 8 |

Las **cuatro restantes** siguen reservadas y **sin validar**: nunca se han
dibujado juntas. Quien las estrene debe revalidarlas *para el número de ranuras
que vaya a usar*, no para seis. La sexta era carmín y se cambió por azul: con la
marca en rojo, un carmín a dos pasos de `--serie-1` es una trampa a la espera.

#### Una sola declaración por token

La paleta oscura estaba escrita **tres veces** —en el `@media`, en el selector
explícito y en los comentarios— y las tres copias podían separarse sin que nada
avisara. Ahora cada token se declara una vez con `light-dark()` y el conmutador
de tema sólo cambia `color-scheme`. Son unas 90 líneas menos y **un modo entero
de error menos**.

### 12.2 Tipografía

**Pila del sistema, no fuente web.** El proyecto prohíbe cargar nada desde un
CDN, y autoalojar una familia añadiría binarios al repositorio y peso al bundle
por una mejora que no cambia ninguna lectura analítica. La jerarquía se
construye con peso, tamaño, interletrado y cifras tabulares.

| Rol | Token | Tratamiento |
|---|---|---|
| Interfaz y prosa | `--f-ui` | `system-ui` con respaldos. Interletrado negativo creciente con el tamaño |
| Cifras | `--f-cifra` | Misma pila. `tabular-nums` **sólo** donde deben alinearse en columna |
| Identificadores | `--f-mono` | `ui-monospace`. Códigos de indicador, ORCID, DOI |

Escala: `--t-xs` 11 px (códigos) · `--t-s` 12,5 px (notas) · `--t-m` 14 px
(tablas y controles) · `--t-base` 16 px (prosa) · `--t-xl` 19 px (h2) ·
`--t-2xl` y `--t-cifra` fluidos con `clamp()`.

Un detalle deliberado: las cifras tabulares se reservan a tablas, ejes y
tooltips. En un KPI suelto las proporcionales se leen mejor, y forzar la
tabulación ahí sólo separa los dígitos sin ganar nada.

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
superficie** (`#171214`, pizarra cálida, no un gris neutro), no una inversión.
Invertir una paleta validada no produce una paleta validada.

El selector de la cabecera tiene tres estados —automático, claro, oscuro—; el
automático sigue al sistema operativo. La elección se recuerda y se aplica antes
de pintar, con un script en línea en el `<head>`, para que no aparezca un
destello del tema equivocado.

**Un token no puede cambiar de oficio entre temas.** `--marca` es tinta en el
tema claro y superficie de cabecera en el oscuro. Las cifras grandes de los KPI
lo usaban como color de texto: en claro daban 7,74:1 y en oscuro **1,05:1** —los
números más grandes de cada página, invisibles—. Por eso existe `--cifra`, que
es tinta en los dos temas y sólo eso.

El fallo sobrevivió a una revisión de la paleta porque no está en la paleta: los
dos valores son correctos por separado y sólo el uso los enfrenta. Se detecta
midiendo el color computado contra el fondo compuesto, página por página y tema
por tema, no leyendo la hoja de estilos.

El mismo fallo, con otra cara, obligó a crear `--boton-tinta`: el botón primario
llevaba texto blanco fijo sobre `--accion`. En claro es un rojo hondo y el
blanco da 7,67:1; en oscuro el mismo token se aclara a un rosa y el blanco
caería a 2,84:1. La tinta del botón cambia con el tema, igual que su fondo.

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

### 13.1 Titular de portada

Tres indicadores, no seis: un titular con seis cifras no tiene titular. Son
`P-01` (cuánto se produce), `I-03` (con qué impacto normalizado) y `C-01` (con
quién se colabora) — los tres ejes que el proyecto declara.

Cada cifra arrastra **su** denominador y, si la tiene, su referencia: un 0,87 de
FWCI sin el «1 = promedio mundial» al lado no es un titular, es un número
suelto. Los tres suben al titular y **bajan de la rejilla de KPI**: un indicador
repetido a cuatro centímetros de sí mismo no gana énfasis, lo pierde.

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
| Desborde horizontal | 430 px y 860 px | **0 px** |
| Sitio sin JavaScript | `index`, `impacto`, `tematica` | módulos, gráficos, tablas y sellos presentes |
| LCP | *Slow 4G*, mediana de 5 corridas | 756–784 ms (presupuesto: < 2.000 ms) |
| Auditoría de datos | 29 reglas | 28 pasan, 0 bloqueantes fallando |
| Barrera pública/interna | artefactos de `dist/` | 0 fallas |

**Presupuestos.** CSS **51,4 KB** en bruto (15,2 KB con gzip), dentro del techo
de 55 KB. JavaScript **72,1 KB** en bruto, **por encima** del techo de 60 KB
declarado; con gzip son **23,7 KB**. Dos cosas relevantes para juzgarlo: el
28 % del JavaScript es comentario en prosa, que este proyecto trata como parte
del entregable, y con el sitio pre-renderizado el JavaScript ya **no está en la
ruta crítica de pintado** —es `type="module"`, o sea diferido, y el contenido ya
está en el HTML—. Queda declarado como excedido, no como resuelto.

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
