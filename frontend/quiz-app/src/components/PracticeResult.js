import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Card, Button, Spin, Row, Col, Collapse, List } from 'antd';
import { TrophyOutlined, ReloadOutlined, HomeOutlined, CheckCircleOutlined, CloseCircleOutlined, DownOutlined, ClockCircleOutlined } from '@ant-design/icons';

const PracticeResult = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const s = (location && location.state) || {};
        if (s.result) {
            setResult(s.result);
            setLoading(false);
        } else {
            setLoading(false);
        }
    }, [location]);

    const getScoreColor = (score) => {
        if (score >= 80) return '#52c41a';
        if (score >= 60) return '#faad14';
        return '#ff4d4f';
    };

    const getScoreText = (score) => {
        if (score >= 90) return 'Xuất sắc';
        if (score >= 80) return 'Giỏi';
        if (score >= 70) return 'Khá';
        if (score >= 60) return 'Trung bình';
        return 'Cần cố gắng';
    };

    const formatTime = (totalSeconds) => {
        const safeSeconds = Math.max(0, Number.isFinite(totalSeconds) ? Math.floor(totalSeconds) : 0);
        const hours = Math.floor(safeSeconds / 3600);
        const minutes = Math.floor((safeSeconds % 3600) / 60);
        const seconds = safeSeconds % 60;
        const pad = (n) => n.toString().padStart(2, '0');
        return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
    };

    if (loading) {
        return (
            <div className="loading-spinner">
                <Spin size="large" />
            </div>
        );
    }

    if (!result) {
        return (
            <div className="quiz-container">
                <Card>
                    <p>Không tìm thấy kết quả luyện tập</p>
                    <Button onClick={() => navigate('/student-weak-skills')}>Quay lại</Button>
                </Card>
            </div>
        );
    }

    return (
        <div className="quiz-container">
            <Card className="result-summary">
                <div className="score-circle" style={{ background: `linear-gradient(135deg, ${getScoreColor(result.score)}, #1890ff)` }}>
                    <div>
                        <div style={{ fontSize: '32px', fontWeight: 'bold' }}>
                            {result.score.toFixed(1)}%
                        </div>
                        <div style={{ fontSize: '14px', opacity: 0.9 }}>
                            {getScoreText(result.score)}
                        </div>
                    </div>
                </div>

                <h2 style={{ marginBottom: 24 }}>
                    <TrophyOutlined style={{ marginRight: 8, color: '#faad14' }} />
                    Kết quả luyện tập
                </h2>

                <Row gutter={16} className="result-stats" justify="center">
                    <Col>
                        <div className="stat-card">
                            <div className="stat-label">Câu đúng</div>
                            <div className="stat-number" style={{ color: '#52c41a' }}>{result.correct_answers}</div>
                        </div>
                    </Col>
                    <Col>
                        <div className="stat-card">
                            <div className="stat-label">Câu sai</div>
                            <div className="stat-number" style={{ color: '#ff4d4f' }}>{result.wrong_answers || 0}</div>
                        </div>
                    </Col>
                    <Col>
                        <div className="stat-card">
                            <div className="stat-label">Câu chưa làm</div>
                            <div className="stat-number" style={{ color: '#8c8c8c' }}>{result.unanswered_questions || 0}</div>
                        </div>
                    </Col>
                    <Col>
                        <div className="stat-card">
                            <div className="stat-label">Tổng câu hỏi</div>
                            <div className="stat-number" style={{ color: '#722ed1' }}>{result.total_questions}</div>
                        </div>
                    </Col>
                    <Col>
                        <div className="stat-card">
                            <div className="stat-label">Thời gian làm bài</div>
                            <div className="stat-number" style={{ color: '#13c2c2' }}>
                                <ClockCircleOutlined style={{ marginRight: 4 }} />
                                {formatTime(result.actual_time_spent || result.time_spent || 0)}
                            </div>
                        </div>
                    </Col>
                </Row>

                <div className="action-buttons">
                    <Button
                        type="primary"
                        size="large"
                        icon={<ReloadOutlined />}
                        onClick={() => navigate('/student-weak-skills')}
                    >
                        Luyện tập kỹ năng khác
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

            <Card style={{ marginTop: 24 }}>
                <Collapse
                    ghost
                    expandIcon={({ isActive }) => <DownOutlined rotate={isActive ? 180 : 0} />}
                >
                    <Collapse.Panel
                        header={
                            <span style={{ fontSize: '16px', fontWeight: 'bold' }}>
                                📋 Chi tiết từng câu hỏi ({result.detailed_results?.length || 0} câu)
                            </span>
                        }
                        key="1"
                    >
                        <List
                            dataSource={result.detailed_results}
                            renderItem={(item, index) => (
                                <List.Item>
                                    <div className={`result-item ${item.correct ? 'correct' : 'incorrect'}`}>
                                        <div style={{ flex: 1 }}>
                                            <div style={{ fontWeight: 'bold', marginBottom: 8 }}>
                                                Câu {index + 1}: {item.question}
                                            </div>
                                            <div style={{ marginBottom: 4 }}>
                                                <strong>Đáp án của bạn:</strong> {item.user_answer}
                                            </div>
                                            <div style={{ marginBottom: 4 }}>
                                                <strong>Đáp án đúng:</strong> {item.correct_answer}
                                            </div>
                                            {item.explanation && (
                                                <div>
                                                    <strong>Giải thích:</strong> {item.explanation}
                                                </div>
                                            )}
                                        </div>
                                        <div style={{ marginLeft: 16 }}>
                                            {item.correct ? (
                                                <CheckCircleOutlined style={{ fontSize: 24, color: '#52c41a' }} />
                                            ) : (
                                                <CloseCircleOutlined style={{ fontSize: 24, color: '#ff4d4f' }} />
                                            )}
                                        </div>
                                    </div>
                                </List.Item>
                            )}
                        />
                    </Collapse.Panel>
                </Collapse>
            </Card>
        </div>
    );
};

export default PracticeResult;


