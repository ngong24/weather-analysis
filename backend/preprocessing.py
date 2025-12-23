import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

# 1. Load dữ liệu
df = pd.read_csv('HanoiWeatherHourly.csv')  # Đường dẫn file gốc
df.drop(columns='visibility',inplace=True)
# 2. One-hot encoding cho weathercode
df = pd.get_dummies(df, columns=['weathercode'], prefix='w')
dummy_cols = [col for col in df.columns if col.startswith('w_')]
df[dummy_cols] = df[dummy_cols].astype(int)

# 3. Xử lý dữ liệu chu kỳ cho winddirection
radians = np.deg2rad(df['winddirection'])
df['wind_x'] = np.sin(radians)
df['wind_y'] = np.cos(radians)
df.drop(columns=['winddirection'], inplace=True)

# 4. Xử lý ngoại lệ cho windspeed và radiation
for col in ['windspeed', 'radiation']:
    lower = df[col].quantile(0.01)
    upper = df[col].quantile(0.99)
    df[col] = df[col].clip(lower, upper)

# 5. Chuẩn hóa các biến numerical
numerical_cols = ['temperature', 'humidity', 'precipitation', 'cloud_cover', 'windspeed', 'pressure_msl', 'radiation', 'wind_x', 'wind_y']
scaler = StandardScaler()
df[numerical_cols] = scaler.fit_transform(df[numerical_cols])

# 6. Kiểm tra missing values
if df.isnull().sum().sum() > 0:
    # Điền giá trị trung bình cho numerical, mode cho categorical nếu có missing
    for col in df.columns:
        if df[col].dtype in [np.float64, np.int64]:
            df[col].fillna(df[col].mean(), inplace=True)
        else:
            df[col].fillna(df[col].mode()[0], inplace=True)

# 7. Lưu kết quả tiền xử lý ra CSV
df.to_csv('weather_preprocessed.csv', index=False)
print('Tiền xử lý hoàn tất. Dữ liệu lưu vào weather_preprocessed.csv')
