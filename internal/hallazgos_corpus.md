# Hallazgos sobre el corpus

**Generado** el 2026-08-26 por `src/review/build_hallazgos.py`. Regenerable.

Esto **no es la cola de revisión de identidad**. Aquí no hay veredictos que aplicar: son preguntas sobre el corpus —qué publicaciones son de la institución y cuáles faltan— y responderlas cambia el alcance del informe, que es una decisión y no un botón.

> **Capa interna.** Nombra publicaciones concretas. No se publica.

---

## Detección institucional discrepante

**68 publicaciones** que este proyecto atribuye a la institución y OpenAlex no.

Dos lecturas, y decidir cuál exige mirar la publicación:

- **La desambiguación de OpenAlex falló.** Habitual cuando la afiliación viene truncada o escrita de forma poco canónica.
- **El patrón blando de este proyecto detectó de más.** Ésta es la que importa: sería un falso positivo en el universo, y la regla `I-05` existe porque el matching laxo ya produjo 16 verificados.

De las 68, **30** no traen ninguna institución en OpenAlex —ahí el silencio no dice nada— y **38** sí traen otra, que es donde conviene mirar.

| EID | Instituciones que sí atribuye OpenAlex |
|---|---|
| `2-s2.0-105000133447` | 01cby8j38 |
| `2-s2.0-105000407376` | 029ycp228 |
| `2-s2.0-105001686445` | 01rwn3f68 | 02jzgtq86 | 035b05819 |
| `2-s2.0-105003281114` | 00j5bwe91 | 03a8gac78 |
| `2-s2.0-105003831479` | 02ma57s91 |
| `2-s2.0-105004356535` | 047gc3g35 | 04jrwm652 |
| `2-s2.0-105005102289` | 02t46gq94 |
| `2-s2.0-105007847416` | 018906e22 | 01aj84f44 | 02crff812 | 040r8fr65 | 057w15z03 |
| `2-s2.0-105010226179` | 00j5bwe91 | 02zhqgq86 | 04teye511 | 05crjpb27 |
| `2-s2.0-105010261920` | 0166e9x11 | 01hrxxx24 | 038j0b276 | 04vdpck27 | 0589fsc66 |
| `2-s2.0-105011383287` | 02vbtzd72 | 040cnym54 | 04teye511 | 05ect4e57 |
| `2-s2.0-105011526303` | 00nqz4988 | 01jp7k726 | 02d9dg697 | 03f6y4g19 |
| `2-s2.0-105012890637` | 001w7jn25 | 00bq4rw46 | 00j5bwe91 | 00rqy9422 | 00xmtrb24 | 00za53h95 | 012jban78 | 0161xgx34 | 016bjqk65 | 016gd3115 | 016mey390 | 01d5vx451 | 01d86hn60 | 01esghr10 | 021e5j056 | 02218z997 | 026pg9j08 | 0270xt841 | 02cetwy62 | 02en5vm52 | 02mh9a093 | 02x4b0932 | 037zgn354 | 03ba28x55 | 03dbr7087 | 03gzbrs57 | 03r0ha626 | 03tc05689 | 03xjacd83 | 044t4x544 | 04cpxjv19 | 04ehjr030 | 04fwa4t58 | 04teye511 | 04y2hdd14 | 051escj72 | 051fd9666 | 05e56c835 | 05nd26619 | 05p52kj31 | 05r2g1b90 |
| `2-s2.0-105014254129` | 03mt12903 | 03v0qd864 | 047gc3g35 | 04dr2j587 | 04s1kgp90 | 04teye511 |
| `2-s2.0-105015299960` | 00h9jrb69 | 028ynny55 | 02bfwt286 | 02cafbr77 | 02t1bej08 | 04bpsn575 | 04teye511 | 05y33vv83 |
| `2-s2.0-105018969990` | 01aj84f44 | 035b05819 | 040r8fr65 | 0435rc536 |
| `2-s2.0-105021421573` | 012pnb193 | 01pp0fx48 | 04nvpdc40 |
| `2-s2.0-105032964720` | 000kjq947 | 034zgem50 |
| `2-s2.0-105034527029` | 05t8bcz72 |
| `2-s2.0-85145641767` | 00krbh354 | 0145fw131 | 014p6mg26 | 019yg0716 | 01a8ajp46 | 01t4k8953 | 02feahw73 | 02ma4wv74 | 02q1spa57 | 02rx3b187 | 02tcf7a68 | 035fsmk47 | 035xkbk20 | 04gqg1a07 | 04w3d2v20 | 04w9mdw91 | 05h9t7759 | 05n5mpz07 |
| `2-s2.0-85150044031` | 00gv7aj90 |
| `2-s2.0-85152245530` | 0326knt82 |
| `2-s2.0-85166670201` | 05x7k6a83 |
| `2-s2.0-85172361519` | 03n6nwv02 |
| `2-s2.0-85182999283` | 028ynny55 |
| … | y 13 más en el CSV |

---

## La brecha de cobertura

**414 obras** que OpenAlex atribuye a la institución y el universo no tiene.

> **Nada de esto entra al corpus.** Scopus y OpenAlex indexan con criterios distintos y sumarlos produce una cifra que nadie puede reconciliar (`D-206`). Si alguna vez entrara, entraría como corpus paralelo declarado, con su propia entrada en `config/sources.yml` y su propio denominador.

| Motivo | Obras |
|---|---:|
| con DOI, y ese DOI no está en el universo | 385 |
| OpenAlex no le asigna DOI: no se puede afirmar que falte | 29 |

### Las 385 que sí miden la brecha

Con DOI y dentro de la ventana: de éstas sí se puede afirmar que el universo no las tiene.

**Por año** — 2023: 104, 2024: 134, 2025: 147

**Por tipo documental** — article: 282, preprint: 43, conference-abstract: 14, editorial: 11, book-chapter: 10, review: 6, other: 4, peer-review: 4

| Año | Título | DOI |
|---|---|---|
| 2023 | A literature review on an IoT-based intelligent smart energy management systems  | <https://doi.org/10.1016/j.hybadv.2023.100136> |
| 2023 | Microtubule-mediated GLUT4 trafficking is disrupted in insulin-resistant skeleta | <https://doi.org/10.7554/elife.83338> |
| 2025 | Absolute neutrophil count and adverse drug reaction monitoring during clozapine  | <https://doi.org/10.1016/s2215-0366(25)00098-7> |
| 2025 | Techno-economic assessment of a green hydrogen production plant for a mining ope | <https://doi.org/10.1016/j.ijhydene.2025.02.164> |
| 2025 | Intracellular and extracellular redox signals during exercise and aging | <https://doi.org/10.1016/j.freeradbiomed.2025.10.283> |
| 2025 | Implementation of real-time optimal load scheduling for IoT-based intelligent sm | <https://doi.org/10.1186/s43067-025-00198-w> |
| 2024 | An IoT Enabled Energy Management System with Precise Forecasting and Load Optimi | <https://doi.org/10.1007/s41403-024-00498-z> |
| 2023 | influencia del clima escolar en el aprendizaje | <https://doi.org/10.38123/rre.v3i2.300> |
| 2025 | The role of cellular senescence in endothelial dysfunction and vascular remodell | <https://doi.org/10.1113/jp287387> |
| 2025 | Novel pembrolizumab-based treatments as first-line therapy in advanced clear-cel | <https://doi.org/10.1016/j.annonc.2025.10.010> |
| 2025 | A review of IoT enabled intelligent smart energy management for photovoltaic pow | <https://doi.org/10.1016/j.uncres.2025.100279> |
| 2025 | Rectus femoris tendon: An emerging option in ACL reconstruction | <https://doi.org/10.1002/ksa.70242> |
| 2025 | Anatomical variants of the vertebral artery and their relationship with cranioce | <https://doi.org/10.1007/s12565-025-00855-0> |
| 2025 | UCI Sports Nutrition Project: The Science of Successful Cycling Performance | <https://doi.org/10.1123/ijsnem.2025-0157> |
| 2024 | Participación parental en educación básica latinoamericana: revisión sistemática | <https://doi.org/10.20511/pyr2024.v12.2000> |
| 2025 | Unraveling the association between obesity and climacteric symptoms: a generaliz | <https://doi.org/10.1097/gme.0000000000002620> |
| 2025 | Reliable pain and function outcomes but limited sport performance after high tib | <https://doi.org/10.1002/ksa.70223> |
| 2023 | Energy homeostasis model for electrical and thermal systems integration in resid | <https://doi.org/10.3389/fenef.2023.1258384> |
| 2023 | Liderazgo en la educación parvularia Chilena durante la pandemia: experiencias y | <https://doi.org/10.1590/s1678-4634202349263089esp> |
| 2023 | Racionalización y mercadización: una mirada en la discusión sobre neoliberalismo | <https://doi.org/10.31619/caledu.n59.1378> |
| 2024 | Adult Code Sepsis: A Narrative Review of its Implementation and Impact | <https://doi.org/10.1177/08850666241293034> |
| 2024 | educación emocional en la primera infancia: Implicancia de las prácticas docente | <https://doi.org/10.38123/rre.v4i2.429> |
| 2025 | ¿Hacia una Política de Educación Sexual Integral en Chile? Percepciones de profe | <https://doi.org/10.5354/0718-2236.2025.78773> |
| 2025 | Reduction of the formation and toxicity of heterocyclic aromatic amines (PhIP, I | <https://doi.org/10.1080/10408398.2025.2534173> |
| 2025 | UCI Sports Nutrition Project: Special Environments | <https://doi.org/10.1123/ijsnem.2025-0101> |
| … | y 360 más en el CSV | |

