# 🏗️ Sistema de Mantenimiento Predictivo Minero - UNT

**Curso:** Ingeniería de Software II (IS-402)  
**Universidad:** Nacional de Trujillo  
**Semestre:** 2026-I

## 📋 Descripción

Aplicación web completa desarrollada en Python + Streamlit + PostgreSQL que implementa un motor de inteligencia artificial para mantenimiento predictivo de equipos industriales mineros, aplicando la metodología CRISP-DM.

## 🚀 Características

- ✅ **Base de datos relacional** con 11 tablas en PostgreSQL
- ✅ **Sistema de autenticación** con JWT + bcrypt y 4 roles
- ✅ **Dashboard interactivo** con KPIs y visualizaciones Plotly
- ✅ **EDA completo** con estadísticas descriptivas, distribuciones, outliers
- ✅ **5 Algoritmos de IA**: Random Forest, XGBoost, SVM, CNN-LSTM, LSTM-AE+RF
- ✅ **Validación cruzada**: K-Fold, Stratified K-Fold, Time Series Split
- ✅ **Optimización de hiperparámetros**: Grid Search, Random Search
- ✅ **Pruebas estadísticas robustas**: t pareada, McNemar, bootstrap, sensibilidad al ruido
- ✅ **Reportes automáticos** en PDF, Word y Excel
- ✅ **Datos sintéticos** para demostración sin conexión a BD

## 🛠️ Instalación

### 1. Requisitos previos
- Python 3.10+
- PostgreSQL 14+
- Git 2.3+

### 2. Clonar y configurar
```bash
git clone https://github.com/marck-h-cmd/mantenimiento-predictivo-equipos-industriales.git
cd mantenimiento-predictivo-equipos-industriales
pip install -r requirements.txt
```

### 3. Configurar base de datos
```bash
# Crear base de datos
psql -U postgres -f database/init_db.sql
psql -U postgres -d mantenimiento_predictivo -f database/seed_data.sql
```

### 4. Configurar variables de entorno (opcional)
Crear archivo `.env`:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mantenimiento_predictivo
DB_USER=postgres
DB_PASSWORD=tu_password
JWT_SECRET=tu_secret_key
```

### 5. Ejecutar aplicación
```bash
streamlit run app.py
```

## 👥 Usuarios de prueba

| Usuario | Contraseña | Rol |
|---------|-----------|-----|
| admin | password123 | Administrador |
| ingeniero1 | password123 | Ingeniero |
| operador1 | password123 | Operador |
| analista1 | password123 | Analista |

## 📂 Estructura del proyecto

```
mantenimiento_predictivo/
├── app.py                      # Punto de entrada
├── config/
│   ├── settings.py             # Configuraciones
│   └── database.py             # Conexión PostgreSQL
├── modules/
│   ├── auth.py                 # Autenticación JWT + bcrypt
│   ├── dashboard.py            # Dashboard con KPIs
│   ├── eda.py                  # Análisis exploratorio
│   ├── ia_engine.py            # Motor de IA (5 algoritmos)
│   ├── reports.py              # Generación de reportes
│   └── utils.py                # Utilidades
├── database/
│   ├── init_db.sql             # Script de creación (11 tablas)
│   └── seed_data.sql           # Datos de prueba
├── models/trained_models/      # Modelos persistidos
├── data/                       # Datos
├── reports/                    # Reportes generados
└── requirements.txt
```

## 📊 Metodología CRISP-DM aplicada

1. **Comprensión del Negocio**: Reducir MTTR, aumentar disponibilidad
2. **Comprensión de los Datos**: EDA con 10+ variables de sensores
3. **Preparación**: Limpieza, normalización, ingeniería de características
4. **Modelado**: 5 algoritmos con validación cruzada
5. **Evaluación**: Métricas robustas con pruebas estadísticas
6. **Despliegue**: Integración en Streamlit con inferencia < 1s

## 📄 Entregables

- [x] Código fuente completo
- [x] Script de base de datos PostgreSQL
- [x] Archivo requirements.txt
- [x] README.md con instrucciones
- [x] Documentación de práctica
- [x] Presentación de diapositivas

## 👨‍💻 Autores

- **Grupo de práctica** - Ingeniería de Software II
- **Escuela Profesional de Ingeniería de Sistemas**
- **Universidad Nacional de Trujillo**

---
"La ingeniería de software no es solo escribir código, es crear soluciones que generan valor real para la sociedad"
