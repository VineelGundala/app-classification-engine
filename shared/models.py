from sqlalchemy import Column, Integer, String, Float, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from shared.db import Base

class AppMetadata(Base):
    __tablename__ = "app_metadata"

    id = Column(Integer, primary_key=True)
    package_name = Column(String(255), nullable=False)
    store = Column(String(10), nullable=False)
    country = Column(String(5), nullable=False)
    app_name = Column(String(500))
    developer_name = Column(String(500))
    category = Column(String(255))
    description = Column(Text)
    rating = Column(Float)
    rating_count = Column(Integer)
    installs = Column(String(50))
    content_rating = Column(String(50))
    icon_url = Column(Text)
    similar_apps = Column(JSONB)
    scraped_at = Column(TIMESTAMP, server_default=func.now())

class AppReview(Base):
    __tablename__ = "app_reviews"

    id = Column(Integer, primary_key=True)
    package_name = Column(String(255), nullable=False)
    store = Column(String(10), nullable=False)
    country = Column(String(5), nullable=False)
    review_text = Column(Text)
    rating = Column(Integer)
    review_date = Column(String(20))
    scraped_at = Column(TIMESTAMP, server_default=func.now())

class AppClassification(Base):
    __tablename__ = "app_classifications"

    id = Column(Integer, primary_key=True)
    package_name = Column(String(255), nullable=False)
    country = Column(String(5), nullable=False)
    gender_label = Column(String(10))
    gender_score = Column(Float)
    gender_confidence = Column(String(10))
    gender_reasoning = Column(Text)
    age_primary = Column(String(10))
    age_primary_score = Column(Float)
    age_confidence = Column(String(10))
    income_label = Column(String(10))
    income_score = Column(Float)
    signal_tier = Column(String(1))
    interests = Column(JSONB)
    model_used = Column(String(50))
    tokens_used = Column(Integer)
    classified_at = Column(TIMESTAMP, server_default=func.now())
