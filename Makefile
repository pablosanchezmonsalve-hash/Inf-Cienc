# Pipeline completo del proyecto.
#
# Cada objetivo depende del anterior. El build aborta si la auditoría tiene
# reglas bloqueantes fallando o si la verificación de capas encuentra material
# interno en un artefacto público.

.PHONY: instalar auditoria factibilidad artefactos sitio servir estado revision validar-unidades kit verificar rendimiento verificar-orcid ror openalex cobertura scopus orcid-afiliacion informe limpiar todo

instalar:
	pip install -r requirements.txt

auditoria:
	python3 src/audit/run_all.py

factibilidad:
	python3 src/analysis/indicator_feasibility.py

artefactos: auditoria factibilidad
	python3 src/build/build_all.py

sitio: artefactos
	python3 src/build/06_assemble_site.py

servir: sitio
	python3 -m http.server -d dist 8000

estado:
	python3 src/state/snapshot.py

# Paquete de sistema de diseño para Claude Design (claude.ai/design).
# Se GENERA desde la hoja de estilo, los constructores de gráfico y los
# artefactos reales, de modo que no puede desactualizarse respecto del
# producto: si divergen, es que no se ha vuelto a generar. Ver docs/UX_UI.md.
kit: artefactos
	node src/design/build_kit.mjs

# Batería de verificación del sitio construido: contraste WCAG, estructura y
# consola, flujos interactivos, responsive e higiene de CSS/JS. Levanta y baja
# su propio servidor. Exige Playwright y Chromium.
#
# Vive aquí y no en un directorio temporal a propósito: una verificación que hay
# que reescribir en cada sesión no es una verificación, y una reescrita de
# memoria no es la misma. Ver src/verify/run_all.mjs.
verificar: sitio
	node src/verify/run_all.mjs

# Fuera de la batería porque tarda minutos: LCP con cinco corridas por página.
# Requiere un segundo servidor en PUERTO_SIN con una versión sin pre-renderizar
# para poder comparar; sin él mide sólo la columna pre-renderizada.
rendimiento: sitio
	node src/verify/rendimiento.mjs

# Herramienta de revisión humana de identidad de autor. Capa interna:
# la salida vive en internal/ y nunca entra en dist/.
# Verificación de ORCID contra el registro público. Requiere credenciales
# gratuitas en el entorno; ver docs/ORCID_API_GUIDE.md.
# En Windows es más simple: scripts/verificar-orcid.ps1 (clic derecho ->
# «Ejecutar con PowerShell») hace la secuencia entera y pide el secret oculto.
verificar-orcid:
	python3 src/enrich/orcid_api.py

# Ficha de la institución en ROR (V2-20): cierra ror_id e isni, y contrasta el
# patrón de detección institucional contra los nombres que ROR registra.
# En Windows:  py src\enrich\ror_institucion.py
ror:
	python3 src/enrich/ror_institucion.py

# Enriquecimiento y contraste desde OpenAlex (V2-19). Aporta ORCID donde no
# había y compara la detección institucional contra la desambiguación de
# OpenAlex. NO cuenta como segunda fuente independiente: OpenAlex ingiere
# Crossref. La mitad del contraste exige haber corrido `make ror` antes.
# En Windows:  py src\enrich\orcid_openalex.py
openalex:
	python3 src/enrich/orcid_openalex.py

# Brecha de cobertura (V2-26): qué producción atribuye OpenAlex a la institución
# que el universo NO tiene. Exige `make ror` antes: pregunta por identificador,
# no por nombre. Es una cola de revisión, no un ajuste del corpus.
# En Windows:  py src\enrich\openalex_cobertura.py
cobertura:
	python3 src/enrich/openalex_cobertura.py

# Fecha de corte para T-06: consulta la Scopus Search API con la misma cadena
# AF-ID + PUBYEAR que hoy se exporta a mano, y reporta instante de ejecución,
# consulta literal y recuento — para pegar a mano en config/sources.yml. NO
# reemplaza el corpus vigente. Exige SCOPUS_API_KEY en el entorno.
# En Windows es más simple: scripts/consultar-scopus.ps1 (clic derecho ->
# «Ejecutar con PowerShell») prueba la lógica, pide la API Key oculta y
# consulta. A mano:  py src\enrich\scopus_api.py
scopus:
	python3 src/enrich/scopus_api.py

# Candidatos de ORCID por afiliación declarada (T-19): busca en el registro
# público a quien declara la institución y cruza contra firmas sin ORCID.
# NO asigna nada solo — deja candidatos en internal/ para make revision.
# Requiere ORCID_CLIENT_ID y ORCID_CLIENT_SECRET (gratuitos, ver
# docs/ORCID_API_GUIDE.md). En Windows: scripts/ampliar-orcid-afiliacion.ps1
orcid-afiliacion:
	python3 src/enrich/orcid_afiliacion.py

# El informe institucional en PDF, desde el sitio ya construido. Usa la MISMA
# hoja de impresión que el botón «Descargar informe» de la interfaz: un origen,
# dos consumidores. Exige Playwright y Chromium, como `make verificar`.
informe: sitio
	node src/build/informe_pdf.mjs dist dist/informe-cienciometrico.pdf

# En Windows: scripts/revisar-identidad.ps1 (clic derecho -> «Ejecutar con
# PowerShell»). Hace la secuencia entera —generar, abrir, recoger el CSV
# exportado, aplicar y reconstruir— porque son siete pasos en el orden justo y
# la decisión D-85 ya dice qué pasa con eso.
revision: auditoria
	python3 src/review/build_review.py
	python3 src/review/build_unit_validation.py
	python3 src/review/build_hallazgos.py

# T-02: genera internal/validacion_unidades.html (herramienta interactiva) y
# .md (lectura). En Windows: scripts/validar-unidades.ps1 hace además el
# recojo del CSV exportado y la aplicación. A mano, tras exportar el CSV:
#   python3 src/review/apply_unit_validation.py --dry-run
#   python3 src/review/apply_unit_validation.py
validar-unidades: auditoria
	python3 src/review/build_unit_validation.py

# Vista de la red de coautoría con el grafo REAL, para revisión interna.
# Depende del grafo, que lo deja el build. C-05 SÍ se publica ahora en el
# sitio (colaboracion.html, recorte en vivo); esta vista sigue siendo la
# herramienta de revisión de internal/, no lo que ve el público.
red:
	python3 src/build/grafo_coautoria.py
	python3 src/review/vista_red.py

limpiar:
	rm -rf dist data/processed design-system
	find . -name __pycache__ -type d -prune -exec rm -rf {} +

todo: sitio estado
