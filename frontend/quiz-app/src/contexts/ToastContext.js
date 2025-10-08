import React, { createContext, useContext, useState, useCallback } from 'react';

let toastId = 0;

const ToastContext = createContext();

export const useToast = () => {
    const context = useContext(ToastContext);
    if (!context) {
        throw new Error('useToast must be used within a ToastProvider');
    }
    return context;
};

export const ToastProvider = ({ children }) => {
    const [toasts, setToasts] = useState([]);

    const addToast = useCallback((message, type = 'info', duration = 3000) => {
        const id = ++toastId;
        const newToast = {
            id,
            message,
            type,
            duration
        };

        setToasts(prev => [...prev, newToast]);
        return id;
    }, []);

    const removeToast = useCallback((id) => {
        setToasts(prev => prev.filter(toast => toast.id !== id));
    }, []);

    const showSuccess = useCallback((message, duration = 3000) => {
        return addToast(message, 'success', duration);
    }, [addToast]);

    const showError = useCallback((message, duration = 5000) => {
        return addToast(message, 'error', duration);
    }, [addToast]);

    const showWarning = useCallback((message, duration = 4000) => {
        return addToast(message, 'warning', duration);
    }, [addToast]);

    const showInfo = useCallback((message, duration = 3000) => {
        return addToast(message, 'info', duration);
    }, [addToast]);

    const showLoading = useCallback((message, duration = 0) => {
        return addToast(message, 'loading', duration);
    }, [addToast]);

    const clearAll = useCallback(() => {
        setToasts([]);
    }, []);

    const value = {
        toasts,
        addToast,
        removeToast,
        showSuccess,
        showError,
        showWarning,
        showInfo,
        showLoading,
        clearAll
    };

    return (
        <ToastContext.Provider value={value}>
            {children}
        </ToastContext.Provider>
    );
};
