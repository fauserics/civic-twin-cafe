# civic_twin_cafe_app.py
# Tablero MVP · Civic Twin · Cafetería Quilmes
# Versión 2025-07-07 – Header azul con logo + bandera

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import base64
import matplotlib.pyplot as plt

# ─── CONFIG BÁSICA ──────────────────────────────────────────
st.set_page_config(
    page_title="Cafetería Quilmes | Civic Twin",
    layout="wide"
)

# ─── UTIL: LOGO A BASE64 ───────────────────────────────────
def embed_logo(png_path: Path, height_px: int = 48) -> str:
    if not png_path.exists():
        # placeholder grey circle
        return f"<div style='width:{height_px}px;height:{height_px}px;border-radius:50%;background:#bdbdbd;display:inline-block;'></div>"
    b64 = base64.b64encode(png_path.read_bytes()).decode()
    return (
        f"<img src='data:image/png;base64,{b64}' "
        f"height='{height_px}' style='vertical-align:middle;margin-right:12px;'>"
    )

LOGO_HTML = embed_logo(Path(__file__).parent / "civictwin_logo.png")

# ─── HEADER CUSTOM HTML/CSS ─────────────────────────────────
HEADER_CSS = """
<style>
/* header contenedor */
.header-bar{
    background: linear-gradient(90deg,#14406b 0%, #1F4E79 100%);
    border-radius:10px;
    padding:8px 16px;
    margin-bottom:10px;
    display:flex;
    align-items:center;
    justify-content:space-between;
}
.header-left{
    display:flex;
    align-items:center;
    gap:8px;
}
.proj-title{
    font-size:34px;
    font-weight:700;
    color:#ffffff;
    margin:0;
}
.proj-sub{
    font-size:20px;
    font-weight:400;
    color:#d0e1ff;
    margin:0 0 0 12px;
}
.flag{
    height:34px;
    border-radius:3px;
}
</style>
"""

FLAG_AR = "https://flagcdn.com/w40/ar.png"

header_html = f"""
{HEADER_CSS}
<div class='header-bar'>
  <div class='header-left'>
    {LOGO_HTML}
    <h1 class='proj-title'>Cafetería Quilmes</h1>
    <h2 class='proj-sub'>Civic Twin</h2>
  </div>
  <img src='{FLAG_AR}' class='flag'>
</div>
"""

st.markdown(header_html, unsafe_allow_html=True)

# ─── CARGA DE DATOS (Excel o CSV) ──────────────────────────
BASE = Path(__file__).parent
CSV = BASE / "CivicTwin_Cafe_Quilmes_Data.csv"
XLSX = BASE / "CivicTwin_Cafe_Quilmes_Data.xlsx"

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

if "tidy" in data:
    tidy = data["tidy"]
    init_df   = tidy[tidy["dataset"]=="initial_costs"]
    month_df  = tidy[tidy["dataset"]=="monthly_costs"]
    sales_df  = tidy[tidy["dataset"]=="sales_scenarios"]
    assump_df = tidy[tidy["dataset"]=="assumptions"]
else:
    init_df   = data["initial_costs"]
    month_df  = data["monthly_costs"]
    sales_df  = data["sales_scenarios"]
    assump_df = data["assumptions"]

ASSUMP      = dict(zip(assump_df["variable"], assump_df["value"]))
WORK_DAYS   = int(ASSUMP.get("working_days_per_month",26))
INSUMOS_PCT = float(ASSUMP.get("insumos_percent_of_sales",0.30))
INV_TOTAL   = init_df["cost_ars"].sum()
FIXED_COSTS = month_df["cost_ars"].sum()

# ─── SIDEBAR (ESCENARIO) ───────────────────────────────────
st.sidebar.header("Escenario")
clients_per_day = st.sidebar.slider(
    "Clientes por día", 30, 200,
    int(sales_df.loc[sales_df["scenario"]=="Moderado","clients_per_day"]),
    5
)
ticket_avg = st.sidebar.slider(
    "Ticket promedio (ARS)", 3000, 8000,
    int(sales_df.loc[sales_df["scenario"]=="Moderado","ticket_ars"]),
    100
)
inflacion = st.sidebar.number_input(
    "Inflación anual (%)", 0.0, 200.0, 0.0, 1.0
)

# ─── CÁLCULOS ───────────────────────────────────────────────
ventas_mens = clients_per_day * ticket_avg * WORK_DAYS
costo_insumos = ventas_mens * INSUMOS_PCT
ganancia_mens = ventas_mens - (costo_insumos + FIXED_COSTS)
payback = "∞" if ganancia_mens<=0 else INV_TOTAL/ganancia_mens

# ─── KPI CARDS ─────────────────────────────────────────────
k1,k2,k3 = st.columns(3)
k1.metric("Ventas mensuales", f"${ventas_mens:,.0f}")
k2.metric("Ganancia mensual", f"${ganancia_mens:,.0f}")
k3.metric("Pay-back (meses)", "No rentable" if payback=="∞" else f"{payback:.1f}")

st.divider()

# ─── GRÁFICO FLUJO 24 MESES ───────────────────────────────
meses = np.arange(1,25)
serie_gan = ganancia_mens * (1+inflacion/100)**(meses/12)
flujo = np.cumsum(serie_gan) - INV_TOTAL

fig,ax = plt.subplots()
ax.plot(meses, flujo, color="#14406b", lw=2)
ax.axhline(0, lw=.8, ls="--", color="#666")
ax.set_xlabel("Mes"); ax.set_ylabel("Flujo (ARS)")
ax.set_title("Proyección 24 meses", color="#14406b", weight="bold")
st.pyplot(fig)
