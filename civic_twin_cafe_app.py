import streamlit as st, pandas as pd, numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

st.set_page_config(page_title="Cafetería Quilmes | Civic Twin™", layout="wide")

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
st.markdown(header_html, unsafe_allow_html=True)
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


# ────── DATOS
BASE = Path(__file__).parent
CSV, XLSX = BASE/'CivicTwin_Cafe_Quilmes_Data.csv', BASE/'CivicTwin_Cafe_Quilmes_Data.xlsx'
@st.cache_data
def load():
    if CSV.exists():  return {"tidy": pd.read_csv(CSV)}
    if XLSX.exists(): return pd.read_excel(XLSX, sheet_name=None)
    st.error("Dataset no encontrado"); return {}
d = load();  st.stop() if not d else None
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

# ────── SIDEBAR controles
st.sidebar.header("Escenario")
cli = st.sidebar.slider("Clientes por día", 30, 200,
      int(sales.loc[sales.scenario=="Moderado","clients_per_day"]), 5)
tic = st.sidebar.slider("Ticket promedio (ARS)", 3000, 8000,
      int(sales.loc[sales.scenario=="Moderado","ticket_ars"]), 100)
inf = st.sidebar.number_input("Inflación anual (%)", 0.0, 200.0, 0.0, 1.0)

st.markdown("""
<style>
.kpi-row { display:flex; gap:16px; margin-bottom:8px; }
.kpi-custom {
  flex:1;
  border:2px solid var(--azul)!important;
  border-radius:10px;
  background:#fff;
  box-shadow:0 2px 6px #0003;
  padding:8px 12px;
  text-align:center;
}
.kpi-custom .kpi-label {
  margin:0;
  font-size:14px;
  color:#555;
  font-weight:600;
}
.kpi-custom .kpi-value {
  margin:4px 0 0;
  font-size:20px;
  font-weight:bold;
  color:#000;
}
</style>
""", unsafe_allow_html=True)


# ────── KPI
ventas   = cli * tic * WD
insumos  = ventas * INS_PCT
ganancia = ventas - (insumos + FIXED)
payback  = "∞" if ganancia <= 0 else INV / ganancia

# ─── KPI — tarjetas HTML personalizadas (sin “None”) ───
ventas_text = f"${ventas:,.0f}"
ganancia_text = f"${ganancia:,.0f}"
payback_text = "No rentable" if payback=="∞" else f"{payback:.1f}"

st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-custom">
    <p class="kpi-label">Ventas mensuales</p>
    <p class="kpi-value">{ventas_text}</p>
  </div>
  <div class="kpi-custom">
    <p class="kpi-label">Ganancia mensual</p>
    <p class="kpi-value">{ganancia_text}</p>
  </div>
  <div class="kpi-custom">
    <p class="kpi-label">Pay-back (meses)</p>
    <p class="kpi-value">{payback_text}</p>
  </div>
</div>
""", unsafe_allow_html=True)


# ────── Gráfico flujo acumulado
mes = np.arange(1,25)
serie = ganancia * (1 + inf/100) ** (mes / 12)
flujo = np.cumsum(serie) - INV
fig, ax = plt.subplots(figsize=(11, 2.3))
ax.plot(mes, flujo, color="#1F4E79", lw=2)
ax.axhline(0, color="#888", lw=.8, ls="--")
ax.set_xlabel("Mes"); ax.set_ylabel("Flujo acumulado (ARS)")
ax.set_title("Proyección 24 meses", color="#14406b", weight="bold")
st.pyplot(fig, use_container_width=False)
st.caption("Datos fuente · Julio 2025 – Civic Twin™")

# Oculta por completo la etiqueta delta (texto y flecha) de TODAS las métricas
st.markdown(
    """
    <style>
    /* oculta la cajita delta (None) en cualquier tag */
[data-testid="stMetricDelta"]{display:none !important;}
/* oculta el primer div (delta) dentro de cada tarjeta KPI */
div[data-testid="stMetric"] > div:first-child{display:none !important;}
 </style>
    """,
    unsafe_allow_html=True
)
# ——— Inmediatamente después de tu header_html (o al final del archivo) ———
st.markdown("""
<style>
  /* Esconde el primer hijo de cada .stMetric (la cajita delta con “None”) */
  .stMetric > div:first-child {
    display: none !important;
  }
</style>
""", unsafe_allow_html=True)

