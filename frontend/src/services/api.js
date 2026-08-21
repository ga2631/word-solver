const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

/**
 * Fetch health status of the backend API
 */
export async function checkHealth() {
  const response = await fetch(`${API_BASE}/api/v1/health`);
  if (!response.ok) {
    throw new Error(`Health check failed with status: ${response.status}`);
  }
  return response.json();
}

/**
 * Fetch available word categories
 */
export async function getCategories() {
  const response = await fetch(`${API_BASE}/api/v1/words/categories`);
  if (!response.ok) {
    throw new Error(`Failed to fetch categories: ${response.status}`);
  }
  return response.json();
}

/**
 * Generate words with parameters
 */
export async function generateWords({ category, count, prefix, minLength, maxLength }) {
  const payload = {
    category: category || 'general',
    count: Number(count) || 5,
    prefix: prefix || '',
    min_length: Number(minLength) || 3,
    max_length: Number(maxLength) || 15,
  };

  const response = await fetch(`${API_BASE}/api/v1/words/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Generation failed with status: ${response.status}`);
  }

  return response.json();
}

/**
 * Analyze a word
 */
export async function analyzeWord(word) {
  const response = await fetch(`${API_BASE}/api/v1/words/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ word }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Analysis failed with status: ${response.status}`);
  }

  return response.json();
}

/**
 * Resolve Wordle puzzle using automated solver API
 * @param {Object} params
 * @param {'daily'|'random'|'word'} params.mode
 * @param {number} [params.size=5]
 * @param {string} [params.word]
 * @param {string} [params.seed]
 * @param {string} [params.startingWord]
 */
export async function resolveWordle({ mode = 'daily', size = 5, word = '', seed = '', startingWord = '' } = {}) {
  const params = new URLSearchParams();
  params.append('mode', mode);
  params.append('size', String(size));

  if (mode === 'word' && word) {
    params.append('word', word.trim().toLowerCase());
  }

  if (mode === 'random' && seed) {
    params.append('seed', seed.trim());
  }

  if (startingWord) {
    params.append('starting_word', startingWord.trim().toLowerCase());
  }

  const response = await fetch(`${API_BASE}/api/v1/resolve?${params.toString()}`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Resolve failed with status: ${response.status}`);
  }

  return response.json();
}

