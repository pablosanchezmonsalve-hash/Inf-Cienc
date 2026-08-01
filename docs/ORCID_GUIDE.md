# Cómo ejecutar el enriquecimiento de ORCID

**Pendiente V2-01** · Tiempo estimado: 10 minutos, la mayoría de espera.

ORCID no viene en los exports de Scopus ni de SciVal. Crossref lo publica por
DOI, gratis y sin registro, y el corpus tiene DOI en el 97,7 % de los
registros.

**Requisitos:** una máquina con Python 3.11+ y salida a internet. Nada más: sin
API key, sin cuenta, sin costo.

---

## Paso 1 — Traer el repositorio

Si ya lo tienes clonado:

```bash
cd Inf-Cienc
git checkout main
git pull
```

Si es la primera vez:

```bash
git clone https://github.com/pablosanchezmonsalve-hash/Inf-Cienc.git
cd Inf-Cienc
```

## Paso 2 — Instalar dependencias

```bash
pip install -r requirements.txt
```

Si `pip` no existe, prueba `pip3`. En Windows, `py -m pip install -r requirements.txt`.

## Paso 3 — Comprobar que todo está bien antes de salir a la red

```bash
python3 src/enrich/orcid_crossref.py --test
```

Verifica la lógica de emparejamiento con casos de prueba, sin tocar internet.
Debe terminar con:

```
TODOS LOS CASOS OK
```

Si esto falla, no sigas: hay algo roto en la instalación.

## Paso 4 — Prueba corta con 20 publicaciones

Antes de lanzar las 799, comprueba que hay conexión con Crossref:

```bash
python3 src/enrich/orcid_crossref.py --limit 20
```

Si ves avisos del tipo `URLError` o `timeout`, no hay salida a
`api.crossref.org` desde esa máquina. Prueba desde otra red.

## Paso 5 — La corrida completa

```bash
python3 src/enrich/orcid_crossref.py
```

**Tarda entre 3 y 5 minutos.** Imprime el avance cada 100 publicaciones.

Puedes cortarlo con `Ctrl+C` y reanudarlo: cada respuesta queda cacheada en
`data/cache/crossref/`, así que al reejecutar no vuelve a consultar lo ya
hecho.

Al terminar verás algo así:

```
  publicaciones con DOI: 799 de 823 (97,1 %)
  DOI sin registro en Crossref : 12
  errores de red               : 0
  firmas con ORCID asignado    : 187 de 589 (31,7 %)
    confianza alta : 142
    confianza media: 45
  conflictos encolados         : 9
```

> Los números concretos son ilustrativos. **No sabemos aún cuántos ORCID
> aparecerán**: depende de cuántos autores lo hayan declarado al publicar.

## Paso 6 — Reconstruir el sitio

```bash
make sitio
```

O, si `make` no está disponible:

```bash
python3 src/audit/run_all.py
python3 src/analysis/indicator_feasibility.py
python3 src/build/build_all.py
python3 src/build/06_assemble_site.py
```

Para verlo antes de publicar:

```bash
python3 -m http.server -d dist 8000
```

y abrir `http://localhost:8000/autores.html`. Entra a una ficha y comprueba que
el ORCID aparece enlazado donde antes decía «No disponible».

## Paso 7 — Publicar

```bash
git add data/interim/authors_orcid.csv internal/orcid_conflicts.csv .gitignore
git commit -m "Enriquecimiento de ORCID desde Crossref"
git push origin main
```

El caché (`data/cache/`) no se versiona: son ~800 archivos que se regeneran
solos.

---

## Qué produce

| Archivo | Capa | Contenido |
|---|---|---|
| `data/interim/authors_orcid.csv` | pública | Firma → ORCID, con confianza y nº de publicaciones que lo respaldan |
| `internal/orcid_conflicts.csv` | **interna** | Firmas con más de un ORCID, y homonimias dentro de una publicación |

En las fichas de autor:

- **ORCID enlazado** cuando la asignación es consistente.
- **«correspondencia probable»** cuando se apoya en una sola publicación o
  Crossref no declaró nombre de pila.
- **«No disponible en las fuentes actuales»** cuando no se encontró.

---

## Cómo empareja, y qué se niega a hacer

Por cada publicación, compara las firmas UFT con los autores que Crossref
declara, usando **apellido normalizado + inicial del nombre**.

Sólo asigna cuando la coincidencia es inequívoca:

| Situación | Qué hace |
|---|---|
| Un único autor coincide y tiene ORCID | Asigna, confianza alta |
| Crossref no declara nombre de pila | Asigna por apellido, confianza media |
| Las iniciales se contradicen (`Diaz F.` vs. `Diaz, Marcela`) | **No asigna** |
| Dos autores comparten apellido e inicial | **No asigna**, encola homonimia |
| La firma aparece con dos ORCID distintos | **No asigna**, encola conflicto |

No consolida identidades por su cuenta. Un ORCID emparejado por apellido e
inicial es una hipótesis verificable, no un dato de la fuente, y por eso viaja
siempre con su nivel de confianza.

---

## Si algo sale mal

| Síntoma | Causa | Solución |
|---|---|---|
| `URLError` o `timeout` en todos los DOI | Sin salida a `api.crossref.org` | Probar desde otra red |
| `ABORTADO: demasiados errores de red` | Más de 25 fallos seguidos | Revisar la conexión y reejecutar; el caché conserva lo hecho |
| `Sin hallazgos. No se escribe ningún archivo` | No se emparejó ningún ORCID | Revisar que `internal/matching_log.csv` exista; correr antes `python3 src/audit/run_all.py` |
| HTTP 429 de Crossref | Límite de tasa | Esperar unos minutos y reejecutar |
| Las fichas siguen sin ORCID | No se reconstruyó el sitio | Ejecutar `make sitio` |

---

## Qué desbloquea

Con ORCID, dos firmas que traen el mismo identificador **son la misma persona**
y no hay nada que decidir. Eso reduce buena parte de la revisión manual
pendiente:

- 123 variantes de nombre por resolver (T-03).
- 20 perfiles de Scopus fragmentados (T-04).
- Y con ellas, la red de coautoría (`C-05`), hoy diferida porque mostraría a
  una misma persona como varios nodos.

Los casos que ORCID no cubra seguirán necesitando revisión humana.
