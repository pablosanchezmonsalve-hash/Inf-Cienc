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

### 12.1 Paleta: qué se usó y qué no

La paleta de referencia entregada es
`#22577A` · `#38A3A5` · `#57CC99` · `#80ED99` · `#C7F9CC`. Se **midió antes de
aplicarla**, y la medición decide dónde va cada cosa.

| Uso | ¿Se aplica la paleta? | Por qué |
|---|---|---|
| Marca, cabecera, superficies | **Sí, literal** | `#22577A` da 7,74:1 sobre blanco; `#C7F9CC` da 6,58:1 sobre la marca |
| Estado interactivo | **Sí, con matiz** | `#38A3A5` da 3,02:1 sobre blanco: sirve para rellenos y bordes, no para texto de enlace. Los enlaces usan `#1a6d78` (6,0:1) |
| Escalas ordenadas | **Sí, es lo que mejor hace** | Rampa de un tono anclada en `#38A3A5`. Pasa las cuatro comprobaciones ordinales |
| **Series de datos** | **No** | Ver abajo |

**Por qué no sirve para series.** Medida como paleta categórica falla tres de
cinco comprobaciones:

- `#80ED99` vs `#57CC99` miden **ΔE 10,3 en visión normal**, bajo el piso de 15.
  Dos verdes que un lector *sin* daltonismo apenas distingue.
- `#C7F9CC` da **1,18:1** contra blanco: sobre una superficie clara no es una
  marca, es un fondo.
- Tres de los cinco tonos quedan fuera de la banda de luminosidad.

La causa es estructural, no de afinado: los cinco colores viven en la franja
cian-verde, que es justo donde la deuteranopía y la protanopía colapsan
diferencias. Ninguna paleta de datos honesta sale de ahí.

**Lo que hay en su lugar** es una paleta categórica de seis ranuras que *abre*
con el azul-teal de la referencia y luego se separa de verdad:

| # | Claro | Oscuro | Tono |
|---|---|---|---|
| 1 | `#0e7ea6` | `#2b9ec7` | azul-teal, hereda `#22577A` |
| 2 | `#e0662a` | `#d16a30` | naranja |
| 3 | `#7b52c9` | `#9078dd` | violeta |
| 4 | `#2fa36b` | `#2aa26a` | verde, hereda `#57CC99` |
| 5 | `#d4a017` | `#b58612` | ámbar |
| 6 | `#cc3f5c` | `#dc5c75` | carmín |

Pasa las cinco comprobaciones en ambos modos: peor par adyacente CVD ΔE 8,7
(claro) y 8,0 (oscuro); visión normal 19,3 y 16,2. **El orden de las ranuras es
el mecanismo de seguridad, no una decisión estética**: violeta se sitúa entre
naranja y verde precisamente porque naranja junto a verde caía en la banda de
aviso. Reordenar es lo único que lo arregla sin cambiar ningún color.

Sólo son **seis**. Una séptima obligaría a meter un tono en la franja que ya
ocupan otros; más allá de seis entidades lo correcto es agrupar en «Otras» o
separar en varios gráficos.

`#d4a017` queda en 2,38:1 contra blanco. Eso obliga a **relieve**: por eso todo
gráfico lleva etiqueta de valor visible junto a la marca y tabla equivalente
desplegable. El color nunca es el único canal de identidad.

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

Radios contenidos (6 px) y **sombra mínima**: la separación entre superficies la
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
superficie** (`#12222a`, un teal-pizarra, no un gris neutro), no una inversión.
Un detalle que lo justifica: `#57CC99` rinde 2,00:1 sobre blanco y 8,15:1 sobre
la superficie oscura. En modo oscuro **sí** puede ser color de acción; en claro
sería ilegible. Invertir una paleta validada no produce una paleta validada.

El selector de la cabecera tiene tres estados —automático, claro, oscuro—; el
automático sigue al sistema operativo. La elección se recuerda y se aplica antes
de pintar, con un script en línea en el `<head>`, para que no aparezca un
destello del tema equivocado.

**Un token no puede cambiar de oficio entre temas.** `--marca` es tinta en el
tema claro (`#22577A`) y superficie de cabecera en el oscuro (`#0d1e26`). Las
cifras grandes de los KPI lo usaban como color de texto: en claro daban 7,74:1
y en oscuro `#0d1e26` sobre `#12222a`, **1,05:1** — los seis números más
grandes de cada página, invisibles. Por eso existe `--cifra`, que es tinta en
los dos temas y sólo eso (`#22577A` / `#7fb4d8`, 7,74:1 y 7,32:1).

El fallo sobrevivió a una revisión de la paleta porque no está en la paleta:
los dos valores son correctos por separado y sólo el uso los enfrenta. Se
detecta midiendo el color computado contra el fondo compuesto, página por
página y tema por tema, no leyendo la hoja de estilos.

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
1.207 pares autor × publicación en `P-07`. Publicar un denominador genérico
sería el error que este proyecto persigue.

Por debajo del umbral de cobertura declarado en `config/indicators.yml` el sello
cambia de registro y advierte. Dispara solo en `A-01` (72,3 %) y `T-04` (38 %).

`P-07` obligó a corregir su denominador: se calcula sobre pares autor ×
publicación, no sobre publicaciones, y con el denominador de config el sello
daba 94,1 % donde la auditoría mide 63,8 %.

### 12.7 Responsive

Tres cortes. Bajo 900 px la navegación pasa a desplazamiento horizontal en una
línea en vez de romper en varias filas. Bajo 640 px baja el tamaño base, se
compacta el espaciado de tarjetas y tablas, y el subtítulo de marca pierde su
filete separador. Hay además una hoja de impresión que oculta cabecera, filtros
y paginación, y evita que los módulos se partan entre páginas.

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
