<phase>
Fase 2: Indicadores, arquitectura y UX/UI
</phase>

<precondition>
Asume que Fase 1 ya fue completada.
Si detectas vacíos críticos en Fase 1, decláralos antes de continuar.
</precondition>

<objective>
1. Construir catálogo de indicadores posibles.
2. Seleccionar indicadores prioritarios para la V1.
3. Diseñar arquitectura técnica general.
4. Diseñar arquitectura UX/UI del dashboard.
5. Definir capa pública e interna.
6. Incorporar ficha pública de autor, filtros y ayuda contextual.
</objective>

<instructions>
### Indicadores
Clasifica indicadores en:
- descriptivos/desempeño,
- impacto,
- colaboración,
- conceptuales/temáticos.

Para cada indicador especifica:
- nombre,
- definición,
- lógica o fórmula,
- columnas requeridas,
- disponibilidad real,
- nivel de confiabilidad,
- prioridad para V1,
- nota metodológica breve.

### Arquitectura técnica
Propón:
- pipeline de datos,
- archivo maestro,
- archivos procesados,
- lógica de actualización,
- despliegue web,
- preparación para futuras integraciones.

### Arquitectura UX/UI
Diseña:
- encabezado institucional,
- panel de KPIs,
- módulos analíticos,
- filtros,
- buscador,
- detalle documental,
- ficha pública de autor,
- navegación general,
- glosario o tooltips para métricas no triviales,
- estados de carga, vacío y error.

### Separación de capas
Define con claridad:
- qué aparece en capa pública,
- qué queda en capa interna,
- qué datos o notas nunca deben exponerse por defecto.

### Rendimiento
Incluye:
- preagregación,
- lazy loading cuando aplique,
- debounce en filtros,
- persistencia ligera de filtros si conviene,
- visualizaciones adecuadas al tipo de dato.
</instructions>

<restrictions>
- No implementes métricas no verificables.
- No conviertas todos los requerimientos deseables en obligatorios.
- No diseñes gráficos decorativos sin propósito analítico.
- No asumas que todo necesita tooltip; úsalo en métricas y visualizaciones no triviales.
- No expongas lógica interna de conciliación en la capa pública.
</restrictions>

<required_output>
Entrega la respuesta en este formato:

## 1. Objetivo de la fase

## 2. Catálogo de indicadores
Presenta una tabla con:
- Indicador
- Categoría
- Definición
- Fórmula o lógica
- Campos requeridos
- Disponible (sí/no/parcial)
- Confiabilidad
- Prioridad V1
- Nota metodológica

## 3. Selección priorizada de indicadores V1
Lista razonada y acotada.

## 4. Arquitectura técnica
Describe componentes, flujo y archivos esperados.

## 5. Arquitectura UX/UI
Presenta módulos y propósito analítico de cada uno.

## 6. Definición de capa pública e interna
Usa tabla o lista explícita.

## 7. Ficha pública de autor
Presenta estructura propuesta y advertencias metodológicas.

## 8. Reglas de filtros, glosario y tooltips

## 9. Reglas de rendimiento y despliegue

## 10. Dudas críticas

## 11. Decisiones tomadas

## 12. Archivos a crear o modificar

## 13. Próximo paso recomendado
</required_output>

<definition_of_done>
La fase termina cuando existan:
- catálogo de indicadores,
- selección V1,
- arquitectura técnica,
- arquitectura UX/UI,
- definición de capas,
- estructura de ficha de autor,
- criterios de filtros y ayuda contextual.
</definition_of_done>
