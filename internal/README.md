# Capa interna — fuera del sitio, dentro del repositorio

Este directorio contiene material de conciliación y depuración: cómo se llegó a
los resultados, no los resultados. Conforme a `CLAUDE.md`, `<data_governance>`:

> Nunca publiques por defecto información que haya sido usada solo para
> depuración o conciliación interna.

## Qué significa «interna» aquí, exactamente

**Excluido del sitio.** Desde la Fase 3 (T-09 cerrado),
`src/build/06_assemble_site.py` no copia este directorio a `dist/` y lo
verifica; el workflow de despliegue lo comprueba otra vez antes de publicar.
Nada de lo que hay aquí ha llegado nunca a
https://pablosanchezmonsalve-hash.github.io/Inf-Cienc/

**No excluido del repositorio, y eso es deliberado.** Este repositorio es
público, de modo que **estos archivos también lo son**. Las compuertas protegen
el sitio; ninguna protege el repositorio, porque no se construyó para eso.

Se decidió mantenerlo así (`T-16`, cerrado el 2026-08-03) tras sopesarlo:

- Los **nombres de los autores ya son públicos**: están en Scopus. El
  repositorio no los revela.
- Lo que sí es propio de aquí son las **dudas**: qué formas de firma podrían
  ser la misma persona sin haberlo comprobado. Se mantienen visibles porque
  documentar la incertidumbre es lo que hace auditable al proyecto, y
  esconderla lo haría parecer más seguro de lo que es.
- Las **exportaciones originales de Elsevier** (`data/raw/`) están igualmente
  versionadas. Su redistribución puede exceder lo que permite la licencia
  institucional: es una cuestión abierta con quien administra la suscripción,
  no una decisión que este proyecto pueda cerrar por su cuenta.

**Cuándo habría que revisar esta decisión:** si la plataforma pasa a ser un
servicio institucional formal, si Elsevier plantea la redistribución, o si
alguna de las personas listadas en las colas objeta aparecer en ellas.
Cualquiera de las tres cambia el cálculo.

## Regla que sigue vigente

Que estos archivos sean accesibles **no los convierte en publicables**. No se
citan, no se enlazan desde el sitio, no se presentan como resultado y no
sustituyen a nada de `docs/`. Lo que puede difundirse es el **recuento agregado**
de ambigüedades y su explicación metodológica, nunca el detalle nominal.

## Contenido

| Archivo | Qué es |
|---|---|
| `matching_log.csv` | Trazabilidad de los 1.207 pares autor × publicación: cadena de afiliación cruda, método de detección, confianza |
| `ambiguities_authors.csv` | Cola de revisión humana de identidad de autor (reglas P-03, P-04, P-05, I-06) |
| `ambiguities_publications.csv` | Cola de revisión de publicaciones (reglas X-01, X-02, X-03, P-01) |
| `orcid_conflicts.csv` | Firmas a las que Crossref atribuye más de un ORCID (V2-01) |
| `identity_candidates.csv` | Firmas distintas que comparten ORCID: candidatas a ser la misma persona, sin confirmar (D-44) |
| `revision_identidad.html` | **Herramienta de revisión.** Generada, no editable a mano. Cruza las cuatro colas anteriores y presenta cada caso con su evidencia junta |
| `identity_decisions.csv` | Decisiones que una persona ha tomado en esa herramienta. No existe hasta que se exporta |

## Cómo revisar la identidad de autor

```bash
make revision                       # regenera internal/revision_identidad.html
```

Ábralo en el navegador. Reúne los 89 casos —variantes de nombre, nombres con
varios Scopus ID, firmas que comparten ORCID y el conflicto de ORCID— y para
cada uno muestra publicaciones, años, unidades, identificadores y tres señales
cruzadas que ningún archivo tenía por separado:

- **si dos firmas aparecen en la misma publicación**, son personas distintas:
  nadie firma dos veces el mismo artículo. Es el descarte más limpio que existe,
  y hoy **no aplica a ninguno de los 127 pares** —dato que por sí solo no prueba
  identidad, pero elimina la vía rápida de descarte;
- coautores en común;
- solapamiento de años y de unidad académica.

Las decisiones se guardan en el navegador mientras trabaja y se exportan a
`identity_decisions.csv`. **La herramienta no decide nada ni propone respuesta
por defecto**: sólo reúne la evidencia.

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
