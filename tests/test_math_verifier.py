"""
Tests unitarios para el motor de verificación simbólica (SymPy Math Verifier).
"""

import sympy as sp
from math_teaching_agents.validators.math_verifier import SymbolicMathVerifier, latex_to_sympy_str


def test_verify_equation_solutions_success():
    verifier = SymbolicMathVerifier()
    # x^2 - 5x + 6 = 0 -> soluciones reales: 2 y 3
    result = verifier.verify_equation_solutions("x^2 - 5*x + 6 = 0", ["2", "3"])
    assert result["all_valid"] is True
    assert set(result["true_solutions"]) == {"2", "3"}


def test_verify_equation_solutions_failure():
    verifier = SymbolicMathVerifier()
    # x^2 - 4 = 0 -> soluciones: 2 y -2. Si se propone 3, debe fallar.
    result = verifier.verify_equation_solutions("x^2 - 4 = 0", ["3"])
    assert result["all_valid"] is False


def test_multiple_choice_valid_item():
    verifier = SymbolicMathVerifier()
    item = {
        "item_id": 1,
        "format": "MULTIPLE_CHOICE",
        "math_verification": {
            "type": "equation_roots",
            "equation": "2*x - 8 = 0",
            "expected_solution": "4"
        },
        "options": [
            {"label": "A", "text": "2", "is_correct": False},
            {"label": "B", "text": "4", "is_correct": True},
            {"label": "C", "text": "-4", "is_correct": False},
            {"label": "D", "text": "8", "is_correct": False}
        ]
    }
    verdict = verifier.verify_multiple_choice_item(item)
    assert verdict["status"] == "PASS"
    assert verdict["has_single_correct_answer"] is True
    assert verdict["distractors_unique"] is True


def test_multiple_choice_detects_duplicated_distractors():
    verifier = SymbolicMathVerifier()
    item = {
        "item_id": 2,
        "format": "MULTIPLE_CHOICE",
        "options": [
            {"label": "A", "text": "1/2", "is_correct": True},
            {"label": "B", "text": "2/4", "is_correct": False},  # 2/4 es matemáticamente idéntico a 1/2
            {"label": "C", "text": "3/4", "is_correct": False},
            {"label": "D", "text": "1", "is_correct": False}
        ]
    }
    verdict = verifier.verify_multiple_choice_item(item)
    assert verdict["status"] == "FAIL"
    assert verdict["distractors_unique"] is False
    assert len(verdict["duplicates"]) > 0


def test_latex_to_sympy_conversion():
    # Fracciones complejas anidadas y raíces
    latex_frac = r"\frac{3}{4} + \frac{x+1}{2}"
    sym_str = latex_to_sympy_str(latex_frac)
    assert "(3)/(4)" in sym_str

    latex_sqrt = r"\sqrt{16} + \sqrt[3]{8}"
    sym_sqrt_str = latex_to_sympy_str(latex_sqrt)
    assert "sqrt(16)" in sym_sqrt_str
    assert "1/(3)" in sym_sqrt_str


def test_canonicalize_fractions_and_decimals():
    verifier = SymbolicMathVerifier()
    # \frac{1}{2} y 0.5 deben ser canónicamente equivalentes
    can_frac = verifier.canonicalize_option_value(r"$\frac{1}{2}$")
    can_dec = verifier.canonicalize_option_value("0.5")
    assert can_frac == can_dec == "1/2"


def test_canonicalize_solution_sets_detects_permutation():
    verifier = SymbolicMathVerifier()
    # \{3, 2\} debe ser idéntico a \{2, 3\}
    set1 = verifier.canonicalize_option_value(r"$\{3, 2\}$")
    set2 = verifier.canonicalize_option_value(r"$\{2, 3\}$")
    assert set1 == set2 == "SET:{2,3}"

    item = {
        "item_id": 3,
        "format": "MULTIPLE_CHOICE",
        "options": [
            {"key": "A", "text": r"$\{2, 3\}$", "is_correct": True},
            {"key": "B", "text": r"$\{3, 2\}$", "is_correct": False},  # Duplicado permutado
            {"key": "C", "text": r"$\{-2, -3\}$", "is_correct": False},
            {"key": "D", "text": r"$\{1, 6\}$", "is_correct": False}
        ]
    }
    verdict = verifier.verify_multiple_choice_item(item)
    assert verdict["status"] == "FAIL"
    assert "matemáticamente equivalente" in verdict["duplicates"][0]


def test_triangle_inequality():
    verifier = SymbolicMathVerifier()
    # Triángulo válido 3, 4, 5
    res_ok = verifier.verify_triangle_inequality(3, 4, 5)
    assert res_ok["valid"] is True
    assert res_ok["error"] is None

    # Triángulo imposible 3, 4, 8 (3 + 4 = 7 < 8)
    res_fail = verifier.verify_triangle_inequality(3, 4, 8)
    assert res_fail["valid"] is False
    assert "desigualdad triangular" in res_fail["error"]

    # Con valores simbólicos y LaTeX: 1, 1, \sqrt{2}
    res_sym = verifier.verify_triangle_inequality(1, 1, r"\sqrt{2}")
    assert res_sym["valid"] is True


def test_polygon_angles():
    verifier = SymbolicMathVerifier()
    # Triángulo con ángulos 60°, 70°, 50° -> suma 180°
    res_tri = verifier.verify_polygon_angles(["60", "70", "50"])
    assert res_tri["valid"] is True
    assert res_tri["expected_sum"] == 180

    # Triángulo con ángulos incompatibles 60°, 70°, 80° -> suma 210°
    res_fail = verifier.verify_polygon_angles(["60", "70", "80"])
    assert res_fail["valid"] is False
    assert "no coincide" in res_fail["error"]

    # Cuadrilátero 4 ángulos de 90°
    res_quad = verifier.verify_polygon_angles(["90", "90", "90", "90"])
    assert res_quad["valid"] is True
    assert res_quad["expected_sum"] == 360


def test_pythagorean_property():
    verifier = SymbolicMathVerifier()
    # Terna pitagórica 3, 4, 5
    res_ok = verifier.verify_pythagorean_property(3, 4, 5)
    assert res_ok["valid"] is True

    # 5, 12, 13
    res_ok2 = verifier.verify_pythagorean_property(5, 12, 13)
    assert res_ok2["valid"] is True

    # Terna falsa 3, 4, 6
    res_fail = verifier.verify_pythagorean_property(3, 4, 6)
    assert res_fail["valid"] is False
    assert "No satisface el Teorema de Pitágoras" in res_fail["error"]


def test_circle_invariants():
    verifier = SymbolicMathVerifier()
    # Radio 5, Diámetro 10, Área 25*pi
    res_ok = verifier.verify_circle_invariants(radius=5, diameter=10, area=r"25*\pi")
    assert res_ok["valid"] is True

    # Radio 5 pero área errónea 30*pi
    res_fail = verifier.verify_circle_invariants(radius=5, area=r"30*\pi")
    assert res_fail["valid"] is False
    assert len(res_fail["errors"]) > 0


def test_probability_distribution():
    verifier = SymbolicMathVerifier()
    # Partición válida: 0.2, 0.5, 0.3 -> suma 1.0
    res_ok = verifier.verify_probability_distribution(["0.2", "0.5", "0.3"])
    assert res_ok["all_valid"] is True

    # Suma excede 1.0: 0.4, 0.8 -> suma 1.2
    res_fail = verifier.verify_probability_distribution(["0.4", "0.8"])
    assert res_fail["all_valid"] is False

    # Probabilidad negativa
    res_neg = verifier.verify_probability_distribution(["-0.2", "1.2"])
    assert res_neg["all_valid"] is False


def test_combinatorics_values():
    verifier = SymbolicMathVerifier()
    # C(5, 2) = 10, P(5, 2) = 20
    res_ok = verifier.verify_combinatorics_values(5, 2, claimed_combinations=10, claimed_permutations=20)
    assert res_ok["all_valid"] is True

    # Valor falso
    res_fail = verifier.verify_combinatorics_values(5, 2, claimed_combinations=15)
    assert res_fail["all_valid"] is False
    assert "incorrecto" in res_fail["error"]


def test_item_with_geometric_verification():
    verifier = SymbolicMathVerifier()
    # Ítem con verificación de triángulo
    item_valid = {
        "item_id": 1,
        "format": "MULTIPLE_CHOICE",
        "stem": "Determine el perímetro del triángulo de lados 3, 4 y 5 cm.",
        "math_verification": {
            "type": "triangle",
            "sides": [3, 4, 5]
        },
        "options": [
            {"label": "A", "text": "12", "is_correct": True},
            {"label": "B", "text": "10", "is_correct": False},
            {"label": "C", "text": "7", "is_correct": False},
            {"label": "D", "text": "15", "is_correct": False}
        ]
    }
    verdict = verifier.verify_item(item_valid)
    assert verdict["status"] == "PASS"
    assert verdict["geometric_check"]["valid"] is True

    # Ítem con geometría imposible
    item_invalid = dict(item_valid)
    item_invalid["math_verification"] = {"type": "triangle", "sides": [3, 4, 8]}
    verdict_fail = verifier.verify_item(item_invalid)
    assert verdict_fail["status"] == "FAIL"
    assert "desigualdad triangular" in verdict_fail["error_detail"]
