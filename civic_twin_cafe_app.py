# civic_twin_cafe_app.py
# Tablero MVP – Civic Twin · Cafetería Quilmes
# Julio 2025
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

# ──────────────────────────────────────────────
# CONFIGURACIÓN BÁSICA DE LA APP
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Civic Twin | Cafetería Quilmes",
    layout="wide",
    page_icon="☕",
)
st.title("☕ Civic Twin | Cafetería Quilmes – Tablero MVP")

# ──────────────────────────────────────────────
# 1. CARGA DE DATOS (acepta CSV o Excel)
# ──────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
CSV_FILE   = BASE_DIR / "CivicTwin_Cafe_Quilmes_Data.csv"
EXCEL_FILE = BASE_DIR / "CivicTwin_Cafe_Quilmes_Data.xlsx"

@st.cache_data
def load_data():
    """Devuelve un dict con los DataFrames necesarios."""
    if CSV_FILE.exists():
        tidy = pd.read_csv(CSV_FILE)
        return {"tidy": tidy}
    elif EXCEL_FILE.exists():
        sheets = pd.read_excel(EXCEL_FILE, sheet_name=None)
        return sheets
    else:
        st.error("❌ No encuentro ni el CSV ni el Excel de datos.")
        return {}

data = load_data()
if not data:
    st.stop()

# ──────────────────────────────────────────────
# 2. NORMALIZA DATOS SEGÚN LA FUENTE
# ──────────────────────────────────────────────
if "tidy" in data:          # Caso CSV tidy largo
    tidy_df   = data["tidy"]
    DS        = lambda name: tidy_df[tidy_df["dataset"] == name]
    init_df   = DS("initial_costs")
    month_df  = DS("monthly_costs")
    sales_df  = DS("sales_scenarios")
    assump_df = DS("assumptions")
else:                        # Caso Excel
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
# 3. PANEL DE ESCENARIO (SIDEBAR)
# ──────────────────────────────────────────────
st.sidebar.header("Escenario")
clients_per_day = st.sidebar.slider(
    "Clientes por día", min_value=30, max_value=200,
    value=int(sales_df.loc[sales_df["scenario"] == "Moderado", "clients_per_day"]),
    step=5,
)
ticket_avg = st.sidebar.slider(
    "Ticket promedio (ARS)", min_value=3_000, max_value=8_000,
    value=int(sales_df.loc[sales_df["scenario"] == "Moderado", "ticket_ars"]),
    step=100,
)
inflation = st.sidebar.number_input(
    "Inflación anual proyectada (%)", min_value=0.0, max_value=200.0,
    value=0.0, step=1.0
)

# ──────────────────────────────────────────────
# 4. CÁLCULOS DINÁMICOS
# ──────────────────────────────────────────────
monthly_sales = clients_per_day * ticket_avg * WORK_DAYS
cost_insumos  = monthly_sales * INSUMOS_PCT
total_monthly_cost = cost_insumos + FIXED_COSTS
profit_monthly = monthly_sales - total_monthly_cost
payback = "∞" if profit_monthly <= 0 else INV_TOTAL / profit_monthly

# ──────────────────────────────────────────────
# 5. KPI CARDS
# ──────────────────────────────────────────────
k1, k2, k3 = st.columns(3)
k1.metric("Ventas mensuales", f"${monthly_sales:,.0f}")
k2.metric("Ganancia mensual", f"${profit_monthly:,.0f}")
k3.metric("Pay-back (meses)",
          "No rentable" if payback == "∞" else f"{payback:.1f}")

st.divider()

# ──────────────────────────────────────────────
# 6. GRÁFICO: FLUJO ACUMULADO 24 MESES
# ──────────────────────────────────────────────
months = np.arange(1, 25)
profits_series = profit_monthly * (1 + inflation/100)**(months/12)
cumulative = np.cumsum(profits_series) - INV_TOTAL

fig, ax = plt.subplots()
ax.plot(months, cumulative)
ax.axhline(0, color="gray", lw=0.8, ls="--")
ax.set_xlabel("Mes")
ax.set_ylabel("Flujo de caja acumulado (ARS)")
ax.set_title("Proyección a 24 meses")
st.pyplot(fig)

# ──────────────────────────────────────────────
# 7. TABLA RESUMEN
# ──────────────────────────────────────────────
st.subheader("Resumen mensual")
df_show = pd.DataFrame({
    "Concepto": ["Ventas", "Insumos", "Costos fijos", "Ganancia"],
    "ARS": [monthly_sales, cost_insumos, FIXED_COSTS, profit_monthly]
})
df_show["ARS"] = df_show["ARS"].apply(lambda x: f"${x:,.0f}")
st.dataframe(df_show, hide_index=True, use_container_width=True)

st.caption("Datos base: CivicTwin_Cafe_Quilmes_Data · Streamlit MVP – Julio 2025")
