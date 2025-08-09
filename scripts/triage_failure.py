"""
Triage failed GitHub Actions workflow runs by summarizing logs and creating an issue.

This script:
- Reads configuration from seed_instructions.yaml
- Aggregates and tails logs from the current directory (unzipped run logs)
- Uses the Triager agent (CrewAI) to produce a Markdown report
- Creates or updates a GitHub Issue with the summary and logs excerpt
"""
from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Any, Dict, List

import yaml

# Local imports
from agents.crew_manager import CrewManager
from agents.github_integration import GitHubIntegration
from utils.logger import setup_logger

logger = setup_logger(__name__)


def tail_lines(text: str, n: int) -> str:
    lines = text.splitlines()[-n:]
    return "\n".join(lines)


def collect_logs_excerpt(root: Path, tail: int) -> tuple[str, str]:
    """Collect *.txt logs under root, return (jobs_summary, excerpt_markdown)."""
    txt_files: List[Path] = sorted(root.rglob("*.txt"))
    if not txt_files:
        return ("No log files found.", "No logs available.")

    parts: List[str] = []
    job_lines: List[str] = []
    for f in txt_files:
        try:
            content = f.read_text(errors="ignore")
        except Exception:
            continue
        excerpt = tail_lines(content, tail)
        rel = f.relative_to(root)
        job_lines.append(f"- {rel}")
        parts.append(f"===== {rel} =====\n{excerpt}\n")
    return ("\n".join(job_lines), "\n".join(parts))


async def main_async(args: argparse.Namespace) -> None:
    # Load config
    with open(Path("seed_instructions.yaml"), "r") as f:
        config = yaml.safe_load(f)

    failure_cfg = (config.get("workflow", {}) or {}).get("failure_reporting", {}) or {}
    tail = int(args.tail_lines or failure_cfg.get("logs_tail_lines", 200))

    # Prepare logs
    root = Path(args.logs_root).resolve()
    jobs_summary, excerpt = collect_logs_excerpt(root, tail)

    # Initialize helpers
    crew = CrewManager(config, mode="triage")
    gh = GitHubIntegration(config)

    # Minimal repository context for the triager
    repo_context = {
        "structure": await gh.get_repository_structure(),
        "recent_changes": await gh.get_recent_commits(),
    }

    triage_input: Dict[str, Any] = {
        "workflow_name": args.workflow_name,
        "run_url": args.run_url,
        "git_ref": args.git_ref,
        "commit_sha": args.commit_sha,
        "failing_jobs_summary": jobs_summary,
        "logs_excerpt": excerpt[:60000],  # avoid overly large payloads
        "repository_context": repo_context,
        "tail_lines": tail,
    }

    # Generate report
    report_md = await crew.run_triage_report(triage_input)

    # Build issue content
    title = f"[CI Failure] {args.workflow_name} on {args.git_ref} @ {args.commit_sha[:7]}"
    body = (
        f"## CI Failure: {args.workflow_name}\n\n"
        f"- Run: {args.run_url}\n"
        f"- Ref: `{args.git_ref}`\n"
        f"- Commit: `{args.commit_sha}`\n\n"
        f"### Auto-Triage Summary\n\n{report_md}\n\n"
        f"<details><summary>Logs Excerpt (last {tail} lines per file)</summary>\n\n"
        f"````\n{excerpt[:120000]}\n````\n\n"
        f"</details>\n"
    )

    labels = failure_cfg.get("issue_labels", ["ci-failure", "triage"]) or []
    dedupe = (labels[0] if labels else None)

    # Create or update issue
    res = await gh.create_issue(title=title, body=body, labels=labels, dedupe_label=dedupe)
    if not res.get("success"):
        logger.error(f"Failed to create triage issue: {res}")
    else:
        logger.info(f"Triage issue ready: #{res.get('issue_number')}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Create CI failure triage issue from logs")
    p.add_argument("--workflow-name", required=True)
    p.add_argument("--run-url", required=True)
    p.add_argument("--git-ref", required=True)
    p.add_argument("--commit-sha", required=True)
    p.add_argument("--logs-root", default=".")
    p.add_argument("--tail-lines", type=int, default=None)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
