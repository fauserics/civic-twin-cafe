import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import base64
from PIL import Image

# -----------------------------------------------------------------------------
# CONFIGURACIÓN BÁSICA ---------------------------------------------------------
# -----------------------------------------------------------------------------
PRIMARY   = "#1F4E79"   # Azul corporativo
BG_MAIN   = "#FFFFFF"
BG_CARD   = "#F2F6FA"

st.set_page_config(
    page_title="Cafetería Quilmes | Civic Twin",
    layout="wide"
)

# -----------------------------------------------------------------------------
# INYECCIÓN DE ESTILOS CSS -----------------------------------------------------
# -----------------------------------------------------------------------------
css = f"""
<style>
html, body {{ background-color:{BG_MAIN}; }}
h1, h2 {{ color:{PRIMARY}; margin:0; }}
[data-testid="stMetric"] > div {{
  background:{BG_CARD};
  border:2px solid {PRIMARY};
  border-radius:12px;
  padding:8px 12px;
}}
div[data-baseweb="slider"] [role="slider"] {{ background:{PRIMARY}; color:#fff; }}
div[data-baseweb="slider"] > div > div {{ background:{PRIMARY}; }}
.stButton>button {{ background:{PRIMARY}; color:#fff; border-radius:6px; }}
[data-testid="stSidebarHeader"] h2 {{ color:{PRIMARY}; }}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# ENCABEZADO (NAVBAR) ----------------------------------------------------------
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
logo_path = BASE_DIR / "civictwin_logo.png"

if logo_path.exists():
    with open(logo_path, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()
    logo_tag = f"<img src='data:image/png;base64,{logo_b64}' style='height:40px;'>"
else:
    # Placeholder
    logo_tag = "<div style='height:40px;width:40px;background:#ccc;border-radius:50%;display:flex;align-items:center;justify-content:center;'>?</div>"

header_html = f"""
<div style='background:{PRIMARY};padding:12px 24px;border-radius:8px;margin-bottom:24px;'>
  <div style='display:flex;justify-content:space-between;align-items:center;'>
    <div style='display:flex;align-items:center;gap:16px;'>
      {logo_tag}
      <span style='font-size:30px;font-weight:600;color:#fff;'>Cafetería Quilmes</span>
      <span style='font-size:22px;font-weight:400;color:#ffffffb3;'>Civic Twin</span>
    </div>
    <img src='https://flagcdn.com/w40/ar.png' style='height:28px;border-radius:2px;'>
  </div>
</div>
"""

st.markdown(header_html, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# CARGA DE DATOS ---------------------------------------------------------------
# -----------------------------------------------------------------------------
CSV_FILE   = BASE_DIR / "CivicTwin_Cafe_Quilmes_Data.csv"
EXCEL_FILE = BASE_DIR / "CivicTwin_Cafe_Quilmes_Data.xlsx"

@st.cache_data
def load():
    if CSV_FILE.exists():
        return {"tidy": pd.read_csv(CSV_FILE)}
    elif EXCEL_FILE.exists():
        return pd.read_excel(EXCEL_FILE, sheet_name=None)
    else:
        st.error("No se encontró archivo de datos (.csv o .xlsx)")
        return {}

data = load()
if not data:
    st.stop()

# Normaliza tablas
if "tidy" in data:
    tidy = data["tidy"]
    DS = lambda n: tidy[tidy["dataset"] == n]
    init_df   = DS("initial_costs")
    month_df  = DS("monthly_costs")
    sales_df  = DS("sales_scenarios")
    assump_df = DS("assumptions")
else:
    init_df   = data["initial_costs"]
    month_df  = data["monthly_costs"]
    sales_df  = data["sales_scenarios"]
    assump_df = data["assumptions"]

ASSUMP      = dict(zip(assump_df["variable"], assump_df["value"]))
WORK_DAYS   = int(ASSUMP.get("working_days_per_month", 26))
INSUMOS_PCT = float(ASSUMP.get("insumos_percent_of_sales", 0.30))
INV_TOTAL   = init_df["cost_ars"].sum()
FIXED_COSTS = month_df["cost_ars"].sum()

# -----------------------------------------------------------------------------
# SIDEBAR – CONTROLES ----------------------------------------------------------
# -----------------------------------------------------------------------------
st.sidebar.header("Escenario")

get_def = lambda col: int(sales_df.loc[sales_df["scenario"]=="Moderado", col].iloc[0])
clients_per_day = st.sidebar.slider("Clientes por día", 30, 200, get_def("clients_per_day"), 5, format="%d")
ticket_avg      = st.sidebar.slider("Ticket promedio (ARS)", 3000, 8000, get_def("ticket_ars"), 100, format="%d")
inflation       = st.sidebar.number_input("Inflación anual (%)", 0.0, 200.0, 0.0, 1.0, format="%.1f")

# -----------------------------------------------------------------------------
# CÁLCULOS --------------------------------------------------------------------
# -----------------------------------------------------------------------------
monthly_sales   = clients_per_day * ticket_avg * WORK_DAYS
cost_insumos    = monthly_sales * INSUMOS_PCT
profit_monthly  = monthly_sales - (cost_insumos + FIXED_COSTS)
payback         = "∞" if profit_monthly <= 0 else INV_TOTAL / profit_monthly

# KPIs
k1,k2,k3 = st.columns(3)
k1.metric("Ventas mensuales", f"${monthly_sales:,.0f}")
k2.metric("Ganancia mensual", f"${profit_monthly:,.0f}")
k3.metric("Pay-back (meses)", "No rentable" if payback == "∞" else f"{payback:.1f}")

st.divider()

# -----------------------------------------------------------------------------
# GRÁFICO – FLUJO ACUMULADO 24M ----------------------------------------------
# -----------------------------------------------------------------------------
months = np.arange(1, 25)
profits_series = profit_monthly * (1 + inflation/100) ** (months/12)
cumulative = np.cumsum(profits_series) - INV_TOTAL

fig, ax = plt.subplots()
ax.plot(months, cumulative, color=PRIMARY)
ax.axhline(0, color="gray", lw=0.8, ls="--")
ax.set_xlabel("Mes")
ax.set_ylabel("Flujo de caja acumulado (ARS)")
ax.set_title("Proyección 24 meses", color=PRIMARY)
st.pyplot(fig)

# -----------------------------------------------------------------------------
# TABLA RESUMEN ---------------------------------------------------------------
# -----------------------------------------------------------------------------
st.subheader("Resumen mensual")
summary = pd.DataFrame({
    "Concepto": ["Ventas", "Insumos", "Costos fijos", "Ganancia"],
    "ARS": [monthly_sales, cost_insumos, FIXED_COSTS, profit_monthly]
})
summary["ARS"] = summary["ARS"].apply(lambda x: f"${x:,.0f}")
st.dataframe(summary, hide_index=True, use_container_width=True)

st.caption("Civic Twin · Cafetería Quilmes · versión 2025‑07‑07")
