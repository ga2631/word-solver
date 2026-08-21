import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { WordleVisualizer } from './components/WordleVisualizer';
import { checkHealth } from './services/api';
import './App.css';

export function App() {
  const [isHealthy, setIsHealthy] = useState(false);

  useEffect(() => {
    const verifyHealth = async () => {
      try {
        await checkHealth();
        setIsHealthy(true);
      } catch (err) {
        setIsHealthy(false);
      }
    };

    verifyHealth();
    const interval = setInterval(verifyHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app-container">
      <Header isHealthy={isHealthy}/>
      <main className="main-content">
        <WordleVisualizer />
      </main>
      <footer className="footer">
        <p>© 2026 WordCraft • Full-Stack Python FastAPI & ReactJS Architecture with Docker</p>
      </footer>
    </div>
  );
}

export default App;

