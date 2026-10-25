"""
Servidor y Dashboard Web Interactivo Liviano para Math Teaching Agents.
Permite a docentes y diseñadores instruccionales configurar, generar y auditar
evaluaciones formativas desde el navegador sin necesidad de usar la consola.
"""

import http.server
import json
import os
from pathlib import Path
import urllib.parse
import webbrowser
from typing import Optional

from math_teaching_agents.llm_runtime import DidacticPipeline, get_provider


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Math Teaching Agents | Dashboard Didáctico</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css">
  <style>
    :root {
      --primary: #1976d2;
      --primary-hover: #1565c0;
      --card-bg: #ffffff;
    }
    body {
      background-color: #f4f6f8;
      font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
      padding-bottom: 3rem;
    }
    header {
      background: linear-gradient(135deg, #1565c0, #0d47a1);
      color: white;
      padding: 1.8rem 1rem;
      margin-bottom: 2rem;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    header h1 { margin-bottom: 0.2rem; color: #fff; font-size: 1.8rem; }
    header p { margin: 0; opacity: 0.85; font-size: 0.95rem; }
    .badge {
      display: inline-block;
      padding: 0.25rem 0.6rem;
      border-radius: 4px;
      font-size: 0.8rem;
      font-weight: 600;
      margin-right: 0.5rem;
    }
    .badge-pass { background-color: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; }
    .badge-fail { background-color: #ffebee; color: #c62828; border: 1px solid #ef9a9a; }
    .badge-info { background-color: #e3f2fd; color: #1565c0; border: 1px solid #90caf9; }
    pre {
      background-color: #272822;
      color: #f8f8f2;
      padding: 1rem;
      border-radius: 6px;
      max-height: 450px;
      overflow-y: auto;
      font-size: 0.85rem;
    }
    .tabs {
      display: flex;
      border-bottom: 2px solid #e0e0e0;
      margin-bottom: 1rem;
    }
    .tab-btn {
      background: none;
      border: none;
      padding: 0.6rem 1.2rem;
      cursor: pointer;
      font-weight: 600;
      color: #666;
      border-bottom: 3px solid transparent;
      margin-bottom: -2px;
    }
    .tab-btn.active {
      color: #1976d2;
      border-bottom-color: #1976d2;
    }
    .tab-content { display: none; }
    .tab-content.active { display: block; }
    .grid-2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
    }
    @media (max-width: 768px) {
      .grid-2 { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <div class="container">
      <h1>📐 Math Teaching Agents</h1>
      <p>Sistema Multiagente de Ingeniería Didáctica, Verificación Simbólica CAS y Evaluación Auténtica</p>
    </div>
  </header>

  <main class="container">
    <div class="grid-2">
      <!-- Panel de Control y Configuración -->
      <article>
        <h3>Configuración de Ingeniería Didáctica</h3>
        <form id="evalForm">
          <label for="artifact_type">Tipo de Artefacto Didáctico:
            <select id="artifact_type" name="artifact_type">
              <option value="assessment" selected>📝 Instrumento de Evaluación (Diagnóstica / Formativa / Sumativa)</option>
              <option value="didactic_unit">📚 Unidad Didáctica y Secuencia de Clase (Fases de Brousseau & DUA)</option>
            </select>
          </label>

          <label for="topic">Tema u Objetivo Didáctico:
            <input type="text" id="topic" name="topic" value="Ecuaciones Cuadráticas y Parábolas" required>
          </label>

          <label for="curriculum">Adaptador Curricular:
            <select id="curriculum" name="curriculum">
              <option value="chile-mineduc" selected>Chile - MINEDUC (Bases Curriculares & PAES)</option>
              <option value="mexico-nem">México - SEP (Nueva Escuela Mexicana)</option>
              <option value="colombia-men">Colombia - MEN & ICFES (Saber 11)</option>
              <option value="spain-lomloe">España - LOMLOE (Bachillerato)</option>
              <option value="ib-dp-math">Bachillerato Internacional (IB DP Math)</option>
            </select>
          </label>

          <label for="framework">Marco Teórico Didáctico:
            <select id="framework" name="framework">
              <option value="duval-trrs" selected>Duval - Registros de Representación Semiótica (TRRS)</option>
              <option value="godino-eos">Godino - Enfoque Ontosemiótico (EOS)</option>
              <option value="brousseau-tds">Brousseau - Teoría de Situaciones Didácticas (TSD)</option>
              <option value="chevallard-atd">Chevallard - Antropología Didáctica (ATD)</option>
            </select>
          </label>

          <label for="format">Formato de Salida y Maquetación:
            <select id="format" name="format">
              <option value="typst" selected>Typst (.typ) - Moderno, ultrarrápido (&lt;50ms)</option>
              <option value="latex">LaTeX (.tex) - Estándar académico tradicional</option>
              <option value="moodle">Moodle XML (.xml) - Interoperable con Canvas/Moodle/Blackboard</option>
            </select>
          </label>

          <fieldset>
            <label for="multi_stage">
              <input type="checkbox" id="multi_stage" name="multi_stage" role="switch">
              Orquestación Multi-Etapa (Análisis MTSK + Redacción GPK)
            </label>
            <label for="self_healing">
              <input type="checkbox" id="self_healing" name="self_healing" role="switch" checked>
              Bucle de Autocorrección (Self-Healing Loop con CAS)
            </label>
          </fieldset>

          <button type="submit" id="submitBtn">⚡ Ejecutar Pipeline y Gatekeeper</button>
        </form>
      </article>

      <!-- Panel de Diagnóstico y Resultados -->
      <article>
        <h3>Estado de Auditoría y Verificación</h3>
        <div id="statusBox" style="margin-bottom: 1rem;">
          <p><em>Configure los parámetros y presione "Ejecutar Pipeline" para auditar en tiempo real.</em></p>
        </div>

        <div class="tabs">
          <button class="tab-btn active" onclick="switchTab('tab-audit')">Auditoría CAS</button>
          <button class="tab-btn" onclick="switchTab('tab-draft')">Borrador Semántico</button>
          <button class="tab-btn" onclick="switchTab('tab-code')">Artefacto Renderizado</button>
        </div>

        <div id="tab-audit" class="tab-content active">
          <pre id="auditDetails">// Los dictámenes de Gate 1 y Gate 2 aparecerán aquí.</pre>
        </div>

        <div id="tab-draft" class="tab-content">
          <pre id="draftContent">// El borrador YAML estructurado aparecerá aquí.</pre>
        </div>

        <div id="tab-code" class="tab-content">
          <pre id="renderedCode">// El código tipográfico (Typst, LaTeX o Moodle XML) aparecerá aquí.</pre>
        </div>
      </article>
    </div>
  </main>

  <script>
    function switchTab(tabId) {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      event.target.classList.add('active');
      document.getElementById(tabId).classList.add('active');
    }

    document.getElementById('evalForm').addEventListener('submit', async function(e) {
      e.preventDefault();
      const btn = document.getElementById('submitBtn');
      const statusBox = document.getElementById('statusBox');
      btn.setAttribute('aria-busy', 'true');
      btn.innerText = 'Ejecutando Pipeline...';

      const payload = {
        artifact_type: document.getElementById('artifact_type').value,
        topic: document.getElementById('topic').value,
        curriculum: document.getElementById('curriculum').value,
        framework: document.getElementById('framework').value,
        format: document.getElementById('format').value,
        multi_stage: document.getElementById('multi_stage').checked,
        max_retries: document.getElementById('self_healing').checked ? 3 : 1
      };

      try {
        const resp = await fetch('/api/run', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await resp.json();

        // Renderizar estado y badges
        const isCompleted = data.status === 'COMPLETED';
        const gate1Status = data.gate_1 ? data.gate_1.status : 'N/A';
        const attempts = data.attempts_needed || 1;

        let html = `<div>`;
        html += `<span class="badge ${isCompleted ? 'badge-pass' : 'badge-fail'}">ESTADO: ${data.status}</span>`;
        html += `<span class="badge ${gate1Status === 'APPROVED' ? 'badge-pass' : 'badge-fail'}">GATE 1 CAS: ${gate1Status}</span>`;
        if (data.gate_2) {
          html += `<span class="badge badge-pass">GATE 2 RENDER: ${data.gate_2.status}</span>`;
        }
        html += `<span class="badge badge-info">Intentos: ${attempts}</span>`;
        html += `</div>`;

        if (data.rendered_path) {
          html += `<p style="margin-top: 0.5rem;"><small>Artefacto listo: <code>${data.rendered_path}</code></small></p>`;
        }
        statusBox.innerHTML = html;

        // Rellenar pestañas
        document.getElementById('auditDetails').innerText = JSON.stringify({
          gate_1: data.gate_1,
          gate_2: data.gate_2
        }, null, 2);

        document.getElementById('draftContent').innerText = data.draft_yaml || '(No generado)';
        document.getElementById('renderedCode').innerText = data.rendered_code || '(No generado)';

      } catch (err) {
        statusBox.innerHTML = `<span class="badge badge-fail">ERROR: ${err.message}</span>`;
      } finally {
        btn.removeAttribute('aria-busy');
        btn.innerText = '⚡ Ejecutar Pipeline y Gatekeeper';
      }
    });
  </script>
</body>
</html>
"""


class DashboardRequestHandler(http.server.BaseHTTPRequestHandler):
    """Manejador de solicitudes HTTP para el servidor de UI interactivo."""

    pipeline: Optional[DidacticPipeline] = None
    root_dir: Optional[Path] = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif path == "/api/info":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            info_data = {
                "version": "0.5.0",
                "curriculums": ["chile-mineduc", "mexico-nem", "colombia-men", "spain-lomloe", "ib-dp-math"],
                "frameworks": ["duval-trrs", "godino-eos", "brousseau-tds", "chevallard-atd"],
                "formats": ["typst", "latex", "moodle"]
            }
            self.wfile.write(json.dumps(info_data).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/run":
            length = int(self.headers.get("Content-Length", 0))
            raw_bytes = self.rfile.read(length)
            try:
                body = raw_bytes.decode("utf-8")
            except UnicodeDecodeError:
                body = raw_bytes.decode("latin-1")
            data = json.loads(body)

            topic = data.get("topic", "Ecuaciones Cuadráticas")
            curriculum = data.get("curriculum", "chile-mineduc")
            framework = data.get("framework", "duval-trrs")
            fmt = data.get("format", "typst")
            multi_stage = bool(data.get("multi_stage", False))
            max_retries = int(data.get("max_retries", 3))
            artifact_type = data.get("artifact_type", "assessment")

            pipeline = self.pipeline or DidacticPipeline(root_dir=self.root_dir)
            result = pipeline.run(
                topic=topic,
                curriculum_id=curriculum,
                framework_id=framework,
                output_format=fmt,
                max_retries=max_retries,
                multi_stage=multi_stage,
                artifact_type=artifact_type
            )

            # Leer contenido de archivos generados si existen
            draft_yaml = ""
            if "draft_path" in result and Path(result["draft_path"]).exists():
                with open(result["draft_path"], "r", encoding="utf-8") as f:
                    draft_yaml = f.read()

            rendered_code = ""
            if "rendered_path" in result and Path(result["rendered_path"]).exists():
                with open(result["rendered_path"], "r", encoding="utf-8") as f:
                    rendered_code = f.read()

            result["draft_yaml"] = draft_yaml
            result["rendered_code"] = rendered_code

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silenciar logs ruidosos en consola
        pass


def start_server(host: str = "127.0.0.1", port: int = 8501, open_browser: bool = True, root_dir: Optional[Path] = None):
    """Inicia el servidor web interactivo local."""
    DashboardRequestHandler.root_dir = root_dir
    DashboardRequestHandler.pipeline = DidacticPipeline(root_dir=root_dir)

    server = http.server.ThreadingHTTPServer((host, port), DashboardRequestHandler)
    url = f"http://{host}:{port}"
    print("=" * 65)
    print("  MATH TEACHING AGENTS: DASHBOARD DIDÁCTICO ACTIVO")
    print("=" * 65)
    print(f"  Servidor local escuchando en: {url}")
    print("  Presione Ctrl+C en esta terminal para detener el servicio.")
    print("=" * 65)

    if open_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
        server.server_close()
