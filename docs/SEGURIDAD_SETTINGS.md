# Seguridad: revisión de interruptores de Settings en GitHub

Checklist de seguridad del repositorio `Inf-Cienc`, para ejecutar desde la
sesión del propietario con permisos de administración. Complementa a
`docs/SEGURIDAD_PURGA.md` (que cubre la purga de historial). Este documento
es el **qué revisar**; el otro es el **cómo purgar**.

Lectura obligatoria antes: `docs/LAYERS.md` (D-SEC-01/D-SEC-02).

---

## 1. Visibilidad y riesgo (bloquea la exposición)

- [ ] **Settings → Danger Zone → Change visibility → Private**.
  Cierra el acceso al historial expuesto. En cuenta gratuita esto **apaga
  GitHub Pages**; decida antes el repositorio de despliegue separado
  (Sección 6).
- [ ] **Settings → Danger Zone → Transfer ownership**: verifique que el
  repositorio pertenece a la organización de la institución y no a una cuenta
  personal, si aplica.

## 2. Protección de rama (`Settings → Branches`) o Rulesets (`Settings → Rules`)

Regla para `main` (branch protection) **o** ruleset equivalente (recomendado):

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
  ramas) que **bloquee force-push y borrado** mientras las 10 ramas con
  `data/raw/`/`internal/` no se purguen o eliminen.

## 3. Acceso y autenticación

- [ ] **Settings → Collaborators and teams**: revisar quién tiene `write`/
  `admin`; dejar solo el mínimo institucional.
- [ ] **2FA obligatoria** en la organización (si se transfiere).
- [ ] **Settings → Actions → General → Workflow permissions**: `Read and
  write` solo si hace falta; por defecto `Read repository contents`.
- [ ] Los **PRs de forks** no deben tener acceso a secretos (opción por
  defecto correcta; verificar).

## 4. Secretos y variables (`Settings → Secrets and variables → Actions`)

- [ ] Rotar `ORCID_CLIENT_ID` y `ORCID_CLIENT_SECRET` (repo fue público).
- [ ] Rotar cualquier API key de Scopus/Elsevier que haya estado versionada
  en algún commit.
- [ ] Verificar que no haya secretos en el historial: ver Sección 7 de este
  documento (grep).

## 5. Gobernanza y despliegue

- [ ] Crear el **repositorio de despliegue separado** (p. ej. `Inf-Cienc-site`,
  público solo si el sitio debe ser visible) que reciba el `dist/` del repo
  privado (ver `docs/SEGURIDAD_PURGA.md` §7).
- [ ] Activar **Pages manualmente** solo en el repositorio de despliegue
  (`Settings → Pages → GitHub Actions`).
- [ ] Configurar **ADN / IP allowlist / SSO** según política institucional.

## 6. Tras ejecutar la purga

Orden recomendado (ver `docs/SEGURIDAD_PURGA.md`): backup → privado → purga
→ force-push → proteger rama → rotar secretos.

- [ ] Ejecutar `scripts/purgar-historial.ps1` (automatiza backup, purga,
  force-push y verificación).
- [ ] Decidir si las 10 ramas con datos sensibles se **purgan** o se
  **eliminan** (borrarlas es más simple si son abandonadas).
- [ ] Re-crear `internal/README.md` en `main` (la purga lo elimina) y
  confirmar `.gitignore` (`internal/*` con `!internal/README.md`).
- [ ] Verificar: `git log --all -- data/raw internal/` → sin resultados.
- [ ] Re-clonar clientes y runners (los hashes cambian tras la purga).

## 7. Verificación de secretos en el historial (local, sin credenciales)

Desde un clon, con lo que NO debe haber versionado:

```
git grep -iE "(api[_-]?key|secret|token|password|passwd|BEGIN (RSA|OPENSSH|EC) PRIVATE)" HEAD -- !*.min.js !*.map
git log --all --oneline -S "ORCID_CLIENT_SECRET" -- .
git log --all --oneline -S "api.elsevier.com" -- .
git ls-files | Select-String -Pattern '(credential|secret|token|\.pem|\.key$)'
```

Para el historial completo (no solo el árbol): si algo aparece, entra en el
alcance de la purga o necesita rotación inmediata.

---

_Última revisión: 2026-09-08. Estado de visibilidad en esa fecha: público._