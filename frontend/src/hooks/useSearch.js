import { useState, useCallback, useEffect, useRef } from 'react';

/**
 * Custom hook for debounced search input
 * @param {Function} callback - Function to call after debounce
 * @param {number} delay - Debounce delay in milliseconds
 * @returns {Function} - Debounced function
 */
export function useDebounce(callback, delay = 300) {
  const timeoutRef = useRef(null);

  const debouncedCallback = useCallback((...args) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    timeoutRef.current = setTimeout(() => {
      callback(...args);
    }, delay);
  }, [callback, delay]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return debouncedCallback;
}

/**
 * Hook for search functionality with debouncing
 * @param {Function} searchFn - Async search function
 * @param {number} debounceMs - Debounce delay
 * @returns {Object} - Search state and controls
 */
export function useSearch(searchFn, debounceMs = 300) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const performSearch = async (searchQuery) => {
    if (!searchQuery.trim()) {
      setResults([]);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await searchFn(searchQuery);
      setResults(data);
    } catch (err) {
      setError(err.message || 'Search failed');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const debouncedSearch = useDebounce(performSearch, debounceMs);

  const handleQueryChange = (newQuery) => {
    setQuery(newQuery);
    debouncedSearch(newQuery);
  };

  const clearSearch = () => {
    setQuery('');
    setResults([]);
    setError(null);
  };

  return {
    query,
    results,
    loading,
    error,
    setQuery: handleQueryChange,
    clearSearch
  };
}
