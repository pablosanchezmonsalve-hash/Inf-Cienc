"""Build 04 — Textos metodológicos: glosario y ejes.

Serializa `docs/GLOSSARY.md` y `docs/EJES.md` a JSON. La fuente de verdad es el
Markdown: así el texto que ve el usuario —en un tooltip o en el panel que abre
una sección— es literalmente el documento metodológico revisado, no una copia
divergente mantenida a mano.

Salidas:
  data/processed/glossary.json
  data/processed/ejes.json
"""

from __future__ import annotations

import re

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
    """
    ind = b.INDICATORS["indicadores"]
    problemas = []
    for pagina in sorted((b.ROOT / "web").glob("*.html")):
        m = re.search(r'id="modulos"[^>]*data-indicadores="([^"]+)"',
                      pagina.read_text(encoding="utf-8"))
        if not m:
            continue
        clave = pagina.stem
        if clave not in ejes:
            problemas.append(f"la página '{clave}' no tiene panel en EJES.md")
            continue
        usados = sorted({ind[c.strip()].get("denominador")
                         for c in m.group(1).split(",")
                         if ind.get(c.strip(), {}).get("denominador")})
        declarados = ejes[clave]["denominadores"]
        if usados != declarados:
            problemas.append(
                f"el eje '{clave}' declara {declarados} y su página usa {usados}"
                f" · sobran {sorted(set(declarados) - set(usados))}"
                f" · faltan {sorted(set(usados) - set(declarados))}")
    if problemas:
        raise SystemExit("BUILD ABORTADO: el panel de una sección declara una "
                         "base que no es la que usa:\n  · "
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


if __name__ == "__main__":
    main()
