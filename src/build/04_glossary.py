"""Build 04 — Glosario y ayuda contextual.

Serializa `docs/GLOSSARY.md` a JSON. La fuente de verdad es el Markdown: así el
texto que ve el usuario en un tooltip es literalmente el documento
metodológico revisado, no una copia divergente mantenida a mano.

Salida:
  data/processed/glossary.json
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


if __name__ == "__main__":
    main()
