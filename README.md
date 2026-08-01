# Plataforma web para informes cienciométricos institucionales

Plataforma abierta y replicable para visualizar producción, impacto,
colaboración y estructura temática de la actividad científica institucional.

**Institución inicial:** Universidad Finis Terrae
**Fuentes:** Scopus y SciVal
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
| Firmas con ORCID recuperado desde Crossref | **174** (29,5 %) |
| Reglas de validación | **29** · 28 pasan · 0 fallas bloqueantes |

### Indicadores (Fase 2)

| | |
|---|---|
| Evaluados contra los datos | **40** |
| Publicados en V1 | **27** (26 calculables + 1 placeholder) |
| Diferidos a V2 | 8 |
| No calculables, declarados | 5 |

### Sitio (Fase 3)

| | |
|---|---|
| Páginas | 9 |
| Fichas de autor | **589**, una por archivo |
| Peso total de `dist/` | ~1,9 MB |
| Carga de la portada | ~25 KB |
| Dependencias externas en el navegador | **0** |

---

## Documentación

| Documento | Contenido |
|---|---|
| **`STATE.md`** | **Punto de entrada: estado, cifras y mapa de lectura** |
| `docs/DECISIONS.md` | Índice de las 47 decisiones, una línea cada una |
| `docs/AUDIT_REPORT.md` | Auditoría completa con cifras verificadas |
| `docs/DATA_MODEL.md` | Modelo lógico, entidades y claves de enlace |
| `docs/METHODOLOGY.md` | Criterios metodológicos que gobiernan todo cálculo |
| `docs/LIMITATIONS.md` | **Limitaciones declaradas. Leer antes de interpretar cualquier indicador** |
| `docs/INDICATORS.md` | Catálogo de 40 indicadores y selección V1 |
| `docs/ARCHITECTURE.md` | Pipeline, artefactos y rendimiento |
| `docs/UX_UI.md` | Navegación, KPIs, módulos, filtros y estados |
| `docs/LAYERS.md` | Qué es público y qué es interno |
| `docs/AUTHOR_PROFILE.md` | Estructura de la ficha pública de autor |
| `docs/GLOSSARY.md` | Glosario y ayuda contextual |
| `docs/DEPLOYMENT.md` | Cómo construir y publicar |
| `docs/UPDATING.md` | Cómo incorporar una carga de datos nueva |
| `docs/ORCID_GUIDE.md` | Cómo ejecutar el enriquecimiento de ORCID desde Crossref |
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
  humana. Nunca se despliega, y la exclusión se verifica automáticamente.

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

No hay ninguna cadena institucional escrita en el código
(`grep -ri "finis" src/ web/` devuelve 0). El límite honesto: **los textos
metodológicos de `docs/` citan cifras de esta institución** y deben revisarse
en un despliegue replicado. Ver `docs/REPLICATION.md` §4.

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
