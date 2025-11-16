# Agent Quick Start Guide

## Using Specialized Agents in This Project

This project has 6 specialized agent definitions in `.claude/agents/` to help complete development with mastery.

## Quick Command Reference

### To start working on a specific phase:

```bash
# Read the agent specification
cat .claude/agents/<agent-name>.md

# Follow the agent's commands
# Each agent has a "Commands You'll Use" section with specific examples
```

## Agent Quick Reference

| When you need to... | Use this agent | File |
|---------------------|----------------|------|
| Set up database migrations and tests | database-tdd-agent | `.claude/agents/database-tdd-agent.md` |
| Implement LLM calls with fallback | llm-integration-agent | `.claude/agents/llm-integration-agent.md` |
| Build the LangGraph workflow | langgraph-workflow-agent | `.claude/agents/langgraph-workflow-agent.md` |
| Create content generation prompts | content-generation-agent | `.claude/agents/content-generation-agent.md` |
| Implement API endpoints & images | api-integration-agent | `.claude/agents/api-integration-agent.md` |
| Build evaluation & integration tests | evaluation-testing-agent | `.claude/agents/evaluation-testing-agent.md` |

## Current Status & Next Steps

**Current Phase**: Phase 3 (Database Implementation)

**Next Agent to Use**: `database-tdd-agent`

### Start here:
```bash
# 1. Read the agent specification
cat .claude/agents/database-tdd-agent.md

# 2. Initialize Alembic
uv run alembic init alembic

# 3. Create initial migration
uv run alembic revision --autogenerate -m "Initial schema"

# 4. Write repository tests (TDD)
# See tests/db/test_repositories.py

# 5. Run tests
uv run pytest tests/db/ -v
```

## Workflow

1. **Read** the agent specification for your current phase
2. **Follow** the technical requirements and patterns
3. **Complete** all tasks in the "Your Responsibilities" section
4. **Verify** using the "Success Criteria" checklist
5. **Move** to the next agent when complete

## Agent Dependencies

```
database-tdd-agent (Phase 3)
    ↓
llm-integration-agent (Phase 4)
    ↓
┌─────────────────────────────────────┐
│ langgraph-workflow-agent (Phase 6a) │
│ content-generation-agent (Phase 6b) │ ← Can work in parallel
└─────────────────────────────────────┘
    ↓
api-integration-agent (Phases 5 + 7)
    ↓
evaluation-testing-agent (Phases 8 + 10)
```

## Tips for Success

1. **Follow TDD**: Write tests before implementation
2. **Use the patterns**: Each agent provides code templates
3. **Check success criteria**: Don't move on until all ✅
4. **Run tests frequently**: `uv run pytest -v`
5. **Read the context**: Refer to `CLAUDE.md` and `docs/ARCHITECTURE.md`

## Getting Help

- **Project context**: `CLAUDE.md`
- **Architecture decisions**: `docs/ARCHITECTURE.md`
- **Overall progress**: `TODO.md`
- **Agent details**: `.claude/agents/README.md`
- **Specific agent**: `.claude/agents/<agent-name>.md`

## Estimated Completion

- Phase 3 (database): ~1 week
- Phase 4 (LLM): ~1-2 weeks
- Phase 6 (agent nodes): ~2 weeks (parallel work)
- Phases 5+7 (API): ~2 weeks
- Phases 8+10 (evaluation): ~2 weeks

**Total**: ~5 weeks of focused development

---

Start with `database-tdd-agent` and work your way through systematically! 🚀
