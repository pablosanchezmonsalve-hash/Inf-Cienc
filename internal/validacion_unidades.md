# Validación institucional de unidades académicas

**Generado** el 2026-08-26 por `src/review/build_unit_validation.py`. Regenerable.

## Qué se pide

El informe cienciométrico agrupa la producción por unidad académica. Esos nombres **no vienen de un catálogo oficial**: están deducidos de cómo aparecen escritos en las afiliaciones de Scopus, porque no había un catálogo disponible al construir la plataforma.

Mientras sigan sin validar, el indicador de producción por unidad se publica con confiabilidad baja y una advertencia que lo declara. Para retirar esa advertencia hacen falta tres cosas:

1. **Confirmar o corregir** el nombre oficial de cada unidad listada.
2. **Señalar las que no existen** o cambiaron de nombre en el período.
3. **Confirmar a qué facultad pertenece cada escuela** (segunda tabla).

No hace falta responder en ningún formato especial: basta con marcar sobre este documento.

---

## 1. Unidades detectadas

Sobre **1.207** apariciones firma × publicación de la ventana 2023–2025. **437** (36,2 %) no permiten deducir unidad y se declaran como «No determinada»: no se imputan.

| Unidad como aparece en el informe | Pares | ¿Nombre oficial correcto? | Corrección |
|---|---:|---|---|
| Facultad de Medicina | 529 | ☐ sí  ☐ no | |
| Facultad de Educación, Psicología y Familia | 51 | ☐ sí  ☐ no | |
| Facultad de Ingeniería | 50 | ☐ sí  ☐ no | |
| Facultad de Odontología | 34 | ☐ sí  ☐ no | |
| Facultad de Economía y Negocios | 28 | ☐ sí  ☐ no | |
| Escuela de Nutrición y Dietética | 24 | ☐ sí  ☐ no | |
| Escuela de Kinesiología | 22 | ☐ sí  ☐ no | |
| Facultad de Derecho | 6 | ☐ sí  ☐ no | |
| Facultad de Artes | 6 | ☐ sí  ☐ no | |
| Facultad de Comunicaciones y Humanidades | 4 | ☐ sí  ☐ no | |
| Facultad de Arquitectura y Diseño | 3 | ☐ sí  ☐ no | |
| Escuela de Enfermería | 3 | ☐ sí  ☐ no | |
| Escuela de Ciencias de la Familia | 2 | ☐ sí  ☐ no | |
| School of Medicine UFT-CLC | 1 | ☐ sí  ☐ no | |
| Facultad de Odontología y Ciencias de la Rehabilitación | 1 | ☐ sí  ☐ no | |
| School of Nutrition and Dietetic | 1 | ☐ sí  ☐ no | |
| Facultad de Educación y Ciencias Sociales | 1 | ☐ sí  ☐ no | |
| School of Civil Engineering | 1 | ☐ sí  ☐ no | |
| Facultad de Economía y Negocios en la Univ | 1 | ☐ sí  ☐ no | |
| School of Industrial Engineering | 1 | ☐ sí  ☐ no | |
| School of Engineering | 1 | ☐ sí  ☐ no | |

### Variantes de escritura que se agrupan bajo cada nombre

El sistema reconoce estas formas y las lleva al nombre canónico. Si falta alguna variante que use la universidad, indíquela.

| Nombre canónico | Variantes reconocidas |
|---|---|
| Facultad de Medicina | `Facultad de Medicina`, `Faculty of Medicine`, `Escuela de Medicina`, `School of Medicine` |
| Escuela de Kinesiología | `Escuela de Kinesiología`, `School of Kinesiology` |
| Escuela de Nutrición y Dietética | `Escuela de Nutrición y Dietética`, `School of Nutrition and Dietetics` |
| Facultad de Ingeniería | `Facultad de Ingeniería`, `Faculty of Engineering` |
| Facultad de Odontología | `Facultad de Odontología`, `Faculty of Dentistry`, `Escuela de Odontología`, `School of Dentistry` |
| Facultad de Educación, Psicología y Familia | `Facultad de Educación`, `Faculty of Education`, `Facultad de Educación Psicología y Familia`, `Facultad de Educación, Psicología y Familia`, `Escuela de Psicología`, `School of Psychology` |
| Facultad de Economía y Negocios | `Facultad de Economía y Negocios`, `Faculty of Economics and Business`, `School of Economics and Business` |
| Facultad de Derecho | `Facultad de Derecho`, `Faculty of Law`, `Escuela de Derecho`, `School of Law` |
| Facultad de Artes | `Facultad de Artes`, `Faculty of Arts`, `Facultad de Artes Visuales`, `Escuela de Artes Visuales`, `School of Arts` |
| Facultad de Arquitectura y Diseño | `Facultad de Arquitectura y Diseño`, `Faculty of Architecture and Design`, `Faculty of Archi-tecture and Design`, `Escuela de Arquitectura`, `School of Architecture` |
| Facultad de Comunicaciones y Humanidades | `Facultad de Comunicaciones y Humanidades`, `Facultad de Humanidades y Comunicaciones`, `Faculty of Communications and Humanities`, `Escuela de Historia`, `School of History` |
| Escuela de Enfermería | `Escuela de Enfermería`, `School of Nursing` |
| Escuela de Ciencias de la Familia | `Escuela de Ciencias de la Familia`, `School of Family Sciences` |

---

## 2. Jerarquía escuela → facultad

El informe suma la producción de cada escuela a su facultad. Una jerarquía equivocada mueve publicaciones de una facultad a otra, así que es la parte más sensible de esta validación.

| Escuela | Se suma a | Estado actual | ¿Correcto? | Corrección |
|---|---|---|---|---|
| Escuela de Kinesiología | Facultad de Medicina | **confirmada** | ☐ sí  ☐ no | |
| Escuela de Nutrición y Dietética | Facultad de Medicina | *inferida de los datos* | ☐ sí  ☐ no | |
| Escuela de Enfermería | Facultad de Medicina | *inferida de los datos* | ☐ sí  ☐ no | |
| Escuela de Ciencias de la Familia | Facultad de Educación, Psicología y Familia | *inferida de los datos* | ☐ sí  ☐ no | |

**3 de 4 jerarquías están inferidas**, no confirmadas. Son las que más importa revisar.

¿Falta alguna escuela o instituto que deba sumar a una facultad y no aparezca en esta tabla?

---

## 3. Evidencia: cómo aparece cada unidad en el origen

Una afiliación real por unidad, tal como la entrega Scopus. Sirve para juzgar si el nombre deducido es razonable.

**Facultad de Medicina** (529 pares)

> Escuela de Medicina, Universidad Finis Terrae, Santiago, 7501015, Chile, Faculty of Medicine and Science, Universidad San Sebastián, Santiago, 8420524, Chile

**Facultad de Educación, Psicología y Familia** (51 pares)

> Escuela de Psicología, Universidad Finis Terrae, Santiago de Chile, Chile

**Facultad de Ingeniería** (50 pares)

> Faculty of Engineering, Universidad Finis Terrae, Providencia, Santiago, Chile

**Facultad de Odontología** (34 pares)

> Clinic of Reconstructive Dentistry, Center for Dental Medicine, University of Zurich, Zurich, Switzerland, Center for Studies and Innovation in Dentistry, Faculty of Dentistry, Universidad Finis Terra

**Facultad de Economía y Negocios** (28 pares)

> Faculty of Economics and Business, University Finis Terrae, Chile

**Escuela de Nutrición y Dietética** (24 pares)

> Facultad de Medicina, Escuela de Nutrición y Dietética, Universidad Finis Terrae, Santiago, Chile

**Escuela de Kinesiología** (22 pares)

> Exercise Physiology and Metabolism Laboratory, School of Kinesiology, Universidad Finis Terrae, Santiago, 7501015, Chile

**Facultad de Derecho** (6 pares)

> Faculty of Law, Finis Terrae University, Santiago, Chile

**Facultad de Artes** (6 pares)

> Facultad de Artes, Universidad Finis Terrae

**Facultad de Comunicaciones y Humanidades** (4 pares)

> Escuela de Historia-CIDOC, Facultad de Humanidades y Comunicaciones, Universidad Finis Terrae, Chile

**Facultad de Arquitectura y Diseño** (3 pares)

> Laboratorio de Investigación Avanzada, Facultad de Arquitectura y Diseño, Universidad Finis Terrae (FAD-UFT), Santiago de Chile, Chile

**Escuela de Enfermería** (3 pares)

> Escuela de Enfermería, Universidad Finis Terrae, Santiago, Chile

**Escuela de Ciencias de la Familia** (2 pares)

> School of Family Sciences, Universidad Finis Terrae, Santiago, Chile

**School of Medicine UFT-CLC** (1 pares)

> Innate Immunity Laboratory, Immunology Program, Biomedical Sciences Institute, Faculty of Medicine, Universidad de Chile, Santiago, Chile, Center of Biomedical Research (CIBMED), School of Medicine UF

**Facultad de Odontología y Ciencias de la Rehabilitación** (1 pares)

> Universidad San Sebastián, Facultad de Odontología y Ciencias de la Rehabilitación, Carrera de Fonoaudiología, Santiago, Chile, Universidad Finis Terrae, Facultad de Educación, Psicología y Familia, S

**School of Nutrition and Dietetic** (1 pares)

> School of Nutrition and Dietetic, Finis Terrae University, Santiago, 7501014, Chile

**Facultad de Educación y Ciencias Sociales** (1 pares)

> Facultad de Educación y Ciencias Sociales, Universidad Finis Terrae, Chile

**School of Civil Engineering** (1 pares)

> School of Civil Engineering, Universidad Finis Terrae, Avenida Pedro de Valdivia 1509, Santiago, Providencia, Chile

**Facultad de Economía y Negocios en la Univ** (1 pares)

> Facultad de Economía y Negocios en la Univ. Finis Terrae, Chile

**School of Industrial Engineering** (1 pares)

> School of Industrial Engineering, Universidad Finis Terrae, Santiago, Chile

**School of Engineering** (1 pares)

> School of Engineering, Universidad Finis Terrae, Providencia, Santiago, Chile

---

## Qué pasa cuando esto vuelva respondido

Las correcciones entran en `config/matching_rules.yml` —vocabulario y jerarquía— y el estado de cada jerarquía pasa de `inferida` a `confirmada`. Con eso, el indicador de producción por unidad puede subir su confiabilidad y perder la advertencia sobre vocabulario no validado. **No requiere reescribir nada del sistema.**

Lo que **no** cambia: la cobertura. 437 pares seguirán sin unidad deducible porque su afiliación no la menciona, y seguirán declarándose como «No determinada» en vez de imputarse.
