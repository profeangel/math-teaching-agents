"""
Visualización Geométrica del Completamiento del Cuadrado de Binomio.
Generado por el subagente manim-motion-engineer (Manim Community Edition v0.18+).
Ejecutar con: manim -pql completing_square_manim.py CompletingTheSquareScene
"""

from manim import *


class CompletingTheSquareScene(Scene):
    def construct(self):
        # 1. Título y Planteamiento
        title = Title(r"Completamiento Geométrico del Trinomio Cuadrado", font_size=36)
        algebra_eq = MathTex(r"x^2 + 2bx + \underline{\quad} = (x + b)^2", color=YELLOW).next_to(title, DOWN)
        self.play(Write(title))
        self.play(FadeIn(algebra_eq))
        self.wait(1)

        # 2. Construcción de Figuras Geométricas
        # Cuadrado x^2
        sq_x = Square(side_length=2.5, color=BLUE, fill_opacity=0.6)
        label_x2 = MathTex(r"x^2").move_to(sq_x)

        # Dos rectángulos b * x
        rect_right = Rectangle(width=0.8, height=2.5, color=GREEN, fill_opacity=0.6).next_to(sq_x, RIGHT, buff=0.05)
        rect_top = Rectangle(width=2.5, height=0.8, color=GREEN, fill_opacity=0.6).next_to(sq_x, UP, buff=0.05)

        label_bx_r = MathTex(r"bx", font_size=28).move_to(rect_right)
        label_bx_t = MathTex(r"bx", font_size=28).move_to(rect_top)

        # Esquina faltante b^2
        missing_corner = Square(side_length=0.8, color=RED, fill_opacity=0.7).next_to(rect_right, UP, buff=0.05)
        label_b2 = MathTex(r"b^2", color=YELLOW, font_size=28).move_to(missing_corner)

        group_geo = VGroup(sq_x, label_x2, rect_right, label_bx_r, rect_top, label_bx_t).center().shift(DOWN * 0.5)

        # 3. Animación Secuencial Didáctica
        self.play(DrawBorderThenFill(sq_x), Write(label_x2))
        self.wait(0.5)
        self.play(DrawBorderThenFill(rect_right), Write(label_bx_r))
        self.play(DrawBorderThenFill(rect_top), Write(label_bx_t))
        self.wait(1)

        # 4. Revelación del Término Faltante b^2
        hint = Text("¿Qué figura falta para completar el gran cuadrado?", font_size=24, color=GRAY_A).next_to(group_geo, DOWN)
        self.play(FadeIn(hint))
        self.wait(1)

        self.play(DrawBorderThenFill(missing_corner), Write(label_b2))
        self.play(FadeOut(hint))

        # 5. Transformación Final a (x + b)^2
        final_eq = MathTex(r"x^2 + 2bx + \mathbf{b^2} = (x + b)^2", color=GREEN).next_to(title, DOWN)
        self.play(Transform(algebra_eq, final_eq))
        self.wait(2)
