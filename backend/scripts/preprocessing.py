import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import pickle
import os
import sys

def preprocess_weather_data(input_file="data/HanoiWeatherHourly.csv", 
                            output_file="data/weather_preprocessed.csv",
                            save_scaler=True):
        
    try:
        # 1. Load dữ liệu
        df = pd.read_csv(input_file)
        
        # Kiểm tra và parse timestamp
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp').reset_index(drop=True)
            print(f"Dữ liệu từ {df['timestamp'].min()} đến {df['timestamp'].max()}")
        
        # 2. One-hot encoding cho weathercode
        df = pd.get_dummies(df, columns=['weathercode'], prefix='w')
        dummy_cols = [col for col in df.columns if col.startswith('w_')]
        df[dummy_cols] = df[dummy_cols].astype(int)
        print(f"   Tạo {len(dummy_cols)} dummy variables")
        
        # 3. Xử lý dữ liệu chu kỳ cho winddirection
        radians = np.deg2rad(df['winddirection'])
        df['wind_x'] = np.sin(radians)
        df['wind_y'] = np.cos(radians)
        df.drop(columns=['winddirection'], inplace=True)
        
        # 4. Xử lý ngoại lệ (outliers)
        for col in ['windspeed', 'radiation']:
            if col in df.columns:
                lower = df[col].quantile(0.01)
                upper = df[col].quantile(0.99)
                df[col] = df[col].clip(lower, upper)
                print(f"   {col}: clipped [{lower:.2f}, {upper:.2f}]")
        
        # 5. Xử lý missing values
        missing_before = df.isnull().sum().sum()
        if missing_before > 0:
            print(f"   Tìm thấy {missing_before} missing values")
            for col in df.columns:
                if df[col].isnull().sum() > 0:
                    if df[col].dtype in [np.float64, np.int64]:
                        df[col].fillna(df[col].mean(), inplace=True)
                    else:
                        df[col].fillna(df[col].mode()[0], inplace=True)
            print(f"   Đã xử lý xong")
        else:
            print(f"   Không có missing values")
        
        # 6. Chuẩn hóa các biến numerical (KHÔNG chuẩn hóa timestamp)
        numerical_cols = ['temperature', 'humidity', 'precipitation', 
                         'cloud_cover', 'windspeed', 'pressure_msl', 
                         'radiation', 'wind_x', 'wind_y']
        
        # Chỉ chuẩn hóa các cột tồn tại
        numerical_cols = [col for col in numerical_cols if col in df.columns]
        
        scaler = StandardScaler()
        df[numerical_cols] = scaler.fit_transform(df[numerical_cols])
        
        print(f"   Chuẩn hóa {len(numerical_cols)} biến")
        
        # 7. Lưu scaler 
        if save_scaler:
            os.makedirs('model', exist_ok=True)
            with open('model/preprocessing_scaler.pkl', 'wb') as f:
                pickle.dump(scaler, f)
            print(f" Đã lưu scaler vào model/preprocessing_scaler.pkl")
        
        # 8. Lưu kết quả
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        df.to_csv(output_file, index=False)
        

        
        # Hiển thị thông tin cột
        print("\n Các cột trong dữ liệu:")
        for col in df.columns:
            print(f"   - {col}")
        
        return True
        
    except Exception as e:
        print(f" Lỗi trong quá trình tiền xử lý: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = preprocess_weather_data()
    sys.exit(0 if success else 1)