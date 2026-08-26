# Estado del proyecto

> **Generado** por `python3 src/state/snapshot.py`. No editar a mano: se sobrescribe.

**Este es el punto de entrada.** Leer sólo este archivo basta para retomar el trabajo. El resto de la documentación es consulta puntual: ver el mapa de lectura al final.

Último commit: `69c3a75` · La ventana, declarada donde no se puede no verla
Snapshot: 2026-08-26

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

Cada cifra declara su **base**: sobre qué conjunto está medida. Donde la consolidación de identidades cambia el resultado figuran las dos, porque citar una donde corresponde la otra es un error silencioso.

| Cifra | Valor | Base |
|---|---|---|
| Ventana temporal | **2023–2025** | `config/institution.yml` |
| Publicaciones (universo) | **823** | denominador `universo_total` · `D-16` |
| Con métricas | **816** | denominador `con_metricas` · `D-16` |
| Con autoría detallada | **818** | denominador `con_autoria_detallada` · `D-16` |
| Formas de firma en la fuente | **589** | sin consolidar · `internal/matching_log.csv` |
| Entidades de autor publicadas | **538** | tras consolidación humana · **la que sirve el sitio** |
| Apariciones firma × publicación | **1207** | filas de `internal/matching_log.csv` |
| Pares firma × publicación distintos | **1205** | sin repetir una firma dentro de la misma publicación |
| Firmas con ORCID | **242** | sin consolidar · `data/enriched/authors_orcid.csv` |
| Entidades con ORCID | **204** | tras consolidación humana · **la que sirve el sitio** |
| Indicadores evaluados | **40** | `config/indicators.yml` |
| Indicadores publicados | **28** | `config/indicators.yml`, `publicar: true` |
| Reglas de validación | **30** | `data/interim/validation_report.csv` |
| Reglas bloqueantes fallando | **0** | ídem, severidad `bloqueante` |
| Scopus Affiliation ID | **60105368** | `config/institution.yml` |

Las cifras de autor van en dos bases porque una revisión humana declaró que **84 formas de firma eran 37 personas** (`config/identidades_consolidadas.yml`, decisión `D-08`: el pipeline nunca fusiona por heurística). Las restantes siguen sin consolidar y pueden incluir variantes de una misma persona.

---

## Colas de revisión humana

Capa interna. Ninguna se resuelve automáticamente (decisión `D-08`). Se enumeran leyendo `internal/`: una cola es un archivo con columna `resolucion`.

| Cola | Entradas |
|---|---|
| `internal/ambiguities_authors.csv` | 415 |
| `internal/ambiguities_publications.csv` | 14 |
| `internal/identity_candidates.csv` | 17 |
| `internal/orcid_candidatos_afiliacion.csv` | 20 |
| `internal/orcid_conflicts.csv` | 1 |
| `internal/orcid_desacuerdos.csv` | 2 |
| `internal/orcid_hallazgos.csv` | 4 |

`make revision` reúne estas colas en 111 casos, de los que **0 siguen pendientes**: 111 ya se decidieron y quedan registrados en `internal/identity_decisions.csv`. Cifras de la última corrida de `make revision`, no de ahora mismo.

---

## Pendientes abiertos (2)

| # | Pendiente |
|---|---|
| `T-06` | Reexportar Scopus con fecha de corte declarada |
| `T-19` | Ampliar cobertura de ORCID buscando por afiliación en el registro |

---

## Decisiones tomadas: 318

Índice completo en **`docs/DECISIONS.md`**. Las de mayor alcance:

- **`D-08`** — Duplicados probables y ambigüedades se encolan, no se resuelven
- **`D-09`** — `No determinada` es categoría de primera clase
- **`D-16`** — Cada indicador declara su propio denominador (823 / 818 / 816)
- **`D-18`** — `AU-04` (FWCI por autor) se descarta, no se aproxima
- **`D-22`** — `src/build/` no lee de `data/raw/`; sólo de `data/interim/` validado
- **`D-23`** — La barrera pública/interna se verifica automáticamente post-build
- **`D-44`** — Compartir ORCID **no** fusiona firmas: se encola en `internal/identity_candidates.csv`

---

## Mapa de lectura

Abrir sólo lo que responde la pregunta que se tiene:

| Si necesita saber… | Abrir |
|---|---|
| Qué decisión se tomó y por qué | `docs/DECISIONS.md` |
| Qué límites tienen los datos | `docs/LIMITATIONS.md` |
| Cómo se calcula un indicador | `docs/INDICATORS.md` |
| Qué pregunta responde una sección | `docs/EJES.md` |
| Por qué un cálculo es válido | `docs/METHODOLOGY.md` |
| Qué entidades y claves hay | `docs/DATA_MODEL.md` |
| Qué es público y qué interno | `docs/LAYERS.md` |
| Cómo se ve la interfaz | `docs/UX_UI.md` |
| Cómo operar el proyecto paso a paso | `docs/OPERACION.md` |
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

