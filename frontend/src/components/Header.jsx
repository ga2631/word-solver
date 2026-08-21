import React from 'react';
import { Sparkles, FileText } from 'lucide-react';

export function Header({ isHealthy }) {
  return (
    <header className="header">
      <div className="header-inner">
        <div className="brand">
          <div className="brand-icon">
            <Sparkles size={22} />
          </div>
          <span className="brand-title">WordCraft</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              fontSize: '0.875rem',
              color: 'var(--text-secondary)',
            }}
          >
            <FileText size={16} />
            <span>API Docs</span>
          </a>

          <div className="status-badge">
            <span className={`status-dot ${isHealthy ? 'online' : 'offline'}`}></span>
            <span>{isHealthy ? 'API Connected' : 'API Connecting...'}</span>
          </div>
        </div>
      </div>
    </header>
  );
}

