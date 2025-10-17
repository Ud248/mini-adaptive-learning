import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Card, Button, Radio, Progress, Spin, Modal } from 'antd';
import { LeftOutlined, RightOutlined, CheckOutlined, ClockCircleOutlined, QuestionCircleOutlined } from '@ant-design/icons';
import { useToast } from '../contexts/ToastContext';
import { submitPracticeResult } from '../api/practice';

// Separate component to ensure clean re-mount
const QuestionOptions = ({ question, selectedAnswer, onAnswerChange }) => {
    return (
        <Radio.Group
            style={{ width: '100%' }}
            value={selectedAnswer}
            onChange={(e) => onAnswerChange(e.target.value)}
        >
            <div
                className="answer-options"
                style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, width: '100%' }}
            >
                {question.options.map((option, index) => {
                    const isSelected = selectedAnswer === index;
                    return (
                        <div
                            key={`${question.id}-opt-${index}`}
                            className="answer-option"
                            onClick={() => onAnswerChange(index)}
                            style={{
                                border: `2px solid ${isSelected ? '#1890ff' : '#d9d9d9'}`,
                                borderRadius: 8,
                                padding: 16,
                                minHeight: 80,
                                display: 'flex',
                                alignItems: 'center',
                                cursor: 'pointer',
                                background: isSelected ? '#e6f7ff' : '#fff',
                                transition: 'all 0.2s ease'
                            }}
                            onMouseEnter={(e) => {
                                if (!isSelected) {
                                    e.currentTarget.style.borderColor = '#40a9ff';
                                    e.currentTarget.style.background = '#f0f8ff';
                                }
                            }}
                            onMouseLeave={(e) => {
                                if (!isSelected) {
                                    e.currentTarget.style.borderColor = '#d9d9d9';
                                    e.currentTarget.style.background = '#fff';
                                }
                            }}
                        >
                            <Radio value={index}>
                                <span style={{ marginLeft: 8 }}>{option}</span>
                            </Radio>
                        </div>
                    );
                })}
            </div>
        </Radio.Group>
    );
};

const PracticeTaking = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { showError, showSuccess } = useToast();

    const { questions = [], meta = {}, practice_id } = useMemo(() => {
        const s = (location && location.state) || {};
        return {
            questions: s.questions || [],
            meta: s.meta || {},
            practice_id: s.practice_id || `practice_${Date.now()}`,
        };
    }, [location]);

    const [currentIndex, setCurrentIndex] = useState(0);
    const [answers, setAnswers] = useState({});
    const [timeLeft, setTimeLeft] = useState(0);
    const [initialTime, setInitialTime] = useState(0);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);

    const currentQuestion = questions[currentIndex];

    // Memoize handler for current question
    const handleCurrentQuestionAnswer = useCallback((value) => {
        if (currentQuestion?.id) {
            setAnswers((prev) => ({ ...prev, [currentQuestion.id]: value }));
        }
    }, [currentQuestion?.id]);

    useEffect(() => {
        if (!questions || questions.length === 0) {
            showError('Không có câu hỏi luyện tập');
            navigate('/student-weak-skills');
            return;
        }
        const totalSeconds = Math.max(0, Number(questions.length || 0) * 60);
        setTimeLeft(totalSeconds);
        setInitialTime(totalSeconds);
        setLoading(false);
    }, [questions, navigate, showError]);

    useEffect(() => {
        if (loading || timeLeft <= 0) return;
        const t = setInterval(() => {
            setTimeLeft((prev) => (prev > 0 ? prev - 1 : 0));
        }, 1000);
        return () => clearInterval(t);
    }, [loading, timeLeft]);

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    const handleSubmit = () => {
        Modal.confirm({
            title: 'Nộp bài luyện tập',
            content: 'Xác nhận nộp bài và xem kết quả?',
            okText: 'Nộp bài',
            cancelText: 'Hủy',
            onOk: async () => {
                setSubmitting(true);
                try {
                    const detailed = questions.map((q) => {
                        const selectedIndex = answers[q.id];
                        const userAnswer = selectedIndex !== undefined ? (q.options?.[selectedIndex] ?? '') : 'Chưa trả lời';
                        const correctAnswer = q.options?.[q.correctIndex] ?? '';
                        const correct = userAnswer === correctAnswer && userAnswer !== 'Chưa trả lời';
                        return {
                            question_id: q.id,
                            question: q.question,
                            user_answer: userAnswer,
                            correct_answer: correctAnswer,
                            correct,
                            explanation: q.explanation || '',
                        };
                    });

                    const total = questions.length;
                    const correctCount = detailed.filter(d => d.correct).length;
                    const answeredCount = Object.keys(answers).length;
                    const wrongCount = Math.max(0, answeredCount - correctCount);
                    const unanswered = Math.max(0, total - answeredCount);
                    const score = total > 0 ? (correctCount / total) * 100 : 0;
                    const timeSpent = initialTime - timeLeft; // Thời gian đã sử dụng (giây)

                    const result = {
                        practice_id,
                        total_questions: total,
                        correct_answers: correctCount,
                        wrong_answers: wrongCount,
                        answered_questions: answeredCount,
                        unanswered_questions: unanswered,
                        score: score,
                        time_spent: timeSpent,
                        actual_time_spent: timeSpent,
                        detailed_results: detailed,
                        meta,
                        questions,
                    };

                    // Submit practice result to update student profile
                    try {
                        const studentEmail = localStorage.getItem('student_email');
                        const skillId = meta?.skill_id || meta?.skill || 'unknown';

                        if (studentEmail && skillId) {
                            await submitPracticeResult({
                                student_email: studentEmail,
                                skill_id: skillId,
                                total_questions: total,
                                correct_answers: correctCount,
                                wrong_answers: wrongCount,
                                unanswered_questions: unanswered,
                                score: score,
                                avg_response_time: null  // Could calculate this if tracking time per question
                            });
                            showSuccess('Đã cập nhật kết quả luyện tập!');
                        }
                    } catch (error) {
                        console.error('Failed to submit practice result:', error);
                        // Continue to show results even if update fails
                        showError('Lưu kết quả thất bại, nhưng bạn vẫn có thể xem điểm');
                    }

                    navigate('/practice/result', { state: { result } });
                } finally {
                    setSubmitting(false);
                }
            }
        });
    };

    if (loading) {
        return (
            <div className="loading-spinner">
                <Spin size="large" />
            </div>
        );
    }

    if (!questions || questions.length === 0) {
        return (
            <div className="quiz-container">
                <Card>
                    <p>Không có câu hỏi luyện tập</p>
                    <Button onClick={() => navigate('/student-weak-skills')}>Quay lại</Button>
                </Card>
            </div>
        );
    }

    return (
        <div className="quiz-container">
            <div className="quiz-header">
                <div className="header-left">
                    <div className="timer">
                        <ClockCircleOutlined style={{ marginRight: 8 }} />
                        {formatTime(timeLeft)}
                    </div>
                </div>
                <div className="header-right">
                    <Progress
                        percent={Math.round((Object.keys(answers).length / questions.length) * 100)}
                        strokeColor="#1890ff"
                        trailColor="#f0f0f0"
                        strokeWidth={10}
                        status="active"
                        showInfo={false}
                    />
                </div>
            </div>

            <Card className="question-content" key={`question-card-${currentQuestion.id}`}>
                <div className="question-top">
                    <div className="question-top-left">
                        <QuestionCircleOutlined style={{ marginRight: 8 }} />
                        Câu {currentIndex + 1} / {questions.length}
                    </div>
                    <div className="question-top-right">
                        <div className="navigation-buttons">
                            <Button
                                onClick={() => setCurrentIndex((i) => Math.max(0, i - 1))}
                                disabled={currentIndex === 0}
                                icon={<LeftOutlined />}
                            >
                                Trước
                            </Button>
                            <Button
                                onClick={() => setCurrentIndex((i) => Math.min(questions.length - 1, i + 1))}
                                disabled={currentIndex === questions.length - 1}
                                icon={<RightOutlined />}
                            >
                                Sau
                            </Button>
                        </div>
                    </div>
                </div>

                <div className="question-text">{currentQuestion.question}</div>

                <div className="answer-section">
                    <QuestionOptions
                        key={`question-${currentQuestion.id}-${currentIndex}`}
                        question={currentQuestion}
                        selectedAnswer={answers[currentQuestion.id]}
                        onAnswerChange={handleCurrentQuestionAnswer}
                    />
                </div>

                <div className="submit-section">
                    <Button
                        type="primary"
                        size="large"
                        icon={<CheckOutlined />}
                        onClick={handleSubmit}
                        loading={submitting}
                        disabled={timeLeft === 0}
                    >
                        {submitting ? 'Đang nộp...' : 'Nộp bài'}
                    </Button>
                </div>
            </Card>
        </div>
    );
};

export default PracticeTaking;


