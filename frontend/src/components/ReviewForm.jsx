import React, { useState } from 'react';
import './ReviewForm.css';

function ReviewForm({ onAnalyze }) {
  const [formData, setFormData] = useState({
    product_name: '',
    review_text: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.product_name.trim()) {
      setError('Product name is required');
      return;
    }
    
    if (!formData.review_text.trim()) {
      setError('Review text is required');
      return;
    }
    
    if (formData.review_text.trim().length < 10) {
      setError('Review text too short (minimum 10 characters)');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      await onAnalyze(formData);
      setFormData({
        product_name: '',
        review_text: ''
      });
    } catch (err) {
      setError(err.message || 'Failed to analyze review');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="review-form-container">
      <div className="form-header">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
          <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
        </svg>
        <h2>Submit Product Review</h2>
      </div>
      
      <form onSubmit={handleSubmit} className="review-form">
        <div className="form-group">
          <label htmlFor="product_name">Product Name *</label>
          <input
            type="text"
            id="product_name"
            name="product_name"
            value={formData.product_name}
            onChange={handleChange}
            placeholder="e.g., iPhone 15 Pro"
            disabled={loading}
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="review_text">Your Review *</label>
          <textarea
            id="review_text"
            name="review_text"
            value={formData.review_text}
            onChange={handleChange}
            placeholder="Share your experience with this product..."
            rows="6"
            disabled={loading}
            required
          />
          <div className="char-count">
            {formData.review_text.length} characters
          </div>
        </div>
        
        {error && (
          <div className="error-message">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
              <path d="M7.002 11a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 4.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995z"/>
            </svg>
            <span>{error}</span>
          </div>
        )}
        
        <button 
          type="submit" 
          className="submit-btn"
          disabled={loading}
        >
          {loading ? (
            <>
              <div className="btn-spinner"></div>
              <span>Analyzing...</span>
            </>
          ) : (
            <span>Analyze Review</span>
          )}
        </button>
      </form>
    </div>
  );
}

export default ReviewForm;