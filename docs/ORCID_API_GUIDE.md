# Verificar los ORCID contra el registro público

**Capa:** pública · **Pendiente que ataca:** `T-14`, `T-15` y la calidad de las
174 asignaciones vigentes

---

## 1. Qué hace y por qué importa

Hoy los 174 ORCID del sitio son **hipótesis**. `orcid_crossref.py` los dedujo
cruzando apellido e inicial contra los autores que Crossref declara en cada DOI.
Que `Díaz F.` y `Díaz Fernández, Francisca` se parezcan no prueba que sean la
misma persona.

Este paso le pregunta al registro de ORCID, donde cada titular declara sus
propias obras y afiliaciones:

> ¿El titular de este ORCID declara **este artículo** entre sus obras?
> ¿Declara a esta universidad entre sus afiliaciones?

Una asignación cuyos DOI aparecen en el registro del titular **deja de ser una
conjetura**. Una cuyos DOI no aparecen en ninguna parte pasa a ser sospechosa y
se encola para revisión.

**No decide identidades.** Produce evidencia, que alimenta la herramienta de
revisión (`make revision`). La conclusión «estas dos firmas son la misma
persona» la sigue tomando una persona (decisión `D-08`).

---

## 2. Obtener las credenciales (gratis, unos minutos)

La API pública de ORCID exige un token. Es gratuito y no depende de ninguna
suscripción institucional.

1. Inicie sesión en **https://orcid.org** con su cuenta ORCID.
   Si no tiene, crearla es gratis.
2. Menú de su nombre → **Developer tools**. Puede pedirle verificar el correo.
3. Registre una **Public API client**. Pide un nombre, una URL y una
   descripción; para este uso vale el nombre del proyecto y la URL del sitio.
4. Le entregarán un **Client ID** (`APP-XXXXXXXXXXXX`) y un **Client Secret**.

> **Nunca escriba las credenciales en un archivo del repositorio.** Es público:
> quedarían expuestas en el mismo commit. Van en variables de entorno, y el
> script sólo las lee de ahí.

---

## 3. Ejecutar

Tres vías. La primera **no requiere instalar nada** y es la indicada si el
equipo está administrado por la institución y no permite instalar programas.

---

### Vía A · En GitHub, sin instalar nada  ← recomendada

El proyecto ya ejecuta Python en GitHub para construir el sitio. Esta
verificación puede correr en el mismo sitio.

Tiene una ventaja que no es sólo comodidad: **las credenciales viven cifradas
en los secretos del repositorio**, en vez de pasar por una consola o quedar en
un archivo local.

**Una sola vez —** guardar las credenciales:

1. En el repositorio, **Settings → Secrets and variables → Actions**.
2. **New repository secret**, dos veces:

   | Name | Secret |
   |---|---|
   | `ORCID_CLIENT_ID` | `APP-XXXXXXXXXXXX` |
   | `ORCID_CLIENT_SECRET` | el que entrega ORCID |

   Una vez guardados no se pueden volver a leer, ni siquiera desde la propia
   interfaz: es lo que se espera de un secreto.

**Cada vez que quiera ejecutarlo:**

1. Pestaña **Actions** → **«Verificar ORCID contra su registro»**.
2. **Run workflow**. Deje el límite en `10` la primera vez.
3. Al terminar, la propia página muestra una tabla con el recuento por
   veredicto, y el resultado queda:
   - guardado en el repositorio, si dejó marcada esa opción;
   - descargable en **Artifacts**, al final de la página, siempre.

Si algo falla, el registro de cada paso dice dónde.

---

### Vía B · Windows, con el asistente

Requiere Python instalado. Clic derecho sobre
`scripts\verificar-orcid.ps1` → **«Ejecutar con PowerShell»**. El asistente
comprueba Python, instala dependencias, prueba la lógica sin red, pide las
credenciales de forma oculta y empieza por 10 peticiones.

> **Si Python no está instalado y no tiene permisos de administrador**, pruebe
> el instalador oficial de python.org de todos modos: la opción por defecto
> instala en su carpeta de usuario y **normalmente no pide administrador**. Si
> aun así lo bloquea, use la **Vía A**, que no necesita nada instalado.

> Si Windows responde *«la ejecución de scripts está deshabilitada»*:
>
>     Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

---

### Vía C · A mano

Una línea cada vez, desde la carpeta del proyecto:

    export ORCID_CLIENT_ID='APP-XXXXXXXXXXXX'
    export ORCID_CLIENT_SECRET='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
    python3 src/enrich/orcid_api.py --test
    python3 src/audit/run_all.py
    python3 src/enrich/orcid_api.py --limit 10
    python3 src/enrich/orcid_api.py

En PowerShell, `$env:ORCID_CLIENT_ID = '...'` en lugar de `export`.

---

**Sea cual sea la vía, empiece por 10.** Si el token o el contrato de la API no
son los esperados, se ve en diez peticiones y no en trescientas.

Las respuestas se cachean en `data/cache/orcid/`, que no se versiona:
reejecutar no vuelve a golpear la API.

## 4. Qué produce

| Archivo | Capa | Qué contiene |
|---|---|---|
| `data/enriched/orcid_verificacion.csv` | pública · **versionar** | Un veredicto por asignación |
| `internal/orcid_hallazgos.csv` | interna | Sólo lo que exige mirada humana |

Cuatro veredictos posibles, y la diferencia entre ellos importa:

| Veredicto | Qué significa |
|---|---|
| **`confirmada`** | Al menos un DOI atribuido a esa firma aparece en el registro del titular. La asignación se sostiene |
| **`sin_coincidencia`** | El titular declara obras con DOI, y **ninguna** coincide. Señal de alarma: probablemente la asignación es de otra persona |
| **`no_verificable`** | El titular no declara ninguna obra con DOI. **No es un fallo**: muchos ORCID están registrados pero vacíos. Ni confirma ni refuta |
| **`sin_registro`** | El ORCID no existe o no es público |

`no_verificable` y `sin_coincidencia` **no son lo mismo**, y por eso son
categorías distintas: la primera es ausencia de evidencia, la segunda es
evidencia en contra.

---

## 5. Después de ejecutar

```bash
git add data/enriched/orcid_verificacion.csv
git commit -m "Verificación de ORCID contra el registro público"

make revision      # regenera la herramienta con la evidencia nueva
```

La herramienta de revisión gana una columna **«Verificado»**, y una señal nueva
en los casos donde ambas firmas tienen su ORCID confirmado: *«el titular declara
estas publicaciones como suyas»*. Esa es la evidencia más fuerte disponible para
resolver `T-14` y `T-15`, porque ya no depende de parecidos de apellido.

---

## 6. Límites honestos

- **No se ha ejercido contra la API real desde este repositorio.** El entorno
  donde se escribió bloquea `pub.orcid.org`. La lógica está cubierta por una
  autoprueba de 9 casos con registros de mentira (`--test`), que corre en cada
  build de CI, pero el contrato de la API —nombres de campo, formato de
  respuesta— está tomado de la documentación y **no verificado en vivo**. Si la
  primera ejecución con `--limit 10` falla al leer la respuesta, es ahí donde
  hay que mirar.
- **Verificar una publicación no verifica una identidad.** Que el titular
  declare un artículo confirma que *ese artículo* es suyo. Que dos firmas
  correspondan a la misma persona sigue siendo una conclusión humana.
- **Un registro vacío no dice nada.** Buena parte de los ORCID existen sin obras
  declaradas. Eso limita cuánto puede confirmarse, y por eso `no_verificable` es
  un resultado esperable y no un error.
- **La cobertura no sube con este paso.** Verifica lo que ya hay; no busca
  ORCID nuevos. Ampliar la cobertura por búsqueda de afiliación es un paso
  distinto, aún no implementado.
