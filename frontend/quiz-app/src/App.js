import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import { ConfigProvider, Button } from 'antd';
import viVN from 'antd/locale/vi_VN';
import QuizSetup from './components/QuizSetup';
import QuizTaking from './components/QuizTaking';
import QuizResult from './components/QuizResult';
import Login from './components/Login';
import { AuthProvider, useAuth } from './auth/AuthContext';
import { ToastProvider, useToast } from './contexts/ToastContext';
import ToastContainer from './components/ToastContainer';
import BackToTop from './components/BackToTop';
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
    const { showSuccess } = useToast();

    if (!token) return null;

    const handleLogout = () => {
        logout();
        showSuccess('Đăng xuất thành công');
    };

    return (
        <div className="app-header-bar">
            <div className="app-header-left">
                <Link to="/" className="app-logo">Adaptive Learning</Link>
            </div>
            <div className="app-header-right">
                <span className="user-email">{user?.email}</span>
                <Button type="primary" onClick={handleLogout} className="logout-btn" size="middle">
                    Đăng xuất
                </Button>
            </div>
        </div>
    );
};

const AppContent = () => {
    const { toasts, removeToast } = useToast();

    return (
        <div className="App">
            <HeaderBar />
            <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/" element={<PrivateRoute><QuizSetup /></PrivateRoute>} />
                <Route path="/quiz/:quizId" element={<PrivateRoute><QuizTaking /></PrivateRoute>} />
                <Route path="/result/:quizId" element={<PrivateRoute><QuizResult /></PrivateRoute>} />
            </Routes>
            <ToastContainer toasts={toasts} removeToast={removeToast} />
            <BackToTop />
        </div>
    );
};

function App() {
    return (
        <ConfigProvider locale={viVN}>
            <Router>
                <AuthProvider>
                    <ToastProvider>
                        <AppContent />
                    </ToastProvider>
                </AuthProvider>
            </Router>
        </ConfigProvider>
    );
}

export default App;
