# modules/utils.py
# Utilidades generales del sistema

import os
import json
import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from config.settings import MODELS_DIR, DATA_DIR, REPORTS_DIR


import shutil

def save_model(model, model_name: str, metadata: dict = None):
    """Persiste modelo entrenado en disco en models y models/trained_models."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    models_root = os.path.dirname(MODELS_DIR)
    os.makedirs(models_root, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_name = model_name.replace(' ', '_').replace('+', '').replace('-', '_').lower()
    filename = f"{clean_name}_{timestamp}.pkl"
    filepath = os.path.join(MODELS_DIR, filename)
    root_filepath = os.path.join(models_root, filename)

    package = {
        'model': model,
        'model_name': model_name,
        'metadata': metadata or {},
        'saved_at': datetime.now().isoformat()
    }

    with open(filepath, 'wb') as f:
        pickle.dump(package, f)

    try:
        shutil.copy2(filepath, root_filepath)
    except Exception:
        pass

    return filepath


def load_model(filepath: str):
    """Carga modelo persistido desde disco."""
    with open(filepath, 'rb') as f:
        package = pickle.load(f)
    return package.get('model'), package.get('metadata', {})


def list_saved_models():
    """Lista modelos guardados en la carpeta models y models/trained_models."""
    results = []
    seen = set()
    dirs_to_check = [MODELS_DIR, os.path.dirname(MODELS_DIR)]
    
    for d in dirs_to_check:
        if os.path.exists(d):
            for f in os.listdir(d):
                if f.endswith('.pkl') or f.endswith('.keras'):
                    if f not in seen:
                        seen.add(f)
                        full_p = os.path.join(d, f)
                        if os.path.isfile(full_p):
                            results.append({
                                'Archivo': f,
                                'Carpeta': os.path.basename(d) if os.path.basename(d) else 'models',
                                'Tamaño (KB)': round(os.path.getsize(full_p) / 1024, 2),
                                'Fecha Modificación': datetime.fromtimestamp(os.path.getmtime(full_p)).strftime("%Y-%m-%d %H:%M:%S")
                            })
    return results


def generate_synthetic_sensor_data(n_samples: int = 5000, n_equipos: int = 6, 
                                    random_state: int = 42) -> pd.DataFrame:
    """Genera datos sintéticos de sensores industriales para mantenimiento predictivo.

    Simula lecturas de sensores de equipos mineros con patrones de degradación
    que preceden a fallas.
    """
    np.random.seed(random_state)

    data = []
    equipos = [f"EQ-{i+1:03d}" for i in range(n_equipos)]

    for equipo in equipos:
        # Cada equipo tiene un perfil de degradación diferente
        base_temp = np.random.uniform(65, 80)
        base_presion = np.random.uniform(180, 220)
        base_rpm = np.random.uniform(1000, 1400)
        base_vibracion = np.random.uniform(3, 5)

        # Generar serie temporal
        for t in range(n_samples // n_equipos):
            # Añadir tendencia de degradación (algunos equipos fallarán)
            degradacion = t / (n_samples // n_equipos)

            # Determinar si hay falla inminente (último 15% de datos para algunos equipos)
            falla_inminente = 0
            if equipo in ["EQ-003", "EQ-005"] and degradacion > 0.75:
                falla_inminente = 1
                factor_stress = (degradacion - 0.75) * 4  # 0 a 1
            else:
                factor_stress = 0

            # Temperatura motor
            temp = base_temp + np.random.normal(0, 3) + factor_stress * 35 + degradacion * 5

            # Presión aceite
            presion = base_presion + np.random.normal(0, 10) - factor_stress * 40 - degradacion * 10

            # RPM
            rpm = base_rpm + np.random.normal(0, 50) - factor_stress * 200

            # Vibración
            vibracion = base_vibracion + np.random.normal(0, 0.5) + factor_stress * 10 + degradacion * 2

            # Temperatura transmisión
            temp_transmision = base_temp - 5 + np.random.normal(0, 2) + factor_stress * 25

            # Horas de operación acumuladas
            horas_op = t * 2 + np.random.randint(0, 2)

            # Carga operativa (0-100%)
            carga = np.random.uniform(60, 95) + factor_stress * 5

            # Corriente eléctrica
            corriente = np.random.uniform(80, 120) + factor_stress * 30

            # Flujo hidráulico
            flujo = np.random.uniform(50, 80) - factor_stress * 15

            # Presión neumáticos
            presion_neumaticos = np.random.uniform(95, 115) - factor_stress * 10

            # Índice de desgaste (feature engineered)
            indice_desgaste = (temp / 100) * 0.3 + (vibracion / 15) * 0.3 +                              ((220 - presion) / 100) * 0.2 + (carga / 100) * 0.2

            # Eficiencia energética
            eficiencia = 100 - (temp - 65) * 0.5 - vibracion * 2 - factor_stress * 20

            # Timestamp
            timestamp = datetime(2026, 1, 1) + timedelta(hours=t)

            data.append({
                'equipo': equipo,
                'timestamp': timestamp,
                'temperatura_motor': round(temp, 2),
                'presion_aceite': round(presion, 2),
                'rpm_motor': round(rpm, 2),
                'vibracion': round(vibracion, 2),
                'temperatura_transmision': round(temp_transmision, 2),
                'horas_operacion': horas_op,
                'carga_operativa': round(carga, 2),
                'corriente': round(corriente, 2),
                'flujo_hidraulico': round(flujo, 2),
                'presion_neumaticos': round(presion_neumaticos, 2),
                'indice_desgaste': round(indice_desgaste, 4),
                'eficiencia': round(eficiencia, 2),
                'falla_inminente': falla_inminente
            })

    df = pd.DataFrame(data)
    df = df.sort_values(['equipo', 'timestamp']).reset_index(drop=True)
    return df


def get_kpi_metrics(df: pd.DataFrame) -> dict:
    """Calcula KPIs principales del sistema."""
    total_equipos = df['equipo'].nunique()
    total_lecturas = len(df)
    fallas_detectadas = df['falla_inminente'].sum()
    tasa_falla = (fallas_detectadas / len(df)) * 100

    # MTBF estimado (Mean Time Between Failures) en horas
    mtbf = total_lecturas * 2 / max(fallas_detectadas, 1)

    # Disponibilidad estimada
    disponibilidad = 100 - (tasa_falla * 0.5)

    # Equipos en riesgo
    equipos_riesgo = df[df['falla_inminente'] == 1]['equipo'].nunique()

    return {
        'total_equipos': total_equipos,
        'total_lecturas': total_lecturas,
        'fallas_detectadas': int(fallas_detectadas),
        'tasa_falla': round(tasa_falla, 2),
        'mtbf_horas': round(mtbf, 2),
        'disponibilidad': round(disponibilidad, 2),
        'equipos_riesgo': equipos_riesgo
    }


def format_number(value, decimals=2):
    """Formatea números para visualización."""
    if isinstance(value, (int, float)):
        return f"{value:,.{decimals}f}"
    return str(value)
