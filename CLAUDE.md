# CLAUDE.md
# Proyecto: Plataforma web para informes bibliométricos UFT

<project_identity>
Nombre del proyecto: Plataforma web interactiva para informes bibliométricos institucionales
Institución inicial: Universidad Finis Terrae
Fuentes iniciales: Scopus y SciVal
Objetivo general: construir una plataforma web abierta, replicable y metodológicamente sólida para visualizar producción, impacto, colaboración y estructura temática de la actividad científica institucional.
</project_identity>

<core_priorities>
Prioriza siempre en este orden:
1. Correctitud metodológica.
2. Integridad y trazabilidad de datos.
3. Claridad analítica.
4. Usabilidad.
5. Rendimiento técnico.
6. Estética visual.
7. Extensibilidad y replicabilidad.
</core_priorities>

<non_negotiable_rules>
- No inventes datos, columnas, métricas, relaciones ni resultados.
- No supongas disponibilidad de APIs, credenciales o endpoints si no fueron confirmados.
- Si un indicador no puede calcularse, debes:
  1. declararlo,
  2. explicar qué falta,
  3. dejarlo como placeholder metodológico.
- No conviertas hipótesis en hechos.
- No mezcles datos públicos con notas internas sin etiquetarlo claramente.
</non_negotiable_rules>

<methodological_frame>
Trabaja con criterios compatibles con:
- bibliometría institucional,
- bibliometrix / Biblioshiny,
- documentación oficial de Scopus y SciVal,
- principios del Leiden Manifesto,
- recomendaciones de DORA.

No confundas:
- productividad con impacto,
- impacto con visibilidad,
- prominencia temática con desempeño individual,
- categoría de revista con tema exacto del artículo,
- exactitud numérica con validez metodológica.
</methodological_frame>

<data_governance>
Separa siempre el sistema en dos capas:
- Capa pública: autores, identificadores públicos, publicaciones, indicadores publicables, visualizaciones, fichas de autor, tablas y textos aptos para difusión.
- Capa interna: reglas de limpieza, trazabilidad de matching, observaciones de validación, ambigüedades, conflictos, logs y notas no destinadas a publicación.

Regla crítica:
Nunca publiques por defecto información que haya sido usada solo para depuración o conciliación interna.
</data_governance>

<author_master_rule>
La tabla maestra de autores afiliados a Universidad Finis Terrae es un componente central del proyecto.

Debes:
- detectar variantes institucionales del nombre,
- documentar reglas de matching,
- mantener nombre en fuente y nombre normalizado cuando corresponda,
- conservar identificadores como ORCID, Scopus Author ID u otros si existen,
- declarar ambigüedades de afiliación en vez de resolverlas arbitrariamente.
</author_master_rule>

<memory_and_continuity>
La memoria de este proyecto es VERSIONADA, no propietaria: `STATE.md` —vista
generada del repositorio—, `SESSION_NOTES.md` —el porqué de cada decisión, con
su fecha— y `docs/DECISIONS.md` —el índice de todas—. Se leen, se auditan y
sobreviven a cambiar de asistente.

Este bloque decía «Este proyecto usa Claude-Mem». Era falso y el propio
`SESSION_NOTES.md` lo tenía registrado como supuesto descartado: no hay
binario, plugin ni servidor MCP, comprobado. Corregido el 2026-08-20.

Antes de retomar una sesión:
1. lee STATE.md — punto de entrada generado, ~120 líneas,
2. abre sólo el documento que responda tu pregunta concreta (STATE.md trae el mapa),
3. si necesitas el porqué de una decisión, búscala en `docs/DECISIONS.md`, que
   la indexa y remite a su sesión,
4. alinea lo recuperado con este archivo.

STATE.md es una VISTA DERIVADA del repositorio, no una fuente de autoridad: no
entra en el orden de precedencia. Si contradice a PLAN.md o a config/, manda la
fuente y STATE.md está viejo. Se regenera con `make estado`.

Leer PLAN.md, SESSION_NOTES.md y docs/ por adelantado son ~3.700 líneas de las
que la mayoría es referencia puntual. Hacerlo consume contexto que hará falta
para el trabajo.

Orden de precedencia si hay conflicto:
1. decisión explícita validada por el usuario en la sesión actual,
2. CLAUDE.md,
3. PROJECT_SPEC.md,
4. PLAN.md,
5. SESSION_NOTES.md,
6. inferencia propia.

No reabras decisiones ya tomadas sin una razón clara.
Si encuentras contradicción, declárala y propone resolución.
</memory_and_continuity>

<session_closure_rule>
Al cerrar cada sesión o subfase, deja explícitamente:
- decisiones tomadas,
- pendientes,
- archivos creados o modificados,
- supuestos descartados,
- ambigüedades abiertas,
- próximo paso recomendado.
</session_closure_rule>

<technical_guardrails>
- Favorece una arquitectura replicable y desplegable en web estática.
- Separa claramente:
  - datos originales,
  - datos procesados,
  - lógica de transformación,
  - presentación.
- Diseña para que otra institución pueda adaptar el sistema cambiando parámetros, no reescribiendo toda la lógica.
</technical_guardrails>
