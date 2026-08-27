"""Valida el sistema cromático completo, token por token, en los dos temas.

POR QUÉ ESTO ES UN ARCHIVO Y NO UNA TABLA EN LA DOCUMENTACIÓN

La documentación de `docs/UX_UI.md` publica una tabla de razones de contraste.
Una tabla es una FOTOGRAFÍA: fue cierta el día que se midió. Este archivo es el
INSTRUMENTO, y se puede volver a correr. La diferencia importa porque el rojo
publicado es provisional —no se pudo verificar el color institucional oficial de
la UFT— y el día que llegue el oficial hay que sustituir cuatro tokens y
comprobar que el sistema entero sigue en pie.

Sin este archivo, ese día habría que reconstruir el método de memoria. Con él,
es cambiar cuatro valores y correr un comando.

QUÉ COMPRUEBA

  1. CONTRASTE (WCAG 2.1). Cada token contra el fondo sobre el que de verdad se
     dibuja, con el piso que fija su USO y no el gusto: 4,5:1 texto normal
     (1.4.3), 3,0:1 texto grande y objeto gráfico (1.4.11).

  2. SEPARACIÓN DATO ↔ ADVERTENCIA (OKLab ΔE ≥ 20). El dato es rojo y la
     advertencia metodológica ámbar. Dos familias cálidas contiguas se pueden
     confundir, y confundir «esto es el dato» con «esto es una advertencia
     sobre el dato» es un fallo metodológico, no estético.

  3. RAMPA ORDINAL (ΔE ≥ 8 entre escalones, luminosidad monótona). Q1–Q4 es una
     escala ORDENADA: tiene que verse ordenada, y los cuatro escalones tienen
     que distinguirse incluso impresos en gris.

  4. PAR CATEGÓRICO EN USO bajo daltonismo. El anillo de C-01 gasta dos ranuras.
     Se simula protanopía, deuteranopía y tritanopía y se exige separación en
     las tres — el peor caso es la deuteranopía, y es el que decide.

Los valores se LEEN de `web/assets/css/app.css`, no se copian aquí: una copia
se desactualiza en silencio.

Uso:  python3 src/design/validar_paleta.py
"""

from __future__ import annotations

import math
import pathlib
import re
import sys
if sys.platform == "win32":
    # La consola de Windows usa cp1252 por defecto: revienta cualquier print()
    # con caracteres como "→"/"—"/"·". Mismo patrón que src/enrich/orcid_openalex.py.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


RAIZ = pathlib.Path(__file__).resolve().parents[2]
HOJA = RAIZ / "web" / "assets" / "css" / "app.css"


# ─────────────────────────────────────────────────────────────── colorimetría

def _lin(c: float) -> float:
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _rgb(h: str) -> list[int]:
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def luminancia(h: str) -> float:
    r, g, b = (_lin(v) for v in _rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(a: str, b: str) -> float:
    x, y = sorted([luminancia(a), luminancia(b)], reverse=True)
    return (x + 0.05) / (y + 0.05)


def oklab(h: str) -> tuple[float, float, float]:
    r, g, b = (_lin(v) for v in _rgb(h))
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def delta_e(a: str, b: str) -> float:
    """Distancia perceptual en OKLab, ×100 para trabajar con números legibles."""
    return 100 * math.dist(oklab(a), oklab(b))


def simular(h: str, tipo: str) -> str:
    """Simulación de dicromacia sobre el espacio LMS (Brettel/Viénot).

    No es una simulación clínica: es suficiente para decidir si dos colores que
    se dibujan juntos se van a distinguir. Que sea aproximada no la hace
    opcional — sin ella, la separación se comprueba sólo en visión normal, que
    es donde nunca falla.
    """
    r, g, b = (_lin(v) for v in _rgb(h))
    L = 17.8824 * r + 43.5161 * g + 4.11935 * b
    M = 3.45565 * r + 27.1554 * g + 3.86714 * b
    S = 0.0299566 * r + 0.184309 * g + 1.46709 * b
    if tipo == "protanopia":
        L = 2.02344 * M - 2.52581 * S
    elif tipo == "deuteranopia":
        M = 0.494207 * L + 1.24827 * S
    else:  # tritanopía
        S = -0.395913 * L + 0.801109 * M
    r2 = 0.080944 * L - 0.130504 * M + 0.116721 * S
    g2 = -0.0102485 * L + 0.0540194 * M - 0.113615 * S
    b2 = -0.000365294 * L - 0.00412163 * M + 0.693513 * S

    def _srgb(c: float) -> int:
        c = max(0.0, min(1.0, c))
        c = 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
        return round(c * 255)

    return "#%02x%02x%02x" % (_srgb(r2), _srgb(g2), _srgb(b2))


# ──────────────────────────────────────────────────── lectura de los tokens

TOKEN = re.compile(
    r"(--[a-z0-9-]+):\s*light-dark\(\s*(#[0-9a-fA-F]{6})\s*,\s*(#[0-9a-fA-F]{6})\s*\)")

# Un token puede declararse con un solo hex, y entonces vale igual en los dos
# temas. Dentro de .banda-contraste es lo habitual: la banda es oscura en claro
# y en oscuro, así que su tinta no cambia.
TOKEN_PLANO = re.compile(r"(--[a-z0-9-]+):\s*(#[0-9a-fA-F]{6})\s*;")


def _bloque(texto: str, selector: str) -> str:
    """Devuelve el cuerpo de la primera regla `selector { ... }`.

    Leer la hoja entera y quedarse con la ÚLTIMA aparición de cada token era un
    error real: .banda-contraste redefine --superficie, --superficie-2 y --plano
    en su propio ámbito, y esos valores pisaban los de :root. El validador
    terminaba midiendo tinta clara contra suelo oscuro y declaraba 12 fallos que
    no existían. Un instrumento que da falsos positivos se deja de mirar, y
    entonces tampoco atrapa los verdaderos.
    """
    i = texto.find(selector + " {")
    if i < 0:
        i = texto.find(selector + "{")
        if i < 0:
            sys.exit(f"No se encuentra la regla `{selector}` en {HOJA.name}")
    a = texto.index("{", i)
    fin = texto.index("}", a)
    return texto[a + 1:fin]


def _tokens_de(cuerpo: str) -> dict[str, dict[str, str]]:
    t = {m.group(1): {"claro": m.group(2).lower(), "oscuro": m.group(3).lower()}
         for m in TOKEN.finditer(cuerpo)}
    for m in TOKEN_PLANO.finditer(cuerpo):
        t.setdefault(m.group(1), {"claro": m.group(2).lower(),
                                  "oscuro": m.group(2).lower()})
    return t


def leer_tokens() -> dict[str, dict[str, str]]:
    if not HOJA.exists():
        sys.exit(f"No se encuentra {HOJA}")
    tokens = _tokens_de(_bloque(HOJA.read_text(encoding="utf-8"), ":root"))
    if not tokens:
        sys.exit("No se leyó ningún token light-dark() de :root.")
    return tokens


def leer_ambito(selector: str) -> dict[str, dict[str, str]]:
    """Los tokens vigentes DENTRO de un ámbito: los de :root con los que ese
    ámbito redefine encima. Es lo que hace la cascada, y es la paleta que ve de
    verdad quien lee esa parte de la página."""
    texto = HOJA.read_text(encoding="utf-8")
    return {**_tokens_de(_bloque(texto, ":root")),
            **_tokens_de(_bloque(texto, selector))}


# ───────────────────────────────────────────────────── la tabla de reglas

# (token, fondo, piso, uso). El PISO lo fija el uso, no la preferencia.
REGLAS = [
    ("--tinta",               "--superficie",   4.5, "texto principal"),
    ("--tinta-2",             "--superficie",   4.5, "texto secundario"),
    ("--tinta-3",             "--superficie-2", 4.5, "metadatos sobre el peor fondo"),
    ("--cifra",               "--superficie",   3.0, "cifra grande de KPI"),
    ("--accion",              "--superficie",   4.5, "texto de enlace"),
    ("--accion",              "--superficie-2", 4.5, "enlace sobre superficie alterna"),
    ("--serie-1",             "--superficie",   3.0, "barra de dato"),
    ("--serie-2",             "--superficie",   3.0, "segunda ranura · anillo C-01"),
    ("--sin-dato",            "--superficie",   3.0, "barra de ausencia"),
    ("--ord-1",               "--superficie",   3.0, "ordinal 1 · Q1"),
    ("--ord-2",               "--superficie",   3.0, "ordinal 2 · Q2"),
    ("--ord-3",               "--superficie",   3.0, "ordinal 3 · Q3"),
    ("--ord-4",               "--superficie",   3.0, "ordinal 4 · Q4"),
    ("--marca-tinta",         "--marca",        4.5, "nav sobre la cabecera"),
    ("--aviso-tinta",         "--aviso-fondo",  4.5, "texto de advertencia"),
    ("--aviso-tinta-grafico", "--superficie",   4.5, "etiqueta de referencia"),
    ("--boton-tinta",         "--accion",       4.5, "tinta del botón primario"),
]

# El segundo suelo de banda lleva figuras, así que tiene que sostener la tinta
# fina, el color del dato y —sobre todo— la marca de ausencia. Ese último piso
# es el que fija cuánto puede oscurecerse el papel: es la regla que impide
# repetir en papel-2 el error de poner figuras sobre el Peach del cierre.
REGLAS_BANDA_PAPEL_2 = [
    ("--tinta",    "--banda-papel-2", 4.5, "texto principal"),
    ("--tinta-3",  "--banda-papel-2", 4.5, "metadatos"),
    ("--accion",   "--banda-papel-2", 4.5, "texto de enlace"),
    ("--serie-1",  "--banda-papel-2", 3.0, "barra de dato"),
    ("--sin-dato", "--banda-papel-2", 3.0, "barra de ausencia"),
]

RAMPA = ["--ord-1", "--ord-2", "--ord-3", "--ord-4"]
PAR_CATEGORICO = ("--serie-1", "--serie-2")
PISO_DE = 20.0        # dato vs advertencia
PISO_ESCALON = 8.0    # entre escalones de la rampa y entre ranuras categóricas


def main() -> None:
    T = leer_tokens()
    print("=" * 78)
    print(f"VALIDACIÓN DEL SISTEMA CROMÁTICO · {len(T)} tokens leídos de app.css")
    print("=" * 78)
    fallos = 0

    def val(tok: str, tema: str) -> str | None:
        return T.get(tok, {}).get(tema)

    def medir(tabla: dict, reglas: list, tema: str) -> int:
        malos = 0
        for tok, fondo, piso, uso in reglas:
            a = tabla.get(tok, {}).get(tema)
            b = tabla.get(fondo, {}).get(tema)
            if a is None or b is None:
                print(f"    ---- {tok} o {fondo} no existen en la hoja")
                malos += 1
                continue
            r = contraste(a, b)
            ok = r >= piso
            malos += 0 if ok else 1
            print(f"    {'OK  ' if ok else 'FALLA'} {r:6.2f}:1 (piso {piso})  "
                  f"{tok:22s} sobre {fondo:16s} {uso}")
        return malos

    # ---- 1. Contraste, token a token, en los dos temas
    for tema in ("claro", "oscuro"):
        print(f"\n  {tema.upper()}")
        fallos += medir(T, REGLAS, tema)
        # Blanco sobre la marca: es donde va el título de la cabecera.
        r = contraste("#ffffff", val("--marca", tema))
        ok = r >= 4.5
        fallos += 0 if ok else 1
        print(f"    {'OK  ' if ok else 'FALLA'} {r:6.2f}:1 (piso 4.5)  "
              f"{'blanco':22s} sobre {'--marca':16s} título de cabecera")

    # ---- 1b. Los suelos de banda, que no son :root
    print("\n  BANDA PAPEL-2 (segundo suelo, admite figuras)")
    for tema in ("claro", "oscuro"):
        print(f"    · {tema}")
        fallos += medir(T, REGLAS_BANDA_PAPEL_2, tema)

    # La banda de contraste es oscura en LOS DOS temas, así que hay que medirla
    # en los dos: en claro es donde un token que la banda no redefine se queda
    # con su valor claro y termina cayendo sobre un suelo oscuro.
    print("\n  BANDA DE CONTRASTE (redefine sus tokens en su ámbito)")
    B = leer_ambito(".banda-contraste")
    for tema in ("claro", "oscuro"):
        print(f"    · {tema}")
        fallos += medir(B, REGLAS, tema)

    # ---- 2. Separación dato ↔ advertencia
    print("\n  SEPARACIÓN DATO ↔ ADVERTENCIA (OKLab ΔE)")
    for tema in ("claro", "oscuro"):
        d = delta_e(val("--serie-1", tema), val("--aviso-borde", tema))
        ok = d >= PISO_DE
        fallos += 0 if ok else 1
        print(f"    {'OK  ' if ok else 'FALLA'} ΔE {d:5.1f} (piso {PISO_DE:.0f})  {tema}")

    # ---- 3. Rampa ordinal: separación y monotonía
    print("\n  RAMPA ORDINAL Q1–Q4")
    for tema in ("claro", "oscuro"):
        cols = [val(t, tema) for t in RAMPA]
        pasos = [delta_e(a, b) for a, b in zip(cols, cols[1:])]
        lums = [luminancia(c) for c in cols]
        monotona = (all(x < y for x, y in zip(lums, lums[1:]))
                    or all(x > y for x, y in zip(lums, lums[1:])))
        ok = min(pasos) >= PISO_ESCALON and monotona
        fallos += 0 if ok else 1
        print(f"    {'OK  ' if ok else 'FALLA'} paso mínimo ΔE {min(pasos):5.1f} "
              f"(piso {PISO_ESCALON:.0f}) · luminosidad {'monótona' if monotona else 'NO MONÓTONA'}  {tema}")

    # ---- 4. El par categórico en uso, bajo daltonismo
    print("\n  PAR CATEGÓRICO EN USO (anillo C-01) BAJO DALTONISMO")
    for tema in ("claro", "oscuro"):
        a, b = (val(t, tema) for t in PAR_CATEGORICO)
        medidas = {"normal": delta_e(a, b)}
        for tipo in ("protanopia", "deuteranopia", "tritanopia"):
            medidas[tipo] = delta_e(simular(a, tipo), simular(b, tipo))
        peor = min(medidas.values())
        ok = peor >= PISO_ESCALON
        fallos += 0 if ok else 1
        detalle = " · ".join(f"{k} {v:.1f}" for k, v in medidas.items())
        print(f"    {'OK  ' if ok else 'FALLA'} peor caso ΔE {peor:5.1f} "
              f"(piso {PISO_ESCALON:.0f})  {tema}")
        print(f"           {detalle}")

    print("\n" + "=" * 78)
    if fallos:
        print(f"{fallos} FALLO(S) · el sistema cromático NO es válido")
        sys.exit(1)
    print("SISTEMA CROMÁTICO VÁLIDO")


if __name__ == "__main__":
    main()
