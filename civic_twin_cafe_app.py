import os
import json
import smtplib
from email.message import EmailMessage
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from openai import OpenAI

# ─── Configuración de página ─────────────────────────────────────────
st.set_page_config(
    page_title="Cafetería en Quilmes | Civic Twin™",
    layout="wide",
    menu_items={
        "Get help": None,
        "Report a bug": None,
        "About": None
    }
)

# ─── Cliente OpenAI ──────────────────────────────────────────────────
def get_openai_client():
    """
    Prioridad de búsqueda de la API key:
    1) st.secrets["openai"]["api_key"]
    2) st.secrets["OPENAI_API_KEY"]
    3) os.environ["OPENAI_API_KEY"]
    """
    api_key = None

    try:
        # 1) Formato por bloques: [openai].api_key
        if "openai" in st.secrets and isinstance(st.secrets["openai"], dict):
            if "api_key" in st.secrets["openai"]:
                api_key = st.secrets["openai"]["api_key"]

        # 2) Clave plana: OPENAI_API_KEY
        if not api_key and "OPENAI_API_KEY" in st.secrets:
            api_key = st.secrets["OPENAI_API_KEY"]
    except Exception as e:
        st.sidebar.error(f"Error leyendo secrets de Streamlit: {e}")
        return None

    # 3) Fallback: variable de entorno
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        # Debug seguro: sólo mostramos los nombres de las claves
        try:
            keys = list(st.secrets.keys())
        except Exception:
            keys = []
        st.sidebar.warning(f"No se encontró ninguna API key de OpenAI. Claves en secrets: {keys}")
        return None

    try:
        return OpenAI(api_key=api_key)
    except Exception as e:
        st.sidebar.error(f"No se pudo crear el cliente de OpenAI: {e}")
        return None


client = get_openai_client()

# ─── Ocultar menú y footer de Streamlit ──────────────────────────────
st.markdown(
    """
    <style>
      #MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
      header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)

# ─── Función para enviar email de contacto ───────────────────────────
def send_contact_email(nombre: str, email: str, mensaje: str):
    """Envía un email con los datos del formulario."""
    msg = EmailMessage()
    msg["Subject"] = f"[Civic Twin™] Nuevo mensaje de {nombre}"
    msg["From"]    = st.secrets["smtp"]["username"]
    msg["To"]      = st.secrets["smtp"]["to_email"]
    msg.set_content(f"De: {nombre} <{email}>\n\nMensaje:\n{mensaje}")

    with smtplib.SMTP_SSL(
        st.secrets["smtp"]["server"],
        st.secrets["smtp"]["port"]
    ) as smtp:
        smtp.login(
            st.secrets["smtp"]["username"],
            st.secrets["smtp"]["password"]
        )
        smtp.send_message(msg)

# ─── Helpers de navegación ───────────────────────────────────────────
def go_home():
    st.session_state.view = "home"

def go_mode():
    st.session_state.view = "mode"  # menú de tipo de proyecto

def go_private():
    st.session_state.view = "dashboard_private"

def go_public():
    st.session_state.view = "dashboard_public"

def go_contact():
    st.session_state.view = "contact"

# Inicializar la vista por defecto
if "view" not in st.session_state:
    st.session_state.view = "home"

# ─── Renderizador de informes interactivos ───────────────────────────
def render_interactive_report(layout: dict, series_data: dict):
    """
    layout: dict con estructura:
    {
      "title": str,
      "narrative": str,
      "sections": [
        {
          "type": "kpi_row",
          "metrics": [{"label":..., "value":..., "suffix":..., "description":...}]
        },
        {
          "type": "line_chart",
          "title": "...",
          "series": [{"id": "flujo_24m", "label": "Flujo acumulado"}]
        },
        {
          "type": "markdown",
          "title": "...",
          "body": "markdown..."
        }
      ]
    }
    series_data: { series_id: {"x": [...], "y": [...], "default_label": str} }
    """
    title = layout.get("title")
    narrative = layout.get("narrative")
    sections = layout.get("sections", [])

    if title:
        st.markdown(f"#### {title}")
    if narrative:
        st.markdown(narrative)

    for sec in sections:
        st.write("---")
        sec_type = sec.get("type")

        if sec_type == "kpi_row":
            metrics = sec.get("metrics", [])
            cols = st.columns(len(metrics)) if metrics else []
            for col, m in zip(cols, metrics):
                with col:
                    label = m.get("label", "Métrica")
                    value = m.get("value", "")
                    suffix = m.get("suffix", "")
                    desc = m.get("description", None)
                    display_value = f"{value}{suffix}" if suffix else f"{value}"
                    col.metric(label, display_value)
                    if desc:
                        st.caption(desc)

        elif sec_type == "line_chart":
            chart_title = sec.get("title", "")
            series_spec = sec.get("series", [])
            if not series_spec:
                continue

            first = series_spec[0]
            sid = first.get("id")
            if sid not in series_data:
                continue
            x = series_data[sid]["x"]
            data = {}
            for s in series_spec:
                sid2 = s.get("id")
                if sid2 in series_data:
                    label = s.get("label") or series_data[sid2].get("default_label", sid2)
                    data[label] = series_data[sid2]["y"]

            df_chart = pd.DataFrame(data, index=x)
            st.markdown(f"**{chart_title}**")
            st.line_chart(df_chart)

        elif sec_type == "markdown":
            md_title = sec.get("title")
            body = sec.get("body", "")
            if md_title:
                st.markdown(f"**{md_title}**")
            if body:
                st.markdown(body)

# ─── CSS global (hero, features) ─────────────────────────────────────
GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');

/* Variables */
:root {
  --primary: #1F4E79;
  --white: #FFFFFF;
  --hero-overlay: rgba(31, 78, 121, 0.6);
  --gap: 24px;
}

/* Body con textura ligera */
body {
  background: #f7f7f7 url("https://www.toptal.com/designers/subtlepatterns/grey_wash_wall.png") repeat;
}

/* Hero a pantalla completa */
.hero {
  position: relative;
  width: 100%;
  height: 35vh;
  background: url("https://images.unsplash.com/photo-1522202195467-52c5a0bfb57c?auto=format&fit=crop&w=1500&q=80") center/cover no-repeat;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--white);
  text-align: center;
  font-family: 'Montserrat', sans-serif;
}
.hero::before {
  content: "";
  position: absolute;
  top: 0; left: 0; right:0; bottom:0;
  background: var(--hero-overlay);
}
.hero-content {
  position: relative;
  z-index: 1;
  max-width: 800px;
  padding: 0 var(--gap);
}
.hero-content h1 {
  font-size: 3.5rem;
  margin-bottom: 0.5rem;
  font-weight: 700;
}
.hero-content p {
  font-size: 1.25rem;
  font-weight: 300;
  margin-bottom: var(--gap);
  line-height: 1.4;
}

/* Feature cards */
.features {
  display: flex;
  justify-content: center;
  gap: var(--gap);
  margin: var(--gap) 0 2rem;
  flex-wrap: wrap;
}
.feature-card {
  background: var(--white);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  padding: 1.5rem;
  max-width: 240px;
  text-align: center;
  font-family: 'Montserrat', sans-serif;
}
.feature-card svg {
  width: 40px;
  height: 40px;
  margin-bottom: 0.75rem;
  fill: var(--primary);
}
.feature-card h3 {
  margin: 0.5rem 0;
  font-size: 1.125rem;
  font-weight: 600;
}
.feature-card p {
  font-size: 0.9rem;
  color: #555;
  font-weight: 300;
  line-height: 1.3;
}
</style>
"""
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

st.markdown(
    """
    <style>
      .hero::before {
        background: rgba(31, 78, 121, 0.6) !important;
      }
    </style>
    """,
    unsafe_allow_html=True
)

# ────── SVG del logo ────────────────────────────────────────────────
SVG_LOGO = """
<svg width="32" height="32" viewBox="0 0 64 64" fill="none"
     xmlns="http://www.w3.org/2000/svg"
     style="vertical-align:middle;margin-right:8px">
  <circle cx="24" cy="32" r="18" stroke="white" stroke-width="6" fill="none"/>
  <circle cx="40" cy="32" r="18" stroke="white" stroke-width="6" fill="none"/>
</svg>
"""

# ────── CSS header y layout general ─────────────────────────────────
HEADER_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');

:root{
  --topbar-h: 42px;
  --header-h: 70px;
  --sidebar-w: 300px;
  --azul: #1F4E79;
}

/* HEADER full-width, debajo de topbar */
.header-bar{
  position:fixed; top:var(--topbar-h); left:0; width:100%; height:var(--header-h);
  background:linear-gradient(90deg,#14406b 0%,var(--azul) 100%);
  display:flex; align-items:center; justify-content:center;
  z-index:100; padding:0 16px;
}

.header-left{
  position:absolute; left:0; width:var(--sidebar-w);
  display:flex; align-items:center; justify-content:center;
}
.header-center{ font:700 30px 'Montserrat',sans-serif; color:#fff; }
.header-flag{
  position:absolute; right:16px; height:32px; border-radius:3px;
}

/* Empujar contenido para que no quede oculto */
section[data-testid="stSidebar"]{ margin-top:calc(var(--topbar-h) + var(--header-h)); }
div.block-container{ margin-top:calc(var(--topbar-h) + var(--header-h) + 4px); }

/* KPI cards */
.stMetric>div{
    border:2px solid var(--azul)!important; border-radius:10px;
    background:#fff; box-shadow:0 2px 6px #0003; padding:8px 8px
}

/* Sliders -> azul */
input[type=range]::-webkit-slider-runnable-track{background:var(--azul)33}
input[type=range]::-webkit-slider-thumb{background:var(--azul); border:none}
input[type=range]::-moz-range-track{background:var(--azul)33}
input[type=range]::-moz-range-thumb{background:var(--azul); border:none}

/* Sidebar gris azulado */
section[data-testid=stSidebar]{ background:#eaf0f7; }

/* centrar imágenes de gráficos */
.block-container img:not(.header-flag){ display:block; margin:0 auto; }
</style>
"""
st.markdown(
    """
<style>
div[data-testid="stMetricDelta"]{display:none!important;}
</style>
""",
    unsafe_allow_html=True
)

FLAG_AR = "https://flagcdn.com/w40/ar.png"

header_html = (
    HEADER_CSS +
    "<div class='header-bar'>"
      "<div class='header-left'>"
        f"{SVG_LOGO}<span style='font:600 20px Montserrat,sans-serif;color:#d0e1ff'>Civic Twin™</span>"
      "</div>"
      "<span class='header-center'>Cafetería en Quilmes</span>"
      f"<img src='{FLAG_AR}' class='header-flag'>"
    "</div>"
)

# ─── HOME ────────────────────────────────────────────────────────────
if st.session_state.view == "home":
    st.markdown(
        """
        <style>
        html, body, [data-testid="stAppViewContainer"] {
          height: 100vh !important;
          overflow-y: hidden !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <style>
        div.block-container, section[data-testid="stAppViewContainer"] {
            margin-top: -100px !important;
            padding-top: 0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <style>
        .feature-card {
          max-width: 300px !important;
          padding: 1rem 0.75rem !important;
          margin: 0.5rem !important;
        }
        .feature-card h3 {
          font-size: 1rem !important;
        }
        .feature-card p {
          font-size: 0.85rem !important;
          line-height: 1.2 !important;
        }
        .features {
          gap: 16px !important;
          margin-bottom: 0.5rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="hero">
          <div class="hero-content">
            <h1>Civic Twin™</h1>
            <p><strong>AI Driven Project Experimentation</strong><br>
               Genera simulaciones y tableros interactivos a demanda</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="features">
          <div class="feature-card">
            <svg viewBox="0 0 24 24"><path d="M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zm0-8h14V7H7v2z"/></svg>
            <h3>1. Describe tu informe</h3>
            <p>Cuenta qué necesitas en lenguaje natural y adjunta tus datos si los tienes.</p>
          </div>
          <div class="feature-card">
            <svg viewBox="0 0 24 24"><path d="M12 2a9.99 9.99 0 0 0-4.75 19.02l.45-2.18c-2.85-.5-5-2.93-5-5.84C2.7 10.4 6.1 7 10.5 7h.5V2z"/></svg>
            <h3>2. El agente procesa</h3>
            <p>Un flujo AI busca, prepara y genera tu tablero.</p>
          </div>
          <div class="feature-card">
            <svg viewBox="0 0 24 24"><path d="M3 3h18v18H3V3zm2 2v14h14V5H5zm3 3h8v2H8V8zm0 4h8v2H8v-2z"/></svg>
            <h3>3. Accede y comparte</h3>
            <p>Recibe el link a tu dashboard para explorar, ajustar y presentar.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.button("▶ Demo", use_container_width=True, on_click=go_mode)
        st.write("")
        st.button("✉️ Contacto", use_container_width=True, on_click=go_contact)

    st.stop()

# ─────────────────────────────────────────────────────────────────────
# MENÚ TIPO DE PROYECTO (PRIVADO / PÚBLICO)
# ─────────────────────────────────────────────────────────────────────
if st.session_state.view == "mode":
    st.markdown(header_html, unsafe_allow_html=True)
    st.markdown("### Elegí el tipo de proyecto")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🏪 Proyecto privado")
        st.write(
            "Evaluar la viabilidad económica de un emprendimiento (ej. cafetería en Quilmes) "
            "desde la perspectiva de un inversor."
        )
        st.button("Entrar a proyecto privado", use_container_width=True, on_click=go_private)

    with col2:
        st.markdown("#### 🏛️ Proyecto público (Civic Twin TCS)")
        st.write(
            "Simular el impacto de una política pública local (ej. simplificación de habilitaciones, "
            "cambios tributarios) sobre actividad económica, movilidad y recaudación."
        )
        st.button("Entrar a proyecto público", use_container_width=True, on_click=go_public)

    st.stop()

# ─────────────────────────────────────────────────────────────────────
# VISTA DASHBOARD PRIVADO (INVERSOR CAFÉ)
# ─────────────────────────────────────────────────────────────────────
if st.session_state.view == "dashboard_private":

    st.button("🏠 Inicio", on_click=go_home)

    st.markdown(header_html, unsafe_allow_html=True)

    st.markdown(
        """
        <style>
        div.block-container {
            margin-top: calc(var(--topbar-h) + var(--header-h)) !important;
            padding-top: 0 !important;
        }
        section[data-testid="stSidebar"] {
            margin-top: calc(var(--topbar-h) + var(--header-h)) !important;
            padding-top: 0 !important;
        }
        hr, div[data-testid="stDivider"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True
    )

    BASE = Path(__file__).parent
    CSV, XLSX = BASE/'CivicTwin_Cafe_Quilmes_Data.csv', BASE/'CivicTwin_Cafe_Quilmes_Data.xlsx'

    @st.cache_data
    def load():
        if CSV.exists():
            return {"tidy": pd.read_csv(CSV)}
        if XLSX.exists():
            return pd.read_excel(XLSX, sheet_name=None)
        st.error("Dataset no encontrado")
        return {}

    d = load()
    if not d:
        st.stop()
    if "tidy" in d:
        t = d["tidy"]
        init, month  = t[t.dataset=="initial_costs"], t[t.dataset=="monthly_costs"]
        sales, ass   = t[t.dataset=="sales_scenarios"], t[t.dataset=="assumptions"]
    else:
        init, month, sales, ass = d["initial_costs"], d["monthly_costs"], d["sales_scenarios"], d["assumptions"]

    ASS      = dict(zip(ass.variable, ass.value))
    WD       = int(ASS.get("working_days_per_month", 26))
    INS_PCT  = float(ASS.get("insumos_percent_of_sales", 0.30))
    INV      = init.cost_ars.sum()
    FIXED    = month.cost_ars.sum()

    st.sidebar.header("Escenario (proyecto privado)")
    cli = st.sidebar.slider(
        "Clientes por día", 30, 200,
        int(sales.loc[sales.scenario=="Moderado","clients_per_day"]),
        5
    )
    tic = st.sidebar.slider(
        "Ticket promedio (ARS)", 3000, 8000,
        int(sales.loc[sales.scenario=="Moderado","ticket_ars"]),
        100
    )
    inf = st.sidebar.number_input("Inflación anual (%)", 0.0, 200.0, 0.0, 1.0)

    ventas   = cli * tic * WD
    insumos  = ventas * INS_PCT
    ganancia = ventas - (insumos + FIXED)
    payback  = "∞" if ganancia <= 0 else INV / ganancia
    NBSP = "\u00A0"

    c1, c2, c3 = st.columns(3)
    c1.metric("Ventas mensuales", f"${ventas:,.0f}", delta=NBSP)
    c2.metric("Ganancia mensual", f"${ganancia:,.0f}", delta=NBSP)
    c3.metric(
        "Pay-back (meses)",
        "No rentable" if payback == "∞" else f"{payback:.1f}",
        delta=NBSP
    )

    mes   = np.arange(1, 25)
    serie = ganancia * (1 + inf/100) ** (mes / 12)
    flujo = np.cumsum(serie) - INV

    fig, ax = plt.subplots(figsize=(11, 2.3))
    ax.plot(mes, flujo, color="#1F4E79", lw=2)
    ax.axhline(0, color="#888", lw=.8, ls="--")
    ax.set_xlabel("Mes")
    ax.set_ylabel("Flujo acumulado (ARS)")
    ax.set_title("Proyección 24 meses", color="#14406b", weight="bold")
    st.pyplot(fig, use_container_width=False)
    st.caption("Datos fuente · Julio 2025 – Civic Twin™")

    st.markdown(
        """
        <style>
        [data-testid="stMetricDelta"] { display:none !important; }
        </style>
        """,
        unsafe_allow_html=True
    )

    series_data_private = {
        "flujo_24m": {
            "x": list(mes),
            "y": flujo.tolist(),
            "default_label": "Flujo acumulado"
        }
    }

    st.markdown("### 🧠 Informe interactivo generado con IA (proyecto privado)")
    st.write(
        "Ingresá un prompt describiendo el informe que querés ver para este proyecto privado. "
        "El modelo devolverá un layout interactivo (KPIs, gráficos, texto) basado en el contexto numérico actual."
    )
    prompt_privado = st.text_area(
        "Prompt para OpenAI (proyecto privado)",
        value="Quiero un dashboard que destaque si el proyecto es rentable, muestre el flujo acumulado y recomiende acciones para mejorar la rentabilidad."
    )

    if st.button("🆕 Generar nuevo informe interactivo (privado)"):
        if client is None:
            st.error("No se pudo inicializar OpenAI. Revisá la configuración de OPENAI_API_KEY en secrets o variables de entorno.")
        else:
            context_privado = f"""
Contexto numérico del proyecto (escenario actual):
- Clientes por día: {cli}
- Ticket promedio: {tic:.0f} ARS
- Días trabajados por mes: {WD}
- Ventas mensuales: {ventas:.0f} ARS
- Ganancia mensual: {ganancia:.0f} ARS
- Costos fijos mensuales: {FIXED:.0f} ARS
- Inversión inicial: {INV:.0f} ARS
- Inflación anual asumida: {inf:.1f} %
- Payback estimado (meses): {"∞" if payback == "∞" else f"{payback:.1f}"}

Series disponibles para gráficos (no inventes otras):
- ID: "flujo_24m" → Descripción: "Flujo acumulado del proyecto en 24 meses"
"""

            schema_description = """
Debes devolver un JSON con este formato (sin texto adicional fuera del JSON):

{
  "title": "Título del informe",
  "narrative": "Texto breve en Markdown (2–4 párrafos) resumiendo la situación.",
  "sections": [
    {
      "type": "kpi_row",
      "metrics": [
        {
          "label": "Nombre de la métrica",
          "value": "texto corto (ej: '$1.200.000')",
          "suffix": "opcional (ej: ' ARS')",
          "description": "opcional, breve explicación"
        }
      ]
    },
    {
      "type": "line_chart",
      "title": "Título del gráfico",
      "series": [
        {
          "id": "flujo_24m",
          "label": "Etiqueta para la leyenda"
        }
      ]
    },
    {
      "type": "markdown",
      "title": "Título de la sección",
      "body": "Texto en Markdown con explicaciones y recomendaciones."
    }
  ]
}

Reglas:
- Usá sólo series con IDs definidos en el contexto (por ejemplo "flujo_24m").
- Podés definir 1–3 secciones de tipo kpi_row, 1–2 line_chart y 1–3 markdown.
- No agregues comentarios fuera del JSON.
"""

            system_prompt_priv = (
                "Sos un analista financiero que diseña dashboards ejecutivos interactivos para inversores "
                "de pequeños negocios en Argentina. Respondés sólo con JSON siguiendo el esquema indicado."
            )

            user_prompt_priv = f"""
{context_privado}

Pedido del usuario:
\"\"\"{prompt_privado}\"\"\"

{schema_description}
"""

            with st.spinner("Generando layout del informe interactivo con OpenAI..."):
                resp = client.responses.create(
                    model="gpt-4.1-mini",
                    input=[
                        {"role": "system", "content": system_prompt_priv},
                        {"role": "user", "content": user_prompt_priv},
                    ],
                    response_format={"type": "json_object"},
                )
                raw = resp.output[0].content[0].text
                try:
                    layout = json.loads(raw)
                except Exception as e:
                    st.error(f"No se pudo parsear el JSON devuelto por el modelo: {e}")
                    st.code(raw)
                else:
                    st.markdown("#### Informe interactivo")
                    render_interactive_report(layout, series_data_private)

# ─────────────────────────────────────────────────────────────────────
# VISTA DASHBOARD PÚBLICO (TCS – POLÍTICAS)
# ─────────────────────────────────────────────────────────────────────
if st.session_state.view == "dashboard_public":

    st.button("🏠 Inicio", on_click=go_home)
    st.markdown(header_html, unsafe_allow_html=True)

    # Override layout para permitir scroll en sector público
    st.markdown(
        """
        <style>
        div.block-container{
            height: auto !important;
            overflow: visible !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### 🏛️ Civic Twin™ · Proyecto público (TCS)")
    st.write(
        "Simulá el efecto de una política pública local (por ejemplo, simplificar habilitaciones de cafés) "
        "sobre la actividad económica (E), la movilidad (M) y la recaudación fiscal (F) de un municipio."
    )

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Parámetros iniciales del territorio")
        E0 = st.number_input("Actividad económica inicial (E₀)", min_value=0.0, value=1_000_000.0, step=50_000.0)
        M0 = st.number_input("Índice de movilidad inicial (M₀)", min_value=0.0, value=100.0, step=5.0)
        F0 = st.number_input("Recaudación fiscal inicial mensual (F₀)", min_value=0.0, value=20_000_000.0, step=500_000.0)

        horizonte = st.slider("Horizonte de simulación (meses)", 6, 60, 24, 6)

    with col_right:
        st.subheader("Política y shocks")
        intensidad = st.slider(
            "Intensidad de la política (0 = sin cambio, 1 = reforma fuerte)",
            0.0, 1.0, 0.3, 0.05
        )
        g_base = st.slider("Crecimiento base anual de E (%)", -10.0, 20.0, 3.0, 0.5)
        infl_anual = st.slider("Inflación anual (%)", 0.0, 200.0, 100.0, 5.0)

    def F_transition(s_t, policy_intensity, infl, g_base):
        E_t, M_t, F_t = s_t

        g_m = (1 + g_base / 100) ** (1 / 12) - 1
        infl_m = (1 + infl / 100) ** (1 / 12) - 1

        g_eff = g_m + 0.01 * policy_intensity
        E_next = E_t * (1 + g_eff)

        if E_t > 0:
            growth_E = (E_next / E_t) - 1
        else:
            growth_E = 0.0
        M_next = M_t * (1 + 0.3 * growth_E)

        base_imponible = E_next * 0.05
        F_next = F_t * (1 + infl_m) + base_imponible * (0.15 + 0.1 * policy_intensity)

        return np.array([E_next, M_next, F_next], dtype=float)

    def simulate_trajectory(S0, policy_intensity, infl, g_base, T):
        S = np.zeros((T + 1, 3))
        S[0, :] = S0
        for t in range(T):
            S[t + 1, :] = F_transition(S[t, :], policy_intensity, infl, g_base)
        return S

    S0 = np.array([E0, M0, F0], dtype=float)
    T = horizonte

    traj_base = simulate_trajectory(S0, policy_intensity=0.0, infl=infl_anual, g_base=g_base, T=T)
    traj_policy = simulate_trajectory(S0, policy_intensity=intensidad, infl=infl_anual, g_base=g_base, T=T)

    w_base = 0.7 * traj_base[-1, 0] + 0.3 * traj_base[-1, 2]
    w_policy = 0.7 * traj_policy[-1, 0] + 0.3 * traj_policy[-1, 2]

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Welfare base (E,F)", f"{w_base:,.0f}")
    with c2:
        st.metric("Welfare con política", f"{w_policy:,.0f}")

    meses = np.arange(0, T + 1)

    st.markdown("#### Trayectorias de E, M y F")

    figE, axE = plt.subplots(figsize=(10, 2.2))
    axE.plot(meses, traj_base[:, 0], label="E base", linestyle="--")
    axE.plot(meses, traj_policy[:, 0], label="E política", linewidth=2)
    axE.set_xlabel("Mes"); axE.set_ylabel("E")
    axE.set_title("Actividad económica (E)")
    axE.legend()
    st.pyplot(figE, use_container_width=True)

    figM, axM = plt.subplots(figsize=(10, 2.2))
    axM.plot(meses, traj_base[:, 1], label="M base", linestyle="--")
    axM.plot(meses, traj_policy[:, 1], label="M política", linewidth=2)
    axM.set_xlabel("Mes"); axM.set_ylabel("M")
    axM.set_title("Movilidad (M)")
    axM.legend()
    st.pyplot(figM, use_container_width=True)

    figF, axF = plt.subplots(figsize=(10, 2.2))
    axF.plot(meses, traj_base[:, 2], label="F base", linestyle="--")
    axF.plot(meses, traj_policy[:, 2], label="F política", linewidth=2)
    axF.set_xlabel("Mes"); axF.set_ylabel("F (recaudación)")
    axF.set_title("Recaudación fiscal (F)")
    axF.legend()
    st.pyplot(figF, use_container_width=True)

    st.caption("Este módulo implementa un modelo dinámico simplificado TCS: S_{t+1} = F(S_t, π_t, ξ_t; θ).")

    series_data_public = {
        "E_base": {
            "x": list(meses),
            "y": traj_base[:, 0].tolist(),
            "default_label": "E base"
        },
        "E_policy": {
            "x": list(meses),
            "y": traj_policy[:, 0].tolist(),
            "default_label": "E política"
        },
        "M_base": {
            "x": list(meses),
            "y": traj_base[:, 1].tolist(),
            "default_label": "M base"
        },
        "M_policy": {
            "x": list(meses),
            "y": traj_policy[:, 1].tolist(),
            "default_label": "M política"
        },
        "F_base": {
            "x": list(meses),
            "y": traj_base[:, 2].tolist(),
            "default_label": "F base"
        },
        "F_policy": {
            "x": list(meses),
            "y": traj_policy[:, 2].tolist(),
            "default_label": "F política"
        },
    }

    st.markdown("### 🧠 Informe interactivo generado con IA (proyecto público)")
    st.write(
        "Ingresá un prompt describiendo el tipo de informe o tablero que querés ver para este proyecto público. "
        "El modelo devolverá un layout (KPIs, gráficos, texto) basado en las trayectorias de E, M y F."
    )
    prompt_publico = st.text_area(
        "Prompt para OpenAI (proyecto público)",
        value="Quiero un dashboard que compare base vs política en E, M y F, identifique trade-offs y recomiende si conviene implementar la política."
    )

    if st.button("🆕 Generar nuevo informe interactivo (público)"):
        if client is None:
            st.error("No se pudo inicializar OpenAI. Revisá la configuración de OPENAI_API_KEY en secrets o variables de entorno.")
        else:
            context_publico = f"""
Contexto del territorio y simulación:

- Estado inicial:
  - E₀ (actividad económica): {E0:,.0f}
  - M₀ (movilidad): {M0:,.1f}
  - F₀ (recaudación mensual): {F0:,.0f} ARS

- Parámetros de simulación:
  - Horizonte: {T} meses
  - Crecimiento base anual de E: {g_base:.1f} %
  - Inflación anual: {infl_anual:.1f} %
  - Intensidad de la política: {intensidad:.2f} (0=sin cambio, 1=reforma fuerte)

- Resultados al final del horizonte:
  - Escenario base:
    - E_T(base): {traj_base[-1,0]:,.0f}
    - M_T(base): {traj_base[-1,1]:,.1f}
    - F_T(base): {traj_base[-1,2]:,.0f} ARS
    - Welfare base (0.7*E + 0.3*F): {w_base:,.0f}
  - Escenario con política:
    - E_T(política): {traj_policy[-1,0]:,.0f}
    - M_T(política): {traj_policy[-1,1]:,.1f}
    - F_T(política): {traj_policy[-1,2]:,.0f} ARS
    - Welfare política (0.7*E + 0.3*F): {w_policy:,.0f}

Series disponibles para gráficos (no inventes otras):
- "E_base"    → E en escenario base
- "E_policy"  → E con política
- "M_base"    → M en escenario base
- "M_policy"  → M con política
- "F_base"    → F en escenario base
- "F_policy"  → F con política
"""

            schema_description_pub = """
Debes devolver un JSON con este formato (sin texto adicional fuera del JSON):

{
  "title": "Título del informe",
  "narrative": "Texto breve en Markdown (2–4 párrafos) resumiendo la situación.",
  "sections": [
    {
      "type": "kpi_row",
      "metrics": [
        {
          "label": "Nombre de la métrica",
          "value": "texto corto (ej: 'Alta', 'Media', '$50M')",
          "suffix": "opcional",
          "description": "opcional, breve explicación"
        }
      ]
    },
    {
      "type": "line_chart",
      "title": "Título del gráfico",
      "series": [
        {
          "id": "E_base",
          "label": "E base"
        },
        {
          "id": "E_policy",
          "label": "E política"
        }
      ]
    },
    {
      "type": "markdown",
      "title": "Título de la sección",
      "body": "Texto en Markdown con análisis y recomendaciones."
    }
  ]
}

Reglas:
- Usá sólo series con IDs definidos en el contexto (E_base, E_policy, M_base, M_policy, F_base, F_policy).
- Podés definir varias secciones de cada tipo, pero no más de 8 secciones en total.
- No agregues comentarios fuera del JSON.
"""

            system_prompt_pub = (
                "Sos un analista de políticas públicas especializado en evaluación de impacto territorial. "
                "Diseñás dashboards interactivos para gobiernos locales en Argentina. "
                "Respondés sólo con JSON siguiendo el esquema indicado."
            )

            user_prompt_pub = f"""
{context_publico}

Pedido del usuario:
\"\"\"{prompt_publico}\"\"\"

{schema_description_pub}
"""

            with st.spinner("Generando layout del informe interactivo con OpenAI..."):
                resp = client.responses.create(
                    model="gpt-4.1-mini",
                    input=[
                        {"role": "system", "content": system_prompt_pub},
                        {"role": "user", "content": user_prompt_pub},
                    ],
                    response_format={"type": "json_object"},
                )
                raw = resp.output[0].content[0].text
                try:
                    layout = json.loads(raw)
                except Exception as e:
                    st.error(f"No se pudo parsear el JSON devuelto por el modelo: {e}")
                    st.code(raw)
                else:
                    st.markdown("#### Informe interactivo")
                    render_interactive_report(layout, series_data_public)

# ─────────────────────────────────────────────────────────────────────
# VISTA CONTACTO
# ─────────────────────────────────────────────────────────────────────
if st.session_state.view == "contact":
    st.button("🏠 Inicio", on_click=go_home)

    st.title("📬 Contacto")
    with st.form("contact_form", clear_on_submit=True):
        nombre  = st.text_input("Nombre")
        email   = st.text_input("Email")
        mensaje = st.text_area("Mensaje")
        enviado = st.form_submit_button("Enviar")

    if enviado:
        try:
            send_contact_email(nombre, email, mensaje)
            st.success("✅ Tu mensaje ha sido enviado, ¡gracias!")
        except Exception as e:
            st.error(f"❌ No se pudo enviar el correo: {e}")

# ─── BLOQUE CSS FINAL ───────────────────────────────────────────────
st.markdown(
    """
<style>
div.block-container{
    margin-top:calc(var(--topbar-h) + var(--header-h)) !important;
    padding-top:0 !important;
    height:calc(100vh - var(--topbar-h) - var(--header-h));
    display:flex; flex-direction:column; overflow:hidden;
}

/* KPI más compactos */
div[data-testid="stMetric"]{
    padding:4px 6px !important;
}
div[data-testid="stMetric"] > label div{
    font-size:14px !important; line-height:16px !important;
}
div[data-testid="stMetric"] > div:nth-child(2) span{
    font-size:19px !important; line-height:21px !important;
}

/* limitar altura del gráfico a 220 px si se usa .graph-row */
.graph-row svg,
.graph-row canvas{
    max-height:220px !important;
}

/* ocultar delta en todas las métricas */
[data-testid="stMetricDelta"]{display:none !important;}
</style>
""",
    unsafe_allow_html=True
)
