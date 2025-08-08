# Copilot Instructions for AI Seed Repository

This repository implements a self-evolving application framework where AI agents autonomously implement features through GitHub issue workflows.

## Architecture Overview

The system follows a **multi-agent workflow pattern**:
- GitHub issues trigger agent orchestration via Actions
- CrewAI coordinates specialized agents (Planner → Coder → Tester → Documenter → Deployer)
- All changes create PRs for human review before deployment
- The Evolver agent continuously improves the system based on outcomes

## Key Components

### Agent System (`agents/`)
- `orchestrator.py` - Main coordination logic for evolution workflows
- `crew_manager.py` - CrewAI-based multi-agent management 
- `github_integration.py` - GitHub API operations for agents

The orchestrator processes evolution requests by:
1. Gathering repository context
2. Creating feature branches  
3. Executing agent workflows via CrewManager
4. Creating PRs with comprehensive descriptions

### Core Application (`src/`)
- `main.py` - FastAPI app that serves as the evolvable base
- Designed to be extended by agents (starts as simple API, grows via evolution)
- Includes evolution logging endpoints for agent coordination

### Configuration (`seed_instructions.yaml`)
- Contains agent prompts, LLM configs, and workflow rules
- The Evolver agent can modify this file to improve system performance
- Use precise prompt templates with `{variable}` placeholders

## Development Patterns

### Agent Prompt Design
Prompts should be specific and include:
- Clear role definitions and goals
- Context variables like `{issue_title}`, `{repository_context}`
- Expected output formats (structured JSON for planning, code for implementation)
- Reference to existing code patterns and conventions

### Testing Strategy
- Comprehensive pytest suites in `tests/`
- Mock external dependencies (GitHub API, LLM calls) for unit tests
- Integration tests simulate complete agent workflows
- Aim for 95%+ coverage as enforced by agents

### Evolution Workflow
When creating new evolution requests:
1. Use the GitHub issue template in `.github/ISSUE_TEMPLATE/`
2. Include clear requirements and acceptance criteria  
3. Specify technical constraints or integration needs
4. The workflow automatically triggers agent coordination

### Error Handling
- All agent operations include retry logic with exponential backoff
- Failed evolutions comment on original issues with error details
- Human notification mechanisms prevent silent failures

## Code Conventions

- Follow PEP8 with comprehensive type hints and docstrings
- Use dependency injection and SOLID principles  
- Implement defensive coding with proper error handling
- All functions/classes must have comprehensive docstrings

## Key Files to Understand

- `seed_instructions.yaml` - Agent behavior and system configuration
- `.github/workflows/evolve-on-issue.yml` - Core automation trigger
- `agents/orchestrator.py` - Central coordination logic
- `src/main.py` - Evolvable application core

When modifying agent behavior, update the corresponding prompt templates in `seed_instructions.yaml` and test with realistic evolution scenarios.
