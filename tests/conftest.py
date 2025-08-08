"""
Test configuration and utilities for the test suite.

This module provides common fixtures, utilities, and configuration
for all tests in the AI seed repository.
"""

import asyncio
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Generator
from unittest.mock import MagicMock

import pytest


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_directory() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    return MagicMock()


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """Create a sample configuration for testing."""
    return {
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.1,
            "max_tokens": 4096
        },
        "agents": {
            "planner": {
                "role": "Strategic Planning Agent",
                "goal": "Create implementation plans",
                "backstory": "Expert software architect",
                "prompt_template": "Plan the following: {issue_title}"
            },
            "coder": {
                "role": "Implementation Agent",
                "goal": "Generate high-quality code",
                "backstory": "Senior software engineer",
                "prompt_template": "Implement: {task_description}"
            }
        },
        "workflow": {
            "max_iterations": 5,
            "agent_timeout": 300,
            "retry_attempts": 3
        }
    }


@pytest.fixture
def sample_repository_structure():
    """Create a sample repository structure for testing."""
    return {
        "tree": [
            {"path": "src/main.py", "type": "blob"},
            {"path": "src/models.py", "type": "blob"},
            {"path": "tests/test_main.py", "type": "blob"},
            {"path": "README.md", "type": "blob"},
            {"path": "requirements.txt", "type": "blob"},
            {"path": "src", "type": "tree"},
            {"path": "tests", "type": "tree"}
        ],
        "structure_summary": "Repository has 2 main directories: src, tests\nFile types: py(3), md(1), txt(1)"
    }


# Test markers for categorizing tests
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "external: Tests that require external services")


# Async test utilities
class AsyncTestHelper:
    """Helper class for async test operations."""
    
    @staticmethod
    async def wait_for_condition(condition_func, timeout=5.0, interval=0.1):
        """Wait for a condition to become true."""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if condition_func():
                return True
            await asyncio.sleep(interval)
            
        return False


@pytest.fixture
def async_helper():
    """Provide async test helper."""
    return AsyncTestHelper()
