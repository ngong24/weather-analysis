import React, { useContext, useState } from 'react';
import AuthContext from '../context/AuthContext';
import { Link } from 'react-router-dom';

const styles = `
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', sans-serif; font-weight: 300; }
    
    .auth-container {
        min-height: 100vh;
        background: linear-gradient(180deg, #fff7e6 0%, #fff7e6 120px, #d4ebf2 450px, #d4ebf2 100%);
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 20px;
    }

    .auth-card {
        background: rgba(255, 255, 255, 0.85);
        padding: 40px;
        border-radius: 25px;
        backdrop-filter: blur(12px);
        box-shadow: 0 10px 40px -10px rgba(0,0,0,0.1);
        border: 1px solid rgba(255, 255, 255, 1);
        width: 100%;
        max-width: 400px;
        text-align: center;
        color: #333;
    }

    .auth-card h2 { margin-bottom: 10px; font-size: 28px; font-weight: 400; color: #444; }
    .sub-text { font-size: 14px; color: #666; margin-bottom: 30px; }

    .form-group { margin-bottom: 15px; text-align: left; }

    .form-input {
        width: 100%;
        padding: 12px 20px;
        border-radius: 30px;
        border: 1px solid rgba(0, 0, 0, 0.1);
        background: #fff;
        color: #333;
        font-size: 15px;
        outline: none;
        transition: all 0.3s;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }

    .form-input::placeholder { color: #999; }
    .form-input:focus { border-color: #FFD8B5; box-shadow: 0 4px 10px rgba(255, 216, 181, 0.3); }

    .submit-btn {
        width: 100%;
        padding: 12px;
        border-radius: 30px;
        border: none;
        background: #FFD8B5;
        color: #444;
        font-size: 16px;
        font-weight: 500;
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
        margin-top: 10px;
        box-shadow: 0 4px 15px rgba(255, 216, 181, 0.6);
    }

    .submit-btn:hover { transform: translateY(-2px); background: #FFC590; box-shadow: 0 6px 20px rgba(255, 216, 181, 0.8); }

    .auth-footer { margin-top: 25px; font-size: 14px; color: #666; }
    .auth-link { color: #FFC069; text-decoration: none; font-weight: 500; margin-left: 5px; }
    .auth-link:hover { text-decoration: underline; color: #ffa940; }
`;

const RegisterPage = () => {
    let { registerUser } = useContext(AuthContext);
    const [formData, setFormData] = useState({
        username: '', email: '', password: ''
    });

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        registerUser(formData.username, formData.password, formData.email);
    };

    return (
        <div className="auth-container">
            <style>{styles}</style>

            <div className="auth-card">
                <img 
                    src="https://cdn-icons-png.flaticon.com/512/869/869869.png" 
                    alt="register-logo" 
                    width="70" 
                    style={{marginBottom: '5px'}}
                />
                <h2>Register</h2>
                <p className="sub-text">Join us to explore the weather</p>
                
                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <input 
                            className="form-input"
                            type="text" 
                            name="username" 
                            placeholder="Username" 
                            onChange={handleChange} 
                            required 
                        />
                    </div>
                    <div className="form-group">
                        <input 
                            className="form-input"
                            type="email" 
                            name="email" 
                            placeholder="Email address" 
                            onChange={handleChange} 
                        />
                    </div>
                    <div className="form-group">
                        <input 
                            className="form-input"
                            type="password" 
                            name="password" 
                            placeholder="Password" 
                            onChange={handleChange} 
                            required 
                        />
                    </div>
                    <button type="submit" className="submit-btn">
                        Sign Up
                    </button>
                </form>

                <div className="auth-footer">
                    <p>Already have an account? <Link to="/login" className="auth-link">Login</Link></p>
                </div>
            </div>
        </div>
    );
};

export default RegisterPage;