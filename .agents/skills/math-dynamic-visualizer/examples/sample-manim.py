# Ejemplo canónico de animación con Manim Community Edition
from manim import *

class QuadraticFunctionIntro(Scene):
    def construct(self):
        title = Text("La Parábola f(x) = x²", font_size=36)
        self.play(Write(title))
        self.wait(1)
        self.play(title.animate.to_edge(UP))

        axes = Axes(x_range=[-3, 3, 1], y_range=[-1, 5, 1], axis_config={"include_numbers": True})
        graph = axes.plot(lambda x: x**2, color=BLUE)
        graph_label = axes.get_graph_label(graph, label="y = x^2")

        self.play(Create(axes))
        self.play(Create(graph), Write(graph_label), run_time=2)
        self.wait(2)
