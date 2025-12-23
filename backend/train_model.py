import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import matplotlib.pyplot as plt
import os

# Tạo thư mục model nếu chưa có
if not os.path.exists('model'):
    os.makedirs('model')

print("=" * 60)
print("TRAINING WEATHER TEMPERATURE PREDICTION MODEL")
print("=" * 60)

# 1. Load dữ liệu đã tiền xử lý
print("\n[1/6] Loading preprocessed data...")
try:
    df = pd.read_csv('weather_preprocessed.csv')
    print(f"  Loaded {len(df)} records")
    print(f"  Columns: {list(df.columns)}")
except FileNotFoundError:
    print("  Error: weather_preprocessed.csv not found!")
    print("Please run the preprocessing script first.")
    exit(1)

# 2. Chuẩn bị features và target
print("\n[2/6] Preparing features and target...")

# Các features quan trọng theo phân tích correlation
feature_columns = [
    'humidity',         # Độ ẩm
    'precipitation',    # Lượng mưa
    'cloud_cover',      # Độ che phủ mây
    'windspeed',        # Tốc độ gió
    'pressure_msl',     # Áp suất (quan trọng nhất - R² = 0.694)
    'radiation',        # Bức xạ (quan trọng thứ 2 - R² = 0.242)
    'wind_x',           # Thành phần gió hướng đông
    'wind_y'            # Thành phần gió hướng bắc (R² = 0.186)
]

# Kiểm tra xem các cột có tồn tại không
missing_cols = [col for col in feature_columns if col not in df.columns]
if missing_cols:
    print(f"  Missing columns: {missing_cols}")
    exit(1)

X = df[feature_columns]
y = df['temperature']

print(f"  Features shape: {X.shape}")
print(f"  Target shape: {y.shape}")

# 3. Split data
print("\n[3/6] Splitting data (80% train, 20% test)...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"  Training set: {len(X_train)} samples")
print(f"  Test set: {len(X_test)} samples")

# 4. Standardize features
print("\n[4/6] Standardizing features...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print("  Features standardized")

# 5. Train model
print("\n[5/6] Training Linear Regression model...")
model = LinearRegression()
model.fit(X_train_scaled, y_train)

print("  Model trained successfully")

# 6. Evaluate model
print("\n[6/6] Evaluating model performance...")
y_pred_train = model.predict(X_train_scaled)
y_pred_test = model.predict(X_test_scaled)

# Metrics
r2_train = r2_score(y_train, y_pred_train)
r2_test = r2_score(y_test, y_pred_test)
mae_test = mean_absolute_error(y_test, y_pred_test)
rmse_test = np.sqrt(mean_squared_error(y_test, y_pred_test))

print("\n" + "=" * 60)
print("MODEL PERFORMANCE METRICS")
print("=" * 60)
print(f"R² Score (Train): {r2_train:.4f}")
print(f"R² Score (Test):  {r2_test:.4f}")
print(f"MAE (Test):       {mae_test:.4f}°C")
print(f"RMSE (Test):      {rmse_test:.4f}°C")
print("=" * 60)

# Feature importance
print("\nFEATURE IMPORTANCE (Coefficients):")
print("-" * 60)
feature_importance = pd.DataFrame({
    'Feature': feature_columns,
    'Coefficient': model.coef_,
    'Abs_Coefficient': np.abs(model.coef_)
}).sort_values('Abs_Coefficient', ascending=False)

for idx, row in feature_importance.iterrows():
    print(f"{row['Feature']:20s}: {row['Coefficient']:8.4f} (|{row['Abs_Coefficient']:.4f}|)")

# 7. Save model và scaler
print("\n" + "=" * 60)
print("SAVING MODEL AND SCALER")
print("=" * 60)

with open('model/weather_model.pkl', 'wb') as f:
    pickle.dump(model, f)
print("  Model saved to: model/weather_model.pkl")

with open('model/scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)
print("  Scaler saved to: model/scaler.pkl")

# 8. Tạo visualization
print("\n" + "=" * 60)
print("CREATING VISUALIZATIONS")
print("=" * 60)

# Plot 1: Actual vs Predicted
plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.scatter(y_test, y_pred_test, alpha=0.5, s=10)
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
plt.xlabel('Actual Temperature (°C)')
plt.ylabel('Predicted Temperature (°C)')
plt.title(f'Actual vs Predicted (R² = {r2_test:.4f})')
plt.grid(True, alpha=0.3)

# Plot 2: Residuals
plt.subplot(1, 2, 2)
residuals = y_test - y_pred_test
plt.scatter(y_pred_test, residuals, alpha=0.5, s=10)
plt.axhline(y=0, color='r', linestyle='--', lw=2)
plt.xlabel('Predicted Temperature (°C)')
plt.ylabel('Residuals (°C)')
plt.title('Residual Plot')
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('model/model_evaluation.png', dpi=150, bbox_inches='tight')
print("  Evaluation plot saved to: model/model_evaluation.png")

# Plot 3: Feature Importance
plt.figure(figsize=(10, 6))
feature_importance_sorted = feature_importance.sort_values('Coefficient')
colors = ['red' if x < 0 else 'green' for x in feature_importance_sorted['Coefficient']]
plt.barh(feature_importance_sorted['Feature'], feature_importance_sorted['Coefficient'], color=colors, alpha=0.7)
plt.xlabel('Coefficient Value')
plt.ylabel('Feature')
plt.title('Feature Importance (Model Coefficients)')
plt.axvline(x=0, color='black', linestyle='--', linewidth=0.8)
plt.grid(True, alpha=0.3, axis='x')
plt.tight_layout()
plt.savefig('model/feature_importance.png', dpi=150, bbox_inches='tight')
print("  Feature importance plot saved to: model/feature_importance.png")

# 9. Test prediction với dữ liệu mẫu
print("\n" + "=" * 60)
print("TESTING PREDICTION WITH SAMPLE DATA")
print("=" * 60)

# Lấy một mẫu từ test set
sample_idx = 0
sample_features = X_test.iloc[sample_idx:sample_idx+1]
actual_temp = y_test.iloc[sample_idx]

# Predict
sample_scaled = scaler.transform(sample_features)
predicted_temp = model.predict(sample_scaled)[0]

print("\nSample Weather Conditions:")
print("-" * 60)
for col in feature_columns:
    print(f"{col:20s}: {sample_features[col].values[0]:.2f}")

print("\nPrediction Results:")
print("-" * 60)
print(f"Actual Temperature:    {actual_temp:.2f}°C")
print(f"Predicted Temperature: {predicted_temp:.2f}°C")
print(f"Difference:            {abs(actual_temp - predicted_temp):.2f}°C")

print("\n" + "=" * 60)
print("  MODEL TRAINING COMPLETED SUCCESSFULLY!")
print("=" * 60)
print("\nNext steps:")
print("1. Start Flask API: python app.py")
print("2. Test prediction API: POST /api/predict-temperature/")
print("3. Check model performance: GET /api/model-performance/")