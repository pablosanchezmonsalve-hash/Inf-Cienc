# Formato del informe exportable a PDF · FUENTE HISTÓRICA CONGELADA

> **Congelado el 2026-09-16** (`D-607`). Esto **no describe el producto actual**.
> Se conserva como registro del criterio con que se diseñó el informe en papel,
> no como especificación de nada.
>
> **Dónde manda hoy el formato del papel:**
> [`web/assets/css/app.css`](../../web/assets/css/app.css) (la hoja de
> impresión, que es la fuente), [`src/build/informe_pdf.mjs`](../../src/build/informe_pdf.mjs)
> (el generador del PDF institucional) y [`docs/UX_UI.md`](../../docs/UX_UI.md)
> §12.7 bis (lo que ese formato tiene que conservar).

---

## Por qué se congela en vez de refrescarse

Porque **la vía que estos artboards especificaban ya se recorrió sin ellos**.

Su propia sección «vía de implementación acordada» pedía una hoja de estilo de
impresión con 0 KB de JavaScript, servida al botón «Exportar» y usada por
Playwright en el build para el PDF canónico. Eso está construido y verificado:
carátula, índice con números de hoja leídos del PDF ya compuesto, folio, unidad
de lectura de cinco partes por figura, y `src/verify/impresion.mjs` comprobando
sobre el texto del PDF y no sobre el DOM.

Refrescarlos no habría añadido nada al producto y habría creado **dos fuentes
para el mismo formato**, que es la condición para que diverjan. Mantenerlos al
día, además, es trabajo recurrente en cada carga de datos: `D-387` ya lo había
declarado —«refrescarla es una tarea de diseño con su propio criterio de
banda/paleta, no una corrección de una línea»— y lo dejó abierto. Esto lo cierra.

## Qué refleja, y por qué ya no rige

| | Lo que fijan estos artboards | Lo vigente |
|---|---|---|
| **Paleta** | La institucional de `D-381`: Ink Black `#071e22`, Deep Ocean `#1d7874`, Peach Glow `#f4c095`, papel `#fdf8f2` | **Paleta H, vino y champán** (`D-596`), desde el 2026-09-01 |
| **Composición** | La banda como unidad narrativa | El explorador la sustituyó; sobrevive sólo como suelo de contraste de los diferidos (`D-597`) |
| **Corpus** | 823 publicaciones · 3.935 citas · FWCI 0,87 · 51,2 % · 556 · 1.207 pares | **1.342 publicaciones**, ventana 2020–2025, 829 entidades |
| **Consolidación** (apéndice) | 63 formas → 30 personas | **94 formas → 39 personas** |

Y una de sus dos reglas medidas **es nula en el medio para el que se dibujó**:
«la ausencia va sobre Ink Black, donde mide 4,71:1» no se cumple en papel,
porque `D-552` decidió imprimir la banda de contraste **en tinta sobre blanco**
—su tinta clara depende de un ajuste del diálogo de impresión que va apagado por
defecto—. En el papel no hay suelo Ink Black sobre el que poner nada.

## Qué se conserva de aquí, y dónde está vivo

El criterio, no el marcado. Estas cinco reglas siguen gobernando el informe, y
viven hoy en la hoja de impresión y en `docs/UX_UI.md` §12.7 bis:

1. **Cada cifra lleva su denominador visible** (`D-16`).
2. **Cada bloque lleva su sello de procedencia**: fuente y fecha de corte.
3. **Cada eje lleva el panel «responde / no responde»**, de `docs/EJES.md`.
4. **Las advertencias van fuera de la familia visual del dato.**
5. **El apéndice metodológico no es opcional.** Un informe sin él no es
   interpretable.

## Los archivos

| Archivo | Qué es |
|---|---|
| `Portada.dc.html` | Cifras de cabecera, procedencia y marca de borrador |
| `Main.dc.html` | Página de eje: panel «responde / no responde» y dos indicadores |
| `Tabla.dc.html` | Página de tabla de datos con denominador y sello |
| `Apendice.dc.html` | Denominadores, evidencia de ORCID y limitaciones declaradas |
| `canvas.json` | Disposición de los artboards y notas del encargo |

Cada `.dc.html` abre con el sello de congelación, para que no haga falta llegar
hasta aquí para saberlo. El archivo ensamblado
(`informe-cienciometrico-pdf.html`, ~2 MB) nunca se versionó: era el editor
empaquetado alrededor de estos cinco y se regeneraba.

## Si alguna vez hace falta un lienzo vigente

Se parte de la paleta y del sistema de **hoy**, no de éste. Copiar estos
artboards y cambiarles los colores reproduciría además su composición por
bandas, que el sitio ya no usa, y su regla de la ausencia, que el papel no
admite. Serían tres errores heredados por ahorrarse un lienzo nuevo.
