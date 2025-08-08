"""
GitHub integration utilities for AI agents.

This module provides utilities for AI agents to interact with GitHub APIs,
including repository operations, issue management, and pull request creation.
"""

import base64
import os
from typing import Any, Dict, List

import requests

from utils.logger import setup_logger


class GitHubIntegration:
    """
    Handles GitHub API interactions for the AI agent system.
    
    Provides methods for repository operations, branch management,
    file operations, and pull request workflows.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize GitHub integration with configuration."""
        self.logger = setup_logger(__name__)
        self.config = config
        self.token = os.getenv('GITHUB_TOKEN')
        self.base_url = "https://api.github.com"
        
        if not self.token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
            
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
        
    def _get_repo_info(self) -> tuple[str, str]:
        """Extract owner and repo from repository context."""
        # This would typically be passed in or configured
        # For now, extracting from current git context
        try:
            import subprocess
            result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                                  capture_output=True, text=True)
            url = result.stdout.strip()
            # Parse GitHub URL to get owner/repo
            if 'github.com' in url:
                parts = url.replace('.git', '').split('/')
                return parts[-2], parts[-1]
        except Exception as e:
            self.logger.warning(f"Could not extract repo info from git: {e}")
            
        # Fallback - these should be configured
        return "owner", "repo"
        
    async def get_repository_structure(self) -> Dict[str, Any]:
        """Get the repository structure for context."""
        owner, repo = self._get_repo_info()
        
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/git/trees/main?recursive=1"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                tree_data = response.json()
                return {
                    "tree": tree_data.get("tree", []),
                    "structure_summary": self._summarize_structure(tree_data.get("tree", []))
                }
            else:
                self.logger.error(f"Failed to get repository structure: {response.status_code}")
                return {"tree": [], "structure_summary": "Could not retrieve structure"}
                
        except Exception as e:
            self.logger.error(f"Error getting repository structure: {e}")
            return {"tree": [], "structure_summary": f"Error: {e}"}
            
    def _summarize_structure(self, tree: List[Dict[str, Any]]) -> str:
        """Create a summary of the repository structure."""
        folders = set()
        file_types = {}
        
        for item in tree:
            if item.get('type') == 'tree':
                folders.add(item.get('path', '').split('/')[0])
            elif item.get('type') == 'blob':
                path = item.get('path', '')
                if '.' in path:
                    ext = path.split('.')[-1]
                    file_types[ext] = file_types.get(ext, 0) + 1
                    
        summary = f"Repository has {len(folders)} main directories: {', '.join(sorted(folders))}\n"
        summary += f"File types: {', '.join([f'{ext}({count})' for ext, count in sorted(file_types.items())])}"
        
        return summary
        
    async def get_key_files(self) -> Dict[str, str]:
        """Get contents of key files for context."""
        key_files = ['README.md', 'requirements.txt', 'pyproject.toml', 'setup.py']
        owner, repo = self._get_repo_info()
        
        file_contents = {}
        
        for filename in key_files:
            try:
                url = f"{self.base_url}/repos/{owner}/{repo}/contents/{filename}"
                response = requests.get(url, headers=self.headers, timeout=30)
                
                if response.status_code == 200:
                    file_data = response.json()
                    if file_data.get('encoding') == 'base64':
                        content = base64.b64decode(file_data['content']).decode('utf-8')
                        file_contents[filename] = content[:2000]  # Truncate for context
                        
            except Exception as e:
                self.logger.warning(f"Could not read {filename}: {e}")
                
        return file_contents
        
    async def get_recent_commits(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent commits for context."""
        owner, repo = self._get_repo_info()
        
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/commits?per_page={count}"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                commits = response.json()
                return [
                    {
                        "sha": commit["sha"][:8],
                        "message": commit["commit"]["message"].split('\n')[0],
                        "author": commit["commit"]["author"]["name"],
                        "date": commit["commit"]["author"]["date"]
                    }
                    for commit in commits
                ]
            else:
                self.logger.error(f"Failed to get recent commits: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting recent commits: {e}")
            return []
            
    async def get_test_files(self) -> List[str]:
        """Get list of test files in the repository."""
        structure = await self.get_repository_structure()
        test_files = []
        
        for item in structure.get("tree", []):
            path = item.get("path", "")
            if "test" in path.lower() and path.endswith(".py"):
                test_files.append(path)
                
        return test_files
        
    async def get_documentation_files(self) -> List[str]:
        """Get list of documentation files."""
        structure = await self.get_repository_structure()
        doc_files = []
        
        for item in structure.get("tree", []):
            path = item.get("path", "")
            if any(doc_indicator in path.lower() for doc_indicator in ["doc", "readme", ".md"]):
                doc_files.append(path)
                
        return doc_files
        
    async def create_branch(self, branch_name: str, base_branch: str = "main") -> bool:
        """Create a new branch for the evolution."""
        owner, repo = self._get_repo_info()
        
        try:
            # Get the SHA of the base branch
            url = f"{self.base_url}/repos/{owner}/{repo}/git/refs/heads/{base_branch}"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code != 200:
                self.logger.error(f"Failed to get base branch SHA: {response.status_code}")
                return False
                
            base_sha = response.json()["object"]["sha"]
            
            # Create the new branch
            url = f"{self.base_url}/repos/{owner}/{repo}/git/refs"
            data = {
                "ref": f"refs/heads/{branch_name}",
                "sha": base_sha
            }
            
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            
            if response.status_code == 201:
                self.logger.info(f"Successfully created branch: {branch_name}")
                return True
            else:
                self.logger.error(f"Failed to create branch: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating branch: {e}")
            return False
            
    async def create_pull_request(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a pull request with the changes."""
        owner, repo = self._get_repo_info()
        
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
            response = requests.post(url, headers=self.headers, json=pr_data, timeout=30)
            
            if response.status_code == 201:
                pr_info = response.json()
                self.logger.info(f"Successfully created PR #{pr_info['number']}: {pr_info['title']}")
                return {
                    "success": True,
                    "pr_number": pr_info["number"],
                    "pr_url": pr_info["html_url"],
                    "pr_data": pr_info
                }
            else:
                self.logger.error(f"Failed to create PR: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            self.logger.error(f"Error creating pull request: {e}")
            return {
                "success": False,
                "error": str(e)
            }
            
    async def comment_on_issue(self, issue_number: int, comment: str) -> bool:
        """Comment on a GitHub issue."""
        owner, repo = self._get_repo_info()
        
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/comments"
            data = {"body": comment}
            
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            
            if response.status_code == 201:
                self.logger.info(f"Successfully commented on issue #{issue_number}")
                return True
            else:
                self.logger.error(f"Failed to comment on issue: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error commenting on issue: {e}")
            return False
            
    async def update_file(self, file_path: str, content: str, commit_message: str, branch: str) -> bool:
        """Update or create a file in the repository."""
        owner, repo = self._get_repo_info()
        
        try:
            # Check if file exists to get SHA for updates
            url = f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}?ref={branch}"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            file_sha = None
            if response.status_code == 200:
                file_sha = response.json().get("sha")
                
            # Update or create file
            url = f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}"
            data = {
                "message": commit_message,
                "content": base64.b64encode(content.encode()).decode(),
                "branch": branch
            }
            
            if file_sha:
                data["sha"] = file_sha
                
            response = requests.put(url, headers=self.headers, json=data, timeout=30)
            
            if response.status_code in [200, 201]:
                self.logger.info(f"Successfully updated file: {file_path}")
                return True
            else:
                self.logger.error(f"Failed to update file: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating file {file_path}: {e}")
            return False
