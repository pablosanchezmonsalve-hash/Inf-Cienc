# Guía de Benchmarking y Monitoreo de Rendimiento

**Nivel:** técnico · **Público:** desarrolladores, DevOps

---

## Objetivo

Proveeer herramientas y procedimientos para medir, monitorear y documentar el rendimiento del pipeline de auditoría y build. Esto permite:

1. Detectar regresiones de rendimiento antes de producción.
2. Cuantificar impacto de cambios de código.
3. Informar decisiones de escalado.
4. Documentar líneas base para comparación futura.

---

## 1. Benchmarking Local (Desarrollador)

### 1.1 Medición Simple con `time`

```bash
# Medir cada fase del pipeline
time make auditoria
time make factibilidad
time make artefactos
time make sitio
time make verificar
```

**Salida esperada:**
```
real    0m4.234s
user    0m3.891s
sys     0m0.256s
```

**Interpretación:**
- `real`: tiempo de reloj de pared (lo que espera el usuario)
- `user`: tiempo de CPU en modo usuario
- `sys`: tiempo de CPU en modo kernel (I/O)
- Si `user + sys << real`, hay esperas de I/O o bloqueos.

### 1.2 Profiling Python con `cProfile`

Para identificar qué función consume más tiempo:

```bash
# Reemplazar en src/audit/run_all.py línea 1:
python3 -m cProfile -s cumtime src/audit/run_all.py 2>&1 | head -30
```

**Ejemplo de salida:**
```
         1234567 function calls in 3.456 seconds

   Ordered by: cumulative time
   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        1    0.012    0.012    3.456    3.456 run_all.py:1(<module>)
       10    0.234    0.023    2.891    0.289 02_reconcile_sources.py:27(main)
      589    0.456    0.001    1.234    0.002 04_author_population.py:200(<listcomp>)
```

**Lectura:**
- `cumtime`: tiempo acumulado incluyendo llamadas internas
- `percall`: promedio por llamada
- Si una función tiene bajo `percall` pero alto `ncalls`, la optimización está en reducir llamadas.

### 1.3 Monitoreo de Memoria

```bash
# Antes de cambios grandes
ps aux | grep python

# Más detallado con memory_profiler
pip install memory-profiler
python3 -m memory_profiler src/audit/02_reconcile_sources.py
```

---

## 2. Instrumentación Permanente en Código

### 2.1 Agregar Timers a Scripts de Auditoría

En `src/audit/run_all.py`, reemplazar:

```python
import time
import sys

START_GLOBAL = time.perf_counter()

def run_phase(name, script_module):
    """Ejecuta una fase y registra tiempo."""
    start = time.perf_counter()
    try:
        script_module.main()
    except Exception as e:
        print(f"❌ {name} falló: {e}", file=sys.stderr)
        raise
    finally:
        elapsed = time.perf_counter() - start
        print(f"\n✓ {name} completado en {elapsed:.2f} s\n")

if __name__ == "__main__":
    run_phase("01_inventory", inventory)
    run_phase("02_reconcile_sources", reconcile)
    run_phase("03_affiliation_variants", variants)
    run_phase("04_author_population", population)
    run_phase("05_validation_rules", validation)
    
    total = time.perf_counter() - START_GLOBAL
    print(f"\n{'='*60}")
    print(f"AUDITORÍA COMPLETA EN {total:.2f} s")
    print(f"{'='*60}\n")
```

**Resultado en consola:**
```
============================================================
01_inventory completado en 0.34 s
02_reconcile_sources completado en 1.23 s
03_affiliation_variants completado en 0.56 s
04_author_population completado en 0.89 s
05_validation_rules completado en 1.12 s
============================================================
AUDITORÍA COMPLETA EN 4.14 s
============================================================
```

### 2.2 Logging Estructurado en Build

En `src/build/build_all.py`:

```python
import json
import time
from datetime import datetime

BUILD_METRICS = []

def log_build_step(name: str, duration: float, row_count: int = None):
    """Registra métrica de build en formato JSON."""
    metric = {
        "timestamp": datetime.utcnow().isoformat(),
        "step": name,
        "duration_seconds": round(duration, 3),
        "row_count": row_count,
    }
    BUILD_METRICS.append(metric)
    status = "✓" if duration < 10 else "⚠"
    print(f"{status} {name}: {duration:.2f} s" + 
          (f" ({row_count} rows)" if row_count else ""))

def save_build_metrics(path="data/interim/build_metrics.jsonl"):
    """Guarda métricas para análisis histórico."""
    with open(path, "a") as f:
        for metric in BUILD_METRICS:
            f.write(json.dumps(metric) + "\n")

# En main():
start = time.perf_counter()
publications = build_publications()
elapsed = time.perf_counter() - start
log_build_step("build_publications", elapsed, len(publications))
```

---

## 3. CI/CD: Detección de Regresiones

### 3.1 GitHub Actions Workflow

Agregar en `.github/workflows/performance.yml`:

```yaml
name: Performance Baseline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run audit pipeline
        run: |
          echo "=== AUDIT BENCHMARK ==="
          /usr/bin/time -v python3 src/audit/run_all.py 2>&1 | tee audit.log
      
      - name: Check build time
        run: |
          echo "=== BUILD BENCHMARK ==="
          /usr/bin/time -v python3 src/build/build_all.py 2>&1 | tee build.log
      
      - name: Compare against baseline
        run: |
          python3 .github/scripts/check_regression.py audit.log build.log
      
      - name: Upload metrics
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: performance-logs
          path: |
            audit.log
            build.log
```

### 3.2 Script de Detección de Regresiones

`.github/scripts/check_regression.py`:

```python
import re
import sys

# Baselines conocidas (actualizar después de cambios intencionales)
BASELINES = {
    "audit": 5.0,        # segundos
    "build": 15.0,       # segundos
    "verify": 30.0,      # segundos (Playwright es lento)
}

THRESHOLD = 1.15  # Alertar si es >15% más lento

def extract_time(logfile):
    """Extrae tiempo real del output de /usr/bin/time -v."""
    with open(logfile) as f:
        for line in f:
            if "Elapsed (wall clock) time" in line:
                # Formato: "Elapsed (wall clock) time (h:mm:ss or m:ss): 0:04.23"
                m = re.search(r"(\d+):(\d+\.\d+)", line)
                if m:
                    return int(m.group(1)) * 60 + float(m.group(2))
    return None

if __name__ == "__main__":
    audit_time = extract_time("audit.log") or BASELINES["audit"]
    build_time = extract_time("build.log") or BASELINES["build"]
    
    print(f"\n{'='*60}")
    print(f"PERFORMANCE CHECK")
    print(f"{'='*60}")
    
    failed = False
    for name, actual, baseline in [("audit", audit_time, BASELINES["audit"]),
                                    ("build", build_time, BASELINES["build"])]:
        ratio = actual / baseline
        status = "✓" if ratio < THRESHOLD else "⚠ REGRESSION" if ratio > THRESHOLD else "="
        print(f"{status} {name}: {actual:.2f}s (baseline: {baseline:.2f}s, {ratio:.1%})")
        if ratio > THRESHOLD:
            failed = True
    
    print(f"{'='*60}\n")
    sys.exit(1 if failed else 0)
```

---

## 4. Análisis Histórico

### 4.1 Graficar Tendencias

Si guardas métricas en `data/interim/build_metrics.jsonl`:

```python
import json
import pandas as pd
import matplotlib.pyplot as plt

metrics = [json.loads(line) for line in open("data/interim/build_metrics.jsonl")]
df = pd.DataFrame(metrics)
df["timestamp"] = pd.to_datetime(df["timestamp"])

# Graficar por paso
for step in df["step"].unique():
    data = df[df["step"] == step]
    plt.plot(data["timestamp"], data["duration_seconds"], label=step, marker="o")

plt.xlabel("Timestamp")
plt.ylabel("Duration (s)")
plt.legend()
plt.title("Build Pipeline Performance Over Time")
plt.savefig("performance_trend.png", dpi=100, bbox_inches="tight")
print("✓ Gráfico guardado en performance_trend.png")
```

### 4.2 Estadísticas por Rama

```bash
# Comparar main vs. feature branch
git checkout main
time make auditoria

git checkout feature/optimization
time make auditoria

# Reporte: "optimization es 15% más rápido"
```

---

## 5. Checklist de Optimización

Antes de considerar optimizado un cambio:

- [ ] ¿Mediste el rendimiento antes y después del cambio?
- [ ] ¿Validaste que la lógica sigue siendo idéntica?
- [ ] ¿Corriste la auditoría completa sin errores?
- [ ] ¿Documentaste el delta esperado?
- [ ] ¿Actualizaste los baselines en CI/CD si cambió la arquitectura?
- [ ] ¿Probaste en máquina de baja capacidad (si es cliente-side)?

---

## 6. Límites Conocidos y Alertas

| Métrica | Umbral | Acción |
|---------|--------|--------|
| Audit time | > 10 s | Revisar regla nueva bloqueante |
| Build time | > 20 s | Perfilar `src/build/` |
| Verify time | > 60 s | Aceptable (Playwright); ignorar |
| publications.json size | > 1 MB (sin comprimir) | Consideraar V2 con índice |
| LCP (portada) | > 3 s | Revisar asset bloqueante |

---

## Referencia Rápida

```bash
# Medir todo
time make auditoria && time make artefactos && time make sitio

# Profiling detallado
python3 -m cProfile -s cumtime src/audit/run_all.py | head -20

# Memory profiling
python3 -m memory_profiler src/audit/04_author_population.py

# Comparar branches
git stash && time make auditoria
git stash pop && time make auditoria
```
