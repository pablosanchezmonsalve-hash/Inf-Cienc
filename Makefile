# Pipeline completo del proyecto.
#
# Cada objetivo depende del anterior. El build aborta si la auditoría tiene
# reglas bloqueantes fallando o si la verificación de capas encuentra material
# interno en un artefacto público.

.PHONY: instalar auditoria factibilidad artefactos sitio servir estado revision kit verificar rendimiento verificar-orcid limpiar todo

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

revision: auditoria
	python3 src/review/build_review.py
	python3 src/review/build_unit_validation.py

limpiar:
	rm -rf dist data/processed design-system
	find . -name __pycache__ -type d -prune -exec rm -rf {} +

todo: sitio estado
