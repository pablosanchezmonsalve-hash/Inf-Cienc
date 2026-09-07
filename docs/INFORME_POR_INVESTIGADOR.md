# Informe por investigador: propuesta

**Capa:** pública · **Fase:** 3 · **Estado:** **propuesta, pendiente de decisión del responsable del proyecto**

Nada de este documento está implementado. Se escribe para que la decisión se
tome antes del código, porque el código que la incumpla no se arregla después:
un informe con el nombre de una persona y cifras de impacto circula, se archiva
y se cita.

---

## 1. Qué se pide decidir

Que un investigador pueda pedir «su» informe, aplicando filtros, descargarlo y
leerlo fuera del sitio.

Hoy no se puede. El explorador filtra por seis dimensiones —año, área QS,
unidad académica, tipo documental, acceso abierto y colaboración— y ninguna es
la persona. A alguien concreto sólo se llega por búsqueda de texto libre, que
no es un filtro sino un colador, o por su ficha, que es otra página con otras
reglas.

Lo que falta no es un informe nuevo. Es **decidir qué puede afirmar**, y luego
conectar dos superficies que ya existen.

---

## 2. Lo que ya existe (verificado, no supuesto)

| Pieza | Estado |
|---|---|
| Ficha de autor por entidad | 530 fichas publicadas, con sus indicadores, su evolución, su coautoría interna y sus advertencias |
| Nombre canónico en el corpus | `publications.json` ya trae los nombres **consolidados**: 530 nombres distintos, ninguno es una variante suelta |
| Unicidad | Ninguna entidad comparte nombre con otra: la correspondencia nombre ↔ entidad es 1 a 1 |
| Recorte en la URL | El filtro viaja en la dirección y el informe descargado ya declara cuál es |
| Informe a medida | `make informe RECORTE="…"` genera el PDF del recorte |

Es decir: **el filtro por persona no necesita recalcular nada del corpus**. La
consolidación de identidades ya está aplicada donde hace falta.

---

## 3. La razón por la que esto no es una tarea de interfaz

La distribución de la producción por entidad, medida sobre el artefacto que
sirve el sitio:

| Publicaciones en la ventana | Entidades |
|---|---:|
| 1 | 360 |
| 2 a 4 | 120 |
| 5 a 9 | 31 |
| 10 o más | 19 |
| **Total** | **530** |

**480 de 530 entidades quedan por debajo del umbral de interpretabilidad** que
el propio proyecto declara (`n_minimo_interpretable: 5` en
`config/indicators.yml`). Para ellas, un «informe de productividad» es un
extracto de una o dos referencias con indicadores de impacto que no significan
nada individualmente.

Y sobre la identidad y la afiliación:

| Situación | Entidades |
|---|---:|
| Identidad marcada como no consolidada | 20 |
| Sin unidad académica determinada | 214 |
| Con más de una unidad | 17 |
| Con ORCID | 268 |

Un informe personal que no diga esto sobre sí mismo es un informe que engaña
por omisión, y el proyecto ya tiene escrito que no se hace (`CLAUDE.md`,
`<non_negotiable_rules>`; `docs/AUTHOR_PROFILE.md` §2 y §4).

---

## 4. Propuesta

### 4.1 La persona es una dimensión de filtro más

Clave `autor`, valores el nombre canónico, igual que `unidad`. El recorte viaja
en la URL, las secciones se recalculan sobre él y el PDF lo declara en su
primera hoja, todo con el mecanismo que ya existe. `Autor: Orellana-Donoso M.`
aparecería en la línea de declaración sin escribir una segunda redacción.

**Restricción de interfaz, no cosmética:** el panel de filtros dibuja una
pastilla por valor con su recuento. Quinientas treinta pastillas no son un
filtro, son una guía telefónica. La dimensión `autor` necesita un campo de
búsqueda con sugerencias, y su entrada natural es la ficha: un enlace «ver el
informe de esta persona» que aplica el recorte. Nunca una lista completa.

### 4.2 El informe por investigador es la ficha más el recorte

No un tercer artefacto. La ficha responde «quién es y qué publicó»; el recorte
responde «cómo se ve el informe institucional mirando sólo su producción». Se
propone que, cuando el recorte sea de una sola persona, la ficha entre como
primera sección del PDF y las demás secciones la sigan.

### 4.3 Las salvaguardas viajan con el informe, no se quedan en la web

Todas existen ya en la ficha. La propuesta es que aparezcan **en la primera
hoja** del informe descargado, no enterradas:

- la advertencia de lectura fija, la que adhiere a DORA y al Manifiesto de
  Leiden y dice que estas métricas no comparan personas;
- **muestra reducida** cuando la persona tiene menos de cinco publicaciones en
  la ventana, que es el caso de 480 de 530;
- el **estado de identidad**, cuando la firma no está consolidada;
- la **unidad no determinada**, cuando falta, en vez de una casilla vacía.

### 4.4 Lo que no se hace, y por qué

- **No se calcula el FWCI de la persona.** Decisión `D-18`: el FWCI de un
  conjunto no es el promedio de los FWCI de sus elementos. En su lugar va
  «publicaciones en el top 10 %», que sí está normalizado por campo y sí existe
  por publicación.
- **No se publica ningún indicador nuevo por autor.** El catálogo ya declara
  cuáles hay y cuáles se descartan.
- **No se ofrece comparación entre personas descargable.** Un ranking en PDF es
  una tabla de desempeño individual con aspecto de dato oficial.
- **Los cortes que cambian de significado sobre una persona se declaran o se
  apagan.** Una red de coautoría de un solo autor es una estrella trivial; una
  mediana sobre una publicación no es una mediana. Qué corte cae en cuál de las
  dos categorías es trabajo de implementación, con la misma regla que ya
  gobierna el resto: si el indicador cambia de significado, se dice.

---

## 5. Decisiones que se piden

Sin estas respuestas la implementación quedaría decidiendo por su cuenta cosas
que no le tocan.

1. **¿A quién se le ofrece?** Recomendación: a las 530 entidades, con la banda
   de muestra reducida donde corresponda. Excluir a alguien de su propio
   informe es una decisión sobre esa persona, tomada en silencio; declararle la
   limitación es una decisión sobre el dato. La alternativa —sólo las 50
   interpretables— produce informes de mejor calidad y deja fuera al 90 %.
2. **¿La ficha entra en el PDF cuando el recorte es una persona?**
   Recomendación: sí, como primera sección.
3. **¿Se permite combinar persona con otras dimensiones?** Recomendación: sí,
   pero la declaración lo dice entero. Añadir año a una persona con tres
   publicaciones deja una, y eso tiene que verse en la hoja, no deducirse.
4. **¿Entra la dimensión en el panel de filtros o sólo por la ficha y la URL?**
   Recomendación: entrada por la ficha y por búsqueda; nunca una lista de 530.
5. **¿Cambia algo respecto de quién puede pedirlo?** Todo el dato es público y
   viene de Scopus, así que técnicamente no hay dato nuevo. Pero un PDF nominal
   circula distinto que una página, y conviene que el documento declare su uso
   previsto. Recomendación: declararlo en la primera hoja, junto a la
   advertencia de lectura.

---

## 6. Pendiente de higiene documental

`docs/AUTHOR_PROFILE.md` arrastra cifras anteriores a la última consolidación:
habla de 84 formas fusionadas en 37 personas y de 538 entidades publicadas. El
artefacto que sirve el sitio dice **94 en 39** (37 por revisión humana y 2 por
diacríticos), 4 descartadas por no ser personas, y **530 entidades**. Conviene
corregirlo antes de que esta propuesta se implemente citando el número viejo.
