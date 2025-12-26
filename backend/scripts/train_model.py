import pandas as pd
import numpy as np
import pickle
import json
from sklearn.model_selection import TimeSeriesSplit
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import matplotlib
matplotlib.use('Agg')  # Backend cho môi trường không có display
import matplotlib.pyplot as plt
import os
import sys
import shutil
from datetime import datetime

# Tạo thư mục model nếu chưa có
if not os.path.exists('model'):
    os.makedirs('model')

print("TRAINING WEATHER PREDICTION MODELS (TIME SERIES)")

try:
    input_file = 'data/weather_preprocessed.csv'
    df = pd.read_csv(input_file)
    
    # Đảm bảo dữ liệu được sắp xếp theo thời gian
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)
except FileNotFoundError:
    print(f"  Error: Preprocessed data not found!")
    sys.exit(1)

# 2. Định nghĩa features cho từng mô hình 
temp_features = ['pressure_msl', 'radiation', 'wind_y']
humidity_features = ['radiation', 'w_51', 'w_53', 'w_61', 'w_63']
precip_features = ['w_63', 'w_65', 'w_61']
all_features = list(set(temp_features + humidity_features + precip_features))
missing_cols = [col for col in all_features if col not in df.columns]
if missing_cols:
    print(f"  Warning: Missing columns: {missing_cols}")

# 3. Backup model cũ nếu có (CHỈ CHO GITHUB ACTIONS)
if os.path.exists('model/all_models.pkl'):
    shutil.copy('model/all_models.pkl', 'model/all_models_backup.pkl')
    print("  Previous models backed up")
if os.path.exists('model/training_results.json'):
    shutil.copy('model/training_results.json', 'model/training_results_previous.json')
    print("  Previous results backed up")
else:
    print("  No previous models found (first run)")

# 4. Chuẩn bị dữ liệu 
split_idx = int(len(df) * 0.8)
train_df = df.iloc[:split_idx]
test_df = df.iloc[split_idx:]

# 5. Time Series Cross-Validation Setup 
tscv = TimeSeriesSplit(n_splits=5)
print(f"  Using TimeSeriesSplit with 5 folds")

# 6. Train các mô hình 
models = {}
scalers = {}
results = {}

# MÔ HÌNH DỰ BÁO NHIỆT ĐỘ  
X_train_temp = train_df[temp_features]
y_train_temp = train_df['temperature']
X_test_temp = test_df[temp_features]
y_test_temp = test_df['temperature']

scaler_temp = StandardScaler()
X_train_temp_scaled = scaler_temp.fit_transform(X_train_temp)
X_test_temp_scaled = scaler_temp.transform(X_test_temp)

cv_scores_temp = []
model_temp = LinearRegression()

for fold, (train_idx, val_idx) in enumerate(tscv.split(X_train_temp_scaled)):
    X_cv_train = X_train_temp_scaled[train_idx]
    y_cv_train = y_train_temp.iloc[train_idx]
    X_cv_val = X_train_temp_scaled[val_idx]
    y_cv_val = y_train_temp.iloc[val_idx]
    
    model_temp.fit(X_cv_train, y_cv_train)
    y_pred_cv = model_temp.predict(X_cv_val)
    
    mae_cv = mean_absolute_error(y_cv_val, y_pred_cv)
    rmse_cv = np.sqrt(mean_squared_error(y_cv_val, y_pred_cv))
    cv_scores_temp.append({'mae': mae_cv, 'rmse': rmse_cv})

model_temp.fit(X_train_temp_scaled, y_train_temp)

y_pred_temp = model_temp.predict(X_test_temp_scaled)
r2_temp = r2_score(y_test_temp, y_pred_temp)
mae_temp = mean_absolute_error(y_test_temp, y_pred_temp)
rmse_temp = np.sqrt(mean_squared_error(y_test_temp, y_pred_temp))

models['temperature'] = model_temp
scalers['temperature'] = scaler_temp
results['temperature'] = {
    'r2': float(r2_temp),
    'mae': float(mae_temp),
    'rmse': float(rmse_temp),
    'cv_mae_mean': float(np.mean([s['mae'] for s in cv_scores_temp])),
    'cv_rmse_mean': float(np.mean([s['rmse'] for s in cv_scores_temp])),
    'features': temp_features,
    'n_samples_train': len(train_df),
    'n_samples_test': len(test_df),
    # Lưu residuals cho visualization
    'residuals': (y_test_temp - y_pred_temp).tolist(),
    'predictions': y_pred_temp.tolist(),
    'actual': y_test_temp.tolist()
}

print(f"      R² Score: {r2_temp:.4f}")
print(f"      MAE: {mae_temp:.4f}°C")
print(f"      RMSE: {rmse_temp:.4f}°C")
print(f"      CV MAE: {np.mean([s['mae'] for s in cv_scores_temp]):.4f}°C")

#  MÔ HÌNH DỰ BÁO ĐỘ ẨM 
available_humidity_features = [f for f in humidity_features if f in df.columns]
if len(available_humidity_features) < len(humidity_features):
    print(f"      Warning: Using available features only: {available_humidity_features}")

if len(available_humidity_features) > 0 and 'humidity' in df.columns:
    X_train_hum = train_df[available_humidity_features]
    y_train_hum = train_df['humidity']
    X_test_hum = test_df[available_humidity_features]
    y_test_hum = test_df['humidity']

    scaler_hum = StandardScaler()
    X_train_hum_scaled = scaler_hum.fit_transform(X_train_hum)
    X_test_hum_scaled = scaler_hum.transform(X_test_hum)

    model_hum = LinearRegression()
    model_hum.fit(X_train_hum_scaled, y_train_hum)

    y_pred_hum = model_hum.predict(X_test_hum_scaled)
    r2_hum = r2_score(y_test_hum, y_pred_hum)
    mae_hum = mean_absolute_error(y_test_hum, y_pred_hum)
    rmse_hum = np.sqrt(mean_squared_error(y_test_hum, y_pred_hum))

    models['humidity'] = model_hum
    scalers['humidity'] = scaler_hum
    results['humidity'] = {
        'r2': float(r2_hum),
        'mae': float(mae_hum),
        'rmse': float(rmse_hum),
        'features': available_humidity_features
    }

    print(f"      R² Score: {r2_hum:.4f}")
    print(f"      MAE: {mae_hum:.4f}%")
    print(f"      RMSE: {rmse_hum:.4f}%")
else:
    print("      Skipped: Missing required features or target")

#  MÔ HÌNH DỰ BÁO LƯỢNG MƯA
available_precip_features = [f for f in precip_features if f in df.columns]
if len(available_precip_features) < len(precip_features):
    print(f"      Warning: Using available features only: {available_precip_features}")

if len(available_precip_features) > 0 and 'precipitation' in df.columns:
    X_train_prec = train_df[available_precip_features]
    y_train_prec = train_df['precipitation']
    X_test_prec = test_df[available_precip_features]
    y_test_prec = test_df['precipitation']

    scaler_prec = StandardScaler()
    X_train_prec_scaled = scaler_prec.fit_transform(X_train_prec)
    X_test_prec_scaled = scaler_prec.transform(X_test_prec)

    model_prec = LinearRegression()
    model_prec.fit(X_train_prec_scaled, y_train_prec)

    y_pred_prec = model_prec.predict(X_test_prec_scaled)
    r2_prec = r2_score(y_test_prec, y_pred_prec)
    mae_prec = mean_absolute_error(y_test_prec, y_pred_prec)
    rmse_prec = np.sqrt(mean_squared_error(y_test_prec, y_pred_prec))

    models['precipitation'] = model_prec
    scalers['precipitation'] = scaler_prec
    results['precipitation'] = {
        'r2': float(r2_prec),
        'mae': float(mae_prec),
        'rmse': float(rmse_prec),
        'features': available_precip_features
    }

    print(f"      R² Score: {r2_prec:.4f}")
    print(f"      MAE: {mae_prec:.4f}mm")
    print(f"      RMSE: {rmse_prec:.4f}mm")
else:
    print("      Skipped: Missing required features or target")

# 7. Residual Analysis 

try:
    plt.figure(figsize=(15, 10))
    
    # Temperature Residuals
    residuals = np.array(results['temperature']['residuals'])
    predictions = np.array(results['temperature']['predictions'])
    actual = np.array(results['temperature']['actual'])
    
    plt.subplot(3, 3, 1)
    plt.scatter(predictions, residuals, alpha=0.5, s=10)
    plt.axhline(y=0, color='r', linestyle='--', lw=2)
    plt.xlabel('Predicted Temperature (°C)')
    plt.ylabel('Residuals (°C)')
    plt.title('Temperature: Residuals vs Predicted')
    plt.grid(True, alpha=0.3)
    
    plt.subplot(3, 3, 2)
    plt.scatter(range(len(residuals)), residuals, alpha=0.5, s=10)
    plt.axhline(y=0, color='r', linestyle='--', lw=2)
    plt.xlabel('Time Index')
    plt.ylabel('Residuals (°C)')
    plt.title('Temperature: Residuals Over Time')
    plt.grid(True, alpha=0.3)
    
    plt.subplot(3, 3, 3)
    plt.hist(residuals, bins=50, alpha=0.7, edgecolor='black')
    plt.xlabel('Residuals (°C)')
    plt.ylabel('Frequency')
    plt.title('Temperature: Residual Distribution')
    plt.grid(True, alpha=0.3)
    
    plt.subplot(3, 3, 5)
    plt.scatter(actual, predictions, alpha=0.5, s=10)
    min_val = min(actual.min(), predictions.min())
    max_val = max(actual.max(), predictions.max())
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2)
    plt.xlabel('Actual Temperature (°C)')
    plt.ylabel('Predicted Temperature (°C)')
    plt.title(f'Temperature: Actual vs Predicted (R²={r2_temp:.4f})')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('model/residual_analysis.png', dpi=150, bbox_inches='tight')
    print("  Residual analysis saved to: model/residual_analysis.png")
except Exception as e:
    print(f"  Warning: Could not create residual plots: {e}")

# 8. Save models 

# Save temperature model 
with open('model/weather_model.pkl', 'wb') as f:
    pickle.dump(models['temperature'], f)
with open('model/scaler.pkl', 'wb') as f:
    pickle.dump(scalers['temperature'], f)
print("  Main temperature model saved to: model/weather_model.pkl")

# Save all models
with open('model/all_models.pkl', 'wb') as f:
    pickle.dump(models, f)
with open('model/all_scalers.pkl', 'wb') as f:
    pickle.dump(scalers, f)
print("  All models saved to: model/all_models.pkl")

# Save feature names
feature_config = {
    'temperature': temp_features,
    'humidity': available_humidity_features if 'humidity' in models else [],
    'precipitation': available_precip_features if 'precipitation' in models else []
}
with open('model/feature_config.pkl', 'wb') as f:
    pickle.dump(feature_config, f)
print("  Feature configuration saved")

# Lưu kết quả dưới dạng JSON 
results_for_json = {}
for key, value in results.items():
    if key == 'temperature':
        # Chỉ lưu metrics, không lưu arrays lớn vào JSON
        results_for_json[key] = {
            'r2': value['r2'],
            'mae': value['mae'],
            'rmse': value['rmse'],
            'cv_mae_mean': value['cv_mae_mean'],
            'cv_rmse_mean': value['cv_rmse_mean'],
            'features': value['features'],
            'n_samples_train': value['n_samples_train'],
            'n_samples_test': value['n_samples_test']
        }
    else:
        results_for_json[key] = value

results_for_json['training_date'] = datetime.now().isoformat()
results_for_json['model_version'] = 'v2.0-timeseries'

with open('model/training_results.json', 'w') as f:
    json.dump(results_for_json, f, indent=2)
print("  Training results saved to JSON")

# 9. Summary Report 
print("\n" + "=" * 60)
print("MODEL PERFORMANCE SUMMARY")
print("=" * 60)

print("\nTEMPERATURE MODEL:")
print(f"  R² Score: {results['temperature']['r2']:.4f}")
print(f"  MAE: {results['temperature']['mae']:.4f}°C")
print(f"  RMSE: {results['temperature']['rmse']:.4f}°C")
print(f"  Cross-Validation MAE: {results['temperature']['cv_mae_mean']:.4f}°C")
print(f"  Features: {temp_features}")

if 'humidity' in results:
    print("\nHUMIDITY MODEL:")
    print(f"  R² Score: {results['humidity']['r2']:.4f}")
    print(f"  MAE: {results['humidity']['mae']:.4f}%")
    print(f"  RMSE: {results['humidity']['rmse']:.4f}%")
    print(f"  Features: {results['humidity']['features']}")

if 'precipitation' in results:
    print("\nPRECIPITATION MODEL:")
    print(f"  R² Score: {results['precipitation']['r2']:.4f}")
    print(f"  MAE: {results['precipitation']['mae']:.4f}mm")
    print(f"  RMSE: {results['precipitation']['rmse']:.4f}mm")
    print(f"  Features: {results['precipitation']['features']}")

print("\nMODEL TRAINING COMPLETED SUCCESSFULLY!")
print("=" * 60)

sys.exit(0)