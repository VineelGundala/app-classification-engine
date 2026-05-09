import os
import json
import psycopg2
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv('GROQ_API_KEY'))

def get_connection():
    return psycopg2.connect('postgresql://admin:appweave123@localhost:5432/appweave')

def get_app_metadata(package_name, country='in'):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT app_name, category, description, content_rating
        FROM app_metadata
        WHERE package_name=%s AND country=%s
    """, (package_name, country))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return {
            'app_name': row[0],
            'category': row[1],
            'description': row[2],
            'content_rating': row[3]
        }
    return None

def get_app_reviews(package_name, country='in', limit=50):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT review_text FROM app_reviews
        WHERE package_name=%s AND country=%s
        LIMIT %s
    """, (package_name, country, limit))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [row[0] for row in rows if row[0]]

def classify_with_llm(app_name, category, description, content_rating, country, reviews):
    reviews_text = '\n'.join([f'- {r}' for r in reviews[:20]])

    prompt = f"""You are an expert mobile app demographic analyst specializing in the Indian market.
You have analyzed thousands of apps and understand exactly which apps skew male, female, or neutral.

APP DETAILS:
App Name: {app_name}
Category: {category}
Description: {description[:500]}
Content Rating: {content_rating}
Country: {country.upper()}

USER REVIEWS (real users talking about the app):
{reviews_text}

ANALYSIS INSTRUCTIONS:

Step 1 - Category Signal:
- Beauty, Fashion, Skincare, Jewellery -> Strong female signal
- Cricket, Fantasy Sports, Gaming, Gym -> Strong male signal
- Food Delivery, Groceries, Finance -> Usually neutral
- Fitness, Yoga -> Slight female signal
- Bikes, Cars, Tech -> Slight male signal

Step 2 - Review Signal (MOST IMPORTANT):
Look for explicit self-identification:
- "as a mom/wife/sister/girl/woman" -> female signal
- "as a dad/husband/brother/guy/man" -> male signal
- "I'm a student" -> age 18-22 signal
- "my kids" -> parent, age 28-45 signal
- Language style: casual slang -> younger, formal -> older

Step 3 - Description Signal:
- Does description say "for women/girls/ladies"? -> female
- Does it say "for men/boys/guys"? -> male
- Does it target professionals? -> 25-40, mid-high income
- Does it mention students? -> 18-22, low income

Step 4 - Income Signal:
- Premium brands (Nykaa, Myntra) -> mid-high income
- Value brands (Meesho, Club Factory) -> low-mid income
- Financial apps (Zerodha, ET Markets) -> mid-high income
- Loan apps -> low-mid income

KNOWN REFERENCE POINTS (use these to calibrate):
- Nykaa = female, 18-34, mid income, Tier S
- Dream11 = male, 18-35, mid income, Tier S
- WhatsApp = neutral, all ages, all income, Tier C
- Zomato = slight male, 18-34, mid income, Tier B
- Meesho = female, 18-34, low-mid income, Tier A

Respond ONLY in this exact JSON format, nothing else:
{{
    "gender": {{
        "label": "male or female or neutral",
        "score": 0.0,
        "confidence": "high or medium or low",
        "reasoning": "specific evidence from app data"
    }},
    "age": {{
        "primary_bucket": "13-17 or 18-34 or 35-54 or 55+",
        "score": 0.0,
        "confidence": "high or medium or low"
    }},
    "income": {{
        "label": "low or mid or high",
        "score": 0.0,
        "confidence": "high or medium or low"
    }},
    "signal_tier": "S or A or B or C",
    "interests": ["interest1", "interest2", "interest3"]
}}

Signal tier rules (be strict):
S = score > 0.85, very obvious demographic skew
A = score 0.65-0.85, clear but not overwhelming skew
B = score 0.55-0.65, slight skew with some evidence
C = score 0.45-0.55, no clear signal, used by everyone"""

    response = client.chat.completions.create(
        model='llama-3.1-8b-instant',
        messages=[{'role': 'user', 'content': prompt}],
        temperature=0.1
    )

    return response.choices[0].message.content

def save_classification(package_name, country, result, tokens_used):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO app_classifications
            (package_name, country, gender_label, gender_score, gender_confidence,
             gender_reasoning, age_primary, age_primary_score, age_confidence,
             income_label, income_score, signal_tier, interests, model_used, tokens_used)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (package_name, country) DO UPDATE SET
            gender_label=EXCLUDED.gender_label,
            gender_score=EXCLUDED.gender_score,
            signal_tier=EXCLUDED.signal_tier,
            classified_at=NOW()
        """, (
            package_name,
            country,
            result['gender']['label'],
            result['gender']['score'],
            result['gender']['confidence'],
            result['gender']['reasoning'],
            result['age']['primary_bucket'],
            result['age']['score'],
            result['age']['confidence'],
            result['income']['label'],
            result['income']['score'],
            result['signal_tier'],
            json.dumps(result['interests']),
            'llama-3.1-8b-instant',
            tokens_used
        ))
        conn.commit()
        print(f"Saved classification for {package_name}")
    except Exception as e:
        print(f"Error saving: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def classify_app(package_name, country='in'):
    metadata = get_app_metadata(package_name, country)
    if not metadata:
        print(f"No metadata found for {package_name}")
        return

    reviews = get_app_reviews(package_name, country)
    print(f"Classifying: {metadata['app_name']}...")

    try:
        raw_result = classify_with_llm(
            metadata['app_name'],
            metadata['category'],
            metadata['description'],
            metadata['content_rating'],
            country,
            reviews
        )

        clean = raw_result.strip()
        if '```json' in clean:
            clean = clean.split('```json')[1].split('```')[0]
        elif '```' in clean:
            clean = clean.split('```')[1].split('```')[0]

        result = json.loads(clean)
        save_classification(package_name, country, result, 0)
        print(f"Done: {metadata['app_name']} -> Gender: {result['gender']['label']} | Tier: {result['signal_tier']}")
        time.sleep(3)

    except Exception as e:
        print(f"Error classifying {package_name}: {e}")
        time.sleep(5)

def classify_all_apps(country='in'):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT package_name FROM app_metadata WHERE country=%s', (country,))
    apps = cursor.fetchall()
    cursor.close()
    conn.close()

    print(f"Classifying {len(apps)} apps...")
    for i, (package_name,) in enumerate(apps):
        print(f"[{i+1}/{len(apps)}]", end=' ')
        classify_app(package_name, country)
    print("All apps classified!")

def classify_failed_apps(country='in'):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT m.package_name FROM app_metadata m
        LEFT JOIN app_classifications c ON m.package_name = c.package_name
        WHERE c.package_name IS NULL AND m.country=%s
    ''', (country,))
    apps = cursor.fetchall()
    cursor.close()
    conn.close()

    print(f"Reclassifying {len(apps)} failed apps...")
    for i, (package_name,) in enumerate(apps):
        print(f"[{i+1}/{len(apps)}]", end=' ')
        classify_app(package_name, country)
    print("Done!")

if __name__ == "__main__":
    classify_all_apps(country='in')