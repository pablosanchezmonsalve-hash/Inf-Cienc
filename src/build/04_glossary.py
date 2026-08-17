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
                   ("no_responde", "No responde"), ("sobre_que", "Sobre qué"))}
        faltan = [k for k, v in partes.items() if not v]
        if faltan:
            raise SystemExit(f"BUILD ABORTADO: al eje '{clave}' de EJES.md le "
                             f"faltan las partes {faltan}")
        ejes[clave] = partes
    return ejes


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
    b.write_json({"meta": b.build_meta(), "ejes": ejes}, "ejes.json")
    print(f"\n  ejes: {len(ejes)}")
    for clave, e in ejes.items():
        print(f"    - {clave}: {e['titulo']}")


if __name__ == "__main__":
    main()
