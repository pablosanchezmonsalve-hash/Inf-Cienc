# Capa interna — NO PUBLICAR

Este directorio contiene material de conciliación y depuración. Conforme a
`CLAUDE.md`, `<data_governance>`:

> Nunca publiques por defecto información que haya sido usada solo para
> depuración o conciliación interna.

**Excluido del bundle público** desde la Fase 3 (T-09 cerrado):
`src/build/06_assemble_site.py` no lo copia a `dist/` y lo verifica, y el
workflow de despliegue lo comprueba otra vez antes de publicar.

> **Alcance de esa exclusión.** Las compuertas cubren `dist/`, es decir el sitio.
> **No cubren el repositorio.** Mientras este directorio esté versionado en un
> repositorio público, su contenido es público, con compuertas o sin ellas.

## Contenido

| Archivo | Qué es |
|---|---|
| `matching_log.csv` | Trazabilidad de los 1.207 pares autor × publicación: cadena de afiliación cruda, método de detección, confianza |
| `ambiguities_authors.csv` | Cola de revisión humana de identidad de autor (reglas P-03, P-04, P-05, I-06) |
| `ambiguities_publications.csv` | Cola de revisión de publicaciones (reglas X-01, X-02, X-03, P-01) |
| `orcid_conflicts.csv` | Firmas a las que Crossref atribuye más de un ORCID (V2-01) |
| `identity_candidates.csv` | Firmas distintas que comparten ORCID: candidatas a ser la misma persona, sin confirmar (D-44) |

## Regla de uso

Ninguna entrada de estas colas se resuelve automáticamente. El campo
`resolucion` indica el tratamiento:

- `PENDIENTE_REVISION_HUMANA` — requiere decisión de una persona.
- `NO_RESOLVER_AUTOMATICAMENTE` — prohibido el colapso o la fusión por
  heurística.
- `DECLARAR_NO_RESOLVER` — se publica como ambigüedad declarada.
- `REVISAR_NORMALIZACION_DE_NOMBRE` — revisar la regla, no el dato.

Lo que puede publicarse es el **recuento agregado** de ambigüedades y su
explicación metodológica, no el detalle nominal de la cola.
