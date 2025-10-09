import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [token, setToken] = useState(() => {
        try {
            const storedToken = localStorage.getItem('access_token') || '';
            return storedToken;
        } catch (e) {
            return '';
        }
    });
    const [user, setUser] = useState(null);

    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (token) {
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
            fetchMe();
        } else {
            delete axios.defaults.headers.common['Authorization'];
            setUser(null);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [token]);

    const fetchMe = async () => {
        try {
            setLoading(true);
            const res = await axios.get('http://localhost:8001/me');
            setUser(res.data);
            // Update email trong localStorage nếu có từ API response
            if (res.data?.email) {
                localStorage.setItem('student_email', res.data.email);
            }
        } catch (e) {
            setUser(null);
        } finally {
            setLoading(false);
        }
    };

    const login = async (identifier, password) => {
        const res = await axios.post('http://localhost:8001/auth/login', {
            email_or_username: identifier,
            password
        });
        const accessToken = res.data?.access_token || '';
        setToken(accessToken);
        try {
            localStorage.setItem('access_token', accessToken);
            // Convert username to email và lưu vào localStorage
            let studentEmail = identifier;
            if (!identifier.includes('@')) {
                // Convert username to email
                studentEmail = `${identifier}@gmail.com`;
            }
            localStorage.setItem('student_email', studentEmail);
        } catch (e) { }
        return res.data;
    };

    const logout = async () => {
        try {
            await axios.post('http://localhost:8001/auth/logout');
        } catch (e) {
            // ignore
        }
        setToken('');
        setUser(null);
        try { localStorage.removeItem('access_token'); } catch (e) { }
    };

    const value = useMemo(() => {
        return { token, user, loading, login, logout };
    }, [token, user, loading]);

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);


