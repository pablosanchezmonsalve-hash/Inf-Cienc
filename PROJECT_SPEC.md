# PROJECT_SPEC.md
# Especificación maestra del proyecto

<context>
Este proyecto busca construir una plataforma web interactiva para informes cienciométricos institucionales, iniciando con la Universidad Finis Terrae y con datos provenientes de Scopus y SciVal.

Referencia de inspiración:
https://dataciencia.anid.gob.cl/institution/1709

La referencia es conceptual y estructural, no una instrucción para copiar diseño literal.
</context>

<mission>
Crear una primera versión funcional, metodológicamente defendible y técnicamente replicable de una plataforma web que permita:
- explorar producción científica,
- analizar impacto,
- observar colaboración,
- identificar áreas temáticas,
- consultar autores afiliados,
- y publicar resultados en una interfaz clara e institucional.
</mission>

<v1_scope_required>
La V1 debe incluir obligatoriamente:
1. Auditoría de datos y modelo lógico inicial.
2. Tabla maestra de autores afiliados UFT.
3. Catálogo de indicadores posibles.
4. Selección priorizada de indicadores V1.
5. Arquitectura técnica base.
6. Diseño UX/UI del dashboard.
7. Definición de capa pública e interna.
8. Ficha pública de autor.
9. Tooltips o glosario en métricas no triviales.
10. Entregable técnico inicial y documentación mínima.
</v1_scope_required>

<v1_scope_desirable>
Deseable para V1 si los datos y el tiempo lo permiten:
- navegación facetada avanzada,
- breadcrumbs completos,
- persistencia de filtros en URL,
- exportación de subconjuntos,
- carga diferida de módulos,
- conectores preparados a APIs.
</v1_scope_desirable>

<out_of_scope_for_v1>
No es obligatorio para V1:
- backend complejo,
- autenticación avanzada,
- automatización completa de ingestión desde APIs pagadas,
- benchmarking interinstitucional amplio,
- analítica predictiva,
- recomendadores,
- paneles administrativos sofisticados,
- modelamiento temático avanzado no sustentado por los datos.
</out_of_scope_for_v1>

<functional_requirements>
La plataforma debe permitir, si los datos lo sostienen:
- visualizar KPIs institucionales,
- filtrar por año, autor, tipo documental, área temática, unidad académica o equivalente,
- consultar tablas de publicaciones,
- explorar rankings de autores y fuentes,
- observar evolución temporal,
- revisar colaboración,
- acceder a fichas públicas de autor,
- interpretar indicadores con ayuda contextual.
</functional_requirements>

<public_author_profile>
La ficha pública de autor debe contemplar, cuando esté disponible:
- nombre normalizado,
- nombre en fuente,
- afiliación UFT asociada,
- ORCID,
- Scopus Author ID,
- otros identificadores públicos,
- total de publicaciones,
- total de citas,
- citas por publicación,
- h-index si puede calcularse con trazabilidad,
- FWCI u otra métrica normalizada solo si existe realmente,
- evolución temporal,
- lista de publicaciones con DOI,
- coautorías o colaboración destacada si es viable.

Debe incluir advertencia metodológica sobre interpretación de métricas individuales.
</public_author_profile>

<replicability_definition>
En este proyecto, “replicable” significa:
1. parametrizable para otra institución,
2. documentado para despliegue independiente,
3. adaptable a nuevas cargas de datos sin reescribir toda la lógica base,
4. separable entre software reutilizable y datos institucionales.
</replicability_definition>

<success_criteria>
Una fase o entregable se considera satisfactorio cuando:
- las decisiones están documentadas,
- las limitaciones están explícitas,
- los supuestos están declarados,
- la salida tiene estructura verificable,
- y el siguiente paso está definido con claridad.
</success_criteria>
