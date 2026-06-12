# AppWeave — App Classification Engine

LLM-powered demographic classifier for mobile apps.

## Accuracy (10-app held-out eval)
- Gender accuracy : 100%
- Age accuracy    : 90%
- Income accuracy : 100%
- Tier accuracy   : 90%
- Model used      : GPT-4o-mini

## Current Status
- 98 Indian apps classified (gender, age, income, signal tier)
- Scaling to 1000 apps in shopping + finance + fitness categories
- See tests/eval.py for accuracy metrics

## Team
- Vineel Gundala — Full Stack

## Tech Stack
- Language  : Python 3.13
- Database  : PostgreSQL (Supabase cloud)
- LLM       : OpenAI GPT-4o-mini
- API       : FastAPI
- Dashboard : Streamlit
- Scraping  : google-play-scraper
- Hosting   : Streamlit Community Cloud

## Live Demo
Dashboard : https://app-classification-engine-dbzp2cdkc7ip6gvkqb4jvg.streamlit.app

## Quick Start
1. Clone the repo
   git clone https://github.com/VineelGundala/app-classification-engine

2. Create virtual environment
   python -m venv venv
   source venv/Scripts/activate

3. Install dependencies
   pip install -r requirements.txt

4. Set up environment variables
   cp .env.example .env
   Edit .env with your credentials

5. Start the database
   docker-compose up -d postgres

6. Start the API
   uvicorn api.main:app --reload

7. Start the dashboard
   streamlit run dashboard/app.py

## Architecture
- collectors/     — Play Store and review scrapers
- classification/ — LLM classification pipeline
- api/            — FastAPI REST API
- dashboard/      — Streamlit dashboard
- shared/         — Database models
- tests/          — Eval suite (eval_set.json + eval.py)