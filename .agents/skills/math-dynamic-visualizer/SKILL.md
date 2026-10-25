---
name: math-dynamic-visualizer
description: >-
  Executable code generation for dynamic mathematical representations: Python vector animations with Manim Community Edition and interactive applets in GeoGebra / Desmos.
  Use when designing vector animations for abstract concepts (calculus, functions, linear algebra, geometry) or interactive exploration applets.
  DO NOT USE / NO USAR for typesetting static text documents or designing written exam papers.
---

# Skill Protocol: math-dynamic-visualizer

This skill connects instrumental genesis and mathematical visualization theories with executable code engines (Manim CE and GeoGebra).

---

## 1. Mathematical Animation Guidelines with Manim CE

1. **Cognitive Purpose**: Motion and spatial transformations must serve conceptual discovery (e.g., Riemann sum rectangle approximations, linear transformations, geometric series), avoiding superficial decorative animations.
2. **Looping Format**: Whenever possible, generate animations suitable for smooth looping when embedded in classroom slides or web modules.
3. **Standard Python Script Structure**:
   ```python
   from manim import *

   class ConceptVisualization(Scene):
       def construct(self):
           # Axes configuration
           axes = Axes(x_range=[-3, 3], y_range=[-1, 5])
           # Main mathematical curve
           curve = axes.plot(lambda x: x**2, color=BLUE)
           # Smooth transitions
           self.play(Create(axes))
           self.play(Create(curve), run_time=2)
           self.wait(1)
   ```

---

## 2. Dynamic Geometric Constructions with GeoGebra

1. **Dynamic Parameters**: Every interactive applet must define sliders with mathematically sensible bounds and steps.
2. **Geometric Invariants**: Ensure parallelism, perpendicularity, or tangency relationships remain invariant when free points are dragged.
