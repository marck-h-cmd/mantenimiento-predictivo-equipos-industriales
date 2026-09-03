# modules/ia_engine.py
# Motor de Inteligencia Artificial para Mantenimiento Predictivo
# 5 Algoritmos: RF, XGBoost, SVM (tradicionales) | CNN-LSTM, LSTM-AE+RF (híbridos)
# Validación cruzada múltiple, optimización de hiperparámetros, pruebas estadísticas robustas

import os
import json
import pickle
import warnings
import numpy as np
import pandas as pd
import streamlit as st
from datetime import datetime
from scipy import stats
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import (
    KFold, StratifiedKFold, TimeSeriesSplit,
    GridSearchCV, RandomizedSearchCV, train_test_split
)
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score,
    confusion_matrix, classification_report,
    roc_curve, precision_recall_curve
)
from sklearn.utils import resample
from imblearn.over_sampling import SMOTE
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

warnings.filterwarnings('ignore')

# Importaciones condicionales para deep learning
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, Model
    from tensorflow.keras.layers import (
        Dense, LSTM, Conv1D, MaxPooling1D, Flatten,
        Dropout, BatchNormalization, Input, RepeatVector,
        TimeDistributed
    )
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    from tensorflow.keras.optimizers import Adam
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    st.warning("TensorFlow no instalado. Los algoritmos híbridos no estarán disponibles.")

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    st.warning("XGBoost no instalado. El algoritmo XGBoost no estará disponible.")

from config.settings import MODELS_DIR, RANDOM_STATE, THRESHOLD_ACCURACY, THRESHOLD_RECALL, THRESHOLD_F1
from modules.utils import save_model, generate_synthetic_sensor_data
from config.database import db


class IAEngine:
    """Motor de Inteligencia Artificial para mantenimiento predictivo."""

    def __init__(self):
        self.models = {}
        self.results = {}
        self.scaler = StandardScaler()
        self.feature_cols = None
        self.target_col = 'falla_inminente'
        self.sequence_length = 10

    # ============================================================
    # PREPROCESAMIENTO
    # ============================================================
    def preprocess_data(self, df: pd.DataFrame, fit_scaler=True, for_deep_learning=False):
        """Preprocesa datos para entrenamiento."""
        df = df.copy()

        # Seleccionar features numéricas
        exclude = ['equipo', 'timestamp', 'fecha', self.target_col]
        self.feature_cols = [c for c in df.columns if c not in exclude and df[c].dtype in ['float64', 'int64', 'float32', 'int32']]

        X = df[self.feature_cols].values
        y = df[self.target_col].values

        # Estandarización
        if fit_scaler:
            X = self.scaler.fit_transform(X)
        else:
            X = self.scaler.transform(X)

        # Para deep learning: crear secuencias temporales
        if for_deep_learning:
            X_seq, y_seq = self._create_sequences(X, y, self.sequence_length)
            return X_seq, y_seq

        return X, y

    def _create_sequences(self, X, y, seq_length):
        """Crea secuencias temporales para modelos de deep learning."""
        X_seq, y_seq = [], []
        for i in range(len(X) - seq_length):
            X_seq.append(X[i:i+seq_length])
            y_seq.append(y[i+seq_length])
        return np.array(X_seq), np.array(y_seq)

    # ============================================================
    # 1. RANDOM FOREST (TRADICIONAL)
    # ============================================================
    def train_random_forest(self, X_train, y_train, X_val=None, y_val=None, 
                            optimize=False, cv_strategy='stratified'):
        """Entrena modelo Random Forest con optimización opcional."""
        st.info("🌲 Entrenando Random Forest...")

        if optimize:
            param_grid = {
                'n_estimators': [100, 200, 300],
                'max_depth': [10, 15, 20, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4],
                'max_features': ['sqrt', 'log2']
            }

            cv = self._get_cv_splitter(cv_strategy, n_splits=3)
            grid = RandomizedSearchCV(
                RandomForestClassifier(random_state=RANDOM_STATE, class_weight='balanced'),
                param_distributions=param_grid,
                n_iter=20, cv=cv, scoring='f1', n_jobs=-1, random_state=RANDOM_STATE
            )
            grid.fit(X_train, y_train)
            model = grid.best_estimator_
            best_params = grid.best_params_
        else:
            model = RandomForestClassifier(
                n_estimators=200, max_depth=15, min_samples_split=5,
                min_samples_leaf=2, class_weight='balanced',
                random_state=RANDOM_STATE, n_jobs=-1
            )
            model.fit(X_train, y_train)
            best_params = model.get_params()

        # Feature importance
        importance = dict(zip(self.feature_cols, model.feature_importances_))

        self.models['Random Forest'] = {
            'model': model,
            'type': 'tradicional',
            'params': best_params,
            'importance': importance
        }

        return model

    # ============================================================
    # 2. XGBOOST (TRADICIONAL)
    # ============================================================
    def train_xgboost(self, X_train, y_train, X_val=None, y_val=None, 
                      optimize=False, cv_strategy='stratified'):
        """Entrena modelo XGBoost con optimización opcional."""
        if not XGB_AVAILABLE:
            st.error("XGBoost no está instalado")
            return None

        st.info("⚡ Entrenando XGBoost...")

        if optimize:
            param_grid = {
                'n_estimators': [100, 200, 300],
                'max_depth': [3, 5, 7, 10],
                'learning_rate': [0.01, 0.05, 0.1, 0.2],
                'subsample': [0.8, 0.9, 1.0],
                'colsample_bytree': [0.8, 0.9, 1.0],
                'scale_pos_weight': [1, 3, 5]
            }

            cv = self._get_cv_splitter(cv_strategy, n_splits=3)
            grid = RandomizedSearchCV(
                xgb.XGBClassifier(random_state=RANDOM_STATE, use_label_encoder=False, eval_metric='logloss'),
                param_distributions=param_grid,
                n_iter=20, cv=cv, scoring='f1', n_jobs=-1, random_state=RANDOM_STATE
            )
            grid.fit(X_train, y_train)
            model = grid.best_estimator_
            best_params = grid.best_params_
        else:
            model = xgb.XGBClassifier(
                n_estimators=300, max_depth=5, learning_rate=0.1,
                subsample=0.9, colsample_bytree=0.9,
                scale_pos_weight=3, random_state=RANDOM_STATE,
                use_label_encoder=False, eval_metric='logloss'
            )
            model.fit(X_train, y_train)
            best_params = model.get_params()

        importance = dict(zip(self.feature_cols, model.feature_importances_))

        self.models['XGBoost'] = {
            'model': model,
            'type': 'tradicional',
            'params': best_params,
            'importance': importance
        }

        return model

    # ============================================================
    # 3. SVM (TRADICIONAL)
    # ============================================================
    def train_svm(self, X_train, y_train, X_val=None, y_val=None, 
                  optimize=False, cv_strategy='stratified'):
        """Entrena modelo SVM con optimización opcional."""
        st.info("🎯 Entrenando SVM...")

        if optimize:
            param_grid = {
                'C': [0.1, 1, 10, 100],
                'kernel': ['rbf', 'poly', 'sigmoid'],
                'gamma': ['scale', 'auto', 0.001, 0.01, 0.1]
            }

            cv = self._get_cv_splitter(cv_strategy, n_splits=3)
            grid = GridSearchCV(
                SVC(random_state=RANDOM_STATE, class_weight='balanced', probability=True),
                param_grid=param_grid, cv=cv, scoring='f1', n_jobs=-1
            )
            grid.fit(X_train, y_train)
            model = grid.best_estimator_
            best_params = grid.best_params_
        else:
            model = SVC(
                C=1.0, kernel='rbf', gamma='scale',
                class_weight='balanced', probability=True,
                random_state=RANDOM_STATE
            )
            model.fit(X_train, y_train)
            best_params = model.get_params()

        self.models['SVM'] = {
            'model': model,
            'type': 'tradicional',
            'params': best_params
        }

        return model

    # ============================================================
    # 4. CNN-LSTM (HÍBRIDO)
    # ============================================================
    def train_cnn_lstm(self, X_train, y_train, X_val=None, y_val=None):
        """Entrena modelo CNN-LSTM híbrido."""
        if not TF_AVAILABLE:
            st.error("TensorFlow no está instalado")
            return None

        st.info("🧠 Entrenando CNN-LSTM...")

        # X_train debe ser 3D: (samples, timesteps, features)
        n_timesteps, n_features = X_train.shape[1], X_train.shape[2]

        model = Sequential([
            Conv1D(filters=64, kernel_size=3, activation='relu', 
                   input_shape=(n_timesteps, n_features)),
            BatchNormalization(),
            MaxPooling1D(pool_size=2),
            Conv1D(filters=32, kernel_size=3, activation='relu'),
            BatchNormalization(),
            MaxPooling1D(pool_size=2),
            LSTM(64, return_sequences=False, dropout=0.3),
            Dense(32, activation='relu'),
            Dropout(0.3),
            Dense(1, activation='sigmoid')
        ])

        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', tf.keras.metrics.Precision(), tf.keras.metrics.Recall()]
        )

        callbacks = [
            EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
            ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6)
        ]

        validation_data = (X_val, y_val) if X_val is not None and y_val is not None else None

        history = model.fit(
            X_train, y_train,
            epochs=100, batch_size=32,
            validation_data=validation_data,
            callbacks=callbacks,
            verbose=0, class_weight={0: 1, 1: 3}
        )

        self.models['CNN-LSTM'] = {
            'model': model,
            'type': 'hibrido',
            'history': history.history,
            'params': {
                'conv_filters': [64, 32],
                'lstm_units': 64,
                'dense_units': 32,
                'dropout': 0.3,
                'learning_rate': 0.001
            }
        }

        return model

    # ============================================================
    # 5. LSTM-AUTOENCODER + RF (HÍBRIDO)
    # ============================================================
    def train_lstm_autoencoder_rf(self, X_train, y_train, X_val=None, y_val=None):
        """Entrena modelo LSTM-Autoencoder + Random Forest híbrido."""
        if not TF_AVAILABLE:
            st.error("TensorFlow no está instalado")
            return None

        st.info("🔮 Entrenando LSTM-Autoencoder + Random Forest...")

        n_timesteps, n_features = X_train.shape[1], X_train.shape[2]

        # Autoencoder LSTM
        inputs = Input(shape=(n_timesteps, n_features))
        encoded = LSTM(64, activation='relu', return_sequences=True)(inputs)
        encoded = LSTM(32, activation='relu', return_sequences=False)(encoded)

        decoded = RepeatVector(n_timesteps)(encoded)
        decoded = LSTM(32, activation='relu', return_sequences=True)(decoded)
        decoded = LSTM(64, activation='relu', return_sequences=True)(decoded)
        decoded = TimeDistributed(Dense(n_features))(decoded)

        autoencoder = Model(inputs, decoded)
        autoencoder.compile(optimizer=Adam(0.001), loss='mse')

        # Entrenar autoencoder
        autoencoder.fit(
            X_train, X_train,
            epochs=50, batch_size=32,
            validation_data=(X_val, X_val) if X_val is not None else None,
            callbacks=[EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)],
            verbose=0
        )

        # Extraer encoder
        encoder = Model(inputs, encoded)

        # Obtener representaciones latentes
        X_train_encoded = encoder.predict(X_train, verbose=0)
        if X_val is not None:
            X_val_encoded = encoder.predict(X_val, verbose=0)

        # Entrenar Random Forest sobre representaciones latentes
        rf = RandomForestClassifier(
            n_estimators=200, max_depth=15, class_weight='balanced',
            random_state=RANDOM_STATE, n_jobs=-1
        )
        rf.fit(X_train_encoded, y_train)

        self.models['LSTM-AE + RF'] = {
            'model': {'encoder': encoder, 'classifier': rf},
            'type': 'hibrido',
            'params': {
                'lstm_units': [64, 32],
                'autoencoder_loss': 'mse',
                'rf_estimators': 200,
                'rf_max_depth': 15
            }
        }

        return self.models['LSTM-AE + RF']['model']

    # ============================================================
    # VALIDACIÓN CRUZADA
    # ============================================================
    def _get_cv_splitter(self, strategy: str, n_splits=5):
        """Retorna el splitter de validación cruzada según estrategia."""
        if strategy == 'kfold':
            return KFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
        elif strategy == 'stratified':
            return StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
        elif strategy == 'timeseries':
            return TimeSeriesSplit(n_splits=n_splits)
        else:
            return StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)

    def cross_validate(self, model_name, X, y, cv_strategy='stratified', n_splits=5):
        """Ejecuta validación cruzada para un modelo."""
        st.info(f"🔀 Validación cruzada ({cv_strategy}, {n_splits} folds) para {model_name}...")

        cv = self._get_cv_splitter(cv_strategy, n_splits)
        metrics = {'accuracy': [], 'precision': [], 'recall': [], 'f1': [], 'auc_roc': [], 'auc_pr': []}

        fold_results = []

        for fold, (train_idx, val_idx) in enumerate(cv.split(X, y)):
            X_tr, X_val = X[train_idx], X[val_idx]
            y_tr, y_val = y[train_idx], y[val_idx]

            # Balancear con SMOTE si es necesario (solo para tradicionales)
            if model_name in ['Random Forest', 'XGBoost', 'SVM']:
                if len(np.unique(y_tr)) > 1:
                    try:
                        smote = SMOTE(random_state=RANDOM_STATE)
                        X_tr, y_tr = smote.fit_resample(X_tr, y_tr)
                    except ValueError:
                        pass

            # Clonar y entrenar modelo
            if model_name == 'Random Forest':
                model = RandomForestClassifier(**self.models[model_name]['params'])
                model.fit(X_tr, y_tr)
                y_pred = model.predict(X_val)
                y_prob = model.predict_proba(X_val)[:, 1]
            elif model_name == 'XGBoost' and XGB_AVAILABLE:
                model = xgb.XGBClassifier(**self.models[model_name]['params'])
                model.fit(X_tr, y_tr)
                y_pred = model.predict(X_val)
                y_prob = model.predict_proba(X_val)[:, 1]
            elif model_name == 'SVM':
                model = SVC(**self.models[model_name]['params'])
                model.fit(X_tr, y_tr)
                y_pred = model.predict(X_val)
                y_prob = model.decision_function(X_val)
            else:
                continue

            # Calcular métricas
            metrics['accuracy'].append(accuracy_score(y_val, y_pred))
            metrics['precision'].append(precision_score(y_val, y_pred, zero_division=0))
            metrics['recall'].append(recall_score(y_val, y_pred, zero_division=0))
            metrics['f1'].append(f1_score(y_val, y_pred, zero_division=0))

            try:
                metrics['auc_roc'].append(roc_auc_score(y_val, y_prob))
                metrics['auc_pr'].append(average_precision_score(y_val, y_prob))
            except:
                metrics['auc_roc'].append(0.5)
                metrics['auc_pr'].append(0.5)

            fold_results.append({
                'fold': fold + 1,
                'accuracy': metrics['accuracy'][-1],
                'precision': metrics['precision'][-1],
                'recall': metrics['recall'][-1],
                'f1': metrics['f1'][-1],
                'auc_roc': metrics['auc_roc'][-1]
            })

        # Resumen estadístico
        summary = {}
        for metric in metrics:
            values = np.array(metrics[metric])
            summary[metric] = {
                'mean': np.mean(values),
                'std': np.std(values),
                'min': np.min(values),
                'max': np.max(values),
                'ci95': 1.96 * np.std(values) / np.sqrt(len(values))
            }

        return summary, fold_results

    # ============================================================
    # EVALUACIÓN
    # ============================================================
    def evaluate_model(self, model_name, X_test, y_test):
        """Evalúa un modelo en conjunto de prueba."""
        model_info = self.models.get(model_name)
        if not model_info:
            return None

        model = model_info['model']

        # Predicciones
        if model_name == 'CNN-LSTM' and TF_AVAILABLE:
            y_prob = model.predict(X_test, verbose=0).flatten()
            y_pred = (y_prob > 0.5).astype(int)
        elif model_name == 'LSTM-AE + RF' and TF_AVAILABLE:
            encoder = model['encoder']
            classifier = model['classifier']
            X_enc = encoder.predict(X_test, verbose=0)
            y_prob = classifier.predict_proba(X_enc)[:, 1]
            y_pred = classifier.predict(X_enc)
        else:
            y_prob = model.predict_proba(X_test)[:, 1]
            y_pred = model.predict(X_test)

        # Métricas
        results = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, zero_division=0),
            'recall': recall_score(y_test, y_pred, zero_division=0),
            'f1': f1_score(y_test, y_pred, zero_division=0),
            'auc_roc': roc_auc_score(y_test, y_prob) if len(np.unique(y_test)) > 1 else 0.5,
            'auc_pr': average_precision_score(y_test, y_prob) if len(np.unique(y_test)) > 1 else 0.5,
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
            'y_true': y_test,
            'y_pred': y_pred,
            'y_prob': y_prob
        }

        self.results[model_name] = results
        return results

    # ============================================================
    # PRUEBAS ESTADÍSTICAS ROBUSTAS
    # ============================================================
    def paired_t_test(self, model_a, model_b, X_test, y_test, n_bootstrap=1000):
        """Prueba t pareada entre dos modelos."""
        st.info(f"📊 Prueba t pareada: {model_a} vs {model_b}")

        # Obtener predicciones
        pred_a = self._get_predictions(model_a, X_test)
        pred_b = self._get_predictions(model_b, X_test)

        # Diferencias en accuracy por bootstrap
        diffs = []
        for _ in range(n_bootstrap):
            idx = resample(range(len(y_test)), random_state=_)
            acc_a = accuracy_score(y_test[idx], pred_a[idx])
            acc_b = accuracy_score(y_test[idx], pred_b[idx])
            diffs.append(acc_a - acc_b)

        diffs = np.array(diffs)
        t_stat, p_value = stats.ttest_1samp(diffs, 0)

        return {
            't_statistic': t_stat,
            'p_value': p_value,
            'mean_diff': np.mean(diffs),
            'ci_lower': np.percentile(diffs, 2.5),
            'ci_upper': np.percentile(diffs, 97.5),
            'significant': p_value < 0.05
        }

    def mcnemar_test(self, model_a, model_b, X_test, y_test):
        """Prueba de McNemar entre dos modelos."""
        st.info(f"📊 Prueba de McNemar: {model_a} vs {model_b}")

        pred_a = self._get_predictions(model_a, X_test)
        pred_b = self._get_predictions(model_b, X_test)

        # Tabla de contingencia
        correct_a = (pred_a == y_test)
        correct_b = (pred_b == y_test)

        n_both_correct = np.sum(correct_a & correct_b)
        n_a_correct_only = np.sum(correct_a & ~correct_b)
        n_b_correct_only = np.sum(~correct_a & correct_b)
        n_both_wrong = np.sum(~correct_a & ~correct_b)

        # McNemar test
        contingency = [[n_both_correct, n_a_correct_only],
                       [n_b_correct_only, n_both_wrong]]

        # Estadístico de McNemar (chi-cuadrado con corrección)
        if n_a_correct_only + n_b_correct_only > 0:
            mcnemar_stat = (abs(n_a_correct_only - n_b_correct_only) - 1) ** 2 / (n_a_correct_only + n_b_correct_only)
            p_value = 1 - stats.chi2.cdf(mcnemar_stat, df=1)
        else:
            mcnemar_stat = 0
            p_value = 1.0

        return {
            'mcnemar_stat': mcnemar_stat,
            'p_value': p_value,
            'n_a_correct_only': int(n_a_correct_only),
            'n_b_correct_only': int(n_b_correct_only),
            'significant': p_value < 0.05
        }

    def noise_sensitivity_test(self, model_name, X_test, y_test, noise_levels=[0.01, 0.05, 0.1, 0.15]):
        """Prueba de sensibilidad al ruido."""
        st.info(f"🔊 Prueba de sensibilidad al ruido: {model_name}")

        results = []
        for noise in noise_levels:
            X_noisy = X_test + np.random.normal(0, noise * np.std(X_test), X_test.shape)
            pred = self._get_predictions(model_name, X_noisy)
            acc = accuracy_score(y_test, pred)
            results.append({'noise_level': noise, 'accuracy': acc})

        return results

    def bootstrap_stability(self, model_name, X_train, y_train, X_test, y_test, n_iterations=100):
        """Prueba de estabilidad bootstrap."""
        st.info(f"🔄 Prueba de estabilidad bootstrap: {model_name}")

        scores = []
        for i in range(n_iterations):
            idx = resample(range(len(X_train)), random_state=i)
            X_boot = X_train[idx]
            y_boot = y_train[idx]

            # Reentrenar modelo simple
            if model_name in ['Random Forest', 'XGBoost', 'SVM']:
                if model_name == 'Random Forest':
                    m = RandomForestClassifier(n_estimators=100, random_state=i, class_weight='balanced')
                elif model_name == 'XGBoost' and XGB_AVAILABLE:
                    m = xgb.XGBClassifier(n_estimators=100, random_state=i, use_label_encoder=False, eval_metric='logloss')
                else:
                    m = SVC(random_state=i, class_weight='balanced')

                m.fit(X_boot, y_boot)
                pred = m.predict(X_test)
                scores.append(accuracy_score(y_test, pred))

        scores = np.array(scores)
        return {
            'mean': np.mean(scores),
            'std': np.std(scores),
            'ci95_lower': np.percentile(scores, 2.5),
            'ci95_upper': np.percentile(scores, 97.5),
            'stability_score': 1 - (np.std(scores) / np.mean(scores)) if np.mean(scores) > 0 else 0
        }

    def _get_predictions(self, model_name, X):
        """Obtiene predicciones de un modelo."""
        model_info = self.models[model_name]
        model = model_info['model']

        if model_name == 'CNN-LSTM' and TF_AVAILABLE:
            return (model.predict(X, verbose=0).flatten() > 0.5).astype(int)
        elif model_name == 'LSTM-AE + RF' and TF_AVAILABLE:
            return model['classifier'].predict(model['encoder'].predict(X, verbose=0))
        else:
            return model.predict(X)

    # ============================================================
    # SELECCIÓN DE MEJOR MODELO
    # ============================================================
    def select_best_model(self, criteria_weights=None):
        """Selecciona el mejor modelo usando criterios ponderados."""
        if not self.results:
            return None

        if criteria_weights is None:
            criteria_weights = {
                'accuracy': 0.15,
                'precision': 0.15,
                'recall': 0.20,
                'f1': 0.25,
                'auc_roc': 0.15,
                'auc_pr': 0.10
            }

        scores = {}
        for model_name, metrics in self.results.items():
            score = sum(metrics[k] * w for k, w in criteria_weights.items() if k in metrics)
            scores[model_name] = score

        best_model = max(scores, key=scores.get)

        return {
            'best_model': best_model,
            'scores': scores,
            'criteria_weights': criteria_weights
        }

    # ============================================================
    # PREDICCIÓN
    # ============================================================
    def predict(self, model_name, X, return_proba=True):
        """Realiza predicción con un modelo entrenado."""
        model_info = self.models.get(model_name)
        if not model_info:
            return None

        model = model_info['model']

        if model_name == 'CNN-LSTM' and TF_AVAILABLE:
            prob = model.predict(X, verbose=0).flatten()
            pred = (prob > 0.5).astype(int)
            return (pred, prob) if return_proba else pred
        elif model_name == 'LSTM-AE + RF' and TF_AVAILABLE:
            X_enc = model['encoder'].predict(X, verbose=0)
            prob = model['classifier'].predict_proba(X_enc)[:, 1]
            pred = model['classifier'].predict(X_enc)
            return (pred, prob) if return_proba else pred
        else:
            prob = model.predict_proba(X)[:, 1]
            pred = model.predict(X)
            return (pred, prob) if return_proba else pred

    # ============================================================
    # PERSISTENCIA
    # ============================================================
    def save_best_model(self, model_name, filepath=None):
        """Guarda el mejor modelo en disco."""
        model_info = self.models.get(model_name)
        if not model_info:
            return None

        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(MODELS_DIR, f"best_model_{model_name.replace(' ', '_')}_{timestamp}.pkl")

        package = {
            'model': model_info['model'],
            'model_name': model_name,
            'type': model_info['type'],
            'params': model_info['params'],
            'feature_cols': self.feature_cols,
            'scaler': self.scaler,
            'results': self.results.get(model_name, {}),
            'saved_at': datetime.now().isoformat()
        }

        with open(filepath, 'wb') as f:
            pickle.dump(package, f)

        return filepath

    def load_model_from_disk(self, filepath):
        """Carga modelo desde disco."""
        with open(filepath, 'rb') as f:
            package = pickle.load(f)

        self.models[package['model_name']] = {
            'model': package['model'],
            'type': package['type'],
            'params': package['params']
        }
        self.feature_cols = package['feature_cols']
        self.scaler = package['scaler']

        return package['model_name']


# ============================================================
# INTERFAZ STREAMLIT
# ============================================================
def render_ia_engine():
    """Renderiza la interfaz del motor de IA en Streamlit."""
    st.title("🤖 Motor de Inteligencia Artificial")
    st.markdown("---")

    engine = IAEngine()

    # Cargar datos
    st.header("1. Carga de Datos")

    data_source = st.radio("Fuente de datos:", ["Sintéticos (demo)", "Base de datos"])

    if data_source == "Sintéticos (demo)":
        n_samples = st.slider("Número de muestras:", 1000, 10000, 5000, 500)
        df = generate_synthetic_sensor_data(n_samples=n_samples)
    else:
        try:
            df = db.query_to_dataframe("""
                SELECT e.codigo_equipo as equipo, ls.timestamp, ls.valor,
                       s.tipo_sensor, m.falla_inminente
                FROM lecturas_sensores ls
                JOIN sensores s ON ls.id_sensor = s.id_sensor
                JOIN equipos e ON ls.id_equipo = e.id_equipo
                LEFT JOIN mantenimientos m ON e.id_equipo = m.id_equipo
            """)
            st.success("Datos cargados desde PostgreSQL")
        except Exception as e:
            st.error(f"Error al cargar desde BD: {e}")
            df = generate_synthetic_sensor_data(n_samples=3000)

    st.write(f"Dataset: {len(df):,} registros, {len(df.columns)} variables")

    # Configuración
    st.markdown("---")
    st.header("2. Configuración de Entrenamiento")

    col1, col2 = st.columns(2)
    with col1:
        optimize = st.checkbox("Optimizar hiperparámetros (Grid/Random Search)", value=False)
        cv_strategy = st.selectbox("Estrategia de validación cruzada:", 
                                    ["stratified", "kfold", "timeseries"])
    with col2:
        train_hybrid = st.checkbox("Entrenar algoritmos híbridos (requiere TensorFlow)", value=TF_AVAILABLE)
        test_size = st.slider("% Test:", 10, 30, 15)

    # División de datos
    st.markdown("---")
    st.header("3. Entrenamiento de Modelos")

    if st.button("🚀 Iniciar Entrenamiento", use_container_width=True):
        progress_bar = st.progress(0)
        status = st.empty()

        # Preprocesar
        status.text("Preprocesando datos...")
        X, y = engine.preprocess_data(df, fit_scaler=True)

        # División temporal preservando orden
        split_idx = int(len(X) * (1 - test_size / 100))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        # División adicional para validación (85/15 del train)
        val_split = int(len(X_train) * 0.85)
        X_tr, X_val = X_train[:val_split], X_train[val_split:]
        y_tr, y_val = y_train[:val_split], y_train[val_split:]

        progress_bar.progress(10)

        # Entrenar modelos tradicionales
        models_to_train = ['Random Forest', 'XGBoost', 'SVM']
        total_models = len(models_to_train) + (2 if train_hybrid else 0)
        current = 0

        for model_name in models_to_train:
            status.text(f"Entrenando {model_name}...")

            if model_name == 'Random Forest':
                engine.train_random_forest(X_tr, y_tr, X_val, y_val, optimize, cv_strategy)
            elif model_name == 'XGBoost' and XGB_AVAILABLE:
                engine.train_xgboost(X_tr, y_tr, X_val, y_val, optimize, cv_strategy)
            elif model_name == 'SVM':
                engine.train_svm(X_tr, y_tr, X_val, y_val, optimize, cv_strategy)

            current += 1
            progress_bar.progress(10 + int(50 * current / total_models))

        # Entrenar modelos híbridos
        if train_hybrid and TF_AVAILABLE:
            X_seq, y_seq = engine.preprocess_data(df, fit_scaler=True, for_deep_learning=True)
            split_idx_seq = int(len(X_seq) * (1 - test_size / 100))
            X_tr_seq, X_test_seq = X_seq[:split_idx_seq], X_seq[split_idx_seq:]
            y_tr_seq, y_test_seq = y_seq[:split_idx_seq], y_seq[split_idx_seq:]
            val_split_seq = int(len(X_tr_seq) * 0.85)
            X_tr_s, X_val_s = X_tr_seq[:val_split_seq], X_tr_seq[val_split_seq:]
            y_tr_s, y_val_s = y_tr_seq[:val_split_seq], y_tr_seq[val_split_seq:]

            status.text("Entrenando CNN-LSTM...")
            engine.train_cnn_lstm(X_tr_s, y_tr_s, X_val_s, y_val_s)
            current += 1
            progress_bar.progress(10 + int(50 * current / total_models))

            status.text("Entrenando LSTM-AE + RF...")
            engine.train_lstm_autoencoder_rf(X_tr_s, y_tr_s, X_val_s, y_val_s)
            current += 1
            progress_bar.progress(10 + int(50 * current / total_models))

        # Evaluación
        status.text("Evaluando modelos...")
        for model_name in engine.models.keys():
            if model_name in ['CNN-LSTM', 'LSTM-AE + RF']:
                if TF_AVAILABLE:
                    engine.evaluate_model(model_name, X_test_seq, y_test_seq)
            else:
                engine.evaluate_model(model_name, X_test, y_test)

        progress_bar.progress(70)

        # Validación cruzada
        status.text("Ejecutando validación cruzada...")
        cv_results = {}
        for model_name in ['Random Forest', 'XGBoost', 'SVM']:
            if model_name in engine.models:
                summary, folds = engine.cross_validate(model_name, X_train, y_train, cv_strategy)
                cv_results[model_name] = {'summary': summary, 'folds': folds}

        progress_bar.progress(85)

        # Pruebas estadísticas
        status.text("Ejecutando pruebas estadísticas robustas...")

        # McNemar entre RF y XGBoost
        if 'Random Forest' in engine.models and 'XGBoost' in engine.models:
            mcnemar = engine.mcnemar_test('Random Forest', 'XGBoost', X_test, y_test)

        # Bootstrap stability
        stability = {}
        for model_name in ['Random Forest', 'XGBoost']:
            if model_name in engine.models:
                stability[model_name] = engine.bootstrap_stability(model_name, X_train, y_train, X_test, y_test)

        progress_bar.progress(95)

        # Selección de mejor modelo
        best = engine.select_best_model()

        progress_bar.progress(100)
        status.text("¡Entrenamiento completado!")

        # ============================================================
        # RESULTADOS
        # ============================================================
        st.markdown("---")
        st.header("4. Resultados de Evaluación")

        # Tabla comparativa
        results_df = []
        for name, res in engine.results.items():
            results_df.append({
                'Modelo': name,
                'Accuracy': f"{res['accuracy']:.4f}",
                'Precision': f"{res['precision']:.4f}",
                'Recall': f"{res['recall']:.4f}",
                'F1-Score': f"{res['f1']:.4f}",
                'AUC-ROC': f"{res['auc_roc']:.4f}",
                'AUC-PR': f"{res['auc_pr']:.4f}"
            })

        st.dataframe(pd.DataFrame(results_df), use_container_width=True)

        # Mejor modelo
        st.success(f"🏆 **Mejor Modelo:** {best['best_model']} (Score ponderado: {best['scores'][best['best_model']]:.4f})")

        # Gráficos de comparación
        st.subheader("Comparación de Métricas")

        metrics_plot = []
        for name, res in engine.results.items():
            for metric in ['accuracy', 'precision', 'recall', 'f1', 'auc_roc']:
                metrics_plot.append({'Modelo': name, 'Métrica': metric, 'Valor': res[metric]})

        df_plot = pd.DataFrame(metrics_plot)
        fig_comp = px.bar(df_plot, x='Modelo', y='Valor', color='Métrica', barmode='group',
                         title="Comparación de Métricas por Modelo")
        fig_comp.update_layout(height=500, template="plotly_white")
        st.plotly_chart(fig_comp, use_container_width=True)

        # Curvas ROC
        st.subheader("Curvas ROC")
        fig_roc = go.Figure()
        for name, res in engine.results.items():
            if 'y_prob' in res and len(np.unique(res['y_true'])) > 1:
                fpr, tpr, _ = roc_curve(res['y_true'], res['y_prob'])
                fig_roc.add_trace(go.Scatter(x=fpr, y=tpr, mode='lines', name=f"{name} (AUC={res['auc_roc']:.3f})"))
        fig_roc.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode='lines', name='Aleatorio', line=dict(dash='dash', color='gray')))
        fig_roc.update_layout(title="Curvas ROC Comparativas", xaxis_title="FPR", yaxis_title="TPR",
                             height=500, template="plotly_white")
        st.plotly_chart(fig_roc, use_container_width=True)

        # Matrices de confusión
        st.subheader("Matrices de Confusión")
        cols = st.columns(len(engine.results))
        for idx, (name, res) in enumerate(engine.results.items()):
            with cols[idx]:
                cm = np.array(res['confusion_matrix'])
                fig_cm = px.imshow(cm, text_auto=True, aspect="equal",
                                  title=f"{name}", color_continuous_scale="Blues")
                fig_cm.update_layout(height=300, template="plotly_white")
                st.plotly_chart(fig_cm, use_container_width=True)

        # Validación cruzada
        st.markdown("---")
        st.header("5. Validación Cruzada")

        for model_name, cv_data in cv_results.items():
            st.subheader(f"{model_name} - {cv_strategy}")

            folds_df = pd.DataFrame(cv_data['folds'])
            st.dataframe(folds_df, use_container_width=True, hide_index=True)

            # Gráfico de folds
            fig_folds = px.line(folds_df, x='fold', y=['accuracy', 'precision', 'recall', 'f1'],
                               title=f"Métricas por Fold - {model_name}", markers=True)
            fig_folds.update_layout(height=350, template="plotly_white")
            st.plotly_chart(fig_folds, use_container_width=True)

            # Resumen estadístico
            summary = cv_data['summary']
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            with col_s1:
                st.metric("F1 Mean ± Std", f"{summary['f1']['mean']:.4f} ± {summary['f1']['std']:.4f}")
            with col_s2:
                st.metric("Accuracy Mean", f"{summary['accuracy']['mean']:.4f}")
            with col_s3:
                st.metric("Recall Mean", f"{summary['recall']['mean']:.4f}")
            with col_s4:
                st.metric("AUC-ROC Mean", f"{summary['auc_roc']['mean']:.4f}")

        # Pruebas estadísticas
        st.markdown("---")
        st.header("6. Pruebas Estadísticas Robustas")

        if 'mcnemar' in locals():
            st.subheader("Prueba de McNemar (RF vs XGBoost)")
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric("Estadístico", f"{mcnemar['mcnemar_stat']:.4f}")
            with col_m2:
                st.metric("p-value", f"{mcnemar['p_value']:.4f}")
            with col_m3:
                st.metric("Significativo", "Sí" if mcnemar['significant'] else "No")
            st.write(f"RF correcto solo: {mcnemar['n_a_correct_only']} | XGB correcto solo: {mcnemar['n_b_correct_only']}")

        if stability:
            st.subheader("Estabilidad Bootstrap")
            stab_df = []
            for name, stab in stability.items():
                stab_df.append({
                    'Modelo': name,
                    'Accuracy Media': f"{stab['mean']:.4f}",
                    'Desv. Estándar': f"{stab['std']:.4f}",
                    'IC 95%': f"[{stab['ci95_lower']:.4f}, {stab['ci95_upper']:.4f}]",
                    'Score Estabilidad': f"{stab['stability_score']:.4f}"
                })
            st.dataframe(pd.DataFrame(stab_df), use_container_width=True, hide_index=True)

        # Feature importance
        st.markdown("---")
        st.header("7. Importancia de Variables")

        for name, info in engine.models.items():
            if 'importance' in info:
                imp_df = pd.DataFrame(list(info['importance'].items()), columns=['Variable', 'Importancia'])
                imp_df = imp_df.sort_values('Importancia', ascending=True)

                fig_imp = px.bar(imp_df, x='Importancia', y='Variable', orientation='h',
                                title=f"Importancia de Variables - {name}")
                fig_imp.update_layout(height=400, template="plotly_white")
                st.plotly_chart(fig_imp, use_container_width=True)

        # Guardar modelo
        st.markdown("---")
        st.header("8. Guardar Mejor Modelo")

        if st.button("💾 Guardar Mejor Modelo en Disco", use_container_width=True):
            filepath = engine.save_best_model(best['best_model'])
            st.success(f"Modelo guardado en: {filepath}")

            # Guardar en base de datos
            try:
                res = engine.results[best['best_model']]
                db.execute_query("""
                    INSERT INTO modelos_ml (nombre_modelo, tipo_modelo, algoritmo, version,
                                           metricas_json, hiperparametros_json, fecha_entrenamiento,
                                           activo, accuracy, precision_score, recall, f1_score, auc_roc)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW(), TRUE, %s, %s, %s, %s, %s)
                """, (
                    best['best_model'], engine.models[best['best_model']]['type'], best['best_model'], '1.0',
                    json.dumps(best['scores']), json.dumps(engine.models[best['best_model']]['params']),
                    res['accuracy'], res['precision'], res['recall'], res['f1'], res['auc_roc']
                ), fetch=False)
                st.success("Metadatos del modelo guardados en PostgreSQL")
            except Exception as e:
                st.warning(f"No se pudo guardar en BD: {e}")
