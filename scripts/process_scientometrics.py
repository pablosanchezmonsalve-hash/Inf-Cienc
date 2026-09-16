#!/usr/bin/env python3
"""
process_scientometrics.py
-------------------------
Script de procesamiento, consolidación y exportación cienciométrica
para el Informe Bibliométrico Institucional UFT (2020–2025).
"""

import json
import csv
from pathlib import Path

# Directorio de salida
OUTPUT_DIR = Path(__file__).parent

# 1. Definición del dataset consolidado (Auditoría UFT 2020–2025)
CONSOLIDATED_METRICS = {
    "institucion": "Universidad Finis Terrae",
    "periodo": "2020–2025",
    "fecha_corte": "2026-08-30",
    "fuente_primaria": "Scopus & SciVal",
    "universo_publicaciones": 1342,
    "citas_totales": 14245,
    "citas_por_publicacion_promedio": 10.61,
    "fwci_mediano": 0.48,
    "fwci_promedio": 1.14,
    "colaboracion_internacional": {
        "publicaciones": 668,
        "porcentaje": 49.8
    },
    "variantes_firma_autores": 829,
    "cuartiles_scimago_citescore": {
        "Q1": {"publicaciones": 612, "porcentaje": 45.6},
        "Q2": {"publicaciones": 378, "porcentaje": 28.2},
        "Q3": {"publicaciones": 220, "porcentaje": 16.4},
        "Q4": {"publicaciones": 132, "porcentaje": 9.8}
    },
    "acceso_abierto": {
        "Gold": 744,
        "Green": 730,
        "Hybrid": 87,
        "Bronze": 46,
        "Closed_Paywall": 399
    },
    "areas_qs": {
        "Life Sciences & Medicine": {"publicaciones": 862, "porcentaje_pubs": 64.2},
        "Social Sciences & Management": {"publicaciones": 344, "porcentaje_pubs": 25.6},
        "Engineering & Technology": {"publicaciones": 167, "porcentaje_pubs": 12.4},
        "Arts & Humanities": {"publicaciones": 153, "porcentaje_pubs": 11.4},
        "Natural Sciences": {"publicaciones": 109, "porcentaje_pubs": 8.1}
    },
    "produccion_por_ano": {
        "2020": 131,
        "2021": 199,
        "2022": 194,
        "2023": 227,
        "2024": 273,
        "2025": 318
    },
    "tipos_documentales": {
        "Article": 1010,
        "Review": 175,
        "Book Chapter": 45,
        "Conference Paper": 37,
        "Letter": 32,
        "Note": 14,
        "Editorial": 13,
        "Erratum": 9,
        "Short Survey": 4,
        "Book": 3
    },
    "unidades_academicas_top": {
        "Facultad de Medicina y Salud": 656,
        "No determinada / General": 482,
        "Facultad de Ingeniería": 70,
        "Facultad de Educación y Ciencias Sociales": 68,
        "Facultad de Economía y Negocios": 39,
        "Escuela de Kinesiología": 36,
        "Escuela de Nutrición y Dietética": 18,
        "Facultad de Humanidades y Comunicaciones": 9,
        "Facultad de Derecho": 9
    }
}

# 2. Generación de exportables

def export_json_ld():
    """Genera JSON-LD compatible con Schema.org ScholarlyArticle / EducationalOrganization."""
    schema = {
        "@context": "https://schema.org",
        "@type": "EducationalOrganization",
        "name": CONSOLIDATED_METRICS["institucion"],
        "publishingPrinciples": "https://doraopenletter.org",
        "memberOf": "Scopus / SciVal Audit Registry",
        "dataset": {
            "@type": "Dataset",
            "name": "Informe Bibliométrico Institucional UFT 2020-2025",
            "temporalCoverage": "2020/2025",
            "dateModified": CONSOLIDATED_METRICS["fecha_corte"],
            "size": f"{CONSOLIDATED_METRICS['universo_publicaciones']} publicaciones",
            "variableMeasured": [
                {"@type": "PropertyValue", "name": "Total Publicaciones", "value": CONSOLIDATED_METRICS["universo_publicaciones"]},
                {"@type": "PropertyValue", "name": "Citas Totales", "value": CONSOLIDATED_METRICS["citas_totales"]},
                {"@type": "PropertyValue", "name": "FWCI Mediano", "value": CONSOLIDATED_METRICS["fwci_mediano"]},
                {"@type": "PropertyValue", "name": "Porcentaje Q1+Q2", "value": "73.8%"}
            ]
        }
    }
    file_path = OUTPUT_DIR / "uft_bibliometria_summary.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
    print(f"[+] JSON-LD generado: {file_path}")

def export_csv_summary():
    """Genera dataset tabular CSV con métricas desglosadas por año."""
    file_path = OUTPUT_DIR / "uft_bibliometria_dataset.csv"
    
    headers = ["Año", "Publicaciones_UFT", "Citas_Acumuladas_Est", "Colaboracion_Int_Est_Pubs", "Publicaciones_Q1_Q2_Est"]
    
    rows = []
    tot_pubs = CONSOLIDATED_METRICS["universo_publicaciones"]
    for year, pubs in CONSOLIDATED_METRICS["produccion_por_ano"].items():
        weight = pubs / tot_pubs
        est_citas = round(CONSOLIDATED_METRICS["citas_totales"] * weight)
        est_colab = round(CONSOLIDATED_METRICS["colaboracion_internacional"]["publicaciones"] * weight)
        est_q1q2 = round((CONSOLIDATED_METRICS["cuartiles_scimago_citescore"]["Q1"]["publicaciones"] + 
                          CONSOLIDATED_METRICS["cuartiles_scimago_citescore"]["Q2"]["publicaciones"]) * weight)
        rows.append([year, pubs, est_citas, est_colab, est_q1q2])

    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"[+] CSV Dataset generado: {file_path}")

def export_markdown_report():
    """Genera informe ejecutivo consolidado en Markdown."""
    file_path = OUTPUT_DIR / "informe_ejecutivo_uft.md"
    m = CONSOLIDATED_METRICS
    
    md_content = f"""# Informe Ejecutivo Bibliométrico Institucional (2020–2025)
**{m['institucion']}** • *Fuentes: {m['fuente_primaria']}*  
**Fecha de Corte de Citas:** {m['fecha_corte']} | **Build:** 2026-09-10

---

## 📊 Métricas Consolidadas

- **Total de Publicaciones en el Quinquenio:** {m['universo_publicaciones']}
- **Citas Recibidas Totales:** {m['citas_totales']:,}
- **Promedio de Citas por Publicación:** {m['citas_por_publicacion_promedio']}
- **FWCI Mediano (Field-Weighted Citation Impact):** {m['fwci_mediano']} *(Media: {m['fwci_promedio']} | Referente global = 1,00)*
- **Colaboración Internacional:** {m['colaboracion_internacional']['porcentaje']}% ({m['colaboracion_internacional']['publicaciones']} publicaciones)
- **Firmas Institucionales Distintas:** {m['variantes_firma_autores']} variantes de firma

---

## 🎖️ Calidad Editorial por Cuartiles (SJR / CiteScore)

| Cuartil | Publicaciones | Porcentaje |
| :--- | :---: | :---: |
| **Q1 (Top 25%)** | {m['cuartiles_scimago_citescore']['Q1']['publicaciones']} | {m['cuartiles_scimago_citescore']['Q1']['porcentaje']}% |
| **Q2** | {m['cuartiles_scimago_citescore']['Q2']['publicaciones']} | {m['cuartiles_scimago_citescore']['Q2']['porcentaje']}% |
| **Q3** | {m['cuartiles_scimago_citescore']['Q3']['publicaciones']} | {m['cuartiles_scimago_citescore']['Q3']['porcentaje']}% |
| **Q4** | {m['cuartiles_scimago_citescore']['Q4']['publicaciones']} | {m['cuartiles_scimago_citescore']['Q4']['porcentaje']}% |
| **Total Q1 + Q2** | **{m['cuartiles_scimago_citescore']['Q1']['publicaciones'] + m['cuartiles_scimago_citescore']['Q2']['publicaciones']}** | **73.8%** |

---

## 🌐 Cobertura por Grandes Áreas Temáticas (QS)

*Nota: Una publicación puede pertenecer a más de una área temática (multivaluado).*

- **Life Sciences & Medicine:** {m['areas_qs']['Life Sciences & Medicine']['publicaciones']} publicaciones
- **Social Sciences & Management:** {m['areas_qs']['Social Sciences & Management']['publicaciones']} publicaciones
- **Engineering & Technology:** {m['areas_qs']['Engineering & Technology']['publicaciones']} publicaciones
- **Arts & Humanities:** {m['areas_qs']['Arts & Humanities']['publicaciones']} publicaciones
- **Natural Sciences:** {m['areas_qs']['Natural Sciences']['publicaciones']} publicaciones

---

## 🔓 Modalidad de Acceso Abierto (OA)

- **Gold Open Access:** {m['acceso_abierto']['Gold']} publicaciones
- **Green Open Access:** {m['acceso_abierto']['Green']} publicaciones
- **Hybrid Gold:** {m['acceso_abierto']['Hybrid']} publicaciones
- **Bronze:** {m['acceso_abierto']['Bronze']} publicaciones
- **Sin dato / Paywall:** {m['acceso_abierto']['Closed_Paywall']} publicaciones

---

*Informe generado automáticamente por `process_scientometrics.py` conforme a las directrices del Manifiesto de Leiden y DORA.*
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"[+] Informe Markdown generado: {file_path}")

if __name__ == "__main__":
    print("Iniciando consolidación cienciométrica UFT...")
    export_json_ld()
    export_csv_summary()
    export_markdown_report()
    print("Procesamiento finalizado con éxito.")
