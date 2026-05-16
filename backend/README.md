AI Database Copilot Backend
Overview

Deterministic AI SQL Copilot backend built using:

FastAPI
LangGraph
PostgreSQL / Supabase
SQLAlchemy
RBAC Authorization
Human Approval Workflow
Multi-Tenant Architecture
Features
Natural language → SQL
Deterministic workflow orchestration
SQL validation
SQL review & approval
Role-based access control
Tenant isolation
Query execution
Workflow checkpointing
Audit traces
Roles
Role	Permissions
analyst	SELECT
developer	SELECT, INSERT, UPDATE
admin	Full access
Tech Stack
FastAPI
LangGraph
SQLAlchemy
PostgreSQL
Supabase
sqlglot
Setup
Create Virtual Environment
python -m venv aisqlhelper
Activate

Windows:

aisqlhelper\Scripts\activate
Install Dependencies
pip install -r requirements.txt
Run Server
uvicorn app.main:app --reload
API Docs
http://127.0.0.1:8000/docs
Architecture
User Query
   ↓
Intent Extraction
   ↓
Clarification
   ↓
Query Planning
   ↓
RBAC Authorization
   ↓
SQL Validation
   ↓
Risk Classification
   ↓
Human Review
   ↓
Execution