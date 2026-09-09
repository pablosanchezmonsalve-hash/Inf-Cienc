"""Build 04 — Textos metodológicos: glosario, ejes y lecturas de gráfico.

Serializa `docs/GLOSSARY.md`, `docs/EJES.md` y `docs/LECTURAS.md` a JSON. La
fuente de verdad es el Markdown: así el texto que ve el usuario —en un tooltip,
en el panel que abre una sección o bajo un gráfico del informe descargado— es
literalmente el documento metodológico revisado, no una copia divergente
mantenida a mano.

Salidas:
  data/processed/glossary.json
  data/processed/ejes.json
  data/processed/lecturas.json
"""

from __future__ import annotations

import re
import sys

if sys.platform == "win32":
    # La consola de Windows usa cp1252 por defecto: revienta cualquier print()
    # con caracteres como "→"/"✗"/"⚠". Mismo patrón que src/enrich/orcid_openalex.py.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import common_build as b


def parse_glossary(text: str) -> list[dict]:
    entradas = []
    # Cada entrada es un bloque '## Título' con un párrafo '**Corto:**' y otro
    # '**Extendido:**'. Se ignora todo lo anterior al primer encabezado.
    bloques = re.split(r"\n## ", text)[1:]
    for bloque in bloques:
        lineas = bloque.split("\n")
        titulo = lineas[0].strip()
        cuerpo = "\n".join(lineas[1:])

        corto = re.search(r"\*\*Corto:\*\*\s*(.+?)(?=\n\n|\Z)", cuerpo, re.S)
        extendido = re.search(r"\*\*Extendido:\*\*\s*(.+?)(?=\n---|\Z)", cuerpo, re.S)
        if not corto:
            continue

        def limpiar(s: str) -> str:
            s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
            s = re.sub(r"\n+", " ", s)
            return re.sub(r"\s+", " ", s).strip()

        entradas.append({
            "termino": titulo,
            "slug": b.slugify(titulo),
            "corto": limpiar(corto.group(1)),
            "extendido": limpiar(extendido.group(1)) if extendido else None,
        })
    return entradas


def parse_lecturas(text: str) -> dict[str, dict]:
    """Extrae de `docs/LECTURAS.md` qué muestra cada gráfico.

    Un bloque por gráfico: `## CÓDIGO — Título` y un párrafo `**Muestra:**`. La
    clave es el código del indicador, o el campo cuando el corte no tiene código
    propio, que es como los declara `vista_explorador.js`.
    """
    lecturas = {}
    for bloque in re.split(r"\n## ", text)[1:]:
        lineas = bloque.split("\n")
        cabecera = lineas[0].strip()
        # `_` en la clase: las claves del tablero son `citas_por_pub` y
        # `fwci_mediano`, y sin él sus bloques se descartaban en silencio.
        # Lo cazó la compuerta —pedía dos lecturas que existían—, que es
        # para lo que está, pero el analizador no debe perder nada callando.
        m = re.match(r"^([A-Za-z0-9_-]+)\s+—\s+(.+)$", cabecera)
        if not m:
            continue
        cuerpo = "\n".join(lineas[1:])
        muestra = re.search(r"\*\*Muestra:\*\*\s*(.+?)(?=\n---|\Z)", cuerpo, re.S)
        if not muestra:
            continue
        limpio = re.sub(r"\*\*(.+?)\*\*", r"\1", muestra.group(1))
        limpio = re.sub(r"\s+", " ", limpio).strip()
        lecturas[m.group(1)] = {"titulo": m.group(2).strip(), "muestra": limpio}
    return lecturas


def verificar_lecturas(lecturas: dict) -> None:
    """Toda figura del sitio tiene su lectura, y ninguna sobra.

    POR QUÉ ES COMPUERTA Y NO AVISO
        La lectura existe para el PAPEL, donde no hay ayuda contextual que
        rescate a nadie. Un gráfico sin ella se imprime igual, sin señal de que
        falta: el defecto no se ve al mirar el sitio, que es la misma familia de
        problemas que ya obligó a comprobar el PDF en vez del DOM.

        La lista de gráficos NO se escribe aquí: se lee de `vista_explorador.js`,
        que es donde se declara qué dibuja cada sección. Mantener una segunda
        lista sería inventar la forma de que las dos se separen.
    """
    fuente = (b.ROOT / "web/assets/js/vista_explorador.js").read_text(encoding="utf-8")
    # `cod: 'I-04'` y, para el corte sin código propio, `campo: 'escuela'`.
    codigos = set(re.findall(r"cod:\s*'([^']+)'", fuente))
    sin_cod = {c for c in re.findall(r"\{\s*campo:\s*'([^']+)'", fuente)}

    # Las figuras BENTO —el treemap y el mapa de calor— no son cortes del
    # explorador: se montan aparte, desde `paginas.js`, y por eso quedaban
    # fuera de esta comprobación. Fuera de ella, el treemap llegó a producción
    # con un párrafo de explicación VACÍO que nadie rellenaba: la figura más
    # difícil de leer del sitio, sin una frase que dijera qué mide un
    # rectángulo, y sin nada que lo denunciara.
    #
    # Se leen de donde de verdad están declaradas, el marcado de las páginas,
    # y no de una lista escrita aquí: `id="treemap-contenedor"` exige la
    # lectura `treemap`. Cualquier figura bento que se añada mañana entra sola
    # en la compuerta.
    bento = set()
    for pagina in sorted((b.ROOT / "web").glob("*.html")):
        bento |= set(re.findall(r'id="([a-z0-9-]+)-contenedor"',
                                pagina.read_text(encoding="utf-8")))

    # Las seis cifras grandes del tablero. Se leen de `FICHAS`, la tabla que las
    # declara, por la misma razón que todo lo demás: una lista escrita aquí se
    # separa de la de allá en cuanto alguien añada o quite una cifra.
    # Acotado al bloque FICHAS: `CORTES`, la tabla de los cuatro cortes de la
    # portada, tiene exactamente la misma forma `['clave', 'Título', …]`, y una
    # búsqueda suelta la barría también, exigiendo lecturas duplicadas para
    # gráficos que ya la tienen bajo su código de indicador.
    bloque_fichas = re.search(r"const FICHAS = \[(.*?)\n\];", fuente, re.S)
    ficha = (set(re.findall(r"\['([a-z_]+)'", bloque_fichas.group(1)))
             if bloque_fichas else set())

    esperados = codigos | sin_cod | bento | ficha

    faltan = sorted(esperados - set(lecturas))
    sobran = sorted(set(lecturas) - esperados)
    problemas = []
    if faltan:
        problemas.append(f"gráficos sin lectura en LECTURAS.md: {faltan}")
    if sobran:
        problemas.append(f"lecturas que ningún gráfico usa: {sobran}")
    if problemas:
        raise SystemExit("BUILD ABORTADO: las lecturas y los gráficos no "
                         "concuerdan:\n  · " + "\n  · ".join(problemas))


def parse_ejes(text: str) -> dict[str, dict]:
    """Extrae los paneles conceptuales de `docs/EJES.md`.

    Mismo criterio que el glosario: el Markdown manda. Un panel que explica qué
    NO responde una sección es afirmación metodológica, y esas se revisan como
    documento, no como cadena dentro de un archivo de JavaScript.

    Las tres partes son obligatorias. Un panel al que le falte «No responde» es
    justamente el que no hacía falta escribir: sin esa parte, el resto es un
    subtítulo.
    """
    ejes: dict[str, dict] = {}
    for bloque in re.split(r"\n## ", text)[1:]:
        lineas = bloque.split("\n")
        clave = lineas[0].strip()
        cuerpo = "\n".join(lineas[1:])

        def campo(etiqueta: str) -> str | None:
            m = re.search(rf"\*\*{etiqueta}:\*\*\s*(.+?)(?=\n\n\*\*|\n---|\Z)",
                          cuerpo, re.S)
            if not m:
                return None
            return re.sub(r"\s+", " ", re.sub(r"\*\*(.+?)\*\*", r"\1", m.group(1))).strip()

        partes = {k: campo(e) for k, e in
                  (("titulo", "Título"), ("responde", "Responde"),
                   ("no_responde", "No responde"), ("sobre_que", "Sobre qué"),
                   ("denominadores", "Denominadores"))}
        faltan = [k for k, v in partes.items() if not v]
        if faltan:
            raise SystemExit(f"BUILD ABORTADO: al eje '{clave}' de EJES.md le "
                             f"faltan las partes {faltan}")
        # `denominadores` no se publica: existe para que la guarda pueda
        # contrastar lo que el panel dice con lo que la página usa.
        partes["denominadores"] = sorted(
            d.strip() for d in partes["denominadores"].split(",") if d.strip())
        ejes[clave] = partes
    return ejes


def verificar_denominadores(ejes: dict[str, dict]) -> None:
    """Que la base declarada por cada panel sea la que la sección usa de verdad.

    EL FALLO QUE ESTO CAZA, y que ya ocurrió:
        El panel de producción decía «las publicaciones del universo» y explicaba
        el caso de la unidad académica. Pero la sección también trae el ranking
        de fuentes, que corre sobre las publicaciones con métricas: 816 y no 823.
        Un lector habría contado mal justo en la frase que promete impedírselo.

    POR QUÉ SE INSTRUMENTA Y NO SE REVISA A MANO
        Los dos lados ya eran legibles por máquina —la página declara sus códigos
        en `data-indicadores` y `config/indicators.yml` declara el denominador de
        cada código—; sólo faltaba que el eje declarara los suyos. Sin esto, la
        lista escrita a mano deja de cubrirlo todo en cuanto alguien añade un
        indicador a una sección, y el panel sigue diciendo su base vieja sin que
        nada avise. Es la misma forma que las guardas de cobertura de
        `contraste.mjs` y `estructura.mjs`.

    Se exige igualdad y no inclusión: un denominador declarado que ninguna página
    usa es una declaración que envejeció, y esa es la mitad del problema.

    Y ya que aquí es donde `data-indicadores` se lee por primera vez contra el
    catálogo, se comprueban dos cosas más que sólo se ven desde este sitio: que
    ningún código sea desconocido, y que ningún eje se quede sin página.
    """
    ind = b.INDICATORS["indicadores"]
    problemas = []
    con_pagina = set()
    for pagina in sorted((b.ROOT / "web").glob("*.html")):
        # El contenedor pasó a llamarse `cortes` cuando las secciones se
        # volvieron explorables: los indicadores ya no se dibujan como módulos
        # precalculados sino como cortes recalculados sobre el recorte. Lo que
        # esta guarda comprueba no cambió —qué indicadores cubre cada sección y
        # con qué denominadores—, así que se acepta cualquiera de los dos
        # contenedores en vez de relajar la comprobación.
        m = re.search(r'id="(?:modulos|cortes)"[^>]*data-indicadores="([^"]+)"',
                      pagina.read_text(encoding="utf-8"))
        if not m:
            continue
        clave = pagina.stem
        con_pagina.add(clave)
        if clave not in ejes:
            problemas.append(f"la página '{clave}' no tiene panel en EJES.md")
            continue

        codigos = [c.strip() for c in m.group(1).split(",") if c.strip()]

        # UN CÓDIGO DESCONOCIDO ES UNA ERRATA, Y HOY BORRABA UN GRÁFICO EN
        # SILENCIO. `paginaModulos` descarta los códigos que no están en las
        # series, así que cambiar `A-01` por `Z-99` en un `data-indicadores`
        # dejaba la página de impacto con cuatro módulos en vez de cinco, y el
        # pipeline entero —auditoría, barrera de capas, batería del navegador—
        # terminaba en verde sin nombrar el código ni una vez. Medido.
        #
        # Aquí no hay nada que interpretar: un código que no está en el catálogo
        # no es una decisión, es un error de escritura.
        desconocidos = [c for c in codigos if c not in ind]
        if desconocidos:
            problemas.append(
                f"la página '{clave}' declara códigos que no existen en "
                f"config/indicators.yml: {desconocidos}")
            continue

        # Sólo los publicados, y esto ENDURECE la guarda en vez de relajarla:
        # al retirar un indicador con `publicar: false`, su denominador deja de
        # estar en uso y el panel pasa a declarar una base que ya nadie tiene.
        # El build se detiene y dice cuál sobra.
        #
        # Es deliberado. `config/indicators.yml` promete que se puede desactivar
        # un indicador «sin tocar el código del build», y sigue siendo cierto:
        # `EJES.md` no es código, es el documento que describe la sección. Si el
        # ranking de fuentes deja de mostrarse, la frase del panel que lo explica
        # deja de ser verdad, y esa frase hay que reescribirla. Dejarlo pasar en
        # silencio sería publicar un panel que describe un gráfico ausente.
        usados = sorted({ind[c].get("denominador") for c in codigos
                         if ind[c].get("publicar") and ind[c].get("denominador")})
        declarados = ejes[clave]["denominadores"]
        if usados != declarados:
            problemas.append(
                f"el eje '{clave}' declara {declarados} y su página usa {usados}"
                f" · sobran {sorted(set(declarados) - set(usados))}"
                f" · faltan {sorted(set(usados) - set(declarados))}")

    # El bucle recorre páginas, así que caza «página sin panel» y no su simétrico.
    # Un eje sin página se serializa a ejes.json igual: se PUBLICA un panel que
    # ninguna sección muestra. Pesa más que el denominador huérfano, que al menos
    # no llegaba al artefacto.
    huerfanos = sorted(set(ejes) - con_pagina)
    if huerfanos:
        problemas.append(f"EJES.md declara ejes que ninguna página usa: {huerfanos}")

    if problemas:
        raise SystemExit("BUILD ABORTADO: los paneles de sección y los "
                         "indicadores de sus páginas no concuerdan:\n  · "
                         + "\n  · ".join(problemas))


def main() -> None:
    b.banner("BUILD 04 — GLOSARIO")

    ruta = b.DOCS / "GLOSSARY.md"
    entradas = parse_glossary(ruta.read_text(encoding="utf-8"))

    if not entradas:
        raise SystemExit("BUILD ABORTADO: no se extrajo ninguna entrada de GLOSSARY.md")

    sin_extendido = [e["termino"] for e in entradas if not e["extendido"]]
    if sin_extendido:
        print(f"  aviso · entradas sin texto extendido: {sin_extendido}")

    b.write_json({"meta": b.build_meta(), "entradas": entradas}, "glossary.json")
    print(f"  entradas: {len(entradas)}")
    for e in entradas:
        print(f"    - {e['termino']}")

    ejes = parse_ejes((b.DOCS / "EJES.md").read_text(encoding="utf-8"))
    if not ejes:
        raise SystemExit("BUILD ABORTADO: no se extrajo ningún eje de EJES.md")
    verificar_denominadores(ejes)

    # La lista de denominadores es instrumental: sirve a la guarda de arriba, no
    # al lector. Publicarla metería en el artefacto un dato que la página no usa.
    publicables = {k: {c: v for c, v in e.items() if c != "denominadores"}
                   for k, e in ejes.items()}
    b.write_json({"meta": b.build_meta(), "ejes": publicables}, "ejes.json")
    print(f"\n  ejes: {len(ejes)}")
    for clave, e in ejes.items():
        print(f"    - {clave}: {e['titulo']}")

    lecturas = parse_lecturas((b.DOCS / "LECTURAS.md").read_text(encoding="utf-8"))
    if not lecturas:
        raise SystemExit("BUILD ABORTADO: no se extrajo ninguna lectura de LECTURAS.md")
    verificar_lecturas(lecturas)
    b.write_json({"meta": b.build_meta(), "lecturas": lecturas}, "lecturas.json")
    print(f"\n  lecturas de gráfico: {len(lecturas)}")


if __name__ == "__main__":
    main()
