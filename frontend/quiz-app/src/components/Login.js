import React, { useState } from 'react';
import { Card, Form, Input, Button, Typography } from 'antd';
import { LockOutlined, UserOutlined, LoginOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { useToast } from '../contexts/ToastContext';

const { Title, Text } = Typography;

const Login = () => {
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();
    const { showSuccess, showError } = useToast();

    const onFinish = async (values) => {
        setLoading(true);
        try {
            await login(values.identifier, values.password);
            showSuccess('Đăng nhập thành công');
            navigate('/');
        } catch (e) {
            showError('Sai tài khoản hoặc mật khẩu');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-container">
            <Card className="login-card">
                <Title level={3} style={{ textAlign: 'center', marginBottom: 16 }}>Đăng nhập</Title>
                <Text type="secondary" style={{ display: 'block', textAlign: 'center', marginBottom: 24 }}>
                    Vui lòng đăng nhập để bắt đầu làm bài kiểm tra
                </Text>
                <Form layout="vertical" onFinish={onFinish} initialValues={{ identifier: '', password: '' }}>
                    <Form.Item label="Email hoặc Tên đăng nhập" name="identifier" rules={[{ required: true, message: 'Vui lòng nhập email hoặc tên đăng nhập' }]}>
                        <Input size="large" prefix={<UserOutlined />} placeholder="Email/Username" />
                    </Form.Item>
                    <Form.Item label="Mật khẩu" name="password" rules={[{ required: true, message: 'Vui lòng nhập mật khẩu' }]}>
                        <Input.Password size="large" prefix={<LockOutlined />} placeholder="Mật khẩu" />
                    </Form.Item>
                    <Form.Item>
                        <Button type="primary" htmlType="submit" size="large" icon={<LoginOutlined />} loading={loading} block>
                            Đăng nhập
                        </Button>
                    </Form.Item>
                </Form>
            </Card>
        </div>
    );
};

export default Login;


