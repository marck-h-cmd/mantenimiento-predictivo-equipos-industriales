# modules/auth.py
# Sistema de autenticación y autorización con JWT + bcrypt
# 4 roles: Administrador, Ingeniero, Operador, Analista

import jwt
import bcrypt
import datetime
from functools import wraps
import streamlit as st
from config.database import db
from config.settings import (
    JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_HOURS,
    ROLES, MATRIZ_PERMISOS
)


class AuthManager:
    """Gestor de autenticación y autorización del sistema."""

    def __init__(self):
        self.secret = JWT_SECRET
        self.algorithm = JWT_ALGORITHM
        self.exp_hours = JWT_EXPIRATION_HOURS

    # ============================================================
    # HASHING DE CONTRASEÑAS
    # ============================================================
    def hash_password(self, password: str) -> str:
        """Genera hash seguro de contraseña con bcrypt."""
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verifica contraseña contra hash almacenado."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    # ============================================================
    # JWT - TOKENS
    # ============================================================
    def generate_token(self, user_id: int, username: str, rol: str) -> str:
        """Genera token JWT con claims del usuario."""
        payload = {
            'user_id': user_id,
            'username': username,
            'rol': rol,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=self.exp_hours),
            'iat': datetime.datetime.utcnow(),
            'type': 'access'
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def decode_token(self, token: str) -> dict:
        """Decodifica y valida token JWT."""
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return {'error': 'Token expirado'}
        except jwt.InvalidTokenError:
            return {'error': 'Token inválido'}

    # ============================================================
    # AUTENTICACIÓN CON BASE DE DATOS
    # ============================================================
    def authenticate(self, username: str, password: str) -> dict:
        """Autentica usuario contra base de datos."""
        query = """
            SELECT u.id_usuario, u.username, u.password_hash, u.nombre_completo,
                   u.email, u.activo, r.nombre_rol
            FROM usuarios u
            JOIN roles r ON u.id_rol = r.id_rol
            WHERE u.username = %s
        """
        result = db.execute_query(query, (username,), dict_cursor=True)

        if not result:
            return {'success': False, 'message': 'Usuario no encontrado'}

        user = result[0]

        if not user['activo']:
            return {'success': False, 'message': 'Usuario inactivo'}

        if not self.verify_password(password, user['password_hash']):
            self.log_access(user['id_usuario'], 'login_fallido', 'auth', False, 'Contraseña incorrecta')
            return {'success': False, 'message': 'Contraseña incorrecta'}

        # Actualizar último acceso
        db.execute_query(
            "UPDATE usuarios SET ultimo_acceso = NOW() WHERE id_usuario = %s",
            (user['id_usuario'],), fetch=False
        )

        # Generar token
        token = self.generate_token(user['id_usuario'], user['username'], user['nombre_rol'])

        # Registrar en bitácora
        self.log_access(user['id_usuario'], 'login_exitoso', 'auth', True)

        return {
            'success': True,
            'token': token,
            'user': {
                'id': user['id_usuario'],
                'username': user['username'],
                'nombre': user['nombre_completo'],
                'email': user['email'],
                'rol': user['nombre_rol']
            }
        }

    def register_user(self, username: str, email: str, password: str, 
                      nombre_completo: str, id_rol: int) -> dict:
        """Registra nuevo usuario en el sistema."""
        # Verificar duplicados
        check = db.execute_query(
            "SELECT id_usuario FROM usuarios WHERE username = %s OR email = %s",
            (username, email)
        )
        if check:
            return {'success': False, 'message': 'Usuario o email ya existe'}

        password_hash = self.hash_password(password)

        query = """
            INSERT INTO usuarios (username, email, password_hash, nombre_completo, id_rol)
            VALUES (%s, %s, %s, %s, %s) RETURNING id_usuario
        """
        try:
            result = db.execute_query(query, (username, email, password_hash, nombre_completo, id_rol))
            user_id = result[0][0]
            return {'success': True, 'message': 'Usuario registrado exitosamente', 'user_id': user_id}
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}

    # ============================================================
    # AUTORIZACIÓN - MATRIZ DE PERMISOS
    # ============================================================
    def has_permission(self, rol: str, permiso: str) -> bool:
        """Verifica si un rol tiene un permiso específico."""
        if rol not in MATRIZ_PERMISOS:
            return False
        return permiso in MATRIZ_PERMISOS[rol]

    def get_user_permissions(self, rol: str) -> list:
        """Obtiene lista de permisos de un rol."""
        return MATRIZ_PERMISOS.get(rol, [])

    def require_permission(self, permiso: str):
        """Decorador para requerir permiso en funciones Streamlit."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                user = st.session_state.get('user')
                if not user:
                    st.error("Debe iniciar sesión")
                    st.stop()
                if not self.has_permission(user['rol'], permiso):
                    st.error("No tiene permisos para acceder a esta funcionalidad")
                    self.log_access(user['id'], f'acceso_denegado_{permiso}', 'auth', False, 'Permiso insuficiente')
                    st.stop()
                return func(*args, **kwargs)
            return wrapper
        return decorator

    # ============================================================
    # BITÁCORA DE ACCESOS
    # ============================================================
    def log_access(self, id_usuario: int, accion: str, modulo: str = None,
                   exitoso: bool = True, detalle: str = None):
        """Registra entrada en bitácora de accesos."""
        query = """
            INSERT INTO bitacora_acceso (id_usuario, accion, modulo, exitoso, detalle)
            VALUES (%s, %s, %s, %s, %s)
        """
        try:
            db.execute_query(query, (id_usuario, accion, modulo, exitoso, detalle), fetch=False)
        except Exception:
            pass  # No fallar si la bitácora no está disponible

    def get_bitacora(self, limit: int = 100, id_usuario: int = None) -> list:
        """Obtiene registros de bitácora."""
        if id_usuario:
            query = """
                SELECT b.*, u.username, u.nombre_completo
                FROM bitacora_acceso b
                LEFT JOIN usuarios u ON b.id_usuario = u.id_usuario
                WHERE b.id_usuario = %s
                ORDER BY b.timestamp DESC
                LIMIT %s
            """
            return db.execute_query(query, (id_usuario, limit), dict_cursor=True)
        else:
            query = """
                SELECT b.*, u.username, u.nombre_completo
                FROM bitacora_acceso b
                LEFT JOIN usuarios u ON b.id_usuario = u.id_usuario
                ORDER BY b.timestamp DESC
                LIMIT %s
            """
            return db.execute_query(query, (limit,), dict_cursor=True)

    # ============================================================
    # GESTIÓN DE USUARIOS
    # ============================================================
    def get_all_users(self) -> list:
        """Obtiene todos los usuarios con información de rol."""
        query = """
            SELECT u.id_usuario, u.username, u.email, u.nombre_completo,
                   u.activo, u.ultimo_acceso, u.fecha_registro,
                   r.id_rol, r.nombre_rol
            FROM usuarios u
            JOIN roles r ON u.id_rol = r.id_rol
            ORDER BY u.fecha_registro DESC
        """
        return db.execute_query(query, dict_cursor=True)

    def update_user_status(self, id_usuario: int, activo: bool) -> bool:
        """Activa o desactiva un usuario."""
        try:
            db.execute_query(
                "UPDATE usuarios SET activo = %s WHERE id_usuario = %s",
                (activo, id_usuario), fetch=False
            )
            return True
        except Exception:
            return False

    def delete_user(self, id_usuario: int) -> bool:
        """Elimina un usuario del sistema."""
        try:
            db.execute_query(
                "DELETE FROM usuarios WHERE id_usuario = %s",
                (id_usuario,), fetch=False
            )
            return True
        except Exception:
            return False


# Instancia global
auth = AuthManager()


# ============================================================
# FUNCIONES AUXILIARES PARA STREAMLIT
# ============================================================
def init_session_state():
    """Inicializa variables de sesión de Streamlit."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'token' not in st.session_state:
        st.session_state.token = None


def login_ui():
    """Interfaz de login en Streamlit."""
    st.title("🔐 Inicio de Sesión")
    st.markdown("### Sistema de Mantenimiento Predictivo Minero")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Usuario", placeholder="Ingrese su usuario")
            password = st.text_input("Contraseña", type="password", placeholder="Ingrese su contraseña")
            submit = st.form_submit_button("Iniciar Sesión", use_container_width=True)

            if submit:
                if not username or not password:
                    st.error("Complete todos los campos")
                    return

                result = auth.authenticate(username, password)
                if result['success']:
                    st.session_state.authenticated = True
                    st.session_state.user = result['user']
                    st.session_state.token = result['token']
                    st.success(f"Bienvenido, {result['user']['nombre']}!")
                    st.rerun()
                else:
                    st.error(result['message'])

        st.info("""
        **Usuarios de prueba:**
        - **Admin:** admin / password123
        - **Ingeniero:** ingeniero1 / password123
        - **Operador:** operador1 / password123
        - **Analista:** analista1 / password123
        """)


def logout():
    """Cierra sesión del usuario."""
    if st.session_state.get('user'):
        auth.log_access(st.session_state.user['id'], 'logout', 'auth', True)
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.token = None
    st.rerun()


def check_permission(permiso: str) -> bool:
    """Verifica permiso del usuario actual."""
    user = st.session_state.get('user')
    if not user:
        return False
    return auth.has_permission(user['rol'], permiso)
