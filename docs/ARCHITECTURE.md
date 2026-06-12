# AppWeave — Architecture Document

## System Overview

AppWeave is an end-to-end LLM-powered demographic classification engine
for mobile apps. It scrapes app data, classifies demographics using AI,
and serves results via API and dashboard.

## Architecture Diagram


┌─────────────────────────────────────────────────────┐

│                 DATA COLLECTION LAYER                │

├──────────────────────┬──────────────────────────────┤

│  Play Store Scraper  │      Review Scraper          │

│  (metadata_scraper)  │      (review_scraper)        │

└──────────┬───────────┴──────────────┬───────────────┘

│                          │

▼                          ▼

┌─────────────────────────────────────────────────────┐

│              PostgreSQL Database                     │

│   app_metadata | app_reviews | app_classifications  │

└─────────────────────────┬───────────────────────────┘

│

▼

┌─────────────────────────────────────────────────────┐

│           LLM CLASSIFICATION PIPELINE               │

│              (GPT-4o-mini via OpenAI)               │

│   Metadata Prompt + Review Analysis + Scoring       │

└─────────────────────────┬───────────────────────────┘

│

┌──────────────┴──────────────┐

▼                             ▼

┌──────────────────┐         ┌──────────────────────┐

│   FastAPI REST   │         │  Streamlit Dashboard │

│   api/main.py    │         │  dashboard/app.py    │

└──────────────────┘         └──────────────────────┘


## Database Schema

### app_metadata
Stores scraped app information from Google Play Store.
- package_name, store, country (unique key)
- app_name, developer_name, category, description
- rating, rating_count, installs, content_rating
- icon_url, similar_apps (JSONB)

### app_reviews
Stores user reviews for demographic signal analysis.
- package_name, store, country
- review_text, rating, review_date (TIMESTAMP)

### app_classifications
Stores LLM-generated demographic profiles.
- package_name, country (unique key)
- gender_label, gender_score, gender_confidence, gender_reasoning
- age_primary, age_primary_score, age_confidence
- income_label, income_score
- signal_tier (S/A/B/C)
- interests (JSONB)
- model_used, tokens_used

## Signal Tier System

| Tier | Gender Score | Meaning | Examples |
|------|-------------|---------|---------|
| S | >0.85 | Very strong signal | Nykaa (F), Dream11 (M) |
| A | 0.65-0.85 | Moderate signal | Meesho (F), ESPN (M) |
| B | 0.55-0.65 | Weak signal | Zomato, Swiggy |
| C | <=0.55 | No signal | WhatsApp, Google Pay |

## LLM Classification Pipeline

Two step process:
1. **Metadata Analysis** — app name, category, description signals
2. **Review Analysis** — user self-identification signals

Combined scoring:
- 50+ reviews → Reviews weighted 60%, metadata 40%
- No reviews → Metadata only, confidence capped at medium

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.13 |
| Database | PostgreSQL 15 (Docker local, Supabase cloud) |
| LLM | OpenAI GPT-4o-mini |
| API | FastAPI + Uvicorn |
| Dashboard | Streamlit |
| Scraping | google-play-scraper |
| Cloud DB | Supabase |
| Hosting | Streamlit Community Cloud |

## DB Access Pattern

All files use environment variables for DB connection:
```python
import os
from dotenv import load_dotenv
load_dotenv()

def get_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"])
```

Local development uses Docker PostgreSQL.
Production uses Supabase PostgreSQL.

## Eval Suite

Located in tests/:
- eval_set.json — 10 hand-labeled apps
- eval.py — accuracy measurement script

Current baseline (GPT-4o-mini):
- Gender: 100%
- Age: 90%
- Income: 100%
- Tier: 90%