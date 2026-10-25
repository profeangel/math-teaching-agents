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
  [*Evaluación:* Evaluación Formativa: Función y Ecuación Cuadrática en Contexto], [*Puntaje:* 12 pts], [*Nota:*]
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
*Ítem 1* (3 pts) \
Considere la ecuación cuadrática $x^2 - 6 x + 8 = 0$. ¿Cuál es el conjunto solución en $RR$?

#grid(
  columns: (1fr, 1fr),
  row-gutter: 8pt,
  [*(A)* $x = 2$ y $x = 4$],
  [*(B)* $x = -2$ y $x = -4$],
  [*(C)* $x = 1$ y $x = 8$],
  [*(D)* $x = 3$ y $x = -3$]
)

#v(10pt)

*Ítem 2* (4 pts) \
La trayectoria de un proyectil lanzado verticalmente está modelada por la función $h(t) = -5 t^2 + 20 t$, donde $h$ es la altura en metros y $t$ el tiempo en segundos ($t  >=  0$). ¿En qué instante $t$ el proyectil alcanza su altura máxima?

#grid(
  columns: (1fr, 1fr),
  row-gutter: 8pt,
  [*(A)* $t = 2$ segundos],
  [*(B)* $t = 4$ segundos],
  [*(C)* $t = 20$ segundos],
  [*(D)* $t = 5$ segundos]
)

#v(10pt)

*Ítem 3* (5 pts) \
Un estudiante afirma que 'si el discriminante $Delta = b^2 - 4 a c$ de una ecuación cuadrática es estrictamente negativo, la ecuación no tiene solución'. Demuestre o refute dicha afirmación especificando con rigor los conjuntos numéricos (conjunto $RR$ vs. $CC$) y su interpretación geométrica en el plano cartesiano.

#v(4pt)
#rect(width: 100%, height: 4.5cm, stroke: 0.5pt + rgb("#94a3b8"), radius: 2pt, inset: 6pt)[
  #text(size: 8pt, fill: rgb("#64748b"), style: "italic")[Espacio reservado para desarrollo y justificación axiomática]
]

#v(10pt)

