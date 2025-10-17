import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { Card, Button, message, Spin, List, Statistic, Row, Col, Collapse, Tag } from 'antd';
import {
    TrophyOutlined,
    ReloadOutlined,
    HomeOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined,
    ClockCircleOutlined,
    BookOutlined,
    DownOutlined,
    SmileOutlined,
    FrownOutlined
} from '@ant-design/icons';

const { Panel } = Collapse;

const QuizResult = () => {
    const { quizId } = useParams();
    const navigate = useNavigate();
    const location = useLocation();
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadResult();
    }, [quizId]); // eslint-disable-line react-hooks/exhaustive-deps

    const loadResult = async () => {
        try {
            // Kiểm tra xem có dữ liệu từ state không (từ QuizTaking)
            if (location.state && location.state.result) {
                const resultData = location.state.result;

                // Tạo detailed_results từ dữ liệu thực và tính đúng/sai
                const detailedResults = [];
                let answeredQuestions = 0;
                let correctAnswers = 0;

                if (resultData.questions) {
                    resultData.questions.forEach((question, index) => {
                        const userAnswerIndex = resultData.user_answers?.[question.id];
                        let userAnswer = 'Chưa trả lời';
                        if (userAnswerIndex !== undefined && userAnswerIndex !== null) {
                            answeredQuestions += 1;
                            if (question.options && question.options[userAnswerIndex] !== undefined) {
                                userAnswer = question.options[userAnswerIndex];
                            } else {
                                userAnswer = String(userAnswerIndex);
                            }
                        }

                        const isCorrect = userAnswer === question.answer;
                        if (isCorrect) correctAnswers += 1;

                        detailedResults.push({
                            question_id: question.id,
                            question: question.question,
                            user_answer: userAnswer,
                            correct_answer: question.answer,
                            correct: isCorrect,
                            // Ưu tiên dùng giải thích từ backend nếu có
                            explanation: question.explanation || `Giải thích cho câu ${index + 1}`
                        });
                    });
                }

                // Tính toán thống kê dựa trên số câu thực tế
                const totalQuestions = resultData.questions ? resultData.questions.length : 0;
                const wrongAnswers = Math.max(0, answeredQuestions - correctAnswers);
                const unansweredQuestions = Math.max(0, totalQuestions - answeredQuestions);

                // Tính điểm trên tổng số câu thực tế
                const scoreOnTotal = totalQuestions > 0 ? (correctAnswers / totalQuestions) * 100 : 0;

                const enhancedResult = {
                    ...resultData,
                    total_questions: totalQuestions,
                    correct_answers: correctAnswers,
                    wrong_answers: wrongAnswers,
                    answered_questions: answeredQuestions,
                    unanswered_questions: unansweredQuestions,
                    score: scoreOnTotal,
                    actual_time_spent: resultData.actual_time_spent || 0,
                    detailed_results: detailedResults
                };

                setResult(enhancedResult);
                setLoading(false);
                return;
            }

            // Nếu không có dữ liệu từ state, tạo dữ liệu mẫu
            const mockResult = {
                quiz_id: quizId,
                total_questions: 40,
                correct_answers: 32,
                wrong_answers: 6,
                answered_questions: 38,
                unanswered_questions: 2,
                score: 80.0,
                actual_time_spent: 1440,
                detailed_results: Array.from({ length: 40 }, (_, i) => ({
                    question_id: `q_${i + 1}`,
                    question: `Câu hỏi ${i + 1}`,
                    user_answer: i < 25 ? 'Đáp án A' : i < 28 ? 'Đáp án B' : 'Chưa trả lời',
                    correct_answer: 'Đáp án A',
                    correct: i < 25,
                    explanation: `Giải thích cho câu ${i + 1}`
                })),
                saint_analysis_data: {
                    student_id: 'demo_student',
                    quiz_id: quizId,
                    total_questions: 40,
                    correct_answers: 32,
                    score: 80.0,
                    time_spent: 1440,
                    difficulty_level: 'medium',
                    subject: 'Toán',
                    grade: 1
                }
            };

            setResult(mockResult);
        } catch (error) {
            console.error('Lỗi tải kết quả:', error);
            message.error('Không thể tải kết quả bài kiểm tra');
            navigate('/');
        } finally {
            setLoading(false);
        }
    };

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

    // Phân tích skills từ detailed_results
    const analyzeSkills = () => {
        if (!result || !result.detailed_results) {
            return { goodSkills: [], weakSkills: [] };
        }

        // Lấy thông tin skill từ questions gốc
        const questions = location.state?.result?.questions || [];

        // Group câu hỏi theo skill_name
        const skillGroups = {};

        result.detailed_results.forEach((item, index) => {
            const question = questions[index] || {};
            // Lấy skill_name từ question (ưu tiên lesson > chapter > skill)
            const skillName = question.lesson || question.chapter || question.skill || `Kỹ năng ${index + 1}`;
            const skillId = question.skill || question.chapter || `SKILL_${index + 1}`;

            if (!skillGroups[skillName]) {
                skillGroups[skillName] = {
                    skill_id: skillId,
                    skill_name: skillName,
                    questions: [],
                    correct: 0,
                    total: 0
                };
            }

            skillGroups[skillName].questions.push(item);
            skillGroups[skillName].total += 1;
            if (item.correct) {
                skillGroups[skillName].correct += 1;
            }
        });

        // Tính accuracy cho mỗi skill và phân loại
        const goodSkills = [];
        const weakSkills = [];

        Object.values(skillGroups).forEach(skill => {
            const accuracy = skill.total > 0 ? (skill.correct / skill.total) * 100 : 0;
            const skillData = {
                ...skill,
                accuracy: accuracy.toFixed(1)
            };

            if (accuracy >= 70) {
                goodSkills.push(skillData);
            } else {
                weakSkills.push(skillData);
            }
        });

        return { goodSkills, weakSkills };
    };

    const { goodSkills, weakSkills } = analyzeSkills();

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
                    <p>Không tìm thấy kết quả bài kiểm tra</p>
                    <Button onClick={() => navigate('/')}>Quay lại trang chủ</Button>
                </Card>
            </div>
        );
    }

    return (
        <div className="quiz-container">
            {/* Result Summary */}
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
                    Kết quả bài kiểm tra
                </h2>

                <Row gutter={16} className="result-stats">
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
                                {formatTime(result.actual_time_spent || result.saint_analysis_data?.time_spent || 0)}
                            </div>
                        </div>
                    </Col>
                </Row>

                <div className="action-buttons">
                    <Button
                        type="primary"
                        size="large"
                        icon={<ReloadOutlined />}
                        onClick={() => navigate('/quiz-setup')}
                    >
                        Làm bài kiểm tra mới
                    </Button>

                    <Button
                        type="default"
                        size="large"
                        icon={<BookOutlined />}
                        onClick={() => navigate('/student-weak-skills', {
                            state: {
                                analysisData: result.saint_analysis_data || {
                                    score: result.score,
                                    total_questions: result.total_questions,
                                    correct_answers: result.correct_answers,
                                    quiz_id: result.quiz_id
                                }
                            }
                        })}
                        style={{ backgroundColor: '#ff4d4f', borderColor: '#ff4d4f', color: 'white' }}
                    >
                        Xem kỹ năng yếu
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

            {/* Skill Analysis - Good Skills & Weak Skills */}
            <Row gutter={16} style={{ marginTop: 24 }}>
                {/* Good Skills */}
                <Col xs={24} md={12}>
                    <Card
                        title={
                            <span>
                                <SmileOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                                Nhóm kỹ năng tốt
                            </span>
                        }
                        headStyle={{ background: '#f6ffed', borderBottom: '2px solid #52c41a' }}
                    >
                        {goodSkills.length > 0 ? (
                            <List
                                dataSource={goodSkills}
                                renderItem={(skill) => (
                                    <List.Item>
                                        <div style={{ width: '100%' }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                <span style={{ fontWeight: 'bold' }}>{skill.skill_name}</span>
                                                <span style={{ color: '#52c41a', fontWeight: 'bold', fontSize: '16px' }}>
                                                    {skill.accuracy}%
                                                </span>
                                            </div>
                                        </div>
                                    </List.Item>
                                )}
                            />
                        ) : (
                            <div style={{ textAlign: 'center', padding: '20px', color: '#8c8c8c' }}>
                                Chưa có kỹ năng tốt
                            </div>
                        )}
                    </Card>
                </Col>

                {/* Weak Skills */}
                <Col xs={24} md={12}>
                    <Card
                        title={
                            <span>
                                <FrownOutlined style={{ color: '#ff4d4f', marginRight: 8 }} />
                                Nhóm kỹ năng yếu
                            </span>
                        }
                        headStyle={{ background: '#fff2e8', borderBottom: '2px solid #ff4d4f' }}
                    >
                        {weakSkills.length > 0 ? (
                            <List
                                dataSource={weakSkills}
                                renderItem={(skill) => (
                                    <List.Item>
                                        <div style={{ width: '100%' }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                <span style={{ fontWeight: 'bold' }}>{skill.skill_name}</span>
                                                <span style={{ color: '#ff4d4f', fontWeight: 'bold', fontSize: '16px' }}>
                                                    {skill.accuracy}%
                                                </span>
                                            </div>
                                        </div>
                                    </List.Item>
                                )}
                            />
                        ) : (
                            <div style={{ textAlign: 'center', padding: '20px', color: '#8c8c8c' }}>
                                Tất cả kỹ năng đều tốt! 🎉
                            </div>
                        )}
                    </Card>
                </Col>
            </Row>

            {/* Detailed Results - Collapsed by default */}
            <Card style={{ marginTop: 24 }}>
                <Collapse
                    ghost
                    expandIcon={({ isActive }) => <DownOutlined rotate={isActive ? 180 : 0} />}
                >
                    <Collapse.Panel
                        header={
                            <span style={{ fontSize: '16px', fontWeight: 'bold' }}>
                                📋 Chi tiết từng câu hỏi ({result.detailed_results.length} câu)
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
                                            <div>
                                                <strong>Giải thích:</strong> {item.explanation}
                                            </div>
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

            {/* Saint Analysis Data */}
            {result.saint_analysis_data && (
                <Card title="Dữ liệu phân tích Saint" style={{ marginTop: 24 }}>
                    <Row gutter={16}>
                        <Col xs={24} sm={12}>
                            <Statistic title="Môn học" value={result.saint_analysis_data.subject} />
                        </Col>
                        <Col xs={24} sm={12}>
                            <Statistic title="Lớp" value={result.saint_analysis_data.grade} />
                        </Col>
                        <Col xs={24} sm={12}>
                            <Statistic title="Độ khó" value={result.saint_analysis_data.difficulty_level} />
                        </Col>
                        <Col xs={24} sm={12}>
                            <Statistic title="Thời gian (giây)" value={result.saint_analysis_data.time_spent} />
                        </Col>
                    </Row>

                    <div style={{ marginTop: 16, padding: 16, background: '#f8f9fa', borderRadius: 8 }}>
                        <h4>Dữ liệu gửi cho Saint Analysis API:</h4>
                        <pre style={{ background: 'white', padding: 12, borderRadius: 4, overflow: 'auto' }}>
                            {JSON.stringify(result.saint_analysis_data, null, 2)}
                        </pre>
                    </div>
                </Card>
            )}



        </div>
    );
};

export default QuizResult;

