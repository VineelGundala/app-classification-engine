# AppWeave — App Classification Engine

LLM-powered demographic classifier for 500K+ mobile apps.

## Team
- Person A — Data Collection (Play Store + Reviews)
- Person B — LLM Classification Pipeline
- Person C — REST API + Database
- Person D — Streamlit Dashboard

## Quick Start

# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/app-classification-engine
cd app-classification-engine

# 2. Copy and fill environment variables
cp .env.example .env

# 3. Start the database
docker-compose up -d postgres

# 4. Create virtual environment
python -m venv venv
source venv/bin/activate

# 5. Install dependencies
pip install -r requirements.txt

## Architecture
- collectors/     — scrapers for Play Store and App Store
- classification/ — LLM classification pipeline
- api/            — FastAPI REST API
- dashboard/      — Streamlit dashboard
- shared/         — shared database models and utilities
