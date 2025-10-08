import React, { useState, useEffect } from 'react';
import './Toast.css';

const Toast = ({ message, type = 'info', duration = 3000, onClose }) => {
    const [isVisible, setIsVisible] = useState(true);

    useEffect(() => {
        const timer = setTimeout(() => {
            setIsVisible(false);
            setTimeout(() => {
                onClose();
            }, 300); // Wait for fade out animation
        }, duration);

        return () => clearTimeout(timer);
    }, [duration, onClose]);

    const getIcon = () => {
        switch (type) {
            case 'success':
                return '✅';
            case 'error':
                return '❌';
            case 'warning':
                return '⚠️';
            case 'loading':
                return '⏳';
            default:
                return 'ℹ️';
        }
    };

    return (
        <div className={`toast toast-${type} ${isVisible ? 'toast-visible' : 'toast-hidden'}`}>
            <div className="toast-content">
                <span className="toast-icon">{getIcon()}</span>
                <span className="toast-message">{message}</span>
            </div>
        </div>
    );
};

export default Toast;
