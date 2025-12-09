"""
Database models untuk Product Review Analyzer
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Review(db.Model):
    """
    Model untuk menyimpan review dan hasil analisisnya
    """
    __tablename__ = 'reviews'
    
    # Kolom database
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_name = db.Column(db.String(200), nullable=False)
    review_text = db.Column(db.Text, nullable=False)
    sentiment = db.Column(db.String(20), nullable=True)  # positive/negative/neutral
    sentiment_score = db.Column(db.Float, nullable=True)  # confidence score
    key_points = db.Column(db.Text, nullable=True)  # JSON string dari Gemini
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """
        Convert model to dictionary untuk JSON response
        """
        return {
            'id': self.id,
            'product_name': self.product_name,
            'review_text': self.review_text,
            'sentiment': self.sentiment,
            'sentiment_score': self.sentiment_score,
            'key_points': self.key_points,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f""