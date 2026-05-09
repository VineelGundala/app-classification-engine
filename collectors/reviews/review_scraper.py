from google_play_scraper import reviews, Sort
import psycopg2
import time
import json

def get_connection():
    return psycopg2.connect('postgresql://admin:appweave123@localhost:5432/appweave')

def save_review(package_name, country, review_data):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO app_reviews
            (package_name, store, country, review_text, rating, review_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            package_name,
            'play',
            country,
            review_data.get('content', '')[:2000],
            review_data.get('score'),
            str(review_data.get('at', ''))[:20]
        ))
        conn.commit()
    except Exception as e:
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
        for review in result:
            save_review(package_name, country, review)
        print(f"Saved {len(result)} reviews for {package_name}")
        time.sleep(0.5)
    except Exception as e:
        print(f"Error scraping reviews for {package_name}: {e}")

def scrape_all_reviews(country='in', reviews_per_app=100):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT package_name FROM app_metadata WHERE country=%s', (country,))
    apps = cursor.fetchall()
    cursor.close()
    conn.close()
    print(f"Scraping reviews for {len(apps)} apps...")
    for i, (package_name,) in enumerate(apps):
        print(f"[{i+1}/{len(apps)}] {package_name}")
        scrape_reviews(package_name, country, reviews_per_app)
    print("All reviews done!")

if __name__ == "__main__":
    scrape_all_reviews(country='in', reviews_per_app=50)
