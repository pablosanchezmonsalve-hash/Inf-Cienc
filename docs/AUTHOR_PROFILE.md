# Ficha pública de autor

**Capa:** pública · **Fase:** 2 · **Estado:** diseño

Responde a `PROJECT_SPEC.md` `<public_author_profile>`. Cada campo exigido por
la especificación aparece abajo con su disponibilidad **verificada**, no
supuesta.

---

## 1. Estructura

### Cabecera

| Campo | Disponible | Fuente | Tratamiento si falta |
|---|---|---|---|
| Nombre en fuente | ✅ 589/589 | Scopus | — |
| Nombre normalizado | ✅ 589/589 | derivado | Se muestra sólo si difiere del nombre en fuente |
| Afiliación UFT | ✅ 589/589 | matching | — |
| Unidad académica | ⚠️ 353/589 (60 %) | inferida | «No determinada» |
| Scopus Author ID | ✅ 575/589 (97,6 %) | Scopus | «No resuelto» + explicación |
| **ORCID** | ❌ **0/589** | — | **«No disponible en las fuentes actuales»** con enlace a la nota metodológica |
| Otros identificadores | ❌ 0/589 | — | Sección oculta si no hay ninguno |

### Indicadores

| Indicador | Disponible | Tratamiento |
|---|---|---|
| Total de publicaciones | ✅ | Con nota de conteo completo |
| Total de citas | ✅ | Con fecha de corte 2026-07-22 |
| Citas por publicación | ✅ | Denominador visible |
| **h-index en ventana 2023–2025** | ⚠️ | **Sólo si n ≥ 5.** Etiquetado siempre «en ventana» |
| **FWCI del autor** | ❌ | **No se muestra.** Ver §3 |
| Evolución temporal | ✅ | 3 barras, no línea |
| Publicaciones en top 10 % | ✅ | Recuento |
| Colaboración internacional | ✅ | % de sus publicaciones |

### Listado de publicaciones

Tabla con año, título, fuente, tipo, citas y DOI enlazado. Ordenable.
Las 7 publicaciones sin métricas muestran «sin métricas» en vez de 0.

### Coautoría

Sección **diferida a V2** (`C-05`). La red de coautoría heredaría las 123
variantes de nombre sin resolver y mostraría a la misma persona como varios
nodos. Se declara la razón en la ficha en vez de omitirla en silencio.

---

## 2. Advertencia metodológica obligatoria

Fija, visible sin desplegar, en todas las fichas:

> **Cómo leer esta ficha.** Los indicadores describen la producción indexada en
> Scopus entre 2023 y 2025, con citas actualizadas al 22 de julio de 2026. No
> representan la trayectoria completa de la persona: publicaciones anteriores a
> 2023, o en medios no indexados por Scopus, no aparecen aquí.
>
> Las métricas individuales sobre ventanas cortas y pocas publicaciones no son
> comparables entre personas ni deben usarse para evaluar desempeño individual.
> Este informe adhiere a los principios de DORA y del Manifiesto de Leiden.

Cuando el autor tiene **n < 5 publicaciones** (538 de 589), se añade:

> **Muestra reducida.** Con menos de 5 publicaciones en la ventana, los
> indicadores de impacto no son interpretables individualmente. Se muestran por
> transparencia, no para comparación.

---

## 3. Por qué la ficha no muestra FWCI del autor

`PROJECT_SPEC.md` pide «FWCI u otra métrica normalizada **sólo si existe
realmente**». No existe a nivel autor en este export.

El FWCI de un conjunto no es el promedio de los FWCI de sus elementos: se
calcula comparando citas observadas contra esperadas del conjunto completo.
Promediar los FWCI individuales produciría un número plausible y equivocado.

Conforme a `CLAUDE.md`, se declara como no calculable y se explica qué falta:
un export de SciVal a nivel de autor, o el cálculo con los denominadores de
campo que SciVal no publica en este archivo.

La ficha muestra en su lugar «Publicaciones en el top 10 % de citación», que sí
es normalizado por campo y **sí está disponible por publicación** (`I-05`).

---

## 4. Identidad de autor: qué se afirma y qué no

La ficha corresponde a **una forma de firma**, no necesariamente a una persona.

Cuando un autor está en la cola de ambigüedad (P-03 o P-04), la ficha muestra:

> **Identidad no consolidada.** Esta firma podría corresponder a la misma
> persona que otras formas registradas en el sistema. La consolidación de
> identidades requiere validación institucional o ORCID, pendientes.

**No se enlazan** las fichas sospechosas entre sí ni se sugiere cuáles serían:
eso publicaría la cola interna de revisión (`LAYERS.md` §3).

---

## 5. Alcance de publicación

Pregunta abierta para el responsable del proyecto: **¿se publican las 589
fichas, o sólo un subconjunto validado?**

Argumentos a considerar:

- Todos los datos provienen de Scopus, que es público. No hay dato personal
  nuevo.
- Pero publicar 589 fichas incluye firmas con una sola publicación, identidad
  no consolidada y unidad desconocida — fichas de baja calidad informativa.
- Un umbral (p. ej. n ≥ 2, o sólo los 396 del ranking validado) reduce ruido
  pero introduce un criterio de exclusión que debe justificarse públicamente.

**Recomendación:** publicar las 589 con el estado de identidad visible, y
ofrecer el ranking filtrado por n ≥ 5 como vista por defecto. Así ninguna
persona queda excluida arbitrariamente y la vista principal mantiene calidad.

Requiere decisión del usuario antes de Fase 3.
