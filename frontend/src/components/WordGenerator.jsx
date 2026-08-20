import React, { useState, useEffect } from 'react';
import { Sparkles, Copy, Check, Info, X, RefreshCw, SlidersHorizontal } from 'lucide-react';
import { getCategories, generateWords, analyzeWord } from '../services/api';

export function WordGenerator() {
  const [categories, setCategories] = useState(['general', 'tech', 'nature', 'science', 'fantasy']);
  const [category, setCategory] = useState('general');
  const [count, setCount] = useState(6);
  const [prefix, setPrefix] = useState('');
  const [minLength, setMinLength] = useState(3);
  const [maxLength, setMaxLength] = useState(15);

  const [words, setWords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [copiedWord, setCopiedWord] = useState(null);

  // Analysis Modal State
  const [analysisData, setAnalysisData] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    // Fetch categories on mount
    getCategories()
      .then((cats) => {
        if (Array.isArray(cats) && cats.length > 0) {
          setCategories(cats);
        }
      })
      .catch(() => {
        // Fallback default categories
      });

    // Initial word generation
    handleGenerate();
  }, []);

  const handleGenerate = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await generateWords({
        category,
        count,
        prefix,
        minLength,
        maxLength,
      });
      setWords(response.words || []);
    } catch (err) {
      setError(err.message || 'Failed to generate words');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (wordText) => {
    navigator.clipboard.writeText(wordText);
    setCopiedWord(wordText);
    setTimeout(() => setCopiedWord(null), 2000);
  };

  const handleAnalyze = async (wordText) => {
    setAnalyzing(true);
    try {
      const result = await analyzeWord(wordText);
      setAnalysisData(result);
    } catch (err) {
      alert(`Could not analyze word: ${err.message}`);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div>
      <section className="hero-section">
        <div className="hero-badge">
          <Sparkles size={14} /> Full-Stack Architecture
        </div>
        <h1 className="hero-title">
          Generate & Analyze <span className="gradient-text">Vocabulary</span>
        </h1>
        <p className="hero-description">
          Powered by a fast Python FastAPI backend microservice and a reactive ReactJS client orchestrated with Docker.
        </p>
      </section>

      {/* Generator Controls */}
      <div className="generator-card">
        <form onSubmit={handleGenerate}>
          <div className="controls-grid">
            <div className="form-group">
              <label className="form-label" htmlFor="category-select">Category</label>
              <select
                id="category-select"
                className="form-select"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
              >
                {categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat.charAt(0).toUpperCase() + cat.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="count-input">Word Count ({count})</label>
              <input
                id="count-input"
                type="number"
                min="1"
                max="30"
                className="form-input"
                value={count}
                onChange={(e) => setCount(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="prefix-input">Prefix Filter</label>
              <input
                id="prefix-input"
                type="text"
                maxLength="10"
                placeholder="e.g. mic, de..."
                className="form-input"
                value={prefix}
                onChange={(e) => setPrefix(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Min / Max Length</label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input
                  type="number"
                  min="1"
                  max="20"
                  className="form-input"
                  value={minLength}
                  onChange={(e) => setMinLength(e.target.value)}
                  placeholder="Min"
                  title="Min Length"
                />
                <input
                  type="number"
                  min="1"
                  max="30"
                  className="form-input"
                  value={maxLength}
                  onChange={(e) => setMaxLength(e.target.value)}
                  placeholder="Max"
                  title="Max Length"
                />
              </div>
            </div>
          </div>

          {error && (
            <div style={{ padding: '0.75rem 1rem', marginBottom: '1rem', borderRadius: '8px', background: 'rgba(244, 63, 94, 0.15)', border: '1px solid rgba(244, 63, 94, 0.3)', color: '#fda4af', fontSize: '0.875rem' }}>
              {error}
            </div>
          )}

          <button id="generate-btn" type="submit" className="btn-primary" disabled={loading}>
            {loading ? <RefreshCw className="animate-spin" size={18} /> : <Sparkles size={18} />}
            <span>{loading ? 'Generating...' : 'Generate Words'}</span>
          </button>
        </form>
      </div>

      {/* Generated Results */}
      <div className="results-container">
        <div className="results-header">
          <h2 className="results-title">Generated Words ({words.length})</h2>
        </div>

        <div className="words-grid">
          {words.map((item, idx) => (
            <div key={`${item.word}-${idx}`} className="word-card">
              <div>
                <div className="word-value">{item.word}</div>
                <div className="word-tags" style={{ marginTop: '0.75rem' }}>
                  <span className="tag">{item.category}</span>
                  <span className="tag">{item.length} chars</span>
                  {item.is_palindrome && <span className="tag palindrome">Palindrome</span>}
                </div>
              </div>

              <div className="word-actions">
                <button
                  className="btn-icon"
                  onClick={() => handleCopy(item.word)}
                  title="Copy to clipboard"
                >
                  {copiedWord === item.word ? <Check size={16} color="#10b981" /> : <Copy size={16} />}
                </button>
                <button
                  className="btn-icon"
                  onClick={() => handleAnalyze(item.word)}
                  title="Analyze Word"
                >
                  <Info size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Word Analysis Modal */}
      {analysisData && (
        <div className="modal-backdrop" onClick={() => setAnalysisData(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Word Analytics: "{analysisData.word}"</h3>
              <button className="btn-icon" onClick={() => setAnalysisData(null)}>
                <X size={18} />
              </button>
            </div>

            <div className="analysis-grid">
              <div className="stat-box">
                <div className="stat-label">Length</div>
                <div className="stat-value">{analysisData.length}</div>
              </div>
              <div className="stat-box">
                <div className="stat-label">Vowels</div>
                <div className="stat-value">{analysisData.vowels_count}</div>
              </div>
              <div className="stat-box">
                <div className="stat-label">Consonants</div>
                <div className="stat-value">{analysisData.consonants_count}</div>
              </div>
              <div className="stat-box">
                <div className="stat-label">Palindrome</div>
                <div className="stat-value">{analysisData.is_palindrome ? 'Yes' : 'No'}</div>
              </div>
            </div>

            <div style={{ marginBottom: '1.25rem' }}>
              <div className="stat-label">Reversed</div>
              <div style={{ fontSize: '1.1rem', fontWeight: '600', color: 'var(--accent-cyan)' }}>
                {analysisData.reversed}
              </div>
            </div>

            <div>
              <div className="stat-label" style={{ marginBottom: '0.5rem' }}>Character Frequencies</div>
              <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                {Object.entries(analysisData.character_frequencies || {}).map(([char, count]) => (
                  <span key={char} className="tag">
                    <strong>{char}</strong>: {count}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
