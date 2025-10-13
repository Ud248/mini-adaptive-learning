import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import viVN from 'antd/locale/vi_VN';
import QuizSetup from './components/QuizSetup';
import QuizTaking from './components/QuizTaking';
import QuizResult from './components/QuizResult';
import StudentWeakSkills from './components/StudentWeakSkills';
import AvatarMenu from './components/AvatarMenu';
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
                <AvatarMenu user={user} onLogout={handleLogout} />
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
                <Route path="/student-weak-skills" element={<PrivateRoute><StudentWeakSkills /></PrivateRoute>} />
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
