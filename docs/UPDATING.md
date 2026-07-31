# Actualización de datos

**Capa:** técnica · **Fase:** 3

Cómo incorporar un nuevo período o un export corregido. **Ningún paso requiere
editar código.**

---

## 1. Procedimiento

### Paso 1 — Depositar los exports

Copiar los archivos nuevos a `data/raw/`. No borrar los anteriores: la
trazabilidad depende de conservarlos.

### Paso 2 — Declararlos en `config/sources.yml`

```yaml
scopus_export:
  archivo: "data/raw/<nuevo archivo>.csv"
  fecha_corte: "AAAA-MM-DD"     # si el export la declara
  fecha_export: "AAAA-MM-DD"
  ventana_declarada: "2023-2026"
  n_registros_declarado: <n>
```

Si el export de SciVal cambia el número de filas de metadatos, ajustar
`header_row`. La regla `E-03` falla ruidosamente si no coincide, en vez de
producir una tabla corrida en silencio.

### Paso 3 — Ajustar la ventana temporal

En `config/institution.yml`:

```yaml
ventana_temporal:
  anio_inicio: 2023
  anio_fin: 2026
```

### Paso 4 — Reejecutar la auditoría

```bash
python3 src/audit/run_all.py
```

**Revisar la salida antes de seguir.** Interesan tres cosas:

1. Reglas bloqueantes fallando → hay que resolverlas; el build no correrá.
2. `I-04` (reconciliación de métodos de detección) → si aparecen casos «sólo
   método duro», hay publicaciones institucionales sin autor identificable.
3. El recuento de ambigüedades nuevas en `internal/`.

### Paso 5 — Revisar las colas de ambigüedad

`internal/ambiguities_authors.csv` y `internal/ambiguities_publications.csv`
crecen con cada carga. Las entradas nuevas necesitan revisión humana: el
sistema no las resuelve por su cuenta y no debe hacerlo.

### Paso 6 — Actualizar los denominadores

`config/indicators.yml` declara los denominadores usados en la interfaz:

```yaml
denominadores:
  universo_total: 823
  con_metricas: 816
  con_autoria_detallada: 818
```

Tomar los valores nuevos de la salida del paso 4 (`reconciliation_summary.csv`).

> Este paso es manual **a propósito**. Cambiar el denominador de todos los
> indicadores publicados es una decisión, no un efecto secundario de copiar un
> archivo.

### Paso 7 — Reconstruir y desplegar

```bash
python3 src/analysis/indicator_feasibility.py
python3 src/build/build_all.py
python3 src/build/06_assemble_site.py
```

Revisar `docs/VALIDATION_REPORT.md` y `docs/BUILD_VERIFICATION.md`, y desplegar
`dist/` según `docs/DEPLOYMENT.md`.

---

## 2. Qué revisar siempre después de una carga

| Comprobación | Dónde | Por qué |
|---|---|---|
| Reglas bloqueantes en 0 | `docs/VALIDATION_REPORT.md` | Compuerta del build |
| Barrera de capas sin fallas | `docs/BUILD_VERIFICATION.md` | Nada interno en lo público |
| Publicaciones sin detección institucional | salida de `03_affiliation_variants` | Debe ser 0 |
| Variantes de unidad fuera del vocabulario | `data/interim/academic_unit_vocabulary.csv` | Un período nuevo trae formas nuevas |
| Fecha de corte visible en el sitio | barra de vigencia | Si no cambió, el build tomó datos viejos |

---

## 3. Cambios que sí requieren tocar configuración

| Situación | Archivo | Qué cambiar |
|---|---|---|
| Aparece una variante institucional nueva | `config/matching_rules.yml` | Añadir el patrón; **nunca** relajar a subcadena suelta |
| Aparece una facultad nueva | `config/matching_rules.yml` | Añadirla al vocabulario controlado |
| Se quiere publicar un indicador diferido | `config/indicators.yml` | `publicar: true` |
| Se quiere ocultar un indicador | `config/indicators.yml` | `publicar: false` |
| Cambia el criterio de fichas de autor | `config/publication.yml` | `n_minimo_ranking_por_defecto` |

---

## 4. Adaptar el sistema a otra institución

Ver `docs/REPLICATION.md`. En resumen: cambiar cuatro archivos de `config/`,
reemplazar `data/raw/` y ejecutar el pipeline. La lógica de `src/` no se toca.

---

## 5. Errores frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `BUILD ABORTADO: falta validation_report.csv` | No se corrió la auditoría | Ejecutar `src/audit/run_all.py` |
| `E-03: cabecera inesperada en SciVal` | El export cambió sus filas de metadatos | Ajustar `header_row` en `config/sources.yml` |
| El sitio muestra datos viejos | Caché del navegador o `dist/` sin reensamblar | Reejecutar el paso 7 y recargar sin caché |
| Las páginas quedan en blanco | Se abrió con `file://` | Servir por HTTP (`python3 -m http.server -d dist`) |
| Cifras del sitio ≠ cifras de la auditoría | `denominadores` desactualizados | Paso 6 |
