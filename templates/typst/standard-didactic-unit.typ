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
  #text(size: 13pt, weight: "semibold", fill: rgb("#1e40af"))[<<UNIT_TITLE>>]
]

#v(8pt)

// --- Ficha Técnica y Metadatos ---
#table(
  columns: (1.5fr, 1fr, 1.2fr, 1fr),
  stroke: 0.5pt + luma(120),
  fill: (col, row) => if row == 0 { rgb("#f1f5f9") } else { none },
  inset: 6pt,
  [*Nivel Educativo:*], [*Sesiones:*], [*Duración por Sesión:*], [*Currículo:*],
  [<<TARGET_GRADE>>], [<<ESTIMATED_SESSIONS>> sesiones], [<<MINUTES_PER_SESSION>> min], [<<CURRICULUM_REF>>]
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
  #text(size: 9.5pt)[*Marcos Activos:* <<ACTIVE_FRAMEWORKS>>] \
  #v(2pt)
  #text(size: 9.5pt)[<<NETWORKING_JUSTIFICATION>>]
]

#v(10pt)

// --- Diagnóstico Epistemológico y Obstáculos (MTSK-KFLM) ---
#text(weight: "bold", size: 11pt, fill: rgb("#0f172a"))[2. Diagnóstico Cognitivo y Obstáculos Epistemológicos (MTSK):] \
#text(size: 9.5pt)[*Prerrequisitos Indispensables:* <<PREREQUISITES>>] \
#v(4pt)
<<MISCONCEPTIONS_BLOCK>>

#v(12pt)

// --- Secuencia de Aprendizaje por Fases (Brousseau & Stein-Smith) ---
#text(weight: "bold", size: 11pt, fill: rgb("#0f172a"))[3. Secuencia de Aprendizaje e Ingeniería de Situaciones:]

<<PHASES_BLOCK>>
