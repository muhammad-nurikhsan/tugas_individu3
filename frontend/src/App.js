import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ReviewForm from './components/ReviewForm';
import ReviewList from './components/ReviewList';
import './App.css';

const API_BASE_URL = 'http://localhost:5000/api';

function App() {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchReviews();
  }, []);

  const fetchReviews = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/reviews?limit=20`);
      
      if (response.data.success) {
        setReviews(response.data.data);
      } else {
        setError('Failed to fetch reviews');
      }
    } catch (err) {
      console.error('Error fetching reviews:', err);
      setError('Unable to connect to server. Make sure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async (formData) => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/analyze-review`,
        formData
      );

      if (response.data.success) {
        setReviews([response.data.data, ...reviews]);
        return response.data;
      } else {
        throw new Error(response.data.error || 'Failed to analyze review');
      }
    } catch (err) {
      console.error('Error analyzing review:', err);
      throw new Error(
        err.response?.data?.error || 
        err.message || 
        'Failed to analyze review'
      );
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="header-icon">
            <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
              <path d="M20 4C11.163 4 4 11.163 4 20C4 28.837 11.163 36 20 36C28.837 36 36 28.837 36 20C36 11.163 28.837 4 20 4ZM20 8C26.627 8 32 13.373 32 20C32 26.627 26.627 32 20 32C13.373 32 8 26.627 8 20C8 13.373 13.373 8 20 8ZM15 16C14.448 16 14 16.448 14 17C14 17.552 14.448 18 15 18C15.552 18 16 17.552 16 17C16 16.448 15.552 16 15 16ZM25 16C24.448 16 24 16.448 24 17C24 17.552 24.448 18 25 18C25.552 18 26 17.552 26 17C26 16.448 25.552 16 25 16ZM14 22C14 25.314 16.686 28 20 28C23.314 28 26 25.314 26 22H14Z" fill="white"/>
            </svg>
          </div>
          <div className="header-text">
            <h1>AI Product Review Analyzer</h1>
            <p>Muhammd Nurikhsan || 123140057 || RB</p>
          </div>
        </div>
      </header>

      <main className="app-main">
        <div className="container">
          {error && (
            <div className="error-banner">
              <div className="error-content">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
                </svg>
                <span>{error}</span>
              </div>
              <button onClick={fetchReviews} className="retry-btn">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                  <path fillRule="evenodd" d="M8 3a5 5 0 104.546 2.914.5.5 0 00-.908-.417A4 4 0 118 4v1.5l2.5-2L8 1v2z"/>
                </svg>
                Retry
              </button>
            </div>
          )}

          <ReviewForm onAnalyze={handleAnalyze} />

          {loading ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Loading reviews...</p>
            </div>
          ) : (
            <ReviewList reviews={reviews} />
          )}
        </div>
      </main>
    </div>
  );
}

export default App;