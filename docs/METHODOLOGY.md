# Nota metodológica

**Capa:** pública · **Fase:** 1 · **Última actualización:** 2026-08-26

Este documento fija los criterios que gobiernan todo cálculo publicado por la
plataforma. Cualquier indicador que los contradiga no debe publicarse.

---

## 1. Unidad de análisis y unidad de atribución

La **publicación** es la unidad de análisis. El **autor afiliado** es la unidad
de atribución. No son intercambiables.

El conteo completo (*full counting*) atribuye una publicación entera a cada
autor UFT participante. Por eso la suma de publicaciones por autor (1.205) es
mayor que el total de publicaciones del universo (823): una publicación con
tres autores UFT aparece tres veces. **Esa suma no es un total institucional.**

Convención adoptada:

| Contexto | Método de conteo |
|---|---|
| KPIs institucionales | publicaciones únicas (conteo entero) |
| Rankings de autor | conteo completo, declarado como tal |
| Participación institucional | `% part. UFT` = autores UFT / autores totales, métrica separada |

## 2. La afiliación pertenece al par autor × publicación

Un autor puede firmar con la UFT en una publicación y con otra institución en
otra. La afiliación **no** es un atributo fijo de la persona.

Consecuencia estructural: el modelo de datos incluye una entidad puente
`Autoria`, y es ahí donde vive la afiliación. La tabla maestra de autores no
tiene columna «facultad»; tiene la lista de unidades observadas y su recuento.
En la auditoría, 24 autores presentan más de una unidad académica entre sus
publicaciones. Eso se declara, no se colapsa.

## 3. Cobertura no es realidad

Scopus indexa una parte de la producción académica, y esa parte no es uniforme
entre disciplinas. Humanidades, ciencias sociales, libros y revistas locales
chilenas están sistemáticamente subrepresentados.

En este corpus el efecto es medible: Medicina concentra 527 de los 770 pares
autor × publicación con unidad identificada, mientras Derecho registra 6 y
Arquitectura y Diseño 3. **Esa diferencia no mide productividad relativa**: mide
productividad indexada en Scopus.

Toda comparación entre unidades académicas debe mostrar esta advertencia.

## 4. Ventanas cortas hacen inestables las métricas normalizadas

El corpus cubre 2023–2025 con corte de citas al **22 de julio de 2026**. Las
publicaciones de 2025 acumulan entre 7 y 19 meses de citación.

Consecuencias operativas:

- El FWCI de una publicación reciente tiene varianza muy alta.
- 538 de los 589 autores tienen menos de 5 publicaciones en la ventana. A ese
  n, las métricas normalizadas individuales no son interpretables.
- El **FWCI de un conjunto se calcula sobre el conjunto**, nunca como promedio
  de los FWCI individuales.

Conforme a **DORA** y al **Manifiesto de Leiden**, toda métrica normalizada
mostrada a nivel individual va acompañada de n, ventana temporal y advertencia
explícita, o no se muestra.

## 5. h-index en ventana ≠ h-index

Con datos de 2023–2025 solamente puede calcularse un h-index restringido a esa
ventana. **No es el h-index de carrera** y presentarlo como tal sería engañoso.
Se etiqueta siempre «h-index en ventana 2023–2025».

## 6. Clasificación temática: de la revista o del documento, nunca del contenido

- **ASJC** clasifica la **fuente**, no el artículo.
- Los **Topics** de SciVal son clústeres de co-citación asignados al documento:
  mejor granularidad, pero siguen siendo una construcción de Elsevier.
- La **prominencia** de un Topic mide la atención del campo, **no** el
  desempeño de la UFT en él.

Toda visualización temática declara qué esquema usa. Las áreas son
multivaluadas: la suma por área excede el total de publicaciones y no debe
presentarse como partición.

## 7. Métricas de revista no son métricas de artículo

SNIP, CiteScore y SJR describen la **fuente** en el año de publicación. Se
modelan en una entidad separada (`MetricaFuente`) precisamente para que no se
confundan con el desempeño del trabajo individual. El percentil de
SJR/CiteScore es la vía defendible para hablar de «cuartil»; nunca como
indicador de calidad del artículo.

## 7 bis. Semántica del percentil de citación — determinada empíricamente y confirmada documentalmente (`T-13` cerrado, 2026-08-26)

El campo `percentil_citacion` viene de la columna **"Outputs in Top Citation
Percentiles, per percentile"** del export de SciVal (`src/audit/02_reconcile_sources.py`).
**No venía con su dirección declarada en el export en sí**: no había forma de
saber, sólo mirando el archivo, si 1 es la mejor posición o la peor. Todo el
indicador `I-05` («publicaciones en el top 10 %») depende de acertar, y
equivocarse lo invierte por completo.

### La evidencia empírica (original, 2026-08-03)

Medida sobre los propios datos (n = 816). Monótona en los dos extremos:

| Publicaciones | Citas | Percentil observado |
|---|---|---|
| Las 5 más citadas | 115 · 77 · 52 · 46 · 45 | **1 · 2 · 3 · 4 · 2** |
| Todas las no citadas | 0 | **78** (el máximo del rango) |

Correlaciones: **−0,66** con el recuento de citas y **−0,58** con el FWCI. El
rango observado es 1–78.

### La confirmación documental (2026-08-26)

`T-13` pedía contrastar esto contra documentación oficial de Elsevier, no sólo
contra los datos propios. Dos hallazgos, buscados por separado para no
confundirlos:

1. **El nombre de columna es real**, confirmado por una herramienta de
   terceros que procesa exports de SciVal de verdad
   ([cu-library/scival-export-tools](https://github.com/cu-library/scival-export-tools),
   subcomando "Per Researcher"), no sólo por lo que trae el archivo del
   proyecto.
2. **La metodología del percentil, documentada por Elsevier**: para la
   métrica «Outputs in Top Citation Percentiles», las publicaciones globales
   de Scopus se ordenan de mayor a menor citación (o FWCI, si está
   field-weighted) y se dividen en 100 percentiles; el campo indica en cuál
   de los umbrales de **top 1 %, 5 %, 10 % o 25 % más citadas** cae cada
   publicación (Elsevier, [SciVal Support Center — "Outputs in Top Citation
   Percentiles"](https://service.elsevier.com/app/answers/detail/a_id/28193/supporthub/scival/p/10961/)).

   **Por qué esto no es circular con la evidencia empírica**: la semántica
   «top X %» de Elsevier no deja ambigüedad posible sobre la dirección —
   «estar en el top 1 %» sólo puede significar la posición más alta, nunca la
   más baja. Que el campo se llame igual que esta métrica, y que las 5
   publicaciones más citadas del corpus caigan justo en los valores más bajos
   (1–4) mientras las no citadas caen en el máximo observado (78), es
   exactamente el patrón que esa semántica predice — no una coincidencia que
   necesitara la métrica para explicarse.

   **Salvedad que sigue abierta**: no se encontró una tabla oficial que diga
   literalmente «valor = 1 → top 1 %» fila por fila para esta columna
   específica de exportación (distinta de la métrica agregada del mismo
   nombre, que cuenta publicaciones en vez de etiquetar cada una). La
   confirmación es sobre la metodología del campo, no una cita textual del
   mapeo exacto valor-a-porcentaje.

**Conclusión: el valor menor es la mejor posición.** El campo expresa «top X %»,
y por eso `I-05` cuenta las publicaciones con percentil ≤ 10. Ya no se declara
como determinada sólo por medición: la medición y la documentación oficial
apuntan en la misma dirección. La medición es reproducible: la ejecuta
`src/analysis/indicator_feasibility.py`.

## 8. Visibilidad no es impacto

`Views` y `Field-Weighted View Impact` miden visualizaciones en Scopus.
Se reportan por separado de las citas y nunca como sinónimo de impacto.

## 9. Trazabilidad

Todo indicador publicado declara: **fuente, fecha de corte, ventana temporal, n
y método de conteo**. El registro de fuentes vive en `config/sources.yml` y es
parte del entregable, no documentación accesoria.

## 10. Reglas de matching y conciliación son capa interna

La detección institucional, las variantes de nombre, las ambigüedades de
identidad y los duplicados probables se registran en `internal/`. No se
publican por defecto. Lo que se publica es el resultado validado y la
declaración de sus límites, no el proceso de depuración.

---

## Referencias metodológicas

- San Francisco Declaration on Research Assessment (DORA).
- Hicks, D., Wouters, P., Waltman, L., de Rijcke, S., Rafols, I. (2015).
  *Bibliometrics: The Leiden Manifesto for research metrics*. Nature 520.
- Aria, M., Cuccurullo, C. (2017). *bibliometrix: An R-tool for comprehensive
  science mapping analysis*. Journal of Informetrics 11(4).
- Documentación oficial de Scopus y SciVal (Elsevier) sobre FWCI, SNIP,
  CiteScore, SJR y Topic Prominence.
