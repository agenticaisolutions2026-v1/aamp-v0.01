from pathlib import Path

# Project root (one level above scripts/)
ROOT = Path(__file__).resolve().parent.parent

folders = [
    "backend",
    "backend/agents",
    "backend/api",
    "backend/workflows",
    "backend/tools",
    "backend/prompts",
    "backend/services",
    "backend/database",
    "backend/models",
    "backend/schemas",
    "backend/config",
    "backend/utils",
    "backend/core",
    "backend/tests",

    "frontend",

    "docs",

    "docker",

    "scripts",

    ".github/workflows",
]

files = [
    ".env.example",
    "backend/main.py",
]

for folder in folders:
    path = ROOT / folder
    path.mkdir(parents=True, exist_ok=True)

    # Create __init__.py for Python packages
    if folder.startswith("backend"):
        init_file = path / "__init__.py"
        init_file.touch(exist_ok=True)

for file in files:
    path = ROOT / file
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)

print("Enterprise project structure created successfully!")