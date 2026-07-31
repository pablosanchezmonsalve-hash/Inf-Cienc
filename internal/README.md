# Capa interna — NO PUBLICAR

Este directorio contiene material de conciliación y depuración. Conforme a
`CLAUDE.md`, `<data_governance>`:

> Nunca publiques por defecto información que haya sido usada solo para
> depuración o conciliación interna.

**Debe quedar excluido del bundle público en el despliegue de Fase 3**
(pendiente T-09 en `PLAN.md`).

## Contenido

| Archivo | Qué es |
|---|---|
| `matching_log.csv` | Trazabilidad de los 1.207 pares autor × publicación: cadena de afiliación cruda, método de detección, confianza |
| `ambiguities_authors.csv` | Cola de revisión humana de identidad de autor (reglas P-03, P-04, P-05, I-06) |
| `ambiguities_publications.csv` | Cola de revisión de publicaciones (reglas X-01, X-02, X-03, P-01) |

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
