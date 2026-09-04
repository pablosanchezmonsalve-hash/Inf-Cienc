# AGENTS.md

Proyecto bibliométrico institucional, web estática. Todo en español: docs, commits, código, este archivo. V1 completa; ver `docs/V2_BACKLOG.md` para lo que sigue.

## Antes de trabajar

- Entrada obligatoria: `STATE.md` (~120 líneas, con mapa de lectura). Es un archivo **derivado**; no editar a mano, se regenera con `make estado`. Si contradice a `PLAN.md`/`config/`, la fuente manda y STATE.md está viejo.
- `CLAUDE.md` define las reglas no negociables del proyecto (no inventar datos/cifras; separación estricta capa pública/interna). Leer y respetar.
- No releer `PLAN.md`, `SESSION_NOTES.md` ni `docs/` completos (~3.700 líneas): usar el mapa de lectura de STATE.md para abrir sólo el documento de la pregunta concreta. El porqué de una decisión se indexa en `docs/DECISIONS.md`.
- Precedencia ante conflicto: decisión validada por el usuario > `CLAUDE.md` > `PROJECT_SPEC.md` > `PLAN.md` > `SESSION_NOTES.md` > inferencia propia.

## Comandos

Pipeline vía Makefile; no correr subcomandos sueltos:

- `make instalar` — `pip install -r requirements.txt` (Python 3.11+).
- `make sitio` — pipeline completo: auditoría → factibilidad → artefactos → `dist/`. `make auditoria`, `make artefactos` para etapas.
- `make estado` — regenera STATE.md.
- `make servir` — `http.server` en `dist` puerto 8000.
- `make verificar` — batería Playwright de `src/verify/` sobre el sitio construido. Playwright/Chromium son **solo dev** (`npm install --no-save playwright`); el sitio no tiene dependencias de runtime.
- `make revision` / `make validar-unidades` / `make revisar-cobertura-openalex` / `make huecos-autores` — generan colas/herramientas de revisión humana en `internal/`.
- `make kit`, `make ror`, `make openalex`, `make cobertura`, `make cobertura-crossref`, `make scopus`, `make orcid-afiliacion`, `make informe`, `make rendimiento` — catalog completo en Makefile.
- `make rendimiento` tarda minutos y exige un segundo servidor (`PUERTO_SIN`); no correrlo por defecto.

Windows:
- El Makefile invoca `python3`; en Windows usar `py src\...` (asistentes comentados en cada objetivo).
- Los flujos con credenciales o de varios pasos en orden fijo tienen asistentes listos en `scripts/*.ps1` (clic derecho → Ejecutar con PowerShell): `verificar-orcid`, `ampliar-orcid-afiliacion`, `consultar-scopus`, `revisar-identidad`, `validar-unidades`. No reinventarlos. Comparten `scripts/_comun.ps1` (dot-source; corregir ahí, no en cada asistente).
- El "python" de la Microsoft Store es un stub, no Python (D-88); `_comun.ps1` ya lo detecta.

## Pipeline y compuertas

`data/raw` (inmutable) → `src/audit` → `data/interim` → `src/build` → `data/processed` → `dist/` (único desplegable).

- `src/build/` **no lee `data/raw/`**; sólo `data/interim/` validado (D-22).
- El build **aborta** si una regla de validación bloqueante falla o si `06_assemble_site.py` encuentra material de la capa interna en artefactos públicos. Es mecanismo, no convención; no tentar de "arreglar la salida".

## Regla cardinal: capas de datos

- Público: `docs/`, `data/processed/`, el sitio. Interno: `internal/` (matching, ambigüedades, colas, hallazgos, logs) y `data/raw/` (exports de Elsevier).
- **`internal/` y `data/raw/` ni se despliegan ni se versionan (D-SEC-01).** Viven sólo en el disco local y en los artefactos de CI. El build lo verifica (`05`/`06`) y el workflow de despliegue lo vuelve a comprobar sobre `dist/` y sobre el índice de git.
- No publicar material usado sólo para depuración/conciliación. Las colas de revisión humana se encolan y se deciden a mano, nunca por heurística (D-08).
- El repo debe permanecer **privado**: `data/raw/` (exports Elsevier «no redistribuibles») e `internal/` (datos de identidad de personas) no pueden residir en un repositorio accesible. Un despliegue público de Pages se sirve desde un repo/sitio específico que no contiene estas capas.

## Configuración ≠ código

La replicabilidad es por configuración, no por reescritura: la institución se adapta tocando `config/institution.yml`, `config/matching_rules.yml`, `config/sources.yml`, `config/indicators.yml`. **Nunca** hardcodear datos institucionales (nombres, IDs Scopus, fechas de corte) en `src/` ni `web/`; se verifica vía `grep -ri "finis" src/ web/` = 0.

## Verificación y tests

- Autopruebas sin red y sin credenciales: cada enriquecedor de `src/enrich/` responde `--test` (`orcid_crossref`, `orcid_api`, `orcid_expand`, `orcid_afiliacion`, `ror_institucion`, `orcid_openalex`, `openalex_cobertura`) y `src/review/apply_decisions.py` también. Se ejercen en CI en cada push/PR. Ej.: `python3 src/enrich/orcid_api.py --test`.
- `node src/verify/run_all.mjs dist` verifica el sitio construido (WCAG, estructura, consola, flujos, responsive, higiene). CI lo corre directamente sobre `dist/`, sin re-construir.
- El CI exige pre-renderizado: `dist/{index,impacto,produccion,colaboracion,tematica}.html` deben contener `data-prerender="1"` y `dist/impacto.html` sus gráficos. Un sitio que depende de JS para mostrar cifras no pasa.

## Sitio (`web/`)

Sin dependencias en el navegador, **sin CDN**: SVG generados en JS propio + nodos pre-renderizados por los constructores (Node, solo build). El sitio debe funcionar en red cerrada institucional; no añadir cargas externas.

## CI / despliegue

- `deploy.yml`: construye y verifica en push a `main` y en PRs; sólo publica (GitHub Pages) desde `main`. En PR sólo valida.
- `ampliar-orcid.yml` y `verificar-orcid.yml`: flujos de enriquecimiento que necesitan la capa de datos SENSIBLE (no versionada). En un runner de GitHub sin esos datos abortan con un mensaje claro (D-SEC-02). El camino canónico es LOCAL: `scripts/verificar-orcid.ps1` / `scripts/ampliar-orcid-afiliacion.ps1` en la máquina institucional. Sólo se usan en CI si hay un runner con las capas montadas; sus commits de bot versionan únicamente lo público (`data/enriched/*`, docs).
- Pages necesita activación manual única (Settings → Pages → GitHub Actions). Mientras no esté activada, el job de publicar falla con "Get Pages site failed" pero el resto del pipeline igual valida.

## Higiene

- `data/interim/`, `data/processed/`, `dist/`, `design-system/` no se versionan (derivados; gitignore). `internal/` y `data/raw/` tampoco se versionan (D-SEC-01): capa sensible, véase «Regla cardinal: capas de datos».
- Cerrar sesión dejando decisiones, pendientes, archivos tocados, supuestos descartados, ambigüedades y próximo paso (regla de cierre en CLAUDE.md).