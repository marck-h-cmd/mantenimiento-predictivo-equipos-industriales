# app.py
# Aplicación Web de Mantenimiento Predictivo con Streamlit
# Universidad Nacional de Trujillo - Ingeniería de Software II

import streamlit as st
from modules.auth import init_session_state, login_ui, logout, check_permission, auth
from modules.dashboard import render_dashboard
from modules.eda import render_eda
from modules.ia_engine import render_ia_engine
from modules.reports import render_reports
from modules.utils import generate_synthetic_sensor_data
from config.database import db

# Configuración de página
st.set_page_config(
    page_title="Mantenimiento Predictivo Minero - UNT",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar sesión
init_session_state()


def render_sidebar():
    """Renderiza la barra lateral de navegación."""
    with st.sidebar:
        st.markdown("## ⛏️ Menú Principal")
        st.markdown("---")

        if st.session_state.authenticated:
            user = st.session_state.user
            st.success(f"👤 {user['nombre']}")
            st.info(f"Rol: **{user['rol']}**")
            st.markdown("---")

            menu_options = ["🏠 Inicio"]

            if check_permission("dashboard_ver"):
                menu_options.append("📊 Dashboard")
            if check_permission("eda_ejecutar"):
                menu_options.append("🔍 EDA")
            if check_permission("ia_entrenar") or check_permission("ia_predecir"):
                menu_options.append("🤖 Motor de IA")
            if check_permission("reportes_generar"):
                menu_options.append("📑 Reportes")
            if check_permission("usuarios_ver"):
                menu_options.append("👥 Usuarios")
            if check_permission("bitacora_ver"):
                menu_options.append("📋 Bitácora")

            menu_options.append("⚙️ Configuración")

            selection = st.radio("Navegación", menu_options)

            st.markdown("---")
            if st.button("🚪 Cerrar Sesión", use_container_width=True):
                logout()

            return selection
        else:
            st.info("Inicie sesión para acceder al sistema")
            return None


def render_home():
    """Renderiza la página de inicio."""
    st.title("🏠 Bienvenido al Sistema de Mantenimiento Predictivo")
    st.markdown("---")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        ### 📘 Sistema de Gestión de Mantenimiento Predictivo con IA

        Este sistema implementa un motor de inteligencia artificial para la 
        predicción de fallas en equipos de carguío minero, aplicando la 
        metodología **CRISP-DM** y principios de ingeniería de software.

        **Funcionalidades principales:**
        - ✅ Autenticación segura con JWT + bcrypt (4 roles)
        - ✅ Dashboard interactivo con KPIs y visualizaciones
        - ✅ Análisis Exploratorio de Datos (EDA) completo
        - ✅ Motor de IA con 5 algoritmos (3 tradicionales + 2 híbridos)
        - ✅ Validación cruzada múltiple y optimización de hiperparámetros
        - ✅ Pruebas estadísticas robustas (t pareada, McNemar, bootstrap)
        - ✅ Generación de reportes en PDF, Word y Excel
        - ✅ Base de datos PostgreSQL con 11 tablas relacionales

        **Metodología:** CRISP-DM (Cross-Industry Standard Process for Data Mining)
        """)

        st.subheader("📡 Estado del Sistema")
        col_db, col_model, col_data = st.columns(3)

        with col_db:
            try:
                ok, msg = db.test_connection()
                if ok:
                    st.success("🟢 PostgreSQL")
                else:
                    st.error("🔴 PostgreSQL")
            except:
                st.warning("🟡 PostgreSQL (verificar conexión)")

        with col_model:
            st.info("🟡 Modelos: Listos para entrenar")

        with col_data:
            st.success("🟢 Datos: Disponibles")

    with col2:
        st.markdown("""
        ### 🎓 Información Académica
        **Curso:** Ingeniería de Software II  
        **Código:** IS-402  
        **Semestre:** 2026-I  
        **Universidad:** Nacional de Trujillo

        ### 📊 Métricas de Negocio Objetivo
        - Reducir MTTR ≥ 20%
        - Aumentar disponibilidad ≥ 5%
        - Reducir costos ≥ 15%
        - Precisión del modelo ≥ 85%
        - Sensibilidad (Recall) ≥ 90%
        """)


def render_users():
    """Renderiza la gestión de usuarios (solo Admin)."""
    st.title("👥 Gestión de Usuarios")
    st.markdown("---")

    if not check_permission("usuarios_ver"):
        st.error("No tiene permisos para ver usuarios")
        return

    users = auth.get_all_users()

    if users:
        df_users = []
        for u in users:
            df_users.append({
                'ID': u['id_usuario'],
                'Usuario': u['username'],
                'Nombre': u['nombre_completo'],
                'Email': u['email'],
                'Rol': u['nombre_rol'],
                'Activo': '✅' if u['activo'] else '❌',
                'Último Acceso': u['ultimo_acceso'].strftime('%Y-%m-%d %H:%M') if u['ultimo_acceso'] else 'Nunca',
                'Registro': u['fecha_registro'].strftime('%Y-%m-%d')
            })

        import pandas as pd
        st.dataframe(pd.DataFrame(df_users), use_container_width=True, hide_index=True)
    else:
        st.info("No hay usuarios registrados")


def render_bitacora():
    """Renderiza la bitácora de accesos."""
    st.title("📋 Bitácora de Accesos")
    st.markdown("---")

    if not check_permission("bitacora_ver"):
        st.error("No tiene permisos para ver la bitácora")
        return

    logs = auth.get_bitacora(limit=200)

    if logs:
        df_logs = []
        for l in logs:
            df_logs.append({
                'ID': l['id_bitacora'],
                'Usuario': l.get('username', 'Sistema'),
                'Nombre': l.get('nombre_completo', 'N/A'),
                'Acción': l['accion'],
                'Módulo': l['modulo'],
                'Exitoso': '✅' if l['exitoso'] else '❌',
                'Detalle': l['detalle'] or '-',
                'Fecha/Hora': l['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            })

        import pandas as pd
        st.dataframe(pd.DataFrame(df_logs), use_container_width=True, hide_index=True)
    else:
        st.info("No hay registros en la bitácora")


def render_settings():
    """Renderiza la configuración del sistema."""
    st.title("⚙️ Configuración del Sistema")
    st.markdown("---")

    st.subheader("🔌 Conexión a Base de Datos")
    try:
        ok, msg = db.test_connection()
        if ok:
            st.success(f"Conectado: {msg[:50]}...")
        else:
            st.error(f"Error de conexión: {msg}")
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        st.info("Verifique que PostgreSQL esté ejecutándose y las credenciales en config/settings.py")

    st.markdown("---")
    st.subheader("📦 Información del Sistema")

    from config.settings import APP_NAME, APP_VERSION, APP_DESCRIPTION
    st.write(f"**Aplicación:** {APP_NAME}")
    st.write(f"**Versión:** {APP_VERSION}")
    st.write(f"**Descripción:** {APP_DESCRIPTION}")

    st.markdown("---")
    st.subheader("🧠 Estado de Librerías de IA")

    col1, col2, col3 = st.columns(3)
    with col1:
        try:
            import sklearn
            st.success(f"✅ scikit-learn {sklearn.__version__}")
        except:
            st.error("❌ scikit-learn")

    with col2:
        try:
            import xgboost
            st.success(f"✅ XGBoost {xgboost.__version__}")
        except:
            st.warning("⚠️ XGBoost no instalado")

    with col3:
        try:
            import tensorflow as tf
            st.success(f"✅ TensorFlow {tf.__version__}")
        except:
            st.warning("⚠️ TensorFlow no instalado (algoritmos híbridos no disponibles)")


# ============================================================
# MAIN
# ============================================================
def main():
    if not st.session_state.authenticated:
        login_ui()
    else:
        selection = render_sidebar()

        if selection == "🏠 Inicio":
            render_home()
        elif selection == "📊 Dashboard":
            if check_permission("dashboard_ver"):
                df = generate_synthetic_sensor_data(n_samples=3000)
                render_dashboard(df)
        elif selection == "🔍 EDA":
            if check_permission("eda_ejecutar"):
                df = generate_synthetic_sensor_data(n_samples=5000)
                render_eda(df)
        elif selection == "🤖 Motor de IA":
            if check_permission("ia_entrenar") or check_permission("ia_predecir"):
                render_ia_engine()
        elif selection == "📑 Reportes":
            if check_permission("reportes_generar"):
                render_reports()
        elif selection == "👥 Usuarios":
            render_users()
        elif selection == "📋 Bitácora":
            render_bitacora()
        elif selection == "⚙️ Configuración":
            render_settings()


if __name__ == "__main__":
    main()
