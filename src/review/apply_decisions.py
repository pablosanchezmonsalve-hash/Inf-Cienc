"""Aplica las decisiones humanas exportadas por la herramienta de revisión.

QUÉ HACE
    Lee `internal/identity_decisions.csv` —lo que una persona decidió en
    `make revision`— y lo convierte en dos artefactos que el pipeline sí sabe
    consumir:

      config/identidades_consolidadas.yml   variantes declaradas la misma persona
      data/enriched/authors_orcid.csv       asignaciones que la revisión confirma

QUÉ NO HACE
    No decide nada. Todo lo que escribe procede de un veredicto explícito; lo
    que quedó `pendiente` sigue pendiente y no se toca.

    No aplica un conjunto de decisiones incoherente. Si alguien declaró A~B y
    B~C la misma persona y a la vez A~C personas distintas, el script se
    detiene: aplicar una contradicción es peor que no aplicar nada, porque deja
    el resultado sin significado y sin aviso.

POR QUÉ LOS CANDIDATOS POR AFILIACIÓN SÍ PUEDEN PUBLICARSE AHORA
    Nacían sin publicación compartida que los anclara, y por eso el conector
    los dejó en la capa interna. Lo que faltaba era el juicio de una persona, y
    es exactamente lo que aporta este archivo. La asignación pasa a existir con
    la fuente que la sostiene declarada: revisión humana, no heurística.

USO
    python3 src/review/apply_decisions.py --test    # lógica, sin tocar nada
    python3 src/review/apply_decisions.py --dry-run # qué haría
    python3 src/review/apply_decisions.py
"""

from __future__ import annotations

import argparse
import itertools
import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
INTERNAL = ROOT / "internal"
ENRICHED = ROOT / "data" / "enriched"
CONFIG = ROOT / "config"

FUENTE_REVISION = "Revisión humana (candidato por afiliación confirmado)"


def leer_decisiones(path: Path) -> pd.DataFrame:
    d = pd.read_csv(path, comment="#", dtype=str).fillna("")
    faltan = {"caso_id", "cola", "firmas", "veredicto"} - set(d.columns)
    if faltan:
        sys.exit(f"El CSV no tiene las columnas esperadas: faltan {sorted(faltan)}")
    return d


def firmas_de(fila) -> list[str]:
    return [x.strip() for x in str(fila["firmas"]).split("|") if x.strip()]


def grupos_de_identidad(d: pd.DataFrame) -> tuple[list[list[str]], list[tuple]]:
    """Une por transitividad las firmas declaradas la misma persona.

    Devuelve también las contradicciones: pares declarados «distintas» que la
    cadena de «misma» ya había unido. No se resuelven aquí porque no hay forma
    de saber cuál de las dos afirmaciones cede.
    """
    padre: dict[str, str] = {}

    def find(x: str) -> str:
        padre.setdefault(x, x)
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    for _, r in d[d.veredicto == "misma"].iterrows():
        fs = firmas_de(r)
        for a, b in itertools.pairwise(fs):
            padre[find(a)] = find(b)

    conflictos = []
    for _, r in d[d.veredicto == "distintas"].iterrows():
        fs = firmas_de(r)
        for a, b in itertools.combinations(fs, 2):
            if a in padre and b in padre and find(a) == find(b):
                conflictos.append((r["caso_id"], a, b))

    agrup: dict[str, list[str]] = {}
    for f in padre:
        agrup.setdefault(find(f), []).append(f)
    return [sorted(v) for v in agrup.values() if len(v) > 1], conflictos


def _tildes_apellido(firma: str) -> int:
    """Diacríticos del APELLIDO, ignorando las iniciales.

    La distinción no es cosmética. Que un apellido pierda la tilde es un
    artefacto conocido de estas exportaciones —en este mismo corpus apareció
    «Ingenierı́a» con una i sin punto y un acento suelto—, y restituirla no
    inventa nada: nadie escribe «Núñez» por error donde la fuente dice
    «Núnez».

    Con las INICIALES no vale el mismo razonamiento. Si una firma aparece como
    «Arenas-Massa Á.» y otra como «Arenas-Massa A.», elegir la acentuada
    afirmaría que el nombre de pila lleva tilde, y eso no se deduce de aquí.
    Por eso sólo cuentan los tokens de más de una letra.
    """
    import unicodedata
    palabras = [t for t in firma.replace(".", " ").replace("-", " ").split()
                if len(t) > 1]
    return sum(1 for t in palabras
               for ch in unicodedata.normalize("NFD", t)
               if unicodedata.category(ch) == "Mn")


def canonica(firmas: list[str], frec: dict[str, int] | None = None) -> str:
    """La forma que mejor representa a la persona en la fuente.

    No se inventa un nombre nuevo: se elige una de las formas que Scopus ya
    contiene, para que lo publicado se pueda rastrear hasta allí.

    El criterio es empírico a propósito. Ordenar por longitud parecía razonable
    —«Castillo Valenzuela O.» dice más que «Castillo O.»— pero a igualdad de
    longitud desempataba alfabéticamente, y en español eso elige la variante
    SIN tilde: publicaba «Diaz F.» teniendo «Díaz F.», y «Castro-Sepulveda M.»
    teniendo «Castro-Sepúlveda M.». Un criterio ortográfico habría exigido
    adivinar si «Arenas-Massa Á.» o «Arenas-Massa A.» es la inicial correcta, y
    eso no se adivina.

    Contar publicaciones no adivina nada: la forma dominante en la fuente es la
    más representativa de esa persona. Se paga que a veces gane la forma más
    corta —«Giglio A.» con 21 publicaciones frente a «Giglio Jiménez A.» con
    2—; a cambio, lo que se publica es lo que la fuente dice.

    Pero la frecuencia sola tampoco bastaba: en los empates el desempate
    alfabético seguía eligiendo la variante sin tilde, y habría publicado
    «Núnez-Lisboa M.» teniendo «Núñez-Lisboa M.». Eso no es una variante de
    firma, es un apellido corrupto. Por eso el primer criterio son los
    diacríticos DEL APELLIDO (ver `_tildes_apellido`), y la frecuencia decide
    a partir de ahí.
    """
    frec = frec or {}
    return sorted(firmas, key=lambda s: (-_tildes_apellido(s), -frec.get(s, 0),
                                         -len(s), s))[0]


def asignaciones_confirmadas(d: pd.DataFrame, cand: pd.DataFrame | None) -> pd.DataFrame:
    """Candidatos por afiliación que la revisión confirmó como la misma persona."""
    cols = ["nombre_en_fuente", "orcid", "publicaciones_de_respaldo", "confianza", "fuente"]
    if cand is None:
        return pd.DataFrame(columns=cols)

    por_firma = {r["nombre_en_fuente"]: r["orcid"] for _, r in cand.iterrows()}
    filas = []
    for _, r in d[(d.veredicto == "misma") & (d.cola.str.startswith("Candidato por afiliación"))].iterrows():
        for f in firmas_de(r):
            if f in por_firma:
                filas.append({"nombre_en_fuente": f, "orcid": por_firma[f],
                              "publicaciones_de_respaldo": 0,
                              # La confianza no la da el recuento de
                              # publicaciones —aquí no hay ninguna que respalde—
                              # sino que una persona lo comprobó.
                              "confianza": "alta", "fuente": FUENTE_REVISION})

    # Los casos «Mismo ORCID por afiliación» agrupan varias firmas bajo un
    # titular: confirmarlos asigna ese ORCID a TODAS las firmas del grupo.
    for _, r in d[(d.veredicto == "misma") & (d.cola == "Mismo ORCID por afiliación")].iterrows():
        for f in firmas_de(r):
            if f in por_firma:
                filas.append({"nombre_en_fuente": f, "orcid": por_firma[f],
                              "publicaciones_de_respaldo": 0,
                              "confianza": "alta", "fuente": FUENTE_REVISION})

    return pd.DataFrame(filas, columns=cols).drop_duplicates("nombre_en_fuente")


def frecuencias(path: Path) -> dict[str, int]:
    """Publicaciones distintas por forma de firma, para elegir la canónica."""
    if not path.exists():
        return {}
    log = pd.read_csv(path, dtype=str)
    return log.groupby("nombre_en_fuente")["eid"].nunique().to_dict()


def descartadas(d: pd.DataFrame) -> list[tuple[str, str]]:
    """Firmas que la revisión declaró que no son personas, con su nota.

    Devuelve la firma y lo que quien revisó escribió al decidirlo. La nota
    importa: dentro de un año, «no es una persona» sin más no permite saber si
    alguien lo comprobó contra la fuente o lo dio por evidente.
    """
    filas = []
    for _, r in d[d.veredicto == "no_es_persona"].iterrows():
        for f in firmas_de(r):
            filas.append((f, str(r.get("nota") or "").strip()))
    return sorted(set(filas))


def yaml_descartadas(firmas: list[tuple[str, str]], fecha: str) -> str:
    """Escrito a mano, por lo mismo que `yaml_consolidacion`: se lee tanto como
    se ejecuta, y un volcado automático perdería el porqué."""
    lineas = [
        "# Firmas que la revisión humana declaró que NO son personas.",
        "#",
        "# GENERADO por src/review/apply_decisions.py desde",
        "# internal/identity_decisions.csv. No editar a mano: se regenera.",
        "#",
        "# QUÉ AUTORIZA",
        "#   Que estas formas de firma dejen de contarse como autores y dejen de",
        "#   tener ficha. Son fragmentos de cadena de afiliación que entraron en",
        "#   la lista de autores de la fuente («School of Psychology», «and",
        "#   Senior Lecturer»), detectados por la regla E-09.",
        "#",
        "# QUÉ NO AUTORIZA",
        "#   Tocar internal/matching_log.csv. La detección institucional que las",
        "#   trajo es REAL: la publicación sí es de la UFT, lo que no es una",
        "#   persona es el nombre. Borrarlas del log dejaría a esas publicaciones",
        "#   sin ninguna detección y haría fallar la regla bloqueante I-01.",
        "#   El descarte se aplica aguas abajo, en src/build/common_build.py.",
        "#",
        "# CONSECUENCIA DECLARADA",
        "#   Las publicaciones donde eran la única detección UFT quedan sin",
        "#   autoría UFT nombrada. Eso se declara; no se rellena con nada.",
        "#",
        f"# Firmas descartadas: {len(firmas)}",
        f"# Fecha de la revisión: {fecha}",
        "",
        "firmas:",
    ]
    for f, nota in firmas:
        lineas.append(f"  - firma: {f!r}")
        if nota:
            lineas.append(f"    nota: {nota!r}")
    return "\n".join(lineas) + "\n"


def yaml_consolidacion(grupos: list[list[str]], fecha: str, n_dec: int,
                       frec: dict[str, int]) -> str:
    """Escribe el mapa a mano en vez de volcarlo con yaml.dump.

    Un volcado automático perdería los comentarios, y este archivo se lee tanto
    como se ejecuta: quien lo abra tiene que entender de dónde salió y qué
    autoriza sin ir a buscar otro documento.
    """
    lineas = [
        "# Identidades consolidadas por revisión humana.",
        "#",
        "# GENERADO por src/review/apply_decisions.py desde",
        "# internal/identity_decisions.csv. No editar a mano: se regenera.",
        "#",
        "# QUÉ AUTORIZA",
        "#   Que las formas de firma de cada grupo se traten como UNA persona en",
        "#   los indicadores y en las fichas. Es la única vía por la que dos",
        "#   variantes se fusionan: el pipeline nunca lo hace por heurística",
        "#   (decisión D-08).",
        "#",
        "# LA FORMA CANÓNICA no es un nombre nuevo: es la que la fuente usa más,",
        "# medida en publicaciones distintas. Entre paréntesis, ese recuento.",
        "# Se elige así y no por longitud porque el desempate alfabético",
        "# publicaba la variante sin tilde teniendo la variante con tilde.",
        "#",
        f"# Decisiones leídas: {n_dec} · grupos consolidados: {len(grupos)}",
        f"# Fecha de la revisión: {fecha}",
        "",
        "grupos:",
    ]
    for g in sorted(grupos, key=lambda x: canonica(x, frec)):
        lineas.append(f"  - canonica: {canonica(g, frec)!r}")
        lineas.append("    variantes:")
        for v in g:
            lineas.append(f"      - {v!r}   # {frec.get(v, 0)} publicaciones")
    return "\n".join(lineas) + "\n"


# --------------------------------------------------------------------------- #

def autotest() -> int:
    casos = []

    def df(filas):
        return pd.DataFrame(filas, columns=["caso_id", "cola", "firmas", "veredicto"])

    # 1. Transitividad: A~B y B~C dan un grupo de tres.
    g, c = grupos_de_identidad(df([
        ("x", "Variantes de nombre", "A | B", "misma"),
        ("y", "Variantes de nombre", "B | C", "misma")]))
    casos.append(("transitividad une A-B-C", g == [["A", "B", "C"]] and not c, g))

    # 2. Lo pendiente no une nada.
    g, _ = grupos_de_identidad(df([("x", "V", "A | B", "pendiente")]))
    casos.append(("pendiente no une", g == [], g))

    # 3. «distintas» que contradice una cadena de «misma» se detecta.
    g, c = grupos_de_identidad(df([
        ("x", "V", "A | B", "misma"), ("y", "V", "B | C", "misma"),
        ("z", "V", "A | C", "distintas")]))
    casos.append(("contradicción detectada", len(c) == 1, c))

    # 4. «distintas» sin cadena previa no es contradicción.
    g, c = grupos_de_identidad(df([("z", "V", "A | C", "distintas")]))
    casos.append(("distintas sola no contradice", not c and g == [], (g, c)))

    # 5. La canónica es la forma más informativa, no una inventada.
    casos.append(("canónica = la forma más frecuente en la fuente",
                  canonica(["Diaz F.", "Díaz F."], {"Diaz F.": 7, "Díaz F.": 14}) == "Díaz F.", None))
    # El apellido corrupto no gana aunque empate en frecuencia.
    casos.append(("la tilde del apellido vence al empate",
                  canonica(["Núnez-Lisboa M.", "Núñez-Lisboa M."],
                           {"Núnez-Lisboa M.": 1, "Núñez-Lisboa M.": 1}) == "Núñez-Lisboa M.", None))
    # Ni siquiera perdiendo en frecuencia: «Sepulveda» sigue siendo un apellido
    # al que la exportación le quitó la tilde.
    casos.append(("la tilde del apellido vence a la frecuencia",
                  canonica(["Castro-Sepulveda M.", "Castro-Sepúlveda M."],
                           {"Castro-Sepulveda M.": 8, "Castro-Sepúlveda M.": 7})
                  == "Castro-Sepúlveda M.", None))
    # Con las INICIALES no se aplica: ahí manda la frecuencia.
    casos.append(("la tilde de la inicial NO decide",
                  canonica(["Arenas-Massa A.", "Arenas-Massa Á."],
                           {"Arenas-Massa A.": 9, "Arenas-Massa Á.": 1}) == "Arenas-Massa A.", None))
    casos.append(("sin frecuencias cae en la más larga",
                  canonica(["Castro M.", "Castro-Sepúlveda M."]) == "Castro-Sepúlveda M.", None))
    casos.append(("canónica es determinista",
                  canonica(["B.", "A."]) == canonica(["A.", "B."]), None))


    # 6. Sólo se asignan ORCID de candidatos realmente confirmados.
    cand = pd.DataFrame([{"nombre_en_fuente": "López V.", "orcid": "0000-X"},
                         {"nombre_en_fuente": "Otro Q.", "orcid": "0000-Y"}])
    a = asignaciones_confirmadas(df([
        ("afil-López V.", "Candidato por afiliación", "López V.", "misma"),
        ("afil-Otro Q.", "Candidato por afiliación", "Otro Q.", "pendiente")]), cand)
    casos.append(("sólo lo confirmado se asigna",
                  list(a.nombre_en_fuente) == ["López V."], a.to_dict("records")))
    casos.append(("la fuente declara que fue revisión humana",
                  a.fuente.iloc[0] == FUENTE_REVISION, None))

    # 7. Sin archivo de candidatos no revienta.
    casos.append(("sin candidatos devuelve vacío",
                  len(asignaciones_confirmadas(df([]), None)) == 0, None))

    # 8. Una firma que no está entre los candidatos no se inventa.
    a = asignaciones_confirmadas(df([
        ("afil-Fantasma Z.", "Candidato por afiliación", "Fantasma Z.", "misma")]), cand)
    casos.append(("firma ausente de los candidatos no se asigna", len(a) == 0, None))

    # 9. Sólo se descarta lo que una persona declaró que no es una persona.
    d9 = df([("e09-School of Psychology", "Firma sin forma de persona",
              "School of Psychology", "no_es_persona"),
             ("e09-Metabolism", "Firma sin forma de persona", "Metabolism", "pendiente"),
             ("e09-Gómez P.", "Firma sin forma de persona", "Gómez P.", "es_persona")])
    casos.append(("sólo no_es_persona descarta",
                  [f for f, _ in descartadas(d9)] == ["School of Psychology"],
                  descartadas(d9)))

    # 10. «es_persona» conserva la firma: decir que no es un fragmento no puede
    #     tener el mismo efecto que decir que lo es.
    casos.append(("es_persona no descarta",
                  "Gómez P." not in {f for f, _ in descartadas(d9)}, None))

    # 11. Descartar una firma NO la mete en ningún grupo de identidad: son dos
    #     preguntas distintas y el veredicto de una no puede responder la otra.
    g, c = grupos_de_identidad(d9)
    casos.append(("descartar no consolida", g == [] and not c, (g, c)))

    ok = True
    for nombre, paso, obs in casos:
        print(f"  {'OK  ' if paso else 'FALLA'} {nombre}" + (f"   {obs}" if not paso else ""))
        ok &= paso
    print("\n" + ("TODOS LOS CASOS OK" if ok else "HAY CASOS FALLANDO"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--test", action="store_true", help="verifica la lógica sin tocar nada")
    ap.add_argument("--dry-run", action="store_true", help="muestra qué haría, sin escribir")
    args = ap.parse_args()

    print("=" * 78)
    print("APLICAR LAS DECISIONES DE LA REVISIÓN HUMANA")
    print("=" * 78)
    if args.test:
        return autotest()

    path = INTERNAL / "identity_decisions.csv"
    if not path.exists():
        sys.exit(f"Falta {path.relative_to(ROOT)}.\n"
                 "Se exporta desde internal/revision_identidad.html "
                 "(se genera con `make revision`).")

    d = leer_decisiones(path)
    resueltas = d[d.veredicto.isin(["misma", "distintas", "no_es_persona", "es_persona"])]
    print(f"  decisiones leídas   : {len(d)}")
    print(f"    resueltas         : {len(resueltas)}")
    print(f"    pendientes        : {int((d.veredicto == 'pendiente').sum())}")

    grupos, conflictos = grupos_de_identidad(d)
    if conflictos:
        print("\n  CONTRADICCIONES:")
        for cid, a, b in conflictos:
            print(f"    {cid}: «{a}» y «{b}» se declaran distintas, pero otra "
                  "decisión las une")
        sys.exit("\nNo se aplica nada. Resuelva la contradicción y vuelva a exportar.")

    firmas_fusionadas = sum(len(g) for g in grupos)
    print(f"\n  grupos consolidados : {len(grupos)}  "
          f"({firmas_fusionadas} formas de firma)")

    # Una firma no puede a la vez fusionarse con una persona y no ser una
    # persona. Si ocurre, alguien decidió dos cosas incompatibles y aplicar
    # cualquiera de las dos publicaría un resultado que nadie decidió.
    desc = descartadas(d)
    en_grupos = {f for g in grupos for f in g}
    choque = sorted({f for f, _ in desc} & en_grupos)
    if choque:
        print("\n  CONTRADICCIONES:")
        for f in choque:
            print(f"    «{f}» se declara «no es una persona» y a la vez se fusiona "
                  "con otra firma como la misma persona")
        sys.exit("\nNo se aplica nada. Resuelva la contradicción y vuelva a exportar.")
    print(f"  firmas descartadas  : {len(desc)} (no son personas)")

    cpath = INTERNAL / "orcid_candidatos_afiliacion.csv"
    cand = pd.read_csv(cpath, dtype=str) if cpath.exists() else None
    nuevas = asignaciones_confirmadas(d, cand)

    opath = ENRICHED / "authors_orcid.csv"
    vig = pd.read_csv(opath, dtype=str)
    nuevas = nuevas[~nuevas.nombre_en_fuente.isin(set(vig.nombre_en_fuente))]
    print(f"  ORCID confirmados   : {len(nuevas)} asignaciones nuevas")
    print(f"  cobertura           : {len(vig)} → {len(vig) + len(nuevas)}")

    if args.dry_run:
        print("\n  --dry-run: no se ha escrito nada.")
        return 0

    frec = frecuencias(INTERNAL / "matching_log.csv")
    hoy = date.today().isoformat()
    (CONFIG / "identidades_consolidadas.yml").write_text(
        yaml_consolidacion(grupos, hoy, len(d), frec), encoding="utf-8")
    (CONFIG / "firmas_descartadas.yml").write_text(
        yaml_descartadas(desc, hoy), encoding="utf-8")

    if len(nuevas):
        salida = pd.concat([vig, nuevas], ignore_index=True)
        salida = salida.sort_values("nombre_en_fuente", kind="stable")
        salida.to_csv(opath, index=False, encoding="utf-8")

    print(f"\n  OK · config/identidades_consolidadas.yml")
    print(f"       config/firmas_descartadas.yml     ({len(desc)} firmas)")
    if len(nuevas):
        print(f"       data/enriched/authors_orcid.csv  (+{len(nuevas)})")
    print("\n  Reconstruya el sitio para que surta efecto:  make sitio")
    return 0


if __name__ == "__main__":
    sys.exit(main())
