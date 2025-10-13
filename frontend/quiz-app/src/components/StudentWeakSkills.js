import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import {
    Card,
    Button,
    List,
    Row,
    Col,
    message,
    Spin,
    Empty,
    Badge,
    Tooltip,
} from 'antd';
import { BookOutlined, TrophyOutlined, ArrowLeftOutlined, HomeOutlined } from '@ant-design/icons';

const StudentWeakSkills = () => {
    const navigate = useNavigate();
    const { user } = useAuth();

    const [, setProfileData] = useState(null);
    const [weakSkills, setWeakSkills] = useState([]);
    const [loading, setLoading] = useState(true);


    const loadStudentProfile = useCallback(async () => {
        try {
            setLoading(true);

            // Lấy student email từ localStorage (vì user object có thể null)
            const studentEmail = localStorage.getItem('student_email') || 'demo_student';

            try {
                // Gọi API để lấy profile student thực tế
                const response = await fetch(`http://localhost:8001/quiz/weak-skills/${studentEmail}`);
                const result = await response.json();


                if (response.ok && result.profile_data) {
                    // Sử dụng dữ liệu thực tế từ API
                    const profileData = {
                        student_id: result.student_email,
                        student_email: result.student_email,
                        username: result.student_email.split('@')[0],
                        full_name: result.student_email.split('@')[0],
                        low_accuracy_skills: result.profile_data.low_accuracy_skills,
                        slow_response_skills: result.profile_data.slow_response_skills,
                        created_at: new Date().toISOString(),
                        updated_at: new Date().toISOString(),
                        status: 'active'
                    };

                    setProfileData(profileData);

                    // Chỉ dùng status và tên kỹ năng; không hiển thị mastered
                    const weakSkillsData = (result.weak_skills || [])
                        .filter(skill => String(skill.status || '').toLowerCase() !== 'mastered')
                        .map(skill => ({
                            skill_id: skill.skill_id,
                            skill_name: skill.skill_name,
                            status: String(skill.status || 'unknown'),
                            subject: skill.subject,
                            grade: skill.grade,
                            difficulty_level: skill.difficulty_level
                        }));

                    setWeakSkills(weakSkillsData);
                } else {
                    // Không có profile hoặc API lỗi - hiển thị 0 kỹ năng yếu
                    // Set empty profile và skills
                    setProfileData(null);
                    setWeakSkills([]);
                }
            } catch (apiError) {
                // Set empty profile và skills
                setProfileData(null);
                setWeakSkills([]);
            }

        } catch (error) {
            console.error('Lỗi tải profile student:', error);
            message.error('Không thể tải thông tin học sinh');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        // Kiểm tra token và email trong localStorage
        const hasToken = localStorage.getItem('access_token');
        const hasEmail = localStorage.getItem('student_email');

        if (hasToken && hasEmail) {
            loadStudentProfile();
        } else {
            setLoading(false);
        }
    }, [user, loadStudentProfile]);

    const getSkillStatusColor = (status) => {
        // Tăng tương phản cho ribbon để dễ đọc trên nền chữ trắng
        const s = String(status || '').toLowerCase();
        if (s === 'mastered') return '#36c26e';      // xanh rõ hơn
        if (s === 'in_progress') return '#f59e0b';   // vàng đậm
        if (s === 'struggling') return '#ff4d4f';    // đỏ đậm (rõ nhất)
        return '#8c8c8c';
    };

    const getSkillStatusText = (status) => {
        const s = String(status || '').toLowerCase();
        if (s === 'mastered') return 'Thành thạo';
        if (s === 'in_progress') return 'Đang học';
        if (s === 'struggling') return 'Gặp khó khăn';
        return 'Không xác định';
    };



    const handlePracticeSkill = (skill) => {
        // TODO: Implement navigation to practice screen for specific skill
        message.info(`Tính năng luyện tập kỹ năng "${skill.skill_name}" sẽ được phát triển sớm!`);
    };

    if (loading) {
        return (
            <div className="loading-spinner">
                <Spin size="large" />
            </div>
        );
    }

    // Kiểm tra token trong localStorage thay vì user object
    const hasToken = localStorage.getItem('access_token');
    const hasEmail = localStorage.getItem('student_email');

    // TODO: Thêm token validation để bảo mật hơn
    // const isTokenValid = (token) => {
    //     try {
    //         const payload = jwt.decode(token);
    //         return payload && payload.exp > Date.now() / 1000;
    //     } catch {
    //         return false;
    //     }
    // };

    if (!hasToken || !hasEmail) {
        return (
            <div style={{ textAlign: 'center', padding: '50px' }}>
                <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description="Vui lòng đăng nhập để xem kỹ năng yếu"
                />
                <Button type="primary" onClick={() => navigate('/login')} style={{ marginTop: '16px' }}>
                    Đăng nhập
                </Button>
            </div>
        );
    }

    return (
        <div className="quiz-container">
            {/* Header with Student Info */}
            <Card className="weak-hero" bordered={false}>
                <Row gutter={[16, 16]} align="middle" justify="center">
                    <Col xs={24} style={{ textAlign: 'center' }}>
                        <div>
                            <div className="weak-hero-title">Kỹ năng cần cải thiện</div>
                            <div style={{ marginTop: 8 }}>
                                <span className="hero-total-pill">Tổng số kỹ năng cần cải thiện: {weakSkills.length} kỹ năng</span>
                            </div>
                            {/* Bỏ mô tả phụ theo yêu cầu */}
                        </div>
                    </Col>
                </Row>
            </Card>

            {/* Weak Skills Analysis */}
            <Card className="weak-skills-list" title={null} bordered={false}>
                {weakSkills.length === 0 ? (
                    <Empty
                        description="Không có kỹ năng yếu nào được phát hiện"
                        image={Empty.PRESENTED_IMAGE_SIMPLE}
                    />
                ) : (
                    <List
                        grid={{ gutter: 16, xs: 1, sm: 1, md: 1, lg: 1, xl: 1, xxl: 1 }}
                        dataSource={weakSkills}
                        renderItem={(skill) => {
                            return (
                                <List.Item>
                                    <Badge.Ribbon text={getSkillStatusText(skill.status)} color={getSkillStatusColor(skill.status)} placement="end">
                                        <Card className="skill-card" hoverable>
                                            <div className="skill-card-header">
                                                <Tooltip title={skill.skill_name} placement="topLeft">
                                                    <div className="skill-title">{skill.skill_name}</div>
                                                </Tooltip>
                                            </div>
                                            <div className="skill-meta">
                                                <span className="skill-chip">{skill.subject}</span>
                                                <span className="skill-chip">Lớp {skill.grade}</span>
                                            </div>
                                            <div className="skill-actions">
                                                <Button type="primary" icon={<BookOutlined />} onClick={() => handlePracticeSkill(skill)}>
                                                    Luyện tập
                                                </Button>
                                            </div>
                                        </Card>
                                    </Badge.Ribbon>
                                </List.Item>
                            );
                        }}
                    />
                )}
            </Card>

            {/* Action Buttons */}
            <Card className="action-buttons">
                <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
                    <Button
                        size="large"
                        icon={<ArrowLeftOutlined />}
                        onClick={() => navigate(-1)}
                    >
                        Quay lại
                    </Button>

                    <Button
                        type="primary"
                        size="large"
                        icon={<TrophyOutlined />}
                        onClick={() => navigate('/')}
                    >
                        Làm bài kiểm tra mới
                    </Button>

                    <Button
                        size="large"
                        icon={<HomeOutlined />}
                        onClick={() => navigate('/')}
                    >
                        Về trang chủ
                    </Button>
                </div>
            </Card>
        </div>
    );
};

export default StudentWeakSkills;

