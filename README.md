# ExamShield

ExamShield is a secure examination paper management and distribution platform designed to prevent paper leaks for competitive examinations (such as NEET, JEE, UPSC, SSC, Banking, and University exams).

The platform separates responsibilities cleanly using **Clean Architecture** (API → Services → Repositories → Database) and implements **Role-Based Access Control (RBAC)** across 8 default examination authority roles.

## Architecture

```
                       API (v1 Routes)
                             │
                             ▼
                    Services (Business Logic)
                             │
                             ▼
                   Repositories (Data Access)
                             │
                             ▼
                      Database (PostgreSQL)
```

- **API Layer**: Exposes routes, serializes request/response payloads via Pydantic v2 schemas, and enforces RBAC check dependencies.
- **Service Layer**: Implements core business workflows (authentication, role assignment, user status lifecycle).
- **Repository Layer**: Generic async database wrappers (SQLAlchemy 2.0) that isolate SQL querying from business logic.
- **Database Layer**: PostgreSQL tables utilizing UUID primary keys and Alembic migration scripts.

---

## Tech Stack

### Backend
- **Python 3.11** + **FastAPI**
- **SQLAlchemy 2.0** (Asyncio / asyncpg) + **Alembic** (Migrations)
- **PostgreSQL 16**
- **JWT (python-jose)** + **bcrypt (passlib)**
- **Pytest** (Async unit and integration testing)

### Frontend
- **React 18** + **TypeScript** + **Vite**
- **React Router v6** + **React Hook Form** + **Zod**
- **Axios** (API calls with automatic bearer auth injection)
- **TanStack Query** (React Query)
- **Tailwind CSS** (Custom dark glassmorphism theme)

---

## Workspace Structure

```
├── backend/
│   ├── alembic/                 # Database migrations
│   ├── app/
│   │   ├── api/                 # Endpoint routes
│   │   ├── core/                # Config, permissions, dependencies
│   │   ├── database/            # Engine session and seeding utility
│   │   ├── exceptions/          # Custom exception classes & handlers
│   │   ├── middleware/          # Rate limiting, logging, auth interceptors
│   │   ├── models/              # ORM Database models
│   │   ├── repositories/        # SQL data access layers
│   │   ├── schemas/             # Pydantic serialization models
│   │   ├── services/            # Business validation services
│   │   └── utils/               # JWT & Hashing helpers
│   └── tests/                   # Pytest suite
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── contexts/            # React AuthContext
│   │   ├── hooks/               # Custom hooks (useAuth)
│   │   ├── layouts/             # Auth and Main Sidebar layouts
│   │   ├── pages/               # Login, Register, Users, Roles pages
│   │   ├── router/              # SPA route maps
│   │   ├── services/            # Axios API wrappers
│   │   └── types/               # TypeScript interfaces
│
└── docker-compose.yml           # Complete system orchestrator
```

---

## RBAC System

ExamShield seeds 8 default roles on initialization:
1. **Admin**: Unrestricted system management.
2. **Controller**: Exam lifecycle moderator (approves, schedules release).
3. **Question Setter**: Subjects expert upload.
4. **Translation Officer**: Regional translations.
5. **Moderator**: Verification and quality review.
6. **Exam Center Officer**: Release download target.
7. **Observer**: Read-only compliance auditor.
8. **Investigator**: Leaks forensic validator.

---

## Setup & Quickstart

### Option 1: Running with Docker Compose (Recommended)
This spins up PostgreSQL, Redis, the FastAPI Backend, and the React Frontend automatically:

```bash
docker compose up --build
```
- **Frontend URL**: `http://localhost:3000`
- **Backend Swagger Docs**: `http://localhost:8000/docs`
- **Default Superuser login**:
  - **Email**: `admin@examshield.gov.in`
  - **Password**: `ChangeThisPassword123!`

### Option 2: Running Locally for Development

#### Backend Setup
1. Change directory and create a virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run Alembic migrations:
   ```bash
   alembic upgrade head
   ```
4. Seed default database roles and superuser:
   ```bash
   python -m app.database.seed
   ```
5. Start local server:
   ```bash
   uvicorn app.main:app --reload
   ```

#### Frontend Setup
1. Change directory and install dependencies:
   ```bash
   cd frontend
   npm install
   ```
2. Start the Vite development server:
   ```bash
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

---

## Verification & Testing

### Running Backend Tests
The backend uses a separate, fast in-memory SQLite database configuration for isolated unit testing:

```bash
cd backend
pytest -v
```

Tests verify:
1. **Authentication API**: Registration constraints, duplicate email protection, login token response validation.
2. **User Operations**: Active status updates, administrative roles change checks.
3. **Generic Repository Pattern**: Database insert/update assertions, relationship eager loading queries.
