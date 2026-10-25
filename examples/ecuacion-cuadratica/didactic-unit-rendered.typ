// --- Plantilla Estándar de Unidad Didáctica y Secuencia de Aprendizaje en Typst ---
#set page(
  paper: "us-letter",
  margin: (top: 2cm, bottom: 2cm, left: 2cm, right: 2cm),
  header: [
    #grid(
      columns: (1fr, 1fr),
      align(left)[*DISEÑO CURRICULAR E INGENIERÍA DIDÁCTICA*],
      align(right)[#datetime.today().display("[day]/[month]/[year]")],
    )
    #v(-4pt)
    #line(length: 100%, stroke: 0.6pt + luma(120))
  ],
  footer: [
    #align(center)[#context counter(page).display("1")]
  ]
)

#set text(
  lang: "es",
  size: 10.5pt,
)

// --- Título de la Unidad ---
#align(center)[
  #text(size: 16pt, weight: "bold", fill: rgb("#0f172a"))[PLANIFICACIÓN DE UNIDAD DIDÁCTICA] \
  #text(size: 13pt, weight: "semibold", fill: rgb("#1e40af"))[Modelización y Raíces de Funciones Cuadráticas]
]

#v(8pt)

// --- Ficha Técnica y Metadatos ---
#table(
  columns: (1.5fr, 1fr, 1.2fr, 1fr),
  stroke: 0.5pt + luma(120),
  fill: (col, row) => if row == 0 { rgb("#f1f5f9") } else { none },
  inset: 6pt,
  [*Nivel Educativo:*], [*Sesiones:*], [*Duración por Sesión:*], [*Currículo:*],
  [2° Medio / Grado 10], [4 sesiones], [90 min], [Bases Curriculares Mineduc - OA 04 / SEP NEM Fase 6]
)

#v(8pt)

// --- Fundamentación Teórica & Articulación (Networking) ---
#rect(
  width: 100%,
  fill: rgb("#f8fafc"),
  stroke: 0.8pt + rgb("#cbd5e1"),
  radius: 3pt,
  inset: 8pt
)[
  #text(weight: "bold", fill: rgb("#0f172a"))[1. Marco Teórico y Articulación Metodológica (Radford / Bikner-Ahsbahs):] \
  #text(size: 9.5pt)[*Marcos Activos:* brousseau-tds, duval-trrs] \
  #v(2pt)
  #text(size: 9.5pt)[Articulación metodológica entre la Teoría de Situaciones Didácticas (Brousseau) para la gestión del medio a-didáctico y los Registros de Representación Semiótica (Duval) para la conversión entre registro gráfico, algebraico y tabular.
]
]

#v(10pt)

// --- Diagnóstico Epistemológico y Obstáculos (MTSK-KFLM) ---
#text(weight: "bold", size: 11pt, fill: rgb("#0f172a"))[2. Diagnóstico Cognitivo y Obstáculos Epistemológicos (MTSK):] \
#text(size: 9.5pt)[*Prerrequisitos Indispensables:* Resolución de ecuaciones de primer grado, Concepto de función y evaluación de imágenes numéricas, Teorema de Pitágoras y plano cartesiano] \
#v(4pt)
#table(
  columns: (1fr, 2fr, 2.5fr),
  stroke: 0.5pt + luma(130),
  fill: (col, row) => if row == 0 { rgb("#f1f5f9") } else { none },
  inset: 5pt,
  [*Código*], [*Concepción Errónea / Obstáculo*], [*Estrategia de Confrontación*],
  [*CONFUSION_VERTICE_CON_RAIZ*], [El estudiante asume que el tiempo en que el proyectil toca el suelo ($h=0$) coincide con la altura máxima.], [Contrastar con simulador GeoGebra la simetría de la parábola respecto al eje vertical del vértice.],
  [*SIGNO_MENOS_CUADRATICO*], [Al evaluar $-5 t^2$ para $t=2$, calcula $(-5  dot  2)^2 = 100$ en lugar de $-5  dot  4 = -20$.], [Uso de paréntesis explícitos y discusión de la jerarquía de operaciones de potencias frente al producto.]
)


#v(12pt)

// --- Secuencia de Aprendizaje por Fases (Brousseau & Stein-Smith) ---
#text(weight: "bold", size: 11pt, fill: rgb("#0f172a"))[3. Secuencia de Aprendizaje e Ingeniería de Situaciones:]

#rect(
  width: 100%,
  stroke: 0.7pt + rgb("#3b82f6"),
  radius: 3pt,
  inset: 8pt
)[
  #grid(
    columns: (3fr, 1.5fr),
    [#text(weight: "bold", size: 10.5pt, fill: rgb("#1e40af"))[Fase 1: Situación de Acción: Lanzamiento Experimental e Indagación]],
    [#align(right)[#text(size: 8pt, weight: "bold", fill: rgb("#1d4ed8"))[Demanda: HACIENDO_MATEMATICA]]]
  )
  #v(3pt)
  *Actividad del Estudiante:* En parejas, tabulan tiempos y alturas buscando deducir cuándo el objeto deja de subir y cuándo impacta el suelo. \
  #v(2pt)
  *Rol y Mediación Docente:* Presenta el problema del proyectil sin enunciar fórmulas de vértice ni factorización. Devuelve las preguntas al medio experimental. \
  #v(2pt)
  *Justificación de Ejemplos (Rowland):* Se escoge la función $h(t) = -5 t^2 + 20 t$ porque sus raíces ($0$ y $4$) y vértice ($t=2, h=20$) son enteros fácilmente manipulables. \
  #v(2pt)
  #text(size: 8.5pt, fill: rgb("#475569"))[*Pautas DUA:* Repr: Gráfica interactiva animada y tabla numérica comparativa. | Acción: Construcción libre de tablas, bosquejos o diagramas de dispersión. | Compromiso: Desafío gamificado de predicción del tiempo de vuelo. \ *Artefacto Dinámico:* `geogebra-projectile-motion-applet`]
]
#v(6pt)

#rect(
  width: 100%,
  stroke: 0.7pt + rgb("#3b82f6"),
  radius: 3pt,
  inset: 8pt
)[
  #grid(
    columns: (3fr, 1.5fr),
    [#text(weight: "bold", size: 10.5pt, fill: rgb("#1e40af"))[Fase 2: Situación de Formulación y Validación: Conjetura de Simetría]],
    [#align(right)[#text(size: 8pt, weight: "bold", fill: rgb("#1d4ed8"))[Demanda: PROCEDIMIENTOS_CON_CONEXIONES]]]
  )
  #v(3pt)
  *Actividad del Estudiante:* Los equipos formulan la conjetura de que el punto máximo ocurre exactamente en el punto medio entre el despegue y el impacto. \
  #v(2pt)
  *Rol y Mediación Docente:* Media el debate plenario sin validar directamente; solicita a los grupos defender por qué las alturas son idénticas a distancias iguales del vértice. \
  #v(2pt)
  *Justificación de Ejemplos (Rowland):* Comparación entre $t=1$ ($h=15$) y $t=3$ ($h=15$) para evidenciar la simetría axial respecto a $t=2$. \
  #v(2pt)
  #text(size: 8.5pt, fill: rgb("#475569"))[*Pautas DUA:* Repr: Trazado del eje de simetría sobre la parábola. | Acción: Debate guiado y registro en pizarra compartida. | Compromiso: Colaboración estructurada con roles rotativos. ]
]
#v(6pt)

#rect(
  width: 100%,
  stroke: 0.7pt + rgb("#3b82f6"),
  radius: 3pt,
  inset: 8pt
)[
  #grid(
    columns: (3fr, 1.5fr),
    [#text(weight: "bold", size: 10.5pt, fill: rgb("#1e40af"))[Fase 3: Institucionalización y Formalización Deductiva]],
    [#align(right)[#text(size: 8pt, weight: "bold", fill: rgb("#1d4ed8"))[Demanda: PROCEDIMIENTOS_CON_CONEXIONES]]]
  )
  #v(3pt)
  *Actividad del Estudiante:* Registran la síntesis conceptual y aplican la relación formal a nuevos casos paramétricos. \
  #v(2pt)
  *Rol y Mediación Docente:* Formaliza el estatus del saber matemático institucional, conecta la conjetura de los estudiantes con la completación de cuadrados. \
  #v(2pt)
  *Justificación de Ejemplos (Rowland):* Generalización a $f(x) = a x^2 + b x + c$ deduciendo la abscisa del vértice $x_v = -b/(2 a)$. \
  #v(2pt)
  #text(size: 8.5pt, fill: rgb("#475569"))[*Pautas DUA:* Repr: Mapa conceptual síntesis que vincula registro gráfico, analítico y canónico. | Acción: Bitácora reflexiva de aprendizaje y formulario de síntesis. | Compromiso: Autoevaluación de metacognición con rúbrica Förster. ]
]
#v(6pt)

