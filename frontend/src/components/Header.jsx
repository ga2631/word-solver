import React from 'react';
import { Sparkles, FileText } from 'lucide-react';

export function Header({ isHealthy }) {
  return (
    <header className="header">
      <div className="header-inner">
        <div className="brand">
          <div className="brand-icon">
            <Sparkles size={20} />
          </div>
          <span className="brand-title">Word Solver</span>
        </div>

        <div className="header-actions">
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="header-link"
          >
            <FileText size={14} />
            <span>API Docs</span>
          </a>

          <div className="status-badge">
            <span className={`status-dot ${isHealthy ? 'online' : 'offline'}`}></span>
            <span>{isHealthy ? 'API Online' : 'Connecting...'}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
