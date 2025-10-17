import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Typography, Row, Col, Button } from 'antd';
import { EditOutlined, BarChartOutlined, RocketOutlined, ArrowRightOutlined } from '@ant-design/icons';
import { useAuth } from '../auth/AuthContext';

const { Title, Text } = Typography;

const HomePage = () => {
    const navigate = useNavigate();
    const { user } = useAuth();
    const [studentName, setStudentName] = useState('Học sinh');

    // Lấy tên thật của học sinh
    useEffect(() => {
        const getStudentName = async () => {
            try {
                // Thử lấy từ localStorage trước
                const storedName = localStorage.getItem('student_name');
                if (storedName) {
                    setStudentName(storedName);
                    return;
                }

                // Nếu không có, lấy từ user object
                if (user?.full_name) {
                    setStudentName(user.full_name);
                    localStorage.setItem('student_name', user.full_name);
                    return;
                }

                // Fallback: lấy từ username
                if (user?.username) {
                    const displayName = user.username.charAt(0).toUpperCase() + user.username.slice(1);
                    setStudentName(displayName);
                }
            } catch (error) {
                setStudentName('Học sinh');
            }
        };

        getStudentName();
    }, [user]);

    const menuItems = [
        {
            title: 'Làm bài kiểm tra mới',
            description: 'Bắt đầu một bài kiểm tra để đánh giá kiến thức của bạn',
            icon: <EditOutlined style={{ fontSize: 48, color: '#1890ff' }} />,
            path: '/quiz-setup',
            color: '#e6f7ff',
            borderColor: '#1890ff',
            buttonText: 'Bắt đầu ngay'
        },
        {
            title: 'Xem kỹ năng còn yếu',
            description: 'Xem các kỹ năng bạn cần cải thiện và luyện tập',
            icon: <BarChartOutlined style={{ fontSize: 48, color: '#52c41a' }} />,
            path: '/student-weak-skills',
            color: '#f6ffed',
            borderColor: '#52c41a',
            buttonText: 'Xem ngay'
        }
    ];

    return (
        <div style={{
            minHeight: '100vh',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            padding: '40px 20px'
        }}>
            <div style={{ maxWidth: 1200, margin: '0 auto' }}>
                {/* Welcome Section */}
                <Card
                    style={{
                        marginBottom: 40,
                        textAlign: 'center',
                        borderRadius: 16,
                        boxShadow: '0 8px 24px rgba(0,0,0,0.12)'
                    }}
                >
                    <RocketOutlined style={{ fontSize: 64, color: '#1890ff', marginBottom: 16 }} />
                    <Title level={2} style={{ marginBottom: 8, color: '#1890ff' }}>
                        Chào mừng, {studentName}! 👋
                    </Title>
                    <Text style={{ fontSize: 16, color: '#666' }}>
                        Hệ thống học tập thích ứng - Học thông minh, tiến bộ mỗi ngày
                    </Text>
                </Card>

                {/* Menu Options */}
                <Row gutter={[24, 24]}>
                    {menuItems.map((item, index) => (
                        <Col xs={24} sm={24} md={12} key={index}>
                            <Card
                                hoverable
                                onClick={() => navigate(item.path)}
                                style={{
                                    height: '100%',
                                    minHeight: 280,
                                    borderRadius: 16,
                                    border: `2px solid ${item.borderColor}`,
                                    background: item.color,
                                    boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                                    transition: 'all 0.3s ease',
                                    cursor: 'pointer'
                                }}
                                bodyStyle={{
                                    height: '100%',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    padding: 32
                                }}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.transform = 'translateY(-8px)';
                                    e.currentTarget.style.boxShadow = '0 12px 24px rgba(0,0,0,0.15)';
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.transform = 'translateY(0)';
                                    e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.08)';
                                }}
                            >
                                <div style={{ marginBottom: 24 }}>
                                    {item.icon}
                                </div>
                                <Title level={3} style={{ marginBottom: 12, textAlign: 'center' }}>
                                    {item.title}
                                </Title>
                                <Text style={{
                                    fontSize: 15,
                                    color: '#666',
                                    textAlign: 'center',
                                    lineHeight: 1.6,
                                    marginBottom: 24,
                                    display: 'block'
                                }}>
                                    {item.description}
                                </Text>
                                <Button
                                    type="primary"
                                    size="large"
                                    icon={<ArrowRightOutlined />}
                                    style={{
                                        marginTop: 'auto',
                                        background: item.borderColor,
                                        borderColor: item.borderColor,
                                        fontWeight: 600,
                                        height: 48,
                                        paddingLeft: 32,
                                        paddingRight: 32
                                    }}
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        navigate(item.path);
                                    }}
                                >
                                    {item.buttonText}
                                </Button>
                            </Card>
                        </Col>
                    ))}
                </Row>

                {/* Quick Stats or Tips (Optional) */}
                <Card
                    style={{
                        marginTop: 40,
                        borderRadius: 16,
                        background: 'rgba(255,255,255,0.95)',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.08)'
                    }}
                >
                    <Title level={4} style={{ marginBottom: 16 }}>
                        💡 Mẹo học tập
                    </Title>
                    <Row gutter={[16, 16]}>
                        <Col xs={24} sm={8}>
                            <div style={{ textAlign: 'center', padding: 16 }}>
                                <Text strong style={{ fontSize: 16, color: '#1890ff' }}>
                                    📚 Học đều đặn
                                </Text>
                                <br />
                                <Text style={{ fontSize: 14, color: '#666' }}>
                                    Mỗi ngày 15-30 phút
                                </Text>
                            </div>
                        </Col>
                        <Col xs={24} sm={8}>
                            <div style={{ textAlign: 'center', padding: 16 }}>
                                <Text strong style={{ fontSize: 16, color: '#52c41a' }}>
                                    🎯 Tập trung kỹ năng yếu
                                </Text>
                                <br />
                                <Text style={{ fontSize: 14, color: '#666' }}>
                                    Cải thiện từng ngày
                                </Text>
                            </div>
                        </Col>
                        <Col xs={24} sm={8}>
                            <div style={{ textAlign: 'center', padding: 16 }}>
                                <Text strong style={{ fontSize: 16, color: '#fa8c16' }}>
                                    ⭐ Kiên trì luyện tập
                                </Text>
                                <br />
                                <Text style={{ fontSize: 14, color: '#666' }}>
                                    Thành công đến từ nỗ lực
                                </Text>
                            </div>
                        </Col>
                    </Row>
                </Card>
            </div>
        </div>
    );
};

export default HomePage;
