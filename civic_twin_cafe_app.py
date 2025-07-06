# civic_twin_cafe_app.py
# Tablero MVP · Civic Twin · Cafetería Quilmes
# Versión mock-up 2025-07-07 (b)

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

# ──────────────────────────────────────────────────────────
# Config de página
# ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Cafetería Quilmes | Civic Twin",
    layout="wide"
)

# ──────────────────────────────────────────────────────────
# HEADER  (logo SVG, títulos y bandera)
# ──────────────────────────────────────────────────────────
SVG_LOGO = """
<svg width="48" height="48" viewBox="0 0 64 64" fill="none"
     xmlns="http://www.w3.org/2000/svg"
     style="vertical-align:middle;margin-right:12px">
  <circle cx="24" cy="32" r="18"
          stroke="white" stroke-width="6" fill="none"/>
  <circle cx="40" cy="32" r="18"
          stroke="white" stroke-width="6" fill="none"/>
</svg>
"""

HEADER_CSS = """
<style>
/* Google Font */
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');

/*********  HEADER *********/
.header-bar{
    background:linear-gradient(90deg,#14406b 0%,#1F4E79 100%);
    border-radius:12px;
    padding:10px 20px;
    margin-bottom:16px;
    display:flex;
    align-items:center;
    justify-content:space-between;
}
.header-left{display:flex;align-items:center;gap:14px}
.proj-title{
    font-family:'Montserrat',sans-serif;
    font-size:34px;font-weight:700;
    color:#ffffff;margin:0
}
.proj-sub{
    font-family:'Montserrat',sans-serif;
    font-size:20px;font-weight:400;
    color:#d0e1ff;margin:0 0 0 12px
}
.flag{height:34px;border-radius:3px}

/*********  KPI CARDS *********/
.stMetric>div{
    border:2px solid #1F4E79 !important;
    border-radius:10px;
    background:#ffffff;
    box-shadow:0 2px 6px #00000014;
    padding:12px 8px;
}

/*********  SLIDERS (todos los navegadores) *********/
input[type=range]::-webkit-slider-runnable-track{background:#1F4E7933}
input[type=range]::-webkit-slider-thumb{background:#1F4E79;border:none}
input[type=range]::-moz-range-track{background:#1F4E7933}
input[type=range]::-moz-range-thumb{background:#1F4E79;border:none}

/*********  SIDEBAR *********/
section[data-testid=stSidebar]{background:#eaf0f7}
</style>
"""

FLAG_AR = "https://flagcdn.com/w40/ar.png"

header_html = f"""
{HEADER_CSS}
<div class='header-bar'>
  <div class='header-left'>
    {SVG_LOGO}
    <h1 class='proj-title'>Cafetería Quilmes</h1>
    <h2 class='proj-sub'>Civic Twin</h2>
  </div>
  <img src='{FLAG_AR}' class='flag'>
</div>
"""

st.markdown(header_html, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────
# Lectura de datos (CSV ó Excel)
# ──────────────────────────────────────────────────────────
BASE  = Path(__file__).parent
CSV   = BASE / "CivicTwin_Cafe_Quilmes_Data.csv"
XLSX  = BASE / "CivicTwin_Cafe_Quilmes_Data.xlsx"

@st.cache_data
def load_data():
    if CSV.exists():
        tidy = pd.read_csv(CSV)
        return {"tidy": tidy}
    if XLSX.exists():
        return pd.read_excel(XLSX, sheet_name=None)
    st.error("No se encontró ni el CSV ni el Excel de datos.")
    return {}

data = load_data()
if not data:
    st.stop()

if "tidy" in data:         # archivo largo "tidy"
    tidy       = data["tidy"]
    init_df    = tidy[tidy.dataset=="initial_costs"]
    month_df   = tidy[tidy.dataset=="monthly_costs"]
    sales_df   = tidy[tidy.dataset=="sales_scenarios"]
    assump_df  = tidy[tidy.dataset=="assumptions"]
else:                       # multi-sheet Excel
    init_df    = data["initial_costs"]
    month_df   = data["monthly_costs"]
    sales_df   = data["sales_scenarios"]
    assump_df  = data["assumptions"]

ASSUMP      = dict(zip(assump_df.variable, assump_df.value))
WORK_DAYS   = int(ASSUMP.get("working_days_per_month", 26))
INSUM_PCT   = float(ASSUMP.get("insumos_percent_of_sales", 0.30))
INV_TOTAL   = init_df.cost_ars.sum()
FIXED_COSTS = month_df.cost_ars.sum()

# ──────────────────────────────────────────────────────────
# Sidebar – escenario interactivo
# ──────────────────────────────────────────────────────────
st.sidebar.header("Escenario")
clients_day = st.sidebar.slider(
    "Clientes por día", 30, 200,
    int(sales_df.loc[sales_df.scenario=="Moderado","clients_per_day"]),
    5
)
ticket_avg  = st.sidebar.slider(
    "Ticket promedio (ARS)", 3000, 8000,
    int(sales_df.loc[sales_df.scenario=="Moderado","ticket_ars"]),
    100
)
inflacion   = st.sidebar.number_input(
    "Inflación anual (%)", 0.0, 200.0, 0.0, 1.0
)

# ──────────────────────────────────────────────────────────
# Cálculos
# ──────────────────────────────────────────────────────────
ventas_m   = clients_day * ticket_avg * WORK_DAYS
costo_ins  = ventas_m * INSUM_PCT
ganancia_m = ventas_m - (costo_ins + FIXED_COSTS)
payback    = "∞" if ganancia_m<=0 else INV_TOTAL/ganancia_m

# ──────────────────────────────────────────────────────────
# KPI
# ──────────────────────────────────────────────────────────
col1,col2,col3 = st.columns(3)
col1.metric("Ventas mensuales", f"${ventas_m:,.0f}")
col2.metric("Ganancia mensual", f"${ganancia_m:,.0f}")
col3.metric("Pay-back (meses)",
            "No rentable" if payback=="∞" else f"{payback:.1f}")

st.divider()

# ──────────────────────────────────────────────────────────
# Gráfico flujo acumulado 24 m
# ──────────────────────────────────────────────────────────
meses  = np.arange(1,25)
serie  = ganancia_m * (1+inflacion/100)**(meses/12)
flujo  = np.cumsum(serie) - INV_TOTAL

fig,ax = plt.subplots()
ax.plot(meses, flujo, color="#1F4E79", lw=2)
ax.axhline(0, color="#888", lw=.8, ls="--")
ax.set_xlabel("Mes")
ax.set_ylabel("Flujo acumulado (ARS)")
ax.set_title("Proyección 24 meses", color="#14406b", weight="bold")
st.pyplot(fig)

st.caption("Datos fuente: CivicTwin_Cafe_Quilmes_Data · Julio 2025")
