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
| GitHub Pages | Publicar `dist/` como raíz del sitio |
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
