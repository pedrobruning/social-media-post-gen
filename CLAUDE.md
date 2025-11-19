# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a learning-focused agentic AI system that generates optimized social media content for LinkedIn, Instagram, and WordPress using LangGraph. The system implements human-in-the-loop review workflows, multi-modal content generation (text + images), and comprehensive observability.

**Status**: Early development (~20% complete). Infrastructure and skeleton code complete; core implementation in progress.

## Development Commands

### Dependencies
```bash
# Install all dependencies (uses UV package manager)
uv sync

# Install dev dependencies only
uv sync --group dev
```

### Running the Application
```bash
# Start API server (when implemented)
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Database
```bash
# Run migrations
uv run alembic upgrade head

# Create new migration
uv run alembic revision --autogenerate -m "description"

# Rollback last migration
uv run alembic downgrade -1
```

### Testing
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/db/test_repositories.py -v

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run single test function
uv run pytest tests/db/test_repositories.py::test_create_post -v
```

### Code Quality
```bash
# Format code
uv run black src/ tests/

# Lint code
uv run ruff check src/ tests/

# Type checking
uv run mypy src/
```

### Docker

The project includes a complete Docker setup with PostgreSQL, Langfuse (LLM observability), and the FastAPI application.

**Quick Start:**
```bash
# 1. Set up environment (first time only)
cp .env.docker .env
# Edit .env and add your OPENROUTER_API_KEY

# 2. Start all services (PostgreSQL, Langfuse, App)
docker compose up -d

# 3. Check service health
docker compose ps

# 4. View logs
docker compose logs -f app

# 5. Access services
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Langfuse UI: http://localhost:3000
```

**Common Operations:**
```bash
# Run migrations in container
docker compose exec app alembic upgrade head

# Run tests
docker compose exec app pytest

# Format code
docker compose exec app black src/ tests/

# Stop services (keeps data)
docker compose down

# Stop and remove all data
docker compose down -v
```

**Architecture:**
- `postgres` - Main application database (port 5432)
- `langfuse-postgres` - Langfuse database (port 5433)
- `langfuse` - LLM observability UI (port 3000)
- `app` - FastAPI application (port 8000)

**For detailed Docker documentation**, see: [docs/DOCKER_SETUP.md](docs/DOCKER_SETUP.md)

## Architecture

### LangGraph Workflow

The system uses a LangGraph state machine with the following nodes:

1. **analyze_topic** → Extracts themes, target audience, visual concepts from user topic
2. **generate_image** → Creates image using DALL-E 3 (shared across all platforms)
3. **generate_linkedin** → Professional post (max 3000 chars, limited hashtags)
4. **generate_instagram** → Visual-focused caption (10-30 hashtags, image required)
5. **generate_wordpress** → Long-form article with section-based structure
6. **wait_for_approval** → Human-in-the-loop checkpoint (PostgreSQL-backed)
7. **apply_feedback** → Regenerates content based on human feedback
8. **finalize** → Persists approved content to database

The workflow supports parallel content generation for all three platforms and uses PostgreSQL checkpointing for state persistence.

### Repository Pattern

The codebase uses the Repository pattern for clean separation between business logic and data access:

- **PostRepository** - CRUD for posts, status management, statistics
- **PostContentRepository** - Platform-specific content storage (stores Pydantic models as JSON)
- **ReviewRepository** - Human review tracking, approval rates, audit trail
- **EvaluationRepository** - Quality metrics, LLM-as-judge scores, trend analysis

All repositories accept a SQLAlchemy `Session` in their constructor and provide typed methods for database operations.

### Platform-Specific Content Models

Each platform has dedicated Pydantic models with validation:

**LinkedIn** (`LinkedInPost`):
- Max 3000 characters
- Professional tone
- Limited hashtags (max 5)
- Optional image at top

**Instagram** (`InstagramPost`):
- Max 2200 character caption
- Image **required**
- 10-30 hashtags
- Visual-first storytelling

**WordPress** (`WordPressPost`):
- Section-based structure (headings, paragraphs, images)
- Images can be placed anywhere via `WordPressSection` objects
- SEO metadata (description, featured_image)
- Flexible article formatting

### LLM Routing Strategy

The system uses OpenRouter with a fallback chain:
1. Primary: `anthropic/claude-3.5-sonnet`
2. Fallback 1: `openai/gpt-4o`
3. Fallback 2: `openai/gpt-3.5-turbo`

Each model attempt includes exponential backoff retry logic. All LLM calls are traced via Langfuse.

### State Management

Agent state is managed via Pydantic models (`PostGenerationState`) which provide:
- Automatic validation
- Type safety throughout workflow
- Clean serialization for checkpointing
- Self-documenting structure

## Key Files and Locations

### Agent System
- `src/agent/state.py` - Pydantic state models for LangGraph
- `src/agent/schemas.py` - Platform content models (LinkedIn, Instagram, WordPress)
- `src/agent/nodes.py` - Node function implementations
- `src/agent/graph.py` - Workflow construction and routing logic

### Database
- `src/db/models.py` - SQLAlchemy ORM models
- `src/db/database.py` - DB connection and session management
- `src/db/repositories.py` - Repository pattern implementations
- `alembic/versions/` - Database migration files

### LLM Integration
- `src/llm/router.py` - OpenRouter client with fallback chain
- `src/llm/observability.py` - Langfuse tracing integration

### API
- `src/api/main.py` - FastAPI app initialization
- `src/api/routes.py` - API endpoints (generate, approve, reject, evaluate)
- `src/api/dependencies.py` - Dependency injection

### Configuration
- `src/config/settings.py` - Pydantic Settings for environment variables
- `.env.example` - Environment variable template

## Development Guidelines

### Test-Driven Development (TDD)

This project strictly follows TDD:
1. **Red**: Write failing test first
2. **Green**: Implement minimal code to pass
3. **Refactor**: Improve while keeping tests green

Always write tests before implementation. Test files mirror source structure (`tests/db/test_repositories.py` for `src/db/repositories.py`).

### Adding New Platforms

To add a new platform (e.g., Twitter):

1. Create Pydantic model in `src/agent/schemas.py`:
```python
class TwitterPost(BaseModel):
    text: str = Field(..., max_length=280)
    thread: Optional[List[str]] = None
    hashtags: List[str] = Field(max_items=2)
```

2. Add generation node in `src/agent/nodes.py`:
```python
async def generate_twitter(state: PostGenerationState) -> PostGenerationState:
    # Implementation
```

3. Wire into graph in `src/agent/graph.py`
4. Add repository method in `src/db/repositories.py`
5. Update API routes in `src/api/routes.py`

### Code Style

- **Line length**: 100 characters (Black + Ruff)
- **Python version**: 3.12+
- **Type hints**: Use throughout (checked via mypy)
- **Docstrings**: Google style for all public functions/classes
- **Imports**: Sorted via isort (integrated in Ruff)

### Environment Variables

Required for local development:
```bash
OPENROUTER_API_KEY=sk-or-...  # Required for LLM calls
DATABASE_URL=postgresql://...  # PostgreSQL connection
LANGFUSE_PUBLIC_KEY=pk-lf-...  # Optional, for observability
LANGFUSE_SECRET_KEY=sk-lf-...  # Optional
```

Copy `.env.example` to `.env` and fill in values.

## Common Patterns

### Creating a Repository Method

```python
def get_by_custom_field(self, value: str) -> Optional[Post]:
    """Get post by custom field.

    Args:
        value: Field value to search

    Returns:
        Post instance or None
    """
    return self.db.query(Post).filter(Post.custom_field == value).first()
```

### Adding an Agent Node

```python
async def my_node(state: PostGenerationState) -> PostGenerationState:
    """Node docstring.

    Args:
        state: Current agent state

    Returns:
        Updated state
    """
    # Implementation
    return state
```

### Storing Platform Content

Platform-specific content is stored as JSON in the `post_contents` table:

```python
content_repo = PostContentRepository(db)
content_repo.create(
    post_id=1,
    platform="linkedin",
    content=linkedin_post.model_dump_json(),
    metadata={"hashtags": ["AI", "ML"]}
)
```

## Project Structure Notes

- **Skeleton complete**: All modules have function/class signatures with docstrings
- **Implementation status**: See TODO.md for detailed phase tracking
- **Tests**: Currently minimal; TDD starts in Phase 3 (database implementation)
- **Docker**: Complete setup with PostgreSQL, Langfuse, and app (see docs/DOCKER_SETUP.md)

## Important Considerations

### Shared Image Strategy
- One image generated per post (after topic analysis)
- Reused across all platforms for consistency and cost efficiency
- WordPress can place it anywhere via section-based structure
- Stored locally in `storage/images/` directory

### Human-in-the-Loop Flow
- Agent pauses at `wait_for_approval` node
- State persisted via PostgreSQL checkpointer
- Resume workflow via API (`/posts/{id}/approve` or `/posts/{id}/reject`)
- Rejected posts trigger `apply_feedback` → regeneration

### Evaluation System
- **Quality metrics**: Readability (textstat), grammar, tone
- **Platform metrics**: Character counts, hashtag appropriateness, SEO
- **LLM-as-judge**: Relevance, engagement, clarity (scored 1-10)
- Triggered after finalization via `/evaluate/{post_id}`

## External Resources

- LangGraph docs: https://python.langchain.com/docs/langgraph
- OpenRouter API: https://openrouter.ai/docs
- Langfuse: https://langfuse.com/docs
- FastAPI: https://fastapi.tiangolo.com/
