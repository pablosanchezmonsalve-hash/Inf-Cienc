"""Herramienta para revisar las obras de repositorios de datos y acceso abierto (PD-04).

QUÉ RESUELVE
    `src/enrich/obras_externas.py` deja en
    `internal/obras_externas_cobertura.csv` las obras que DataCite, Europe PMC
    y Zenodo atribuyen a una firma o a la afiliación institucional y que el
    universo Scopus no tiene. Es una cola de revisión, no un ajuste del corpus
    (`D-206`): "no está en Scopus" admite aquí cuatro lecturas incompatibles, y
    elegir entre ellas exige criterio humano.

    Misma clase de tarea que `build_openalex_review.py`, y por eso comparte su
    interacción: la evidencia ya está delante —firma, ORCID consultado, autor
    y afiliación tal como los declara la fuente, DOI, año, tipo, y si otra de
    las tres fuentes trae el mismo DOI— y responder debe costar una lectura y
    un clic.

EL CUARTO VEREDICTO, QUE NINGUNA OTRA COLA NECESITA
    Zenodo acuña un DOI por cada versión de un depósito, además del DOI de
    concepto que las agrupa; DataCite indexa preprints cuya versión publicada
    sí está en Scopus. Son DOI distintos para la misma obra, así que la
    deduplicación por DOI no los colapsa y contarlos sería inflar la cifra con
    duplicados que el propio mecanismo no puede ver. «Otra versión de una obra
    ya contada» no es una atribución errónea —la obra sí es de esta
    institución— ni un tipo excluido: es su propia categoría, y se registra
    como tal.

SEÑALES AUTOMÁTICAS QUE ARGUMENTAN, PERO NO DECIDEN
    Cada tarjeta muestra el resultado de las comprobaciones de
    `senales_obras_externas.py` contra lo que el proyecto ya sabe: qué ORCID
    vigente sostiene el caso y con qué confianza, qué institución declara la
    fuente para esa firma EN ESA OBRA, y si el título ya está contado en el
    corpus o repetido en la propia cola.

    Ninguna marca un veredicto ni preselecciona un botón. Existen porque
    averiguar eso a mano, 322 veces, es lo que hace que una cola no se empiece
    nunca; y no deciden porque un recuento salido de un umbral automático
    sería Nivel D, y `PD-04` se publica como Nivel V.

QUÉ NO HACE
    No decide nada por sí sola y no toca
    `data/interim/publications_universe.csv` bajo ninguna circunstancia.
    Marcar «Sí, es UFT» NO agrega la obra al corpus: la cuenta como `PD-04`,
    en su propia sección, con su propio denominador, sin citas ni FWCI.

CAPA
    Interna: no entra en `dist/`.

Uso:
    python3 src/review/build_obras_externas_review.py
    python3 src/review/build_obras_externas_review.py --test

Salida:
    internal/revision_obras_externas.html
"""

from __future__ import annotations

import argparse
import html as htmlmod
import io
import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

if sys.platform == "win32":
    # La consola de Windows usa cp1252 por defecto: revienta cualquier print()
    # con caracteres como "→"/"✗"/"⚠". Mismo patrón que src/enrich/orcid_openalex.py.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(ROOT / "src" / "review"))
# CSS, JS y el armado del <script> se importan, no se copian: la lógica de
# marcar, filtrar, guardar y exportar es la misma que la de la cola de
# OpenAlex, y dos copias significan corregir cada bug de exportación dos veces.
from build_openalex_review import CSS, _json_para_script, render_js  # noqa: E402
import senales_obras_externas as senales  # noqa: E402

FUENTE = ROOT / "internal" / "obras_externas_cobertura.csv"
DECISIONES = ROOT / "internal" / "obras_externas_decisiones.csv"
SALIDA = ROOT / "internal" / "revision_obras_externas.html"
DEPURADAS = ROOT / "internal" / "obras_externas_depuradas.csv"

FUENTE_LEGIBLE = {"datacite": "DataCite", "europepmc": "Europe PMC", "zenodo": "Zenodo"}


def b_ventana() -> tuple[int, int]:
    """La ventana declarada del proyecto, leída de la configuración."""
    sys.path.insert(0, str(ROOT / "src" / "audit"))
    import common as c  # noqa: PLC0415
    v = c.load_config("institution.yml")["ventana_temporal"]
    return int(v["anio_inicio"]), int(v["anio_fin"])

CABECERA_CSV = [
    "# Revisión de obras en repositorios de datos y acceso abierto (PD-04) — decisión humana",
    "# Generado por internal/revision_obras_externas.html",
    "# veredicto: uft     = producción real de la UFT fuera de Scopus ·",
    "#            error   = no es de esta institución (homónimo o atribución errónea) ·",
    "#            tipo    = tipo documental que este proyecto excluye a propósito ·",
    "#            version = otra versión, o el DOI de concepto, de una obra ya contada",
    "# ESTO NO MODIFICA EL UNIVERSO PUBLICADO. Sólo lo marcado 'uft' se cuenta como PD-04.",
]

COLUMNAS = ["fuente", "id_fuente", "doi"]


def clave_de(fila) -> str:
    """La identidad de una fila de la cola: fuente + identificador en esa fuente.

    Ni el DOI ni el identificador solos sirven: la misma obra puede estar en
    las tres fuentes con el mismo DOI (y debe poder decidirse por separado en
    cada una, porque la evidencia que cada fuente aporta es distinta), y dos
    fuentes pueden reutilizar el mismo identificador local.
    """
    return f"{fila['fuente']} · {fila['id_fuente']}"


def leer_previas(ruta: Path) -> dict[str, dict]:
    """Decisiones de una corrida anterior de esta misma herramienta, si existe.

    Se salta la cabecera de comentario por POSICIÓN, no con
    `pd.read_csv(comment='#')`: eso trunca en la primera almohadilla esté
    donde esté, y una nota como «ítem #3» perdería la mitad en silencio
    (mismo bug ya corregido en `decisiones.py::leer()`).
    """
    if not ruta.exists():
        return {}
    lineas = ruta.read_text(encoding="utf-8-sig").splitlines()
    i = 0
    while i < len(lineas) and lineas[i].startswith("#"):
        i += 1
    df = pd.read_csv(io.StringIO("\n".join(lineas[i:])), dtype=str).fillna("")
    faltan = {"fuente", "id_fuente"} - set(df.columns)
    if faltan:
        sys.exit(f"Faltan columnas en {ruta.name}: {sorted(faltan)}")
    return {clave_de(r): {"veredicto": r.get("veredicto", ""), "nota": r.get("nota", "")}
            for _, r in df.iterrows()
            if r.get("veredicto") not in (None, "", "pendiente")}


def _bloque_corroboracion(otras: str) -> str:
    """Caja de evidencia cruzada: el mismo DOI en otra de las tres fuentes.

    Regla 3 de `docs/METODOLOGIA_FUERA_DE_SCOPUS.md`: dos fuentes
    independientes sobre el mismo registro son evidencia MÁS FUERTE para ese
    registro, nunca un registro más. Se muestra para que quien revisa lo sepa
    al decidir; el recuento lo resta después, al agregar.
    """
    if not otras:
        return ""
    nombres = ", ".join(FUENTE_LEGIBLE.get(f, f) for f in otras.split("|") if f)
    return f"""
      <p class="xref hay-afiliacion">
        <span class="etq">Evidencia independiente (mismo DOI en otra fuente)</span><br>
        También la trae <b>{htmlmod.escape(nombres)}</b>. Dos registros del mismo
        DOI son UNA obra corroborada dos veces, no dos obras: el recuento lo
        descuenta al agregar.
      </p>"""


def _recorta(texto: str, n: int = 140) -> str:
    """Cadenas de afiliación de 400 caracteres rompen la tarjeta y no se leen."""
    t = " ".join(str(texto or "").split())
    return t if len(t) <= n else t[: n - 1].rstrip() + "…"


def _bloque_senales(r) -> str:
    """Los hechos que el proyecto ya sabe sobre este caso, dichos antes de decidir.

    Cada línea es una comprobación mecánica con su resultado, verde cuando
    empuja hacia «sí» y roja cuando empuja hacia «no». NINGUNA marca el
    veredicto ni preselecciona un botón: la decisión sigue costando un clic
    humano, que es lo único que hace de `PD-04` un indicador de Nivel V.

    Si la fila no trae columnas de señal —una cola vieja, o una prueba— el
    bloque simplemente no aparece.
    """
    identificador = str(r.get("s_identificador") or "")
    firma = str(r.get("s_firma") or "")
    afiliacion = str(r.get("s_afiliacion") or "")
    en_corpus = str(r.get("s_titulo_corpus") or "")
    try:
        en_cola = int(r.get("s_titulo_cola") or 0)
    except (TypeError, ValueError):
        en_cola = 0
    if not (identificador or afiliacion or en_corpus or en_cola):
        return ""

    lineas: list[tuple[str, str]] = []
    # Las firmas del corpus llevan la inicial con punto ("Abara J.F."), así que
    # cerrar la frase a ciegas produce "Abara J.F..".
    quien = f" — <b>{htmlmod.escape(firma)}</b>" if firma else ""
    punto = "" if firma.endswith(".") else "."
    if identificador == "alta":
        lineas.append(("si",
                       f"La sostiene un ORCID que este proyecto da por firme{quien}{punto}"))
    elif identificador:
        lineas.append(("neutro",
                       f"La sostiene un ORCID de confianza <b>{htmlmod.escape(identificador)}</b>"
                       f"{quien}: asignación probable, no comprobada."))
    else:
        lineas.append(("no", "Ningún ORCID vigente la sostiene: el vínculo es sólo "
                             "la cadena de afiliación."))

    declarada = _recorta(r.get("afiliacion_declarada"))
    if afiliacion == "institucion":
        lineas.append(("si", "La fuente declara a esta institución como afiliación "
                             "<b>en esta obra</b>."))
    elif afiliacion == "otra":
        lineas.append(("no", "La fuente declara <b>otra institución</b> en esta obra: "
                             f"«{htmlmod.escape(declarada)}». La producción institucional "
                             "se define por la afiliación de la firma."))
    elif afiliacion == "sin dato":
        lineas.append(("neutro", "La fuente no declara afiliación en esta obra: "
                                 "aquí no hay evidencia en ningún sentido."))

    if en_corpus:
        ya = "" if en_corpus == "sí" else f" (<span class=\"mono\">{htmlmod.escape(en_corpus)}</span>)"
        lineas.append(("no", f"Un título idéntico ya está en el corpus Scopus con otro DOI{ya}. "
                             "Suele ser «otra versión de una obra ya contada»."))
    if en_cola:
        # Tras la regla de título repetido, las demás versiones ya no están en
        # la cola: decir que "aparece dos veces más" sería falso. Ésta es la
        # que quedó, y por eso la línea es neutra y no roja — no hay nada en
        # contra de ella, hay algo que ella representa.
        otras = "otra versión" if en_cola == 1 else f"otras {en_cola} versiones"
        lineas.append(("neutro",
                       f"Del mismo título había {otras} en la cola, depuradas por regla. "
                       "Ésta es la única que puede contarse: si es de la institución, "
                       "cuenta por todas."))

    filas = "".join(f'<span class="sig {cl}">{txt}</span>' for cl, txt in lineas)
    return f"""
      <p class="xref senales">
        <span class="etq">Señales automáticas · no deciden nada, sólo arman el caso</span>
        {filas}
      </p>"""


def _via_legible(via: str) -> str:
    etiquetas = {"orcid": "por ORCID confirmado", "afiliacion": "por afiliación declarada"}
    return " y ".join(etiquetas.get(v, v) for v in via.split("|") if v)


def render_html(filas: pd.DataFrame, n_ventana: int | None = None,
                n_depuradas: int = 0) -> str:
    previas = leer_previas(DECISIONES)
    items: list[dict] = []
    cuerpo = ""
    for _, r in filas.iterrows():
        clave = clave_de(r)
        fuente = str(r.get("fuente") or "")
        doi = str(r.get("doi") or "")
        titulo = str(r.get("titulo") or "(sin título)")
        anio = str(r.get("anio") or "")
        tipo = str(r.get("tipo") or "")
        via = str(r.get("via") or "")
        firma = str(r.get("firma_uft") or "")
        autor = str(r.get("autor_en_la_fuente") or "")
        orcid = str(r.get("orcid_en_la_fuente") or "")
        afiliacion = str(r.get("afiliacion_declarada") or "")
        motivo = str(r.get("motivo") or "")

        items.append({
            "id": clave,
            "campos": {"fuente": fuente, "id_fuente": str(r.get("id_fuente") or ""), "doi": doi},
            "previa": previas.get(clave),
        })

        doi_html = (f'<a href="https://doi.org/{htmlmod.escape(doi)}" target="_blank" '
                    f'rel="noopener">{htmlmod.escape(doi)}</a>' if doi
                    else '<em>sin DOI</em>')
        # Los tokens de señal entran en el índice de búsqueda: escribir
        # "sig-afiliacion-otra" en el buscador filtra la cola por esa señal
        # sin tocar el JavaScript compartido con la cola de OpenAlex.
        tokens = str(r.get("s_tokens") or "")
        buscar = htmlmod.escape(
            f"{titulo} {autor} {firma} {doi} {tipo} {fuente} {tokens}".lower())

        # La vía por afiliación es matching por cadena suelta (`I-05`): la
        # advertencia va en la propia tarjeta, no en una nota general al pie
        # que nadie relaciona con el caso que tiene delante.
        aviso_via = ('<br><span class="aviso-via">Llegó sólo por la cadena de '
                     'afiliación: confirme que es esta persona y no un homónimo.</span>'
                     if via == "afiliacion" else "")

        cuerpo += f"""
    <article class="item" data-id="{htmlmod.escape(clave)}" data-decidido="0"
             data-buscar="{buscar}">
      <div class="meta">
        <span class="n">{htmlmod.escape(FUENTE_LEGIBLE.get(fuente, fuente))}</span>
        <span class="n">{htmlmod.escape(anio)}</span>
        <span class="n">{htmlmod.escape(tipo)}</span>
      </div>
      <h3>{htmlmod.escape(titulo)}</h3>
      <p class="ctx">
        Hallada <b>{htmlmod.escape(_via_legible(via))}</b>
        {f' · firma UFT: <b>{htmlmod.escape(firma)}</b>' if firma else ''}
        {f'<br>La fuente lo nombra: <b>{htmlmod.escape(autor)}</b>' if autor else ''}
        {f' · ORCID: <span class="mono">{htmlmod.escape(orcid)}</span>' if orcid else ''}
        {f'<br>Afiliación declarada: <b>{htmlmod.escape(afiliacion)}</b>' if afiliacion else ''}
        <br>DOI: <span class="mono">{doi_html}</span>
        <br><span class="mono">{htmlmod.escape(motivo)}</span>{aviso_via}
      </p>{_bloque_corroboracion(str(r.get("corroborada_por") or ""))}{_bloque_senales(r)}
      <div class="dec">
        <button type="button" data-v="uft" aria-pressed="false">Sí, es UFT</button>
        <button type="button" data-v="error" aria-pressed="false">No es de esta institución</button>
        <button type="button" data-v="tipo" aria-pressed="false">Tipo excluido a propósito</button>
        <button type="button" data-v="version" aria-pressed="false">Otra versión de una obra ya contada</button>
        <input type="text" data-campo="nota" placeholder="Nota (opcional)">
      </div>
    </article>"""

    datos = _json_para_script(items)
    hoy = date.today().isoformat()
    n = len(filas)
    por_fuente = ", ".join(
        f"{c} {FUENTE_LEGIBLE.get(f, f)}" for f, c in filas["fuente"].value_counts().items()
    ) if n else "ninguna"

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Revisión de obras en repositorios externos (PD-04) — capa interna</title>
<style>{CSS}
.aviso-via{{color:#8a5a00;font-size:.95em}}
.senales{{border-left-color:var(--marca);background:#f7f8fb}}
.sig{{display:block;padding-left:1.15rem;position:relative;margin-top:.3rem}}
.sig::before{{position:absolute;left:0;font-weight:700}}
.sig.si::before{{content:"+";color:var(--si)}}
.sig.no::before{{content:"−";color:var(--no)}}
.sig.neutro::before{{content:"·";color:var(--tinta2)}}
.filtros{{font-size:.83rem;margin:.4rem 0 0}}
.filtros code{{background:var(--sup);border:1px solid var(--linea);border-radius:4px;
  padding:.05rem .3rem;font-size:.95em;cursor:pointer}}
</style>
</head>
<body>
<header><div class="c">
  <h1>Obras en repositorios de datos y acceso abierto que Scopus no indexa</h1>
  <p>Capa interna · generado el {hoy} · {n} obras ({por_fuente})</p>
  {f'<p>Las <b>{n_ventana}</b> primeras caen en la ventana {b_ventana()[0]}-{b_ventana()[1]} y son las únicas que pueden llegar a contarse. {"La restante queda detrás, sin descartarse" if n - n_ventana == 1 else f"Las {n - n_ventana} restantes quedan detrás, sin descartarse"}.</p>' if n_ventana is not None else ''}
  {f'<p>Otras <b>{n_depuradas}</b> quedaron fuera por la regla de título repetido: varias versiones de un mismo depósito son una obra, y de todas ellas a lo sumo una puede contarse. Quedan listadas en <span class="mono">internal/obras_externas_depuradas.csv</span> con la fila que las sustituye.</p>' if n_depuradas else ''}
</div></header>

<div class="barra"><div class="c">
  <span class="avance" id="avance"></span>
  <input type="text" class="buscar" id="buscar" placeholder="Buscar título, autor, DOI, fuente…">
  <select id="filtro-estado">
    <option value="todos">Todos</option>
    <option value="pendientes">Sólo pendientes</option>
    <option value="revisados">Sólo revisados</option>
  </select>
  <button type="button" class="pri" id="exportar">Exportar decisiones (CSV)</button>
  <button type="button" id="limpiar">Borrar todo</button>
</div></div>

<main class="c">
  <div class="aviso">
    <strong>Esto NO modifica el universo publicado.</strong> Marcar «Sí, es UFT»
    no agrega la obra al corpus Scopus: la cuenta como <span class="mono">PD-04</span>,
    en su propia sección, con su propio denominador y sin citas ni FWCI —SciVal
    no mide nada de esto— (<span class="mono">D-206</span>, Regla 5 de
    <span class="mono">docs/METODOLOGIA_FUERA_DE_SCOPUS.md</span>). Lo que quede
    pendiente NO se cuenta.
    <br><br>
    Dos avisos que cambian cómo leer cada caso. Las obras halladas
    <b>por afiliación</b> llegaron por una cadena de texto, no por un
    identificador: ahí la pregunta real es si es esta persona o un homónimo.
    Y <b>Zenodo acuña un DOI por versión</b>, además del DOI de concepto: si
    reconoce una obra que ya está contada, use «Otra versión», no «No es de
    esta institución» — sí es de la institución, y esa diferencia importa
    para saber cuánto de la cola es duplicación y cuánto atribución errada.
    <br><br>
    Cada tarjeta trae <b>señales automáticas</b>: comprobaciones mecánicas
    contra lo que este proyecto ya sabe —qué ORCID la sostiene y con cuánta
    confianza, qué institución declara la fuente para esa firma en esa obra,
    y si el título ya está contado—. <b>Ninguna decide</b> ni preselecciona un
    botón: están para que el caso llegue armado y la respuesta cueste una
    lectura. El veredicto sigue siendo suyo, y es lo único que convierte una
    obra en recuento.
    <p class="filtros">Filtre por señal (clic para poner y quitar):
      <code>sig-afiliacion-institucion</code>
      <code>sig-afiliacion-otra</code>
      <code>sig-afiliacion-sin-dato</code>
      <code>sig-orcid-alta</code>
      <code>sig-sin-identificador</code>
      <code>sig-titulo-en-corpus</code>
      <code>sig-titulo-repetido</code>
    </p>
  </div>
  {cuerpo}
</main>
<footer><div class="c">
  Generado por <span class="mono">src/review/build_obras_externas_review.py</span>
  a partir de <span class="mono">internal/obras_externas_cobertura.csv</span>.
  Regenerable — no pierde respuestas ya exportadas a CSV. Exporte y aplique con
  <span class="mono">python3 src/review/apply_obras_externas_review.py</span>.
</div></footer>
<script>{render_js(datos, COLUMNAS, "revision_obras_externas_v1",
                   "obras_externas_decisiones", CABECERA_CSV)}</script>
<script>
// Los tokens de señal son texto dentro de `data-buscar`, así que filtrar por
// ellos es escribirlos en el buscador. Esto sólo ahorra teclearlos; el filtro
// es el mismo que ya comparten las dos colas.
document.querySelectorAll('.filtros code').forEach(el => {{
  el.addEventListener('click', () => {{
    const b = document.getElementById('buscar');
    b.value = b.value.trim() === el.textContent ? '' : el.textContent;
    b.dispatchEvent(new Event('input', {{bubbles: true}}));
  }});
}});
</script>
</body>
</html>
"""


def autotest() -> int:
    casos = []

    def caso(n, ok, obs=None):
        casos.append((n, ok, obs))

    df = pd.DataFrame([
        {"fuente": "zenodo", "id_fuente": "10.5281/zenodo.1", "doi": "10.5281/zenodo.1",
         "titulo": "Dataset </script> con marcado", "anio": "2024", "tipo": "dataset",
         "via": "orcid", "consulta": "0000-0001-0000-0001", "firma_uft": "Pérez A.",
         "autor_en_la_fuente": "Pérez, Ana", "orcid_en_la_fuente": "0000-0001-0000-0001",
         "afiliacion_declarada": "Universidad Finis Terrae", "motivo": "m",
         "corroborada_por": "datacite", "resolucion": "PENDIENTE_REVISION_HUMANA"},
        {"fuente": "europepmc", "id_fuente": "MED:1", "doi": "", "titulo": "Preprint",
         "anio": "2023", "tipo": "preprint", "via": "afiliacion",
         "consulta": "Universidad Finis Terrae", "firma_uft": "",
         "autor_en_la_fuente": "", "orcid_en_la_fuente": "",
         "afiliacion_declarada": "Universidad Finis Terrae", "motivo": "sin DOI",
         "corroborada_por": "", "resolucion": "PENDIENTE_REVISION_HUMANA"},
    ])
    df = senales.calcular(
        df,
        orcids={"0000-0001-0000-0001": {"firma": "Pérez A.", "confianza": "alta"}},
        variantes=["universidad finis terrae"],
        universo={},
    )
    html = render_html(df)

    caso("una tarjeta por obra", html.count('<article class="item"') == 2)
    caso("los cuatro veredictos están disponibles",
         all(f'data-v="{v}"' in html for v in ("uft", "error", "tipo", "version")))
    caso("el veredicto propio de PD-04 tiene su botón",
         'Otra versión de una obra ya contada' in html)
    caso("el marcado del título no escapa del atributo ni del HTML",
         "</script> con marcado" not in html and "&lt;/script&gt;" in html)
    caso("la obra corroborada por otra fuente lo dice",
         "mismo DOI en otra fuente" in html and "DataCite" in html)
    caso("la hallada sólo por afiliación advierte del homónimo",
         "no un homónimo" in html or "un homónimo" in html)
    caso("una obra sin DOI se muestra como tal", "<em>sin DOI</em>" in html)
    caso("la clave identifica fuente e identificador, no sólo el DOI",
         clave_de(df.iloc[0]) != clave_de(df.iloc[1])
         and "zenodo" in clave_de(df.iloc[0]))
    caso("el CSV exportado lleva las tres columnas de identidad",
         '["fuente", "id_fuente", "doi"]' in html.replace("'", '"'))
    caso("la clave de navegador no choca con la de la cola de OpenAlex",
         "revision_obras_externas_v1" in html
         and "revision_cobertura_openalex_v1" not in html)
    caso("las señales se muestran y se declaran como no decisorias",
         "Señales automáticas" in html and "no deciden nada" in html)
    caso("la señal de identificador nombra la firma que lo sostiene",
         "Pérez A." in html and "da por firme" in html)
    caso("la señal de afiliación reconoce la institución configurada",
         "declara a esta institución" in html)
    # Los cuatro botones de las dos tarjetas salen sin pulsar. (En el CSS sí
    # aparece `aria-pressed="true"`, dentro de un selector; el discriminante
    # es el `>` que cierra la etiqueta.)
    caso("ninguna señal preselecciona un veredicto",
         html.count('aria-pressed="false"') == 8
         and 'aria-pressed="true">' not in html)
    caso("los tokens de señal quedan en el índice de búsqueda",
         "sig-afiliacion-institucion" in html and "sig-orcid-alta" in html)

    con_depuradas = render_html(df, 2, 7)
    caso("lo depurado por regla se declara en la cabecera, no se calla",
         "<b>7</b>" in con_depuradas and "título repetido" in con_depuradas
         and "obras_externas_depuradas.csv" in con_depuradas)
    caso("sin nada depurado no se anuncia una depuración vacía",
         "título repetido" not in html)

    # Una cola generada antes de que existieran las señales no debe romper el
    # render: sin columnas `s_*`, el bloque simplemente no aparece.
    sin_senales = render_html(df.drop(columns=senales.COLUMNAS))
    caso("una cola sin columnas de señal sigue renderizando",
         sin_senales.count('<article class="item"') == 2
         and "Señales automáticas" not in sin_senales)

    fallos = [n for n, ok, _ in casos if not ok]
    for n, ok, obs in casos:
        marca = "OK  " if ok else "FALLA"
        print(f"  {marca} {n}" + (f"  ({obs})" if not ok and obs is not None else ""))
    print(f"\n{len(casos) - len(fallos)}/{len(casos)} comprobaciones")
    return 1 if fallos else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--test", action="store_true", help="verifica el render con datos sintéticos")
    args = ap.parse_args()

    print("=" * 78)
    print("REVISIÓN DE OBRAS EN REPOSITORIOS DE DATOS Y ACCESO ABIERTO (PD-04)")
    print("=" * 78)
    if args.test:
        return autotest()

    if not FUENTE.exists():
        sys.exit(f"Falta {FUENTE.relative_to(ROOT)}. Ejecute: "
                  "python3 src/enrich/obras_externas.py")
    df = pd.read_csv(FUENTE, dtype=str).fillna("")

    # Las señales se calculan AQUÍ, al presentar, y no en el conector: son
    # una lectura de lo que el proyecto ya sabe, no un dato nuevo de la
    # fuente. Así se pueden cambiar, corregir o ampliar sin volver a salir a
    # la red ni invalidar la cola ya descargada.
    df = senales.calcular(df)

    # Orden: primero lo que puede llegar a contarse, después lo que más
    # evidencia trae.
    #
    # La ventana manda por encima de todo. `build 09` sólo cuenta lo que cae
    # en 2023-2025, así que revisar una obra de 2015 es trabajo que no puede
    # traducirse en cifra por mucho que se confirme. En la corrida real eso
    # separa 322 filas de 1.967: la diferencia entre una cola revisable y una
    # que nadie va a empezar. Las de fuera NO se descartan —la ventana puede
    # cambiar, y son evidencia igual—, van detrás.
    #
    # Dentro de la ventana ordena `s_fuerza`, que resume las señales: primero
    # los casos que varias comprobaciones sostienen, al final los que huelen a
    # duplicado. Es orden de lectura, no una decisión: nada queda fuera.
    ventana = b_ventana()
    en_ventana = df["anio"].str.slice(0, 4)
    en_ventana = en_ventana.where(en_ventana.str.isdigit(), "")
    df = df.assign(
        _ventana=[1 if a and ventana[0] <= int(a) <= ventana[1] else 0 for a in en_ventana],
    )

    # Regla de título repetido, decidida por el usuario el 2026-09-04: de
    # cada título, una sola fila queda revisable. Se aplica ANTES de ordenar
    # y de contar la ventana, porque lo depurado no es cola: no se revisa, no
    # se cuenta y no se esconde — queda en su propio CSV con la fila que lo
    # sustituye. Dentro de un grupo prefiere la que cae en ventana, y a
    # igualdad la de señales más fuertes: de nada sirve conservar la versión
    # de 2019 de un depósito cuya versión de 2024 sí podría contarse.
    previas = leer_previas(DECISIONES)
    df = senales.depurar_repetidos(
        df,
        preferencia=df["_ventana"] * 10 + df["s_fuerza"],
        protegidas=set(previas),
    )
    depuradas = df[df["s_duplicada"] == 1]
    df = df[df["s_duplicada"] == 0]
    if len(depuradas):
        DEPURADAS.parent.mkdir(parents=True, exist_ok=True)
        depuradas.drop(columns=["_ventana"]).to_csv(DEPURADAS, index=False)

    df = df.sort_values(["_ventana", "s_fuerza", "anio"], ascending=[False, False, False])
    n_ventana = int(df["_ventana"].sum())
    df = df.drop(columns=["_ventana"])

    SALIDA.write_text(render_html(df, n_ventana, len(depuradas)), encoding="utf-8")

    print(f"  obras a revisar          : {len(df)}")
    print(f"    en ventana {b_ventana()[0]}-{b_ventana()[1]}, primero : {n_ventana}"
          f"  (las únicas que pueden contarse)")
    print(f"  ya revisadas             : {len(previas)}")
    print(f"  pendientes               : {len(df) - len(previas)}")
    for fuente, n in df["fuente"].value_counts().items():
        print(f"    {FUENTE_LEGIBLE.get(fuente, fuente):<12}: {n}")
    print(f"  corroboradas entre fuentes: {int(df['corroborada_por'].astype(bool).sum())}")
    if len(depuradas):
        print(f"  depuradas por título repetido: {len(depuradas)}"
              f"  ({DEPURADAS.name}, con la fila que las sustituye)")

    # Qué hay delante, contado sobre lo que de verdad se va a revisar. Sin
    # esto, las señales sólo se ven caso a caso y no dan idea del reparto.
    v = df.head(n_ventana)
    if n_ventana:
        print(f"\n  señales sobre esas {n_ventana} (no deciden nada, ordenan la lectura):")
        marcas = [
            ("afiliación institucional en la obra", (v["s_afiliacion"] == "institucion").sum()),
            ("afiliación de otra institución     ", (v["s_afiliacion"] == "otra").sum()),
            ("la fuente no declara afiliación    ", (v["s_afiliacion"] == "sin dato").sum()),
            ("ORCID de confianza alta            ", (v["s_identificador"] == "alta").sum()),
            ("sin ORCID vigente que la sostenga  ", (v["s_identificador"] == "").sum()),
            ("título ya presente en el corpus    ", (v["s_titulo_corpus"] != "").sum()),
            ("título repetido dentro de la cola  ", (v["s_titulo_cola"] > 0).sum()),
        ]
        for etiqueta, n in marcas:
            print(f"    {etiqueta}: {int(n)}")
    print(f"\n  OK · {SALIDA.relative_to(ROOT)}")
    print("       Abra el .html, marque cada caso, exporte el CSV, y aplíquelo con")
    print("       python3 src/review/apply_obras_externas_review.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
