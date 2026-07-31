# Replicabilidad

**Capa:** técnica · **Fase:** 3

`PROJECT_SPEC.md` define «replicable» como: parametrizable para otra
institución, documentado para despliegue independiente, adaptable a nuevas
cargas sin reescribir la lógica base, y separable entre software reutilizable y
datos institucionales.

Este documento explica cómo se cumple cada punto y qué límites tiene.

---

## 1. Separación software / datos

| Reutilizable (no depende de la UFT) | Institucional (propio de cada organización) |
|---|---|
| `src/` — auditoría, análisis y build | `data/raw/` — exports de Scopus y SciVal |
| `web/` — interfaz | `data/interim/`, `data/processed/` — derivados |
| `docs/` metodológicos | `internal/` — colas de revisión |
| Estructura de `config/` | **Valores** dentro de `config/` |

Ninguna cadena institucional está escrita en el código. `src/` lee el nombre,
el identificador de afiliación y los patrones de detección desde `config/`.

---

## 2. Los cuatro archivos que se cambian

### `config/institution.yml`

```yaml
institucion:
  nombre_canonico: "<Nombre de la institución>"
  nombre_corto: "<Sigla>"
  scopus_affiliation_id: "<ID de afiliación en Scopus>"   # clave del método duro
ventana_temporal:
  anio_inicio: <año>
  anio_fin: <año>
presentacion:
  titulo_plataforma: "<Título>"
  color_primario: "#RRGGBB"
```

**Cómo obtener el `scopus_affiliation_id`:** buscar la institución en Scopus;
el identificador aparece en la URL del perfil de afiliación. En este proyecto es
`60105368`, presente en 816 de 818 registros del export de SciVal.

### `config/matching_rules.yml`

El patrón de detección textual y el vocabulario de unidades académicas:

```yaml
metodo_blando:
  patrones:
    - '\b<primera palabra>[\s\-]+<segunda palabra>\b'
```

**Advertencia heredada de la Fase 1:** el patrón debe llevar límite de palabra.
En este proyecto, usar la subcadena `inis` en lugar de `\bfinis[\s\-]+terrae\b`
producía 15 cadenas de falso positivo («Ministerio de Salud», «Faculty of
Economics and Business»). El separador admite guion porque
`Universidad Finis-Terrae` existe en los datos.

Otra institución debe repetir esta verificación con su propio nombre, no
asumirla. El script `03_affiliation_variants.py` la ejecuta y la reporta.

### `config/sources.yml`

Rutas, fechas de corte, ventana declarada y rol de cada archivo.

### `config/indicators.yml`

Qué indicadores se publican, con qué denominador y con qué advertencias. Una
institución con cobertura distinta puede necesitar activar o desactivar
indicadores sin tocar el build.

---

## 3. Procedimiento completo

```bash
git clone <repositorio> informe-cienciometrico
cd informe-cienciometrico

rm data/raw/*                      # retirar los datos de la institución anterior
cp <sus exports> data/raw/

$EDITOR config/institution.yml     # nombre, ID de afiliación, ventana, branding
$EDITOR config/sources.yml         # rutas y fechas de corte
$EDITOR config/matching_rules.yml  # patrón institucional y unidades

pip install -r requirements.txt
python3 src/audit/run_all.py       # revisar la salida antes de seguir
```

La auditoría dirá si el matching funciona. Tres señales:

1. **Publicaciones sin detección institucional** debe ser 0.
2. **Casos «sólo método duro»** debe ser 0 o tener explicación estructural.
3. **Falsos positivos de los patrones prohibidos** confirma que el patrón
   estricto es necesario.

Luego actualizar los denominadores en `config/indicators.yml` con las cifras
reales y construir:

```bash
python3 src/analysis/indicator_feasibility.py
python3 src/build/build_all.py
python3 src/build/06_assemble_site.py
```

---

## 4. Qué se adapta solo y qué no

### Se adapta solo

- Cifras, series y facetas: todo se recalcula desde los datos.
- Textos de la interfaz que citan números (denominadores, fechas de corte,
  ventana): se leen de `meta.json`.
- Fichas de autor: una por firma detectada.
- Glosario: se serializa desde `docs/GLOSSARY.md`.

### No se adapta solo

| Elemento | Por qué | Qué hacer |
|---|---|---|
| Vocabulario de unidades académicas | Cada institución tiene su estructura | Reescribir la sección en `matching_rules.yml` |
| Cifras dentro de los textos de `docs/` | Son prosa, no plantillas | Revisar `LIMITATIONS.md`, `METHODOLOGY.md` y `GLOSSARY.md` |
| Advertencias específicas en `indicators.yml` | Mencionan coberturas concretas | Ajustar tras la primera auditoría |
| Idioma de la interfaz | La V1 está sólo en español | Pendiente V2 |

**Este es el límite honesto de la replicabilidad actual:** el código y la
estructura son reutilizables sin cambios, pero **los textos metodológicos citan
cifras de esta institución** y hay que revisarlos. Un despliegue que copie
`LIMITATIONS.md` sin adaptarlo publicaría datos incorrectos.

---

## 5. Verificación de un despliegue replicado

| Comprobación | Cómo | Esperado |
|---|---|---|
| Sin cadenas institucionales en el código | `grep -ri "finis" src/ web/` | Sólo comentarios explicativos |
| Detección institucional funciona | salida de `03_affiliation_variants.py` | 0 publicaciones sin detección |
| Barrera de capas | `docs/BUILD_VERIFICATION.md` | Sin fallas |
| Denominadores coherentes | `config/indicators.yml` vs. `reconciliation_summary.csv` | Iguales |
| Textos revisados | lectura de `docs/LIMITATIONS.md` | Sin cifras de la institución anterior |
