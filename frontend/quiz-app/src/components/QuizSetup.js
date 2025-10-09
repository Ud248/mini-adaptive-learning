import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, Select, Button, Card } from 'antd';
import { PlayCircleOutlined } from '@ant-design/icons';
import axios from 'axios';
import { useToast } from '../contexts/ToastContext';

const { Option } = Select;

const QuizSetup = () => {
    const [form] = Form.useForm();
    const navigate = useNavigate();
    const { showSuccess, showError } = useToast();
    const [loading, setLoading] = useState(false);
    const [subjects, setSubjects] = useState([]);
    const [grades, setGrades] = useState([]);

    useEffect(() => {
        loadInitialData();
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    const loadInitialData = async () => {
        try {
            const [subjectsRes, gradesRes] = await Promise.all([
                axios.get('http://localhost:8001/quiz/subjects'),
                axios.get('http://localhost:8001/quiz/grades')
            ]);

            setSubjects(subjectsRes.data.subjects);
            setGrades(gradesRes.data.grades);
        } catch (error) {
            console.error('Lỗi tải dữ liệu:', error);
            showError('Không thể tải dữ liệu khởi tạo từ API. Sử dụng dữ liệu mặc định...');

            // Fallback về dữ liệu mặc định
            setSubjects(["Toán", "Tiếng Việt", "Khoa học", "Lịch sử", "Địa lý"]);
            setGrades([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]);
        }
    };


    const handleSubmit = async (values) => {
        setLoading(true);
        try {
            const response = await axios.post('http://localhost:8001/quiz/generate', {
                grade: values.grade,
                subject: values.subject,
                num_questions: 30  // Mặc định 30 câu hỏi
            });

            if (response.data.quiz_id) {
                showSuccess('Tạo bài kiểm tra thành công!');
                navigate(`/quiz/${response.data.quiz_id}`);
            }
        } catch (error) {
            console.error('Lỗi tạo quiz:', error);
            showError('Không thể tạo bài kiểm tra từ API. Vui lòng thử lại.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="quiz-container">
            <Card className="setup-form">
                <h2>
                    <PlayCircleOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                    Thiết lập bài kiểm tra
                </h2>

                <Form
                    form={form}
                    layout="vertical"
                    onFinish={handleSubmit}
                    initialValues={{
                        grade: 1,
                        subject: "Toán"
                    }}
                >
                    <Form.Item
                        label="Lớp học"
                        name="grade"
                        rules={[{ required: true, message: 'Vui lòng chọn lớp học!' }]}
                    >
                        <Select placeholder="Chọn lớp học" size="large" disabled>
                            {grades.map(grade => (
                                <Option key={grade} value={grade}>
                                    Lớp {grade}
                                </Option>
                            ))}
                        </Select>
                    </Form.Item>

                    <Form.Item
                        label="Môn học"
                        name="subject"
                        rules={[{ required: true, message: 'Vui lòng chọn môn học!' }]}
                    >
                        <Select
                            placeholder="Chọn môn học"
                            size="large"
                            disabled
                        >
                            {subjects.map(subject => (
                                <Option key={subject} value={subject}>
                                    {subject}
                                </Option>
                            ))}
                        </Select>
                    </Form.Item>

                    <div style={{
                        background: '#f0f8ff',
                        padding: '16px',
                        borderRadius: '8px',
                        marginBottom: '16px',
                        border: '1px solid #d9d9d9'
                    }}>
                        <p style={{ margin: 0, color: '#1890ff', fontWeight: '500' }}>
                            📚 Hệ thống sẽ lấy ngẫu nhiên 40 câu hỏi từ tất cả các chương của môn Toán lớp 1
                        </p>
                    </div>

                    <Form.Item>
                        <Button
                            type="primary"
                            htmlType="submit"
                            size="large"
                            className="start-quiz-btn"
                            loading={loading}
                            icon={<PlayCircleOutlined />}
                        >
                            {loading ? 'Đang tạo bài kiểm tra...' : 'Bắt đầu làm bài'}
                        </Button>
                    </Form.Item>
                </Form>
            </Card>
        </div>
    );
};

export default QuizSetup;
