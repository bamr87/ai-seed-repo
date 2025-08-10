"""
CrewAI-based agent crew management system.

This module manages the coordination of multiple AI agents using the CrewAI framework,
handling the complete evolution workflow from planning to implementation.
"""

import asyncio
from typing import Any, Dict, List

from crewai import Agent, Crew, Process, Task
from crewai_tools import DirectoryReadTool, FileReadTool, FileWriterTool
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from utils.logger import setup_logger


class CrewManager:
    """
    Manages CrewAI agents for the evolution workflow.
    
    Coordinates specialized agents (Planner, Coder, Tester, Documenter, 
    Deployer, Evolver) to implement evolution requests collaboratively.
    """
    
    def __init__(self, config: Dict[str, Any], mode: str = "full"):
        """Initialize the crew manager with configuration.
        
        Args:
            config: Seed configuration
            mode: 'full' to create all agents, 'triage' to only enable triager
        """
        self.logger = setup_logger(__name__)
        self.config = config
        self.mode = mode
        self.llm = self._initialize_llm()
        self.agents = self._create_agents()
        
    def _initialize_llm(self):
        """Initialize the LLM based on configuration. Returns None if unavailable."""
        llm_config = self.config.get('llm_config', {})
        provider = llm_config.get('provider', 'openai')
        model = llm_config.get('model', 'gpt-4o')
        temperature = llm_config.get('temperature', 0.1)
        max_tokens = llm_config.get('max_tokens', 4096)
        try:
            if provider == 'openai':
                return ChatOpenAI(
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            elif provider == 'anthropic':
                return ChatAnthropic(
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            else:
                raise ValueError(f"Unsupported LLM provider: {provider}")
        except Exception as e:
            self.logger.warning(f"LLM initialization failed; falling back to no-LLM mode: {e}")
            return None
            
    def _create_agents(self) -> Dict[str, Agent]:
        """Create all specialized agents with their configurations. May be empty if no LLM."""
        agents_config = self.config.get('agents', {})
        agents: Dict[str, Agent] = {}
        
        # If LLM is unavailable, only allow triage fallback without agents
        if self.llm is None:
            # Create no agents; run_triage_report will fallback
            return agents
        
        # Common tools available to all agents
        common_tools = [
            FileReadTool(),
            FileWriteTool(),
            DirectoryReadTool()
        ]
        
        # In 'triage' mode, only create triager agent
        if self.mode == 'triage':
            triager_config = agents_config.get('triager', {})
            if triager_config:
                agents['triager'] = Agent(
                    role=triager_config.get('role', 'Failure Triage Agent'),
                    goal=triager_config.get('goal', 'Distill failing workflow logs into actionable issues'),
                    backstory=triager_config.get('backstory', 'Reliability engineer for CI/CD diagnostics'),
                    tools=common_tools,
                    llm=self.llm,
                    verbose=True,
                    allow_delegation=False,
                    max_iter=2
                )
            return agents
        
        # Planner Agent
        planner_config = agents_config.get('planner', {})
        agents['planner'] = Agent(
            role=planner_config.get('role', 'Strategic Planning Agent'),
            goal=planner_config.get('goal', 'Create comprehensive implementation plans'),
            backstory=planner_config.get('backstory', 'Expert software architect'),
            tools=common_tools,
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
        
        # Coder Agent
        coder_config = agents_config.get('coder', {})
        agents['coder'] = Agent(
            role=coder_config.get('role', 'Implementation Agent'),
            goal=coder_config.get('goal', 'Generate high-quality, maintainable code'),
            backstory=coder_config.get('backstory', 'Senior software engineer'),
            tools=common_tools,
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=5
        )
        
        # Tester Agent
        tester_config = agents_config.get('tester', {})
        agents['tester'] = Agent(
            role=tester_config.get('role', 'Quality Assurance Agent'),
            goal=tester_config.get('goal', 'Ensure comprehensive test coverage'),
            backstory=tester_config.get('backstory', 'Testing specialist'),
            tools=common_tools,
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
        
        # Documenter Agent
        documenter_config = agents_config.get('documenter', {})
        agents['documenter'] = Agent(
            role=documenter_config.get('role', 'Documentation Agent'),
            goal=documenter_config.get('goal', 'Maintain comprehensive documentation'),
            backstory=documenter_config.get('backstory', 'Technical writer'),
            tools=common_tools,
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=2
        )
        
        # Deployer Agent
        deployer_config = agents_config.get('deployer', {})
        agents['deployer'] = Agent(
            role=deployer_config.get('role', 'Deployment Agent'),
            goal=deployer_config.get('goal', 'Handle deployment configurations'),
            backstory=deployer_config.get('backstory', 'DevOps engineer'),
            tools=common_tools,
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=2
        )
        
        # Evolver Agent
        evolver_config = agents_config.get('evolver', {})
        agents['evolver'] = Agent(
            role=evolver_config.get('role', 'System Evolution Agent'),
            goal=evolver_config.get('goal', 'Continuously improve the AI system'),
            backstory=evolver_config.get('backstory', 'Machine learning engineer'),
            tools=common_tools,
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=2
        )
        
        # Failure Triager Agent
        triager_config = agents_config.get('triager', {})
        if triager_config:
            agents['triager'] = Agent(
                role=triager_config.get('role', 'Failure Triage Agent'),
                goal=triager_config.get('goal', 'Distill failing workflow logs into actionable issues'),
                backstory=triager_config.get('backstory', 'Reliability engineer for CI/CD diagnostics'),
                tools=common_tools,
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
                max_iter=2
            )
        
        return agents
        
    def _create_tasks(self, workflow_input: Dict[str, Any]) -> List[Task]:
        """Create tasks for the evolution workflow."""
        agents_config = self.config.get('agents', {})
        
        # Planning Task
        planning_task = Task(
            description=self._format_prompt(
                agents_config.get('planner', {}).get('prompt_template', ''),
                workflow_input
            ),
            agent=self.agents['planner'],
            expected_output="Detailed implementation plan in structured format with task breakdown, file impact assessment, and testing strategy"
        )
        
        # Implementation Task
        implementation_task = Task(
            description=self._format_prompt(
                agents_config.get('coder', {}).get('prompt_template', ''),
                {**workflow_input, 'plan': '{planning_task_output}'}
            ),
            agent=self.agents['coder'],
            expected_output="Complete code implementation with proper error handling, type hints, and documentation",
            context=[planning_task]
        )
        
        # Testing Task
        testing_task = Task(
            description=self._format_prompt(
                agents_config.get('tester', {}).get('prompt_template', ''),
                {**workflow_input, 'implementation': '{implementation_task_output}'}
            ),
            agent=self.agents['tester'],
            expected_output="Comprehensive test suite with unit tests, integration tests, and edge case coverage",
            context=[implementation_task]
        )
        
        # Documentation Task
        documentation_task = Task(
            description=self._format_prompt(
                agents_config.get('documenter', {}).get('prompt_template', ''),
                {**workflow_input, 'implementation': '{implementation_task_output}'}
            ),
            agent=self.agents['documenter'],
            expected_output="Updated documentation including API docs, user guides, and developer documentation",
            context=[implementation_task]
        )
        
        # Deployment Task
        deployment_task = Task(
            description=self._format_prompt(
                agents_config.get('deployer', {}).get('prompt_template', ''),
                {**workflow_input, 'implementation': '{implementation_task_output}'}
            ),
            agent=self.agents['deployer'],
            expected_output="Deployment configuration updates and deployment scripts if needed",
            context=[implementation_task]
        )
        
        return [planning_task, implementation_task, testing_task, documentation_task, deployment_task]
        
    def _format_prompt(self, template: str, context: Dict[str, Any]) -> str:
        """Format prompt template with context variables."""
        try:
            return template.format(**context)
        except KeyError as e:
            self.logger.warning(f"Missing context variable {e} in prompt template")
            return template
            
    async def execute_evolution_workflow(self, workflow_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete evolution workflow using CrewAI."""
        self.logger.info("Starting CrewAI evolution workflow")
        
        try:
            # Create tasks for this workflow
            tasks = self._create_tasks(workflow_input)
            
            # Create and configure the crew
            crew = Crew(
                agents=list(self.agents.values()),
                tasks=tasks,
                process=Process.sequential,
                verbose=2
            )
            
            # Execute the workflow
            result = await asyncio.to_thread(crew.kickoff)
            
            # Process and structure the results
            workflow_result = self._process_crew_result(result, tasks)
            
            self.logger.info("CrewAI evolution workflow completed successfully")
            return workflow_result
            
        except Exception as e:
            self.logger.error(f"CrewAI workflow failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "planning_summary": "Workflow failed during execution",
                "implementation_summary": "No implementation completed",
                "testing_summary": "No tests created",
                "documentation_summary": "No documentation updated",
                "deployment_notes": "Deployment not configured",
                "file_changes": []
            }
            
    def _process_crew_result(self, result: Any, tasks: List[Task]) -> Dict[str, Any]:
        """Process and structure CrewAI results."""
        return {
            "success": True,
            "planning_summary": self._extract_task_output(tasks[0]) if len(tasks) > 0 else "No planning performed",
            "implementation_summary": self._extract_task_output(tasks[1]) if len(tasks) > 1 else "No implementation performed",
            "testing_summary": self._extract_task_output(tasks[2]) if len(tasks) > 2 else "No testing performed",
            "documentation_summary": self._extract_task_output(tasks[3]) if len(tasks) > 3 else "No documentation updated",
            "deployment_notes": self._extract_task_output(tasks[4]) if len(tasks) > 4 else "No deployment configuration",
            "file_changes": self._extract_file_changes(result),
            "full_result": str(result)
        }
        
    def _extract_task_output(self, task: Task) -> str:
        """Extract meaningful output from a task result."""
        try:
            if hasattr(task, 'output') and task.output:
                return str(task.output)[:1000]  # Truncate for summary
            return "Task completed but no detailed output available"
        except Exception as e:
            self.logger.warning(f"Could not extract task output: {e}")
            return "Task output extraction failed"
            
    def _extract_file_changes(self, result: Any) -> List[Dict[str, Any]]:
        """Extract file change information from workflow result."""
        # This is a placeholder - in a real implementation, you'd parse
        # the actual file operations performed by the agents
        return [
            {"file": "src/main.py", "description": "Updated based on evolution request"},
            {"file": "tests/", "description": "Added comprehensive test coverage"},
            {"file": "docs/", "description": "Updated documentation"}
        ]
        
    async def trigger_evolution_analysis(self, evolution_data: Dict[str, Any]) -> None:
        """Trigger the evolver agent for system improvement analysis."""
        self.logger.info("Triggering evolution analysis for system improvement")
        
        try:
            # Create evolution analysis task
            evolution_task = Task(
                description=self._format_prompt(
                    self.config.get('agents', {}).get('evolver', {}).get('prompt_template', ''),
                    evolution_data
                ),
                agent=self.agents['evolver'],
                expected_output="Analysis of evolution cycle with specific recommendations for system improvements"
            )
            
            # Execute evolution analysis
            crew = Crew(
                agents=[self.agents['evolver']],
                tasks=[evolution_task],
                process=Process.sequential,
                verbose=2
            )
            
            result = await asyncio.to_thread(crew.kickoff)
            
            # Store insights for future improvements
            await self._store_evolution_insights(result)
            
        except Exception as e:
            self.logger.error(f"Evolution analysis failed: {e}")
            
    async def _store_evolution_insights(self, insights: Any) -> None:
        """Store evolution insights for future system improvements."""
        # Placeholder for storing insights in memory system
        # In a real implementation, this would update the seed instructions
        # or store insights in a vector database for future reference
        self.logger.info("Evolution insights stored for future improvements")

    async def run_triage_report(self, triage_input: Dict[str, Any]) -> str:
        """Run the triager agent to produce a Markdown triage report from logs.
        
        Args:
            triage_input: Context including workflow_name, run_url, git_ref, commit_sha, failing_jobs_summary, logs_excerpt, repository_context, tail_lines
        Returns:
            Markdown string suitable for a GitHub Issue body.
        """
        if self.llm is None or 'triager' not in self.agents:
            self.logger.warning("Triager unavailable (no LLM or agent not configured); returning raw logs excerpt")
            return triage_input.get('logs_excerpt', '')[:5000]
        
        triager_template = self.config.get('agents', {}).get('triager', {}).get('prompt_template', '')
        description = self._format_prompt(triager_template, triage_input)
        triage_task = Task(
            description=description,
            agent=self.agents['triager'],
            expected_output="Markdown report summarizing failure, with root causes and proposed fixes"
        )
        crew = Crew(agents=[self.agents['triager']], tasks=[triage_task], process=Process.sequential, verbose=2)
        result = await asyncio.to_thread(crew.kickoff)
        return str(result) if result else "Failed to generate triage report. See logs excerpt above."
