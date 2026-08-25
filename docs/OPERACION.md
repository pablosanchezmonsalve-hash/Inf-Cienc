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

## Paso 5 — Los conectores externos

Consultan API públicas y **no corren en el entorno de desarrollo remoto**, cuya
red las bloquea. Van desde aquí.

```powershell
py src\enrich\ror_institucion.py      # V2-20 · ya ejecutado
py src\enrich\orcid_openalex.py       # V2-19 · unos minutos, 804 DOI
py src\enrich\openalex_cobertura.py   # V2-26 · exige el ror_id
```

Los tres **cachean en disco**: reejecutarlos no vuelve a golpear la API. Y los
tres admiten `--test`, que comprueba la lógica sin red y sin credenciales.

Si alguno se detiene diciendo **«el contrato de la API no es el esperado»**, no
insista: deja la respuesta cruda en `data\cache\…\ultima_respuesta.json`, y con
ese archivo se corrige de una vez.

`orcid_openalex.py` **modifica `data\enriched\authors_orcid.csv`**, que es dato
publicable: después hay que rehacer el Paso 4 para que las cifras nuevas lleguen
a las fichas.

Para la verificación contra el registro de ORCID, que sí exige credenciales, use
`scripts\verificar-orcid.ps1` — clic derecho, «Ejecutar con PowerShell».

---

## Paso 6 — La revisión de identidad

Es la única parte que **no puede automatizarse**: decidir que dos firmas son la
misma persona es una afirmación sobre alguien real, y la decisión `D-08` la
reserva a una persona.

**La vía cómoda**, que hace la secuencia entera:

> `scripts\revisar-identidad.ps1` → clic derecho → **«Ejecutar con PowerShell»**

Comprueba el intérprete, genera la página, la abre en el navegador y, cuando
usted vuelve con el CSV exportado, lo recoge de la carpeta de descargas,
respalda el anterior, le enseña **en seco** qué aplicaría y sólo entonces aplica
y reconstruye.

**A mano**, si prefiere:

```powershell
py src\review\build_review.py        # genera la herramienta y las listas
py src\review\build_hallazgos.py     # informe de hallazgos sobre el corpus
```

Abra `internal\revision_identidad.html`, decida, pulse **Exportar decisiones**,
guarde el archivo como `internal\identity_decisions.csv` y aplique:

```powershell
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

---

## Dónde está lo demás

| Pregunta | Documento |
|---|---|
| Qué falta y qué se decidió | `STATE.md`, y `docs\DECISIONS.md` para el porqué |
| Cómo cargar datos nuevos | `docs\UPDATING.md` |
| Cómo recuperar ORCID | `docs\ORCID_GUIDE.md` y `docs\ORCID_API_GUIDE.md` |
| Qué fuentes se consultan | `docs\FUENTES_Y_APIS.md` |
| Qué límites tienen los datos | `docs\LIMITATIONS.md` |
| Cómo desplegar | `docs\DEPLOYMENT.md` |
| Adaptarlo a otra institución | `docs\REPLICATION.md` |
