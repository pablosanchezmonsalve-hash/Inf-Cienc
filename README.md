# Plataforma web para informes bibliométricos institucionales

Plataforma abierta y replicable para visualizar producción, impacto,
colaboración y estructura temática de la actividad científica institucional.

**Institución inicial:** Universidad Finis Terrae
**Fuentes primarias:** Scopus y SciVal · **enriquecimiento:** Crossref, ORCID, OpenAlex
**Estado:** V1 completa — entregable técnico funcional

---

## Estado del proyecto

| Fase | Alcance | Estado |
|---|---|---|
| 1 | Fundamentos, auditoría de datos y validación | ✅ Completada |
| 2 | Indicadores, arquitectura y UX/UI | ✅ Completada |
| 3 | Implementación, despliegue, documentación y replicabilidad | ✅ Completada |

**Para retomar el trabajo, leer `STATE.md`**: punto de entrada generado, con las
cifras vigentes, los pendientes abiertos y un mapa de qué documento abrir para
cada pregunta. Se regenera con `make estado`.

Ver `PLAN.md` para el detalle por fase y `docs/V2_BACKLOG.md` para lo que sigue.

---

## Inicio rápido

```bash
make instalar     # dependencias de Python
make sitio        # auditoría → validación → artefactos → sitio en dist/
make servir       # http://localhost:8000
```

Sin Node, sin npm, sin generador de sitios. **El navegador no carga nada desde
un CDN**: los gráficos son SVG generados en el propio JavaScript. Los datos son
institucionales y el sitio debe poder servirse en una red cerrada.

---

## Estructura

```
config/          Parámetros institucionales y reglas. Punto único de replicabilidad.
data/raw/        Archivos originales. Inmutables. No se despliegan.
data/interim/    Salidas de auditoría. Regenerables.
data/processed/  Artefactos JSON publicables. Regenerables.
src/audit/       Auditoría y validación (Fase 1).
src/analysis/    Factibilidad de indicadores (Fase 2).
src/build/       Construcción de artefactos y ensamblado del sitio (Fase 3).
web/             Interfaz estática.
dist/            Sitio ensamblado. Lo único que se despliega.
docs/            Documentación pública.
internal/        Capa interna: matching, ambigüedades. No se despliega.
prompts/         Especificaciones de cada fase.
scripts/         Asistentes de ejecución para Windows.
```

---

## Pipeline

```
data/raw/  →  src/audit/  →  data/interim/  →  src/build/  →  data/processed/  →  dist/
(inmutable)   (29 reglas)     (validado)       (compuertas)    (publicable)      (desplegable)
```

Tres compuertas detienen el proceso si algo está mal, no avisan:

| Compuerta | Verifica |
|---|---|
| `require_validation()` | La auditoría corrió sin reglas bloqueantes fallando |
| `05_verify_public_layer` | Ningún artefacto público contiene campos de la capa interna |
| `06_assemble_site` | `data/raw/` e `internal/` no aparecen en `dist/` |

---

## Resultados

### Datos (Fase 1)

| | |
|---|---|
| Publicaciones en el universo canónico | **823** (2023–2025) |
| Con métricas normalizadas | 816 |
| Con autoría detallada | 818 |
| Formas de firma de autor | **589** |
| Pares autor × publicación | **1.207** |
| Firmas con ORCID (sin consolidar) | **328** |
| Entidades publicadas con ORCID | **252** |
| Reglas de validación | **30** · 29 pasan · 0 fallas bloqueantes |

### Indicadores (Fase 2)

| | |
|---|---|
| Evaluados contra los datos | **43** |
| Publicados | **31** |
| Diferidos a V2 | 7 |
| No calculables, declarados | 5 |

### Sitio (Fase 3)

| | |
|---|---|
| Páginas | 11 |
| Fichas de autor | **513**, una por archivo |
| Peso total de `dist/` | ~3,6 MB |
| Dependencias externas en el navegador | **0** |

Peso por página, medido en navegador. La segunda columna es lo que realmente
viaja: GitHub Pages sirve con gzip, y estos artefactos son JSON muy repetitivo.

| Página | Sin comprimir | **Transferido** | Qué domina |
|---|---|---|---|
| Portada | 107 KB | **~29 KB** | CSS 33 · `paginas.js` 30 · `core.js` 22 · `series.json` 11 |
| Impacto y demás módulos | 105 KB | **~28 KB** | lo mismo, sin `kpis.json` |
| Autores | 267 KB | **~44 KB** | `authors.json` 171 → 14 KB |
| Publicaciones | 808 KB | **~181 KB** | `publications.json` 699 → 146 KB |

`publications.json` comprime al **20 %** de su tamaño y `authors.json` al **8 %**.
Las dos tablas grandes cargan su conjunto completo porque el filtrado ocurre en
el cliente, sin servidor que consultar; a 146 KB comprimidos eso es un precio
razonable por filtrar 823 publicaciones sin una sola petición más.

El armazón común —hoja de estilo, motor de gráficos y glosario, unos 26 KB
comprimidos— lo cachea el navegador entre páginas.

---

## Documentación

| Documento | Contenido |
|---|---|
| **`STATE.md`** | **Punto de entrada: estado, cifras y mapa de lectura** |
| `docs/DECISIONS.md` | Índice de las 400 decisiones, una línea cada una |
| `docs/AUDIT_REPORT.md` | Auditoría completa con cifras verificadas |
| `docs/DATA_MODEL.md` | Modelo lógico, entidades y claves de enlace |
| `docs/METHODOLOGY.md` | Criterios metodológicos que gobiernan todo cálculo |
| `docs/METODOLOGIA_FUERA_DE_SCOPUS.md` | Cómo se clasifica y publica una fuente que no es Scopus/SciVal |
| `docs/LIMITATIONS.md` | **Limitaciones declaradas. Leer antes de interpretar cualquier indicador** |
| `docs/INDICATORS.md` | Catálogo de 43 indicadores y selección V1 |
| `docs/FUENTES_Y_APIS.md` | De dónde sale cada dato hoy, y qué plataformas podrían aportar lo que falta |
| `docs/ORCID_COVERAGE.md` | Cobertura de ORCID: hasta dónde llega y por qué no llega al 100 % |
| `docs/ARCHITECTURE.md` | Pipeline, artefactos y rendimiento |
| `docs/UX_UI.md` | Navegación, KPIs, módulos, filtros y estados |
| `docs/LAYERS.md` | Qué es público y qué es interno |
| `docs/AUTHOR_PROFILE.md` | Estructura de la ficha pública de autor |
| `docs/GLOSSARY.md` | Glosario y ayuda contextual |
| `docs/EJES.md` | Qué pregunta responde cada sección, y cuál no |
| `docs/OPERACION.md` | Cómo se opera el proyecto, paso a paso |
| `docs/DEPLOYMENT.md` | Cómo construir y publicar |
| `docs/UPDATING.md` | Cómo incorporar una carga de datos nueva |
| `docs/UPDATING_REQUEST.md` | Qué pedir en la próxima exportación de datos |
| `docs/ORCID_GUIDE.md` | Cómo ejecutar el enriquecimiento de ORCID desde Crossref |
| `docs/ORCID_API_GUIDE.md` | Cómo verificar los ORCID contra el registro público |
| `docs/DESIGN_SYNC_GUIDE.md` | Cómo integrar un proyecto de Claude Design |
| `src/verify/run_all.mjs` | Batería de verificación del sitio (`make verificar`) |
| `src/design/validar_paleta.py` | Validador del sistema cromático |
| `docs/REPLICATION.md` | Cómo adaptar el sistema a otra institución |
| `docs/DATA_LICENSE.md` | Uso de datos institucionales |
| `docs/V2_BACKLOG.md` | Pendientes de la siguiente versión |
| `docs/VALIDATION_REPORT.md` | Salida de las reglas de validación |
| `docs/BUILD_VERIFICATION.md` | Salida de la verificación de capas |

---

## Capas de datos

El proyecto separa estrictamente dos capas (`CLAUDE.md`, `<data_governance>`):

- **Pública** — `docs/`, `data/processed/`, el sitio.
- **Interna** — `internal/`: reglas de matching, trazabilidad, colas de revisión
  humana. **Nunca llega al sitio**, y la exclusión se verifica en cada build y
  otra vez en el despliegue.

«Interna» sigue significando *fuera del sitio*: la exclusión de `internal/` de
`dist/` se verifica en cada build y otra vez en el despliegue. El repositorio es
**privado**, de modo que `data/raw/` (exports de Elsevier) y `internal/` no son
descargables por terceros; la decisión de renunciar al repositorio público para
cerrar la exposición de los exportes se tomó en la auditoría de 2026-09-01. El
razonamiento sobre por qué unos archivos internos se mantuvieron en el repo, y
las condiciones que habrían obligado a revisarlo, queda registrado en
`internal/README.md`.

El criterio: **público lo que describe un resultado, interno lo que describe
cómo se llegó a él.** Los nombres de autor son públicos —están en Scopus—, pero
la cola que los agrupa como posibles duplicados no lo es: publicarla afirmaría
una identidad no verificada sobre personas reales.

---

## Replicabilidad

Adaptar la plataforma a otra institución no requiere tocar `src/` ni `web/`.
Se cambian cuatro archivos de configuración:

| Archivo | Qué se cambia |
|---|---|
| `config/institution.yml` | Nombre, `scopus_affiliation_id`, ventana temporal, branding |
| `config/matching_rules.yml` | Patrones de detección y vocabulario de unidades |
| `config/sources.yml` | Rutas, fechas de corte y roles de los archivos |
| `config/indicators.yml` | Qué indicadores se publican y con qué advertencias |

Esto se verifica, no se afirma: `grep -ri "finis" src/ web/` devuelve 0, y
también los nombres de hoja del libro Excel de validación, la columna de autor y
la ventana de ese archivo viven en `config/sources.yml`. La auditoría del
2026-08-01 encontró que sólo la cadena «finis» se había comprobado, y que
`Publicaciones_UFT_detalle` y un `>= 2024` seguían escritos en `src/`; ambos
están ahora en configuración.

Dos límites honestos, ninguno resuelto por configuración:

- **Los textos metodológicos de `docs/` citan cifras de esta institución** y
  deben revisarse en un despliegue replicado.
- **`src/audit/04_author_population.py` supone que existe un set de validación
  manual** con la forma del libro Excel de esta institución. Otra institución
  que no lo tenga no necesita reescribirlo, pero sí omitir ese paso.

Ver `docs/REPLICATION.md` §4.

---

## Licencia

- **Software** (`src/`, `web/`, estructura de `config/`): MIT — ver `LICENSE`.
- **Datos**: no cubiertos por MIT. Ver `docs/DATA_LICENSE.md`.

---

## Advertencia de interpretación

Los indicadores describen **producción indexada en Scopus**, no productividad
académica total. La cobertura de la base no es uniforme entre disciplinas. Las
métricas individuales sobre ventanas cortas y n bajo no son interpretables
aisladamente.

Este informe adhiere a los principios de **DORA** y del **Manifiesto de
Leiden**. Ver `docs/LIMITATIONS.md` y `docs/METHODOLOGY.md`.
