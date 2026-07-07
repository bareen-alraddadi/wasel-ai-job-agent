# WASEL – AI Job Agent

> **Team Project**

WASEL is an AI-powered career assistant designed to help job seekers analyze their CVs, discover relevant opportunities, identify skill gaps, improve application materials, and receive personalized career guidance.

## Overview

WASEL combines multiple AI agents through a LangGraph orchestration workflow to support users throughout their job-search journey.

The platform helps users:

- Analyze uploaded CVs
- Match candidates with relevant jobs
- Identify missing skills
- Recommend learning resources
- Improve CV quality
- Generate tailored cover letters
- Practice interview questions
- Receive AI-powered career guidance

## Key Features

### Resume Analysis
- Extracts skills, experience, education, and projects from uploaded CVs
- Generates structured candidate profiles
- Provides CV improvement suggestions

### Job Matching
- Matches candidates with job descriptions or relevant job opportunities
- Calculates compatibility scores
- Highlights matched and missing skills

### Skill Gap Analysis
- Identifies missing skills and competencies
- Provides personalized learning recommendations
- Builds a career-development roadmap

### AI Career Assistant
- Answers career-related questions
- Supports CV improvement and interview preparation
- Uses user context and previous analyses for more relevant guidance

### Cover Letter Generation
- Generates tailored cover letters based on the CV and job description

## System Architecture

```text
React Frontend
      │
      ▼
FastAPI Backend
      │
      ▼
LangGraph Orchestrator
      │
      ├── Resume Agent
      ├── Job Agent
      ├── Gap Analysis Agent
      ├── Cover Letter Agent
      ├── CV Improvement Agent
      └── Chat Agent
      │
      ├── OpenAI
      ├── Qdrant Vector Database
      └── Supabase Database
```

## Tech Stack

- **Frontend:** React, TypeScript, Vite, Tailwind CSS
- **Backend:** Python, FastAPI, Pydantic, Uvicorn
- **AI & Agents:** OpenAI, LangChain, LangGraph
- **Vector Search:** Qdrant
- **Database & Storage:** Supabase
- **Development Tools:** Git, GitHub, Docker

## Project Structure

```text
02_src/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   ├── api/
│   │   ├── core/
│   │   ├── memory/
│   │   ├── models/
│   │   ├── rag/
│   │   └── tools/
│   ├── scripts/
│   └── requirements.txt
│
└── frontend/
    ├── src/
    ├── package.json
    └── vite.config.ts

03_asset/
└── Project assets and visual materials
```

## My Contribution

Contributed to the development, testing, documentation, and final presentation of the project as part of a collaborative team.

## Team Project

This repository represents a collaborative team project. Contributions were completed jointly across system design, implementation, testing, documentation, and presentation.

## Running the Project

### Backend

```bash
cd 02_src/backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd 02_src/frontend
npm install
npm run dev
```

## Important Note

This repository does not include private API keys, `.env` files, or production credentials. Create your own environment variables before running the application.
