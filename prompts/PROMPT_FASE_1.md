<phase>
Fase 1: Fundamentos, auditoría de datos y validación
</phase>

<objective>
Construir la base metodológica y estructural del proyecto mediante:
1. fundamentación mínima para la fase,
2. auditoría completa de archivos,
3. modelo lógico preliminar,
4. reglas de validación de datos científicos.
</objective>

<instructions>
1. Inspecciona todos los archivos disponibles.
2. Identifica:
   - archivo,
   - tipo,
   - hojas o tablas,
   - columnas reales,
   - posibles claves de enlace,
   - utilidad para autores, publicaciones, métricas, afiliación, áreas temáticas y colaboración.
3. Propón un modelo lógico con estas entidades si los datos lo permiten:
   - Autor,
   - Publicación,
   - Afiliación,
   - Métrica,
   - Área temática,
   - Colaboración,
   - Fuente de datos.
4. Diseña la tabla maestra de autores UFT:
   - variantes institucionales,
   - reglas de matching,
   - campos obligatorios,
   - manejo de ambigüedad.
5. Propón reglas de validación:
   - integridad estructural,
   - duplicados exactos,
   - duplicados probables,
   - coherencia institucional,
   - coherencia entre fuentes,
   - plausibilidad de indicadores.
</instructions>

<restrictions>
- No inventes columnas ni relaciones.
- No resuelvas duplicados probables de forma automática.
- No asumas equivalencia total entre Scopus y SciVal.
- No resuelvas ambigüedades institucionales sin declararlas.
</restrictions>

<required_output>
Entrega la respuesta en este formato:

## 1. Objetivo de la fase

## 2. Fundamentación metodológica mínima

## 3. Inventario de archivos
Presenta una tabla con estas columnas:
- Archivo
- Tipo
- Hojas/Tablas
- Utilidad principal
- Observaciones

## 4. Inventario de columnas
Presenta una tabla por archivo o tabla con:
- Campo
- Tipo aparente
- Posible significado
- Posible uso
- Riesgo/ambigüedad

## 5. Modelo lógico preliminar
Presenta una tabla con:
- Entidad
- Campos
- Fuente
- Relación con otras entidades
- Observaciones

## 6. Reglas de validación
Lista estructurada y verificable.

## 7. Ambigüedades críticas

## 8. Decisiones tomadas

## 9. Archivos a crear o modificar

## 10. Próximo paso recomendado
</required_output>

<definition_of_done>
La fase termina cuando existan:
- inventario de archivos,
- inventario de columnas reales,
- modelo lógico preliminar,
- reglas de validación,
- ambigüedades críticas identificadas.
</definition_of_done>
