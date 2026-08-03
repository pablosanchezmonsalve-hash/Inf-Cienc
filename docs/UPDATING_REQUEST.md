# Qué pedir en la próxima exportación de datos

**Capa:** pública · **Pendiente:** `T-06`

Este documento existe para que la siguiente carga de datos no herede la
ambigüedad que tiene la actual. No es una tarea de código: es lo que hay que
pedir, y a quién.

---

## 1. El problema, en una frase

**La exportación de Scopus no declara su fecha de corte.** La de SciVal sí
(2026-07-22), y por eso el sitio puede afirmar «citas actualizadas al
2026-07-22». La de Scopus sólo sabe cuándo se descargó el archivo (2026-07-31),
que no es lo mismo.

| Fuente | Rol | Fecha de corte declarada | Fecha de descarga |
|---|---|---|---|
| `scival_export` | primaria | **2026-07-22** | 2026-07-31 |
| `scopus_export` | primaria | **ninguna** | 2026-07-31 |

---

## 2. Por qué importa, y por qué importa menos de lo que parece

**Por qué importa.** Una base bibliográfica crece hacia atrás: un artículo de
2024 puede indexarse en 2026. Sin fecha de corte declarada no se puede afirmar
«estas son todas las publicaciones de 2023–2025», sólo «estas son las que había
cuando se descargó el archivo». Para un informe institucional que se compara
consigo mismo año a año, esa distinción es la diferencia entre una serie
reproducible y una que se mueve sola.

**Por qué importa menos de lo que parece.** Las cifras de citación —que son las
que más se mueven— vienen de SciVal, que **sí** declara su corte. Lo que queda
sin fechar es la cobertura: cuántas publicaciones había indexadas. Eso cambia
mucho más despacio.

---

## 3. Qué pedir exactamente

A quien administre la suscripción a Scopus, o a quien realice la exportación:

> Al exportar el conjunto de publicaciones desde Scopus, necesito que quede
> registrada **la fecha a la que están actualizados los datos**, no sólo la
> fecha en que se descargó el archivo. En la interfaz de Scopus aparece
> normalmente como *«Data last updated»* o equivalente en la cabecera del
> conjunto de resultados. Si la exportación no la incluye, basta con anotarla
> aparte junto con la consulta usada.
>
> Aprovecho para pedir también, si es posible:
>
> - **la cadena de consulta exacta** (`AF-ID`, rango de años, filtros aplicados);
> - **el recuento de resultados** que mostraba Scopus antes de exportar, para
>   comprobar que la exportación no se truncó.

---

## 4. Dónde entra la respuesta

En `config/sources.yml`, sin tocar código:

```yaml
  scopus_export:
    fecha_corte: "AAAA-MM-DD"      # la que devuelva la consulta
    consulta: "AF-ID(60105368) AND PUBYEAR > 2022 AND PUBYEAR < 2026"
    n_resultados_declarado: 000    # lo que mostraba Scopus
```

La regla de validación `V-07` ya comprueba que cada fuente de métricas declare
su fecha de corte, y hoy pasa porque la fuente de citación (SciVal) la tiene.
Cuando Scopus también la declare, la afirmación de cobertura del sitio deja de
apoyarse en una fecha de descarga.

---

## 5. Lo que este documento no resuelve

Que la exportación actual ya está hecha. Nada de esto se aplica
retroactivamente: la carga vigente seguirá sin fecha de corte de Scopus, y así
se declara en `docs/LIMITATIONS.md`. Esto es para la siguiente.
