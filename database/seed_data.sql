-- ============================================================
-- DATOS DE PRUEBA - MANTENIMIENTO PREDICTIVO MINERO
-- ============================================================

-- Insertar roles
INSERT INTO roles (nombre_rol, descripcion) VALUES
('Administrador', 'Control total del sistema, gestión de usuarios y configuración'),
('Ingeniero', 'Gestión de equipos, sensores, mantenimientos y modelos de IA'),
('Operador', 'Monitoreo de equipos, visualización de dashboards y reportes'),
('Analista', 'Análisis de datos, EDA, entrenamiento y evaluación de modelos');

-- Insertar permisos
INSERT INTO permisos (nombre_permiso, descripcion, modulo) VALUES
('usuarios_ver', 'Ver lista de usuarios', 'usuarios'),
('usuarios_crear', 'Crear nuevos usuarios', 'usuarios'),
('usuarios_editar', 'Editar usuarios existentes', 'usuarios'),
('usuarios_eliminar', 'Eliminar usuarios', 'usuarios'),
('equipos_ver', 'Ver equipos', 'equipos'),
('equipos_crear', 'Crear equipos', 'equipos'),
('equipos_editar', 'Editar equipos', 'equipos'),
('equipos_eliminar', 'Eliminar equipos', 'equipos'),
('sensores_ver', 'Ver sensores', 'sensores'),
('sensores_configurar', 'Configurar umbrales de sensores', 'sensores'),
('mantenimientos_ver', 'Ver mantenimientos', 'mantenimientos'),
('mantenimientos_programar', 'Programar mantenimientos', 'mantenimientos'),
('mantenimientos_ejecutar', 'Ejecutar mantenimientos', 'mantenimientos'),
('dashboard_ver', 'Ver dashboard principal', 'dashboard'),
('eda_ejecutar', 'Ejecutar análisis exploratorio', 'eda'),
('ia_entrenar', 'Entrenar modelos de IA', 'ia'),
('ia_predecir', 'Realizar predicciones', 'ia'),
('ia_evaluar', 'Evaluar modelos de IA', 'ia'),
('reportes_generar', 'Generar reportes', 'reportes'),
('reportes_descargar', 'Descargar reportes', 'reportes'),
('bitacora_ver', 'Ver bitácora de accesos', 'bitacora');

-- Matriz de permisos por rol
-- Administrador: todos los permisos
INSERT INTO rol_permiso (id_rol, id_permiso)
SELECT 1, id_permiso FROM permisos;

-- Ingeniero: equipos, sensores, mantenimientos, IA, reportes
INSERT INTO rol_permiso (id_rol, id_permiso) VALUES
(2, 5), (2, 6), (2, 7), (2, 8),  -- equipos
(2, 9), (2, 10),                   -- sensores
(2, 11), (2, 12), (2, 13),        -- mantenimientos
(2, 14),                           -- dashboard
(2, 16), (2, 17), (2, 18),        -- IA
(2, 19), (2, 20);                  -- reportes

-- Operador: solo ver dashboard, equipos, sensores, mantenimientos, reportes
INSERT INTO rol_permiso (id_rol, id_permiso) VALUES
(3, 5), (3, 9), (3, 11), (3, 14), (3, 19), (3, 20);

-- Analista: EDA, IA, reportes, dashboard
INSERT INTO rol_permiso (id_rol, id_permiso) VALUES
(4, 14), (4, 15), (4, 16), (4, 17), (4, 18), (4, 19), (4, 20);

-- Insertar usuarios (contraseñas hasheadas con bcrypt - 'password123')
-- hash generado con bcrypt.hashpw(b'password123', bcrypt.gensalt())
INSERT INTO usuarios (username, email, password_hash, nombre_completo, id_rol) VALUES
('admin', 'admin@untrujillo.edu.pe', '$2b$12$ZNRMuSewjPAC0DE0Xcmby.o1J92LIC03AmqcVlw7WwClOCSe1TT5u', 'Administrador del Sistema', 1),
('ingeniero1', 'ingeniero@untrujillo.edu.pe', '$2b$12$ZNRMuSewjPAC0DE0Xcmby.o1J92LIC03AmqcVlw7WwClOCSe1TT5u', 'Ing. Carlos Mendoza', 2),
('operador1', 'operador@untrujillo.edu.pe', '$2b$12$ZNRMuSewjPAC0DE0Xcmby.o1J92LIC03AmqcVlw7WwClOCSe1TT5u', 'Operador Juan Pérez', 3),
('analista1', 'analista@untrujillo.edu.pe', '$2b$12$ZNRMuSewjPAC0DE0Xcmby.o1J92LIC03AmqcVlw7WwClOCSe1TT5u', 'Analista María López', 4);

-- Insertar equipos
INSERT INTO equipos (codigo_equipo, nombre_equipo, tipo_equipo, marca, modelo, anio_fabricacion, horas_operacion_total, estado_operativo, ubicacion) VALUES
('CARG-001', 'Camión de Carguío Komatsu 930E', 'carguio', 'Komatsu', '930E-4', 2018, 24500, 'activo', 'Mina Cerro Verde - Piso 1'),
('CARG-002', 'Camión de Carguío Caterpillar 797F', 'carguio', 'Caterpillar', '797F', 2019, 18900, 'activo', 'Mina Cerro Verde - Piso 2'),
('CARG-003', 'Pala Eléctrica P&H 4100XPC', 'carguio', 'Komatsu', 'P&H 4100XPC', 2017, 31200, 'mantenimiento', 'Mina Cerro Verde - Piso 1'),
('TRAN-001', 'Camión de Transporte Komatsu 830E', 'transporte', 'Komatsu', '830E-1AC', 2020, 15600, 'activo', 'Mina Cerro Verde - Ruta A'),
('TRAN-002', 'Camión de Transporte Liebherr T 284', 'transporte', 'Liebherr', 'T 284', 2019, 22100, 'activo', 'Mina Cerro Verde - Ruta B'),
('PERF-001', 'Perforadora Sandvik DR412i', 'perforacion', 'Sandvik', 'DR412i', 2021, 8900, 'activo', 'Mina Cerro Verde - Zona Norte');

-- Insertar sensores
INSERT INTO sensores (id_equipo, nombre_sensor, tipo_sensor, unidad_medida, umbral_minimo, umbral_maximo, umbral_critico) VALUES
-- CARG-001
(1, 'Temperatura Motor', 'temperatura', '°C', 60, 95, 110),
(1, 'Presión Aceite Hidráulico', 'presion', 'bar', 150, 280, 320),
(1, 'RPM Motor', 'rpm', 'rpm', 800, 1800, 2200),
(1, 'Vibración Eje Trasero', 'vibracion', 'mm/s', 2, 8, 15),
(1, 'Temperatura Transmisión', 'temperatura', '°C', 50, 85, 100),
-- CARG-002
(2, 'Temperatura Motor', 'temperatura', '°C', 60, 95, 110),
(2, 'Presión Aceite Hidráulico', 'presion', 'bar', 150, 280, 320),
(2, 'RPM Motor', 'rpm', 'rpm', 800, 1800, 2200),
(2, 'Vibración Eje Delantero', 'vibracion', 'mm/s', 2, 8, 15),
-- CARG-003
(3, 'Temperatura Motor', 'temperatura', '°C', 60, 95, 110),
(3, 'Presión Aceite Hidráulico', 'presion', 'bar', 150, 280, 320),
(3, 'Vibración Eje Trasero', 'vibracion', 'mm/s', 2, 8, 15),
-- TRAN-001
(4, 'Temperatura Motor', 'temperatura', '°C', 55, 90, 105),
(4, 'Presión Neumáticos', 'presion', 'psi', 80, 120, 140),
(4, 'RPM Motor', 'rpm', 'rpm', 700, 1600, 2000),
-- TRAN-002
(5, 'Temperatura Motor', 'temperatura', '°C', 55, 90, 105),
(5, 'Vibración Chasis', 'vibracion', 'mm/s', 1.5, 6, 12),
-- PERF-001
(6, 'Temperatura Motor', 'temperatura', '°C', 50, 85, 100),
(6, 'Presión Aire Comprimido', 'presion', 'bar', 6, 10, 12),
(6, 'RPM Perforación', 'rpm', 'rpm', 50, 150, 200);

-- Insertar mantenimientos
INSERT INTO mantenimientos (id_equipo, tipo_mantenimiento, descripcion, fecha_programada, fecha_ejecutada, costo, duracion_horas, tecnico_responsable, estado, resultado) VALUES
(1, 'preventivo', 'Cambio de aceite y filtros', '2026-08-15', '2026-08-15', 2500.00, 4, 'Téc. Roberto Silva', 'completado', 'exitoso'),
(2, 'preventivo', 'Inspección de frenos y suspensión', '2026-08-20', '2026-08-20', 1800.00, 6, 'Téc. Ana Torres', 'completado', 'exitoso'),
(3, 'correctivo', 'Reparación de sistema hidráulico', '2026-08-25', '2026-08-26', 8500.00, 16, 'Téc. Luis García', 'completado', 'exitoso'),
(1, 'predictivo', 'Mantenimiento basado en predicción IA', '2026-09-05', NULL, 3200.00, 8, 'Téc. Roberto Silva', 'programado', NULL),
(4, 'preventivo', 'Revisión de neumáticos y alineación', '2026-09-10', NULL, 1500.00, 3, 'Téc. Ana Torres', 'programado', NULL);

-- Insertar modelos_ml de ejemplo
INSERT INTO modelos_ml (nombre_modelo, tipo_modelo, algoritmo, version, metricas_json, hiperparametros_json, fecha_entrenamiento, activo, accuracy, precision_score, recall, f1_score, auc_roc) VALUES
('Random Forest v1.0', 'tradicional', 'Random Forest', '1.0', '{"cv_mean": 0.87, "cv_std": 0.03}', '{"n_estimators": 200, "max_depth": 15}', '2026-08-20 10:30:00', TRUE, 0.89, 0.87, 0.91, 0.89, 0.93),
('XGBoost v1.0', 'tradicional', 'XGBoost', '1.0', '{"cv_mean": 0.89, "cv_std": 0.02}', '{"n_estimators": 300, "learning_rate": 0.1}', '2026-08-21 14:15:00', FALSE, 0.91, 0.89, 0.93, 0.91, 0.95),
('SVM v1.0', 'tradicional', 'SVM', '1.0', '{"cv_mean": 0.84, "cv_std": 0.04}', '{"C": 1.0, "kernel": "rbf"}', '2026-08-22 09:00:00', FALSE, 0.85, 0.83, 0.88, 0.85, 0.90);
