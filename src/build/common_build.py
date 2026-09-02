"""Utilidades compartidas por el build de artefactos publicables.

BARRERA DE CAPAS (decisión D-22): este módulo lee de `data/interim/` y
`config/`. Nunca de `data/raw/`. De `internal/` lee DOS archivos, ambos
declarados aquí y en `docs/LAYERS.md`, y de ambos se proyecta sólo lo
publicable:

  · `internal/matching_log.csv` — campos publicables (autor, eid, año, unidad).
    Nunca la cadena de afiliación cruda ni el método de detección.

  · `internal/ambiguities_authors.csv` — SÓLO los `nombre_en_fuente` de las
    filas `E-09`, y sólo para contarlos. Nunca `detalle`, `consecuencia` ni
    `resolucion`, que son material de conciliación interna. Lo que llega a un
    artefacto público es un RECUENTO, no los nombres. Se lee porque que varias
    de las fichas publicadas probablemente no correspondan a personas es una
    limitación del dato, y publicar el recuento sin ella sería publicar una
    cifra que ya sabemos que sobra.
"""

from __future__ import annotations

import json
import math
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config"
INTERIM = ROOT / "data" / "interim"
INTERNAL = ROOT / "internal"
PROCESSED = ROOT / "data" / "processed"
DOCS = ROOT / "docs"

# Campos de la capa interna que jamás pueden aparecer en un artefacto público.
# La verificación automática (05_verify_public_layer.py) falla si los encuentra.
CAMPOS_PROHIBIDOS = (
    "afiliacion_declarada_raw",
    "metodo_blando",
    "metodo_duro_publicacion",
    "confianza",
    "resolucion",
    "clave_normalizada",
    "clave_apellido",
    "cadena_afiliacion",
)


def load_config(name: str) -> dict:
    with open(CONFIG / name, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


INSTITUTION = load_config("institution.yml")
SOURCES = load_config("sources.yml")["fuentes"]
INDICATORS = load_config("indicators.yml")


def slugify(text: str) -> str:
    """Identificador seguro para nombres de archivo y URLs.

    NO es único por sí solo: la normalización quita acentos y guiones, de modo
    que 'Orellana-Donoso M.' y 'Orellana Donoso M.' colapsan al mismo valor.
    Use `unique_slugs()` para asignar identificadores a un conjunto de firmas.
    """
    base = unicodedata.normalize("NFD", str(text))
    base = "".join(ch for ch in base if unicodedata.category(ch) != "Mn")
    base = re.sub(r"[^a-zA-Z0-9]+", "-", base).strip("-").lower()
    return base or "sin-nombre"


def unique_slugs(names) -> dict[str, str]:
    """Asigna un identificador único a cada firma, sin fusionar variantes.

    Dos formas de firma distintas ('Díaz F.' y 'Diaz F.') producen el mismo
    slug base. Colapsarlas en un solo archivo sería exactamente el colapso
    automático de variantes que prohíbe la decisión D-08: una ficha
    sobrescribiría a la otra y el ranking mostraría menos personas de las
    detectadas.

    Cuando un slug base es reclamado por más de una firma, TODAS las firmas en
    conflicto reciben un sufijo derivado del nombre exacto. El sufijo depende
    sólo del nombre, no del orden de iteración, por lo que el identificador es
    estable entre builds y entre cargas de datos distintas.
    """
    import hashlib
    from collections import Counter

    names = list(names)
    bases = {n: slugify(n) for n in names}
    colisionados = {b for b, c in Counter(bases.values()).items() if c > 1}

    out: dict[str, str] = {}
    for n in names:
        base = bases[n]
        if base in colisionados:
            h = hashlib.sha1(n.encode("utf-8")).hexdigest()[:4]
            out[n] = f"{base}-{h}"
        else:
            out[n] = base
    return out


def clean(value):
    """Convierte NaN/NaT a None para que el JSON no lleve 'NaN' inválido."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if pd.isna(value):
        return None
    return value


def to_num(value):
    v = clean(value)
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if math.isnan(f):
        return None
    return int(f) if f.is_integer() else round(f, 4)


def split_multi(value) -> list[str]:
    """Separa un campo multivaluado de SciVal ('|') conservando el orden."""
    v = clean(value)
    if v is None:
        return []
    return [p.strip() for p in str(v).split("|") if p.strip() and p.strip() != "-"]


def load_universe() -> pd.DataFrame:
    return pd.read_csv(INTERIM / "publications_universe.csv", dtype=str)


# ─────────────────────────────────────────── consolidación de identidades
#
# El pipeline NUNCA fusiona variantes de nombre por heurística (decisión D-08).
# La única vía es este archivo, que genera src/review/apply_decisions.py a
# partir de lo que una persona decidió en `make revision`. Si no existe, no hay
# consolidación y todo funciona como antes: 589 formas de firma.
def _mapa_consolidacion() -> dict[str, str]:
    # Ausente mientras nadie haya revisado. No es un error: es el estado
    # inicial del proyecto, y `load_config` reventaría en vez de decirlo.
    if not (CONFIG / "identidades_consolidadas.yml").exists():
        return {}
    cfg = load_config("identidades_consolidadas.yml") or {}
    mapa = {}
    for g in cfg.get("grupos") or []:
        for v in g["variantes"]:
            mapa[v] = g["canonica"]
    return mapa


def _origen_consolidacion() -> dict[str, str]:
    """Canónica -> qué sostiene ese grupo: humana, ortografica o mixta.

    Hace falta porque el texto público NO puede decir «revisión humana caso por
    caso» de un grupo que resolvió una normalización de cadena. Son dos niveles
    distintos de evidencia y el informe los tiene que distinguir; si se cuentan
    juntos, una afirmación verificada y una deducida se leen igual.
    """
    if not (CONFIG / "identidades_consolidadas.yml").exists():
        return {}
    cfg = load_config("identidades_consolidadas.yml") or {}
    # `humana` por omisión: los archivos escritos antes de que el origen se
    # declarara sólo contenían decisiones de una persona.
    return {g["canonica"]: g.get("origen", "humana")
            for g in (cfg.get("grupos") or [])}


CONSOLIDACION = _mapa_consolidacion()
ORIGEN_CONSOLIDACION = _origen_consolidacion()


# Firmas que una revisión humana declaró que no son personas: fragmentos de
# cadena de afiliación que la fuente metió en la lista de autores. La auditoría
# los detecta (regla `E-09`) y los encola; descartarlos lo decide una persona.
#
# El descarte se aplica AQUÍ y no en `internal/matching_log.csv` a propósito.
# La detección institucional que los trajo es real —la publicación sí es de la
# UFT—, y la regla bloqueante `I-01` exige que toda publicación tenga al menos
# una. Quitarlos del log dejaría a esas publicaciones sin ninguna y abortaría la
# auditoría entera. Lo que no es una persona es el nombre, no la afiliación.
def _resueltas_e09() -> tuple[set[str], set[str]]:
    """Descartadas y confirmadas como persona. Las dos importan.

    La confirmación no cambia ningún dato, pero cierra el caso: la auditoría
    vuelve a marcar la firma en cada corrida —se calcula sobre el log, que no
    se toca—, así que sin esta lista decir «sí es una persona» no tendría
    efecto alguno.
    """
    if not (CONFIG / "firmas_e09_resueltas.yml").exists():
        return set(), set()
    cfg = load_config("firmas_e09_resueltas.yml") or {}
    def leer(clave: str) -> set[str]:
        return {f["firma"] for f in (cfg.get(clave) or [])}
    return leer("descartadas"), leer("confirmadas")


DESCARTADAS, CONFIRMADAS_E09 = _resueltas_e09()


# Veredictos humanos sobre asignaciones de ORCID (`config/orcid_revisado.yml`,
# generado por `apply_decisions.py`). Tres cosas distintas:
#
#   confirmado   el ORCID vigente lo respalda una persona que lo comprobó.
#   retirado     el ORCID vigente NO es de esa firma. El build deja de usarlo.
#   sin_registro alguien buscó y no encontró. Es un dato: distingue «no tiene»
#                de «nadie ha mirado», que es la distinción que D-09 exige.
#
# El retiro se aplica como FILTRO y no como borrado de
# `data/enriched/authors_orcid.csv` porque ese archivo lo regeneran los
# conectores de enriquecimiento: un borrado se deshace solo en la siguiente
# corrida, y sin aviso.
def _orcid_revisado() -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    if not (CONFIG / "orcid_revisado.yml").exists():
        return {}, {}, {}
    cfg = load_config("orcid_revisado.yml") or {}
    def leer(clave: str) -> dict[str, str]:
        return {f["firma"]: f.get("orcid") or "" for f in (cfg.get(clave) or [])}
    return leer("confirmadas"), leer("retiradas"), leer("sin_registro")


ORCID_CONFIRMADO, ORCID_RETIRADO, ORCID_SIN_REGISTRO = _orcid_revisado()


def canonizar(nombre: str) -> str:
    """Forma canónica de una firma, o la misma firma si no se consolidó."""
    return CONSOLIDACION.get(nombre, nombre)


def load_authors() -> pd.DataFrame:
    """Tabla maestra, con las variantes ya fusionadas donde una persona lo decidió.

    Fusionar filas no es concatenar: cada campo tiene su regla. Los Scopus
    Author ID se UNEN sin repetir —una persona con tres variantes suele tener
    tres identificadores, y perder dos rompería el enlace a la fuente—; los
    años se toman por extremos; y `n_publicaciones` se recuenta desde el log en
    vez de sumarse, porque sumar contaría dos veces una publicación en la que
    dos variantes de la misma persona aparecen por separado.
    """
    df = pd.read_csv(INTERIM / "authors_master_draft.csv", dtype=str)
    df = df[~df["nombre_en_fuente"].isin(DESCARTADAS)]
    if not CONSOLIDACION:
        return df

    df["nombre_en_fuente"] = df["nombre_en_fuente"].map(canonizar)
    log = pd.read_csv(INTERNAL / "matching_log.csv", dtype=str)
    log["nombre_en_fuente"] = log["nombre_en_fuente"].map(canonizar)
    npub = log.groupby("nombre_en_fuente")["eid"].nunique().to_dict()

    def union(serie) -> str:
        vistos = {x for v in serie.dropna()
                  for x in str(v).split("|") if x and x != "nan"}
        return "|".join(sorted(vistos))

    def primero(serie):
        v = serie.dropna()
        return v.iloc[0] if len(v) else None

    filas = []
    for nombre, g in df.groupby("nombre_en_fuente", sort=False):
        if len(g) == 1:
            fila = g.iloc[0].to_dict()
        else:
            ids = union(g["scopus_author_ids"])
            unidades = union(g["unidades_academicas"])
            anios = pd.to_numeric(pd.concat([g["anio_min"], g["anio_max"]]),
                                  errors="coerce").dropna()
            fila = {
                "nombre_en_fuente": nombre,
                "clave_normalizada": primero(g["clave_normalizada"]),
                "clave_apellido": primero(g["clave_apellido"]),
                "scopus_author_ids": ids,
                "n_scopus_author_ids": str(len([x for x in ids.split("|") if x])),
                "orcid": primero(g["orcid"]),
                "anio_min": str(int(anios.min())) if len(anios) else None,
                "anio_max": str(int(anios.max())) if len(anios) else None,
                "unidades_academicas": unidades,
                "n_unidades_distintas": str(len([x for x in unidades.split("|") if x])),
                "confianza_maxima": ("alta" if (g["confianza_maxima"] == "alta").any()
                                     else primero(g["confianza_maxima"])),
                "en_ranking_manual": str((g["en_ranking_manual"] == "True").any()),
                "en_detalle_manual": str((g["en_detalle_manual"] == "True").any()),
            }
        fila["n_publicaciones"] = str(npub.get(nombre, 0))
        filas.append(fila)
    return pd.DataFrame(filas, columns=df.columns)


_JERARQUIA = load_config("matching_rules.yml")["unidad_academica"].get("jerarquia", {})


def facultad_de(unidad: str) -> str:
    """Facultad a la que pertenece una unidad académica.

    Una escuela sin entrada en la jerarquía se devuelve tal cual: no se infiere
    a qué facultad pertenece.
    """
    entrada = _JERARQUIA.get(unidad)
    return entrada["facultad"] if entrada else unidad


def load_authorship() -> pd.DataFrame:
    """Pares autor x publicación, restringidos a las columnas publicables.

    El archivo de origen es capa interna; aquí se proyecta sólo lo que puede
    publicarse. Los campos de trazabilidad del matching se descartan en la
    lectura, no más adelante: así no pueden filtrarse por descuido.
    """
    df = pd.read_csv(INTERNAL / "matching_log.csv", dtype=str)
    df = df[["eid", "anio", "nombre_en_fuente", "unidad_academica",
             "posicion_autor", "n_autores_total"]].copy()
    # Único punto por el que pasan TODOS los consumidores de autoría: aplicar
    # aquí la consolidación y el descarte los propaga a los indicadores, a las
    # fichas y al recuento de autores sin que ninguno tenga que acordarse.
    df = df[~df["nombre_en_fuente"].isin(DESCARTADAS)]
    df["nombre_en_fuente"] = df["nombre_en_fuente"].map(canonizar)
    return df


def firmas_e09_encoladas() -> set[str]:
    """Firmas marcadas por `E-09` que siguen esperando a que alguien decida.

    Devuelve la forma CANÓNICA, no la de la fuente: si una firma marcada se
    fusionó con otra por revisión humana, ya no tiene ficha propia, y contarla
    aparte declararía una ficha que no existe.

    Se publica el RECUENTO, no los nombres (ver la barrera de capas arriba).
    """
    p = INTERNAL / "ambiguities_authors.csv"
    if not p.exists():
        return set()
    amb = pd.read_csv(p, dtype=str)
    marcadas = set(amb[amb["tipo"] == "E-09_firma_sin_forma_de_persona"]["nombre_en_fuente"])
    pendientes = marcadas - DESCARTADAS - CONFIRMADAS_E09
    return {canonizar(f) for f in pendientes}


def nota_p06(publicadas: int) -> dict:
    """Puente entre las 589 formas de firma de la fuente y las que publica el sitio.

    La portada mostraba 556 con una nota cualitativa y la auditoría hablaba de
    589: dos cifras sin puente, que es justo lo que un lector no puede
    reconciliar por su cuenta. Se construye con los números del momento en vez
    de fijarla en config, para que no vuelva a divergir cuando alguien resuelva
    más casos de identidad.

    Declara además las firmas que la regla `E-09` marcó como probables
    fragmentos de cadena de afiliación. Siguen contándose —descartarlas es una
    decisión de identidad y la toma una persona, `D-08`—, pero el valor
    publicado sobra en esa cantidad, y eso se dice en vez de esperar a que
    alguien lo note.

    Vive aquí y no en cada consumidor porque ya divergió una vez: la portada
    servía este texto construido con las cifras del momento mientras la página
    de autores servía el estático de `config/indicators.yml`. Dos notas para un
    mismo indicador es una de más.
    """
    grupos = len(set(CONSOLIDACION.values()))
    fusionadas = len(CONSOLIDACION)
    descartadas = len(DESCARTADAS)
    encoladas = len(firmas_e09_encoladas())
    if not (grupos or descartadas or encoladas):
        return nota("P-06")

    origen = publicadas - grupos + fusionadas + descartadas
    t = f"Formas de firma, no personas. De las {origen} detectadas en la fuente, "
    if grupos:
        # Misma distinción que en la advertencia de la tabla de autores: un
        # grupo unido por normalización de cadena no lo revisó nadie.
        n_ort = sum(1 for o in ORIGEN_CONSOLIDACION.values() if o == "ortografica")
        n_hum = grupos - n_ort
        if n_ort and n_hum:
            t += (f"{fusionadas} se fusionaron en {grupos} personas: {n_hum} tras "
                  f"una revisión humana caso por caso y {n_ort} por ser la misma "
                  "firma escrita con distintos diacríticos o separadores; ")
        elif n_ort:
            t += (f"{fusionadas} se fusionaron en {grupos} personas por ser la "
                  "misma firma escrita con distintos diacríticos o separadores; ")
        else:
            t += (f"{fusionadas} se fusionaron en {grupos} personas tras una "
                  "revisión humana caso por caso; ")
    if descartadas:
        t += (f"{descartadas} se descartaron por no ser personas sino fragmentos "
              "de cadena de afiliación; ")
    t += f"las {publicadas - grupos} restantes siguen sin consolidar."
    if encoladas:
        t += (f" De las {publicadas} publicadas, {encoladas} son PROBABLES "
              "fragmentos de cadena de afiliación, detectados por la auditoría y "
              "pendientes de revisión humana (regla E-09): si se confirman, las "
              f"firmas que corresponden a personas serían {publicadas - encoladas}.")
    return {"texto": t, "destacada": bool(encoladas)}


def denominadores() -> dict:
    return INDICATORS["denominadores"]


def indicador(code: str) -> dict:
    return INDICATORS["indicadores"][code]


def nota(code: str) -> dict | None:
    """Nota metodológica y advertencia destacada de un indicador, si tiene."""
    spec = INDICATORS["indicadores"].get(code, {})
    texto = spec.get("advertencia")
    if not texto:
        return None
    return {"texto": texto, "destacada": bool(spec.get("advertencia_destacada"))}


# Qué fuente sostiene cada indicador. Se declara aquí y no se infiere: el sitio
# venía atribuyendo todo a «Scopus» mientras la metodología decía «Scopus y
# SciVal», y sin SciVal no existirían el FWCI ni los percentiles de citación.
# Decirlo por indicador es más preciso que decirlo una vez en el pie.
FUENTE_POR_INDICADOR = {
    "P-01": "Scopus", "P-02": "Scopus", "P-03": "Scopus", "P-04": "Scopus",
    "P-05": "Scopus", "P-06": "Scopus", "P-07": "Scopus",
    "A-01": "Scopus",
    "I-01": "SciVal", "I-02": "SciVal", "I-03": "SciVal",
    "I-04": "SciVal", "I-05": "SciVal",
    "R-01": "SciVal",
    "C-01": "Scopus", "C-03": "Scopus", "C-04": "Scopus", "C-06": "Scopus", "C-05": "Scopus",
    "T-01": "Scopus", "T-04": "SciVal", "T-05": "SciVal",
    # ORCID no está en ninguna de las dos fuentes: se recupera aparte. El
    # catálogo publica esta columna, así que dejarlo caer en el genérico
    # «Scopus · SciVal» sería publicar una procedencia falsa.
    "AU-05": "Crossref · registro de ORCID",
    # PD-01 no nombra una Facultad específica a propósito: el mecanismo es
    # general (config/sources.yml declara cuáles Facultades contribuyen), y
    # hoy sólo una lo hace.
    "PD-01": "Declarado por la Facultad (no Scopus)",
    # PD-02: evidencia de otra naturaleza que PD-01 — no es una Facultad
    # declarando su propia lista, es OpenAlex confirmado por revisión humana
    # caso por caso (V2-26).
    "PD-02": "OpenAlex, confirmado por revisión humana (no Scopus)",
}


def procedencia(code: str, cubiertas: int | None = None,
                n: int | None = None, unidad: str = "publicaciones",
                corte: str | None = None) -> dict:
    """Sello de procedencia de un indicador: fuente, corte, N y cobertura.

    El N NO es global: cambia según el indicador —823 en producción, 816 en
    impacto, 818 en autoría— y publicarlo con un denominador genérico sería
    exactamente el error que este proyecto persigue. `cubiertas` es cuántas
    publicaciones tienen realmente el dato; si es None se asume el denominador
    completo.

    `corte` por defecto es la fecha de corte de SciVal — válido para
    cualquier indicador Scopus/SciVal, pero engañoso para uno que no viene de
    ninguna de las dos (p. ej. PD-01, producción declarada por una Facultad):
    mostraría una fecha de corte que no tiene relación con ese dato. Un
    llamador con su propia fecha de referencia la pasa explícita.
    """
    spec = INDICATORS["indicadores"].get(code, {})
    # El denominador de config está en publicaciones. Un indicador que se
    # calcula sobre otra unidad —P-07 cuenta pares autor x publicación— tiene
    # que traer el suyo, o el sello publicaría una cobertura que no es la que
    # mide la auditoría.
    if n is None:
        n = denominadores().get(spec.get("denominador"), 0)
    cub = n if cubiertas is None else cubiertas
    umbral = INDICATORS["reglas_transversales"]["cobertura_minima_sin_advertencia"]
    return {
        "fuente": FUENTE_POR_INDICADOR.get(code, "Scopus · SciVal"),
        "corte": corte if corte is not None else SOURCES["scival_export"]["fecha_corte"],
        "n": n,
        "cubiertas": cub,
        "unidad": unidad,
        "cobertura": round(100 * cub / n, 1) if n else None,
        # Por debajo del umbral declarado, el sello deja de ser informativo y
        # pasa a ser una advertencia. Lo decide el dato, no quien maqueta.
        "insuficiente": bool(n and cub / n < umbral),
    }


def build_meta() -> dict:
    """Procedencia del build. Se incrusta en todos los artefactos."""
    scival = SOURCES["scival_export"]
    return {
        "institucion": INSTITUTION["institucion"]["nombre_canonico"],
        "institucion_corta": INSTITUTION["institucion"]["nombre_corto"],
        "titulo_plataforma": INSTITUTION["presentacion"]["titulo_plataforma"],
        "ventana": {
            "inicio": INSTITUTION["ventana_temporal"]["anio_inicio"],
            "fin": INSTITUTION["ventana_temporal"]["anio_fin"],
        },
        "fuentes": ["Scopus", "SciVal"],
        "fecha_corte_citas": scival["fecha_corte"],
        "fecha_export": scival["fecha_export"],
        "fecha_build": date.today().isoformat(),
        "denominadores": denominadores(),
        # Lo consume el explorador para decidir cuándo el sello de un corte
        # pasa a ser advertencia. Antes sólo lo conocía el build, así que el
        # navegador habría tenido que fijar un umbral propio — y dos umbrales
        # para una misma regla es la forma de que digan cosas distintas.
        "cobertura_minima_sin_advertencia":
            INDICATORS["reglas_transversales"]["cobertura_minima_sin_advertencia"],
        "advertencia_global": (
            "Los indicadores describen la producción indexada en Scopus, con las "
            "métricas normalizadas de SciVal. La cobertura de la base no es "
            "uniforme entre disciplinas."
        ),
        # Escuela -> facultad, la misma jerarquía que agrega P-07 en el build
        # (`facultad_de()`, más arriba). El explorador la necesita para no
        # mostrar escuelas sueltas junto a facultades en el mismo gráfico: sin
        # esto, cada corte reactivo tendría que traer su propio criterio, y
        # dos criterios para la misma jerarquía es la forma de que un día
        # digan cosas distintas. Sólo el nombre de la facultad — el campo
        # `estado` (confirmada/inferida) es trazabilidad interna, no dato
        # publicable.
        "jerarquia": {k: v["facultad"] for k, v in _JERARQUIA.items()},
    }


def write_json(payload, name: str, subdir: str | None = None) -> Path:
    target = PROCESSED / subdir if subdir else PROCESSED
    target.mkdir(parents=True, exist_ok=True)
    path = target / name
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))
    return path


def banner(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def require_validation() -> None:
    """Regla de barrera: sin auditoría válida no hay build (decisión D-22)."""
    report = INTERIM / "validation_report.csv"
    if not report.exists():
        sys.exit("BUILD ABORTADO: falta data/interim/validation_report.csv. "
                 "Ejecute antes `python3 src/audit/run_all.py`.")
    df = pd.read_csv(report)
    bloqueantes = df[(df["resultado"] == "FALLA") & (df["severidad"] == "bloqueante")]
    if len(bloqueantes):
        print(bloqueantes.to_string(index=False))
        sys.exit(f"BUILD ABORTADO: {len(bloqueantes)} regla(s) bloqueante(s) fallando.")
