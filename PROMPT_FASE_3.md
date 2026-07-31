<phase>
Fase 3: Implementación, despliegue, documentación y replicabilidad
</phase>

<precondition>
Asume que Fase 1 y Fase 2 ya fueron aprobadas.
Si detectas contradicciones entre ellas, decláralas antes de implementar.
</precondition>

<objective>
1. Preparar la estructura técnica inicial del proyecto.
2. Generar entregable funcional base.
3. Documentar despliegue y actualización.
4. Dejar el proyecto listo para apertura y replicabilidad.
</objective>

<instructions>
### Implementación
Define:
- estructura de carpetas,
- scripts de preparación y validación,
- archivos procesados,
- interfaz web inicial,
- lógica de filtros,
- componentes de autor, indicadores y detalle documental,
- separación entre capa pública e interna.

### Documentación
Genera o especifica:
- README,
- instrucciones de instalación,
- instrucciones de actualización de datos,
- instrucciones de despliegue,
- documentación mínima de arquitectura,
- nota metodológica,
- lista de pendientes V2.

### Replicabilidad
Asegura que otra institución pueda adaptar el sistema cambiando:
- nombre institucional,
- branding básico,
- reglas de matching,
- fuentes de datos procesadas,
sin reescribir la lógica principal.

### Licencia y uso
Propón:
- licencia del software,
- nota sobre uso de datos institucionales,
- separación entre código reutilizable y datos sensibles o locales.
</instructions>

<restrictions>
- No dependas de un backend obligatorio para la V1 pública.
- No asumas acceso activo a APIs pagadas.
- No dejes la parametrización oculta.
- No mezcles decisiones metodológicas con instrucciones técnicas sin etiquetarlas.
</restrictions>

<required_output>
Entrega la respuesta en este formato:

## 1. Objetivo de la fase

## 2. Estructura del proyecto
Incluye árbol de carpetas y propósito por carpeta/archivo.

## 3. Archivos a crear
Presenta una tabla con:
- Archivo
- Propósito
- Capa (pública/interna/técnica)
- Prioridad

## 4. Implementación inicial
Describe módulos, scripts y flujo de trabajo.

## 5. Documentación requerida
Lista exacta de documentos y contenido mínimo.

## 6. Estrategia de despliegue

## 7. Estrategia de replicabilidad

## 8. Licencia y uso de datos

## 9. Pendientes V2

## 10. Dudas críticas

## 11. Decisiones tomadas

## 12. Próximo paso recomendado
</required_output>

<definition_of_done>
La fase termina cuando existan:
- estructura del proyecto,
- lista de archivos a crear,
- estrategia de despliegue,
- estrategia de replicabilidad,
- propuesta de licencia,
- pendientes claros para V2.
</definition_of_done>
