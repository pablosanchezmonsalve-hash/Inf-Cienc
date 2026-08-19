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
