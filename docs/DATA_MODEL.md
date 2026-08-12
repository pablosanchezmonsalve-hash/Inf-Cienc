# Modelo lógico preliminar

**Capa:** pública · **Fase:** 1 · **Estado:** preliminar, sujeto a Fase 2

---

## Diagrama

```mermaid
erDiagram
    FUENTE_DE_DATOS ||--o{ PUBLICACION : "origina"
    PUBLICACION  ||--o{ AUTORIA        : "tiene"
    AUTOR        ||--o{ AUTORIA        : "participa en"
    AUTORIA      }o--|| UNIDAD_ACADEMICA : "declara"
    AUTORIA      }o--|| AFILIACION      : "declara"
    PUBLICACION  }o--|| FUENTE          : "publicada en"
    FUENTE       ||--o{ METRICA_FUENTE  : "medida por año"
    PUBLICACION  ||--|| METRICA         : "medida por"
    PUBLICACION  ||--|| COLABORACION    : "caracterizada por"
    PUBLICACION  ||--o{ PUBLICACION_AREA : "clasificada en"
    AREA_TEMATICA ||--o{ PUBLICACION_AREA : "agrupa"
```

`AUTORIA` es la entidad puente sin la cual el modelo no puede representar que
la afiliación de un autor cambia entre publicaciones.

---

## Entidades

| Entidad | Campos | Fuente | Relación | Observaciones |
|---|---|---|---|---|
| **Publicacion** | `eid` (PK), `doi`, `titulo`, `anio`, `tipo_documental`, `fuente_titulo`, `en_scopus`, `en_scival`, `tiene_metricas`, `tiene_autoria_detallada`, `tiene_area_tematica` | Scopus CSV ∪ SciVal XLSX, join por `eid` | 1:N `Autoria`; N:1 `Fuente`; 1:1 `Metrica`; 1:1 `Colaboracion`; N:M `AreaTematica` | **823 registros.** Las banderas de disponibilidad determinan el denominador de cada indicador |
| **Autor** | `autor_id` (PK), `scopus_author_ids`, `nombre_en_fuente`, `clave_normalizada`, `clave_apellido`, `orcid`, `n_publicaciones`, `anio_min`, `anio_max`, `confianza_maxima` | Scopus CSV | 1:N `Autoria` | **589 autores.** 575 con Scopus Author ID. `orcid` existe y está vacío: declarado no disponible, no omitido |
| **Autoria** | `eid` (FK), `autor_id` (FK), `posicion_autor`, `n_autores_total`, `afiliacion_declarada_raw`, `unidad_academica`, `metodo_blando`, `metodo_duro_publicacion`, `confianza` | `Authors with affiliations` (Scopus) + `Scopus Affiliation IDs` (SciVal) | N:1 `Publicacion`; N:1 `Autor` | **1.207 filas** = apariciones firma × publicación; 1.205 pares distintos. Entidad central: aquí vive la afiliación (ver METHODOLOGY §2) |
| **Afiliacion** | `afiliacion_id` (PK), `scopus_affiliation_id`, `nombre_normalizado`, `cadena_raw`, `es_institucion_foco` | Scopus + SciVal | N:M `Publicacion` vía `Autoria` | `60105368` = UFT, parametrizado en `config/institution.yml`. **421 cadenas literales distintas** |
| **UnidadAcademica** | `unidad_id` (PK), `nombre_canonico`, `variantes[]` | Parsing de la cadena de afiliación | 1:N `Autoria` | Cobertura **63,8 %** de los pares. Vocabulario **inferido, no validado institucionalmente**. `No determinada` es categoría de primera clase |
| **Fuente** | `fuente_id` (PK, `Source ID` SciVal), `titulo`, `issn`, `editorial`, `tipo_fuente` | SciVal + Scopus | 1:N `Publicacion`; 1:N `MetricaFuente` | `Source ID` es mejor clave que el ISSN |
| **MetricaFuente** | `fuente_id` (FK), `anio`, `snip`, `snip_pct`, `citescore`, `citescore_pct`, `sjr`, `sjr_pct` | SciVal | N:1 `Fuente` | **Separada de `Metrica` a propósito**: describe la revista, no el artículo |
| **Metrica** | `eid` (FK), `citas`, `fwci`, `field_citation_average`, `views`, `fw_view_impact`, `top_citation_percentile`, `fecha_corte`, `fuente_metrica` | SciVal | 1:1 `Publicacion` | `fecha_corte = 2026-07-22`, obligatoria en todo despliegue. Disponible en 816/823 |
| **AreaTematica** | `area_id` (PK), `esquema`, `codigo`, `nombre` | SciVal | N:M `Publicacion` vía `PublicacionArea` | Esquemas: ASJC, Topic, QS, THE, ANZSRC, ODS. **Multivaluado: no sumable** |
| **PublicacionArea** | `eid` (FK), `area_id` (FK), `esquema` | SciVal | — | Necesaria por la multivaluación |
| **Colaboracion** | `eid` (FK), `n_paises`, `paises[]`, `n_instituciones`, `instituciones[]`, `sectores[]`, `es_internacional` | SciVal | 1:1 `Publicacion` | Nivel publicación. La red autor–autor es derivable de `Autoria`; se difiere a Fase 2 |
| **FuenteDeDatos** | `fuente_datos_id` (PK), `nombre`, `archivo`, `rol`, `fecha_corte`, `fecha_export`, `ventana`, `filtros`, `n_registros` | `config/sources.yml` | Referenciada por todas | Materializa el requisito de trazabilidad |

---

## Claves de enlace

| Enlace | Clave | Cobertura |
|---|---|---|
| Scopus ↔ SciVal | `EID` | 811 de 823 |
| Publicación → Fuente | `Source ID` (SciVal) | 816 de 823 |
| Autoría → Autor | `Scopus Author ID` | 575 de 589 autores |
| Publicación → externo | `DOI` | 97,7 % |
| Autoría → Institución | `Scopus Affiliation ID` | 811 de 823 |

`EID` es la única clave primaria sólida: 100 % de cobertura, cero duplicados.
`DOI` no sirve como PK (19 registros sin DOI).

---

## Campos declarados como no disponibles

Se modelan y quedan vacíos, con la razón explícita. No se omiten del esquema.

| Campo | Estado | Vía de recuperación |
|---|---|---|
| `Autor.orcid` | No existe en ninguna fuente | Crossref por DOI, repositorio institucional UFT, ORCID Public API. **Pendiente de Fase 2/3** |
| `Afiliacion.ror_id` | No verificado | Registro ROR |
| `UnidadAcademica` oficial | Sin catálogo institucional | Validación con la universidad |
| `scopus_export.fecha_corte` | No declarada por el export | Reexportar con fecha registrada |
