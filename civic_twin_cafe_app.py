import streamlit as st, pandas as pd, numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

# Configuración básica
st.set_page_config(page_title="Cafetería Quilmes | Civic Twin", layout="wide")

# ──────────── Logo SVG (dos círculos)
SVG_LOGO = """
<svg width="40" height="40" viewBox="0 0 64 64" fill="none"
     xmlns="http://www.w3.org/2000/svg"
     style="vertical-align:middle;margin-right:10px">
  <circle cx="24" cy="32" r="18" stroke="white" stroke-width="6" fill="none"/>
  <circle cx="40" cy="32" r="18" stroke="white" stroke-width="6" fill="none"/>
</svg>
"""

# ──────────── CSS global
HEADER_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');

/* Variables útiles */
:root{
  --header-h: 70px;
  --sidebar-w: 300px;            /* ancho sidebar default de Streamlit */
  --azul-pt:#1F4E79;
}

/* Header fijo full-width */
.header-bar{
  position:fixed; top:0; left:0; width:100%; height:var(--header-h);
  background:linear-gradient(90deg,#14406b 0%,var(--azul-pt) 100%);
  display:flex; align-items:center; justify-content:space-between;
  padding:0 20px; z-index:100;
}

/* Bloque izq (sobre sidebar) */
.header-left{
  width:var(--sidebar-w); display:flex; align-items:center; justify-content:center;
}

/* Bloque derecho (área del reporte) */
.header-right{
  flex:1; display:flex; align-items:center; justify-content:space-between;
  padding-left:12px;
}

.proj-title{font:700 28px 'Montserrat',sans-serif;color:#fff;margin:0}
.proj-sub{font:400 18px 'Montserrat',sans-serif;color:#d0e1ff;margin:0 0 0 14px}
.flag{height:32px;border-radius:3px}

/* Ajustar desplazamiento del contenido y sidebar para no quedar bajo el header */
section[data-testid="stSidebar"]{margin-top:var(--header-h);}
div.block-container{margin-top:calc(var(--header-h) + 8px);}

/* Tarjetas KPI */
.stMetric>div{border:2px solid var(--azul-pt)!important;border-radius:10px;
              background:#fff;box-shadow:0 2px 6px #0003;padding:12px 8px}

/* Sliders color */
input[type=range]::-webkit-slider-runnable-track{background:var(--azul-pt)33}
input[type=range]::-webkit-slider-thumb{background:var(--azul-pt);border:none}
input[type=range]::-moz-range-track{background:var(--azul-pt)33}
input[type=range]::-moz-range-thumb{background:var(--azul-pt);border:none}

/* Sidebar fondo */
section[data-testid=stSidebar]{background:#eaf0f7}
</style>
"""

FLAG_AR = "https://flagcdn.com/w40/ar.png"

# ──────────── Inserto header (logo + Civic Twin | título + bandera)
header_html = f"""
{HEADER_CSS}
<div class='header-bar'>
  <div class='header-left'>
    {SVG_LOGO}
    <span class='proj-sub'>Civic Twin</span>
  </div>

  <div class='header-right'>
    <span class='proj-title'>Cafetería Quilmes</span>
    <img src="{FLAG_AR}" class="flag">
  </div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

# ──────────── Carga de datos (idéntica a la versión previa)
BASE=Path(__file__).parent
CSV, XLSX = BASE/'CivicTwin_Cafe_Quilmes_Data.csv', BASE/'CivicTwin_Cafe_Quilmes_Data.xlsx'

@st.cache_data
def load():
    if CSV.exists(): return {"tidy":pd.read_csv(CSV)}
    if XLSX.exists(): return pd.read_excel(XLSX, sheet_name=None)
    st.error("Dataset no encontrado"); return {}
d=load(); 
if not d: st.stop()

if "tidy" in d:
    t=d["tidy"]
    init=t[t.dataset=="initial_costs"]; month=t[t.dataset=="monthly_costs"]
    sales=t[t.dataset=="sales_scenarios"]; ass=t[t.dataset=="assumptions"]
else:
    init=d["initial_costs"]; month=d["monthly_costs"]; sales=d["sales_scenarios"]; ass=d["assumptions"]

ASS=dict(zip(ass.variable,ass.value))
WD=int(ASS.get("working_days_per_month",26))
INS_P=float(ASS.get("insumos_percent_of_sales",0.30))
INV=init.cost_ars.sum(); FIX=month.cost_ars.sum()

# ──────────── Sidebar controles
st.sidebar.header("Escenario")
cli=st.sidebar.slider("Clientes por día",30,200,int(sales.loc[sales.scenario=="Moderado","clients_per_day"]),5)
tic=st.sidebar.slider("Ticket promedio (ARS)",3000,8000,int(sales.loc[sales.scenario=="Moderado","ticket_ars"]),100)
inf=st.sidebar.number_input("Inflación anual (%)",0.0,200.0,0.0,1.0)

# ──────────── Cálculos KPI
vent=cli*tic*WD; ins=vent*INS_P; gan=vent-(ins+FIX); pay="∞" if gan<=0 else INV/gan

c1,c2,c3=st.columns(3)
c1.metric("Ventas mensuales",f"${vent:,.0f}")
c2.metric("Ganancia mensual",f"${gan:,.0f}")
c3.metric("Pay-back (meses)","No rentable" if pay=="∞" else f"{pay:.1f}")
st.divider()

# ──────────── Gráfico flujo acumulado 24 m
mes=np.arange(1,25); serie=gan*(1+inf/100)**(mes/12); flujo=np.cumsum(serie)-INV
fig,ax=plt.subplots()
ax.plot(mes,flujo,color="#1F4E79",lw=2); ax.axhline(0,color="#888",lw=.8,ls="--")
ax.set_xlabel("Mes"); ax.set_ylabel("Flujo acumulado (ARS)")
ax.set_title("Proyección 24 meses",color="#14406b",weight="bold")
st.pyplot(fig)
st.caption("Datos base – Julio 2025 · Civic Twin")
