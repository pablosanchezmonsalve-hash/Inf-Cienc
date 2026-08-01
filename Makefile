# Pipeline completo del proyecto.
#
# Cada objetivo depende del anterior. El build aborta si la auditoría tiene
# reglas bloqueantes fallando o si la verificación de capas encuentra material
# interno en un artefacto público.

.PHONY: instalar auditoria factibilidad artefactos sitio servir estado limpiar todo

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

limpiar:
	rm -rf dist data/processed
	find . -name __pycache__ -type d -prune -exec rm -rf {} +

todo: sitio estado
