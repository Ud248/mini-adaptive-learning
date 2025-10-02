import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import { ConfigProvider, Button } from 'antd';
import viVN from 'antd/locale/vi_VN';
import QuizSetup from './components/QuizSetup';
import QuizTaking from './components/QuizTaking';
import QuizResult from './components/QuizResult';
import Login from './components/Login';
import { AuthProvider, useAuth } from './auth/AuthContext';
import './App.css';

const PrivateRoute = ({ children }) => {
    const { token } = useAuth();
    if (!token) {
        return <Navigate to="/login" replace />;
    }
    return children;
};

const HeaderBar = () => {
    const { token, user, logout } = useAuth();
    if (!token) return null;
    return (
        <div className="app-header-bar">
            <div className="app-header-left">
                <Link to="/" className="app-logo">Adaptive Learning</Link>
            </div>
            <div className="app-header-right">
                <span className="user-email">{user?.email}</span>
                <Button type="primary" onClick={logout} className="logout-btn" size="middle">
                    Đăng xuất
                </Button>
            </div>
        </div>
    );
};

function App() {
    return (
        <ConfigProvider locale={viVN}>
            <Router>
                <AuthProvider>
                    <div className="App">
                        <HeaderBar />
                        <Routes>
                            <Route path="/login" element={<Login />} />
                            <Route path="/" element={<PrivateRoute><QuizSetup /></PrivateRoute>} />
                            <Route path="/quiz/:quizId" element={<PrivateRoute><QuizTaking /></PrivateRoute>} />
                            <Route path="/result/:quizId" element={<PrivateRoute><QuizResult /></PrivateRoute>} />
                        </Routes>
                    </div>
                </AuthProvider>
            </Router>
        </ConfigProvider>
    );
}

export default App;
