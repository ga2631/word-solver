import React, { useState, useEffect, useRef } from 'react';
import { Play, RotateCcw, Sparkles, CheckCircle2, AlertCircle, Calendar, Shuffle, Edit3, HelpCircle } from 'lucide-react';
import { resolveWordle } from '../services/api';

const MODE_CONFIG = {
  daily: {
    label: 'Daily',
    description: 'Đoán từ thử thách mỗi ngày',
    icon: Calendar,
  },
  random: {
    label: 'Random',
    description: 'Đoán từ ngẫu nhiên từ kho từ vựng',
    icon: Shuffle,
  },
  selected: {
    label: 'Selected',
    description: 'Nhập từ bí mật cần hệ thống tự động đoán',
    icon: Edit3,
  },
};

export function WordleVisualizer() {
  const [mode, setMode] = useState('daily');
  const [selectedWord, setSelectedWord] = useState('');
  const [startingWord, setStartingWord] = useState('crane');
  const [wordLength, setWordLength] = useState(5);

  // Resolution status: 'idle' | 'loading' | 'animating' | 'completed' | 'error'
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState(null);

  // Resolution data from API
  const [resolveResult, setResolveResult] = useState(null);

  // Animation state
  // revealedRows: number of rows currently rendered
  // flippedTiles: 2D boolean array [rowIdx][colIdx] indicating if tile has completed flip
  const [revealedRowCount, setRevealedRowCount] = useState(0);
  const [flippedTiles, setFlippedTiles] = useState([]);

  const animationTimersRef = useRef([]);

  const clearTimers = () => {
    animationTimersRef.current.forEach((t) => clearTimeout(t));
    animationTimersRef.current = [];
  };

  useEffect(() => {
    return () => clearTimers();
  }, []);

  const handleModeChange = (newMode) => {
    if (status === 'loading' || status === 'animating') return;
    setMode(newMode);
    handleReset();
  };

  const handleReset = () => {
    clearTimers();
    setStatus('idle');
    setError(null);
    setResolveResult(null);
    setRevealedRowCount(0);
    setFlippedTiles([]);
  };

  const handleStartResolving = async () => {
    if (status === 'loading' || status === 'animating') return;

    setError(null);

    // Validation for 'selected' mode
    if (mode === 'selected') {
      const cleanWord = selectedWord.trim().toLowerCase();
      if (!cleanWord) {
        setError('Vui lòng nhập từ cần đoán (Target Word).');
        return;
      }
      if (!/^[a-zA-Z]+$/.test(cleanWord)) {
        setError('Từ cần đoán chỉ được chứa các chữ cái tiếng Anh (a-z).');
        return;
      }
      if (cleanWord.length < 2 || cleanWord.length > 15) {
        setError('Độ dài từ cần đoán nên từ 2 đến 15 ký tự.');
        return;
      }
    }

    setStatus('loading');
    setRevealedRowCount(0);
    setFlippedTiles([]);

    try {
      const targetMode = mode === 'selected' ? 'word' : mode;
      const payload = {
        mode: targetMode,
        size: mode === 'selected' ? selectedWord.trim().length : wordLength,
        word: mode === 'selected' ? selectedWord.trim().toLowerCase() : undefined,
        startingWord: startingWord.trim() || undefined,
      };

      const result = await resolveWordle(payload);
      setResolveResult(result);
      runFlipAnimation(result.steps || []);
    } catch (err) {
      setError(err.message || 'Không thể kết nối đến API resolve.');
      setStatus('error');
    }
  };

  const runFlipAnimation = (steps) => {
    clearTimers();
    if (!steps || steps.length === 0) {
      setStatus('completed');
      return;
    }

    setStatus('animating');

    const totalSteps = steps.length;
    const initialFlipped = steps.map((step) => new Array(step.results.length).fill(false));
    setFlippedTiles(initialFlipped);

    let delayAccumulator = 100;

    steps.forEach((step, rowIdx) => {
      // 1. Reveal the row (letters appear)
      const rowRevealTimer = setTimeout(() => {
        setRevealedRowCount((prev) => Math.max(prev, rowIdx + 1));
      }, delayAccumulator);
      animationTimersRef.current.push(rowRevealTimer);

      delayAccumulator += 150;

      // 2. Flip each tile with staggered delay
      step.results.forEach((_, colIdx) => {
        const tileFlipTimer = setTimeout(() => {
          setFlippedTiles((prev) => {
            const next = prev.map((row) => [...row]);
            if (next[rowIdx]) {
              next[rowIdx][colIdx] = true;
            }
            return next;
          });
        }, delayAccumulator);
        animationTimersRef.current.push(tileFlipTimer);
        delayAccumulator += 200;
      });

      // Pause briefly between rows
      delayAccumulator += 300;
    });

    // 3. Mark animation as completed
    const finalTimer = setTimeout(() => {
      setStatus('completed');
    }, delayAccumulator + 200);
    animationTimersRef.current.push(finalTimer);
  };

  // Determine grid dimensions
  const activeSteps = resolveResult?.steps || [];
  const totalGridRows = Math.max(6, activeSteps.length);
  const activeWordSize =
    mode === 'selected' && selectedWord
      ? selectedWord.trim().length
      : resolveResult?.steps?.[0]?.guess?.length || wordLength;

  return (
    <div className="wordle-visualizer-container">
      {/* Control Panel */}
      <div className="solver-control-panel">
        {/* Mode Selector Tabs */}
        <div className="mode-selector-group">
          <span className="control-label">Chế độ đoán:</span>
          <div className="mode-tabs">
            {Object.entries(MODE_CONFIG).map(([modeKey, config]) => {
              const Icon = config.icon;
              const isActive = mode === modeKey;
              return (
                <button
                  key={modeKey}
                  type="button"
                  className={`mode-tab-btn ${isActive ? 'active' : ''}`}
                  onClick={() => handleModeChange(modeKey)}
                  disabled={status === 'loading' || status === 'animating'}
                >
                  <Icon size={16} />
                  <span>{config.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Selected Word Input (Conditional for 'selected' mode) */}
        {mode === 'selected' && (
          <div className="selected-word-input-container">
            <label className="control-label" htmlFor="selected-word-input">
              Từ cần giải (Secret Word):
            </label>
            <div className="input-with-badge">
              <input
                id="selected-word-input"
                type="text"
                className="form-input selected-input"
                placeholder="Nhập từ bí mật (ví dụ: apple, tiger, plant...)"
                value={selectedWord}
                onChange={(e) => setSelectedWord(e.target.value.replace(/[^a-zA-Z]/g, ''))}
                disabled={status === 'loading' || status === 'animating'}
                maxLength={15}
                autoComplete="off"
                spellCheck="false"
              />
              {selectedWord && (
                <span className="length-badge">{selectedWord.length} chữ cái</span>
              )}
            </div>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="alert-box error">
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        {/* Action Buttons */}
        <div className="action-buttons-container">
          <button
            id="start-resolve-btn"
            type="button"
            className="btn-primary start-btn"
            onClick={handleStartResolving}
            disabled={status === 'loading' || status === 'animating'}
          >
            {status === 'loading' || status === 'animating' ? (
              <>
                <RotateCcw className="animate-spin" size={18} />
                <span>Đang giải từ...</span>
              </>
            ) : (
              <>
                <Play size={18} fill="currentColor" />
                <span>Bắt đầu đoán từ</span>
              </>
            )}
          </button>

          <button
            id="reset-btn"
            type="button"
            className="btn-secondary reset-btn"
            onClick={handleReset}
            disabled={status === 'loading'}
          >
            <RotateCcw size={18} />
            <span>Đoán lại</span>
          </button>
        </div>
      </div>

      {/* Wordle Board Presentation */}
      <div className="board-wrapper">
        <div
          className="wordle-grid"
          style={{
            gridTemplateRows: `repeat(${totalGridRows}, minmax(52px, 62px))`,
          }}
        >
          {Array.from({ length: totalGridRows }).map((_, rowIdx) => {
            const stepData = activeSteps[rowIdx];
            const isRowRevealed = rowIdx < revealedRowCount && stepData;

            return (
              <div
                key={`row-${rowIdx}`}
                className={`wordle-row ${isRowRevealed ? 'revealed' : ''}`}
                style={{
                  gridTemplateColumns: `repeat(${activeWordSize}, minmax(52px, 62px))`,
                }}
              >
                {Array.from({ length: activeWordSize }).map((_, colIdx) => {
                  let letter = '';
                  let resultState = '';
                  let isFlipped = false;

                  if (isRowRevealed && stepData) {
                    const charObj = stepData.results?.[colIdx];
                    letter = charObj?.guess || stepData.guess?.[colIdx] || '';
                    resultState = charObj?.result || '';
                    isFlipped = flippedTiles[rowIdx]?.[colIdx] || false;
                  }

                  const tileClasses = [
                    'wordle-tile',
                    letter ? 'has-letter' : 'empty',
                    isFlipped ? `flipped state-${resultState}` : '',
                  ]
                    .filter(Boolean)
                    .join(' ');

                  return (
                    <div key={`tile-${rowIdx}-${colIdx}`} className={tileClasses}>
                      <div className="tile-inner">
                        <div className="tile-front">{letter.toUpperCase()}</div>
                        <div className="tile-back">{letter.toUpperCase()}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>
      </div>

      {/* Result Stats & Breakdown */}
      {resolveResult && (status === 'animating' || status === 'completed') && (
        <div className="solve-summary-card">
          <div className="summary-header">
            <div className="status-indicator">
              <CheckCircle2 size={22} className="text-emerald" />
              <div>
                <h3 className="summary-title">
                  {resolveResult.success ? 'Giải thành công!' : 'Kết quả đoán từ'}
                </h3>
                <p className="summary-subtitle">{resolveResult.message}</p>
              </div>
            </div>

            {resolveResult.target_word && (
              <div className="target-word-badge">
                <span className="badge-label">Từ bí mật:</span>
                <span className="badge-value">{resolveResult.target_word.toUpperCase()}</span>
              </div>
            )}
          </div>

          {/* Quick Metrics */}
          <div className="metrics-grid">
            <div className="metric-box">
              <div className="metric-label">Tổng số lần đoán</div>
              <div className="metric-value">{resolveResult.total_attempts}</div>
            </div>
            <div className="metric-box">
              <div className="metric-label">Từ khởi đầu</div>
              <div className="metric-value highlight">{resolveResult.starting_word?.toUpperCase()}</div>
            </div>
            <div className="metric-box">
              <div className="metric-label">Chế độ giải</div>
              <div className="metric-value capitalize">{resolveResult.mode}</div>
            </div>
          </div>

          {/* Step Timeline */}
          <div className="timeline-section">
            <h4 className="timeline-title">Quá trình thu hẹp không gian tìm kiếm (Information Gain)</h4>
            <div className="timeline-list">
              {activeSteps.slice(0, revealedRowCount).map((step) => (
                <div key={`timeline-${step.step}`} className="timeline-item">
                  <div className="step-badge">Lần {step.step}</div>
                  <div className="step-guess">{step.guess?.toUpperCase()}</div>
                  <div className="step-results-mini">
                    {step.results.map((r, i) => (
                      <span key={i} className={`mini-dot state-${r.result}`} title={`${r.guess}: ${r.result}`} />
                    ))}
                  </div>
                  <div className="step-remaining">
                    Còn lại:{' '}
                    <strong>
                      {step.remaining_candidates_count === 1 && step.step === resolveResult.total_attempts
                        ? '1 (Đã tìm ra từ)'
                        : `${step.remaining_candidates_count} từ`}
                    </strong>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
