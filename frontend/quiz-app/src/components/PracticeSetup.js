import React, { useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Card, Button, Tag, Row, Col, Radio, Typography, Spin } from 'antd';
import { useAuth } from '../auth/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { generateAgentQuestions } from '../api/agent';

const PracticeSetup = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { token, user } = useAuth();
    const { showError, showSuccess } = useToast();

    const skillInfo = useMemo(() => {
        const s = (location && location.state) || {};
        return {
            skill_id: s.skill_id || 'S01',
            skill_name: s.skill_name || 'Kỹ năng',
            grade: s.grade || 1,
            subject: s.subject || 'Toán',
        };
    }, [location]);

    const [numQuestions, setNumQuestions] = useState(10);
    const [loading, setLoading] = useState(false);

    const startPractice = async () => {
        try {
            setLoading(true);
            const baseUrl = (window.env && window.env.API_URL) ? window.env.API_URL : 'http://localhost:8001';
            const username = user?.username || user?.email || 'hoc_sinh';
            const { questions } = await generateAgentQuestions({
                baseUrl,
                token,
                grade: Number(skillInfo.grade) || 1,
                skill: skillInfo.skill_id,
                skill_name: skillInfo.skill_name,
                num_questions: Number(numQuestions) || 10,
                username,
            });

            if (!questions || questions.length === 0) {
                showError('Không tạo được câu hỏi luyện tập');
                return;
            }

            showSuccess(`Tạo ${questions.length} câu hỏi luyện tập thành công`);
            const practiceId = `practice_${Date.now()}`;
            navigate('/practice/taking', {
                state: {
                    practice_id: practiceId,
                    questions,
                    meta: skillInfo,
                }
            });
        } catch (e) {
            showError('Lỗi khi tạo câu hỏi luyện tập');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="quiz-container" style={{ position: 'relative' }}>
            <Card className="question-content">
                <Typography.Title level={3} style={{ marginTop: 0 }}>
                    Luyện tập: {skillInfo.skill_name}
                </Typography.Title>

                <div style={{ marginBottom: 16 }}>
                    <Tag color="blue">Môn: {skillInfo.subject}</Tag>
                    <Tag color="purple" style={{ borderRadius: 16 }}>Lớp {skillInfo.grade}</Tag>
                </div>

                <div style={{ marginTop: 8, marginBottom: 8 }}>
                    <Typography.Text strong>Chọn số câu hỏi:</Typography.Text>
                </div>

                <Radio.Group
                    value={numQuestions}
                    onChange={(e) => setNumQuestions(e.target.value)}
                    style={{ width: '100%' }}
                >
                    <Row gutter={[12, 12]}>
                        {[5, 10, 15, 20].map((n) => (
                            <Col key={n} xs={12} sm={6}>
                                <Card
                                    hoverable
                                    onClick={() => setNumQuestions(n)}
                                    style={{ textAlign: 'center' }}
                                >
                                    <Radio value={n}>{n} câu</Radio>
                                </Card>
                            </Col>
                        ))}
                    </Row>
                </Radio.Group>

                <div style={{ marginTop: 24 }}>
                    <Button type="primary" size="large" disabled={loading} onClick={startPractice}>
                        Bắt đầu luyện tập
                    </Button>
                </div>
            </Card>

            {loading && (
                <div
                    style={{
                        position: 'fixed',
                        top: 0,
                        left: 0,
                        width: '100vw',
                        height: '100vh',
                        background: 'rgba(0,0,0,0.45)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        zIndex: 1000,
                    }}
                >
                    <Card
                        style={{
                            width: 420,
                            textAlign: 'center',
                            boxShadow: '0 12px 40px rgba(0,0,0,0.25)'
                        }}
                    >
                        <div style={{ fontSize: 16, marginBottom: 12, color: '#8c8c8c' }}>
                            Hệ thống đang tạo câu hỏi phù hợp với bạn, đợi chút nhé
                        </div>
                        <div className="loading-spinner" style={{ paddingTop: 4, paddingBottom: 8 }}>
                            <Spin size="large" />
                        </div>
                    </Card>
                </div>
            )}
        </div>
    );
};

export default PracticeSetup;


