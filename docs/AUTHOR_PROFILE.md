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
| **ORCID** | ✅ **268/530 (50,6 %)** | Crossref + registro de ORCID | **«No disponible en las fuentes actuales»** con enlace a la nota metodológica |
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

Publicado el 2026-08-26 (`T-10`). Lista, con quién de la UFT coautoró cada
publicación de esta persona dentro de la ventana, con el recuento de
publicaciones compartidas y enlace a la ficha de cada coautor. Sólo cuenta
coautoría interna (otra firma UFT en la misma publicación) — no es un
desglose de la red completa, que vive en `colaboracion.html` (`C-05`).

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

### 589 en la auditoría, 530 en el sitio: no es una incoherencia

Las cifras son correctas y miden cosas distintas. La consolidación avanza con
cada revisión de identidad, así que el número de entidades baja con el
tiempo — lo que sigue fijo es el método, no la cifra puntual (ver
`STATE.md` para el valor vigente).

- **589** son las formas de firma que la auditoría detecta en Scopus. Describe
  la fuente, y no cambia porque nosotros revisemos nada.
- **530** son las entidades que el sitio publica hoy, en dos pasos: una
  revisión humana fusionó 94 formas de firma en 39 personas
  (589 − 94 + 39 = 534, `config/identidades_consolidadas.yml`), y la regla
  `E-09` marcó 4 formas más como fragmentos de cadena de afiliación —no
  personas—, confirmados y descartados tras revisión (534 − 4 = 530,
  `config/firmas_e09_resueltas.yml`; ver `docs/LIMITATIONS.md` §7).

La consolidación no la hace ninguna heurística (decisión `D-08`). La única vía
es `config/identidades_consolidadas.yml`, que genera `apply_decisions.py` a
partir de lo que una persona decidió en `make revision`. Sin ese archivo el
sitio publica las 589 y todo funciona igual.

Cada ficha fusionada declara **qué formas de firma la componen**, y el buscador
encuentra por cualquiera de ellas: quien llegue desde Scopus con «Giglio A.»
tiene que dar con la ficha aunque hoy se titule «Giglio Jiménez A.».

La forma canónica no se inventa. Es la que la fuente usa más, con una salvedad:
si una variante conserva la tilde del apellido y otra no, gana la acentuada
aunque sea menos frecuente. Perder una tilde es un artefacto conocido de estas
exportaciones —en este corpus apareció `Ingenierı́a` con una i sin punto—, y
publicar «Núnez-Lisboa» teniendo «Núñez-Lisboa» sería publicar un apellido
corrupto. Con las **iniciales** no se aplica ese criterio: que el nombre de pila
lleve tilde no se deduce de aquí, y ahí decide la frecuencia.

Cuando un autor está en la cola de ambigüedad (P-03 o P-04), la ficha muestra:

> **Identidad no consolidada.** Esta firma podría corresponder a la misma
> persona que otras formas registradas en el sistema. La consolidación de
> identidades requiere validación institucional o ORCID, pendientes.

**No se enlazan** las fichas sospechosas entre sí ni se sugiere cuáles serían:
eso publicaría la cola interna de revisión (`LAYERS.md` §3).

### El ORCID que se muestra viene con su evidencia

Un ORCID de esta plataforma **no procede de Scopus**: lo propone Crossref
emparejando apellido e inicial, que es una heurística y puede confundir a dos
personas con la misma firma abreviada. Publicarlo sin más lo convertiría en un
hecho, y no lo es.

Por eso cada asignación se contrasta contra el registro público del propio
titular (`src/enrich/orcid_api.py`) y la ficha muestra el resultado:

| Etiqueta en la ficha | Qué significa | Firmas |
|---|---|---:|
| `verificado` | Lo transmitió el editor a Crossref **y** el titular lo declara en su registro: dos fuentes independientes | 139 |
| `declarado por el titular` | Se encontró preguntando al registro quién declara esta publicación. Una sola fuente, sin segunda comprobación | 43 |
| `confirmado por revisión` | Una persona confirmó, caso por caso, que el titular que declara la institución corresponde a esta firma | 15 |
| `no verificable` | El titular no declara ninguna obra con DOI: no hay contra qué contrastar | 16 |
| `sin confirmar` | El titular declara obras, pero ninguna coincide con las de esta firma | 3 |
| `registro no accesible` | El ORCID no existe o su registro no es público | 0 |
| `comprobado por revisión` | La vía automática no pudo resolverla y una persona abrió el registro del titular y la respaldó | 0 |
| `encontrado por revisión` | Ninguna vía automática dio con el identificador; una persona lo buscó en el registro y lo encontró | 0 |

Ver `ORCID_COVERAGE.md` §2 bis para por qué las 43 no dicen «verificado».

Los recuentos son **posteriores a la consolidación**: varias variantes de una
misma persona que traían el mismo ORCID cuentan ahora una vez.

Las dos últimas están en cero porque nadie ha revisado todavía; existen desde
que `make revision` encola las asignaciones que la comprobación automática no
puede resolver. No se omiten por valer cero: una etiqueta ausente y una en cero
dicen cosas distintas.

`sin confirmar` **no afirma que la asignación sea falsa**. Afirma que la
evidencia disponible no la respalda, que es una frase distinta y la única que
los datos sostienen. Esas tres —cuatro formas de firma antes de consolidar—
entran en la cola «ORCID sin confirmar» de `make revision`, con enlace al
registro del titular y la lista de publicaciones que hay que comparar;
resolverlas automáticamente está prohibido. Las 16 `no verificable` tienen su
propia cola, separada a propósito: que no haya nada contra qué contrastar no es
lo mismo que contrastar y no encontrar coincidencia.

Lo que se publica de esa cola es el **recuento**, arriba. El detalle nominal de
por qué cada una no se confirma —qué DOI, qué afiliaciones declara— se queda en
la capa interna.

---

## 5. Alcance de publicación

> **Nota de base (actualizada 2026-09-03).** Las cifras de esta sección son de
> antes de la consolidación humana: 589 es el número de **formas de firma** de
> la fuente, de las que 94 se fusionaron en 39 personas, y 4 más se
> descartaron por no ser personas (regla `E-09`, ver `docs/LIMITATIONS.md` §7).
> Las **entidades publicadas hoy son 530**. El razonamiento no cambia; los
> números sí. El supuesto vigente está en `V2_BACKLOG.md` §4 (`T-11`).

Pregunta abierta para el responsable del proyecto: **¿se publican las 589
formas de firma, o sólo un subconjunto validado?**

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
