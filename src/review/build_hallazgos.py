"""Hallazgos sobre el CORPUS, que no son decisiones de identidad.

POR QUÉ NO VAN A `make revision`
    La herramienta de revisión responde una sola clase de pregunta: quién es
    quién. Tiene un vocabulario de veredictos, un archivo de decisiones y un
    camino de aplicación —`apply_decisions.py`— y `D-08` se apoya en que haya
    uno solo.

    Lo que emiten `orcid_openalex.py` y `openalex_cobertura.py` en estas dos
    colas es otra cosa: preguntas sobre el CORPUS. «¿Esta publicación es de la
    institución?» y «¿esta obra debería estar en el universo?» no se responden
    con «misma persona» ni «el ORCID es correcto», y **no tienen camino de
    aplicación**: cambiar el universo es una decisión de alcance, no un
    veredicto que un script aplique.

    Meterlas en la herramienta obligaría a inventar veredictos que no hacen
    nada. Un botón que no tiene efecto se pulsa igual, y entonces el registro
    de decisiones dice que algo se resolvió cuando no cambió nada.

    Por eso son un INFORME: se leen, se discuten y, si de ahí sale una acción,
    esa acción se decide aparte y se declara.

QUÉ RESUME
    · `internal/openalex_deteccion.csv`  — publicaciones que este proyecto
      atribuye a la institución y OpenAlex no. Dos lecturas, ninguna
      automática: o su desambiguación falló, o el patrón blando detectó de más.
    · `internal/openalex_cobertura.csv`  — la brecha: producción que OpenAlex
      atribuye a la institución y el universo no tiene. NUNCA entra al corpus
      (`D-206`): Scopus y OpenAlex indexan con criterios distintos.

Uso:
    python3 src/review/build_hallazgos.py

Salida:
    internal/hallazgos_corpus.md    (capa interna)
"""

from __future__ import annotations

import sys
from collections import Counter
from datetime import date
from pathlib import Path

import pandas as pd

if sys.platform == "win32":
    # La consola de Windows usa cp1252 por defecto: revienta cualquier print()
    # con caracteres como "→"/"✗"/"⚠". Mismo patrón que src/enrich/orcid_openalex.py.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[2]
INTERNAL = ROOT / "internal"

# Cuántos casos se listan por grupo antes de resumir el resto. La brecha puede
# traer miles de filas: una lista de miles no se lee, y una que se corta sin
# decir cuánto queda miente por omisión.
MAX_LISTA = 25


def leer(nombre: str) -> pd.DataFrame | None:
    p = INTERNAL / nombre
    return pd.read_csv(p, dtype=str) if p.exists() else None


def bloque_deteccion(df: pd.DataFrame | None) -> list[str]:
    if df is None:
        return ["## Detección institucional discrepante", "",
                "_Sin datos: `orcid_openalex.py` no se ha ejecutado, o no encontró "
                "ninguna discrepancia._", ""]
    L = ["## Detección institucional discrepante", "",
         f"**{len(df)} publicaciones** que este proyecto atribuye a la institución y "
         "OpenAlex no.", "",
         "Dos lecturas, y decidir cuál exige mirar la publicación:", "",
         "- **La desambiguación de OpenAlex falló.** Habitual cuando la afiliación "
         "viene truncada o escrita de forma poco canónica.",
         "- **El patrón blando de este proyecto detectó de más.** Ésta es la que "
         "importa: sería un falso positivo en el universo, y la regla `I-05` existe "
         "porque el matching laxo ya produjo 16 verificados.", ""]
    sin_ror = (df["rors_en_openalex"] == "(ninguno)").sum() if "rors_en_openalex" in df else 0
    L += [f"De las {len(df)}, **{sin_ror}** no traen ninguna institución en OpenAlex "
          "—ahí el silencio no dice nada— y "
          f"**{len(df) - sin_ror}** sí traen otra, que es donde conviene mirar.", ""]
    otras = df[df["rors_en_openalex"] != "(ninguno)"] if "rors_en_openalex" in df else df
    if len(otras):
        L += ["| EID | Instituciones que sí atribuye OpenAlex |", "|---|---|"]
        for _, r in otras.head(MAX_LISTA).iterrows():
            L.append(f"| `{r['eid']}` | {r['rors_en_openalex']} |")
        if len(otras) > MAX_LISTA:
            L.append(f"| … | y {len(otras) - MAX_LISTA} más en el CSV |")
        L.append("")
    return L


def bloque_cobertura(df: pd.DataFrame | None) -> list[str]:
    if df is None:
        return ["## La brecha de cobertura", "",
                "_Sin datos: `openalex_cobertura.py` no se ha ejecutado, o no encontró "
                "ninguna obra fuera del universo._", ""]
    L = ["## La brecha de cobertura", "",
         f"**{len(df)} obras** que OpenAlex atribuye a la institución y el universo no "
         "tiene.", "",
         "> **Nada de esto entra al corpus.** Scopus y OpenAlex indexan con criterios "
         "distintos y sumarlos produce una cifra que nadie puede reconciliar "
         "(`D-206`). Si alguna vez entrara, entraría como corpus paralelo declarado, "
         "con su propia entrada en `config/sources.yml` y su propio denominador.", ""]
    if "motivo" in df:
        L += ["| Motivo | Obras |", "|---|---:|"]
        for m, n in Counter(df["motivo"]).most_common():
            L.append(f"| {m} | {n} |")
        L.append("")
    # Lo que de verdad mide la brecha son las que TIENEN DOI y están en ventana:
    # de las otras no se puede afirmar que falten.
    reales = df[df["motivo"].str.startswith("con DOI")] if "motivo" in df else df
    L += [f"### Las {len(reales)} que sí miden la brecha", "",
          "Con DOI y dentro de la ventana: de éstas sí se puede afirmar que el "
          "universo no las tiene.", ""]
    if len(reales):
        if "anio" in reales:
            por_anio = ", ".join(f"{a}: {n}" for a, n in
                                 sorted(Counter(reales["anio"].dropna()).items()))
            L += [f"**Por año** — {por_anio}", ""]
        if "tipo" in reales:
            por_tipo = ", ".join(f"{t}: {n}" for t, n in
                                 Counter(reales["tipo"].dropna()).most_common(8))
            L += [f"**Por tipo documental** — {por_tipo}", ""]
        L += ["| Año | Título | DOI |", "|---|---|---|"]
        for _, r in reales.head(MAX_LISTA).iterrows():
            t = str(r.get("titulo") or "")[:80]
            L.append(f"| {r.get('anio') or '—'} | {t} | <https://doi.org/{r['doi']}> |")
        if len(reales) > MAX_LISTA:
            L.append(f"| … | y {len(reales) - MAX_LISTA} más en el CSV | |")
        L.append("")
    return L


def main() -> int:
    det = leer("openalex_deteccion.csv")
    cob = leer("openalex_cobertura.csv")

    if det is None and cob is None:
        print("  Ninguna de las dos colas existe todavía.")
        print("  Se generan con:  make openalex   y   make cobertura")
        print("  No se escribe nada.")
        return 0

    L = ["# Hallazgos sobre el corpus", "",
         f"**Generado** el {date.today().isoformat()} por "
         "`src/review/build_hallazgos.py`. Regenerable.", "",
         "Esto **no es la cola de revisión de identidad**. Aquí no hay veredictos "
         "que aplicar: son preguntas sobre el corpus —qué publicaciones son de la "
         "institución y cuáles faltan— y responderlas cambia el alcance del "
         "informe, que es una decisión y no un botón.", "",
         "> **Capa interna.** Nombra publicaciones concretas. No se publica.", "",
         "---", ""]
    L += bloque_deteccion(det)
    L += ["---", ""]
    L += bloque_cobertura(cob)

    salida = INTERNAL / "hallazgos_corpus.md"
    salida.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"  detección discrepante : {len(det) if det is not None else '(sin datos)'}")
    print(f"  brecha de cobertura   : {len(cob) if cob is not None else '(sin datos)'}")
    print(f"\n  OK · {salida.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
