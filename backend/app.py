"""
Flask Backend API untuk Product Review Analyzer
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from models import db, Review
from config import config
import requests
import google.generativeai as genai
import os
import json


def create_app(config_name='development'):
    """
    Factory function untuk create Flask app
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    CORS(app)  # Enable CORS untuk React frontend
    db.init_app(app)
    
    # Configure Gemini
    genai.configure(api_key=app.config['GEMINI_API_KEY'])
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app


app = create_app()


def analyze_sentiment_huggingface(text):
    """
    Analyze sentiment menggunakan Hugging Face API
    Model alternatif yang lebih stabil dan cepat
    """
    # Gunakan model yang lebih stabil dan jarang overload
    API_URL = "https://api-inference.huggingface.co/models/cardiffnlp/twitter-roberta-base-sentiment-latest"
    headers = {"Authorization": f"Bearer {app.config['HUGGINGFACE_API_KEY']}"}
    
    # Retry mechanism
    max_retries = 3
    retry_delay = 3  # seconds
    
    for attempt in range(max_retries):
        try:
            print(f"Attempting sentiment analysis (attempt {attempt + 1}/{max_retries})...")
            
            response = requests.post(
                API_URL, 
                headers=headers, 
                json={"inputs": text},
                timeout=30
            )
            
            # Check status
            if response.status_code == 503:
                print(f"Model loading... waiting {retry_delay}s")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    continue
            
            # Check for rate limit
            if response.status_code == 429:
                print("Rate limited, waiting...")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay * 2)
                    continue
            
            response.raise_for_status()
            result = response.json()
            
            print(f"HuggingFace response: {result}")
            
            # Format result for cardiffnlp model
            if isinstance(result, list) and len(result) > 0:
                # Ambil prediction dengan score tertinggi
                prediction = max(result[0], key=lambda x: x['score'])
                
                # Map label ke sentiment (cardiffnlp format)
                label = prediction['label'].lower()
                
                if 'positive' in label or label == 'label_2':
                    sentiment = 'positive'
                elif 'negative' in label or label == 'label_0':
                    sentiment = 'negative'
                else:  # neutral atau label_1
                    sentiment = 'neutral'
                
                score = prediction['score']
                
                print(f"Sentiment result: {sentiment} ({score})")
                
                return {
                    'sentiment': sentiment,
                    'score': round(score, 4)
                }
            else:
                print("Unexpected response format")
                return {
                    'sentiment': 'neutral',
                    'score': 0.5
                }
                
        except requests.exceptions.Timeout:
            print(f"Timeout on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                import time
                time.sleep(retry_delay)
            else:
                # Fallback: analisis sederhana berbasis keyword
                return analyze_sentiment_fallback(text)
            
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(retry_delay)
            else:
                # Fallback
                return analyze_sentiment_fallback(text)
    
    # Final fallback
    return analyze_sentiment_fallback(text)


def analyze_sentiment_fallback(text):
    """
    Fallback sentiment analysis menggunakan keyword-based
    Digunakan jika Hugging Face API gagal
    """
    print("Using fallback sentiment analysis...")
    
    text_lower = text.lower()
    
    # Positive keywords
    positive_words = [
        'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
        'love', 'perfect', 'best', 'awesome', 'outstanding', 'brilliant',
        'superb', 'impressive', 'beautiful', 'nice', 'happy', 'satisfied',
        'recommend', 'quality', 'fast', 'easy', 'helpful', 'worth'
    ]
    
    # Negative keywords
    negative_words = [
        'bad', 'terrible', 'awful', 'horrible', 'poor', 'worst',
        'hate', 'disappointing', 'disappointed', 'waste', 'useless',
        'broken', 'defective', 'slow', 'difficult', 'complicated',
        'expensive', 'overpriced', 'problem', 'issue', 'fail', 'failed'
    ]
    
    # Count matches
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    # Determine sentiment
    if positive_count > negative_count:
        sentiment = 'positive'
        score = min(0.6 + (positive_count * 0.1), 0.95)
    elif negative_count > positive_count:
        sentiment = 'negative'
        score = min(0.6 + (negative_count * 0.1), 0.95)
    else:
        sentiment = 'neutral'
        score = 0.5
    
    print(f"Fallback result: {sentiment} ({score}) - pos:{positive_count} neg:{negative_count}")
    
    return {
        'sentiment': sentiment,
        'score': round(score, 4)
    }

def extract_key_points_gemini(text):
    """
    Extract key points dari review menggunakan Google Gemini
    
    Args:
        text (str): Review text
        
    Returns:
        str: Key points dalam format JSON string
    """
    try:
        # Initialize Gemini model - UPDATE: gunakan gemini-1.5-flash
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        # Prompt untuk extract key points
        prompt = f"""
        Analyze this product review and extract the key points.
        Provide the output as a JSON array of strings, where each string is a key point.
        Focus on important aspects like quality, price, features, pros, and cons.
        Keep each point concise (max 15 words).
        
        Review: {text}
        
        Return ONLY the JSON array, no other text.
        Example format: ["Good quality", "Fast delivery", "Expensive price"]
        """
        
        # Generate response
        response = model.generate_content(prompt)
        
        # Extract text dari response
        key_points_text = response.text.strip()
        
        # Remove markdown code blocks jika ada
        if key_points_text.startswith('```'):
            key_points_text = key_points_text.split('```')[1]
            if key_points_text.startswith('json'):
                key_points_text = key_points_text[4:]
        
        key_points_text = key_points_text.strip()
        
        # Validate JSON
        try:
            key_points_array = json.loads(key_points_text)
            if isinstance(key_points_array, list):
                return json.dumps(key_points_array)
            else:
                return json.dumps([key_points_text])
        except json.JSONDecodeError:
            # Jika bukan valid JSON, wrap sebagai single item
            return json.dumps([key_points_text])
            
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return json.dumps([f"Error extracting key points: {str(e)}"])


# ===========================
# API ENDPOINTS
# ===========================

@app.route('/api/analyze-review', methods=['POST'])
def analyze_review():
    """
    Endpoint untuk analyze review baru
    
    Request Body:
    {
        "product_name": "iPhone 15 Pro",
        "review_text": "Great phone with amazing camera..."
    }
    
    Response:
    {
        "success": true,
        "data": {
            "id": 1,
            "product_name": "iPhone 15 Pro",
            "review_text": "Great phone...",
            "sentiment": "positive",
            "sentiment_score": 0.9876,
            "key_points": ["Great camera", "Fast performance"],
            "created_at": "2024-12-08T..."
        }
    }
    """
    try:
        # Get request data
        data = request.get_json()
        
        # Validation
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        product_name = data.get('product_name', '').strip()
        review_text = data.get('review_text', '').strip()
        
        if not product_name:
            return jsonify({
                'success': False,
                'error': 'Product name is required'
            }), 400
        
        if not review_text:
            return jsonify({
                'success': False,
                'error': 'Review text is required'
            }), 400
        
        if len(review_text) < 10:
            return jsonify({
                'success': False,
                'error': 'Review text too short (minimum 10 characters)'
            }), 400
        
        # Analyze sentiment dengan Hugging Face
        sentiment_result = analyze_sentiment_huggingface(review_text)
        
        # Extract key points dengan Gemini
        key_points_json = extract_key_points_gemini(review_text)
        
        # Create new review object
        new_review = Review(
            product_name=product_name,
            review_text=review_text,
            sentiment=sentiment_result.get('sentiment', 'neutral'),
            sentiment_score=sentiment_result.get('score', 0.0),
            key_points=key_points_json
        )
        
        # Save to database
        db.session.add(new_review)
        db.session.commit()
        
        # Prepare response
        review_dict = new_review.to_dict()
        
        # Parse key_points dari JSON string ke array
        try:
            review_dict['key_points'] = json.loads(review_dict['key_points'])
        except:
            review_dict['key_points'] = []
        
        return jsonify({
            'success': True,
            'message': 'Review analyzed successfully',
            'data': review_dict
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in analyze_review: {e}")
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500


@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    """
    Endpoint untuk get all reviews
    
    Query Parameters (optional):
    - limit: jumlah review yang diambil (default: 50)
    - sentiment: filter by sentiment (positive/negative/neutral)
    
    Response:
    {
        "success": true,
        "count": 10,
        "data": [...]
    }
    """
    try:
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        sentiment_filter = request.args.get('sentiment', None)
        
        # Query database
        query = Review.query.order_by(Review.created_at.desc())
        
        # Apply sentiment filter if provided
        if sentiment_filter:
            query = query.filter(Review.sentiment == sentiment_filter.lower())
        
        # Apply limit
        reviews = query.limit(limit).all()
        
        # Convert to dict
        reviews_data = []
        for review in reviews:
            review_dict = review.to_dict()
            
            # Parse key_points dari JSON string ke array
            try:
                review_dict['key_points'] = json.loads(review_dict['key_points'])
            except:
                review_dict['key_points'] = []
            
            reviews_data.append(review_dict)
        
        return jsonify({
            'success': True,
            'count': len(reviews_data),
            'data': reviews_data
        }), 200
        
    except Exception as e:
        print(f"Error in get_reviews: {e}")
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        'success': True,
        'message': 'API is running',
        'database': 'connected' if db.engine else 'disconnected'
    }), 200


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)