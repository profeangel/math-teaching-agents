"""
Motor de Maquetación y Renderizado Typst para evaluaciones e instrumentos matemáticos.
Soporte integral para sintaxis moderna de Typst (0.11+) y detección de binario local/winget.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import os
import shutil
import subprocess
import re

KNOWN_TYPST_KEYWORDS = {
    'sin', 'cos', 'tan', 'cot', 'sec', 'csc', 'arcsin', 'arccos', 'arctan',
    'ln', 'log', 'exp', 'det', 'dim', 'gcd', 'lcm', 'lim', 'max', 'min',
    'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'eta', 'theta',
    'iota', 'kappa', 'lambda', 'mu', 'nu', 'xi', 'pi', 'rho', 'sigma',
    'tau', 'upsilon', 'phi', 'chi', 'psi', 'omega',
    'Gamma', 'Delta', 'Theta', 'Lambda', 'Xi', 'Pi', 'Sigma', 'Upsilon',
    'Phi', 'Psi', 'Omega', 'RR', 'NN', 'ZZ', 'QQ', 'CC',
    'sqrt', 'root', 'dot', 'times', 'plus', 'minus', 'infinity', 'in'
}


class TypstEngine:
    """Inyecta borradores semánticos en plantillas Typst oficiales y gestiona la compilación."""

    def __init__(self, template_path: Optional[Path] = None):
        if template_path:
            self.template_path = Path(template_path)
        else:
            current = Path(__file__).resolve()
            root = current.parents[3]
            self.template_path = root / "templates" / "typst" / "standard-evaluation.typ"

    @classmethod
    def _ensure_math_formatting(cls, text: str) -> str:
        """
        Garantiza que variables, ecuaciones y expresiones algebraicas en las alternativas
        se maqueten siempre en modo matemático formal y no en texto plano.
        """
        if not text or '$' in text:
            return text
        # Convertir ecuaciones tipo x = 2 o t = 5
        res = re.sub(r'([a-zA-Z]\s*=\s*-?\d+(?:/\d+)?)', r'$\1$', text)
        if res != text:
            return res
        # Si es puramente algebraico o numérico con operadores (ej: 2/4 o -2, 3)
        if re.match(r'^[0-9a-zA-Z+\-*/^=,.\s\(\)\{\}\\]+$', text) and any(c in text for c in '=+-*/^'):
            return f"${text.strip()}$"
        return text

    @staticmethod
    def _sanitize_for_typst(text: str) -> str:
        """Adapta construcciones matemáticas comunes de LaTeX a Typst si es necesario."""
        if not text:
            return ""

        def replace_math_block(match):
            content = match.group(1)

            # 1. Blackboard bold y conjuntos canónicos
            content = re.sub(r'\\mathbb\{R\}', 'RR', content)
            content = re.sub(r'\\mathbb\{N\}', 'NN', content)
            content = re.sub(r'\\mathbb\{Z\}', 'ZZ', content)
            content = re.sub(r'\\mathbb\{Q\}', 'QQ', content)
            content = re.sub(r'\\mathbb\{C\}', 'CC', content)

            # 2. Llaves de conjuntos en Typst: \{ y \} -> { y }
            content = content.replace(r'\{', '{').replace(r'\}', '}')

            # 3. Fracciones \frac{num}{den} -> ((num)/(den))
            for _ in range(5):
                new_c = re.sub(r'\\frac\{([^{}]+)\}\{([^{}]+)\}', r'((\1)/(\2))', content)
                if new_c == content:
                    break
                content = new_c

            # 4. Raíces
            content = re.sub(r'\\sqrt\[([^\]]+)\]\{([^{}]+)\}', r'root(\1, \2)', content)
            content = re.sub(r'\\sqrt\{([^{}]+)\}', r'sqrt(\1)', content)

            # 5. Operadores y relaciones
            content = re.sub(r'\\cdot', ' dot ', content)
            content = re.sub(r'\\times', ' times ', content)
            content = re.sub(r'\\pm', ' plus.minus ', content)
            content = re.sub(r'\\leq?', ' <= ', content)
            content = re.sub(r'\\geq?', ' >= ', content)
            content = re.sub(r'\\neq', ' != ', content)
            content = re.sub(r'\\notin', ' in.not ', content)
            content = re.sub(r'\\in', ' in ', content)
            content = re.sub(r'\\infty', ' infinity ', content)

            # 6. Letras griegas y funciones matemáticas
            greek_and_fns = (
                r'\\(alpha|beta|gamma|delta|epsilon|zeta|eta|theta|iota|kappa|lambda|mu|nu|xi|pi|rho|sigma|tau|upsilon|phi|chi|psi|omega|'
                r'Gamma|Delta|Theta|Lambda|Xi|Pi|Sigma|Upsilon|Phi|Psi|Omega|'
                r'sin|cos|tan|cot|sec|csc|arcsin|arccos|arctan|ln|log|exp|det|dim|gcd|lcm|lim|max|min)'
            )
            content = re.sub(greek_and_fns, r'\1', content)

            # 7. Separar dígitos seguidos de letras: 4ac -> 4 ac
            content = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', content)

            # 8. Separar letras yuxtapuestas desconocidas: ac -> a c
            def repl_word(m):
                w = m.group(0)
                if w in KNOWN_TYPST_KEYWORDS:
                    return w
                return ' '.join(list(w))

            content = re.sub(r'[a-zA-Z]{2,}', repl_word, content)

            # 9. Limpiar barras invertidas huérfanas
            content = re.sub(r'\\([a-zA-Z])', r'\1', content)

            return f"${content.strip()}$"

        # Reemplazar expresiones matemáticas $...$
        return re.sub(r'\$(.*?)\$', replace_math_block, text)

    def render_body(self, items: list) -> str:
        """Genera el bloque tipográfico de ítems para el cuerpo del documento Typst."""
        blocks = []
        for idx, item in enumerate(items, start=1):
            points = item.get("points", 1)
            pts_str = f"({points} pt)" if points == 1 else f"({points} pts)"
            stem = self._sanitize_for_typst(item.get("stem", ""))
            fmt = item.get("format", "OPEN_DEVELOPMENT")

            item_lines = [
                f"*Ítem {idx}* {pts_str} \\",
                f"{stem}\n"
            ]

            if fmt == "MULTIPLE_CHOICE" and "options" in item:
                grid_items = []
                for opt in item["options"]:
                    lbl = opt.get("key") or opt.get("label", "")
                    txt = self._sanitize_for_typst(self._ensure_math_formatting(opt.get("text", "")))
                    grid_items.append(f"  [*({lbl})* {txt}]")
                grid_str = "#grid(\n  columns: (1fr, 1fr),\n  row-gutter: 8pt,\n" + ",\n".join(grid_items) + "\n)\n"
                item_lines.append(grid_str)
            elif fmt in ("OPEN_DEVELOPMENT", "PROOF_ARGUMENT"):
                box_str = (
                    "#v(4pt)\n"
                    "#rect(width: 100%, height: 4.5cm, stroke: 0.5pt + rgb(\"#94a3b8\"), radius: 2pt, inset: 6pt)[\n"
                    "  #text(size: 8pt, fill: rgb(\"#64748b\"), style: \"italic\")[Espacio reservado para desarrollo y justificación axiomática]\n"
                    "]\n"
                )
                item_lines.append(box_str)

            item_lines.append("#v(10pt)\n")
            blocks.append("\n".join(item_lines))

        return "\n".join(blocks)

    def render_didactic_unit(self, unit_data: Dict[str, Any]) -> str:
        """Renderiza una unidad didáctica completa y secuencia de clase en Typst."""
        root = Path(__file__).resolve().parents[3]
        unit_tmpl_path = root / "templates" / "typst" / "standard-didactic-unit.typ"
        with open(unit_tmpl_path, "r", encoding="utf-8") as f:
            template = f.read()

        meta = unit_data.get("metadata", {})
        theo = unit_data.get("theoretical_alignment", {})
        diag = unit_data.get("epistemological_diagnostics", {})
        phases = unit_data.get("phases", [])

        # Bloque de concepciones erróneas
        misconceptions = diag.get("target_misconceptions", [])
        misc_rows = []
        for m in misconceptions:
            code = m.get("code", "")
            desc = self._sanitize_for_typst(self._ensure_math_formatting(m.get("description", "")))
            strat = self._sanitize_for_typst(self._ensure_math_formatting(m.get("confrontation_strategy", "")))
            misc_rows.append(f'  [*{code}*], [{desc}], [{strat}]')

        if misc_rows:
            misc_table = (
                "#table(\n"
                "  columns: (1fr, 2fr, 2.5fr),\n"
                "  stroke: 0.5pt + luma(130),\n"
                "  fill: (col, row) => if row == 0 { rgb(\"#f1f5f9\") } else { none },\n"
                "  inset: 5pt,\n"
                "  [*Código*], [*Concepción Errónea / Obstáculo*], [*Estrategia de Confrontación*],\n"
                + ",\n".join(misc_rows) + "\n)\n"
            )
        else:
            misc_table = "[_No se declararon concepciones erróneas específicas._]"

        # Bloque de fases de la secuencia didáctica
        phase_blocks = []
        for p in phases:
            pid = p.get("phase_id", 1)
            pname = p.get("phase_name", f"Fase {pid}")
            cog = p.get("cognitive_demand", "HACIENDO_MATEMATICA")
            act = self._sanitize_for_typst(self._ensure_math_formatting(p.get("student_activity", "")))
            teacher = self._sanitize_for_typst(self._ensure_math_formatting(p.get("teacher_role", "")))
            rationale = self._sanitize_for_typst(self._ensure_math_formatting(p.get("example_choice_rationale", "No especificado.")))
            udl = p.get("udl_guidelines", {})
            udl_str = f"Repr: {udl.get('representation', 'N/A')} | Acción: {udl.get('action_expression', 'N/A')} | Compromiso: {udl.get('engagement', 'N/A')}"
            dyn_ref = p.get("dynamic_artifact_ref")
            dyn_line = f"\\ *Artefacto Dinámico:* `{dyn_ref}`" if dyn_ref else ""

            phase_rect = (
                "#rect(\n"
                "  width: 100%,\n"
                "  stroke: 0.7pt + rgb(\"#3b82f6\"),\n"
                "  radius: 3pt,\n"
                "  inset: 8pt\n"
                ")[\n"
                f"  #grid(\n"
                f"    columns: (3fr, 1.5fr),\n"
                f"    [#text(weight: \"bold\", size: 10.5pt, fill: rgb(\"#1e40af\"))[Fase {pid}: {pname}]],\n"
                f"    [#align(right)[#text(size: 8pt, weight: \"bold\", fill: rgb(\"#1d4ed8\"))[Demanda: {cog}]]]\n"
                f"  )\n"
                f"  #v(3pt)\n"
                f"  *Actividad del Estudiante:* {act} \\\n"
                f"  #v(2pt)\n"
                f"  *Rol y Mediación Docente:* {teacher} \\\n"
                f"  #v(2pt)\n"
                f"  *Justificación de Ejemplos (Rowland):* {rationale} \\\n"
                f"  #v(2pt)\n"
                f"  #text(size: 8.5pt, fill: rgb(\"#475569\"))[*Pautas DUA:* {udl_str} {dyn_line}]\n"
                "]\n"
                "#v(6pt)\n"
            )
            phase_blocks.append(phase_rect)

        rendered = template
        rendered = rendered.replace("<<UNIT_TITLE>>", meta.get("unit_title", "Unidad Didáctica"))
        rendered = rendered.replace("<<TARGET_GRADE>>", meta.get("target_grade", "General"))
        rendered = rendered.replace("<<ESTIMATED_SESSIONS>>", str(meta.get("estimated_sessions", 1)))
        rendered = rendered.replace("<<MINUTES_PER_SESSION>>", str(meta.get("minutes_per_session", 90)))
        rendered = rendered.replace("<<CURRICULUM_REF>>", meta.get("curriculum_expectation_ref", "Bases Curriculares"))
        rendered = rendered.replace("<<ACTIVE_FRAMEWORKS>>", ", ".join(theo.get("active_frameworks", [])))
        rendered = rendered.replace("<<NETWORKING_JUSTIFICATION>>", theo.get("networking_justification", "Articulación teórica didáctica."))
        rendered = rendered.replace("<<PREREQUISITES>>", ", ".join(diag.get("prerequisites_required", [])))
        rendered = rendered.replace("<<MISCONCEPTIONS_BLOCK>>", misc_table)
        rendered = rendered.replace("<<PHASES_BLOCK>>", "\n".join(phase_blocks))

        return rendered

    def render_document(self, assessment_data: Dict[str, Any]) -> str:
        """Renderiza el documento Typst completo inyectando metadatos y cuerpo."""
        if "phases" in assessment_data:
            return self.render_didactic_unit(assessment_data)

        if not self.template_path.exists():
            raise FileNotFoundError(f"Plantilla Typst no encontrada en: {self.template_path}")

        with open(self.template_path, "r", encoding="utf-8") as f:
            template_content = f.read()

        meta = assessment_data.get("metadata", {})
        title = meta.get("title", "Evaluación de Matemática")
        total_points = str(meta.get("total_points", 0))

        content_body = self.render_body(assessment_data.get("items", []))

        rendered = template_content.replace("<<METADATA_TITLE>>", title).replace("<<TOTAL_POINTS>>", total_points).replace("<<CONTENT_BODY>>", content_body)

        return rendered

    def compile_pdf(self, typ_file_path: Path, output_pdf_path: Optional[Path] = None) -> Dict[str, Any]:
        """Compila un archivo Typst a PDF utilizando el binario oficial typst."""
        typ_path = Path(typ_file_path)
        out_pdf = Path(output_pdf_path) if output_pdf_path else typ_path.with_suffix(".pdf")

        binary = shutil.which("typst")
        if not binary:
            # Intentar localizar en WinGet Packages
            local_appdata = os.environ.get("LOCALAPPDATA", "")
            if local_appdata:
                winget_pkgs = Path(local_appdata) / "Microsoft" / "WinGet" / "Packages"
                candidates = list(winget_pkgs.glob("**/typst.exe"))
                if candidates:
                    binary = str(candidates[0])

        if not binary:
            return {
                "status": "SKIPPED",
                "message": "Binario 'typst' no encontrado en el sistema. Instale Typst para compilar a PDF."
            }

        try:
            cmd = [binary, "compile", str(typ_path), str(out_pdf)]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
            if proc.returncode == 0:
                return {
                    "status": "SUCCESS",
                    "pdf_file": str(out_pdf),
                    "log": proc.stdout
                }
            else:
                return {
                    "status": "FAIL",
                    "error": proc.stderr,
                    "returncode": proc.returncode
                }
        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"Error ejecutando compilador Typst: {e}"
            }
