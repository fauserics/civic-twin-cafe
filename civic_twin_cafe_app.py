import streamlit as st, pandas as pd, numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import smtplib
from email.message import EmailMessage

import streamlit as st

# ─── Set page config ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Cafetería Quilmes | Civic Twin™",
    layout="wide",
    # opcional: deshabilitar items de ayuda / report
    menu_items={
        "Get help": None,
        "Report a bug": None,
        "About": None
    }
)

# ─── Oculta el menú (hamburguesa) y el footer ─────────────────────────
st.markdown(
    """
    <style>
      /* Oculta el menú principal (incluye 'View source') */
      #MainMenu {visibility: hidden;}
      /* Oculta el footer de Streamlit */
      footer {visibility: hidden;}
      /* Opcional: oculta el header que aparece al mover el ratón arriba */
      header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)

# … el resto de tu app …


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


# ─── helpers de navegación ──────────────────────────────
def go_home():
    st.session_state.view = "home"

def go_dashboard():
    st.session_state.view = "dashboard"

def go_contact():
    st.session_state.view = "contact"


st.set_page_config(page_title="Cafetería en Quilmes | Civic Twin™", layout="wide")

# Inicializar la vista por defecto
if "view" not in st.session_state:
    st.session_state.view = "home"


GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');

/* Variables */
:root {
  --primary: #1F4E79;
  --white: #FFFFFF;
  --dark-overlay: rgba(0, 0, 0, 0.5);
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
  background: var(--dark-overlay);
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


# ────── SVG del logo (dos “círculos abiertos”)
SVG_LOGO = """
<svg width="32" height="32" viewBox="0 0 64 64" fill="none"
     xmlns="http://www.w3.org/2000/svg"
     style="vertical-align:middle;margin-right:8px">
  <circle cx="24" cy="32" r="18" stroke="white" stroke-width="6" fill="none"/>
  <circle cx="40" cy="32" r="18" stroke="white" stroke-width="6" fill="none"/>
</svg>
"""

# ────── CSS global
HEADER_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');

:root{
  --topbar-h: 42px;   /* barra de íconos de Streamlit Cloud */
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

/* Secciones internas */
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
.stMetric>div{border:2px solid var(--azul)!important; border-radius:10px;
              background:#fff; box-shadow:0 2px 6px #0003; padding:8px 8px}

/* Sliders -> azul */
input[type=range]::-webkit-slider-runnable-track{background:var(--azul)33}
input[type=range]::-webkit-slider-thumb{background:var(--azul); border:none}
input[type=range]::-moz-range-track{background:var(--azul)33}
input[type=range]::-moz-range-thumb{background:var(--azul); border:none}

/* Sidebar gris azulado */
section[data-testid=stSidebar]{ background:#eaf0f7; }
/* Centrar imagen del gráfico */
  .block-container img:not(.header-flag){ display:block; margin:0 auto; }
</style>
"""
st.markdown("""
<style>
/* oculta cualquier delta (None) que se pueda colar */
div[data-testid="stMetricDelta"]{display:none!important;}
</style>
""", unsafe_allow_html=True)

FLAG_AR = "https://flagcdn.com/w40/ar.png"

SVG_LOGO = """
<svg width="32" height="32" viewBox="0 0 64 64" fill="none"
     xmlns="http://www.w3.org/2000/svg"
     style="vertical-align:middle;margin-right:8px">
  <circle cx="24" cy="32" r="18" stroke="white" stroke-width="6" fill="none"/>
  <circle cx="40" cy="32" r="18" stroke="white" stroke-width="6" fill="none"/>
</svg>
"""

header_html = (
    HEADER_CSS +
    "<div class='header-bar'>"
      "<div class='header-left'>"
        f"{SVG_LOGO}<span style='font:600 20px Montserrat,sans-serif;color:#d0e1ff'>Civic Twin™</span>"
      "</div>"
      "<span class='header-center'>Cafetería Quilmes</span>"
      f"<img src='{FLAG_AR}' class='header-flag'>"
    "</div>"
)


# ─── Después de st.markdown(header_html, unsafe_allow_html=True) ───
if "view" not in st.session_state:
    st.session_state.view = "home"

# Vista HOME
# ─── CSS para quitar scroll en Home ───────────────────────
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

# ─── VISTA HOME ───────────────────────────────
if st.session_state.view == "home":
    # Inyectamos el CSS para overflow:hidden (aunque ya está en GLOBAL_CSS)
    st.markdown(
        """
        <style>
        html, body, [data-testid="stAppViewContainer"] {
          overflow: hidden !important;
          height: 100vh !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Hero reducido
    st.markdown(
        """
        <div class="hero">
          <div class="hero-content">
            <h1>Civic Twin™</h1>
            <p><strong>AI-Driven Project Experimentation:</strong><br>
               Genera gemelos digitales y tableros interactivos a demanda.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

   # Feature cards explicativas
    st.markdown(
        """
        <div class="features">
          <div class="feature-card">
            <!-- Icono de datos -->
            <svg viewBox="0 0 24 24"><path d="M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zm0-8h14V7H7v2z"/></svg>
            <h3>1. Describe tu informe</h3>
            <p>Cuenta qué necesitas en lenguaje natural y adjunta tus datos si los tienes.</p>
          </div>
          <div class="feature-card">
            <!-- Icono de IA -->
            <svg viewBox="0 0 24 24"><path d="M12 2a9.99 9.99 0 0 0-4.75 19.02l.45-2.18c-2.85-.5-5-2.93-5-5.84C2.7 10.4 6.1 7 10.5 7h.5V2z"/></svg>
            <h3>2. El agente procesa</h3>
            <p>Un flujo AI busca, prepara y genera tu tablero automáticamente.</p>
          </div>
          <div class="feature-card">
            <!-- Icono de tablero -->
            <svg viewBox="0 0 24 24"><path d="M3 3h18v18H3V3zm2 2v14h14V5H5zm3 3h8v2H8V8zm0 4h8v2H8v-2z"/></svg>
            <h3>3. Accede y comparte</h3>
            <p>Recibe el link a tu dashboard para explorar, ajustar y presentar.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Botones centrados
    st.write("")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.button("▶ Demo", use_container_width=True, on_click=go_dashboard)
        st.write("")
        st.button("✉️ Contacto", use_container_width=True, on_click=go_contact)
    st.stop()

    # CTA final: Demo y Contacto centrados
    st.write("")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.button("▶ Demo", use_container_width=True, on_click=go_dashboard)
        st.write("")
        st.button("✉️ Contacto", use_container_width=True, on_click=go_contact)
    st.stop()


# ————————————————————————————————————————————————
# VISTA DASHBOARD
# ————————————————————————————————————————————————
if st.session_state.view == "dashboard":
   
    # — Botón para volver a Home —
    st.button("🏠 Inicio", on_click=go_home)

    # — Header azul —
    st.markdown(header_html, unsafe_allow_html=True)

     # ────── AJUSTE DE MÁRGENES & OCULTAR RAYA ─────────────
    st.markdown(
        """
        <style>
         /* Eleva todo el contenido principal 40px hacia arriba */
        div.block-container {
            margin-top: calc(var(--topbar-h) + var(--header-h) - 80px) !important;
            padding-top: 0 !important;
        }
        /* Mueve TODO el contenido justo bajo el banner azul (sin gap) */
        div.block-container,
        section[data-testid="stSidebar"] {
            margin-top: calc(var(--topbar-h) + var(--header-h) + 0px) !important;
            padding-top: 0 !important;
        }
        /* Oculta cualquier línea <hr> (divider) que aparezca */
        hr, div[data-testid="stDivider"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True
    )

    # ────── DATOS ───────────────────────────────────────
    BASE = Path(__file__).parent
    CSV, XLSX = BASE/'CivicTwin_Cafe_Quilmes_Data.csv', BASE/'CivicTwin_Cafe_Quilmes_Data.xlsx'
    @st.cache_data
    def load():
        if CSV.exists():  return {"tidy": pd.read_csv(CSV)}
        if XLSX.exists(): return pd.read_excel(XLSX, sheet_name=None)
        st.error("Dataset no encontrado"); return {}
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

    # ────── SIDEBAR controles ────────────────────────────
    st.sidebar.header("Escenario")
    cli = st.sidebar.slider("Clientes por día", 30, 200,
          int(sales.loc[sales.scenario=="Moderado","clients_per_day"]), 5)
    tic = st.sidebar.slider("Ticket promedio (ARS)", 3000, 8000,
          int(sales.loc[sales.scenario=="Moderado","ticket_ars"]), 100)
    inf = st.sidebar.number_input("Inflación anual (%)", 0.0, 200.0, 0.0, 1.0)

    # ────── KPI ───────────────────────────────────────────
    ventas   = cli * tic * WD
    insumos  = ventas * INS_PCT
    ganancia = ventas - (insumos + FIXED)
    payback  = "∞" if ganancia <= 0 else INV / ganancia
    NBSP = "\u00A0"
    c1, c2, c3 = st.columns(3)
    c1.metric("Ventas mensuales", f"${ventas:,.0f}", delta=NBSP)
    c2.metric("Ganancia mensual", f"${ganancia:,.0f}", delta=NBSP)
    c3.metric("Pay-back (meses)",
              "No rentable" if payback == "∞" else f"{payback:.1f}",
              delta=NBSP)

    # ────── Gráfico flujo acumulado ───────────────────────
    mes   = np.arange(1,25)
    serie = ganancia * (1 + inf/100) ** (mes / 12)
    flujo = np.cumsum(serie) - INV
    fig, ax = plt.subplots(figsize=(11,2.3))
    ax.plot(mes, flujo, color="#1F4E79", lw=2)
    ax.axhline(0, color="#888", lw=.8, ls="--")
    ax.set_xlabel("Mes"); ax.set_ylabel("Flujo acumulado (ARS)")
    ax.set_title("Proyección 24 meses", color="#14406b", weight="bold")
    st.pyplot(fig, use_container_width=False)
    st.caption("Datos fuente · Julio 2025 – Civic Twin™")

    # oculta cualquier delta (None)
    st.markdown(
        """
        <style>
        [data-testid="stMetricDelta"] { display:none !important; }
        </style>
        """, unsafe_allow_html=True
    )

# ————————————————————————————————————————————————
# VISTA CONTACTO
# ————————————————————————————————————————————————
if st.session_state.view == "contact":
    st.button("🏠 Inicio", on_click=go_home)

    st.title("📬 Contáctame")
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


# ─── BLOQUE CSS FINAL (se inyecta al final para que siempre gane) ───
st.markdown("""
<style>
/* ① reducir margen bajo el header */
div.block-container{
    margin-top:calc(var(--topbar-h) + var(--header-h)) !important; /* ↓ 4 px → 0 px */
    padding-top:0 !important;          /* quita padding interno extra */
    height:calc(100vh - var(--topbar-h) - var(--header-h));
    display:flex; flex-direction:column; overflow:hidden;
}


/* ② KPI más compactos — se conserva el borde azul de 2 px */
div[data-testid="stMetric"]{
    padding:4px 6px !important;        /* antes 12 px */
}
div[data-testid="stMetric"] > label div{
    font-size:14px !important; line-height:16px !important;
}
div[data-testid="stMetric"] > div:nth-child(2) span{
    font-size:19px !important; line-height:21px !important;
}

/* ③ limitar altura del gráfico a 220 px */
.graph-row svg,
.graph-row canvas{
    max-height:220px !important;
}
</style>
""", unsafe_allow_html=True)


# Oculta por completo la etiqueta delta (texto y flecha) de TODAS las métricas
st.markdown(
    """
    <style>
    /* oculta la cajita delta (None) en cualquier tag */
[data-testid="stMetricDelta"]{display:none !important;}
 </style>
    """,
    unsafe_allow_html=True
)
