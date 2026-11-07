"""Demo de churn: evaluación individual, análisis what-if y cartera de clientes."""

from itertools import product

import pandas as pd
import streamlit as st

from model import predict

THRESHOLD = 0.50
PRESETS = {
    "Personalizado": {"tenure_months": 12, "monthly_spend_eur": 60.0,
                      "support_calls": 1, "has_annual_contract": False},
    "Cliente nuevo y descontento": {"tenure_months": 2, "monthly_spend_eur": 95.0,
                                    "support_calls": 4, "has_annual_contract": False},
    "Cliente fiel": {"tenure_months": 36, "monthly_spend_eur": 35.0,
                     "support_calls": 0, "has_annual_contract": True},
    "Gran cuenta sin contrato": {"tenure_months": 18, "monthly_spend_eur": 220.0,
                                 "support_calls": 2, "has_annual_contract": False},
}

st.set_page_config(page_title="Churn Radar", page_icon="📉", layout="wide")


@st.cache_data
def build_portfolio() -> pd.DataFrame:
    """Cartera sintética y reproducible puntuada con el modelo."""
    rows = []
    grid = product([1, 4, 10, 18, 30, 60], [25.0, 55.0, 95.0, 160.0],
                   [0, 2, 5], [False, True])
    for i, (tenure, spend, calls, annual) in enumerate(grid, 1):
        result = predict(tenure, spend, calls, annual)
        rows.append({
            "Cliente": f"C-{i:03d}",
            "Antigüedad (meses)": tenure,
            "Gasto mensual (€)": spend,
            "Llamadas soporte": calls,
            "Contrato anual": annual,
            "Score": result["risk_score"],
            "Resultado": result["label"],
            "Ingresos en riesgo (€)": spend * 12 if result["will_churn"] else 0.0,
        })
    return pd.DataFrame(rows)


def sweep(profile: dict, field: str, grid: list) -> pd.DataFrame:
    """Score al variar un campo, con el resto del perfil fijo."""
    return pd.DataFrame(
        [{field: v, "Score": predict(**{**profile, field: v})["risk_score"],
          "Umbral": THRESHOLD} for v in grid]
    ).set_index(field)


# --- Cabecera y barra lateral ----------------------------------------------
st.title("📉 Churn Radar")
st.caption("Evalúa el riesgo de baja de un cliente y explora la cartera. "
           "Regla sintética: el score no es una probabilidad calibrada.")

with st.sidebar:
    st.header("Perfil de partida")
    preset_name = st.radio("Plantilla", list(PRESETS), index=1)
    st.divider()
    st.markdown(f"**Umbral de decisión:** {THRESHOLD:.2f}")
    st.caption("Por encima del umbral el cliente se marca como «Baja probable».")

preset = PRESETS[preset_name]
tab_client, tab_portfolio = st.tabs(["🔍 Evaluar cliente", "📊 Cartera"])

# --- Pestaña 1: evaluación individual --------------------------------------
with tab_client:
    form_col, result_col = st.columns([1, 1.4], gap="large")

    with form_col:
        # La clave depende de la plantilla para que el formulario se reinicie al cambiarla.
        with st.form(f"churn_form_{preset_name}", border=True):
            st.subheader("Datos del cliente")
            tenure = st.slider("Antigüedad (meses)", 0, 120, preset["tenure_months"])
            spend = st.slider("Gasto mensual (€)", 0.0, 300.0,
                              preset["monthly_spend_eur"], 5.0)
            calls = st.slider("Llamadas a soporte (último trimestre)", 0, 20,
                              preset["support_calls"])
            annual = st.toggle("Contrato anual", value=preset["has_annual_contract"])
            submitted = st.form_submit_button("Calcular riesgo", type="primary",
                                              width="stretch")

    with result_col:
        if not submitted:
            st.info("Elige una plantilla o ajusta los datos y pulsa **Calcular riesgo**.",
                    icon="👈")
        else:
            profile = {"tenure_months": tenure, "monthly_spend_eur": spend,
                       "support_calls": calls, "has_annual_contract": annual}
            try:
                result = predict(**profile)
            except ValueError:
                st.error("No se pudo calcular el riesgo. Revisa los datos.")
            else:
                score = result["risk_score"]
                baseline = predict(**PRESETS["Cliente fiel"])["risk_score"]

                if result["will_churn"]:
                    st.error(f"### {result['label']}", icon="🚨")
                else:
                    st.success(f"### {result['label']}", icon="✅")

                m1, m2, m3 = st.columns(3)
                m1.metric("Score", f"{score:.2f}",
                          delta=f"{score - baseline:+.2f} vs. cliente fiel",
                          delta_color="inverse")
                m2.metric("Margen al umbral", f"{score - THRESHOLD:+.2f}")
                m3.metric("Ingresos anuales", f"{spend * 12:,.0f} €",
                          delta="en riesgo" if result["will_churn"] else "estables",
                          delta_color="inverse" if result["will_churn"] else "normal")
                st.progress(score, text=f"Riesgo relativo: {score:.0%}")

                with st.expander("¿Por qué este resultado?"):
                    st.write(result["explanation"])

                st.markdown("#### ¿Y si cambiara una sola variable?")
                t1, t2, t3, t4 = st.tabs(["Antigüedad", "Gasto", "Llamadas", "Contrato"])
                lines = ["#d62728", "#9e9e9e"]
                with t1:
                    st.line_chart(sweep(profile, "tenure_months", list(range(121))),
                                  x_label="Antigüedad (meses)", y_label="Score",
                                  color=lines, height=260)
                with t2:
                    st.line_chart(sweep(profile, "monthly_spend_eur",
                                        [float(v) for v in range(0, 301, 5)]),
                                  x_label="Gasto mensual (€)", y_label="Score",
                                  color=lines, height=260)
                with t3:
                    st.bar_chart(sweep(profile, "support_calls", list(range(21)))[["Score"]],
                                 x_label="Llamadas a soporte", y_label="Score",
                                 color="#1f77b4", height=260)
                with t4:
                    contract = pd.DataFrame({
                        "Contrato": ["Sin contrato anual", "Con contrato anual"],
                        "Score": [predict(**{**profile, "has_annual_contract": a})
                                  ["risk_score"] for a in (False, True)],
                    })
                    st.bar_chart(contract, x="Contrato", y="Score", horizontal=True,
                                 color="#2ca02c", height=200)

# --- Pestaña 2: cartera ----------------------------------------------------
with tab_portfolio:
    data = build_portfolio()

    f1, f2 = st.columns([2, 1])
    with f1:
        min_score = st.slider("Mostrar clientes con score mayor o igual a",
                              0.0, 1.0, 0.0, 0.05)
    with f2:
        contract_filter = st.segmented_control(
            "Contrato", ["Todos", "Anual", "Sin contrato"], default="Todos")

    view = data[data["Score"] >= min_score]
    if contract_filter == "Anual":
        view = view[view["Contrato anual"]]
    elif contract_filter == "Sin contrato":
        view = view[~view["Contrato anual"]]

    at_risk = view[view["Resultado"] == "Baja probable"]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Clientes", len(view))
    k2.metric("En riesgo", len(at_risk),
              f"{len(at_risk) / max(len(view), 1):.0%} del filtro", delta_color="off")
    k3.metric("Score medio", f"{view['Score'].mean():.2f}" if len(view) else "—")
    k4.metric("Ingresos anuales en riesgo", f"{at_risk['Ingresos en riesgo (€)'].sum():,.0f} €")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Antigüedad vs. gasto** (tamaño = score)")
        st.scatter_chart(view, x="Antigüedad (meses)", y="Gasto mensual (€)",
                         size="Score", color="Resultado", height=320)
    with c2:
        st.markdown("**Score medio por llamadas a soporte**")
        st.bar_chart(view.groupby("Llamadas soporte")["Score"].mean(),
                     y_label="Score medio", height=320)

    st.markdown("**Detalle de clientes**")
    st.dataframe(
        view.sort_values("Score", ascending=False),
        hide_index=True,
        width="stretch",
        column_config={
            "Score": st.column_config.ProgressColumn(
                "Score", min_value=0.0, max_value=1.0, format="%.2f"),
            "Gasto mensual (€)": st.column_config.NumberColumn(format="%.0f €"),
            "Ingresos en riesgo (€)": st.column_config.NumberColumn(format="%.0f €"),
            "Contrato anual": st.column_config.CheckboxColumn(),
        },
    )
    st.download_button("⬇️ Descargar CSV", view.to_csv(index=False).encode("utf-8"),
                       file_name="cartera_churn.csv", mime="text/csv")
