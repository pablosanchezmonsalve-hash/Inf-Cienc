# Estado del proyecto

> **Generado** por `python3 src/state/snapshot.py`. No editar a mano: se sobrescribe.

**Este es el punto de entrada.** Leer sólo este archivo basta para retomar el trabajo. El resto de la documentación es consulta puntual: ver el mapa de lectura al final.

Último commit: `94681da` · Emite la cola de firmas que comparten ORCID (#8)
Snapshot: 2026-08-01

---

## Fases

| Fase | Alcance | Estado |
|---|---|---|
| 1 | Fundamentos, auditoría de datos y validación | ✅ **Completada** (2026-07-31) |
| 2 | Indicadores, arquitectura y UX/UI | ✅ **Completada** (2026-07-31) |
| 3 | Implementación, despliegue, documentación y replicabilidad | ✅ **Completada** (2026-07-31) |

---

## Cifras canónicas

Las que gobiernan todo lo publicado. Si alguna cambia, se regenera este archivo.

| | |
|---|---|
| Ventana temporal | **2023–2025** |
| Publicaciones (universo) | **823** |
| Con métricas | **816** |
| Con autoría detallada | **818** |
| Formas de firma de autor | **589** |
| Pares autor × publicación | **1207** |
| Firmas con ORCID | **174** |
| Indicadores evaluados | **40** |
| Indicadores publicados | **27** |
| Reglas de validación | **29** |
| Reglas bloqueantes fallando | **0** |
| Scopus Affiliation ID | **60105368** |

---

## Colas de revisión humana

Capa interna. Ninguna se resuelve automáticamente (decisión `D-08`).

| Cola | Entradas |
|---|---|
| `internal/ambiguities_authors.csv` | 416 |
| `internal/ambiguities_publications.csv` | 14 |
| `internal/orcid_conflicts.csv` | 1 |

---

## Pendientes abiertos (8)

| # | Pendiente |
|---|---|
| `T-01` | Enriquecer ORCID desde Crossref por DOI (cobertura 97,7 %) |
| `T-02` | Validar institucionalmente el vocabulario de unidades académicas |
| `T-03` | Revisión humana de las 123 variantes de nombre encoladas |
| `T-04` | Revisión humana de los 20 nombres con múltiples Scopus ID |
| `T-05` | Decidir tratamiento del duplicado probable Article/Letter |
| `T-06` | Reexportar Scopus con fecha de corte declarada |
| `T-10` | Red de coautoría autor–autor derivada de `Autoria` |
| `T-13` | Confirmar semántica del percentil de citación con documentación SciVal |

---

## Decisiones tomadas: 40

Índice completo en **`docs/DECISIONS.md`**. Las de mayor alcance:

- **`D-08`** — Duplicados probables y ambigüedades se encolan, no se resuelven
- **`D-09`** — `No determinada` es categoría de primera clase
- **`D-16`** — Cada indicador declara su propio denominador (823 / 818 / 816)
- **`D-18`** — `AU-04` (FWCI por autor) se descarta, no se aproxima
- **`D-22`** — `src/build/` no lee de `data/raw/`; sólo de `data/interim/` validado
- **`D-23`** — La barrera pública/interna se verifica automáticamente post-build

---

## Mapa de lectura

Abrir sólo lo que responde la pregunta que se tiene:

| Si necesita saber… | Abrir |
|---|---|
| Qué decisión se tomó y por qué | `docs/DECISIONS.md` |
| Qué límites tienen los datos | `docs/LIMITATIONS.md` |
| Cómo se calcula un indicador | `docs/INDICATORS.md` |
| Por qué un cálculo es válido | `docs/METHODOLOGY.md` |
| Qué entidades y claves hay | `docs/DATA_MODEL.md` |
| Qué es público y qué interno | `docs/LAYERS.md` |
| Cómo se ve la interfaz | `docs/UX_UI.md` |
| Cómo construir y publicar | `docs/DEPLOYMENT.md` |
| Cómo cargar datos nuevos | `docs/UPDATING.md` |
| Cómo adaptarlo a otra institución | `docs/REPLICATION.md` |
| Cómo recuperar ORCID | `docs/ORCID_GUIDE.md` |
| Qué falta para la V2 | `docs/V2_BACKLOG.md` |
| Historia de cada sesión | `SESSION_NOTES.md` |

---

## Reconstruir todo

```bash
make sitio     # auditoría → validación → artefactos → dist/
make estado    # regenera este archivo
```

