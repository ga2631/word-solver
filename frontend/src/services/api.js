const API_BASE = import.meta.env.VITE_API_BASE_URL || '';
const REMOTE_VOTEE_API_BASE = 'https://wordle.votee.dev:8000';

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
 * Get strategic initial starting word for a word length
 */
export async function getStartingWord(size = 5) {
  const response = await fetch(`${API_BASE}/api/v1/solver/starting-word?size=${size}`);
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to fetch starting word for length ${size}`);
  }
  return response.json();
}

/**
 * Get a random word from the dictionary of the specified size
 */
export async function getRandomWord(size = 5, seed = null) {
  const seedParam = seed ? `&seed=${encodeURIComponent(seed)}` : '';
  const response = await fetch(`${API_BASE}/api/v1/random/word?size=${size}${seedParam}`);
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to fetch random word for length ${size}`);
  }
  return response.json();
}

/**
 * Request next optimal guess based on previous history feedback
 */
export async function getNextGuess(size, history) {
  const response = await fetch(`${API_BASE}/api/v1/solver/next-guess`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      size: Number(size),
      history: history.map((h) => ({
        guess: h.guess,
        feedback: h.feedback || h.results,
      })),
    }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to calculate next guess');
  }

  return response.json();
}

/**
 * Evaluate a single guess against either Local Mock API or Remote Votee API
 */
export async function evaluateGuessLive({
  mode = 'daily',
  guess = '',
  size = 5,
  word = '',
  seed = '',
  useRemoteApi = false,
} = {}) {
  const baseUrl = useRemoteApi ? REMOTE_VOTEE_API_BASE : `${API_BASE}/api/v1`;
  let url = '';

  const cleanGuess = guess.trim().toLowerCase();

  if (mode === 'daily') {
    url = `${baseUrl}/daily?guess=${encodeURIComponent(cleanGuess)}&size=${size}`;
  } else if (mode === 'random') {
    const seedParam = seed ? `&seed=${encodeURIComponent(seed)}` : '';
    url = `${baseUrl}/random?guess=${encodeURIComponent(cleanGuess)}&size=${size}${seedParam}`;
  } else if (mode === 'word' || mode === 'selected') {
    const targetWord = word.trim().toLowerCase();
    url = `${baseUrl}/word/${encodeURIComponent(targetWord)}?guess=${encodeURIComponent(cleanGuess)}`;
  } else {
    throw new Error(`Unsupported mode: ${mode}`);
  }

  const response = await fetch(url);
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || `Evaluation API returned error (${response.status})`);
  }

  return response.json();
}

/**
 * Resolve Wordle puzzle using backend batch solver API (Legacy & fallback support)
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

  // In selected / word mode, starting word is automatically chosen based on secret word length and not passed to API
  if (startingWord && mode !== 'word' && mode !== 'selected') {
    params.append('starting_word', startingWord.trim().toLowerCase());
  }

  const response = await fetch(`${API_BASE}/api/v1/resolve?${params.toString()}`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Resolve failed with status: ${response.status}`);
  }

  return response.json();
}
