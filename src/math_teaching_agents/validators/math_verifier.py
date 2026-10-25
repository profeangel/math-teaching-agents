"""
Motor de Verificación Simbólica Formal con SymPy para Gate 1 (Zero-Trust).
Blindaje analítico contra alucinaciones aritméticas, algebraicas y distractores duplicados.
"""

from typing import Dict, Any, List, Optional
import re
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application


def _parse_balanced_braces(s: str, pos: int):
    """Extrae el contenido de un bloque delimitado por llaves { ... } balanceadas."""
    if pos >= len(s) or s[pos] != '{':
        return None, pos
    depth = 1
    i = pos + 1
    while i < len(s) and depth > 0:
        if s[i] == '{':
            depth += 1
        elif s[i] == '}':
            depth -= 1
        i += 1
    if depth == 0:
        return s[pos + 1:i - 1], i
    return None, pos


def latex_to_sympy_str(latex: str) -> str:
    """
    Convierte expresiones matemáticas en sintaxis LaTeX a una cadena procesable por SymPy.
    Maneja fracciones anidadas \\frac{A}{B}, raíces \\sqrt[n]{A}, operadores y macros.
    """
    s = latex.strip()
    # Eliminar delimitadores de modo matemático
    s = re.sub(r'^\$+|\$+$', '', s).strip()
    s = s.replace(r'\(', '').replace(r'\)', '').replace(r'\[', '').replace(r'\]', '')

    # Eliminar macros de formato y estilo visual
    s = re.sub(r'\\(?:left|right|displaystyle|limits)', '', s)
    s = re.sub(r'\\(?:text|mathrm|textbf)\{([^}]*)\}', r'\1', s)

    # Normalizar constantes, símbolos y unidades angulares
    s = s.replace(r'\pi', 'pi').replace(r'\infty', 'oo')
    s = s.replace(r'^\circ', '').replace(r'\circ', '').replace(r'\degree', '').replace('°', '')

    # Normalizar operadores
    s = s.replace(r'\cdot', '*').replace(r'\times', '*').replace('^', '**')

    # Convertir recursivamente fracciones \frac{numerador}{denominador}
    while r'\frac' in s:
        idx = s.find(r'\frac')
        p1 = idx + 5
        while p1 < len(s) and s[p1].isspace():
            p1 += 1
        num, p2 = _parse_balanced_braces(s, p1)
        if num is None:
            break
        while p2 < len(s) and s[p2].isspace():
            p2 += 1
        den, p3 = _parse_balanced_braces(s, p2)
        if den is None:
            break
        num_conv = latex_to_sympy_str(num)
        den_conv = latex_to_sympy_str(den)
        s = s[:idx] + f'(({num_conv})/({den_conv}))' + s[p3:]

    # Convertir raíces \sqrt[n]{arg} o \sqrt{arg}
    while r'\sqrt' in s:
        idx = s.find(r'\sqrt')
        p = idx + 5
        n_deg = '2'
        if p < len(s) and s[p] == '[':
            close_b = s.find(']', p)
            if close_b != -1:
                n_deg = s[p + 1:close_b]
                p = close_b + 1
        while p < len(s) and s[p].isspace():
            p += 1
        arg, p_end = _parse_balanced_braces(s, p)
        if arg is None:
            break
        arg_conv = latex_to_sympy_str(arg)
        if n_deg.strip() == '2':
            s = s[:idx] + f'(sqrt({arg_conv}))' + s[p_end:]
        else:
            s = s[:idx] + f'(({arg_conv})**(1/({n_deg})))' + s[p_end:]

    # Reemplazar llaves remanentes por paréntesis
    s = s.replace('{', '(').replace('}', ')')
    return s


class SymbolicMathVerifier:
    """Verifica la consistencia matemática formal de ítems de evaluación."""

    def __init__(self):
        self.transformations = standard_transformations + (implicit_multiplication_application,)

    def parse_math(self, expr_str: str) -> sp.Expr:
        """
        Parsea una expresión matemática (en sintaxis LaTeX o texto algebraico) a objeto SymPy.
        """
        clean = latex_to_sympy_str(expr_str)
        return parse_expr(clean, transformations=self.transformations)

    def canonicalize_option_value(self, text: str) -> str:
        """
        Calcula la forma canónica unificada de una alternativa para detectar equivalencias o distractores duplicados.
        Soporta:
        - Conjuntos solución: \\{2, 3\\} == \\{3, 2\\}
        - Fracciones vs decimales: \\frac{1}{2} == 0.5
        - Expresiones algebraicas equivalentes: 2(x+1) == 2x+2
        """
        cleaned = text.strip()
        cleaned = re.sub(r'^\$+|\$+$', '', cleaned).strip()

        # Detección de conjunto solución: \{ ... \} o { ... }
        is_escaped_set = cleaned.startswith(r'\{') and cleaned.endswith(r'\}')
        is_raw_set = cleaned.startswith('{') and cleaned.endswith('}')
        if is_escaped_set or is_raw_set:
            inner = cleaned[2:-2] if is_escaped_set else cleaned[1:-1]
            parts = [p.strip() for p in inner.split(',') if p.strip()]
            canonical_elements = []
            for p in parts:
                try:
                    expr = self.parse_math(p)
                    simp = sp.nsimplify(sp.simplify(expr))
                    canonical_elements.append(str(simp))
                except Exception:
                    canonical_elements.append(p.lower().strip())
            return "SET:{" + ",".join(sorted(canonical_elements)) + "}"

        # Expresión matemática regular
        try:
            expr = self.parse_math(cleaned)
            simp = sp.nsimplify(sp.simplify(expr))
            return str(simp)
        except Exception:
            # Fallback a texto normalizado
            return cleaned.lower().strip()

    def verify_equation_solutions(self, equation_str: str, proposed_solutions: List[str], var_symbol: str = "x") -> Dict[str, Any]:
        """
        Verifica formalmente si las soluciones propuestas satisfacen la ecuación.
        Ecuación en formato 'LHS = RHS' o 'EXPR = 0'.
        """
        x = sp.Symbol(var_symbol)
        clean_eq = re.sub(r'^\$+|\$+$', '', equation_str).strip()
        if "=" in clean_eq:
            lhs_str, rhs_str = clean_eq.split("=", 1)
            lhs = self.parse_math(lhs_str)
            rhs = self.parse_math(rhs_str)
            eq = sp.Eq(lhs, rhs)
        else:
            eq = sp.Eq(self.parse_math(clean_eq), 0)

        true_solutions = sp.solve(eq, x)
        evaluated_solutions = []
        all_valid = True

        for sol_str in proposed_solutions:
            clean_sol = re.sub(r'^\$+|\$+$', '', sol_str).strip()
            # Si la solución viene en forma x = valor
            if "=" in clean_sol:
                clean_sol = clean_sol.split("=", 1)[1].strip()

            try:
                sol_expr = self.parse_math(clean_sol)
                satisfied = False
                for true_sol in true_solutions:
                    diff = sp.simplify(sol_expr - true_sol)
                    if diff == 0:
                        satisfied = True
                        break
            except Exception:
                satisfied = False

            evaluated_solutions.append({
                "proposed": sol_str,
                "is_valid_solution": satisfied
            })
            if not satisfied:
                all_valid = False

        return {
            "equation": str(eq),
            "true_solutions": [str(s) for s in true_solutions],
            "verified_solutions": evaluated_solutions,
            "all_valid": all_valid
        }

    def verify_multiple_choice_item(self, item_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Audita un ítem de opción múltiple:
        1. Comprueba que las opciones sean mutuamente excluyentes (sin distractores matemáticamente idénticos).
        2. Si contiene ecuación y soluciones, verifica la veracidad de la clave y de los distractores.
        """
        options = item_dict.get("options", [])
        if not options:
            return {"status": "SKIP", "reason": "No contiene opciones de selección múltiple"}

        simplified_options = []
        duplicates = []
        seen = {}

        for opt in options:
            label = opt.get("key") or opt.get("label", "")
            text = opt.get("text", "")
            canonical_form = self.canonicalize_option_value(text)

            if canonical_form in seen:
                prev_label = seen[canonical_form]
                duplicates.append(
                    f"Opción {label} ('{text}') es matemáticamente equivalente a la opción {prev_label} ('{canonical_form}')."
                )
            else:
                seen[canonical_form] = label

            simplified_options.append({
                "label": label,
                "raw_text": text,
                "canonical_form": canonical_form,
                "is_correct": opt.get("is_correct", False),
                "misconception_code": opt.get("misconception_code", None)
            })

        num_correct = sum(1 for opt in options if opt.get("is_correct"))

        verdict = {
            "status": "PASS" if (len(duplicates) == 0 and num_correct == 1) else "FAIL",
            "has_single_correct_answer": num_correct == 1,
            "distractors_unique": len(duplicates) == 0,
            "duplicates": duplicates,
            "options_analyzed": len(options)
        }

        # Si el ítem declara explícitamente una verificación de ecuación o invariante:
        if "math_verification" in item_dict:
            mv = item_dict["math_verification"]
            mv_type = str(mv.get("type", "")).lower()
            if mv_type == "equation_roots":
                eq_check = self.verify_equation_solutions(
                    equation_str=mv["equation"],
                    proposed_solutions=[mv["expected_solution"]],
                    var_symbol=mv.get("variable", "x")
                )
                verdict["equation_check"] = eq_check
                if not eq_check["all_valid"]:
                    verdict["status"] = "FAIL"
                    verdict["error_detail"] = "La clave declarada correcta NO satisface formalmente la ecuación."
            elif mv_type in ("triangle", "triangle_inequality", "polygon_angles", "angles", "pythagorean", "right_triangle", "circle", "circle_invariants", "geometric"):
                geom_check = self.verify_geometric_constraints(mv)
                verdict["geometric_check"] = geom_check
                if not geom_check.get("valid", False):
                    verdict["status"] = "FAIL"
                    verdict["error_detail"] = geom_check.get("error", "Fallo de restricción geométrica formal.")
            elif mv_type in ("probability", "probability_distribution"):
                prob_check = self.verify_probability_distribution(
                    probabilities=mv.get("probabilities", []),
                    check_partition_sum=mv.get("check_partition_sum", True)
                )
                verdict["probability_check"] = prob_check
                if not prob_check.get("all_valid", False):
                    verdict["status"] = "FAIL"
                    verdict["error_detail"] = prob_check.get("error", "Fallo en axiomas de probabilidad.")
            elif mv_type in ("combinatorics", "combinatorial", "permutation_combination"):
                comb_check = self.verify_combinatorics_values(
                    n=mv.get("n"),
                    k=mv.get("k"),
                    claimed_combinations=mv.get("combinations"),
                    claimed_permutations=mv.get("permutations")
                )
                verdict["combinatorics_check"] = comb_check
                if not comb_check.get("all_valid", False):
                    verdict["status"] = "FAIL"
                    verdict["error_detail"] = comb_check.get("error", "Fallo en cálculo combinatorio.")

        return verdict

    def verify_triangle_inequality(self, a: Any, b: Any, c: Any) -> Dict[str, Any]:
        """
        Verifica formalmente la desigualdad triangular para lados a, b, c:
        1. a > 0, b > 0, c > 0
        2. a + b > c, a + c > b, b + c > a
        """
        try:
            expr_a = self.parse_math(str(a))
            expr_b = self.parse_math(str(b))
            expr_c = self.parse_math(str(c))
        except Exception as e:
            return {
                "valid": False,
                "error": f"Error parseando lados del triángulo: {e}",
                "sides": [str(a), str(b), str(c)]
            }

        # Comprobar positividad
        for name, val in [("a", expr_a), ("b", expr_b), ("c", expr_c)]:
            try:
                num = float(sp.N(val))
                if num <= 0:
                    return {
                        "valid": False,
                        "error": f"Lado {name}={val} no es estrictamente positivo (> 0).",
                        "sides": [str(expr_a), str(expr_b), str(expr_c)]
                    }
            except Exception:
                pass

        # Desigualdad triangular estricta
        diff1 = sp.simplify(expr_a + expr_b - expr_c)
        diff2 = sp.simplify(expr_a + expr_c - expr_b)
        diff3 = sp.simplify(expr_b + expr_c - expr_a)

        try:
            val1 = float(sp.N(diff1))
            val2 = float(sp.N(diff2))
            val3 = float(sp.N(diff3))
            is_valid = (val1 > 0 and val2 > 0 and val3 > 0)
        except Exception:
            is_valid = bool(diff1.is_positive and diff2.is_positive and diff3.is_positive)

        error_msg = None
        if not is_valid:
            error_msg = (
                f"Violación de la desigualdad triangular con lados ({expr_a}, {expr_b}, {expr_c}). "
                f"La suma de cualquier par de lados debe ser estrictamente mayor al tercero."
            )

        return {
            "valid": is_valid,
            "sides": [str(expr_a), str(expr_b), str(expr_c)],
            "error": error_msg
        }

    def verify_polygon_angles(self, angles: List[Any], n_sides: Optional[int] = None) -> Dict[str, Any]:
        """
        Verifica la suma de ángulos interiores de un polígono de n lados:
        Suma esperada = (n - 2) * 180°
        Cada ángulo debe ser estrictamente positivo (> 0) y < 360°.
        """
        if not angles:
            return {"valid": False, "error": "Lista de ángulos vacía."}

        n = n_sides or len(angles)
        if n < 3:
            return {"valid": False, "error": f"Un polígono debe tener al menos 3 lados/ángulos (recibido {n})."}

        expected_sum = (n - 2) * 180
        parsed_angles = []
        for ang in angles:
            try:
                parsed_angles.append(self.parse_math(str(ang)))
            except Exception as e:
                return {"valid": False, "error": f"Error parseando ángulo '{ang}': {e}"}

        # Verificar rango de cada ángulo
        for i, val in enumerate(parsed_angles):
            try:
                num = float(sp.N(val))
                if num <= 0:
                    return {"valid": False, "error": f"Ángulo {i+1} ({val}) no es positivo (> 0)."}
                if num >= 360:
                    return {"valid": False, "error": f"Ángulo {i+1} ({val}) excede el límite de 360°."}
            except Exception:
                pass

        actual_sum = sp.simplify(sum(parsed_angles))
        diff = sp.simplify(actual_sum - expected_sum)
        try:
            diff_num = float(sp.N(diff))
            sum_matches = abs(diff_num) < 1e-7
        except Exception:
            sum_matches = (diff == 0)

        error_msg = None
        if not sum_matches:
            error_msg = (
                f"La suma de ángulos interiores obtenida ({actual_sum}°) "
                f"no coincide con la suma teórica para {n} lados ({expected_sum}°)."
            )

        return {
            "valid": sum_matches,
            "n_sides": n,
            "expected_sum": expected_sum,
            "actual_sum": str(actual_sum),
            "angles": [str(a) for a in parsed_angles],
            "error": error_msg
        }

    def verify_pythagorean_property(self, a: Any, b: Any, c: Any) -> Dict[str, Any]:
        """
        Verifica si los catetos a, b y la hipotenusa c cumplen el Teorema de Pitágoras:
        a^2 + b^2 = c^2, con a > 0, b > 0, c > 0.
        """
        try:
            expr_a = self.parse_math(str(a))
            expr_b = self.parse_math(str(b))
            expr_c = self.parse_math(str(c))
        except Exception as e:
            return {"valid": False, "error": f"Error parseando lados para Pitágoras: {e}"}

        for name, val in [("a", expr_a), ("b", expr_b), ("c", expr_c)]:
            try:
                if float(sp.N(val)) <= 0:
                    return {"valid": False, "error": f"Longitud de lado {name}={val} debe ser estrictamente positiva."}
            except Exception:
                pass

        diff = sp.simplify(expr_a**2 + expr_b**2 - expr_c**2)
        try:
            diff_num = float(sp.N(diff))
            is_valid = abs(diff_num) < 1e-7
        except Exception:
            is_valid = (diff == 0)

        error_msg = None
        if not is_valid:
            error_msg = (
                f"No satisface el Teorema de Pitágoras: ({expr_a})^2 + ({expr_b})^2 "
                f"!= ({expr_c})^2 (diferencia: {diff})."
            )

        return {
            "valid": is_valid,
            "cathetus_a": str(expr_a),
            "cathetus_b": str(expr_b),
            "hypotenuse": str(expr_c),
            "identity_diff": str(diff),
            "error": error_msg
        }

    def verify_circle_invariants(
        self,
        radius: Any,
        diameter: Optional[Any] = None,
        perimeter: Optional[Any] = None,
        area: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Verifica la consistencia analítica de los invariantes del círculo:
        r > 0, d = 2r, P = 2*pi*r, A = pi*r^2.
        """
        try:
            r = self.parse_math(str(radius))
        except Exception as e:
            return {"valid": False, "error": f"Error parseando radio: {e}"}

        errors = []
        if diameter is not None:
            try:
                d = self.parse_math(str(diameter))
                diff = sp.simplify(d - 2 * r)
                if diff != 0:
                    errors.append(f"Diámetro {d} no coincide con 2*r ({2*r}).")
            except Exception as e:
                errors.append(f"Error comprobando diámetro: {e}")

        if perimeter is not None:
            try:
                p = self.parse_math(str(perimeter))
                diff = sp.simplify(p - 2 * sp.pi * r)
                if diff != 0:
                    errors.append(f"Perímetro {p} no coincide con 2*pi*r ({2*sp.pi*r}).")
            except Exception as e:
                errors.append(f"Error comprobando perímetro: {e}")

        if area is not None:
            try:
                a = self.parse_math(str(area))
                diff = sp.simplify(a - sp.pi * r**2)
                if diff != 0:
                    errors.append(f"Área {a} no coincide con pi*r^2 ({sp.pi*r**2}).")
            except Exception as e:
                errors.append(f"Error comprobando área: {e}")

        return {
            "valid": len(errors) == 0,
            "radius": str(r),
            "errors": errors,
            "error": "; ".join(errors) if errors else None
        }

    def verify_probability_distribution(
        self,
        probabilities: List[Any],
        check_partition_sum: bool = True
    ) -> Dict[str, Any]:
        """
        Verifica axiomas de Kolmogorov para distribuciones de probabilidad:
        1. 0 <= P(E) <= 1 para cada probabilidad declarada.
        2. Si check_partition_sum es True, la suma debe ser exactamente 1.
        """
        if not probabilities:
            return {"all_valid": False, "errors": ["Lista de probabilidades vacía."]}

        parsed_probs = []
        errors = []

        for i, p in enumerate(probabilities):
            try:
                p_expr = self.parse_math(str(p))
                parsed_probs.append(p_expr)
                val = float(sp.N(p_expr))
                if val < 0 or val > 1:
                    errors.append(f"Probabilidad P({i+1})={p} fuera de rango [0, 1].")
            except Exception as e:
                errors.append(f"Error evaluando probabilidad '{p}': {e}")

        if check_partition_sum and parsed_probs and len(errors) == 0:
            total_sum = sp.simplify(sum(parsed_probs))
            try:
                sum_num = float(sp.N(total_sum))
                if abs(sum_num - 1.0) > 1e-7:
                    errors.append(f"La suma de probabilidades del espacio muestral es {total_sum} != 1.0.")
            except Exception:
                if total_sum != 1:
                    errors.append(f"La suma simbólica de probabilidades es {total_sum} != 1.")

        return {
            "all_valid": len(errors) == 0,
            "probabilities": [str(p) for p in parsed_probs],
            "errors": errors,
            "error": "; ".join(errors) if errors else None
        }

    def verify_combinatorics_values(
        self,
        n: Any,
        k: Any,
        claimed_combinations: Optional[Any] = None,
        claimed_permutations: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Verifica condiciones de combinatoria y valores calculados:
        n >= k >= 0 enteros, C(n, k) = n! / (k!(n-k)!), P(n, k) = n! / (n-k)!.
        """
        errors = []
        try:
            n_int = int(n)
            k_int = int(k)
        except Exception:
            return {"all_valid": False, "errors": [f"n ({n}) y k ({k}) deben ser enteros."]}

        if n_int < 0 or k_int < 0:
            errors.append(f"n ({n_int}) y k ({k_int}) deben ser no negativos (>= 0).")
        if k_int > n_int:
            errors.append(f"k ({k_int}) no puede ser mayor que n ({n_int}).")

        if errors:
            return {"all_valid": False, "errors": errors, "error": "; ".join(errors)}

        true_comb = sp.binomial(n_int, k_int)
        true_perm = sp.factorial(n_int) // sp.factorial(n_int - k_int)

        if claimed_combinations is not None:
            try:
                c_expr = self.parse_math(str(claimed_combinations))
                if sp.simplify(c_expr - true_comb) != 0:
                    errors.append(f"Combinaciones C({n_int}, {k_int}) = {claimed_combinations} es incorrecto. Valor exacto: {true_comb}.")
            except Exception as e:
                errors.append(f"Error validando combinaciones: {e}")

        if claimed_permutations is not None:
            try:
                p_expr = self.parse_math(str(claimed_permutations))
                if sp.simplify(p_expr - true_perm) != 0:
                    errors.append(f"Permutaciones P({n_int}, {k_int}) = {claimed_permutations} es incorrecto. Valor exacto: {true_perm}.")
            except Exception as e:
                errors.append(f"Error validando permutaciones: {e}")

        return {
            "all_valid": len(errors) == 0,
            "n": n_int,
            "k": k_int,
            "true_combinations": int(true_comb),
            "true_permutations": int(true_perm),
            "errors": errors,
            "error": "; ".join(errors) if errors else None
        }

    def verify_geometric_constraints(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrutador y validador de restricciones geométricas generales.
        Soporta:
        - triangle / triangle_inequality: { sides: [a, b, c] }
        - polygon_angles / angles: { angles: [...], n_sides: int }
        - pythagorean / right_triangle: { a, b, c }
        - circle / circle_invariants: { radius, diameter, perimeter, area }
        """
        stype = str(spec.get("type", "")).lower()
        if stype in ("triangle", "triangle_inequality"):
            sides = spec.get("sides", [])
            if len(sides) != 3:
                return {"valid": False, "error": f"Se requieren exactamente 3 lados para triángulo (recibidos {len(sides)})."}
            return self.verify_triangle_inequality(sides[0], sides[1], sides[2])
        elif stype in ("polygon_angles", "angles"):
            angles = spec.get("angles", [])
            return self.verify_polygon_angles(angles, n_sides=spec.get("n_sides"))
        elif stype in ("pythagorean", "right_triangle"):
            return self.verify_pythagorean_property(
                a=spec.get("a", spec.get("cathetus_a")),
                b=spec.get("b", spec.get("cathetus_b")),
                c=spec.get("c", spec.get("hypotenuse"))
            )
        elif stype in ("circle", "circle_invariants"):
            return self.verify_circle_invariants(
                radius=spec.get("radius", spec.get("r")),
                diameter=spec.get("diameter", spec.get("d")),
                perimeter=spec.get("perimeter", spec.get("p")),
                area=spec.get("area", spec.get("a"))
            )
        else:
            return {"valid": False, "error": f"Tipo de verificación geométrica no reconocido: '{stype}'"}

    def verify_item(self, item_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Audita un ítem de evaluación con soporte para múltiples formatos:
        - Si es MULTIPLE_CHOICE, ejecuta verificación de distractores y matemáticas.
        - Si es OPEN_DEVELOPMENT u otro formato pero incluye 'math_verification', ejecuta la verificación correspondiente.
        """
        fmt = item_dict.get("format", "")
        if fmt == "MULTIPLE_CHOICE":
            return self.verify_multiple_choice_item(item_dict)

        verdict = {
            "status": "PASS",
            "format": fmt,
            "observations": []
        }

        if "math_verification" in item_dict:
            mv = item_dict["math_verification"]
            mv_type = str(mv.get("type", "")).lower()
            if mv_type == "equation_roots":
                eq_check = self.verify_equation_solutions(
                    equation_str=mv["equation"],
                    proposed_solutions=[mv["expected_solution"]],
                    var_symbol=mv.get("variable", "x")
                )
                verdict["equation_check"] = eq_check
                if not eq_check["all_valid"]:
                    verdict["status"] = "FAIL"
                    verdict["error_detail"] = "La clave declarada correcta NO satisface formalmente la ecuación."
            elif mv_type in ("triangle", "triangle_inequality", "polygon_angles", "angles", "pythagorean", "right_triangle", "circle", "circle_invariants", "geometric"):
                geom_check = self.verify_geometric_constraints(mv)
                verdict["geometric_check"] = geom_check
                if not geom_check.get("valid", False):
                    verdict["status"] = "FAIL"
                    verdict["error_detail"] = geom_check.get("error", "Fallo de restricción geométrica formal.")
            elif mv_type in ("probability", "probability_distribution"):
                prob_check = self.verify_probability_distribution(
                    probabilities=mv.get("probabilities", []),
                    check_partition_sum=mv.get("check_partition_sum", True)
                )
                verdict["probability_check"] = prob_check
                if not prob_check.get("all_valid", False):
                    verdict["status"] = "FAIL"
                    verdict["error_detail"] = prob_check.get("error", "Fallo en axiomas de probabilidad.")
            elif mv_type in ("combinatorics", "combinatorial", "permutation_combination"):
                comb_check = self.verify_combinatorics_values(
                    n=mv.get("n"),
                    k=mv.get("k"),
                    claimed_combinations=mv.get("combinations"),
                    claimed_permutations=mv.get("permutations")
                )
                verdict["combinatorics_check"] = comb_check
                if not comb_check.get("all_valid", False):
                    verdict["status"] = "FAIL"
                    verdict["error_detail"] = comb_check.get("error", "Fallo en cálculo combinatorio.")

        return verdict
