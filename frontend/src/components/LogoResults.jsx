import React from 'react';

const LogoResults = ({ results }) => {
    if (!results || results.length === 0) {
        return null;
    }

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    return (
        <div className="results-section">
            <div className="results-header">
                <h2>📊 Resultados del Análisis</h2>
                <p>Se detectaron {results.length} logo{results.length !== 1 ? 's' : ''} en el video</p>
            </div>

            <div className="results-grid">
                {results.map((logo, index) => (
                    <div key={index} className="logo-card">
                        <div className="logo-name">
                            <span className="logo-icon">🏷️</span>
                            {logo.name}
                        </div>

                        <div className="logo-stats">
                            <div className="stat-item">
                                <span className="stat-label">Tiempo en pantalla</span>
                                <span className="stat-value">{formatTime(logo.screenTime)}</span>
                            </div>

                            <div className="stat-item">
                                <span className="stat-label">Apariciones</span>
                                <span className="stat-value">{logo.appearances}</span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default LogoResults;
