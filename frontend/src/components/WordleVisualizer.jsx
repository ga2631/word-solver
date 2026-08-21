import React, { useState, useEffect, useRef } from 'react';
import {
  Play,
  RotateCcw,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Calendar,
  Shuffle,
  Edit3,
  Server,
  Globe,
  Cpu,
  BarChart3,
  Layers,
  Zap,
  Info,
  Timer,
} from 'lucide-react';
import { getStartingWord, getNextGuess, evaluateGuessLive } from '../services/api';

const MODE_CONFIG = {
  daily: {
    label: 'Daily',
    description: 'Đoán từ thử thách mỗi ngày',
    icon: Calendar,
  },
  random: {
    label: 'Random',
    description: 'Đoán từ ngẫu nhiên trong kho từ vựng',
    icon: Shuffle,
  },
  selected: {
    label: 'Selected',
    description: 'Nhập từ bí mật cần hệ thống giải',
    icon: Edit3,
  },
};

const ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');

export function WordleVisualizer() {
  // Mode configuration
  const [mode, setMode] = useState('daily');
  const [wordLength, setWordLength] = useState(5);
  const [selectedWord, setSelectedWord] = useState('');
  const [inputError, setInputError] = useState('');

  // Environment configuration: false = Local Test Evaluator, true = Live Votee Dev API
  const [useRemoteApi, setUseRemoteApi] = useState(false);

  // Strategic starting word preview
  const [strategicStartingWord, setStrategicStartingWord] = useState('crane');

  // Execution state: 'idle' | 'running' | 'completed' | 'error'
  const [status, setStatus] = useState('idle');
  const [globalError, setGlobalError] = useState(null);

  // Resolution Steps History
  // Each step: { step: number, guess: string, results: [{slot, guess, result}], remainingCount: number, timeMs: number }
  const [steps, setSteps] = useState([]);
  const [flippedRows, setFlippedRows] = useState([]); // 2D array of flipped state

  // Analytics & Stats
  const [targetWord, setTargetWord] = useState(null);
  const [eliminatedLetters, setEliminatedLetters] = useState([]);
  const [letterStatusMap, setLetterStatusMap] = useState({}); // letter -> 'correct' | 'present' | 'absent'
  const [solveStats, setSolveStats] = useState({
    totalAttempts: 0,
    startTime: 0,
    elapsedMs: 0,
    isSuccess: false,
    message: '',
  });

  const abortControllerRef = useRef(false);

  // Load initial starting word on length change
  useEffect(() => {
    let isMounted = true;
    const loadStartingWord = async () => {
      try {
        const data = await getStartingWord(wordLength);
        if (isMounted && data.starting_word) {
          setStrategicStartingWord(data.starting_word);
        }
      } catch (err) {
        if (isMounted) {
          setStrategicStartingWord(wordLength === 5 ? 'crane' : 'roam');
        }
      }
    };
    loadStartingWord();
    return () => {
      isMounted = false;
    };
  }, [wordLength]);

  // Handle selected word change with instant validation
  const handleSelectedWordChange = (val) => {
    const clean = val.replace(/[^a-zA-Z]/g, '').toLowerCase();
    setSelectedWord(clean);
    if (clean.length > 0) {
      setWordLength(clean.length);
    }
    if (clean.length > 0 && (clean.length < 2 || clean.length > 15)) {
      setInputError('Độ dài từ nên từ 2 đến 15 ký tự.');
    } else {
      setInputError('');
    }
  };

  const handleModeChange = (newMode) => {
    if (status === 'running') return;
    setMode(newMode);
    setInputError('');
    setGlobalError(null);
    if (newMode !== 'selected') {
      setWordLength(5);
    } else if (selectedWord) {
      setWordLength(selectedWord.length);
    }
    handleReset();
  };

  const handleReset = () => {
    abortControllerRef.current = true;
    setStatus('idle');
    setGlobalError(null);
    setInputError('');
    setSteps([]);
    setFlippedRows([]);
    setTargetWord(null);
    setEliminatedLetters([]);
    setLetterStatusMap({});
    setSolveStats({
      totalAttempts: 0,
      startTime: 0,
      elapsedMs: 0,
      isSuccess: false,
      message: '',
    });
  };

  // Helper sleep for staggered live steps
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  // Core Solver Execution Loop
  const handleStartSolve = async () => {
    if (status === 'running') return;

    // Validate Selected Mode
    if (mode === 'selected') {
      const cleanWord = selectedWord.trim().toLowerCase();
      if (!cleanWord) {
        setInputError('Vui lòng nhập từ bí mật.');
        return;
      }
      if (cleanWord.length < 2 || cleanWord.length > 15) {
        setInputError('Độ dài từ phải từ 2 đến 15 ký tự.');
        return;
      }
      if (!/^[a-z]+$/.test(cleanWord)) {
        setInputError('Từ bí mật chỉ được chứa chữ cái tiếng Anh (a-z).');
        return;
      }
    }

    // Reset previous run
    abortControllerRef.current = false;
    setStatus('running');
    setGlobalError(null);
    setSteps([]);
    setFlippedRows([]);
    setTargetWord(null);
    setEliminatedLetters([]);
    setLetterStatusMap({});

    const startTime = Date.now();
    const effectiveSize = mode === 'selected' ? selectedWord.trim().length : wordLength;

    try {
      // 1. Get initial strategic starting word
      let currentGuess = strategicStartingWord;
      try {
        const startData = await getStartingWord(effectiveSize);
        if (startData.starting_word) {
          currentGuess = startData.starting_word;
        }
      } catch (e) {
        // fallback
      }

      const historyAccumulator = [];
      let stepIndex = 1;
      const maxAttempts = 15;
      let isSolved = false;
      let finalTarget = null;
      let newEliminated = [];
      const updatedLetterMap = {};

      while (stepIndex <= maxAttempts && !isSolved) {
        if (abortControllerRef.current) break;

        const currentStepNumber = stepIndex;

        // 2. Add row placeholder to UI with empty flip state
        const initialRowFlipped = new Array(effectiveSize).fill(false);
        setSteps((prev) => [
          ...prev,
          {
            step: currentStepNumber,
            guess: currentGuess,
            results: [],
            remainingCount: stepIndex === 1 ? '...' : undefined,
          },
        ]);
        setFlippedRows((prev) => [...prev, initialRowFlipped]);

        // 3. Call Evaluation API
        const evalFeedback = await evaluateGuessLive({
          mode: mode === 'selected' ? 'word' : mode,
          guess: currentGuess,
          size: effectiveSize,
          word: mode === 'selected' ? selectedWord.trim().toLowerCase() : undefined,
          useRemoteApi,
        });

        if (abortControllerRef.current) break;

        // 4. Update letter status mapping & eliminated letters
        evalFeedback.forEach((item) => {
          const char = item.guess.toUpperCase();
          if (item.result === 'correct') {
            updatedLetterMap[char] = 'correct';
          } else if (item.result === 'present' && updatedLetterMap[char] !== 'correct') {
            updatedLetterMap[char] = 'present';
          } else if (item.result === 'absent' && !updatedLetterMap[char]) {
            updatedLetterMap[char] = 'absent';
          }
        });
        setLetterStatusMap({ ...updatedLetterMap });

        // Update step with actual results
        setSteps((prev) =>
          prev.map((s, idx) =>
            idx === currentStepNumber - 1 ? { ...s, results: evalFeedback } : s
          )
        );

        // 5. Staggered 3D Tile Flip Animation
        for (let col = 0; col < effectiveSize; col++) {
          if (abortControllerRef.current) break;
          await sleep(140);
          setFlippedRows((prev) => {
            const next = prev.map((row) => [...row]);
            if (next[currentStepNumber - 1]) {
              next[currentStepNumber - 1][col] = true;
            }
            return next;
          });
        }

        // 6. Check if target word found (all correct)
        const allCorrect = evalFeedback.every((item) => item.result === 'correct');
        if (allCorrect) {
          isSolved = true;
          finalTarget = currentGuess;

          setSteps((prev) =>
            prev.map((s, idx) =>
              idx === currentStepNumber - 1 ? { ...s, remainingCount: 1 } : s
            )
          );
          break;
        }

        // 7. Calculate next guess via solver API
        historyAccumulator.push({
          guess: currentGuess,
          feedback: evalFeedback,
        });

        const nextData = await getNextGuess(effectiveSize, historyAccumulator);
        if (abortControllerRef.current) break;

        newEliminated = nextData.eliminated_letters || [];
        setEliminatedLetters(newEliminated);

        setSteps((prev) =>
          prev.map((s, idx) =>
            idx === currentStepNumber - 1
              ? { ...s, remainingCount: nextData.remaining_candidates_count }
              : s
          )
        );

        if (nextData.is_exhausted || !nextData.next_guess) {
          setGlobalError(
            `Đã loại trừ toàn bộ ứng viên sau ${stepIndex} lần đoán. Từ này có thể không nằm trong từ điển.`
          );
          break;
        }

        currentGuess = nextData.next_guess;
        stepIndex++;

        // Brief delay before launching next live guess
        await sleep(400);
      }

      const elapsed = Date.now() - startTime;
      setTargetWord(finalTarget || (isSolved ? currentGuess : null));
      setSolveStats({
        totalAttempts: isSolved ? stepIndex : steps.length,
        startTime,
        elapsedMs: elapsed,
        isSuccess: isSolved,
        message: isSolved
          ? `Đã giải thành công từ bí mật trong ${stepIndex} lần đoán (${(elapsed / 1000).toFixed(2)}s).`
          : 'Không thể tìm ra từ mục tiêu trong số lần đoán cho phép.',
      });
      setStatus('completed');
    } catch (err) {
      if (!abortControllerRef.current) {
        setGlobalError(err.message || 'Lỗi xảy ra trong quá trình giải từ.');
        setStatus('error');
      }
    }
  };

  // Dimensions for Center Wordle Grid
  const totalGridRows = Math.max(6, steps.length);
  const activeWordSize =
    mode === 'selected' && selectedWord ? selectedWord.length : wordLength;

  return (
    <div className="dashboard-container">
      {/* =========================================================================
          BOX 1: LEFT PANEL - CONTROLS & ENVIRONMENT (Bảng điều khiển)
         ========================================================================= */}
      <aside className="panel-box left-panel">
        <div className="panel-header">
          <div className="panel-title-group">
            <Cpu size={18} className="panel-icon text-indigo" />
            <h2 className="panel-title">Bảng điều khiển</h2>
          </div>
          <span className="badge-pill">v2.0</span>
        </div>

        {/* Environment Toggle Switch */}
        <div className="control-section">
          <label className="section-label">Môi trường API</label>
          <div className="env-toggle-card">
            <button
              type="button"
              className={`env-tab-btn ${!useRemoteApi ? 'active' : ''}`}
              onClick={() => {
                if (status !== 'running') setUseRemoteApi(false);
              }}
              disabled={status === 'running'}
            >
              <Server size={14} />
              <span>Local Evaluator</span>
            </button>
            <button
              type="button"
              className={`env-tab-btn ${useRemoteApi ? 'active' : ''}`}
              onClick={() => {
                if (status !== 'running') setUseRemoteApi(true);
              }}
              disabled={status === 'running'}
            >
              <Globe size={14} />
              <span>Votee Dev Live</span>
            </button>
          </div>
        </div>

        {/* Mode Selector */}
        <div className="control-section">
          <label className="section-label">Chế độ đoán</label>
          <div className="mode-tabs-grid">
            {Object.entries(MODE_CONFIG).map(([key, item]) => {
              const Icon = item.icon;
              const isActive = mode === key;
              return (
                <button
                  key={key}
                  type="button"
                  className={`mode-btn ${isActive ? 'active' : ''}`}
                  onClick={() => handleModeChange(key)}
                  disabled={status === 'running'}
                >
                  <Icon size={16} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Word Length Selector (For Daily & Random) */}
        {mode !== 'selected' && (
          <div className="control-section">
            <div className="label-with-value">
              <label className="section-label" htmlFor="word-length-select">
                Độ dài từ (Word Length)
              </label>
              <span className="length-indicator">{wordLength} ký tự</span>
            </div>
            <div className="length-pills">
              {[3, 4, 5, 6, 7, 8].map((len) => (
                <button
                  key={len}
                  type="button"
                  className={`length-pill-btn ${wordLength === len ? 'active' : ''}`}
                  onClick={() => {
                    if (status !== 'running') {
                      setWordLength(len);
                      handleReset();
                    }
                  }}
                  disabled={status === 'running'}
                >
                  {len}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Selected Word Input (Selected Mode Only) */}
        {mode === 'selected' && (
          <div className="control-section animate-fade-in">
            <label className="section-label" htmlFor="target-secret-word">
              Từ bí mật (Secret Word)
            </label>
            <div className="input-box-wrapper">
              <input
                id="target-secret-word"
                type="text"
                className={`form-input uppercase ${inputError ? 'is-invalid' : ''}`}
                placeholder="Nhập từ bí mật (ví dụ: apple, plant...)"
                value={selectedWord}
                onChange={(e) => handleSelectedWordChange(e.target.value)}
                disabled={status === 'running'}
                maxLength={15}
                autoComplete="off"
                spellCheck="false"
              />
              {selectedWord && (
                <span className="badge-inside">{selectedWord.length} chữ cái</span>
              )}
            </div>
            {inputError && <p className="input-error-msg">{inputError}</p>}
          </div>
        )}

        {/* Auto Strategic Starting Word Info Badge */}
        <div className="strategic-word-card">
          <div className="strategic-header">
            <Zap size={14} className="text-amber" />
            <span className="strategic-title">Từ khởi đầu chiến lược</span>
          </div>
          <div className="strategic-body">
            <span className="strategic-word">{strategicStartingWord.toUpperCase()}</span>
          </div>
        </div>

        {/* Global Error Banner */}
        {globalError && (
          <div className="alert-banner error">
            <AlertCircle size={16} />
            <span>{globalError}</span>
          </div>
        )}

        {/* Main Action Buttons */}
        <div className="action-buttons-stack">
          <button
            id="start-solving-btn"
            type="button"
            className="btn-start"
            onClick={handleStartSolve}
            disabled={status === 'running'}
          >
            {status === 'running' ? (
              <>
                <RotateCcw className="animate-spin" size={18} />
                <span>Đang tự động giải từ...</span>
              </>
            ) : (
              <>
                <Play size={18} fill="currentColor" />
                <span>Bắt đầu đoán từ</span>
              </>
            )}
          </button>

          <button
            id="reset-state-btn"
            type="button"
            className="btn-reset"
            onClick={handleReset}
            disabled={status === 'idle' && steps.length === 0}
          >
            <RotateCcw size={16} />
            <span>Đoán lại (Reset)</span>
          </button>
        </div>
      </aside>

      {/* =========================================================================
          BOX 2: CENTER PANEL - WORDLE BOARD & 3D ANIMATION (Khung đoán từ)
         ========================================================================= */}
      <main className="panel-box center-panel">
        <div className="panel-header center">
          <div className="panel-title-group">
            <Sparkles size={18} className="panel-icon text-cyan" />
            <h2 className="panel-title">Khung hiển thị các bước đoán</h2>
          </div>
          {status === 'running' && (
            <div className="live-pill animate-pulse">
              <span className="live-dot" />
              <span>Đang giải bước {steps.length}...</span>
            </div>
          )}
        </div>

        {/* Wordle Board Grid */}
        <div className="board-scrollable-area">
          <div
            className="wordle-board-matrix"
            style={{
              gridTemplateRows: `repeat(${totalGridRows}, minmax(46px, 56px))`,
            }}
          >
            {Array.from({ length: totalGridRows }).map((_, rowIdx) => {
              const stepData = steps[rowIdx];
              const isRowActive = !!stepData;

              return (
                <div
                  key={`row-${rowIdx}`}
                  className={`wordle-row-container ${isRowActive ? 'active' : 'empty'}`}
                  style={{
                    gridTemplateColumns: `repeat(${activeWordSize}, minmax(46px, 56px))`,
                  }}
                >
                  {Array.from({ length: activeWordSize }).map((_, colIdx) => {
                    const charObj = stepData?.results?.[colIdx];
                    const letter = charObj?.guess || stepData?.guess?.[colIdx] || '';
                    const resultState = charObj?.result || '';
                    const isFlipped = flippedRows[rowIdx]?.[colIdx] || false;

                    const tileClasses = [
                      'wordle-tile-cell',
                      letter ? 'has-char' : 'is-blank',
                      isFlipped ? `flipped state-${resultState}` : '',
                    ]
                      .filter(Boolean)
                      .join(' ');

                    return (
                      <div key={`tile-${rowIdx}-${colIdx}`} className={tileClasses}>
                        <div className="tile-flipper">
                          <div className="face face-front">{letter.toUpperCase()}</div>
                          <div className="face face-back">{letter.toUpperCase()}</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </div>
        </div>

        {/* Mini Legend Footer */}
        <div className="board-legend">
          <div className="legend-item">
            <span className="legend-dot correct" />
            <span>Đúng vị trí (Correct)</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot present" />
            <span>Sai vị trí (Present)</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot absent" />
            <span>Không có (Absent)</span>
          </div>
        </div>
      </main>

      {/* =========================================================================
          BOX 3: RIGHT PANEL - ANALYTICS, CHART & ALPHABET MATRIX (Kết quả & Phân tích)
         ========================================================================= */}
      <aside className="panel-box right-panel">
        <div className="panel-header">
          <div className="panel-title-group">
            <BarChart3 size={18} className="panel-icon text-emerald" />
            <h2 className="panel-title">Kết quả & Phân tích</h2>
          </div>
          {solveStats.isSuccess && (
            <span className="badge-pill success">
              <CheckCircle2 size={13} />
              Thắng
            </span>
          )}
        </div>

        {/* Final Result Card */}
        <div className={`result-summary-card ${solveStats.isSuccess ? 'success-border' : ''}`}>
          <div className="result-main-row">
            <div>
              <span className="result-label">Từ bí mật tìm được</span>
              <div className="result-target-word">
                {targetWord ? targetWord.toUpperCase() : '------'}
              </div>
            </div>
            <div className="attempts-pill">
              <span className="attempts-count">
                {solveStats.totalAttempts || steps.length}
              </span>
              <span className="attempts-label">lần đoán</span>
            </div>
          </div>
          {solveStats.message && (
            <p className="result-message-text">{solveStats.message}</p>
          )}
          {solveStats.elapsedMs > 0 && (
            <div className="time-badge">
              <Timer size={13} />
              <span>Thời gian: {(solveStats.elapsedMs / 1000).toFixed(2)}s</span>
            </div>
          )}
        </div>

        {/* Search Space Reduction Graph (Đồ thị thu hẹp không gian tìm kiếm) */}
        <div className="analytics-card">
          <div className="analytics-card-header">
            <Layers size={15} className="text-cyan" />
            <h3 className="analytics-card-title">Đồ thị thu hẹp không gian tìm kiếm</h3>
          </div>
          <div className="chart-container">
            {steps.length === 0 ? (
              <div className="chart-placeholder">
                <BarChart3 size={28} className="text-muted" />
                <span>Bắt đầu đoán để theo dõi đồ thị thu hẹp</span>
              </div>
            ) : (
              <div className="bars-graph">
                {steps.map((s, idx) => {
                  const count =
                    typeof s.remainingCount === 'number' ? s.remainingCount : 2500;
                  // Logarithmic height scale for clean presentation
                  const maxLog = Math.log10(3000);
                  const currLog = Math.max(0.2, Math.log10(Math.max(1, count)));
                  const heightPercent = Math.min(100, Math.max(15, (currLog / maxLog) * 100));

                  return (
                    <div key={`bar-${idx}`} className="bar-column">
                      <span className="bar-count-label">
                        {count === 1 && s.results?.every((r) => r.result === 'correct')
                          ? '1 (ĐÚNG)'
                          : count}
                      </span>
                      <div className="bar-track">
                        <div
                          className="bar-fill"
                          style={{
                            height: `${heightPercent}%`,
                            background:
                              idx === steps.length - 1 && solveStats.isSuccess
                                ? 'linear-gradient(180deg, #10b981, #059669)'
                                : 'linear-gradient(180deg, #6366f1, #3b82f6)',
                          }}
                        />
                      </div>
                      <span className="bar-step-label">Lần {s.step}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Alphabet A-Z Status Matrix (Bảng chữ cái đã kiểm tra / loại bỏ) */}
        <div className="analytics-card">
          <div className="analytics-card-header">
            <Zap size={15} className="text-amber" />
            <h3 className="analytics-card-title">Bảng chữ cái A-Z đã phân tích</h3>
          </div>
          <div className="alphabet-grid">
            {ALPHABET.map((char) => {
              const state = letterStatusMap[char] || 'untested';
              return (
                <div key={char} className={`alpha-tile state-${state}`}>
                  {char}
                </div>
              );
            })}
          </div>
        </div>

        {/* Step Breakdown History List */}
        <div className="analytics-card flex-grow">
          <div className="analytics-card-header">
            <Info size={15} className="text-indigo" />
            <h3 className="analytics-card-title">Lịch sử các bước đoán</h3>
          </div>
          <div className="steps-history-list">
            {steps.length === 0 ? (
              <p className="no-steps-text">Chưa có bước đoán nào.</p>
            ) : (
              steps.map((stepItem) => (
                <div key={`hist-${stepItem.step}`} className="step-history-item">
                  <span className="step-num-badge">Lần {stepItem.step}</span>
                  <span className="step-word-str">{stepItem.guess?.toUpperCase()}</span>
                  <div className="step-dots-row">
                    {stepItem.results?.map((res, dotIdx) => (
                      <span
                        key={dotIdx}
                        className={`mini-result-dot ${res.result}`}
                        title={`${res.guess}: ${res.result}`}
                      />
                    ))}
                  </div>
                  <span className="step-cand-badge">
                    {stepItem.remainingCount !== undefined
                      ? `Còn ${stepItem.remainingCount} từ`
                      : 'Đang tính...'}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </aside>
    </div>
  );
}
