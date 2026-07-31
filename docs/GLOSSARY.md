# Glosario y ayuda contextual

**Capa:** pública · **Fase:** 2

Fuente de los tooltips de la interfaz. Se serializa a `glossary.json` en Fase 3.

**Criterio de uso:** tooltip sólo en métricas no triviales. «Publicaciones
totales» no lleva tooltip; FWCI, percentiles y cuartiles sí. Un tooltip en todo
es equivalente a ninguno.

Cada entrada tiene un texto corto (tooltip, ≤ 200 caracteres) y uno extendido
(glosario).

---

## FWCI — Field-Weighted Citation Impact

**Corto:** Citas recibidas frente a las esperadas para publicaciones del mismo
campo, año y tipo. 1,0 = promedio mundial.

**Extendido:** Compara las citas observadas con las esperadas de un conjunto de
referencia mundial equivalente. Un valor de 1,0 significa exactamente el
promedio mundial; 0,5, la mitad.

Se calcula **sobre el conjunto completo**, no promediando los FWCI
individuales. Es inestable con pocas publicaciones o ventanas cortas: no debe
usarse para comparar personas.

En este informe: media **0,87**, mediana **0,41** sobre 816 publicaciones. La
diferencia entre ambas indica una distribución muy asimétrica — unas pocas
publicaciones muy citadas elevan la media.

---

## Percentil de citación / Top 10 %

**Corto:** Posición de la publicación entre las más citadas de su campo. Menor
es mejor: el top 10 % son las más citadas.

**Extendido:** Cada publicación recibe un percentil según sus citas dentro de
su campo y año. El «top 10 %» agrupa las que están en el decil más citado.

En un conjunto sin sesgo, ~10 % de las publicaciones caen en el top 10 %. Aquí
son **75 de 816 (9,2 %)**.

---

## SJR, CiteScore, SNIP — métricas de revista

**Corto:** Miden la revista donde se publicó, **no el artículo**. Una revista
de alto percentil publica artículos de impacto muy variable.

**Extendido:**
- **SJR** pondera las citas según el prestigio de la fuente que cita.
- **CiteScore** es el promedio de citas por documento de la revista.
- **SNIP** normaliza por la propensión a citar del campo.

Los tres describen la **fuente**. Atribuir la posición de la revista al mérito
de un artículo concreto es el error que DORA identifica explícitamente.

---

## Cuartil Q1

**Corto:** La revista está entre el 25 % de mayor percentil de su categoría.
Describe la revista, no el artículo.

**Extendido:** Se calcula con el percentil SJR del año de publicación: Q1 =
percentil ≤ 25. Cobertura **762 de 816** publicaciones; las restantes no tienen
percentil SJR y se muestran como «sin dato», no como Q4.

---

## Colaboración internacional

**Corto:** Publicaciones con autores de más de un país. Aquí: 51,2 %.

**Extendido:** Cuenta países distintos entre las afiliaciones. No mide la
intensidad ni la calidad de la colaboración: una publicación con un coautor
extranjero y otra con quince cuentan igual.

---

## ASJC — All Science Journal Classification

**Corto:** Clasificación temática de la **revista**, no del artículo. Una
publicación puede estar en varias áreas.

**Extendido:** Elsevier clasifica cada fuente en una o más de 249 categorías.
Como es multivaluada, **las asignaciones (1.796) superan a las publicaciones
(816)** y los porcentajes no suman 100 %.

Que un artículo esté en «General Medicine» significa que su revista está
clasificada así, no que ese sea su tema exacto.

---

## Topic y prominencia temática

**Corto:** Clúster de artículos que se citan entre sí. La prominencia mide la
atención del campo, **no** el desempeño de la institución.

**Extendido:** Los Topics agrupan documentos por patrones de co-citación. Se
asignan al documento, no a la revista, y por eso son más precisos que ASJC.

La **prominencia** combina citas, visualizaciones y financiamiento recientes
del *topic*. Un topic muy prominente indica un área con mucha actividad
mundial; no dice nada sobre la calidad del trabajo institucional en ella.

---

## h-index en ventana 2023–2025

**Corto:** h publicaciones con al menos h citas, **contando sólo 2023–2025**.
No es el h-index de carrera.

**Extendido:** Restringido a la ventana del informe, es sistemáticamente mucho
menor que el h-index de trayectoria completa. Con 3 años, **497 de 589 firmas
tienen h ≤ 1**: el indicador casi no discrimina.

Se muestra sólo en fichas con 5 o más publicaciones, y siempre etiquetado «en
ventana».

---

## Acceso abierto

**Corto:** Estado OA declarado por Scopus. La ausencia de valor no significa
«no es OA».

**Extendido:** Disponible en **590 de 816** publicaciones (72,3 %). Tipos: Gold,
Green, Hybrid gold, Bronze; una publicación puede tener varios.

Las 226 sin valor se muestran como «sin dato declarado», no como acceso
cerrado.

---

## ODS — Objetivos de Desarrollo Sostenible

**Corto:** Mapeo de la publicación a los ODS de Naciones Unidas. Sólo 38 % del
corpus tiene ODS asignado.

**Extendido:** Con cobertura del 38 %, se reporta como **recuento** de
publicaciones con ODS asignado, nunca como distribución porcentual del total:
eso implicaría que el 62 % restante no se relaciona con ningún ODS, lo cual no
está establecido.

---

## Conteo completo

**Corto:** Cada autor UFT recibe la publicación entera. Por eso la suma por
autor supera el total institucional.

**Extendido:** Una publicación con 3 autores UFT aporta 1 a cada uno. La suma de
publicaciones por autor (**1.205**) excede el total de publicaciones
(**823**). Es correcto y esperado: **esa suma no es un total institucional**.

---

## Formas de firma vs. personas

**Corto:** 589 formas de firma detectadas. El número de personas distintas es
menor: hay variantes de nombre sin consolidar.

**Extendido:** Sin un identificador persistente como ORCID —ausente en las
fuentes— no es posible afirmar que dos variantes son la misma persona. 123
firmas comparten apellido base con otra variante y 20 nombres tienen más de un
Scopus Author ID.

Estas ambigüedades se declaran sin resolver: consolidarlas por similitud de
nombre produciría fusiones erróneas entre homónimos.

---

## Fecha de corte

**Corto:** Las citas están actualizadas al 22 de julio de 2026. Un corte
posterior daría cifras mayores.

**Extendido:** Las citas se acumulan continuamente. Toda cifra de impacto es
válida sólo respecto de su corte. Las publicaciones de 2025 tienen entre 7 y 19
meses de ventana de citación: **el 46 % aún no tiene citas**, lo que hace sus
indicadores provisionales.

---

## Unidad académica

**Corto:** Inferida desde la afiliación declarada. Disponible en el 63,8 % de
los casos; el resto figura como «No determinada».

**Extendido:** No existe como campo en las fuentes: se extrae de la cadena de
afiliación. El vocabulario de unidades es **inferido de los datos y no ha sido
validado institucionalmente**.

La comparación entre unidades está además afectada por la cobertura desigual de
Scopus entre disciplinas: medicina aparece sobrerrepresentada frente a
humanidades, artes y derecho por razones de indexación, no de productividad.
