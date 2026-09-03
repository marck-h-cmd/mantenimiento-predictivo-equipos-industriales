# config/settings.py
# Configuraciones generales del sistema de Mantenimiento Predictivo

import os

# ============================================================
# BASE DE DATOS
# ============================================================
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "mantenimiento_predictivo"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres")
}

# ============================================================
# SEGURIDAD
# ============================================================
JWT_SECRET = os.getenv("JWT_SECRET", "untrujillo_mantenimiento_predictivo_secret_key_2026")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 8

BCRYPT_ROUNDS = 12

# ============================================================
# APLICACIÓN
# ============================================================
APP_NAME = "Mantenimiento Predictivo Minero - UNT"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Sistema de gestión de mantenimiento predictivo con IA para equipos mineros"

# ============================================================
# RUTAS
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models", "trained_models")
DATA_DIR = os.path.join(BASE_DIR, "data")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# ============================================================
# IA / ML
# ============================================================
RANDOM_STATE = 42
TEST_SIZE = 0.15
VAL_SIZE = 0.15
N_SPLITS_CV = 5

# Umbrales de rendimiento del modelo
THRESHOLD_ACCURACY = 0.85
THRESHOLD_RECALL = 0.90
THRESHOLD_F1 = 0.85

# ============================================================
# EQUIPOS Y SENSORES
# ============================================================
TIPOS_EQUIPO = ["carguio", "transporte", "perforacion", "apoyo"]
TIPOS_SENSOR = ["temperatura", "presion", "vibracion", "rpm", "flujo", "corriente"]
ESTADOS_EQUIPO = ["activo", "mantenimiento", "fuera_servicio"]
NIVELES_RIESGO = ["bajo", "medio", "alto", "critico"]

# ============================================================
# ROLES
# ============================================================
ROLES = {
    1: "Administrador",
    2: "Ingeniero",
    3: "Operador",
    4: "Analista"
}

# Matriz de permisos por rol (nombre de permiso)
MATRIZ_PERMISOS = {
    "Administrador": [
        "usuarios_ver", "usuarios_crear", "usuarios_editar", "usuarios_eliminar",
        "equipos_ver", "equipos_crear", "equipos_editar", "equipos_eliminar",
        "sensores_ver", "sensores_configurar",
        "mantenimientos_ver", "mantenimientos_programar", "mantenimientos_ejecutar",
        "dashboard_ver", "eda_ejecutar", "ia_entrenar", "ia_predecir", "ia_evaluar",
        "reportes_generar", "reportes_descargar", "bitacora_ver"
    ],
    "Ingeniero": [
        "equipos_ver", "equipos_crear", "equipos_editar", "equipos_eliminar",
        "sensores_ver", "sensores_configurar",
        "mantenimientos_ver", "mantenimientos_programar", "mantenimientos_ejecutar",
        "dashboard_ver", "ia_entrenar", "ia_predecir", "ia_evaluar",
        "reportes_generar", "reportes_descargar"
    ],
    "Operador": [
        "equipos_ver", "sensores_ver", "mantenimientos_ver",
        "dashboard_ver", "reportes_generar", "reportes_descargar"
    ],
    "Analista": [
        "dashboard_ver", "eda_ejecutar", "ia_entrenar", "ia_predecir", "ia_evaluar",
        "reportes_generar", "reportes_descargar"
    ]
}
