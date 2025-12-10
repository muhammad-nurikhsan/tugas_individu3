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
from deep_translator import GoogleTranslator
from langdetect import detect, LangDetectException


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


def detect_and_translate(text):
    """
    Deteksi bahasa dan translate ke English jika bukan English
    Menggunakan deep-translator (lebih stabil)
    
    Args:
        text (str): Text yang akan dideteksi dan ditranslate
        
    Returns:
        dict: {
            'original_text': str,
            'translated_text': str,
            'original_language': str,
            'is_translated': bool
        }
    """
    try:
        print("\n" + "="*50)
        print("🌐 Language Detection & Translation")
        print(f"Original text: {text[:100]}...")
        
        # Detect language
        try:
            detected_lang = detect(text)
            print(f"Detected language: {detected_lang}")
        except LangDetectException:
            print("⚠️ Could not detect language, assuming English")
            detected_lang = 'en'
        
        # Jika bukan English, translate
        if detected_lang != 'en':
            print(f"📝 Translating from {detected_lang} to English...")
            
            try:
                # Use deep-translator
                translated_text = GoogleTranslator(source=detected_lang, target='en').translate(text)
                
                print(f"✅ Translation successful!")
                print(f"Translated text: {translated_text[:100]}...")
                print("="*50 + "\n")
                
                return {
                    'original_text': text,
                    'translated_text': translated_text,
                    'original_language': detected_lang,
                    'is_translated': True
                }
            except Exception as e:
                print(f"⚠️ Translation failed: {e}")
                print("Using original text...")
                print("="*50 + "\n")
                
                return {
                    'original_text': text,
                    'translated_text': text,
                    'original_language': detected_lang,
                    'is_translated': False
                }
        else:
            print("✅ Text is already in English, no translation needed")
            print("="*50 + "\n")
            
            return {
                'original_text': text,
                'translated_text': text,
                'original_language': 'en',
                'is_translated': False
            }
            
    except Exception as e:
        print(f"❌ Error in language detection: {e}")
        print("Using original text as fallback...")
        print("="*50 + "\n")
        
        return {
            'original_text': text,
            'translated_text': text,
            'original_language': 'unknown',
            'is_translated': False
        }


def analyze_sentiment_huggingface(text):
    """
    Analyze sentiment menggunakan Hugging Face API
    Menggunakan model yang lebih akurat untuk sentiment analysis
    """
    # Model yang lebih akurat untuk sentiment
    API_URL = "https://api-inference.huggingface.co/models/cardiffnlp/twitter-roberta-base-sentiment-latest"
    headers = {"Authorization": f"Bearer {app.config['HUGGINGFACE_API_KEY']}"}
    
    max_retries = 3
    retry_delay = 3
    
    for attempt in range(max_retries):
        try:
            print(f"\n{'='*50}")
            print(f"Analyzing sentiment (attempt {attempt + 1}/{max_retries})")
            print(f"Text: {text[:100]}...")
            
            response = requests.post(
                API_URL, 
                headers=headers, 
                json={"inputs": text},
                timeout=30
            )
            
            if response.status_code == 503:
                print(f"⚠️ Model loading... waiting {retry_delay}s")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    continue
            
            if response.status_code == 429:
                print("⚠️ Rate limited, waiting...")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay * 2)
                    continue
            
            response.raise_for_status()
            result = response.json()
            
            print(f"HuggingFace raw response: {result}")
            
            if isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
                # Ambil semua predictions
                predictions = result[0]
                
                # Print semua scores untuk debugging
                for pred in predictions:
                    print(f"  {pred['label']}: {pred['score']:.4f}")
                
                # Cari score tertinggi
                best_prediction = max(predictions, key=lambda x: x['score'])
                label = best_prediction['label'].lower()
                score = best_prediction['score']
                
                # Map label ke sentiment
                # cardiffnlp model format: negative, neutral, positive
                if 'positive' in label or label == 'label_2':
                    sentiment = 'positive'
                elif 'negative' in label or label == 'label_0':
                    sentiment = 'negative'
                else:  # neutral atau label_1
                    sentiment = 'neutral'
                
                print(f"✅ Final result: {sentiment} ({score:.4f})")
                print(f"{'='*50}\n")
                
                return {
                    'sentiment': sentiment,
                    'score': round(score, 4)
                }
            else:
                print("⚠️ Unexpected response format, using fallback")
                return analyze_sentiment_fallback(text)
                
        except requests.exceptions.Timeout:
            print(f"⚠️ Timeout on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                import time
                time.sleep(retry_delay)
            else:
                return analyze_sentiment_fallback(text)
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error: {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(retry_delay)
            else:
                return analyze_sentiment_fallback(text)
    
    return analyze_sentiment_fallback(text)


def analyze_sentiment_fallback(text):
    """
    Fallback sentiment analysis menggunakan keyword-based
    Versi yang lebih akurat dengan weighted scoring
    """
    print("\n" + "="*50)
    print("🔄 Using FALLBACK sentiment analysis...")
    
    text_lower = text.lower()
    
    # Positive keywords dengan weight
    positive_keywords = {
        # Very strong positive (weight 3)
        'excellent': 3, 'outstanding': 3, 'amazing': 3, 'perfect': 3, 
        'fantastic': 3, 'wonderful': 3, 'brilliant': 3, 'superb': 3,
        'exceptional': 3, 'incredible': 3, 'awesome': 3,
        
        # Strong positive (weight 2)
        'great': 2, 'good': 2, 'best': 2, 'love': 2, 'recommend': 2,
        'impressive': 2, 'beautiful': 2, 'satisfied': 2, 'happy': 2,
        'quality': 2, 'fast': 2, 'easy': 2, 'helpful': 2,
        
        # Moderate positive (weight 1)
        'nice': 1, 'okay': 1, 'decent': 1, 'fine': 1, 'solid': 1,
        'worth': 1, 'reliable': 1, 'comfortable': 1
    }
    
    # Negative keywords dengan weight
    negative_keywords = {
        # Very strong negative (weight 3)
        'terrible': 3, 'awful': 3, 'horrible': 3, 'worst': 3,
        'disgusting': 3, 'pathetic': 3, 'useless': 3, 'garbage': 3,
        'trash': 3, 'hate': 3, 'scam': 3, 'fraud': 3,
        
        # Strong negative (weight 2)
        'bad': 2, 'poor': 2, 'disappointing': 2, 'disappointed': 2,
        'waste': 2, 'broken': 2, 'defective': 2, 'fail': 2,
        'failed': 2, 'problem': 2, 'issue': 2, 'unfortunately': 2,
        
        # Moderate negative (weight 1)
        'slow': 1, 'difficult': 1, 'complicated': 1, 'expensive': 1,
        'overpriced': 1, 'not good': 1, 'not great': 1, 'could be better': 1
    }
    
    # Negation words yang membalik sentiment
    negations = ['not', 'no', 'never', 'nothing', 'neither', 'nobody', 
                 'nowhere', 'hardly', 'barely', "don't", "doesn't", 
                 "didn't", "won't", "wouldn't", "can't", "cannot"]
    
    # Split text into words
    words = text_lower.replace(',', ' ').replace('.', ' ').split()
    
    positive_score = 0
    negative_score = 0
    
    # Analyze with negation handling
    for i, word in enumerate(words):
        # Check if previous word is negation
        is_negated = (i > 0 and words[i-1] in negations)
        
        # Check positive keywords
        if word in positive_keywords:
            weight = positive_keywords[word]
            if is_negated:
                # Negated positive = negative
                negative_score += weight
                print(f"  Found: NOT {word} (negated positive) -> negative +{weight}")
            else:
                positive_score += weight
                print(f"  Found: {word} (positive) -> +{weight}")
        
        # Check negative keywords
        elif word in negative_keywords:
            weight = negative_keywords[word]
            if is_negated:
                # Negated negative = positive
                positive_score += weight
                print(f"  Found: NOT {word} (negated negative) -> positive +{weight}")
            else:
                negative_score += weight
                print(f"  Found: {word} (negative) -> +{weight}")
    
    print(f"\nScore calculation:")
    print(f"  Positive score: {positive_score}")
    print(f"  Negative score: {negative_score}")
    
    # Determine sentiment based on scores
    if positive_score == 0 and negative_score == 0:
        sentiment = 'neutral'
        score = 0.5
    elif positive_score > negative_score:
        # Calculate confidence: higher difference = higher confidence
        difference = positive_score - negative_score
        total = positive_score + negative_score
        score = 0.6 + (difference / total * 0.35)  # Range: 0.6 to 0.95
        sentiment = 'positive'
    elif negative_score > positive_score:
        difference = negative_score - positive_score
        total = positive_score + negative_score
        score = 0.6 + (difference / total * 0.35)  # Range: 0.6 to 0.95
        sentiment = 'negative'
    else:
        # Equal scores = neutral
        sentiment = 'neutral'
        score = 0.5
    
    score = min(0.95, score)  # Cap at 0.95
    
    print(f"\n✅ Fallback result: {sentiment} (confidence: {score:.4f})")
    print("="*50 + "\n")
    
    return {
        'sentiment': sentiment,
        'score': round(score, 4)
    }

def extract_key_points_gemini(text):
    """
    Extract key points dari review menggunakan Google Gemini
    Support multi-language (English & Indonesian)
    """
    try:
        print("\n" + "="*50)
        print("🤖 Extracting key points with Gemini...")
        print(f"Review text: {text[:100]}...")
        
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        # Prompt yang support multi-language
        prompt = f"""
        Analyze this product review and extract 3-5 key points that summarize the review.
        The review might be in English or Indonesian - handle both languages.
        
        IMPORTANT RULES:
        1. Maintain the ORIGINAL SENTIMENT of each point (positive stays positive, negative stays negative)
        2. Be concise - maximum 12 words per point
        3. Focus on specific aspects: quality, price, performance, features, delivery, pros, cons
        4. If the review mentions problems or complaints, include them as negative points
        5. Extract key points in the SAME LANGUAGE as the review (if Indonesian review, give Indonesian key points)
        6. Return ONLY a valid JSON array of strings, nothing else
        
        Review: "{text}"
        
        Example output format:
        For English: ["Outstanding camera quality", "Battery life disappointing", "Fast performance"]
        For Indonesian: ["Kualitas kamera bagus", "Baterai cepat habis", "Performa lambat"]
        
        Return only the JSON array:
        """
        
        response = model.generate_content(prompt)
        key_points_text = response.text.strip()
        
        print(f"Gemini raw response: {key_points_text[:200]}")
        
        # Clean markdown if present
        if key_points_text.startswith('```'):
            lines = key_points_text.split('\n')
            key_points_text = '\n'.join([l for l in lines if not l.startswith('```')])
            key_points_text = key_points_text.replace('json', '').strip()
        
        # Parse JSON
        try:
            key_points_array = json.loads(key_points_text)
            if isinstance(key_points_array, list):
                print(f"✅ Extracted {len(key_points_array)} key points")
                for i, point in enumerate(key_points_array, 1):
                    print(f"  {i}. {point}")
                print("="*50 + "\n")
                return json.dumps(key_points_array)
            else:
                print("⚠️ Response not a list, wrapping...")
                return json.dumps([key_points_text])
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parse error: {e}")
            return json.dumps([key_points_text.strip()])
            
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        print("="*50 + "\n")
        return json.dumps([f"Error extracting key points: {str(e)}"])


# ===========================
# API ENDPOINTS
# ===========================

@app.route('/api/analyze-review', methods=['POST'])
def analyze_review():
    """
    Endpoint untuk analyze review baru
    Dengan support auto-translation untuk bahasa Indonesia
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
        
        # ============================================
        # AUTO-DETECT & TRANSLATE
        # ============================================
        translation_result = detect_and_translate(review_text)
        text_for_analysis = translation_result['translated_text']
        original_language = translation_result['original_language']
        is_translated = translation_result['is_translated']
        
        print(f"Analysis will use: {'translated' if is_translated else 'original'} text")
        
        # ============================================
        # SENTIMENT ANALYSIS (dengan text yang sudah ditranslate)
        # ============================================
        sentiment_result = analyze_sentiment_huggingface(text_for_analysis)
        
        # ============================================
        # KEY POINTS EXTRACTION (gunakan text ORIGINAL untuk Gemini)
        # Gemini bisa handle multiple languages
        # ============================================
        key_points_json = extract_key_points_gemini(review_text)  # Pakai original text
        
        # Create new review object
        new_review = Review(
            product_name=product_name,
            review_text=review_text,  # Simpan original text
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
        
        # Add translation info to response (optional, for debugging)
        review_dict['meta'] = {
            'original_language': original_language,
            'was_translated': is_translated
        }
        
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