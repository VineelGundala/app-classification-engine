from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import json
from typing import Optional

app = FastAPI(
    title="AppWeave Classification API",
    description="Demographic classification engine for mobile apps",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

def get_connection():
    return psycopg2.connect(
        'postgresql://admin:appweave123@localhost:5432/appweave'
    )

# Health check
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "AppWeave API is running"}

# Get single app classification
@app.get("/api/v1/apps/{package_name}")
def get_app(package_name: str, country: str = "in"):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT m.app_name, m.category, m.rating, m.installs,
                   c.gender_label, c.gender_score, c.gender_confidence,
                   c.gender_reasoning, c.age_primary, c.age_primary_score,
                   c.income_label, c.income_score, c.signal_tier,
                   c.interests, c.classified_at
            FROM app_metadata m
            JOIN app_classifications c ON m.package_name = c.package_name
            WHERE m.package_name=%s AND m.country=%s
        """, (package_name, country))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="App not found")
        return {
            "package_name": package_name,
            "app_name": row[0],
            "category": row[1],
            "rating": row[2],
            "installs": row[3],
            "gender": {
                "label": row[4],
                "score": row[5],
                "confidence": row[6],
                "reasoning": row[7]
            },
            "age": {
                "primary": row[8],
                "score": row[9]
            },
            "income": {
                "label": row[10],
                "score": row[11]
            },
            "signal_tier": row[12],
            "interests": row[13],
            "classified_at": str(row[14])
        }
    finally:
        cursor.close()
        conn.close()

# Search and filter apps
@app.get("/api/v1/apps")
def search_apps(
    gender: Optional[str] = None,
    tier: Optional[str] = None,
    category: Optional[str] = None,
    country: str = "in",
    limit: int = 20,
    offset: int = 0
):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT m.package_name, m.app_name, m.category,
                   m.rating, m.installs, c.gender_label,
                   c.signal_tier, c.age_primary, c.income_label
            FROM app_metadata m
            JOIN app_classifications c ON m.package_name = c.package_name
            WHERE m.country=%s
        """
        params = [country]

        if gender:
            query += " AND c.gender_label=%s"
            params.append(gender)
        if tier:
            query += " AND c.signal_tier=%s"
            params.append(tier)
        if category:
            query += " AND m.category ILIKE %s"
            params.append(f"%{category}%")

        query += " ORDER BY m.rating_count DESC NULLS LAST"
        query += f" LIMIT {limit} OFFSET {offset}"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return {
            "total": len(rows),
            "apps": [
                {
                    "package_name": row[0],
                    "app_name": row[1],
                    "category": row[2],
                    "rating": row[3],
                    "installs": row[4],
                    "gender": row[5],
                    "signal_tier": row[6],
                    "age": row[7],
                    "income": row[8]
                }
                for row in rows
            ]
        }
    finally:
        cursor.close()
        conn.close()

# Batch lookup
@app.post("/api/v1/apps/batch")
def batch_lookup(package_names: list[str], country: str = "in"):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT m.package_name, m.app_name, c.gender_label,
                   c.signal_tier, c.age_primary, c.income_label
            FROM app_metadata m
            JOIN app_classifications c ON m.package_name = c.package_name
            WHERE m.package_name = ANY(%s) AND m.country=%s
        """, (package_names, country))
        rows = cursor.fetchall()
        return {
            "results": [
                {
                    "package_name": row[0],
                    "app_name": row[1],
                    "gender": row[2],
                    "signal_tier": row[3],
                    "age": row[4],
                    "income": row[5]
                }
                for row in rows
            ]
        }
    finally:
        cursor.close()
        conn.close()

# Stats endpoint
@app.get("/api/v1/stats")
def get_stats(country: str = "in"):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT COUNT(*) FROM app_classifications WHERE country=%s",
            (country,)
        )
        total = cursor.fetchone()[0]

        cursor.execute("""
            SELECT signal_tier, COUNT(*)
            FROM app_classifications
            WHERE country=%s
            GROUP BY signal_tier
        """, (country,))
        tiers = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT gender_label, COUNT(*)
            FROM app_classifications
            WHERE country=%s
            GROUP BY gender_label
        """, (country,))
        genders = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT m.category, COUNT(*)
            FROM app_metadata m
            JOIN app_classifications c ON m.package_name = c.package_name
            WHERE m.country=%s
            GROUP BY m.category
            ORDER BY COUNT(*) DESC
        """, (country,))
        categories = {row[0]: row[1] for row in cursor.fetchall()}

        return {
            "total_classified": total,
            "tier_distribution": tiers,
            "gender_distribution": genders,
            "category_distribution": categories
        }
    finally:
        cursor.close()
        conn.close()

# Override endpoint
@app.post("/api/v1/apps/{package_name}/override")
def override_classification(
    package_name: str,
    gender: str,
    signal_tier: str,
    country: str = "in"
):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE app_classifications
            SET gender_label=%s, signal_tier=%s
            WHERE package_name=%s AND country=%s
        """, (gender, signal_tier, package_name, country))
        conn.commit()
        return {"message": "Override saved successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()