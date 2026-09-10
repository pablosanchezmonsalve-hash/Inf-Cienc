# Reporte de validación — Fase 1

Generado por `src/audit/05_validation_rules.py`. Reejecutable.

| Regla | Severidad | Descripción | Resultado | Observado |
|---|---|---|---|---|
| `E-01` | bloqueante | Todo registro tiene EID con formato válido | **PASA** | 1342/1342 |
| `E-02` | bloqueante | EID único en cada fuente primaria | **PASA** | scopus=0 scival=0 |
| `E-03` | bloqueante | Cabecera de SciVal en la fila configurada | **PASA** | primera columna='Title' |
| `E-04` | bloqueante | Año dentro de la ventana declarada | **PASA** | rango observado=2020-2025 |
| `E-05` | bloqueante | Citas enteras y no negativas | **PASA** | mínimo=0 |
| `E-06` | alta | Sin columnas de cobertura nula en el universo activo | **FALLA** | vacías=['Molecular Sequence Numbers'] |
| `E-07` | alta | Sin columnas residuales de join en fuentes activas | **PASA** | fuente de referencia no leída (paquete `rdata` ausente); no afecta a las fuentes activas |
| `E-08` | media | n de registros leído coincide con el declarado | **PASA** | declarado=1342 leído=1342 |
| `D-01` | bloqueante | Sin EID repetido | **PASA** | 0 |
| `D-02` | alta | Sin DOI repetido entre los no nulos | **FALLA** | 2 |
| `D-03` | alta | Sin filas íntegramente duplicadas | **PASA** | 0 |
| `P-01` | alta | Duplicados probables por título marcados, no resueltos | **PASA** | 3 grupo(s) · 1 revisado(s) por una persona · 2 pendiente(s) |
| `P-03` | alta | Variantes de nombre encoladas sin colapso automático | **PASA** | 207 entradas |
| `P-04` | alta | Nombres con múltiples Scopus ID encolados | **PASA** | 29 entradas |
| `E-09` | alta | Firmas sin forma de persona encoladas, no eliminadas | **PASA** | 4 firma(s) · 4 publicación(es) quedarían sin autoría UFT nombrada si se descartaran |
| `I-01` | bloqueante | Toda publicación tiene al menos una detección institucional | **PASA** | sin detección=1 · 1 resuelta(s) por una persona y corroborada(s) por el método duro · 0 pendiente(s) |
| `I-04` | alta | Métodos duro y blando reconciliados sin contradicción | **PASA** | solo_duro=1 (1 revisado(s) por una persona · 0 pendiente(s)) solo_blando=0 |
| `I-05` | bloqueante | Ningún patrón prohibido en uso | **PASA** | prohibidos declarados=['inis', 'finis'] |
| `I-06` | media | Unidad académica no imputada cuando no es inferible | **PASA** | cobertura=64.2 %, 703 pares etiquetados 'No determinada' |
| `I-08` | alta | Identificador institucional en configuración, no en código | **PASA** | scopus_affiliation_id=60105368 |
| `X-01` | alta | Discrepancias entre fuentes listadas nominalmente | **PASA** | solo_scopus=0 solo_scival=0 |
| `X-02` | alta | Año coincide entre fuentes | **PASA** | 0 |
| `X-03` | alta | DOI coincide entre fuentes | **PASA** | 0 |
| `X-04` | media | Diferencia de citas entre fuentes dentro de tolerancia (1 %) | **FALLA** | scopus=14421 scival=14245 delta=-176 (-1.22 %) |
| `X-05` | bloqueante | Los .RData no alimentan indicadores publicables | **PASA** | rol=referencia en las tres entradas |
| `V-01` | bloqueante | Suma por año igual al total del universo | **PASA** | 1342/1342 |
| `V-03` | bloqueante | Suma de publicaciones por autor mayor al total (conteo completo) | **PASA** | suma_por_autor=1960 universo=1342 |
| `V-06` | alta | Autores con n<5 marcables como no interpretables | **PASA** | 818/888 autores con n<5 |
| `V-07` | bloqueante | Fecha de corte declarada para la fuente de métricas | **PASA** | scival=2026-08-30 scopus=sin declarar (T-06) |
| `V-10` | alta | Campos bajo el umbral de cobertura (80 %) identificados | **PASA** | ODS 38.8 % · Open Access 70.3 % · unidad académica 64.2 % (pares autor x publicación) |

**Reglas evaluadas:** 30 · **Pasan:** 27 · **Fallan:** 3 (bloqueantes: 0)
