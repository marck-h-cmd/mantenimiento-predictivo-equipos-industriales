# modules/dashboard.py
# Dashboard interactivo con KPIs y visualizaciones

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from config.database import db
from modules.utils import get_kpi_metrics, format_number


def render_dashboard(df: pd.DataFrame = None):
    """Renderiza el dashboard principal del sistema."""

    st.title("📊 Dashboard de Mantenimiento Predictivo")
    st.markdown("---")

    # Si no hay DataFrame, intentar cargar desde BD o generar sintético
    if df is None:
        try:
            df = db.query_to_dataframe("""
                SELECT e.codigo_equipo as equipo, ls.timestamp,
                       ls.valor as temperatura_motor,
                       s.tipo_sensor
                FROM lecturas_sensores ls
                JOIN sensores s ON ls.id_sensor = s.id_sensor
                JOIN equipos e ON ls.id_equipo = e.id_equipo
                WHERE s.tipo_sensor = 'temperatura'
                ORDER BY ls.timestamp DESC
                LIMIT 1000
            """)
        except Exception:
            from modules.utils import generate_synthetic_sensor_data
            df = generate_synthetic_sensor_data(n_samples=3000)
            st.info("🔄 Mostrando datos sintéticos de demostración")

    # KPIs
    kpis = get_kpi_metrics(df)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🚜 Equipos Monitoreados", kpis['total_equipos'])
    with col2:
        st.metric("📈 Lecturas Registradas", format_number(kpis['total_lecturas'], 0))
    with col3:
        st.metric("⚠️ Fallas Detectadas", kpis['fallas_detectadas'], 
                 delta=f"{kpis['tasa_falla']}%", delta_color="inverse")
    with col4:
        st.metric("✅ Disponibilidad Estimada", f"{kpis['disponibilidad']}%")

    st.markdown("---")

    # Gráficos
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📉 Tendencia de Temperatura por Equipo")
        fig_temp = px.line(
            df, x='timestamp', y='temperatura_motor', color='equipo',
            title="Temperatura del Motor (°C)",
            labels={'temperatura_motor': 'Temperatura (°C)', 'timestamp': 'Fecha/Hora'}
        )
        fig_temp.update_layout(height=400, template="plotly_white")
        st.plotly_chart(fig_temp, use_container_width=True)

        st.subheader("🔧 Distribución de Vibración")
        fig_vib = px.histogram(
            df, x='vibracion', color='falla_inminente',
            nbins=50, title="Distribución de Vibraciones",
            labels={'vibracion': 'Vibración (mm/s)', 'falla_inminente': 'Falla Inminente'},
            color_discrete_map={0: '#2ecc71', 1: '#e74c3c'}
        )
        fig_vib.update_layout(height=350, template="plotly_white")
        st.plotly_chart(fig_vib, use_container_width=True)

    with col_right:
        st.subheader("📊 Estado de Equipos")
        estado_counts = df.groupby('equipo')['falla_inminente'].max().value_counts().reset_index()
        estado_counts.columns = ['Estado', 'Cantidad']
        estado_counts['Estado'] = estado_counts['Estado'].map({0: 'Normal', 1: 'Riesgo'})

        fig_pie = px.pie(
            estado_counts, values='Cantidad', names='Estado',
            title="Proporción de Equipos por Estado",
            color='Estado', color_discrete_map={'Normal': '#2ecc71', 'Riesgo': '#e74c3c'}
        )
        fig_pie.update_layout(height=350, template="plotly_white")
        st.plotly_chart(fig_pie, use_container_width=True)

        st.subheader("⚡ Correlación Presión vs RPM")
        fig_scatter = px.scatter(
            df, x='presion_aceite', y='rpm_motor', color='falla_inminente',
            size='vibracion', hover_data=['equipo', 'temperatura_motor'],
            title="Presión de Aceite vs RPM del Motor",
            labels={'presion_aceite': 'Presión Aceite (bar)', 'rpm_motor': 'RPM'},
            color_discrete_map={0: '#3498db', 1: '#e74c3c'}
        )
        fig_scatter.update_layout(height=400, template="plotly_white")
        st.plotly_chart(fig_scatter, use_container_width=True)

    # Mapa de calor de correlaciones
    st.markdown("---")
    st.subheader("🌡️ Mapa de Calor de Correlaciones")

    numeric_cols = ['temperatura_motor', 'presion_aceite', 'rpm_motor', 
                    'vibracion', 'temperatura_transmision', 'carga_operativa',
                    'corriente', 'flujo_hidraulico', 'indice_desgaste', 'falla_inminente']
    corr_matrix = df[numeric_cols].corr()

    fig_heatmap = px.imshow(
        corr_matrix, text_auto=".2f", aspect="auto",
        title="Matriz de Correlación de Variables",
        color_continuous_scale="RdBu_r", zmin=-1, zmax=1
    )
    fig_heatmap.update_layout(height=500, template="plotly_white")
    st.plotly_chart(fig_heatmap, use_container_width=True)

    # Tabla de equipos en riesgo
    st.markdown("---")
    st.subheader("🚨 Equipos en Riesgo de Falla")

    equipos_riesgo = df[df['falla_inminente'] == 1].groupby('equipo').agg({
        'temperatura_motor': 'mean',
        'vibracion': 'mean',
        'presion_aceite': 'mean',
        'indice_desgaste': 'mean',
        'timestamp': 'max'
    }).reset_index()

    if not equipos_riesgo.empty:
        equipos_riesgo.columns = ['Equipo', 'Temp. Promedio (°C)', 'Vibración Promedio', 
                                   'Presión Promedio', 'Índice Desgaste', 'Última Lectura']
        equipos_riesgo['Nivel Riesgo'] = equipos_riesgo['Índice Desgaste'].apply(
            lambda x: 'CRÍTICO' if x > 0.7 else 'ALTO' if x > 0.5 else 'MEDIO'
        )
        st.dataframe(equipos_riesgo.sort_values('Índice Desgaste', ascending=False), 
                    use_container_width=True, hide_index=True)
    else:
        st.success("✅ No hay equipos en riesgo de falla detectados")

    # Métricas de rendimiento temporal
    st.markdown("---")
    st.subheader("📈 Tendencia de Eficiencia Energética")

    df['fecha'] = pd.to_datetime(df['timestamp']).dt.date
    eficiencia_diaria = df.groupby('fecha')['eficiencia'].mean().reset_index()

    fig_ef = px.area(
        eficiencia_diaria, x='fecha', y='eficiencia',
        title="Eficiencia Energética Promedio Diaria",
        labels={'eficiencia': 'Eficiencia (%)', 'fecha': 'Fecha'},
        color_discrete_sequence=['#9b59b6']
    )
    fig_ef.update_layout(height=350, template="plotly_white")
    fig_ef.add_hline(y=80, line_dash="dash", line_color="red", 
                     annotation_text="Umbral Crítico")
    st.plotly_chart(fig_ef, use_container_width=True)
