# my_agent.py
import os, json, subprocess
import pandas as pd, requests
from pathlib import Path
from langchain.agents import initialize_agent, Tool
from langchain.llms import OpenAI

# ── Funciones “tools” para el Agent ─────────────────────────

def fetch_data(source: dict) -> str:
    """Descarga datos de URL, S3 o DB; devuelve ruta local CSV."""
    if source is None:
        raise ValueError("No source provided")
    if source["type"] == "url":
        r = requests.get(source["url"])
        path = Path("/tmp")/Path(source["url"]).name
        path.write_bytes(r.content)
        return str(path)
    # (añade s3/db si las usarás)
    raise ValueError(f"Source type {source['type']} no soportado")

def prepare_data(path: str, transforms: list) -> str:
    """Carga CSV, aplica transforms y guarda CSV limpio."""
    df = pd.read_csv(path)
    for t in transforms:
        if t["op"] == "dropna":
            df = df.dropna()
        elif t["op"] == "rename":
            df = df.rename(columns=t["mappings"])
    out = Path("/tmp")/f"cleaned_{Path(path).name}"
    df.to_csv(out, index=False)
    return str(out)

def generate_dashboard(params: dict) -> str:
    """Rellena plantilla Jinja y guarda un .py Streamlit."""
    from jinja2 import Template
    template = Path("templates/dashboard.py.j2").read_text()
    script = Template(template).render(**params)
    out = Path("/tmp")/f"dashboard_{params['project_name']}.py"
    out.write_text(script)
    return str(out)

def deploy_dashboard(script_path: str) -> str:
    """Commit a GitHub y devuelve URL pública."""
    branch = f"deploy/{Path(script_path).stem}"
    subprocess.run(["git", "checkout", "-b", branch], check=True)
    dest = Path("dashboards")/Path(script_path).name
    dest.write_text(Path(script_path).read_text())
    subprocess.run(["git", "add", str(dest)], check=True)
    subprocess.run(["git", "commit", "-m", f"Deploy {branch}"], check=True)
    subprocess.run(["git", "push", "--set-upstream", "origin", branch], check=True)
    return f"https://{branch.replace('/','-')}.streamlit.app"

def send_alert(message: str) -> None:
    """Envía alertas (ej. webhook Slack)."""
    webhook = os.environ.get("SLACK_WEBHOOK")
    if webhook:
        requests.post(webhook, json={"text": message})

# ── Inicializa el Agent ─────────────────────────────────────

tools = [
    Tool(name="fetch_data", func=fetch_data, description="Descarga CSV."),
    Tool(name="prepare_data", func=prepare_data, description="Limpia datos."),
    Tool(name="generate_dashboard", func=generate_dashboard, description="Genera script .py."),
    Tool(name="deploy_dashboard", func=deploy_dashboard, description="Despliega el tablero."),
    Tool(name="send_alert", func=send_alert, description="Envía alertas si algo falla.")
]

llm = OpenAI(temperature=0)
agent = initialize_agent(tools, llm, agent="openai-functions", verbose=False)
