import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

# ──────────────────────────────────────────────
# PALETA Y ESTILO (azules Civic Twin)
# ──────────────────────────────────────────────
PRIMARY   = "#1F4E79"   # Navy / Civic Twin brand
BG_MAIN   = "#FFFFFF"   # Fondo blanco limpio
BG_CARD   = "#F2F6FA"   # Secundario muy claro
TEXT_MAIN = "#000000"

# ──────────────────────────────────────────────
# CONFIGURACIÓN DE LA PÁGINA
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Civic Twin | Cafetería Quilmes",
    layout="wide",
    page_icon="☕",
)

# Inyección de CSS para aspecto azul armonizado
theme_css = f"""
<style>
html, body {{ background-color:{BG_MAIN}; }}
h1, h2, h3, h4 {{ color:{PRIMARY}; }}
/* Tarjetas KPI */
[data-testid="stMetric"] > div {{
    background-color:{BG_CARD};
    border: 2px solid {PRIMARY};
    border-radius: 12px;
    padding: 8px 12px;
}}
/* Sliders */
div[data-baseweb="slider"] [role="slider"] {{ background-color:{PRIMARY}; }}
/* Slider fill */
div[data-baseweb="slider"] > div > div {{ background-color:{PRIMARY}; }}
/* Botones */
.stButton>button {{ background-color:{PRIMARY}; color:#fff; border-radius:6px; }}
/* Sidebar titles */
[data-testid="stSidebarHeader"] h2 {{ color:{PRIMARY}; }}
</style>
"""

st.markdown(theme_css, unsafe_allow_html=True)

st.title("☕ Civic Twin | Cafetería Quilmes – Tablero MVP")

# ──────────────────────────────────────────────
# 1. CARGA DE DATOS (CSV o Excel multi-sheet)
# ──────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
CSV_FILE   = BASE_DIR / "CivicTwin_Cafe_Quilmes_Data.csv"
EXCEL_FILE = BASE_DIR / "CivicTwin_Cafe_Quilmes_Data.xlsx"

@st.cache_data
def load_data():
    if CSV_FILE.exists():
        tidy = pd.read_csv(CSV_FILE)
        return {"tidy": tidy}
    elif EXCEL_FILE.exists():
        sheets = pd.read_excel(EXCEL_FILE, sheet_name=None)
        return sheets
    else:
        st.error("❌ No se encontró ni CSV ni Excel de datos.")
        return {}

data = load_data()
if not data:
    st.stop()

# ──────────────────────────────────────────────
# 2. NORMALIZACIÓN SEGÚN FUENTE
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
# 3. SIDEBAR – ESCENARIO
# ──────────────────────────────────────────────
st.sidebar.header("Escenario")
clients_per_day = st.sidebar.slider("Clientes por día", 30, 200,
                                    int(sales_df[sales_df["scenario"]=="Moderado"]["clients_per_day"]), 5)

ticket_avg = st.sidebar.slider("Ticket promedio (ARS)", 3000, 8000,
                               int(sales_df[sales_df["scenario"]=="Moderado"]["ticket_ars"]), 100)

inflation = st.sidebar.number_input("Inflación anual (%)", 0.0, 200.0, 0.0, 1.0)

# ──────────────────────────────────────────────
# 4. CÁLCULOS
# ──────────────────────────────────────────────
monthly_sales = clients_per_day * ticket_avg * WORK_DAYS
cost_insumos  = monthly_sales * INSUMOS_PCT
total_monthly_cost = cost_insumos + FIXED_COSTS
profit_monthly = monthly_sales - total_monthly_cost
payback = "∞" if profit_monthly <= 0 else INV_TOTAL / profit_monthly

# ──────────────────────────────────────────────
# 5. KPI CARDS
# ──────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric("Ventas mensuales", f"${monthly_sales:,.0f}")
col2.metric("Ganancia mensual", f"${profit_monthly:,.0f}")
col3.metric("Pay-back (meses)", "No rentable" if payback=="∞" else f"{payback:.1f}")

st.divider()

# ──────────────────────────────────────────────
# 6. GRÁFICO DE FLUJO ACUMULADO (24 MESES)
# ──────────────────────────────────────────────
months = np.arange(1, 25)
profits_series = profit_monthly * (1 + inflation/100) ** (months/12)
cumulative = np.cumsum(profits_series) - INV_TOTAL

fig, ax = plt.subplots()
ax.plot(months, cumulative, color=PRIMARY)
ax.axhline(0, color="gray", lw=0.8, ls="--")
ax.set_xlabel("Mes")
ax.set_ylabel("Flujo de caja acumulado (ARS)")
ax.set_title("Proyección a 24 meses", color=PRIMARY)

st.pyplot(fig)

# ──────────────────────────────────────────────
# 7. TABLA RESUMEN
# ──────────────────────────────────────────────
st.subheader("Resumen mensual", anchor="resumen")
df_show = pd.DataFrame({
    "Concepto": ["Ventas", "Insumos", "Costos fijos", "Ganancia"],
    "ARS": [monthly_sales, cost_insumos, FIXED_COSTS, profit_monthly]
})

df_show["ARS"] = df_show["ARS"].apply(lambda x: f"${x:,.0f}")

st.dataframe(df_show, hide_index=True, use_container_width=True)

st.caption("Datos base: CivicTwin_Cafe_Quilmes_Data · Streamlit MVP – Julio 2025 · Paleta azul")
