-- ============================================================
-- BASE DE DATOS: MANTENIMIENTO PREDICTIVO MINERO
-- Universidad Nacional de Trujillo - Ingeniería de Software II
-- 8+ Tablas con restricciones y relaciones
-- ============================================================

CREATE DATABASE IF NOT EXISTS mantenimiento_predictivo;
\c mantenimiento_predictivo;

-- 1. TABLA: roles
CREATE TABLE roles (
    id_rol SERIAL PRIMARY KEY,
    nombre_rol VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. TABLA: permisos
CREATE TABLE permisos (
    id_permiso SERIAL PRIMARY KEY,
    nombre_permiso VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,
    modulo VARCHAR(50)
);

-- 3. TABLA: rol_permiso (matriz de permisos)
CREATE TABLE rol_permiso (
    id_rol_permiso SERIAL PRIMARY KEY,
    id_rol INTEGER NOT NULL REFERENCES roles(id_rol) ON DELETE CASCADE,
    id_permiso INTEGER NOT NULL REFERENCES permisos(id_permiso) ON DELETE CASCADE,
    fecha_asignacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(id_rol, id_permiso)
);

-- 4. TABLA: usuarios
CREATE TABLE usuarios (
    id_usuario SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nombre_completo VARCHAR(150),
    id_rol INTEGER NOT NULL REFERENCES roles(id_rol),
    activo BOOLEAN DEFAULT TRUE,
    ultimo_acceso TIMESTAMP,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. TABLA: equipos
CREATE TABLE equipos (
    id_equipo SERIAL PRIMARY KEY,
    codigo_equipo VARCHAR(50) NOT NULL UNIQUE,
    nombre_equipo VARCHAR(100) NOT NULL,
    tipo_equipo VARCHAR(50), -- 'carguio', 'transporte', 'perforacion', etc.
    marca VARCHAR(50),
    modelo VARCHAR(50),
    anio_fabricacion INTEGER,
    horas_operacion_total INTEGER DEFAULT 0,
    estado_operativo VARCHAR(20) DEFAULT 'activo', -- 'activo', 'mantenimiento', 'fuera_servicio'
    ubicacion VARCHAR(100),
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. TABLA: sensores
CREATE TABLE sensores (
    id_sensor SERIAL PRIMARY KEY,
    id_equipo INTEGER NOT NULL REFERENCES equipos(id_equipo) ON DELETE CASCADE,
    nombre_sensor VARCHAR(100) NOT NULL,
    tipo_sensor VARCHAR(50), -- 'temperatura', 'presion', 'vibracion', 'rpm'
    unidad_medida VARCHAR(20),
    umbral_minimo DECIMAL(10,2),
    umbral_maximo DECIMAL(10,2),
    umbral_critico DECIMAL(10,2),
    activo BOOLEAN DEFAULT TRUE,
    fecha_instalacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. TABLA: lecturas_sensores
CREATE TABLE lecturas_sensores (
    id_lectura SERIAL PRIMARY KEY,
    id_sensor INTEGER NOT NULL REFERENCES sensores(id_sensor),
    id_equipo INTEGER NOT NULL REFERENCES equipos(id_equipo),
    valor DECIMAL(10,4) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    calidad_dato VARCHAR(20) DEFAULT 'valido' -- 'valido', 'anomalo', 'nulo'
);

-- 8. TABLA: mantenimientos
CREATE TABLE mantenimientos (
    id_mantenimiento SERIAL PRIMARY KEY,
    id_equipo INTEGER NOT NULL REFERENCES equipos(id_equipo),
    tipo_mantenimiento VARCHAR(30) NOT NULL, -- 'preventivo', 'correctivo', 'predictivo'
    descripcion TEXT,
    fecha_programada DATE,
    fecha_ejecutada DATE,
    costo DECIMAL(12,2),
    duracion_horas INTEGER,
    tecnico_responsable VARCHAR(100),
    estado VARCHAR(20) DEFAULT 'programado', -- 'programado', 'en_proceso', 'completado', 'cancelado'
    resultado VARCHAR(50), -- 'exitoso', 'falla_persiste', 'reprogramar'
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. TABLA: predicciones
CREATE TABLE predicciones (
    id_prediccion SERIAL PRIMARY KEY,
    id_equipo INTEGER NOT NULL REFERENCES equipos(id_equipo),
    id_usuario INTEGER REFERENCES usuarios(id_usuario),
    modelo_utilizado VARCHAR(50),
    probabilidad_falla DECIMAL(5,4),
    clase_predicha INTEGER, -- 0: normal, 1: falla inminente
    nivel_riesgo VARCHAR(20), -- 'bajo', 'medio', 'alto', 'critico'
    recomendacion TEXT,
    features_json JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tiempo_inferencia_ms INTEGER
);

-- 10. TABLA: bitacora_acceso
CREATE TABLE bitacora_acceso (
    id_bitacora SERIAL PRIMARY KEY,
    id_usuario INTEGER REFERENCES usuarios(id_usuario),
    accion VARCHAR(100) NOT NULL,
    modulo VARCHAR(50),
    ip_address INET,
    user_agent TEXT,
    exitoso BOOLEAN DEFAULT TRUE,
    detalle TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 11. TABLA: modelos_ml
CREATE TABLE modelos_ml (
    id_modelo SERIAL PRIMARY KEY,
    nombre_modelo VARCHAR(100) NOT NULL,
    tipo_modelo VARCHAR(30), -- 'tradicional', 'hibrido'
    algoritmo VARCHAR(50),
    version VARCHAR(20),
    ruta_archivo VARCHAR(255),
    metricas_json JSONB,
    hiperparametros_json JSONB,
    fecha_entrenamiento TIMESTAMP,
    activo BOOLEAN DEFAULT FALSE,
    accuracy DECIMAL(5,4),
    precision_score DECIMAL(5,4),
    recall DECIMAL(5,4),
    f1_score DECIMAL(5,4),
    auc_roc DECIMAL(5,4)
);

-- Índices para optimización
CREATE INDEX idx_lecturas_sensor ON lecturas_sensores(id_sensor);
CREATE INDEX idx_lecturas_equipo ON lecturas_sensores(id_equipo);
CREATE INDEX idx_lecturas_timestamp ON lecturas_sensores(timestamp);
CREATE INDEX idx_predicciones_equipo ON predicciones(id_equipo);
CREATE INDEX idx_mantenimientos_equipo ON mantenimientos(id_equipo);
CREATE INDEX idx_bitacora_usuario ON bitacora_acceso(id_usuario);
CREATE INDEX idx_bitacora_timestamp ON bitacora_acceso(timestamp);

-- Comentarios de documentación
COMMENT ON TABLE roles IS 'Catálogo de roles del sistema (Admin, Ingeniero, Operador, Analista)';
COMMENT ON TABLE permisos IS 'Catálogo de permisos granulares por módulo';
COMMENT ON TABLE rol_permiso IS 'Matriz de permisos: asigna permisos a roles';
COMMENT ON TABLE usuarios IS 'Usuarios del sistema con autenticación segura';
COMMENT ON TABLE equipos IS 'Equipos mineros de carguío y transporte';
COMMENT ON TABLE sensores IS 'Sensores IoT instalados en equipos';
COMMENT ON TABLE lecturas_sensores IS 'Lecturas históricas de sensores (series temporales)';
COMMENT ON TABLE mantenimientos IS 'Registro de mantenimientos realizados';
COMMENT ON TABLE predicciones IS 'Predicciones generadas por el motor de IA';
COMMENT ON TABLE bitacora_acceso IS 'Bitácora de auditoría de accesos';
COMMENT ON TABLE modelos_ml IS 'Metadatos de modelos de ML entrenados';
