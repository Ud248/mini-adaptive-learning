import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, Select, Button, Card } from 'antd';
import { PlayCircleOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import { useToast } from '../contexts/ToastContext';

const { Option } = Select;

const QuizSetup = () => {
    const [form] = Form.useForm();
    const navigate = useNavigate();
    const { showSuccess, showError, showInfo } = useToast();
    const [loading, setLoading] = useState(false);

    // Mặc định hiển thị và khóa thay đổi (tính năng đang phát triển)
    const defaultSubject = 'Toán';
    const defaultGrade = 1;
    const allSubjects = ['Toán', 'Tiếng Việt', 'Khoa học', 'Lịch sử', 'Địa lý'];
    const allGrades = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];

    const handleOpenDropdown = (open) => {
        if (open) {
            showInfo('Chức năng thay đổi Lớp/Môn đang phát triển');
        }
    };


    const handleSubmit = async (values) => {
        setLoading(true);
        try {
            // Dùng mặc định lớp 1, môn Toán; các lựa chọn khác đang phát triển

            // Điều hướng sang trang làm bài, trang đó sẽ tự gọi generate một lần.
            showSuccess('Bắt đầu bài kiểm tra!');
            const tempId = `temp_${Date.now()}`;
            navigate(`/quiz/${tempId}`);
        } catch (error) {
            console.error('Lỗi điều hướng quiz:', error);
            showError('Không thể bắt đầu bài kiểm tra. Vui lòng thử lại.');
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

                <div style={{
                    background: '#f6ffed',
                    border: '1px solid #b7eb8f',
                    borderRadius: '6px',
                    padding: '12px 16px',
                    marginBottom: '24px',
                    fontSize: '14px',
                    color: '#52c41a'
                }}>
                    <strong>📝 Lưu ý:</strong> Hệ thống sẽ tạo câu hỏi phù hợp với lớp học và môn học của bạn. Chỉ bắt đầu làm bài khi muốn cập nhật đánh giá năng lực học tập.
                </div>

                <Form
                    form={form}
                    layout="vertical"
                    onFinish={handleSubmit}
                    initialValues={{
                        grade: defaultGrade,
                        subject: defaultSubject
                    }}
                >
                    <Form.Item
                        label="Lớp học"
                        name="grade"
                        rules={[{ required: true, message: 'Vui lòng chọn lớp học!' }]}
                    >
                        <Select placeholder="Chọn lớp học" size="large" onDropdownVisibleChange={handleOpenDropdown}>
                            {allGrades.map(grade => (
                                <Option key={grade} value={grade} disabled={grade !== defaultGrade}>
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
                            onDropdownVisibleChange={handleOpenDropdown}
                        >
                            {allSubjects.map(subject => (
                                <Option key={subject} value={subject} disabled={subject !== defaultSubject}>
                                    {subject}
                                </Option>
                            ))}
                        </Select>
                    </Form.Item>


                    <Form.Item>
                        <Button
                            type="primary"
                            htmlType="submit"
                            size="large"
                            className="start-quiz-btn"
                            loading={loading}
                            icon={<PlayCircleOutlined />}
                            block
                        >
                            {loading ? 'Đang tạo bài kiểm tra...' : 'Bắt đầu làm bài'}
                        </Button>
                    </Form.Item>

                    <Form.Item style={{ marginBottom: 0 }}>
                        <Button
                            icon={<ArrowLeftOutlined />}
                            onClick={() => navigate('/')}
                            danger
                            type="primary"
                            size="large"
                            block
                        >
                            Quay lại trang chủ
                        </Button>
                    </Form.Item>
                </Form>
            </Card>
        </div>
    );
};

export default QuizSetup;
