"""
Tests unitarios para el dashboard web interactivo (UI HTTP Server).
"""

import json
import io
from pathlib import Path
from unittest.mock import MagicMock
from math_teaching_agents.ui import DashboardRequestHandler, HTML_TEMPLATE
from math_teaching_agents.llm_runtime import DidacticPipeline, MockLLMProvider


def test_ui_html_template_contains_didactic_unit():
    assert "Unidad Didáctica y Secuencia de Clase" in HTML_TEMPLATE
    assert "artifact_type" in HTML_TEMPLATE
    assert "didactic_unit" in HTML_TEMPLATE


def test_ui_api_info_endpoint():
    handler = DashboardRequestHandler.__new__(DashboardRequestHandler)
    handler.path = "/api/info"
    handler.wfile = io.BytesIO()

    # Mock send_response and send_header
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()

    handler.do_GET()

    handler.send_response.assert_called_with(200)
    data = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert "version" in data
    assert "curriculums" in data
    assert "frameworks" in data


def test_ui_api_run_didactic_unit():
    root = Path(__file__).resolve().parents[1]
    DashboardRequestHandler.root_dir = root
    DashboardRequestHandler.pipeline = DidacticPipeline(root_dir=root, provider=MockLLMProvider())

    payload = {
        "artifact_type": "didactic_unit",
        "topic": "Funciones Cuadráticas y Modelización",
        "curriculum": "chile-mineduc",
        "framework": "brousseau-tds",
        "format": "typst",
        "multi_stage": False,
        "max_retries": 1
    }

    body = json.dumps(payload).encode("utf-8")
    handler = DashboardRequestHandler.__new__(DashboardRequestHandler)
    handler.path = "/api/run"
    handler.headers = {"Content-Length": str(len(body))}
    handler.rfile = io.BytesIO(body)
    handler.wfile = io.BytesIO()

    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()

    handler.do_POST()

    handler.send_response.assert_called_with(200)
    res = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert res["status"] == "COMPLETED"
    assert res["artifact_type"] == "didactic_unit"
    assert res["gate_1"]["status"] == "APPROVED"
    assert "PLANIFICACIÓN DE UNIDAD DIDÁCTICA" in res["rendered_code"]
    assert "Fase 1" in res["rendered_code"]
