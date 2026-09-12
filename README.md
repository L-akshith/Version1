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

## Railway & Netlify Staging Deployment Guide

### Deployment Architecture
- **Frontend**: Netlify (React 18 + Vite SPA)
- **Backend API**: Railway (`examshield-api` FastAPI Service)
- **Release Worker**: Railway (`examshield-worker` Dedicated Daemon Service)
- **Database**: Railway PostgreSQL

---

### Step-by-Step Deployment Instructions

#### STEP 1: Repository Push
Push the ExamShield codebase to your GitHub repository.

#### STEP 2: Create Railway Project & PostgreSQL Database
1. Log into [Railway.app](https://railway.app) and create a new project.
2. Add a **PostgreSQL** database service.
3. Note the provided `DATABASE_URL` connection string.

#### STEP 3: Deploy Backend API Service (`examshield-api`)
1. Add a new service connected to your GitHub repository targeting the `backend/` path.
2. Configure Environment Variables in Railway:
   - `DATABASE_URL`: Your Railway PostgreSQL connection URL
   - `JWT_SECRET_KEY`: High-entropy 256-bit secret string
   - `ENVIRONMENT`: `staging`
   - `CRYPTO_PROVIDER`: `local` (or `kms` if using AWS KMS)
   - `STORAGE_PROVIDER`: `local` (or `s3` if using S3)
   - `LOCAL_KEYS_DIR`: `/app/data/.local_keys` (Subdirectory on persistent volume)
   - `UPLOAD_DIR`: `/app/data/uploads` (Subdirectory on persistent volume)
   - `CORS_ORIGINS`: `["https://your-app.netlify.app"]`
3. Persistent Volume Mounting (Cryptographic & File Storage Safety):
   - In Railway UI, add a **Persistent Volume** to the backend service mounted at `/app/data`.
   - Configure `LOCAL_KEYS_DIR=/app/data/.local_keys` and `UPLOAD_DIR=/app/data/uploads`.
   - This ensures generated RSA wrapping keys (`.pem` files) and encrypted paper artifacts survive backend process restarts and redeployments without obscuring application files at `/app`.
4. Start Command:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

#### STEP 4: Execute Alembic Database Migrations
Run Alembic migrations via Railway CLI or one-off container command:
```bash
alembic upgrade head
python -m app.database.seed
```

#### STEP 5: Deploy Release Worker Service (`examshield-worker`)
1. Create a second Railway service in the same project connected to the same repository.
2. Link the same `DATABASE_URL` and environment variables.
3. Start Command:
   ```bash
   python -m app.worker.release_worker
   ```

#### STEP 6: Deploy React Frontend to Netlify
1. Log into [Netlify.com](https://netlify.com) and create a new site from your GitHub repository.
2. Build Settings:
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `frontend/dist`
3. Environment Variables:
   - `VITE_API_URL`: `https://<your-railway-api-domain>.up.railway.app`
4. Deploy the site.

#### STEP 7: Verification
1. Access `https://<your-railway-api-domain>.up.railway.app/api/v1/health` to confirm API health.
2. Access `https://<your-netlify-app>.netlify.app` to log in, upload, approve, encrypt, and schedule question paper releases.

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