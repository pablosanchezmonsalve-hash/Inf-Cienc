"""Higiene del código de presentación: nada declarado que no se use, nada usado
que no esté declarado. Se corre sobre el sitio construido, que es lo que se
despliega, y no sobre `web/`: lo que importa es lo que viaja.

Uso:  python3 src/verify/higiene.py [dist]
"""
import re, pathlib, json, sys

DIST = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'dist')
css = (DIST / 'assets/css/app.css').read_text(encoding='utf-8')
js = '\n'.join(p.read_text(encoding='utf-8') for p in sorted((DIST / 'assets/js').glob('*.js')))
html = '\n'.join(p.read_text(encoding='utf-8') for p in sorted(DIST.glob('*.html')))
marcado = html + '\n' + js

# El comentario de la hoja cita nombres de token en prosa; se descarta para no
# contar una mención en un párrafo como un uso real.
css_codigo = re.sub(r'/\*.*?\*/', '', css, flags=re.S)

fallos = []

# ---- 1. Variables CSS: declaradas vs usadas
declaradas = set(re.findall(r'(--[a-z0-9-]+)\s*:', css_codigo))
# Los tokens de dato se consumen desde el JS, algunos por plantilla
# (`var(--serie-${i+1})`), así que el JS cuenta como consumidor.
usadas = set(re.findall(r'var\(\s*(--[a-z0-9-]+)', css_codigo + js))
usadas |= {f'--serie-{i}' for i in range(1, 7)} if 'var(--serie-${' in js else set()
usadas |= {f'--ord-{i}' for i in range(1, 5)} if '--ord-1' in js else set()
# `var(--serie-${i + 1})` deja un prefijo suelto al leerlo con expresión
# regular; no es una variable, es media plantilla.
usadas = {v for v in usadas if not v.endswith('-')}
sin_declarar = usadas - declaradas
sin_usar = declaradas - usadas
for v in sorted(sin_declarar):
    fallos.append(f'variable usada y NO declarada: {v}')
print(f'  variables CSS: {len(declaradas)} declaradas · {len(usadas)} usadas')
if sin_usar:
    print(f'    declaradas sin usar ({len(sin_usar)}): {", ".join(sorted(sin_usar))}')

# ---- 2. Clases CSS: declaradas vs presentes en el marcado
clases_css = set(re.findall(r'\.([a-záéíóúñ][a-z0-9áéíóúñ_-]*)', css_codigo, re.I))
# Palabras que aparecen tras un punto pero no son clases (decimales, ficheros).
clases_css = {c for c in clases_css if not c[0].isdigit()}
# `http://www.w3.org/2000/svg` dentro de un data URI no declara clases.
clases_css -= {'org', 'w3'}
clases_marcado = set()
for m in re.finditer(r'class="([^"]*)"', marcado):
    clases_marcado.update(m.group(1).split())
# class="a ${cond ? 'b' : ''}" no cierra la comilla antes de la interpolación.
for m in re.finditer(r'class="([^"]{0,200}?)(?:\$\{|")', marcado):
    clases_marcado.update(re.findall(r'[a-záéíóúñ][\w-]*', m.group(1), re.I))
clases_marcado.update(re.findall(r"'([a-z][\w-]*)'", js))
for m in re.findall(r'className\s*\+=\s*.([\w\s-]+)', marcado):
    clases_marcado.update(m.split())
# `class="num ${cond ? 'ordenada' : ''}"` dentro de plantilla literal.
clases_marcado.update(re.findall(r'[\'"`]([a-záéíóúñ][\w-]*)[\'"`]', js, re.I))
# Nombres compuestos por plantilla: nota-orcid-${clase} -> prefijo.
prefijos = set(re.findall(r'([a-z][\w-]*-)\$\{', js))
for m in re.finditer(r"classList\.(?:add|remove|toggle)\('([^']+)'", js):
    clases_marcado.add(m.group(1))
for m in re.finditer(r'className\s*=\s*[\'"]([^\'"]+)', js):
    clases_marcado.update(m.group(1).split())
huerfanas = sorted(c for c in clases_css - clases_marcado
                   if not any(c.startswith(p) for p in prefijos))
print(f'  clases CSS: {len(clases_css)} declaradas · {len(clases_css & clases_marcado)} en uso')
if huerfanas:
    print(f'    sin aparecer en el marcado ({len(huerfanas)}): {", ".join(huerfanas)}')

# ---- 3. Exportaciones JS: declaradas vs importadas/usadas
exportadas = set(re.findall(r'export (?:async )?(?:function|const) ([a-zA-Z_$][\w$]*)', js))
sin_uso = set()
for nombre in exportadas:
    # se usa si aparece como c.nombre, v.nombre, o suelto en otro archivo
    if not re.search(rf'\b[a-z]\.{re.escape(nombre)}\b', js) and \
       len(re.findall(rf'\b{re.escape(nombre)}\b', js)) <= 1:
        sin_uso.add(nombre)
print(f'  exportaciones JS: {len(exportadas)} · sin consumidor: {len(sin_uso)}')
if sin_uso:
    print(f'    {", ".join(sorted(sin_uso))}')

# ---- 4. Identificadores que el JS busca y que deben existir en algún HTML
ids_html = set(re.findall(r'\bid="([^"]+)"', html))
ids_js = set(re.findall(r"getElementById\('([^']+)'\)", js))
# Estos los crea el propio JS al pintar la paginación o el estado vacío.
EFIMEROS = {'ant', 'sig', 'limpiar2'}
faltan = sorted(i for i in ids_js - ids_html - EFIMEROS)
print(f'  getElementById: {len(ids_js)} distintos · ausentes del HTML: {len(faltan)}')
if faltan:
    print(f'    {", ".join(faltan)}')

# ---- 5. Coherencia de artefactos: todo indicador pedido por una página existe
series = json.loads((DIST / 'data/series.json').read_text(encoding='utf-8'))
for p in sorted(DIST.glob('*.html')):
    m = re.search(r'data-indicadores="([^"]+)"', p.read_text(encoding='utf-8'))
    if not m:
        continue
    for cod in [c.strip() for c in m.group(1).split(',')]:
        if cod not in series:
            fallos.append(f'{p.name} pide {cod} y series.json no lo trae')
        elif f'id="{cod}"' not in p.read_text(encoding='utf-8'):
            fallos.append(f'{p.name} pide {cod} y el HTML pre-renderizado no lo contiene')

# ---- 6. La capa interna no puede haber viajado
PROHIBIDOS = ['matching_log', 'ambiguities_', 'orcid_conflicts', 'identity_candidates',
              'identity_decisions', 'orcid_candidatos_afiliacion']
for term in PROHIBIDOS:
    colados = [str(p.relative_to(DIST)) for p in DIST.rglob('*')
               if p.is_file() and term in p.read_bytes()[:2_000_000].decode('utf-8', 'ignore')]
    if colados:
        fallos.append(f'término interno «{term}» presente en: {colados[:4]}')

print()
if fallos:
    print(f'  {len(fallos)} FALLO(S):')
    for f in fallos:
        print(f'    ✗ {f}')
    sys.exit(1)
print('  Sin fallos de higiene.')
