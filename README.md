# AI Seed Repository - Self-Evolving Application Framework

A comprehensive boilerplate for building self-evolving applications powered by AI agents. This repository serves as the foundational skeleton for any application type (web API, CLI tool, service) where AI agents autonomously handle development tasks through GitHub issue-driven evolution.

## 🎯 Core Philosophy

- **80% Autonomy, 20% Human Oversight**: AI agents handle planning, coding, testing, documenting, and deploying, with human review for critical decisions
- **Issue-Driven Evolution**: Submit a GitHub issue → AI agents implement → Create PR → Human review → Deploy
- **Multi-Agent Collaboration**: Specialized agents work together using CrewAI orchestration
- **Continuous Self-Improvement**: Agents learn from outcomes and evolve their own capabilities

## 🏗️ Architecture

```
GitHub Issue → Workflow Trigger → Agent Orchestra → Code/Test/Doc → PR → Review → Deploy → Learn
```

### Agent Roles
- **Planner**: Analyzes issues and creates implementation roadmaps
- **Coder**: Generates and modifies application code
- **Tester**: Creates and runs comprehensive test suites
- **Documenter**: Maintains up-to-date documentation
- **Deployer**: Handles deployment and infrastructure
- **Evolver**: Reflects on outcomes and improves the system

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- GitHub repository with Actions enabled
- API keys for OpenAI or Anthropic

### Initial Setup

1. **Clone and Configure**:
```bash
git clone <your-repo-url>
cd ai-seed-repo
cp .env.example .env
# Edit .env with your API keys
```

2. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure GitHub Secrets**:
   - `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
   - `GITHUB_TOKEN` (for agent GitHub operations)

4. **Start the Base Application**:
```bash
python src/main.py
```

5. **Trigger Evolution**:
   - Create a GitHub issue using the provided template
   - Watch as agents automatically implement your request
   - Review and merge the generated PR

## 📁 Project Structure

```
ai-seed-repo/
├── .github/
│   ├── workflows/          # CI/CD automation
│   ├── ISSUE_TEMPLATE/     # Standardized evolution requests
│   └── copilot-instructions.md
├── agents/                 # AI agent implementations
├── src/                    # Evolvable application code
├── tests/                  # Automated test suites
├── docs/                   # Auto-generated documentation
├── config/                 # System configurations
└── seed_instructions.yaml  # AI agent prompts and rules
```

## 🧠 How It Works

1. **Submit an Issue**: Use the GitHub issue template to describe desired functionality
2. **Automatic Planning**: Planner agent breaks down the request into actionable tasks
3. **Implementation**: Coder agent generates code following project patterns
4. **Quality Assurance**: Tester agent creates comprehensive tests
5. **Documentation**: Documenter agent updates all relevant documentation
6. **Review Process**: Human review of the generated PR
7. **Deployment**: Automatic deployment upon PR merge
8. **Learning**: Evolver agent analyzes outcomes for system improvement

## 🔧 Configuration

Key configuration files:
- `seed_instructions.yaml`: Agent prompts and behavioral rules
- `config/agents.yaml`: Agent-specific configurations
- `config/llm.yaml`: LLM provider settings
- `.env`: Environment variables and API keys

## 📖 Documentation

Documentation is automatically generated and deployed:
- **API Docs**: Auto-generated from docstrings
- **Architecture**: System design and patterns
- **Agent Guides**: How each agent operates
- **Evolution Log**: History of autonomous improvements

Visit the [documentation site](https://your-username.github.io/ai-seed-repo) for comprehensive guides.

## 🛡️ Safety & Best Practices

- **Code Quality**: Enforced PEP8, type hints, security scans
- **Human Oversight**: All changes require PR review
- **Rollback Capability**: Easy reversion of problematic changes
- **Reflection Loops**: Agents continuously improve their performance
- **A/B Testing**: Framework for testing improvements

## 🔮 Future Evolution

This repository is designed to evolve. The Evolver agent will continuously:
- Improve agent prompts based on outcomes
- Add new capabilities as needed
- Optimize workflows and processes
- Integrate new tools and technologies

## 🤝 Contributing

While this repo evolves autonomously, human contributions are welcome:
1. Submit evolution requests via GitHub issues
2. Review and provide feedback on agent-generated PRs
3. Contribute to the seed instructions and configurations

## 📄 License

MIT License - See LICENSE file for details.

---

*Built with ❤️ by AI agents, guided by human wisdom*
