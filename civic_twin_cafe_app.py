import streamlit as st, pandas as pd, numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

# ─────────  BÁSICO  ─────────────────────────────────────────────
st.set_page_config(page_title="Cafetería Quilmes | Civic Twin™",
                   layout="wide", initial_sidebar_state="expanded")

# ─────────  HEADER (igual a la versión buena)  ─────────────────
SVG_LOGO = """<svg width="32" height="32" viewBox="0 0 64 64" fill="none"
xmlns="http://www.w3.org/2000/svg"
style="vertical-align:middle;margin-right:8px"><circle cx="24" cy="32" r="18"
stroke="white" stroke-width="6" fill="none"/><circle cx="40" cy="32" r="18"
stroke="white" stroke-width="6" fill="none"/></svg>"""
FLAG = "https://flagcdn.com/w40/ar.png"

BASE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');
:root{--header-h:72px;--sidebar-w:300px;--azul:#1F4E79;}

html,body,#root{height:100vh;overflow:hidden;}

.header-bar{position:fixed;top:0;left:0;right:0;height:var(--header-h);
  background:linear-gradient(90deg,#14406b 0%,var(--azul) 100%);
  display:flex;align-items:center;justify-content:center;padding:0 16px;z-index:100;}
.header-left{position:absolute;left:0;width:var(--sidebar-w);
  display:flex;align-items:center;justify-content:center;}
.header-left span{font:600 18px 'Montserrat',sans-serif;color:#d0e1ff;}
.header-title{font:700 30px 'Montserrat',sans-serif;color:#fff;}
.header-flag{position:absolute;right:16px;height:32px;border-radius:3px;}

section[data-testid="stSidebar"]{margin-top:var(--header-h);background:#eaf0f7;}
div.block-container{margin-top:calc(var(--header-h)+2px)!important;
  height:calc(100vh - var(--header-h) - 2px);
  display:flex;flex-direction:column;overflow:hidden;}

.kpi-row{flex:none;}
.graph-row{flex:1 1 0;overflow:hidden;}

/* — MINI-KPI — */
div[data-testid="stMetric"]{padding:2px 4px!important;border:none!important;
  border-radius:8px!important;box-shadow:none!important;}
div[data-testid="stMetric"]>label div{font-size:13px!important;line-height:15px!important}
div[data-testid="stMetric"]>div:nth-child(2) span{font-size:18px!important;line-height:20px!important}

/* — Gráfico máx 200 px — */
.graph-row svg,.graph-row canvas{max-height:200px!important}

/* Oculta p vacío que mostraba “nono” */
div.block-container>p:first-child{display:none!important;margin:0!important}
</style>
"""
st.markdown(BASE_CSS, unsafe_allow_html=True)
st.markdown(f"""
<div class='header-bar'>
  <div class='header-left'>{SVG_LOGO}<span>Civic Twin™</span></div>
  <span class='header-title'>Cafetería Quilmes</span>
  <img src='{FLAG}' class='header-flag'>
</div>""", unsafe_allow_html=True)

# ─────────  DATOS  (sin cambios)  ────────────────────────────
BASE=Path(__file__).parent
CSV,XLSX=BASE/'CivicTwin_Cafe_Quilmes_Data.csv',BASE/'CivicTwin_Cafe_Quilmes_Data.xlsx'
@st.cache_data
def load():
    if CSV.exists(): return {"tidy":pd.read_csv(CSV)}
    if XLSX.exists(): return pd.read_excel(XLSX,sheet_name=None)
    st.error("Dataset faltante"); return {}
d=load(); st.stop() if not d else None
if "tidy" in d:
    t=d["tidy"]; init=t[t.dataset=="initial_costs"]; month=t[t.dataset=="monthly_costs"]
    sales=t[t.dataset=="sales_scenarios"]; ass=t[t.dataset=="assumptions"]
else:
    init=d["initial_costs"]; month=d["monthly_costs"]; sales=d["sales_scenarios"]; ass=d["assumptions"]
ASS=dict(zip(ass.variable,ass.value))
WD=int(ASS.get("working_days_per_month",26))
INS=float(ASS.get("insumos_percent_of_sales",0.30))
INV=init.cost_ars.sum(); FIX=month.cost_ars.sum()

# ─────────  SIDEBAR  ─────────────────────────────────────────
st.sidebar.header("Escenario")
cli=st.sidebar.slider("Clientes por día",30,200,
      int(sales.loc[sales.scenario=="Moderado","clients_per_day"]),5)
tic=st.sidebar.slider("Ticket promedio (ARS)",3000,8000,
      int(sales.loc[sales.scenario=="Moderado","ticket_ars"]),100)
inf=st.sidebar.number_input("Inflación anual (%)",0.0,200.0,0.0,1.0)

# ─────────  KPI  ────────────────────────────────────────────
ventas=cli*tic*WD; ins=ventas*INS; gan=ventas-(ins+FIX); pay="∞" if gan<=0 else INV/gan
kpi=st.container(); kpi.markdown("<div class='kpi-row'>", unsafe_allow_html=True)
c1,c2,c3=kpi.columns(3)
c1.metric("Ventas mensuales",f"${ventas:,.0f}")
c2.metric("Ganancia mensual",f"${gan:,.0f}")
c3.metric("Pay-back (meses)","No rentable" if pay=="∞" else f"{pay:.1f}")
kpi.markdown("</div>", unsafe_allow_html=True)
st.markdown("<hr style='margin:4px 0;border:none;border-top:1px solid #ddd;'>",
            unsafe_allow_html=True)

# ─────────  GRÁFICO  ────────────────────────────────────────
graf=st.container(); graf.markdown("<div class='graph-row'>", unsafe_allow_html=True)
fig,ax=plt.subplots(figsize=(6,2.0))   # 200 px alto aprox
mes=np.arange(1,25); flujo=np.cumsum(gan*(1+inf/100)**(mes/12))-INV
ax.plot(mes,flujo,color="#1F4E79",lw=2); ax.axhline(0,color="#888",lw=.8,ls="--")
ax.set_xlabel("Mes"); ax.set_ylabel("Flujo acumulado (ARS)")
ax.set_title("Proyección 24 meses",color="#14406b",weight="bold",fontsize=18)
graf.pyplot(fig,use_container_width=True)
graf.markdown("</div>", unsafe_allow_html=True)
