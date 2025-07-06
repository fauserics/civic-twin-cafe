import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import base64, textwrap

# ╔══════════════════════════════════════╗
# ║  CONFIGURACIÓN VISUAL – VERSIÓN 2.0  ║
# ╚══════════════════════════════════════╝
PRIMARY         = "#0C365A"   # Navy profundo (mock‑up)
PRIMARY_LIGHT   = "#1F4E79"   # azul medio slider
BG_MAIN         = "#FFFFFF"
BG_CARD         = "#F5F8FC"   # cards / KPI
BORDER_CARD     = "#0C365A22" # navy 13% opacidad
FONT_TITLE      = "34px"
FONT_SUBTITLE   = "20px"

st.set_page_config(page_title="Cafetería Quilmes | Civic Twin", layout="wide")

# -----------------------------------------------------------------------------
# CSS GLOBAL (mock‑up fidelity)
# -----------------------------------------------------------------------------
mock_css = f"""
<style>
html, body {{ background:{BG_MAIN}; }}
/* Remover padding top default */
#main > div:first-child {{ padding-top:0rem; }}

/* Encabezado full‑width barra */
.civic-header {{
  width:100%;
  background:{PRIMARY};
  padding:14px 32px;
  display:flex;
  justify-content:space-between;
  align-items:center;
  margin-bottom:24px;
}}

.civic-header .titles {{ display:flex; align-items:center; gap:16px; color:#fff; }}
.civic-header .titles .title  {{ font-size:{FONT_TITLE}; font-weight:600; }}
.civic-header .titles .subtitle {{ font-size:{FONT_SUBTITLE}; font-weight:400; opacity:.9; }}

/* KPI cards */
[data-testid="stMetric"] > div {{
  background:{BG_CARD};
  border:1px solid {BORDER_CARD};
  border-radius:10px;
  padding:12px 16px;
}}
[data-testid="stMetricLabel"] {{ font-size:15px; }}
[data-testid="stMetricValue"] {{ font-size:28px; }}

/* Slider knob + track */
div[data-baseweb="slider"] [role="slider"] {{ background:{PRIMARY_LIGHT}; }}
div[data-baseweb="slider"] > div > div {{ background:{PRIMARY_LIGHT}; }}

/* Sidebar title color */
[data-testid="stSidebarHeader"] h2 {{ color:{PRIMARY}; }}
</style>
"""

st.markdown(mock_css, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# ENCABEZADO (HTML)
# -----------------------------------------------------------------------------
logo_tag = "<div style='width:48px;height:48px;border-radius:50%;background:#ddd;display:flex;align-items:center;justify-content:center;font-weight:700;'>?</div>"
logo_path = Path(__file__).parent / "civictwin_logo.png"
if logo_path.exists():
    logo_b64 = base64.b64encode(logo_path.read_bytes()).decode()
    logo_tag = f"<img src='data:image/png;base64,{logo_b64}' style='height:48px;'>"

header_html = f"""
<div class='civic-header'>
  <div class='titles'>
    {logo_tag}
    <span class='title'>Cafetería&nbsp;Quilmes</span>
    <span class='subtitle'>Civic&nbsp;Twin</span>
  </div>
  <img src='https://flagcdn.com/w40/ar.png' style='height:30px;border-radius:2px;'>
</div>
"""

st.markdown(header_html, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# CARGA DATOS (igual que antes)
# -----------------------------------------------------------------------------
BASE = Path(__file__).parent
CSV  = BASE / "CivicTwin_Cafe_Quilmes_Data.csv"
XLSX = BASE / "CivicTwin_Cafe_Quilmes_Data.xlsx"
@st.cache_data
def load():
    if CSV.exists():
        return {"tidy": pd.read_csv(CSV)}
    elif XLSX.exists():
        return pd.read_excel(XLSX, sheet_name=None)
    st.error("Archivo de datos no encontrado"); return {}

data = load();
if not data: st.stop()

if "tidy" in data:
    tidy = data["tidy"]; DS=lambda n: tidy[tidy["dataset"]==n]
    init_df, month_df, sales_df, assump_df = map(DS,["initial_costs","monthly_costs","sales_scenarios","assumptions"])
else:
    init_df   = data["initial_costs"]
    month_df  = data["monthly_costs"]
    sales_df  = data["sales_scenarios"]
    assump_df = data["assumptions"]

ASSUMP = dict(zip(assump_df["variable"], assump_df["value"]))
WORK, PCT = int(ASSUMP.get("working_days_per_month",26)), float(ASSUMP.get("insumos_percent_of_sales",0.30))
INV, FIXED = init_df["cost_ars"].sum(), month_df["cost_ars"].sum()

def defval(col): return int(sales_df.loc[sales_df["scenario"]=="Moderado",col].iloc[0])

# -----------------------------------------------------------------------------
# SIDEBAR CONTROLES
# -----------------------------------------------------------------------------
st.sidebar.header("Escenario")
clients = st.sidebar.slider("Clientes por día",30,200,defval("clients_per_day"),5)
ticket  = st.sidebar.slider("Ticket promedio (ARS)",3000,8000,defval("ticket_ars"),100)
infl    = st.sidebar.number_input("Inflación anual (%)",0.0,200.0,0.0,1.0)

# -----------------------------------------------------------------------------
# KPI
# -----------------------------------------------------------------------------
sales   = clients*ticket*WORK
insumos = sales*PCT
profit  = sales - (insumos+FIXED)
payback = "∞" if profit<=0 else INV/profit

k1,k2,k3 = st.columns(3)
k1.metric("Ventas mensuales",f"${sales:,.0f}")
k2.metric("Ganancia mensual",f"${profit:,.0f}")
k3.metric("Pay‑back (meses)","No rentable" if payback=="∞" else f"{payback:.1f}")

st.divider()

# -----------------------------------------------------------------------------
# GRÁFICO
# -----------------------------------------------------------------------------
months = np.arange(1,25)
series  = profit*(1+infl/100)**(months/12)
cum     = np.cumsum(series)-INV
fig,ax  = plt.subplots(); ax.plot(months,cum,color=PRIMARY_LIGHT)
ax.axhline(0,color="#999",lw=.8,ls="--"); ax.set_xlabel("Mes"); ax.set_ylabel("Flujo acumulado (ARS)")
ax.set_title("Proyección 24 meses",color=PRIMARY_LIGHT)
st.pyplot(fig)

# -----------------------------------------------------------------------------
# TABLA RESUMEN
# -----------------------------------------------------------------------------
summary = pd.DataFrame({"Concepto":["Ventas","Insumos","Costos fijos","Ganancia"],"ARS":[sales,insumos,FIXED,profit]})
summary["ARS"] = summary["ARS"].apply(lambda x:f"${x:,.0f}")
st.subheader("Resumen mensual"); st.dataframe(summary,hide_index=True,use_container_width=True)

st.caption("Civic Twin · Cafetería Quilmes · 07‑Jul‑2025")
