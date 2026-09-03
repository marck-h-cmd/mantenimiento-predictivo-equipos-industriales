# modules/eda.py
# Análisis Exploratorio de Datos (EDA) completo con visualizaciones

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


def render_eda(df: pd.DataFrame):
    """Renderiza el módulo completo de EDA."""

    st.title("🔍 Análisis Exploratorio de Datos (EDA)")
    st.markdown("---")

    # 1. VISTA GENERAL
    st.header("1. Vista General del Dataset")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Filas", f"{len(df):,}")
    with col2:
        st.metric("Columnas", len(df.columns))
    with col3:
        st.metric("Memoria (MB)", f"{df.memory_usage(deep=True).sum() / 1024**2:.2f}")
    with col4:
        st.metric("Valores Nulos", df.isnull().sum().sum())

    with st.expander("📋 Vista previa de datos"):
        st.dataframe(df.head(20), use_container_width=True)

    with st.expander("📊 Tipos de datos y estadísticas básicas"):
        col_a, col_b = st.columns(2)
        with col_a:
            st.write("**Tipos de datos:**")
            st.write(df.dtypes)
        with col_b:
            st.write("**Valores nulos por columna:**")
            st.write(df.isnull().sum())

    # 2. ESTADÍSTICAS DESCRIPTIVAS
    st.markdown("---")
    st.header("2. Estadísticas Descriptivas")

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if 'falla_inminente' in numeric_cols:
        numeric_cols.remove('falla_inminente')

    stats_df = df[numeric_cols].describe().T
    stats_df['skewness'] = df[numeric_cols].skew()
    stats_df['kurtosis'] = df[numeric_cols].kurtosis()
    stats_df['missing'] = df[numeric_cols].isnull().sum()
    stats_df['missing_pct'] = (df[numeric_cols].isnull().sum() / len(df)) * 100

    st.dataframe(stats_df.round(4), use_container_width=True)

    # 3. DISTRIBUCIONES
    st.markdown("---")
    st.header("3. Distribuciones de Variables")

    selected_var = st.selectbox("Seleccione variable para analizar:", numeric_cols)

    col_dist1, col_dist2 = st.columns(2)

    with col_dist1:
        # Histograma con KDE
        fig_hist = px.histogram(
            df, x=selected_var, nbins=50, marginal="box",
            title=f"Distribución de {selected_var}",
            color_discrete_sequence=['#3498db'],
            opacity=0.7
        )
        fig_hist.update_layout(height=400, template="plotly_white")
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_dist2:
        # Q-Q Plot para normalidad
        fig_qq = go.Figure()

        sample = df[selected_var].dropna().sample(min(1000, len(df)), random_state=42)
        theoretical_quantiles = stats.norm.ppf(np.linspace(0.01, 0.99, len(sample)))
        sample_sorted = np.sort(sample)

        fig_qq.add_trace(go.Scatter(
            x=theoretical_quantiles, y=sample_sorted,
            mode='markers', name='Datos',
            marker=dict(color='#e74c3c', size=6, opacity=0.6)
        ))

        # Línea de referencia
        min_val = min(theoretical_quantiles.min(), sample_sorted.min())
        max_val = max(theoretical_quantiles.max(), sample_sorted.max())
        fig_qq.add_trace(go.Scatter(
            x=[min_val, max_val], y=[min_val, max_val],
            mode='lines', name='Línea Normal',
            line=dict(color='black', dash='dash')
        ))

        fig_qq.update_layout(
            title=f"Q-Q Plot - {selected_var}",
            xaxis_title="Cuantiles Teóricos (Normal)",
            yaxis_title="Cuantiles Muestrales",
            height=400, template="plotly_white"
        )
        st.plotly_chart(fig_qq, use_container_width=True)

    # Test de normalidad
    shapiro_stat, shapiro_p = stats.shapiro(df[selected_var].dropna().sample(min(5000, len(df)), random_state=42))
    ks_stat, ks_p = stats.kstest(df[selected_var].dropna(), 'norm', 
                                  args=(df[selected_var].mean(), df[selected_var].std()))

    col_test1, col_test2 = st.columns(2)
    with col_test1:
        st.info(f"**Test Shapiro-Wilk:**\nEstadístico: {shapiro_stat:.4f}\np-value: {shapiro_p:.2e}")
    with col_test2:
        st.info(f"**Test Kolmogorov-Smirnov:**\nEstadístico: {ks_stat:.4f}\np-value: {ks_p:.2e}")

    # 4. CORRELACIONES
    st.markdown("---")
    st.header("4. Análisis de Correlaciones")

    corr_matrix = df[numeric_cols + ['falla_inminente']].corr()

    fig_corr = px.imshow(
        corr_matrix, text_auto=".2f", aspect="auto",
        title="Matriz de Correlación de Pearson",
        color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
        height=600
    )
    fig_corr.update_layout(template="plotly_white")
    st.plotly_chart(fig_corr, use_container_width=True)

    # Correlaciones con target
    st.subheader("Correlaciones con variable objetivo (Falla Inminente)")
    target_corr = corr_matrix['falla_inminente'].drop('falla_inminente').sort_values(key=abs, ascending=False)

    fig_target_corr = px.bar(
        x=target_corr.index, y=target_corr.values,
        title="Correlación con Falla Inminente",
        labels={'x': 'Variable', 'y': 'Correlación'},
        color=target_corr.values, color_continuous_scale="RdBu_r",
        color_continuous_midpoint=0
    )
    fig_target_corr.update_layout(height=400, template="plotly_white")
    st.plotly_chart(fig_target_corr, use_container_width=True)

    # 5. DETECCIÓN DE OUTLIERS
    st.markdown("---")
    st.header("5. Detección de Outliers")

    outlier_var = st.selectbox("Variable para detección de outliers:", numeric_cols, key="outlier_var")

    # Método IQR
    Q1 = df[outlier_var].quantile(0.25)
    Q3 = df[outlier_var].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    outliers_iqr = df[(df[outlier_var] < lower_bound) | (df[outlier_var] > upper_bound)]

    # Método Z-Score
    z_scores = np.abs(stats.zscore(df[outlier_var].dropna()))
    outliers_z = df[z_scores > 3]

    col_out1, col_out2, col_out3 = st.columns(3)
    with col_out1:
        st.metric("Outliers (IQR)", len(outliers_iqr))
    with col_out2:
        st.metric("Outliers (Z-Score > 3)", len(outliers_z))
    with col_out3:
        st.metric("% Outliers (IQR)", f"{len(outliers_iqr)/len(df)*100:.2f}%")

    # Boxplot
    fig_box = px.box(
        df, y=outlier_var, color='falla_inminente',
        title=f"Boxplot de {outlier_var} (detección de outliers)",
        color_discrete_map={0: '#2ecc71', 1: '#e74c3c'}
    )
    fig_box.update_layout(height=400, template="plotly_white")
    st.plotly_chart(fig_box, use_container_width=True)

    # 6. ANÁLISIS TEMPORAL
    st.markdown("---")
    st.header("6. Análisis Temporal")

    if 'timestamp' in df.columns:
        df['fecha'] = pd.to_datetime(df['timestamp'])
        df['hora'] = df['fecha'].dt.hour
        df['dia_semana'] = df['fecha'].dt.day_name()

        col_temp1, col_temp2 = st.columns(2)

        with col_temp1:
            # Serie temporal
            temp_ts = df.groupby('fecha')[outlier_var].mean().reset_index()
            fig_ts = px.line(
                temp_ts, x='fecha', y=outlier_var,
                title=f"{outlier_var} - Serie Temporal",
                labels={'fecha': 'Fecha'}
            )
            fig_ts.update_layout(height=350, template="plotly_white")
            st.plotly_chart(fig_ts, use_container_width=True)

        with col_temp2:
            # Patrón por hora
            hora_avg = df.groupby('hora')[outlier_var].mean().reset_index()
            fig_hora = px.bar(
                hora_avg, x='hora', y=outlier_var,
                title=f"{outlier_var} - Promedio por Hora del Día",
                labels={'hora': 'Hora', outlier_var: 'Valor Promedio'}
            )
            fig_hora.update_layout(height=350, template="plotly_white")
            st.plotly_chart(fig_hora, use_container_width=True)

    # 7. ANÁLISIS POR EQUIPO
    st.markdown("---")
    st.header("7. Análisis por Equipo")

    if 'equipo' in df.columns:
        equipo_stats = df.groupby('equipo').agg({
            'temperatura_motor': ['mean', 'std', 'max'],
            'vibracion': ['mean', 'std', 'max'],
            'presion_aceite': ['mean', 'std', 'min'],
            'falla_inminente': 'sum'
        }).round(2)

        equipo_stats.columns = ['_'.join(col).strip() for col in equipo_stats.columns]
        st.dataframe(equipo_stats, use_container_width=True)

        # Radar chart por equipo
        equipos = df['equipo'].unique()
        selected_equipo = st.selectbox("Seleccione equipo para análisis detallado:", equipos)

        eq_data = df[df['equipo'] == selected_equipo][numeric_cols].mean()
        eq_data_norm = (eq_data - eq_data.min()) / (eq_data.max() - eq_data.min())

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=eq_data_norm.values,
            theta=eq_data_norm.index,
            fill='toself',
            name=selected_equipo
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            title=f"Perfil Normalizado - {selected_equipo}",
            height=500, template="plotly_white"
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    # 8. ANÁLISIS DE CLASES
    st.markdown("---")
    st.header("8. Análisis de Balance de Clases")

    if 'falla_inminente' in df.columns:
        class_counts = df['falla_inminente'].value_counts()
        class_pct = df['falla_inminente'].value_counts(normalize=True) * 100

        col_cls1, col_cls2 = st.columns(2)
        with col_cls1:
            st.metric("Clase 0 (Normal)", f"{class_counts.get(0, 0):,} ({class_pct.get(0, 0):.1f}%)")
        with col_cls2:
            st.metric("Clase 1 (Falla)", f"{class_counts.get(1, 0):,} ({class_pct.get(1, 0):.1f}%)")

        if class_pct.get(1, 0) < 20:
            st.warning("⚠️ Dataset desbalanceado. Se recomienda aplicar técnicas de balanceo (SMOTE, undersampling, etc.)")
        else:
            st.success("✅ Dataset relativamente balanceado")

    # 9. RESUMEN EJECUTIVO
    st.markdown("---")
    st.header("9. Resumen Ejecutivo del EDA")

    resumen = f"""
    **Resumen del Análisis Exploratorio de Datos:**

    - **Dataset:** {len(df):,} registros con {len(df.columns)} variables
    - **Variables numéricas:** {len(numeric_cols)}
    - **Valores nulos:** {df.isnull().sum().sum()} ({df.isnull().sum().sum()/df.size*100:.2f}% del total)
    - **Desbalance de clases:** {class_pct.get(1, 0):.1f}% de fallas
    - **Outliers detectados (IQR):** {len(outliers_iqr):,} registros ({len(outliers_iqr)/len(df)*100:.2f}%)
    - **Variable más correlacionada con falla:** {target_corr.abs().idxmax()} (r={target_corr.abs().max():.3f})

    **Recomendaciones para modelado:**
    1. Aplicar normalización/estandarización a variables numéricas
    2. Manejar desbalance de clases con SMOTE o class_weight
    3. Considerar ingeniería de características (ventanas temporales, estadísticas móviles)
    4. Preservar orden temporal en división train/validation/test
    """

    st.info(resumen)
