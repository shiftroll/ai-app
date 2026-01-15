# Deployment Guide - Crafta Revenue Control Room

## Architecture Overview

```
                    ┌─────────────────────────────────────────┐
                    │            Load Balancer                 │
                    │         (CloudFlare / AWS ALB)           │
                    └─────────────────────────────────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
              ▼                       ▼                       ▼
    ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
    │   Frontend      │   │    Backend      │   │   Agent Worker  │
    │   (Next.js)     │   │   (FastAPI)     │   │   (Python)      │
    │   Port: 3000    │   │   Port: 8000    │   │   Celery/Redis  │
    └─────────────────┘   └─────────────────┘   └─────────────────┘
              │                       │                       │
              └───────────────────────┼───────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
                    ▼                                   ▼
          ┌─────────────────┐               ┌─────────────────┐
          │   PostgreSQL    │               │      Redis      │
          │   (Supabase)    │               │   (Optional)    │
          └─────────────────┘               └─────────────────┘
```

---

## Quick Start with Docker

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

### 1. Clone and Configure

```bash
git clone <repository>
cd crafta-control-room

# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# Edit .env files with your configuration
```

### 2. Build and Run

```bash
# Build all services
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 3. Access the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://crafta:crafta@db:5432/crafta
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.worker worker -l info
    environment:
      - DATABASE_URL=postgresql://crafta:crafta@db:5432/crafta
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=crafta
      - POSTGRES_PASSWORD=crafta
      - POSTGRES_DB=crafta
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

---

## Cloud Deployment

### AWS Deployment

#### Option 1: ECS with Fargate

1. **Create ECR repositories**
```bash
aws ecr create-repository --repository-name crafta-frontend
aws ecr create-repository --repository-name crafta-backend
```

2. **Build and push images**
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -t crafta-frontend ./frontend
docker tag crafta-frontend:latest <account>.dkr.ecr.us-east-1.amazonaws.com/crafta-frontend:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/crafta-frontend:latest

# Repeat for backend
```

3. **Create ECS cluster and services**
- Use AWS Console or Terraform
- Configure ALB for routing
- Set up RDS PostgreSQL
- Configure ElastiCache Redis

#### Option 2: Elastic Beanstalk

1. Initialize EB application
```bash
eb init crafta-control-room --platform docker
```

2. Create environment
```bash
eb create production --database.engine postgres
```

### GCP Deployment

#### Cloud Run

1. **Enable services**
```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudsql.googleapis.com
```

2. **Deploy backend**
```bash
gcloud run deploy crafta-backend \
  --source ./backend \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=$DATABASE_URL
```

3. **Deploy frontend**
```bash
gcloud run deploy crafta-frontend \
  --source ./frontend \
  --region us-central1 \
  --allow-unauthenticated
```

### Supabase for Database

1. Create Supabase project at https://supabase.com
2. Get connection string from Settings > Database
3. Update `DATABASE_URL` in backend `.env`

---

## Environment Variables

### Backend (.env)

```bash
# Required
DATABASE_URL=postgresql://user:pass@host:5432/crafta
SECRET_KEY=<generate-secure-key>
ENCRYPTION_KEY=<32-byte-key>

# Optional - LLM
OPENAI_API_KEY=sk-...

# Optional - ERP
QUICKBOOKS_CLIENT_ID=...
QUICKBOOKS_CLIENT_SECRET=...
XERO_CLIENT_ID=...
XERO_CLIENT_SECRET=...

# Optional - Redis
REDIS_URL=redis://localhost:6379/0
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_URL=https://api.crafta.ai
```

---

## CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run tests
        run: |
          cd backend
          pytest tests/ -v

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to production
        run: |
          # Add deployment commands here
          echo "Deploying..."
```

---

## Health Checks

### Endpoints

- `GET /health` - Basic health check
- `GET /health/ready` - Readiness check (all dependencies)
- `GET /health/live` - Liveness check

### Monitoring

Recommended monitoring setup:

1. **Application**: Sentry for error tracking
2. **Infrastructure**: CloudWatch / Datadog
3. **Uptime**: Pingdom / UptimeRobot
4. **Logs**: CloudWatch Logs / Papertrail

---

## Scaling Considerations

### Horizontal Scaling

- Frontend: Stateless, scale behind load balancer
- Backend: Stateless API, scale based on CPU/requests
- Workers: Scale based on queue depth

### Database Scaling

- Read replicas for read-heavy workloads
- Connection pooling (PgBouncer)
- Consider partitioning for large audit logs

### File Storage

- Use S3/GCS for uploaded files in production
- Configure CDN for static assets

---

## Security Checklist

- [ ] TLS certificates configured
- [ ] Secrets stored in secrets manager
- [ ] Database credentials rotated
- [ ] Firewall rules restricted
- [ ] WAF enabled
- [ ] Backup encryption enabled
- [ ] Audit logging to external system
