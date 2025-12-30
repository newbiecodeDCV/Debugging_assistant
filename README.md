# Code Understanding & Debugging Assistant

🔧 An LLM-powered tool that reads your codebase, explains functions, detects bugs, and suggests improvements.

## Features

- **Code Explanation**: Understand any function or class in your codebase
- **Bug Detection**: Identify potential bugs and security issues
- **Refactoring Suggestions**: Get context-aware improvement recommendations
- **Test Generation**: Automatically generate unit tests
- **Docker Sandbox**: Safely execute code in isolated containers

## Tech Stack

- **LLM**: OpenAI GPT-4
- **Vector Store**: Chroma (local)
- **Framework**: LangChain Agents
- **API**: FastAPI
- **Sandbox**: Docker

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/code-assistant.git
cd code-assistant

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
# Edit .env with your API keys
```

## Quick Start

### CLI Usage

```bash
# Index a codebase
code-assistant index ./my_project

# Explain a function
code-assistant explain my_module.calculate_sum

# Debug a file
code-assistant debug ./my_file.py

# Generate tests
code-assistant generate-tests my_module.MyClass

# Interactive chat
code-assistant chat
```

### API Usage

```bash
# Start the API server
code-assistant serve

# Or directly with uvicorn
uvicorn code_assistant.api.main:app --reload
```

API Endpoints:
- `POST /api/index` - Index a codebase
- `POST /api/explain` - Explain code
- `POST /api/debug` - Detect bugs
- `POST /api/refactor` - Get refactoring suggestions
- `POST /api/generate-tests` - Generate tests
- `POST /api/chat` - Interactive chat

## Development

```bash
# Run tests
pytest

# Type checking
mypy src/code_assistant

# Linting
ruff check src/

# Format code
ruff format src/
```

## Project Structure

```
src/code_assistant/
├── config.py           # Settings management
├── models/             # Pydantic schemas
├── parsers/            # Code parsing (AST)
├── embeddings/         # Vector store operations
├── agents/             # LangChain agents & tools
├── services/           # Business logic
├── sandbox/            # Docker sandbox
├── api/                # FastAPI endpoints
└── cli/                # CLI interface
```

## License

MIT License
