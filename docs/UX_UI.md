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

Implementado en `web/assets/css/app.css`. Sin dependencias externas: ninguna
fuente, hoja ni script se carga desde un CDN.

### Tokens

Todo el color pasa por variables CSS. Cambiar la identidad visual no requiere
tocar ningún componente.

| Grupo | Variables | Para qué |
|---|---|---|
| Superficies | `--plano`, `--superficie`, `--superficie-2/3` | Página, tarjetas, fondos secundarios |
| Tinta | `--tinta`, `--tinta-2`, `--tinta-3` | Texto principal, secundario y apagado (ejes, metadatos) |
| Marca | `--marca`, `--marca-2` | Identidad institucional. Nunca codifica un dato |
| Acento | `--acento`, `--acento-suave` | Estado interactivo. Nunca codifica un dato |
| Series | `--serie-1` … `--serie-8` | Paleta categórica, orden fijo |
| Ordinal | `--ord-1` … `--ord-4` | Rampa de un solo tono para escalas ordenadas |
| Ausencia | `--sin-dato` | Gris. Toda categoría que representa ausencia de dato |
| Aviso | `--aviso-*` | Advertencia metodológica. Ámbar, distinto de toda serie |

### Modo claro y oscuro

El modo oscuro es una paleta **elegida**, no una inversión: las ocho series
están re-escalonadas para la superficie oscura. El selector de la cabecera tiene
tres estados —automático, claro, oscuro— y el automático sigue al sistema
operativo. La elección se recuerda y se aplica antes de pintar, con un script en
línea en el `<head>`, para que no aparezca un destello del tema equivocado.

### Reglas de color en gráficos

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

### Validación de daltonismo

La paleta categórica se validó con la herramienta de la habilidad `dataviz`
contra las superficies reales del sitio:

- **Claro** (`#ffffff`): banda de luminosidad, piso de croma, separación CVD
  (peor par adyacente ΔE 9,1) y piso de visión normal (ΔE 19,6) pasan. Tres
  series quedan bajo 3:1 de contraste.
- **Oscuro** (`#12151c`): las cinco comprobaciones pasan, contraste incluido.

El contraste bajo en modo claro obliga a **relieve**: por eso todo gráfico lleva
etiqueta de valor visible junto a la marca y una tabla equivalente desplegable.
El color nunca es el único canal de identidad.

### Advertencias de lectura

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
