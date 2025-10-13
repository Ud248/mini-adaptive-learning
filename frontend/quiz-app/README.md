# Quiz App Frontend

## 📋 Tổng quan

**Quiz App** là module frontend React chuyên về giao diện làm bài kiểm tra trực tuyến trong hệ thống học tập thích ứng. Module này kết nối với backend FastAPI `quiz_api` để tạo bài kiểm tra, xử lý câu trả lời và hiển thị kết quả.

**Vai trò trong hệ thống:**
- Cung cấp giao diện người dùng cho việc làm bài kiểm tra
- Tích hợp với Quiz API backend để tạo và nộp bài
- Hiển thị kết quả và phân tích học tập
- Hỗ trợ đa ngôn ngữ (tiếng Việt)

## ⚙️ Yêu cầu

- **Node.js**: 16.x trở lên
- **npm**: 8.x trở lên (hoặc yarn)
- **Backend**: Quiz API chạy tại `http://localhost:8001`

## 🚀 Cài đặt

```bash
# Cài đặt dependencies
cd frontend/quiz-app
npm install

# Hoặc sử dụng yarn
yarn install
```

## 🔧 Cấu hình

### Environment Variables
File `public/env.js` chứa cấu hình:
```javascript
window.env = {
    PORT: 3001,
    API_URL: 'http://localhost:8001',
    // Tuỳ chọn: SAINT Analysis service (nếu chạy)
    SAINT_API_URL: 'http://localhost:8000'
};
```

### Backend Integration
- **API Base URL**: `http://localhost:8001`
- **Proxy**: Được cấu hình trong `package.json`
- **Authentication**: Yêu cầu đăng nhập bằng JWT (email/username + password)
- **SAINT Analysis**: client có thể gửi logs đến `SAINT_API_URL` (tuỳ chọn) thông qua backend hoặc trực tiếp

## 📁 Cấu trúc thư mục

```
frontend/quiz-app/
├── public/
│   ├── env.js              # Environment config
│   └── index.html          # HTML template
├── src/
│   ├── App.js              # Main component với routing + PrivateRoute
│   ├── App.css             # Global styles
│   ├── index.js            # Entry point
│   ├── index.css           # Global styles
│   ├── auth/
│   │   └── AuthContext.js  # Quản lý login/logout, lưu token
│   ├── contexts/
│   │   └── ToastContext.js # Context hiển thị toast tuỳ biến
│   └── components/         # UI components chính
│       ├── AvatarMenu.js
│       ├── BackToTop.js
│       ├── BackToTop.css
│       ├── Login.js
│       ├── QuizSetup.js
│       ├── QuizTaking.js
│       ├── QuizResult.js
│       ├── StudentWeakSkills.js
│       ├── Toast.js
│       ├── Toast.css
│       └── ToastContainer.js
├── package.json            # Dependencies
└── README.md              # Tài liệu này
```

Ghi chú: các thư mục trống `src/api`, `src/hooks`, `src/theme` đã được xoá để gọn dự án.

## 🏃‍♂️ Chạy ứng dụng

### Development Mode
```bash
# Chạy với port mặc định (3000)
npm start

# Chạy với port 3001 (như cấu hình)
npm run dev
```

Ứng dụng sẽ chạy tại: `http://localhost:3001`

### Production Build
```bash
npm run build
```

## 🔌 API Integration

### Endpoints được sử dụng:
- **Auth**:
  - `POST /auth/login` — đăng nhập
  - `POST /auth/logout` — đăng xuất
  - (Đã bỏ) `GET /me`
- **Quiz**:
  - `POST /quiz/generate` — tạo bài kiểm tra
  - `POST /quiz/submit` — nộp bài và chấm điểm
  - `GET /quiz/subjects` — danh sách môn học
  - `GET /quiz/grades` — danh sách lớp học

### HTTP Client:
- **Axios**: Được sử dụng để gọi API
- **Proxy**: Cấu hình trong package.json để tránh CORS

## 🧩 Components chính

### 1. **QuizSetup** (`/`)
- Thiết lập thông tin bài kiểm tra (hiện tại cố định lớp 1, môn Toán; có fallback dữ liệu)
- Chuyển hướng đến trang làm bài

### 2. **QuizTaking** (`/quiz/:quizId`)
- Hiển thị câu hỏi và đáp án
- Xử lý logic làm bài
- Timer và navigation
- Gọi API nộp bài; có gửi logs phân tích (tuỳ chọn) tới SAINT qua backend

### 3. **QuizResult** (`/result/:quizId`)
- Hiển thị kết quả chi tiết
- Phân tích đúng/sai
- Điểm số và thống kê

## 🎨 UI/UX Features

### Tech Stack:
- **React 18.2.0** - Frontend framework
- **Ant Design 5.12.0** - UI component library
- **React Router 6.8.0** - Client-side routing
- **Axios 1.6.0** - HTTP client

### UI Features:
- **Responsive design** - Tương thích mobile/desktop
- **Vietnamese locale** - Giao diện tiếng Việt
- **Modern UI** - Sử dụng Ant Design components
- **Real-time updates** - Cập nhật trạng thái real-time

## 🧪 Testing

### Chạy tests:
```bash
npm test
```

### Test thủ công luồng đăng nhập
1. Mở `http://localhost:3001` → chuyển hướng tới `/login`
2. Đăng nhập bằng tài khoản mẫu:
   - email: `student1@example.com` (hoặc username: `student1`)
   - password: `123456`
3. Sau khi đăng nhập thành công, hệ thống điều hướng về trang chính → bắt đầu quiz
4. Dùng nút “Đăng xuất” trên thanh header để thoát tài khoản

### Test coverage:
- Component rendering
- User interactions
- API integration
- Routing navigation

## 🔄 Workflow

### 1. **Setup Phase:**
```
User → QuizSetup → API /quiz/generate → Quiz ID
```

### 2. **Taking Phase:**
```
User → QuizTaking → Submit answers → API /quiz/submit
```

### 3. **Result Phase:**
```
API Response → QuizResult → Display results
```

## 🐛 Troubleshooting

### Lỗi kết nối API:
- Kiểm tra Quiz API backend chạy tại `http://localhost:8001`
- Kiểm tra proxy configuration trong `package.json`

### Lỗi CORS:
- Đảm bảo backend có CORS middleware
- Kiểm tra `allow_origins` trong backend

### Lỗi build:
```bash
# Xóa node_modules và cài lại
rm -rf node_modules package-lock.json
npm install
```

Nếu dùng Windows PowerShell:
```powershell
Remove-Item -Recurse -Force node_modules, package-lock.json
npm install
```

## 📱 Responsive Design

- **Mobile-first** approach
- **Breakpoints**: 768px, 1024px, 1200px
- **Touch-friendly** interface
- **Cross-browser** compatibility

## 🚀 Deployment

### Development:
```bash
npm run dev
```

### Production:
```bash
npm run build
# Deploy build/ folder to web server
```

Module frontend Quiz App sẵn sàng để phát triển và deploy! 🎉
