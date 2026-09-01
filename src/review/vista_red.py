"""Vista de la red de coautoría con el grafo REAL, para revisión interna.

QUÉ ES ESTO AHORA QUE C-05 SE PUBLICÓ (T-10, 2026-08-26)
    Esta página en `internal/` sigue existiendo, pero ya no es «la vista de
    C-05 antes de decidir publicarla» — esa decisión ya se tomó, y el público
    la ve en `colaboracion.html`, recalculada en vivo sobre el recorte de
    filtros vigente (`web/assets/js/grafo.js` + `vista_explorador.js`).

    Lo que esta página sigue aportando que la pública no tiene: el grafo
    COMPLETO sin filtrar, de una sola vez, con nombres de persona visibles sin
    depender de que alguien pase el mouse — más cómodo para revisar de un
    vistazo que para consumir como informe. Usa exactamente las mismas
    primitivas que el sitio —`red()` de core.js y app.css—, así que lo que se
    ve aquí es fiel a lo que vería el público con ese mismo recorte.

Y POR QUÉ SÍ VALE LA PENA SEGUIR GENERÁNDOLA
    Porque el heurístico de apellido compartido no era sólo para T-03: sigue
    siendo una segunda mirada, más amplia y más ruidosa, sobre coincidencias de
    apellido entre nodos —incluyendo pares que son personas genuinamente
    distintas (apellidos comunes), no sólo variantes de una misma firma—. Leer
    esa lista en un CSV es una cosa; verla dibujada sobre la red real es otra.

    Por eso la vista marca los CANDIDATOS: pares de nodos cuyo apellido
    normalizado coincide. No decide nada —eso sigue siendo juicio humano— pero
    pone la duda donde se puede mirar.

USO
    python3 src/review/vista_red.py        # genera internal/red_coautoria.html
    python3 src/review/vista_red.py --test # sólo la lógica
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

if sys.platform == "win32":
    # La consola de Windows usa cp1252 por defecto: revienta cualquier print()
    # con caracteres como "→"/"✗"/"⚠". Mismo patrón que src/enrich/orcid_openalex.py.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(ROOT / "src" / "review"))

import equivalencia_ortografica as EQ  # noqa: E402

GRAFO = ROOT / "data" / "interim" / "coauthorship_graph.json"
SALIDA = ROOT / "internal" / "red_coautoria.html"


def _json_para_script(obj) -> str:
    """JSON seguro para incrustar en <script>: json.dumps no escapa '</',
    así que un título o afiliación con "</script>" cerraría el bloque antes
    de tiempo y el resto se interpretaría como HTML."""
    return (
        json.dumps(obj, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def apellido(firma: str) -> str:
    """La parte de la firma que no son iniciales, normalizada.

    «Núñez-Lisboa M.N.» -> «nunez lisboa». Se usa sólo para AGRUPAR candidatos,
    nunca para decidir: dos personas distintas comparten apellido a menudo, y
    ese es justamente el caso que hay que mirar.
    """
    n = EQ.normalizar(firma)
    partes = [p for p in n.split() if len(p) > 1]
    return " ".join(partes) or n


def candidatos_t03(personas: list[str]) -> dict[str, list[str]]:
    """Nodos que comparten apellido: los que podrían ser la misma persona."""
    por: dict[str, list[str]] = defaultdict(list)
    for p in personas:
        por[apellido(p)].append(p)
    return {k: sorted(v) for k, v in por.items() if len(v) > 1}


MINIMO = 5


def preparar(grafo: dict, minimo: int = MINIMO) -> dict:
    """Del artefacto del pipeline a la forma que consume `red()` de core.js.

    core.js espera `[{i, id, valor, n, unidad, com}]` y aristas por índice. Se
    usa la COMPONENTE y no la comunidad de Louvain para agrupar el dibujo: la
    componente es un hecho del grafo y la comunidad una heurística, y el
    agrupamiento visual es lo primero que un lector toma por real.

    POR QUÉ HAY UN MÍNIMO
        El grafo tiene 271 componentes y 200 de ellas son una persona sola.
        Dibujarlas todas como grupos produce un anillo de 271 cúmulos con las
        etiquetas encabalgadas, donde no se lee nada: la primitiva reparte los
        grupos alrededor de una órbita y eso funciona con una docena, no con
        cientos.

        Se dibujan las componentes de `minimo` personas o más. Las demás NO se
        meten en un grupo «resto»: 132 personas repartidas en 54 componentes
        que no se tocan entre sí formarían el cúmulo más grande del dibujo y se
        leerían como el grupo mayor, que es lo contrario de lo que son. Se
        declaran en cifras.

        Lo que se recorta es el DIBUJO, no el análisis: la lista de candidatos
        de T-03 se calcula sobre todos los nodos, porque para eso se hizo.
    """
    todos = grafo["nodos"]
    cands = candidatos_t03([n["persona"] for n in todos])
    sospechosos = {p for v in cands.values() for p in v}

    tam: dict[int, int] = defaultdict(int)
    for n in todos:
        tam[n["componente"]] += 1
    visibles = [n for n in todos if tam[n["componente"]] >= minimo]
    idx = {n["persona"]: i for i, n in enumerate(visibles)}

    nodos = [{"i": i, "id": n["persona"], "valor": n["persona"],
              "n": n["publicaciones"], "unidad": n["unidad"],
              "com": n["componente"], "sospechoso": n["persona"] in sospechosos}
             for i, n in enumerate(visibles)]
    aristas = [{"a": idx[e["a"]], "b": idx[e["b"]], "n": e["peso"]}
               for e in grafo["aristas"] if e["a"] in idx and e["b"] in idx]

    menores = [c for c, k in tam.items() if 1 < k < minimo]
    return {"nodos": nodos, "aristas": aristas, "candidatos": cands,
            "resumen": grafo["resumen"], "excluidas": grafo.get("excluidas_e09", []),
            "minimo": minimo,
            "fuera": {"componentes_menores": len(menores),
                      "personas_en_menores": sum(tam[c] for c in menores),
                      "personas_aisladas": sum(1 for c, k in tam.items() if k == 1)}}


PAGINA = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Red de coautoría · revisión interna</title>
<style>{css}</style>
<style>
  body {{ padding: var(--e6) var(--e5); }}
  .marco {{ max-width: 1100px; margin: 0 auto; }}
  .aviso-interno {{
    background: var(--aviso-fondo); border-left: 4px solid var(--aviso-borde);
    color: var(--aviso-tinta); padding: var(--e4); margin-bottom: var(--e5);
    border-radius: var(--radio); }}
  .aviso-interno b {{ display: block; margin-bottom: var(--e2); }}
  .cifras {{ display: flex; flex-wrap: wrap; gap: var(--e5); margin: var(--e5) 0; }}
  .cifras div b {{ display: block; font: 700 var(--t-xl)/1 var(--f-ui); color: var(--cifra); }}
  .cifras div span {{ font-size: var(--t-s); color: var(--tinta-2); }}
  .vistas {{ display: flex; gap: var(--e2); margin-bottom: var(--e4); }}
  .vistas button[aria-pressed="true"] {{ background: var(--accion); color: var(--boton-tinta); }}
  svg.chart .nodo-red.sospechoso circle.marca-nodo {{
    stroke: var(--aviso-borde); stroke-width: 2; }}
  .lista-cand {{ columns: 2; font-size: var(--t-s); }}
  .lista-cand li {{ break-inside: avoid; margin-bottom: .3rem; }}
</style>
</head><body data-tema="claro"><div class="marco">

<div class="aviso-interno"><b>Herramienta de revisión · no es la vista pública</b>
C-05 ya se publicó (T-10, 2026-08-26) en <code>colaboracion.html</code>, recorte
en vivo incluido: estos mismos nombres y vínculos ya son públicos ahí. Esta
página sigue en <code>internal/</code> porque muestra el grafo COMPLETO sin
filtrar de una vez, y porque marca candidatos a la misma persona para la
revisión de identidad — dos usos que la vista pública no cubre, no un secreto
que la vista pública no tenga.</div>

<h1>Red de coautoría interna</h1>
<p class="nota">Grafo real, con las mismas primitivas que usará el sitio cuando
C-05 se publique. Firmas E-09 excluidas: {excluidas}.</p>
<p class="nota">Se dibujan las componentes de <b>{minimo} personas o más</b>. Quedan
fuera del dibujo {fuera_menores} componentes de 2 a {minimo_1} personas
({fuera_personas} personas) y {fuera_aisladas} personas sin ninguna coautoría
interna. No se agrupan en un «resto» porque no son un grupo: son componentes que
no se tocan entre sí, y juntas formarían el cúmulo mayor del dibujo.
<b>La lista de candidatos de abajo sí cubre a todas las personas.</b></p>

<div class="cifras">{cifras}</div>

<div class="vistas" role="group" aria-label="Forma de la red">
  <button class="boton" data-vista="nodos" aria-pressed="true">Nodos</button>
  <button class="boton" data-vista="matriz" aria-pressed="false">Matriz</button>
  <button class="boton" data-vista="arcos" aria-pressed="false">Arcos</button>
</div>
<div class="grafico" id="red"></div>

<h2>Candidatos a la misma persona ({n_cand} apellidos)</h2>
<p class="nota">Nodos que comparten apellido normalizado. No es un veredicto:
es dónde mirar. Aparecen con anillo ámbar en la vista de nodos.</p>
<ul class="lista-cand">{candidatos}</ul>

</div>
<script type="module">
{core}

const D_RAW = {datos};
const D = disponerRed(D_RAW.nodos, D_RAW.aristas);
D.ents.forEach((e, i) => {{ e.sospechoso = D_RAW.nodos[i].sospechoso; }});

const cont = document.getElementById('red');
let forma = 'nodos';
function pintar() {{
  cont.innerHTML = red(D, forma);
  cont.querySelectorAll('g.nodo-red').forEach((g, k) => {{
    if (D.ents[k] && D.ents[k].sospechoso) g.classList.add('sospechoso');
  }});
}}
document.querySelectorAll('.vistas button').forEach(b => b.addEventListener('click', () => {{
  forma = b.dataset.vista;
  document.querySelectorAll('.vistas button').forEach(x =>
    x.setAttribute('aria-pressed', String(x === b)));
  pintar();
}}));
pintar();
</script>
</body></html>
"""


def main() -> int:
    if not GRAFO.exists():
        sys.exit(f"Falta {GRAFO.relative_to(ROOT)}. Corra primero el build "
                 "(python3 src/build/grafo_coautoria.py).")
    d = preparar(json.loads(GRAFO.read_text(encoding="utf-8")))

    css = (ROOT / "web" / "assets" / "css" / "app.css").read_text(encoding="utf-8")
    # core.js es un módulo con `export`; aquí se incrusta en un <script type=module>
    # del mismo documento, así que los `export` sobran y estorban.
    core = (ROOT / "web" / "assets" / "js" / "core.js").read_text(encoding="utf-8")
    core = core.replace("export function ", "function ").replace("export const ", "const ")

    etiquetas = [("personas", "personas"), ("aristas", "pares de coautoría"),
                 ("publicaciones_con_dos_o_mas_personas", "publicaciones con 2+"),
                 ("componentes", "componentes"), ("componente_mayor", "la mayor"),
                 ("personas_aisladas", "sin coautoría interna")]
    cifras = "".join(f"<div><b>{d['resumen'][k]}</b><span>{t}</span></div>"
                     for k, t in etiquetas if k in d["resumen"])
    cands = "".join(f"<li><b>{k}</b> — {' · '.join(v)}</li>"
                    for k, v in sorted(d["candidatos"].items()))

    SALIDA.write_text(PAGINA.format(
        css=css, core=core, cifras=cifras, candidatos=cands,
        n_cand=len(d["candidatos"]), minimo=d["minimo"], minimo_1=d["minimo"] - 1,
        fuera_menores=d["fuera"]["componentes_menores"],
        fuera_personas=d["fuera"]["personas_en_menores"],
        fuera_aisladas=d["fuera"]["personas_aisladas"],
        excluidas=", ".join(d["excluidas"]) or "ninguna",
        datos=_json_para_script({"nodos": d["nodos"], "aristas": d["aristas"]})),
        encoding="utf-8")

    print("\n  VISTA DE LA RED (capa interna)")
    print(f"    nodos dibujados      : {len(d['nodos'])} "
          f"(componentes de {d['minimo']}+ personas)")
    print(f"    fuera del dibujo     : {d['fuera']['personas_en_menores']} en "
          f"{d['fuera']['componentes_menores']} componentes menores · "
          f"{d['fuera']['personas_aisladas']} aisladas")
    print(f"    aristas              : {len(d['aristas'])}")
    print(f"    apellidos con más de un nodo: {len(d['candidatos'])}")
    print(f"    nodos marcados       : {sum(1 for n in d['nodos'] if n['sospechoso'])}")
    print(f"\n  OK · {SALIDA.relative_to(ROOT)}")
    return 0


# --------------------------------------------------------------------------- #

def autotest() -> int:
    fallos = []

    def ok(c, m):
        if not c:
            fallos.append(m)

    ok(apellido("Núñez-Lisboa M.N.") == "nunez lisboa", apellido("Núñez-Lisboa M.N."))
    ok(apellido("García J.") == apellido("Garcia J."), "los diacríticos no deberían separar")
    ok(apellido("De la Fuente M.") == "de la fuente", apellido("De la Fuente M."))

    c = candidatos_t03(["Gutiérrez M.", "Gutierrez J.", "Solo A."])
    ok(list(c) == ["gutierrez"], f"agrupación inesperada: {c}")
    ok("Solo A." not in {p for v in c.values() for p in v}, "un apellido único no es candidato")

    g = {"nodos": [{"persona": "Pérez B.", "unidad": "U", "publicaciones": 2,
                    "grado": 1, "componente": 0, "comunidad_louvain": 0},
                   {"persona": "Perez C.", "unidad": "No determinada", "publicaciones": 1,
                    "grado": 1, "componente": 0, "comunidad_louvain": 0}],
          "aristas": [{"a": "Pérez B.", "b": "Perez C.", "peso": 1, "peso_fraccional": 1.0}],
          "resumen": {"personas": 2}}
    d = preparar(g, minimo=2)
    ok(d["aristas"] == [{"a": 0, "b": 1, "n": 1}], f"aristas por índice: {d['aristas']}")
    ok(all(n["sospechoso"] for n in d["nodos"]), "dos «Pérez» comparten apellido")
    ok(d["nodos"][0]["com"] == 0, "el agrupamiento usa la componente")

    # El umbral recorta el DIBUJO y no el análisis: los dos nodos salen del
    # dibujo, pero siguen contados como candidatos.
    d2 = preparar(g, minimo=5)
    ok(d2["nodos"] == [] and d2["aristas"] == [], "el umbral debería vaciar el dibujo")
    ok(len(d2["candidatos"]) == 1, "los candidatos se calculan sobre TODOS los nodos")
    ok(d2["fuera"]["personas_en_menores"] == 2, f"fuera: {d2['fuera']}")

    # Una arista con un extremo fuera del dibujo no puede quedar colgando.
    g3 = {"nodos": [{"persona": f"P{i} X.", "unidad": "U", "publicaciones": 1,
                     "grado": 1, "componente": 0 if i < 3 else 1,
                     "comunidad_louvain": 0} for i in range(4)],
          "aristas": [{"a": "P0 X.", "b": "P1 X.", "peso": 1, "peso_fraccional": 1.0},
                      {"a": "P2 X.", "b": "P3 X.", "peso": 1, "peso_fraccional": 1.0}],
          "resumen": {}}
    d3 = preparar(g3, minimo=3)
    ok(len(d3["nodos"]) == 3, f"sólo la componente de 3: {len(d3['nodos'])}")
    ok(len(d3["aristas"]) == 1, f"la arista hacia fuera debe caer: {d3['aristas']}")
    ok(all(a["a"] < 3 and a["b"] < 3 for a in d3["aristas"]), "índices reindexados")

    for f in fallos:
        print(f"  FALLA  {f}")
    print(f"  {'OK' if not fallos else 'FALLOS'} · vista_red: {14 - len(fallos)}/14 comprobaciones")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(autotest() if "--test" in sys.argv else main())
