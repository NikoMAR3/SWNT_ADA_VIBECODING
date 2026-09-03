"""EcoTrack — MVP de huella de carbono con lenguaje natural."""

import pandas as pd
import streamlit as st

from carbon_calculator import parse_activities
from history import daily_totals, load_history, save_entry

st.set_page_config(
    page_title="EcoTrack",
    page_icon="🌿",
    layout="centered",
)

st.title("🌿 EcoTrack")
st.caption(
    "Estima la huella de carbono del día a partir de lo que escribes. "
    "Los factores son aproximados e ilustrativos, no datos oficiales."
)

st.markdown("---")

example = "Hoy comí carne y viajé 20 km en bus"
with st.form("registro_diario"):
    user_text = st.text_area(
        "¿Qué hiciste hoy?",
        placeholder=example,
        height=120,
        help="Ejemplos: transporte (bus, auto, avión + km), comida (carne, pollo, ensalada), energía (ducha, aire acondicionado).",
    )
    col_btn, col_hint = st.columns([1, 2])
    with col_btn:
        submitted = st.form_submit_button("Calcular", type="primary", use_container_width=True)
    with col_hint:
        st.caption("Prueba: *Hoy comí carne y viajé 20 km en bus*")

if submitted:
    result = parse_activities(user_text)

    if result.unrecognized:
        st.warning(
            "No reconocí ninguna actividad. Prueba con más detalle: "
            "medios de transporte (bus, auto, avión) y kilómetros, "
            "comidas (carne, pollo, ensalada) o energía (ducha, lavadora, aire acondicionado)."
        )
    else:
        save_entry(result)
        st.success("Registro guardado en el historial local.")

        st.markdown("### Resultado del día")
        st.metric(
            label="CO₂ estimado",
            value=f"{result.total_kg_co2:.2f} kg",
            help="Suma de las actividades detectadas con factores ilustrativos.",
        )

        rows = [
            {
                "Actividad": a.label,
                "Categoría": a.category,
                "Detalle": a.note,
                "kg CO2e": a.kg_co2,
            }
            for a in result.activities
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

with st.expander("📈 Historial y evolución", expanded=True):
    history = load_history()
    if history.empty:
        st.info("Aún no hay registros. Calcula tu primer día para ver el gráfico.")
    else:
        chart_data = daily_totals(history)
        st.subheader("Evolución de CO₂ (kg por día)")
        st.bar_chart(chart_data.set_index("fecha")["kg CO2e"])

        st.subheader("Últimos registros")
        display = history[["fecha", "hora", "texto", "total_kg_co2"]].copy()
        display = display.rename(
            columns={
                "fecha": "Fecha",
                "hora": "Hora",
                "texto": "Texto",
                "total_kg_co2": "kg CO2e",
            }
        )
        st.dataframe(
            display.sort_values(["Fecha", "Hora"], ascending=False),
            use_container_width=True,
            hide_index=True,
        )

st.markdown("---")
st.caption(
    "Factores de emisión orientativos (DEFRA / Our World in Data, orden de magnitud). "
    "No usar para reportes oficiales."
)
