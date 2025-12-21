// src/pages/HomePage.js
import React, { useState, useEffect, useContext } from 'react';
import AuthContext from '../context/AuthContext';
import api from '../utils/api';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import { Link } from 'react-router-dom';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { 
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import AiAssistant from '../components/AiAssistant'; 
import SearchBar from '../components/SearchBar';

// --- setup leaflet---
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
    iconUrl: require('leaflet/dist/images/marker-icon.png'),
    shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

function ChangeView({ center }) {
    const map = useMap();
    map.setView(center, 11);
    return null;
}

// --- helper functions ---
const getWeatherStatus = (code) => {
    if (code === undefined) return ""; if (code === 0) return "Clear sky"; if (code <= 3) return "Partly cloudy"; if (code <= 48) return "Fog"; if (code <= 67) return "Rain"; if (code >= 95) return "Thunderstorm"; return "Rain";
};
const formatDate = (dateStr) => { if(!dateStr) return ""; const [y,m,d] = dateStr.split("-"); return `${d}/${m}`; };
const getWeatherIcon = (code) => {
    if (code === 0) return "https://cdn-icons-png.flaticon.com/512/869/869869.png"; 
    if (code <= 3) return "https://cdn-icons-png.flaticon.com/512/1163/1163661.png";
    if (code <= 67) return "https://cdn-icons-png.flaticon.com/512/1163/1163627.png";
    return "https://cdn-icons-png.flaticon.com/512/1163/1163636.png";
};

// --- Custom Dot ---
const CustomizedDot = (props) => {
    const { cx, cy, payload } = props;
    const iconUrl = getWeatherIcon(payload.code);
    return (
        <g>
            <foreignObject x={cx - 15} y={cy - 35} width={30} height={30}>
                <img src={iconUrl} alt="icon" style={{ width: '100%', height: '100%' }} />
            </foreignObject>
            <text x={cx} y={cy + 15} dy={4} textAnchor="middle" fill="#333" fontSize={13} fontWeight="400">
                {payload.temp}°
            </text>
        </g>
    );
};

// --- Custom XAxis Tick ---
const CustomXAxisTick = ({ x, y, payload }) => {
    const timeStr = payload.value; 
    return (
        <g transform={`translate(${x},${y})`}>
            <text x={0} y={0} dy={16} textAnchor="middle" fill="#666" fontSize={12} fontWeight={300}>
                {timeStr}
            </text>
        </g>
    );
};


// --- Custom Tooltip ---
const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const fullDate = payload[0].payload.full_time ? payload[0].payload.full_time.split(' ')[0] : '';
      return (
        <div style={{
            background: 'rgba(255, 255, 255, 0.95)',
            border: 'none',
            borderRadius: '12px',
            padding: '10px 15px',
            boxShadow: '0 4px 15px rgba(0,0,0,0.1)',
            color: '#333'
        }}>
          <p style={{ margin: 0, fontWeight: '500', fontSize: '13px', color:'#888' }}>{formatDate(fullDate)}</p>
          <p style={{ margin: 0, fontWeight: '500', fontSize: '15px', marginBottom: 5 }}>{label}</p>
          {payload.map((entry, index) => (
            <p key={index} style={{ margin: 0, color: entry.color, fontSize: '13px', fontWeight: '300' }}>
              {entry.name}: {entry.value} {entry.unit}
            </p>
          ))}
        </div>
      );
    }
    return null;
};

const styles = `
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: inherit; font-weight: 300; }
    
    .dashboard-container { 
        min-height: 100vh; 
        
        /* Gradient nền: Cam nhạt ở đầu -> Xanh nhạt ở dưới */
        background: linear-gradient(
            180deg, 
            #fff7e6 0%,      
            #fff7e6 120px,   
            #d4ebf2 450px,   
            #d4ebf2 100%     
        );

        color: #333; 
        padding: 30px; 
        display: flex; 
        flex-direction: column; 
        gap: 20px; 
        font-family: 'Segoe UI', sans-serif; 
    }
    
    /* Header */
    .dashboard-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
    .search-wrap { flex: 1; max-width: 500px; }
    
    .search-bar { display: flex; align-items: center; background: rgba(255,255,255,0.7); padding: 10px 20px; border-radius: 30px; backdrop-filter: blur(5px); box-shadow: 0 4px 15px rgba(0,0,0,0.05); transition: 0.3s; }
    .search-bar:focus-within { background: rgba(255,255,255,1); box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
    .search-bar input { background: transparent; border: none; color: #333; width: 100%; outline: none; margin-left: 10px; font-size: 16px; font-weight: 300; }
    .search-bar button { background: transparent; border: none; cursor: pointer; font-size: 18px; color: #555; }

    .auth-section { display: flex; gap: 15px; align-items: center; }

    .btn-green {
        background: #FFD8B5;  
        border: none;
        color: #444;          
        padding: 8px 20px;
        border-radius: 20px;
        cursor: pointer;
        font-weight: inherit; 
        box-shadow: 0 4px 15px rgba(255, 216, 181, 0.6); 
        transition: all 0.2s ease-in-out;
        display: inline-flex;
        align-items: center; 
        justify-content: center;
        gap: 5px;
        text-decoration: none;
        letter-spacing: 0.5px;
        font-size: 15px;
    }
    .btn-green:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 216, 181, 0.8);
        background: #FFC590; /* Đậm hơn chút khi hover */
    }

    /* --- LAYOUT --- */
    .main-grid { display: grid; grid-template-columns: 2.5fr 1fr; gap: 20px; align-items: start; }
    .left-column { display: flex; flex-direction: column; gap: 20px; min-width: 0; }
    .right-column { display: flex; flex-direction: column; gap: 20px; min-width: 0; }

    /* CARD STYLES */
    .weather-main-card { background: linear-gradient(145deg, rgba(255,255,255,0.9), rgba(245,245,245,0.9)); border-radius: 25px; padding: 30px; display: flex; flex-direction: column; justify-content: space-between; min-height: 350px; box-shadow: 0 10px 40px -10px rgba(0,0,0,0.1); color: #333; border: 1px solid rgba(255,255,255,1); }
    .weather-header { display: flex; justify-content: space-between; }
    
    .temp-section { display: flex; align-items: center; margin: 20px 0; }
    .temp-number { font-size: 85px; font-weight: 100; line-height: 1; color: #333; letter-spacing: -2px; }
    .metrics-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; background: rgba(0,0,0,0.03); padding: 15px; border-radius: 15px; margin-top: auto; }
    .metric-item { text-align: center; color: #666; font-size: 13px; font-weight: 300; } 
    .metric-value { font-weight: 500; color: #000; font-size: 15px; margin-top: 3px; }
    
    .map-card { background: #fff; border-radius: 25px; overflow: hidden; height: 350px; border: 4px solid #fff; box-shadow: 0 10px 40px -10px rgba(0,0,0,0.1); }

    .forecast-section { margin-top: 0; }
    .forecast-row { display: grid; grid-template-columns: repeat(14, 1fr); gap: 10px; }
    .forecast-item { background: rgba(255,255,255,0.6); padding: 15px 10px; border-radius: 18px; text-align: center; display: flex; flex-direction: column; align-items: center; transition: all 0.2s; cursor: pointer; border: 1px solid rgba(255,255,255,0.5); box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .forecast-item:hover { transform: translateY(-5px); background: #fff; }
    .forecast-item.active { background: #fff; border: 1px solid rgba(0,0,0,0.1); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }

    /* CHART SECTION */
    .hourly-section { 
        margin-top: 0; 
        background: rgba(255,255,255,0.7); 
        padding: 25px; 
        border-radius: 25px; 
        height: 400px; 
        display: flex; 
        flex-direction: column; 
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        border: 1px solid rgba(255,255,255,0.8);
    }
    .hourly-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
    
    /* Favorites */
    .favorites-bar { margin-top: 20px; padding-top: 20px; border-top: 1px solid rgba(0,0,0,0.05); }
    .fav-tags { display: flex; gap: 10px; flex-wrap: wrap; }
    .fav-tag { background: rgba(255,255,255,0.8); padding: 8px 18px; border-radius: 20px; cursor: pointer; display: flex; align-items: center; gap: 10px; transition: 0.2s; box-shadow: 0 2px 5px rgba(0,0,0,0.05); color: #444; font-weight: 300; }
    .fav-tag:hover { background: #fff; transform: translateY(-2px); }
    .delete-x { color: #ff6b6b; font-weight: 400; cursor: pointer; margin-left: 5px; padding: 0 5px;}

    @media (max-width: 900px) {
        .main-grid { grid-template-columns: 1fr; }
        .metrics-row { grid-template-columns: repeat(2, 1fr); }
        .forecast-row { display: flex; overflow-x: auto; }
        .forecast-item { min-width: 80px; }
        .map-card { height: 300px; }
    }
`;

const HomePage = () => {
    const { user, logoutUser } = useContext(AuthContext);
    const [citySearch, setCitySearch] = useState('');
    const [weatherData, setWeatherData] = useState(null);
    const [favorites, setFavorites] = useState([]);
    const [mapCenter, setMapCenter] = useState([21.02, 105.85]); 
    const [loading, setLoading] = useState(false);
    const [selectedDate, setSelectedDate] = useState(null);

    useEffect(() => {
        if (user) fetchFavorites();
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(p => getWeatherByCoords(p.coords.latitude, p.coords.longitude));
        }
    }, [user]);

    useEffect(() => {
        if (weatherData && weatherData.forecast.length > 0) {
            setSelectedDate(weatherData.forecast[0].date);
        }
    }, [weatherData]);

    const fetchFavorites = async () => {
        try {
            const res = await api.get('favorites/');
            const listWithTemp = await Promise.all(res.data.map(async (item) => {
                try {
                    const w = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${item.latitude}&longitude=${item.longitude}&current=temperature_2m`);
                    const j = await w.json();
                    return { ...item, current_temp: j.current.temperature_2m };
                } catch {
                    return { ...item, current_temp: null };
                }
            }));
            setFavorites(listWithTemp);
        } catch (error) {
            console.error("Error fetching list:", error);
        }
    };

    const handleSearch = async (e) => {
        e.preventDefault(); setLoading(true);
        try {
            const resGeo = await api.get(`search-city/?city=${citySearch}`);
            if (resGeo.data.length > 0) getWeatherByCoords(resGeo.data[0].latitude, resGeo.data[0].longitude, resGeo.data[0].name, resGeo.data[0].country);
            else alert("No results found!");
        } catch { alert("Something went wrong!"); } setLoading(false);
    };

    const getWeatherByCoords = async (lat, lon, name="Your location", country="") => {
        try {
            const res = await api.get(`weather/?lat=${lat}&lon=${lon}`);
            setWeatherData({ ...res.data, city_name: name, country: country, lat: lat, lon: lon });
            setMapCenter([lat, lon]);
        } catch { console.error("Err"); }
    };
    
    const addToFavorites = async () => {
        if (!user) { alert("Login required to save!"); return; }
        if (!weatherData) return;
        const payload = { city_name: weatherData.city_name, latitude: weatherData.lat, longitude: weatherData.lon };
        try {
            await api.post('favorites/', payload);
            alert(`Save "${weatherData.city_name}" success!`);
            fetchFavorites(); 
        } catch (error) {
            if (error.response && error.response.status === 400) alert("This location might already be in your list!");
            else alert("Failed to save. Please try again.");
        }
    };

    const removeFavorite = async (id, e) => { 
        e.stopPropagation(); 
        if(!window.confirm("Are you sure you want to delete this location?")) return; 
        try{ await api.delete(`favorites/${id}/`); fetchFavorites(); } catch { alert("Failed to delete!"); } 
    };

    const getHourlyContinuous = () => {
        if (!weatherData || !weatherData.hourly || !selectedDate) return [];
        const startIndex = weatherData.hourly.findIndex(h => h.full_time.startsWith(selectedDate));
        if (startIndex === -1) return [];
        return weatherData.hourly.slice(startIndex, startIndex + 25);
    };
    
    const hourlyDisplay = getHourlyContinuous();

    return (
        <div className="dashboard-container">
            <style>{styles}</style>
            <header className="dashboard-header">
                <div className="search-wrap">
                    <SearchBar onSelectLocation={(loc) => getWeatherByCoords(loc.latitude, loc.longitude, loc.name, loc.country)} user={user} />
                </div>
                <div className="auth-section">
                    {user ? (
                        <>
                            <span style={{fontWeight:'500', color: '#555'}}>{user.username}</span>
                            <button onClick={logoutUser} className="btn-green">Logout</button>
                        </> 
                    ) : (
                        <>
                            <Link to="/login" className="btn-green" style={{marginRight: 10}}>Login</Link>
                            <Link to="/register" className="btn-green">Reg</Link>
                        </>
                    )}
                </div>
            </header>

            {weatherData ? (
                <div className="main-grid">
                    <div className="left-column">
                        <div className="weather-main-card">
                            <div className="weather-header">
                                <div><h2 style={{fontWeight:'400'}}>{weatherData.city_name}</h2><p style={{color:'#666', marginTop: 5, fontWeight:'300'}}>{weatherData.country}</p></div>
                                <button onClick={addToFavorites} className="btn-green">Save</button>
                            </div>
                            <div className="temp-section">
                                <img src={getWeatherIcon(weatherData.current.weathercode)} width="100" alt="icon"/>
                                <div className="temp-details">
                                    <span className="temp-number">{weatherData.current.temperature}°</span>
                                    <div style={{fontSize:'22px', fontWeight: '300', color: '#555'}}>{getWeatherStatus(weatherData.current.weathercode)}</div>
                                </div>
                            </div>
                            <div className="metrics-row">
                                <div className="metric-item"><div>Wind</div><div className="metric-value">{weatherData.current.windspeed} km/h</div></div>
                                <div className="metric-item"><div>Humidity</div><div className="metric-value">{weatherData.current.humidity}%</div></div>
                                <div className="metric-item"><div>Pressure</div><div className="metric-value">{weatherData.current.pressure} hPa</div></div>
                                <div className="metric-item"><div>Rain</div><div className="metric-value">{weatherData.current.precipitation} mm</div></div>
                            </div>
                        </div>

                        <div className="forecast-section">
                            <h3 style={{marginBottom:15, color:'#444', fontWeight: '400'}}>  Forecast 14 days </h3>
                            <div className="forecast-row">
                                {weatherData.forecast.map((day, index) => (
                                    <div 
                                        key={index} 
                                        className={`forecast-item ${selectedDate === day.date ? 'active' : ''}`}
                                        onClick={() => setSelectedDate(day.date)}
                                    >
                                        <span style={{fontWeight:'400', color:'#555'}}>{formatDate(day.date)}</span>
                                        <img src={getWeatherIcon(day.weathercode || 3)} width="40" style={{margin:'10px 0'}} alt="d"/>
                                        <b style={{color:'#333', fontSize:'18px', fontWeight: '400'}}>{day.max_temp}°</b>
                                        <span style={{fontSize:13, opacity:0.7, color:'#666'}}>{day.min_temp}°</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {hourlyDisplay.length > 0 && (
                            <div className="hourly-section">
                                <div className="hourly-header">
                                    <h3 style={{color:'#444', fontWeight: '400'}}> Forecast 24 hours {formatDate(selectedDate)}</h3>
                                </div>
                                <div style={{ width: '100%', height: '100%', fontSize: '12px' }}>
                                    <ResponsiveContainer width="100%" height="100%">
                                        <LineChart
                                            data={hourlyDisplay}
                                            margin={{ top: 40, right: 20, left: 0, bottom: 20 }}
                                        >
                                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.05)" vertical={false} />
                                            <XAxis 
                                                dataKey="time" 
                                                stroke="#888" 
                                                tick={<CustomXAxisTick />}
                                                interval={1} 
                                                dy={10}
                                            />
                                            <YAxis yAxisId="left" hide={true} domain={['dataMin - 2', 'dataMax + 2']} />
                                            <YAxis yAxisId="right" orientation="right" hide={true} domain={[0, 'auto']} />

                                            <Tooltip content={<CustomTooltip />} />
                                            <Legend verticalAlign="top" height={36} wrapperStyle={{top: -30}}/>
                                            
                                            <Line 
                                                yAxisId="left"
                                                type="monotone" 
                                                dataKey="temp" 
                                                name="Temperature" 
                                                unit="°C"
                                                stroke="#ffcc00" 
                                                strokeWidth={3} 
                                                dot={<CustomizedDot />}
                                                activeDot={{ r: 6 }} 
                                            />
                                            <Line 
                                                yAxisId="right"
                                                type="monotone" 
                                                dataKey="rain" 
                                                name="Precipitation" 
                                                unit="mm"
                                                stroke="#3498db" 
                                                strokeWidth={2} 
                                                strokeDasharray="5 5"
                                                dot={{ r: 3, fill: '#3498db' }}
                                                activeDot={{ r: 5 }}
                                            />
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="right-column">
                        <div className="map-card">
                            <MapContainer center={mapCenter} zoom={11} style={{ height: '100%', width: '100%' }} zoomControl={false}>
                                <ChangeView center={mapCenter} />
                                <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                                <Marker position={mapCenter}><Popup>{weatherData.city_name}</Popup></Marker>
                            </MapContainer>
                        </div>
                    </div>
                </div>
            ) : (
                <div style={{textAlign:'center', marginTop: 80, opacity: 0.6, color: '#555'}}><h2>Enter city name...</h2></div>
            )}

            {user && favorites.length > 0 && (
                <div className="favorites-bar">
                    <h4 style={{color:'#555', fontWeight:'400'}}>Saved ({favorites.length})</h4>
                    <div className="fav-tags">
                        {favorites.map(fav => (
                            <div key={fav.id} className="fav-tag" onClick={() => getWeatherByCoords(fav.latitude, fav.longitude, fav.city_name)}>
                                {fav.city_name} <b>{fav.current_temp ? fav.current_temp : '--'}°</b> 
                                <span className="delete-x" onClick={(e)=>removeFavorite(fav.id,e)}>×</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {weatherData && (
                <AiAssistant lat={weatherData.lat} lon={weatherData.lon} city={weatherData.city_name} />
            )}

        </div>
    );
};

export default HomePage;