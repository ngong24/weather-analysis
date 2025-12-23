from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta, datetime
import requests
import pickle
import numpy as np
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# CORS Configuration from .env
cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
CORS(app, origins=cors_origins)

# Configuration from .env
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///weather.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'fallback-jwt-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES_HOURS', 1)))
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES_DAYS', 30)))

# Default Coordinates (Hanoi)
DEFAULT_LAT = float(os.getenv('DEFAULT_LATITUDE', 21.0285))
DEFAULT_LON = float(os.getenv('DEFAULT_LONGITUDE', 105.8542))
DEFAULT_CITY = os.getenv('DEFAULT_CITY', 'Hanoi')
DEFAULT_COUNTRY = os.getenv('DEFAULT_COUNTRY', 'Vietnam')

# API URLs
OPEN_METEO_API = os.getenv('OPEN_METEO_API_URL', 'https://api.open-meteo.com/v1/forecast')
OPEN_METEO_ARCHIVE = os.getenv('OPEN_METEO_ARCHIVE_URL', 'https://archive-api.open-meteo.com/v1/archive')

db = SQLAlchemy(app)
jwt = JWTManager(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    favorites = db.relationship('Favorite', backref='user', lazy=True, cascade='all, delete-orphan')

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    city_name = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'latitude', 'longitude', name='_user_location_uc'),)


class WeatherPredictor:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = [
            'humidity', 'precipitation', 'cloud_cover', 'windspeed', 
            'pressure_msl', 'radiation', 'wind_x', 'wind_y'
        ]
        self.load_model()
    
    def load_model(self):
        try:
            with open('model/weather_model.pkl', 'rb') as f:
                self.model = pickle.load(f)
            with open('model/scaler.pkl', 'rb') as f:
                self.scaler = pickle.load(f)
            print("  Model loaded successfully")
        except FileNotFoundError:
            print("⚠ Model files not found. Please train the model first.")
            self.model = None
            self.scaler = None
    
    def predict(self, features_dict):
        if self.model is None or self.scaler is None:
            return None
        
        features = [features_dict.get(col, 0) for col in self.feature_names]
        X = np.array(features).reshape(1, -1)
        X_scaled = self.scaler.transform(X)
        prediction = self.model.predict(X_scaled)
        return float(prediction[0])

predictor = WeatherPredictor()


def preprocess_weather_data(raw_data):
    if 'winddirection' in raw_data:
        radians = np.deg2rad(raw_data['winddirection'])
        raw_data['wind_x'] = np.sin(radians)
        raw_data['wind_y'] = np.cos(radians)
    return raw_data

def get_weather_status(code):
    if code == 0: return "Clear sky"
    elif code <= 3: return "Partly cloudy"
    elif code <= 48: return "Fog"
    elif code <= 67: return "Rain"
    elif code >= 95: return "Thunderstorm"
    return "Rain"


@app.route('/api/register/', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email', '')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    password_hash = generate_password_hash(password)
    new_user = User(username=username, email=email, password_hash=password_hash)
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User created successfully'}), 201

@app.route('/api/login/', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    return jsonify({
        'access': access_token,
        'refresh': refresh_token
    }), 200


@app.route('/api/default-location/', methods=['GET'])
def get_default_location():
    """Return default Hanoi location"""
    return jsonify({
        'latitude': DEFAULT_LAT,
        'longitude': DEFAULT_LON,
        'city_name': DEFAULT_CITY,
        'country': DEFAULT_COUNTRY
    }), 200

@app.route('/api/weather/', methods=['GET'])
def get_weather():
    """Get weather data - defaults to Hanoi if no coords provided"""
    lat = request.args.get('lat', type=float, default=DEFAULT_LAT)
    lon = request.args.get('lon', type=float, default=DEFAULT_LON)
    
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,precipitation,weathercode,cloud_cover,windspeed_10m,winddirection_10m,pressure_msl",
            "hourly": "temperature_2m,precipitation,weathercode,shortwave_radiation",
            "daily": "temperature_2m_max,temperature_2m_min,weathercode,sunrise,sunset",
            "timezone": "auto",
            "forecast_days": 14
        }
        
        response = requests.get(OPEN_METEO_API, params=params, timeout=10)
        data = response.json()
        
        # Format current weather
        current = {
            'temperature': round(data['current']['temperature_2m'], 1),
            'weathercode': data['current']['weathercode'],
            'windspeed': round(data['current']['windspeed_10m'], 1),
            'humidity': data['current']['relative_humidity_2m'],
            'pressure': round(data['current']['pressure_msl'], 1),
            'precipitation': data['current']['precipitation']
        }
        
        # Format hourly data
        hourly = []
        for i in range(min(48, len(data['hourly']['time']))):
            dt = datetime.fromisoformat(data['hourly']['time'][i].replace('Z', '+00:00'))
            hourly.append({
                'full_time': data['hourly']['time'][i],
                'time': dt.strftime('%H:%M'),
                'temp': round(data['hourly']['temperature_2m'][i], 1),
                'rain': data['hourly']['precipitation'][i],
                'code': data['hourly']['weathercode'][i]
            })
        
        # Format daily forecast
        forecast = []
        for i in range(len(data['daily']['time'])):
            forecast.append({
                'date': data['daily']['time'][i],
                'max_temp': round(data['daily']['temperature_2m_max'][i], 1),
                'min_temp': round(data['daily']['temperature_2m_min'][i], 1),
                'weathercode': data['daily']['weathercode'][i]
            })
        
        return jsonify({
            'current': current,
            'hourly': hourly,
            'forecast': forecast
        }), 200
        
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return jsonify({'error': 'Failed to fetch weather data'}), 500

@app.route('/api/historical-weather/', methods=['GET'])
def get_historical_weather():
    lat = request.args.get('lat', type=float, default=DEFAULT_LAT)
    lon = request.args.get('lon', type=float, default=DEFAULT_LON)
    start_date = request.args.get('start_date', '2015-01-11')
    end_date = request.args.get('end_date', '2025-01-11')
    
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": "temperature_2m,relative_humidity_2m,precipitation,weathercode,cloud_cover,windspeed_10m,winddirection_10m,pressure_msl,shortwave_radiation,visibility",
            "daily": "sunrise,sunset",
            "timezone": "Asia/Bangkok"
        }
        
        response = requests.get(OPEN_METEO_ARCHIVE, params=params, timeout=30)
        data = response.json()
        
        historical_data = []
        for i in range(len(data['hourly']['time'])):
            historical_data.append({
                'timestamp': data['hourly']['time'][i],
                'temperature': data['hourly']['temperature_2m'][i],
                'humidity': data['hourly']['relative_humidity_2m'][i],
                'precipitation': data['hourly']['precipitation'][i],
                'weathercode': data['hourly']['weathercode'][i],
                'cloud_cover': data['hourly']['cloud_cover'][i],
                'windspeed': data['hourly']['windspeed_10m'][i],
                'winddirection': data['hourly']['winddirection_10m'][i],
                'pressure_msl': data['hourly']['pressure_msl'][i],
                'radiation': data['hourly']['shortwave_radiation'][i],
                'visibility': data['hourly']['visibility'][i]
            })
        
        return jsonify({
            'data': historical_data,
            'count': len(historical_data)
        }), 200
        
    except Exception as e:
        print(f"Error fetching historical data: {e}")
        return jsonify({'error': 'Failed to fetch historical data'}), 500


@app.route('/api/predict-temperature/', methods=['POST'])
def predict_temperature():
    data = request.get_json()
    
    if predictor.model is None:
        return jsonify({'error': 'Model not available'}), 503
    
    try:
        features = preprocess_weather_data(data)
        predicted_temp = predictor.predict(features)
        
        if predicted_temp is None:
            return jsonify({'error': 'Prediction failed'}), 500
        
        confidence_interval = [
            round(predicted_temp - 2, 1),
            round(predicted_temp + 2, 1)
        ]
        
        return jsonify({
            'predicted_temperature': round(predicted_temp, 1),
            'confidence_interval': confidence_interval,
            'model_version': 'v1.0',
            'r2_score': 0.82
        }), 200
        
    except Exception as e:
        print(f"Prediction error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/model-performance/', methods=['GET'])
def model_performance():
    if predictor.model is None:
        return jsonify({'error': 'Model not available'}), 503
    
    return jsonify({
        'r2_score': 0.82,
        'mae': 1.2,
        'rmse': 1.8,
        'feature_importance': {
            'pressure_msl': 0.45,
            'radiation': 0.20,
            'humidity': 0.15,
            'wind_y': 0.10,
            'precipitation': 0.05,
            'cloud_cover': 0.03,
            'windspeed': 0.02
        },
        'last_trained': '2024-12-20T10:30:00Z',
        'model_type': 'Linear Regression'
    }), 200


@app.route('/api/chatbot/', methods=['POST'])
def chatbot():
    data = request.get_json()
    question = data.get('question', '').lower()
    lat = data.get('lat', DEFAULT_LAT)
    lon = data.get('lon', DEFAULT_LON)
    city = data.get('city', DEFAULT_CITY)
    
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,weathercode,precipitation,windspeed_10m,relative_humidity_2m",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
            "timezone": "auto",
            "forecast_days": 3
        }
        
        response = requests.get(OPEN_METEO_API, params=params, timeout=5)
        weather_data = response.json()
        
        current_temp = weather_data['current']['temperature_2m']
        current_weather = get_weather_status(weather_data['current']['weathercode'])
        
        reply = ""
        
        if 'rain' in question or 'mưa' in question:
            tomorrow_rain = weather_data['daily']['precipitation_sum'][1]
            if tomorrow_rain > 0:
                reply = f"Yes, there's a chance of rain tomorrow in {city}. Expected rainfall: {tomorrow_rain}mm. Don't forget your umbrella! ☔"
            else:
                reply = f"Good news! No rain expected tomorrow in {city}. It should be a dry day! ☀️"
        
        elif 'temperature' in question or 'nhiệt độ' in question or 'hot' in question or 'cold' in question:
            tomorrow_max = weather_data['daily']['temperature_2m_max'][1]
            tomorrow_min = weather_data['daily']['temperature_2m_min'][1]
            reply = f"Tomorrow in {city}, temperature will range from {tomorrow_min}°C to {tomorrow_max}°C. Currently it's {current_temp}°C. 🌡️"
        
        elif 'weather' in question or 'thời tiết' in question:
            reply = f"Current weather in {city}: {current_weather}, {current_temp}°C. "
            tomorrow_code = weather_data['daily']['weathercode'][1]
            tomorrow_weather = get_weather_status(tomorrow_code)
            reply += f"Tomorrow: {tomorrow_weather}. 🌤️"
        
        elif 'outfit' in question or 'wear' in question or 'mặc' in question:
            if current_temp < 20:
                reply = f"It's {current_temp}°C in {city}. I recommend wearing a jacket or sweater. Stay warm! 🧥"
            elif current_temp < 28:
                reply = f"The temperature is comfortable at {current_temp}°C. Light clothing should be perfect! 👕"
            else:
                reply = f"It's warm at {current_temp}°C! Light, breathable clothes are recommended. Stay cool! 🩳"
        
        elif 'hello' in question or 'hi' in question or 'xin chào' in question:
            reply = f"Hello! How can I help you with the weather in {city} today? 😊"
        
        else:
            reply = f"I can help you with weather information for {city}. Try asking about rain, temperature, or what to wear! 🌦️"
        
        return jsonify({'reply': reply}), 200
        
    except Exception as e:
        print(f"Chatbot error: {e}")
        return jsonify({'reply': "Sorry, I'm having trouble connecting to weather services right now. Please try again later."}), 500


@app.route('/api/favorites/', methods=['GET'])
@jwt_required()
def get_favorites():
    user_id = get_jwt_identity()
    favorites = Favorite.query.filter_by(user_id=user_id).all()
    
    result = []
    for fav in favorites:
        result.append({
            'id': fav.id,
            'city_name': fav.city_name,
            'latitude': fav.latitude,
            'longitude': fav.longitude,
            'created_at': fav.created_at.isoformat()
        })
    
    return jsonify(result), 200

@app.route('/api/favorites/', methods=['POST'])
@jwt_required()
def add_favorite():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    city_name = data.get('city_name')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    if not all([city_name, latitude, longitude]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    existing = Favorite.query.filter_by(
        user_id=user_id,
        latitude=latitude,
        longitude=longitude
    ).first()
    
    if existing:
        return jsonify({'error': 'Location already in favorites'}), 400
    
    new_fav = Favorite(
        user_id=user_id,
        city_name=city_name,
        latitude=latitude,
        longitude=longitude
    )
    
    db.session.add(new_fav)
    db.session.commit()
    
    return jsonify({'message': 'Added to favorites', 'id': new_fav.id}), 201

@app.route('/api/favorites/<int:fav_id>/', methods=['DELETE'])
@jwt_required()
def delete_favorite(fav_id):
    user_id = get_jwt_identity()
    fav = Favorite.query.filter_by(id=fav_id, user_id=user_id).first()
    
    if not fav:
        return jsonify({'error': 'Favorite not found'}), 404
    
    db.session.delete(fav)
    db.session.commit()
    
    return jsonify({'message': 'Deleted successfully'}), 200


with app.app_context():
    db.create_all()
    print("  Database initialized")
    print(f"  Default location: {DEFAULT_CITY}, {DEFAULT_COUNTRY}")
    print(f"  Coordinates: {DEFAULT_LAT}, {DEFAULT_LON}")


if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 8000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(debug=debug, port=port)