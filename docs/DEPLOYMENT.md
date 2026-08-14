# Despliegue

**Capa:** técnica · **Fase:** 3

El sitio es estático: HTML, CSS, JavaScript y JSON. Sin backend, sin base de
datos, sin proceso servidor, sin variables de entorno en tiempo de ejecución.

---

## 1. Requisitos

- Python 3.11 o superior.
- `pip install -r requirements.txt` (pandas, openpyxl, PyYAML, rdata).
- Nada más. El sitio no usa Node, ni npm, ni un generador de sitios.

**Sin dependencias de terceros en el navegador.** No se carga ninguna fuente,
hoja de estilo ni librería desde un CDN. Los gráficos son SVG generados en el
propio JavaScript. Esto es deliberado: los datos son institucionales y el sitio
debe poder servirse en una red cerrada.

---

## 2. Construir

```bash
pip install -r requirements.txt

python3 src/audit/run_all.py                    # 1. auditoría y validación
python3 src/analysis/indicator_feasibility.py   # 2. factibilidad de indicadores
python3 src/build/build_all.py                  # 3. artefactos publicables
python3 src/build/06_assemble_site.py           # 4. sitio desplegable
```

O en un solo paso:

```bash
make sitio
```

El resultado queda en `dist/`. **Eso es todo lo que se despliega.**

### Compuertas del proceso

El build se detiene solo si algo está mal. No son avisos:

| Compuerta | Qué verifica | Si falla |
|---|---|---|
| `require_validation()` | La auditoría corrió y no hay reglas bloqueantes fallando | Aborta el build |
| `05_verify_public_layer` | Ningún artefacto público contiene campos de la capa interna | Aborta con código ≠ 0 |
| `06_assemble_site` | `data/raw/` e `internal/` no aparecen en `dist/` | Aborta el ensamblado |

---

## 3. Probar en local

```bash
python3 -m http.server -d dist 8000
```

Abrir `http://localhost:8000`.

**Debe servirse por HTTP, no abrirse como archivo.** El sitio usa módulos ES y
`fetch`; con `file://` el navegador los bloquea por política de origen.

---

## 4. Publicar

`dist/` se sirve desde cualquier hosting de archivos estáticos. Ninguna opción
requiere cambios en el código.

| Destino | Cómo |
|---|---|
| Servidor web institucional | Copiar `dist/` al directorio público (`rsync -av --delete dist/ servidor:/var/www/informe/`) |
| **GitHub Pages** | **Automatizado.** `.github/workflows/deploy.yml` reconstruye y publica en cada push a `main`. Requiere activar Pages en Settings → Pages → Source: GitHub Actions |
| Netlify / Cloudflare Pages | Directorio de publicación: `dist`; comando de build: el del §2 |
| Red interna sin salida | Copiar `dist/` a un recurso compartido y servirlo con cualquier servidor de archivos |

### Cabeceras recomendadas

| Ruta | Cache-Control | Razón |
|---|---|---|
| `*.html` | `no-cache` | Para que una actualización se vea de inmediato |
| `assets/*` | `max-age=604800` | Cambian poco |
| `data/*.json` | `max-age=3600` | Se regeneran con cada carga de datos |

Si el hosting permite una política de seguridad de contenido, el sitio funciona
con una estricta, porque no carga nada externo:

```
Content-Security-Policy: default-src 'self'; img-src 'self' data:; style-src 'self'
```

---

## 4 bis. Despliegue automatizado

`.github/workflows/deploy.yml` ejecuta el mismo pipeline que en local y publica
en GitHub Pages con cada push a `main`.

### Dos disparadores: se verifica antes y después, se publica sólo después

El workflow tiene dos jobs y no corren en los mismos casos:

| Job | `pull_request` | `push` a `main` | `workflow_dispatch` |
|---|---|---|---|
| `construir` — pipeline, autopruebas y verificación | **sí** | sí | sí |
| `desplegar` — publica en Pages | **no** | sí | sí |

Antes la compuerta corría **sólo** al empujar a `main`, es decir después de
fusionar: ningún pull request se validaba antes de entrar, y el primero que
rompiera una regla bloqueante lo haría sobre la rama publicada. Ahora el mismo
job de verificación corre en las dos situaciones y lo único reservado a `main`
es la publicación.

Las corridas de pull request además:

- se **cancelan entre sí** por rama (de tres empujones seguidos sólo interesa el
  veredicto del último), mientras que los despliegues se serializan y nunca se
  cancelan: interrumpir una publicación a medias deja el sitio en un estado que
  nadie eligió;
- **no tocan Pages**. Los pasos `configure-pages` y `upload-pages-artifact` se
  saltan, y los permisos de escritura sobre Pages viven en cada job en vez de en
  la cabecera del workflow.

### Qué comprueba

Además del pipeline y de las compuertas de la sección siguiente:

| Paso | Qué ejerce |
|---|---|
| Autopruebas de los cuatro módulos de ORCID | Qué identificador se atribuye a qué persona |
| Autoprueba de `apply_decisions` (20 casos) | Qué firmas se fusionan como una persona y cuáles dejan de contarse |
| Contenido sin JavaScript | Que el pre-renderizado ocurrió de verdad |
| Barrera pública/interna | Que nada de `internal/` viaja en `dist/` |
| `src/verify/run_all.mjs` | Contraste WCAG, estructura, consola, flujos, responsive e higiene |

La batería de `src/verify/` existía desde `D-137` pero había que acordarse de
correrla a mano, que es la forma que tiene una verificación de no correrse. La
versión de Playwright se fija en el workflow —no en un `package.json`, porque el
sitio no tiene dependencias de JavaScript— y es la misma con la que se verifica
en local: una batería que corre contra otro navegador no comprueba lo mismo.

### Activación: un paso manual, una sola vez

> **Settings → Pages → Build and deployment → Source: `GitHub Actions`**

**Esto no se puede automatizar.** Se intentó con `enablement: true` en el
workflow y GitHub respondió:

```
Create Pages site failed. Error: Resource not accessible by integration
```

El `GITHUB_TOKEN` del workflow puede **publicar** en un sitio de Pages que ya
existe, pero no puede **crearlo**. Hacerlo requeriría un token personal con
permiso de administración del repositorio, que no compensa introducir —y
custodiar— para un paso que se hace una vez.

La otra condición, ya cumplida en este repositorio: **Pages requiere que el
repositorio sea público**, o una cuenta con plan de pago (Pro, Team o
Enterprise).

Mientras Pages no esté activado, el workflow **falla sólo en el último paso**.
Todo lo anterior —auditoría, 30 reglas de validación, autopruebas, build y
verificación de capas y del sitio— se ejecuta igual, y los informes quedan
disponibles como artefactos de la ejecución. Lo único que no ocurre es la
publicación.

El workflow reproduce las mismas compuertas y añade una verificación extra en
CI: falla si `internal/`, `data/raw/` o cualquier rastro de las colas de
revisión aparece en `dist/`. Publica además `VALIDATION_REPORT.md` y
`BUILD_VERIFICATION.md` como artefactos de cada ejecución, de modo que queda
registro de qué se validó en cada despliegue.

---

## 5. Qué NO se despliega

Verificado automáticamente por `06_assemble_site.py`:

- `data/raw/` — exports originales de Scopus y SciVal (ver `docs/DATA_LICENSE.md`).
- `internal/` — log de matching, colas de ambigüedad.
- `data/interim/` — salidas de auditoría intermedias.
- `src/`, `config/`, `docs/`, `prompts/`.

---

## 6. Rendimiento observado

Sobre el build actual (823 publicaciones, 589 fichas):

| | |
|---|---|
| Peso total de `dist/` | ~1,9 MB |
| Carga de la portada | `meta.json` + `kpis.json` + `glossary.json` ≈ 25 KB |
| Página de publicaciones | + `publications.json` ≈ 700 KB |
| Ficha de autor | + un archivo de ~5 KB |

La portada no descarga el corpus. Cada módulo pide su artefacto al abrirse.

**Límite conocido:** el filtrado ocurre en el navegador sobre
`publications.json`. Con este corpus es instantáneo. El supuesto deja de valer
alrededor de las ~10.000 publicaciones, punto en el que haría falta un índice
precomputado o paginación servida.

---

## 7. Accesibilidad y compatibilidad

- Requiere un navegador con módulos ES (Chrome/Edge 61+, Firefox 60+, Safari 11+).
- Enlace de salto al contenido, navegación por teclado, `aria-sort` en las
  tablas ordenables.
- Los tooltips responden a foco además de a puntero: de otro modo no existirían
  por teclado ni en móvil.
- Cada gráfico tiene una tabla de datos equivalente desplegable.
- Tema claro y oscuro según la preferencia del sistema.
