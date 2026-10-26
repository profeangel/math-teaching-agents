"""
Módulo de Auditoría de Layout y Maquetación Visual para PDFs (Gate 2).
Inspecciona documentos compilados mediante pypdf para prevenir la 'ilusión del código 0':
detecta desbordes huérfanos, reactivos partidos entre páginas, títulos huérfanos,
violaciones de presupuesto de páginas y corrupción tipográfica de fórmulas (LaTeX residual).
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import re
import pypdf


class LayoutAuditor:
    """Auditor determinista de estructura de páginas y calidad visual de PDFs."""

    # Patrones de comandos o expresiones LaTeX que no fueron adaptados a Typst
    # Typst compila sin error expresiones como \text{m} tratándolas como variables en cursiva
    LATEX_CORRUPTION_PATTERNS = [
        (re.compile(r'(?:\\text|text|𝑡𝑒𝑥𝑡)\s*\{', re.IGNORECASE), "Comando \\text{} no convertido a string entre comillas"),
        (re.compile(r'\d+\s*(?:\\circ|circ|𝑐𝑖𝑟𝑐)', re.IGNORECASE), "Símbolo de grados \\circ no convertido a 'degree' o '°'"),
        (re.compile(r'(?:\\frac|frac|𝑓𝑟𝑎𝑐)\s*\{', re.IGNORECASE), "Fracción \\frac{} no convertida a sintaxis Typst (a/b)"),
        (re.compile(r'(?:\\triangle|triangle|𝑡𝑟𝑖𝑎𝑛𝑔𝑙𝑒)\b', re.IGNORECASE), "Símbolo \\triangle no adaptado a glifo △"),
        (re.compile(r'(?:\\sqrt|sqrt)\s*\{', re.IGNORECASE), "Raíz \\sqrt{} con sintaxis de llaves LaTeX"),
        (re.compile(r'\\(?:mathbb|cdot|pm|leq|geq|neq|alpha|beta|theta)', re.IGNORECASE), "Comandos o letras griegas con barra invertida LaTeX residual"),
    ]

    def __init__(self, default_budget: int = 2):
        self.default_budget = default_budget

    def audit_pdf(
        self,
        pdf_path: Path,
        page_budget: Optional[int] = None,
        min_density_ratio: float = 0.20,
        min_last_page_chars: int = 400,
        strict: bool = False
    ) -> Dict[str, Any]:
        """
        Audita el layout visual de un archivo PDF.
        
        Args:
            pdf_path: Ruta al binario PDF.
            page_budget: Presupuesto máximo esperado de páginas (ej. 2 para anverso/reverso).
            min_density_ratio: Ratio mínimo de caracteres de la última página respecto a la media.
            min_last_page_chars: Mínimo absoluto de caracteres en la última página si hay >1 página.
            strict: Si True, convierte las advertencias en fallos formales.
            
        Returns:
            Dict con dictamen 'PASS' o 'FAIL', métricas de densidad y lista de incidencias.
        """
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            return {
                "status": "ERROR",
                "pdf_path": str(pdf_file),
                "passed": False,
                "error": f"Archivo PDF no encontrado: {pdf_file}",
                "issues": [{"type": "FILE_NOT_FOUND", "severity": "ERROR", "message": f"No existe {pdf_file}"}]
            }

        try:
            reader = pypdf.PdfReader(str(pdf_file))
        except Exception as e:
            return {
                "status": "ERROR",
                "pdf_path": str(pdf_file),
                "passed": False,
                "error": f"Error al leer PDF con pypdf: {e}",
                "issues": [{"type": "CORRUPTED_PDF", "severity": "ERROR", "message": str(e)}]
            }

        total_pages = len(reader.pages)
        budget = page_budget if page_budget is not None else self.default_budget

        page_texts = []
        page_metrics = []
        for i, page in enumerate(reader.pages):
            try:
                txt = page.extract_text() or ""
            except Exception:
                txt = ""
            page_texts.append(txt)
            page_metrics.append({
                "page": i + 1,
                "char_count": len(txt),
                "word_count": len(txt.split()),
                "line_count": len(txt.splitlines())
            })

        issues: List[Dict[str, str]] = []

        # 1. Verificación de Presupuesto de Páginas
        if budget is not None and total_pages > budget:
            issues.append({
                "type": "PAGE_BUDGET_EXCEEDED",
                "severity": "ERROR",
                "message": (
                    f"El documento excede el presupuesto de páginas físicas: "
                    f"se esperaban máximo {budget} página(s), pero el PDF tiene {total_pages} páginas."
                )
            })

        # 2. Verificación de Desborde Huérfano en la Última Página
        if total_pages > 1:
            prev_chars = [m["char_count"] for m in page_metrics[:-1]]
            avg_prev = sum(prev_chars) / len(prev_chars) if prev_chars else 1
            last_chars = page_metrics[-1]["char_count"]
            density_ratio = last_chars / avg_prev if avg_prev > 0 else 1.0

            # Si la última página tiene muy poco contenido y el ratio es ínfimo (ej. solo 2-3 líneas)
            if last_chars < min_last_page_chars and density_ratio < min_density_ratio:
                issues.append({
                    "type": "ORPHAN_OVERFLOW",
                    "severity": "ERROR",
                    "message": (
                        f"Desborde huérfano detectado en página {total_pages}: contiene solo {last_chars} caracteres "
                        f"({density_ratio * 100:.1f}% de la densidad promedio). Típico de ejercicios huérfanos que desbordan 2 o 3 líneas."
                    )
                })

        # 3. Detección de Corrupción Tipográfica (LaTeX residual en Typst)
        for i, txt in enumerate(page_texts, start=1):
            for pattern, desc in self.LATEX_CORRUPTION_PATTERNS:
                matches = pattern.findall(txt)
                if matches:
                    sample = matches[:3]
                    issues.append({
                        "type": "LATEX_SYNTAX_BLEED",
                        "severity": "ERROR",
                        "message": (
                            f"En página {i}: {desc}. Muestras detectadas en PDF: {sample}. "
                            f"Typst compila esto sin error tratándolo como variables en cursiva."
                        )
                    })

        # 4. Detección de Ítems Evaluativos Partidos entre Páginas
        for i in range(len(page_texts) - 1):
            curr_txt = page_texts[i]
            next_txt = page_texts[i + 1]

            curr_lines = [l.strip() for l in curr_txt.splitlines() if l.strip()]
            next_lines = [l.strip() for l in next_txt.splitlines() if l.strip()]

            # Buscar si la página actual termina con opciones (A) o (B) de un ítem evaluativo
            tail = " ".join(curr_lines[-5:]) if len(curr_lines) >= 5 else " ".join(curr_lines)
            head = " ".join(next_lines[:5]) if len(next_lines) >= 5 else " ".join(next_lines)

            has_early_options_tail = bool(re.search(r'\(A\).*?\(B\)', tail))
            has_late_options_head = bool(re.search(r'^\s*\(C\)|(?:\(C\).*?\(D\))', head))

            if has_early_options_tail and has_late_options_head:
                issues.append({
                    "type": "SPLIT_ITEM_DETECTED",
                    "severity": "ERROR",
                    "message": (
                        f"Reactivo evaluativo partido entre Página {i + 1} y Página {i + 2}: "
                        f"las opciones (A)/(B) quedaron al pie de la primera y (C)/(D) en la cabecera de la siguiente. "
                        f"Debe envolverse en #block(breakable: false)."
                    )
                })

        # 5. Detección de Títulos y Encabezados Huérfanos al fondo de página
        header_patterns = re.compile(r'^(?:===|==|#|Parte\s+\d+|Sección\s+[IVX\d]+|Bloque\s+\d+)', re.IGNORECASE)
        for i in range(len(page_texts) - 1):
            curr_lines = [l.strip() for l in page_texts[i].splitlines() if l.strip()]
            if curr_lines:
                last_line = curr_lines[-1]
                if header_patterns.search(last_line) and len(last_line) < 60:
                    issues.append({
                        "type": "ORPHAN_HEADER",
                        "severity": "ERROR",
                        "message": (
                            f"Encabezado huérfano detectado al pie de Página {i + 1}: '{last_line}'. "
                            f"Quedó cortado sin contenido debajo antes del salto de página."
                        )
                    })

        has_errors = any(iss["severity"] == "ERROR" for iss in issues)
        status = "FAIL" if has_errors else "PASS"

        return {
            "status": status,
            "pdf_path": str(pdf_file),
            "passed": status == "PASS",
            "total_pages": total_pages,
            "page_budget": budget,
            "issues_count": len(issues),
            "issues": issues,
            "metrics": {
                "pages": page_metrics,
                "density_ratio_last_page": round(page_metrics[-1]["char_count"] / (sum(m["char_count"] for m in page_metrics[:-1]) / max(1, len(page_metrics) - 1)), 2) if total_pages > 1 else 1.0
            }
        }
