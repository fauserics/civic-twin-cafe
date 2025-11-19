import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import smtplib
from email.message import EmailMessage

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
    # Sin scroll en home
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

    # Ajuste de hero
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

    # Override feature cards
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

    # Hero reducido
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

    # Feature cards
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

    # Botones centrados
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

    # Ajuste de márgenes
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

    # ────── DATOS CAFÉ ─────────────────────────────────────────────
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

    # ────── SIDEBAR controles ─────────────────────────────────────
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

    # ────── KPI actuales ───────────────────────────────────────────
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

    # ────── Gráfico flujo acumulado 24 meses ───────────────────────
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

    # Ocultar delta métricas
    st.markdown(
        """
        <style>
        [data-testid="stMetricDelta"] { display:none !important; }
        </style>
        """,
        unsafe_allow_html=True
    )

    # ────── BLOQUE: Dashboard AI a demanda (stub OpenAI) ──────────
    st.markdown("### 🧠 Dashboard generado con IA (proyecto privado)")
    st.write(
        "Ingresá un prompt describiendo el informe que querés ver para este proyecto privado. "
        "En la versión integrada, este texto se enviará a OpenAI para generar un dashboard a medida."
    )
    prompt_privado = st.text_area(
        "Prompt para OpenAI (proyecto privado)",
        value="Quiero un dashboard que muestre el punto de equilibrio, el payback y escenarios de estrés para la cafetería."
    )
    if st.button("Generar dashboard AI (demo privado)"):
        # Aquí, en producción, llamarías a la API de OpenAI con el prompt_privado
        # y renderizarías gráficos/tablas dinámicas. Por ahora, mostramos un placeholder.
        st.info("🔧 Esta es una demo. Aquí se mostraría el dashboard generado por OpenAI según tu prompt.")
        st.write("**Prompt enviado (demo):**")
        st.code(prompt_privado, language="markdown")


# ─────────────────────────────────────────────────────────────────────
# VISTA DASHBOARD PÚBLICO (TCS – POLÍTICAS)
# ─────────────────────────────────────────────────────────────────────
if st.session_state.view == "dashboard_public":

    st.button("🏠 Inicio", on_click=go_home)
    st.markdown(header_html, unsafe_allow_html=True)

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

    # Modelo dinámico simplificado TCS
    def F_transition(s_t, policy_intensity, infl, g_base):
        """
        s_t = [E_t, M_t, F_t]
        policy_intensity ∈ [0,1]
        infl: inflación anual (%)
        g_base: crecimiento base anual de E (%)
        """
        E_t, M_t, F_t = s_t

        # Tasas mensuales aproximadas
        g_m = (1 + g_base / 100) ** (1 / 12) - 1
        infl_m = (1 + infl / 100) ** (1 / 12) - 1

        # Política: aumenta tasa de crecimiento de E
        g_eff = g_m + 0.01 * policy_intensity
        E_next = E_t * (1 + g_eff)

        # Movilidad responde a cambios en E
        if E_t > 0:
            growth_E = (E_next / E_t) - 1
        else:
            growth_E = 0.0
        M_next = M_t * (1 + 0.3 * growth_E)

        # Recaudación: inflación + base imponible ligada a E
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

    # Escenario base
    traj_base = simulate_trajectory(S0, policy_intensity=0.0, infl=infl_anual, g_base=g_base, T=T)
    # Escenario con política
    traj_policy = simulate_trajectory(S0, policy_intensity=intensidad, infl=infl_anual, g_base=g_base, T=T)

    # Welfare simple: combinación de E y F al final
    w_base = 0.7 * traj_base[-1, 0] + 0.3 * traj_base[-1, 2]
    w_policy = 0.7 * traj_policy[-1, 0] + 0.3 * traj_policy[-1, 2]

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Welfare base (E,F)", f"{w_base:,.0f}")
    with c2:
        st.metric("Welfare con política", f"{w_policy:,.0f}")

    meses = np.arange(0, T + 1)

    st.markdown("#### Trayectorias de E, M y F")

    # Gráfico E
    figE, axE = plt.subplots(figsize=(10, 2.2))
    axE.plot(meses, traj_base[:, 0], label="E base", linestyle="--")
    axE.plot(meses, traj_policy[:, 0], label="E política", linewidth=2)
    axE.set_xlabel("Mes"); axE.set_ylabel("E")
    axE.set_title("Actividad económica (E)")
    axE.legend()
    st.pyplot(figE, use_container_width=True)

    # Gráfico M
    figM, axM = plt.subplots(figsize=(10, 2.2))
    axM.plot(meses, traj_base[:, 1], label="M base", linestyle="--")
    axM.plot(meses, traj_policy[:, 1], label="M política", linewidth=2)
    axM.set_xlabel("Mes"); axM.set_ylabel("M")
    axM.set_title("Movilidad (M)")
    axM.legend()
    st.pyplot(figM, use_container_width=True)

    # Gráfico F
    figF, axF = plt.subplots(figsize=(10, 2.2))
    axF.plot(meses, traj_base[:, 2], label="F base", linestyle="--")
    axF.plot(meses, traj_policy[:, 2], label="F política", linewidth=2)
    axF.set_xlabel("Mes"); axF.set_ylabel("F (recaudación)")
    axF.set_title("Recaudación fiscal (F)")
    axF.legend()
    st.pyplot(figF, use_container_width=True)

    st.caption("Este módulo implementa un modelo dinámico simplificado TCS: S_{t+1} = F(S_t, π_t, ξ_t; θ).")

    # ────── BLOQUE: Dashboard AI a demanda (stub OpenAI) ──────────
    st.markdown("### 🧠 Dashboard generado con IA (proyecto público)")
    st.write(
        "Ingresá un prompt describiendo el informe que querés ver para este proyecto público. "
        "En la versión integrada, este texto se enviará a OpenAI para generar un dashboard a medida "
        "sobre E, M, F y las políticas simuladas."
    )
    prompt_publico = st.text_area(
        "Prompt para OpenAI (proyecto público)",
        value="Quiero un dashboard que compare la política actual con la reforma, mostrando E, M y F con bandas de incertidumbre y una recomendación de política."
    )
    if st.button("Generar dashboard AI (demo público)"):
        st.info("🔧 Esta es una demo. Aquí se mostraría el dashboard generado por OpenAI según tu prompt (proyecto público).")
        st.write("**Prompt enviado (demo):**")
        st.code(prompt_publico, language="markdown")


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
