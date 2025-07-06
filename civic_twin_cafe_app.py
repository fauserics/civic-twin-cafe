import streamlit as st, pandas as pd, numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

st.set_page_config(page_title="Cafetería Quilmes | Civic Twin", layout="wide")

#──────── Logo SVG
SVG_LOGO="""<svg width="32" height="32" viewBox="0 0 64 64" fill="none"
xmlns="http://www.w3.org/2000/svg"
style="vertical-align:middle;margin-right:8px"><circle cx="24" cy="32" r="18"
stroke="white" stroke-width="6" fill="none"/><circle cx="40" cy="32" r="18"
stroke="white" stroke-width="6" fill="none"/></svg>"""

#──────── CSS global (header + layout full-viewport)
CSS="""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');
:root{
  --topbar:42px; --header:70px; --sidebar:300px; --azul:#1F4E79;
}
/* body sin scroll */
html,body{height:100vh!important; overflow-y:hidden;}
/* header */
.header{position:fixed; top:var(--topbar); left:0; width:100%;
  height:var(--header); z-index:100;
  background:linear-gradient(90deg,#14406b 0%,var(--azul) 100%);
  display:flex; align-items:center; justify-content:center; padding:0 16px;}
.header-left{position:absolute; left:0; width:var(--sidebar);
  display:flex; align-items:center; justify-content:center;}
.header-title{font:700 30px 'Montserrat',sans-serif; color:#fff;}
.flag{position:absolute; right:16px; height:32px; border-radius:3px;}
/* empujo layout principal */
section[data-testid=stSidebar]{margin-top:calc(var(--topbar)+var(--header));}
div.block-container{
  margin-top:calc(var(--topbar)+var(--header)+8px);
  height:calc(100vh - var(--topbar) - var(--header) - 16px);
  display:flex; flex-direction:column;
}
/* fila KPI fija y gráfico flexible */
.kpi-row{flex:none;}
.graph-row{flex:1 1 0; }
/* KPI cards */
.stMetric>div{border:2px solid var(--azul)!important;border-radius:10px;
  background:#fff;box-shadow:0 2px 6px #0003;padding:12px 8px;}
/* sliders / sidebar */
input[type=range]::-webkit-slider-runnable-track{background:var(--azul)33}
input[type=range]::-webkit-slider-thumb{background:var(--azul);border:none}
input[type=range]::-moz-range-track{background:var(--azul)33}
input[type=range]::-moz-range-thumb{background:var(--azul);border:none}
section[data-testid=stSidebar]{background:#eaf0f7;}
</style>
"""

FLAG="https://flagcdn.com/w40/ar.png"
st.markdown(
  CSS+
  f"""<div class='header'>
        <div class='header-left'>{SVG_LOGO}
          <span style='font:600 20px Montserrat,sans-serif;color:#d0e1ff'>Civic&nbsp;Twin</span>
        </div>
        <span class='header-title'>Cafetería Quilmes</span>
        <img src='{FLAG}' class='flag'>
      </div>""", unsafe_allow_html=True)

#──────── Datos (sin cambios)
BASE=Path(__file__).parent
CSV,XLSX=BASE/'CivicTwin_Cafe_Quilmes_Data.csv',BASE/'CivicTwin_Cafe_Quilmes_Data.xlsx'
@st.cache_data
def load():
    if CSV.exists(): return {"tidy":pd.read_csv(CSV)}
    if XLSX.exists(): return pd.read_excel(XLSX,sheet_name=None)
    st.error("Dataset faltante"); return {}
d=load(); st.stop() if not d else None
if "tidy" in d:
    t=d["tidy"]
    init=t[t.dataset=="initial_costs"]; month=t[t.dataset=="monthly_costs"]
    sales=t[t.dataset=="sales_scenarios"]; ass=t[t.dataset=="assumptions"]
else:
    init=d["initial_costs"]; month=d["monthly_costs"]; sales=d["sales_scenarios"]; ass=d["assumptions"]
ASS=dict(zip(ass.variable,ass.value))
WD=int(ASS.get("working_days_per_month",26))
INS=float(ASS.get("insumos_percent_of_sales",0.30))
INV=init.cost_ars.sum(); FIX=month.cost_ars.sum()

#──────── Sidebar
st.sidebar.header("Escenario")
cli=st.sidebar.slider("Clientes por día",30,200,
      int(sales.loc[sales.scenario=="Moderado","clients_per_day"]),5)
tic=st.sidebar.slider("Ticket promedio (ARS)",3000,8000,
      int(sales.loc[sales.scenario=="Moderado","ticket_ars"]),100)
inf=st.sidebar.number_input("Inflación anual (%)",0.0,200.0,0.0,1.0)

#──────── KPI + layout
vent=cli*tic*WD; ins=vent*INS; gan=vent-(ins+FIX); pay="∞" if gan<=0 else INV/gan
kpi=st.container(); kpi.markdown("<div class='kpi-row'>",unsafe_allow_html=True)
c1,c2,c3=kpi.columns(3)
c1.metric("Ventas mensuales",f"${vent:,.0f}")
c2.metric("Ganancia mensual",f"${gan:,.0f}")
c3.metric("Pay-back (meses)","No rentable" if pay=="∞" else f"{pay:.1f}")
kpi.markdown("</div>",unsafe_allow_html=True)
st.divider()

#──────── Gráfico flexible
graf=st.container(); graf.markdown("<div class='graph-row'>",unsafe_allow_html=True)
mes=np.arange(1,25); serie=gan*(1+inf/100)**(mes/12); flujo=np.cumsum(serie)-INV
fig,ax=plt.subplots(figsize=(8,3))
ax.plot(mes,flujo,color="#1F4E79",lw=2); ax.axhline(0,color="#888",lw=.8,ls="--")
ax.set_xlabel("Mes"); ax.set_ylabel("Flujo acumulado (ARS)")
ax.set_title("Proyección 24 meses",color="#14406b",weight="bold")
graf.pyplot(fig,use_container_width=True)
graf.markdown("</div>",unsafe_allow_html=True)
