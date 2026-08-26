"""Aplica las respuestas de `internal/validacion_unidades.html` a
`config/matching_rules.yml` (T-02).

QUÉ HACE
    Lee `internal/unit_validation_decisions.csv` (exportado por la
    herramienta interactiva) y edita `config/matching_rules.yml` en el
    lugar preciso que corresponde a cada respuesta:

      · Jerarquía confirmada  -> `estado: inferida` pasa a `confirmada`.
      · Jerarquía corregida   -> se cambia la `facultad` y se marca
                                 `confirmada`.
      · Unidad confirmada     -> no toca el archivo (ya está bien como está).
      · Unidad corregida      -> el nombre detectado se registra como
                                 VARIANTE del nombre correcto — nunca se
                                 borra, porque seguirá apareciendo en el
                                 origen y hay que seguir reconociéndolo.
      · Cuando TODAS las unidades y jerarquías quedan respondidas,
        `vocabulario_validado_por_institucion` pasa de `false` a `true`.

QUÉ NO HACE
    No usa `yaml.dump()`. Ese archivo lleva más comentarios de justificación
    que líneas de dato, y volcarlo de nuevo los borraría todos. Se edita el
    TEXTO con reemplazos anclados a un patrón exacto, y se valida que el
    resultado siga siendo YAML válido antes de escribirlo — nunca después.

CAPA
    Interna. Escribe en `config/`, que sí es la capa que usa el build; por
    eso valida dos veces (patrón encontrado, YAML parseable) antes de tocar
    el archivo, y deja un respaldo en `internal/.respaldos/`.

Uso:
    python3 src/review/apply_unit_validation.py [--dry-run]
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
CSV = ROOT / "internal" / "unit_validation_decisions.csv"
CONFIG = ROOT / "config" / "matching_rules.yml"
RESPALDOS = ROOT / "internal" / ".respaldos"


def leer_decisiones(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, comment="#").fillna("")
    faltan = {"id", "tipo", "nombre", "correcto", "correccion", "nota"} - set(df.columns)
    if faltan:
        sys.exit(f"El CSV no trae las columnas esperadas: faltan {sorted(faltan)}")
    return df


def bloque_vocabulario(texto: str, nombre: str) -> re.Match | None:
    """Encuentra el bloque `    "nombre":\\n      - "..."\\n...` de un canónico."""
    patron = r'^(    )"' + re.escape(nombre) + r'":\n((?:      - .*\n)+)'
    return re.search(patron, texto, re.MULTILINE)


def bloque_jerarquia(texto: str, escuela: str) -> re.Match | None:
    """Encuentra el bloque de una escuela en `jerarquia:`."""
    patron = (r'^(    )"' + re.escape(escuela) + r'":\n'
              r'(      facultad: "[^"]*"\n)'
              r'(      estado: \w+[^\n]*\n)')
    return re.search(patron, texto, re.MULTILINE)


def aplicar_jerarquia(texto: str, escuela: str, correcto: str, correccion: str,
                       fecha: str, cambios: list[str], avisos: list[str]) -> tuple[str, bool]:
    """Devuelve (texto_actualizado, quedó_confirmada)."""
    m = bloque_jerarquia(texto, escuela)
    if not m:
        avisos.append(f"jerarquía «{escuela}»: no se encontró su bloque en "
                       f"{CONFIG.relative_to(ROOT)} — revisar a mano")
        return texto, False

    ya_confirmada = "estado: confirmada" in m.group(3)
    if correcto == "si":
        if ya_confirmada:
            return texto, True
        nuevo = (m.group(1) + f'"{escuela}":\n' + m.group(2)
                 + f"      estado: confirmada        # confirmado por revisión humana, {fecha}\n")
        cambios.append(f"jerarquía «{escuela}»: inferida → confirmada")
        return texto[:m.start()] + nuevo + texto[m.end():], True

    if correcto == "no":
        if not correccion.strip():
            avisos.append(f"jerarquía «{escuela}»: marcada «no» pero sin corrección — "
                           "no se toca, sigue inferida")
            return texto, False
        nuevo = (m.group(1) + f'"{escuela}":\n'
                 + f'      facultad: "{correccion.strip()}"\n'
                 + f"      estado: confirmada        # corregido por revisión humana, {fecha}\n")
        cambios.append(f"jerarquía «{escuela}»: facultad corregida a «{correccion.strip()}» y confirmada")
        return texto[:m.start()] + nuevo + texto[m.end():], True

    return texto, ya_confirmada


def aplicar_unidad(texto: str, nombre: str, correcto: str, correccion: str,
                    cambios: list[str], avisos: list[str]) -> tuple[str, bool]:
    """Devuelve (texto_actualizado, quedó_registrada_o_confirmada)."""
    if correcto == "si":
        # No hace falta que exista como clave propia: si el dato ya sale bien
        # formado del extractor, confirmar «sí» no obliga a inventarle una
        # entrada de vocabulario que nadie necesita.
        return texto, True

    if correcto != "no":
        return texto, False

    destino = correccion.strip()
    if not destino:
        avisos.append(f"unidad «{nombre}»: marcada «no» pero sin corrección — no se toca")
        return texto, False

    if destino == nombre:
        avisos.append(f"unidad «{nombre}»: corrección igual al nombre original — no se toca")
        return texto, True

    m_destino = bloque_vocabulario(texto, destino)
    m_origen = bloque_vocabulario(texto, nombre)

    if m_destino:
        # El nombre correcto YA es una entrada: sólo falta que reconozca esta
        # forma como variante, si todavía no la tiene.
        variantes = m_destino.group(2)
        if f'- "{nombre}"' in variantes:
            cambios.append(f"unidad «{nombre}»: ya estaba registrada como variante de «{destino}»")
            return texto, True
        nuevo = variantes + f'      - "{nombre}"\n'
        cambios.append(f"unidad «{nombre}»: agregada como variante de «{destino}»")
        return texto[:m_destino.start(2)] + nuevo + texto[m_destino.end(2):], True

    if m_origen:
        # El nombre detectado ES una entrada propia, pero con el nombre
        # incorrecto: se renombra la clave y se conserva su lista de
        # variantes, agregando el nombre original como una variante más.
        variantes = m_origen.group(2)
        if f'- "{nombre}"' not in variantes:
            variantes = variantes + f'      - "{nombre}"\n'
        nuevo = m_origen.group(1) + f'"{destino}":\n' + variantes
        cambios.append(f"unidad «{nombre}»: renombrada a «{destino}» (conserva sus variantes)")
        texto = texto[:m_origen.start()] + nuevo + texto[m_origen.end():]
        # Si alguna jerarquía apuntaba a la facultad por el nombre viejo,
        # dejarla así sería una referencia a una clave que ya no existe.
        patron_ref = r'facultad: "' + re.escape(nombre) + r'"'
        n_refs = len(re.findall(patron_ref, texto))
        if n_refs:
            texto = re.sub(patron_ref, f'facultad: "{destino}"', texto)
            cambios.append(f"  · {n_refs} referencia(s) de jerarquía actualizada(s) a «{destino}»")
        return texto, True

    # Ninguno de los dos nombres tiene entrada propia: se crea una nueva,
    # con el nombre corregido como canónico y el detectado como variante.
    ancla = re.search(r'^  vocabulario:\n', texto, re.MULTILINE)
    if not ancla:
        avisos.append(f"unidad «{nombre}»: no se encontró el bloque `vocabulario:` — revisar a mano")
        return texto, False
    insercion = f'    "{destino}":\n      - "{destino}"\n      - "{nombre}"\n'
    cambios.append(f"unidad «{nombre}»: nueva entrada de vocabulario «{destino}», con «{nombre}» como variante")
    return texto[:ancla.end()] + insercion + texto[ancla.end():], True


FIXTURE = """unidad_academica:
  vocabulario_validado_por_institucion: false
  vocabulario:
    "Facultad de Ingeniería":
      - "Facultad de Ingeniería"
      - "Faculty of Engineering"
    "Facultad de Economía y Negocios":
      - "Facultad de Economía y Negocios"
  jerarquia:
    "Escuela de Kinesiología":
      facultad: "Facultad de Medicina"
      estado: confirmada        # usuario, sesión 2026-07-31
    "Escuela de Nutrición y Dietética":
      facultad: "Facultad de Medicina"
      estado: inferida          # aparece bajo Facultad de Medicina en las afiliaciones
    "Escuela de Enfermería":
      facultad: "Facultad de Medicina"
      estado: inferida
"""


def autotest() -> int:
    fallos = []

    def ok(cond, msg):
        if not cond:
            fallos.append(msg)

    fecha = "2026-08-26"

    # 1. Jerarquía ya confirmada + "sí": no cambia nada.
    t = FIXTURE
    t2, quedo = aplicar_jerarquia(t, "Escuela de Kinesiología", "si", "", fecha, [], [])
    ok(t2 == t, "confirmar una jerarquía ya confirmada no debería tocar el texto")
    ok(quedo, "debería quedar confirmada")

    # 2. Jerarquía inferida + "sí": pasa a confirmada.
    cambios = []
    t2, quedo = aplicar_jerarquia(t, "Escuela de Nutrición y Dietética", "si", "", fecha, cambios, [])
    ok("estado: confirmada" in t2 and 'facultad: "Facultad de Medicina"' in t2,
       "Nutrición debería quedar confirmada con la misma facultad")
    ok(len(cambios) == 1, "debería registrar un cambio")
    ok(yaml.safe_load(t2)["unidad_academica"]["jerarquia"]
       ["Escuela de Nutrición y Dietética"]["estado"] == "confirmada", "YAML resultante debe reflejar el cambio")

    # 3. Jerarquía inferida + "no" con corrección: cambia facultad y confirma.
    t2, quedo = aplicar_jerarquia(t, "Escuela de Enfermería", "no", "Facultad de Ingeniería", fecha, [], [])
    d = yaml.safe_load(t2)["unidad_academica"]["jerarquia"]["Escuela de Enfermería"]
    ok(d["facultad"] == "Facultad de Ingeniería" and d["estado"] == "confirmada",
       "Enfermería debería quedar con la facultad corregida y confirmada")

    # 4. Jerarquía "no" sin corrección: no toca nada y avisa.
    avisos = []
    t2, quedo = aplicar_jerarquia(t, "Escuela de Enfermería", "no", "", fecha, [], avisos)
    ok(t2 == t, "sin corrección no debería tocar el texto")
    ok(not quedo and len(avisos) == 1, "debería avisar y no quedar confirmada")

    # 5. Unidad "sí": no toca nada.
    t2, quedo = aplicar_unidad(t, "Facultad de Ingeniería", "si", "", [], [])
    ok(t2 == t and quedo, "confirmar una unidad no debería tocar el texto")

    # 6. Unidad "no", el destino YA existe como clave: se agrega como variante.
    t2, quedo = aplicar_unidad(t, "School of Civil Engineering", "no", "Facultad de Ingeniería", [], [])
    vocab = yaml.safe_load(t2)["unidad_academica"]["vocabulario"]
    ok("School of Civil Engineering" in vocab["Facultad de Ingeniería"],
       "debería aparecer como variante de Facultad de Ingeniería")
    ok(len(vocab) == 2, "no debería crear una clave nueva")

    # 7. Unidad "no", el ORIGEN existe como clave (nombre mal puesto): se renombra.
    t2, quedo = aplicar_unidad(t, "Facultad de Economía y Negocios", "no",
                                "Facultad de Economía, Negocios y Empresa", [], [])
    vocab = yaml.safe_load(t2)["unidad_academica"]["vocabulario"]
    ok("Facultad de Economía, Negocios y Empresa" in vocab, "debería existir la clave nueva")
    ok("Facultad de Economía y Negocios" in vocab["Facultad de Economía, Negocios y Empresa"],
       "el nombre viejo debería quedar como variante de la clave nueva")
    ok("Facultad de Economía y Negocios" not in vocab, "la clave vieja no debería sobrevivir")

    # 8. Unidad "no", ni origen ni destino existen: crea entrada nueva.
    t2, quedo = aplicar_unidad(t, "School of Medicine UFT-CLC", "no", "Instituto Nuevo", [], [])
    vocab = yaml.safe_load(t2)["unidad_academica"]["vocabulario"]
    ok("Instituto Nuevo" in vocab and "School of Medicine UFT-CLC" in vocab["Instituto Nuevo"],
       "debería crear una entrada nueva con la variante detectada")

    # 9. Renombrar una unidad que una jerarquía usa como facultad: la
    #    referencia debe actualizarse, o la jerarquía apuntaría a una clave
    #    que ya no existe.
    t3 = t.replace('facultad: "Facultad de Medicina"', 'facultad: "Facultad de Ingeniería"', 1)
    t3, _ = aplicar_unidad(t3, "Facultad de Ingeniería", "no", "Facultad de Ingeniería y Tecnología", [], [])
    ok('facultad: "Facultad de Ingeniería y Tecnología"' in t3,
       "la referencia de jerarquía al nombre viejo debería actualizarse al renombrar")

    # 10. Todo el resultado sigue siendo YAML válido en cada paso ya probado
    #     arriba (ya se parseó con yaml.safe_load en 2, 3, 6, 7, 8, 9 sin
    #     lanzar) — comprobación adicional sobre el texto completo sin tocar.
    try:
        yaml.safe_load(FIXTURE)
    except yaml.YAMLError:
        fallos.append("el fixture base ya no es YAML válido")

    for f in fallos:
        print(f"  FALLA  {f}")
    print(f"  {'OK' if not fallos else 'FALLOS'} · apply_unit_validation: "
          f"{10 - len(fallos)}/10 comprobaciones")
    return 1 if fallos else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--test", action="store_true", help="verifica la lógica con datos sintéticos, sin tocar nada")
    ap.add_argument("--dry-run", action="store_true", help="muestra qué haría, sin escribir nada")
    args = ap.parse_args()

    if args.test:
        return autotest()

    print("=" * 78)
    print("APLICAR LA VALIDACIÓN DE UNIDADES ACADÉMICAS")
    print("=" * 78)

    if not CSV.exists():
        sys.exit(f"Falta {CSV.relative_to(ROOT)}.\n"
                  "Se exporta desde internal/validacion_unidades.html "
                  "(se genera con `python3 src/review/build_unit_validation.py`).")

    d = leer_decisiones(CSV)
    pendientes = d[~d["correcto"].isin(["si", "no"])]
    respondidas = d[d["correcto"].isin(["si", "no"])]
    print(f"  filas leídas   : {len(d)}")
    print(f"    respondidas  : {len(respondidas)}")
    print(f"    pendientes   : {len(pendientes)}")

    texto = CONFIG.read_text(encoding="utf-8")
    fecha = datetime.now().strftime("%Y-%m-%d")
    cambios: list[str] = []
    avisos: list[str] = []

    todas_jerarquias_ok = True
    for _, r in d[d["tipo"] == "jerarquia"].iterrows():
        texto, ok = aplicar_jerarquia(texto, r["nombre"], r["correcto"], r["correccion"],
                                       fecha, cambios, avisos)
        todas_jerarquias_ok = todas_jerarquias_ok and ok

    todas_unidades_ok = True
    for _, r in d[d["tipo"] == "unidad"].iterrows():
        texto, ok = aplicar_unidad(texto, r["nombre"], r["correcto"], r["correccion"],
                                    cambios, avisos)
        todas_unidades_ok = todas_unidades_ok and ok

    # El vocabulario se declara validado sólo cuando TODO lo que la hoja
    # preguntó tiene respuesta. Marcarlo con preguntas sin contestar sería
    # publicar una confianza que nadie dio.
    if todas_jerarquias_ok and todas_unidades_ok and not len(pendientes):
        if 'vocabulario_validado_por_institucion: false' in texto:
            texto = texto.replace(
                'vocabulario_validado_por_institucion: false',
                'vocabulario_validado_por_institucion: true    '
                f'# confirmado por revisión humana, {fecha}')
            cambios.append("vocabulario_validado_por_institucion: false → true")
    else:
        avisos.append("vocabulario_validado_por_institucion sigue en false: "
                       f"quedan {len(pendientes)} fila(s) sin responder")

    print()
    if cambios:
        print("  CAMBIOS:")
        for c in cambios:
            print(f"    · {c}")
    else:
        print("  Sin cambios que aplicar.")
    if avisos:
        print("\n  AVISOS (revisar a mano):")
        for a in avisos:
            print(f"    ⚠ {a}")

    if not cambios:
        print("\n  Nada que escribir.")
        return 0

    # Se valida ANTES de escribir, no después: un YAML roto detectado tras
    # sobrescribir el archivo ya rompió el build.
    try:
        yaml.safe_load(texto)
    except yaml.YAMLError as e:
        sys.exit(f"\nEL RESULTADO NO ES YAML VÁLIDO. No se escribió nada.\n{e}")

    if args.dry_run:
        print("\n  --dry-run: no se escribió nada.")
        return 0

    RESPALDOS.mkdir(parents=True, exist_ok=True)
    respaldo = RESPALDOS / f"matching_rules_{datetime.now().strftime('%Y%m%dT%H%M%S')}.yml"
    respaldo.write_text(CONFIG.read_text(encoding="utf-8"), encoding="utf-8")
    CONFIG.write_text(texto, encoding="utf-8")

    print(f"\n  OK · {CONFIG.relative_to(ROOT)} actualizado")
    print(f"       Respaldo en {respaldo.relative_to(ROOT)}")
    print("\n  Próximo paso: python3 src/audit/run_all.py && "
          "python3 src/build/build_all.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
