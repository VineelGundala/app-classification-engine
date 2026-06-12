from google_play_scraper import app, search, Sort
import psycopg2
import time
import json
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"])

def save_apps(apps_data, country):
    conn = get_connection()
    cursor = conn.cursor()
    saved = 0
    try:
        for data in apps_data:
            try:
                cursor.execute("""
                    INSERT INTO app_metadata
                    (package_name, store, country, app_name, developer_name,
                     category, description, rating, rating_count, installs,
                     content_rating, icon_url, similar_apps)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (package_name, store, country) DO NOTHING
                """, (
                    data.get('appId'),
                    'play',
                    country,
                    data.get('title'),
                    data.get('developer'),
                    data.get('genre'),
                    data.get('description', '')[:5000],
                    data.get('score'),
                    data.get('ratings'),
                    data.get('installs'),
                    data.get('contentRating'),
                    data.get('icon'),
                    json.dumps(data.get('similarApps', []))
                ))
                saved += 1
            except Exception as e:
                logger.error(f"Failed to save app {data.get('title')}: {e}")
        conn.commit()
        logger.info(f"Saved {saved} apps for {country}")
    except Exception as e:
        logger.error(f"Batch save failed: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def scrape_by_keyword(keyword, country='in', limit=30):
    logger.info(f"Searching: {keyword} in {country}...")
    try:
        results = search(
            keyword,
            lang='en',
            country=country,
            n_hits=limit
        )
        apps_data = []
        for result in results:
            try:
                app_data = app(
                    result['appId'],
                    lang='en',
                    country=country
                )
                apps_data.append(app_data)
                time.sleep(0.2)
            except Exception as e:
                logger.error(f"Error fetching {result['appId']}: {e}")

        save_apps(apps_data, country)
        logger.info(f"Done: {keyword} - {len(apps_data)} apps")

    except Exception as e:
        logger.error(f"Error searching {keyword}: {e}")

if __name__ == "__main__":
    keywords = [
        'shopping',
        'food delivery',
        'social media',
        'fitness',
        'finance'
    ]
    for keyword in keywords:
        scrape_by_keyword(keyword, country='in', limit=20)
        time.sleep(2)
    logger.info("All done!")