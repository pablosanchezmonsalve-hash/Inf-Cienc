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

**Excluido del repositorio (D-SEC-01).** La auditoría de seguridad de
2026-09-03 cerró la exposición que quedaba en el REPOSITORIO: `internal/` y
`data/raw/` dejan de versionarse por completo. Antes se mantenían versionadas
(desde `T-16`, 2026-08-03) con la transparencia como argumento; eso las hacía
accesibles a cualquiera que pudiera leer el repositorio, y el repositorio estaba
público. El razonamiento que sostuvo `T-16` —y los gatillos que lo
condicionaban— queda aquí como registro, aunque ya no es la postura vigente:

- Los **nombres de los autores ya son públicos**: están en Scopus. Pero este
  directorio no guarda sólo nombres: guarda **dudas y decisiones de identidad
  sobre personas reales** (`identity_decisions.csv`, `ambiguities_*.csv`,
  `matching_log.csv`, `orcid_*`), que `docs/LAYERS.md` §3 clasifica como
  «nunca se exponen por defecto». La transparencia no obliga a publicar
  afirmaciones no verificadas sobre una persona.
- Las **exportaciones originales de Elsevier** (`data/raw/`) son «no
  redistribuibles» por la licencia institucional. Versionarlas en un
  repositorio accesible las redistribuía igual que el sitio, con menos
  control.

**Postura vigente (D-SEC-01):** ambos directorios viven sólo en el disco de
trabajo local y en los artefactos de CI (que sí los conservan como registros
descargables de cada ejecución). No se citan desde el repositorio. Lo que puede
difundirse sigue siendo el **recuento agregado** de ambigüedades y su
explicación metodológica, nunca el detalle nominal.

**Regla que se preserva, sin excepción:** que una corrida de CI genere estos
archivos no los convierte en publicables; los workflows los suben como
artefactos y **no** los commitean de vuelta al repositorio.

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
| `orcid_hallazgos.csv` | Asignaciones que el registro de ORCID no confirma (V2-01) |
| `orcid_ampliacion_log.csv` | Traza de cada hallazgo de `orcid_expand.py`: firma, ORCID, publicación y tipo de coincidencia |
| `orcid_desacuerdos.csv` | Crossref y el registro atribuyen ORCID distintos a la misma firma (V2-03) |
| `orcid_candidatos_afiliacion.csv` | Titulares que declaran la universidad y coinciden en nombre con una firma sin ORCID (V2-04). **Candidatos, no asignaciones** |

## Cómo revisar la identidad de autor

```bash
make revision                       # regenera internal/revision_identidad.html
```

Ábralo en el navegador. Reúne los 110 casos —variantes de nombre, nombres con
varios Scopus ID, firmas que comparten ORCID, el conflicto de ORCID, los
desacuerdos entre fuentes y los candidatos por afiliación— y para cada uno
muestra publicaciones, años, unidades, identificadores y tres señales cruzadas
que ningún archivo tenía por separado:

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

## Los candidatos por afiliación no son asignaciones

`orcid_candidatos_afiliacion.csv` sale de preguntarle a ORCID quién declara la
universidad, y cruzar esos nombres con las firmas que aún no tienen ORCID. A
diferencia de las otras dos vías, **no hay ninguna publicación compartida que
ancle la coincidencia**: sólo el nombre y la institución. Dos personas
apellidadas Díaz con inicial F. en la misma universidad son indistinguibles por
este método.

Por eso `src/enrich/orcid_afiliacion.py` no escribe nunca en
`data/enriched/authors_orcid.csv` y nada de esto llega al sitio. Cada fila trae
`titulares_que_coinciden_con_la_firma` y `firmas_que_coinciden_con_el_titular`
para que quien revise vea de un vistazo si el caso es un 1-a-1 o un 1-a-3.

Lo que puede publicarse es el **recuento agregado** de ambigüedades y su
explicación metodológica, no el detalle nominal de la cola.
