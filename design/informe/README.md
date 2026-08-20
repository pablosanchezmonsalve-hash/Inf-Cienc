# Formato del informe exportable a PDF

Fuente del lienzo de diseño del **modo informe**: cuatro páginas A4 vertical
(794×1123 px a 96 dpi) que definen el formato del PDF exportable.

| Archivo | Qué es |
|---|---|
| `Portada.dc.html` | Cifras de cabecera, procedencia y marca de borrador |
| `Main.dc.html` | Página de eje: panel «responde / no responde» y dos indicadores |
| `Tabla.dc.html` | Página de tabla de datos con denominador y sello |
| `Apendice.dc.html` | Denominadores, evidencia de ORCID y limitaciones declaradas |
| `canvas.json` | Disposición de los artboards y notas del encargo |

## Lo que NO está aquí

El archivo ensamblado (`informe-cienciometrico-pdf.html`, ~2 MB) **no se
versiona**: es el editor empaquetado alrededor de estos cinco archivos, y se
regenera. Lo que importa y se revisa es la fuente.

## Por qué estos datos son reales

Las cifras que aparecen —823, 3.935, 4,82, FWCI 0,87, 51,2 %, 556, y las series
de producción anual, áreas QS y tipo documental— salen de `data/processed/`, no
son maqueta. Un formato probado con datos inventados no revela que una etiqueta
no cabe, que una cifra desborda su columna o que un denominador es más largo de
lo que el diseño supuso.

## Sistema visual: narrativa por bandas

Adopta el sistema del rediseño del sitio (lienzo «Rediseño Informe
Cienciométrico»), no la paleta anterior. Tipografía **Newsreader** para titulares
y cifras, **Public Sans** para interfaz y prosa.

| Token | Valor | Qué admite |
|---|---|---|
| `papel` | `#fdf8f2` | Todo |
| `papel-2` | `#f7efe5` | Todo |
| `contraste` | `#071e22` | Todo. Es donde va la **ausencia** (4,71:1) |
| `énfasis` | `#f4c095` | **Sólo titular y prosa** |
| dato | `#1d7874` | Figuras sobre papel y contraste |

**Las dos reglas medidas que gobiernan estas cuatro páginas:**

1. **La banda Peach es tipográfica, nunca de datos.** Sobre ella el color del
   dato cae a 3,21:1 y la marca de ausencia a **2,35:1**. La primera versión del
   rediseño ponía la banda de la ausencia justo ahí: el único sitio donde esa
   marca no se veía.
2. **La ausencia va sobre Ink Black**, donde mide 4,71:1. Lo que el informe no
   sabe ocupa el suelo más fuerte, no una nota al pie.

**Reglas de composición** que estas páginas siguen: una afirmación por banda ·
los fondos alternan y no se repiten seguidos · contraste y énfasis una vez por
página · una figura por banda · el sello viaja con su figura, nunca agrupado al
final · la advertencia va **antes** de la figura que califica.

**Apertura y cierre se aplican al documento, no a cada hoja**: la portada abre,
el apéndice cierra en Peach; las interiores son bandas de trabajo. Y la página
de tabla mantiene la banda como marco dejando la tabla como superficie de
consulta — el mismo criterio por el que el rediseño deja fuera a Publicaciones,
Autores, la ficha y el catálogo.

## Lo que el formato tiene que conservar al implementarse

No son adornos; son las reglas que separan este informe de uno que presenta
métricas sin sus límites:

1. **Cada cifra lleva su denominador visible.** 823, 816 o 818 según el
   indicador (`D-16`).
2. **Cada bloque lleva su sello de procedencia**: fuente y fecha de corte.
3. **Cada eje lleva el panel «responde / no responde»**, de `docs/EJES.md`.
4. **Las advertencias van en el bloque ámbar**, fuera de la familia visual del
   dato.
5. **El apéndice metodológico no es opcional.** Un informe sin él no es
   interpretable.

## Decisión pendiente que el diseño refleja

La marca de agua «BORRADOR — identidad visual sin validar» está tras un
interruptor porque `color_primario` y `logo_path` de `config/institution.yml`
siguen siendo placeholders. Se apaga cuando lleguen los definitivos.

## Vía de implementación acordada

Hoja de estilo de impresión (**0 KB de JavaScript añadido**) que sirve al botón
«Exportar» del navegador, y **la misma hoja** usada por Playwright en el build
para generar el PDF institucional canónico. Un origen, dos consumidores — el
mismo patrón que `prerender.mjs` con `vista.js`.
