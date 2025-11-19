# Docker Setup Guide

This guide explains how to run the Social Media Post Generation Agent system using Docker and Docker Compose. The Docker setup includes PostgreSQL, Langfuse (for LLM observability), and the FastAPI application.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Services](#services)
- [Common Operations](#common-operations)
- [Troubleshooting](#troubleshooting)
- [Production Deployment](#production-deployment)

## Prerequisites

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher (or `docker compose` plugin)
- **OpenRouter API Key**: Required for LLM calls ([Get it here](https://openrouter.ai/keys))

### Verify Installation

```bash
docker --version
docker compose version
```

## Quick Start

### 1. Set Up Environment Variables

Copy the Docker-specific environment file:

```bash
cp .env.docker .env
```

Edit `.env` and add your OpenRouter API key:

```bash
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
```

### 2. Start All Services

```bash
docker compose up -d
```

This will start:
- PostgreSQL (main database) on port 5432
- Langfuse PostgreSQL (observability database) on port 5433
- Langfuse UI on port 3000
- FastAPI application on port 8000

### 3. Check Service Status

```bash
docker compose ps
```

All services should show as "healthy" or "running".

### 4. View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f app
docker compose logs -f langfuse
docker compose logs -f postgres
```

### 5. Access the Application

- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Langfuse UI**: http://localhost:3000

### 6. Set Up Langfuse (Optional)

1. Open http://localhost:3000
2. Create an account (first time only)
3. Create a new project
4. Copy the API keys (Public Key and Secret Key)
5. Update `.env` with the Langfuse keys:
   ```bash
   LANGFUSE_PUBLIC_KEY=pk-lf-...
   LANGFUSE_SECRET_KEY=sk-lf-...
   ```
6. Restart the app:
   ```bash
   docker compose restart app
   ```

## Architecture

### Services Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                        │
│                                                          │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────┐ │
│  │   FastAPI    │   │   Langfuse   │   │ PostgreSQL │ │
│  │     App      │───│      UI      │───│  (Main DB) │ │
│  │  Port: 8000  │   │  Port: 3000  │   │ Port: 5432 │ │
│  └──────────────┘   └──────────────┘   └────────────┘ │
│         │                   │                           │
│         │            ┌──────────────┐                   │
│         └────────────│  PostgreSQL  │                   │
│                      │ (Langfuse DB)│                   │
│                      │  Port: 5433  │                   │
│                      └──────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

### Volume Mounts

- `postgres_data`: Persists application database
- `langfuse_postgres_data`: Persists Langfuse database
- `./storage/images`: Persists generated images
- `./src`: Source code (hot reload in development)

## Configuration

### Environment Variables

The `.env` file configures all services. Key variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENROUTER_API_KEY` | OpenRouter API key for LLM calls | Yes |
| `POSTGRES_USER` | PostgreSQL username | No (default: admin) |
| `POSTGRES_PASSWORD` | PostgreSQL password | No (default: secret) |
| `POSTGRES_DB` | PostgreSQL database name | No (default: social_media_posts) |
| `LANGFUSE_PUBLIC_KEY` | Langfuse public key | No (optional) |
| `LANGFUSE_SECRET_KEY` | Langfuse secret key | No (optional) |
| `LANGFUSE_HOST` | Langfuse host URL | No (default: http://langfuse:3000) |

See `.env.docker` for all available configuration options.

### Using Langfuse Cloud

If you prefer to use Langfuse Cloud instead of self-hosted:

1. Sign up at https://cloud.langfuse.com
2. Create a project and get API keys
3. Update `.env`:
   ```bash
   LANGFUSE_PUBLIC_KEY=pk-lf-your-cloud-key
   LANGFUSE_SECRET_KEY=sk-lf-your-cloud-secret
   LANGFUSE_HOST=https://cloud.langfuse.com
   ```
4. Comment out the `langfuse` and `langfuse-postgres` services in `docker-compose.yml`
5. Restart: `docker compose up -d`

## Services

### PostgreSQL (Main Database)

- **Port**: 5432
- **Container**: `social-media-postgres`
- **Credentials**: admin/secret (configurable via `.env`)

Connect from host:
```bash
psql -h localhost -p 5432 -U admin -d social_media_posts
```

### Langfuse (Observability)

- **Port**: 3000
- **Container**: `langfuse`
- **Default credentials**: Set on first login

Features:
- LLM call tracing
- Token usage tracking
- Cost monitoring
- Performance analytics

### FastAPI Application

- **Port**: 8000
- **Container**: `social-media-app`
- **Health check**: http://localhost:8000/health

## Common Operations

### Starting Services

```bash
# Start all services in background
docker compose up -d

# Start and view logs
docker compose up

# Start specific service
docker compose up -d app
```

### Stopping Services

```bash
# Stop all services (keeps data)
docker compose down

# Stop and remove volumes (deletes data!)
docker compose down -v
```

### Database Migrations

```bash
# Run migrations
docker compose exec app alembic upgrade head

# Create new migration
docker compose exec app alembic revision --autogenerate -m "description"

# Rollback last migration
docker compose exec app alembic downgrade -1
```

### Running Tests

```bash
# Run all tests
docker compose exec app pytest

# Run specific test file
docker compose exec app pytest tests/db/test_repositories.py -v

# Run with coverage
docker compose exec app pytest --cov=src --cov-report=html
```

### Code Quality Checks

```bash
# Format code
docker compose exec app black src/ tests/

# Lint code
docker compose exec app ruff check src/ tests/

# Type checking
docker compose exec app mypy src/
```

### Rebuilding Services

```bash
# Rebuild after code changes
docker compose build app

# Rebuild and restart
docker compose up -d --build app

# Force rebuild (no cache)
docker compose build --no-cache app
```

### Shell Access

```bash
# Python shell
docker compose exec app python

# Bash shell
docker compose exec app bash

# PostgreSQL shell
docker compose exec postgres psql -U admin -d social_media_posts
```

### Viewing Logs

```bash
# All services
docker compose logs -f

# Last 100 lines
docker compose logs --tail=100

# Specific service
docker compose logs -f app

# With timestamps
docker compose logs -f -t app
```

## Troubleshooting

### Services Won't Start

**Check if ports are already in use:**
```bash
# Linux/Mac
lsof -i :8000
lsof -i :5432
lsof -i :3000

# Windows
netstat -ano | findstr :8000
```

**Solution**: Stop conflicting services or change ports in `docker-compose.yml`.

### Database Connection Errors

**Error**: `FATAL: password authentication failed`

**Solution**:
1. Stop services: `docker compose down`
2. Remove volumes: `docker volume rm social-media-post-gen_postgres_data`
3. Start fresh: `docker compose up -d`

### Migration Errors

**Error**: `Target database is not up to date`

**Solution**:
```bash
# Check migration status
docker compose exec app alembic current

# Run pending migrations
docker compose exec app alembic upgrade head
```

### App Container Keeps Restarting

**Check logs**:
```bash
docker compose logs app
```

**Common issues**:
- Missing `OPENROUTER_API_KEY` in `.env`
- Database not ready (wait a few seconds)
- Port 8000 already in use

### Langfuse Not Accessible

**Check if container is running**:
```bash
docker compose ps langfuse
```

**Check logs**:
```bash
docker compose logs langfuse
```

**Solution**: Ensure Langfuse PostgreSQL is healthy:
```bash
docker compose ps langfuse-postgres
```

### Out of Disk Space

**Check Docker disk usage**:
```bash
docker system df
```

**Clean up**:
```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove everything unused
docker system prune -a --volumes
```

## Production Deployment

### Security Considerations

1. **Change default passwords**:
   ```bash
   # Generate secure passwords
   openssl rand -base64 32
   ```

2. **Update `.env`**:
   - Set strong `POSTGRES_PASSWORD`
   - Set secure `SECRET_KEY`
   - Set secure `LANGFUSE_NEXTAUTH_SECRET` and `LANGFUSE_SALT`
   - Change `ENVIRONMENT=production`

3. **Disable hot reload**:
   - Remove `--reload` from the app command in `docker-compose.yml`
   - Remove source code volume mount

4. **Use secrets management**:
   - Use Docker secrets or environment-specific secret managers
   - Never commit `.env` to version control

### Performance Optimization

1. **Database**:
   - Increase PostgreSQL `shared_buffers` and `work_mem`
   - Enable connection pooling (use pgBouncer)

2. **Application**:
   - Use gunicorn with multiple workers
   - Enable caching (Redis)
   - Configure logging levels (WARNING or ERROR)

3. **Resources**:
   - Add resource limits to `docker-compose.yml`:
     ```yaml
     services:
       app:
         deploy:
           resources:
             limits:
               cpus: '2'
               memory: 4G
             reservations:
               cpus: '1'
               memory: 2G
     ```

### Monitoring

1. **Health checks**: All services include health checks
2. **Logs**: Use centralized logging (ELK, Grafana Loki)
3. **Metrics**: Use Langfuse for LLM metrics
4. **Alerts**: Set up alerts for service failures

### Backup

**Database backup**:
```bash
# Backup
docker compose exec postgres pg_dump -U admin social_media_posts > backup.sql

# Restore
docker compose exec -T postgres psql -U admin social_media_posts < backup.sql
```

**Volume backup**:
```bash
# Backup volumes
docker run --rm -v social-media-post-gen_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [Langfuse Documentation](https://langfuse.com/docs)
- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## Support

For issues related to:
- **Docker setup**: See troubleshooting section above
- **Application**: Check the main README.md
- **LangGraph**: See LangGraph documentation
- **Langfuse**: See Langfuse documentation

## License

MIT
