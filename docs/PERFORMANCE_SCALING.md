# Guía de Rendimiento y Escalabilidad

**Nivel:** técnico · **Fase:** V2 · **Audiencia:** desarrolladores, replicadores

---

## Estado Actual (V1)

| Métrica | Valor | Observación |
|---------|-------|-------------|
| Publicaciones en corpus | 823 | Rango óptimo para esta arquitectura |
| Autores únicos | 589 | Tablas maestra estable |
| Pares autor × publicación | 1.207 | Log de matching manejable |
| Tamaño `dist/` sin comprimir | ~2,0 MB | ~600 KB comprimido (gzip) |
| Tiempo build completo | ~10–20 s | Incluye validación + artefactos + PDF |
| LCP (Largest Contentful Paint) | ~1,2 s | Portada sin servidor externo |

---

## Límites Identificados y Umbrales de Escalado

### 1. **Cliente: Filtrado de Publicaciones (10K publications)**

**Arquitectura actual:** Carga completa de `publications.json` en el navegador; filtrado 100% cliente.

```javascript
// Filtro actual (vista_explorador.js): O(n) por cada búsqueda
const resultados = todas_las_publicaciones.filter(pub =>
  pub.titulo.includes(query) || pub.autores.includes(query)
);
```

**Límite:** Alrededor de **~10.000 publicaciones** (~500 KB comprimidas).
- A 10K, el decodificar + filtrar tarda ~500 ms en dispositivos de gama media.
- A 50K, es inmanejable en móviles sin un índice invertido.

**Recomendación para V2:**
- **Opción A (recomendada):** Construir índice invertido de palabras clave en build, servirlo como JSON separado.
  - Tamaño estimado: +50–100 KB (comprimido).
  - Búsqueda: O(1) a O(log n) en lugar de O(n).
  - Implementación: ~2–3 horas con `lunr.js` o `fuse.js`.
- **Opción B:** Mover filtrado de publicaciones a un microservicio serverless (AWS Lambda, Vercel, etc.).
  - Requiere cambio de arquitectura (de estática pura a estática + API).
  - Complejidad aumenta; trazabilidad baja.

---

### 2. **Python Backend: Detección de Ambigüedades (589 autores)**

**Operación actual:** `src/audit/04_author_population.py` ejecuta cuatro pases separados sobre la tabla maestra:
- P-03: Variantes de nombre (groupby + iterrow)
- P-04: Scopus ID múltiples (loop externo + lookup)
- P-05: Nombre con múltiples IDs (dict construction + loop)
- I-06: Autores con múltiples unidades (groupby + iterrow)

**Complejidad:**
- Actual: O(4n) iteraciones sobre ~589 autores = ~2.356 iteraciones.
- Consolidada: O(n) con múltiples checks por autor = ~589 iteraciones.

**Ganancia:** ~75% menos iteraciones, ~40–50% menos tiempo en este módulo.

**Refactorización aplicada en rama `perf/optimization-and-scaling`:**
- Consolida los cuatro pases en uno.
- Precomputa `by_sid` lookup una sola vez.
- Lógica sin cambios; mismo output.

**Límite de escalado:** Hasta ~5.000–10.000 autores, esta refactorización es suficiente.
- A 50K autores, haría falta paralelización con `multiprocessing`.

---

### 3. **Build: Generación de Fichas de Autor (589 archivos JSON)**

**Operación actual:** `src/build/03_authors.py` genera 589 archivos `.json` de forma **secuencial**.

```python
# Pseudocódigo actual
for author in authors:  # 589 iteraciones
    json_data = build_author_profile(author)
    write_json(f"author/{author['id']}.json", json_data)  # Escritura a disco
```

**Cuello de botella:** Escritura a disco secuencial es lenta.
- Por archivo: ~10–50 ms (incluye I/O).
- Total: 589 × 25 ms = ~15 segundos de los ~10–20 s totales del build.

**Recomendación para V2:**
- Usar `multiprocessing.Pool(max_workers=4)` para paralelizar escrituras.
  - Esperado: ~4× aceleración (4 núcleos).
  - Nueva duración estimada: ~5–7 s solo para autores.
  - Implementación: ~30 minutos, muy bajo riesgo.

**Código ejemplo:**
```python
from multiprocessing import Pool

def write_author(author_dict):
    json_data = build_author_profile(author_dict)
    path = f"author/{author_dict['id']}.json"
    with open(path, 'w') as f:
        json.dump(json_data, f)

with Pool(processes=4) as pool:
    pool.map(write_author, authors_list)
```

---

### 4. **JavaScript: Re-renderización SVG en Filtros**

**Riesgo:** Si gráficos (líneas, barras, red de coautoría) se regeneran en SVG sobre cada cambio de filtro, la CPU está saturada en dispositivos con poca capacidad.

**Verificación actual:**
- `src/verify/run_all.mjs` mide LCP con Playwright.
- `make rendimiento` mide con servidor dual (pre-renderizado vs. no).

**Recomendación:**
- Guardar en caché los SVG generados por filtro combinación.
  - Usar estructura: `cache[filtro_hash] = svg_element`.
  - Invalidar sólo si datos subyacentes cambian.
  - Ganancia: Pasar de ~300 ms de re-render a ~0 ms (lookup).

---

## Monitoreo y Métricas de Rendimiento

### Build-time (Developer Experience)

Añadir timestamps a `src/audit/run_all.py` y `src/build/build_all.py`:

```python
import time

start = time.perf_counter()
# ... ejecutar operación ...
elapsed = time.perf_counter() - start
print(f"Operación completada en {elapsed:.2f} s")
```

**Metas:**
- `make auditoria`: < 5 s
- `make artefactos`: < 10 s
- `make sitio`: < 3 s
- `make verificar`: < 30 s (incluye Playwright)

### Runtime (User Experience)

Consola del navegador con [`web-vitals`](https://github.com/GoogleChrome/web-vitals):

```javascript
import {getCLS, getFID, getFCP, getLCP, getTTFB} from 'web-vitals';

getLCP(metric => console.log('LCP:', metric.value));
getFID(metric => console.log('FID:', metric.value));
```

**Metas Core Web Vitals:**
- **LCP (Largest Contentful Paint):** < 2,5 s ✅ (actual: ~1,2 s)
- **FID (First Input Delay):** < 100 ms ✅ (actual: depende del dispositivo)
- **CLS (Cumulative Layout Shift):** < 0,1 ✅ (actual: buenos, sin shifts observadas)

---

## Roadmap V2: Escalado a 10K+ Publicaciones

| Tarea | Complejidad | Tiempo | Bloqueador | Notas |
|-------|-------------|--------|------------|---------|
| Índice invertido de publicaciones | Media | 2–3 h | No | Ganancia crítica en búsqueda |
| Paralelización de fichas de autor | Baja | 30 m | No | Mejora build time 4×, sin cambios lógicos |
| Caché SVG en vista_explorador.js | Media | 1–2 h | No | Previene CPU stalls en filtros |
| Validación de límites en auditoría | Baja | 30 m | No | Alerta si se aproxima a 10K |
| Benchmark regression suite | Media | 3–4 h | Deseable | Prevenir regresiones de rendimiento |

---

## Decisiones de Arquitectura Documentadas

### D-207: Índice invertido en V2, no V1

**Razón:** A 823 publicaciones, la carga completa + filtrado cliente es más simple, más auditableque mantener dos índices síncronos. Cambia en V2 cuando la búsqueda sea perceptiblemente lenta.

### D-208: Fichas de autor secuencial en V1, no paralelizado

**Razón:** Evitar complejidad de concurrencia hasta que sea medible problema. Hoy son 15 s de 200 s totales (build es dominado por verificación + PDF).

### D-209: SVG pre-renderizado en build + post-procesamiento cliente

**Razón:** Una sola fuente de verdad visual; sin discrepancias entre preview y publicado. Filtrado cliente es O(n) pero n es pequeño hoy.

---

## Configuración de Desarrollo para Rendimiento

### Perfil de Rendimiento Rápido

```bash
# Omitir verificación (Playwright es 80% del build)
make auditoria factibilidad artefactos sitio

# O: omitir PDF
make todo  # sin `make informe`
```

### Verificación Selectiva

```bash
# Sólo una página
node src/verify/run_all.mjs --only-page=index.html
```

### Benchmarking Local

```bash
# Medir impacto de cambios
time make auditoria
time make artefactos
time make sitio
```

---

## Checklist para Replicadores en Otra Institución

- [ ] Corpus inicial < 2.000 publicaciones? → Arquitectura actual está bien.
- [ ] Corpus 2K–10K? → Aplica refactorización de ambigüedades + paralelización fichas (sin riesgo).
- [ ] Corpus > 10K? → Implementa índice invertido **antes** de lanzar búsqueda pública.
- [ ] Corpus > 50K? → Considera microservicio de búsqueda + caché agresivo de resultados.

---

## Referencias

- `docs/ARCHITECTURE.md` §7: Rendimiento (guía base).
- `src/verify/run_all.mjs`: Suite de verificación (contiene timers).
- `src/verify/rendimiento.mjs`: Benchmark LCP dual (pre-renderizado vs. dinámico).
- GitHub Issues (V2_BACKLOG.md §7): Integraciones evaluadas (performance not yet applied).
