# Limitaciones declaradas

**Capa:** pública · **Fase:** 1

Este documento existe porque publicar indicadores sin sus límites es un error
metodológico. Todo lo aquí listado está verificado sobre los datos, no
supuesto.

---

## 1. Cobertura temporal

El corpus cubre **2023–2025**. No hay serie histórica previa a 2023, por lo que
**no pueden calcularse tendencias de largo plazo** ni indicadores acumulados de
carrera.

El corte de citas es el **22 de julio de 2026**. Las publicaciones de 2025
tienen entre 7 y 19 meses de ventana de citación: sus indicadores de impacto
son provisionales por construcción.

## 2. Sin identificador persistente de autor

**ORCID no existe en ninguna de las fuentes.** El único identificador es el
Scopus Author ID, con dos problemas verificados:

- **20 nombres completos** están asociados a más de un Scopus Author ID
  (perfiles fragmentados u homonimia).
- **123 entradas** corresponden a autores cuyo apellido base aparece con más de
  una forma de nombre (`Yanine F.` / `Yanine F.F.`; `López-Arana S.` /
  `Lopez-Arana S.`; `Castro-Sepúlveda M.` / `Castro-Sepulveda M.`).
- **249 entradas** corresponden a un mismo Scopus Author ID firmando con
  nombres distintos.

Estas ambigüedades están **declaradas y encoladas, no resueltas**. La cifra de
589 autores debe leerse como *589 formas de firma detectadas*, no como 589
personas. El número real de personas es menor y sólo puede fijarse con
validación humana o con ORCID.

Recuperar ORCID desde Crossref (cobertura DOI: 97,7 %) o desde el repositorio
institucional es la vía identificada. **No implementada en Fase 1.**

## 3. Unidad académica incompleta

La unidad académica **no existe como campo** en ninguna fuente: se infiere
parseando la cadena de afiliación.

- Cobertura: **63,8 %** de los pares autor × publicación (**65,0 %** medido
  sobre cadenas de afiliación ponderadas por frecuencia). Ambos denominadores
  son legítimos y se declaran por separado.
- **437 pares quedan como `No determinada`.** No se imputan.
- El vocabulario controlado de 13 unidades es **inferido de los datos y no está
  validado institucionalmente**. 11 variantes quedan fuera del vocabulario y se
  conservan tal cual (incluidos artefactos de la fuente como
  `Facultad de MedicinaEscuela de Medicina`, donde falta la coma separadora).

**Ninguna comparación entre unidades académicas es completa.**

## 4. Sesgo de cobertura de la base

Scopus no indexa uniformemente todas las disciplinas. En este corpus:

| Unidad | Pares autor × publicación |
|---|---|
| Facultad de Medicina | 527 |
| Facultad de Educación, Psicología y Familia | 50 |
| Facultad de Ingeniería | 49 |
| Facultad de Odontología | 34 |
| Facultad de Economía y Negocios | 28 |
| Facultad de Derecho | 6 |
| Facultad de Artes | 6 |
| Facultad de Arquitectura y Diseño | 3 |

Esta distribución mide **producción indexada en Scopus**, no productividad
académica. Humanidades, artes, derecho y ciencias sociales publican en formatos
y revistas que Scopus cubre parcialmente.

## 5. Doce publicaciones con datos incompletos

De las 823 del universo:

- **7 están sólo en Scopus** → sin FWCI ni clasificación temática. Quedan
  excluidas de todo indicador de impacto normalizado y de las vistas temáticas.
  Son mayoritariamente humanidades y ciencias sociales; se conservaron
  deliberadamente para no agravar el sesgo del punto 4.
- **5 están sólo en SciVal** → sin detalle de autoría, por lo que no son
  atribuibles a ningún autor UFT. Cuentan en totales institucionales pero no en
  rankings de autor.

Cada indicador declara su propio denominador: 823 publicaciones totales, 816
con métricas, 818 con autoría detallada.

## 6. Discrepancia de citas entre fuentes

Scopus reporta 3.909 citas totales; SciVal 3.935. Diferencia de +26 (+0,67 %),
distribuida en 88 publicaciones. Compatible con distinta fecha de corte, pero
**el export de Scopus no declara la suya**, lo que impide cerrar la explicación.

Se adopta SciVal como fuente única de citas, por venir con fecha de corte
declarada y acompañada del FWCI del mismo corte.

## 7. Riesgo de parsing de afiliaciones

El campo `Authors with affiliations` usa la coma como separador tanto entre
nombre y afiliación como dentro de la propia afiliación. En **8 de 818
publicaciones** el número de bloques no coincide con el número de autores
declarados: en esos casos la atribución autor→afiliación puede ser incorrecta.
Están registradas en `internal/matching_reconciliation.csv`.

Durante la auditoría se detectó y corrigió un error propio en esta lógica: la
extracción de unidad académica tomaba la facultad de **otra** institución
cuando el autor tenía doble afiliación (30 pares se atribuían a
`Faculty of Medicine and Nursing`, de la Universidad del País Vasco). La
corrección redujo la cobertura declarada de unidad de 70,1 % a los valores
reales del punto 3.

### Cuatro firmas publicadas que no son personas

El mismo separador produce un segundo efecto, y este llega hasta lo publicado:
**cuatro de las formas de firma son fragmentos de cadena de afiliación** que
entraron en la lista de autores. Tienen ficha pública.

| Firma | Publicación | Qué la delata |
|---|---|---|
| `and Senior Lecturer` | `2-s2.0-85190421197` | posición 9 de 7 autores declarados |
| `School of Psychology` | `2-s2.0-85151493381` | la misma firma en las posiciones 2, 5 y 9 |
| `Metabolism` | `2-s2.0-85199751688` | ninguna inicial con punto |
| `Movement Sciences (NUTRIM)` | `2-s2.0-85207388806` | ninguna inicial con punto |

En **las cuatro publicaciones son la única detección UFT**: si se descartaran,
esas publicaciones quedarían sin autoría UFT nombrada. Siguen en el universo,
porque la afiliación que las trajo es real; lo que no es una persona es el
nombre.

Las detecta la regla `E-09` de `src/audit/05_validation_rules.py` con tres
señales, y **no se eliminan**: declarar que una firma no es una persona es una
decisión de identidad, y `D-08` la reserva a la revisión humana. Están encoladas
en `internal/ambiguities_authors.csv` y en la cola «Firma sin forma de persona»
de `make revision`.

**Efecto en `P-06`:** publica **556**, y las firmas con forma de persona son
**552**. La nota del indicador lo declara mientras la revisión siga pendiente.
Cuando alguien resuelva, `config/firmas_descartadas.yml` aplica el descarte y
`P-06` pasa a 552 solo.

## 8. Un duplicado probable sin resolver

Dos registros comparten título normalizado con EID y DOI distintos:

- `2-s2.0-85203352103` — Article, 2024
- `2-s2.0-85211925904` — Letter, 2025

Lectura probable: una carta comentando al artículo original. **No se fusionan.**
Ambos permanecen en el universo, marcados en
`internal/ambiguities_publications.csv`.

## 9. Campos bajo umbral de cobertura

| Campo | Cobertura | Consecuencia |
|---|---|---|
| ODS (SDG 2025) | 37,9 % | Sólo publicable como «n de publicaciones con ODS asignado» |
| Financiamiento | 37,4 % | Insuficiente para reportar |
| Open Access | 72,2 % | La ausencia no equivale a «no OA» |
| Unidad académica | 63,8 % | Ver punto 3 |
| `Molecular Sequence Numbers` | 0 % | Columna vacía, se excluye |

## 10. Los archivos `.RData` no alimentan indicadores

Los tres objetos `bibliometrixDB` provienen de un proceso desconocido y no
reproducible, y arrastran seis columnas residuales de *joins* repetidos.
`Scival_Normalizado.RData` **no contiene ninguna métrica de SciVal** pese a su
nombre. Se usan sólo como referencia comparativa del matching.
