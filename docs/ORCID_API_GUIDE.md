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

### Windows — la forma recomendada

En el Explorador de archivos, entre en la carpeta del proyecto, luego en
`scripts`, y haga **clic derecho sobre `verificar-orcid.ps1` → «Ejecutar con
PowerShell»**.

Eso es todo. El asistente se encarga del resto: comprueba que Python esté
instalado, instala lo que falte, prueba la lógica sin tocar la red, corre la
auditoría si hace falta, **pide las credenciales de forma oculta** y empieza por
una prueba de 10 antes de ofrecerle las 174.

No hay que copiar comandos ni definir variables a mano. El Client Secret se
teclea una vez, no se guarda en ningún archivo y no queda en el historial de la
consola.

> Si Windows responde *«la ejecución de scripts está deshabilitada»*, abra
> PowerShell y ejecute una sola vez:
>
>     Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
>
> Es el ajuste que Microsoft recomienda para scripts propios.

### macOS, Linux, o si prefiere hacerlo a mano

Una línea cada vez, desde la carpeta del proyecto:

    export ORCID_CLIENT_ID='APP-XXXXXXXXXXXX'
    export ORCID_CLIENT_SECRET='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
    python3 src/enrich/orcid_api.py --test
    python3 src/audit/run_all.py
    python3 src/enrich/orcid_api.py --limit 10
    python3 src/enrich/orcid_api.py

**Empiece siempre por `--limit 10`.** Si el token o el contrato de la API no son
los esperados, se ve en diez peticiones y no en trescientas.

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
