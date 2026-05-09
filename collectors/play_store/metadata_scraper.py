from google_play_scraper import app, search, reviews, Sort
import psycopg2
import time
import json

# Database connection
def get_connection():
    return psycopg2.connect('postgresql://admin:appweave123@localhost:5432/appweave')

# Save one app to database
def save_app(data, country):
    conn = get_connection()
    cursor = conn.cursor()
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
        conn.commit()
        print(f"Saved: {data.get('title')}")
    except Exception as e:
        print(f"Error saving {data.get('title')}: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

# Search and scrape apps by keyword
def scrape_by_keyword(keyword, country='in', limit=30):
    print(f"Searching: {keyword} in {country}...")
    try:
        results = search(
            keyword,
            lang='en',
            country=country,
            n_hits=limit
        )
        for result in results:
            try:
                app_data = app(
                    result['appId'],
                    lang='en',
                    country=country
                )
                save_app(app_data, country)
                time.sleep(0.2)
            except Exception as e:
                print(f"Error fetching {result['appId']}: {e}")
        print(f"Done: {keyword}")
    except Exception as e:
        print(f"Error searching {keyword}: {e}")

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
    print("All done!")