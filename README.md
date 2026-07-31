# Plataforma web para informes cienciométricos institucionales

Plataforma abierta y replicable para visualizar producción, impacto,
colaboración y estructura temática de la actividad científica institucional.

**Institución inicial:** Universidad Finis Terrae
**Fuentes:** Scopus y SciVal
**Estado:** Fase 1 completada — auditoría de datos y modelo lógico

---

## Estado del proyecto

| Fase | Alcance | Estado |
|---|---|---|
| 1 | Fundamentos, auditoría de datos y validación | ✅ Completada |
| 2 | Indicadores, arquitectura y UX/UI | ⏳ Pendiente |
| 3 | Implementación, despliegue y replicabilidad | ⏳ Pendiente |

Ver `PLAN.md` para el detalle y los pendientes abiertos.

---

## Estructura

```
config/          Parámetros institucionales y reglas. Punto único de replicabilidad.
data/raw/        Archivos originales. Inmutables.
data/interim/    Salidas de auditoría. Regenerables, no versionadas.
src/audit/       Scripts de auditoría reproducibles.
docs/            Documentación pública: auditoría, modelo, metodología, límites.
internal/        Capa interna: matching, ambigüedades, colas de revisión.
prompts/         Especificaciones de cada fase.
```

---

## Instalación y ejecución

```bash
pip install -r requirements.txt
python3 src/audit/run_all.py
```

La auditoría completa se reconstruye desde `data/raw/` sin pasos manuales.
Los cinco scripts tienen dependencias entre sí y `run_all.py` respeta el orden.

---

## Resultados de la Fase 1

| | |
|---|---|
| Publicaciones en el universo canónico | **823** (2023–2025) |
| Con métricas normalizadas | 816 |
| Con autoría detallada | 818 |
| Formas de firma de autor detectadas | **589** |
| Pares autor × publicación | **1.207** |
| Reglas de validación | **29** · 28 pasan · 0 fallas bloqueantes |

Ver `docs/AUDIT_REPORT.md`.

---

## Documentación

| Documento | Contenido |
|---|---|
| `docs/AUDIT_REPORT.md` | Auditoría completa con cifras verificadas |
| `docs/DATA_MODEL.md` | Modelo lógico, entidades y claves de enlace |
| `docs/METHODOLOGY.md` | Criterios metodológicos que gobiernan todo cálculo |
| `docs/LIMITATIONS.md` | **Limitaciones declaradas. Leer antes de interpretar cualquier indicador** |
| `docs/VALIDATION_REPORT.md` | Resultado de las reglas de validación |

---

## Capas de datos

El proyecto separa estrictamente dos capas (`CLAUDE.md`, `<data_governance>`):

- **Pública** — `docs/`, indicadores publicables, fichas de autor.
- **Interna** — `internal/`: reglas de matching, trazabilidad, ambigüedades,
  colas de revisión humana. **No se publica por defecto** y debe quedar excluida
  del build público en Fase 3.

---

## Replicabilidad

Adaptar la plataforma a otra institución no requiere tocar la lógica de `src/`.
Se cambian tres archivos:

| Archivo | Qué se cambia |
|---|---|
| `config/institution.yml` | Nombre, `scopus_affiliation_id`, ventana temporal, branding |
| `config/matching_rules.yml` | Patrones de detección y vocabulario de unidades |
| `config/sources.yml` | Rutas, fechas de corte y roles de los archivos de datos |

---

## Advertencia de interpretación

Los indicadores de esta plataforma describen **producción indexada en Scopus**,
no productividad académica total. La cobertura de la base no es uniforme entre
disciplinas. Las métricas individuales sobre ventanas cortas y n bajo no son
interpretables aisladamente.

Ver `docs/LIMITATIONS.md` y `docs/METHODOLOGY.md`.
