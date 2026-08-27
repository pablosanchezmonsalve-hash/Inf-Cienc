"""Grafo de coautoría interna (C-05), derivado de los pares autor x publicación.

QUÉ CONSTRUYE
    Un nodo por persona UFT y una arista entre dos personas que firman una
    misma publicación. Sobre eso, dos particiones que NO son lo mismo:

      componente   hecho objetivo del grafo. Dos personas están en la misma
                   componente si existe un camino de coautorías entre ellas.
                   No tiene parámetros, no tiene aleatoriedad y no admite
                   discusión: o hay camino o no lo hay.

      comunidad    resultado de un ALGORITMO con supuestos (Louvain, que
                   maximiza modularidad de forma voraz). Otra ejecución con
                   otro orden, u otro algoritmo, puede dar otra partición. Se
                   publica como lo que es.

    La distinción no es pedantería: presentar una comunidad detectada como si
    fuera un grupo de investigación existente convierte una hipótesis en un
    hecho, que es justo lo que este proyecto no hace.

POR QUÉ ESTE ARTEFACTO SIGUE SIENDO INTERNO, AUNQUE C-05 YA SE PUBLICÓ
    C-05 se publicó el 2026-08-26 (T-10, config/indicators.yml). Pero el JSON
    que este módulo escribe en data/interim/ —el grafo completo, sin filtrar,
    de una sola vez— sigue sin copiarse a dist/: es el artefacto de revisión
    (`make red`), no lo que ve el público. Lo que SÍ llega a dist/ es distinto:
    un resumen agregado en series.json (02_indicators.py, mismas funciones de
    aquí) y el recorte que recalcula en vivo, en el navegador,
    `web/assets/js/grafo.js` — un puerto de este mismo archivo, verificado
    línea a línea para que las dos superficies no puedan divergir.

QUÉ SE EXCLUYE, Y POR QUÉ IMPORTA MÁS AQUÍ QUE EN OTROS INDICADORES
    Las firmas marcadas por E-09 —«School of Psychology», «and Senior
    Lecturer», «Metabolism», «Movement Sciences (NUTRIM)»— son fragmentos de
    cadena de afiliación, no personas. En un recuento inflan un total; en un
    grafo son mucho peor: un fragmento presente en una publicación con seis
    autores UFT genera seis aristas hacia una persona que no existe, y esas
    aristas se leen como colaboración.

LA LIMITACIÓN DE FONDO, QUE NINGÚN ALGORITMO ARREGLA
    Una publicación con n autores UFT produce un clique de n(n-1)/2 aristas,
    así que un solo trabajo muy multiautoral pesa más que decenas de
    colaboraciones reales de dos personas. Por eso cada arista lleva DOS pesos:
    el recuento de publicaciones compartidas y el peso fraccional de Newman
    (cada publicación reparte 1/(n-1) entre sus pares), que es el que corrige
    esa inflación. Se guardan los dos porque responden preguntas distintas.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict, deque
from itertools import combinations
from pathlib import Path
if sys.platform == "win32":
    # La consola de Windows usa cp1252 por defecto: revienta cualquier print()
    # con caracteres como "→"/"—"/"·". Mismo patrón que src/enrich/orcid_openalex.py.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# common_build se importa DENTRO de main() a propósito. Las funciones de este
# módulo son puras —reciben pares y devuelven estructuras— y el análisis de
# viabilidad necesita las mismas para no calcular el grafo por segunda vez con
# otra implementación. Importar la capa de build aquí arriba obligaría a cargar
# la configuración entera sólo para contar aristas, y ya hubo una divergencia
# real por tener dos cuentas: 818 publicaciones aquí y 814 allá, porque una de
# las dos no excluía las firmas E-09.


# --------------------------------------------------------------- construcción

def construir(autoria, excluir: set[str] | None = None,
              unidades: dict[str, str] | None = None) -> dict:
    """Pares (persona, publicación) -> nodos y aristas.

    `autoria` es cualquier iterable de pares. Se deduplica antes de nada: una
    firma que aparece dos veces en la misma publicación no coautora consigo
    misma, y en el log hay un caso real de eso.
    """
    excluir = excluir or set()
    pares = {(p, e) for p, e in autoria if p not in excluir}

    por_pub: dict[str, set[str]] = defaultdict(set)
    for persona, eid in pares:
        por_pub[eid].add(persona)

    pubs_por_persona: dict[str, int] = defaultdict(int)
    for persona, _ in pares:
        pubs_por_persona[persona] += 1

    peso: dict[tuple[str, str], int] = defaultdict(int)
    fraccional: dict[tuple[str, str], float] = defaultdict(float)
    for eid in sorted(por_pub):
        gente = sorted(por_pub[eid])
        if len(gente) < 2:
            continue
        cuota = 1.0 / (len(gente) - 1)
        for a, c in combinations(gente, 2):
            peso[(a, c)] += 1
            fraccional[(a, c)] += cuota

    aristas = [{"a": a, "b": c, "peso": peso[(a, c)],
                "peso_fraccional": round(fraccional[(a, c)], 4)}
               for a, c in sorted(peso)]
    nodos = sorted({p for p, _ in pares})
    return {"nodos": nodos, "aristas": aristas,
            "unidades": {n: (unidades or {}).get(n, "No determinada") for n in nodos},
            "publicaciones_por_persona": dict(sorted(pubs_por_persona.items())),
            "publicaciones": len(por_pub),
            "publicaciones_con_dos_o_mas": sum(1 for g in por_pub.values() if len(g) > 1)}


# ------------------------------------------------------------- particiones

def componentes(nodos: list[str], aristas: list[dict]) -> dict[str, int]:
    """Componentes conexas por recorrido en anchura. Determinista y sin supuestos.

    El índice se asigna por orden de tamaño descendente y, a igual tamaño, por
    el primer nombre: así el número de componente no cambia entre corridas si
    los datos no cambian.
    """
    vecinos: dict[str, set[str]] = defaultdict(set)
    for e in aristas:
        vecinos[e["a"]].add(e["b"])
        vecinos[e["b"]].add(e["a"])

    vistos: set[str] = set()
    grupos: list[list[str]] = []
    for raiz in nodos:
        if raiz in vistos:
            continue
        cola, grupo = deque([raiz]), []
        vistos.add(raiz)
        while cola:
            x = cola.popleft()
            grupo.append(x)
            for y in sorted(vecinos[x]):
                if y not in vistos:
                    vistos.add(y)
                    cola.append(y)
        grupos.append(sorted(grupo))

    grupos.sort(key=lambda g: (-len(g), g[0]))
    return {n: i for i, g in enumerate(grupos) for n in g}


def _modularidad(comunidad: dict[str, int], vecinos: dict[str, dict[str, float]],
                 grados: dict[str, float], m2: float) -> float:
    if m2 == 0:
        return 0.0
    dentro: dict[int, float] = defaultdict(float)
    total: dict[int, float] = defaultdict(float)
    for n, com in comunidad.items():
        total[com] += grados[n]
        for v, w in vecinos[n].items():
            if comunidad[v] == com:
                dentro[com] += w
    return sum(dentro[c] / m2 - (total[c] / m2) ** 2 for c in total)


def comunidades(nodos: list[str], aristas: list[dict],
                clave_peso: str = "peso_fraccional") -> dict[str, int]:
    """Louvain, en su variante determinista.

    El Louvain habitual recorre los nodos en orden aleatorio, y por eso dos
    corridas sobre los mismos datos dan particiones distintas. Aquí el orden es
    alfabético y los empates se rompen por el identificador de la comunidad, de
    modo que el resultado es reproducible. Sigue siendo una heurística voraz:
    reproducible no quiere decir correcta.

    Se pondera por defecto con el peso FRACCIONAL, no con el recuento: si no,
    una publicación con quince autores UFT forma un bloque tan denso que el
    algoritmo lo declara comunidad por sí solo, y lo único que habría detectado
    es que ese trabajo existe.
    """
    vecinos: dict[str, dict[str, float]] = {n: {} for n in nodos}
    for e in aristas:
        w = float(e[clave_peso])
        vecinos[e["a"]][e["b"]] = vecinos[e["a"]].get(e["b"], 0.0) + w
        vecinos[e["b"]][e["a"]] = vecinos[e["b"]].get(e["a"], 0.0) + w

    grados = {n: sum(vs.values()) for n, vs in vecinos.items()}
    m2 = sum(grados.values())
    if m2 == 0:
        return {n: i for i, n in enumerate(nodos)}

    comunidad = {n: i for i, n in enumerate(sorted(nodos))}
    total = {i: grados[n] for n, i in comunidad.items()}

    for _ in range(100):                      # tope de seguridad, no un ajuste
        movido = False
        for n in sorted(nodos):
            propia = comunidad[n]
            total[propia] -= grados[n]
            hacia: dict[int, float] = defaultdict(float)
            for v, w in vecinos[n].items():
                hacia[comunidad[v]] += w
            mejor, mejor_gan = propia, hacia.get(propia, 0.0) - total[propia] * grados[n] / m2
            for com in sorted(hacia):
                gan = hacia[com] - total[com] * grados[n] / m2
                if gan > mejor_gan + 1e-12:
                    mejor, mejor_gan = com, gan
            total[mejor] += grados[n]
            if mejor != propia:
                comunidad[n] = mejor
                movido = True
        if not movido:
            break

    # Renumerado estable: por tamaño y, a igual tamaño, por el primer nombre.
    grupos: dict[int, list[str]] = defaultdict(list)
    for n, com in comunidad.items():
        grupos[com].append(n)
    orden = sorted(grupos.values(), key=lambda g: (-len(g), sorted(g)[0]))
    return {n: i for i, g in enumerate(orden) for n in g}


# --------------------------------------------------------------------- salida

def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import common_build as b

    autoria = b.load_authorship()
    fragmentos = b.firmas_e09_encoladas()
    # La unidad se toma de la primera declarada por la persona. Una persona con
    # dos unidades es una ambigüedad aparte (I-06) y no se resuelve aquí; el
    # nodo se pinta con la trama de ausencia si no hay ninguna.
    unidades = (autoria.dropna(subset=["unidad_academica"])
                .groupby("nombre_en_fuente")["unidad_academica"].first().to_dict())
    g = construir(zip(autoria["nombre_en_fuente"], autoria["eid"]),
                  excluir=fragmentos, unidades=unidades)

    comp = componentes(g["nodos"], g["aristas"])
    coms = comunidades(g["nodos"], g["aristas"])

    conectados = [n for n in g["nodos"] if comp[n] in
                  {c for c, k in _tamanos(comp).items() if k > 1}]
    aislados = [n for n in g["nodos"] if n not in set(conectados)]

    salida = {
        "generado_por": "src/build/grafo_coautoria.py",
        "capa": "interna · artefacto de revisión, no se copia a dist/ (C-05 se publica desde series.json y grafo.js)",
        "excluidas_e09": sorted(fragmentos),
        "resumen": {
            "personas": len(g["nodos"]),
            "personas_con_coautoria": len(conectados),
            "personas_aisladas": len(aislados),
            "aristas": len(g["aristas"]),
            "publicaciones": g["publicaciones"],
            "publicaciones_con_dos_o_mas_personas": g["publicaciones_con_dos_o_mas"],
            "componentes": len(set(comp.values())),
            "componente_mayor": max(_tamanos(comp).values()) if comp else 0,
            "comunidades_louvain": len(set(coms.values())),
        },
        "nodos": [{"persona": n, "unidad": g["unidades"][n],
                   "publicaciones": g["publicaciones_por_persona"][n],
                   "grado": sum(1 for e in g["aristas"] if n in (e["a"], e["b"])),
                   "componente": comp[n], "comunidad_louvain": coms[n]}
                  for n in g["nodos"]],
        "aristas": g["aristas"],
    }

    salida_path = b.INTERIM / "coauthorship_graph.json"
    b.INTERIM.mkdir(parents=True, exist_ok=True)
    salida_path.write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")

    r = salida["resumen"]
    print("\n  GRAFO DE COAUTORÍA (C-05, capa interna)")
    print(f"    personas             : {r['personas']}  "
          f"({r['personas_con_coautoria']} con coautoría · {r['personas_aisladas']} aisladas)")
    print(f"    aristas              : {r['aristas']}")
    print(f"    publicaciones        : {r['publicaciones']}  "
          f"({r['publicaciones_con_dos_o_mas_personas']} con 2+ personas UFT)")
    print(f"    componentes          : {r['componentes']}  "
          f"(la mayor, {r['componente_mayor']} personas)")
    print(f"    comunidades Louvain  : {r['comunidades_louvain']}  (heurística)")
    print(f"    firmas E-09 excluidas: {len(fragmentos)}")
    print(f"\n  OK · {salida_path.relative_to(b.ROOT)}")
    return 0


def _tamanos(part: dict[str, int]) -> dict[int, int]:
    t: dict[int, int] = defaultdict(int)
    for c in part.values():
        t[c] += 1
    return t


# --------------------------------------------------------------------------- #

def autotest() -> int:
    fallos = []

    def ok(c, m):
        if not c:
            fallos.append(m)

    # Un triángulo y un par suelto: dos componentes, y el par no cuelga del
    # triángulo por casualidad de ordenación.
    g = construir([("A", "p1"), ("B", "p1"), ("C", "p1"), ("D", "p2"), ("E", "p2")])
    ok(len(g["nodos"]) == 5, f"nodos: {g['nodos']}")
    ok(len(g["aristas"]) == 4, f"aristas: {len(g['aristas'])}")
    comp = componentes(g["nodos"], g["aristas"])
    ok(len(set(comp.values())) == 2, "deberían salir dos componentes")
    ok(comp["A"] == comp["B"] == comp["C"], "el triángulo es una componente")
    ok(comp["D"] == comp["E"] != comp["A"], "el par es otra")

    # Una publicación de un solo autor UFT no genera arista.
    g1 = construir([("A", "p1")])
    ok(g1["aristas"] == [], "un autor solo no coautora con nadie")

    # La misma firma repetida en la misma publicación no coautora consigo misma.
    g2 = construir([("A", "p1"), ("A", "p1"), ("B", "p1")])
    ok(len(g2["aristas"]) == 1, f"esperaba 1 arista, hubo {len(g2['aristas'])}")

    # Las firmas excluidas no aportan nodos ni aristas.
    g3 = construir([("A", "p1"), ("School of Psychology", "p1"), ("B", "p1")],
                   excluir={"School of Psychology"})
    ok(g3["nodos"] == ["A", "B"] and len(g3["aristas"]) == 1,
       "un fragmento E-09 no debería producir aristas")

    # El peso fraccional reparte 1/(n-1) y el recuento no.
    g4 = construir([("A", "p1"), ("B", "p1"), ("C", "p1")])
    ok(all(e["peso"] == 1 for e in g4["aristas"]), "recuento por publicación")
    ok(all(abs(e["peso_fraccional"] - 0.5) < 1e-9 for e in g4["aristas"]),
       f"fraccional en un trío debería ser 0,5: {g4['aristas']}")

    # Determinismo: dos corridas, misma partición.
    g5 = construir([(p, e) for e, gente in
                    {"p1": "ABC", "p2": "CD", "p3": "EF", "p4": "FG", "p5": "AD"}.items()
                    for p in gente])
    c1 = comunidades(g5["nodos"], g5["aristas"])
    c2 = comunidades(g5["nodos"], g5["aristas"])
    ok(c1 == c2, "Louvain debería ser reproducible")
    ok(componentes(g5["nodos"], g5["aristas"])["A"] ==
       componentes(g5["nodos"], g5["aristas"])["D"], "A y D coautoran en p5")

    # Dos grupos densos unidos por una sola arista débil: Louvain debería
    # separarlos. Es la propiedad que justifica usarlo en vez de componentes.
    densos = [(p, e) for e, gente in
              {"q1": "ABC", "q2": "ABC", "q3": "XYZ", "q4": "XYZ", "q5": "CX"}.items()
              for p in gente]
    g6 = construir(densos)
    c6 = comunidades(g6["nodos"], g6["aristas"])
    ok(len(set(c6.values())) == 2, f"esperaba dos comunidades, hubo {len(set(c6.values()))}")
    ok(c6["A"] == c6["B"] == c6["C"] and c6["X"] == c6["Y"] == c6["Z"],
       f"la partición no separó los dos bloques: {c6}")
    ok(len(set(componentes(g6["nodos"], g6["aristas"]).values())) == 1,
       "los dos bloques SÍ son una sola componente: es lo que distingue las dos particiones")

    for f in fallos:
        print(f"  FALLA  {f}")
    print(f"  {'OK' if not fallos else 'FALLOS'} · grafo_coautoria: "
          f"{15 - len(fallos)}/15 comprobaciones")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(autotest() if "--test" in sys.argv else main())
