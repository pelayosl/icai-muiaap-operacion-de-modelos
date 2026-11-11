"""Demo interactiva de Streamlit para explorar el modelo sintético de churn."""

from itertools import product
from math import cos, pi, sin

import pandas as pd
import streamlit as st

from model import predict


st.set_page_config(
    page_title="Demo de churn",
    page_icon="📊",
    layout="wide",
)


@st.cache_data
def build_demo_data() -> pd.DataFrame:
    """Genera perfiles reproducibles y calcula su resultado con el modelo."""

    profiles = [
        (tenure, spend, calls, annual)
        for tenure, spend, calls, annual in product(
            [2, 8, 24, 48],
            [25.0, 95.0, 180.0],
            [0, 2, 5],
            [False, True],
        )
    ]
    rows = []
    for customer_id, (tenure, spend, calls, annual) in enumerate(profiles, 1):
        result = predict(tenure, spend, calls, annual)
        rows.append(
            {
                "Cliente": f"C-{customer_id:02d}",
                "Antigüedad (meses)": tenure,
                "Gasto mensual (€)": spend,
                "Llamadas soporte": calls,
                "Contrato anual": "Sí" if annual else "No",
                "Score de riesgo": result["risk_score"],
                "Resultado": result["label"],
            }
        )
    return pd.DataFrame(rows)


def render_risk_gauge(risk_score: float) -> None:
    """Muestra un indicador semicircular sencillo sin añadir dependencias gráficas."""

    percentage = int(round(risk_score * 100))
    if risk_score >= 0.7:
        color = "#d9534f"
    elif risk_score >= 0.5:
        color = "#f0ad4e"
    else:
        color = "#2ca02c"

    radius = 80
    arc_length = pi * radius
    dash_offset = arc_length * (1 - risk_score)
    needle_x = 100 - 64 * cos(risk_score * pi)
    needle_y = 100 - 64 * sin(risk_score * pi)

    st.markdown(
        f"""
        <div style="text-align:center">
            <svg viewBox="0 0 200 120" style="max-width:240px">
                <path d="M20 100 A80 80 0 0 1 180 100"
                    fill="none" stroke="#e6e6e6" stroke-width="14"
                    stroke-linecap="round"/>
                <path d="M20 100 A80 80 0 0 1 180 100"
                    fill="none" stroke="{color}" stroke-width="14"
                    stroke-linecap="round" stroke-dasharray="{arc_length}"
                    stroke-dashoffset="{dash_offset}"
                    pathLength="{arc_length}"/>
                <line x1="100" y1="100" x2="{needle_x:.2f}" y2="{needle_y:.2f}"
                    stroke="{color}" stroke-width="4" stroke-linecap="round"/>
                <circle cx="100" cy="100" r="7" fill="{color}"/>
                <text x="20" y="116" font-size="11" fill="#777">0</text>
                <text x="169" y="116" font-size="11" fill="#777">1</text>
            </svg>
            <div style="font-size:1.5rem;font-weight:700;margin-top:-0.4rem">
                {percentage}%
            </div>
            <strong>Indicador de riesgo</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.title("Demo de churn con Streamlit")
st.caption(
    "Pelayo Sierra Lobo"
)

data = build_demo_data()

tab_prediction, tab_exploration, tab_data = st.tabs(
    ["Predicción individual", "Explorador gráfico", "Datos"]
)

with tab_prediction:
    st.subheader("Calcula el riesgo de un cliente")
    with st.form("churn_form"):
        left, right = st.columns(2)
        with left:
            tenure = st.slider("Antigüedad (meses)", 0, 120, 8)
            monthly_spend = st.slider("Gasto mensual (€)", 0.0, 300.0, 95.0, 5.0)
        with right:
            support_calls = st.slider("Llamadas a soporte", 0, 20, 2)
            annual_contract = st.checkbox("Tiene contrato anual")
        submitted = st.form_submit_button("Calcular riesgo", type="primary")

    if submitted:
        result = predict(tenure, monthly_spend, support_calls, annual_contract)
        metric_col, status_col, gauge_col = st.columns([1, 1, 1.2])
        with metric_col:
            st.metric("Score orientativo", f"{result['risk_score']:.2f}")
            st.progress(result["risk_score"], text="Riesgo relativo")
        with status_col:
            if result["will_churn"]:
                st.error(f"Resultado: {result['label']}")
            else:
                st.success(f"Resultado: {result['label']}")
        with gauge_col:
            render_risk_gauge(result["risk_score"])
        st.info(result["explanation"])
    else:
        st.info("Ajusta los valores y pulsa «Calcular riesgo».")

with tab_exploration:
    st.subheader("Cómo cambia el score según el perfil")
    selected_result = st.selectbox(
        "Filtra el resultado mostrado",
        ["Todos", "Baja probable", "Permanencia probable"],
    )
    filtered_data = data if selected_result == "Todos" else data[data["Resultado"] == selected_result]

    chart_col, distribution_col = st.columns(2)
    with chart_col:
        st.markdown("**Score por gasto mensual y antigüedad**")
        st.scatter_chart(
            filtered_data,
            x="Antigüedad (meses)",
            y="Gasto mensual (€)",
            size="Score de riesgo",
            color="Resultado",
        )
    with distribution_col:
        st.markdown("**Score medio por número de llamadas**")
        calls_summary = (
            filtered_data.groupby("Llamadas soporte", as_index=True)["Score de riesgo"]
            .mean()
            .rename("Score medio")
        )
        st.bar_chart(calls_summary)

    st.markdown("**Comparación de perfiles**")
    st.line_chart(
        filtered_data.sort_values(["Antigüedad (meses)", "Gasto mensual (€)"]).set_index(
            "Cliente"
        )[["Score de riesgo"]]
    )

with tab_data:
    st.subheader("Dataset sintético usado en la demo")
    st.write(
        f"{len(data)} perfiles calculados con `model.predict` "
        f"({int(data['Resultado'].eq('Baja probable').sum())} con baja probable)."
    )
    st.dataframe(data, use_container_width=True, hide_index=True)
    st.download_button(
        "Descargar datos CSV",
        data.to_csv(index=False).encode("utf-8"),
        file_name="perfiles_churn_demo.csv",
        mime="text/csv",
    )