// src/App.js (Sửa lại)
import { Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import HomePage from './pages/HomePage'; // <--- Import file thật này

function App() {
  return (
    <div className="App">
      <AuthProvider>
        <Routes>
          {/* Trang chủ (Dashboard) */}
          <Route path="/" element={<HomePage />} /> 
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Routes>
      </AuthProvider>
    </div>
  );
}

export default App;