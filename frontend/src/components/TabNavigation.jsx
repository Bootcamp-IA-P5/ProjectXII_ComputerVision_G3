import React from 'react';

const TabNavigation = ({ activeTab, setActiveTab }) => {
    return (
        <div className="tab-navigation">
            <button
                className={`tab-button ${activeTab === 'analysis' ? 'active' : ''}`}
                onClick={() => setActiveTab('analysis')}
            >
                <span className="tab-icon">🎬</span>
                <span className="tab-label">Análisis</span>
            </button>
            <button
                className={`tab-button ${activeTab === 'history' ? 'active' : ''}`}
                onClick={() => setActiveTab('history')}
            >
                <span className="tab-icon">📊</span>
                <span className="tab-label">Historial</span>
            </button>
        </div>
    );
};

export default TabNavigation;
