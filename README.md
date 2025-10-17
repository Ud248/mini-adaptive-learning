# 🎓 Mini Adaptive Learning

> **Hệ thống học tập thích ứng thông minh cho học sinh tiểu học Việt Nam** - Sử dụng AI để tự động sinh câu hỏi phù hợp với kỹ năng yếu của từng học sinh

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-18.2+-61dafb.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.110-009688.svg)](https://fastapi.tiangolo.com/)
[![Status](https://img.shields.io/badge/status-beta-orange.svg)](https://github.com/Ud248/mini-adaptive-learning)

---

## 📖 Giới thiệu

**Mini Adaptive Learning** là một hệ thống học tập thích ứng (Adaptive Learning System) được xây dựng riêng cho học sinh tiểu học Việt Nam. Hệ thống tự động phát hiện kỹ năng yếu của học sinh và sử dụng AI để sinh câu hỏi luyện tập phù hợp, giúp cải thiện hiệu quả học tập.

### 🎯 Vấn đề giải quyết

- **Thiếu cá nhân hóa**: Học sinh học cùng tài liệu, không phù hợp với trình độ cá nhân
- **Khó phát hiện điểm yếu**: Giáo viên khó theo dõi chi tiết kỹ năng của từng em
- **Thiếu tài nguyên luyện tập**: Không đủ câu hỏi thích hợp để luyện tập kỹ năng yếu
- **Học theo kiểu truyền thống**: Chưa tận dụng công nghệ AI trong giáo dục

### ⭐ Tại sao Adaptive Learning quan trọng?

Adaptive Learning giúp mỗi học sinh có lộ trình học tập riêng, tập trung vào những gì còn yếu, tránh lãng phí thời gian vào những gì đã thành thạo. Kết quả là **học nhanh hơn, hiệu quả hơn và hứng thú hơn**.

---

## ✨ Tính năng chính

### 🤖 **AI Question Generation**
- Tự động sinh câu hỏi bằng AI Agent (sử dụng Gemini, Ollama)
- RAG-powered: Kết hợp kiến thức từ SGK và SGV qua vector search
- Tuân thủ chuẩn kiến thức kỹ năng giáo dục tiểu học Việt Nam

### 📊 **Knowledge Tracing với SAINT++**
- Theo dõi tiến độ học tập của học sinh theo thời gian
- Dự đoán khả năng trả lời đúng câu hỏi tiếp theo
- Phát hiện tự động kỹ năng yếu cần luyện tập

### 💪 **Adaptive Practice Mode**
- Luyện tập thông minh theo kỹ năng yếu
- Câu hỏi được tạo động dựa trên profile học sinh
- Cập nhật real-time khả năng của học sinh

### ✅ **Auto Validation & Grading**
- Validation tự động câu hỏi về logic, toán học, ngôn ngữ
- Chấm điểm tự động với detailed feedback
- Hỗ trợ câu hỏi có hình ảnh (via SeaweedFS)

### 🎨 **Modern UI/UX**
- Giao diện thân thiện với học sinh tiểu học
- Ant Design components với Vietnamese locale
- Responsive: tương thích mobile và desktop

### 🔐 **Secure Authentication**
- JWT-based authentication
- Role-based access control (học sinh, giáo viên, admin)
- Password hashing với bcrypt

---

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                         │
│                      http://localhost:3001                       │
│                    Ant Design + React Router                     │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      │ HTTP REST API (JWT Auth)
                      │
┌─────────────────────┴───────────────────────────────────────────┐
│                      BACKEND SERVICES                            │
├──────────────────────────────────────────────────────────────────┤
│  Quiz API (FastAPI)          │   SAINT Analysis (FastAPI)       │
│  http://localhost:8001       │   http://localhost:8000          │
│  • Quiz management           │   • Knowledge tracing            │
│  • Auto grading              │   • Skill prediction             │
│  • User authentication       │   • Progress tracking            │
│  • AI Agent integration      │   • Profile update               │
└────────────┬─────────────────┴──────────────┬───────────────────┘
             │                                │
             │                                │
┌────────────┴────────────┐      ┌───────────┴────────────┐
│     AI AGENT MODULE     │      │  DATABASES & STORAGE   │
│  • Question generation  │      │  • MongoDB (primary)   │
│  • RAG with Milvus      │      │  • Milvus (vectors)    │
│  • Multi-LLM Hub        │      │  • MinIO (object)      │
│  • Validation pipeline  │      │  • SeaweedFS (images)  │
└─────────────────────────┘      └────────────────────────┘
```

### 🔧 Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 18.2, Ant Design 5.12, React Router 6.8, Axios |
| **Backend** | FastAPI 0.110, Uvicorn, Pydantic, Python 3.10+ |
| **AI/ML** | LangChain, Google Gemini API, Ollama (local LLM), Sentence-Transformers |
| **Databases** | MongoDB 7.0+ (primary), Milvus 2.3 (vectors), MinIO (object storage) |
| **Authentication** | JWT (python-jose), bcrypt (passlib) |
| **DevOps** | Docker, Docker Compose, Poetry (optional) |
| **Embeddings** | Vietnamese Sentence-Transformers (keepitreal/vietnamese-sbert) |

---

## 🚀 Quick Start

### Prerequisites

- **Python** 3.10+ ([download](https://www.python.org/downloads/))
- **Node.js** 16+ và npm ([download](https://nodejs.org/))
- **Docker Desktop** ([download](https://www.docker.com/products/docker-desktop/))
- **Git** ([download](https://git-scm.com/downloads))

### 1️⃣ Clone Repository

```bash
git clone https://github.com/Ud248/mini-adaptive-learning.git
cd mini-adaptive-learning
```

### 2️⃣ Setup Environment Variables

Tạo file `.env` ở project root:

```env
# MongoDB
MONGO_URL=mongodb://localhost:27017
DATABASE_NAME=mini_adaptive_learning

# Milvus Vector DB
MILVUS_HOST=localhost
MILVUS_PORT=19530

# JWT Authentication
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Google Gemini API (để sử dụng AI Agent)
GEMINI_API_KEY=your-google-gemini-api-key

# Ollama (optional, local LLM)
OLLAMA_IP=http://localhost:11434

# Image Service
IMAGE_BASE_URL=http://125.212.229.11:8888

# Data paths
SGK_JSON_1=database/data_insert/sgk-toan-1-ket-noi-tri-thuc-tap-1.json
SGK_JSON_2=database/data_insert/sgk-toan-1-ket-noi-tri-thuc-tap-2.json
SGV_JSON_PATH=database/data_insert/sgv_ketnoitrithuc.json
```

### 3️⃣ Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend/quiz-app
npm install
cd ../..
```

### 4️⃣ Start All Services (Automatic)

```bash
# Sử dụng script tự động (khuyến nghị)
python app.py
```

**Script này sẽ tự động:**
- ✅ Kiểm tra và khởi động Docker Desktop
- ✅ Start Milvus, MongoDB, MinIO containers
- ✅ Start Backend Quiz API (port 8001)
- ✅ Start Backend SAINT Analysis (port 8000)
- ✅ Start Frontend React App (port 3001)

### 5️⃣ Setup Databases (First Time Only)

**Trong terminal mới:**

```bash
# Setup MongoDB collections & indexes
python database/mongodb/setup_mongodb.py

# Setup Milvus collections
python database/milvus/setup_milvus.py

# Import sample data
python database/mongodb/insert_users.py
python database/mongodb/insert_placement_questions.py
python database/mongodb/insert_sgk_to_mongodb.py
python database/mongodb/insert_sgv_to_mongodb.py

# Insert vector embeddings (có thể mất vài phút)
python database/milvus/insert_sgv_to_milvus.py
python database/milvus/insert_sgk_to_milvus.py
```

### 6️⃣ Access Application

- **Frontend Quiz App**: http://localhost:3001
- **Backend Quiz API**: http://localhost:8001
- **Backend SAINT API**: http://localhost:8000
- **Quiz API Docs**: http://localhost:8001/docs
- **SAINT API Docs**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001 (admin/admin)
- **Milvus Attu**: http://localhost:3000 (nếu có trong docker-compose)

### 🧪 Test Login

**Sample credentials** (được tạo từ `database/data_insert/users_sample.json`):

```
Email: student1@example.com
Password: password123
```

---

## 📁 Cấu trúc dự án

```
mini-adaptive-learning/
├── 📱 frontend/
│   └── quiz-app/              # React frontend (Ant Design)
│       ├── src/
│       │   ├── components/    # UI components
│       │   ├── contexts/      # React contexts (Auth, Quiz)
│       │   └── api/          # API client utilities
│       └── public/
├── 🔧 backend/
│   ├── quiz_api/             # Main Quiz API (FastAPI)
│   │   ├── main.py          # API endpoints
│   │   └── schemas.py       # Pydantic models
│   └── saint_analysis/      # Knowledge Tracing API (SAINT++)
│       ├── main.py
│       └── app/
│           ├── api/         # SAINT endpoints
│           └── services/    # Business logic
├── 🤖 agent/                 # AI Agent Module (ALQ-Agent)
│   ├── llm/                 # Multi-LLM Hub (Gemini, Ollama)
│   ├── prompts/             # Prompt templates
│   ├── tools/               # Question generation, RAG, validation
│   └── workflow/            # Agent workflow orchestration
├── 🗄️ database/
│   ├── mongodb/             # MongoDB clients & scripts
│   ├── milvus/              # Milvus clients & scripts
│   └── embeddings/          # Vietnamese embedding service
├── ⚙️ configs/
│   └── agent.yaml           # AI Agent configuration
├── 🧪 tests/                # Unit & integration tests
├── 📦 volumes/              # Docker persistent data
│   ├── milvus/
│   └── minio/
├── 📄 app.py                # Auto-start script
├── 🐳 docker-compose.yml    # Docker services
├── 📋 requirements.txt      # Python dependencies
└── 📖 README.md            # This file
```

### 📚 Module Documentation

Mỗi module có README riêng với hướng dẫn chi tiết:

- [**Frontend Quiz App**](frontend/quiz-app/README.md) - React UI, authentication, quiz flows
- [**Backend Quiz API**](backend/quiz_api/README.md) - REST API, auto grading, user management
- [**Backend SAINT Analysis**](backend/saint_analysis/README.md) - Knowledge tracing, skill prediction
- [**AI Agent Module**](agent/README.md) - Question generation, RAG, validation pipeline
- [**Database Module**](database/README.md) - MongoDB, Milvus setup, data import scripts
- [**Configs**](configs/README.md) - Configuration files và guidelines

---

## 🛠️ Installation & Setup Chi tiết

### Manual Setup (Alternative)

Nếu không dùng `python app.py`, bạn có thể start từng service thủ công:

#### Terminal 1: Docker Services
```bash
docker-compose up -d
```

#### Terminal 2: Backend Quiz API
```bash
python -m uvicorn backend.quiz_api.main:app --host 0.0.0.0 --port 8001 --reload
```

#### Terminal 3: Backend SAINT Analysis
```bash
python -m uvicorn backend.saint_analysis.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Terminal 4: Frontend
```bash
cd frontend/quiz-app
npm start  # Chạy ở port 3001
```

### Setup LLM Providers

#### Option A: Google Gemini (Cloud)
```bash
# Lấy API key từ: https://aistudio.google.com/app/apikey
# Thêm vào .env:
GEMINI_API_KEY=your-api-key-here
```

#### Option B: Ollama (Local)
```bash
# Install Ollama: https://ollama.ai
# Pull model
ollama pull gemma2:9b

# Verify
curl http://localhost:11434/api/tags
```

### Database Setup Notes

- **MongoDB**: Collections được tạo tự động khi insert data
- **Milvus**: Cần chạy `setup_milvus.py` trước khi insert vectors
- **Embeddings**: Lần đầu tiên sẽ download model (~400MB)
- **Sample Data**: `users_sample.json` chứa 3 users để test

---

## 💻 Development

### Workflow phát triển

```bash
# 1. Create feature branch
git checkout -b feature/your-feature-name

# 2. Make changes

# 3. Test locally
python -m pytest tests/

# 4. Commit with meaningful message
git commit -m "feat: add new feature description"

# 5. Push and create PR
git push origin feature/your-feature-name
```

### Branch Strategy

- `main` - Production-ready code
- `develop` - Development branch
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Urgent production fixes

### Code Conventions

#### Python (PEP 8)
```python
# Use snake_case for functions and variables
def generate_question(student_id: str) -> dict:
    """Docstring with description."""
    pass

# Use PascalCase for classes
class QuestionGenerator:
    pass
```

#### JavaScript (Airbnb Style Guide)
```javascript
// Use camelCase for variables and functions
const fetchQuizData = async (userId) => {
  // ...
};

// Use PascalCase for React components
const QuizComponent = () => {
  return <div>...</div>;
};
```

### Running Tests

```bash
# All tests
python -m pytest tests/

# Specific test file
python -m pytest tests/test_question_generation_tool.py

# With coverage
python -m pytest tests/ --cov=agent --cov-report=html
```

---

## 🚢 Deployment

### Production Checklist

- [ ] Đổi `JWT_SECRET_KEY` thành giá trị bảo mật mạnh
- [ ] Setup SSL/TLS certificates
- [ ] Configure production MongoDB với authentication
- [ ] Setup backup strategy cho databases
- [ ] Configure CORS properly cho production domain
- [ ] Setup monitoring và logging (e.g., Sentry, CloudWatch)
- [ ] Optimize Docker images (multi-stage builds)
- [ ] Setup CI/CD pipeline (GitHub Actions, GitLab CI)
- [ ] Configure rate limiting
- [ ] Setup CDN cho static assets

### Docker Production Build

```bash
# Build production frontend
cd frontend/quiz-app
npm run build

# Build backend Docker images (nếu có Dockerfile)
docker build -t mini-adaptive-backend:latest .

# Or use docker-compose with production config
docker-compose -f docker-compose.prod.yml up -d
```

### Cloud Deployment Options

- **Frontend**: Vercel, Netlify, AWS S3 + CloudFront
- **Backend**: AWS ECS, Google Cloud Run, DigitalOcean App Platform
- **Databases**: MongoDB Atlas, Zilliz Cloud (Milvus managed)
- **Full Stack**: AWS, Google Cloud Platform, Azure

---

## 📚 Documentation

### API Documentation

- **Quiz API**: http://localhost:8001/docs (Swagger UI)
- **SAINT API**: http://localhost:8000/docs (Swagger UI)
- **Redoc Format**: Thay `/docs` bằng `/redoc`

### Architecture Documentation

Xem file [ARCHITECTURE.md](docs/ARCHITECTURE.md) (coming soon) để hiểu:
- System design patterns
- Database schemas
- AI Agent workflow
- Security considerations

### User Guides

- [Student User Guide](docs/USER_GUIDE_STUDENT.md) (coming soon)
- [Teacher User Guide](docs/USER_GUIDE_TEACHER.md) (coming soon)
- [Admin User Guide](docs/USER_GUIDE_ADMIN.md) (coming soon)

---

## 🤝 Contributing

Chúng tôi rất hoan nghênh mọi đóng góp! Vui lòng đọc [CONTRIBUTING.md](CONTRIBUTING.md) trước khi submit PR.

### How to Contribute

1. Fork repository này
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

### Issue Templates

- [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md)
- [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md)
- [Question](.github/ISSUE_TEMPLATE/question.md)

### PR Guidelines

- Viết description rõ ràng về changes
- Link đến related issues
- Update documentation nếu cần
- Ensure tests pass
- Follow code style guidelines

---

## 🗓️ Roadmap

### ✅ Phase 1: MVP (Completed)
- [x] Basic question generation với AI
- [x] MongoDB integration
- [x] Simple React frontend
- [x] JWT authentication
- [x] Auto grading

### 🚧 Phase 2: Adaptive Learning (In Progress)
- [x] SAINT++ knowledge tracing
- [x] Skill-based question filtering
- [x] Milvus RAG integration
- [ ] Advanced student analytics dashboard
- [ ] Teacher dashboard với insights

### 📋 Phase 3: Enhanced Features (Planned)
- [ ] Multi-grade support (grade 2-5)
- [ ] Gamification (badges, leaderboard)
- [ ] Parent monitoring portal
- [ ] Mobile app (React Native)
- [ ] Offline mode support
- [ ] Speech-to-text cho câu hỏi nghe

### 🚀 Phase 4: Scale & Optimize (Future)
- [ ] Kubernetes deployment
- [ ] Microservices architecture
- [ ] Real-time collaboration
- [ ] Multi-tenancy support
- [ ] Performance optimization (caching, CDN)
- [ ] Advanced NLP features

---

## 👥 Team & Credits

### Core Team

- **Ud248** - Project Lead & Full Stack Developer - [GitHub](https://github.com/Ud248)

### Contributors

Cảm ơn những người đã đóng góp vào dự án này:

<!-- ALL-CONTRIBUTORS-LIST:START -->
<!-- Danh sách contributors sẽ được tự động generate -->
<!-- ALL-CONTRIBUTORS-LIST:END -->

### Acknowledgments

- **Vietnamese SBERT Model**: [keepitreal/vietnamese-sbert](https://huggingface.co/keepitreal/vietnamese-sbert)
- **SAINT++ Paper**: "SAINT+: Integrating Temporal Features for EdNet Correctness Prediction" (Kim et al., 2020)
- **Milvus**: Vector database của Zilliz
- **FastAPI**: Modern Python web framework
- **React & Ant Design**: Powerful UI libraries

### References & Papers

- [SAINT++: Integrating Temporal Features for EdNet Correctness Prediction](https://arxiv.org/abs/2010.12042)
- [Deep Knowledge Tracing](https://papers.nips.cc/paper/2015/hash/bac9162b47c56fc8a4d2a519803d51b3-Abstract.html)
- [Adaptive Learning Systems: A Comprehensive Survey](https://ieeexplore.ieee.org/)

---

## 📄 License

Dự án này được phát hành dưới **MIT License** - xem file [LICENSE](LICENSE) để biết thêm chi tiết.

```
MIT License

Copyright (c) 2025 Ud248

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

[Full license text...]
```

---

## 📞 Contact & Support

### Support Channels

- **GitHub Issues**: [Create an issue](https://github.com/Ud248/mini-adaptive-learning/issues)
- **Email**: your-email@example.com (replace với email thật)
- **Discord**: [Join our community](https://discord.gg/your-invite) (optional)

### FAQ

**Q: Tôi gặp lỗi "Docker not running"?**  
A: Khởi động Docker Desktop và đợi nó fully loaded, sau đó chạy lại `python app.py`.

**Q: Port 8001 bị chiếm?**  
A: Dừng process đang chiếm port: `netstat -ano | findstr :8001` rồi `taskkill /PID <pid> /F`

**Q: Không sinh được câu hỏi AI?**  
A: Kiểm tra `GEMINI_API_KEY` trong `.env` hoặc cài Ollama và pull model `gemma2:9b`

**Q: Milvus không kết nối được?**  
A: Đợi 30-60s sau khi `docker-compose up -d` để Milvus fully started. Kiểm tra: `docker ps`

**Q: Frontend không load được?**  
A: Kiểm tra đã chạy `npm install` trong `frontend/quiz-app/` chưa.

---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Ud248/mini-adaptive-learning&type=Date)](https://star-history.com/#Ud248/mini-adaptive-learning&Date)

---

<div align="center">

### 💚 Made with love for Vietnamese education 🇻🇳

**Nếu project này hữu ích, hãy cho một ⭐️ để ủng hộ nhé!**

[🏠 Homepage](https://github.com/Ud248/mini-adaptive-learning) · 
[📖 Documentation](https://github.com/Ud248/mini-adaptive-learning/wiki) · 
[🐛 Report Bug](https://github.com/Ud248/mini-adaptive-learning/issues) · 
[✨ Request Feature](https://github.com/Ud248/mini-adaptive-learning/issues)

</div>