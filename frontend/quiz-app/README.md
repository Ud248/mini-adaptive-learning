# 🎓 Quiz App Frontend

> React-based frontend cho Mini Adaptive Learning - Giao diện làm bài kiểm tra, luyện tập kỹ năng yếu và phân tích kết quả

## 📋 Giới thiệu

Module **quiz-app** là giao diện chính của hệ thống học tập thích ứng, đảm nhận:

- 🎯 **Adaptive Quiz**: Làm bài kiểm tra thích ứng theo trình độ
- 💪 **Skill Practice**: Luyện tập kỹ năng yếu được AI recommend
- 🔐 **JWT Authentication**: Đăng nhập bảo mật với JWT tokens
- 📊 **Result Analysis**: Phân tích chi tiết kết quả và điểm yếu
- 🎨 **Modern UI**: Ant Design components với Vietnamese locale
- 📱 **Responsive**: Tương thích mobile và desktop
- 🖼️ **Rich Media**: Hỗ trợ câu hỏi và đáp án có hình ảnh

## 🛠️ Tech Stack

```javascript
// Core
react: ^18.2.0              // UI framework
react-dom: ^18.2.0          // DOM rendering
react-router-dom: ^6.8.0    // Client-side routing

// UI Library
antd: ^5.12.0               // Ant Design components
                            // Vietnamese locale built-in

// HTTP Client
axios: ^1.6.0               // API calls với interceptors

// Build Tool
react-scripts: 5.0.1        // Create React App scripts

// Testing
@testing-library/react: ^13.3.0
@testing-library/jest-dom: ^5.16.4
@testing-library/user-event: ^13.5.0
```

## � Cài đặt

### Prerequisites

```bash
# Node.js version
node --version  # Should be >= 16.x

# npm version
npm --version   # Should be >= 8.x
```

### Install Dependencies

```bash
# From project root
cd frontend/quiz-app

# Install packages
npm install

# Or with yarn
yarn install
```

## ⚙️ Cấu hình

### Environment Variables

File `public/env.js` (runtime configuration):

```javascript
window.env = {
    PORT: 3001,
    API_URL: 'http://localhost:8001',  // Quiz API backend
    SAINT_API_URL: 'http://localhost:8000'  // SAINT Analysis (optional)
};
```

### package.json Configuration

```json
{
  "proxy": "http://localhost:8001",
  "homepage": "http://localhost:3001",
  "scripts": {
    "start": "set PORT=3001 && react-scripts start",
    "dev": "set PORT=3001 && react-scripts start",
    "build": "react-scripts build"
  }
}
```

### Backend Integration

- **Quiz API**: `http://localhost:8001` (required)
- **SAINT Analysis**: `http://localhost:8000` (optional)
- **Authentication**: JWT-based với localStorage
- **Proxy**: Tránh CORS issues trong development
- **Image Service**: SeaweedFS cho câu hỏi có hình

## 📁 Cấu trúc Module

```
frontend/quiz-app/
├── public/                      # 🌐 Static files
│   ├── env.js                   # Runtime environment config
│   └── index.html               # HTML template
│
├── src/                         # 📦 Source code
│   ├── App.js                   # Main application với routing
│   ├── App.css                  # Global styles
│   ├── index.js                 # React entry point
│   ├── index.css                # Base CSS
│   │
│   ├── auth/                    # 🔐 Authentication
│   │   └── AuthContext.js       # JWT token management
│   │                            # Login/logout logic
│   │                            # User state management
│   │
│   ├── contexts/                # 🎯 React Contexts
│   │   └── ToastContext.js      # Toast notification system
│   │
│   └── components/              # 🧩 UI Components
│       ├── HomePage.js          # Landing page (dashboard)
│       ├── Login.js             # Login form
│       ├── AvatarMenu.js        # User menu dropdown
│       │
│       ├── QuizSetup.js         # Quiz configuration
│       ├── QuizTaking.js        # Quiz interface
│       ├── QuizResult.js        # Quiz results & analysis
│       │
│       ├── StudentWeakSkills.js # Weak skills dashboard
│       ├── PracticeSetup.js     # Practice configuration
│       ├── PracticeTaking.js    # Practice interface
│       ├── PracticeResult.js    # Practice results
│       │
│       ├── Toast.js             # Toast notification component
│       ├── Toast.css            # Toast styles
│       ├── ToastContainer.js    # Toast container
│       ├── BackToTop.js         # Scroll to top button
│       └── BackToTop.css        # BackToTop styles
│
├── build/                       # 🏗️ Production build (generated)
├── node_modules/                # 📚 Dependencies (generated)
├── package.json                 # NPM configuration
├── package-lock.json            # Dependency lock file
└── README.md                    # 📖 This file
```

## 🚀 Chạy Ứng Dụng

### Development Mode

```bash
# Start development server
npm start
# Or
npm run dev

# App runs at http://localhost:3001
# Auto-reload on file changes
# Opens browser automatically
```

### Production Build

```bash
# Create optimized build
npm run build

# Build output in build/ folder
# Ready for deployment
```

### Test

```bash
# Run test suite
npm test

# Run with coverage
npm test -- --coverage
```

### Scripts Available

```json
{
  "start": "set PORT=3001 && react-scripts start",  // Dev server
  "dev": "set PORT=3001 && react-scripts start",     // Alias for start
  "build": "react-scripts build",                     // Production build
  "test": "react-scripts test",                       // Run tests
  "eject": "react-scripts eject"                      // Eject CRA (irreversible)
}
```

## 🔌 API Integration

### Axios Configuration

```javascript
// Axios instance với interceptors
import axios from 'axios';

const api = axios.create({
  baseURL: window.env?.API_URL || 'http://localhost:8001'
});

// Request interceptor - Add JWT token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor - Handle errors
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### Endpoints Được Sử Dụng

#### Authentication 🔐
```javascript
POST /auth/login              // Login với email/username + password
POST /auth/logout             // Logout (client-side token removal)
GET /api/users/name           // Get user info (with JWT)
```

#### Quiz Management 📝
```javascript
POST /quiz/generate           // Generate quiz (grade, subject, num_questions)
POST /quiz/submit             // Submit answers & get results
GET /quiz/weak-skills/{email} // Get student's weak skills
```

#### Practice Management 💪
```javascript
POST /agent/questions/generate // Generate AI-powered practice questions
POST /practice/submit          // Submit practice & update profile
```

#### SAINT Integration 📊
```javascript
POST /quiz/submit-saint-data  // Send logs to SAINT analysis (optional)
```

## 🧩 Components & Routes

### Route Structure

```javascript
// Public routes
/login                         // Login page

// Protected routes (require JWT)
/                              // HomePage - Dashboard
/quiz-setup                    // Quiz configuration
/quiz/:quizId                  // Quiz taking interface
/result/:quizId                // Quiz results & analysis
/student-weak-skills           // Weak skills dashboard
/practice/setup                // Practice configuration
/practice/taking               // Practice interface
/practice/result               // Practice results
```

### Core Components

#### 1. **HomePage** (`/`)
- Dashboard với options:
  - 📝 Làm bài kiểm tra định kỳ
  - 💪 Luyện tập kỹ năng yếu
  - 📊 Xem phân tích kết quả
- Navigation hub cho toàn bộ app

#### 2. **Login** (`/login`)
- JWT authentication form
- Email/username + password
- Remember token in localStorage
- Auto redirect sau khi login

#### 3. **QuizSetup** (`/quiz-setup`)
- Configuration form:
  - Grade selection (default: Lớp 1)
  - Subject selection (default: Toán)
  - Number of questions
- Call `POST /quiz/generate`
- Redirect to QuizTaking

#### 4. **QuizTaking** (`/quiz/:quizId`)
- **Features**:
  - Question display với images
  - Multiple choice answers
  - Question navigation (prev/next)
  - Timer countdown
  - Progress indicator
  - Mark for review
  - Submit confirmation
- **State management**:
  - Answers tracking
  - Time tracking
  - Current question index
- **API calls**:
  - `POST /quiz/submit`
  - Optional: `POST /quiz/submit-saint-data`

#### 5. **QuizResult** (`/result/:quizId`)
- **Display**:
  - Overall score & percentage
  - Correct/incorrect breakdown
  - Detailed question-by-question results
  - Explanations for each answer
  - Images for questions/answers
- **Actions**:
  - Retry quiz
  - View weak skills
  - Go to practice

#### 6. **StudentWeakSkills** (`/student-weak-skills`)
- **Features**:
  - List weak skills from profile
  - Skill details (accuracy, avg time, status)
  - Filter by status (struggling, in_progress)
  - Sort by accuracy
- **API**: `GET /quiz/weak-skills/{email}`
- **Actions**:
  - Start practice for specific skill
  - View skill analytics

#### 7. **PracticeSetup** (`/practice/setup`)
- Select weak skill to practice
- Configure number of questions
- Call AI Agent for question generation
- Redirect to PracticeTaking

#### 8. **PracticeTaking** (`/practice/taking`)
- Similar to QuizTaking but for practice
- AI-generated questions
- Real-time feedback
- Adaptive difficulty

#### 9. **PracticeResult** (`/practice/result`)
- Practice results & analysis
- Profile update
- Skill mastery progress
- Recommendations for next practice

## 🎨 UI/UX Features

### Ant Design Components Used

```javascript
// Layout
import { Layout, Card, Row, Col, Divider } from 'antd';

// Navigation
import { Menu, Breadcrumb, Pagination } from 'antd';

// Forms
import { Form, Input, Button, Select, Radio, Checkbox } from 'antd';

// Feedback
import { Modal, message, notification, Spin, Progress } from 'antd';

// Data Display
import { Table, List, Avatar, Badge, Tag, Statistic } from 'antd';

// Icons
import { UserOutlined, LogoutOutlined, CheckCircleOutlined } from '@ant-design/icons';
```

### UI Features

#### 🌍 Vietnamese Locale
```javascript
import { ConfigProvider } from 'antd';
import viVN from 'antd/locale/vi_VN';

<ConfigProvider locale={viVN}>
  <App />
</ConfigProvider>
```

#### 📱 Responsive Design
- Mobile-first approach
- Breakpoints: 576px, 768px, 992px, 1200px
- Grid system với Ant Design Row/Col
- Touch-friendly buttons và inputs

#### 🎯 User Feedback
- **Toast notifications**: Success/error/info/warning
- **Loading states**: Spin components cho async operations
- **Progress indicators**: Quiz progress, skill mastery
- **Confirmations**: Modal cho critical actions (submit, exit)

#### 🖼️ Image Handling
- Lazy loading cho images
- Fallback cho missing images
- SeaweedFS integration với @ prefix
- Responsive images

#### 🎨 Theming
- Custom CSS với variables
- Ant Design theme customization
- Consistent color palette
- Modern, clean design

## 🧪 Testing & Development

### Run Tests

```bash
# Run test suite
npm test

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test -- Login.test.js
```

### Manual Testing Workflow

#### 1. Login Flow
```bash
# Start app
npm start

# Navigate to http://localhost:3001
# Should redirect to /login

# Login với account mẫu:
Email/Username: student1@gmail.com hoặc student1
Password: 123456

# Should redirect to HomePage (/)
```

#### 2. Quiz Flow
```
HomePage → Click "Làm bài kiểm tra"
  ↓
QuizSetup → Configure & Click "Bắt đầu"
  ↓
API: POST /quiz/generate
  ↓
QuizTaking → Answer questions → Click "Nộp bài"
  ↓
API: POST /quiz/submit
  ↓
QuizResult → View results & analysis
```

#### 3. Practice Flow
```
HomePage → Click "Luyện tập kỹ năng yếu"
  ↓
StudentWeakSkills → Select skill → Click "Luyện tập"
  ↓
PracticeSetup → Configure → Click "Bắt đầu"
  ↓
API: POST /agent/questions/generate
  ↓
PracticeTaking → Answer → Click "Nộp bài"
  ↓
API: POST /practice/submit
  ↓
PracticeResult → View results & profile update
```

### Test Accounts

```javascript
// Student account
{
  email: "student1@gmail.com",
  username: "student1",
  password: "123456",
  role: "student"
}

// Add more in MongoDB users collection
```

### Browser DevTools

```javascript
// Check localStorage
localStorage.getItem('token')
localStorage.getItem('user')

// Check API calls
// Network tab → Filter: XHR/Fetch

// Check React components
// React DevTools extension
```

## 🔄 Application Workflow

### Complete User Journey

```
┌─────────────────────────────────────────────────────────┐
│                    User Opens App                        │
│                 http://localhost:3001                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
              ┌─────────────┐
              │ Has Token?  │
              └──────┬──────┘
                     │
         ┌───────────┴────────────┐
         │                        │
        No                       Yes
         │                        │
         ↓                        ↓
    ┌────────┐              ┌──────────┐
    │ Login  │              │ HomePage │
    └────┬───┘              └────┬─────┘
         │                       │
         │ POST /auth/login      │
         ↓                       │
    ┌────────────┐               │
    │ Save Token │               │
    └────┬───────┘               │
         │                       │
         └───────────┬───────────┘
                     │
                     ↓
         ┌───────────────────────┐
         │ Choose Activity:      │
         │ 1. Quiz               │
         │ 2. Practice           │
         │ 3. View Weak Skills   │
         └───────────┬───────────┘
                     │
         ┌───────────┴────────────┐
         │                        │
     Quiz Path              Practice Path
         │                        │
         ↓                        ↓
    ┌──────────┐          ┌──────────────┐
    │QuizSetup │          │WeakSkills    │
    └────┬─────┘          └──────┬───────┘
         │                       │
         │ POST /quiz/generate   │ Select Skill
         ↓                       ↓
    ┌──────────┐          ┌──────────────┐
    │QuizTaking│          │PracticeSetup │
    └────┬─────┘          └──────┬───────┘
         │                       │
         │ POST /quiz/submit     │ POST /agent/questions/generate
         ↓                       ↓
    ┌──────────┐          ┌───────────────┐
    │QuizResult│          │PracticeTaking │
    └────┬─────┘          └──────┬────────┘
         │                       │
         │                       │ POST /practice/submit
         │                       ↓
         │               ┌────────────────┐
         │               │PracticeResult  │
         │               └────────┬───────┘
         │                        │
         └────────────┬───────────┘
                      │
                      ↓
              ┌───────────────┐
              │ Back to Home  │
              │ or Logout     │
              └───────────────┘
```

### State Management Flow

```javascript
// AuthContext manages:
- token (JWT)
- user (user info)
- login()
- logout()

// Local state per component:
- QuizTaking: questions, answers, currentQuestion, timeRemaining
- PracticeTaking: questions, answers, currentQuestion
- StudentWeakSkills: weakSkills, loading, filters

// API response handling:
try {
  const response = await axios.post('/quiz/submit', data);
  // Success: navigate to results
  navigate(`/result/${quizId}`);
} catch (error) {
  // Error: show toast notification
  showError('Có lỗi xảy ra');
}
```

## 🔗 Kết nối Module Khác

### Backend Dependencies

```javascript
// Quiz API (backend/quiz_api)
http://localhost:8001
- Authentication endpoints
- Quiz generation & submission
- User profile & weak skills
- Practice management

// SAINT Analysis (backend/saint_analysis) [Optional]
http://localhost:8000
- Knowledge tracing
- Learning analytics
- Skill mastery prediction
```

### Integration Points

1. **Authentication Flow**
   - Frontend: Login form → `POST /auth/login`
   - Backend: Validate credentials → Return JWT
   - Frontend: Store token → Add to all requests

2. **Quiz Flow**
   - Frontend: Quiz setup → `POST /quiz/generate`
   - Backend: Query MongoDB → Return questions
   - Frontend: Display → User answers → `POST /quiz/submit`
   - Backend: Grade → Return results

3. **Practice Flow**
   - Frontend: Select skill → `POST /agent/questions/generate`
   - Backend: AI Agent → RAG + LLM → Generate questions
   - Frontend: Display → User answers → `POST /practice/submit`
   - Backend: Update profile → Return results

## 🐛 Troubleshooting

### 1. App Won't Start

**Error**: `Port 3001 already in use`

```bash
# Windows - Find process
netstat -ano | findstr :3001

# Kill process
taskkill /PID <PID> /F

# Or use different port
set PORT=3002 && npm start
```

### 2. API Connection Failed

**Error**: `Network Error` or `ERR_CONNECTION_REFUSED`

```bash
# Check backend is running
curl http://localhost:8001/

# Check proxy in package.json
"proxy": "http://localhost:8001"

# Check window.env.API_URL in public/env.js
window.env = {
  API_URL: 'http://localhost:8001'
}
```

### 3. CORS Errors

**Error**: `Access-Control-Allow-Origin` in browser console

```python
# Backend (quiz_api/main.py) should have:
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. Login Fails / 401 Unauthorized

**Issue**: Cannot login or token invalid

```bash
# Check user exists in MongoDB
python -c "
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017')
db = client['mini_adaptive_learning']
user = db.users.find_one({'email': 'student1@gmail.com'})
print(user)
"

# Check JWT_SECRET_KEY matches between frontend storage and backend
# Clear localStorage and login again
localStorage.clear()
```

### 5. Images Not Loading

**Issue**: `image_question` or `image_answer` not displaying

```javascript
// Images should have @ prefix from backend
// Example: @http://125.212.229.11:8888/path/image.png

// Check SeaweedFS is running
curl http://125.212.229.11:8888

// In component, handle missing images:
<img 
  src={imageUrl} 
  alt="Question"
  onError={(e) => { e.target.style.display = 'none' }}
/>
```

### 6. Build Errors

**Error**: Module not found or compilation failed

```bash
# Clear cache and reinstall
Remove-Item -Recurse -Force node_modules, package-lock.json
npm install

# Clear React Scripts cache
Remove-Item -Recurse -Force node_modules/.cache
npm start
```

### 7. Quiz Not Generating

**Issue**: Empty quiz or error on generate

```bash
# Check backend logs
# Backend should have questions in MongoDB

# Check frontend request
console.log('Generating quiz:', { grade, subject, num_questions });

# Fallback to JSON file if MongoDB empty
# Backend handles this automatically
```

### 8. Toast Notifications Not Showing

**Issue**: No feedback after actions

```javascript
// Check ToastContext is wrapped properly
<ToastProvider>
  <App />
</ToastProvider>

// Use in component
const { showSuccess, showError } = useToast();
showSuccess('Message here');
```

### 9. Private Routes Not Working

**Issue**: Can access protected routes without login

```javascript
// Check PrivateRoute logic in App.js
const PrivateRoute = ({ children }) => {
  const { token } = useAuth();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

// Wrap routes:
<Route path="/" element={<PrivateRoute><HomePage /></PrivateRoute>} />
```

### 10. React DevTools Not Working

```bash
# Install React DevTools extension
# Chrome: https://chrome.google.com/webstore/detail/react-developer-tools/
# Firefox: https://addons.mozilla.org/en-US/firefox/addon/react-devtools/

# Check console for React warnings
# Use Profiler to debug performance
```

## 🚀 Deployment

### Development

```bash
npm run dev
# App runs at http://localhost:3001
```

### Production Build

```bash
# Create optimized build
npm run build

# Test build locally
npx serve -s build -l 3001

# Deploy build/ folder to:
# - Netlify
# - Vercel
# - AWS S3 + CloudFront
# - Nginx/Apache server
```

### Environment Variables for Production

```javascript
// production.env.js
window.env = {
  API_URL: 'https://api.yourdomain.com',
  SAINT_API_URL: 'https://saint.yourdomain.com'
};
```

---

## 📚 Tài liệu tham khảo

- [React Documentation](https://react.dev/)
- [Ant Design Components](https://ant.design/components/overview/)
- [React Router v6](https://reactrouter.com/en/main)
- [Axios Documentation](https://axios-http.com/docs/intro)
- [Quiz API README](../../backend/quiz_api/README.md)
- [Agent Module README](../../agent/README.md)

---

**Maintainer**: Mini Adaptive Learning Team  
**Last Updated**: October 17, 2025
