# Product Requirements Document (PRD) & Brief Ejecutivo

**Proyecto:** Plataforma Institucional de Inteligencia Cienciométrica y Memoria Científica  
**Institución Patrocinante:** Vicerrectoría de Investigación y Doctorados (VRID) — Universidad Finis Terrae  
**Versión del Documento:** 1.0 (Auditoría & Consolidación)  
**Fecha:** Octubre 2024 / Ventana Analítica: 2020–2025 (Corte Scopus/SciVal: 2026-08-30)  
**Estado:** Aprobado para Implementación y Despliegue  

---

## 1. Resumen Ejecutivo y Visión del Producto

### 1.1 Declaración de la Visión
Construir el ecosistema digital de referencia para la consulta, gobernanza, rendición de cuentas y comunicación del impacto científico de la Universidad Finis Terrae. La solución transforma datos cienciométricos crudos (Elsevier Scopus y SciVal) en inteligencia estratégica accionable, con doble propósito:
1. **Gobierno y Acreditación:** Proveer a directivos, decanos y comisiones evaluadoras métricas normalizadas rigurosas, trazables y auditadas conforme a las directrices DORA y el Manifiesto de Leiden.
2. **Pedagogía y Alfabetización Científica:** Explicar con claridad conceptual a públicos no expertos los fenómenos cienciométricos (asimetría del impacto, maduración temporal de citas y normalización disciplinar).

### 1.2 Objetivos Estratégicos de Negocio / Institucionales
- **Centralizar el universo analítico auditado:** 1.342 publicaciones arbitradas (2020–2025), 14.245 citas acumuladas (10,61 citas/doc) y 829 formas de firma estandarizadas.
- **Democratizar el acceso al conocimiento:** Visibilizar el 70,3% de producción en Ciencia Abierta (Rutas Dorada, Verde e Híbrida) conforme a la Política Nacional de Ciencia Abierta (ANID).
- **Proveer capacidad de exportación multicanal:** Generación inmediata de informes ejecutivos en PDF de alta fidelidad para imprenta (300 DPI / A4) y exportación masiva de datos en formatos abiertos (.CSV, .XLSX, .RIS, JSON-LD).
- **Garantizar inclusión digital:** Cumplimiento estricto del estándar de accesibilidad web **WCAG 2.1 Niveles AA y AAA**.

---

## 2. Personas y Usuarios Clave

| Arquetipo de Usuario | Rol Institucional | Necesidades Principales | Pain Points Actuales |
| :--- | :--- | :--- | :--- |
| **Vicerrector / Director de Investigación** | Tomador de Decisiones Estratégicas | KPIs consolidados a primer golpe de vista, tendencias sexenales, comparativa con la media mundial (FWCI = 1,14). | Sobrecarga de tablas densas sin jerarquía visual ni narrativa de impacto. |
| **Decano / Director de Escuela** | Gestión Académica y Curricular | Desglose por áreas QS y unidades académicas, identificación de fortalezas interdisciplinares y áreas de oportunidad. | Dificultad para desglosar el aporte facultativo frente a filiaciones centrales genéricas (35,9%). |
| **Investigador(a) / Claustro Académico** | Generador de Conocimiento | Trazabilidad de citas, visibilidad de sus obras insignia, coautorías internacionales (49,8%) e identificadores (ORCID, Scopus ID). | Miedo a ser evaluados por factores de impacto brutos sin normalización disciplinar. |
| **Pares Evaluadores / Comisión Nacional de Acreditación (CNA)** | Auditor Externo de Calidad | Evidencia verificable, fechas de corte congeladas, trazabilidad criptográfica (SHA-256) y colofón técnico de edición. | Informes estáticos desactualizados o con duplicidades por filiaciones hospitalarias. |

---

## 3. Arquitectura de Información y Mapa de Pantallas

El ecosistema digital se estructura en **6 interfaces interactivas** complementadas por el **Dossier Editorial Exportable**:

```
                              [ Acceso Institucional SSO (SCREEN_11) ]
                                                │
                                                ▼
                                [ Dashboard Ejecutivo Central (SCREEN_17) ]
                                                │
        ┌────────────────────────┬──────────────┴───────────────┬────────────────────────┐
        ▼                        ▼                              ▼                        ▼
[ Explorador Científico ] [ Perfiles de Investigador ] [ Detalle de Facultad ] [ Data Hub de Exportación ]
     (SCREEN_16)               (SCREEN_15)                   (SCREEN_13)               (SCREEN_14)
        │
        └───────────────────────────────────────┬────────────────────────────────────────┘
                                                ▼
                         [ Dossier Editorial & Memoria Científica (SCREEN_2) ]
                                     (Versión Imprenta A4 / PDF 300 DPI)
```

### 3.1 Detalle Funcional por Módulo
1. **Acceso Institucional SSO (`SCREEN_11`):** Autenticación federada (SAML 2.0 / Google Workspace UFT / Entra ID) con roles parametrizados (*Autoridad Central*, *Decanatura*, *Investigador*, *Auditor CNA*).
2. **Dashboard Ejecutivo Central (`SCREEN_17`):** Bento Grid con 6 KPIs cardinales, curva de crecimiento sexenal (131 a 318 docs/año, $R^2=0,942$), taxonomía QS y conmutador didáctico Media vs. Mediana FWCI.
3. **Explorador Científico (`SCREEN_16`):** Catálogo granular de 1.342 artículos con filtros facetados en cascada (Años, Áreas QS, Tipo Documental, Cuartil Scimago, Acceso Abierto). Acciones rápidas de copiado de DOI y citas BibTeX.
4. **Detalle de Investigador (`SCREEN_15`):** Monografía de productividad individual (e.g., Dr. Roberto Arismendi), mapa de grafos de coautoría internacional y desglose de impacto normalizado.
5. **Detalle de Facultad (`SCREEN_13`):** Benchmark interno departamental, cumplimiento de mandatos Open Access y productividad cruzada interdisciplinar.
6. **Data Hub de Descarga (`SCREEN_14`):** Generador de datasets a la medida con selectores de campos por `<fieldset>`, previsualización de esquema y estimación de tiempo de descarga (~2.4s).
7. **Dossier Editorial A4 (`SCREEN_2`):** Informe monográfico autónomo empaquetado en HTML5/CSS nativo con reglas `@media print` para volcado directo a PDF de 300 DPI o imprenta offset.

---

## 4. Requerimientos Funcionales (FR)

- **FR-01 (Métricas Normalizadas):** El sistema debe calcular y desplegar simultáneamente el **FWCI Promedio (1,14)** y el **FWCI Mediano (0,48)**, acompañados de micro-textos explicativos para evitar interpretaciones erróneas por outliers hipercitados.
- **FR-02 (Filtros Facetados Reactivos):** El explorador debe permitir filtrar el universo por ventanas de año, unidades académicas, áreas temáticas y rutas de acceso abierto en tiempo real con indicador `aria-live`.
- **FR-03 (Exportación Dual PDF / Datos Abiertos):**
  - Botón de generación de **PDF Oficial** con preservación de formato A4 vertical, márgenes de 18mm/15mm y eliminación de elementos cromáticos superfluos mediante `@media print`.
  - Exportador masivo de tablas en `.CSV` (UTF-8 con BOM), `.XLSX` estructurado y `.RIS` para gestores bibliográficos (Zotero, Mendeley).
- **FR-04 (Trazabilidad y Sello Criptográfico):** Cada reporte generado debe exhibir el hash SHA-256 de integridad del dataset, la versión del algoritmo de desduplicación (v4.2) y la fecha de corte auditada.
- **FR-05 (Autonomía de Código):** La pantalla de reporte (`dossier.html`) debe ser 100% autónoma (*self-contained*), permitiendo su alojamiento estático directo en GitHub Pages sin dependencias de backend.

---

## 5. Requerimientos No Funcionales (NFR)

- **NFR-01 — Accesibilidad (WCAG 2.1 AA/AAA):**
  - Contraste tipográfico de al menos 4.5:1 en textos secundarios y superior a 12.5:1 en textos principales (#00205b sobre blanco).
  - Navegabilidad íntegra por teclado (`Tab`, `Shift+Tab`, `Enter`, `Space`) con enlace de salto rápido (`#contenido-principal`).
  - Atributos ARIA en todos los estados dinámicos (`aria-pressed`, `aria-selected`, `role="progressbar"`, `role="img"`).
- **NFR-02 — Rendimiento:**
  - First Contentful Paint (FCP) < 1.0s sobre redes institucionales.
  - Cero dependencias de librerías pesadas en cliente; estilización mediante utilidades CSS optimizadas y tipografías optimizadas de Google Fonts (*Newsreader* e *Inter*).
- **NFR-03 — Compatibilidad Cross-Browser y de Impresión:**
  - Soporte asegurado para Chromium (Chrome, Edge), Gecko (Firefox) y WebKit (Safari).
  - Fidelidad idéntica en generación de PDF a través del motor de impresión del navegador o automatizaciones headless (Playwright / Puppeteer).

---

## 6. Principios Editoriales & Cienciométricos (Directrices de Marca y Contenido)

1. **Adhesión a DORA (San Francisco Declaration on Research Assessment):** Prohibición explícita de categorizar o evaluar la calidad de investigadores individuales basándose en el Factor de Impacto (JIF) de la revista.
2. **Principio de Multivaluación ASJC:** Toda tabla y gráfico de áreas QS debe advertir explícitamente que los porcentajes suman más de 100% debido a publicaciones interdisciplinarias.
3. **Ventana de Maduración Temporal:** Señalización obligatoria en los últimos 2 años de la serie (2024 y 2025) como "Ventana Temprana / En Maduración" para evitar comparaciones injustas con años que ya han acumulado 5 años de citas.

---

## 7. Plan de Lanzamiento, Despliegue y Próximos Pasos

1. **Fase 1 (Completada):** Auditoría analítica de fuentes Scopus/SciVal, diseño del Design System institucional, prototipado de 6 pantallas y desarrollo del Dossier Editorial en HTML5/CSS autónomo.
2. **Fase 2 (Inmediata):** Integración de `dossier.html` en la raíz del repositorio de GitHub Pages (`Inf-Cienc`), enlazado en la cabecera del portal.
3. **Fase 3 (Automatización):** Configuración de un workflow de *GitHub Actions* para compilación automatizada de PDF con *Playwright* en cada release semestral.