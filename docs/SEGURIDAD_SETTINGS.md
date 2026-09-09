# Seguridad: revisión de interruptores de Settings en GitHub

Checklist de seguridad del repositorio `Inf-Cienc`, para ejecutar desde la
sesión del propietario con permisos de administración. Complementa a
`docs/SEGURIDAD_PURGA.md` (que cubre la purga de historial). Este documento
es el **qué revisar**; el otro es el **cómo purgar**.

Lectura obligatoria antes: `docs/LAYERS.md` (D-SEC-01/D-SEC-02).

---

## Estado de seguridad (registro vivo)

Verificaciones hechas desde el clon / API pública **2026-09-08**, tras la
purga de historial:

| Punto | Estado |
|---|---|
| 1. Visibilidad del repositorio | ⬜ **Público** (`private: False` verificado por API) |
| 2. Purga del historial (`data/raw/` + `internal/`) | ✅ Ejecutada y verificada (0 commits en las 15 ramas; `internal/README.md` re-creado en `cf573c0`) |
| 3. Protección de rama `/` rulesets | ⬜ Sin protección: API devuelve `rulesets: 0` y sin branch protection en `main` |
| 3. Rotación de secretos ORCID/Scopus | ⬜ Pendiente (repo fue público) |
| 4. Repositorio de despliegue separado | ⬜ Pendiente (decisión de gobernanza) |

Ojo: aunque el repo siga **público**, ya **no contiene datos sensibles en
ninguna rama** tras la purga. Igual debe pasar a privado por política
(D-SEC-01) y porque el historial previo a la purga se descargó antes de
cerrarlo.

---

## 1. Visibilidad y riesgo (bloquea la exposición)

- [ ] **Settings → Danger Zone → Change visibility → Private**.
  Cierra el acceso al historial expuesto. En cuenta gratuita esto **apaga
  GitHub Pages**; decida antes el repositorio de despliegue separado
  (Sección 5).
- [ ] **Settings → Danger Zone → Transfer ownership**: verifique que el
  repositorio pertenece a la organización de la institución y no a una cuenta
  personal, si aplica.

## 2. Protección de rama (`Settings → Branches`) o Rulesets (`Settings → Rules`)

Regla para `main` (branch protection) **o** ruleset equivalente (recomendado).
**Estado actual: sin proteger** (verificado vía API 2026-09-08).

- [ ] **Require a pull request before merging**: mínimo 1 revisor, sin
  auto-aprobación.
- [ ] **Require status checks to pass**: exigir los checks de CI
  (`deploy.yml` en PR, autopruebas `--test` de cada enriquecedor).
- [ ] **Do not allow bypassing the above settings** (ni siquiera admin).
- [ ] **Block force pushes** y **block deletions** en `main`.
- [ ] **Require linear history** si el equipo acepta rebase.
- [ ] **Require signed commits** si la institución lo exige.
- [ ] **Restrict who can push** a escritura mínima.
- [ ] Extender la política a una regla **global** (o ruleset en todas las
  ramas) que **bloquee force-push y borrado**.

## 3. Acceso y autenticación

- [ ] **Settings → Collaborators and teams**: revisar quién tiene `write`/
  `admin`; dejar solo el mínimo institucional.
- [ ] **2FA obligatoria** en la organización (si se transfiere).
- [ ] **Settings → Actions → General → Workflow permissions**: `Read and
  write` solo si hace falta; por defecto `Read repository contents`.
- [ ] Los **PRs de forks** no deben tener acceso a secretos (opción por
  defecto correcta; verificar).
- [ ] **Secretos referenciados** (workflows): `ORCID_CLIENT_ID`,
  `ORCID_CLIENT_SECRET`. No se detectaron valores inline en el historial
  (solo placeholders).

## 4. Secretos y variables (`Settings → Secrets and variables → Actions`)

- [ ] Rotar `ORCID_CLIENT_ID` y `ORCID_CLIENT_SECRET` (repo fue público):
  regenerar en el panel de desarrollador ORCID y actualizar en Settings →
  Secrets and variables → Actions.
- [ ] Rotar cualquier API key de Scopus/Elsevier que haya estado versionada
  en algún commit (verificación Sección 7).
- [ ] Verificar que no haya secretos en el historial: ver Sección 7 de este
  documento (grep).

## 5. Gobernanza y despliegue

- [ ] Crear el **repositorio de despliegue separado** (p. ej. `Inf-Cienc-site`,
  público solo si el sitio debe ser visible) que reciba el `dist/` del repo
  privado (ver `docs/SEGURIDAD_PURGA.md` §7).
- [ ] Activar **Pages manualmente** solo en el repositorio de despliegue
  (`Settings → Pages → GitHub Actions`).
- [ ] Configurar **ADN / IP allowlist / SSO** según política institucional.

## 6. Tras la purga del historial (registro de lo ejecutado)

La **purga se ejecutó el 2026-09-08** con `git filter-repo` (1.5-2.6 s):
backup mirror en `C:\Users\Pablo\Documents\Inf-Cienc-backup-mirror.git`,
purga de `data/raw/` e `internal/` (`--invert-paths`) en las 15 ramas,
force-push `--all`, y re-creación de `internal/README.md` (commit `cf573c0`).

- [x] Backup mirror creado antes de la purga (no destructivo).
- [x] 15 ramas remotas reescritas y force-push (`forced update`).
- [x] `data/raw/` y `internal/` ausentes del historial (0 commits).
- [x] `internal/README.md` re-creado (único archivo versionado de `internal/`).
- [x] `.gitignore` vigente: `internal/*` con `!internal/README.md`.
- [ ] Re-clonar clientes y runners (los hashes cambian tras la purga).

## 7. Verificación de secretos en el historial (local, sin credenciales)

Desde un clon, con lo que NO debe haber versionado:

```
git grep -iE "(api[_-]?key|secret|token|password|passwd|BEGIN (RSA|OPENSSH|EC) PRIVATE)" HEAD -- !*.min.js !*.map
git log --all --oneline -S "ORCID_CLIENT_SECRET" -- .
git log --all --oneline -S "api.elsevier.com" -- .
git ls-files | Select-String -Pattern '(credential|secret|token|\.pem|\.key$)'
```

Ejecutado el 2026-09-08: **sin valores reales de secretos** (solo
placeholders `xxxxxxxx-...`); los scripts referencian secretos vía entorno
(`${{ secrets.* }}`, `$env:`), patrón D-253 correcto.

---

_Última revisión: 2026-09-08 (punto 2 ejecutado; puntos 1, 3 y 4 pendientes
de la sesión del propietario)._