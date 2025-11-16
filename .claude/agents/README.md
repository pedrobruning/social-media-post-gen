# Specialized Subagents for Social Media Post Generation

This directory contains specialized agent definitions for completing the Social Media Post Generation project with mastery.

## Overview

Six specialized agents have been designed to tackle different phases of the project, each with clear responsibilities, success criteria, and technical guidance.

## Agent Execution Strategy

### Phase Mapping
| Agent | Phases | Priority | Estimated Time |
|-------|--------|----------|----------------|
| database-tdd-agent | Phase 3 | IMMEDIATE | 1 week |
| llm-integration-agent | Phase 4 | HIGH | 1-2 weeks |
| langgraph-workflow-agent | Phase 6 (control) | HIGH | 2 weeks |
| content-generation-agent | Phase 6 (content) | MEDIUM | 2 weeks |
| api-integration-agent | Phases 5 + 7 | MEDIUM | 2 weeks |
| evaluation-testing-agent | Phases 8 + 10 | MEDIUM-LOW | 2 weeks |

### Execution Order

**Sequential (must complete before next):**
1. **database-tdd-agent** - Foundation layer
2. **llm-integration-agent** - Enables all content generation

**Parallel (can work simultaneously):**
3. **langgraph-workflow-agent** + **content-generation-agent**
   - Workflow agent handles graph structure and control nodes
   - Content agent handles content generation nodes
   - Minimal overlap, can coordinate on interfaces

**Sequential (after parallel work):**
4. **api-integration-agent** - Connects all components
5. **evaluation-testing-agent** - Quality assurance layer

## How to Use These Agents

### Option 1: Using Claude Code Task Tool
When working with Claude Code, you can reference these agent specifications when delegating work:

```
I need to implement the database layer with TDD.
Please follow the specifications in .claude/agents/database-tdd-agent.md
```

### Option 2: Manual Reference
Use these documents as comprehensive implementation guides when working on each phase:
- Read the agent specification for your current phase
- Follow the technical requirements and patterns
- Complete all items in the "Success Criteria" section
- Run the specified commands to verify completion

### Option 3: AI Assistant Context
Provide the relevant agent specification to any AI coding assistant:
```
Here's my task specification: [paste database-tdd-agent.md]
Please help me implement this following TDD principles.
```

## Agent Details

### 1. database-tdd-agent.md
**Purpose**: Alembic migrations + comprehensive repository testing

**Key Outputs:**
- Alembic initialized and configured
- Initial migration for all models
- Full test coverage for 4 repositories (PostRepository, PostContentRepository, ReviewRepository, EvaluationRepository)

**Prerequisites:** None (starts from current skeleton)

**Success Indicators:**
- `uv run alembic upgrade head` works
- `uv run pytest tests/db/ -v` all pass
- Repository tests demonstrate TDD patterns

---

### 2. llm-integration-agent.md
**Purpose**: OpenRouter integration with fallback chain + Langfuse observability

**Key Outputs:**
- LLMRouter with 3-model fallback chain
- Exponential backoff retry logic
- Token tracking and cost calculation
- Langfuse tracing integration

**Prerequisites:** None (can start in parallel with database agent)

**Success Indicators:**
- `uv run pytest tests/llm/ -v` all pass
- Can successfully call OpenRouter API
- Langfuse traces appear (if configured)

---

### 3. langgraph-workflow-agent.md
**Purpose**: LangGraph state machine with PostgreSQL checkpointing

**Key Outputs:**
- All workflow control nodes (wait_for_approval, apply_feedback, finalize, handle_error)
- Graph wired with conditional routing
- PostgreSQL checkpointer configured
- Human-in-the-loop checkpoint working

**Prerequisites:**
- Database layer complete (for checkpointing)
- LLM integration complete (for content nodes coordination)

**Success Indicators:**
- `uv run pytest tests/agent/test_graph.py -v` all pass
- Workflow can pause and resume
- State persists across interruptions

---

### 4. content-generation-agent.md
**Purpose**: Platform-specific content generation with optimized prompts

**Key Outputs:**
- analyze_topic node implementation
- generate_linkedin node with professional tone
- generate_instagram node with visual focus
- generate_wordpress node with section structure
- All content validates against Pydantic schemas

**Prerequisites:**
- LLM integration complete (uses LLMRouter)

**Success Indicators:**
- `uv run pytest tests/agent/test_nodes.py -v` all pass
- Generated content is high quality (manual review)
- Character limits enforced
- Platform-specific requirements met

---

### 5. api-integration-agent.md
**Purpose**: DALL-E image generation + all FastAPI endpoints

**Key Outputs:**
- ImageGenerator with DALL-E 3 integration
- 9 API endpoints implemented
- Background task orchestration
- Workflow resume functionality (approve/reject)
- Image serving endpoint

**Prerequisites:**
- Database layer complete (for repositories)
- LLM integration complete (for image prompt generation)
- LangGraph workflow complete (for workflow resume)

**Success Indicators:**
- `uv run pytest tests/api/ -v` all pass
- `uv run pytest tests/images/ -v` all pass
- API server starts without errors
- Can generate, approve, reject posts via API

---

### 6. evaluation-testing-agent.md
**Purpose**: Content evaluation system + integration testing

**Key Outputs:**
- Complete evaluator implementations (Quality, Platform, LLM-as-Judge)
- EvaluationRunner orchestration
- Comprehensive integration tests
- >80% code coverage

**Prerequisites:**
- All other components complete (tests the full system)

**Success Indicators:**
- `uv run pytest tests/evaluation/ -v` all pass
- `uv run pytest tests/integration/ -v` all pass
- `uv run pytest --cov=src --cov-report=term` shows >80%
- Full workflow works end-to-end

## Coordination Points

### Between langgraph-workflow-agent and content-generation-agent
- **Interface**: `src/agent/nodes.py`
- **Workflow agent**: Implements control nodes (wait_for_approval, apply_feedback, finalize, handle_error)
- **Content agent**: Implements content nodes (analyze_topic, generate_linkedin, generate_instagram, generate_wordpress)
- **Shared**: Both import PostGenerationState from `src/agent/state.py`

### Between all agents
- All agents use shared models from `src/db/models.py` and `src/agent/schemas.py`
- All agents follow TDD principles
- All agents write tests in parallel with implementation
- All agents use LLMRouter from `src/llm/router.py` for LLM calls

## Testing Strategy

Each agent is responsible for:
1. **Unit tests** - Test individual functions/classes in isolation
2. **Integration tests** - Test interaction with dependencies (where applicable)
3. **TDD approach** - Write tests before/during implementation

Final integration testing by evaluation-testing-agent ensures everything works together.

## Progress Tracking

As each agent completes their work, update `TODO.md` to mark phases complete:
- Phase 3 complete → database-tdd-agent done
- Phase 4 complete → llm-integration-agent done
- Phase 6 complete → langgraph-workflow-agent + content-generation-agent done
- Phases 5 + 7 complete → api-integration-agent done
- Phases 8 + 10 complete → evaluation-testing-agent done

## Questions or Issues?

If agents encounter issues or need clarification:
1. Check `CLAUDE.md` for project context
2. Review `docs/ARCHITECTURE.md` for design decisions
3. Examine existing code in `src/` for patterns
4. Check `TODO.md` for phase dependencies

## Estimated Timeline

- **Week 1**: database-tdd-agent + llm-integration-agent (parallel)
- **Week 2-3**: langgraph-workflow-agent + content-generation-agent (parallel)
- **Week 3-4**: api-integration-agent
- **Week 4-5**: evaluation-testing-agent

**Total**: ~5 weeks to complete all phases with high quality.
