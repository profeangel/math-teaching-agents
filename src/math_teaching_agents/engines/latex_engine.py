"""
Motor de Maquetación y Renderizado LaTeX para evaluaciones e instrumentos matemáticos.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import shutil
import subprocess
import re


class LatexEngine:
    """Inyecta borradores semánticos en plantillas LaTeX oficiales y gestiona la compilación."""

    def __init__(self, template_path: Optional[Path] = None):
        if template_path:
            self.template_path = Path(template_path)
        else:
            # Buscar en templates/latex/standard-evaluation.tex relativo a la raíz del proyecto
            current = Path(__file__).resolve()
            # Navegar hacia la raíz del proyecto (3 niveles arriba de engines/: engines -> pkg -> src -> root)
            root = current.parents[3]
            self.template_path = root / "templates" / "latex" / "standard-evaluation.tex"

    @staticmethod
    def _ensure_math_formatting(text: str) -> str:
        """Garantiza que variables y ecuaciones en alternativas se maqueten en modo matemático."""
        if not text or '$' in text:
            return text
        res = re.sub(r'([a-zA-Z]\s*=\s*-?\d+(?:/\d+)?)', r'$\1$', text)
        if res != text:
            return res
        if re.match(r'^[0-9a-zA-Z+\-*/^=,.\s\(\)\{\}\\]+$', text) and any(c in text for c in '=+-*/^'):
            return f"${text.strip()}$"
        return text

    def render_body(self, items: list) -> str:
        """Genera el bloque tipográfico de ítems para el cuerpo de la evaluación."""
        lines = []
        for idx, item in enumerate(items, start=1):
            points = item.get("points", 1)
            pts_str = f"({points} pt)" if points == 1 else f"({points} pts)"
            stem = item.get("stem", "")
            fmt = item.get("format", "OPEN_DEVELOPMENT")

            lines.append(f"\\noindent \\textbf{{Ítem {idx}}} {pts_str}\\\\")
            lines.append(f"{stem}\n")

            if fmt == "MULTIPLE_CHOICE" and "options" in item:
                lines.append("\\begin{tasks}(2)")
                for opt in item["options"]:
                    lbl = opt.get("key") or opt.get("label", "")
                    txt = self._ensure_math_formatting(opt.get("text", ""))
                    lines.append(f"  \\task \\textbf{{{lbl})}} {txt}")
                lines.append("\\end{tasks}\n")
            elif fmt in ("OPEN_DEVELOPMENT", "PROOF_ARGUMENT"):
                lines.append("\\vspace{0.2cm}")
                lines.append("\\begin{tcolorbox}[colback=white,colframe=neutralGray,arc=1mm,boxrule=0.5pt,height=4.5cm,valign=top]")
                lines.append("{\\footnotesize\\color{gray}\\textit{Espacio reservado para desarrollo y justificación axiomática}}")
                lines.append("\\end{tcolorbox}\n")

            lines.append("\\vspace{0.4cm}\n")

        return "\n".join(lines)

    def render_didactic_unit(self, unit_data: Dict[str, Any]) -> str:
        """Renderiza una unidad didáctica completa en LaTeX."""
        root = Path(__file__).resolve().parents[3]
        unit_tmpl_path = root / "templates" / "latex" / "standard-didactic-unit.tex"
        with open(unit_tmpl_path, "r", encoding="utf-8") as f:
            template = f.read()

        meta = unit_data.get("metadata", {})
        theo = unit_data.get("theoretical_alignment", {})
        diag = unit_data.get("epistemological_diagnostics", {})
        phases = unit_data.get("phases", [])

        # Bloque de concepciones erróneas
        misconceptions = diag.get("target_misconceptions", [])
        misc_lines = []
        for m in misconceptions:
            code = m.get("code", "")
            desc = self._ensure_math_formatting(m.get("description", ""))
            strat = self._ensure_math_formatting(m.get("confrontation_strategy", ""))
            misc_lines.append(f"\\noindent \\textbf{{{code}:}} {desc}\\\\\n\\textit{{Estrategia de Confrontación:}} {strat}\\\\[0.2cm]")

        # Bloque de fases de la secuencia
        phase_lines = []
        for p in phases:
            pid = p.get("phase_id", 1)
            pname = p.get("phase_name", f"Fase {pid}")
            cog = p.get("cognitive_demand", "HACIENDO_MATEMATICA")
            act = self._ensure_math_formatting(p.get("student_activity", ""))
            teacher = self._ensure_math_formatting(p.get("teacher_role", ""))
            rationale = self._ensure_math_formatting(p.get("example_choice_rationale", "No especificado."))
            udl = p.get("udl_guidelines", {})
            udl_str = f"Repr: {udl.get('representation', 'N/A')} | Acción: {udl.get('action_expression', 'N/A')} | Compromiso: {udl.get('engagement', 'N/A')}"

            phase_lines.append(
                f"\\begin{{tcolorbox}}[colback=white,colframe=primaryBlue,arc=1mm,title=\\textbf{{Fase {pid}: {pname} (Demanda: {cog})}}]\n"
                f"\\textbf{{Actividad del Estudiante:}} {act}\\\\[0.15cm]\n"
                f"\\textbf{{Rol Docente / Mediación:}} {teacher}\\\\[0.15cm]\n"
                f"\\textbf{{Justificación de Ejemplos:}} {rationale}\\\\[0.15cm]\n"
                f"{{\\footnotesize\\color{{gray}}\\textbf{{Pautas DUA:}} {udl_str}}}\n"
                f"\\end{{tcolorbox}}\n\\vspace{{0.2cm}}\n"
            )

        rendered = template
        rendered = rendered.replace("<<UNIT_TITLE>>", meta.get("unit_title", "Unidad Didáctica"))
        rendered = rendered.replace("<<TARGET_GRADE>>", meta.get("target_grade", "General"))
        rendered = rendered.replace("<<ESTIMATED_SESSIONS>>", str(meta.get("estimated_sessions", 1)))
        rendered = rendered.replace("<<MINUTES_PER_SESSION>>", str(meta.get("minutes_per_session", 90)))
        rendered = rendered.replace("<<CURRICULUM_REF>>", meta.get("curriculum_expectation_ref", "Bases Curriculares"))
        rendered = rendered.replace("<<ACTIVE_FRAMEWORKS>>", ", ".join(theo.get("active_frameworks", [])))
        rendered = rendered.replace("<<NETWORKING_JUSTIFICATION>>", theo.get("networking_justification", "Articulación teórica."))
        rendered = rendered.replace("<<PREREQUISITES>>", ", ".join(diag.get("prerequisites_required", [])))
        rendered = rendered.replace("<<MISCONCEPTIONS_BLOCK>>", "\n".join(misc_lines) if misc_lines else "No declaradas.")
        rendered = rendered.replace("<<PHASES_BLOCK>>", "\n".join(phase_lines))

        return rendered

    def render_document(self, assessment_data: Dict[str, Any]) -> str:
        """Renderiza el documento LaTeX completo inyectando metadatos y cuerpo."""
        if "phases" in assessment_data:
            return self.render_didactic_unit(assessment_data)

        if not self.template_path.exists():
            raise FileNotFoundError(f"Plantilla no encontrada en: {self.template_path}")

        with open(self.template_path, "r", encoding="utf-8") as f:
            template_content = f.read()

        meta = assessment_data.get("metadata", {})
        title = meta.get("title", "Evaluación de Matemática")
        total_points = str(meta.get("total_points", 0))

        content_body = self.render_body(assessment_data.get("items", []))

        rendered = template_content.replace("<<METADATA_TITLE>>", title)
        rendered = rendered.replace("<<TOTAL_POINTS>>", total_points)
        rendered = rendered.replace("<<CONTENT_BODY>>", content_body)

        return rendered

    def compile_pdf(self, tex_file_path: Path, output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Intenta compilar con tectonic o pdflatex si están instalados en el sistema."""
        tex_path = Path(tex_file_path)
        out_dir = Path(output_dir) if output_dir else tex_path.parent

        tectonic_cmd = shutil.which("tectonic")
        pdflatex_cmd = shutil.which("pdflatex")

        if tectonic_cmd:
            cmd = [tectonic_cmd, "-o", str(out_dir), str(tex_path)]
            engine_used = "tectonic"
        elif pdflatex_cmd:
            cmd = [pdflatex_cmd, "-interaction=nonstopmode", f"-output-directory={out_dir}", str(tex_path)]
            engine_used = "pdflatex"
        else:
            return {
                "status": "SKIPPED",
                "message": "Ningún compilador LaTeX detectado (Tectonic o pdfLaTeX no están en el PATH). Archivo .tex conservado intacto.",
                "tex_file": str(tex_path)
            }

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if res.returncode == 0:
                pdf_path = out_dir / (tex_path.stem + ".pdf")
                return {
                    "status": "SUCCESS",
                    "engine": engine_used,
                    "pdf_file": str(pdf_path)
                }
            else:
                return {
                    "status": "ERROR",
                    "engine": engine_used,
                    "returncode": res.returncode,
                    "log": res.stdout + res.stderr
                }
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
