import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import base64, textwrap

# ──────────────────────────────────────────────
# CONFIG BÁSICA & PALETA
# ──────────────────────────────────────────────
PRIMARY      = "#103B61"          # Azul más profundo (navy)
PRIMARY_LIGHT= "#1F4E79"          # Azul medio
BG_MAIN      = "#FFFFFF"
BG_CARD      = "#F2F6FA"

st.set_page_config(page_title="Cafetería Quilmes | Civic Twin", layout="wide")

# CSS GLOBAL
st.markdown(textwrap.dedent(f"""
<style>
html, body {{ background:{BG_MAIN}; }}
/* ENCABEZADO FULL WIDTH */
#main > div:first-child {{ padding-top:0; }}  /* borra espacio default */

/* Tipografías */
h1,h2,h3,h4,h5,h6 {{ color:{BG_MAIN}; margin:0; }}

/* Tarjetas KPI */
[data-testid="stMetric"] > div {{
  background:{BG_CARD};
  border:2px solid {PRIMARY_LIGHT};
  border-radius:12px;
  padding:10px 14px;
}}

/* Slider colores */
div[data-baseweb="slider"] [role="slider"] {{ background:{PRIMARY_LIGHT}; }}
div[data-baseweb="slider"] > div > div {{ background:{PRIMARY_LIGHT}; }}

/* Sidebar */
[data-testid="stSidebarHeader"] h2 {{ color:{PRIMARY_LIGHT}; }}
</style>
"""), unsafe_allow_html=True)

# ──────────────────────────────────────────────
# HEADER (NAVBAR) - estilo mock‑up
# ──────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
logo_path = BASE_DIR / "civictwin_logo.png"
if logo_path.exists():
    logo_b64 = base64.b64encode(logo_path.read_bytes()).decode()
    logo_html = f"<img src='data:image/png;base64,{logo_b64}' style='height:48px;'>"
else:
    logo_html = "<div style='height:48px;width:48px;border-radius:50%;background:#ccc;display:flex;align-items:center;justify-content:center;font-weight:600;'>?</div>"

header_html = f"""
<div style='width:100%;background:{PRIMARY_LIGHT};padding:12px 32px;border-radius:8px;display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;'>
  <div style='display:flex;align-items:center;gap:20px;'>
    {logo_html}
    <span style='font-size:34px;font-weight:700;color:#fff;'>Cafetería&nbsp;Quilmes</span>
    <span style='font-size:20px;font-weight:400;color:#ffffffb3;'>Civic&nbsp;Twin</span>
  </div>
  <img src='https://flagcdn.com/w40/ar.png' style='height:30px;border-radius:2px;'>
</div>
"""

st.markdown(header_html, unsafe_allow_html=True)

# ──────────────────────────────────────────────
# CARGA DE DATOS
# ──────────────────────────────────────────────
CSV = BASE_DIR / "CivicTwin_Cafe_Quilmes_Data.csv"
XLSX = BASE_DIR / "CivicTwin_Cafe_Quilmes_Data.xlsx"
@st.cache_data
def load():
    if CSV.exists():
        return {"tidy": pd.read_csv(CSV)}
    elif XLSX.exists():
        return pd.read_excel(XLSX, sheet_name=None)
    else:
        st.stop()

data = load()
if "tidy" in data:
    tidy = data["tidy"]
    DS   = lambda n: tidy[tidy["dataset"]==n]
    init_df, month_df, sales_df, assump_df = map(DS,["initial_costs","monthly_costs","sales_scenarios","assumptions"])
else:
    init_df   = data["initial_costs"]
    month_df  = data["monthly_costs"]
    sales_df  = data["sales_scenarios"]
    assump_df = data["assumptions"]

ASSUMP = dict(zip(assump_df["variable"], assump_df["value"]))
WORK   = int(ASSUMP.get("working_days_per_month",26))
PCT    = float(ASSUMP.get("insumos_percent_of_sales",0.30))
INV    = init_df["cost_ars"].sum()
FIXED  = month_df["cost_ars"].sum()

def defval(col):
    return int(sales_df.loc[sales_df["scenario"]=="Moderado", col].iloc[0])

# ──────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────
st.sidebar.header("Escenario")
clients = st.sidebar.slider("Clientes por día",30,200,defval("clients_per_day"),5,format="%d")
ticket  = st.sidebar.slider("Ticket promedio (ARS)",3000,8000,defval("ticket_ars"),100,format="%d")
infl    = st.sidebar.number_input("Inflación anual (%)",0.0,200.0,0.0,1.0,format="%.1f")

# CÁLCULOS
sales   = clients*ticket*WORK
insumos = sales*PCT
profit  = sales-(insumos+FIXED)
payback = "∞" if profit<=0 else INV/profit

k1,k2,k3=st.columns(3)
k1.metric("Ventas mensuales",f"${sales:,.0f}")
k2.metric("Ganancia mensual",f"${profit:,.0f}")
k3.metric("Pay-back (meses)","No rentable" if payback=="∞" else f"{payback:.1f}")

st.divider()

# GRÁFICO
months=np.arange(1,25)
series=profit*(1+infl/100)**(months/12)
cum=np.cumsum(series)-INV
fig,ax=plt.subplots()
ax.plot(months,cum,color=PRIMARY_LIGHT)
ax.axhline(0,color="grey",lw=0.8,ls="--")
ax.set_xlabel("Mes"); ax.set_ylabel("Flujo acumulado (ARS)")
ax.set_title("Proyección 24 meses",color=PRIMARY_LIGHT)
st.pyplot(fig)

# TABLA RESUMEN
st.subheader("Resumen mensual")
summary=pd.DataFrame({"Concepto":["Ventas","Insumos","Costos fijos","Ganancia"],"ARS":[sales,insumos,FIXED,profit]})
summary["ARS"]=summary["ARS"].apply(lambda x:f"${x:,.0f}")
st.dataframe(summary,hide_index=True,use_container_width=True)

st.caption("Civic Twin – Tablero MVP · 07‑Jul‑2025")
