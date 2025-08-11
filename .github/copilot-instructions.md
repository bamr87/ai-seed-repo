# Copilot Instructions for AI Seed Repository

This repository implements a self-evolving application framework where AI agents autonomously implement features through GitHub issue workflows.

## Architecture Overview

The system follows a **multi-agent workflow pattern**:
- GitHub issues with `evolution` label or `[EVOLUTION]` title trigger automation via `.github/workflows/evolve-on-issue.yml`
- `AgentOrchestrator` coordinates the complete evolution lifecycle in `agents/orchestrator.py`
- CrewAI manages specialized agents (Planner → Coder → Tester → Documenter → Deployer → Evolver)
- All changes create PRs for human review before deployment
- Agents learn from outcomes and continuously improve system performance

## Key Components

### Agent System (`agents/`)
- `orchestrator.py` - Main coordination via `AgentOrchestrator.process_evolution_request()`
- `crew_manager.py` - CrewAI-based multi-agent workflow execution
- `github_integration.py` - GitHub API operations (branch creation, PR management, context gathering)

The orchestrator follows this exact workflow:
1. `_gather_repository_context()` - Analyzes current codebase state
2. `github.create_branch()` - Creates feature branch from issue number
3. `_execute_agent_workflow()` - Runs CrewAI agent sequence
4. `_create_pull_request()` - Generates PR with agent-created changes
5. `_post_process_evolution()` - Learning and feedback collection

### Core Application (`src/`)
- `main.py` - FastAPI app serving as evolvable foundation (starts with basic endpoints, agents extend it)
- Uses Pydantic models for request/response validation
- CORS enabled for cross-origin development
- Health check and evolution status endpoints at `/health` and `/evolution/*`

### Configuration (`seed_instructions.yaml`)
- **Critical**: Contains all agent prompts, LLM configs, and behavioral rules
- Agents can self-modify this file to improve performance
- Uses template variables like `{issue_title}`, `{repository_context}`, `{issue_body}`
- Includes dependency policy: "latest-unpinned" with eager upgrade strategy

## Development Patterns

### Agent Prompt Engineering
All agent behavior is controlled via `seed_instructions.yaml`:
- Use specific role definitions, goals, and backstories for each agent
- Include context variables: `{issue_title}`, `{issue_body}`, `{repository_context}` 
- Specify expected output formats (JSON for planning, code blocks for implementation)
- Reference existing patterns: agents learn from current codebase structure and conventions

### Testing Strategy
- **Async test patterns**: Use `@pytest.fixture(scope="session")` for event loops in `tests/conftest.py`
- **Mock external dependencies**: GitHub API calls, LLM requests using `unittest.mock.AsyncMock`
- **Integration tests**: Simulate complete agent workflows with `EvolutionRequest` objects
- **Coverage target**: 95%+ as enforced by CI/CD pipeline
- Run tests: `python -m pytest tests/ -v --cov=src --cov=agents`

### Evolution Workflow Triggers
**To trigger evolution**: Create GitHub issue with:
- Label `evolution` OR title containing `[EVOLUTION]`
- Clear requirements and acceptance criteria in issue body
- The workflow automatically creates branch `evolution-issue-{number}` and processes through agents

### Error Handling & Logging
- All operations use `utils.logger.setup_logger(__name__)` with structured formatting
- Implement retry logic with exponential backoff for external API calls
- Failed evolutions automatically comment on original issues with error details
- Use defensive coding: validate inputs, handle None values, provide fallbacks

## Code Conventions

### Python Standards
- **PEP8 compliance** with comprehensive type hints for all functions/methods
- **Comprehensive docstrings**: Google-style docstrings for all modules, classes, functions
- **Project structure**: Add project root to path using `sys.path.append(str(project_root))`
- **Dependency management**: Use "latest-unpinned" policy from `seed_instructions.yaml`
- **Async patterns**: Use `async`/`await` for I/O operations, especially GitHub API calls

### FastAPI Patterns (in `src/main.py`)
- **Pydantic models**: Define request/response schemas (e.g., `HealthResponse`, `InfoResponse`)
- **CORS middleware**: Pre-configured for development (`allow_origins=["*"]`)
- **Structured endpoints**: Use clear REST patterns, include comprehensive OpenAPI docs
- **Evolution endpoints**: Agents can extend the API by adding new endpoints and models

### Testing Patterns
- **Fixture organization**: Common fixtures in `tests/conftest.py` (event loops, temp dirs, mock configs)
- **Mock patterns**: `AsyncMock` for async operations, `MagicMock` for sync operations
- **Test data**: Use `EvolutionRequest` dataclass for consistent test scenarios
- **File structure**: Mirror `src/` structure in `tests/` (e.g., `test_main.py` for `src/main.py`)

## Key Commands & Development Workflow

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Run FastAPI application locally
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run comprehensive tests with coverage
python -m pytest tests/ -v --cov=src --cov=agents --cov-report=html

# Generate/update documentation
python scripts/generate_docs.py
mkdocs serve  # View at http://localhost:8000
```

### Key Files to Understand

- `seed_instructions.yaml` - **Central nervous system**: All agent behavior, prompts, and system configuration
- `.github/workflows/evolve-on-issue.yml` - **Evolution trigger**: Detects issues and orchestrates agent workflows
- `agents/orchestrator.py` - **Coordination hub**: `AgentOrchestrator.process_evolution_request()` manages entire lifecycle
- `src/main.py` - **Evolvable core**: FastAPI application that agents can extend and modify
- `utils/logger.py` - **Logging standard**: Use `setup_logger(__name__)` for consistent logging across all modules

### Critical Integration Points
- **CrewAI integration**: Agents communicate via CrewAI's task and crew system in `agents/crew_manager.py`
- **GitHub API**: All repository operations go through `agents/github_integration.py` 
- **LLM providers**: Configurable OpenAI/Anthropic via environment variables and `seed_instructions.yaml`

When modifying agent behavior, update the corresponding prompt templates in `seed_instructions.yaml` and test with realistic evolution scenarios.
