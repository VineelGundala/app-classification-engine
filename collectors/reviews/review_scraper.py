from google_play_scraper import reviews, Sort
import psycopg2
import time
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"])

def save_reviews(package_name, country, reviews_data):
    conn = get_connection()
    cursor = conn.cursor()
    saved = 0
    try:
        for review in reviews_data:
            try:
                cursor.execute("""
                    INSERT INTO app_reviews
                    (package_name, store, country, review_text, rating, review_date)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    package_name,
                    'play',
                    country,
                    review.get('content', '')[:2000],
                    review.get('score'),
                    str(review.get('at', ''))[:20]
                ))
                saved += 1
            except Exception as e:
                logger.error(f"Failed to save review for {package_name}: {e}")
        conn.commit()
        logger.info(f"Saved {saved} reviews for {package_name}")
    except Exception as e:
        logger.error(f"Batch save failed for {package_name}: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def scrape_reviews(package_name, country='in', count=100):
    try:
        result, _ = reviews(
            package_name,
            lang='en',
            country=country,
            sort=Sort.MOST_RELEVANT,
            count=count
        )
        save_reviews(package_name, country, result)
        time.sleep(0.5)
    except Exception as e:
        logger.error(f"Error scraping reviews for {package_name}: {e}")

def scrape_all_reviews(country='in', reviews_per_app=100):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT package_name FROM app_metadata WHERE country=%s',
        (country,)
    )
    apps = cursor.fetchall()
    cursor.close()
    conn.close()

    logger.info(f"Scraping reviews for {len(apps)} apps...")
    for i, (package_name,) in enumerate(apps):
        logger.info(f"[{i+1}/{len(apps)}] {package_name}")
        scrape_reviews(package_name, country, reviews_per_app)

    logger.info("All reviews done!")

if __name__ == "__main__":
    scrape_all_reviews(country='in', reviews_per_app=50)