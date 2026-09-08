# Informe por investigador

**Capa:** pública · **Fase:** 3 · **Estado:** **decidido e implementado** (2026-09-07)

La pregunta que gobernaba el diseño la respondió el responsable del proyecto:
**se ofrece a las 530 entidades, con la banda de muestra reducida donde
corresponda.** Las otras cuatro se implementaron con la recomendación de este
documento, que queda marcada como tal en el §5 para que se pueda corregir
cualquiera sin rehacer las demás.

El documento se conserva porque la decisión importa más que el código que la
cumple: un informe con el nombre de una persona y cifras de impacto circula, se
archiva y se cita.

---

## 1. Qué se pedía

Que un investigador pueda pedir «su» informe, aplicando filtros, descargarlo y
leerlo fuera del sitio.

Antes de esto no se podía. El explorador filtraba por seis dimensiones —año, área QS,
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

## 4. El diseño

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
responde «cómo se ve el informe institucional mirando sólo su producción». Cuando el recorte es de una sola persona, la ficha entra como primera sección
del PDF y las demás la siguen.

### 4.3 Las salvaguardas viajan con el informe, no se quedan en la web

Todas existen ya en la ficha. La propuesta es que aparezcan **en la primera
hoja** del informe descargado, no enterradas:

- la advertencia de lectura fija, la que adhiere a DORA y al Manifiesto de
  Leiden y dice que estas métricas no comparan personas;
- **muestra reducida** cuando la persona tiene menos de cinco publicaciones en
  la ventana, que es el caso de 480 de 530.

Las otras dos —el estado de identidad y la unidad no determinada— **no se
repiten en el recorte**: viven en la ficha, con su evidencia, y la ficha abre
el PDF personal. Duplicarlas aquí habría creado una segunda redacción de una
advertencia metodológica, que es lo que este proyecto ya vio divergir una vez.
El recorte enlaza a la ficha en su pie.

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
  apagan.** Resuelto el 2026-09-07, caso por caso:
  - **La red de coautoría (`C-05`) se apaga**, con su explicación en el sitio
    del gráfico. Recortada a una firma no es una red sino una estrella —esa
    persona al centro y sus coautores alrededor—, y lo que el indicador mide,
    cómo se agrupan las personas entre sí, deja de existir. Su contenido no se
    pierde: la coautoría de esa persona está en su ficha (`T-10`), que además
    abre el informe personal.
  - **La mediana por año (`I-04`) se queda, con aviso.** Es una cifra correcta
    sobre pocos valores; ocultarla dejaría un hueco que se leería como ausencia
    de dato. Lo que hacía falta era decir sobre cuántos se calcula. Apagar de
    más también engaña.
  - **Las instituciones colaboradoras (`C-04`) ya declaraban** que no responden
    al recorte, y eso no cambia.

---

## 5. Lo decidido

1. **A quién se le ofrece.** **Decidido por el usuario: a las 530 entidades**,
   con la banda de muestra reducida donde corresponda. Excluir a alguien de su
   propio informe es una decisión sobre esa persona, tomada en silencio;
   declararle la limitación es una decisión sobre el dato. La alternativa
   —sólo las 50 interpretables— habría dejado fuera al 90 %.
2. **La ficha abre el PDF cuando el recorte es una persona.** Implementado con
   la recomendación: es lo único que declara identidad, ORCID con su evidencia
   y unidad.
3. **Se permite combinar persona con otras dimensiones**, y la declaración lo
   dice entero. Añadir año a una persona con tres publicaciones deja una, y eso
   se ve en la hoja en vez de deducirse. La banda de muestra reducida mira la
   producción de la persona **en la ventana**, no la del corte: un filtro de año
   no convierte a nadie en muestra reducida.
4. **La dimensión no entra como lista.** El panel dibuja las firmas elegidas y
   un campo con autocompletado del navegador; la entrada natural es el enlace
   de la ficha. Nunca 530 pastillas.
5. **Uso previsto en la primera hoja.** La advertencia de lectura —DORA y
   Leiden— va sobre las cifras y viaja al papel con ellas.

Cualquiera de las cuatro últimas se puede corregir sin tocar la primera.

---

## 6. Pendiente de higiene documental

`docs/AUTHOR_PROFILE.md` arrastra cifras anteriores a la última consolidación:
habla de 84 formas fusionadas en 37 personas y de 538 entidades publicadas. El
artefacto que sirve el sitio dice **94 en 39** (37 por revisión humana y 2 por
diacríticos), 4 descartadas por no ser personas, y **530 entidades**. Conviene
corregirlo antes de que esta propuesta se implemente citando el número viejo.

---

## 7. Cómo quedó

- **Filtro `autor`**, una dimensión más del explorador: viaja en la URL, las
  secciones se recalculan sobre él y el PDF lo declara en su primera hoja.
- **Salvaguardas** sobre las cifras cuando el recorte es de una persona: la
  advertencia de lectura siempre, y la de muestra reducida por debajo del
  umbral, con **una sola redacción compartida con la ficha**.
- **`make informe RECORTE="autor=Firma"`** produce el informe personal: la
  ficha primero y las cinco secciones después, todas declarando el mismo
  recorte, todas etiquetadas para lectores de pantalla.
- **Ida y vuelta**: la ficha enlaza al informe recortado, y el informe
  recortado enlaza a `autores.html?q=…`, que abre la lista entera —no sólo las
  interpretables— para que una firma bajo el umbral se encuentre.
- **La compuerta de impresión** comprueba, sobre el PDF y en cada corrida, que
  un informe personal lleve el recorte declarado y las dos advertencias.

Coste medido: la portada pasa de 39 a 60 KB en bruto y de 8 a 12 KB
comprimidos, por la lista de sugerencias. Los artefactos de datos no cambian:
el corpus ya traía los nombres canónicos.
