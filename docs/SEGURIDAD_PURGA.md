# Purga de historial: expulsión definitiva de `data/raw/` e `internal/`

> **Documento operativo (D-SEC-01/D-SEC-02).** Generado el 2026-09-03 tras la
> auditoría de seguridad. Complementa `docs/LAYERS.md` (capas) y `AGENTS.md`
> (reglas). **Requiere la aprobación y la sesión autenticada del propietario.**

## 1. Por qué es necesario

La auditoría de seguridad del 2026-09-03 confirmó que el repositorio era
**PÚBLICO** y que contenía datos sensibles versionados:

- `data/raw/` — exportaciones originales de Scopus/SciVal de **Elsevier**,
  «no redistribuibles» según `docs/DATA_LICENSE.md` §2.
- `internal/` — matching, ambigüedades, **decisiones de identidad sobre
  personas reales**, hallazgos de ORCID, logs y herramientas de revisión
  (`docs/LAYERS.md` §3: «nunca se exponen por defecto»).

El commit `e24bd42` (D-SEC-01/D-SEC-02) y el `3a856a9` (archivos sensibles
nuevos incorporados por el remoto) **expulsaron estas capas del árbol
publicado en `main`** y se empujaron a `origin/main`.

Sin embargo, eso **no borra el historial**: cualquier persona puede seguir
descargando los blobs viejos desde commits históricos. Además,

- **10 de 12 ramas remotas** todavía tienen `data/raw/` (7–10 archivos) e
  `internal/` (13–37 archivos) en su árbol actual (`git ls-tree`):
  `c05-red-coautoria-preparacion`, `claude/cabecera-y-cobertura`,
  `claude/coding-session-7pokjp`, `claude/openalex-contraste`,
  `claude/pensive-tesla-81t44z`, `claude/project-status-review-3tnz4y`,
  `claude/ror-institucion`, `claude/state-review-next-steps-wzzq0h`,
  `perf/optimization-and-scaling`, `rediseno-bandas-paleta`.
- `internal/` aparece en **89 commits** a través de todas las refs.

Para cumplir el objetivo de «impenetrable» hay que **reescribir el historial**
y después forzar la actualización del remoto.

> ⚠️ **Riesgo y garantía previa**
> - La reescritura **cambia los hashes de todos los commits afectados** y, por
>   tanto, **invalida** cualquier clon, PR abierto o referencia a commits
>   antiguos. Es una operación **destructiva** sobre historia publicada.
> - Se ejecuta sobre un **clon fresco**; **no** daña el trabajo local ni las
>   ramas no tocadas por el filtro.
> - **Backup**: local existe `backup-sec-11056d8` (el estado post-fix previo a
>   la reconciliación). Antes de purgar, cree un backup del remoto completo
>   (Sección 3).

## 2. Alcance de exactitud del filtro

Elimine **dos rutas** del historial en **todas las ramas**:

| Ruta | Motivo |
|------|--------|
| `data/raw/` | Exports propietarios de Elsevier (no redistribuibles) |
| `internal/` | Capa interna: identidad de personas + logs (conservar solo `internal/README.md`) |

> `data/processed/` es **pública** (CC BY 4.0) y **se conserva**: es la fuente
> que CI usa para ensamblar el sitio sin capas sensibles (D-SEC-02).
> `internal/README.md` es documentación sin datos nominales y **se conserva**.

## 3. Backup del remoto (obligatorio antes)

En la sesión autenticada del propietario, cree un respaldo independiente
(por ejemplo un *mirror* local fuera del clon de trabajo):

```bash
# PowerShell / bash — en un directorio nuevo, NO dentro del clon actual
git clone --mirror https://github.com/pablosanchezmonsalve-hash/Inf-Cienc.git backup-inf-cienc-mirror.git
```

Y, si es lo más conservador, archive ese directorio (`Compress-Archive`/`tar`)
en otro medio. Solo tras tener el mirror comprobado se procede.

## 4. Método recomendado: `git filter-repo` (rápido y seguro)

`filter-repo` no está instalado en esta máquina. Instálelo (requiere Python 3):

```bash
pip install git-filter-repo
```

`filter-repo` **exige un clon fresco** y **elimina el remoto por defecto**,
así que trabaje en un clon dedicado y vuelva a apuntar `origin` al final:

```bash
# 1) Clon fresco con TODAS las ramas
git clone --no-local https://github.com/pablosanchezmonsalve-hash/Inf-Cienc.git purga-inf-cienc
cd purga-inf-cienc
git fetch --all --tags

# 2) Purga EN UNA SOLA PASADA: elimina data/raw/ e internal/ de TODA la
#    historia (blobs, árboles, commits, en todas las ramas), CONSERVANDO
#    internal/README.md, que es lo que pide la Sección 2.
git filter-repo --force --filename-callback "return None if (filename.startswith(b'data/raw/') or (filename.startswith(b'internal/') and filename != b'internal/README.md')) else filename"
```

> **Por qué un callback y no `--invert-paths`.** `--invert-paths` elimina
> exactamente las rutas listadas, sin excepciones: con él, `internal/README.md`
> desaparece del historial, en contra de lo que la Sección 2 declara como
> alcance. El callback decide archivo por archivo y sí admite la excepción.
> Comprobado el 2026-09-03 sobre un repositorio de laboratorio con dos ramas y
> una etiqueta: el README sobrevive, todo lo demás de `internal/` y
> `data/raw/` desaparece de las dos ramas, y las etiquetas se reescriben.
>
> Las cadenas de Python del callback van con **comillas simples**: PowerShell
> maltrata las comillas dobles al pasar argumentos a un ejecutable nativo, y el
> callback llegaría roto a `git`.
>
> `data/processed/` no se toca y **se conserva intacto** (es la capa pública
> CC BY 4.0 que CI usa en D-SEC-02). Compruébelo explícitamente tras la purga:
> verificar sólo que lo sensible desapareció dejaría pasar un filtro que además
> se llevara la capa pública, y sin ella el despliegue no puede ensamblar el
> sitio.

Verificación tras la purga, las dos direcciones:

```bash
# lo que NO debe quedar (vacío = limpio)
git log --all --oneline -- data/raw internal/ ':!internal/README.md'
# lo que SÍ debe seguir
git ls-tree -r --name-only HEAD -- data/processed | head
git ls-tree -r --name-only HEAD -- internal/README.md
```

### Volver a asociar el remoto y forzar el push

```bash
git remote add origin https://github.com/pablosanchezmonsalve-hash/Inf-Cienc.git
git push origin --force --atomic --all
git push origin --force --tags
```

> En un repo que tenga **protección de rama** sobre `main`, el force-push se
> rechazará: Settings → Branches → main → desactive temporalmente
> «Require a pull request» / «Do not allow bypassing». Restáurelo tras la purga.

## 5. Método alternativo: `git filter-branch` (disponible ya en esta máquina)

> **Validado (2026-09-03):** se probó `filter-branch` en un clon local de este
> mismo repositorio y **no completó en 2 minutos** sólo para eliminar
> `data/raw/` (13 refs, decenas de commits). `filter-branch` es funcional pero
> **lento** porque ejecuta un `git rm` por commit en el index. Si no puede
> instalar `filter-repo`, prevea **decenas de minutos o más**. Si puede,
> use la Sección 4 (recomendada). Los comandos siguientes son correctos pero
> lentos:

```bash
# PowerShell (Windows)
git clone https://github.com/pablosanchezmonsalve-hash/Inf-Cienc.git purga-inf-cienc
cd purga-inf-cienc
git fetch --all --tags

# Elimina data/raw/ del historial completo
git filter-branch --force --index-filter `
  "git rm -r --cached --ignore-unmatch data/raw/" `
  --prune-empty --tag-name-filter cat -- --all

# Elimina internal/ completo del historial
git filter-branch --force --index-filter `
  "git rm -r --cached --ignore-unmatch internal/" `
  --prune-empty --tag-name-filter cat -- --all

# Limpia los refs temporales y objetos huérfanos
git for-each-ref --format="%(refname)" refs/original/ | xargs -n 1 git update-ref -d
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

`internal/README.md` se eliminó junto con `internal/` — **a diferencia del
método recomendado de la Sección 4**, que lo conserva: `filter-branch` con
`git rm -r --cached` no admite excepciones dentro de la ruta. Tras la purga,
**re-créelo** en `main` (es documentación pequeña, sin datos nominales) y
ajuste `.gitignore` (`internal/*` con `!internal/README.md`) si fuera parte de
lo purgado. Luego force-push igual que en la Sección 4.

---

## 6. Checklist en Settings (requiere la cuenta del propietario)

Los siguientes pasos **no pueden automatizarse** desde un workflow ni desde un
clon con el `GITHUB_TOKEN` de un workflow (falta permiso de administración).
Debe hacerlos el propietario en el navegador:

### 6.1 (Primero, antes de nada) Pasar el repositorio a PRIVADO
1. Repositorio `Inf-Cienc` → **Settings**.
2. **Danger Zone** (al final de la página de Settings) → **Change repository visibility**.
3. Seleccione **Private** y confirme escribiendo el nombre del repositorio.

> ⚠️ **Consecuencia necesaria:** estando en una cuenta gratuita, **GitHub Pages
> deja de servirse** si el repo es privado. Eso es **correcto** con el modelo
> D-SEC-02: el sitio público debe servirse desde un **repositorio de despliegue
> separado** que contenga solo la capa pública (`web/`, `docs/`, `data/processed/`)
> o el `dist/` ya ensamblado. Mientras no exista ese repo de despliegue, el
> sitio deja de publicarse. No lo haga privado sin haber decidido ese repo de
> despliegue, o la página queda caída.

### 6.2 Después de la purga: verificar y proteger
1. **Settings → Branches → Add branch protection rule** → `main`:
   - «Require a pull request before merging» (si es el flujo habitual).
   - «Do not allow bypassing the above settings» (decisión de gobernanza).
2. **Settings → Actions → General → Workflow permissions**:
   - conﬁrme que `GITHUB_TOKEN` usa **Read repository contents** (contraste con
     `deploy.yml`, que pide `contents: read` y `pages: write` puntualmente).

### 6.3 Rotar secretos (por si hubo exposición)
Dado que el repo era **público**, los secretos de Actions (aunque cifrados) no
se filtran por contenido, pero rote por prudencia si sospecha exposición:
1. **Settings → Secrets and variables → Actions**:
   - `ORCID_CLIENT_ID`, `ORCID_CLIENT_SECRET`: regenere en el panel de
     desarrollador de ORCID y actualice.
   - Cualquier API key de Scopus/Elsevier de `config/` o scripts: no debe
     estar versionada; si lo estuvo en algún commit, gire esa key.

### 6.4 Tras la purga: comprobar `internal/README.md` y el `.gitignore`
- `internal/README.md` **se conserva** con el filtro de la Sección 4, así que
  normalmente no hay nada que recrear: compruébelo con
  `git ls-tree -r --name-only HEAD -- internal/README.md`. Si usó
  `--invert-paths` en vez del callback, sí desapareció y hay que reponerlo
  (es documentación pequeña, sin datos nominales;
  la purga lo eliminó junto con `internal/`), revise `.gitignore`
  (`internal/*` con `!internal/README.md`) y comitee.
- `git ls-tree -r --name-only origin/main -- data/raw` → **vacío**.
- `git log --all -- data/raw internal/` → **sin resultados** (historial limpio).
- En el navegador (repo privado, solo visible para ti): Settings → «Empty this
  repository»? **NO**: no borre el repo; la verificación es por git.

---

## 7. ¿Qué ocurre con el despliegue de Pages tras esto?

El modelo D-SEC-02 documentado en `deploy.yml` asume que CI ensambla `dist/`
desde la capa pública **versionada** (`data/processed/` + `web/`). Si el repo
pasa a privado, Pages se apaga; para volver a publicar hay que crear un
repositorio de despliegue (p. ej. `Inf-Cienc-site`, público) que reciba por
acción el `dist/` ensamblado del repositorio privado, o que contenga la capa
pública. Ese flujo queda fuera del alcance de este documento y es una decisión
de gobernanza de la institución.

## 8. Estado pendiente registrado

- [X] Árbol de `main` limpio (commit `3a856a9`, empujado).
- [ ] Repositorio a **privado** (Settings, propietario).
- [ ] Purga de historial con `filter-repo`/`filter-branch` (Secciones 4/5).
- [ ] Force-push a `main` y a las demás ramas.
- [ ] Otras 10 ramas con `data/raw/`/`internal/`: decidir si se purgan o se
      eliminan (si son ramas de trabajo abandonadas, borrarlas es más simple y
      elimina su copia de los datos).
- [ ] Rotar secretos ORCID/Scopus si hubo exposición (6.3).
- [ ] Decidir y montar el repositorio de despliegue separado (Sección 7).
