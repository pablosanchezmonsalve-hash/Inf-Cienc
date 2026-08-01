"""03 — Variantes institucionales, matching y unidad académica.

Aplica las reglas I-01..I-08. Construye el log de trazabilidad autor x publicación
y reconcilia el método duro (Scopus Affiliation ID) contra el blando (patrón
sobre la cadena de afiliación).

Salidas:
  data/interim/affiliation_variants.csv
  data/interim/academic_unit_vocabulary.csv
  data/interim/matching_reconciliation.csv
  internal/matching_log.csv
"""

from __future__ import annotations

import re

import pandas as pd

import common as c


def main() -> None:
    c.banner("03 — VARIANTES INSTITUCIONALES Y MATCHING")

    scopus = c.read_scopus()
    scival = c.read_scival()
    sv_idx = scival.set_index("EID")

    # ------------------------------------------------- I-05: falsos positivos
    # Se mide el daño de cada patrón prohibido en vez de afirmarlo: cada cadena
    # que el patrón laxo captura y el patrón con límite de palabra no, es un
    # falso positivo que se habría colado como afiliación institucional.
    prohibidos = c.MATCHING["deteccion_institucional"]["metodo_blando"]["patrones_prohibidos"]
    for laxo_pat in prohibidos:
        laxo = re.compile(laxo_pat, re.IGNORECASE)
        fp = set()
        for aff in scopus["Affiliations"].dropna():
            for chunk in aff.split(";"):
                chunk = chunk.strip()
                if laxo.search(c.strip_accents(chunk)) and not c.matches_institution_soft(chunk):
                    fp.add(chunk[:90])
        print(f"I-05 · patrón prohibido {laxo_pat!r}: {len(fp)} cadenas de falso positivo")
        for x in sorted(fp)[:3]:
            print(f"        {x}")

    # --------------------------------------- I-03: catálogo de variantes reales
    variantes: dict[str, int] = {}
    for aff in scopus["Affiliations"].dropna():
        for chunk in aff.split(";"):
            chunk = chunk.strip()
            if c.matches_institution_soft(chunk):
                variantes[chunk] = variantes.get(chunk, 0) + 1

    var_df = (pd.DataFrame(
        [{"cadena_afiliacion": k, "frecuencia": v,
          "unidad_extraida": c.extract_academic_unit(k),
          "unidad_canonica": c.canonical_academic_unit(c.extract_academic_unit(k))}
         for k, v in variantes.items()])
        .sort_values("frecuencia", ascending=False)
        .reset_index(drop=True))

    total_apariciones = int(var_df["frecuencia"].sum())
    con_unidad = int(var_df.loc[var_df["unidad_extraida"].notna(), "frecuencia"].sum())
    print(f"I-03 · cadenas de afiliación institucional distintas: {len(var_df)}")
    print(f"I-03 · apariciones totales: {total_apariciones}")
    print(f"I-06 · con unidad académica inferible: {con_unidad} "
          f"({100 * con_unidad / total_apariciones:.1f} %)")

    # --------------------------------------------------- I-07: vocabulario
    vocab = (var_df[var_df["unidad_extraida"].notna()]
             .groupby(["unidad_canonica", "unidad_extraida"], as_index=False)["frecuencia"].sum()
             .sort_values(["unidad_canonica", "frecuencia"], ascending=[True, False]))
    en_vocab = set(c.MATCHING["unidad_academica"]["vocabulario"])
    vocab["en_vocabulario_controlado"] = vocab["unidad_canonica"].isin(en_vocab)
    print(f"I-07 · variantes de unidad distintas: {vocab['unidad_extraida'].nunique()}")
    print(f"I-07 · mapeadas al vocabulario controlado: "
          f"{int(vocab.loc[vocab['en_vocabulario_controlado'], 'frecuencia'].sum())} apariciones")
    print(f"I-07 · fuera del vocabulario (conservadas tal cual): "
          f"{vocab.loc[~vocab['en_vocabulario_controlado'], 'unidad_extraida'].nunique()} variantes")

    # ------------------------- log de trazabilidad autor x publicación (I-01/04)
    log, desalineadas = [], []
    for _, row in scopus.iterrows():
        eid = row["EID"]
        bloques = c.split_author_blocks(row["Authors with affiliations"])
        autores = [a.strip() for a in str(row["Authors"]).split(";") if a.strip()]
        if len(bloques) != len(autores):
            desalineadas.append(eid)

        hard = c.matches_institution_hard(
            sv_idx.loc[eid]["Scopus Affiliation IDs"] if eid in sv_idx.index else None)

        for pos, bloque in enumerate(bloques, start=1):
            if not c.matches_institution_soft(bloque):
                continue
            nombre = c.author_name_from_block(bloque)
            afil = bloque[len(nombre):].lstrip(", ").strip()
            unidad_raw = c.extract_academic_unit(afil)
            log.append({
                "eid": eid,
                "anio": row["Year"],
                "posicion_autor": pos,
                "n_autores_total": len(autores),
                "nombre_en_fuente": nombre,
                "clave_normalizada": c.normalize_author_key(nombre),
                "clave_apellido": c.surname_key(nombre),
                "afiliacion_declarada_raw": afil[:300],
                "unidad_academica_raw": unidad_raw,
                "unidad_academica": c.canonical_academic_unit(unidad_raw),
                "metodo_blando": True,
                "metodo_duro_publicacion": hard,
                "confianza": "alta" if hard else "media",
            })

    log_df = pd.DataFrame(log)

    # -------------------------------------------------- I-04: reconciliación
    pub_soft = set(log_df["eid"])
    pub_hard = {eid for eid in scopus["EID"]
                if eid in sv_idx.index
                and c.matches_institution_hard(sv_idx.loc[eid]["Scopus Affiliation IDs"])}
    solo_duro = pub_hard - pub_soft
    solo_blando = pub_soft - pub_hard

    print(f"\nI-02 · publicaciones detectadas por método duro  : {len(pub_hard)}")
    print(f"I-03 · publicaciones detectadas por método blando: {len(pub_soft)}")
    print(f"I-04 · sólo por método duro   : {len(solo_duro)}  <- sin autor de la institución identificable")
    print(f"I-04 · sólo por método blando : {len(solo_blando)}")
    print(f"I-01 · publicaciones sin ninguna detección: "
          f"{len(set(scopus['EID']) - pub_soft - pub_hard)}")
    print(f"\nRiesgo de parsing · publicaciones con nº de bloques != nº de autores: "
          f"{len(desalineadas)}")

    recon = pd.DataFrame(
        [{"eid": e, "caso": "solo_metodo_duro",
          "consecuencia": "afiliación institucional confirmada, pero ningún autor identificable como de la institución",
          "resolucion": "PENDIENTE_REVISION_HUMANA"} for e in sorted(solo_duro)]
        + [{"eid": e, "caso": "solo_metodo_blando",
            "consecuencia": "cadena de afiliación coincide, pero sin Scopus Affiliation ID institucional",
            "resolucion": "PENDIENTE_REVISION_HUMANA"} for e in sorted(solo_blando)]
        + [{"eid": e, "caso": "bloques_autor_desalineados",
            "consecuencia": "el parsing de 'Authors with affiliations' puede atribuir mal la afiliación",
            "resolucion": "PENDIENTE_REVISION_HUMANA"} for e in sorted(desalineadas)])

    c.write_interim(var_df, "affiliation_variants.csv")
    c.write_interim(vocab, "academic_unit_vocabulary.csv")
    c.write_interim(recon, "matching_reconciliation.csv")
    c.write_internal(log_df, "matching_log.csv")

    print(f"\nLog de trazabilidad: {len(log_df)} pares autor x publicación")
    print(f"  confianza alta : {int((log_df['confianza'] == 'alta').sum())}")
    print(f"  confianza media: {int((log_df['confianza'] == 'media').sum())}")
    print("\nDistribución por unidad académica (pares autor x publicación):")
    print(log_df["unidad_academica"].value_counts().head(12).to_string())
    print("\nOK · internal/matching_log.csv")


if __name__ == "__main__":
    main()
