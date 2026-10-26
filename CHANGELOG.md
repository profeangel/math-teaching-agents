# Registro de Cambios (`CHANGELOG.md`)

Todas las modificaciones notables en este proyecto se documentan en este archivo.
El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y se adhiere a [Semantic Versioning](https://semver.org/lang/es/).

---

## [0.8.1] - 2026-10-26 (Pedagogical Reality and Visual Layout Auditor)

### Added
- **Visual & Layout Auditor Tool (`tools/audit_pdf_layout.py`)**:
  - Deterministic CLI tool for Gate 2 layout verification using `pypdf`.
  - Detection of orphan overflows on final pages (< 20% character density ratio).
  - Detection of unparsed LaTeX syntax bleed in Typst (`\text{}`, `\circ`, `\frac{}`).
  - Detection of evaluation reactivos/items split across page breaks.
  - Page budget enforcement (`--budget`, `--draft`, `--json`).
  - Comprehensive unit test suite in `tests/test_tools.py` with standalone PDF fixtures in `tests/fixtures/pdf/`.
- **Lesson Study Problem-Solving Framework (`frameworks/isoda-olfos-resolucion-problemas.yaml`)**:
  - Canonical 5-moment mathematics lesson model (Nohda & Shimada / Isoda & Olfos 2009):
    1. Review / Warm-up (*Fukushuu*).
    2. Problem Posing (*Hatsumon*).
    3. Independent / Group Solving (*Kikan-shido*).
    4. Comparison & Discussion (*Neriage*).
    5. Summary & Institutionalization (*Matome*).

### Changed
- **Orchestrator Out-of-the-Box Classroom Intake (`AGENTS.md`, `agents/orchestrator.md`, `CLAUDE.md`, `.cursor/rules/`)**:
  - Proactive classroom constraints interview: calculator policy (forbidden/allowed), geometry tools vs. pre-printed cotas, exact radicals vs. decimal approximations.
  - Didactic balance: recognizes that not every lesson is an abstract inquiry session; incorporates dedicated intensive deliberate practice and procedural fluency workshops.
- **Anti-Token Waste & Lazy Answer Key Policy**:
  - Eliminates unnecessary dual generation of student vs. teacher worksheets.
  - The core material is designed 100% for student autonomous work (UDL/DUA accessible).
  - Teachers receive a 1-page executive Lesson Roadmap (5 moments).
  - Answer keys (solucionarios) are generated lazily on-demand only after the student document is frozen and approved in Gate 2.

---

## [0.8.0] - 2026-10-24

### Añadido (The Synthesis Release: Fusión v0.1.0 + v0.7.0 & Guía de Agentes)
* **Meta-Estándar Universal de Entrada en Raíz**:
  * Creado `AGENTS.md` como punto único de verdad (*Single Source of Truth*) para descubrimiento automático en Google Antigravity y arneses agénticos.
  * Creado `CONVENTIONS.md` con puntero para Aider Pair-Programming.
  * Creadas reglas modulares en `.cursor/rules/`: `core.mdc` (`alwaysApply: true`) y `math-teaching.mdc` (globs para plantillas, marcos y esquemas).
  * Actualizado `CLAUDE.md` con comandos inmediatos ("checks to run") para Claude Code.
* **Skills Canónicas Modulares (`.agents/skills/`) con Progressive Disclosure**:
  * `.agents/skills/math-didactic-unit/`: Diseño de secuencias de aprendizaje y situaciones de clase en 4 fases de Brousseau, registros de Duval y niveles APOE.
  * `.agents/skills/math-assessment/`: Construcción de instrumentos psicométricos, cálculo determinista de distractores con SymPy y exportación Moodle XML.
  * `.agents/skills/math-dynamic-visualizer/`: Generación de animaciones en bucle con Manim Community Edition y construcciones dinámicas en GeoGebra.
  * Cada skill implementa frontmatter YAML con disparadores negativos (`NO USAR para...`) para prevenir falsos positivos.
* **Evaluador Pedagógico Semántico (Capa 2: LLM-as-a-Judge)**:
  * Nuevo módulo `src/math_teaching_agents/validators/pedagogical_judge.py` (`PedagogicalJudge`):
    * Audita semánticamente 4 dimensiones: Devolución Brousseau (ausencia de Efecto Topaze), Multirregistro Duval, Demanda Cognitiva Bloom y Calidad de Evaluación Auténtica Förster.
    * Conectable a cualquier proveedor LLM (Gemini, Claude, OpenAI, Ollama o Mock determinista para tests).
    * Modo heurístico estructurado de respaldo (*fallback local*) con salida JSON cuantitativa y cualitativa.
  * Nueva herramienta de terminal `tools/pedagogical_judge.py` con flags `--json` y `--sample`.
* **Ampliación de la Suite de Pruebas**:
  * Nuevos tests unitarios en `tests/test_pedagogical_judge.py` (auditoría Topaze, multirregistro y mock LLM).
  * Nuevos tests en `tests/test_skills_and_metastandard.py` (conformidad de Meta-Estándar, skills canónicas, marcos y currículos).
  * Cobertura ampliada a **76/76 pruebas pasando al 100% en verde** en 1.33s.
* **Política de Versionamiento Inmutable**:
  * Creado `VERSIONS.md` formalizando la inmutabilidad de versiones históricas en repositorios independientes (`math-teaching-agents-v0.1.0` y `math-teaching-agents-v0.7.0`).

---

## [0.7.0] - 2026-10-24

### Añadido
* **Punto de Control Humano (Human-in-the-Loop Checkpoint - Recomendación 1):**
  * Nuevo módulo `src/math_teaching_agents/human_review.py` que genera resúmenes didácticos en lenguaje natural estructurado (metadatos, matriz cognitiva, distractores KFLM, pautas DUA).
  * Interfaz interactiva de control previa a Gate 2 con 4 opciones:
    1) Aprobación directa.
    2) Apertura automática en el editor del sistema para ajustes de aula en YAML.
    3) Modificación rápida de metadatos desde la consola.
    4) Cancelación segura del flujo.
  * **Re-validación Zero-Trust:** Si el docente edita el YAML, el pipeline re-ejecuta inmediatamente Gate 1 con SymPy; si los cambios humanos introducen errores algebraicos o de contrato, el sistema alerta y bloquea la maquetación.
  * Nuevo flag `--interactive-review` / `-i` en `math-agent run`.
  * Integración en `DidacticPipeline.run(...)` con parámetros `interactive_review` y `review_callback`.
* **Ampliación de Verificadores Simbólicos Más Allá de SymPy (Recomendación 2):**
  * Extensión de `SymbolicMathVerifier` en `src/math_teaching_agents/validators/math_verifier.py`:
    * **Desigualdad Triangular (`verify_triangle_inequality`):** Comprobación formal estricta de $a > 0, b > 0, c > 0$ y $a + b > c$, $a + c > b$, $b + c > a$. Detección de triángulos degenerados o imposibles.
    * **Suma de Ángulos de Polígonos (`verify_polygon_angles`):** Comprobación de suma interior teórica $(n - 2) \cdot 180^\circ$ y ángulos válidos.
    * **Teorema de Pitágoras e Invariantes Rectangulares (`verify_pythagorean_property`):** Comprobación exacta de $a^2 + b^2 = c^2$.
    * **Invariantes del Círculo (`verify_circle_invariants`):** Consistencia entre radio, diámetro ($2r$), perímetro ($2\pi r$) y área ($\pi r^2$).
    * **Axiomas de Kolmogorov para Probabilidades (`verify_probability_distribution`):** $0 \le P(E) \le 1$ y suma de partición igual a $1.0$.
    * **Cálculo e Invariantes Combinatorios (`verify_combinatorics_values`):** Comprobación de $\binom{n}{k}$, permutaciones y restricciones $n \ge k \ge 0$.
  * Soporte en herramientas CLI `tools/verify_math.py` con nuevos flags: `--check-geom`, `--check-prob` y `--check-comb`.
  * Soporte de verificación matemática general en ítems abiertos y de opción múltiple vía `verify_item`.
* **Suite de Pruebas Ampliada:**
  * Creado `tests/test_human_review.py` con 10 tests unitarios del flujo interactivo y Zero-Trust.
  * Ampliado `tests/test_math_verifier.py` con 7 nuevos tests de geometría, probabilidad y combinatoria.
  * Ampliado `tests/test_tools.py` con 3 nuevos tests CLI.
  * Total de la suite: **68/68 tests pasando al 100% en verde (1.25s)**.

---

## [0.6.1] - 2026-10-24

### Añadido
* **Asistente de Inicialización y Perfil Pedagógico Docente (`math-agent init`):**
  * Nuevo módulo `src/math_teaching_agents/profile.py` con gestión de perfiles declarativos `.math-agent.yaml`.
  * Asistente interactivo en consola para calibrar nombre, nivel educativo, currículo base y **tono de comunicación** (`pragmatic`, `mentoring`, `academic`).
  * Modo desatendido con flags (`--non-interactive`, `--name`, `--level`, `--curriculum`, `--tone`, `--format`).
  * Inyección contextual del perfil docente en los System Prompts del `DidacticPipeline` y agentes orquestadores.
  * Nuevo comando `math-agent init` integrado en `src/math_teaching_agents/cli.py` y detección automática de perfiles en `math-agent run` y `math-agent info`.
  * Batería completa de pruebas unitarias en `tests/test_profile.py` (total de la suite: **48/48 tests pasando en verde**).
* **Actualización de Documentación de Harnesses:**
  * Actualizados `agents/orchestrator.md` y `CLAUDE.md` con la Fase 0 (Calibración de Perfil Docente) para adaptar el lenguaje y evitar sobrecarga de jerga académica con docentes de aula.

---

## [0.6.0] - 2026-10-24

### Añadido
* **Herramientas CLI Deterministas en `tools/` para Agent Harnesses:**
  * `tools/verify_math.py`: Auditor formal SymPy CAS de línea de comandos para Gate 1. Admite archivos `.yaml`, `.json`, modo estructurado `--json`, flags `--expr` para igualdades aisladas y `--solve` para resolución analítica directa.
  * `tools/validate.py`: Validador de esquemas JSON (Draft 2020-12) y contratos. Soporta validación de borradores individuales con inferencia automática de tipo y auditoría global `--all`.
  * `tools/render.py`: Renderizador y compilador multiformato para Gate 2 (Typst, LaTeX, Moodle XML) con flag `--compile` para compilación directa a PDF y reporte JSON para agentes.
  * `tools/README.md`: Guía de referencia y manual de comandos de terminal para desarrolladores y harnesses.
* **Integración Nativa con Agent Harnesses (Claude Code, OpenCode, Antigravity):**
  * `CLAUDE.md`: Manifiesto y guía integral de comandos, arquitectura Actor-Crítico y protocolo de ejecución para Claude Code y OpenCode.
  * Actualización de especificaciones en `agents/*.md` (`evaluator.md`, `orchestrator.md`, `universal-format-engine.md`): instrucciones mandatorias para que los subagentes ejecuten las herramientas de `tools/` por consola vía terminal y lean respuestas JSON para el bucle de autorreparación (Self-Healing).
* **Suite de Pruebas Unitarias Ampliada:**
  * Creado `tests/test_tools.py` con cobertura completa para las herramientas independientes de `tools/` y validación de borradores individuales en `test_cli.py`.
  * Total: **41/41 tests pasando al 100% en verde**.

---

## [0.5.0] - 2026-10-24

### Añadido
* **Generación de Unidades Didácticas y Secuencias de Clase (`schemas/didactic-unit.json`):**
  * Soporte completo para el ciclo de vida didáctico completo más allá de evaluaciones puntuales.
  * Modelado de Fases de Situaciones Didácticas de Guy Brousseau (Acción, Formulación, Validación e Institucionalización).
  * Asignación explícita de Niveles de Demanda Cognitiva de Stein & Smith (`MEMORIZACION`, `PROCEDIMIENTOS_SIN_CONEXIONES`, `PROCEDIMIENTOS_CON_CONEXIONES`, `HACIENDO_MATEMATICA`).
  * Integración obligatoria de Pautas DUA (Diseño Universal para el Aprendizaje - CAST): representación múltiple, acción/expresión y compromiso.
  * Justificación didáctica de la selección de ejemplos según el marco de Rowland (*Knowledge Quartet*).
* **Plantillas y Motores de Maquetación para Unidades Didácticas:**
  * Typst: `templates/typst/standard-didactic-unit.typ` con tablas estructuradas, diseño modular con `#rect` y microtipografía moderna.
  * LaTeX: `templates/latex/standard-didactic-unit.tex` con cajas estilizadas `tcolorbox`, badges y formato de publicación docente.
  * Soporte en `LatexEngine.render_didactic_unit` y `TypstEngine.render_didactic_unit`.
* **Soporte CLI y Dashboard Web para Unidades Didácticas:**
  * Parámetro `--type` (`assessment` vs `didactic-unit`) en `math-agent run`.
  * Selector visual en el Dashboard Web (`ui.py`) con pestañas reactivas para auditar Gate 1, el borrador YAML y el código maquetado.
* **Ampliación de Pruebas Unitarias:**
  * Batería de pruebas expandida a 31 tests unitarios pasando al 100% en verde con cobertura para UI, CLI, Typst y LaTeX para unidades didácticas.

---

## [0.4.0] - 2026-10-24

### Añadido
* **Bucle Autónomo de Autocorrección (*Self-Healing Loop*):**
  * Mecanismo reflexivo en `DidacticPipeline.run`: cuando Gate 1 (Schema o SymPy CAS) detecta fallas, extrae retroalimentación estructurada y genera un prompt correctivo específico reintentando hasta `max_retries` (por defecto 3) antes de rechazar.
  * Registro de métricas de autorreparación: `attempts_needed`, `history_repairs` y notas diagnósticas en `gate1_verdict.json`.
* **Parser Matemático LaTeX $\to$ SymPy CAS Robusto:**
  * Soporte recursivo para fracciones complejas anidadas `\frac{num}{den}` y radicales de cualquier orden `\sqrt[n]{arg}` mediante parser de llaves balanceadas.
  * Canonicalización de conjuntos solución (`\{2, 3\}` == `\{3, 2\}`): detección de permutaciones y distractores idénticos bajo notación de conjuntos.
  * Unificación de fracciones y números decimales con `sp.nsimplify` (`\frac{1}{2}` == `0.5`).
* **Motor de Exportación para Entornos Virtuales de Aprendizaje (LMS):**
  * `src/math_teaching_agents/engines/moodle_engine.py`: `MoodleEngine` para exportar a formato Moodle XML universal compatible con Moodle, Canvas, Blackboard y Chamilo.
  * Inyección automática de retroalimentación formativa y códigos de error didáctico (`misconception_ref`) en las opciones de preguntas.
  * Sanitización y normalización de sintaxis matemática MathJax (`\( ... \)`) para evitar colisiones con HTML en plataformas LMS.
* **Orquestación Multi-Etapa Modular:**
  * Modo `--multi-stage` que descompone el flujo en fases reales: Fase 1 (Análisis Didáctico de prerrequisitos, obstáculos y matriz Anderson-Krathwohl vía agentes MTSK) y Fase 2 (Construcción del instrumento vía `gpk-assessment`).
* **Dashboard Web Interactivo Liviano (`src/math_teaching_agents/ui.py`):**
  * Servidor HTTP local embebido (`math-agent ui` / `math-agent serve`) con interfaz gráfica responsiva, selectores de currículo/marco y visualizador en vivo de Gate 1/Gate 2, YAML y código compilable.
* **Ampliación de la Suite de Pruebas Unitarias:**
  * Cobertura expandida de 15 a 24 tests unitarios pasando al 100% en verde (`tests/test_moodle_engine.py`, `tests/test_math_verifier.py`, `tests/test_llm_runtime.py`, `tests/test_cli.py`).

---

## [0.3.0] - 2026-10-24

### Añadido
* **Runtime de Conexión LLM y Pipeline Multiagente (`llm_runtime.py`):**
  * `AgentLoader`: Descubrimiento y parseo automático de especificaciones markdown de agentes en `agents/` extrayendo roles, misiones y system prompts oficiales.
  * `LLMProvider` y `MockLLMProvider`: Abstracción de conexión para proveedores de LLM con implementación determinista fuera de línea para pruebas unitarias reproducibles y CI/CD sin consumo de API tokens.
  * `HTTPLLMProvider`: Conector universal preparado para Ollama, OpenAI, Google Gemini y Anthropic Claude.
  * `DidacticPipeline`: Orquestador integral del ciclo de vida multiagente bajo arquitectura Zero-Trust (Borrador -> Gate 1 CAS Simbólico -> Gate 2 Renderizado Técnico).
* **Nuevo Motor Tipográfico Moderno Typst (`engines/typst_engine.py`):**
  * Soporte nativo para maquetación tipográfica ultrarrápida con Typst.
  * Plantilla institucional `templates/typst/standard-evaluation.typ`.
  * Conversor y sanitizador de expresiones matemáticas LaTeX a sintaxis Typst.
  * Compilador automático opcional vía binario `typst`.
* **Nuevos Adaptadores Curriculares Oficiales:**
  * `curriculums/mexico-nem.yaml`: Plan de Estudio de la Nueva Escuela Mexicana (SEP) con Campo Formativo Saberes y Pensamiento Científico, Fase 6 (Secundaria), MCCEMS y exámenes MEJOREDU / EXANI.
  * `curriculums/colombia-men.yaml`: Ministerio de Educación Nacional de Colombia (MEN) & ICFES con 5 Pensamientos Matemáticos, Derechos Básicos de Aprendizaje (DBA V2) y Pruebas Saber 11 / Saber Pro.
* **Nuevo Marco Teórico Didáctico de Referencia:**
  * `frameworks/godino-eos.yaml`: Enfoque Ontosemiótico del Conocimiento y la Instrucción Matemáticos (Godino, Batanero y Font), configuraciones ontosemióticas (6 entidades primarias), dualidades cognitivas y criterios de idoneidad didáctica.
* **Ampliación de la CLI (`math-agent`):**
  * Nuevo comando `math-agent run`: Ejecución desatendida del pipeline didáctico completo con parámetros `--topic`, `--curriculum`, `--framework`, `--format` y `--provider`.
  * Comando `math-agent render`: Soporte extendido con selector `--format [latex|typst]`.
* **Suite de Pruebas Unitarias Ampliada (`tests/`):**
  * Nuevos tests `test_typst_engine.py`, `test_llm_runtime.py` y `test_cli.py`.
  * Cobertura incrementada de 8 a 15 pruebas automatizadas pasando al 100% en verde.

---

## [0.2.0] - 2026-10-24

### Añadido
* **Infraestructura de Empaquetado y Dependencias:**
  * Archivo `pyproject.toml` con metadatos del proyecto, dependencias (`sympy`, `jsonschema`, `pyyaml`, `jinja2`) y punto de entrada para CLI `math-agent`.
  * Archivos `requirements.txt` y `.gitignore` exhaustivo adaptado a Python, compilación LaTeX, Typst y Office.
* **Integración Continua (CI/CD) para GitHub Actions:**
  * `.github/workflows/ci.yml`: Validación automática de esquemas, curriculums, frameworks y ejecución de tests en Python 3.10, 3.11 y 3.12.
  * `.github/workflows/latex-check.yml`: Comprobación automática de compilación de plantillas LaTeX con Tectonic.
  * `.github/PULL_REQUEST_TEMPLATE.md`: Plantilla de PR con verificación de políticas didácticas y preservación de Gate 1.
  * `.github/ISSUE_TEMPLATE/bug_report.yml`: Plantilla estructurada para reporte de bugs didácticos o técnicos.
  * `.github/ISSUE_TEMPLATE/new_curriculum_or_framework.yml`: Plantilla para proponer adaptadores curriculares o marcos de investigación.
* **Paquete de Software Oficial (`src/math_teaching_agents/`):**
  * `src/math_teaching_agents/cli.py`: Interfaz de línea de comandos con comandos `info`, `validate`, `verify-math` y `render`. Resiliente a codificación UTF-8 en consolas Windows (cp1252).
  * `src/math_teaching_agents/validators/schema_validator.py`: Validador programático de metarreglas JSON Schema Draft 2020-12, adaptadores curriculares y marcos didácticos.
  * `src/math_teaching_agents/validators/math_verifier.py`: **Motor de Verificación Simbólica Formal con SymPy**. Elimina alucinaciones de LLMs comprobando analíticamente raíces de ecuaciones, validez de soluciones y unicidad matemática de distractores en Gate 1.
  * `src/math_teaching_agents/engines/latex_engine.py`: Motor de templating para maquetación tipográfica de evaluaciones con entornos `tasks`, cajas didácticas `tcolorbox` y compilador opcional a PDF.
* **Suite de Pruebas Automatizadas (`tests/`):**
  * `tests/test_schemas.py`: Verificación de todos los esquemas JSON y archivos declarativos YAML.
  * `tests/test_math_verifier.py`: Pruebas de resolución de ecuaciones y detección de distractores duplicados/inválidos con SymPy.
  * `tests/test_latex_engine.py`: Pruebas de inyección de metadatos y generación de cuerpo LaTeX.
  * Cobertura: 8/8 tests pasando en verde.
* **Galería de Ejemplos de Producción (`examples/ecuacion-cuadratica/`):**
  * `assessment-draft.yaml`: Borrador conforme a `assessment-spec.json`, PAES M1 Mineduc y Duval TRRS.
  * `gate1_verdict.json`: Dictamen de auditoría con validación SymPy y rúbrica cualitativa Förster.
  * `rendered-evaluation.tex`: Archivo LaTeX listo para compilar.
  * `geogebra_commands.txt`: Script de comandos GeoGebra con deslizadores y preguntas de indagación.
  * `completing_square_manim.py`: Animación vectorial en Manim Community Edition (v0.18+).

### Modificado
* `README.md`: Actualizado con insignias de build, sección de *Quickstart* con comandos de terminal, arquitectura actualizada con SymPy CAS en Gate 1, y árbol del repositorio completo.

---

## [0.1.0] - 2026-10-24
* Lanzamiento inicial de especificaciones conceptuales: 16 especificaciones de agentes en Markdown, 2 esquemas JSON, 3 marcos didácticos y 3 adaptadores curriculares.
