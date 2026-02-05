import React from 'react';

const UploadSection = ({ youtubeUrl, setYoutubeUrl, onUpload, isLoading, error }) => {
    const handleSubmit = (e) => {
        e.preventDefault();
        onUpload();
    };

    return (
        <div className="upload-section">
            <form onSubmit={handleSubmit}>
                <div className="input-group">
                    <label htmlFor="youtube-url" className="input-label">
                        URL de YouTube
                    </label>
                    <input
                        id="youtube-url"
                        type="text"
                        className="input-field"
                        placeholder="https://www.youtube.com/watch?v=..."
                        value={youtubeUrl}
                        onChange={(e) => setYoutubeUrl(e.target.value)}
                        disabled={isLoading}
                    />
                </div>

                <button
                    type="submit"
                    className="btn"
                    disabled={isLoading || !youtubeUrl.trim()}
                >
                    {isLoading ? (
                        <>
                            <span className="spinner"></span>
                            Procesando...
                        </>
                    ) : (
                        <>
                            📤 Subir y Analizar Video
                        </>
                    )}
                </button>

                {error && (
                    <div className="error-message">
                        ⚠️ {error}
                    </div>
                )}
            </form>
        </div>
    );
};

export default UploadSection;
