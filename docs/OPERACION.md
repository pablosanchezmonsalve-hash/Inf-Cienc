# Cómo se opera el proyecto, paso a paso

Guía para quien se sienta delante del teclado. Empieza desde cero: si ya tiene
el repositorio clonado, salte al Paso 3.

> **En Windows el comando de Python es `py`, no `python3`.** Y los comandos van
> en **PowerShell**, no dentro del intérprete de Python: si ve el prompt `>>>`,
> escriba `exit()` para salir.
>
> Tampoco hay `make` en Windows. Cada objetivo del `Makefile` se ejecuta
> llamando directamente al guion; esta guía trae los dos, el objetivo y el
> comando real.

---

## Paso 1 — Lo que hace falta instalar

1. **Python 3.11 o superior.** Desde <https://www.python.org/downloads/>.
   En la **primera** pantalla del instalador marque **«Add python.exe to PATH»**
   antes de pulsar Install. Sin eso, PowerShell no lo encontrará.
2. **Git.** Desde <https://git-scm.com/download/win>, con las opciones por
   defecto.

Para comprobar que quedaron bien, abra PowerShell y escriba:

```powershell
py --version
git --version
```

Si `py` responde con un error o le abre la Microsoft Store, Python no está
instalado de verdad: es un atajo vacío de Windows. Vuelva al punto 1.

---

## Paso 2 — Traer el repositorio

Abra PowerShell. Está en el menú Inicio, escribiendo «PowerShell».

```powershell
cd $HOME\Documents
git clone https://github.com/pablosanchezmonsalve-hash/Inf-Cienc.git
cd Inf-Cienc
py -m pip install -r requirements.txt
```

La carpeta queda en `Documentos\Inf-Cienc`. **Todos los comandos de esta guía se
escriben estando dentro de ella.** Si abre una consola nueva, vuelva con:

```powershell
cd $HOME\Documents\Inf-Cienc
```

---

## Paso 3 — Antes de cualquier cosa, actualizar

```powershell
git pull origin main
```

Si esto devuelve conflictos, pare y pregunte. No los resuelva a ojo: hay
archivos generados que **no se fusionan, se regeneran** (ver Paso 7).

---

## Paso 4 — Reconstruir el sitio

Es la secuencia completa, de los datos crudos al sitio desplegable. Tarda menos
de un minuto.

| Objetivo | Comando real | Qué hace |
|---|---|---|
| `make auditoria` | `py src\audit\run_all.py` | Lee `data\raw\`, valida y escribe los intermedios |
| `make factibilidad` | `py src\analysis\indicator_feasibility.py` | Decide qué indicadores se pueden calcular |
| `make artefactos` | `py src\build\build_all.py` | Genera los JSON publicables |
| `make sitio` | `py src\build\06_assemble_site.py` | Ensambla `dist\` |
| `make estado` | `py src\state\snapshot.py` | Regenera `STATE.md` y `docs\DECISIONS.md` |

Para verlo en el navegador:

```powershell
py -m http.server -d dist 8000
```

y abra <http://localhost:8000>. Se detiene con `Ctrl+C`.

**Si algo aborta, léalo.** El build se detiene a propósito cuando una regla
bloqueante falla o cuando la capa interna se colaría al sitio. El mensaje dice
qué y dónde.

---

## Paso 4 bis — Descargar un informe en PDF

Hay dos vías y **una sola maquetación**: las dos imprimen las mismas páginas de
`dist\` con la misma hoja de estilo, así que no pueden divergir. La diferencia
no es el aspecto, es el alcance y quién decide los ajustes.

### La vía normal es el botón, no un comando

En la barra que trae la fecha de vigencia, presente en **todas** las páginas del
sitio, está **«Descargar informe»**. Abre el diálogo de impresión del navegador;
elija **«Guardar como PDF»** como destino.

Imprime **la página en la que está**, con los filtros aplicados y los gráficos
elegidos en el catálogo de indicadores. No hay que repetir nada al descargar: el
recorte y la selección viven en la dirección de la página, y lo que se imprime
es lo que ya está dibujado. Lo que se ve es lo que sale.

Dos ajustes del diálogo, bajo **«Más ajustes»**, cambian el resultado:

| Ajuste | Cómo conviene | Qué pasa si no |
|---|---|---|
| Gráficos de fondo | **Encendido** | Las bandas de aviso pierden su tinte. Se leen igual: conservan su borde y su texto, y los gráficos no dependen de este ajuste porque su color va en el propio SVG |
| Encabezados y pies de página | **Apagado** | Cada hoja añade la dirección y la fecha del navegador sobre el informe |

Tamaño de hoja y márgenes **no** dependen del diálogo: los fija la hoja de
estilo (A4 vertical, regla `@page` en `web\assets\css\app.css`).

**En publicaciones** el botón imprime la página de la tabla que esté viendo, no
las 1.342 filas. Para llevarse esa lista está **«Exportar CSV (todo el recorte)»**,
en la misma página.

### La otra vía: el comando, para el informe completo

El botón resuelve a quien mira una sección y quiere llevársela. No resuelve el
informe completo, igual en cada corrida y archivable, que no puede depender de
que alguien abra un navegador y acierte con los ajustes.

```powershell
node src\build\informe_pdf.mjs dist dist\informe-cienciometrico.pdf
```

En Linux o macOS, `make informe`, que además reconstruye el sitio antes.

Recorre seis páginas —portada, producción, impacto, colaboración, temática y el
anexo metodológico— y deja **un archivo por sección**,
`dist\informe-cienciometrico-*.pdf`. No un PDF único: unir PDF exigiría una
dependencia de manipulación que este proyecto no tiene, y se declara en vez de
fingir un informe de una pieza.

**Deja fuera** publicaciones, autores, las fichas y el catálogo. Son tablas con
filtro y paginación, y volcarlas produciría un anexo de cientos de hojas que
nadie lee.

Numera las hojas y **abre con un índice**: cada sección con su archivo y su
número de hojas, y cada gráfico con la hoja en la que cae. Los números son
reales, leídos del PDF ya compuesto, así que si alguno faltara el comando lo
diría por su código. Ninguna de las dos cosas puede hacerlas el botón: el
navegador no sabe en qué hoja cae nada.

#### El informe que ofrece el sitio

**No hay que hacer nada para eso.** El despliegue compone el informe dentro del
sitio que publica, después de verificarlo, y la portada muestra un bloque con
los seis archivos y sus hojas. Los PDF **no se versionan**: son un derivado del
sitio, y comitearlos habría metido 3,4 MB de binarios por cada carga de datos
además de abrir el hueco de siempre —actualizar los datos, olvidar regenerar el
informe y ofrecer un PDF que contradice a sus propias páginas—.

Si quiere el mismo bloque en su copia local, genere el informe **dentro de
`dist\`**:

```powershell
node src\build\informe_pdf.mjs dist dist\informe\informe-cienciometrico.pdf
```

El generador deja ahí un manifiesto (`dist\data\informe.json`) con lo que de
verdad compuso, y la portada dibuja el bloque sólo si lo encuentra. Si el
informe se compuso con datos más viejos que los del sitio, el bloque lo dice.

**Exige Node y Chromium**, que el Paso 1 no instala porque el sitio no los
necesita. Sólo hacen falta para esto y para `make verificar`:

```powershell
npm install
```

#### El informe a medida

`RECORTE` lleva **la misma consulta que el explorador escribe en la dirección**:
se aplican los filtros en pantalla y se copia lo que va después del `?` en la
barra de direcciones. El cuarto argumento del comando es esa cadena.

| Qué quiere | Con `make` | Argumento en PowerShell |
|---|---|---|
| Un año y un tipo | `make informe RECORTE="anio=2024&tipo=Article"` | `"anio=2024&tipo=Article"` |
| Una unidad académica | `make informe RECORTE="unidad=Facultad de Medicina y Salud"` | `"unidad=Facultad de Medicina y Salud"` |
| Una persona | `make informe RECORTE="autor=Orellana-Donoso M."` | `"autor=Orellana-Donoso M."` |
| Tres gráficos sueltos | `make informe RECORTE="grafico=P-07\|I-04\|T-05"` | `"grafico=P-07\|I-04\|T-05"` |

Es decir, en Windows:

```powershell
node src\build\informe_pdf.mjs dist dist\informe.pdf "unidad=Facultad de Medicina y Salud"
```

El recorte va en el nombre del archivo —dos informes distintos no pueden
llamarse igual en la carpeta de descargas de nadie— y, sobre todo, **declarado
en la hoja 1**, que es lo único que sobrevive a que alguien renombre el archivo.

Con `autor=` de una sola firma, la ficha de esa persona abre el informe y sobre
las cifras aparecen las advertencias de lectura. Una selección de gráficos deja
fuera las secciones que se quedan sin ninguno; la portada y el anexo
metodológico se imprimen siempre.

#### Cuándo hace falta el comando y no el botón

- Necesita el PDF **etiquetado** para lectores de pantalla. El comando lo pide
  explícitamente y dice cuántas secciones lo consiguieron; con el botón depende
  del navegador y de los ajustes de quien imprime, que el sitio no controla.
- Quiere **las seis secciones** de una vez, sin recorrerlas a mano.
- Va a generar **varios informes seguidos**, o generarlos desde un servidor.

Para leer y descargar el suyo, el botón basta.

---

## Paso 5 — Los conectores externos

Consultan API públicas y **no corren en el entorno de desarrollo remoto**, cuya
red las bloquea. Van desde aquí.

```powershell
py src\enrich\ror_institucion.py      # V2-20 · ya ejecutado
py src\enrich\orcid_openalex.py       # V2-19 · unos minutos, 804 DOI
py src\enrich\openalex_cobertura.py   # V2-26 · exige el ror_id
py src\enrich\scopus_api.py           # T-06 · exige SCOPUS_API_KEY
py src\enrich\orcid_afiliacion.py     # T-19 · exige ORCID_CLIENT_ID/SECRET
```

Los cuatro primeros **cachean en disco**: reejecutarlos no vuelve a golpear la
API. `orcid_afiliacion.py` no cachea — cada corrida vuelve a preguntar, porque
el registro de ORCID cambia y ese es justo el punto de correrlo de nuevo. Los
cinco admiten `--test`, que comprueba la lógica sin red y sin credenciales.

Si alguno se detiene diciendo **«el contrato de la API no es el esperado»**, no
insista: deja la respuesta cruda en `data\cache\…\ultima_respuesta.json`, y con
ese archivo se corrige de una vez.

`orcid_openalex.py` **modifica `data\enriched\authors_orcid.csv`**, que es dato
publicable: después hay que rehacer el Paso 4 para que las cifras nuevas lleguen
a las fichas.

Para la verificación contra el registro de ORCID, que sí exige credenciales, use
`scripts\verificar-orcid.ps1` — clic derecho, «Ejecutar con PowerShell».

Para la consulta a la API de Scopus (T-06), que también exige credenciales, use
`scripts\consultar-scopus.ps1` — clic derecho, «Ejecutar con PowerShell». Pide
la API Key en texto visible, prueba la lógica sin red primero, y al final
imprime el bloque para pegar a mano en `config\sources.yml`: el script no lo
escribe solo.

Para ampliar la cobertura de ORCID por afiliación (T-19), use
`scripts\ampliar-orcid-afiliacion.ps1` — clic derecho, «Ejecutar con
PowerShell». Mismas credenciales que `verificar-orcid.ps1`. Deja candidatos
en `internal\orcid_candidatos_afiliacion.csv`; **no asigna nada solo** — para
decidir sobre ellos, corra después `scripts\revisar-identidad.ps1`, que los
recoge en la cola «Candidato por afiliación».

Además del disparo manual, `.github/workflows/ampliar-orcid.yml` corre solo
el día 1 de cada mes (`schedule`, `cron: '0 6 1 * *'`): el registro de ORCID
cambia despacio y una corrida mensual basta. Usa
`ORCID_CLIENT_ID`/`ORCID_CLIENT_SECRET` desde los Secrets del repositorio, no
desde el equipo local, y comitea el resultado sola si hay cambios.

Para revisar la brecha de cobertura que deja `openalex_cobertura.py`
(`V2-26`) — 414 obras que OpenAlex atribuye a la UFT y el universo no
tiene —, use `scripts\revisar-cobertura-openalex.ps1`. Mismo patrón que
`revisar-identidad.ps1`: genera la página, la abre, recoge el CSV
exportado y lo aplica. **No agrega nada al universo publicado**: sólo dejar
constancia, por obra, de si es producción real fuera de Scopus, un error de
atribución de OpenAlex, o un tipo documental excluido a propósito (`D-206`).

---

## Paso 6 — La revisión de identidad

Es la única parte que **no puede automatizarse**: decidir que dos firmas son la
misma persona es una afirmación sobre alguien real, y la decisión `D-08` la
reserva a una persona.

**La vía cómoda**, que hace la secuencia entera:

> `scripts\revisar-identidad.ps1` → clic derecho → **«Ejecutar con PowerShell»**

Comprueba el intérprete, genera la página, la abre en el navegador y, cuando
usted vuelve con el CSV exportado, lo recoge de la carpeta de descargas,
respalda el vigente, lo **fusiona** (`merge_decisions.py`, no lo sobrescribe),
le enseña **en seco** qué aplicaría y sólo entonces aplica y reconstruye.

**Por qué fusiona y no reemplaza.** La página sólo pinta la cola VIVA de
ambigüedades: un caso decidido en una ronda anterior, cuya consolidación hace
que esa ambigüedad ya no vuelva a detectarse, desaparece del formulario — no
porque se haya revocado. Reemplazar `internal\identity_decisions.csv` con la
exportación nueva pierde esas filas en silencio, y como `apply_decisions.py`
regenera `config\identidades_consolidadas.yml` entero en cada corrida, eso
retrocede la consolidación histórica sin ningún aviso. Pasó de verdad el
2026-08-26 (`D-263`, `SESSION_NOTES.md`): 38 grupos comiteados quedaron en 16.

**A mano**, si prefiere:

```powershell
py src\review\build_review.py        # genera la herramienta y las listas
py src\review\build_hallazgos.py     # informe de hallazgos sobre el corpus
```

Abra `internal\revision_identidad.html`, decida, pulse **Exportar decisiones**,
y fusione el archivo descargado con el vigente (NO lo guarde encima):

```powershell
py src\review\merge_decisions.py "C:\ruta\a\identity_decisions.csv"   # fusiona por caso_id
py src\review\apply_decisions.py --dry-run   # qué haría, sin escribir
py src\review\apply_decisions.py             # aplicar de verdad
```

Después, el Paso 4 otra vez.

**Nada se pierde al regenerar.** La auditoría no toca
`internal\identity_decisions.csv`: es su exportación, y la herramienta la lee
para marcar lo que usted ya decidió.

---

## Paso 7 — Qué se commitea y qué no

```powershell
git add -A
git commit -m "descripción de lo que cambió"
git push origin main
```

**Sí se versiona:** `data\enriched\` —dato que costó consultas externas—,
`config\` —incluidas las decisiones humanas aplicadas—, `internal\` y todo lo
de `src\`, `web\` y `docs\`.

**No se versiona:** `data\interim\`, `data\processed\`, `dist\` y
`data\cache\`. Se regeneran; están en `.gitignore`.

**Archivos generados que NUNCA se fusionan a mano:** `STATE.md`,
`docs\DECISIONS.md`, `internal\revision_identidad.html` y las listas de
pendientes. Si dan conflicto, quédese con cualquiera de los dos lados y
**vuelva a generarlos**: un archivo derivado fusionado a mano no corresponde a
ningún estado real.

---

## Paso 8 — Antes de cerrar

```powershell
py src\state\snapshot.py
```

`STATE.md` es el punto de entrada de la sesión siguiente. Si se queda atrás, la
próxima persona —o el próximo asistente— empieza leyendo un mapa viejo.

**Córralo en este equipo, no en un clon limpio.** `STATE.md` se deriva en parte
de `internal\` y de `data\interim\`, que no se versionan: donde no están, el
archivo saldría sin cinco cifras canónicas y sin la tabla de colas de revisión,
y esos huecos se leen como ceros. El guion lo comprueba y **no toca `STATE.md`**
si le faltan insumos: dice qué falta y con qué se rehace. `docs\DECISIONS.md` sí
se regenera siempre, porque su única fuente es `SESSION_NOTES.md`.

Si aun así quiere el archivo a medias, `py src\state\snapshot.py --parcial` lo
escribe declarando en su primera línea qué le falta. No lo commitee encima de
uno completo.

Y escriba en `SESSION_NOTES.md` qué se decidió y por qué. Un mensaje de commit
explica un cambio; el diario explica una sesión, y es lo que se lee dentro de un
mes.

---

## Si algo sale mal

| Síntoma | Qué mirar |
|---|---|
| `py` abre la Microsoft Store | Python no está instalado. Paso 1 |
| `ModuleNotFoundError` | Falta `py -m pip install -r requirements.txt` |
| El build aborta con una regla bloqueante | Es correcto: léala. `docs\VALIDATION_REPORT.md` trae el detalle |
| «la capa interna apareció en dist/» | La compuerta hizo su trabajo. Nada de `internal\` puede viajar al sitio |
| Un conector no alcanza su API | Red o proxy. Los tres declaran qué pasó y qué hacer |
| Las cifras del sitio no cambian | Falta rehacer el Paso 4: `dist\` no se regenera solo |
| El PDF sale con la dirección web en cada hoja | Apague «Encabezados y pies de página» en el diálogo. Paso 4 bis |
| El PDF sale sin los colores de fondo | Encienda «Gráficos de fondo» en el diálogo. Paso 4 bis |
| El PDF descargado trae una sola sección | Es lo que hace el botón: imprime la página que ve. Las seis van con el comando. Paso 4 bis |
| `informe_pdf.mjs` no arranca | Falta `npm install`: Node y Chromium no los instala el Paso 1 |
| `snapshot.py` dice que no toca `STATE.md` | Está bien: le faltan insumos que no se versionan. Córralo donde estén. Paso 8 |

---

## Dónde está lo demás

| Pregunta | Documento |
|---|---|
| Qué falta y qué se decidió | `STATE.md`, y `docs\DECISIONS.md` para el porqué |
| Cómo cargar datos nuevos | `docs\UPDATING.md` |
| Cómo recuperar ORCID | `docs\ORCID_GUIDE.md` y `docs\ORCID_API_GUIDE.md` |
| Qué fuentes se consultan | `docs\FUENTES_Y_APIS.md` |
| Qué límites tienen los datos | `docs\LIMITATIONS.md` |
| Cómo se ve el informe en papel, y por qué así | `docs\UX_UI.md` §12.7 bis |
| Qué explica cada gráfico del informe | `docs\LECTURAS.md` |
| Por qué hay informe por persona, y con qué salvaguardas | `docs\INFORME_POR_INVESTIGADOR.md` |
| Cómo desplegar | `docs\DEPLOYMENT.md` |
| Adaptarlo a otra institución | `docs\REPLICATION.md` |
