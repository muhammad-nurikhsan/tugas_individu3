import React from 'react';
import './ReviewList.css';

function ReviewList({ reviews }) {
  if (!reviews || reviews.length === 0) {
    return (
      <div className="review-list-section">
        <div className="section-header">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 3v18h18"/>
            <path d="M18 17V9"/>
            <path d="M13 17V5"/>
            <path d="M8 17v-3"/>
          </svg>
          <h2>Analysis Results</h2>
        </div>
        
        <div className="empty-state">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <circle cx="11" cy="11" r="8"/>
            <path d="M21 21l-4.35-4.35"/>
            <path d="M11 8v6"/>
            <path d="M8 11h6"/>
          </svg>
          <p>No reviews yet. Submit a review above to see the AI analysis!</p>
        </div>
      </div>
    );
  }

  const getSentimentColor = (sentiment) => {
    switch (sentiment) {
      case 'positive': return 'success';
      case 'negative': return 'danger';
      case 'neutral': return 'warning';
      default: return 'neutral';
    }
  };

  const getSentimentIcon = (sentiment) => {
    switch (sentiment) {
      case 'positive':
        return <path d="M8 14s1.5 2 4 2 4-2 4-2M9 9h.01M15 9h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>;
      case 'negative':
        return <path d="M8 16s1.5-2 4-2 4 2 4 2M9 9h.01M15 9h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>;
      default:
        return <path d="M8 13h8M9 9h.01M15 9h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>;
    }
  };

  return (
    <div className="review-list-section">
      <div className="section-header">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M3 3v18h18"/>
          <path d="M18 17V9"/>
          <path d="M13 17V5"/>
          <path d="M8 17v-3"/>
        </svg>
        <h2>Analysis Results</h2>
      </div>
      
      <div className="reviews-grid">
        {reviews.map((review) => (
          <div key={review.id} className="review-card">
            <div className="card-header">
              <h3>{review.product_name}</h3>
              <div className={`sentiment-badge ${getSentimentColor(review.sentiment)}`}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  {getSentimentIcon(review.sentiment)}
                </svg>
                <span className="sentiment-label">
                  {review.sentiment.charAt(0).toUpperCase() + review.sentiment.slice(1)}
                </span>
                {review.sentiment_score > 0 && (
                  <span className="sentiment-score">
                    {(review.sentiment_score * 100).toFixed(1)}%
                  </span>
                )}
              </div>
            </div>

            <p className="review-text">{review.review_text}</p>

            <div className="key-points">
              <h4>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="9 11 12 14 22 4"/>
                  <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>
                </svg>
                Key Points:
              </h4>
              <ul>
                {review.key_points && review.key_points.length > 0 ? (
                  review.key_points.map((point, index) => (
                    <li key={index}>{point}</li>
                  ))
                ) : (
                  <li className="no-points">No key points extracted</li>
                )}
              </ul>
            </div>

            <div className="card-footer">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
              <span>Analyzed: {new Date(review.created_at).toLocaleString()}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ReviewList;