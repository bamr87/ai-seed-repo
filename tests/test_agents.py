"""
Test suite for AI agent orchestration and workflow management.

This module tests the coordination between different AI agents,
workflow execution, and integration with external systems.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.crew_manager import CrewManager
from agents.github_integration import GitHubIntegration

# Import modules to test
from agents.orchestrator import AgentOrchestrator, EvolutionRequest


@pytest.fixture
def sample_evolution_request():
    """Create a sample evolution request for testing."""
    return EvolutionRequest(
        issue_number=123,
        title="Add user authentication system",
        body="We need to add JWT-based authentication to the API",
        repository="test-owner/test-repo",
        branch_name="evolution-issue-123"
    )


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
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
                "backstory": "Expert architect",
                "prompt_template": "Plan: {issue_title}"
            },
            "coder": {
                "role": "Implementation Agent",
                "goal": "Generate code",
                "backstory": "Senior engineer",
                "prompt_template": "Code: {task_description}"
            }
        },
        "workflow": {
            "max_iterations": 5,
            "agent_timeout": 300,
            "retry_attempts": 3
        }
    }


class TestAgentOrchestrator:
    """Test the main agent orchestrator functionality."""
    
    @pytest.fixture
    def orchestrator(self, mock_config):
        """Create orchestrator with mocked dependencies."""
        with patch('agents.orchestrator.CrewManager') as mock_crew:
            with patch('agents.orchestrator.GitHubIntegration') as mock_github:
                orchestrator = AgentOrchestrator.__new__(AgentOrchestrator)
                orchestrator.logger = MagicMock()
                orchestrator.config = mock_config
                orchestrator.github = mock_github.return_value
                orchestrator.crew_manager = mock_crew.return_value
                return orchestrator
    
    @pytest.mark.asyncio
    async def test_process_evolution_request_success(self, orchestrator, sample_evolution_request):
        """Test successful evolution request processing."""
        # Mock dependencies
        orchestrator.github.create_branch = AsyncMock(return_value=True)
        orchestrator._gather_repository_context = AsyncMock(return_value={"structure": "test"})
        orchestrator._execute_agent_workflow = AsyncMock(return_value={"success": True, "changes": []})
        orchestrator._create_pull_request = AsyncMock(return_value={"success": True, "pr_number": 456})
        orchestrator._post_process_evolution = AsyncMock()
        
        # Execute
        result = await orchestrator.process_evolution_request(sample_evolution_request)
        
        # Verify
        assert result is True
        orchestrator.github.create_branch.assert_called_once_with("evolution-issue-123")
        orchestrator._execute_agent_workflow.assert_called_once()
        orchestrator._create_pull_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_evolution_request_workflow_failure(self, orchestrator, sample_evolution_request):
        """Test evolution request processing when workflow fails."""
        # Mock dependencies
        orchestrator.github.create_branch = AsyncMock(return_value=True)
        orchestrator._gather_repository_context = AsyncMock(return_value={"structure": "test"})
        orchestrator._execute_agent_workflow = AsyncMock(return_value={"success": False, "error": "Workflow failed"})
        orchestrator._handle_evolution_failure = AsyncMock()
        
        # Execute
        result = await orchestrator.process_evolution_request(sample_evolution_request)
        
        # Verify
        assert result is False
        orchestrator._handle_evolution_failure.assert_not_called()  # Should not be called for workflow failure
    
    @pytest.mark.asyncio
    async def test_gather_repository_context(self, orchestrator):
        """Test repository context gathering."""
        # Mock GitHub integration methods
        orchestrator.github.get_repository_structure = AsyncMock(return_value={"tree": []})
        orchestrator.github.get_key_files = AsyncMock(return_value={"README.md": "content"})
        orchestrator.github.get_recent_commits = AsyncMock(return_value=[{"sha": "abc123"}])
        orchestrator.github.get_test_files = AsyncMock(return_value=["test_main.py"])
        orchestrator.github.get_documentation_files = AsyncMock(return_value=["README.md"])
        
        # Execute
        context = await orchestrator._gather_repository_context("test-repo")
        
        # Verify
        assert "structure" in context
        assert "key_files" in context
        assert "recent_changes" in context
        assert "existing_tests" in context
        assert "documentation" in context
        
        # Verify all methods were called
        orchestrator.github.get_repository_structure.assert_called_once()
        orchestrator.github.get_key_files.assert_called_once()
        orchestrator.github.get_recent_commits.assert_called_once()
    
    def test_generate_pr_description(self, orchestrator, sample_evolution_request):
        """Test PR description generation."""
        workflow_result = {
            "planning_summary": "Created implementation plan",
            "implementation_summary": "Added authentication system",
            "testing_summary": "Added comprehensive tests",
            "documentation_summary": "Updated API documentation",
            "file_changes": [
                {"file": "src/auth.py", "description": "Added authentication module"},
                {"file": "tests/test_auth.py", "description": "Added auth tests"}
            ]
        }
        
        description = orchestrator._generate_pr_description(sample_evolution_request, workflow_result)
        
        assert sample_evolution_request.title in description
        assert f"#{sample_evolution_request.issue_number}" in description
        assert "Created implementation plan" in description
        assert "src/auth.py" in description
        assert "Added authentication module" in description


class TestCrewManager:
    """Test the CrewAI management system."""
    
    @pytest.fixture
    def crew_manager(self, mock_config):
        """Create crew manager with mocked dependencies."""
        with patch('agents.crew_manager.ChatOpenAI'):
            with patch('agents.crew_manager.Agent'):
                with patch('agents.crew_manager.FileReadTool'):
                    crew_manager = CrewManager.__new__(CrewManager)
                    crew_manager.logger = MagicMock()
                    crew_manager.config = mock_config
                    crew_manager.llm = MagicMock()
                    crew_manager.agents = {
                        'planner': MagicMock(),
                        'coder': MagicMock(),
                        'tester': MagicMock()
                    }
                    return crew_manager
    
    def test_initialize_llm_openai(self, mock_config):
        """Test LLM initialization with OpenAI."""
        with patch('agents.crew_manager.ChatOpenAI') as mock_openai:
            crew_manager = CrewManager.__new__(CrewManager)
            crew_manager.config = mock_config
            
            crew_manager._initialize_llm()
            
            mock_openai.assert_called_once_with(
                model="gpt-4o",
                temperature=0.1,
                max_tokens=4096
            )
    
    def test_initialize_llm_anthropic(self, mock_config):
        """Test LLM initialization with Anthropic."""
        mock_config["llm_config"]["provider"] = "anthropic"
        mock_config["llm_config"]["model"] = "claude-3-5-sonnet-20241022"
        
        with patch('agents.crew_manager.ChatAnthropic') as mock_anthropic:
            crew_manager = CrewManager.__new__(CrewManager)
            crew_manager.config = mock_config
            
            crew_manager._initialize_llm()
            
            mock_anthropic.assert_called_once_with(
                model="claude-3-5-sonnet-20241022",
                temperature=0.1,
                max_tokens=4096
            )
    
    def test_format_prompt(self, crew_manager):
        """Test prompt formatting with context variables."""
        template = "Task: {task_name}, Issue: {issue_number}"
        context = {
            "task_name": "implement auth",
            "issue_number": 123
        }
        
        result = crew_manager._format_prompt(template, context)
        
        assert result == "Task: implement auth, Issue: 123"
    
    def test_format_prompt_missing_variable(self, crew_manager):
        """Test prompt formatting with missing context variable."""
        template = "Task: {task_name}, Issue: {missing_var}"
        context = {"task_name": "implement auth"}
        
        # Should return original template when variable is missing
        result = crew_manager._format_prompt(template, context)
        assert result == template
    
    @pytest.mark.asyncio
    async def test_execute_evolution_workflow_success(self, crew_manager):
        """Test successful evolution workflow execution."""
        workflow_input = {
            "issue_title": "Add auth",
            "issue_body": "Need authentication",
            "repository_context": {"structure": "test"}
        }
        
        # Mock crew execution
        mock_result = "Workflow completed successfully"
        mock_tasks = [MagicMock(), MagicMock()]
        
        with patch.object(crew_manager, '_create_tasks', return_value=mock_tasks):
            with patch('agents.crew_manager.Crew') as mock_crew:
                with patch('asyncio.to_thread', return_value=mock_result):
                    result = await crew_manager.execute_evolution_workflow(workflow_input)
        
        assert result["success"] is True
        assert "planning_summary" in result
        assert "implementation_summary" in result


class TestGitHubIntegration:
    """Test GitHub API integration functionality."""
    
    @pytest.fixture
    def github_integration(self, mock_config):
        """Create GitHub integration with mocked dependencies."""
        with patch.dict('os.environ', {'GITHUB_TOKEN': 'test-token'}):
            integration = GitHubIntegration.__new__(GitHubIntegration)
            integration.logger = MagicMock()
            integration.config = mock_config
            integration.token = 'test-token'
            integration.base_url = 'https://api.github.com'
            integration.headers = {
                'Authorization': 'Bearer test-token',
                'Accept': 'application/vnd.github.v3+json',
                'Content-Type': 'application/json'
            }
            return integration
    
    def test_get_repo_info_from_git(self, github_integration):
        """Test extracting repository info from git remote."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = "https://github.com/test-owner/test-repo.git\n"
            mock_run.return_value.returncode = 0
            
            owner, repo = github_integration._get_repo_info()
            
            assert owner == "test-owner"
            assert repo == "test-repo"
    
    def test_summarize_structure(self, github_integration):
        """Test repository structure summarization."""
        tree_data = [
            {"path": "src/main.py", "type": "blob"},
            {"path": "src/auth.py", "type": "blob"},
            {"path": "tests/test_main.py", "type": "blob"},
            {"path": "docs", "type": "tree"},
            {"path": "src", "type": "tree"}
        ]
        
        summary = github_integration._summarize_structure(tree_data)
        
        assert "2 main directories" in summary
        assert "docs, src" in summary
        assert "py(3)" in summary
    
    @pytest.mark.asyncio
    async def test_create_branch_success(self, github_integration):
        """Test successful branch creation."""
        with patch('requests.get') as mock_get:
            with patch('requests.post') as mock_post:
                # Mock getting base branch SHA
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = {"object": {"sha": "abc123"}}
                
                # Mock creating branch
                mock_post.return_value.status_code = 201
                
                result = await github_integration.create_branch("test-branch")
                
                assert result is True
                mock_get.assert_called_once()
                mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_branch_failure(self, github_integration):
        """Test branch creation failure."""
        with patch('requests.get') as mock_get:
            # Mock failure to get base branch
            mock_get.return_value.status_code = 404
            
            result = await github_integration.create_branch("test-branch")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_create_pull_request_success(self, github_integration):
        """Test successful pull request creation."""
        pr_data = {
            "title": "Test PR",
            "body": "Test PR body",
            "head": "test-branch",
            "base": "main"
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = {
                "number": 456,
                "html_url": "https://github.com/test/repo/pull/456"
            }
            
            result = await github_integration.create_pull_request(pr_data)
            
            assert result["success"] is True
            assert result["pr_number"] == 456
            assert "github.com" in result["pr_url"]
    
    @pytest.mark.asyncio
    async def test_comment_on_issue_success(self, github_integration):
        """Test successful issue commenting."""
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 201
            
            result = await github_integration.comment_on_issue(123, "Test comment")
            
            assert result is True
            mock_post.assert_called_once()


# Integration tests combining multiple components
class TestAgentIntegration:
    """Integration tests for agent collaboration."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_evolution_workflow(self, sample_evolution_request):
        """Test complete end-to-end evolution workflow."""
        with patch.dict('os.environ', {'GITHUB_TOKEN': 'test-token'}):
            with patch('agents.orchestrator.CrewManager') as mock_crew:
                with patch('agents.orchestrator.GitHubIntegration') as mock_github:
                    # Setup mocks
                    mock_github_instance = mock_github.return_value
                    mock_github_instance.create_branch = AsyncMock(return_value=True)
                    mock_github_instance.create_pull_request = AsyncMock(return_value={
                        "success": True,
                        "pr_number": 456
                    })
                    
                    mock_crew_instance = mock_crew.return_value
                    mock_crew_instance.execute_evolution_workflow = AsyncMock(return_value={
                        "success": True,
                        "planning_summary": "Plan created",
                        "implementation_summary": "Code implemented",
                        "testing_summary": "Tests added"
                    })
                    
                    # Create orchestrator and execute
                    orchestrator = AgentOrchestrator()
                    result = await orchestrator.process_evolution_request(sample_evolution_request)
                    
                    # Verify workflow executed successfully
                    assert result is True
                    mock_github_instance.create_branch.assert_called_once()
                    mock_crew_instance.execute_evolution_workflow.assert_called_once()
                    mock_github_instance.create_pull_request.assert_called_once()


# Performance and reliability tests
class TestAgentReliability:
    """Test agent system reliability and error handling."""
    
    @pytest.mark.asyncio
    async def test_orchestrator_handles_timeout(self, sample_evolution_request):
        """Test orchestrator handles agent timeouts gracefully."""
        with patch.dict('os.environ', {'GITHUB_TOKEN': 'test-token'}):
            with patch('agents.orchestrator.CrewManager') as mock_crew:
                # Simulate timeout
                mock_crew.return_value.execute_evolution_workflow = AsyncMock(
                    side_effect=asyncio.TimeoutError("Agent timeout")
                )
                
                orchestrator = AgentOrchestrator()
                result = await orchestrator.process_evolution_request(sample_evolution_request)
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_github_api_rate_limiting(self, github_integration):
        """Test handling of GitHub API rate limiting."""
        with patch('requests.get') as mock_get:
            # Simulate rate limiting response
            mock_get.return_value.status_code = 403
            mock_get.return_value.json.return_value = {
                "message": "API rate limit exceeded"
            }
            
            result = await github_integration.get_repository_structure()
            
            # Should handle gracefully and return empty structure
            assert "tree" in result
            assert result["tree"] == []
