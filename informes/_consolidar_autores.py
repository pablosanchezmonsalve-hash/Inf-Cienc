"""Consolida toda la información de autores en un informe por autor.

Lee fuentes ya en disco + la cobertura fresca de OpenAlex (fork a informes/)
y produce:
    informes/informe_autores.md        informe legible por autor
    informes/autores_consolidado.csv   tabla cruzada plana
No escribe en internal/ ni data/enriched.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

MASTER = ROOT / "data" / "interim" / "authors_master_draft.csv"
ORCID_ENRICHED = ROOT / "data" / "enriched" / "authors_orcid.csv"
IDENTIDADES_YML = ROOT / "config" / "identidades_consolidadas.yml"
AMBIGUITIES = ROOT / "internal" / "ambiguities_authors.csv"
COBERTURA = ROOT / "informes" / "run" / "openalex_cobertura" / "internal" / "openalex_cobertura.csv"


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    master = read_csv(MASTER)
    orcid_rows = read_csv(ORCID_ENRICHED)
    amb = read_csv(AMBIGUITIES)
    cob = read_csv(COBERTURA)

    # Mapa ORCID por forma de firma (la del enriched es más detallada).
    orcid_por_firma: dict[str, dict] = {}
    for r in orcid_rows:
        orcid_por_firma.setdefault(r["nombre_en_fuente"], r)

    # Mapa de identidad consolidada: variante -> canonica, origen, grupo.
    grupos: list[dict] = []
    if IDENTIDADES_YML.exists():
        data = yaml.safe_load(IDENTIDADES_YML.read_text(encoding="utf-8"))
        for g in data.get("grupos", []):
            grupos.append(g)

    variante_a_canonica: dict[str, dict] = {}
    for i, g in enumerate(grupos):
        for v in g.get("variantes", []):
            variante_a_canonica[v] = {"canonica": g["canonica"], "origen": g.get("origen", ""), "grupo": i}
        variante_a_canonica.setdefault(g["canonica"], {"canonica": g["canonica"], "origen": g.get("origen", ""), "grupo": i})

    # Ambigüedades por firma.
    amb_por_firma: dict[str, list[dict]] = {}
    for r in amb:
        amb_por_firma.setdefault(r["nombre_en_fuente"], []).append(r)

    # Cobertura: contar obras fuera del universo con DOI, agrupadas por autor
    # (nombre completo recuperado de OpenAlex si está).
    # La columna de autor no es estándar; lo contamos por título/DOI a nivel agregado.

    filas: list[dict] = []
    for m in master:
        nombre = m.get("nombre_en_fuente", "")
        nombre_norm = m.get("clave_normalizada", "")
        ident = variante_a_canonica.get(nombre) or variante_a_canonica.get(nombre_norm) or {}
        o = orcid_por_firma.get(nombre, None)
        filas.append({
            "forma_de_firma": nombre,
            "scopus_author_ids": m.get("scopus_author_ids", ""),
            "n_scopus_ids": m.get("n_scopus_author_ids", ""),
            "orcid_master": m.get("orcid", ""),
            "orcid_detallado": (o or {}).get("orcid", ""),
            "orcid_fuente": (o or {}).get("fuente", ""),
            "orcid_confianza": (o or {}).get("confianza", ""),
            "n_publicaciones": m.get("n_publicaciones", ""),
            "unidades": m.get("unidades_academicas", ""),
            "n_unidades": m.get("n_unidades_distintas", ""),
            "confianza_max": m.get("confianza_maxima", ""),
            "identidad_grupo": ident.get("canonica", ""),
            "identidad_origen": ident.get("origen", ""),
        })

    # ---- informe por autor (solo los que tienen algo de unidad O ORCID O identidad) ----
    out = ROOT / "informes"
    out.mkdir(parents=True, exist_ok=True)

    con_unidad = sum(1 for f in filas if f["unidades"])
    con_orcid = sum(1 for f in filas if f["orcid_detallado"])
    con_identidad = sum(1 for f in filas if f["identidad_grupo"])
    n_grupos = len(grupos)

    lines = []
    lines.append("# Informe consolidado de autores — recogida de datos\n")
    lines.append(f"_Generado: recogida de datos de todas las autorías y fuentes. "
                 f"No escribe en `internal/` ni `data/enriched`._\n")
    lines.append("## Resumen\n")
    lines.append(f"| Indicador | Valor |")
    lines.append(f"|---|---|")
    lines.append(f"| Formas de firma (fuente) | **{len(filas)}** |")
    lines.append(f"| Con unidad académica inferida | **{con_unidad}** |")
    lines.append(f"| Con ORCID (enriched) | **{con_orcid}** |")
    lines.append(f"| Con identidad consolidada visible | **{con_identidad}** |")
    lines.append(f"| Grupos de identidad consolidados | **{n_grupos}** |")
    lines.append(f"| Obras fuera del universo (OpenAlex, cola de revisión) | **{len(cob)}** |")
    lines.append("")

    # Distribución de unidades
    from collections import Counter
    uni_counter = Counter()
    for f in filas:
        if f["unidades"]:
            for u in f["unidades"].split("|"):
                uni_counter[u.strip()] += 1
    lines.append("### Distribución de unidades académicas (firmas)\n")
    lines.append("| Unidad | Firmas |")
    lines.append("|---|---|")
    for u, n in uni_counter.most_common():
        lines.append(f"| {u} | {n} |")
    if not uni_counter:
        lines.append("_(sin unidades inferidas)_")
    lines.append("")

    # Fuentes de ORCID
    fuentes_counter = Counter(f["orcid_fuente"] for f in filas if f["orcid_detallado"])
    lines.append("### ORCID por fuente\n")
    lines.append("| Fuente | Firmas |")
    lines.append("|---|---|")
    for src, n in fuentes_counter.most_common():
        lines.append(f"| {src or 'N/D'} | {n} |")
    lines.append("")

    # ---- detalle por autor ----
    lines.append("## Detalle por forma de firma\n")
    lines.append("Formas sin dato de unidad, ORCID ni identidad se omiten del detalle "
                 "(van en la tabla plana completa).\n")
    lines.append("| Firma | Scopus ID | ORCID | Fuente ORCID | Unidad | Publ. | Identidad |")
    lines.append("|---|---|---|---|---|---|---|")
    for f in filas:
        if not (f["unidades"] or f["orcid_detallado"] or f["identidad_grupo"]):
            continue
        ident = f["identidad_grupo"] + (f" · {f['identidad_origen']}" if f["identidad_origen"] else "")
        lines.append(
            f"| {f['forma_de_firma']} | {f['scopus_author_ids']} | "
            f"{f['orcid_detallado'] or ''} | {f['orcid_fuente'] or ''} | "
            f"{f['unidades'] or '—'} | {f['n_publicaciones']} | {ident or '—'} |"
        )
    lines.append("")

    (out / "informe_autores.md").write_text("\n".join(lines), encoding="utf-8")

    # ---- tabla plana completa ----
    cols = list(filas[0].keys())
    with open(out / "autores_consolidado.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(filas)

    # ---- consola ----
    print("\nAutores: cobertura de datos")
    for k, v in [
        ("Formas de firma", len(filas)),
        ("Con unidad", con_unidad),
        ("Con ORCID", con_orcid),
        ("Con identidad", con_identidad),
        ("Grupos de identidad", n_grupos),
        ("Fuera del universo (OpenAlex)", len(cob)),
    ]:
        print(f"  {k:32s}: {v}")

    print(f"\n  Informe : {out / 'informe_autores.md'}")
    print(f"  Tabla   : {out / 'autores_consolidado.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
