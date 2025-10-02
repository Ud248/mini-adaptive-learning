import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Button, Radio, Image, Progress, message, Spin, Modal } from 'antd';
import {
    LeftOutlined,
    RightOutlined,
    CheckOutlined,
    ClockCircleOutlined,
    QuestionCircleOutlined
} from '@ant-design/icons';
import axios from 'axios';

const QuizTaking = () => {
    const { quizId } = useParams();
    const navigate = useNavigate();
    const [questions, setQuestions] = useState([]);
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [answers, setAnswers] = useState({});
    const [timeLeft, setTimeLeft] = useState(1800); // 30 phút
    const [startTime, setStartTime] = useState(Date.now()); // Thời gian bắt đầu
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        loadQuiz();
    }, [quizId]);

    useEffect(() => {
        const timer = setInterval(() => {
            setTimeLeft(prev => {
                if (prev <= 1) {
                    handleSubmitQuiz();
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);

        return () => clearInterval(timer);
    }, []);

    const loadQuiz = async () => {
        try {
            // Gọi API để lấy quiz data thực tế
            const response = await axios.post('http://localhost:8001/quiz/generate', {
                grade: 1,
                subject: 'Toán',
                num_questions: 30
            });

            if (response.data && response.data.questions) {
                // Sử dụng options từ API (từ questions_grade1.json)
                setQuestions(response.data.questions);
                message.success(`Đã tải ${response.data.questions.length} câu hỏi từ API`);
            } else {
                throw new Error('Không có dữ liệu từ API');
            }
        } catch (error) {
            console.error('Lỗi tải quiz:', error);
            message.error('Không thể tải bài kiểm tra từ API. Đang sử dụng dữ liệu mẫu...');

            // Fallback về dữ liệu mẫu nếu API không hoạt động
            const mockQuestions = Array.from({ length: 30 }, (_, i) => ({
                id: `q_${i + 1}`,
                lesson: `Bài học ${i + 1}`,
                grade: 1,
                chapter: 'Số học',
                subject: 'Toán',
                question: `Câu hỏi ${i + 1}: Đây là câu hỏi mẫu cho bài kiểm tra. Bạn hãy chọn đáp án đúng nhất.`,
                image_question: i % 5 === 0 ? ['@http://125.212.229.11:8888/data-ai/images/class_1/toan/sgk/ketnoitrithuc/tap1/image_0010_bbox_000_figure_cls3.png'] : [], // Chỉ 20% câu hỏi có hình ảnh
                answer: `Đáp án ${i + 1}`,
                image_answer: [],
                options: [
                    `Đáp án A cho câu ${i + 1}`,
                    `Đáp án B cho câu ${i + 1}`,
                    `Đáp án C cho câu ${i + 1}`,
                    `Đáp án D cho câu ${i + 1}`
                ]
            }));

            setQuestions(mockQuestions);
        } finally {
            setLoading(false);
        }
    };

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    const handleAnswerChange = (questionId, answer) => {
        setAnswers(prev => ({
            ...prev,
            [questionId]: answer
        }));
    };

    const handleNext = () => {
        if (currentQuestionIndex < questions.length - 1) {
            setCurrentQuestionIndex(prev => prev + 1);
        }
    };

    const handlePrevious = () => {
        if (currentQuestionIndex > 0) {
            setCurrentQuestionIndex(prev => prev - 1);
        }
    };

    const handleSubmitQuiz = () => {
        Modal.confirm({
            title: 'Nộp bài kiểm tra',
            content: 'Bạn có chắc chắn muốn nộp bài kiểm tra? Bạn sẽ không thể thay đổi câu trả lời sau khi nộp.',
            okText: 'Nộp bài',
            cancelText: 'Hủy',
            onOk: async () => {
                setSubmitting(true);
                try {
                    // Tính thời gian thực tế đã làm bài
                    const endTime = Date.now();
                    const actualTimeSpent = Math.floor((endTime - startTime) / 1000);

                    // Chuyển đổi answers từ index thành string
                    const formattedAnswers = {};
                    Object.keys(answers).forEach(questionId => {
                        const answerIndex = answers[questionId];
                        const question = questions.find(q => q.id === questionId);
                        if (question && question.options && question.options[answerIndex]) {
                            formattedAnswers[questionId] = question.options[answerIndex];
                        } else {
                            formattedAnswers[questionId] = `Đáp án ${answerIndex}`;
                        }
                    });

                    console.log('📤 Gửi submission:', {
                        quiz_id: quizId,
                        answers: formattedAnswers
                    });

                    const response = await axios.post('http://localhost:8001/quiz/submit-simple', {
                        quiz_id: quizId,
                        answers: formattedAnswers
                    });

                    if (response.data) {
                        // Tạo kết quả chi tiết với thông tin thời gian thực
                        const detailedResult = {
                            ...response.data,
                            actual_time_spent: actualTimeSpent,
                            total_questions: 30, // Luôn là 30 câu
                            questions: questions,
                            user_answers: answers,
                            formatted_answers: formattedAnswers
                        };

                        message.success('Nộp bài thành công!');
                        navigate(`/result/${quizId}`, {
                            state: {
                                result: detailedResult,
                                questions: questions,
                                answers: answers
                            }
                        });
                    }
                } catch (error) {
                    console.error('Lỗi nộp bài:', error);
                    message.error('Không thể nộp bài. Vui lòng thử lại.');
                } finally {
                    setSubmitting(false);
                }
            }
        });
    };

    const getAnsweredCount = () => {
        return Object.keys(answers).length;
    };

    const getProgressPercentage = () => {
        if (!questions || questions.length === 0) {
            return 0;
        }
        const percent = (getAnsweredCount() / questions.length) * 100;
        return Math.max(0, Math.min(100, percent));
    };

    if (loading) {
        return (
            <div className="loading-spinner">
                <Spin size="large" />
            </div>
        );
    }

    if (questions.length === 0) {
        return (
            <div className="quiz-container">
                <Card>
                    <p>Không tìm thấy bài kiểm tra</p>
                    <Button onClick={() => navigate('/')}>Quay lại</Button>
                </Card>
            </div>
        );
    }

    const currentQuestion = questions[currentQuestionIndex];

    return (
        <div className="quiz-container">
            {/* Header (no Ant Card body wrapper) */}
            <div className="quiz-header">
                <div className="header-left">
                    <div className="timer">
                        <ClockCircleOutlined style={{ marginRight: 8 }} />
                        {formatTime(timeLeft)}
                    </div>
                </div>
                <div className="header-right">
                    <Progress
                        percent={Math.round(getProgressPercentage())}
                        strokeColor="#1890ff"
                        trailColor="#f0f0f0"
                        strokeWidth={10}
                        status="active"
                        showInfo={false}
                    />
                </div>
            </div>

            {/* Question Content */}
            <Card className="question-content">
                <div className="question-top">
                    <div className="question-top-left">
                        <QuestionCircleOutlined style={{ marginRight: 8 }} />
                        Câu {currentQuestionIndex + 1} / {questions.length}
                    </div>
                    <div className="question-top-right">
                        <div className="navigation-buttons">
                            <Button
                                onClick={handlePrevious}
                                disabled={currentQuestionIndex === 0}
                                icon={<LeftOutlined />}
                            >
                                Trước
                            </Button>
                            <Button
                                onClick={handleNext}
                                disabled={currentQuestionIndex === questions.length - 1}
                                icon={<RightOutlined />}
                            >
                                Sau
                            </Button>
                        </div>
                    </div>
                </div>
                <div className="question-text">
                    {currentQuestion.question}
                </div>

                {currentQuestion.image_question &&
                    currentQuestion.image_question.length > 0 &&
                    currentQuestion.image_question.some(url => url && url.trim() !== '') && (
                        <div className="question-images">
                            {currentQuestion.image_question
                                .filter(imageUrl => imageUrl && imageUrl.trim() !== '') // Lọc bỏ URL rỗng
                                .map((imageUrl, index) => {
                                    // Loại bỏ @ từ URL để hiển thị ảnh
                                    const cleanUrl = imageUrl.startsWith('@') ? imageUrl.substring(1) : imageUrl;
                                    return (
                                        <div key={index} className="question-image-container" style={{ marginBottom: '16px' }}>
                                            <Image
                                                src={cleanUrl}
                                                alt={`Hình ảnh câu hỏi ${index + 1}`}
                                                className="question-image"
                                                style={{
                                                    maxWidth: '100%',
                                                    height: 'auto',
                                                    border: '1px solid #d9d9d9',
                                                    borderRadius: '6px',
                                                    boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                                                }}
                                                preview={{
                                                    mask: 'Xem ảnh',
                                                    maskClassName: 'image-preview-mask'
                                                }}
                                            />
                                        </div>
                                    );
                                })}
                        </div>
                    )}

                <div className="answer-section">
                    <Radio.Group
                        value={answers[currentQuestion.id]}
                        onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
                    >
                        <div className="answer-options">
                            {currentQuestion.options.map((option, index) => (
                                <div key={index} className="answer-option">
                                    <Radio value={index}>
                                        <span style={{ marginLeft: 8 }}>{option}</span>
                                    </Radio>
                                </div>
                            ))}
                        </div>
                    </Radio.Group>
                </div>

                {/* Submit Button */}
                <div className="submit-section">
                    <Button
                        type="primary"
                        size="large"
                        icon={<CheckOutlined />}
                        onClick={handleSubmitQuiz}
                        loading={submitting}
                        disabled={timeLeft === 0}
                    >
                        {submitting ? 'Đang nộp...' : 'Nộp bài'}
                    </Button>
                </div>
            </Card>

            {/* Time Warning */}
            {timeLeft === 0 && (
                <Card>
                    <div style={{ color: '#ff4d4f', textAlign: 'center', fontWeight: 'bold' }}>
                        ⏰ Hết thời gian! Bài kiểm tra sẽ được tự động nộp.
                    </div>
                </Card>
            )}
        </div>
    );
};

export default QuizTaking;
