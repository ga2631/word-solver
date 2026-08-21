# Word Solver • Full-Stack Wordle Solver

A modern, production-ready full-stack application built with **Docker**, **Python (FastAPI)** on the backend, and **ReactJS (Vite)** on the frontend. The project features an intelligent heuristic-based Wordle puzzle solver, interactive step-by-step 3D board visualizer, dual API support (local simulation & live Votee API), and real-time candidate search space analytics.

---

## 📑 Table of Contents

- [📚 Problem Analysis & Resolution Process (`/docs`)](#-problem-analysis--resolution-process-docs)
- [✨ Key Features](#-key-features)
- [🏛️ Project Architecture](#️-project-architecture)
- [🚀 Quickstart with Docker Compose](#-quickstart-with-docker-compose)
- [🛠️ Local Development](#️-local-development)
  - [Backend Setup (Python / FastAPI)](#backend-setup-python--fastapi)
  - [Frontend Setup (React / Vite)](#frontend-setup-react--vite)
- [📡 API Endpoints](#-api-endpoints)
- [🧠 Solving Algorithm & Strategy](#-solving-algorithm--strategy)
- [🧪 Verification & Testing](#-verification--testing)
- [👥 Collaboration & Contribution](#-collaboration--contribution)

---

## 📚 Problem Analysis & Resolution Process (`/docs`)

This project was systematically designed, developed, and optimized through a structured three-phase engineering process documented in the [`/docs`](docs/) directory:

| Phase Document                                                      | Focus Area                  | Description                                                                                                                                                                                                         |
| :------------------------------------------------------------------ | :-------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [**1. Approaching the Problem**](docs/1.approaching-the-problem.md) | Requirements & Architecture | Deconstructs Wordle rules, analyzes the external [Votee API specification](https://wordle.votee.dev:8000/redoc), designs the core solver algorithm workflow, and outlines UI/UX requirements.                       |
| [**2. Problem Resolution**](docs/2.resolve-problem.md)              | Implementation & Testing    | Details dictionary preparation, local mock evaluator API implementation, candidate filtering rules (`matches_feedback`), end-to-end solver endpoints, and Docker containerization.                                  |
| [**3. Solution Optimization**](docs/3.optimize-solution.md)         | Performance & Experience    | Documents weighted letter frequency heuristics, dictionary length chunking, the 3-panel zero-scroll UI layout, interactive step-by-step solving API (`/solver/next-guess`), and multi-stage non-root Docker builds. |

---

## ✨ Key Features

- 🧠 **Intelligent Heuristic Solver**: Precomputed high-entropy starting words and weighted letter frequency scoring to solve puzzles in an average of 3–5 attempts across word lengths 3–8 (supporting 2–15).
- 🎮 **3-Panel Interactive Dashboard**: Single-viewport responsive layout with real-time controls, animated 3D tile-flip board, search space reduction charts, and an A–Z analyzed letter matrix.
- 🔄 **Interactive & Batch Solving Modes**:
  - **Live Step-by-Step (`/solver/next-guess`)**: Coordinates sequential API requests for live UI stepping and state inspection.
  - **End-to-End Batch (`/resolve`)**: Solves the entire puzzle in a single round-trip with full audit trace.
- 🌐 **Dual Environment Support**: Seamlessly switch between the **Local Mock Evaluator API** (for offline testing) and the **Live Votee API** (`https://wordle.votee.dev:8000`).
- ⚡ **Optimized Performance**: Segmented dictionary index (`words_len_*.json`) for fast $O(K)$ candidate pruning and minimal memory usage.
- 🐳 **Production-Ready Docker**: Multi-stage builds with non-root security compliance, native healthchecks, and Nginx reverse proxy.

---

## 🏛️ Project Architecture

```
word-solver/
├── backend/                  # Python FastAPI Microservice
│   ├── app/
│   │   ├── api/              # API routing & v1 versioned endpoints
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── daily.py       # Daily puzzle evaluation
│   │   │       │   ├── health.py      # Microservice health check
│   │   │       │   ├── random.py      # Random puzzle evaluation
│   │   │       │   ├── resolve.py     # Batch puzzle auto-solver
│   │   │       │   ├── solver.py      # Interactive step-by-step solver
│   │   │       │   └── word.py        # Target word evaluation
│   │   │       └── router.py          # Unified API router
│   │   ├── core/             # Configuration & Pydantic settings
│   │   │   └── config.py
│   │   ├── schemas/          # Pydantic validation models
│   │   │   ├── resolve.py
│   │   │   ├── solver.py
│   │   │   ├── word.py
│   │   │   └── wordle.py
│   │   ├── services/         # Business logic layer
│   │   │   ├── daily_store.py         # Daily word storage & generation
│   │   │   ├── resolver_service.py    # Batch solver engine
│   │   │   └── wordle_service.py      # Evaluator & dictionary candidate engine
│   │   ├── static/           # Dictionary datasets & partitioned chunks
│   │   └── main.py           # FastAPI application entrypoint
│   ├── scripts/              # Data processing & dictionary chunking utilities
│   │   └── process_words.py
│   ├── tests/                # Automated pytest test suites
│   │   ├── test_daily.py
│   │   ├── test_main.py
│   │   ├── test_process_words.py
│   │   ├── test_random.py
│   │   ├── test_resolve.py
│   │   └── test_word.py
│   ├── .dockerignore
│   ├── .env.example
│   ├── Dockerfile            # Multi-stage Python 3.11 slim container
│   └── requirements.txt
├── docs/                     # Design, Implementation & Optimization Documentation
│   ├── 1.approaching-the-problem.md
│   ├── 2.resolve-problem.md
│   └── 3.optimize-solution.md
├── frontend/                 # ReactJS + Vite SPA
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   │   ├── Header.jsx             # Top navigation & status bar
│   │   │   └── WordleVisualizer.jsx   # 3-panel dashboard & live board visualizer
│   │   ├── services/         # API HTTP client & service connectors
│   │   │   └── api.js
│   │   ├── App.css           # UI design system, glassmorphism & animations
│   │   ├── App.jsx           # Application root container
│   │   ├── index.css         # Global styles & CSS resets
│   │   └── main.jsx          # React DOM entrypoint
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
└── README.md                 # Project documentation
```

---

## 🚀 Quickstart with Docker Compose

The simplest way to spin up the entire application stack is with Docker Compose:

### 1. Configure Environment

```bash
cp .env.example .env
```

### 2. Build and Start All Containers

```bash
docker compose up --build
```

### 3. Access Services

| Service                      | URL                                                        | Description                                      |
| :--------------------------- | :--------------------------------------------------------- | :----------------------------------------------- |
| **Frontend Application**     | [http://localhost:3000](http://localhost:3000)             | Interactive React visualizer & solver dashboard  |
| **Backend API**              | [http://localhost:8000](http://localhost:8000)             | FastAPI REST API microservice                    |
| **Swagger Interactive Docs** | [http://localhost:8000/docs](http://localhost:8000/docs)   | Interactive OpenAPI documentation & API explorer |
| **ReDoc Documentation**      | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Alternative formatted API specification          |

To stop running containers:

```bash
docker compose down
```

---

## 🛠️ Local Development

### Backend Setup (Python / FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the FastAPI development server with hot reload:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
5. Run automated tests:
   ```bash
   pytest tests/ -v
   ```

---

### Frontend Setup (React / Vite)

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
4. Open [http://localhost:3000](http://localhost:3000) (or `http://localhost:5173`) in your browser.

---

## 📡 API Endpoints

| Method | Endpoint                    | Parameters / Body                                            | Description                                                |
| :----- | :-------------------------- | :----------------------------------------------------------- | :--------------------------------------------------------- |
| `GET`  | `/`                         | —                                                            | Root health greeting & route summary                       |
| `GET`  | `/api/v1/health`            | —                                                            | Microservice health check status                           |
| `GET`  | `/api/v1/daily`             | `?guess=crane&size=5`                                        | Check guess against the deterministic daily word           |
| `GET`  | `/api/v1/random`            | `?guess=crane&size=5&seed=123`                               | Check guess against a random word (optional seed)          |
| `GET`  | `/api/v1/word/{word}`       | `?guess=crane`                                               | Check guess against a specific target word                 |
| `GET`  | `/api/v1/resolve`           | `?mode=daily&size=5&starting_word=crane`                     | Solve puzzle in batch mode and return complete step trace  |
| `POST` | `/api/v1/solver/next-guess` | JSON body (`word_length`, `history`, `remaining_candidates`) | Compute optimal next candidate guess & update search space |

---

## 🧠 Solving Algorithm & Strategy

The solver uses an information-theoretic candidate reduction strategy:

1. **Strategic Starting Seed**: Uses precomputed words containing common vowels and consonants (e.g., `crane` for 5 letters, `roam` for 4 letters, `stare`/`soare` variations) to maximize initial information gain.
2. **Strict Feedback Pruning (`matches_feedback`)**:
   - `correct`: Retains only candidate words having the exact letter at the exact position.
   - `present`: Retains only candidate words containing the letter, excluding candidates with the letter at the current position.
   - `absent`: Eliminates words containing the letter (accounting for letter frequencies if the letter also appears as `present` or `correct`).
3. **Positional & Frequency Heuristic Scoring**:
   - Ranks remaining candidates by unique letter frequency weights across the English language (`E, T, A, O, I, N, S, R, H, D, L, U, C...`).
   - Prioritizes words that test high-probability unseen characters to maximize candidate elimination per round.

---

## 🧪 Verification & Testing

- **Backend Pytest Suite** (unit & integration tests):
  ```bash
  cd backend && pytest tests/ -v
  ```
- **Frontend Production Build**:
  ```bash
  cd frontend && npm run build
  ```
- **Docker Compose Configuration Check**:
  ```bash
  docker compose config
  ```

---

## 👥 Collaboration & Contribution

This project was developed through a pair programming collaboration between **Tan Huynh Nhat** and the **AI Assistant (Antigravity)**.

### 👤 Tan Huynh Nhat (Lead Developer & Product Owner)

- **Requirements & Strategy**: Defined project requirements, scope, target APIs ([Votee API](https://wordle.votee.dev:8000/redoc)), and algorithm performance expectations.
- **Problem-Solving Roadmap**: Structured the phased analysis and documentation methodology across [`/docs`](docs/) (Approaching -> Resolving -> Optimizing).
- **System Architecture**: Designed the containerized multi-service architecture (Docker Compose, FastAPI backend, Nginx reverse proxy, React SPA).
- **UI/UX Direction**: Envisioned the 3-panel single-viewport dashboard, interactive step-by-step solver mode, dark theme aesthetics, and search space visualization.
- **Project Governance**: Managed Git version control, branching workflows, commits, integration testing, and build verification.

### 🤖 AI Assistant / Antigravity (AI Pair Programmer)

- **Algorithm Implementation**: Built the core candidate filtering logic (`matches_feedback`), strict letter frequency constraints, and weighted heuristic scoring engine.
- **Backend Engineering**: Implemented FastAPI microservice endpoints (`/daily`, `/random`, `/word`, `/resolve`, `/solver/next-guess`), Pydantic validation schemas, and dictionary chunking utilities.
- **Frontend Development**: Developed React components (`WordleVisualizer.jsx`, `Header.jsx`), API client layer (`api.js`), 3D tile-flip animations, A–Z letter matrix, and responsive CSS styling.
- **Testing & Quality Assurance**: Created automated `pytest` test suites covering data processing, endpoints, and solver logic.
- **DevOps & Documentation**: Authored multi-stage Dockerfiles (non-root execution, healthchecks), `docker-compose.yml`, `nginx.conf`, comprehensive documentation in [`/docs`](docs/), and the project `README.md`.
