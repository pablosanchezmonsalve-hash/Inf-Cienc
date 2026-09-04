"""Señales automáticas que ARGUMENTAN cada caso de la cola PD-04, sin decidirlo.

POR QUÉ EXISTE
    La cola de `PD-04` trae 1.967 obras, 322 de ellas en la ventana. Revisar
    cada una exigía abrir el DOI para averiguar cosas que el proyecto YA SABE:
    si el ORCID por el que apareció es de confianza alta o media, si la
    afiliación que la propia fuente declara para esa firma nombra a la
    institución o a otra, y si el título ya está en el corpus con otro DOI.

    Ese trabajo es mecánico y repetirlo 322 veces a mano es lo que hace que
    una cola no se empiece nunca.

LA LÍNEA QUE NO SE CRUZA
    Estas señales NO deciden y NO se guardan como veredicto. No hay
    autoaprobación, ni un umbral que marque casos por su cuenta: cada obra
    sigue necesitando que una persona pulse uno de los cuatro botones, que es
    lo único que la convierte en Nivel V (Regla 1 de
    `docs/METODOLOGIA_FUERA_DE_SCOPUS.md`). Si el recuento saliera de un
    filtro automático sería Nivel D, y `PD-04` dejaría de ser lo que dice ser.

    Lo que hacen es poner delante el hecho comprobable para que la decisión
    cueste una lectura en vez de una investigación.

LAS CUATRO SEÑALES
    identificador  Qué ORCID sostiene el vínculo, y con qué confianza lo
                   sostiene el proyecto. Una obra hallada por un ORCID de
                   confianza `alta` llega por identificador; una de confianza
                   `media` llega por una asignación que este proyecto marcó
                   como probable, no como cierta (`D-08`).

    afiliación     Qué institución declara la FUENTE para esa persona EN ESA
                   OBRA. Es la señal de mayor rendimiento de las cuatro: la
                   consulta por ORCID en Europe PMC devuelve toda la obra de
                   una persona, incluida la que firmó en otra institución, y
                   la producción institucional se define por la afiliación de
                   la firma, no por dónde trabaja hoy quien firma.

    título/corpus  El mismo título, ya en el universo Scopus, con OTRO DOI.
                   El cribado por DOI no puede verlo: un preprint y su versión
                   publicada son dos DOI. Es el indicio típico de «otra
                   versión de una obra ya contada».

    título/cola    El mismo título repetido dentro de la propia cola. Zenodo
                   acuña un DOI por versión de un depósito: una obra con tres
                   versiones aparece tres veces, y una de ellas —a lo sumo—
                   puede contarse.

CAPA
    Interna. Ninguna de estas columnas llega a `dist/`.

Uso:
    python3 src/review/senales_obras_externas.py --test
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(ROOT / "src" / "audit"))
import common as c  # noqa: E402

# El mapa ORCID→firma se lee del conector, no se reimplementa: allí vive la
# regla de qué ORCID sigue vigente y cuál retiró una decisión humana. Dos
# copias de esa regla significan que un ORCID retirado vuelva por la puerta
# de atrás en cuanto una de las dos se quede vieja.
sys.path.insert(0, str(ROOT / "src" / "enrich"))
from obras_externas import orcid_vigentes  # noqa: E402

UNIVERSO = ROOT / "data" / "interim" / "publications_universe.csv"

# Un título corto normaliza a poca cosa ("Editorial", "Introduction") y
# colisionaría con cualquier otro igual de corto. Por debajo de este umbral
# la señal de título se declara no aplicable en vez de arriesgar un falso
# positivo que empuje a marcar «otra versión» una obra distinta.
MINIMO_TITULO = 20

COLUMNAS = ["s_identificador", "s_firma", "s_afiliacion", "s_titulo_corpus",
            "s_titulo_cola", "s_fuerza", "s_tokens"]


def normalizar(texto: str) -> str:
    """Minúsculas, sin acentos y sin puntuación, para comparar títulos.

    Las mismas palabras con distinta puntuación o mayúsculas son el mismo
    título; sin normalizar, «COVID-19: a review» y «Covid 19 a review» no se
    cruzarían nunca.
    """
    s = unicodedata.normalize("NFKD", str(texto or ""))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).casefold()
    return " ".join(re.sub(r"[^0-9a-z]+", " ", s).split())


def confirmados() -> dict[str, dict]:
    """ORCID vigente → firma y confianza con que el proyecto lo sostiene."""
    return {v["orcid"]: {"firma": v.get("firma", ""), "confianza": v.get("confianza", "")}
            for v in orcid_vigentes()}


def variantes_institucion() -> list[str]:
    """Cadenas normalizadas que, si aparecen, nombran a la institución foco.

    Salen de `config/institution.yml`, nunca escritas en el código: otra
    institución cambia ese archivo y esta señal sigue funcionando
    (guardarraíl de replicabilidad de `CLAUDE.md`).
    """
    inst = c.load_config("institution.yml")["institucion"]
    brutas = [inst.get("nombre_canonico", ""), inst.get("ror_id", ""), inst.get("isni", "")]
    return [n for n in (normalizar(b) for b in brutas) if len(n) >= 6]


def titulos_del_universo() -> dict[str, str]:
    """Título normalizado → el DOI o EID con que el corpus ya lo cuenta."""
    if not UNIVERSO.exists():
        return {}
    df = pd.read_csv(UNIVERSO, dtype=str).fillna("")
    fuera = {}
    for _, r in df.iterrows():
        k = normalizar(r.get("titulo", ""))
        if len(k) >= MINIMO_TITULO and k not in fuera:
            fuera[k] = (r.get("doi") or r.get("eid") or "").strip()
    return fuera


def _identificador(fila, orcids: dict[str, dict]) -> tuple[str, str]:
    """Qué ORCID vigente sostiene esta fila, y con qué confianza.

    Dos caminos llegan al mismo sitio. La vía `orcid` consultó un ORCID que
    el proyecto sostiene, y es él. La vía `afiliacion` llegó por una cadena
    de texto, pero si la fuente declara para ese autor un ORCID que el
    proyecto también sostiene, el vínculo deja de ser una cadena suelta y
    pasa a ser un identificador: eso hay que decirlo, porque cambia por
    completo la fuerza del caso.
    """
    candidatos = []
    if "orcid" in str(fila.get("via") or ""):
        candidatos += [v.strip() for v in str(fila.get("consulta") or "").split("|")]
    candidatos.append(str(fila.get("orcid_en_la_fuente") or "").rstrip("/").split("/")[-1])
    for o in candidatos:
        if o and o in orcids:
            return orcids[o].get("confianza", "") or "sin declarar", orcids[o].get("firma", "")
    return "", ""


def _afiliacion(fila, variantes: list[str]) -> str:
    """Si la afiliación que la fuente declara en ESA obra es la institución.

    Tres estados, y el tercero no es el segundo: «la fuente no declara
    afiliación» es un dato ausente, y tratarlo como «declara otra» sería
    inventar evidencia en contra.
    """
    declarada = normalizar(fila.get("afiliacion_declarada") or "")
    if not declarada:
        return "sin dato"
    return "institucion" if any(v in declarada for v in variantes) else "otra"


def calcular(df: pd.DataFrame, orcids: dict[str, dict] | None = None,
             variantes: list[str] | None = None,
             universo: dict[str, str] | None = None) -> pd.DataFrame:
    """Añade las columnas de señal a la cola. No toca ninguna columna existente.

    Los tres insumos se pueden inyectar para poder probar la función sin
    depender de los datos del repositorio.
    """
    orcids = confirmados() if orcids is None else orcids
    variantes = variantes_institucion() if variantes is None else variantes
    universo = titulos_del_universo() if universo is None else universo

    claves = [normalizar(t) for t in df.get("titulo", pd.Series([""] * len(df)))]
    repetidos = pd.Series(claves).value_counts()

    filas = []
    for (_, fila), k in zip(df.iterrows(), claves):
        confianza, firma = _identificador(fila, orcids)
        afiliacion = _afiliacion(fila, variantes)
        largo = len(k) >= MINIMO_TITULO
        en_corpus = universo.get(k, "") if largo else ""
        en_corpus = en_corpus or ("sí" if largo and k in universo else "")
        n_cola = int(repetidos.get(k, 0)) - 1 if largo else 0

        # Orden de revisión, no veredicto: qué mirar primero. La corroboración
        # entre fuentes pesa más que el identificador porque es evidencia
        # independiente; la afiliación pesa porque es la definición misma de
        # producción institucional.
        #
        # La repetición dentro de la cola NO resta aquí: de eso se ocupa
        # `depurar_repetidos`, y penalizar además a la superviviente sería
        # castigarla por un duplicado que ya no está.
        fuerza = (2 * int(bool(str(fila.get("corroborada_por") or "")))
                  + 2 * int(afiliacion == "institucion")
                  - int(afiliacion == "otra")
                  + int(confianza == "alta")
                  - 2 * int(bool(en_corpus)))

        tokens = " ".join(filter(None, [
            f"sig-orcid-{confianza}" if confianza else "sig-sin-identificador",
            f"sig-afiliacion-{afiliacion.replace(' ', '-')}",
            "sig-titulo-en-corpus" if en_corpus else "",
            "sig-titulo-repetido" if n_cola > 0 else "",
        ]))

        filas.append({"s_identificador": confianza, "s_firma": firma,
                      "s_afiliacion": afiliacion, "s_titulo_corpus": en_corpus,
                      "s_titulo_cola": n_cola, "s_fuerza": fuerza, "s_tokens": tokens})

    return df.assign(**{col: [f[col] for f in filas] for col in COLUMNAS})


def depurar_repetidos(df: pd.DataFrame, preferencia, protegidas=None) -> pd.DataFrame:
    """Regla de título repetido: de cada título, una sola fila queda revisable.

    POR QUÉ ES ARITMÉTICA Y NO CRITERIO
        Zenodo acuña un DOI por versión de un depósito, además del DOI de
        concepto; dos repositorios pueden traer la misma obra con DOI
        distintos. Son varias filas para UNA obra, y de todas ellas a lo sumo
        una puede contarse. Decidir las demás a mano no añade información:
        la respuesta ya está determinada por la primera.

        Es la asimetría que permite aplicarla en bloque. Una regla que
        DESCARTA sólo puede dejar el recuento corto, y quedarse corto se
        declara. Una regla que ACEPTA lo infla, y por eso el «sí» sigue
        costando un clic humano por obra.

    QUIÉN SOBREVIVE
        La de mayor `preferencia` —la calcula quien llama, normalmente la
        ventana temporal por delante de la fuerza de las señales—, y a
        igualdad, la más reciente y luego el orden de identificador. El
        criterio es determinista a propósito: la misma cola debe elegir
        siempre la misma superviviente, o las decisiones ya tomadas dejarían
        de corresponder con las filas al regenerar.

    LO QUE LA REGLA NO PUEDE TOCAR
        Una fila que ya lleva veredicto humano nunca se desplaza. El orden de
        precedencia de `CLAUDE.md` pone la decisión explícita por encima de
        cualquier regla, y una regla que borrase trabajo ya hecho sería
        justamente eso.

    Añade `s_duplicada` (1 si la desplaza la regla) y `s_sobrevive`, el
    identificador de la fila que la desplaza, para que el descarte sea
    auditable y no un silencio.
    """
    protegidas = set(protegidas or ())
    claves = [normalizar(t) for t in df.get("titulo", pd.Series([""] * len(df)))]
    pref = list(preferencia)
    ids = [f"{f} · {i}" for f, i in zip(df.get("fuente", [""] * len(df)),
                                        df.get("id_fuente", [""] * len(df)))]
    anios = [str(a or "") for a in df.get("anio", [""] * len(df))]

    grupos: dict[str, list[int]] = {}
    for n, k in enumerate(claves):
        if len(k) >= MINIMO_TITULO:
            grupos.setdefault(k, []).append(n)

    duplicada = [0] * len(df)
    sobrevive = [""] * len(df)
    for filas in grupos.values():
        if len(filas) < 2:
            continue
        decididas = [n for n in filas if ids[n] in protegidas]
        # Con veredicto humano de por medio, la regla se aparta entera: no
        # desplaza las decididas ni elige por encima de ellas.
        if decididas:
            for n in filas:
                if n not in decididas:
                    duplicada[n], sobrevive[n] = 1, ids[decididas[0]]
            continue
        elegida = max(filas, key=lambda n: (pref[n], anios[n], ids[n]))
        for n in filas:
            if n != elegida:
                duplicada[n], sobrevive[n] = 1, ids[elegida]

    return df.assign(s_duplicada=duplicada, s_sobrevive=sobrevive)


def autotest() -> int:
    casos = []

    def caso(n, ok, obs=None):
        casos.append((n, ok, obs))

    orcids = {"0000-0001-0000-0001": {"firma": "Pérez A.", "confianza": "alta"},
              "0000-0002-0000-0002": {"firma": "Soto B.", "confianza": "media"}}
    variantes = ["universidad finis terrae", "0225snd59"]
    universo = {"un titulo suficientemente largo para el umbral": "10.1000/ya"}

    df = pd.DataFrame([
        # 0 · ORCID alta + afiliación institucional + corroborada
        {"titulo": "Estudio clinico sobre una cohorte amplia", "via": "orcid",
         "consulta": "0000-0001-0000-0001", "orcid_en_la_fuente": "0000-0001-0000-0001",
         "afiliacion_declarada": "Facultad de Medicina, Universidad Finis Terrae, Chile",
         "corroborada_por": "datacite"},
        # 1 · ORCID alta pero firmado en otra institución
        {"titulo": "Ensayo hecho durante una estancia en el extranjero", "via": "orcid",
         "consulta": "0000-0001-0000-0001", "orcid_en_la_fuente": "0000-0001-0000-0001",
         "afiliacion_declarada": "Karolinska Institutet, Stockholm", "corroborada_por": ""},
        # 2 · sólo cadena de afiliación, sin identificador
        {"titulo": "Trabajo hallado por la cadena institucional", "via": "afiliacion",
         "consulta": "Universidad Finis Terrae", "orcid_en_la_fuente": "",
         "afiliacion_declarada": "Universidad Finis Terrae", "corroborada_por": ""},
        # 3 · llegó por afiliación pero la fuente declara un ORCID vigente
        {"titulo": "Otro trabajo hallado por la cadena institucional", "via": "afiliacion",
         "consulta": "Universidad Finis Terrae",
         "orcid_en_la_fuente": "https://orcid.org/0000-0002-0000-0002",
         "afiliacion_declarada": "Universidad Finis Terrae", "corroborada_por": ""},
        # 4 · título ya contado en el corpus con otro DOI
        {"titulo": "Un título suficientemente largo para el umbral", "via": "orcid",
         "consulta": "0000-0001-0000-0001", "orcid_en_la_fuente": "0000-0001-0000-0001",
         "afiliacion_declarada": "Universidad Finis Terrae", "corroborada_por": ""},
        # 5 y 6 · dos versiones del mismo depósito dentro de la cola
        {"titulo": "Conjunto de datos de la cohorte version uno", "via": "orcid",
         "consulta": "0000-0002-0000-0002", "orcid_en_la_fuente": "0000-0002-0000-0002",
         "afiliacion_declarada": "", "corroborada_por": ""},
        {"titulo": "Conjunto de datos de la cohorte version uno", "via": "orcid",
         "consulta": "0000-0002-0000-0002", "orcid_en_la_fuente": "0000-0002-0000-0002",
         "afiliacion_declarada": "", "corroborada_por": ""},
        # 7 · título corto: la señal de título no aplica
        {"titulo": "Editorial", "via": "afiliacion", "consulta": "Universidad Finis Terrae",
         "orcid_en_la_fuente": "", "afiliacion_declarada": "Universidad Finis Terrae",
         "corroborada_por": ""},
    ])
    s = calcular(df, orcids, variantes, universo)

    caso("no se pierde ni se altera ninguna columna de la cola",
         list(df.columns) == list(s.columns)[:len(df.columns)] and len(s) == len(df))
    caso("la vía ORCID reporta la confianza con que el proyecto lo sostiene",
         s.loc[0, "s_identificador"] == "alta" and s.loc[0, "s_firma"] == "Pérez A.")
    caso("la afiliación institucional se reconoce dentro de una cadena larga",
         s.loc[0, "s_afiliacion"] == "institucion")
    caso("una obra del mismo ORCID firmada en otra institución se marca como tal",
         s.loc[1, "s_afiliacion"] == "otra")
    caso("sin ORCID vigente no se inventa identificador",
         s.loc[2, "s_identificador"] == "" and "sig-sin-identificador" in s.loc[2, "s_tokens"])
    caso("un ORCID vigente declarado por la fuente rescata la vía por afiliación",
         s.loc[3, "s_identificador"] == "media" and s.loc[3, "s_firma"] == "Soto B.")
    caso("la URL de ORCID se compara por el identificador, no por la cadena",
         s.loc[3, "s_identificador"] != "")
    caso("un título ya presente en el corpus se señala con el DOI que lo cuenta",
         s.loc[4, "s_titulo_corpus"] == "10.1000/ya")
    caso("dos versiones del mismo título se ven la una a la otra",
         s.loc[5, "s_titulo_cola"] == 1 and s.loc[6, "s_titulo_cola"] == 1)
    caso("un título por debajo del umbral no dispara señal de título",
         s.loc[7, "s_titulo_corpus"] == "" and s.loc[7, "s_titulo_cola"] == 0)
    caso("la afiliación ausente no se cuenta como afiliación ajena",
         s.loc[5, "s_afiliacion"] == "sin dato")
    caso("la fuerza ordena el caso más sólido por delante del más dudoso",
         s.loc[0, "s_fuerza"] > s.loc[2, "s_fuerza"] > s.loc[1, "s_fuerza"])
    caso("un duplicado probable cae al final aunque tenga buen identificador",
         s.loc[4, "s_fuerza"] < s.loc[0, "s_fuerza"])
    caso("los tokens permiten filtrar por señal desde el buscador",
         "sig-afiliacion-otra" in s.loc[1, "s_tokens"]
         and "sig-titulo-repetido" in s.loc[5, "s_tokens"])
    caso("normalizar iguala puntuación, acentos y mayúsculas",
         normalizar("COVID-19: una Revisión") == normalizar("covid 19 una revision"))
    caso("las variantes salen de la configuración, no del código",
         "universidad finis terrae" in variantes_institucion())

    # --- regla de título repetido -----------------------------------------
    d = pd.DataFrame([
        {"fuente": "zenodo", "id_fuente": "z1", "anio": "2024",
         "titulo": "Conjunto de datos de la cohorte longitudinal"},
        {"fuente": "zenodo", "id_fuente": "z2", "anio": "2024",
         "titulo": "Conjunto de datos de la cohorte longitudinal"},
        {"fuente": "zenodo", "id_fuente": "z3", "anio": "2024",
         "titulo": "Conjunto de datos de la cohorte longitudinal"},
        {"fuente": "datacite", "id_fuente": "d1", "anio": "2024", "titulo": "Editorial"},
        {"fuente": "datacite", "id_fuente": "d2", "anio": "2024", "titulo": "Editorial"},
        {"fuente": "europepmc", "id_fuente": "e1", "anio": "2024",
         "titulo": "Un trabajo que aparece una sola vez en la cola"},
    ])
    r = depurar_repetidos(d, preferencia=[0, 5, 1, 0, 0, 0])

    caso("de tres versiones del mismo título sólo una queda revisable",
         list(r["s_duplicada"])[:3] == [1, 0, 1])
    caso("sobrevive la de mayor preferencia, no la primera que llega",
         r.loc[0, "s_sobrevive"] == "zenodo · z2" and r.loc[2, "s_sobrevive"] == "zenodo · z2")
    caso("una obra que aparece una sola vez no la toca la regla",
         r.loc[5, "s_duplicada"] == 0 and r.loc[5, "s_sobrevive"] == "")
    caso("los títulos por debajo del umbral no se agrupan entre sí",
         r.loc[3, "s_duplicada"] == 0 and r.loc[4, "s_duplicada"] == 0)
    caso("la regla es determinista: dos corridas eligen la misma superviviente",
         list(depurar_repetidos(d, [0, 5, 1, 0, 0, 0])["s_sobrevive"])
         == list(r["s_sobrevive"]))
    caso("a igualdad de preferencia decide el orden, no el azar",
         list(depurar_repetidos(d, [0, 0, 0, 0, 0, 0])["s_duplicada"])[:3] == [1, 1, 0])

    prot = depurar_repetidos(d, preferencia=[0, 5, 1, 0, 0, 0], protegidas={"zenodo · z1"})
    caso("una fila ya decidida por una persona nunca la desplaza la regla",
         prot.loc[0, "s_duplicada"] == 0)
    caso("la decisión humana desplaza a las demás del grupo, aunque pesen más",
         prot.loc[1, "s_duplicada"] == 1 and prot.loc[1, "s_sobrevive"] == "zenodo · z1")

    fallos = [n for n, ok, _ in casos if not ok]
    for n, ok, obs in casos:
        print(f"  {'OK  ' if ok else 'FALLA'} {n}" + (f"  ({obs})" if not ok and obs else ""))
    print(f"\n{len(casos) - len(fallos)}/{len(casos)} comprobaciones")
    return 1 if fallos else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--test", action="store_true", help="verifica las señales con datos sintéticos")
    args = ap.parse_args()
    if args.test:
        return autotest()
    print("Módulo de señales para la cola PD-04. Se usa desde")
    print("src/review/build_obras_externas_review.py. Pruebe con --test.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
