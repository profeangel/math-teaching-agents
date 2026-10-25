// --- Plantilla Estándar de Evaluación Matemática en Typst ---
#set page(
  paper: "us-letter",
  margin: (top: 2cm, bottom: 2cm, left: 2cm, right: 2cm),
  header: [
    #grid(
      columns: (1fr, 1fr),
      align(left)[*DEPARTAMENTO DE MATEMÁTICA*],
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
  size: 11pt,
)

// --- Membrete Institucional ---
#table(
  columns: (3fr, 1fr, 1fr),
  stroke: 0.5pt + luma(100),
  inset: 6pt,
  [*Estudiante:*], [*Curso:*], [*Fecha:*],
  [*Evaluación:* <<METADATA_TITLE>>], [*Puntaje:* <<TOTAL_POINTS>> pts], [*Nota:*]
)

#v(8pt)

// --- Caja de Instrucciones Generales ---
#rect(
  width: 100%,
  fill: rgb("#f1f5f9"),
  stroke: 0.8pt + rgb("#1e293b"),
  radius: 3pt,
  inset: 8pt
)[
  #text(weight: "bold", fill: rgb("#1e293b"))[Instrucciones Generales:] \
  Lea atentamente cada situación problema. Justifique formalmente sus procedimientos matemáticos. En los ítems de selección múltiple, marque únicamente la opción correcta con una línea clara.
]

#v(12pt)

// --- Cuerpo de Ítems Generado Dinámicamente ---
<<CONTENT_BODY>>
