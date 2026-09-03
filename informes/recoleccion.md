# Recolección de datos de red — registro

Ejecutada con `informes/_fork_runner.py` (fork a `informes/run/`, sin tocar
`internal/` ni `data/enriched`). Credenciales ORCID configuradas solo como
variables de entorno de la corrida, nunca en disco/repo.

## Vía 1 — Crossref por DOI (`orcid_crossref.py`) → 174 asignaciones
Ya en disco (ejecutado 2026-08-26). Sin credenciales.

## Vía 2 — OpenAlex (`orcid_openalex.py`) → 80 asignaciones
Ya en disco (ejecutado 2026-08-26). Sin credenciales.

## Vía 3 — Registro ORCID expandido (`orcid_expand.py`)
Ejecutado **hoy con credenciales**, fork a `informes/run/orcid_expand/`:

- Publicaciones con DOI consultadas: **804**
- DOI cuyo titular existe en ORCID: **640**
- Errores de red: **0**
- Asignaciones nuevas: **0**
- Desacuerdos encolados: **2** (`orcid_desacuerdos.csv` en el fork)
- Hallazgos brutos en el log de ampliación: **351** (todos ya consolidados en vigentes)

**Conclusión**: la vía expandida no aporta asignaciones nuevas. Las 322
asignaciones vigentes (Crossref + OpenAlex + afiliación confirmada) ya cubren
todo lo que el registro ORCID declara para este corpus vía DOI. La cobertura
se mantiene en **322/589 (54,7 %)**.

## Vía 4 — Candidatos por afiliación (`orcid_afiliacion.py`)
Ejecutado **hoy con credenciales**, fork a `informes/run/orcid_afiliacion/`:

- Consulta: `affiliation-org-name:"Universidad Finis Terrae"`
- Titulares que declaran la institución en ORCID: **633**
- Firmas sin ORCID a cruzar: **267**
- Candidatos nuevos: **0** (ninguna clave de firma coincide)

**Conclusión**: tampoco aporta. Los 20 candidatos por afiliación ya confirmados
de corridas anteriores no crecen; las claves de firma de los 267 sin ORCID no
coinciden con ningún titular adicional que declare la institución.

## Resultado general

| Vía | Sin credenciales | Escritura aislada | Aportó |
|---|---|---|---|
| Crossref por DOI | ✅ | n/a (disco) | 174 |
| OpenAlex | ✅ | n/a (disco) | 80 |
| Registro expandido | ❌ | ✅ fork | 0 nuevas |
| Afiliación | ❌ | ✅ fork | 0 nuevas |

La cobertura ORCID queda en **322 de 589 firmas (54,7 %)**, confirmada por
todas las vías públicas/registro disponible. Las 267 restantes no tienen un
ORCID identificable por ninguna fuente actual: están fuera del registro, no
vinculadas por DOI, o no comparten clave de firma con titulares que declaren
la institución.

Fuentes autoritativas de las corridas:
- `informes/run/orcid_expand/orcid_ampliacion_log.csv`
- `informes/run/orcid_expand/orcid_desacuerdos.csv`
- `informes/run/orcid_afiliacion/` (sin salidas de candidatos)