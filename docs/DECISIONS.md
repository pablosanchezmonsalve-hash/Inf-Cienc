# Índice de decisiones

**Generado** por `src/state/snapshot.py` desde las tablas de `SESSION_NOTES.md`. No editar a mano.

Una decisión registrada aquí **no se reabre sin una razón nueva** (`CLAUDE.md`, `<memory_and_continuity>`).

| # | Decisión | Fundamento | Fase |
|---|---|---|---|
| `D-01` | `EID` es PK de Publicación; `DOI` clave secundaria | 100 % cobertura, 0 duplicados; 19 registros sin DOI | Fase 1 |
| `D-02` | Doble método de detección institucional con reconciliación obligatoria | Un solo método no es auditable | Fase 1 |
| `D-03` | Prohibido el matching por subcadena; patrón con límite de palabra | 15 falsos positivos medidos con `inis` | Fase 1 |
| `D-04` | `Autoria` es entidad puente de primera clase | La afiliación varía entre publicaciones | Fase 1 |
| `D-05` | Los `.RData` son referencia, nunca fuente de indicadores | Proceso generador no trazable | Fase 1 |
| `D-06` | SciVal = métricas y temática; Scopus = autoría y afiliación | Cada fuente aporta lo que la otra no tiene | Fase 1 |
| `D-07` | ORCID se modela vacío y declarado, no se omite | Exigido por `PROJECT_SPEC.md` | Fase 1 |
| `D-08` | Duplicados probables y ambigüedades se encolan, no se resuelven | Restricción de `CLAUDE.md` | Fase 1 |
| `D-09` | `No determinada` es categoría de primera clase | No inventar datos | Fase 1 |
| `D-10` | Todo indicador declara fuente, corte, ventana, n y método | Trazabilidad | Fase 1 |
| `D-11` | Métricas de revista en entidad separada de métricas de documento | No confundir revista con artículo | Fase 1 |
| `D-12` | «h-index en ventana», nunca «h-index» | No es el h-index de carrera | Fase 1 |
| `D-13` | ID institucional y reglas en configuración, no en código | Replicabilidad | Fase 1 |
| `D-14` | Salidas de conciliación son capa interna por defecto | `<data_governance>` | Fase 1 |
| `D-15` | Los 396 investigadores son set de validación, no fuente de verdad | Confirmado por el usuario | Fase 1 |
| `D-16` | Cada indicador declara su propio denominador (823 / 818 / 816) | Las banderas de disponibilidad de Fase 1 no permiten un total único | Fase 2 |
| `D-17` | Dos niveles de advertencia: nota contextual (19) y advertencia destacada (5) | Marcar todo por igual equivale a no marcar nada | Fase 2 |
| `D-18` | `AU-04` (FWCI por autor) se descarta, no se aproxima | El FWCI de un autor no es el promedio de sus publicaciones; calcularlo sería inventar la métrica | Fase 2 |
| `D-19` | La ficha de autor muestra «top 10 % de citación» en lugar de FWCI | Es normalizado por campo y sí está disponible por publicación | Fase 2 |
| `D-20` | Web estática con preagregación total en build | Corpus pequeño y de actualización esporádica; garantiza que lo publicado sea idéntico a lo auditado | Fase 2 |
| `D-21` | Fichas de autor como archivos individuales, no bundle único | Evita descargar ~3 MB para ver una ficha | Fase 2 |
| `D-22` | `src/build/` no lee de `data/raw/`; sólo de `data/interim/` validado | Barrera de calidad: sin validación no hay build | Fase 2 |
| `D-23` | La barrera pública/interna se verifica automáticamente post-build | No puede depender de que nadie se equivoque al escribir el build | Fase 2 |
| `D-24` | «Sin dato declarado» nunca se representa como 0 ni se excluye del 100 % | Consecuencia directa de D-09 (no imputar) | Fase 2 |
| `D-25` | Sin flechas de tendencia en los KPIs | Con 3 años y sin histórico previo, implicaría una tendencia que los datos no sostienen | Fase 2 |
| `D-26` | El FWCI se muestra con media y mediana juntas | Sólo la media (0,87) ocultaría que la mediana es 0,41 | Fase 2 |
| `D-27` | Los filtros incluyen «No determinada» y «Sin dato» como opciones reales | La ausencia de dato es información, no ruido a esconder | Fase 2 |
| `D-28` | Mapa coroplético y nube de palabras descartados | 23 países sobre ~200 exagera visualmente; la nube no tiene lectura cuantitativa | Fase 2 |
| `D-29` | Ranking de autores por defecto filtrado a n >= 5, sin excluir a nadie del catálogo | Calidad en la vista principal sin exclusión arbitraria | Fase 2 |
| `D-30` | Stack: HTML/CSS/JS sin dependencias + build en Python | Cero dependencias en el navegador; el sitio debe poder servirse en red cerrada. Sin toolchain que mantener | Fase 3 |
| `D-31` | Gráficos como SVG generados en el propio JS | Evita cargar una librería desde un CDN, cosa que el proyecto no puede permitirse | Fase 3 |
| `D-32` | El sitio se sirve desde `dist/`, no desde `web/` | Sin los datos ensamblados, `web/` no debe aparentar estar completo | Fase 3 |
| `D-33` | Tres compuertas con código de salida, no avisos | La separación de capas no puede depender de que nadie se equivoque | Fase 3 |
| `D-34` | Los atributos de publicación se materializan en `data/interim/` | Permite que `src/build/` no lea nunca de `data/raw/` (respeta D-22) | Fase 3 |
| `D-35` | Identificadores de autor únicos por firma, con sufijo de desambiguación | Dos variantes distintas nunca comparten archivo (ver hallazgo) | Fase 3 |
| `D-36` | `load_authorship()` proyecta sólo columnas publicables en la lectura | Los campos internos no pueden filtrarse por descuido más adelante | Fase 3 |
| `D-37` | Los denominadores se actualizan a mano en `config/indicators.yml` | Cambiar el denominador de todo lo publicado es una decisión, no un efecto secundario | Fase 3 |
| `D-38` | Toda exportación CSV arrastra la procedencia en su cabecera | Un CSV suelto sin fecha de corte deja de ser interpretable | Fase 3 |
| `D-39` | Licencia MIT para el software, separada de los datos | Permite adoptar el software sin heredar restricciones de Elsevier | Fase 3 |
| `D-40` | T-11 se implementa como supuesto parametrizado, no se bloquea | Publicar las 589 con ranking por defecto n >= 5; cambiarlo no requiere código | Fase 3 |
