# Generate Word • Full-Stack Web Application

A modern, production-ready full-stack application built with **Docker**, **Python (FastAPI)** on the backend, and **ReactJS (Vite)** on the frontend.

---

## 🏛️ Project Architecture

```
generate-word/
├── backend/                  # Python FastAPI Microservice
│   ├── app/
│   │   ├── api/              # API router & v1 versioned endpoints
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── daily.py
│   │   │       │   ├── health.py
│   │   │       │   ├── random.py
│   │   │       │   └── word.py
│   │   │       └── router.py
│   │   ├── core/             # Configuration & Pydantic settings
│   │   │   └── config.py
│   │   ├── schemas/          # Pydantic data validation models
│   │   │   ├── word.py
│   │   │   └── wordle.py
│   │   ├── services/         # Business logic layer
│   │   │   ├── daily_store.py
│   │   │   └── wordle_service.py
│   │   ├── static/           # Dictionary assets
│   │   └── main.py           # FastAPI application entrypoint
│   ├── scripts/              # Data processing utilities
│   │   └── process_words.py
│   ├── tests/                # Automated pytest test suites
│   │   ├── test_daily.py
│   │   ├── test_main.py
│   │   ├── test_process_words.py
│   │   ├── test_random.py
│   │   └── test_word.py
│   ├── .dockerignore
│   ├── .env.example
│   ├── Dockerfile            # Python 3.11 slim container
│   └── requirements.txt
├── frontend/                 # ReactJS + Vite SPA
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   │   ├── Header.jsx
│   │   │   └── WordGenerator.jsx
│   │   ├── services/         # API HTTP client
│   │   │   └── api.js
│   │   ├── App.css           # Component styles
│   │   ├── App.jsx           # Main application shell
│   │   ├── index.css         # Design system & tokens
│   │   └── main.jsx          # React DOM mounting
│   ├── .dockerignore
│   ├── .env.example
│   ├── Dockerfile            # Multi-stage Node build + Nginx Alpine
│   ├── nginx.conf            # SPA routing & API reverse proxy
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── .env.example              # Root environment template
├── .gitignore                # Global git ignore configuration
├── docker-compose.yml        # Multi-container orchestration
└── README.md
```

---

## 🚀 Quickstart with Docker Compose

The easiest way to run the full stack is using Docker Compose:

### 1. Clone & Configure Environment
```bash
cp .env.example .env
```

### 2. Build and Start All Containers
```bash
docker compose up --build
```

### 3. Access Services
- **Frontend App**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

To stop the containers:
```bash
docker compose down
```

---

## 🛠️ Local Development (Without Docker)

### Backend Setup (Python)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
5. Run automated tests:
   ```bash
   pytest tests/
   ```

---

### Frontend Setup (ReactJS / Vite)

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
4. Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Root API greeting & route directory |
| `GET` | `/api/v1/health` | Service health status |
| `GET` | `/api/v1/daily` | Check guess against daily puzzle word (`?guess=...&size=5`) |
| `GET` | `/api/v1/random` | Check guess against random puzzle word (`?guess=...&size=5&seed=...`) |
| `GET` | `/api/v1/word/{word}` | Check guess against target word (`?guess=...`) |

---

## 🧪 Verification & Testing

- **Backend Pytest**:
  ```bash
  cd backend && pytest tests/ -v
  ```
- **Frontend Build**:
  ```bash
  cd frontend && npm run build
  ```
- **Docker Compose Config Validation**:
  ```bash
  docker compose config
  ```
