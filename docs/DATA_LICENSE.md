# Uso de datos institucionales

**Capa:** pública · **Fase:** 3

**Estado:** la elección de licencias fue **aprobada por el responsable del
proyecto** (sesión 2026-07-31): MIT para el software, CC BY 4.0 para los datos
derivados.

Esa aprobación fija la intención, **no sustituye la verificación jurídica** de
qué permite publicar la licencia institucional de Elsevier (§2 y §5.1). Son dos
cosas distintas: una es una decisión del proyecto, la otra es un hecho externo
que hay que comprobar con quien administra la suscripción.

---

## 1. Separación entre software y datos

| Componente | Licencia | Alcance |
|---|---|---|
| `src/`, `web/`, estructura de `config/` | **MIT** (`LICENSE`) | Reutilizable libremente, incluso comercialmente |
| `data/raw/` | **Términos de Elsevier** | No redistribuible |
| `data/processed/`, `docs/` | **CC BY 4.0** | Ver §3 |
| `internal/` | **No publicable** | Capa interna |

La separación es deliberada: permite que otra institución adopte el software
sin heredar restricciones sobre datos que no le pertenecen.

---

## 2. Datos de origen: Scopus y SciVal

Los archivos de `data/raw/` provienen de exports de Scopus y SciVal, productos
de Elsevier bajo licencia institucional.

**Restricciones que este proyecto asume:**

- Los exports originales **no se redistribuyen**. `data/raw/` está excluido del
  bundle desplegado, verificado automáticamente en `06_assemble_site.py`.
- La plataforma publica **indicadores derivados y metadatos bibliográficos**
  (título, autores, año, DOI, fuente, tipo), no los archivos de origen.
- Las métricas de Elsevier que se muestran —FWCI, SNIP, CiteScore, SJR,
  percentiles, Topics— se atribuyen explícitamente a SciVal con su fecha de
  corte en la barra de vigencia de cada página.

**Advertencia:** el alcance exacto de lo que la licencia institucional de
Elsevier permite publicar **no ha sido verificado jurídicamente en este
proyecto**. Antes de una publicación abierta debe confirmarse con la unidad que
administra la suscripción. Este documento describe supuestos razonables, no un
dictamen legal.

---

## 3. Datos derivados publicados

**CC BY 4.0** para `data/processed/` y la documentación pública. Aprobado por
el responsable del proyecto (sesión 2026-07-31).

Justificación: los metadatos bibliográficos son de interés público, la
atribución preserva la trazabilidad, y una licencia abierta es coherente con el
objetivo de una plataforma «abierta y replicable» de `PROJECT_SPEC.md`.

Cita sugerida:

> Universidad Finis Terrae (2026). *Informe Cienciométrico Institucional*.
> Datos derivados de Scopus y SciVal (Elsevier), corte al 22 de julio de 2026.

Toda exportación desde el sitio incluye esta procedencia en la cabecera del
archivo: un CSV suelto sin fecha de corte deja de ser interpretable.

---

## 4. Datos personales

Las fichas de autor contienen únicamente información ya pública en Scopus:
nombre de firma, afiliación declarada, identificador de autor y publicaciones.
No se incorpora ningún dato personal que no esté en la fuente.

Aun así hay tres decisiones deliberadas:

1. **No se afirma identidad.** Cada ficha corresponde a una forma de firma, no
   a una persona verificada. Las 123 variantes de nombre y los 20
   identificadores fragmentados se declaran sin resolver.
2. **No se enlazan firmas sospechosas entre sí.** Sugerir que dos firmas son la
   misma persona publicaría una afirmación no verificada. La cola de revisión
   permanece interna.
3. **No se publican rankings de desempeño individual.** El orden por número de
   publicaciones es descriptivo y va acompañado de la advertencia DORA/Leiden.

**Pendiente:** definir el procedimiento por el cual una persona puede solicitar
corrección de su ficha. En Scopus, la vía es corregir el perfil de autor en la
fuente; la plataforma lo reflejará en la siguiente carga. Conviene declararlo
explícitamente en el sitio (pendiente V2-08).

---

## 5. Qué debe resolverse antes de publicar abiertamente

| # | Pendiente | Responsable |
|---|---|---|
| 1 | Confirmar con Elsevier o con la unidad de suscripción qué métricas derivadas pueden publicarse abiertamente | Institución |
| ~~2~~ | ~~Elegir la licencia de los datos derivados~~ | **Resuelto: CC BY 4.0** |
| 3 | Definir y publicar el procedimiento de corrección de fichas | Institución |
| 4 | Validar el vocabulario de unidades académicas | Institución |
| 5 | Confirmar el titular del copyright del software | Institución |
