# Reporte de validación — Fase 1

Generado por `src/audit/05_validation_rules.py`. Reejecutable.

| Regla | Severidad | Descripción | Resultado | Observado |
|---|---|---|---|---|
| `E-01` | bloqueante | Todo registro tiene EID con formato válido | **PASA** | 818/818 |
| `E-02` | bloqueante | EID único en cada fuente primaria | **PASA** | scopus=0 scival=0 |
| `E-03` | bloqueante | Cabecera de SciVal en la fila configurada | **PASA** | primera columna='Title' |
| `E-04` | bloqueante | Año dentro de la ventana declarada | **PASA** | rango observado=2023-2025 |
| `E-05` | bloqueante | Citas enteras y no negativas | **PASA** | mínimo=0 |
| `E-06` | alta | Sin columnas de cobertura nula en el universo activo | **FALLA** | vacías=['Molecular Sequence Numbers'] |
| `E-07` | alta | Sin columnas residuales de join en fuentes activas | **PASA** | detectadas en rdata (fuente de referencia, no activa): 6 |
| `E-08` | media | n de registros leído coincide con el declarado | **PASA** | declarado=816 leído=816 |
| `D-01` | bloqueante | Sin EID repetido | **PASA** | 0 |
| `D-02` | alta | Sin DOI repetido entre los no nulos | **PASA** | 0 |
| `D-03` | alta | Sin filas íntegramente duplicadas | **PASA** | 0 |
| `P-01` | alta | Duplicados probables por título marcados, no resueltos | **PASA** | 1 grupo(s) · 1 revisado(s) por una persona · 0 pendiente(s) |
| `P-03` | alta | Variantes de nombre encoladas sin colapso automático | **PASA** | 123 entradas |
| `P-04` | alta | Nombres con múltiples Scopus ID encolados | **PASA** | 20 entradas |
| `I-01` | bloqueante | Toda publicación tiene al menos una detección institucional | **PASA** | sin detección=0 |
| `I-04` | alta | Métodos duro y blando reconciliados sin contradicción | **PASA** | solo_duro=0 solo_blando=7 |
| `I-05` | bloqueante | Ningún patrón prohibido en uso | **PASA** | prohibidos declarados=['inis', 'finis'] |
| `I-06` | media | Unidad académica no imputada cuando no es inferible | **PASA** | cobertura=63.8 %, 437 pares etiquetados 'No determinada' |
| `I-08` | alta | Identificador institucional en configuración, no en código | **PASA** | scopus_affiliation_id=60105368 |
| `X-01` | alta | Discrepancias entre fuentes listadas nominalmente | **PASA** | solo_scopus=7 solo_scival=5 |
| `X-02` | alta | Año coincide entre fuentes | **PASA** | 0 |
| `X-03` | alta | DOI coincide entre fuentes | **PASA** | 0 |
| `X-04` | media | Diferencia de citas entre fuentes dentro de tolerancia (1 %) | **PASA** | scopus=3909 scival=3935 delta=+26 (+0.67 %) |
| `X-05` | bloqueante | Los .RData no alimentan indicadores publicables | **PASA** | rol=referencia en las tres entradas |
| `V-01` | bloqueante | Suma por año igual al total del universo | **PASA** | 823/823 |
| `V-03` | bloqueante | Suma de publicaciones por autor mayor al total (conteo completo) | **PASA** | suma_por_autor=1205 universo=823 |
| `V-06` | alta | Autores con n<5 marcables como no interpretables | **PASA** | 538/589 autores con n<5 |
| `V-07` | bloqueante | Fecha de corte declarada para la fuente de métricas | **PASA** | scival=2026-07-22 scopus=None |
| `V-10` | alta | Campos bajo el umbral de cobertura (80 %) identificados | **PASA** | ODS 37,9 % · Open Access 72,2 % · unidad académica 63.8 % (pares autor x publicación) |

**Reglas evaluadas:** 29 · **Pasan:** 28 · **Fallan:** 1 (bloqueantes: 0)
