"""
Motor de Exportación a Formato Moodle XML.
Permite interoperabilidad directa con Entornos Virtuales de Aprendizaje (LMS)
como Moodle, Canvas, Blackboard y Chamilo.
"""

from typing import Dict, Any, List
import html
import re
from xml.sax.saxutils import escape


class MoodleEngine:
    """Transforma especificaciones neutras de evaluación a Moodle XML estándar."""

    def __init__(self):
        pass

    def _sanitize_math_for_lms(self, text: str) -> str:
        """
        Normaliza delimitadores matemáticos para compatibilidad con MathJax / KaTeX en LMS.
        Convierte $...$ a \\( ... \\) para evitar colisiones con signos de moneda en HTML.
        """
        # Reemplazar $expr$ por \(expr\)
        def repl(match):
            content = match.group(1)
            return f"\\({content}\\)"

        return re.sub(r"\$([^\$]+)\$", repl, text)

    def _format_html_text(self, text: str) -> str:
        """Envuelve texto en párrafo HTML y normaliza fórmulas."""
        sanitized = self._sanitize_math_for_lms(text)
        return f"<p>{sanitized}</p>"

    def render_document(self, assessment_data: Dict[str, Any]) -> str:
        """Genera el documento XML completo en formato Moodle XML."""
        metadata = assessment_data.get("metadata", {})
        title = metadata.get("title", "Evaluación de Matemática")
        items = assessment_data.get("items", [])
        category_name = f"{title} ({metadata.get('target_grade', 'General')})"

        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<quiz>',
            '  <!-- Categoría de Importación en el Banco de Preguntas -->',
            '  <question type="category">',
            '    <category>',
            f'      <text>$course$/top/{escape(category_name)}</text>',
            '    </category>',
            '  </question>',
            ''
        ]

        for item in items:
            item_id = item.get("item_id", 1)
            fmt = item.get("format", "MULTIPLE_CHOICE")
            points = item.get("points", 1)
            stem = item.get("stem", "")
            bloom = item.get("bloom_anderson_level", "APLICAR")
            mtsk = item.get("mtsk_subdomain", "KoT")

            # Resumen para el nombre de la pregunta
            stem_clean = re.sub(r"[\$\\]", "", stem)[:50].strip()
            q_name = f"Ítem {item_id} [{mtsk}-{bloom}]: {stem_clean}..."

            if fmt == "MULTIPLE_CHOICE":
                lines.extend(self._render_multichoice(item, q_name, stem, points))
            else:
                lines.extend(self._render_essay(item, q_name, stem, points))

        lines.append('</quiz>')
        return "\n".join(lines)

    def _render_multichoice(self, item: Dict[str, Any], q_name: str, stem: str, points: float) -> List[str]:
        lines = [
            '  <!-- Pregunta de Selección Múltiple -->',
            '  <question type="multichoice">',
            f'    <name><text>{escape(q_name)}</text></name>',
            '    <questiontext format="html">',
            f'      <text><![CDATA[{self._format_html_text(stem)}]]></text>',
            '    </questiontext>',
            f'    <defaultgrade>{points}</defaultgrade>',
            '    <penalty>0.0000000</penalty>',
            '    <hidden>0</hidden>',
            '    <single>true</single>',
            '    <shuffleanswers>true</shuffleanswers>',
            '    <answernumbering>abc</answernumbering>'
        ]

        options = item.get("options", [])
        for opt in options:
            is_correct = opt.get("is_correct", False)
            fraction = "100" if is_correct else "0"
            text = opt.get("text", "")
            feedback = opt.get("feedback_clue", "")
            misconception = opt.get("misconception_ref")

            feedback_content = feedback
            if misconception:
                feedback_content += f" [Diagnóstico didáctico: {misconception}]"

            lines.extend([
                f'    <answer fraction="{fraction}" format="html">',
                f'      <text><![CDATA[{self._format_html_text(text)}]]></text>',
                '      <feedback format="html">',
                f'        <text><![CDATA[{self._format_html_text(feedback_content)}]]></text>',
                '      </feedback>',
                '    </answer>'
            ])

        lines.append('  </question>\n')
        return lines

    def _render_essay(self, item: Dict[str, Any], q_name: str, stem: str, points: float) -> List[str]:
        lines = [
            '  <!-- Pregunta de Desarrollo / Demostración Abierta -->',
            '  <question type="essay">',
            f'    <name><text>{escape(q_name)}</text></name>',
            '    <questiontext format="html">',
            f'      <text><![CDATA[{self._format_html_text(stem)}]]></text>',
            '    </questiontext>',
            f'    <defaultgrade>{points}</defaultgrade>',
            '    <responseformat>editor</responseformat>',
            '    <responserequired>1</responserequired>',
            '    <responsefieldlines>15</responsefieldlines>'
        ]

        rubric = item.get("rubric")
        if rubric:
            criterion = rubric.get("criterion_name", "Criterio de Evaluación")
            levels = rubric.get("levels", {})
            graderinfo_parts = [f"<h4>Rúbrica de Corrección: {escape(criterion)}</h4><ul>"]
            for level_name, desc in levels.items():
                graderinfo_parts.append(f"<li><strong>{escape(level_name.capitalize())}:</strong> {escape(desc)}</li>")
            graderinfo_parts.append("</ul>")
            graderinfo_html = "".join(graderinfo_parts)

            lines.extend([
                '    <graderinfo format="html">',
                f'      <text><![CDATA[{graderinfo_html}]]></text>',
                '    </graderinfo>'
            ])

        lines.append('  </question>\n')
        return lines
