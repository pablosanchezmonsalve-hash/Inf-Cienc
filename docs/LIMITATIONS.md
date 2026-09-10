# Limitaciones declaradas

**Capa:** pública · **Fase:** 1

Este documento existe porque publicar indicadores sin sus límites es un error
metodológico. Todo lo aquí listado está verificado sobre los datos, no
supuesto.

---

## 1. Cobertura temporal

El corpus cubre **2020–2025**, seis años. No hay serie previa a 2020, por lo que
**no pueden calcularse indicadores acumulados de carrera**: el h en ventana de
un autor no es su h de carrera, y una serie de seis puntos no sostiene una
afirmación de tendencia de largo plazo.

El corte de citas es el **30 de agosto de 2026**. Las publicaciones de 2025
tienen entre 8 y 20 meses de ventana de citación: sus indicadores de impacto
son provisionales por construcción.

### El corpus cambia entre cortes, no sólo crece

La carga del 2026-09-08 permitió comparar dos exports del mismo período. En la
subventana 2023–2025 ambos traen **818 publicaciones**, pero no son las mismas:
**5 salieron y 5 entraron**. Las que salieron no son marginales —una acumulaba
9 citas, otra 4, otra 2— y las que entraron son publicaciones cuya afiliación
institucional Scopus escribe con el nombre mal deletreado.

Que el total coincida es casualidad. La consecuencia práctica: **dos informes
del mismo período con distinta fecha de corte no son comparables registro a
registro**, aunque sus totales coincidan. Comparar sólo los recuentos oculta el
cambio. El export anterior se conserva en `data/raw/` y queda declarado en
`config/sources.yml` bajo `reemplaza_a`, que es lo único que permite medir esta
rotación.

## 2. Sin identificador persistente de autor, en el export original

**ORCID no existe en ninguna de las fuentes originales de Fase 1** (el export
de Scopus/SciVal). El único identificador ahí es el Scopus Author ID, con dos
problemas verificados:

- **29 nombres completos** están asociados a más de un Scopus Author ID
  (perfiles fragmentados u homonimia).
- **207 entradas** corresponden a autores cuyo apellido base aparece con más de
  una forma de nombre (`Yanine F.` / `Yanine F.F.`; `López-Arana S.` /
  `Lopez-Arana S.`; `Castro-Sepúlveda M.` / `Castro-Sepulveda M.`).
- **447 entradas** corresponden a un mismo Scopus Author ID firmando con
  nombres distintos.

Estas ambigüedades están **declaradas y encoladas, no resueltas**. La cifra de
888 autores debe leerse como *888 formas de firma detectadas*, no como 888
personas. La consolidación humana previa (`D-08`, nunca automática) sigue
aplicándose y deja **829 entidades** —esa es la base que sirve el sitio—: 94
formas de firma resultaron ser 39 personas (37 por revisión caso por caso y 2
por diacríticos, `config/identidades_consolidadas.yml`) y 4 más se descartaron
por no ser personas.

La ampliación de la ventana a 2020–2025 sumó 299 formas de firma nuevas sobre
las 589 de la carga anterior, y **ninguna de ellas ha pasado por revisión
humana todavía**: las colas de `internal/` crecieron con la carga y lo que
entró después del 2026-09-08 está sin revisar. La distancia entre formas de
firma y personas es hoy mayor de lo que era, no menor.

**Actualización posterior a Fase 1: ORCID sí se recuperó**, desde Crossref,
el repositorio institucional (DSpace), el inventario de autoarchivo de
biblioteca y la propia API pública de ORCID — nunca inventado, siempre con
su fuente declarada por firma. Cobertura hoy: **328 formas de firma con
ORCID** sin consolidar, **268 entidades con ORCID** tras consolidación
humana (`STATE.md`). El detalle metodológico completo —qué vía aportó qué,
dónde persiste la brecha y por qué no llega al 100 %— vive en
`docs/ORCID_COVERAGE.md` y `docs/ORCID_GUIDE.md`, no se repite aquí.

**La cobertura de ORCID se diluyó con la carga del 2026-09-08 y todavía no se
ha vuelto a medir.** Las 328 firmas con ORCID siguen todas presentes en el
corpus nuevo —no se perdió ninguna—, pero el total sin identificador pasa de
261 a **560 formas de firma**. Ese salto tiene dos componentes que no conviene
confundir: **299 son formas de firma que la ampliación añadió y que ninguna vía
ha consultado todavía**; las 261 restantes ya estaban en el corpus 2023–2025 y
se consultaron sin encontrarles identificador, que es un hueco distinto y más
difícil. En proporción, la cobertura pasa de 328 de 589 (55,7 %) a 328 de 888
(36,9 %), y esa caída es de denominador, no de dato perdido. Los conectores que recuperan
ORCID salen a red y no se reejecutaron en esta carga: hasta que se corran,
toda cifra de cobertura de ORCID describe el corpus 2023–2025 medido contra un
universo 2020–2025. Queda como pendiente `T-21`, cuyo alcance real son las 299
formas nunca consultadas.

## 3. Unidad académica incompleta

La unidad académica **no existe como campo** en ninguna fuente: se infiere
parseando la cadena de afiliación.

- Cobertura: **64,2 %** de los pares autor × publicación (medición de la carga
  2026-09-08).
- **703 pares quedan como `No determinada`.** No se imputan.
- El vocabulario controlado de 13 unidades se infirió de los datos y, desde
  entonces, **fue validado institucionalmente** (`T-02`, cerrado 2026-08-26;
  `config/matching_rules.yml`: `vocabulario_validado_por_institucion: true`).
- **La ventana 2020–2025 trajo 11 variantes que esa validación no cubre**, con
  17 pares afectados: cuatro son la forma inglesa de facultades ya conocidas
  (`School of Physiotherapy`, `Faculty of Humanities and Communications`,
  `School of Business and Economics`, `School of Family Studies`), una es un
  duplicado ortográfico (`Escuela de Post grado` frente a `Escuela de
  Postgrado`), otra un error de codificación de la fuente (`Facultad de
  Ingenierĺa`), otra una cadena compuesta (`Facultad de Medicina y Facultad de
  Odontología`) y tres son escuelas que antes no aparecían. Se conservan tal
  cual: **declarar que dos formas son la misma unidad es una afirmación
  institucional, no una deducción** (`D-08`). Queda como pendiente `T-22`, con
  su cola ya generada.

**Ninguna comparación entre unidades académicas es completa.**

## 4. Sesgo de cobertura de la base

Scopus no indexa uniformemente todas las disciplinas. En este corpus:

| Unidad | Pares autor × publicación |
|---|---|
| Facultad de Medicina y Salud | 992 |
| Facultad de Ingeniería | 84 |
| Facultad de Educación y Ciencias Sociales | 76 |
| Facultad de Economía y Negocios | 55 |
| Facultad de Derecho | 10 |
| Facultad de Humanidades y Comunicaciones | 9 |
| Facultad de Artes | 6 |
| School of Physiotherapy | 5 |
| Facultad de Arquitectura, Diseño y Estudios Creativos | 3 |
| Escuela de Literatura | 3 |

Diez unidades con más pares, de las que el gráfico `P-07` publica; las demás
tienen dos o menos. A ellas se suman **700 pares
`No determinada`**, que no se imputan a ninguna unidad.

Esta distribución mide **producción indexada en Scopus**, no productividad
académica. Humanidades, artes, derecho y ciencias sociales publican en formatos
y revistas que Scopus cubre parcialmente. La concentración en salud no
disminuyó al ampliar la ventana: se mantuvo.

## 5. Publicaciones con datos incompletos: ninguna en esta carga

En la carga del 2026-09-08 el cruce entre las dos fuentes primarias por `EID`
es **1 a 1 completo sobre las 1342 publicaciones**: ninguna aparece sólo en
Scopus ni sólo en SciVal. Los cuatro denominadores coinciden en 1342.

Esto es una propiedad de estos dos exports, no una garantía del sistema. En la
carga anterior 12 publicaciones estaban en una sola fuente —7 sólo en Scopus,
sin FWCI ni clasificación temática, mayoritariamente humanidades y ciencias
sociales; 5 sólo en SciVal, sin detalle de autoría— y los denominadores eran
823 / 816 / 818. La regla `D-16` sigue vigente y cada indicador sigue
declarando el suyo: que hoy sean iguales no autoriza a suponer que lo serán en
la próxima carga.

## 6. Discrepancia de citas entre fuentes

Scopus reporta 14.421 citas totales; SciVal 14.245. Diferencia de **-176
(-1,22 %)**, distribuida en 115 publicaciones. Supera la tolerancia del 1 % que
vigila la regla `X-04`, que se deja fallando a propósito: subir el umbral para
que pase sería calibrar la regla contra el dato que debe vigilar.

Lo relevante no es el tamaño sino el **cambio de signo**. En la carga anterior
la diferencia era de +26 (+0,67 %), con SciVal por encima de Scopus; ahora
SciVal queda por debajo. Con SciVal cortado el 2026-08-30 y Scopus exportado el
2026-09-08, que la fuente más antigua acumule menos citas es lo esperable, y el
signo positivo anterior era el anómalo. Sigue sin poder cerrarse la explicación,
porque **el export de Scopus no declara su fecha de corte** (pendiente `T-06`).

Se adopta SciVal como fuente única de citas, por venir con fecha de corte
declarada y acompañada del FWCI del mismo corte.

## 7. Riesgo de parsing de afiliaciones

El campo `Authors with affiliations` usa la coma como separador tanto entre
nombre y afiliación como dentro de la propia afiliación. En **9 de 1342
publicaciones** el número de bloques no coincide con el número de autores
declarados: en esos casos la atribución autor→afiliación puede ser incorrecta.
Están registradas en `data/interim/matching_reconciliation.csv`.

Durante la auditoría se detectó y corrigió un error propio en esta lógica: la
extracción de unidad académica tomaba la facultad de **otra** institución
cuando el autor tenía doble afiliación (30 pares se atribuían a
`Faculty of Medicine and Nursing`, de la Universidad del País Vasco). La
corrección redujo la cobertura declarada de unidad de 70,1 % a los valores
reales del punto 3.

### Cuatro firmas que resultaron ser fragmentos de cadena de afiliación, no personas — resuelto

El mismo separador produjo un segundo efecto que llegó hasta lo publicado:
**cuatro formas de firma eran fragmentos de cadena de afiliación** que habían
entrado en la lista de autores.

| Firma | Publicación | Qué la delataba |
|---|---|---|
| `and Senior Lecturer` | `2-s2.0-85190421197` | posición 9 de 7 autores declarados |
| `School of Psychology` | `2-s2.0-85151493381` | la misma firma en las posiciones 2, 5 y 9 |
| `Metabolism` | `2-s2.0-85199751688` | ninguna inicial con punto |
| `Movement Sciences (NUTRIM)` | `2-s2.0-85207388806` | ninguna inicial con punto |

En las cuatro publicaciones era la única detección UFT: descartar la firma no
retira la publicación del universo, porque la afiliación que la trajo es
real — lo que estaba en duda era el nombre, no la afiliación.

Las detectó la regla `E-09` de `src/audit/05_validation_rules.py`, y **no se
eliminaron automáticamente**: declarar que una firma no es una persona es una
decisión de identidad, y `D-08` la reserva a la revisión humana. Pasaron por
esa revisión y **las cuatro se confirmaron como fragmentos** (ninguna era un
autor mononímico real): `config/firmas_e09_resueltas.yml` las registra en
`descartadas`, y ya no forman parte de las entidades publicadas.

**Efecto en `P-06`:** las 888 formas de firma detectadas en la fuente,
consolidadas por revisión humana (94 formas → 39 personas, `D-08`) y con
estas 4 ya descartadas, publican **829 entidades** (`STATE.md`,
`data/processed/authors.json`) — la cifra ya refleja la resolución, no una
proyección hipotética.

## 8. Dos duplicados probables sin resolver, y uno ya descartado

La carga del 2026-09-08 dejó **tres grupos de título repetido: uno revisado y
dos pendientes**. Los tres siguen enteros en el universo; ninguno se fusiona.

**Revisado y descartado** (`config/resoluciones_humanas.yml`, 2026-08-03):
`2-s2.0-85203352103` (Article, 2024) y `2-s2.0-85211925904` (Letter, 2025)
comparten título, pero son dos trabajos distintos: el segundo es una carta al
editor que comenta al primero. Comprobado abriendo ambos DOI.

**Pendientes**, los dos traídos por los años que la ampliación incorporó y con
el mismo DOI en cada par, que es una señal más fuerte que el título repetido:

- `2-s2.0-85088811762` y `2-s2.0-85088892718` — 2020, DOI
  `10.3390/ijms21155225`, mismo título con distinta capitalización y **con las
  citas repartidas entre los dos registros** (10 y 3).
- `2-s2.0-85153057163` y `2-s2.0-85107084838` — 2021, DOI
  `10.5867/medwave.2021.04.8168`, ambos sin citas.

Son los dos casos que hacen fallar la regla `D-02`. Quedan encolados en
`internal/ambiguities_publications.csv` porque decidir que dos registros son el
mismo trabajo es una afirmación sobre la fuente, no una deducción (`D-08`).
Mientras no se resuelvan, **el universo de 1.342 cuenta dos veces dos trabajos**
y las citas de uno de esos pares aparecen partidas.

## 9. Campos bajo umbral de cobertura

| Campo | Cobertura | Consecuencia |
|---|---|---|
| ODS (SDG 2025) | 38,8 % | Sólo publicable como «n de publicaciones con ODS asignado» |
| Financiamiento | 36,5 % | Insuficiente para reportar |
| Open Access | 70,3 % | La ausencia no equivale a «no OA» |
| Unidad académica | 64,2 % | Ver punto 3 |
| `Molecular Sequence Numbers` | 0 % | Columna vacía, se excluye |

## 10. Los archivos `.RData` no alimentan indicadores

Los tres objetos `bibliometrixDB` provienen de un proceso desconocido y no
reproducible, y arrastran seis columnas residuales de *joins* repetidos.
`Scival_Normalizado.RData` **no contiene ninguna métrica de SciVal** pese a su
nombre. Se usan sólo como referencia comparativa del matching.
