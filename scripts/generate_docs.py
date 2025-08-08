"""
Script to generate API documentation from Python docstrings.

This script automatically generates API documentation for the AI Seed
repository by scanning Python modules and extracting docstrings.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))


def generate_api_docs():
    """Generate API documentation files."""
    
    # Create API reference directory
    docs_dir = project_root / "docs" / "reference"
    docs_dir.mkdir(exist_ok=True)
    
    # Generate main API index
    api_index = """# API Reference

This section provides detailed API documentation for all modules in the AI Seed repository.

## Core Application

- [Main Application](main.md) - FastAPI application and endpoints
- [Models](models.md) - Data models and schemas

## AI Agents

- [Orchestrator](orchestrator.md) - Main agent coordination system
- [Crew Manager](crew_manager.md) - CrewAI management and execution
- [GitHub Integration](github_integration.md) - GitHub API interactions

## Utilities

- [Logger](logger.md) - Logging configuration and utilities
- [Configuration](config.md) - Configuration management

## Testing

- [Test Utilities](test_utils.md) - Testing helpers and fixtures
"""
    
    with open(docs_dir / "index.md", "w") as f:
        f.write(api_index)
    
    # Generate individual module documentation
    modules = [
        ("src.main", "main.md", "Main Application"),
        ("agents.orchestrator", "orchestrator.md", "Agent Orchestrator"),
        ("agents.crew_manager", "crew_manager.md", "Crew Manager"),
        ("agents.github_integration", "github_integration.md", "GitHub Integration"),
        ("utils.logger", "logger.md", "Logger Utilities")
    ]
    
    for module_name, filename, title in modules:
        doc_content = f"""# {title}

::: {module_name}
"""
        
        with open(docs_dir / filename, "w") as f:
            f.write(doc_content)
    
    print("API documentation generated successfully!")


if __name__ == "__main__":
    generate_api_docs()
