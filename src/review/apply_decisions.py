"""Aplica las decisiones humanas exportadas por la herramienta de revisión.

QUÉ HACE
    Lee `internal/identity_decisions.csv` —lo que una persona decidió en
    `make revision`— y lo convierte en dos artefactos que el pipeline sí sabe
    consumir:

      config/identidades_consolidadas.yml   variantes declaradas la misma persona
      config/firmas_e09_resueltas.yml       firmas que no son personas
      config/orcid_revisado.yml             veredictos sobre asignaciones de ORCID
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
import yaml

if sys.platform == "win32":
    # La consola de Windows usa cp1252 por defecto, que no tiene "→": revienta
    # el print de cobertura antes de escribir las decisiones (mismo bug que
    # src/enrich/orcid_openalex.py).
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import decisiones as D
import equivalencia_ortografica as EQ

ROOT = Path(__file__).resolve().parents[2]
INTERNAL = ROOT / "internal"
ENRICHED = ROOT / "data" / "enriched"
CONFIG = ROOT / "config"

FUENTE_REVISION = "Revisión humana (candidato por afiliación confirmado)"
# Distinta de la anterior a propósito: aquella confirma un candidato que un
# conector había propuesto; ésta nace de que una persona fue a buscar al
# registro y encontró algo que ningún conector había visto. La evidencia no es
# la misma y la ficha no debe decir que sí.
FUENTE_BUSQUEDA = "Revisión humana (búsqueda manual en el registro)"

firmas_de = D.firmas_de


def leer_decisiones(path: Path) -> pd.DataFrame:
    d = D.leer(path)
    faltan = {"caso_id", "cola", "firmas", "veredicto"} - set(d.columns)
    if faltan:
        sys.exit(f"El CSV no tiene las columnas esperadas: faltan {sorted(faltan)}")
    return d


def grupos_de_identidad(d: pd.DataFrame,
                        ortograficos: list[list[str]] | None = None
                        ) -> tuple[list[list[str]], list[tuple]]:
    """Une por transitividad las firmas declaradas la misma persona.

    `ortograficos` son clases de equivalencia de CADENA, no de identidad: la
    misma firma escrita con otros diacríticos o separadores. Se unen aquí
    porque el resultado es el mismo grupo, pero su origen se registra aparte
    para que el archivo generado no las presente como algo que alguien
    verificó. Ver equivalencia_ortografica.py.

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

    for clase in (ortograficos or []):
        for a, b in itertools.pairwise(clase):
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



def casos_pendientes_variantes(d: pd.DataFrame) -> list[tuple[str, list[str]]]:
    """Los casos de la cola de variantes que nadie ha resuelto todavía."""
    sel = d[(d.cola == "Variantes de nombre") & (d.veredicto == "pendiente")]
    return [(r["caso_id"], firmas_de(r)) for _, r in sel.iterrows()]


def pares_declarados_distintos(d: pd.DataFrame) -> set[frozenset[str]]:
    """Pares que una persona declaró de personas distintas.

    Bloquean la fusión ortográfica: un veredicto humano manda sobre la
    normalización, siempre y en esa dirección.
    """
    pares = set()
    for _, r in d[d.veredicto == "distintas"].iterrows():
        for a, b in itertools.combinations(firmas_de(r), 2):
            pares.add(frozenset({a, b}))
    return pares


def origen_de_grupos(grupos: list[list[str]], d: pd.DataFrame) -> dict[int, str]:
    """Qué sostiene cada grupo: revisión humana, normalización, o las dos.

    Un grupo es «humana» si alguna decisión con veredicto «misma» tocó alguna
    de sus firmas. Si además hay formas que sólo entraron por equivalencia de
    cadena, es «mixta». Se registra porque el archivo generado se lee como
    evidencia, y una afirmación verificada y una normalizada no pueden verse
    igual.
    """
    humanas = set()
    for _, r in d[d.veredicto == "misma"].iterrows():
        humanas.update(firmas_de(r))
    origen = {}
    for i, g in enumerate(grupos):
        dentro = [f in humanas for f in g]
        origen[i] = ("humana" if all(dentro)
                     else "mixta" if any(dentro) else "ortografica")
    return origen


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

    NO TODO DIACRÍTICO CUENTA IGUAL. Contarlos a bulto elegía «Nùñez-Lisboa M.»
    frente a «Núñez-Lisboa M.»: las dos llevan dos marcas, empataban, y el
    desempate alfabético publicaba la forma con acento grave. En español el
    acento grave sobre vocal no existe; es la misma clase de corrupción de
    exportación que «Ingenierı́a». Así que las marcas del repertorio del español
    suman y las ajenas restan, y una forma corrupta no puede ganar por empate.
    """
    import unicodedata
    # agudo, tilde de eñe, diéresis: lo que el español escribe.
    ESPANOL = {"\u0301", "\u0303", "\u0308"}
    palabras = [t for t in firma.replace(".", " ").replace("-", " ").split()
                if len(t) > 1]
    marcas = [ch for t in palabras
              for ch in unicodedata.normalize("NFD", t)
              if unicodedata.category(ch) == "Mn"]
    return sum(1 if m in ESPANOL else -1 for m in marcas)


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


def asignaciones_confirmadas(d: pd.DataFrame, cand: pd.DataFrame | None,
                             cand_dspace: pd.DataFrame | None = None,
                             cand_autoarchivo: pd.DataFrame | None = None) -> pd.DataFrame:
    """Candidatos por afiliación o por alguno de los inventarios
    institucionales que la revisión confirmó como la misma persona."""
    cols = ["nombre_en_fuente", "orcid", "publicaciones_de_respaldo", "confianza", "fuente"]
    por_firma = {r["nombre_en_fuente"]: r["orcid"] for _, r in cand.iterrows()} if cand is not None else {}
    por_firma_dsp = ({r["nombre_en_fuente"]: r["orcid"] for _, r in cand_dspace.iterrows()}
                     if cand_dspace is not None else {})
    por_firma_aa = ({r["nombre_en_fuente"]: r["orcid"] for _, r in cand_autoarchivo.iterrows()}
                    if cand_autoarchivo is not None else {})
    if not por_firma and not por_firma_dsp and not por_firma_aa:
        return pd.DataFrame(columns=cols)

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

    # Mismo criterio para los candidatos por nombre en el repositorio
    # institucional (DSpace): otra fuente, mismo patrón de confirmación.
    for _, r in d[(d.veredicto == "misma")
                 & (d.cola.str.startswith("Candidato por repositorio institucional"))].iterrows():
        for f in firmas_de(r):
            if f in por_firma_dsp:
                filas.append({"nombre_en_fuente": f, "orcid": por_firma_dsp[f],
                              "publicaciones_de_respaldo": 0,
                              "confianza": "alta", "fuente": FUENTE_REVISION})

    # Idem para el inventario de autoarchivo de biblioteca.
    for _, r in d[(d.veredicto == "misma")
                 & (d.cola.str.startswith("Candidato por inventario de autoarchivo"))].iterrows():
        for f in firmas_de(r):
            if f in por_firma_aa:
                filas.append({"nombre_en_fuente": f, "orcid": por_firma_aa[f],
                              "publicaciones_de_respaldo": 0,
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


def resueltas_e09(d: pd.DataFrame, veredicto: str) -> list[tuple[str, str]]:
    """Firmas de la cola `E-09` resueltas con un veredicto, con su nota.

    Los DOS veredictos tienen efecto, y por razones distintas. «No es una
    persona» descarta la firma. «Sí es una persona» no descarta nada, pero
    tiene que sacarla de la cola igual: la auditoría la vuelve a marcar en cada
    corrida —se calcula sobre el log, que no se toca—, así que sin registrar la
    confirmación el sitio seguiría publicando que esa firma probablemente no es
    una persona para siempre, y la única salida que el sistema ofrecería sería
    declararla inexistente.

    La nota importa: dentro de un año, un veredicto sin más no permite saber si
    alguien lo comprobó contra la fuente o lo dio por evidente.
    """
    vistas: dict[str, str] = {}
    for _, r in d[d.veredicto == veredicto].iterrows():
        for f in firmas_de(r):
            # Por firma, no por (firma, nota): la misma firma decidida dos veces
            # —dos exportaciones concatenadas, una nota ampliada— duplicaría la
            # entrada e inflaría el recuento que se le imprime al operador.
            nota = str(r.get("nota") or "").strip()
            if f not in vistas or (not vistas[f] and nota):
                vistas[f] = nota
    return sorted(vistas.items())


def veredictos_orcid(d: pd.DataFrame, vigente: dict[str, str]) -> dict:
    """Traduce los cuatro veredictos de ORCID a lo que hay que escribir.

    LA ASIMETRÍA, QUE ES DELIBERADA
        Lo que se AÑADE va a `data/enriched/authors_orcid.csv`, igual que hace
        `asignaciones_confirmadas`: es dato nuevo, con su fuente declarada.

        Lo que se RETIRA no se borra de ahí. Se anota en `config/` y el build lo
        filtra, por la misma razón que las firmas de la cola E-09 no se borran
        del log: borrar la fila destruiría de dónde vino el dato, y además los
        conectores de enriquecimiento regeneran ese archivo —la próxima corrida
        de `orcid_crossref.py` devolvería la asignación retirada y nadie se
        enteraría—. Un filtro declarado sobrevive a la regeneración; un borrado,
        no.

    Devuelve las cuatro listas y los errores, sin decidir qué hacer con ellos.
    """
    conf: dict[str, tuple[str, str]] = {}
    ret: dict[str, tuple[str, str]] = {}
    sinreg: dict[str, str] = {}
    nuevas: list[dict] = []
    errores: list[str] = []
    avisos: list[str] = []

    # Retirar y reemplazar el ORCID de la MISMA firma en una sola corrida es
    # un caso real, no hipotético: una fuente nueva contradice la asignación
    # vigente Y propone la correcta a la vez. `vigente` se calculó ANTES de
    # esta corrida (viene de `authors_orcid.csv` en disco), así que sin este
    # ajuste "orcid_encontrado" vería la firma "ya asignada" con el valor que
    # la misma corrida está retirando, y se negaría a añadir el reemplazo. Se
    # calcula qué se va a retirar ANTES del bucle principal, y se usa una
    # copia de `vigente` sin esas firmas sólo para la rama "orcid_encontrado".
    firmas_retiradas_ahora = {
        f for _, r in d[d.veredicto == "orcid_incorrecto"].iterrows()
        for f in firmas_de(r) if f in vigente
    }
    vigente_para_nuevo = {f: v for f, v in vigente.items() if f not in firmas_retiradas_ahora}

    # NO ES LA PRIMERA VEZ QUE SE APLICA. `identity_decisions.csv` no borra
    # decisiones ya cumplidas (misma razón de siempre: es historial, no un
    # buzón de tareas). Si un retirar-y-reemplazar YA quedó reflejado en
    # `authors_orcid.csv` por una corrida anterior, `vigente` (leído de ese
    # mismo archivo) ya trae el ORCID NUEVO, no el viejo — y sin este chequeo
    # `orcid_incorrecto` retiraría el reemplazo correcto pensando que sigue
    # siendo el error original. Se detectó fusionando dos ramas que habían
    # aplicado la misma decisión de Arroyo A. por separado.
    propuestos_por_firma: dict[str, str] = {}
    for _, r in d[d.veredicto == "orcid_encontrado"].iterrows():
        propuesto = str(r.get("orcid_propuesto") or "").strip().upper()
        for f in firmas_de(r):
            propuestos_por_firma[f] = propuesto

    for _, r in d.iterrows():
        v = str(r.get("veredicto") or "")
        if not v.startswith("orcid_"):
            continue
        nota = str(r.get("nota") or "").strip()
        propuesto = str(r.get("orcid_propuesto") or "").strip().upper()
        for f in firmas_de(r):
            if v in ("orcid_correcto", "orcid_incorrecto"):
                actual = vigente.get(f)
                if not actual:
                    avisos.append(f"«{f}»: veredicto «{v}» pero hoy no tiene "
                                  "ninguna asignación vigente que confirmar o retirar")
                    continue
                if v == "orcid_incorrecto" and propuestos_por_firma.get(f) == actual:
                    avisos.append(f"«{f}»: el retiro ya está aplicado — lo vigente "
                                  f"hoy ({actual}) es el reemplazo, no el original. "
                                  "No se retira de nuevo.")
                    continue
                (conf if v == "orcid_correcto" else ret)[f] = (actual, nota)
            elif v == "orcid_encontrado":
                if f in vigente_para_nuevo:
                    avisos.append(f"«{f}»: se declara un ORCID encontrado a mano, "
                                  f"pero ya tiene asignado {vigente_para_nuevo[f]}. No se toca.")
                    continue
                if not propuesto:
                    errores.append(f"«{f}»: veredicto «orcid_encontrado» sin "
                                   "identificador en la columna orcid_propuesto")
                elif not D.orcid_valido(propuesto):
                    errores.append(f"«{f}»: «{propuesto}» no es un ORCID válido "
                                   "(forma o dígito de control)")
                else:
                    nuevas.append({"nombre_en_fuente": f, "orcid": propuesto,
                                   "publicaciones_de_respaldo": 0,
                                   "confianza": "alta", "fuente": FUENTE_BUSQUEDA,
                                   "nota": nota})
            elif v == "orcid_no_encontrado":
                sinreg[f] = nota

    # La misma firma confirmada y retirada son dos afirmaciones incompatibles
    # sobre una persona con nombre y apellido. No se desempata: se detiene.
    for f in sorted(set(conf) & set(ret)):
        errores.append(f"«{f}» se declara a la vez con el ORCID correcto y con "
                       "el ORCID equivocado")

    # «No encontrado en el registro» es ausencia de evidencia, no una
    # afirmación sobre un ORCID concreto — no pesa lo mismo que «correcto» o
    # «equivocado», que sí la tienen (D-341: convicción exige evidencia
    # dispositiva). Por eso NO se trata como la misma clase de contradicción
    # que conf∩ret: se desempata siempre a favor del veredicto con evidencia,
    # sin importar el orden temporal en que se registraron. Encontrado real:
    # «Dreyse J.» quedó en `sin_registro` (2026-08-26, búsqueda sin éxito) Y
    # en `confirmadas` (2026-09-01, ORCID 0000-0002-8201-5956 con URL de
    # respaldo) — dos filas reales de `identity_decisions.csv`, ninguna se
    # borra (es historial), pero sólo una debe gobernar lo publicado.
    for f in sorted((set(conf) | set(ret)) & set(sinreg)):
        avisos.append(f"«{f}»: figura como «no encontrado en el registro» y "
                       "también con un veredicto de ORCID correcto/equivocado "
                       "con evidencia — prevalece este último; se descarta el "
                       "«no encontrado»")
        del sinreg[f]

    return {"confirmadas": conf, "retiradas": ret, "sin_registro": sinreg,
            "nuevas": nuevas, "errores": errores, "avisos": avisos}


def yaml_orcid(v: dict, fecha: str) -> str:
    """Escrito a mano, como los otros dos: se lee tanto como se ejecuta."""
    lineas = [
        "# Veredictos humanos sobre asignaciones de ORCID.",
        "#",
        "# GENERADO por src/review/apply_decisions.py desde",
        "# internal/identity_decisions.csv. No editar a mano: se regenera.",
        "#",
        "# confirmadas   el ORCID vigente es de esta persona. No cambia el dato;",
        "#               cambia lo que la ficha declara sobre su respaldo.",
        "# retiradas     el ORCID vigente NO es de esta persona. El build deja de",
        "#               usarlo. La fila sigue en data/enriched/authors_orcid.csv",
        "#               a propósito: borrarla perdería de dónde vino, y el",
        "#               conector la repondría en la siguiente corrida.",
        "# sin_registro  alguien buscó en el registro y no encontró a esta",
        "#               persona. No es lo mismo que «nadie ha mirado».",
        "#",
        f"# Aplicado: {fecha}",
        "",
        f"fecha_de_aplicacion: {fecha}",
    ]
    for clave, entradas in (("confirmadas", v["confirmadas"]),
                            ("retiradas", v["retiradas"])):
        lineas.append(f"\n{clave}:")
        if not entradas:
            lineas[-1] = f"\n{clave}: []"
            continue
        for f, (orcid, nota) in sorted(entradas.items()):
            lineas.append(f"  - firma: {_escalar(f)}")
            lineas.append(f"    orcid: {_escalar(orcid)}")
            lineas.append(f"    nota: {_escalar(nota)}")
    lineas.append("\nsin_registro:" if v["sin_registro"] else "\nsin_registro: []")
    for f, nota in sorted(v["sin_registro"].items()):
        lineas.append(f"  - firma: {_escalar(f)}")
        lineas.append(f"    nota: {_escalar(nota)}")
    return "\n".join(lineas) + "\n"


def _escalar(v: str) -> str:
    """Comillas de YAML de verdad, no `repr()` de Python.

    `repr()` acierta casi siempre y falla justo donde duele: una nota con
    comilla simple y doble a la vez produce un escalar entrecomillado con
    barras invertidas que YAML 1.1 no desescapa. `DESCARTADAS` se evalúa al
    importar `common_build`, así que un archivo mal escrito no da un error
    localizado: mata todos los objetivos del build a la vez.
    """
    # Se vuelca como mapeo de una clave y se recorta la clave: un escalar suelto
    # sale con el marcador `...` de fin de documento pegado detrás. `width`
    # evita el plegado de líneas, que partiría una nota larga en dos y rompería
    # el formato de una línea por entrada.
    linea = yaml.safe_dump({"v": v}, allow_unicode=True, width=10**9,
                           default_flow_style=False).strip()
    return linea[len("v: "):]


def yaml_e09(descartadas: list[tuple[str, str]], confirmadas: list[tuple[str, str]],
             fecha: str) -> str:
    """Escrito a mano, por lo mismo que `yaml_consolidacion`: se lee tanto como
    se ejecuta, y un volcado automático perdería el porqué."""
    lineas = [
        "# Resolución humana de la cola E-09 — firmas sin forma de persona.",
        "#",
        "# GENERADO por src/review/apply_decisions.py desde",
        "# internal/identity_decisions.csv. No editar a mano: se regenera.",
        "#",
        "# POR QUÉ ESTÁN LAS DOS LISTAS",
        "#   La auditoría vuelve a marcar estas firmas en CADA corrida: se",
        "#   calcula sobre internal/matching_log.csv, que no se toca. Sin",
        "#   registrar también las confirmadas, decir «sí es una persona» no",
        "#   tendría ningún efecto y el sitio seguiría publicando que esa firma",
        "#   probablemente no lo es. La única salida sería declararla inexistente.",
        "#",
        "# QUÉ AUTORIZA `descartadas`",
        "#   Que esas formas de firma dejen de contarse como autores y dejen de",
        "#   tener ficha. Son fragmentos de cadena de afiliación que entraron en",
        "#   la lista de autores de la fuente («School of Psychology», «and",
        "#   Senior Lecturer»), detectados por la regla E-09.",
        "#",
        "# QUÉ AUTORIZA `confirmadas`",
        "#   Sólo cerrar el caso. La firma sigue contando y con ficha, igual que",
        "#   antes de la revisión: lo único que cambia es que deja de declararse",
        "#   como probable fragmento.",
        "#",
        "# QUÉ NO AUTORIZA NINGUNA DE LAS DOS",
        "#   Tocar internal/matching_log.csv. La detección institucional que las",
        "#   trajo es REAL: la publicación sí es de la UFT, lo que no es una",
        "#   persona es el nombre. Borrarlas del log dejaría a esas publicaciones",
        "#   sin ninguna detección y haría fallar la regla bloqueante I-01.",
        "#   El descarte se aplica aguas abajo, en src/build/common_build.py.",
        "#",
        "# CONSECUENCIA DECLARADA",
        "#   Las publicaciones donde una firma descartada era la única detección",
        "#   UFT quedan sin autoría UFT nombrada. Eso se declara; no se rellena",
        "#   con nada.",
        "#",
        f"# Descartadas: {len(descartadas)} · confirmadas como persona: {len(confirmadas)}",
        f"# Fecha de la revisión: {fecha}",
        "",
    ]
    for clave, firmas in (("descartadas", descartadas), ("confirmadas", confirmadas)):
        lineas.append(f"{clave}:")
        for f, nota in firmas:
            lineas.append(f"  - firma: {_escalar(f)}")
            if nota:
                lineas.append(f"    nota: {_escalar(nota)}")
    return "\n".join(lineas) + "\n"


def yaml_consolidacion(grupos: list[list[str]], fecha: str, n_dec: int,
                       frec: dict[str, int],
                       origen: dict[int, str] | None = None) -> str:
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
        "# EL ORIGEN DE CADA GRUPO va declarado:",
        "#   humana      una persona revisó y decidió que son la misma",
        "#   ortografica la MISMA firma escrita con otros diacríticos o",
        "#               separadores. No es un juicio sobre personas: es",
        "#               equivalencia de cadena. Ver equivalencia_ortografica.py",
        "#   mixta       las dos cosas dentro del mismo grupo",
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
    origen = origen or {}
    por_origen = {g_id: origen.get(g_id, "humana") for g_id in range(len(grupos))}
    orden = sorted(range(len(grupos)), key=lambda i: canonica(grupos[i], frec))
    for i in orden:
        g = grupos[i]
        lineas.append(f"  - canonica: {canonica(g, frec)!r}")
        lineas.append(f"    origen: {por_origen[i]}")
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
    casos.append(("un acento que el español no usa no gana el empate",
                  canonica(["Nuñez-Lisboa M.", "Nùñez-Lisboa M.",
                            "Núnez-Lisboa M.", "Núñez-Lisboa M."],
                           {}) == "Núñez-Lisboa M.", None))
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

    # 6 bis. Mismo criterio para los candidatos del repositorio institucional
    # (DSpace): otra fuente, misma lógica de confirmación, sin mezclarse.
    cand_dsp = pd.DataFrame([{"nombre_en_fuente": "Ríos T.", "orcid": "0000-Z"}])
    a = asignaciones_confirmadas(df([
        ("dspacecand-Ríos T.-0000-Z", "Candidato por repositorio institucional",
         "Ríos T.", "misma"),
        ("afil-López V.", "Candidato por afiliación", "López V.", "pendiente")]),
        cand, cand_dsp)
    casos.append(("candidato de DSpace confirmado se asigna",
                  list(a.nombre_en_fuente) == ["Ríos T."] and a.orcid.iloc[0] == "0000-Z",
                  a.to_dict("records")))
    casos.append(("las dos fuentes de candidatos no se cruzan entre sí",
                  "López V." not in set(a.nombre_en_fuente), None))

    # 7 bis. Mismo criterio para el inventario de autoarchivo — tercera
    # fuente, tampoco se cruza con las otras dos.
    cand_aa = pd.DataFrame([{"nombre_en_fuente": "Soto B.", "orcid": "0000-W"}])
    a = asignaciones_confirmadas(df([
        ("aacand-Soto B.-0000-W", "Candidato por inventario de autoarchivo",
         "Soto B.", "misma"),
        ("dspacecand-Ríos T.-0000-Z", "Candidato por repositorio institucional",
         "Ríos T.", "pendiente")]),
        cand, cand_dsp, cand_aa)
    casos.append(("candidato de autoarchivo confirmado se asigna",
                  list(a.nombre_en_fuente) == ["Soto B."] and a.orcid.iloc[0] == "0000-W",
                  a.to_dict("records")))

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
                  [f for f, _ in resueltas_e09(d9, "no_es_persona")]
                  == ["School of Psychology"], resueltas_e09(d9, "no_es_persona")))

    # 10. «es_persona» conserva la firma: decir que no es un fragmento no puede
    #     tener el mismo efecto que decir que lo es.
    casos.append(("es_persona no descarta",
                  "Gómez P." not in {f for f, _ in resueltas_e09(d9, "no_es_persona")},
                  None))

    # 10b. Pero SÍ se registra: sin eso, confirmar que una firma es una persona
    #      no tendría ningún efecto y la auditoría la volvería a marcar siempre.
    casos.append(("es_persona se registra igualmente",
                  [f for f, _ in resueltas_e09(d9, "es_persona")] == ["Gómez P."],
                  resueltas_e09(d9, "es_persona")))

    # 10c. Una firma decidida dos veces no se duplica, y gana la nota que dice algo.
    d10 = pd.DataFrame(
        [("a", "Firma sin forma de persona", "X", "no_es_persona", ""),
         ("b", "Firma sin forma de persona", "X", "no_es_persona", "comprobado en la fuente")],
        columns=["caso_id", "cola", "firmas", "veredicto", "nota"])
    casos.append(("una firma decidida dos veces no se duplica",
                  resueltas_e09(d10, "no_es_persona")
                  == [("X", "comprobado en la fuente")],
                  resueltas_e09(d10, "no_es_persona")))

    # 10d. El YAML se entrecomilla como YAML, no con repr() de Python: una nota
    #      con las dos comillas rompía el archivo y, con él, todo el build.
    dura = 'dice "School of X", no es persona'
    vuelta = yaml.safe_load(yaml_e09([("O'Brien \"Bob\" A.", dura)], [], "2026-01-01"))
    casos.append(("el YAML generado se relee intacto",
                  vuelta["descartadas"] == [{"firma": "O'Brien \"Bob\" A.", "nota": dura}]
                  and vuelta["confirmadas"] is None,
                  vuelta))

    # 11. Descartar una firma NO la mete en ningún grupo de identidad: son dos
    #     preguntas distintas y el veredicto de una no puede responder la otra.
    g, c = grupos_de_identidad(d9)
    casos.append(("descartar no consolida", g == [] and not c, (g, c)))

    # ── 12. Los cuatro veredictos de ORCID.
    def dfo(filas):
        return pd.DataFrame(filas, columns=["caso_id", "cola", "firmas", "veredicto",
                                            "orcid_propuesto", "nota"])

    VIG = {"Aedo S.": "0000-0001-5567-3374"}
    # ORCID reales por su dígito de control; el inválido es el mismo con el
    # último dígito cambiado, que es exactamente la errata que se comete.
    BUENO, MALO = "0000-0002-1825-0097", "0000-0002-1825-0098"

    v = veredictos_orcid(dfo([
        ("ver-Aedo S.", "ORCID sin confirmar", "Aedo S.", "orcid_correcto", "", "cotejado")]), VIG)
    casos.append(("orcid_correcto confirma la asignación vigente",
                  v["confirmadas"] == {"Aedo S.": ("0000-0001-5567-3374", "cotejado")}
                  and not v["errores"], v))

    v = veredictos_orcid(dfo([
        ("ver-Aedo S.", "ORCID sin confirmar", "Aedo S.", "orcid_incorrecto", "", "otra persona")]), VIG)
    casos.append(("orcid_incorrecto retira, no borra",
                  v["retiradas"] == {"Aedo S.": ("0000-0001-5567-3374", "otra persona")},
                  v))

    # Un veredicto sobre algo que ya no existe avisa y no aplica nada: es un CSV
    # viejo, no un error del operador, y abortar por eso bloquearía el resto.
    v = veredictos_orcid(dfo([
        ("ver-Fantasma Z.", "ORCID sin confirmar", "Fantasma Z.", "orcid_correcto", "", "")]), VIG)
    casos.append(("veredicto sobre firma sin asignación vigente avisa",
                  not v["confirmadas"] and not v["errores"] and len(v["avisos"]) == 1, v))

    v = veredictos_orcid(dfo([
        ("sinorcid-Dreyse J.", "Firma sin ORCID", "Dreyse J.", "orcid_encontrado", BUENO, "buscado")]), VIG)
    casos.append(("orcid_encontrado añade con su fuente propia",
                  len(v["nuevas"]) == 1 and v["nuevas"][0]["orcid"] == BUENO
                  and v["nuevas"][0]["fuente"] == FUENTE_BUSQUEDA and not v["errores"], v))

    v = veredictos_orcid(dfo([
        ("sinorcid-Dreyse J.", "Firma sin ORCID", "Dreyse J.", "orcid_encontrado", MALO, "")]), VIG)
    casos.append(("un dígito de control malo no se aplica",
                  not v["nuevas"] and len(v["errores"]) == 1, v))

    v = veredictos_orcid(dfo([
        ("sinorcid-Dreyse J.", "Firma sin ORCID", "Dreyse J.", "orcid_encontrado", "", "")]), VIG)
    casos.append(("orcid_encontrado sin identificador es un error",
                  not v["nuevas"] and len(v["errores"]) == 1, v))

    v = veredictos_orcid(dfo([
        ("a", "ORCID sin confirmar", "Aedo S.", "orcid_correcto", "", ""),
        ("b", "ORCID no verificable", "Aedo S.", "orcid_incorrecto", "", "")]), VIG)
    casos.append(("la misma firma correcta e incorrecta se detiene",
                  len(v["errores"]) == 1, v))

    v = veredictos_orcid(dfo([
        ("sinorcid-X", "Firma sin ORCID", "X", "orcid_no_encontrado", "", "no está")]), VIG)
    casos.append(("orcid_no_encontrado deja constancia de que se buscó",
                  v["sin_registro"] == {"X": "no está"}, v))

    # Retirar Y reemplazar la MISMA firma en una sola corrida (caso real:
    # Arroyo A., 2026-09-01). "vigente" trae el valor viejo porque se leyó
    # antes de esta corrida; la retirada tiene que "abrir hueco" para que
    # orcid_encontrado no se niegue a añadir el reemplazo en la misma pasada.
    v = veredictos_orcid(dfo([
        ("ver-Aedo S.", "ORCID sin confirmar", "Aedo S.", "orcid_incorrecto", "", "no es suyo"),
        ("nuevo-Aedo S.", "Firma sin ORCID", "Aedo S.", "orcid_encontrado", BUENO, "reemplazo")]), VIG)
    casos.append(("retirar y reemplazar la misma firma en una sola corrida",
                  v["retiradas"] == {"Aedo S.": ("0000-0001-5567-3374", "no es suyo")}
                  and len(v["nuevas"]) == 1 and v["nuevas"][0]["orcid"] == BUENO
                  and not v["errores"], v))

    # Volver a aplicar el MISMO par de decisiones una segunda vez, ya con el
    # reemplazo instalado como vigente (caso real: fusionar dos ramas que
    # habían corrido apply_decisions.py por separado sobre la decisión de
    # Arroyo A.). Sin el chequeo, esto "retira" el reemplazo correcto
    # pensando que sigue siendo el error original.
    v = veredictos_orcid(dfo([
        ("ver-Aedo S.", "ORCID sin confirmar", "Aedo S.", "orcid_incorrecto", "", "no es suyo"),
        ("nuevo-Aedo S.", "Firma sin ORCID", "Aedo S.", "orcid_encontrado", BUENO, "reemplazo")]),
        {"Aedo S.": BUENO})
    casos.append(("reaplicar un retirar-y-reemplazar ya vigente no se retira de nuevo",
                  not v["retiradas"] and len(v["avisos"]) == 1 and not v["errores"], v))

    # Pero confirmar Y "encontrar" a la vez para la misma firma sigue sin
    # tener sentido: confirmar dice que el vigente SÍ es correcto, así que no
    # hay hueco que abrir. orcid_encontrado se comporta igual que sin la
    # retirada: avisa y no toca nada.
    v = veredictos_orcid(dfo([
        ("ver-Aedo S.", "ORCID sin confirmar", "Aedo S.", "orcid_correcto", "", ""),
        ("nuevo-Aedo S.", "Firma sin ORCID", "Aedo S.", "orcid_encontrado", BUENO, "")]), VIG)
    casos.append(("confirmar no abre hueco para un reemplazo",
                  not v["nuevas"] and len(v["avisos"]) == 1, v))

    # 13. El YAML de ORCID se relee intacto, con una nota hostil.
    dura = 'dice \'no\' y "sí" a la vez: # 3'
    v = veredictos_orcid(dfo([
        ("a", "ORCID sin confirmar", "Aedo S.", "orcid_incorrecto", "", dura)]), VIG)
    vuelta = yaml.safe_load(yaml_orcid(v, "2026-01-01"))
    casos.append(("el YAML de ORCID se relee intacto",
                  vuelta["retiradas"] == [{"firma": "Aedo S.",
                                           "orcid": "0000-0001-5567-3374", "nota": dura}]
                  and vuelta["confirmadas"] == [] and vuelta["sin_registro"] == [],
                  vuelta))

    # 14. Los guardianes del vocabulario.
    casos.append(("un veredicto inventado se detecta",
                  D.veredictos_desconocidos(df([("x", "V", "A", "quizas")])) == ["quizas"],
                  None))
    casos.append(("un veredicto en la cola equivocada se detecta",
                  len(D.veredictos_fuera_de_cola(
                      df([("x", "ORCID sin confirmar", "A", "misma")]))) == 1, None))
    casos.append(("cada cola ofrece sólo veredictos que existen",
                  all(v in D.VOCABULARIO
                      for vs in list(D.COLAS.values()) + [D.POR_DEFECTO] for v in vs), None))

    # 15. La almohadilla de una nota ya no se come media línea.
    tmp = ROOT / "internal" / ".autotest_decisiones.csv"
    tmp.write_text('# cabecera\n# otra\ncaso_id,cola,firmas,veredicto,nota\n'
                   'x,V,A,misma,"cotejado con el registro #2, ok"\n', encoding="utf-8")
    leido = D.leer(tmp)
    tmp.unlink()
    casos.append(("una nota con almohadilla se lee entera",
                  leido.nota.iloc[0] == "cotejado con el registro #2, ok",
                  leido.nota.iloc[0]))

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

    # GUARDA DE VOCABULARIO. Antes esta línea filtraba con una lista de
    # veredictos escrita a mano: un veredicto que la página ofrecía y esta lista
    # no conocía se leía, se contaba como leído y no hacía nada. Ahora la lista
    # es el vocabulario compartido, y lo que no esté en él detiene la aplicación
    # nombrándolo en vez de ignorarlo.
    desconocidos = D.veredictos_desconocidos(d)
    if desconocidos:
        sys.exit(f"El CSV trae veredictos que este programa no sabe aplicar: "
                 f"{desconocidos}\nVeredictos válidos: {sorted(D.VOCABULARIO)}\n"
                 "No se aplica nada.")
    fuera = D.veredictos_fuera_de_cola(d)
    if fuera:
        print("\n  VEREDICTOS QUE NO CORRESPONDEN A SU COLA:")
        for cid, cola, v in fuera:
            print(f"    {cid}: «{v}» en la cola «{cola}»")
        sys.exit("\nSólo puede venir de un CSV editado a mano o de dos "
                 "exportaciones de versiones distintas. No se aplica nada.")

    resueltas = d[d.veredicto.isin(set(D.VOCABULARIO) - {"pendiente"})]
    print(f"  decisiones leídas   : {len(d)}")
    print(f"    resueltas         : {len(resueltas)}")
    print(f"    pendientes        : {int((d.veredicto == 'pendiente').sum())}")

    # EQUIVALENCIA ORTOGRÁFICA. No decide identidades: reconoce que la fuente
    # escribió la misma firma de varias maneras. Se calcula sólo sobre lo que
    # sigue pendiente y nunca contra un veredicto humano de «distintas».
    prohibidos = pares_declarados_distintos(d)
    eq_res, eq_resp = EQ.resolver(casos_pendientes_variantes(d), prohibidos)
    ortograficos = [clase for _, clase in eq_res]
    if ortograficos:
        print(f"\n  equivalencia ortográfica: {len(ortograficos)} clase(s), "
              f"{sum(len(c) for c in ortograficos)} formas de firma")
        for cid, clase in eq_res:
            print(f"    {cid}: {' = '.join(clase)}")
    if eq_resp:
        print(f"\n  NO fusionadas por veredicto humano de «distintas»: {len(eq_resp)}")
        for cid, clase in eq_resp:
            print(f"    {cid}: {' | '.join(clase)}")

    grupos, conflictos = grupos_de_identidad(d, ortograficos)
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
    desc = resueltas_e09(d, "no_es_persona")
    conf = resueltas_e09(d, "es_persona")
    en_grupos = {f for g in grupos for f in g}
    choque = sorted({f for f, _ in desc} & en_grupos)
    if choque:
        print("\n  CONTRADICCIONES:")
        for f in choque:
            print(f"    «{f}» se declara «no es una persona» y a la vez se fusiona "
                  "con otra firma como la misma persona")
        sys.exit("\nNo se aplica nada. Resuelva la contradicción y vuelva a exportar.")

    # Un veredicto sobre una fila sin firmas no descarta nada y no lo diría:
    # el operador vería «firmas descartadas: 0» y un código de salida cero.
    vacias = [r["caso_id"] for _, r in d[d.veredicto.isin(["no_es_persona", "es_persona"])].iterrows()
              if not firmas_de(r)]
    if vacias:
        print(f"\n  AVISO · {len(vacias)} decisión(es) de la cola E-09 sin ninguna "
              "firma asociada, que no se pueden aplicar:")
        for cid in vacias:
            print(f"    {cid}")

    print(f"  firmas descartadas  : {len(desc)} (probables fragmentos)")
    print(f"  confirmadas persona : {len(conf)} (se conservan, salen de la cola)")

    cpath = INTERNAL / "orcid_candidatos_afiliacion.csv"
    cand = pd.read_csv(cpath, dtype=str) if cpath.exists() else None
    dspath = INTERNAL / "dspace_candidatos.csv"
    cand_dspace = pd.read_csv(dspath, dtype=str) if dspath.exists() else None
    aapath = INTERNAL / "autoarchivo_candidatos.csv"
    cand_autoarchivo = pd.read_csv(aapath, dtype=str) if aapath.exists() else None
    nuevas = asignaciones_confirmadas(d, cand, cand_dspace, cand_autoarchivo)

    opath = ENRICHED / "authors_orcid.csv"
    vig = pd.read_csv(opath, dtype=str)
    vigente = dict(zip(vig.nombre_en_fuente, vig.orcid))

    orc = veredictos_orcid(d, vigente)
    for a in orc["avisos"]:
        print(f"\n  AVISO · {a}")
    if orc["errores"]:
        print("\n  NO SE PUEDE APLICAR:")
        for e in orc["errores"]:
            print(f"    {e}")
        sys.exit("\nCorrija el CSV y vuelva a intentarlo. No se aplica nada.")

    halladas = pd.DataFrame(
        [{k: v for k, v in n.items() if k != "nota"} for n in orc["nuevas"]],
        columns=list(nuevas.columns))
    nuevas = pd.concat([nuevas, halladas], ignore_index=True)
    nuevas = nuevas.drop_duplicates("nombre_en_fuente")

    # Reemplazo, no duplicado. `nuevas` sólo puede traer una firma que YA
    # está en `vig` cuando `veredictos_orcid` la dejó pasar precisamente
    # porque esta misma corrida la retiró (ver el comentario de
    # `vigente_para_nuevo` más arriba): esa fila vieja hay que QUITARLA de
    # `vig` antes de escribir —`vig_efectiva`—, o quedarían dos filas para
    # la misma persona. Lo que sí sigue siendo un duplicado genuino es
    # cualquier otra coincidencia entre `nuevas` y lo que queda en
    # `vig_efectiva`, y ésas se filtran de `nuevas`.
    reemplazadas = set(nuevas.nombre_en_fuente) & set(vig.nombre_en_fuente)
    vig_efectiva = vig[~vig.nombre_en_fuente.isin(reemplazadas)]
    nuevas = nuevas[~nuevas.nombre_en_fuente.isin(set(vig_efectiva.nombre_en_fuente))]

    print(f"  ORCID confirmados   : {len(orc['confirmadas'])} asignaciones que "
          "una persona respalda")
    print(f"  ORCID retirados     : {len(orc['retiradas'])} que el build dejará "
          "de usar")
    print(f"  buscados sin éxito  : {len(orc['sin_registro'])} firmas sin registro")
    print(f"  asignaciones nuevas : {len(nuevas)} "
          f"({len(halladas)} de búsqueda manual)")
    efectiva = len(vig) + len(nuevas) - len(orc["retiradas"])
    print(f"  cobertura           : {len(vig)} → {efectiva} "
          "(asignaciones que el build usará)")

    if args.dry_run:
        print("\n  --dry-run: no se ha escrito nada.")
        return 0

    frec = frecuencias(INTERNAL / "matching_log.csv")
    hoy = date.today().isoformat()
    (CONFIG / "identidades_consolidadas.yml").write_text(
        yaml_consolidacion(grupos, hoy, len(d), frec, origen_de_grupos(grupos, d)), encoding="utf-8")
    (CONFIG / "firmas_e09_resueltas.yml").write_text(
        yaml_e09(desc, conf, hoy), encoding="utf-8")
    (CONFIG / "orcid_revisado.yml").write_text(
        yaml_orcid(orc, hoy), encoding="utf-8")

    if len(nuevas):
        salida = pd.concat([vig_efectiva, nuevas], ignore_index=True)
        salida = salida.sort_values("nombre_en_fuente", kind="stable")
        salida.to_csv(opath, index=False, encoding="utf-8")

    print(f"\n  OK · config/identidades_consolidadas.yml")
    print(f"       config/firmas_e09_resueltas.yml   "
          f"({len(desc)} descartadas · {len(conf)} confirmadas)")
    print(f"       config/orcid_revisado.yml        "
          f"({len(orc['confirmadas'])} confirmadas · {len(orc['retiradas'])} "
          f"retiradas · {len(orc['sin_registro'])} sin registro)")
    if len(nuevas):
        print(f"       data/enriched/authors_orcid.csv  (+{len(nuevas)})")
    print("\n  Reconstruya el sitio para que surta efecto:  make sitio")
    return 0


if __name__ == "__main__":
    sys.exit(main())
