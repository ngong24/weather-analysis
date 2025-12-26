import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

def collect_weather_data(days_back=365*10, output_file="data/HanoiWeatherHourly.csv"):
      
    # Tính toán ngày bắt đầu và kết thúc
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # Đảm bảo không vượt quá giới hạn API (từ 2015)
    if start_date.year < 2015:
        start_date = datetime(2015, 1, 1)
        
    url = "https://archive-api.open-meteo.com/v1/archive"
    
    params = {
        "latitude": 21.0285,
        "longitude": 105.8542,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "hourly": (
            "temperature_2m,relative_humidity_2m,precipitation,weathercode,"
            "cloud_cover,windspeed_10m,winddirection_10m,"
            "pressure_msl,shortwave_radiation"
        ),
        "timezone": "Asia/Bangkok"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Tạo DataFrame
        df = pd.DataFrame({
            "timestamp": data["hourly"]["time"],
            "temperature": data["hourly"]["temperature_2m"],
            "humidity": data["hourly"]["relative_humidity_2m"],
            "precipitation": data["hourly"]["precipitation"],
            "weathercode": data["hourly"]["weathercode"],
            "cloud_cover": data["hourly"]["cloud_cover"],
            "windspeed": data["hourly"]["windspeed_10m"],
            "winddirection": data["hourly"]["winddirection_10m"],
            "pressure_msl": data["hourly"]["pressure_msl"],
            "radiation": data["hourly"]["shortwave_radiation"]
        })
        
        # Xử lý missing values
        df = df.dropna()
        
        # Tạo thư mục nếu chưa có
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Lưu file
        df.to_csv(output_file, index=False)
        
        print(f"Thống kê cơ bản:")
        print(df.describe())
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gọi API: {e}")
        return False
    except Exception as e:
        print(f"Lỗi không xác định: {e}")
        return False

if __name__ == "__main__":
    # Có thể truyền số ngày qua command line
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 365*10
    success = collect_weather_data(days_back=days)
    sys.exit(0 if success else 1)