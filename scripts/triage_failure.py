"""
Triage failed GitHub Actions workflow runs by summarizing logs and creating an issue.

This script:
- Reads configuration from seed_instructions.yaml
- Aggregates and tails logs from the current directory (unzipped run logs)
- Uses the Triager agent (CrewAI) to produce a Markdown report when LLM keys are set
- Otherwise falls back to a heuristic summary
- Creates or updates a GitHub Issue with the summary and logs excerpt
"""
from __future__ import annotations

import argparse
import asyncio
import os

# Ensure repository root is on sys.path when running this file directly
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Local imports (GitHubIntegration is lightweight)
from agents.github_integration import GitHubIntegration  # noqa: E402
from utils.logger import setup_logger  # noqa: E402

logger = setup_logger(__name__)


def tail_lines(text: str, n: int) -> str:
    lines = text.splitlines()[-n:]
    return "\n".join(lines)


def collect_logs_excerpt(root: Path, tail: int) -> tuple[str, str]:
    """Collect *.txt and *.log logs under root, return (jobs_summary, excerpt_markdown)."""
    if not root.exists():
        return ("Logs root not found.", "No logs available.")

    # Include both .txt (per-step logs) and .log files
    txt_files: List[Path] = sorted(list(root.rglob("*.txt")) + list(root.rglob("*.log")))
    if not txt_files:
        return ("No log files found.", "No logs available.")

    parts: List[str] = []
    job_lines: List[str] = []
    max_per_file = 2_000_000  # 2MB safeguard to avoid huge payloads
    for f in txt_files:
        try:
            content = f.read_text(errors="ignore")
        except Exception:
            continue
        if len(content) > max_per_file:
            content = content[-max_per_file:]
        excerpt = tail_lines(content, tail)
        rel = f.relative_to(root)
        job_lines.append(f"- {rel}")
        parts.append(f"===== {rel} =====\n{excerpt}\n")
    return ("\n".join(job_lines), "\n".join(parts))


def build_logs_details_markdown(root: Path, tail: int, max_files: int = 25) -> str:
    """Return a Markdown string with per-file <details> blocks containing the tail of each log.

    This improves rendering in GitHub Issues versus one giant fenced block.
    """
    if not root.exists():
        return "No logs directory found."

    def _sanitize(md: str) -> str:
        # Prevent accidental closing of fenced blocks inside logs
        return md.replace("```", "``\`")

    files: List[Path] = sorted(list(root.rglob("*.txt")) + list(root.rglob("*.log")))
    if not files:
        # As a fallback, show any files present (may help diagnose unzip issues)
        others = sorted([p for p in root.rglob("*") if p.is_file()])
        if not others:
            return "No log files available."
        listing = "\n".join([f"- {p.relative_to(root)}" for p in others[:50]])
        more = "" if len(others) <= 50 else f"\n... and {len(others) - 50} more files"
        return f"No *.txt/*.log files found. Directory listing sample:\n{listing}{more}"

    parts: List[str] = []
    shown = 0
    max_per_file = 2_000_000
    for f in files:
        if shown >= max_files:
            break
        try:
            content = f.read_text(errors="ignore")
        except Exception:
            continue
        if len(content) > max_per_file:
            content = content[-max_per_file:]
        excerpt = tail_lines(content, tail)
        excerpt = _sanitize(excerpt)
        rel = f.relative_to(root)
        parts.append(
            (
                f"<details><summary>{rel}</summary>\n\n"
                f"```text\n{excerpt}\n```\n\n"
                f"</details>\n"
            )
        )
        shown += 1

    if shown < len(files):
        parts.append(f"\n<sub>Showing {shown} of {len(files)} files (last {tail} lines each).</sub>")

    return "\n".join(parts)


def simple_summary(workflow_name: str, jobs_summary: str, excerpt: str, tail: int) -> str:
    """Produce a basic Markdown summary without LLMs."""
    hint = "Potential network or dependency issue" if "pip install" in excerpt or "Collecting" in excerpt else "Check failing step"
    return (
        f"### Auto-Triage Summary (fallback)\n\n"
        f"Workflow '{workflow_name}' failed.\n\n"
        f"Jobs/Logs files:\n{jobs_summary}\n\n"
        f"Likely area: {hint}.\n\n"
        f"Actions:\n"
        f"1. Inspect the first failing step in the run.\n"
        f"2. Re-run failed jobs with increased verbosity.\n"
        f"3. If dependency-related, try pinning the minimal conflicting version.\n"
        f"\n(Logs excerpt below shows last {tail} lines per file.)"
    )


async def main_async(args: argparse.Namespace) -> None:
    # Load config
    with open(Path("seed_instructions.yaml"), "r") as f:
        config = yaml.safe_load(f)

    failure_cfg = (config.get("workflow", {}) or {}).get("failure_reporting", {}) or {}
    tail = int(args.tail_lines or failure_cfg.get("logs_tail_lines", 200))

    # Prepare logs
    root = Path(args.logs_root).resolve()
    jobs_summary, excerpt = collect_logs_excerpt(root, tail)
    logs_details_md = build_logs_details_markdown(root, tail)

    # Initialize helpers
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

    # Decide whether to use LLMs
    have_llm = bool(os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))
    if have_llm:
        try:
            from agents.crew_manager import (
                CrewManager,  # lazy import to avoid heavy deps otherwise
            )

            crew = CrewManager(config, mode="triage")
            report_md = await crew.run_triage_report(triage_input)
        except Exception as e:
            logger.warning(f"Triager unavailable, falling back to simple summary: {e}")
            report_md = simple_summary(args.workflow_name, jobs_summary, excerpt, tail)
    else:
        report_md = simple_summary(args.workflow_name, jobs_summary, excerpt, tail)

    # Build issue content
    title = f"[CI Failure] {args.workflow_name} on {args.git_ref} @ {args.commit_sha[:7]}"
    files_scanned_md = (f"\n**Files scanned:**\n\n{jobs_summary}\n\n" if jobs_summary else "")
    body = (
        f"## CI Failure: {args.workflow_name}\n\n"
        f"- Run: {args.run_url}\n"
        f"- Ref: `{args.git_ref}`\n"
        f"- Commit: `{args.commit_sha}`\n\n"
        f"{report_md}\n"
        f"{files_scanned_md}"
        f"<details><summary>Logs Excerpts (last {tail} lines per file)</summary>\n\n"
        f"{logs_details_md}\n\n"
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
