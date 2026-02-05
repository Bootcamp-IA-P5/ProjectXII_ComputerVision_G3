import React from 'react';

const ProgressBar = ({ progress }) => {
    return (
        <div className="progress-container">
            <div className="progress-bar-wrapper">
                <div
                    className="progress-bar-fill"
                    style={{ width: `${progress}%` }}
                ></div>
            </div>
            <span className="progress-text">
                {progress}% completado
            </span>
        </div>
    );
};

export default ProgressBar;
