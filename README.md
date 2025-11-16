# Social Media Post Generation Agent System

> An intelligent multi-platform content generation system built with LangGraph, featuring human-in-the-loop review, image generation, and comprehensive observability.

## 🎯 Project Overview

This project is a learning-focused implementation of an agentic AI system that generates optimized social media content for LinkedIn, Instagram, and WordPress. It demonstrates modern AI engineering practices including:

- **Agentic Workflows**: LangGraph state machines with conditional routing
- **Human-in-the-Loop**: Checkpointing and approval workflows
- **Multi-Modal Generation**: Text and image content creation
- **LLM Resilience**: Intelligent routing with fallback chains via OpenRouter
- **Observability**: Full tracing with Langfuse
- **Quality Assurance**: Automated evaluation pipeline with LLM-as-judge
- **Test-Driven Development**: Comprehensive test coverage following TDD principles

## 🏗️ Architecture

### System Flow

```mermaid
graph TD
    A[API: POST /posts/generate] --> B[Analyze Topic]
    B --> C[Generate Image DALL-E 3]
    C --> D1[Generate LinkedIn Post]
    C --> D2[Generate Instagram Post]
    C --> D3[Generate WordPress Article]
    D1 --> E[Wait for Approval]
    D2 --> E
    D3 --> E
    E -->|Approved| F[Finalize & Store]
    E -->|Rejected| G[Apply Feedback]
    G --> D1
    F --> H[Evaluation Pipeline]
    H --> I[Store Metrics]
```

### LangGraph Agent Nodes

1. **analyze_topic**: Extracts key themes, target audience, and visual concepts
2. **generate_image**: Creates a relevant image using DALL-E 3 via OpenRouter
3. **generate_linkedin**: Professional post (max 3000 chars) with image reference
4. **generate_instagram**: Visual-focused caption with hashtags
5. **generate_wordpress**: Long-form article with embedded image
6. **wait_for_approval**: Human-in-the-loop checkpoint (PostgreSQL-backed)
7. **apply_feedback**: Regenerates content based on human feedback
8. **finalize**: Persists approved content to database

### Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Agent Framework | LangGraph | State machine orchestration |
| LLM Provider | OpenRouter | Multi-model routing with fallback |
| Image Generation | DALL-E 3 | Visual content creation |
| API Framework | FastAPI | RESTful API with async support |
| Database | PostgreSQL 16 | State persistence & checkpointing |
| Observability | Langfuse | LLM call tracing & monitoring |
| Testing | Pytest | TDD implementation |
| Containerization | Docker + Compose | Deployment & isolation |

### LLM Routing Strategy

```
Primary: anthropic/claude-3.5-sonnet
   ↓ (on failure)
Fallback 1: openai/gpt-4o
   ↓ (on failure)
Fallback 2: openai/gpt-3.5-turbo
```

Each model attempt includes exponential backoff retry logic.

## 🏛️ Architecture Highlights

### Repository Pattern
We use the Repository pattern for clean data access:
- `PostRepository` - Manages post records
- `PostContentRepository` - Manages platform-specific content
- `ReviewRepository` - Tracks human reviews
- `EvaluationRepository` - Stores quality metrics

### Platform-Specific Schemas
Type-safe Pydantic models for each platform:
- `LinkedInPost` - Professional posts (max 3000 chars, limited hashtags)
- `InstagramPost` - Visual-first (required image, 10-30 hashtags)
- `WordPressPost` - Section-based structure with flexible image placement

### State Management
Pydantic-based state model for the LangGraph workflow:
- Automatic validation
- Type safety throughout the workflow
- Easy serialization for checkpointing

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed design decisions.

---

## 📁 Project Structure

```
social-media-post-gen/
├── src/
│   ├── agent/              # LangGraph agent implementation
│   │   ├── __init__.py
│   │   ├── state.py        # State schema definition
│   │   ├── nodes.py        # Agent node functions
│   │   └── graph.py        # Graph construction & routing
│   ├── api/                # FastAPI application
│   │   ├── __init__.py
│   │   ├── main.py         # FastAPI app initialization
│   │   ├── routes.py       # API endpoints
│   │   └── dependencies.py # Dependency injection
│   ├── db/                 # Database layer
│   │   ├── __init__.py
│   │   ├── models.py       # SQLAlchemy models
│   │   ├── database.py     # DB connection & session
│   │   └── crud.py         # Database operations
│   ├── llm/                # LLM integration
│   │   ├── __init__.py
│   │   ├── router.py       # OpenRouter with fallback
│   │   └── observability.py # Langfuse integration
│   ├── images/             # Image generation
│   │   ├── __init__.py
│   │   ├── generator.py    # DALL-E integration
│   │   └── storage.py      # Image storage logic
│   ├── evaluation/         # Quality evaluation
│   │   ├── __init__.py
│   │   ├── evaluators.py   # Metric calculators
│   │   └── runner.py       # Evaluation orchestration
│   └── config/             # Configuration
│       ├── __init__.py
│       └── settings.py     # Pydantic settings
├── tests/                  # Test suite (mirrors src/)
│   ├── conftest.py         # Pytest fixtures
│   ├── test_config.py
│   ├── agent/
│   ├── api/
│   ├── db/
│   ├── llm/
│   ├── images/
│   └── evaluation/
├── docs/                   # Documentation
│   ├── ARCHITECTURE.md     # Detailed design docs
│   ├── EVALUATION.md       # Eval metrics guide
│   ├── LEARNINGS.md        # Development insights
│   └── TDD_NOTES.md        # TDD patterns used
├── docker/                 # Docker configuration
│   └── postgres/           # PostgreSQL init scripts
├── alembic/                # Database migrations
│   └── versions/
├── storage/                # Local file storage
│   └── images/             # Generated images
├── .env.example            # Environment template
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml          # Dependencies (uv)
└── README.md               # This file
```

## 📊 Project Status

### Current Phase: Database Implementation (Phase 3)

**Completed**:
- ✅ Project infrastructure and setup
- ✅ All dependencies installed via UV
- ✅ Complete module skeleton (2,644 lines of code)
- ✅ Repository pattern implementation
- ✅ Pydantic schemas for all platforms
- ✅ Architecture documentation

**In Progress**:
- 🚧 Alembic database migrations
- 🚧 Repository unit tests

**Next Steps**:
- 📋 LLM integration (OpenRouter + Langfuse)
- 📋 Image generation (DALL-E 3)
- 📋 Agent node implementation
- 📋 API endpoint implementation

See [TODO.md](TODO.md) for detailed progress tracking.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- UV package manager
- Docker & Docker Compose (for deployment)
- OpenRouter API key ([get one here](https://openrouter.ai/)) - Required for LLM calls
- (Optional) Langfuse account for observability

### Development Setup

**Note**: The system is currently in development. Basic functionality is not yet implemented.

1. **Clone and navigate to project**:
```bash
cd /Users/pedrobruning/Projects/social-media-post-gen
```

2. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Start services with Docker**:
```bash
docker-compose up -d
```

This starts:
- PostgreSQL on port 5432
- FastAPI application on port 8000
- (Optional) Langfuse on port 3000

4. **Run database migrations**:
```bash
docker-compose exec app alembic upgrade head
```

### Development Setup (Without Docker)

1. **Install dependencies with uv**:
```bash
uv sync
```

2. **Start PostgreSQL** (using Docker or local install):
```bash
docker run -d -p 5432:5432 \
  -e POSTGRES_DB=social_media_posts \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=secret \
  postgres:16
```

3. **Run migrations**:
```bash
uv run alembic upgrade head
```

4. **Start the API**:
```bash
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

## 📖 API Usage

### Generate Posts

```bash
curl -X POST http://localhost:8000/api/posts/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "The future of AI in software development"
  }'

# Response:
# {
#   "post_id": 1,
#   "status": "pending_review",
#   "message": "Content generation started"
# }
```

### Get Generated Content

```bash
curl http://localhost:8000/api/posts/1

# Response:
# {
#   "post_id": 1,
#   "topic": "The future of AI in software development",
#   "status": "pending_review",
#   "image_url": "/api/posts/1/image",
#   "linkedin_post": {...},
#   "instagram_post": {...},
#   "wordpress_post": {...},
#   "created_at": "2025-11-16T..."
# }
```

### Approve Content

```bash
curl -X POST http://localhost:8000/api/posts/1/approve
```

### Reject with Feedback

```bash
curl -X POST http://localhost:8000/api/posts/1/reject \
  -H "Content-Type: application/json" \
  -d '{
    "feedback": "Make the LinkedIn post more technical and add code examples"
  }'
```

### Edit Specific Platform

```bash
curl -X POST http://localhost:8000/api/posts/1/edit \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "linkedin",
    "content": "Updated post content..."
  }'
```

### Trigger Evaluation

```bash
curl -X POST http://localhost:8000/api/evaluate/1
```

## 🧪 Testing

### Run All Tests

```bash
uv run pytest
```

### Run with Coverage

```bash
uv run pytest --cov=src --cov-report=html
```

### Run Specific Test Module

```bash
uv run pytest tests/agent/test_nodes.py -v
```

### TDD Workflow

This project follows strict Test-Driven Development:

1. **Red**: Write a failing test that defines desired behavior
2. **Green**: Write minimal code to make the test pass
3. **Refactor**: Improve code quality while keeping tests green

Example from `tests/llm/test_router.py`:

```python
def test_primary_model_success(mock_openrouter):
    """Test successful call to primary model"""
    router = LLMRouter()
    response = router.generate("Test prompt")
    
    assert response.content is not None
    assert response.model == "anthropic/claude-3.5-sonnet"
    assert mock_openrouter.call_count == 1

def test_fallback_on_primary_failure(mock_openrouter):
    """Test fallback to secondary model on primary failure"""
    mock_openrouter.side_effect = [Exception("API Error"), "Success"]
    
    router = LLMRouter()
    response = router.generate("Test prompt")
    
    assert response.model == "openai/gpt-4o"
    assert mock_openrouter.call_count == 2
```

## 📊 Evaluation Metrics

The system automatically evaluates generated content across multiple dimensions:

### Quality Metrics
- **Readability Score**: Flesch reading ease
- **Grammar Check**: Language tool validation
- **Tone Consistency**: Appropriate for each platform

### Platform-Specific Metrics
- **LinkedIn**: Professional tone, character count (≤3000), hashtag appropriateness
- **Instagram**: Visual focus, hashtag count (10-30), emoji usage
- **WordPress**: SEO score, structure (headers, paragraphs), readability

### LLM-as-Judge
- **Relevance** (1-10): Content matches the original topic
- **Engagement** (1-10): Likely to generate interactions
- **Clarity** (1-10): Clear and well-structured

### Human Feedback Metrics
- Approval rate per topic category
- Common rejection reasons
- Time to approval

View evaluation results:
```bash
curl http://localhost:8000/api/posts/1/evaluations
```

## 🔍 Observability with Langfuse

All LLM calls, agent executions, and key events are traced in Langfuse:

- **Traces**: Full agent execution flow
- **Spans**: Individual LLM calls with prompts/responses
- **Metrics**: Token usage, latency, costs per model
- **Tags**: post_id, platform, model_used, generation_attempt
- **Custom Events**: human_review, image_generation, feedback_applied

Access your traces at: `http://localhost:3000` (if self-hosted) or cloud.langfuse.com

## 🐳 Docker Configuration

### Services

**app**: FastAPI application with LangGraph agent
- Depends on PostgreSQL
- Exposes port 8000
- Mounts `storage/` for images

**postgres**: PostgreSQL 16 database
- Persists data with volume
- Stores posts, checkpoints, evaluations

**langfuse** (optional): Self-hosted observability
- Web UI on port 3000
- Requires separate PostgreSQL database

### Environment Variables

```bash
# OpenRouter
OPENROUTER_API_KEY=sk-or-...

# Database
DATABASE_URL=postgresql://admin:secret@postgres:5432/social_media_posts

# Langfuse (cloud or self-hosted)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## 📈 Progress Metrics

- **Total Lines of Code**: ~2,644
- **Python Modules**: 25 files
- **Repositories**: 4 classes with 23+ methods
- **Pydantic Models**: 7 content schemas
- **Completion**: ~20% (infrastructure complete, implementation in progress)

## 📚 Learning Objectives

This project serves as a comprehensive learning resource for:

### 1. Agentic AI Systems
- Building complex state machines with LangGraph
- Implementing human-in-the-loop patterns
- Managing agent state and checkpoints
- Designing conditional routing logic

### 2. Production LLM Applications
- Multi-model routing and fallback strategies
- Cost optimization through model selection
- Retry logic and error handling
- Token usage tracking

### 3. API Design
- RESTful endpoints for async operations
- Background task processing
- Webhook patterns for notifications
- Error response standardization

### 4. Observability
- Tracing LLM applications
- Debugging complex agent flows
- Cost and performance monitoring
- Custom event logging

### 5. Test-Driven Development
- Writing testable agent code
- Mocking external APIs effectively
- Integration testing strategies
- Achieving high test coverage

### 6. Software Engineering Practices
- Clean architecture and separation of concerns
- Configuration management
- Database design and migrations
- Containerization and deployment

## 📝 Development Roadmap

See [TODO.md](TODO.md) for detailed task breakdown.

### Phase 1: Infrastructure & Setup ✅ COMPLETE
- ✅ Project structure and dependencies
- ✅ Configuration management with Pydantic Settings
- ✅ Repository pattern implementation
- ✅ Platform-specific Pydantic schemas
- ✅ Complete module skeleton (~2,644 lines)

### Phase 2: Core Modules (Skeleton) ✅ COMPLETE
- ✅ Database models (SQLAlchemy)
- ✅ Repository classes (4 repositories)
- ✅ Agent state and schemas
- ✅ LLM router and observability classes
- ✅ API route signatures
- ✅ Evaluation framework

### Phase 3: Database Implementation 🚧 IN PROGRESS
- 🚧 Alembic migrations
- 📋 Repository unit tests
- 📋 Database integration tests

### Phase 4: LLM Integration 📋 NEXT
- 📋 OpenRouter client implementation
- 📋 Fallback chain with retry logic
- 📋 Langfuse tracing integration
- 📋 Cost and token tracking

### Phase 5: Image Generation 📋
- 📋 DALL-E 3 integration via OpenRouter
- 📋 Image prompt generation
- 📋 Local storage implementation

### Phase 6: Agent Implementation 📋
- 📋 Topic analysis node
- 📋 Content generation nodes (3 platforms)
- 📋 Human-in-the-loop nodes
- 📋 Graph construction and checkpointing

### Phase 7: API Implementation 📋
- 📋 Generate endpoint with background tasks
- 📋 Review endpoints (approve/reject/edit)
- 📋 Evaluation endpoints
- 📋 Image serving

### Phase 8: Evaluation Implementation 📋
- 📋 Quality evaluators (readability, grammar)
- 📋 Platform-specific evaluators
- 📋 LLM-as-judge implementation

### Phase 9: Docker & Deployment 📋
- 📋 Dockerfile (multi-stage build)
- 📋 docker-compose.yml
- 📋 Container orchestration

### Phase 10: Testing 📋
- 📋 Unit tests (TDD approach)
- 📋 Integration tests
- 📋 >80% code coverage

### Phase 11: Documentation 📋
- ✅ Architecture documentation
- 📋 Evaluation metrics guide
- 📋 Learning journal
- 📋 API examples

### Phase 12: Future Enhancements ⏸️
- ⏸️ Web UI for review
- ⏸️ Multi-language support
- ⏸️ A/B testing
- ⏸️ Actual platform publishing

## 🤝 Contributing

This is a learning project, but suggestions and improvements are welcome!

## 📄 License

MIT License - feel free to use this for learning and portfolio purposes.

## 🔗 Resources

- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [OpenRouter API Docs](https://openrouter.ai/docs)
- [Langfuse Docs](https://langfuse.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

**Built with ❤️ for learning and experimentation**

