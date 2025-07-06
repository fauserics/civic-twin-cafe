import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from PIL import Image

"""
Civic Twin · Cafetería Quilmes – Tablero MVP  
Versión 2025‑07‑07 – Paleta azul / Encabezado renovado

Cambios:
• Header con logo (64 px), bandera 🇦🇷 y doble título:  
  ‑ “Cafetería Quilmes” (h1, 30 px)  
  ‑ “Civic Twin” (h2, 22 px)
• Mantiene sliders y cálculos originales.
• Requiere subir un archivo PNG llamado **civictwin_logo.png** en la raíz del repo.
"""

# ──────────────────────────────────────────────
# PALETA
# ──────────────────────────────────────────────
PRIMARY   = "#1F4E79"   # Azul Civic Twin
BG_MAIN   = "#FFFFFF"
BG_CARD   = "#F2F6FA"

# ──────────────────────────────────────────────
# CONFIG PÁGINA
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Cafetería Quilmes | Civic Twin",
    layout="wide",
    page_icon="☕",
)

# CSS global
st.markdown(f"""
<style>
html, body {{ background-color:{BG_MAIN}; }}
h1, h2, h3, h4 {{ color:{PRIMARY}; }}
[data-testid="stMetric"] > div {{
  background-color:{BG_CARD};
  border:2px solid {PRIMARY};
  border-radius:12px;
  padding:8px 12px;
}}
div[data-baseweb="slider"] [role="slider"] {{ background-color:{PRIMARY}; color:#fff; }}
div[data-baseweb="slider"] > div > div {{ background-color:{PRIMARY}; }}
.stButton>button {{ background-color:{PRIMARY}; color:#fff; border-radius:6px; }}
[data-testid="stSidebarHeader"] h2 {{ color:{PRIMARY}; }}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# ENCABEZADO CUSTOM
# ──────────────────────────────────────────────
header = st.container()
with header:
    col_logo, col_titles, col_flag = st.columns([1, 5, 1])
    with col_logo:
        try:
            logo = Image.open(Path(__file__).parent / "civictwin_logo.png")
            st.image(logo, width=64)
        except FileNotFoundError:
            st.write("<div style='width:64px;height:64px;background:#ccc;border-radius:50%;display:flex;align-items:center;justify-content:center;'>LOGO</div>", unsafe_allow_html=True)
    with col_titles:
        st.markdown(f"<h1 style='margin-bottom:0;font-size:30px;color:{PRIMARY};'>Cafetería Quilmes</h1>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='margin-top:0;font-size:22px;font-weight:400;color:{PRIMARY};'>Civic Twin</h2>", unsafe_allow_html=True)
    with col_flag:
        st.image("https://flagcdn.com/w40/ar.png", width=40)

# ──────────────────────────────────────────────
# CARGA DE DATOS
# ──────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
CSV_FILE   = BASE_DIR / "CivicTwin_Cafe_Quilmes_Data.csv"
EXCEL_FILE = BASE_DIR / "CivicTwin_Cafe_Quilmes_Data.xlsx"

@st.cache_data
def load_data():
    if CSV_FILE.exists():
        return {"tidy": pd.read_csv(CSV_FILE)}
    elif EXCEL_FILE.exists():
        return pd.read_excel(EXCEL_FILE, sheet_name=None)
    else:
        st.error("❌ No se encontró ni CSV ni Excel de datos.")
        return {}

data = load_data()
if not data:
    st.stop()

# ──────────────────────────────────────────────
# NORMALIZA TABLAS
# ──────────────────────────────────────────────
if "tidy" in data:
    tidy_df   = data["tidy"]
    DS        = lambda name: tidy_df[tidy_df["dataset"] == name]
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

# ──────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────
st.sidebar.header("Escenario")

def default_from(df, scenario, col):
    return int(df.loc[df["scenario"] == scenario, col].iloc[0])

clients_per_day = st.sidebar.slider(
    "Clientes por día", 30, 200,
    default_from(sales_df, "Moderado", "clients_per_day"), 5, format="%d"
)

ticket_avg = st.sidebar.slider(
    "Ticket promedio (ARS)", 3000, 8000,
    default_from(sales_df, "Moderado", "ticket_ars"), 100, format="%d"
)

inflation = st.sidebar.number_input(
    "Inflación anual (%)", 0.0, 200.0, 0.0, 1.0, format="%.1f"
)

# ──────────────────────────────────────────────
# CÁLCULOS
# ──────────────────────────────────────────────
monthly_sales = clients_per_day * ticket_avg * WORK_DAYS
cost_insumos  = monthly_sales * INSUMOS_PCT
profit_monthly = monthly_sales - (cost_insumos + FIXED_COSTS)
payback = "∞" if profit_monthly <= 0 else INV_TOTAL / profit_monthly

# ──────────────────────────────────────────────
# KPI CARDS
# ──────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric("Ventas mensuales", f"${monthly_sales:,.0f}")
col2.metric("Ganancia mensual", f"${profit_monthly:,.0f}")
col3.metric("Pay‑back (meses)", "No rentable" if payback == "∞" else f"{payback:.1f}")

st.divider()

# ──────────────────────────────────────────────
# GRÁFICO – FLUJO ACUMULADO 24 MESES
# ──────────────────────────────────────────────
months = np.arange(1, 25)
profits_series = profit_monthly * (1 + inflation/100) ** (months/12)
cuenta = np.cumsum(profits_series) - INV_TOTAL

fig, ax = plt.subplots()
ax.plot(months, cuenta, color=PRIMARY)
ax.axhline(0, color="gray", lw=0.8, ls="--")
ax.set_xlabel("Mes")
ax.set_ylabel("Flujo de caja acumulado (ARS)")
ax.set_title("Proyección 24 meses", color=PRIMARY)
st.pyplot(fig)

# ──────────────────────────────────────────────
# TABLA RESUMEN
# ──────────────────────────────────────────────
st.subheader("Resumen mensual")
summary = pd.DataFrame({
    "Concepto": ["Ventas", "Insumos", "Costos fijos", "Ganancia"],
    "ARS": [monthly_sales, cost_insumos, FIXED_COSTS, profit_monthly]
})
summary["ARS"] = summary["ARS"].apply(lambda x: f"${x:,.0f}")
st.dataframe(summary, hide_index=True, use_container_width=True)

st.caption("Civic Twin · Cafetería Quilmes · Última actualización 2025‑07‑07")
