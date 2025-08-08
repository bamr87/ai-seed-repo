"""
AI Agent Orchestrator - Main coordination system for the evolution workflow.

This module coordinates the entire AI agent workflow, from issue processing
to pull request creation, ensuring proper sequencing and communication
between all specialized agents.
"""

import argparse
import asyncio
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import yaml

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from agents.crew_manager import CrewManager
from agents.github_integration import GitHubIntegration
from utils.logger import setup_logger


@dataclass
class EvolutionRequest:
    """Data class representing an evolution request from a GitHub issue."""
    issue_number: int
    title: str
    body: str
    repository: str
    branch_name: str
    labels: List[str] = None


class AgentOrchestrator:
    """
    Main orchestrator that coordinates all AI agents in the evolution workflow.
    
    This class manages the complete lifecycle from issue analysis to PR creation,
    ensuring proper sequencing, error handling, and communication between agents.
    """
    
    def __init__(self, config_path: str = "seed_instructions.yaml"):
        """Initialize the orchestrator with configuration."""
        self.logger = setup_logger(__name__)
        self.config = self._load_config(config_path)
        self.github = GitHubIntegration(self.config)
        self.crew_manager = CrewManager(self.config)
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            config_file = project_root / config_path
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Failed to load config from {config_path}: {e}")
            raise
            
    async def process_evolution_request(self, request: EvolutionRequest) -> bool:
        """
        Process a complete evolution request through the agent workflow.
        
        Args:
            request: The evolution request to process
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info(f"Starting evolution process for issue #{request.issue_number}")
        
        try:
            # Step 1: Repository context gathering
            repo_context = await self._gather_repository_context(request.repository)
            
            # Step 2: Create working branch
            await self.github.create_branch(request.branch_name)
            
            # Step 3: Agent workflow execution
            workflow_result = await self._execute_agent_workflow(request, repo_context)
            
            if not workflow_result["success"]:
                self.logger.error("Agent workflow failed")
                return False
                
            # Step 4: Create pull request
            pr_result = await self._create_pull_request(request, workflow_result)
            
            # Step 5: Post-process and learn
            await self._post_process_evolution(request, workflow_result, pr_result)
            
            self.logger.info(f"Evolution process completed successfully for issue #{request.issue_number}")
            return True
            
        except Exception as e:
            self.logger.error(f"Evolution process failed: {e}")
            await self._handle_evolution_failure(request, str(e))
            return False
            
    async def _gather_repository_context(self, repository: str) -> Dict[str, Any]:
        """Gather comprehensive repository context for agents."""
        self.logger.info("Gathering repository context...")
        
        context = {
            "structure": await self.github.get_repository_structure(),
            "key_files": await self.github.get_key_files(),
            "recent_changes": await self.github.get_recent_commits(),
            "existing_tests": await self.github.get_test_files(),
            "documentation": await self.github.get_documentation_files(),
        }
        
        return context
        
    async def _execute_agent_workflow(self, request: EvolutionRequest, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete agent workflow."""
        self.logger.info("Executing agent workflow...")
        
        # Prepare workflow input
        workflow_input = {
            "issue_number": request.issue_number,
            "issue_title": request.title,
            "issue_body": request.body,
            "repository_context": context,
            "branch_name": request.branch_name
        }
        
        # Execute the CrewAI workflow
        result = await self.crew_manager.execute_evolution_workflow(workflow_input)
        
        return result
        
    async def _create_pull_request(self, request: EvolutionRequest, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create a pull request with the agent-generated changes."""
        self.logger.info("Creating pull request...")
        
        pr_data = {
            "title": f"[AI Evolution] {request.title}",
            "body": self._generate_pr_description(request, workflow_result),
            "head": request.branch_name,
            "base": "main"
        }
        
        pr_result = await self.github.create_pull_request(pr_data)
        return pr_result
        
    def _generate_pr_description(self, request: EvolutionRequest, workflow_result: Dict[str, Any]) -> str:
        """Generate comprehensive PR description."""
        return f"""
# AI Evolution: {request.title}

## 🎯 Original Request
Resolves #{request.issue_number}

{request.body}

## 🤖 AI Implementation Summary

### 📋 Planning Phase
{workflow_result.get('planning_summary', 'No planning summary available')}

### 💻 Implementation
{workflow_result.get('implementation_summary', 'No implementation summary available')}

### 🧪 Testing
{workflow_result.get('testing_summary', 'No testing summary available')}

### 📚 Documentation Updates
{workflow_result.get('documentation_summary', 'No documentation summary available')}

## 🔍 Files Changed
{self._format_file_changes(workflow_result.get('file_changes', []))}

## ✅ Quality Checks
- [ ] All tests passing
- [ ] Code coverage maintained
- [ ] Documentation updated
- [ ] Security scan passed
- [ ] Performance impact assessed

## 🚀 Deployment Notes
{workflow_result.get('deployment_notes', 'Standard deployment process')}

---
*This PR was generated automatically by AI agents. Please review thoroughly before merging.*
"""
        
    def _format_file_changes(self, file_changes: List[Dict[str, Any]]) -> str:
        """Format file changes for PR description."""
        if not file_changes:
            return "No file changes reported"
            
        formatted = []
        for change in file_changes:
            formatted.append(f"- `{change['file']}`: {change['description']}")
            
        return "\n".join(formatted)
        
    async def _post_process_evolution(self, request: EvolutionRequest, workflow_result: Dict[str, Any], pr_result: Dict[str, Any]) -> None:
        """Post-process the evolution for learning and improvement."""
        self.logger.info("Post-processing evolution results...")
        
        # Trigger the evolver agent for system improvement
        evolution_data = {
            "original_request": request.__dict__,
            "workflow_result": workflow_result,
            "pr_result": pr_result
        }
        
        await self.crew_manager.trigger_evolution_analysis(evolution_data)
        
    async def _handle_evolution_failure(self, request: EvolutionRequest, error_message: str) -> None:
        """Handle evolution process failures."""
        self.logger.error(f"Handling evolution failure for issue #{request.issue_number}")
        
        # Comment on the original issue with failure information
        failure_comment = f"""
🚨 **Evolution Process Failed**

The AI agent workflow encountered an error while processing this evolution request.

**Error Details:**
```
{error_message}
```

**Next Steps:**
1. Review the error details above
2. Check if the issue description needs clarification
3. Verify that all requirements are clearly specified
4. Re-trigger the evolution by commenting `/retry-evolution`

The development team has been notified and will investigate the issue.
"""
        
        await self.github.comment_on_issue(request.issue_number, failure_comment)


def main():
    """Main entry point for the orchestrator."""
    parser = argparse.ArgumentParser(description="AI Agent Evolution Orchestrator")
    parser.add_argument("--issue-number", type=int, required=True, help="GitHub issue number")
    parser.add_argument("--issue-title", type=str, required=True, help="GitHub issue title")
    parser.add_argument("--issue-body", type=str, required=True, help="GitHub issue body")
    parser.add_argument("--repository", type=str, required=True, help="Repository name")
    parser.add_argument("--branch-name", type=str, required=True, help="Branch name for changes")
    
    args = parser.parse_args()
    
    # Create evolution request
    request = EvolutionRequest(
        issue_number=args.issue_number,
        title=args.issue_title,
        body=args.issue_body,
        repository=args.repository,
        branch_name=args.branch_name
    )
    
    # Initialize and run orchestrator
    orchestrator = AgentOrchestrator()
    
    # Run async workflow
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        success = loop.run_until_complete(orchestrator.process_evolution_request(request))
        sys.exit(0 if success else 1)
    except Exception as e:
        logging.error(f"Orchestrator failed: {e}")
        sys.exit(1)
    finally:
        loop.close()


if __name__ == "__main__":
    main()
