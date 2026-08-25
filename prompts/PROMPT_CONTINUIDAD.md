<role>
Continúas un proyecto en curso: plataforma web de informes cienciométricos
institucionales. No parte de cero.
</role>

<arranque>
Lee **STATE.md** y nada más.

Contiene el estado de las fases, las cifras canónicas, las colas de revisión
abiertas, los pendientes y el índice de decisiones. Está generado desde el
repositorio, así que no puede estar desactualizado respecto de los datos.

**No leas PLAN.md, SESSION_NOTES.md ni docs/ por adelantado.** Son ~3.700
líneas de referencia. STATE.md trae un mapa que indica cuál abrir para cada
pregunta concreta; ábrelo sólo cuando tengas esa pregunta.
</arranque>

<si_state_md_falta_o_esta_viejo>
Regenéralo antes de nada:

    python3 src/state/snapshot.py

Si sus cifras contradicen a PLAN.md o a config/, **manda la fuente, no
STATE.md**: es una vista derivada, no una autoridad. Regenerar resuelve la
discrepancia. Si persiste, hay un defecto en el generador y hay que declararlo.
</si_state_md_falta_o_esta_viejo>

<reglas_heredadas>
Vigentes desde la Fase 1, ya validadas. No se reabren sin una razón nueva:

- No inventar datos, columnas, métricas ni relaciones.
- Un indicador que no se puede calcular se declara, se explica qué falta y se
  deja como placeholder. No se aproxima.
- Ambigüedades y duplicados probables se **encolan**, nunca se resuelven
  automáticamente. Vale sobre todo para identidad de autor: afirmar que dos
  firmas son la misma persona es afirmar algo sobre alguien real.
- Capa pública y capa interna separadas. `internal/` no se despliega, y una
  compuerta del build lo verifica.
- Todo indicador declara su denominador, su fuente y su fecha de corte.

El índice completo está en `docs/DECISIONS.md`, una línea por decisión. Decía
«92» y van muchas más: la cifra la publica STATE.md, que se regenera. Léelo sólo
si vas a tocar algo que podría contradecirlas.
</reglas_heredadas>

<antes_de_dar_algo_por_terminado>
    make sitio

Corre auditoría, validación, artefactos y ensamblado. Tres compuertas lo
detienen si algo está mal: reglas bloqueantes fallando, capa interna filtrada a
lo público, o `data/raw/` colándose en el bundle.

Luego:

    python3 src/state/snapshot.py

Para que STATE.md refleje lo que acabas de hacer.
</antes_de_dar_algo_por_terminado>

<cierre_de_sesion>
Añade una sección a SESSION_NOTES.md con: decisiones tomadas (numeradas
`D-xx`, que el generador indexa solo), archivos creados o modificados,
supuestos que resultaron falsos, ambigüedades abiertas y próximo paso.

Los supuestos descartados importan tanto como las decisiones: evitan que la
siguiente sesión repita un camino ya recorrido.
</cierre_de_sesion>

<formato_de_respuesta>
1. Objetivo de la sesión.
2. Hallazgos.
3. Decisiones tomadas.
4. Archivos creados o modificados.
5. Dudas críticas.
6. Próximo paso.
</formato_de_respuesta>
