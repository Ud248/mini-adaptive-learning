import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Dropdown,
    Avatar,
    Button,
    message
} from 'antd';
import {
    UserOutlined,
    BookOutlined,
    BarChartOutlined,
    LogoutOutlined
} from '@ant-design/icons';

const AvatarMenu = ({ user, onLogout }) => {
    const navigate = useNavigate();
    const [studentName, setStudentName] = useState('Student');

    // Lấy tên thật của học sinh từ localStorage hoặc API
    useEffect(() => {
        const getStudentName = async () => {
            try {
                // Debug: Clear localStorage để test API
                localStorage.removeItem('student_name');

                // Thử lấy từ localStorage trước
                const storedName = localStorage.getItem('student_name');
                if (storedName) {
                    setStudentName(storedName);
                    return;
                }

                // Nếu không có trong localStorage, gọi API để lấy tên thật
                const token = localStorage.getItem('access_token');
                const studentEmail = localStorage.getItem('student_email');

                if (token && studentEmail) {
                    try {
                        const response = await fetch('http://localhost:8001/api/users/name', {
                            method: 'GET',
                            headers: {
                                'Authorization': `Bearer ${token}`,
                                'Content-Type': 'application/json'
                            }
                        });

                        if (response.ok) {
                            const userData = await response.json();
                            const fullName = userData.full_name;

                            if (fullName) {
                                setStudentName(fullName);
                                localStorage.setItem('student_name', fullName);
                                return;
                            }
                        }
                    } catch (apiError) {
                        // API call failed, using fallback logic
                    }
                }

                // Fallback: lấy từ email
                if (studentEmail) {
                    // Lấy username từ email (ví dụ: student1@gmail.com -> student1)
                    const username = studentEmail.split('@')[0];

                    // Tạo tên thật từ username (có thể customize logic này)
                    const displayName = username.charAt(0).toUpperCase() + username.slice(1);
                    setStudentName(displayName);

                    // Lưu vào localStorage để lần sau không cần tính lại
                    localStorage.setItem('student_name', displayName);
                }
            } catch (error) {
                setStudentName('Student');
            }
        };

        getStudentName();
    }, []);


    const handlePlacementTest = () => {
        // Navigate to placement test (same as quiz setup for now)
        navigate('/');
        message.info('Bắt đầu làm bài kiểm tra đầu vào');
    };

    const handleViewWeakSkills = () => {
        // Navigate to weak skills view using profile_student data
        navigate('/student-weak-skills');
    };

    const menuItems = [
        {
            key: 'placement',
            icon: <BookOutlined />,
            label: 'Làm bài kiểm tra đầu vào',
            onClick: handlePlacementTest
        },
        {
            key: 'weak-skills',
            icon: <BarChartOutlined />,
            label: 'Xem kỹ năng yếu',
            onClick: handleViewWeakSkills
        },
        {
            type: 'divider'
        },
        {
            key: 'logout',
            icon: <LogoutOutlined />,
            label: 'Đăng xuất',
            onClick: onLogout,
            danger: true
        }
    ];

    const menu = {
        items: menuItems,
        style: { minWidth: 200 }
    };

    return (
        <Dropdown menu={menu} placement="bottomRight" trigger={['click']}>
            <Button
                type="text"
                style={{
                    padding: 0,
                    height: 'auto',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                }}
            >
                <Avatar
                    size={32}
                    icon={<UserOutlined />}
                    style={{ backgroundColor: '#1890ff' }}
                />
                <span style={{ color: '#555', fontSize: '14px' }}>
                    {studentName}
                </span>
            </Button>
        </Dropdown>
    );
};

export default AvatarMenu;
