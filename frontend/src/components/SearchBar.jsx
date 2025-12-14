import { useState } from 'react';
import PropTypes from 'prop-types';
import { useSearch } from '../hooks/useSearch';
import { searchMessages } from '../api/client';
import '../styles/SearchBar.css';

export default function SearchBar({ onResultClick }) {
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    sessionType: '',
    modelId: '',
    startDate: '',
    endDate: ''
  });

  const performSearch = async (query) => {
    const params = new URLSearchParams({
      query,
      limit: '50'
    });

    if (filters.sessionType) params.append('session_type', filters.sessionType);
    if (filters.modelId) params.append('model_id', filters.modelId);
    if (filters.startDate) params.append('start_date', filters.startDate);
    if (filters.endDate) params.append('end_date', filters.endDate);

    return await searchMessages(params.toString());
  };

  const { query, results, loading, error, setQuery, clearSearch } = useSearch(performSearch);

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleResultClick = (result) => {
    if (onResultClick) {
      onResultClick(result);
    }
    clearSearch();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      clearSearch();
    }
  };

  return (
    <div className="search-bar-container">
      <div className="search-input-wrapper">
        <input
          type="text"
          className="search-input"
          placeholder="Search messages... (try 'error', &quot;exact phrase&quot;, -exclude)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          aria-label="Search messages"
        />
        
        {query && (
          <button 
            className="search-clear-btn"
            onClick={clearSearch}
            aria-label="Clear search"
          >
            ✕
          </button>
        )}

        <button
          className="search-filter-btn"
          onClick={() => setShowFilters(!showFilters)}
          aria-label="Toggle filters"
        >
          🔍 Filters
        </button>
      </div>

      {showFilters && (
        <div className="search-filters">
          <select
            value={filters.sessionType}
            onChange={(e) => handleFilterChange('sessionType', e.target.value)}
            aria-label="Filter by session type"
          >
            <option value="">All Types</option>
            <option value="chat">Chat</option>
            <option value="code">Code</option>
            <option value="documents">Documents</option>
            <option value="playground">Playground</option>
          </select>

          <input
            type="date"
            placeholder="Start Date"
            value={filters.startDate}
            onChange={(e) => handleFilterChange('startDate', e.target.value)}
            aria-label="Start date"
          />

          <input
            type="date"
            placeholder="End Date"
            value={filters.endDate}
            onChange={(e) => handleFilterChange('endDate', e.target.value)}
            aria-label="End date"
          />

          <button 
            className="search-reset-filters"
            onClick={() => setFilters({ sessionType: '', modelId: '', startDate: '', endDate: '' })}
          >
            Reset Filters
          </button>
        </div>
      )}

      {loading && (
        <div className="search-loading">Searching...</div>
      )}

      {error && (
        <div className="search-error">
          Error: {error}
        </div>
      )}

      {results.length > 0 && (
        <div className="search-results">
          <div className="search-results-header">
            Found {results.length} result{results.length !== 1 ? 's' : ''}
          </div>
          <div className="search-results-list">
            {results.map((result) => (
              <div
                key={result.id}
                className="search-result-item"
                onClick={() => handleResultClick(result)}
              >
                <div className="search-result-header">
                  <span className="search-result-role">{result.role}</span>
                  <span className="search-result-type">{result.session_type}</span>
                  <span className="search-result-date">
                    {new Date(result.created_at).toLocaleDateString()}
                  </span>
                </div>
                
                {result.session_title && (
                  <div className="search-result-session">
                    Session: {result.session_title}
                  </div>
                )}
                
                <div 
                  className="search-result-snippet"
                  dangerouslySetInnerHTML={{ __html: result.snippet }}
                />
                
                <div className="search-result-score">
                  Relevance: {result.rank.toFixed(2)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {query && !loading && results.length === 0 && !error && (
        <div className="search-no-results">
          No messages found for &quot;{query}&quot;
        </div>
      )}
    </div>
  );
}

SearchBar.propTypes = {
  onResultClick: PropTypes.func
};
