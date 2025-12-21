import React, { useContext } from 'react';
import AuthContext from '../context/AuthContext';
import { Link } from 'react-router-dom';

const styles = `
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', sans-serif; font-weight: 300; }
    
    .auth-container {
        min-height: 100vh;
        /* Gradient khớp hoàn toàn với HomePage */
        background: linear-gradient(
            180deg, 
            #fff7e6 0%,      
            #fff7e6 120px,   
            #d4ebf2 450px,   
            #d4ebf2 100%     
        );
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 20px;
    }

    .auth-card {
        background: rgba(255, 255, 255, 0.85); /* Nền trắng mờ */
        padding: 40px;
        border-radius: 25px;
        backdrop-filter: blur(12px);
        box-shadow: 0 10px 40px -10px rgba(0,0,0,0.1);
        border: 1px solid rgba(255, 255, 255, 1);
        width: 100%;
        max-width: 400px;
        text-align: center;
        color: #333; /* Chữ màu tối */
    }

    .auth-card h2 {
        margin-bottom: 10px;
        font-size: 28px;
        font-weight: 400;
        color: #444;
    }
    
    .sub-text {
        font-size: 14px;
        color: #666;
        margin-bottom: 30px;
    }

    .form-group {
        margin-bottom: 20px;
        text-align: left;
    }

    .form-input {
        width: 100%;
        padding: 12px 20px;
        border-radius: 30px;
        border: 1px solid rgba(0, 0, 0, 0.1); /* Viền nhạt */
        background: #fff;
        color: #333;
        font-size: 15px;
        outline: none;
        transition: all 0.3s;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }

    .form-input::placeholder {
        color: #999;
    }

    .form-input:focus {
        border-color: #FFD8B5; /* Viền cam khi focus */
        box-shadow: 0 4px 10px rgba(255, 216, 181, 0.3);
    }

    .submit-btn {
        width: 100%;
        padding: 12px;
        border-radius: 30px;
        border: none;
        background: #FFD8B5; /* Màu Cam Đào giống HomePage */
        color: #444;
        font-size: 16px;
        font-weight: 500;
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
        margin-top: 10px;
        box-shadow: 0 4px 15px rgba(255, 216, 181, 0.6);
    }

    .submit-btn:hover {
        transform: translateY(-2px);
        background: #FFC590;
        box-shadow: 0 6px 20px rgba(255, 216, 181, 0.8);
    }

    .auth-footer {
        margin-top: 25px;
        font-size: 14px;
        color: #666;
    }

    .auth-link {
        color: #FFC069;
        text-decoration: none;
        font-weight: 500;
        margin-left: 5px;
    }

    .auth-link:hover {
        text-decoration: underline;
        color: #ffa940;
    }
`;

const LoginPage = () => {
    let { loginUser } = useContext(AuthContext);

    return (
        <div className="auth-container">
            <style>{styles}</style>
            
            <div className="auth-card">
                <img 
                    src="https://cdn-icons-png.flaticon.com/512/1163/1163661.png" 
                    alt="logo" 
                    width="70" 
                    style={{marginBottom: '5px'}}
                />
                <h2>Welcome</h2>
                <p className="sub-text">Please enter your details to sign in</p>
                
                <form onSubmit={loginUser}>
                    <div className="form-group">
                        <input 
                            className="form-input" 
                            type="text" 
                            name="username" 
                            placeholder="Username" 
                            required 
                        />
                    </div>
                    <div className="form-group">
                        <input 
                            className="form-input" 
                            type="password" 
                            name="password" 
                            placeholder="Password" 
                            required 
                        />
                    </div>
                    <button type="submit" className="submit-btn">
                        Sign in
                    </button>
                </form>

                <div className="auth-footer">
                    <p>Don't have an account? <Link to="/register" className="auth-link">Register now</Link></p>
                </div>
            </div>
        </div>
    );
};

export default LoginPage;