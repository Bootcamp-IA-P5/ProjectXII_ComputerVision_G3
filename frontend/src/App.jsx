import { useState } from 'react';
import UploadSection from './components/UploadSection';
import ProgressBar from './components/ProgressBar';
import LogoResults from './components/LogoResults';
import './App.css';
import './components/components.css';

function App() {
    const [youtubeUrl, setYoutubeUrl] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [uploadComplete, setUploadComplete] = useState(false);
    const [error, setError] = useState('');
    const [logoResults, setLogoResults] = useState([]);

    const validateYoutubeUrl = (url) => {
        const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w-]+/;
        return youtubeRegex.test(url);
    };

    const handleUpload = async () => {
        // Reset states
        setError('');
        setUploadComplete(false);
        setLogoResults([]);

        // Validate URL
        if (!validateYoutubeUrl(youtubeUrl)) {
            setError('Por favor, introduce una URL válida de YouTube');
            return;
        }

        setIsLoading(true);
        setProgress(0);

        try {
            // Simulate progress
            const progressInterval = setInterval(() => {
                setProgress((prev) => {
                    if (prev >= 90) {
                        clearInterval(progressInterval);
                        return 90;
                    }
                    return prev + 10;
                });
            }, 500);

            // TODO: Replace with actual API call to your backend
            // Example API call structure:
            // const response = await fetch('http://localhost:8000/api/analyze', {
            //   method: 'POST',
            //   headers: {
            //     'Content-Type': 'application/json',
            //   },
            //   body: JSON.stringify({ youtube_url: youtubeUrl }),
            // });
            // const data = await response.json();

            // Simulate API call with timeout
            await new Promise((resolve) => setTimeout(resolve, 5000));

            // Clear progress interval and set to 100%
            clearInterval(progressInterval);
            setProgress(100);

            // Mock data - Replace with actual API response
            const mockResults = [
                {
                    name: 'Nike',
                    screenTime: 45.5,
                    appearances: 12
                },
                {
                    name: 'Adidas',
                    screenTime: 32.8,
                    appearances: 8
                },
                {
                    name: 'Coca-Cola',
                    screenTime: 28.3,
                    appearances: 6
                },
                {
                    name: 'Apple',
                    screenTime: 15.7,
                    appearances: 4
                }
            ];

            setLogoResults(mockResults);
            setUploadComplete(true);

        } catch (err) {
            setError('Error al procesar el video. Por favor, inténtalo de nuevo.');
            console.error('Upload error:', err);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="app">
            <div className="container">
                <header className="app-header">
                    <h1>🎬 YouTube Logo Detector</h1>
                    <p className="app-subtitle">
                        Analiza videos de YouTube y detecta logos con inteligencia artificial
                    </p>
                </header>

                <main className="app-main">
                    <UploadSection
                        youtubeUrl={youtubeUrl}
                        setYoutubeUrl={setYoutubeUrl}
                        onUpload={handleUpload}
                        isLoading={isLoading}
                        error={error}
                    />

                    {isLoading && (
                        <ProgressBar progress={progress} />
                    )}

                    {uploadComplete && !isLoading && (
                        <div className="success-message">
                            <span className="success-icon">✅</span>
                            <p className="success-text">¡Video cargado y analizado exitosamente!</p>
                        </div>
                    )}

                    {logoResults.length > 0 && (
                        <LogoResults results={logoResults} />
                    )}
                </main>

                <footer className="app-footer">
                    <p>Desarrollado con ❤️ usando React + Vite</p>
                </footer>
            </div>
        </div>
    );
}

export default App;
