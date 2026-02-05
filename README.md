# Bug Reporting System API

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-red.svg)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)

Production-ready Bug Reporting System API built with FastAPI, PostgreSQL, and Redis. Designed for ~50 developers across 10 projects with enterprise-grade security, role-based access control, and comprehensive audit logging.

## Features

-  **RESTful API** with FastAPI and automatic OpenAPI documentation
-  **Authentication & Authorization** with RS256 JWT tokens and RBAC
-  **Database** with PostgreSQL 15, async SQLAlchemy, and Alembic migrations
-  **Caching & Sessions** with Redis
-  **Security** with bcrypt password hashing, rate limiting, and account lockout
-  **Audit Logging** for all sensitive operations
-  **State Machine** for issue status transitions with validation
-  **Containerization** with Docker and Docker Compose
-  **Kubernetes** ready with manifests and HPA
-  **CI/CD Pipeline** with GitHub Actions (code quality, testing, build, deploy)
-  **API Documentation** at `/docs` (Swagger UI) and `/redoc`

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Local Development

1. **Clone the repository**
```bash
git clone <repository-url>
cd bug-reporting-api
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Generate RSA keys for JWT**
```bash
mkdir -p keys
openssl genrsa -out keys/private_key.pem 2048
openssl rsa -in keys/private_key.pem -pubout -out keys/public_key.pem
```

5. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

6. **Run database migrations**
```bash
alembic upgrade head
```

7. **Seed the database (optional)**
```bash
python seed_data.py
```

8. **Run the application**
```bash
uvicorn src.app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Docker Deployment

1. **Build and run with Docker Compose**
```bash
cd docker
docker-compose up -d
```

2. **Access the API**
- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

3. **Run migrations and seed data**
```bash
docker-compose exec api alembic upgrade head
docker-compose exec api python seed_data.py
```

### Kubernetes Deployment

1. **Create namespace**
```bash
kubectl create namespace bug-reporting
```

2. **Apply configurations**
```bash
kubectl apply -f k8s/configmap.yaml -n bug-reporting
kubectl apply -f k8s/secrets.yaml -n bug-reporting
kubectl apply -f k8s/deployment.yaml -n bug-reporting
kubectl apply -f k8s/service.yaml -n bug-reporting
kubectl apply -f k8s/ingress.yaml -n bug-reporting
kubectl apply -f k8s/hpa.yaml -n bug-reporting
```

3. **Verify deployment**
```bash
kubectl get pods -n bug-reporting
kubectl get svc -n bug-reporting
```

## API Documentation

### Authentication

All endpoints except `/health`, `/docs`, and `/redoc` require authentication.

**Register a new user:**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass@123",
    "role": "developer"
  }'
```

**Login:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass@123"
  }'
```

**Use the access token:**
```bash
curl -H "Authorization: Bearer <access_token>" \
  http://localhost:8000/api/projects
```

### Test Users (after running seed_data.py)

| Email | Password | Role |
|-------|----------|------|
| admin@example.com | Admin@123 | Admin |
| manager1@example.com | Manager@123 | Manager |
| dev1@example.com | Dev@123 | Developer |
| dev2@example.com | Dev@123 | Developer |
| dev3@example.com | Dev@123 | Developer |

### Endpoints

- **Authentication:** `/api/auth/*`
  - `POST /api/auth/register` - Register new user
  - `POST /api/auth/login` - Login
  - `POST /api/auth/refresh` - Refresh access token
  - `POST /api/auth/logout` - Logout
  - `POST /api/auth/logout-all` - Logout all devices
  - `GET /api/auth/me` - Get current user

- **Projects:** `/api/projects/*`
  - `GET /api/projects` - List projects (paginated, searchable)
  - `POST /api/projects` - Create project (manager/admin only)
  - `GET /api/projects/{id}` - Get project details
  - `PATCH /api/projects/{id}` - Update project
  - `DELETE /api/projects/{id}` - Archive project

- **Issues:** `/api/projects/{id}/issues/*` and `/api/issues/*`
  - `GET /api/projects/{id}/issues` - List issues for project
  - `POST /api/projects/{id}/issues` - Create issue
  - `GET /api/issues/{id}` - Get issue details
  - `PATCH /api/issues/{id}` - Update issue

- **Comments:** `/api/issues/{id}/comments/*` and `/api/comments/*`
  - `GET /api/issues/{id}/comments` - List comments for issue
  - `POST /api/issues/{id}/comments` - Add comment
  - `PATCH /api/comments/{id}` - Update comment

## Architecture

### Technology Stack

- **Framework:** FastAPI 0.104.1
- **Database:** PostgreSQL 15 with async SQLAlchemy
- **Cache:** Redis 7
- **Authentication:** RS256 JWT tokens
- **Password Hashing:** bcrypt
- **Migrations:** Alembic
- **Containerization:** Docker & Docker Compose
- **Orchestration:** Kubernetes
- **Reverse Proxy:** Nginx

### Security Features

- ✅ RS256 asymmetric JWT tokens
- ✅ Password complexity validation
- ✅ Account lockout after 5 failed login attempts
- ✅ Rate limiting (100 req/min global, 5 req/min for login)
- ✅ CORS whitelist configuration
- ✅ Security headers (X-Frame-Options, X-Content-Type-Options, etc.)
- ✅ SQL injection prevention (parameterized queries)
- ✅ XSS prevention (HTML sanitization)
- ✅ Audit logging for all sensitive operations

### Permission Matrix

| Action | Developer | Manager | Admin |
|--------|-----------|---------|-------|
| View projects | ✅ | ✅ | ✅ |
| Create project | ❌ | ✅ | ✅ |
| Edit/Archive project | Owner only | ✅ | ✅ |
| Create issue | ✅ | ✅ | ✅ |
| Edit issue | Reporter/Assignee | ✅ | ✅ |
| Add comment | ✅ | ✅ | ✅ |
| Edit comment | Author only | Author only | ✅ |

## Environment Variables

See `.env.example` for all available configuration options.

**Required:**
- `SECRET_KEY` - Secret key for encryption
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string

**Optional:**
- `ENVIRONMENT` - Environment (development/production)
- `LOG_LEVEL` - Logging level (DEBUG/INFO/WARNING/ERROR)
- `CORS_ORIGINS` - Comma-separated list of allowed origins
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` - Access token expiry (default: 15)
- `JWT_REFRESH_TOKEN_EXPIRE_DAYS` - Refresh token expiry (default: 7)


## CI/CD Pipeline

The project includes a comprehensive GitHub Actions CI/CD pipeline with four stages:

### Pipeline Stages

1. **Code Quality** (`ci-code-quality.yml`)
   - Linting with Ruff
   - Code formatting with Black
   - Type checking with MyPy
   - Security scanning with Bandit, pip-audit, and Safety

2. **Testing** (`ci-testing.yml`)
   - Unit and integration tests with pytest
   - Code coverage reporting (≥70% required)
   - PostgreSQL and Redis service containers
   - Coverage reports uploaded as artifacts

3. **Build & Scan** (`ci-build.yml`)
   - Multi-stage Docker image build
   - Trivy vulnerability scanning
   - Image push to GitHub Container Registry
   - Security reports uploaded to GitHub Security tab

4. **Deploy** (`ci-deploy.yml`)
   - Kubernetes deployment to staging/production
   - Automated rollout with health checks
   - Smoke tests post-deployment
   - Automatic rollback on failure

### Workflow Triggers

- **Push to main/develop**: Runs all stages
- **Pull Requests**: Runs code quality, testing, and build (without push)
- **Manual Dispatch**: Deploy workflow can be triggered manually
- **Tag Push**: Triggers versioned releases

### Required Secrets

Configure these secrets in your GitHub repository settings:

- `GITHUB_TOKEN` - Automatically provided by GitHub
- `KUBE_CONFIG` - Base64-encoded Kubernetes config (for deployment)
- `DATABASE_URL` - Production database connection string
- `REDIS_URL` - Production Redis connection string
- `SECRET_KEY` - Application secret key
- `SLACK_WEBHOOK` - (Optional) Slack webhook for notifications
- `CODECOV_TOKEN` - (Optional) Codecov token for coverage reporting

### Running Workflows Locally

You can test workflows locally using [act](https://github.com/nektos/act):

```bash
# Install act
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Test code quality workflow
act -W .github/workflows/ci-code-quality.yml

# Test with specific event
act pull_request -W .github/workflows/ci-pr.yml
```

### Automated Dependency Updates

Dependabot is configured to automatically create PRs for:
- Python package updates (weekly)
- GitHub Actions updates (weekly)
- Docker base image updates (weekly)


## Project Structure

```
bug-reporting-api/
├── src/
│   ├── app/           # Application configuration
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   ├── routers/       # API endpoints
│   ├── services/      # Business logic
│   ├── middleware/    # Custom middleware
│   ├── utils/         # Utility functions
│   └── database/      # Database configuration
├── tests/             # Test suite
├── docker/            # Docker configuration
├── k8s/               # Kubernetes manifests
├── .github/workflows/ # CI/CD pipelines
└── seed_data.py       # Database seeding script
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please open an issue on GitHub.
