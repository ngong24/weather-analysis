// src/context/AuthContext.js
import { createContext, useState, useEffect } from 'react';
import { jwtDecode } from "jwt-decode";
import { useNavigate } from 'react-router-dom';
import api from '../utils/api'; 

const AuthContext = createContext();

export default AuthContext;

export const AuthProvider = ({ children }) => {
    // Lấy token từ localStorage nếu có (để F5 không bị mất đăng nhập)
    let [authTokens, setAuthTokens] = useState(() => 
        localStorage.getItem('authTokens') ? JSON.parse(localStorage.getItem('authTokens')) : null
    );
    
    let [user, setUser] = useState(() => 
        localStorage.getItem('authTokens') ? jwtDecode(localStorage.getItem('authTokens')) : null
    );

    const navigate = useNavigate();

    // Hàm Đăng nhập
    let loginUser = async (e) => {
        e.preventDefault();
        try {
            // Gọi API Login của Django
            let response = await api.post('login/', {
                username: e.target.username.value,
                password: e.target.password.value
            });

            if (response.status === 200) {
                setAuthTokens(response.data);
                setUser(jwtDecode(response.data.access));
                localStorage.setItem('authTokens', JSON.stringify(response.data));
                navigate('/'); // Chuyển về trang chủ sau khi login xong
            } else {
                alert('Sai tài khoản hoặc mật khẩu!');
            }
        } catch (error) {
            alert('Đăng nhập thất bại! Kiểm tra lại Backend.');
            console.error(error);
        }
    };

    // Hàm Đăng xuất
    let logoutUser = () => {
        setAuthTokens(null);
        setUser(null);
        localStorage.removeItem('authTokens');
        navigate('/login');
    };

    // Hàm Đăng ký
    let registerUser = async (username, password, email) => {
        try {
            await api.post('register/', { username, password, email });
            alert("Đăng ký thành công! Hãy đăng nhập.");
            navigate('/login');
        } catch (error) {
            alert("Đăng ký thất bại (Có thể tên đã tồn tại)");
        }
    };

    let contextData = {
        user: user,
        authTokens: authTokens,
        loginUser: loginUser,
        logoutUser: logoutUser,
        registerUser: registerUser
    };

    return (
        <AuthContext.Provider value={contextData}>
            {children}
        </AuthContext.Provider>
    );
};