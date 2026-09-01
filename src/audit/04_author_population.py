"""04 — Población de autores afiliados y descomposición de la brecha 585/440/396.

Construye el borrador de la tabla maestra de autores y explica la diferencia
entre la extracción automática y el trabajo manual previo. Aplica P-03..P-05.

El colapso de variantes de nombre está DESHABILITADO por configuración: las
variantes se detectan y se encolan, nunca se fusionan (CLAUDE.md,
<author_master_rule>).

Salidas:
  data/interim/authors_master_draft.csv
  data/interim/author_population_gap.csv
  internal/ambiguities_authors.csv
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

if sys.platform == "win32":
    # La consola de Windows usa cp1252 por defecto: revienta cualquier print()
    # con caracteres como "→"/"✗"/"⚠". Mismo patrón que src/enrich/orcid_openalex.py.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import common as c



def scopus_id_map(scopus: pd.DataFrame) -> dict[str, set[str]]:
    """Nombre completo -> Scopus Author ID(s), desde 'Author full names'."""
    out: dict[str, set[str]] = {}
    for full in scopus["Author full names"].dropna():
        for part in full.split("; "):
            m = re.match(r"(.+?)\s+\((\d+)\)$", part.strip())
            if m:
                out.setdefault(m.group(1).strip(), set()).add(m.group(2))
    return out



def _firma_corta(full: str) -> str:
    """«Apellido, Nombre» -> «Apellido N.», la forma con la que firma.

    Es el mismo cálculo que arma `id_by_short`. Se extrae a función porque
    ahora lo necesitan dos sitios, y tenerlo dos veces era la forma segura de
    que un día dejaran de coincidir.
    """
    parts = full.split(",")
    short = parts[0].strip()
    if len(parts) > 1:
        initials = "".join(w[0] + "." for w in parts[1].split() if w[:1].isalpha())
        short = f"{short} {initials}".strip()
    return short


def _ids_por_publicacion(scopus: pd.DataFrame) -> dict[str, set[str]]:
    """EID -> los Scopus Author ID que firman esa publicación."""
    col = "EID" if "EID" in scopus.columns else scopus.columns[0]
    out: dict[str, set[str]] = {}
    for _, r in scopus.iterrows():
        full = r.get("Author full names")
        if not isinstance(full, str):
            continue
        out[r[col]] = {m.group(2) for m in
                       (re.match(r"(.+?)\s+\((\d+)\)$", p.strip())
                        for p in full.split("; ")) if m}
    return out


# Una firma de persona en esta fuente lleva siempre inicial con punto:
# «Apellido X.», «Apellido-Compuesto X.Y.». Un fragmento de cadena de afiliación
# —«School of Psychology», «and Senior Lecturer»— no.
INICIAL = re.compile(r"[A-ZÁÉÍÓÚÑÜ]\.")


def firmas_sin_forma_de_persona(log: pd.DataFrame) -> dict[str, dict[str, str]]:
    """Firmas que probablemente no son personas, con la señal que delata a cada una.

    Tres señales que NO pesan igual, y por eso se devuelven por separado en vez
    de como un veredicto:

      1 y 2 son INVARIANTES. La fuente se contradice a sí misma —una posición de
      autoría mayor que el total de autores que ella misma declara, o una firma
      ocupando tres posiciones del mismo trabajo— y eso no admite lectura
      benévola.

      3 es una HEURÍSTICA sobre la forma del nombre. Aquí aísla exactamente los
      mismos casos, pero en otra institución marcaría a un autor mononímico, que
      es una persona real. Sola no basta para acusar a nadie de no existir.

    Nada de esto resuelve: alimenta una cola de revisión humana, porque declarar
    que una firma no es una persona es una decisión de identidad (`D-08`). Quien
    revise necesita saber cuál de las tres disparó, y de ahí que se conserven.
    """
    pos = pd.to_numeric(log["posicion_autor"], errors="coerce")
    tot = pd.to_numeric(log["n_autores_total"], errors="coerce")
    señales: dict[str, dict[str, str]] = {}

    def marca(nombre: str, señal: str, evidencia: str) -> None:
        señales.setdefault(nombre, {})[señal] = evidencia

    for _, r in log[pos > tot].iterrows():
        marca(r["nombre_en_fuente"], "posicion_fuera_de_rango",
              f"posición {r['posicion_autor']} de {r['n_autores_total']} autores "
              f"en {r['eid']}")

    # Nadie firma dos veces el mismo trabajo. Una cadena de afiliación repetida
    # a lo largo de la lista de autores, sí.
    for (eid, nombre), n in log.groupby(["eid", "nombre_en_fuente"]).size().items():
        if n > 1:
            marca(nombre, "firma_repetida_en_publicacion",
                  f"{n} posiciones distintas en {eid}")

    for nombre in log["nombre_en_fuente"].dropna().unique():
        if not INICIAL.search(str(nombre)):
            marca(nombre, "sin_inicial_de_nombre",
                  "el nombre no contiene ninguna inicial con punto")

    return señales


def main() -> None:
    c.banner("04 — POBLACIÓN DE AUTORES AFILIADOS")

    scopus = c.read_scopus()
    log = pd.read_csv(c.INTERNAL / "matching_log.csv", dtype=str)
    log["anio"] = log["anio"].astype(int)

    ventana = c.INSTITUTION["ventana_temporal"]
    log = log[(log["anio"] >= ventana["anio_inicio"]) & (log["anio"] <= ventana["anio_fin"])]

    # ------------------------------------------- descomposición de la brecha
    # La ventana del set de validación manual se declara en config: es una
    # propiedad del archivo Excel, no del sistema, y comparar poblaciones exige
    # igualar ventanas antes de restar.
    val = c.SOURCES["reporte_excel_2026"]["ventana_validacion"]
    v_ini, v_fin = val["anio_inicio"], val["anio_fin"]
    etiqueta_val = f"{v_ini}-{v_fin}"

    autores_full = set(log["nombre_en_fuente"])
    en_ventana_val = log[(log["anio"] >= v_ini) & (log["anio"] <= v_fin)]
    autores_2425 = set(en_ventana_val["nombre_en_fuente"])
    solo_2023 = autores_full - autores_2425

    hojas = c.SOURCES["reporte_excel_2026"]["hojas_utiles"]
    detalle = c.read_report_sheet("publicaciones_detalle")
    manual_detalle = set(detalle[hojas["publicaciones_detalle"]["columna_autor"]].dropna())
    investigadores = c.read_report_sheet("investigadores")
    manual_ranking = set(investigadores[hojas["investigadores"]["columna_autor"]].dropna())

    ventana_sistema = f"{ventana['anio_inicio']}-{ventana['anio_fin']}"
    archivo_val = Path(c.SOURCES["reporte_excel_2026"]["archivo"]).name
    fuera_de_val = ", ".join(
        str(a) for a in range(ventana["anio_inicio"], ventana["anio_fin"] + 1)
        if not (v_ini <= a <= v_fin)) or "ninguno"

    print(f"Extracción automática {ventana_sistema} : {len(autores_full)}")
    print(f"Extracción automática {etiqueta_val} : {len(autores_2425)}")
    print(f"Excel · hoja detalle  ({etiqueta_val}) : {len(manual_detalle)}")
    print(f"Excel · hoja ranking  ({etiqueta_val}) : {len(manual_ranking)}")
    print(f"\nAutores sólo en {fuera_de_val}  : {len(solo_2023)}")
    print(f"Ranking contenido en detalle     : "
          f"{len(manual_ranking - manual_detalle) == 0}")
    print(f"En detalle y no en ranking       : {len(manual_detalle - manual_ranking)}")

    gap = pd.DataFrame([
        {"poblacion": "automatica_ventana_sistema", "n": len(autores_full),
         "ventana": ventana_sistema, "fuente": "extracción reproducible"},
        {"poblacion": "automatica_ventana_validacion", "n": len(autores_2425),
         "ventana": etiqueta_val, "fuente": "extracción reproducible"},
        {"poblacion": "manual_detalle", "n": len(manual_detalle),
         "ventana": etiqueta_val, "fuente": archivo_val},
        {"poblacion": "manual_ranking", "n": len(manual_ranking),
         "ventana": etiqueta_val, "fuente": archivo_val},
        {"poblacion": "delta_fuera_de_ventana_validacion", "n": len(solo_2023),
         "ventana": fuera_de_val, "fuente": "autores exclusivos de esos años"},
        {"poblacion": "delta_automatica_vs_manual_misma_ventana",
         "n": len(autores_2425) - len(manual_detalle),
         "ventana": etiqueta_val, "fuente": "residuo tras igualar la ventana"},
        {"poblacion": "delta_detalle_vs_ranking",
         "n": len(manual_detalle) - len(manual_ranking),
         "ventana": etiqueta_val, "fuente": "deduplicación manual de variantes"},
    ])

    # -------------------------------------------- borrador de tabla maestra
    ids = scopus_id_map(scopus)
    id_by_short: dict[str, set[str]] = {}
    for full, sid in ids.items():
        parts = full.split(",")
        short = parts[0].strip()
        if len(parts) > 1:
            initials = "".join(w[0] + "." for w in parts[1].split() if w[:1].isalpha())
            short = f"{short} {initials}".strip()
        id_by_short.setdefault(short, set()).update(sid)

    rows = []
    for name, grp in log.groupby("nombre_en_fuente"):
        unidades = [u for u in grp["unidad_academica"].unique()
                    if u != c.MATCHING["unidad_academica"]["etiqueta_sin_dato"]]
        rows.append({
            "nombre_en_fuente": name,
            "clave_normalizada": c.normalize_author_key(name),
            "clave_apellido": c.surname_key(name),
            "scopus_author_ids": "|".join(sorted(id_by_short.get(name, []))) or None,
            "n_scopus_author_ids": len(id_by_short.get(name, [])),
            "orcid": None,  # placeholder declarado: no existe en las fuentes
            "n_publicaciones": grp["eid"].nunique(),
            "anio_min": int(grp["anio"].min()),
            "anio_max": int(grp["anio"].max()),
            "unidades_academicas": "|".join(sorted(unidades)) or
                                   c.MATCHING["unidad_academica"]["etiqueta_sin_dato"],
            "n_unidades_distintas": len(unidades),
            "confianza_maxima": "alta" if (grp["confianza"] == "alta").any() else "media",
            "en_ranking_manual": name in manual_ranking,
            "en_detalle_manual": name in manual_detalle,
        })
    master = pd.DataFrame(rows).sort_values("n_publicaciones", ascending=False)

    # ----------------------------------------------------- ambigüedades P-03..05
    amb = []

    for key, grp in master.groupby("clave_apellido"):
        if key and len(grp) > 1:
            for _, r in grp.iterrows():
                amb.append({
                    "tipo": "P-03_variantes_de_nombre", "severidad": "alta",
                    "clave": key, "nombre_en_fuente": r["nombre_en_fuente"],
                    "detalle": "|".join(sorted(grp["nombre_en_fuente"])),
                    "consecuencia": "posible misma persona contada varias veces",
                    "resolucion": "NO_RESOLVER_AUTOMATICAMENTE",
                })

    # P-04 se acompaña de DOS HECHOS MEDIDOS. Ninguno decide la ambigüedad —eso
    # sigue siendo juicio humano— pero los dos cambian cuánto importa y qué
    # lecturas quedan en pie:
    #
    #   en_poblacion_uft  si la firma no está en el log de matching, no tiene
    #                     ficha, no cuenta en «autores UFT distintos» y no
    #                     entraría en la red de coautoría. La ambigüedad existe
    #                     y se declara, pero no afecta a ninguna cifra
    #                     publicada. Diez de los veinte casos son de coautores
    #                     externos, y mezclarlos con los diez que sí son UFT
    #                     hacía la cola el doble de larga sin ningún efecto.
    #
    #   coocurren         si los dos identificadores figuran como coautores del
    #                     MISMO trabajo, «perfil fragmentado» queda descartado:
    #                     un perfil fragmentado es que la fuente repartió los
    #                     trabajos de una persona entre dos identificadores, y
    #                     eso no puede ocurrir dentro de una sola publicación.
    #                     Se reporta el hecho, no el veredicto: entre homonimia
    #                     y error de la fuente decide quien revisa.
    firmas_uft = set(log["nombre_en_fuente"])
    ids_por_pub = _ids_por_publicacion(scopus)
    for full, sids in ids.items():
        if len(sids) > 1:
            coocurren = sum(1 for s in ids_por_pub.values() if len(s & sids) > 1)
            amb.append({
                "tipo": "P-04_nombre_con_multiples_scopus_id", "severidad": "alta",
                "clave": full, "nombre_en_fuente": full,
                "detalle": "|".join(sorted(sids)),
                "consecuencia": "perfil Scopus fragmentado u homonimia",
                "resolucion": "NO_RESOLVER_AUTOMATICAMENTE",
                "en_poblacion_uft": _firma_corta(full) in firmas_uft,
                "coocurren_en_publicaciones": coocurren,
            })

    by_sid: dict[str, set[str]] = {}
    for full, sids in ids.items():
        for sid in sids:
            by_sid.setdefault(sid, set()).add(full)
    for sid, names in by_sid.items():
        if len(names) > 1:
            amb.append({
                "tipo": "P-05_scopus_id_con_multiples_nombres", "severidad": "media",
                "clave": sid, "nombre_en_fuente": sorted(names)[0],
                "detalle": "|".join(sorted(names)),
                "consecuencia": "variantes de firma bajo un mismo identificador",
                "resolucion": "REVISAR_NORMALIZACION_DE_NOMBRE",
            })

    for _, r in master[master["n_unidades_distintas"] > 1].iterrows():
        amb.append({
            "tipo": "I-06_autor_con_multiples_unidades", "severidad": "media",
            "clave": r["nombre_en_fuente"], "nombre_en_fuente": r["nombre_en_fuente"],
            "detalle": r["unidades_academicas"],
            "consecuencia": "afiliación interna variable entre publicaciones",
            "resolucion": "DECLARAR_NO_RESOLVER",
        })

    for name in sorted(manual_detalle - autores_2425):
        amb.append({
            "tipo": "V-manual_no_reproducido", "severidad": "alta",
            "clave": name, "nombre_en_fuente": name, "detalle": "",
            "consecuencia": "presente en el Excel manual, no reproducido por la extracción",
            "resolucion": "PENDIENTE_REVISION_HUMANA",
        })

    # ── E-09: firmas que no tienen forma de persona.
    #
    # No se eliminan aquí, y no por timidez: el descarte NO PUEDE aplicarse
    # sobre este log. `I-01` es bloqueante, exige que toda publicación tenga al
    # menos una detección institucional y se calcula justo sobre estas filas.
    # Las firmas marcadas suelen ser la única detección de su publicación, así
    # que quitarlas dejaría a esas publicaciones sin ninguna y abortaría la
    # auditoría entera. La afiliación UFT que las trajo es real; lo que no es
    # una persona es el nombre.
    #
    # El filtro vive aguas abajo, en `load_authors()`/`load_authorship()` de
    # `src/build/common_build.py`, y sólo se activa con lo que una persona haya
    # confirmado en `make revision`.
    for nombre, sig in sorted(firmas_sin_forma_de_persona(log).items()):
        eids = sorted(set(log[log["nombre_en_fuente"] == nombre]["eid"]))
        # Publicación a publicación, no sobre la unión: una firma puede ser la
        # única detección de un trabajo y compartir otro. Evaluarlo en bloque
        # dejaba el aviso en silencio en cuanto acompañara a alguien en algún
        # sitio, que es justo el caso en que hace falta.
        solas = [e for e in eids
                 if not set(log[(log["eid"] == e)
                                & (log["nombre_en_fuente"] != nombre)]["nombre_en_fuente"])]
        amb.append({
            "tipo": "E-09_firma_sin_forma_de_persona", "severidad": "alta",
            "clave": nombre, "nombre_en_fuente": nombre,
            "detalle": " · ".join(f"{k} ({v})" for k, v in sorted(sig.items()))
                       + " · publicaciones: " + ", ".join(eids),
            # Dato estructurado, no prosa. La regla E-09 contaba las
            # publicaciones afectadas buscando un literal dentro de esta misma
            # frase: reescribirla la habría puesto a cero y el reporte habría
            # publicado un «0» tranquilizador sobre el hecho que la regla existe
            # para sacar a la luz.
            "n_publicaciones_sin_otra_deteccion": len(solas),
            "consecuencia": (
                "probable fragmento de cadena de afiliación, no una persona"
                + ("" if not solas else
                   "; es la única detección UFT de "
                   + (f"{len(solas)} de sus publicaciones, que quedarían"
                      if len(solas) > 1 else
                      "la publicación en que aparece, que quedaría")
                   + " sin autoría UFT nombrada")),
            "resolucion": "NO_RESOLVER_AUTOMATICAMENTE",
        })

    amb_df = pd.DataFrame(amb)

    # Orden determinista antes de volcar: el dict de ambigüedades se ensambla
    # recorriendo diccionarios y conjuntos cuyo orden depende del hash de las
    # claves (PYTHONHASHSEED), así que sin esta pasada el archivo sale con las
    # mismas filas en distinto orden en cada corrida y ensucia el diff.
    amb_df = amb_df.sort_values(
        ["tipo", "clave", "nombre_en_fuente"], kind="stable"
    ).reset_index(drop=True)

    c.write_interim(master, "authors_master_draft.csv")
    c.write_interim(gap, "author_population_gap.csv")
    c.write_internal(amb_df, "ambiguities_authors.csv")

    print(f"\nBorrador de tabla maestra: {len(master)} autores")
    print(f"  con Scopus Author ID resuelto : {int(master['scopus_author_ids'].notna().sum())}")
    print("  con ORCID                     : 0  (no existe en las fuentes)")
    print(f"  con unidad académica          : "
          f"{int((master['unidades_academicas'] != 'No determinada').sum())}")
    print(f"  validados contra ranking manual: {int(master['en_ranking_manual'].sum())}")

    print("\nAmbigüedades encoladas por tipo:")
    print(amb_df["tipo"].value_counts().to_string())
    print("\nOK · internal/ambiguities_authors.csv, data/interim/authors_master_draft.csv")


if __name__ == "__main__":
    main()
