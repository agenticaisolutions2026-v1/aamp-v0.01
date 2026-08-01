# AAMP Backend Setup & Basic API Development

## Project

**Agentic AI Marketing Platform (AAMP)**

This document explains the complete backend setup process, including project structure, FastAPI setup, API endpoints, environment configuration, and common issues encountered during development.

---

# Prerequisites

- Python 3.12+
- UV Package Manager

---

# Step 1 : Install Required Packages

or

```bash
uv pip install fastapi uvicorn pydantic-setting
```

Verify installation

```bash
uv pip show fastapi
```

Expected Output

```
Name: fastapi
Version: x.x.x
```

---

# Step 2 : Backend Folder Structure

```
backend/
│
├── api/
│   ├── __init__.py
│   ├── routes.py
│   ├── home.py
│   ├── health.py
│   └── version.py
│
├── config/
│   └── settings.py
│
├── core/
│   └── logging.py
│
├── database/
├── models/
├── schemas/
├── services/
├── agents/
├── prompts/
├── tests/
├── tools/
├── utils/
├── workflows/
│
├── __init__.py
└── main.py
```

---

# Step 3 : Create Root API

File

```
backend/api/home.py
```

Endpoint

```
GET /
```

Response

```json
{
    "message": "Welcome AAMP Project"
}
```

---

# Step 4 : Create Health API

File

```
backend/api/health.py
```

Endpoint

```
GET /health
```

Response

```json
{
    "status": "healthy"
}
```

---

# Step 5 : Create Version API

File

```
backend/api/version.py
```

Endpoint

```
GET /version
```

Response

```json
{
    "version": "0.0.1"
}
```

---

# Step 6 : Register API Routes

File

```
backend/api/routes.py
```

Register all API routers

- Home
- Health
- Version

---

# Step 7 : Configure FastAPI Application

File

```
backend/main.py
```

Initialize

- FastAPI Application
- Application Name
- Application Version
- Include Router

---

# Step 8 : Create Logging Module

File

```
backend/core/logging.py
```

Purpose

- Configure application logging
- Maintain centralized logging configuration
- Used across backend modules

---

# Step 9 : Create Configuration Module

File

```
backend/config/settings.py
```

backend/config/constants.py

Purpose

- Read application configuration
- Manage environment variables
- Centralize project settings

---

# Step 10 : Create Environment Example File

Create

```
.env.example
```

---

# Step 11 : Run FastAPI Server

From project root

```bash
uv run uvicorn backend.main:app --reload
```

Expected Output

```
INFO: Started server process
INFO: Waiting for application startup.
INFO: Application startup complete.
INFO: Uvicorn running on http://127.0.0.1:8000
```

---

# Step 12 : Test APIs

Swagger Documentation

```
http://127.0.0.1:8000/docs
```

Available APIs

| Method | Endpoint | Purpose             |
| ------ | -------- | ------------------- |
| GET    | /        | Welcome Message     |
| GET    | /health  | Health Check        |
| GET    | /version | Application Version |

---

# Step 13 : API Testing

### Root

```
GET /
```

Response

```json
{
    "message":"Welcome AAMP Project"
}
```

---

### Health

```
GET /health
```

Response

```json
{
    "status":"healthy"
}
```

---

### Version

```
GET /version
```

Response

```json
{
    "version":"0.0.1"
}
```

---

# Common Issues Encountered

## Issue 1

```
ModuleNotFoundError: No module named 'api'
```

### Cause

Incorrect import path.

```
from .api.routes import router
```

### Solution

Use package imports.

```
from backend.api.routes import router
```

or relative imports

```
from .health import router
```

---

## Issue 2

```
Import "fastapi" could not be resolved
```

### Cause

VS Code selected the wrong Python interpreter.

### Solution

Select project interpreter

```
.venv/Scripts/python.exe
```

Reload VS Code.

---

# Team Workflow

Repository

```
GitHub
│
├── .env.example
├── backend/
├── frontend/
```

Each developer

```
Clone Repository

↓

Copy

.env.example

↓

Create

.env

↓

Add local credentials

↓

Run project
```

---

# Commands Summary

Clone

```bash
git clone <repository-url>
```

Enter project

```bash
cd aamp-v0.01
```

Activate environment

```bash
.venv\Scripts\activate
```

Install packages

```bash
uv add fastapi uvicorn pydantic-settings
```

Run server

```bash
uv run uvicorn backend.main:app --reload
```

Open Swagger

```
http://127.0.0.1:8000/docs
```

---

# Completed Tasks

- Backend project setup
- FastAPI initialization
- Root endpoint
- Health endpoint
- Version endpoint
- API routing
- Logging module structure
- Configuration module structure
- Environment configuration
- Swagger documentation
- Basic backend validation
